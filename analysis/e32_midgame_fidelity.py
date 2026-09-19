#!/usr/bin/env python3
"""E32 Stage-B midgame fidelity only.

Run from repository root:
    python analysis/e32_midgame_fidelity.py

This intentionally ignores the old step23 hard gate. E32 already has:
- step23: crops12 / structures5 / animals5 / hands4
- step47: crops17 / structures5 / animals5 / hands4
- step71: crops18 / structures5 / animals5 / hands6
- step143: crops20 / structures5 / animals5 / hands6

The purpose here is to decide whether the M-line is worth population testing,
not to optimize one early crop count.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import importlib
import json
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
sys.path.insert(0, str(BUNDLE))

PREFIX = "@@E32MID@@"
CHECKPOINTS = (167, 215, 239, 287, 719)

MODULES = {
    "e32": "agent_e32_m_family_opening_build_priority",
    "e21": "agent_e21_tetsu_market_v23",
}
ELITE = {
    "aurax7_v7": "aurax7_v7_current",
}

def load_module_agent(module_name):
    mod = importlib.import_module(module_name)
    for name in (
        "agent", "kaggle_submission_agent", "submission_agent",
        "melon_maxxer", "policy", "kaggriculture_e776_agent",
    ):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    raise RuntimeError(f"No callable in {module_name}")

def load_elite(name):
    from elite_runtime import load_agent, call_agent
    base = load_agent(name)
    def wrapped(obs, configuration=None):
        return call_agent(base, obs, configuration)
    return wrapped

def resolve(name):
    if name in MODULES:
        return load_module_agent(MODULES[name])
    return load_elite(ELITE[name])

def diag(env, seat, step):
    state = env.steps[min(step, len(env.steps)-1)][seat]
    obs = state.get("observation") or {}
    farm = (obs.get("farms") or [{}])[seat]

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
        "money": float(farm.get("money", 0) or 0),
        "hands": len(farm.get("hands") or []),
        "quadrants": len(farm.get("unlocked_quadrants") or []),
        "crops": sum(crops.values()),
        "structures": sum(structures.values()),
        "animals": sum(animals.values()),
        "crop_mix": dict(crops),
        "animal_mix": dict(animals),
    }

def child(opponent, seed, seat):
    from kaggle_environments import make

    e32 = resolve("e32")
    opp = resolve(opponent)
    agents = [e32, opp] if seat == 0 else [opp, e32]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run(agents)

    a = float(env.steps[-1][seat].get("reward"))
    b = float(env.steps[-1][1-seat].get("reward"))

    print(PREFIX + json.dumps({
        "opponent": opponent,
        "seed": seed,
        "seat": seat,
        "reward": a,
        "opponent_reward": b,
        "outcome": "W" if a > b else "L" if a < b else "D",
        "trajectory": {str(s): diag(env, seat, s) for s in CHECKPOINTS},
    }, ensure_ascii=False))

def run_one(opponent, seed, seat):
    p = subprocess.run(
        [
            sys.executable, str(Path(__file__).resolve()),
            "--child", opponent, str(seed), str(seat),
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
        "seat": seat,
        "error": (p.stderr or p.stdout or "no result")[-4000:],
    }

def medians(rows):
    valid = [r for r in rows if "error" not in r]
    out = {}
    for s in CHECKPOINTS:
        vals = [r["trajectory"][str(s)] for r in valid]
        out[str(s)] = {
            k: statistics.median(v[k] for v in vals)
            for k in ("money", "hands", "quadrants", "crops", "structures", "animals")
        }
    return out

def main():
    if len(sys.argv) == 5 and sys.argv[1] == "--child":
        child(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
        return

    seeds = [33000, 33001, 33002]
    opponents = ("e21", "aurax7_v7")
    rows = []
    total = len(seeds) * len(opponents) * 2
    done = 0

    for opp in opponents:
        for seed in seeds:
            for seat in (0, 1):
                done += 1
                print(f"[{done}/{total}] E32 vs {opp} seed={seed} seat={seat}", flush=True)
                rows.append(run_one(opp, seed, seat))

    errors = [r for r in rows if "error" in r]
    if errors:
        print("\nERRORS:", len(errors))
        print(errors[0]["error"])
        raise SystemExit(2)

    m = medians(rows)

    print("\n# E32 Midgame Fidelity\n")
    print("| Step | Crops | Structures | Animals | Hands | Q | Money |")
    print("|---:|---:|---:|---:|---:|---:|---:|")
    for s in CHECKPOINTS:
        d = m[str(s)]
        print(
            f"| {s} | {d['crops']} | {d['structures']} | {d['animals']} | "
            f"{d['hands']} | {d['quadrants']} | {d['money']} |"
        )

    print("\nM-family references:")
    print("- 167: crops≈33 / structures≈11 / animals≈11 / hands≈8 / Q2")
    print("- 215: crops≈38 / structures≈12 / animals≈12 / hands≈9 / Q2")
    print("- 239: crops≈53 / structures≈14 / animals≈14 / hands≈10 / Q3")
    print("- 287: crops≈58.5 / structures≈15 / animals≈15 / hands≈11 / Q3")

    # Diagnostic only: do not make final competition decisions from these 12 games.
    c = Counter(r["outcome"] for r in rows)
    rewards = [r["reward"] for r in rows]
    print("\nDiagnostic W-D-L:", f"{c['W']}-{c['D']}-{c['L']}")
    print("Median E32 reward:", statistics.median(rewards))

if __name__ == "__main__":
    main()
