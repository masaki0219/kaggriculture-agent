"""
trace_h1_economy.py

One-game economy trace for agent_h1 vs agent_v15.
Use this BEFORE any further strength benchmark.

Run:
    python trace_h1_economy.py

Prints one compact line at the start of each day:
money, land, hands, crop/animal counts, shed value-ish inventory,
plus the market orders h1 tries to issue at hour 0/1/5.
"""

from __future__ import annotations

from collections import Counter
from kaggle_environments import make

from agent_h1 import agent as h1
from agent_v15 import agent as v15


BASE = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
    "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200,
    "FERTILIZER": 100,
}
PRODUCTS = tuple(BASE)


def get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def counts(farm):
    crops = Counter()
    animals = Counter()
    structures = Counter()
    weeds = 0
    for row in get(farm, "tiles", []) or []:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "PLANT":
                crops[str(tile.get("crop"))] += 1
            elif kind in ("PASTURE", "COOP"):
                structures[kind] += 1
                a = tile.get("animal")
                if a:
                    animals[str(a)] += 1
            elif kind == "WEED":
                weeds += 1
    return crops, animals, structures, weeds


class Trace:
    def __init__(self, fn):
        self.fn = fn
        self.last_day = None

    def __call__(self, obs, config=None):
        day = int(get(obs, "day", 0) or 0)
        hour = int(get(obs, "hour", 0) or 0)
        player = int(get(obs, "player", 0) or 0)
        farm = (get(obs, "farms", []) or [])[player]
        private = get(obs, "private", {}) or {}
        shed = get(private, "shed", {}) or {}
        seeds = get(private, "seeds", {}) or {}
        crops, animals, structures, weeds = counts(farm)

        if hour == 0 and day != self.last_day:
            self.last_day = day
            prices = get(get(obs, "market", {}) or {}, "prices", {}) or {}
            shed_total = sum(int(v or 0) for v in shed.values())
            shed_base = sum(
                int(shed.get(p, 0) or 0) * BASE[p]
                for p in PRODUCTS
            )
            print(
                f"D{day:02d} money={float(get(farm,'money',0) or 0):8.0f} "
                f"land={len(get(farm,'unlocked_quadrants',[]) or [])} "
                f"hands={len(get(farm,'hands',[]) or [])} "
                f"crop[W={crops['WHEAT']:2d} C={crops['CARROT']:2d} "
                f"T={crops['TOMATO']:2d} S={crops['STRAWBERRY']:2d} "
                f"M={crops['MELON']:2d}] "
                f"animal[G={animals['GOOSE']:2d} C={animals['COW']:2d} "
                f"S={animals['SHEEP']:2d}] "
                f"shed={shed_total:3d} base≈{shed_base:6d} "
                f"fert={int(shed.get('FERTILIZER',0) or 0):2d} "
                f"milk={int(shed.get('MILK',0) or 0):2d} "
                f"wool={int(shed.get('WOOL',0) or 0):2d} "
                f"straw={int(shed.get('STRAWBERRY',0) or 0):2d} "
                f"melon={int(shed.get('MELON',0) or 0):2d} "
                f"wheat={int(shed.get('WHEAT',0) or 0):2d} "
                f"px[MILK={int(prices.get('MILK',0) or 0):3d} "
                f"WOOL={int(prices.get('WOOL',0) or 0):3d} "
                f"ST={int(prices.get('STRAWBERRY',0) or 0):3d} "
                f"M={int(prices.get('MELON',0) or 0):3d}]"
            )

        try:
            action = self.fn(obs, config)
        except TypeError:
            action = self.fn(obs)

        if hour in (0, 1, 5) and isinstance(action, dict):
            orders = action.get("market", []) or []
            if orders:
                print(f"    h{hour:02d} orders={orders}")

        return action


def main():
    traced = Trace(h1)
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": 0},
        debug=False,
    )
    env.run([traced, v15])
    final = env.steps[-1]
    print(
        f"\nFINAL h1={float(final[0].reward):.0f} "
        f"v15={float(final[1].reward):.0f}"
    )


if __name__ == "__main__":
    main()
