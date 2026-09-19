#!/usr/bin/env python3
"""Trace E31 opening for one game, steps 0..23 only."""

from __future__ import annotations
from collections import Counter
from pathlib import Path
import importlib
import sys

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
sys.path.insert(0, str(BUNDLE))

from kaggle_environments import make
from agent_e31_m_family_opening_scheduler import agent as e31
from agent_e21_tetsu_market_v23 import agent as e21


def diag(obs, seat):
    farm = obs["farms"][seat]
    private = obs.get("private") or {}

    crops = Counter()
    structures = Counter()
    placed = Counter()
    occupied = []

    for y, row in enumerate(farm.get("tiles") or []):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "PLANT":
                crops[str(tile.get("crop"))] += 1
                occupied.append(((x, y), f"P:{tile.get('crop')}"))
            elif kind in ("PASTURE", "COOP"):
                structures[kind] += 1
                animal = tile.get("animal")
                if animal:
                    placed[str(animal)] += 1
                    occupied.append(((x, y), f"{kind}:{animal}"))
                else:
                    occupied.append(((x, y), kind))

    return {
        "money": farm.get("money"),
        "farmer": farm.get("farmer"),
        "hands": farm.get("hands"),
        "hires_today": farm.get("hires_today"),
        "structures": dict(structures),
        "placed": dict(placed),
        "crops": dict(crops),
        "shed": {k: v for k, v in (private.get("shed") or {}).items() if v},
        "seeds": {k: v for k, v in (private.get("seeds") or {}).items() if v},
        "inventories": private.get("inventories"),
        "occupied": occupied,
    }


def main():
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": 32000},
        debug=False,
    )
    env.run([e31, e21])

    print("=== E31 opening trace: seed=32000, seat=0 ===")
    print()

    for step in range(24):
        state = env.steps[step][0]
        obs = state.get("observation") or {}
        action = state.get("action")
        d = diag(obs, 0)

        print("=" * 90)
        print(f"STEP {step}")
        print(
            f"money={d['money']} hires_today={d['hires_today']} "
            f"structures={d['structures']} placed={d['placed']} crops={d['crops']}"
        )
        print(f"farmer={d['farmer']} hands={d['hands']}")
        print(f"shed={d['shed']}")
        print(f"seeds={d['seeds']}")
        print(f"inventories={d['inventories']}")
        print(f"action={action}")
        print("occupied:")
        print("  " + " ".join(f"{p}:{x}" for p, x in d["occupied"]))

    print()
    print("=== compact transitions ===")
    for step in range(23):
        a = diag(env.steps[step][0].get("observation") or {}, 0)
        b = diag(env.steps[step + 1][0].get("observation") or {}, 0)
        action = env.steps[step][0].get("action")
        print(
            f"{step:02d}->{step+1:02d} "
            f"S {sum(a['structures'].values())}->{sum(b['structures'].values())} "
            f"A {sum(a['placed'].values())}->{sum(b['placed'].values())} "
            f"C {sum(a['crops'].values())}->{sum(b['crops'].values())} "
            f"H {len(a['hands'])}->{len(b['hands'])} "
            f"$ {a['money']}->{b['money']} "
            f"action={action}"
        )


if __name__ == "__main__":
    main()
