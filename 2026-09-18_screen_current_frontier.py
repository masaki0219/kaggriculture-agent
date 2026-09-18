#!/usr/bin/env python3
"""
2026-09-18 — Current Frontier Screen

Place this file directly in the Kaggle repository root and run:

    python 2026-09-18_screen_current_frontier.py

Default design
--------------
A. Direct current-frontier round robin
   - E21 Tetsu Market-Smart V23
   - Ahmed V44
   - aurax V7
   - 16 fresh seeds
   - both seats

B. Common fixed panel
   Every candidate faces exactly the same opponent set:
   - E11 Prvsiyan Frontier
   - Shape Top10
   - Kaito58
   - Boatlee29
   - Adaptive Route V2
   - 8 fresh seeds
   - both seats

This avoids the old comparability bug where each candidate was averaged over a
different family set because self-match opponents were missing.

Outputs in Kaggle root
----------------------
    2026-09-18_CURRENT_FRONTIER_SCREEN.md
    2026-09-18_CURRENT_FRONTIER_SCREEN.json

No Kaggle submission is performed.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import argparse
import importlib
import json
import math
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
REPORT = ROOT / "2026-09-18_CURRENT_FRONTIER_SCREEN.md"
DATA = ROOT / "2026-09-18_CURRENT_FRONTIER_SCREEN.json"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"

PREFIX = "@@FRONTIER_RESULT@@"

CANDIDATES = ("e21", "ahmed_v44", "aurax7_v7")
FIXED_PANEL = ("e11", "shape_top10", "kaito58", "boatlee29", "adaptive_route_v2")

ELITE_NAMES = {
    "ahmed_v44": "ahmed_v44_current",
    "aurax7_v7": "aurax7_v7_current",
    "shape_top10": "shape_top10",
    "kaito58": "kaito58",
    "boatlee29": "boatlee29",
    "adaptive_route_v2": "adaptive_route_v2",
}

MODULE_NAMES = {
    "e21": "agent_e21_tetsu_market_v23",
    "e11": "agent_e11_prvsiyan_frontier",
}

CALLABLE_NAMES = (
    "agent",
    "kaggle_submission_agent",
    "submission_agent",
    "melon_maxxer",
    "policy",
    "kaggriculture_e776_agent",
)


def bundle_path():
    p = str(BUNDLE)
    if p not in sys.path:
        sys.path.insert(0, p)


def load_module_agent(module_name):
    bundle_path()
    mod = importlib.import_module(module_name)
    for name in CALLABLE_NAMES:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    raise AttributeError(f"{module_name} exposes none of {CALLABLE_NAMES}")


def load_elite_agent(elite_name):
    bundle_path()
    from elite_runtime import load_agent, call_agent

    base = load_agent(elite_name)

    def wrapped(obs, configuration=None):
        return call_agent(base, obs, configuration)

    return wrapped


def resolve(name):
    if name in MODULE_NAMES:
        return load_module_agent(MODULE_NAMES[name])
    if name in ELITE_NAMES:
        return load_elite_agent(ELITE_NAMES[name])
    raise KeyError(name)


def final_reward(env, seat):
    st = env.steps[-1][seat]
    val = st.get("reward")
    return float(val)


def child(args):
    from kaggle_environments import make

    left = resolve(args.left)
    right = resolve(args.right)

    # seat=0 => left in seat 0, seat=1 => left in seat 1
    agents = [left, right] if args.seat == 0 else [right, left]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    left_seat = args.seat
    right_seat = 1 - args.seat
    lr = final_reward(env, left_seat)
    rr = final_reward(env, right_seat)

    if lr > rr:
        outcome = "W"
    elif lr < rr:
        outcome = "L"
    else:
        outcome = "D"

    result = {
        "left": args.left,
        "right": args.right,
        "seed": args.seed,
        "left_seat": args.seat,
        "left_reward": lr,
        "right_reward": rr,
        "margin": lr - rr,
        "outcome": outcome,
    }
    print(PREFIX + json.dumps(result, ensure_ascii=False))


def run_game(left, right, seed, seat):
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--left", left,
        "--right", right,
        "--seed", str(seed),
        "--seat", str(seat),
    ]
    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    for line in p.stdout.splitlines():
        if line.startswith(PREFIX):
            return json.loads(line[len(PREFIX):])

    detail = (p.stderr or p.stdout or "no child result")[-5000:]
    return {
        "left": left,
        "right": right,
        "seed": seed,
        "left_seat": seat,
        "error": detail,
    }


def wdl(rows):
    c = Counter(r["outcome"] for r in rows if "outcome" in r)
    return c["W"], c["D"], c["L"]


def score(rows):
    w, d, l = wdl(rows)
    n = w + d + l
    return (w + 0.5 * d) / n if n else float("nan")


def mean_margin(rows):
    vals = [r["margin"] for r in rows if "margin" in r]
    return sum(vals) / len(vals) if vals else float("nan")


def pct(x):
    return "nan%" if isinstance(x, float) and math.isnan(x) else f"{100*x:.1f}%"


def fmt_margin(x):
    return "nan" if isinstance(x, float) and math.isnan(x) else f"{x:+.0f}"


def run_block(label, pairs, seeds):
    rows = []
    total = len(pairs) * len(seeds) * 2
    done = 0
    print(f"\n=== {label} ===")
    print("Games:", total)

    for left, right in pairs:
        pair_rows = []
        print(f"\n--- {left} vs {right} ---")
        for seed in seeds:
            for seat in (0, 1):
                done += 1
                print(
                    f"[{done:>3}/{total}] {left} vs {right} "
                    f"seed={seed} left-seat={seat}",
                    flush=True,
                )
                r = run_game(left, right, seed, seat)
                rows.append(r)
                pair_rows.append(r)

        valid = [r for r in pair_rows if "error" not in r]
        if len(valid) != len(pair_rows):
            print(f"ERRORS: {len(pair_rows)-len(valid)}")
        else:
            w, d, l = wdl(valid)
            print(
                f"{w}-{d}-{l} score={pct(score(valid))} "
                f"margin(diag)={fmt_margin(mean_margin(valid))}"
            )
    return rows


def parent(args):
    rr_seeds = list(range(args.rr_seed_start, args.rr_seed_start + args.rr_seeds))
    panel_seeds = list(range(args.panel_seed_start, args.panel_seed_start + args.panel_seeds))

    rr_pairs = [
        ("e21", "ahmed_v44"),
        ("e21", "aurax7_v7"),
        ("ahmed_v44", "aurax7_v7"),
    ]
    panel_pairs = [
        (candidate, opponent)
        for candidate in CANDIDATES
        for opponent in FIXED_PANEL
    ]

    rr_rows = run_block("DIRECT CURRENT-FRONTIER ROUND ROBIN", rr_pairs, rr_seeds)
    panel_rows = run_block("COMMON FIXED PANEL", panel_pairs, panel_seeds)

    all_rows = rr_rows + panel_rows
    errors = [r for r in all_rows if "error" in r]

    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    payload = {
        "generated": generated,
        "design": {
            "round_robin_seeds": rr_seeds,
            "panel_seeds": panel_seeds,
            "candidates": list(CANDIDATES),
            "fixed_panel": list(FIXED_PANEL),
        },
        "round_robin": rr_rows,
        "fixed_panel": panel_rows,
        "errors": errors,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        REPORT.write_text(
            "# Current Frontier Screen\n\n"
            f"- Generated: `{generated}`\n"
            f"- Status: **ABORTED**\n"
            f"- Errors: **{len(errors)}**\n\n"
            "No ranking was produced because at least one game failed.\n",
            encoding="utf-8",
        )
        raise SystemExit(
            f"\nABORTED: {len(errors)} game errors. "
            f"See {DATA.name} and {REPORT.name}"
        )

    report = [
        "# Current Frontier Screen",
        "",
        f"- Generated: `{generated}`",
        f"- Candidates: {', '.join(f'`{x}`' for x in CANDIDATES)}",
        f"- RR seeds: `{rr_seeds[0]}..{rr_seeds[-1]}`",
        f"- Fixed-panel seeds: `{panel_seeds[0]}..{panel_seeds[-1]}`",
        f"- Errors: **0**",
        "",
        "Primary purpose: identify the strongest current public baseline before E22.",
        "Reward margin is diagnostic only; W/D/L score is primary.",
        "",
        "## 1. Direct current-frontier round robin",
        "",
        "| Matchup | W-D-L from left perspective | Score | Margin (diag) |",
        "|---|---:|---:|---:|",
    ]

    for left, right in rr_pairs:
        rows = [
            r for r in rr_rows
            if r["left"] == left and r["right"] == right
        ]
        w, d, l = wdl(rows)
        report.append(
            f"| `{left}` vs `{right}` | {w}-{d}-{l} | "
            f"{pct(score(rows))} | {fmt_margin(mean_margin(rows))} |"
        )

    report += [
        "",
        "## 2. Direct-round-robin candidate summary",
        "",
        "Each candidate is evaluated only on the two direct frontier opponents.",
        "",
        "| Candidate | W-D-L | Score |",
        "|---|---:|---:|",
    ]

    rr_candidate = {}
    for c in CANDIDATES:
        transformed = []
        for r in rr_rows:
            if r["left"] == c:
                transformed.append(r)
            elif r["right"] == c:
                flipped = dict(r)
                flipped["outcome"] = {"W": "L", "L": "W", "D": "D"}[r["outcome"]]
                flipped["margin"] = -r["margin"]
                transformed.append(flipped)
        rr_candidate[c] = transformed
        w, d, l = wdl(transformed)
        report.append(f"| `{c}` | {w}-{d}-{l} | {pct(score(transformed))} |")

    report += [
        "",
        "## 3. Common fixed panel",
        "",
        "All candidates face the exact same opponents, seeds, and both seats.",
        "",
        "| Candidate | W-D-L | Score | Worst opponent score | Margin (diag) |",
        "|---|---:|---:|---:|---:|",
    ]

    panel_summary = {}
    for c in CANDIDATES:
        rows = [r for r in panel_rows if r["left"] == c]
        per_opp = {}
        for o in FIXED_PANEL:
            oo = [r for r in rows if r["right"] == o]
            per_opp[o] = score(oo)
        worst = min(per_opp.values()) if per_opp else float("nan")
        panel_summary[c] = {
            "score": score(rows),
            "worst": worst,
            "per_opponent": per_opp,
        }
        w, d, l = wdl(rows)
        report.append(
            f"| `{c}` | {w}-{d}-{l} | {pct(score(rows))} | "
            f"{pct(worst)} | {fmt_margin(mean_margin(rows))} |"
        )

    report += [
        "",
        "## 4. Per-opponent common-panel score",
        "",
        "| Candidate | " + " | ".join(FIXED_PANEL) + " |",
        "|---|" + "|".join(["---:" for _ in FIXED_PANEL]) + "|",
    ]
    for c in CANDIDATES:
        vals = [pct(panel_summary[c]["per_opponent"][o]) for o in FIXED_PANEL]
        report.append(f"| `{c}` | " + " | ".join(vals) + " |")

    # Decision gate: report evidence, but do not conflate local result with final BT.
    rr_order = sorted(
        CANDIDATES,
        key=lambda c: (
            score(rr_candidate[c]),
            panel_summary[c]["score"],
            panel_summary[c]["worst"],
        ),
        reverse=True,
    )

    report += [
        "",
        "## 5. Baseline decision gate",
        "",
        f"- Local direct-RR order for this screen: "
        + " > ".join(f"`{x}`" for x in rr_order),
        "- Use this only to choose the **development baseline**, not as a final-leaderboard prediction.",
        "- If one candidate clearly leads direct RR and is not worse on the common panel, freeze it as the new frontier baseline.",
        "- If the direct RR is mixed/non-transitive, keep multiple frontier baselines and design E22 against their shared failure modes.",
        "- Final objective remains population-level W/D/L / Bradley–Terry over the unknown active leaderboard population.",
        "",
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {generated} — Current frontier screen\n\n"
            f"- Candidates: {', '.join(CANDIDATES)}\n"
            f"- Direct RR seeds: `{rr_seeds[0]}..{rr_seeds[-1]}`\n"
            f"- Fixed panel seeds: `{panel_seeds[0]}..{panel_seeds[-1]}`\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- No Kaggle submission performed.\n\n"
        )

    print("\n=== CURRENT FRONTIER SCREEN COMPLETE ===")
    print("Report:", REPORT.name)
    print("Data:", DATA.name)
    print("Direct-RR local order:", " > ".join(rr_order))


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--rr-seeds", type=int, default=16)
    ap.add_argument("--rr-seed-start", type=int, default=20000)
    ap.add_argument("--panel-seeds", type=int, default=8)
    ap.add_argument("--panel-seed-start", type=int, default=21000)

    ap.add_argument("--child", action="store_true")
    ap.add_argument("--left")
    ap.add_argument("--right")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--seat", type=int, choices=(0, 1))

    args = ap.parse_args()

    if args.child:
        child(args)
    else:
        parent(args)


if __name__ == "__main__":
    main()
