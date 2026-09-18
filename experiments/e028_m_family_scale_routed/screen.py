#!/usr/bin/env python3
"""
Screen E28 scale-routed M-family agent.

Run from Kaggle repo root:

    python experiments/e028_m_family_scale_routed/screen.py

Smoke:
- E21 + aurax V7
- 3 fresh seeds
- both seats
- 12 games

Gates:
1) no errors
2) economic:
   - median reward >= 50,000
   - >=9/12 games reward >= 30,000
3) M-family scale trajectory:
   - step143: median occupied >=22, hands>=6
   - step167: median occupied >=35, hands>=8, quadrants>=2
   - step215: median occupied >=42, hands>=8
   - step239: median quadrants>=3
   - step287: median occupied >=60, hands>=10

Only if all gates pass:
- 8 fresh seeds × both seats vs
  E21 / E22 / aurax / Ahmed / Kaito43 / tetsu_shape

Outputs:
    experiments/e028_m_family_scale_routed/results.md
    experiments/e028_m_family_scale_routed/results.json
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import argparse
import importlib
import json
import math
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
REPORT = HERE / "results.md"
DATA = HERE / "results.json"
HISTORY = ROOT / "docs" / "experiment_run_history.md"
PREFIX = "@@E28SCREEN@@"

CHECKPOINTS = (71, 143, 167, 215, 239, 287, 359, 431, 575, 719)

OPPONENTS = (
    "e21",
    "e22",
    "aurax7_v7",
    "ahmed_v44",
    "kaito43",
    "tetsu_shape",
)

MODULES = {
    "e28": "agent_e28_m_family_scale_routed",
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


def diag_at(env, seat, step):
    if step >= len(env.steps):
        step = len(env.steps) - 1

    st = env.steps[step][seat]
    obs = st.get("observation") or {}
    farms = obs.get("farms") or [{}]
    farm = farms[seat] if seat < len(farms) else {}

    crops = Counter()
    animals = Counter()
    structures = Counter()

    for row in farm.get("tiles") or []:
        if not isinstance(row, list):
            continue
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT" and tile.get("crop"):
                crops[str(tile["crop"])] += 1
            if tile.get("animal"):
                animals[str(tile["animal"])] += 1
            if tile.get("kind") in ("PASTURE", "COOP"):
                structures[str(tile["kind"])] += 1

    crop_total = sum(crops.values())
    structure_total = sum(structures.values())

    return {
        "step": step,
        "hands": len(farm.get("hands") or []),
        "quadrants": len(farm.get("unlocked_quadrants") or []),
        "money": float(farm.get("money", 0) or 0),
        "crop_total": crop_total,
        "structure_total": structure_total,
        "occupied_total": crop_total + structure_total,
        "animal_total": sum(animals.values()),
        "crops": dict(crops),
        "structures": dict(structures),
        "animals": dict(animals),
    }


def child(args):
    from kaggle_environments import make

    e28 = resolve("e28")
    opp = resolve(args.opponent)
    agents = [e28, opp] if args.e28_seat == 0 else [opp, e28]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    a = reward(env, args.e28_seat)
    b = reward(env, 1 - args.e28_seat)
    outcome = "W" if a > b else "L" if a < b else "D"

    trajectory = {
        str(s): diag_at(env, args.e28_seat, s)
        for s in CHECKPOINTS
    }

    print(PREFIX + json.dumps({
        "opponent": args.opponent,
        "seed": args.seed,
        "e28_seat": args.e28_seat,
        "e28_reward": a,
        "opponent_reward": b,
        "margin": a-b,
        "outcome": outcome,
        "trajectory": trajectory,
    }, ensure_ascii=False))


def run_game(opponent, seed, seat):
    p = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            "--opponent", opponent,
            "--seed", str(seed),
            "--e28-seat", str(seat),
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
        "e28_seat": seat,
        "error": (p.stderr or p.stdout or "no child result")[-5000:],
    }


def wdl(rows):
    c = Counter(r["outcome"] for r in rows if "outcome" in r)
    return c["W"], c["D"], c["L"]


def score(rows):
    w, d, l = wdl(rows)
    n = w+d+l
    return (w+0.5*d)/n if n else float("nan")


def mean_margin(rows):
    vals = [r["margin"] for r in rows if "margin" in r]
    return sum(vals)/len(vals) if vals else float("nan")


def pct(x):
    return "n/a" if isinstance(x,float) and math.isnan(x) else f"{100*x:.1f}%"


def fmt_margin(x):
    return "n/a" if isinstance(x,float) and math.isnan(x) else f"{x:+.0f}"


def run_block(label, opponents, seeds):
    rows = []
    total = len(opponents)*len(seeds)*2
    done = 0

    print(f"\n=== {label} ===")
    print("Games:", total)

    for opponent in opponents:
        pair = []
        print(f"\n--- E28 vs {opponent} ---")

        for seed in seeds:
            for seat in (0,1):
                done += 1
                print(
                    f"[{done:>3}/{total}] E28 vs {opponent} seed={seed} seat={seat}",
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
            w,d,l = wdl(valid)
            rewards = [r["e28_reward"] for r in valid]
            print(
                f"  {w}-{d}-{l} score={pct(score(valid))} "
                f"reward median={statistics.median(rewards):.0f} "
                f"range={min(rewards):.0f}..{max(rewards):.0f} "
                f"margin(diag)={fmt_margin(mean_margin(valid))}"
            )
    return rows


def trajectory_medians(rows):
    out = {}
    valid = [r for r in rows if "error" not in r]

    for step in CHECKPOINTS:
        vals = [
            r["trajectory"][str(step)]
            for r in valid
            if str(step) in r.get("trajectory", {})
        ]
        if not vals:
            continue

        out[str(step)] = {
            "occupied": statistics.median(v["occupied_total"] for v in vals),
            "structures": statistics.median(v["structure_total"] for v in vals),
            "crops": statistics.median(v["crop_total"] for v in vals),
            "animals": statistics.median(v["animal_total"] for v in vals),
            "hands": statistics.median(v["hands"] for v in vals),
            "quadrants": statistics.median(v["quadrants"] for v in vals),
            "money": statistics.median(v["money"] for v in vals),
        }
    return out


def parent(args):
    if not (BUNDLE / "agent_e28_m_family_scale_routed.py").exists():
        raise SystemExit(
            "Missing E28 agent. Run experiments/e028_m_family_scale_routed/builder.py first."
        )

    smoke_seeds = list(range(args.smoke_seed_start, args.smoke_seed_start+3))
    smoke = run_block("SMOKE", ("e21","aurax7_v7"), smoke_seeds)

    errors = [r for r in smoke if "error" in r]
    valid = [r for r in smoke if "error" not in r]
    rewards = [r["e28_reward"] for r in valid]

    median_reward = statistics.median(rewards) if rewards else 0
    productive = sum(x >= 30000 for x in rewards)
    traj = trajectory_medians(smoke)

    def at(step, key, default=0):
        return traj.get(str(step), {}).get(key, default)

    economic_pass = (
        not errors
        and median_reward >= args.min_median_reward
        and productive >= args.min_productive_games
    )

    trajectory_pass = (
        at(143,"occupied") >= 22
        and at(143,"hands") >= 6
        and at(167,"occupied") >= 35
        and at(167,"hands") >= 8
        and at(167,"quadrants") >= 2
        and at(215,"occupied") >= 42
        and at(215,"hands") >= 8
        and at(239,"quadrants") >= 3
        and at(287,"occupied") >= 60
        and at(287,"hands") >= 10
    )

    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    if not (economic_pass and trajectory_pass):
        payload = {
            "generated": generated,
            "status": "smoke_failed",
            "economic_pass": economic_pass,
            "trajectory_pass": trajectory_pass,
            "median_reward": median_reward,
            "productive_games_30k": productive,
            "trajectory_medians": traj,
            "smoke": smoke,
            "errors": errors,
        }
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        lines = [
            "# E28 Scale-Routed M-Family Screen",
            "",
            f"- Generated: `{generated}`",
            "- Status: **SMOKE FAILED**",
            f"- Errors: **{len(errors)}**",
            f"- Median reward: **{median_reward:.0f}**",
            f"- Games >=30k: **{productive}/12**",
            f"- Economic gate: **{'PASS' if economic_pass else 'FAIL'}**",
            f"- Scale trajectory gate: **{'PASS' if trajectory_pass else 'FAIL'}**",
            "",
            "## Smoke trajectory medians",
            "",
            "| Step | Occupied | Structures | Crops | Animals | Hands | Quadrants | Money |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]

        for step in CHECKPOINTS:
            d = traj.get(str(step), {})
            lines.append(
                f"| {step} | {d.get('occupied','')} | {d.get('structures','')} | "
                f"{d.get('crops','')} | {d.get('animals','')} | {d.get('hands','')} | "
                f"{d.get('quadrants','')} | {d.get('money','')} |"
            )

        lines += [
            "",
            "M-family scale references from the 84-run corpus:",
            "- day5 / step143: crops≈20, herd≈5",
            "- day6 / step167: crops≈33, herd≈11, hands≈8",
            "- day8 / step215: crops≈38, herd≈12, hands≈9",
            "- day11 / step287: crops≈57, herd≈16, hands≈11",
            "",
            "The larger W/L screen was intentionally not run.",
        ]

        REPORT.write_text("\n".join(lines), encoding="utf-8")
        raise SystemExit(
            f"Smoke gate failed: reward={median_reward:.0f}, productive30k={productive}/12, "
            f"economic={economic_pass}, trajectory={trajectory_pass}. See {REPORT.name}"
        )

    seeds = list(range(args.seed_start, args.seed_start+args.seeds))
    fresh = run_block("FRESH SCREEN", OPPONENTS, seeds)
    fresh_errors = [r for r in fresh if "error" in r]

    payload = {
        "generated": generated,
        "status": "complete" if not fresh_errors else "fresh_errors",
        "smoke_median_reward": median_reward,
        "smoke_productive_games_30k": productive,
        "trajectory_medians": traj,
        "fresh_seeds": seeds,
        "opponents": list(OPPONENTS),
        "fresh": fresh,
        "errors": fresh_errors,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if fresh_errors:
        REPORT.write_text(
            "# E28 Scale-Routed M-Family Screen\n\n"
            f"- Generated: `{generated}`\n"
            f"- Status: **ABORTED**\n"
            f"- Fresh errors: **{len(fresh_errors)}**\n",
            encoding="utf-8",
        )
        raise SystemExit(f"{len(fresh_errors)} fresh errors. See {DATA.name}")

    report = [
        "# E28 Scale-Routed State-Based M-Family — Fresh Screen",
        "",
        f"- Generated: `{generated}`",
        f"- Fresh seeds: `{seeds[0]}..{seeds[-1]}`",
        f"- Smoke median reward: **{median_reward:.0f}**",
        f"- Smoke games >=30k: **{productive}/12**",
        "- Economic gate: **PASS**",
        "- Scale trajectory gate: **PASS**",
        "- Errors: **0**",
        "",
        "## Per-opponent",
        "",
        "| Opponent | W-D-L | Score | Reward median | Margin (diag) |",
        "|---|---:|---:|---:|---:|",
    ]

    aggregate = []
    for opponent in OPPONENTS:
        rr = [r for r in fresh if r["opponent"] == opponent]
        aggregate.extend(rr)
        w,d,l = wdl(rr)
        med = statistics.median(r["e28_reward"] for r in rr)
        report.append(
            f"| `{opponent}` | {w}-{d}-{l} | {pct(score(rr))} | "
            f"{med:.0f} | {fmt_margin(mean_margin(rr))} |"
        )

    w,d,l = wdl(aggregate)
    report += [
        "",
        "## Aggregate",
        "",
        f"- W-D-L: **{w}-{d}-{l}**",
        f"- Unweighted panel score: **{pct(score(aggregate))}**",
        "",
        "## Interpretation",
        "",
        "E28 is only judged on W/L after it reproduces the current M-family scale trajectory.",
        "If it remains weak after passing both gates, the remaining gap is strategy/executor quality rather than family-scale reconstruction.",
        "",
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")

    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {generated} — E28 scale-routed M-family screen\n\n"
            f"- Smoke median reward: {median_reward:.0f}\n"
            f"- Smoke >=30k: {productive}/12\n"
            "- Smoke scale trajectory gate: PASS\n"
            f"- Fresh aggregate W-D-L: {w}-{d}-{l}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- No replay action routing used.\n"
            "- No Kaggle submission performed.\n\n"
        )

    print()
    print("=== E28 SCREEN COMPLETE ===")
    print("Aggregate:", f"{w}-{d}-{l}", pct(score(aggregate)))
    print("Report:", REPORT.name)
    print("Data:", DATA.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-seed-start", type=int, default=28990)
    ap.add_argument("--min-median-reward", type=float, default=50000)
    ap.add_argument("--min-productive-games", type=int, default=9)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed-start", type=int, default=29000)

    ap.add_argument("--child", action="store_true")
    ap.add_argument("--opponent")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--e28-seat", type=int, choices=(0,1))

    args = ap.parse_args()

    if args.child:
        child(args)
    else:
        parent(args)


if __name__ == "__main__":
    main()
