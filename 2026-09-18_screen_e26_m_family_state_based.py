#!/usr/bin/env python3
"""
2026-09-18 — Screen E26 state-based M-family agent

Run from Kaggle repo root:

    python 2026-09-18_screen_e26_m_family_state_based.py

Smoke:
- E21 and aurax V7
- 3 fresh seeds
- both seats
- 12 games

Smoke gate:
- no errors
- median E26 reward >= 30,000
- at least 6/12 games with reward >= 20,000

Only after smoke passes:
- 8 fresh seeds × both seats vs
  E21 / E22 / aurax / Ahmed / Kaito43 / tetsu_shape

Outputs:
    2026-09-18_E26_M_FAMILY_SCREEN.md
    2026-09-18_E26_M_FAMILY_SCREEN.json
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
REPORT = ROOT / "2026-09-18_E26_M_FAMILY_SCREEN.md"
DATA = ROOT / "2026-09-18_E26_M_FAMILY_SCREEN.json"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"
PREFIX = "@@E26SCREEN@@"

OPPONENTS = (
    "e21",
    "e22",
    "aurax7_v7",
    "ahmed_v44",
    "kaito43",
    "tetsu_shape",
)

MODULES = {
    "e26": "agent_e26_m_family_state_based",
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


def final_reward(env, seat):
    return float(env.steps[-1][seat].get("reward"))


def final_diag(env, seat):
    st = env.steps[-1][seat]
    obs = st.get("observation") or {}
    farms = obs.get("farms") or [{}]
    farm = farms[seat] if seat < len(farms) else {}
    private = obs.get("private") or {}

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
        "hands": len(farm.get("hands") or []),
        "quadrants": len(farm.get("unlocked_quadrants") or []),
        "money": float(farm.get("money", 0) or 0),
        "crops": dict(crops),
        "animals": dict(animals),
        "structures": dict(structures),
        "shed": dict(private.get("shed") or {}),
        "seeds": dict(private.get("seeds") or {}),
    }


def child(args):
    from kaggle_environments import make

    e26 = resolve("e26")
    opp = resolve(args.opponent)
    agents = [e26, opp] if args.e26_seat == 0 else [opp, e26]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    a = final_reward(env, args.e26_seat)
    b = final_reward(env, 1 - args.e26_seat)
    outcome = "W" if a > b else "L" if a < b else "D"

    print(PREFIX + json.dumps({
        "opponent": args.opponent,
        "seed": args.seed,
        "e26_seat": args.e26_seat,
        "e26_reward": a,
        "opponent_reward": b,
        "margin": a - b,
        "outcome": outcome,
        "final": final_diag(env, args.e26_seat),
    }, ensure_ascii=False))


def run_game(opponent, seed, seat):
    p = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            "--opponent", opponent,
            "--seed", str(seed),
            "--e26-seat", str(seat),
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
        "e26_seat": seat,
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
        print(f"\n--- E26 vs {opponent} ---")

        for seed in seeds:
            for seat in (0, 1):
                done += 1
                print(
                    f"[{done:>3}/{total}] E26 vs {opponent} seed={seed} seat={seat}",
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
            rewards = [r["e26_reward"] for r in valid]
            print(
                f"  {w}-{d}-{l} score={pct(score(valid))} "
                f"reward median={statistics.median(rewards):.0f} "
                f"range={min(rewards):.0f}..{max(rewards):.0f} "
                f"margin(diag)={fmt_margin(mean_margin(valid))}"
            )

    return rows


def smoke_summary(rows):
    valid = [r for r in rows if "error" not in r]
    rewards = [r["e26_reward"] for r in valid]

    if not rewards:
        return {
            "median_reward": 0,
            "productive_games": 0,
            "max_reward": 0,
        }

    return {
        "median_reward": float(statistics.median(rewards)),
        "productive_games": sum(x >= 20000 for x in rewards),
        "max_reward": float(max(rewards)),
    }


def parent(args):
    if not (BUNDLE / "agent_e26_m_family_state_based.py").exists():
        raise SystemExit(
            "Missing E26 agent. Run 2026-09-18_install_e26_m_family_state_based.py first."
        )

    smoke_seeds = list(range(args.smoke_seed_start, args.smoke_seed_start + 3))
    smoke = run_block("SMOKE", ("e21", "aurax7_v7"), smoke_seeds)

    errors = [r for r in smoke if "error" in r]
    ss = smoke_summary(smoke)
    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    smoke_pass = (
        not errors
        and ss["median_reward"] >= args.min_median_reward
        and ss["productive_games"] >= args.min_productive_games
    )

    if not smoke_pass:
        payload = {
            "generated": generated,
            "status": "smoke_failed",
            "smoke_gate": {
                "min_median_reward": args.min_median_reward,
                "min_productive_games": args.min_productive_games,
            },
            "smoke_summary": ss,
            "smoke": smoke,
            "errors": errors,
        }
        DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        finals = [
            r.get("final")
            for r in smoke
            if "error" not in r and isinstance(r.get("final"), dict)
        ]

        report = [
            "# E26 State-Based M-Family Screen",
            "",
            f"- Generated: `{generated}`",
            "- Status: **SMOKE FAILED**",
            f"- Errors: **{len(errors)}**",
            f"- Median E26 reward: **{ss['median_reward']:.0f}**",
            f"- Games >=20k: **{ss['productive_games']}/12**",
            f"- Max reward: **{ss['max_reward']:.0f}**",
            "",
            "The larger screen was intentionally not run.",
            "",
            "Unlike E23-E25, E26 contains no replay action sequence. If this gate fails, inspect the",
            "planner/executor economics directly (herd, structures, acreage, hands), not tape fidelity.",
            "",
            "## Final-state smoke diagnostics",
            "",
        ]
        for i, d in enumerate(finals, 1):
            report.append(
                f"- game {i}: money={d.get('money')} quadrants={d.get('quadrants')} "
                f"animals={d.get('animals')} crops={d.get('crops')} structures={d.get('structures')}"
            )

        REPORT.write_text("\n".join(report), encoding="utf-8")

        raise SystemExit(
            f"Smoke gate failed: median={ss['median_reward']:.0f}, "
            f"productive={ss['productive_games']}/12, errors={len(errors)}. "
            f"See {REPORT.name}"
        )

    seeds = list(range(args.seed_start, args.seed_start + args.seeds))
    fresh = run_block("FRESH SCREEN", OPPONENTS, seeds)
    fresh_errors = [r for r in fresh if "error" in r]

    payload = {
        "generated": generated,
        "status": "complete" if not fresh_errors else "fresh_errors",
        "smoke_summary": ss,
        "smoke": smoke,
        "fresh_seeds": seeds,
        "opponents": list(OPPONENTS),
        "fresh": fresh,
        "errors": fresh_errors,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if fresh_errors:
        REPORT.write_text(
            "# E26 State-Based M-Family Screen\n\n"
            f"- Generated: `{generated}`\n"
            f"- Status: **ABORTED**\n"
            f"- Fresh errors: **{len(fresh_errors)}**\n",
            encoding="utf-8",
        )
        raise SystemExit(f"{len(fresh_errors)} fresh errors. See {DATA.name}")

    report = [
        "# E26 State-Based M-Family — Fresh Screen",
        "",
        f"- Generated: `{generated}`",
        f"- Fresh seeds: `{seeds[0]}..{seeds[-1]}`",
        f"- Smoke median reward: **{ss['median_reward']:.0f}**",
        f"- Smoke games >=20k: **{ss['productive_games']}/12**",
        f"- Errors: **0**",
        "",
        "E26 uses no replay/tape actions. It is the first direct policy-level M-family implementation.",
        "Reward margin is diagnostic only.",
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
        w, d, l = wdl(rr)
        med = statistics.median(r["e26_reward"] for r in rr)
        report.append(
            f"| `{opponent}` | {w}-{d}-{l} | {pct(score(rr))} | "
            f"{med:.0f} | {fmt_margin(mean_margin(rr))} |"
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
        "- If E26 has economically normal rewards but weak W/L, improve complete policy modules using population evidence.",
        "- If E26 has a distinct competitive W/L profile, move to live-population-weighted evaluation.",
        "- Do not reintroduce replay action routing.",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")

    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {generated} — E26 state-based M-family screen\n\n"
            f"- Smoke median reward: {ss['median_reward']:.0f}\n"
            f"- Smoke productive games: {ss['productive_games']}/12\n"
            f"- Fresh aggregate W-D-L: {w}-{d}-{l}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- No replay action routing used.\n"
            "- No Kaggle submission performed.\n\n"
        )

    print()
    print("=== E26 SCREEN COMPLETE ===")
    print("Aggregate:", f"{w}-{d}-{l}", pct(score(aggregate)))
    print("Report:", REPORT.name)
    print("Data:", DATA.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-seed-start", type=int, default=26990)
    ap.add_argument("--min-median-reward", type=float, default=30000)
    ap.add_argument("--min-productive-games", type=int, default=6)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed-start", type=int, default=27000)

    ap.add_argument("--child", action="store_true")
    ap.add_argument("--opponent")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--e26-seat", type=int, choices=(0, 1))

    args = ap.parse_args()

    if args.child:
        child(args)
    else:
        parent(args)


if __name__ == "__main__":
    main()
