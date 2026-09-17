"""
agent_h3.py — repaired independent heuristic Kaggriculture agent

Design goal:
- No public-agent route/tape copying.
- Reuse only generic ideas/mechanics and the user's own earlier engineering style.
- Closed-loop policy based on current public game state:
    town demand + market prices + opponent future supply + remaining horizon.

Main heuristics:
1. 12-hand labour core, tapered late.
2. Two extra land buys when the economy can support them.
3. Wheat operating base for animal feed.
4. Dynamic animal portfolio (cow/sheep/goose) from demand/price/opponent exposure.
5. Dynamic crop portfolio across wheat/carrot/tomato/strawberry/melon.
6. Feed + care animals and collect fertilizer aggressively.
7. Sell shortly after town-consumption ticks when possible.
8. Hold depressed premium goods unless shed pressure forces sale.
9. Stop long-horizon investment late and liquidate everything to cash.

This file is intended as an EXPERIMENTAL local candidate, not an asserted best agent.
"""

from __future__ import annotations

from collections import Counter, deque
import math


# ---------------------------------------------------------------------------
# Static official-game constants (embedded to keep the candidate self-contained)
# ---------------------------------------------------------------------------

CROPS = {
    "WHEAT":      {"seed": 10,  "first": 2,  "max_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first": 2,  "max_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first": 8,  "max_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "max_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first": 10, "max_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first": 4, "interval": 1, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first": 8, "interval": 2, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first": 6, "interval": 3, "product": "WOOL"},
}

BASE_PRICE = {
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

SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}

PRODUCTS = tuple(BASE_PRICE)
ANIMAL_ITEMS = tuple(ANIMALS)
CROP_ITEMS = tuple(CROPS)

LAND_PRICES = (1000, 2000, 4000)

MOVES = (
    ("NORTH", 0, -1),
    ("WEST", -1, 0),
    ("SOUTH", 0, 1),
    ("EAST", 1, 0),
)

# Lower = more urgent.
P_RESCUE = 0
P_FEED = 1
P_HARVEST = 2
P_FERT = 3
P_CARE = 4
P_WATER = 5
P_PLACE = 6
P_BUILD = 7
P_PLANT = 8
P_DIG = 9


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def _get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _shed_cells(board_size, tiles):
    half = board_size // 2
    candidates = (
        (half - 1, half - 1),
        (half, half - 1),
        (half - 1, half),
        (half, half),
    )
    # Shed ops are legal even from a LOCKED access tile, but for generic routing
    # prefer currently unlocked access cells when available.
    accessible = [
        p for p in candidates
        if 0 <= p[0] < board_size
        and 0 <= p[1] < board_size
        and tiles[p[1]][p[0]] != "LOCKED"
    ]
    return accessible or [candidates[0]]


def _nearest_shed(pos, board_size, tiles):
    return min(
        _shed_cells(board_size, tiles),
        key=lambda p: (_distance(pos, p), p[1], p[0]),
    )


def _bfs_first_step(tiles, source, target):
    source = tuple(source)
    target = tuple(target)

    if source == target:
        return None

    n = len(tiles)
    q = deque([source])
    parent = {source: None}
    move_used = {}

    while q:
        x, y = q.popleft()
        for name, dx, dy in MOVES:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < n and 0 <= ny < n):
                continue
            nxt = (nx, ny)
            if nxt in parent:
                continue

            # Official engine allows movement through LOCKED cells.
            parent[nxt] = (x, y)
            move_used[nxt] = name

            if nxt == target:
                q.clear()
                break
            q.append(nxt)

    if target not in parent:
        return None

    cur = target
    while parent[cur] != source:
        cur = parent[cur]
        if cur is None:
            return None
    return move_used[cur]


def _inventory_sum(inventories, item):
    return sum(int((_get(inv, item, 0) or 0)) for inv in inventories)


def _stock(private, item):
    shed = _get(private, "shed", {}) or {}
    inventories = list(_get(private, "inventories", []) or [])
    return int(_get(shed, item, 0) or 0) + _inventory_sum(inventories, item)


def _shed_total(private):
    shed = _get(private, "shed", {}) or {}
    return sum(int(v or 0) for v in shed.values() if isinstance(v, (int, float)))


def _fib_hire_cost(n_already):
    # 1,1,2,3,5,...
    if n_already <= 1:
        return 1
    a, b = 1, 1
    for _ in range(2, n_already + 1):
        a, b = b, a + b
    return a


# ---------------------------------------------------------------------------
# Public-state accounting
# ---------------------------------------------------------------------------

def _farm_counts(farm):
    crops = Counter()
    animals = Counter()
    structures = Counter()
    weeds = 0
    empty = 0

    for row in _get(farm, "tiles", []) or []:
        for tile in row:
            if tile == "LOCKED":
                continue
            if tile is None:
                empty += 1
                continue
            if not isinstance(tile, dict):
                continue

            kind = tile.get("kind")
            if kind == "PLANT":
                crops[str(tile.get("crop"))] += 1
            elif kind == "WEED":
                weeds += 1
            elif kind in ("PASTURE", "COOP"):
                structures[kind] += 1
                animal = tile.get("animal")
                if animal:
                    animals[str(animal)] += 1

    return {
        "crops": crops,
        "animals": animals,
        "structures": structures,
        "weeds": weeds,
        "empty": empty,
    }


def _owned_animals(farm, private):
    c = _farm_counts(farm)["animals"]
    shed = _get(private, "shed", {}) or {}
    invs = list(_get(private, "inventories", []) or [])
    return Counter({
        a: (
            int(c.get(a, 0))
            + int(_get(shed, a, 0) or 0)
            + _inventory_sum(invs, a)
        )
        for a in ANIMAL_ITEMS
    })


def _shop_daily_pull(obs):
    """
    Approximate daily public demand:
      - town center: 1/day for every non-fertilizer item
      - each multi-product shop: 1 item / 4 turns = 6/day
      - each single-product shop: 2 items / 4 turns = 12/day
    """
    pull = Counter({p: 1.0 for p in PRODUCTS if p != "FERTILIZER"})
    town = _get(obs, "town", {}) or {}
    shops = list(_get(town, "unlocked_shops", []) or [])

    for shop in shops:
        products = SHOP_PRODUCTS.get(shop, ())
        mult = 2.0 if len(products) == 1 else 1.0
        for p in products:
            pull[p] += 6.0 * mult
    return pull


def _price_ratio(obs, item):
    market = _get(obs, "market", {}) or {}
    prices = _get(market, "prices", {}) or {}
    px = float(_get(prices, item, BASE_PRICE[item]) or BASE_PRICE[item])
    return max(0.01, px / BASE_PRICE[item])


def _opponent_exposure(obs, player):
    farms = _get(obs, "farms", []) or []
    if len(farms) < 2:
        return Counter()

    opp = farms[1 - player]
    c = _farm_counts(opp)
    exposure = Counter()

    for crop, n in c["crops"].items():
        exposure[crop] += n

    for animal, n in c["animals"].items():
        product = ANIMALS.get(animal, {}).get("product")
        if product:
            exposure[product] += n

    return exposure


# ---------------------------------------------------------------------------
# Dynamic production planning
# ---------------------------------------------------------------------------

def _hand_target(day):
    # Keep labour cheap until the farm itself is producing cash.
    # Eight hands cost only 54/day and was already a stable scale in v10/v11.
    if day <= 17:
        return 8
    if day <= 23:
        return 9
    if day <= 26:
        return 8
    if day == 27:
        return 6
    if day == 28:
        return 4
    return 0


def _extra_land_target(day):
    # Land is expansion capital, not an opening purchase.
    if day < 9:
        return 0
    if day < 16:
        return 1
    if day <= 18:
        return 2
    return 0


def _animal_total_target(day):
    # Get the first productive herd running before expanding acreage.
    if day < 3:
        return 0
    if day < 5:
        return 2
    if day < 7:
        return 4
    if day < 10:
        return 8
    if day < 14:
        return 10
    if day <= 17:
        return 12
    return 0  # no new animal investment after day 17


def _animal_goals(obs, farm, private, player):
    total = _animal_total_target(int(_get(obs, "day", 0) or 0))
    if total <= 0:
        return Counter()

    demand = _shop_daily_pull(obs)
    opp = _opponent_exposure(obs, player)
    prices = {p: _price_ratio(obs, p) for p in ("EGG", "MILK", "WOOL")}

    # Long-run output/day with daily FEED+CARE after ramp.
    # Goose ~2/day, cow ~3 every 2d, sheep ~4 every 3d.
    rate = {"GOOSE": 2.0, "COW": 1.5, "SHEEP": 4.0 / 3.0}
    base_pref = {"GOOSE": 0.38, "COW": 1.00, "SHEEP": 0.92}
    caps = {"GOOSE": 3, "COW": 10, "SHEEP": 8}

    # Do not force poultry unless egg demand/price actually justifies it.
    egg_shop_signal = max(0.0, demand["EGG"] - 1.0)

    score = {}
    for animal in ANIMAL_ITEMS:
        product = ANIMALS[animal]["product"]
        demand_factor = 1.0 + 0.035 * max(0.0, demand[product] - 1.0)
        crowd_penalty = 1.0 / (1.0 + 0.055 * opp[product])
        s = (
            base_pref[animal]
            * rate[animal]
            * BASE_PRICE[product]
            * (prices[product] ** 1.35)
            * demand_factor
            * crowd_penalty
        )
        if animal == "GOOSE" and egg_shop_signal < 10 and prices["EGG"] < 1.15:
            s *= 0.28
        score[animal] = s

    goals = Counter()
    # Greedy marginal allocation with diminishing returns creates diversification.
    for _ in range(total):
        candidates = []
        for animal in ANIMAL_ITEMS:
            if goals[animal] >= caps[animal]:
                continue
            marginal = score[animal] / (1.0 + 0.14 * goals[animal])
            candidates.append((marginal, animal))
        if not candidates:
            break
        _, chosen = max(candidates)
        goals[chosen] += 1

    # Maintain a minimum mixed pasture core once scaled, unless a species is
    # overwhelmingly disfavoured.
    if total >= 8:
        if goals["COW"] < 4:
            donor = max(("SHEEP", "GOOSE"), key=lambda a: goals[a])
            shift = min(4 - goals["COW"], goals[donor])
            goals[donor] -= shift
            goals["COW"] += shift
        if goals["SHEEP"] < 2:
            donor = max(("COW", "GOOSE"), key=lambda a: goals[a])
            shift = min(2 - goals["SHEEP"], max(0, goals[donor] - 1))
            goals[donor] -= shift
            goals["SHEEP"] += shift

    return goals


def _crop_targets(obs, farm, private, player):
    day = int(_get(obs, "day", 0) or 0)
    owned = _owned_animals(farm, private)
    animal_count = sum(owned.values())

    # Feed backbone. Do not fill the opening 5x5: reserve physical space for
    # pastures/coops so the animal engine can start before any land purchase.
    wheat_target = max(10, min(14, animal_count + 4))

    if day < 3:
        return Counter({
            "WHEAT": 10,
            "CARROT": 4,   # quick liquidity bridge
            "MELON": 4,    # small long-horizon premium position
        })

    if day < 6:
        premium_slots = 10
    elif day < 10:
        premium_slots = 18
    else:
        premium_slots = 28

    demand = _shop_daily_pull(obs)
    opp = _opponent_exposure(obs, player)

    # Preference is intentionally diversified. Market price and town demand
    # decide where the extra slots go.
    base_pref = {
        "CARROT": 0.42,
        "TOMATO": 0.52,
        "STRAWBERRY": 1.15,
        "MELON": 0.92,
    }
    caps = {
        "CARROT": 12,
        "TOMATO": 12,
        "STRAWBERRY": 24,
        "MELON": 14,
    }
    last_new_day = {
        "CARROT": 25,
        "TOMATO": 20,
        "STRAWBERRY": 17,
        "MELON": 17,
    }
    # Steep-glut products get stronger opponent-crowding penalties.
    crowd_k = {
        "CARROT": 0.020,
        "TOMATO": 0.025,
        "STRAWBERRY": 0.040,
        "MELON": 0.065,
    }

    scores = {}
    for crop in ("CARROT", "TOMATO", "STRAWBERRY", "MELON"):
        if day > last_new_day[crop]:
            scores[crop] = 0.0
            continue

        pr = _price_ratio(obs, crop)
        demand_factor = 1.0 + 0.030 * max(0.0, demand[crop] - 1.0)
        crowd_penalty = 1.0 / (1.0 + crowd_k[crop] * opp[crop])

        # Penalize long-horizon crops as their first possible yield approaches
        # the end of the season.
        first = CROPS[crop]["first"]
        horizon = max(1, 30 - day)
        horizon_factor = min(1.0, horizon / max(1.0, first + 3.0))

        scores[crop] = (
            base_pref[crop]
            * (pr ** 1.55)
            * demand_factor
            * crowd_penalty
            * horizon_factor
        )

    targets = Counter({"WHEAT": wheat_target})

    # Stable minimum diversification in the main investment window.
    if day <= 17:
        targets["STRAWBERRY"] = 4
        targets["MELON"] = 4
        remaining = max(0, premium_slots - 8)
    else:
        remaining = premium_slots

    for _ in range(remaining):
        choices = []
        for crop in ("CARROT", "TOMATO", "STRAWBERRY", "MELON"):
            if scores[crop] <= 0:
                continue
            if targets[crop] >= caps[crop]:
                continue
            marginal = scores[crop] / (1.0 + 0.075 * targets[crop])
            choices.append((marginal, crop))
        if not choices:
            break
        _, crop = max(choices)
        targets[crop] += 1

    # Late season: recycle long-horizon acreage into quick crops/wheat.
    if day >= 18:
        quick_extra = 8 if day <= 24 else 4
        carrot_signal = scores.get("CARROT", 0.0)
        tomato_signal = scores.get("TOMATO", 0.0)
        if carrot_signal >= tomato_signal:
            targets["CARROT"] += quick_extra
        elif day <= 20:
            targets["TOMATO"] += quick_extra

    return targets


# ---------------------------------------------------------------------------
# Field task creation
# ---------------------------------------------------------------------------

def _build_tasks(obs, farm, private, player):
    day = int(_get(obs, "day", 0) or 0)
    hour = int(_get(obs, "hour", 0) or 0)
    tiles = _get(farm, "tiles", []) or []
    n = len(tiles)

    counts = _farm_counts(farm)
    seeds = _get(private, "seeds", {}) or {}
    shed = _get(private, "shed", {}) or {}
    invs = list(_get(private, "inventories", []) or [])

    animal_goals = _animal_goals(obs, farm, private, player)
    crop_targets = _crop_targets(obs, farm, private, player)

    available_animals = Counter({
        a: int(_get(shed, a, 0) or 0) + _inventory_sum(invs, a)
        for a in ANIMAL_ITEMS
    })

    tasks = []
    empty_cells = []
    empty_pastures = []
    empty_coops = []

    for y in range(n):
        for x in range(n):
            tile = tiles[y][x]

            if tile == "LOCKED":
                continue
            if tile is None:
                empty_cells.append((x, y))
                continue
            if not isinstance(tile, dict):
                continue

            kind = tile.get("kind")

            if kind == "WEED":
                tasks.append({
                    "priority": P_DIG,
                    "target": (x, y),
                    "action": ["DIG"],
                    "requires": None,
                    "tag": "dig",
                })
                continue

            if kind == "PLANT":
                crop = str(tile.get("crop"))
                spec = CROPS.get(crop)
                if not spec:
                    continue

                planted = int(tile.get("planted_day", day) or day)
                age = day - planted
                units = int(tile.get("yield_units", 0) or 0)

                if spec["ongoing"]:
                    ready = (
                        age >= spec["first"]
                        and (
                            units >= 2
                            or day >= 27
                            or (hour >= 18 and day >= 26 and units > 0)
                        )
                    )
                else:
                    ready = (
                        age >= spec["first"]
                        and (
                            units >= spec["max_yield"]
                            or age >= spec["max_day"]
                            or day >= 28
                        )
                    )

                if ready and units > 0:
                    tasks.append({
                        "priority": P_HARVEST,
                        "target": (x, y),
                        "action": ["HARVEST"],
                        "requires": None,
                        "tag": f"harvest_{crop}",
                    })

                # Every plant is watered daily when possible. This both avoids
                # the 2-day weed death rule and maximizes one-time yield.
                if not tile.get("watered_today", False) and day < 29:
                    consecutive = int(tile.get("consecutive_unwatered", 0) or 0)
                    pri = P_RESCUE if consecutive >= 1 else P_WATER
                    tasks.append({
                        "priority": pri,
                        "target": (x, y),
                        "action": ["WATER"],
                        "requires": None,
                        "tag": f"water_{crop}",
                    })
                continue

            if kind in ("PASTURE", "COOP"):
                animal = tile.get("animal")
                if not animal:
                    if kind == "PASTURE":
                        empty_pastures.append((x, y))
                    else:
                        empty_coops.append((x, y))
                    continue

                animal = str(animal)

                # On day 29 there is no next daily production refresh, so do not
                # waste actions/cash on feed/care. Harvest and fertilizer only.
                if day < 29:
                    if not tile.get("fed_today", False):
                        consecutive = int(tile.get("consecutive_unfed", 0) or 0)
                        tasks.append({
                            "priority": P_RESCUE if consecutive >= 1 else P_FEED,
                            "target": (x, y),
                            "action": ["FEED"],
                            "requires": "WHEAT",
                            "tag": "feed",
                        })

                    if tile.get("fed_today", False) and not tile.get("cared_today", False):
                        tasks.append({
                            "priority": P_CARE,
                            "target": (x, y),
                            "action": ["CARE"],
                            "requires": None,
                            "tag": "care",
                        })

                units = int(tile.get("yield_units", 0) or 0)
                if units >= 2 or (day >= 27 and units > 0):
                    tasks.append({
                        "priority": P_HARVEST,
                        "target": (x, y),
                        "action": ["HARVEST"],
                        "requires": None,
                        "tag": f"harvest_{animal}",
                    })

                if tile.get("fertilizer_available", False):
                    tasks.append({
                        "priority": P_FERT,
                        "target": (x, y),
                        "action": ["COLLECT_FERTILIZER"],
                        "requires": None,
                        "tag": "collect_fertilizer",
                    })

    # Decide which purchased animal should occupy each currently empty structure.
    placed = counts["animals"]
    deficits = Counter({
        a: max(0, int(animal_goals.get(a, 0)) - int(placed.get(a, 0)))
        for a in ANIMAL_ITEMS
    })

    pasture_species = []
    for _ in empty_pastures:
        choices = [
            a for a in ("COW", "SHEEP")
            if deficits[a] > 0 and available_animals[a] > 0
        ]
        if not choices:
            choices = [
                a for a in ("COW", "SHEEP")
                if available_animals[a] > 0
            ]
        if not choices:
            break
        chosen = max(choices, key=lambda a: (deficits[a], available_animals[a]))
        pasture_species.append(chosen)
        available_animals[chosen] -= 1
        deficits[chosen] = max(0, deficits[chosen] - 1)

    for cell, animal in zip(empty_pastures, pasture_species):
        tasks.append({
            "priority": P_PLACE,
            "target": cell,
            "action": ["PLACE", animal],
            "requires": animal,
            "tag": f"place_{animal}",
        })

    goose_need = min(
        len(empty_coops),
        max(0, int(animal_goals.get("GOOSE", 0)) - int(placed.get("GOOSE", 0))),
        available_animals["GOOSE"],
    )
    for cell in empty_coops[:goose_need]:
        tasks.append({
            "priority": P_PLACE,
            "target": cell,
            "action": ["PLACE", "GOOSE"],
            "requires": "GOOSE",
            "tag": "place_GOOSE",
        })

    # Reserve central empty tiles for the desired animal structures before crops.
    shed_cells = _shed_cells(n, tiles)
    empty_cells.sort(
        key=lambda p: (
            min(_distance(p, s) for s in shed_cells),
            p[1],
            p[0],
        )
    )

    desired_pastures = int(animal_goals.get("COW", 0) + animal_goals.get("SHEEP", 0))
    pasture_need = max(0, desired_pastures - int(counts["structures"].get("PASTURE", 0)))

    desired_coops = int(animal_goals.get("GOOSE", 0))
    coop_need = max(0, desired_coops - int(counts["structures"].get("COOP", 0)))

    for _ in range(min(pasture_need, len(empty_cells))):
        cell = empty_cells.pop(0)
        tasks.append({
            "priority": P_BUILD,
            "target": cell,
            "action": ["BUILD_PASTURE"],
            "requires": None,
            "tag": "build_pasture",
        })

    for _ in range(min(coop_need, len(empty_cells))):
        cell = empty_cells.pop(0)
        tasks.append({
            "priority": P_BUILD,
            "target": cell,
            "action": ["BUILD_COOP"],
            "requires": None,
            "tag": "build_coop",
        })

    # Plant toward dynamic target. Use a local seed budget so multiple tasks do
    # not all assume the same single seed exists.
    local_seed = Counter({
        crop: int(_get(seeds, crop, 0) or 0)
        for crop in CROP_ITEMS
    })

    # Stable priority: feed wheat first, then the currently most under-target crop.
    deficits_crop = Counter({
        crop: max(
            0,
            int(crop_targets.get(crop, 0))
            - int(counts["crops"].get(crop, 0))
        )
        for crop in CROP_ITEMS
    })

    while empty_cells:
        choices = [
            crop for crop in CROP_ITEMS
            if deficits_crop[crop] > 0 and local_seed[crop] > 0
        ]
        if not choices:
            break

        # Wheat operating base gets first call until satisfied; after that use
        # relative deficit to avoid all-or-nothing planting.
        if "WHEAT" in choices and counts["crops"].get("WHEAT", 0) < crop_targets["WHEAT"]:
            chosen = "WHEAT"
        else:
            chosen = max(
                choices,
                key=lambda c: deficits_crop[c] / max(1, crop_targets.get(c, 1)),
            )

        cell = empty_cells.pop(0)
        tasks.append({
            "priority": P_PLANT,
            "target": cell,
            "action": ["PLANT", chosen],
            "requires": None,
            "tag": f"plant_{chosen}",
        })
        deficits_crop[chosen] -= 1
        local_seed[chosen] -= 1

    return tasks


# ---------------------------------------------------------------------------
# Market policy
# ---------------------------------------------------------------------------

def _append_hires(orders, farm, money, target, limit=10):
    current = len(_get(farm, "hands", []) or [])
    already = int(_get(farm, "hires_today", 0) or 0)
    need = max(0, target - current)

    for i in range(need):
        if len(orders) >= limit:
            break
        cost = _fib_hire_cost(already + i)
        if money < cost:
            break
        orders.append(["HIRE"])
        money -= cost
    return money


def _market_actions(obs, farm, private, player):
    day = int(_get(obs, "day", 0) or 0)
    hour = int(_get(obs, "hour", 0) or 0)
    money = float(_get(farm, "money", 0) or 0)
    shed = _get(private, "shed", {}) or {}
    seeds = _get(private, "seeds", {}) or {}
    market = _get(obs, "market", {}) or {}
    prices = _get(market, "prices", {}) or {}

    counts = _farm_counts(farm)
    owned = _owned_animals(farm, private)
    animal_goals = _animal_goals(obs, farm, private, player)
    crop_targets = _crop_targets(obs, farm, private, player)
    demand = _shop_daily_pull(obs)

    orders = []

    # ---- capital + labour -------------------------------------------------
    extra_land = max(0, len(_get(farm, "unlocked_quadrants", []) or []) - 1)
    land_target = _extra_land_target(day)

    if (
        hour == 0
        and day <= 18
        and extra_land < land_target
        and extra_land < len(LAND_PRICES)
    ):
        land_cost = LAND_PRICES[extra_land]
        herd = sum(owned.values())

        # First expansion only after the herd is actually running and cash has
        # recovered. Second expansion requires a mature herd and still more cash.
        if extra_land == 0:
            allow_land = herd >= 4 and money >= land_cost + 2800
        else:
            allow_land = herd >= 8 and money >= land_cost + 4200

        if allow_land:
            orders.append(["BUY_LAND"])
            money -= land_cost

    if hour <= 1:
        hand_target = _hand_target(day)
        # Never let labour consume the operating runway.
        if money < 450:
            hand_target = min(hand_target, 4)
        elif money < 800:
            hand_target = min(hand_target, 6)
        elif money < 1400:
            hand_target = min(hand_target, 8)
        elif money < 2400:
            hand_target = min(hand_target, 9)
        money = _append_hires(
            orders,
            farm,
            money,
            hand_target,
            limit=10,
        )

    # On hour 0, labour/land is the whole mission; avoid crowding out hires.
    if hour == 0:
        return orders[:10]

    # ---- sales ------------------------------------------------------------
    # Town consumes at hour 0,4,8,... after market processing. Selling at the
    # following hour captures the post-consumption price instead of pre-empting it.
    sell_window = (hour % 4 == 1 and hour >= 5)
    endgame = day >= 28
    terminal = day >= 29
    pressure = _shed_total(private) >= 78

    animal_count = sum(counts["animals"].values())
    wheat_reserve = 0 if endgame else max(10, 2 * animal_count + 4)

    sell_candidates = []
    for item in PRODUCTS:
        qty = int(_get(shed, item, 0) or 0)
        if qty <= 0:
            continue

        if item == "WHEAT":
            qty = max(0, qty - wheat_reserve)
            if qty <= 0:
                continue

        px = float(_get(prices, item, BASE_PRICE[item]) or BASE_PRICE[item])
        ratio = px / BASE_PRICE[item]

        sell_qty = 0
        if terminal:
            sell_qty = qty
        elif endgame:
            sell_qty = qty
        elif pressure:
            sell_qty = min(qty, 24)
        elif sell_window:
            if item == "FERTILIZER":
                if ratio >= 0.55:
                    sell_qty = min(qty, 14)
            elif ratio >= 1.08:
                sell_qty = min(qty, 24)
            elif ratio >= 0.82 and demand[item] > 1.0:
                sell_qty = min(qty, 12)
            elif ratio >= 0.95:
                sell_qty = min(qty, 8)

        if sell_qty > 0:
            # Higher cash value first; helps fund same-turn later purchases.
            sell_candidates.append((px * sell_qty, item, sell_qty))

    for _, item, qty in sorted(sell_candidates, reverse=True):
        if len(orders) >= 10:
            break
        orders.append(["SELL", item, int(qty)])
        money += float(_get(prices, item, BASE_PRICE[item]) or BASE_PRICE[item]) * qty

    # Emergency liquidity. Holding inventory while cash is near zero can lock the
    # whole farm out of labour/seed purchases. Sacrifice some WHEAT reserve first.
    already_sell_wheat = any(
        o and o[0] == "SELL" and len(o) > 1 and o[1] == "WHEAT"
        for o in orders
    )
    raw_wheat = int(_get(shed, "WHEAT", 0) or 0)
    if (
        money < 500
        and raw_wheat > 4
        and not already_sell_wheat
        and len(orders) < 10
    ):
        emergency_qty = min(8, raw_wheat - 4)
        if emergency_qty > 0:
            orders.append(["SELL", "WHEAT", emergency_qty])
            money += float(_get(prices, "WHEAT", 25) or 25) * emergency_qty

    if terminal:
        return orders[:10]

    # ---- feed reserve -----------------------------------------------------
    # Bought WHEAT lands directly in the shed. Only buy if our own crop pipeline
    # is not keeping a 2-day operating buffer.
    total_wheat = _stock(private, "WHEAT")
    need_feed_stock = max(8, 2 * animal_count + 4)

    if (
        day <= 28
        and total_wheat < need_feed_stock
        and len(orders) < 10
    ):
        wheat_px = max(1, int(_get(prices, "WHEAT", 25) or 25))
        gap = min(16, need_feed_stock - total_wheat)
        reserve = 650
        affordable = max(0, int((money - reserve) // wheat_px))
        qty = min(gap, affordable)
        if qty > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", qty])
            money -= qty * wheat_px

    # ---- animal investment ------------------------------------------------
    if day <= 17:
        empty_pastures = max(
            0,
            int(counts["structures"].get("PASTURE", 0))
            - int(counts["animals"].get("COW", 0))
            - int(counts["animals"].get("SHEEP", 0)),
        )
        empty_coops = max(
            0,
            int(counts["structures"].get("COOP", 0))
            - int(counts["animals"].get("GOOSE", 0)),
        )

        available_slots = {
            "COW": empty_pastures,
            "SHEEP": empty_pastures,
            "GOOSE": empty_coops,
        }

        deficits = []
        for animal in ANIMAL_ITEMS:
            need = max(0, int(animal_goals.get(animal, 0)) - int(owned.get(animal, 0)))
            if need > 0 and available_slots[animal] > 0:
                deficits.append((need, animal))

        # One order/species per turn, conservative cash runway.
        for need, animal in sorted(deficits, reverse=True):
            if len(orders) >= 10:
                break
            unit = ANIMALS[animal]["cost"]
            reserve = 450 + max(25, int(_get(prices, "WHEAT", 25) or 25)) * (animal_count + 2)
            max_qty = min(2, need, available_slots[animal])
            affordable = max(0, int((money - reserve) // unit))
            qty = min(max_qty, affordable)
            if qty > 0:
                orders.append(["BUY_ANIMAL", animal, qty])
                money -= qty * unit
                animal_count += qty
                if animal in ("COW", "SHEEP"):
                    # Shared pasture capacity.
                    available_slots["COW"] -= qty
                    available_slots["SHEEP"] -= qty
                else:
                    available_slots["GOOSE"] -= qty

    # ---- seeds ------------------------------------------------------------
    # Buy only enough to cover the current dynamic target, in small batches.
    # When cash is weak, preserve runway for labour/animals instead of cycling
    # scarce cash into seed inventory.
    if day <= 25 and (money >= 1000 or day < 3):
        crop_counts = counts["crops"]
        seed_needs = []
        for crop in CROP_ITEMS:
            target = int(crop_targets.get(crop, 0))
            have = int(crop_counts.get(crop, 0)) + int(_get(seeds, crop, 0) or 0)
            need = max(0, target - have)
            if need <= 0:
                continue

            # Don't buy seed too late to have a plausible first harvest.
            if day + CROPS[crop]["first"] >= 30:
                continue

            # Relative shortage first, then cheaper crops.
            frac = need / max(1, target)
            seed_needs.append((frac, -CROPS[crop]["seed"], crop, need))

        for _, _, crop, need in sorted(seed_needs, reverse=True):
            if len(orders) >= 10:
                break

            unit = CROPS[crop]["seed"]
            reserve = 850 if day < 18 else 350
            affordable = max(0, int((money - reserve) // unit))
            qty = min(6, need, affordable)
            if qty > 0:
                orders.append(["BUY_SEED", crop, qty])
                money -= qty * unit

    return orders[:10]


# ---------------------------------------------------------------------------
# Worker scheduler
# ---------------------------------------------------------------------------

def _unit_actions(obs, farm, private, player):
    tiles = _get(farm, "tiles", []) or []
    n = len(tiles)
    day = int(_get(obs, "day", 0) or 0)
    hour = int(_get(obs, "hour", 0) or 0)

    positions = [tuple(_get(farm, "farmer", (0, 0)))] + [
        tuple(p) for p in (_get(farm, "hands", []) or [])
    ]

    invs = list(_get(private, "inventories", []) or [])
    while len(invs) < len(positions):
        invs.append({})

    shed = dict(_get(private, "shed", {}) or {})
    tasks = _build_tasks(obs, farm, private, player)
    actions = [["PASS"] for _ in positions]
    claimed = set()

    planned_shed = Counter({
        "WHEAT": int(_get(shed, "WHEAT", 0) or 0),
        "COW": int(_get(shed, "COW", 0) or 0),
        "SHEEP": int(_get(shed, "SHEEP", 0) or 0),
        "GOOSE": int(_get(shed, "GOOSE", 0) or 0),
    })

    output_items = set(PRODUCTS)

    def free_tasks():
        return [t for t in tasks if t["target"] not in claimed]

    for i, pos in enumerate(positions):
        inv = invs[i] or {}
        at_shed = pos in _shed_cells(n, tiles)

        carried_output = sum(
            int(_get(inv, item, 0) or 0)
            for item in output_items
        )

        # Terminal priority: get inventory into the shed early enough to sell.
        must_return = (
            carried_output >= 8
            or (day >= 28 and hour >= 20 and carried_output > 0)
            or (day >= 29 and hour >= 14 and carried_output > 0)
        )

        if must_return:
            if at_shed:
                actions[i] = ["DROP"]
            else:
                target = _nearest_shed(pos, n, tiles)
                step = _bfs_first_step(tiles, pos, target)
                if step:
                    actions[i] = [step]
            continue

        # Feed animals using carried wheat.
        feeds = [t for t in free_tasks() if t["tag"] == "feed"]
        if feeds and int(_get(inv, "WHEAT", 0) or 0) > 0:
            t = min(
                feeds,
                key=lambda x: (x["priority"], _distance(pos, x["target"])),
            )
            claimed.add(t["target"])
            if pos == t["target"]:
                actions[i] = t["action"]
            else:
                step = _bfs_first_step(tiles, pos, t["target"])
                if step:
                    actions[i] = [step]
            continue

        # Fetch a useful batch of feed.
        if feeds and int(_get(inv, "WHEAT", 0) or 0) == 0 and planned_shed["WHEAT"] > 0:
            if at_shed:
                take = min(6, planned_shed["WHEAT"], max(1, len(feeds)))
                actions[i] = ["PICKUP", "WHEAT", take]
                planned_shed["WHEAT"] -= take
            else:
                target = _nearest_shed(pos, n, tiles)
                step = _bfs_first_step(tiles, pos, target)
                if step:
                    actions[i] = [step]
            continue

        # Place a carried animal.
        carried_animal = next(
            (a for a in ANIMAL_ITEMS if int(_get(inv, a, 0) or 0) > 0),
            None,
        )
        if carried_animal:
            pts = [
                t for t in free_tasks()
                if t["tag"] == f"place_{carried_animal}"
            ]
            if pts:
                t = min(pts, key=lambda x: _distance(pos, x["target"]))
                claimed.add(t["target"])
                if pos == t["target"]:
                    actions[i] = t["action"]
                else:
                    step = _bfs_first_step(tiles, pos, t["target"])
                    if step:
                        actions[i] = [step]
                continue

        # Fetch an animal waiting in the shed when a matching placement exists.
        pickup_animal = None
        for t in sorted(free_tasks(), key=lambda x: x["priority"]):
            if not t["tag"].startswith("place_"):
                continue
            animal = t["requires"]
            if planned_shed[animal] > 0:
                pickup_animal = animal
                break

        if pickup_animal:
            if at_shed:
                actions[i] = ["PICKUP", pickup_animal, 1]
                planned_shed[pickup_animal] -= 1
            else:
                target = _nearest_shed(pos, n, tiles)
                step = _bfs_first_step(tiles, pos, target)
                if step:
                    actions[i] = [step]
            continue

        # Generic task assignment.
        candidates = [
            t for t in free_tasks()
            if t["requires"] is None
        ]

        # On day 29 after hour 18, only harvest/fertilizer/drop work is worth doing.
        if day >= 29 and hour >= 18:
            candidates = [
                t for t in candidates
                if t["tag"].startswith("harvest_")
                or t["tag"] == "collect_fertilizer"
            ]

        if candidates:
            t = min(
                candidates,
                key=lambda x: (
                    x["priority"],
                    _distance(pos, x["target"]),
                    x["target"][1],
                    x["target"][0],
                ),
            )
            claimed.add(t["target"])
            if pos == t["target"]:
                actions[i] = t["action"]
            else:
                step = _bfs_first_step(tiles, pos, t["target"])
                if step:
                    actions[i] = [step]

    return actions


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def agent(obs, config=None):
    try:
        farms = _get(obs, "farms", []) or []
        player = int(_get(obs, "player", 0) or 0)

        if not (0 <= player < len(farms)):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        farm = farms[player]
        private = _get(obs, "private", {}) or {}

        unit = _unit_actions(obs, farm, private, player)

        return {
            "farmer": unit[0] if unit else ["PASS"],
            "hands": unit[1:],
            "market": _market_actions(obs, farm, private, player),
        }

    except Exception:
        farms = _get(obs, "farms", []) or []
        player = int(_get(obs, "player", 0) or 0)
        hand_count = 0
        if 0 <= player < len(farms):
            hand_count = len(_get(farms[player], "hands", []) or [])
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(hand_count)],
            "market": [],
        }


melon_maxxer = agent
