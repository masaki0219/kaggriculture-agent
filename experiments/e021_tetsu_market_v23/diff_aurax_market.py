#!/usr/bin/env python3
"""
2026-09-18 — Diff E21 vs aurax V7 at policy-block level

Run from the Kaggle repository root:

    python experiments/e021_tetsu_market_v23/diff_aurax_market.py

Outputs:
    experiments/e021_tetsu_market_v23/aurax_market_diff.md
    experiments/e021_tetsu_market_v23/aurax_market_diff.json

Purpose
-------
Failure-regime analysis showed E21 and aurax realize almost identical farms.
This script therefore compares their exact local artifacts at AST/policy-block
level and surfaces only the blocks most related to market execution.

It does NOT modify any agent and does NOT submit anything.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import ast
import difflib
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
ELITE = ROOT / "artifacts" / "bundles" / "current" / "public_agents" / "elite"

TETSU_DIR = ELITE / "tetsu_market_v23_current"
AURAX_DIR = ELITE / "aurax7_v7_current"

REPORT = HERE / "aurax_market_diff.md"
DATA = HERE / "aurax_market_diff.json"
HISTORY = ROOT / "docs" / "experiment_run_history.md"

MARKET_PATTERNS = [
    r"\bSELL\b", r"\bBUY_PRODUCT\b", r"\bmarket\b", r"\bprice\b",
    r"\bprices\b", r"\bsell\b", r"\bbuy\b", r"\bshed\b",
    r"\binventory\b", r"\bprojected\b", r"\bsuppress\b",
    r"\blead\b", r"\bfront\b", r"\brace\b", r"\bquote\b",
    r"\bliquid", r"\bdead_stock\b", r"\bclamp",
]

PRODUCTION_PATTERNS = [
    r"\bPLANT\b", r"\bBUY_SEED\b", r"\bBUY_ANIMAL\b",
    r"\bCOW\b", r"\bSHEEP\b", r"\bGOOSE\b", r"\bWHEAT\b",
    r"\bCARROT\b", r"\bTOMATO\b", r"\bSTRAWBERRY\b", r"\bMELON\b",
    r"\bBUILD_PASTURE\b", r"\bBUILD_COOP\b", r"\bCARE\b",
    r"\bFEED\b", r"\bFERTILIZE\b", r"\bHARVEST\b",
]


def resolve_entrypoint(base: Path) -> Path:
    ep = base / "entrypoint.txt"
    if ep.exists():
        rel = ep.read_text(encoding="utf-8").strip()
        p = base / rel
        if p.exists():
            return p

    # Conservative fallback: prefer extracted main.py files.
    candidates = sorted(base.rglob("main.py"))
    if not candidates:
        raise SystemExit(f"No main.py under {base}")
    candidates.sort(
        key=lambda p: (
            "_extract" in str(p),
            "raw" in str(p),
            p.stat().st_size,
        ),
        reverse=True,
    )
    return candidates[0]


def read(path: Path):
    return path.read_text(encoding="utf-8", errors="replace")


def score(text: str, patterns):
    return sum(len(re.findall(p, text, flags=re.I)) for p in patterns)


def normalized_ast(node):
    return ast.dump(node, annotate_fields=True, include_attributes=False)


def top_units(text: str):
    tree = ast.parse(text)
    lines = text.splitlines()
    counts = Counter()
    units = []

    for node in tree.body:
        if not isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue

        name = node.name
        counts[(type(node).__name__, name)] += 1
        ordinal = counts[(type(node).__name__, name)]
        key = f"{type(node).__name__}:{name}#{ordinal}"

        start = node.lineno
        end = getattr(node, "end_lineno", start)
        src = "\n".join(lines[start - 1:end])

        units.append({
            "key": key,
            "name": name,
            "kind": type(node).__name__,
            "ordinal": ordinal,
            "start": start,
            "end": end,
            "source": src,
            "ast": normalized_ast(node),
            "market_score": score(src, MARKET_PATTERNS),
            "production_score": score(src, PRODUCTION_PATTERNS),
        })
    return units


def assignment_units(text: str):
    tree = ast.parse(text)
    lines = text.splitlines()
    units = []
    counts = Counter()

    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue

        names = []
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for t in targets:
            if isinstance(t, ast.Name):
                names.append(t.id)

        if not names:
            continue

        joined = ",".join(names)
        counts[joined] += 1
        key = f"Assign:{joined}#{counts[joined]}"

        start = node.lineno
        end = getattr(node, "end_lineno", start)
        src = "\n".join(lines[start - 1:end])

        # Only retain assignments likely to configure market/runtime behavior.
        ms = score(src, MARKET_PATTERNS)
        if ms <= 0 and not any(
            token in joined.upper()
            for token in ("SETTING", "RACE", "MARKET", "SELL", "PRICE", "ROUTE")
        ):
            continue

        units.append({
            "key": key,
            "name": joined,
            "kind": "Assign",
            "ordinal": counts[joined],
            "start": start,
            "end": end,
            "source": src,
            "ast": normalized_ast(node),
            "market_score": ms,
            "production_score": score(src, PRODUCTION_PATTERNS),
        })

    return units


def index(units):
    return {u["key"]: u for u in units}


def trunc(s: str, n=4000):
    if len(s) <= n:
        return s
    return s[:n] + "\n... [truncated] ..."


def unified(a, b, a_label, b_label):
    return "\n".join(
        difflib.unified_diff(
            a.splitlines(),
            b.splitlines(),
            fromfile=a_label,
            tofile=b_label,
            lineterm="",
            n=3,
        )
    )


def main():
    tetsu_path = resolve_entrypoint(TETSU_DIR)
    aurax_path = resolve_entrypoint(AURAX_DIR)

    t_text = read(tetsu_path)
    a_text = read(aurax_path)

    t_sha = hashlib.sha256(tetsu_path.read_bytes()).hexdigest()
    a_sha = hashlib.sha256(aurax_path.read_bytes()).hexdigest()

    t_units = top_units(t_text) + assignment_units(t_text)
    a_units = top_units(a_text) + assignment_units(a_text)

    ti = index(t_units)
    ai = index(a_units)

    all_keys = sorted(set(ti) | set(ai))
    diffs = []

    for key in all_keys:
        t = ti.get(key)
        a = ai.get(key)

        if t and a and t["ast"] == a["ast"]:
            continue

        ms = max(
            t["market_score"] if t else 0,
            a["market_score"] if a else 0,
        )
        ps = max(
            t["production_score"] if t else 0,
            a["production_score"] if a else 0,
        )

        if ms <= 0:
            continue

        status = (
            "changed" if t and a
            else "tetsu-only" if t
            else "aurax-only"
        )

        diffs.append({
            "key": key,
            "status": status,
            "market_score": ms,
            "production_score": ps,
            "tetsu": t,
            "aurax": a,
        })

    diffs.sort(
        key=lambda d: (
            d["market_score"] - 0.5 * d["production_score"],
            d["market_score"],
        ),
        reverse=True,
    )

    # Also compute exact top-level source similarity for context.
    t_lines = t_text.splitlines()
    a_lines = a_text.splitlines()
    ratio = difflib.SequenceMatcher(None, t_lines, a_lines, autojunk=False).ratio()

    now = datetime.now().astimezone().isoformat(timespec="seconds")

    payload = {
        "generated": now,
        "tetsu": {
            "path": str(tetsu_path.relative_to(ROOT)),
            "sha256": t_sha,
            "lines": len(t_lines),
        },
        "aurax": {
            "path": str(aurax_path.relative_to(ROOT)),
            "sha256": a_sha,
            "lines": len(a_lines),
        },
        "line_similarity": ratio,
        "market_related_diffs": [
            {
                "key": d["key"],
                "status": d["status"],
                "market_score": d["market_score"],
                "production_score": d["production_score"],
                "tetsu_lines": (
                    [d["tetsu"]["start"], d["tetsu"]["end"]]
                    if d["tetsu"] else None
                ),
                "aurax_lines": (
                    [d["aurax"]["start"], d["aurax"]["end"]]
                    if d["aurax"] else None
                ),
            }
            for d in diffs
        ],
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# E21 vs aurax V7 — Market Policy Diff",
        "",
        f"- Generated: `{now}`",
        f"- Tetsu/E21: `{tetsu_path.relative_to(ROOT)}`",
        f"- Tetsu SHA256: `{t_sha}`",
        f"- aurax: `{aurax_path.relative_to(ROOT)}`",
        f"- aurax SHA256: `{a_sha}`",
        f"- Whole-file line similarity: **{ratio:.3f}**",
        f"- Market-related differing blocks: **{len(diffs)}**",
        "",
        "Purpose: choose an architecturally complete market-policy block for E22, "
        "not add one-off shop/seed patches.",
        "",
        "## 1. Ranked market-related block differences",
        "",
        "| Rank | Block | Status | Market score | Production score | E21 lines | aurax lines |",
        "|---:|---|---|---:|---:|---:|---:|",
    ]

    for i, d in enumerate(diffs, 1):
        tline = (
            f"{d['tetsu']['start']}-{d['tetsu']['end']}"
            if d["tetsu"] else "—"
        )
        aline = (
            f"{d['aurax']['start']}-{d['aurax']['end']}"
            if d["aurax"] else "—"
        )
        report.append(
            f"| {i} | `{d['key']}` | {d['status']} | "
            f"{d['market_score']} | {d['production_score']} | "
            f"{tline} | {aline} |"
        )

    report += [
        "",
        "## 2. High-value diffs",
        "",
        "The following blocks are market-heavy and are the first candidates for E22.",
        "",
    ]

    # Show only first 12 to keep report readable.
    for rank, d in enumerate(diffs[:12], 1):
        report += [
            f"### {rank}. `{d['key']}` — {d['status']}",
            "",
            f"- market_score: **{d['market_score']}**",
            f"- production_score: **{d['production_score']}**",
            "",
        ]

        if d["tetsu"] and d["aurax"]:
            diff_text = unified(
                d["tetsu"]["source"],
                d["aurax"]["source"],
                f"E21:{d['key']}",
                f"aurax:{d['key']}",
            )
            report += ["```diff", trunc(diff_text, 7000), "```", ""]
        elif d["tetsu"]:
            report += [
                "**E21-only block:**",
                "",
                "```python",
                trunc(d["tetsu"]["source"], 5000),
                "```",
                "",
            ]
        else:
            report += [
                "**aurax-only block:**",
                "",
                "```python",
                trunc(d["aurax"]["source"], 5000),
                "```",
                "",
            ]

    report += [
        "## 3. E22 selection rule",
        "",
        "- Prefer a block that changes SELL timing/ordering/price response while leaving route/farm planning untouched.",
        "- Do not copy a block solely because aurax wins particular seeds; E21 beats aurax overall in the current screen.",
        "- The first E22 should be a complete market-policy variant that can be toggled as a unit.",
        "- After E22 exists, test it on fresh seeds against E21, aurax, Ahmed, and a refreshed population-representative panel.",
        "",
        "Final objective remains population-level W/D/L / Bradley–Terry.",
        "",
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")

    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {now} — Diff E21 vs aurax market policy\n\n"
            f"- E21 SHA256: `{t_sha}`\n"
            f"- aurax SHA256: `{a_sha}`\n"
            f"- Market-related differing blocks: {len(diffs)}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- Read-only; no agent modification or Kaggle submission.\n\n"
        )

    print("=== E21 vs aurax market diff complete ===")
    print("E21:", tetsu_path.relative_to(ROOT))
    print("aurax:", aurax_path.relative_to(ROOT))
    print("Line similarity:", f"{ratio:.3f}")
    print("Market-related differing blocks:", len(diffs))
    print("Report:", REPORT.name)
    print("Data:", DATA.name)
    print()
    print("Top differing blocks:")
    for d in diffs[:10]:
        print(
            f"  {d['key']:<45} "
            f"status={d['status']:<10} "
            f"market={d['market_score']:<4} "
            f"production={d['production_score']}"
        )


if __name__ == "__main__":
    main()
