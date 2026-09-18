#!/usr/bin/env python3
"""
Screen E27 trajectory-corrected M-family agent.

Run from Kaggle repo root:

    python 2026-09-18_screen_e27_m_family_trajectory.py

Smoke:
- E21 + aurax V7
- 3 fresh seeds
- both seats
- 12 games

Economic gate:
- no errors
- median reward >= 30,000
- at least 6/12 games >= 20,000

Trajectory gate against M-corpus medians:
- step 71: median structures 4..6, median crops >= 15
- step 215: median structures 8..16, median crops >= 25
- step 287: median structures 12..20, median crops >= 40

Only if both gates pass:
- fresh 8 seeds × both seats vs E21/E22/aurax/Ahmed/Kaito43/tetsu_shape

Outputs:
    2026-09-18_E27_M_FAMILY_SCREEN.md
    2026-09-18_E27_M_FAMILY_SCREEN.json
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

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
REPORT = ROOT / "2026-09-18_E27_M_FAMILY_SCREEN.md"
DATA = ROOT / "2026-09-18_E27_M_FAMILY_SCREEN.json"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"
PREFIX = "@@E27SCREEN@@"

CHECKPOINTS = (71, 143, 215, 287, 359, 431, 575, 719)

OPPONENTS = (
    "e21",
    "e22",
    "aurax7_v7",
    "ahmed_v44",
    "kaito43",
    "tetsu_shape",
)

MODULES = {
    "e27": "agent_e27_m_family_trajectory",
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

    return {
        "step": step,
        "hands": len(farm.get("hands") or []),
        "quadrants": len(farm.get("unlocked_quadrants") or []),
        "money": float(farm.get("money", 0) or 0),
        "crop_total": sum(crops.values()),
        "structure_total": sum(structures.values()),
        "animal_total": sum(animals.values()),
        "crops": dict(crops),
        "structures": dict(structures),
        "animals": dict(animals),
    }


def child(args):
    from kaggle_environments import make

    e27 = resolve("e27")
    opp = resolve(args.opponent)
    agents = [e27, opp] if args.e27_seat == 0 else [opp, e27]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    a = reward(env, args.e27_seat)
    b = reward(env, 1 - args.e27_seat)
    outcome = "W" if a > b else "L" if a < b else "D"

    trajectory = {
        str(s): diag_at(env, args.e27_seat, s)
        for s in CHECKPOINTS
    }

    print(PREFIX + json.dumps({
        "opponent": args.opponent,
        "seed": args.seed,
        "e27_seat": args.e27_seat,
        "e27_reward": a,
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
            "--e27-seat", str(seat),
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
        "e27_seat": seat,
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
        print(f"\n--- E27 vs {opponent} ---")

        for seed in seeds:
            for seat in (0,1):
                done += 1
                print(
                    f"[{done:>3}/{total}] E27 vs {opponent} seed={seed} seat={seat}",
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
            rewards = [r["e27_reward"] for r in valid]
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
            "structures": statistics.median(v["structure_total"] for v in vals),
            "crops": statistics.median(v["crop_total"] for v in vals),
            "animals": statistics.median(v["animal_total"] for v in vals),
            "hands": statistics.median(v["hands"] for v in vals),
            "quadrants": statistics.median(v["quadrants"] for v in vals),
            "money": statistics.median(v["money"] for v in vals),
        }
    return out


def parent(args):
    if not (BUNDLE / "agent_e27_m_family_trajectory.py").exists():
        raise SystemExit(
            "Missing E27 agent. Run 2026-09-18_install_e27_m_family_trajectory.py first."
        )

    smoke_seeds = list(range(args.smoke_seed_start, args.smoke_seed_start+3))
    smoke = run_block("SMOKE", ("e21","aurax7_v7"), smoke_seeds)

    errors = [r for r in smoke if "error" in r]
    valid = [r for r in smoke if "error" not in r]
    rewards = [r["e27_reward"] for r in valid]

    median_reward = statistics.median(rewards) if rewards else 0
    productive = sum(x >= 20000 for x in rewards)
    traj = trajectory_medians(smoke)

    def at(step, key, default=0):
        return traj.get(str(step), {}).get(key, default)

    economic_pass = (
        not errors
        and median_reward >= args.min_median_reward
        and productive >= args.min_productive_games
    )

    trajectory_pass = (
        4 <= at(71,"structures") <= 6
        and at(71,"crops") >= 15
        and 8 <= at(215,"structures") <= 16
        and at(215,"crops") >= 25
        and 12 <= at(287,"structures") <= 20
        and at(287,"crops") >= 40
    )

    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    if not (economic_pass and trajectory_pass):
        payload = {
            "generated": generated,
            "status": "smoke_failed",
            "economic_pass": economic_pass,
            "trajectory_pass": trajectory_pass,
            "median_reward": median_reward,
            "productive_games": productive,
            "trajectory_medians": traj,
            "smoke": smoke,
            "errors": errors,
        }
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        lines = [
            "# E27 Trajectory-Corrected M-Family Screen",
            "",
            f"- Generated: `{generated}`",
            "- Status: **SMOKE FAILED**",
            f"- Errors: **{len(errors)}**",
            f"- Median reward: **{median_reward:.0f}**",
            f"- Games >=20k: **{productive}/12**",
            f"- Economic gate: **{'PASS' if economic_pass else 'FAIL'}**",
            f"- Trajectory gate: **{'PASS' if trajectory_pass else 'FAIL'}**",
            "",
            "## Smoke trajectory medians",
            "",
            "| Step | Structures | Crops | Animals | Hands | Quadrants | Money |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]

        for step in CHECKPOINTS:
            d = traj.get(str(step), {})
            lines.append(
                f"| {step} | {d.get('structures','')} | {d.get('crops','')} | "
                f"{d.get('animals','')} | {d.get('hands','')} | "
                f"{d.get('quadrants','')} | {d.get('money','')} |"
            )

        lines += [
            "",
            "M-corpus reference medians:",
            "- step71: structures≈5, crops≈20",
            "- step215: structures≈12, crops≈38",
            "- step287: structures≈16, crops≈57",
            "",
            "The larger screen was intentionally not run.",
        ]
        REPORT.write_text("\n".join(lines), encoding="utf-8")

        raise SystemExit(
            f"Smoke gate failed: reward={median_reward:.0f}, productive={productive}/12, "
            f"economic={economic_pass}, trajectory={trajectory_pass}. See {REPORT.name}"
        )

    seeds = list(range(args.seed_start, args.seed_start+args.seeds))
    fresh = run_block("FRESH SCREEN", OPPONENTS, seeds)
    fresh_errors = [r for r in fresh if "error" in r]

    payload = {
        "generated": generated,
        "status": "complete" if not fresh_errors else "fresh_errors",
        "smoke_median_reward": median_reward,
        "smoke_productive_games": productive,
        "trajectory_medians": traj,
        "fresh_seeds": seeds,
        "opponents": list(OPPONENTS),
        "fresh": fresh,
        "errors": fresh_errors,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if fresh_errors:
        REPORT.write_text(
            "# E27 Trajectory-Corrected M-Family Screen\n\n"
            f"- Generated: `{generated}`\n"
            f"- Status: **ABORTED**\n"
            f"- Fresh errors: **{len(fresh_errors)}**\n",
            encoding="utf-8",
        )
        raise SystemExit(f"{len(fresh_errors)} fresh errors. See {DATA.name}")

    report = [
        "# E27 Trajectory-Corrected State-Based M-Family — Fresh Screen",
        "",
        f"- Generated: `{generated}`",
        f"- Fresh seeds: `{seeds[0]}..{seeds[-1]}`",
        f"- Smoke median reward: **{median_reward:.0f}**",
        f"- Smoke games >=20k: **{productive}/12**",
        "- Economic gate: **PASS**",
        "- Trajectory gate: **PASS**",
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
        med = statistics.median(r["e27_reward"] for r in rr)
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
        "E27 is evaluated only after its farm trajectory resembles the observed M family.",
        "If W/L is weak now, that is meaningful strategy evidence rather than a tape/planner integrity failure.",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {generated} — E27 M-family trajectory screen\n\n"
            f"- Smoke median reward: {median_reward:.0f}\n"
            f"- Smoke productive games: {productive}/12\n"
            "- Smoke trajectory gate: PASS\n"
            f"- Fresh aggregate W-D-L: {w}-{d}-{l}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- No Kaggle submission performed.\n\n"
        )

    print()
    print("=== E27 SCREEN COMPLETE ===")
    print("Aggregate:", f"{w}-{d}-{l}", pct(score(aggregate)))
    print("Report:", REPORT.name)
    print("Data:", DATA.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-seed-start", type=int, default=27990)
    ap.add_argument("--min-median-reward", type=float, default=30000)
    ap.add_argument("--min-productive-games", type=int, default=6)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed-start", type=int, default=28000)

    ap.add_argument("--child", action="store_true")
    ap.add_argument("--opponent")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--e27-seat", type=int, choices=(0,1))

    args = ap.parse_args()

    if args.child:
        child(args)
    else:
        parent(args)


if __name__ == "__main__":
    main()
