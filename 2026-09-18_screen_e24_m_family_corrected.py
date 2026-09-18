#!/usr/bin/env python3
"""
2026-09-18 — Screen E24 corrected M-family replay-router

Place in Kaggle repo root and run:

    python 2026-09-18_screen_e24_m_family_corrected.py

Stage 1: smoke vs E21 and aurax, 2 seeds × both seats.
The script ABORTS before the larger screen if:
- any game errors, or
- max E24 reward across smoke < 5,000.

Stage 2: if smoke passes, 8 fresh seeds × both seats vs:
- E21
- E22
- aurax V7
- Ahmed V44
- Kaito43
- tetsu_shape

Outputs:
    2026-09-18_E24_M_FAMILY_SCREEN.md
    2026-09-18_E24_M_FAMILY_SCREEN.json
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

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
REPORT = ROOT / "2026-09-18_E24_M_FAMILY_SCREEN.md"
DATA = ROOT / "2026-09-18_E24_M_FAMILY_SCREEN.json"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"
PREFIX = "@@E24SCREEN@@"

OPPONENTS = (
    "e21",
    "e22",
    "aurax7_v7",
    "ahmed_v44",
    "kaito43",
    "tetsu_shape",
)

MODULES = {
    "e24": "agent_e24_m_family_corrected",
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

    e24 = resolve("e24")
    opp = resolve(args.opponent)
    agents = [e24, opp] if args.e24_seat == 0 else [opp, e24]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    a = reward(env, args.e24_seat)
    b = reward(env, 1 - args.e24_seat)
    outcome = "W" if a > b else "L" if a < b else "D"

    print(PREFIX + json.dumps({
        "opponent": args.opponent,
        "seed": args.seed,
        "e24_seat": args.e24_seat,
        "e24_reward": a,
        "opponent_reward": b,
        "margin": a - b,
        "outcome": outcome,
    }, ensure_ascii=False))


def run_game(opponent, seed, seat):
    p = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            "--opponent", opponent,
            "--seed", str(seed),
            "--e24-seat", str(seat),
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
        "e24_seat": seat,
        "error": (p.stderr or p.stdout or "no child result")[-5000:],
    }


def wdl(rows):
    c = Counter(r["outcome"] for r in rows if "outcome" in r)
    return c["W"], c["D"], c["L"]


def score(rows):
    w, d, l = wdl(rows)
    n = w + d + l
    return (w + 0.5*d) / n if n else float("nan")


def mean_margin(rows):
    vals = [r["margin"] for r in rows if "margin" in r]
    return sum(vals) / len(vals) if vals else float("nan")


def pct(x):
    return "n/a" if isinstance(x, float) and math.isnan(x) else f"{100*x:.1f}%"


def fmt_margin(x):
    return "n/a" if isinstance(x, float) and math.isnan(x) else f"{x:+.0f}"


def run_block(label, opponents, seeds):
    rows = []
    total = len(opponents) * len(seeds) * 2
    done = 0
    print(f"\n=== {label} ===")
    print("Games:", total)

    for opponent in opponents:
        pair = []
        print(f"\n--- E24 vs {opponent} ---")
        for seed in seeds:
            for seat in (0, 1):
                done += 1
                print(
                    f"[{done:>3}/{total}] E24 vs {opponent} seed={seed} seat={seat}",
                    flush=True,
                )
                r = run_game(opponent, seed, seat)
                rows.append(r)
                pair.append(r)

        valid = [r for r in pair if "error" not in r]
        errors = [r for r in pair if "error" in r]
        if errors:
            print("  ERRORS:", len(errors))
        else:
            w, d, l = wdl(valid)
            print(
                f"  {w}-{d}-{l} score={pct(score(valid))} "
                f"margin(diag)={fmt_margin(mean_margin(valid))} "
                f"reward-range={min(r['e24_reward'] for r in valid):.0f}.."
                f"{max(r['e24_reward'] for r in valid):.0f}"
            )
    return rows


def parent(args):
    agent_path = BUNDLE / "agent_e24_m_family_corrected.py"
    if not agent_path.exists():
        raise SystemExit(
            "Missing E24 agent. Run 2026-09-18_install_e24_m_family_corrected.py first."
        )

    smoke_seeds = list(range(args.smoke_seed_start, args.smoke_seed_start + 2))
    smoke = run_block("SMOKE", ("e21", "aurax7_v7"), smoke_seeds)

    smoke_errors = [r for r in smoke if "error" in r]
    smoke_valid = [r for r in smoke if "error" not in r]
    smoke_max_reward = max((r["e24_reward"] for r in smoke_valid), default=0)

    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    if smoke_errors or smoke_max_reward < args.min_smoke_reward:
        payload = {
            "generated": generated,
            "status": "smoke_failed",
            "smoke_max_reward": smoke_max_reward,
            "min_smoke_reward": args.min_smoke_reward,
            "smoke": smoke,
        }
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        REPORT.write_text(
            "# E24 M-Family Screen\n\n"
            f"- Generated: `{generated}`\n"
            f"- Status: **SMOKE FAILED**\n"
            f"- Errors: **{len(smoke_errors)}**\n"
            f"- Max E24 smoke reward: **{smoke_max_reward:.0f}**\n"
            f"- Minimum required: **{args.min_smoke_reward:.0f}**\n\n"
            "The larger screen was intentionally not run.\n",
            encoding="utf-8",
        )
        raise SystemExit(
            f"Smoke gate failed: errors={len(smoke_errors)}, "
            f"max_reward={smoke_max_reward:.0f}. See {REPORT.name}"
        )

    seeds = list(range(args.seed_start, args.seed_start + args.seeds))
    fresh = run_block("FRESH SCREEN", OPPONENTS, seeds)
    errors = [r for r in fresh if "error" in r]

    payload = {
        "generated": generated,
        "status": "complete" if not errors else "fresh_errors",
        "smoke_max_reward": smoke_max_reward,
        "smoke": smoke,
        "fresh_seeds": seeds,
        "opponents": list(OPPONENTS),
        "fresh": fresh,
        "errors": errors,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        REPORT.write_text(
            "# E24 M-Family Screen\n\n"
            f"- Generated: `{generated}`\n"
            f"- Status: **ABORTED**\n"
            f"- Fresh errors: **{len(errors)}**\n",
            encoding="utf-8",
        )
        raise SystemExit(f"{len(errors)} fresh-screen errors. See {DATA.name}")

    report = [
        "# E24 Corrected M-Family Replay-Router — Fresh Screen",
        "",
        f"- Generated: `{generated}`",
        f"- Fresh seeds: `{seeds[0]}..{seeds[-1]}`",
        f"- Smoke max reward: **{smoke_max_reward:.0f}**",
        f"- Errors: **0**",
        "",
        "E24 fixes E23's replay state/action alignment and preserves donor cash-flow timing.",
        "Reward margin is diagnostic only.",
        "",
        "## Per-opponent",
        "",
        "| Opponent | W-D-L | Score | Reward mean | Margin (diag) |",
        "|---|---:|---:|---:|---:|",
    ]

    aggregate = []
    for opponent in OPPONENTS:
        rr = [r for r in fresh if r["opponent"] == opponent]
        aggregate.extend(rr)
        w, d, l = wdl(rr)
        mean_reward = sum(r["e24_reward"] for r in rr) / len(rr)
        report.append(
            f"| `{opponent}` | {w}-{d}-{l} | {pct(score(rr))} | "
            f"{mean_reward:.0f} | {fmt_margin(mean_margin(rr))} |"
        )

    w, d, l = wdl(aggregate)
    report += [
        "",
        "## Aggregate",
        "",
        f"- W-D-L: **{w}-{d}-{l}**",
        f"- Unweighted panel score: **{pct(score(aggregate))}**",
        "",
        "## Decision gate",
        "",
        "- If rewards are now economically normal but W/L is poor, the M-family hypothesis is being tested meaningfully and v1 can be rejected/retained on strategy grounds.",
        "- If rewards are still near zero, E24 remains an implementation failure; do not infer anything about M-family quality.",
        "- If E24 is competitive on several frontier opponents with a distinct W/L pattern, keep the M-family track and move to population-weighted evaluation.",
        "- Do not patch individual seeds.",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {generated} — E24 corrected M-family screen\n\n"
            f"- Smoke max reward: {smoke_max_reward:.0f}\n"
            f"- Fresh seeds: `{seeds[0]}..{seeds[-1]}`\n"
            f"- Aggregate W-D-L: {w}-{d}-{l}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- No Kaggle submission performed.\n\n"
        )

    print()
    print("=== E24 SCREEN COMPLETE ===")
    print("Aggregate:", f"{w}-{d}-{l}", pct(score(aggregate)))
    print("Report:", REPORT.name)
    print("Data:", DATA.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-seed-start", type=int, default=24990)
    ap.add_argument("--min-smoke-reward", type=float, default=5000)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed-start", type=int, default=25000)

    ap.add_argument("--child", action="store_true")
    ap.add_argument("--opponent")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--e24-seat", type=int, choices=(0, 1))

    args = ap.parse_args()

    if args.child:
        child(args)
    else:
        parent(args)


if __name__ == "__main__":
    main()
