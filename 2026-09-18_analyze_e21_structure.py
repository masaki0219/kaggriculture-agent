#!/usr/bin/env python3
"""
2026-09-18 — Analyze E21 Tetsu Market-Smart V23 structure

Place this file directly in the Kaggle repository root and run:

    python 2026-09-18_analyze_e21_structure.py

Output:
    2026-09-18_E21_STRUCTURE_REPORT.md

Purpose:
Map the frozen E21 agent into strategic regions before creating E22.
This script does NOT modify any agent and does NOT submit anything.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import ast
import hashlib
import re

ROOT = Path(__file__).resolve().parent
SOURCE = (
    ROOT / "artifacts" / "bundles" / "current"
    / "public_agents" / "elite" / "tetsu_market_v23_current"
    / "raw" / "_extract_submission_tar" / "main.py"
)
REPORT = ROOT / "2026-09-18_E21_STRUCTURE_REPORT.md"

CATEGORY_PATTERNS = {
    "shop-routing": [
        r"\bshop\b", r"\btown\b", r"YARN_STORE", r"PIZZA_SHOP",
        r"BRUNCH_SPOT", r"ICE_CREAM_SHOP", r"PET_CAFE",
        r"SMOOTHIE_SHOP", r"FARMERS_MARKET", r"BAKERY",
        r"unlocked_shops", r"demand",
    ],
    "production": [
        r"\bplant\b", r"\bseed\b", r"\bcrop\b", r"\bpasture\b",
        r"\bcoop\b", r"\bcow\b", r"\bsheep\b", r"\bgoose\b",
        r"\bwater\b", r"\bfeed\b", r"\bfertil", r"\bharvest\b",
        r"\bcollect\b", r"STRAWBERRY", r"TOMATO", r"CARROT",
        r"MELON", r"WHEAT", r"MILK", r"WOOL", r"EGG",
    ],
    "market": [
        r"\bsell\b", r"\bbuy\b", r"\bmarket\b", r"\bprice\b",
        r"\binventory\b", r"\bscarcity\b", r"\bspread\b",
        r"\border\b", r"\bliquid", r"\bfront.?run", r"\bmeter",
    ],
    "executor": [
        r"\bmove\b", r"\btask\b", r"\btarget\b", r"\bpath\b",
        r"\broute\b", r"\bassign\b", r"\bworker\b", r"\bhand\b",
        r"\bdistance\b", r"\bnearest\b", r"\baction\b",
    ],
    "endgame": [
        r"\bendgame\b", r"\bterminal\b", r"\blate\b", r"\bfinal\b",
        r"\bhorizon\b", r"\bremaining\b", r"\blast_day\b",
        r"\blast.?plant\b", r"\bstop\b",
    ],
    "opponent": [
        r"\bopponent\b", r"\benemy\b", r"\brival\b", r"\btheir\b",
        r"\bother_player\b", r"\bplayer.?1\b",
    ],
}

KEY_TERMS = [
    "SELL", "BUY", "market", "price", "shop", "town", "route", "target",
    "cow", "sheep", "goose", "strawberry", "tomato", "carrot", "melon",
    "wheat", "milk", "wool", "egg", "fertilizer", "terminal", "horizon",
    "front", "meter", "liquid", "worker", "hand",
]

def classify(text: str):
    scores = []
    for cat, pats in CATEGORY_PATTERNS.items():
        score = sum(len(re.findall(p, text, flags=re.I)) for p in pats)
        if score:
            scores.append((cat, score))
    scores.sort(key=lambda x: (-x[1], x[0]))
    return scores

def source_segment(lines, node):
    start = max(1, getattr(node, "lineno", 1))
    end = max(start, getattr(node, "end_lineno", start))
    return "\n".join(lines[start - 1:end])

def names_called(node):
    out = Counter()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            f = sub.func
            if isinstance(f, ast.Name):
                out[f.id] += 1
            elif isinstance(f, ast.Attribute):
                out[f.attr] += 1
    return out

def assigned_names(tree):
    names = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    names.append(t.id)
    return names

def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing E21 source: {SOURCE}")

    text = SOURCE.read_text(encoding="utf-8", errors="replace")
    sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    lines = text.splitlines()

    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        raise SystemExit(f"E21 source does not parse: {e}")

    top_defs = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            seg = source_segment(lines, node)
            top_defs.append({
                "name": node.name,
                "kind": type(node).__name__,
                "start": node.lineno,
                "end": getattr(node, "end_lineno", node.lineno),
                "lines": getattr(node, "end_lineno", node.lineno) - node.lineno + 1,
                "cats": classify(seg),
                "calls": names_called(node),
            })

    methods = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for sub in node.body:
            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                seg = source_segment(lines, sub)
                methods.append({
                    "name": f"{node.name}.{sub.name}",
                    "kind": "method",
                    "start": sub.lineno,
                    "end": getattr(sub, "end_lineno", sub.lineno),
                    "lines": getattr(sub, "end_lineno", sub.lineno) - sub.lineno + 1,
                    "cats": classify(seg),
                    "calls": names_called(sub),
                })

    units = top_defs + methods

    keyword_hits = defaultdict(list)
    for i, line in enumerate(lines, start=1):
        for term in KEY_TERMS:
            if term.lower() in line.lower():
                keyword_hits[term].append(i)

    seams = []
    for u in units:
        if u["lines"] < 4 or not u["cats"]:
            continue
        total = sum(v for _, v in u["cats"])
        purity = u["cats"][0][1] / max(1, total)
        if purity >= 0.45:
            seams.append((purity, u))
    seams.sort(key=lambda x: (-x[0], -x[1]["lines"]))

    hotspots = []
    for u in units:
        active = [(c, s) for c, s in u["cats"] if s >= 2]
        if len(active) >= 3 and u["lines"] >= 10:
            hotspots.append((sum(s for _, s in active), u, active))
    hotspots.sort(key=lambda x: (-x[0], -x[1]["lines"]))

    whole_categories = classify(text)

    def fmt_cats(cats):
        return ", ".join(f"{c}:{s}" for c, s in cats[:5]) if cats else "none"

    now = datetime.now().astimezone().isoformat(timespec="seconds")

    report = []
    report += [
        "# E21 Structure Report — Tetsu Market-Smart Farming V23",
        "",
        f"- Generated: `{now}`",
        f"- Source: `{SOURCE.relative_to(ROOT)}`",
        f"- SHA256: `{sha}`",
        f"- Source lines: **{len(lines)}**",
        "- Purpose: identify architectural seams before creating E22.",
        "- Static analysis only; strategic causality still requires games.",
        "",
        "## 1. Whole-source strategic footprint",
        "",
    ]
    for cat, score in whole_categories:
        report.append(f"- **{cat}**: {score} lexical hits")

    report += ["", "## 2. Top-level definitions", "",
               "| Definition | Kind | Lines | Categories |",
               "|---|---|---:|---|"]
    for u in top_defs:
        report.append(
            f"| `{u['name']}` | {u['kind']} | "
            f"{u['start']}-{u['end']} ({u['lines']}) | {fmt_cats(u['cats'])} |"
        )

    report += ["", "## 3. Class methods", "",
               "| Method | Lines | Categories |",
               "|---|---:|---|"]
    for u in methods:
        report.append(
            f"| `{u['name']}` | {u['start']}-{u['end']} ({u['lines']}) | "
            f"{fmt_cats(u['cats'])} |"
        )

    report += [
        "", "## 4. Candidate architectural seams", "",
        "Relatively concentrated functions/methods. Inspect these first when "
        "separating production planning from market execution.", ""
    ]
    for purity, u in seams[:30]:
        report.append(
            f"- `{u['name']}` lines {u['start']}-{u['end']}: "
            f"dominant **{u['cats'][0][0]}**, purity={purity:.2f}; "
            f"{fmt_cats(u['cats'])}"
        )
    if not seams:
        report.append("- No clear lexical seams detected.")

    report += [
        "", "## 5. Cross-coupling hotspots", "",
        "These units mix several concerns. Avoid threshold-only patches inside "
        "them unless the complete policy interaction is understood.", ""
    ]
    for _, u, active in hotspots[:25]:
        report.append(
            f"- `{u['name']}` lines {u['start']}-{u['end']}: "
            + ", ".join(f"{c}:{s}" for c, s in active[:6])
        )
    if not hotspots:
        report.append("- No large multi-category hotspots detected.")

    report += ["", "## 6. High-frequency calls", ""]
    global_calls = Counter()
    for u in top_defs:
        global_calls.update(u["calls"])
    for name, n in global_calls.most_common(40):
        report.append(f"- `{name}`: {n}")

    report += ["", "## 7. Important keyword locations", ""]
    for term in KEY_TERMS:
        hits = keyword_hits.get(term, [])
        if hits:
            preview = ", ".join(map(str, hits[:30]))
            tail = " ..." if len(hits) > 30 else ""
            report.append(f"- `{term}`: {preview}{tail} ({len(hits)} lines)")

    report += ["", "## 8. Top-level state/constants", ""]
    names = assigned_names(tree)
    report.append(", ".join(f"`{x}`" for x in names[:200]) if names
                  else "No top-level assignments detected.")

    report += [
        "", "## 9. E22 design rule", "",
        "Do **not** create E22 by changing one threshold only because it improves "
        "E21 head-to-head. E22 must represent a complete strategy hypothesis.",
        "",
        "The intended next hypothesis is: preserve frontier-grade market execution "
        "while introducing a coherent shop-conditioned production policy, then judge "
        "it on population-level W/D/L rather than E21 head-to-head alone.",
        "",
        "The next step is to inspect the highest-value seams/hotspots above and "
        "choose the smallest architecturally complete block that can support a "
        "separate shop-routed production policy.",
        "",
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("=== E21 structure analysis complete ===")
    print("Source SHA256:", sha)
    print("Definitions:", len(top_defs))
    print("Methods:", len(methods))
    print("Report:", REPORT.name)
    print("")
    print("Top candidate seams:")
    for purity, u in seams[:10]:
        print(
            f"  {u['name']:<40} "
            f"L{u['start']}-{u['end']} "
            f"{u['cats'][0][0]} purity={purity:.2f}"
        )

if __name__ == "__main__":
    main()
