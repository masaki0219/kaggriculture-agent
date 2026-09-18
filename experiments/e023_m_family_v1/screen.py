#!/usr/bin/env python3
"""
2026-09-18 — Screen E23 M-family replay-router v1

Place in Kaggle repo root and run:

    python experiments/e023_m_family_v1/screen.py

Design:
1. Smoke: 2 seeds × both seats vs E21 and aurax.
2. If no errors, fresh screen: 8 seeds × both seats against:
   - E21
   - E22
   - aurax V7
   - Ahmed V44
   - Kaito43
   - tetsu_shape

Outputs:
    experiments/e023_m_family_v1/results.md
    experiments/e023_m_family_v1/results.json

No Kaggle submission is performed.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import argparse
import importlib
import json
import math
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
REPORT = HERE / "results.md"
DATA = HERE / "results.json"
HISTORY = ROOT / "docs" / "experiment_run_history.md"

PREFIX = "@@E23SCREEN@@"

OPPONENTS = (
    "e21",
    "e22",
    "aurax7_v7",
    "ahmed_v44",
    "kaito43",
    "tetsu_shape",
)

MODULES = {
    "e23": "agent_e23_m_family_v1",
    "e21": "agent_e21_tetsu_market_v23",
    "e22": "agent_e22_market_policy_swap",
}

ELITE = {
    "aurax7_v7": "aurax7_v7_current",
    "ahmed_v44": "ahmed_v44_current",
    "kaito43": "kaito43_current",
    "tetsu_shape": "tetsu_shape",
}

CALLABLES = (
    "agent",
    "kaggle_submission_agent",
    "submission_agent",
    "melon_maxxer",
    "policy",
    "kaggriculture_e776_agent",
)


def _bundle_path():
    p = str(BUNDLE)
    if p not in sys.path:
        sys.path.insert(0, p)


def _load_module(name):
    _bundle_path()
    mod = importlib.import_module(name)
    for key in CALLABLES:
        fn = getattr(mod, key, None)
        if callable(fn):
            return fn
    raise AttributeError(f"No callable agent in {name}")


def _load_elite(name):
    _bundle_path()
    from elite_runtime import load_agent, call_agent

    base = load_agent(name)

    def wrapped(obs, configuration=None):
        return call_agent(base, obs, configuration)

    return wrapped


def resolve(name):
    if name in MODULES:
        return _load_module(MODULES[name])
    if name in ELITE:
        return _load_elite(ELITE[name])
    raise KeyError(name)


def reward(env, seat):
    return float(env.steps[-1][seat].get("reward"))


def child(args):
    from kaggle_environments import make

    e23 = resolve("e23")
    opp = resolve(args.opponent)

    agents = [e23, opp] if args.e23_seat == 0 else [opp, e23]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    e23_seat = args.e23_seat
    opp_seat = 1 - e23_seat
    a = reward(env, e23_seat)
    b = reward(env, opp_seat)

    outcome = "W" if a > b else "L" if a < b else "D"

    print(
        PREFIX + json.dumps(
            {
                "opponent": args.opponent,
                "seed": args.seed,
                "e23_seat": e23_seat,
                "e23_reward": a,
                "opponent_reward": b,
                "margin": a - b,
                "outcome": outcome,
            },
            ensure_ascii=False,
        )
    )


def run_game(opponent, seed, seat):
    p = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            "--opponent", opponent,
            "--seed", str(seed),
            "--e23-seat", str(seat),
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    for line in p.stdout.splitlines():
        if line.startswith(PREFIX):
            return json.loads(line[len(PREFIX):])

    return {
        "opponent": opponent,
        "seed": seed,
        "e23_seat": seat,
        "error": (p.stderr or p.stdout or "no child result")[-5000:],
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
    if isinstance(x, float) and math.isnan(x):
        return "n/a"
    return f"{100*x:.1f}%"


def fmt_margin(x):
    if isinstance(x, float) and math.isnan(x):
        return "n/a"
    return f"{x:+.0f}"


def run_block(label, opponents, seeds):
    rows = []
    total = len(opponents) * len(seeds) * 2
    done = 0

    print(f"\n=== {label} ===")
    print("Games:", total)

    for opponent in opponents:
        pair = []
        print(f"\n--- E23 vs {opponent} ---")
        for seed in seeds:
            for seat in (0, 1):
                done += 1
                print(
                    f"[{done:>3}/{total}] E23 vs {opponent} "
                    f"seed={seed} seat={seat}",
                    flush=True,
                )
                r = run_game(opponent, seed, seat)
                rows.append(r)
                pair.append(r)

        errors = [r for r in pair if "error" in r]
        valid = [r for r in pair if "error" not in r]
        if errors:
            print("  ERRORS:", len(errors))
        else:
            w, d, l = wdl(valid)
            print(
                f"  {w}-{d}-{l} score={pct(score(valid))} "
                f"margin(diag)={fmt_margin(mean_margin(valid))}"
            )

    return rows


def parent(args):
    if not (BUNDLE / "agent_e23_m_family_v1.py").exists():
        raise SystemExit(
            "Missing canonical E23 agent: artifacts/bundles/current/agent_e23_m_family_v1.py"
        )

    smoke_seeds = list(range(args.smoke_seed_start, args.smoke_seed_start + 2))
    smoke = run_block(
        "SMOKE",
        ("e21", "aurax7_v7"),
        smoke_seeds,
    )

    smoke_errors = [r for r in smoke if "error" in r]
    if smoke_errors:
        payload = {
            "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "smoke_failed",
            "smoke": smoke,
        }
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        REPORT.write_text(
            "# E23 M-Family Screen\n\n"
            f"- Status: **SMOKE FAILED**\n"
            f"- Errors: **{len(smoke_errors)}**\n",
            encoding="utf-8",
        )
        raise SystemExit(f"Smoke failed with {len(smoke_errors)} errors. See {DATA.name}")

    seeds = list(range(args.seed_start, args.seed_start + args.seeds))
    fresh = run_block("FRESH SCREEN", OPPONENTS, seeds)

    errors = [r for r in fresh if "error" in r]
    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    payload = {
        "generated": generated,
        "smoke": smoke,
        "fresh_seeds": seeds,
        "opponents": list(OPPONENTS),
        "fresh": fresh,
        "errors": errors,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        REPORT.write_text(
            "# E23 M-Family Screen\n\n"
            f"- Generated: `{generated}`\n"
            f"- Status: **ABORTED**\n"
            f"- Fresh-screen errors: **{len(errors)}**\n",
            encoding="utf-8",
        )
        raise SystemExit(f"{len(errors)} fresh-screen errors. See {DATA.name}")

    report = [
        "# E23 M-Family Replay-Router v1 — Fresh Screen",
        "",
        f"- Generated: `{generated}`",
        f"- Fresh seeds: `{seeds[0]}..{seeds[-1]}`",
        f"- Errors: **0**",
        "",
        "E23 is an independent M-family candidate. Reward margin is diagnostic only.",
        "",
        "## Per-opponent",
        "",
        "| Opponent | W-D-L | Score | Margin (diag) |",
        "|---|---:|---:|---:|",
    ]

    aggregate = []
    for opponent in OPPONENTS:
        rr = [r for r in fresh if r["opponent"] == opponent]
        aggregate.extend(rr)
        w, d, l = wdl(rr)
        report.append(
            f"| `{opponent}` | {w}-{d}-{l} | "
            f"{pct(score(rr))} | {fmt_margin(mean_margin(rr))} |"
        )

    w, d, l = wdl(aggregate)
    report += [
        "",
        "## Aggregate",
        "",
        f"- W-D-L: **{w}-{d}-{l}**",
        f"- Unweighted common-panel score: **{pct(score(aggregate))}**",
        "",
        "## Decision gate",
        "",
        "- If E23 is catastrophically weak across the panel, reject v1 as an implementation failure; do not patch individual seeds.",
        "- If E23 is competitive against several frontier agents and its W/L pattern differs from E21/E22, keep it as a genuine M-family track.",
        "- If E23 beats the old/public K-line opponents but loses heavily only to E21/E22, that can still be useful population evidence; direct H2H is not the final objective.",
        "- Any promising result must next be evaluated with a population-weighted panel reflecting the live 2026-09-18 leaderboard family mix.",
        "",
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {generated} — E23 M-family v1 fresh screen\n\n"
            f"- Seeds: `{seeds[0]}..{seeds[-1]}`\n"
            f"- Opponents: {', '.join(OPPONENTS)}\n"
            f"- Aggregate W-D-L: {w}-{d}-{l}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- No Kaggle submission performed.\n\n"
        )

    print()
    print("=== E23 SCREEN COMPLETE ===")
    print("Aggregate:", f"{w}-{d}-{l}", pct(score(aggregate)))
    print("Report:", REPORT.name)
    print("Data:", DATA.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-seed-start", type=int, default=23990)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed-start", type=int, default=24000)

    ap.add_argument("--child", action="store_true")
    ap.add_argument("--opponent")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--e23-seat", type=int, choices=(0, 1))

    args = ap.parse_args()

    if args.child:
        child(args)
    else:
        parent(args)


if __name__ == "__main__":
    main()
