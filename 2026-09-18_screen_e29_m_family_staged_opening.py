#!/usr/bin/env python3
"""
Screen E29 staged-opening M-family agent.

Run from Kaggle repo root:

    python 2026-09-18_screen_e29_m_family_staged_opening.py

Stage A: opening fidelity
- E21 + aurax
- 2 fresh seeds
- both seats
- 8 games

Opening reference from M-family logs:
- step23: crops≈15.5, structures=5, animals=5, hands=4
- step47: crops≈19.5, structures=5, animals=5, hands=4
- step71: crops≈20, structures=5, animals=5, hands=6
- step143: crops≈20, structures=5, animals=5, hands=6

Only if Stage A passes:
Stage B: midgame fidelity
- same opponents
- 3 fresh seeds × both seats
- references:
  step167 crops≈33 / structures≈11 / animals≈11 / hands≈8 / q=2
  step215 crops≈38 / structures≈12 / animals≈12 / hands≈9 / q=2
  step239 crops≈53 / structures≈14 / animals≈14 / hands≈10 / q=3
  step287 crops≈58.5 / structures≈15 / animals≈15 / hands≈11 / q=3

Only if both fidelity stages pass:
Stage C: W/L screen on fresh seeds vs
E21 / E22 / aurax / Ahmed / Kaito43 / tetsu_shape.
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
REPORT = ROOT / "2026-09-18_E29_M_FAMILY_SCREEN.md"
DATA = ROOT / "2026-09-18_E29_M_FAMILY_SCREEN.json"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"
PREFIX = "@@E29SCREEN@@"

CHECKPOINTS = (23,47,71,143,167,215,239,287,719)

OPPONENTS = (
    "e21",
    "e22",
    "aurax7_v7",
    "ahmed_v44",
    "kaito43",
    "tetsu_shape",
)

MODULES = {
    "e29": "agent_e29_m_family_staged_opening",
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


def diag_at(env, seat, step):
    st = env.steps[min(step, len(env.steps)-1)][seat]
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
            if tile.get("kind") in ("PASTURE","COOP"):
                structures[str(tile["kind"])] += 1

    return {
        "step": step,
        "money": float(farm.get("money",0) or 0),
        "hands": len(farm.get("hands") or []),
        "quadrants": len(farm.get("unlocked_quadrants") or []),
        "crop_total": sum(crops.values()),
        "structure_total": sum(structures.values()),
        "animal_total": sum(animals.values()),
        "crops": dict(crops),
        "structures": dict(structures),
        "animals": dict(animals),
    }


def child(args):
    from kaggle_environments import make

    e29 = resolve("e29")
    opp = resolve(args.opponent)
    agents = [e29, opp] if args.e29_seat == 0 else [opp, e29]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    a = final_reward(env, args.e29_seat)
    b = final_reward(env, 1-args.e29_seat)

    print(PREFIX + json.dumps({
        "opponent": args.opponent,
        "seed": args.seed,
        "e29_seat": args.e29_seat,
        "e29_reward": a,
        "opponent_reward": b,
        "margin": a-b,
        "outcome": "W" if a>b else "L" if a<b else "D",
        "trajectory": {
            str(s): diag_at(env, args.e29_seat, s)
            for s in CHECKPOINTS
        },
    }, ensure_ascii=False))


def run_game(opponent, seed, seat):
    p = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            "--opponent", opponent,
            "--seed", str(seed),
            "--e29-seat", str(seat),
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
        "e29_seat": seat,
        "error": (p.stderr or p.stdout or "no result")[-5000:],
    }


def run_block(label, opponents, seeds):
    rows=[]
    total=len(opponents)*len(seeds)*2
    done=0

    print(f"\n=== {label} ===")

    for opponent in opponents:
        print(f"\n--- E29 vs {opponent} ---")
        for seed in seeds:
            for seat in (0,1):
                done += 1
                print(
                    f"[{done:>3}/{total}] E29 vs {opponent} seed={seed} seat={seat}",
                    flush=True,
                )
                rows.append(run_game(opponent, seed, seat))

    return rows


def medians(rows):
    valid=[r for r in rows if "error" not in r]
    out={}
    for s in CHECKPOINTS:
        vals=[r["trajectory"][str(s)] for r in valid]
        if not vals:
            continue
        out[str(s)]={
            "money": statistics.median(v["money"] for v in vals),
            "hands": statistics.median(v["hands"] for v in vals),
            "quadrants": statistics.median(v["quadrants"] for v in vals),
            "crops": statistics.median(v["crop_total"] for v in vals),
            "structures": statistics.median(v["structure_total"] for v in vals),
            "animals": statistics.median(v["animal_total"] for v in vals),
        }
    return out


def wdl(rows):
    c=Counter(r["outcome"] for r in rows if "outcome" in r)
    return c["W"],c["D"],c["L"]


def score(rows):
    w,d,l=wdl(rows)
    n=w+d+l
    return (w+0.5*d)/n if n else float("nan")


def parent(args):
    if not (BUNDLE/"agent_e29_m_family_staged_opening.py").exists():
        raise SystemExit(
            "Missing E29 agent. Run 2026-09-18_install_e29_m_family_staged_opening.py first."
        )

    generated=datetime.now().astimezone().isoformat(timespec="seconds")

    # ---------- Stage A ----------
    opening_seeds=list(range(args.opening_seed_start,args.opening_seed_start+2))
    opening=run_block("STAGE A — OPENING FIDELITY",("e21","aurax7_v7"),opening_seeds)
    opening_errors=[r for r in opening if "error" in r]
    om=medians(opening)

    def at(m,s,k,default=0):
        return m.get(str(s),{}).get(k,default)

    opening_pass=(
        not opening_errors
        and 13 <= at(om,23,"crops") <= 18
        and at(om,23,"structures") == 5
        and at(om,23,"animals") >= 4
        and at(om,23,"hands") >= 4
        and 17 <= at(om,47,"crops") <= 22
        and at(om,47,"structures") == 5
        and at(om,47,"animals") >= 4
        and at(om,47,"hands") >= 4
        and 18 <= at(om,71,"crops") <= 22
        and at(om,71,"structures") == 5
        and at(om,71,"animals") >= 4
        and at(om,71,"hands") >= 5
        and 18 <= at(om,143,"crops") <= 24
        and at(om,143,"structures") == 5
        and at(om,143,"animals") >= 4
        and at(om,143,"hands") >= 5
    )

    if not opening_pass:
        payload={
            "generated":generated,
            "status":"opening_failed",
            "opening_medians":om,
            "opening":opening,
            "errors":opening_errors,
        }
        DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
        write_failure_report(generated,"OPENING FIDELITY FAIL",om,None,opening_errors)
        raise SystemExit(f"Opening fidelity failed. See {REPORT.name}")

    # ---------- Stage B ----------
    mid_seeds=list(range(args.mid_seed_start,args.mid_seed_start+3))
    mid=run_block("STAGE B — MIDGAME FIDELITY",("e21","aurax7_v7"),mid_seeds)
    mid_errors=[r for r in mid if "error" in r]
    mm=medians(mid)

    mid_pass=(
        not mid_errors
        and at(mm,167,"crops") >= 28
        and at(mm,167,"structures") >= 9
        and at(mm,167,"animals") >= 9
        and at(mm,167,"hands") >= 7
        and at(mm,167,"quadrants") >= 2
        and at(mm,215,"crops") >= 33
        and at(mm,215,"structures") >= 10
        and at(mm,215,"animals") >= 10
        and at(mm,215,"hands") >= 8
        and at(mm,215,"quadrants") >= 2
        and at(mm,239,"crops") >= 45
        and at(mm,239,"structures") >= 11
        and at(mm,239,"animals") >= 11
        and at(mm,239,"hands") >= 9
        and at(mm,239,"quadrants") >= 3
        and at(mm,287,"crops") >= 50
        and at(mm,287,"structures") >= 12
        and at(mm,287,"animals") >= 12
        and at(mm,287,"hands") >= 10
        and at(mm,287,"quadrants") >= 3
    )

    rewards=[r["e29_reward"] for r in mid if "error" not in r]
    economic_pass=(
        rewards
        and statistics.median(rewards) >= args.min_mid_reward
        and sum(x>=20000 for x in rewards) >= 8
    )

    if not (mid_pass and economic_pass):
        payload={
            "generated":generated,
            "status":"midgame_failed",
            "opening_medians":om,
            "midgame_medians":mm,
            "economic_pass":economic_pass,
            "midgame_pass":mid_pass,
            "mid_rewards":rewards,
            "opening":opening,
            "midgame":mid,
            "errors":mid_errors,
        }
        DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
        write_failure_report(
            generated,
            f"MIDGAME FAIL (trajectory={mid_pass}, economic={economic_pass})",
            om,mm,mid_errors
        )
        raise SystemExit(f"Midgame fidelity failed. See {REPORT.name}")

    # ---------- Stage C ----------
    fresh_seeds=list(range(args.seed_start,args.seed_start+args.seeds))
    fresh=run_block("STAGE C — W/L SCREEN",OPPONENTS,fresh_seeds)
    fresh_errors=[r for r in fresh if "error" in r]

    payload={
        "generated":generated,
        "status":"complete" if not fresh_errors else "fresh_errors",
        "opening_medians":om,
        "midgame_medians":mm,
        "fresh_seeds":fresh_seeds,
        "fresh":fresh,
        "errors":fresh_errors,
    }
    DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")

    if fresh_errors:
        raise SystemExit(f"{len(fresh_errors)} fresh errors. See {DATA.name}")

    lines=[
        "# E29 Staged-Opening M-Family Screen",
        "",
        f"- Generated: `{generated}`",
        "- Opening fidelity: **PASS**",
        "- Midgame fidelity: **PASS**",
        "",
        "## Fresh W/L",
        "",
        "| Opponent | W-D-L | Score | Median reward |",
        "|---|---:|---:|---:|",
    ]

    aggregate=[]
    for opp in OPPONENTS:
        rr=[r for r in fresh if r["opponent"]==opp]
        aggregate.extend(rr)
        w,d,l=wdl(rr)
        med=statistics.median(r["e29_reward"] for r in rr)
        lines.append(f"| `{opp}` | {w}-{d}-{l} | {100*score(rr):.1f}% | {med:.0f} |")

    w,d,l=wdl(aggregate)
    lines += [
        "",
        f"- Aggregate: **{w}-{d}-{l}** ({100*score(aggregate):.1f}%)",
        "",
        "E29 is only judged on W/L because it first passed opening and midgame fidelity gates.",
    ]

    REPORT.write_text("\n".join(lines),encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n",encoding="utf-8")
    with HISTORY.open("a",encoding="utf-8") as f:
        f.write(
            f"## {generated} — E29 staged-opening M-family screen\n\n"
            "- Opening fidelity: PASS\n"
            "- Midgame fidelity: PASS\n"
            f"- Fresh aggregate W-D-L: {w}-{d}-{l}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- No Kaggle submission performed.\n\n"
        )

    print()
    print("=== E29 SCREEN COMPLETE ===")
    print("Aggregate:",f"{w}-{d}-{l}",f"{100*score(aggregate):.1f}%")
    print("Report:",REPORT.name)


def write_failure_report(generated,status,om,mm,errors):
    lines=[
        "# E29 Staged-Opening M-Family Screen",
        "",
        f"- Generated: `{generated}`",
        f"- Status: **{status}**",
        f"- Errors: **{len(errors)}**",
        "",
        "## Opening medians",
        "",
        "| Step | Crops | Structures | Animals | Hands | Q | Money |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for s in (23,47,71,143):
        d=om.get(str(s),{})
        lines.append(
            f"| {s} | {d.get('crops','')} | {d.get('structures','')} | "
            f"{d.get('animals','')} | {d.get('hands','')} | "
            f"{d.get('quadrants','')} | {d.get('money','')} |"
        )

    lines += [
        "",
        "M-family references:",
        "- step23: crops≈15.5 / structures5 / animals5 / hands4",
        "- step47: crops≈19.5 / structures5 / animals5 / hands4",
        "- step71: crops≈20 / structures5 / animals5 / hands6",
        "- step143: crops≈20 / structures5 / animals5 / hands6",
    ]

    if mm is not None:
        lines += [
            "",
            "## Midgame medians",
            "",
            "| Step | Crops | Structures | Animals | Hands | Q | Money |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for s in (167,215,239,287):
            d=mm.get(str(s),{})
            lines.append(
                f"| {s} | {d.get('crops','')} | {d.get('structures','')} | "
                f"{d.get('animals','')} | {d.get('hands','')} | "
                f"{d.get('quadrants','')} | {d.get('money','')} |"
            )

        lines += [
            "",
            "M-family references:",
            "- step167: crops≈33 / structures≈11 / animals≈11 / hands≈8 / q2",
            "- step215: crops≈38 / structures≈12 / animals≈12 / hands≈9 / q2",
            "- step239: crops≈53 / structures≈14 / animals≈14 / hands≈10 / q3",
            "- step287: crops≈58.5 / structures≈15 / animals≈15 / hands≈11 / q3",
        ]

    REPORT.write_text("\n".join(lines),encoding="utf-8")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--opening-seed-start",type=int,default=29990)
    ap.add_argument("--mid-seed-start",type=int,default=29994)
    ap.add_argument("--min-mid-reward",type=float,default=25000)
    ap.add_argument("--seed-start",type=int,default=30000)
    ap.add_argument("--seeds",type=int,default=8)

    ap.add_argument("--child",action="store_true")
    ap.add_argument("--opponent")
    ap.add_argument("--seed",type=int)
    ap.add_argument("--e29-seat",type=int,choices=(0,1))

    args=ap.parse_args()
    if args.child:
        child(args)
    else:
        parent(args)


if __name__=="__main__":
    main()
