"""
trace_h2_economy.py

Reliable one-game economy trace for agent_h2 vs agent_v15.

Unlike the first version, this DOES NOT rely on print() from inside the
Kaggle agent callback. It stores snapshots/actions in memory and prints them
only after env.run() has completed.

Run:
    python trace_h2_economy.py
"""

from __future__ import annotations

from collections import Counter
from kaggle_environments import make

from agent_h2 import agent as h2
from agent_v15 import agent as v15


BASE = {
    "WHEAT": 25,
    "CARROT": 35,
    "TOMATO": 60,
    "STRAWBERRY": 120,
    "MELON": 250,
    "EGG": 50,
    "MILK": 160,
    "WOOL": 200,
    "FERTILIZER": 100,
}

PRODUCTS = tuple(BASE)


def get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def count_farm(farm):
    crops = Counter()
    animals = Counter()
    structures = Counter()
    weeds = 0
    empty = 0

    for row in get(farm, "tiles", []) or []:
        for tile in row or []:
            if tile == "LOCKED":
                continue
            if tile is None:
                empty += 1
                continue
            if not isinstance(tile, dict):
                continue

            kind = tile.get("kind")
            if kind == "PLANT":
                crop = tile.get("crop")
                if crop:
                    crops[str(crop)] += 1
            elif kind in ("PASTURE", "COOP"):
                structures[kind] += 1
                animal = tile.get("animal")
                if animal:
                    animals[str(animal)] += 1
            elif kind == "WEED":
                weeds += 1

    return crops, animals, structures, weeds, empty


class TraceAgent:
    def __init__(self, fn):
        self.fn = fn
        self.daily = []
        self.orders = []
        self._seen_days = set()

    def __call__(self, obs, config=None):
        day = int(get(obs, "day", 0) or 0)
        hour = int(get(obs, "hour", 0) or 0)
        player = int(get(obs, "player", 0) or 0)

        farms = get(obs, "farms", []) or []
        farm = farms[player]
        private = get(obs, "private", {}) or {}
        shed = get(private, "shed", {}) or {}
        seeds = get(private, "seeds", {}) or {}

        crops, animals, structures, weeds, empty = count_farm(farm)

        market = get(obs, "market", {}) or {}
        prices = get(market, "prices", {}) or {}
        town = get(obs, "town", {}) or {}

        if hour == 0 and day not in self._seen_days:
            self._seen_days.add(day)

            shed_total = sum(
                int(v or 0)
                for v in shed.values()
                if isinstance(v, (int, float))
            )

            shed_base_value = sum(
                int(shed.get(p, 0) or 0) * BASE[p]
                for p in PRODUCTS
            )

            self.daily.append({
                "day": day,
                "money": float(get(farm, "money", 0) or 0),
                "land": len(get(farm, "unlocked_quadrants", []) or []),
                "hands": len(get(farm, "hands", []) or []),
                "hires_today": int(get(farm, "hires_today", 0) or 0),
                "crops": dict(crops),
                "animals": dict(animals),
                "structures": dict(structures),
                "weeds": weeds,
                "empty": empty,
                "shed_total": shed_total,
                "shed_base_value": shed_base_value,
                "shed": {
                    k: int(v)
                    for k, v in shed.items()
                    if int(v or 0) != 0
                },
                "seeds": {
                    k: int(v)
                    for k, v in seeds.items()
                    if int(v or 0) != 0
                },
                "prices": {
                    p: float(get(prices, p, 0) or 0)
                    for p in PRODUCTS
                },
                "shops": list(get(town, "unlocked_shops", []) or []),
            })

        try:
            action = self.fn(obs, config)
        except TypeError:
            action = self.fn(obs)

        if isinstance(action, dict):
            market_orders = action.get("market", []) or []
            if market_orders:
                self.orders.append({
                    "day": day,
                    "hour": hour,
                    "orders": market_orders,
                    "money_before": float(get(farm, "money", 0) or 0),
                })

        return action


def print_daily(trace: TraceAgent):
    print("\n================ DAILY ECONOMY ================")

    for r in trace.daily:
        c = r["crops"]
        a = r["animals"]
        s = r["shed"]
        p = r["prices"]

        print(
            f"D{r['day']:02d} "
            f"money={r['money']:8.0f} "
            f"land={r['land']} "
            f"hands={r['hands']:2d} "
            f"empty={r['empty']:2d} "
            f"weeds={r['weeds']:2d} | "
            f"crop W={c.get('WHEAT',0):2d} "
            f"C={c.get('CARROT',0):2d} "
            f"T={c.get('TOMATO',0):2d} "
            f"St={c.get('STRAWBERRY',0):2d} "
            f"M={c.get('MELON',0):2d} | "
            f"animal G={a.get('GOOSE',0):2d} "
            f"C={a.get('COW',0):2d} "
            f"S={a.get('SHEEP',0):2d} | "
            f"shed={r['shed_total']:3d} "
            f"base≈{r['shed_base_value']:6.0f} "
            f"W={s.get('WHEAT',0):2d} "
            f"F={s.get('FERTILIZER',0):2d} "
            f"E={s.get('EGG',0):2d} "
            f"Mi={s.get('MILK',0):2d} "
            f"Wo={s.get('WOOL',0):2d} "
            f"St={s.get('STRAWBERRY',0):2d} "
            f"M={s.get('MELON',0):2d} | "
            f"px Mi={p.get('MILK',0):5.0f} "
            f"Wo={p.get('WOOL',0):5.0f} "
            f"St={p.get('STRAWBERRY',0):5.0f} "
            f"M={p.get('MELON',0):5.0f}"
        )


def print_orders(trace: TraceAgent):
    print("\n================ MARKET ORDERS ================")

    interesting_hours = {0, 1, 5, 9, 13, 17, 21, 23}

    for r in trace.orders:
        if r["hour"] in interesting_hours:
            print(
                f"D{r['day']:02d} H{r['hour']:02d} "
                f"money_before={r['money_before']:8.0f} "
                f"{r['orders']}"
            )


def main():
    trace = TraceAgent(h2)

    env = make(
        "kaggriculture",
        configuration={
            "episodeSteps": 720,
            "seed": 0,
        },
        debug=False,
    )

    env.run([trace, v15])

    final = env.steps[-1]

    print_daily(trace)
    print_orders(trace)

    print("\n================ FINAL ================")
    print(
        f"h2={float(final[0].reward):.0f} "
        f"v15={float(final[1].reward):.0f}"
    )


if __name__ == "__main__":
    main()
