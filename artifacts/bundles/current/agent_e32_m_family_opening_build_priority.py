"""
E32 — M-family opening build-priority fix.

This agent uses NO replay action/tape sequence.

It implements policy-level mechanisms inferred from the 2026-09-18
M-family replay corpus:
- opening family: 4H / 2C3S / M6 / W~10
- second land soon after shop 2 (~step 150)
- third land soon after shop 3 (~step 220)
- shop-conditioned herd targets
- shop-conditioned strawberry / tomato / carrot acreage
- wheat as the flexible backbone
- state-based job planning and greedy execution
- live-state market decisions

E23-E27 remain historical experiments.
"""

from __future__ import annotations

from collections import Counter

# ---------- observed family-level constants ----------

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

CROP_INFO = {
    "WHEAT":      {"max_day": 4,  "max_yield": 6, "ongoing": False, "first": 2,  "interval": 0},
    "CARROT":     {"max_day": 3,  "max_yield": 4, "ongoing": False, "first": 2,  "interval": 0},
    "TOMATO":     {"max_day": 8,  "max_yield": 4, "ongoing": True,  "first": 8,  "interval": 1},
    "STRAWBERRY": {"max_day": 10, "max_yield": 4, "ongoing": True,  "first": 10, "interval": 2},
    "MELON":      {"max_day": 12, "max_yield": 6, "ongoing": False, "first": 10, "interval": 0},
}

ANIMAL_COST = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
LAND_PRICES = [1000, 2000, 4000]

# Daily hires inferred from the M-core median.
HANDS_BY_DAY = [
    4,4,6,6,6,6,8,9,9,10,
    11,11,11,11,11,11,11,11,11,11,
    11,11,11,11,11,11,11,11,10,10,
]

# Replay-derived M-family scale trajectory.
# Early days are directly anchored by checkpoint medians:
# step23 ~15.5 crops, step47 ~19.5, step71 ~20, step143 ~20,
# step167 ~33, step215 ~38, step239 ~53, step287 ~58.5.
CROP_TOTAL_BY_DAY = [
    15,19,20,20,20,20,33,35,38,53,
    56,59,59,59,58,58,58,58,58,58,
    57,57,57,57,56,56,56,56,36,7,
]

HERD_TOTAL_BY_DAY = [
    5,5,5,5,5,5,11,11,12,14,
    16,16,16,16,16,17,17,17,17,17,
    16,16,16,16,16,16,16,16,15,12,
]

# Core M opening layout: five NW pastures around the shed.
PASTURE_ORDER = [
    (4,2),(4,3),(2,4),(3,4),(4,4),
    # NE after land 2
    (5,3),(5,4),(6,3),(6,4),(5,2),(6,2),(7,4),(7,3),(7,2),
    # SW after land 3
    (4,5),(3,5),(4,6),(3,6),(2,5),(2,6),(4,7),(3,7),(1,5),(1,6),
    # later spare positions
    (7,5),(6,5),(5,5),(8,4),(4,8),(2,7),(1,7),
]

COOP_ORDER = [
    (1,3),(3,2),(4,1),
    (7,4),(8,3),(9,4),
    (1,5),(2,5),(3,7),(4,8),
]

# Replay-derived NW opening footprint.
# M6 means six melon seeds bought on day 0, NOT six total melon plants.
# By step 71 the M-core median is 12 melon / 6 wheat / 2 strawberry.
MELON_OPENING = [
    (3,1),(4,1),(3,2),(1,3),(3,3),(1,4),
    (4,0),(2,2),(2,3),(1,0),(1,2),(3,0),
]
EARLY_STRAWBERRY_2 = [(1,1),(0,0)]
EARLY_STRAWBERRY_8 = [
    (1,1),(0,3),(0,4),(0,1),(2,0),(0,2),(0,0),(2,1),
]
EARLY_WHEAT_6 = [(0,1),(2,1),(0,3),(0,4),(2,0),(0,2)]

# Shed-access positions observed/used by the engine's standard geometry.
SHED_ACCESS = ((4,4),(5,4),(4,5),(5,5))

MOVE = {"NORTH","SOUTH","EAST","WEST"}
ANIMALS = ("COW","SHEEP","GOOSE")
PRODUCTS = ("MILK","WOOL","EGG","STRAWBERRY","MELON","TOMATO","CARROT","WHEAT","FERTILIZER")

TELEMETRY = {
    "calls": 0,
    "jobs": 0,
    "market_orders": 0,
    "fallbacks": 0,
}


# ---------- generic helpers ----------

def _me(obs):
    return obs["farms"][int(obs["player"])]


def _day_hour(obs):
    return divmod(int(obs.get("step", 0)), 24)


def _quadrant(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


def _dist(a, b):
    return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))


def _step_toward(pos, target):
    x, y = int(pos[0]), int(pos[1])
    tx, ty = int(target[0]), int(target[1])
    dx, dy = tx-x, ty-y
    if dx == 0 and dy == 0:
        return ["PASS"]
    if abs(dx) >= abs(dy):
        return ["EAST" if dx > 0 else "WEST"]
    return ["SOUTH" if dy > 0 else "NORTH"]


def _tile(obs, pos):
    try:
        x, y = int(pos[0]), int(pos[1])
        return _me(obs)["tiles"][y][x]
    except Exception:
        return None


def _unlocked(obs, pos):
    t = _tile(obs, pos)
    return t != "LOCKED"


def _shed_tiles(obs):
    avail = [p for p in SHED_ACCESS if _unlocked(obs, p)]
    return avail or [(4,4)]


def _nearest_shed(obs, pos):
    return min(_shed_tiles(obs), key=lambda p: _dist(pos, p))


def _at_shed(obs, pos):
    return tuple(pos) in set(_shed_tiles(obs))


def _shop_demand(obs):
    """Demand signal used by the learned M-family router.

    The response tables were estimated from the first four revealed shops.
    Later shops must not keep increasing herd/crop targets indefinitely.
    """
    c = Counter()
    shops = list((obs.get("town") or {}).get("unlocked_shops", []) or [])[:4]
    for shop in shops:
        c.update(SHOP_PRODUCTS.get(shop, ()))
    return c


def _count_animals(obs):
    farm = _me(obs)
    private = obs.get("private") or {}
    out = Counter()

    for row in farm.get("tiles") or []:
        for tile in row:
            if isinstance(tile, dict) and tile.get("animal") in ANIMALS:
                out[tile["animal"]] += 1

    shed = private.get("shed") or {}
    for a in ANIMALS:
        out[a] += int(shed.get(a, 0) or 0)

    for inv in private.get("inventories") or []:
        inv = inv or {}
        for a in ANIMALS:
            out[a] += int(inv.get(a, 0) or 0)

    return out


def _count_structures(obs):
    c = Counter()
    for row in _me(obs).get("tiles") or []:
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ("PASTURE","COOP"):
                c[tile["kind"]] += 1
    return c


def _count_crops(obs):
    c = Counter()
    for row in _me(obs).get("tiles") or []:
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                if crop:
                    c[crop] += 1
    return c


def _carried(obs):
    c = Counter()
    for inv in (obs.get("private") or {}).get("inventories") or []:
        c.update(inv or {})
    return c


def _hire_cost(n):
    a, b, total = 1, 1, 0
    for _ in range(max(0, int(n))):
        total += a
        a, b = b, a+b
    return total


# ---------- M-family target policy ----------

def _animal_targets(obs):
    day, _ = _day_hour(obs)
    d = _shop_demand(obs)

    # Opening family is invariant through day5.
    if day < 6:
        return {"COW": 2, "SHEEP": 3, "GOOSE": 0}

    total = HERD_TOTAL_BY_DAY[min(day, len(HERD_TOTAL_BY_DAY)-1)]

    milk = min(4, d.get("MILK", 0))
    wool = min(2, d.get("WOOL", 0))
    egg  = min(4, d.get("EGG", 0))

    raw = {
        "COW": (5, 7, 10, 13, 14)[milk],
        "SHEEP": (3, 10, 15)[wool],
        "GOOSE": (1, 2, 3, 5, 5)[egg],
    }

    # Total herd scale is family-wide; shops only route its composition.
    target = {"COW": 2, "SHEEP": 3, "GOOSE": 0}
    slots = max(0, total - 5)

    while slots > 0:
        choices = []
        for a in ("COW", "SHEEP", "GOOSE"):
            deficit = raw[a] - target[a]
            if deficit > 0:
                bias = 0.20 if a == "COW" else 0.15 if a == "SHEEP" else 0.0
                choices.append((deficit + bias, a))

        if choices:
            _, a = max(choices)
        else:
            a = "COW" if milk >= wool else "SHEEP"

        target[a] += 1
        slots -= 1

    return target

def _crop_targets(obs):
    day, _ = _day_hour(obs)
    d = _shop_demand(obs)

    straw = min(4, d.get("STRAWBERRY", 0))
    carrot = min(4, d.get("CARROT", 0))
    tomato = min(3, d.get("TOMATO", 0))

    strawberry_target = (17,24,29,37,41)[straw]
    carrot_target = (12,18,25,31,36)[carrot]
    tomato_target = (6,11,13,18)[tomato]

    return {
        "MELON": 12 if day <= 8 else 0,
        "STRAWBERRY": strawberry_target if 2 <= day <= 13 else 0,
        "TOMATO": tomato_target if 14 <= day <= 20 else 0,
        "CARROT": carrot_target if 21 <= day <= 27 else 0,
    }


def _desired_structure_positions(obs, targets):
    day, _ = _day_hour(obs)
    unlocked_quads = set(_me(obs).get("unlocked_quadrants") or [])

    # Replay trajectory medians:
    # step71≈5 structures, step215≈12, step287≈16, later≈17.
    if day < 6:
        structure_cap = 5
    elif day < 9:
        structure_cap = 12
    elif day < 12:
        structure_cap = 16
    else:
        structure_cap = 20

    pasture_need = min(targets["COW"] + targets["SHEEP"], structure_cap)
    coop_need = min(targets["GOOSE"], max(0, structure_cap - pasture_need))

    pastures = [
        p for p in PASTURE_ORDER
        if _quadrant(*p) in unlocked_quads and _unlocked(obs, p)
    ][:pasture_need]

    pset = set(pastures)
    coops = [
        p for p in COOP_ORDER
        if p not in pset and _quadrant(*p) in unlocked_quads and _unlocked(obs, p)
    ][:coop_need]

    return pastures, coops

def _crop_order(obs, crop, reserved):
    unlocked = set(_me(obs).get("unlocked_quadrants") or [])
    coords = []

    for y in range(10):
        for x in range(10):
            p = (x,y)
            if _quadrant(x,y) not in unlocked:
                continue
            if p in reserved:
                continue
            if _tile(obs, p) == "LOCKED":
                continue
            coords.append(p)

    qprio = {
        "STRAWBERRY": {"NE":0,"NW":1,"SW":2,"SE":3},
        "TOMATO":     {"SW":0,"NE":1,"NW":2,"SE":3},
        "CARROT":     {"SW":0,"NW":1,"NE":2,"SE":3},
        "WHEAT":      {"SW":0,"NW":1,"NE":2,"SE":3},
    }[crop]

    # Strawberry likes the broad northern/eastern acreage; late crops use SW.
    return sorted(
        coords,
        key=lambda p: (
            qprio[_quadrant(*p)],
            _dist(p, (4,4)) if crop in ("TOMATO","CARROT") else -_dist(p, (4,4)),
            p[1],
            p[0],
        ),
    )


def _desired_crop_map(obs, pasture_positions, coop_positions):
    day, _ = _day_hour(obs)
    targets = _crop_targets(obs)
    reserved = set(pasture_positions) | set(coop_positions)
    desired = {}

    def add_crop(crop, n, order=None):
        current = sum(1 for c in desired.values() if c == crop)
        need = max(0, int(n) - current)
        if need <= 0:
            return

        coords = order if order is not None else _crop_order(obs, crop, reserved)
        for p in coords:
            if need <= 0:
                break
            if p in reserved or p in desired or not _unlocked(obs, p):
                continue
            desired[p] = crop
            need -= 1

    # Keep live ongoing crops unless the policy has explicitly moved past them.
    for y, row in enumerate(_me(obs).get("tiles") or []):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
                continue
            crop = tile.get("crop")
            if crop in ("STRAWBERRY", "TOMATO"):
                desired[(x, y)] = crop

    # The opening is a trajectory, not a day-0 final target.
    # 14-run checkpoint medians:
    # day0: M6 + W9 ~= 15 crops
    # day1: M10 + W9 ~= 19
    # day2: M12 + S2 + W6 ~= 20
    # day3-5: M12 + S8 ~= 20
    if day == 0:
        add_crop("MELON", 6, MELON_OPENING)
        add_crop("WHEAT", 9)
        return desired

    if day == 1:
        add_crop("MELON", 10, MELON_OPENING)
        add_crop("WHEAT", 9)
        return desired

    if day == 2:
        add_crop("MELON", 12, MELON_OPENING)
        add_crop("STRAWBERRY", 2)
        add_crop("WHEAT", 6)
        return desired

    if day <= 5:
        add_crop("MELON", 12, MELON_OPENING)
        add_crop("STRAWBERRY", 8)
        return desired

    total_target = CROP_TOTAL_BY_DAY[min(day, len(CROP_TOTAL_BY_DAY)-1)]

    # Preserve still-live melons during the early expansion, but stop replants
    # after their opening production cycle.
    if day <= 9:
        add_crop("MELON", 12, MELON_OPENING)

    phase_crop = None
    phase_target = 0

    if day <= 13:
        phase_crop = "STRAWBERRY"
        phase_target = min(targets["STRAWBERRY"], total_target)
    elif day <= 20:
        phase_crop = "TOMATO"
        phase_target = min(targets["TOMATO"], total_target)
    elif day <= 27:
        phase_crop = "CARROT"
        phase_target = min(targets["CARROT"], total_target)

    if phase_crop:
        add_crop(phase_crop, phase_target)

    # Wheat is the residual backbone. Stop exactly at the family scale target.
    if day <= 28:
        for p in _crop_order(obs, "WHEAT", reserved):
            if len(desired) >= total_target:
                break
            if p not in desired:
                desired[p] = "WHEAT"

    return desired


# ---------- job planner ----------

def _harvest_ready(tile, day, desired_crop=None):
    if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
        return False
    units = int(tile.get("yield_units", 0) or 0)
    if units <= 0:
        return False

    crop = tile.get("crop")
    info = CROP_INFO.get(crop)
    if not info:
        return True

    age = day - int(tile.get("planted_day", day) or day)

    if info["ongoing"]:
        return True

    # Convert a filler earlier when the policy wants a different crop.
    if desired_crop and desired_crop != crop and age >= info["first"]:
        return True

    if units >= info["max_yield"]:
        return True
    return age >= info["max_day"]


def _ongoing_exhausted(tile, day):
    if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
        return False

    crop = tile.get("crop")
    info = CROP_INFO.get(crop)
    if not info or not info["ongoing"]:
        return False
    if int(tile.get("yield_units", 0) or 0) > 0:
        return False

    age = day - int(tile.get("planted_day", day) or day)
    last_age = info["first"] + info["interval"] * (info["max_yield"] - 1)
    return age >= last_age


def _job(kind, pos, action, priority, need=None):
    return {
        "kind": kind,
        "pos": tuple(pos),
        "action": list(action),
        "priority": float(priority),
        "need": need,
        "taken": False,
    }


def _build_jobs(obs):
    day, hour = _day_hour(obs)
    farm = _me(obs)
    private = obs.get("private") or {}
    seeds = Counter(private.get("seeds") or {})

    animal_targets = _animal_targets(obs)
    pasture_pos, coop_pos = _desired_structure_positions(obs, animal_targets)
    desired_crop = _desired_crop_map(obs, pasture_pos, coop_pos)

    jobs = []

    # 1. Existing tile maintenance and harvest.
    for y, row in enumerate(farm.get("tiles") or []):
        for x, tile in enumerate(row):
            p = (x,y)
            if not isinstance(tile, dict):
                continue

            if tile.get("kind") == "WEED":
                jobs.append(_job("DIG", p, ["DIG"], 1.0))
                continue

            if tile.get("kind") == "PLANT":
                want = desired_crop.get(p)

                if _harvest_ready(tile, day, want):
                    pr = -8.0 if tile.get("crop") == "MELON" else -3.0
                    jobs.append(_job("HARVEST", p, ["HARVEST"], pr))

                if not tile.get("watered_today", False):
                    must = int(tile.get("consecutive_unwatered", 0) or 0) >= 1
                    if day <= 2:
                        pr = -10.0 if must else -4.0
                    else:
                        pr = -5.0 if must else 3.0
                        if tile.get("crop") == "MELON":
                            pr -= 2.0
                    jobs.append(_job("WATER", p, ["WATER"], pr))

                # Use fertilizer mainly where it has leverage.
                crop = tile.get("crop")
                age = day - int(tile.get("planted_day", day) or day)
                fert_ok = int(tile.get("fertilized_until_day", -1) or -1) < day
                if (
                    day >= 9 and day < 28 and fert_ok
                    and crop in ("STRAWBERRY","WHEAT","CARROT")
                    and age in ((9,11,13,15) if crop == "STRAWBERRY" else (2,))
                ):
                    jobs.append(_job(
                        "FERTILIZE", p, ["FERTILIZE"], 6.5,
                        need=("FERTILIZER",1),
                    ))

                if _ongoing_exhausted(tile, day):
                    jobs.append(_job("DIG", p, ["DIG"], 0.5))

            if tile.get("animal") in ANIMALS:
                if not tile.get("fed_today", False):
                    pr = -7.0 if hour >= 16 else -1.0
                    jobs.append(_job("FEED", p, ["FEED"], pr, need=("WHEAT",1)))

                if not tile.get("cared_today", False):
                    jobs.append(_job("CARE", p, ["CARE"], 4.0 if day <= 2 else 1.5))

                if tile.get("fertilizer_available"):
                    jobs.append(_job("COLLECT", p, ["COLLECT_FERTILIZER"], 4.0))

                if int(tile.get("yield_units", 0) or 0) > 0:
                    jobs.append(_job("HARVEST_ANIMAL", p, ["HARVEST"], 1.0))

    # 2. Build toward the herd target gradually. The prior version emitted every
    # missing structure at once and starved crop work.
    build_slots = 2

    for p in pasture_pos:
        tile = _tile(obs, p)
        if tile is None and build_slots > 0:
            jobs.append(_job("BUILD_PASTURE", p, ["BUILD_PASTURE"], -12.0 if day <= 2 else -6.0))
            build_slots -= 1
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            jobs.append(_job("DIG", p, ["DIG"], -7.0))

    for p in coop_pos:
        tile = _tile(obs, p)
        if tile is None and build_slots > 0:
            jobs.append(_job("BUILD_COOP", p, ["BUILD_COOP"], -5.0))
            build_slots -= 1
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            jobs.append(_job("DIG", p, ["DIG"], -6.0))

    # 3. Place purchased animals into empty structures.
    #
    # E29/E30 emitted TWO mutually-exclusive jobs for every empty pasture.
    # During day0..2 E31 emits exactly one placement job per empty pasture.
    if day <= 2:
        owned = _count_animals(obs)
        placed = Counter()
        for row in farm.get("tiles") or []:
            for tile in row:
                if isinstance(tile, dict) and tile.get("animal") in ANIMALS:
                    placed[tile["animal"]] += 1

        remaining_to_place = {
            "COW": max(0, min(2, owned["COW"]) - placed["COW"]),
            "SHEEP": max(0, min(3, owned["SHEEP"]) - placed["SHEEP"]),
            "GOOSE": max(0, owned["GOOSE"] - placed["GOOSE"]),
        }

        for y, row in enumerate(farm.get("tiles") or []):
            for x, tile in enumerate(row):
                if not isinstance(tile, dict) or tile.get("animal"):
                    continue

                if tile.get("kind") == "PASTURE":
                    animal = None
                    if remaining_to_place["COW"] > 0:
                        animal = "COW"
                    elif remaining_to_place["SHEEP"] > 0:
                        animal = "SHEEP"

                    if animal is not None:
                        jobs.append(_job(
                            "PLACE_"+animal, (x,y), ["PLACE", animal], -8.0,
                            need=(animal,1),
                        ))
                        remaining_to_place[animal] -= 1

                elif tile.get("kind") == "COOP" and remaining_to_place["GOOSE"] > 0:
                    jobs.append(_job(
                        "PLACE_GOOSE", (x,y), ["PLACE","GOOSE"], -8.0,
                        need=("GOOSE",1),
                    ))
                    remaining_to_place["GOOSE"] -= 1

    else:
        for y, row in enumerate(farm.get("tiles") or []):
            for x, tile in enumerate(row):
                if not isinstance(tile, dict):
                    continue
                if tile.get("animal"):
                    continue
                if tile.get("kind") == "PASTURE":
                    d = _shop_demand(obs)
                    first = "COW" if d.get("MILK",0) >= d.get("WOOL",0) else "SHEEP"
                    second = "SHEEP" if first == "COW" else "COW"
                    jobs.append(_job(
                        "PLACE_"+first, (x,y), ["PLACE", first], -5.5,
                        need=(first,1),
                    ))
                    jobs.append(_job(
                        "PLACE_"+second, (x,y), ["PLACE", second], -5.0,
                        need=(second,1),
                    ))
                elif tile.get("kind") == "COOP":
                    jobs.append(_job(
                        "PLACE_GOOSE", (x,y), ["PLACE","GOOSE"], -5.0,
                        need=("GOOSE",1),
                    ))

    # 4. Plant current policy targets on empty tiles.
    if hour <= 21 and day < 28:
        seed_budget = Counter(seeds)

        # Melon / premium crops before wheat.
        if day <= 2:
            crop_pr = {"MELON":-9.5,"STRAWBERRY":-8.0,"TOMATO":-7.5,"CARROT":-7.5,"WHEAT":-8.5}
        else:
            crop_pr = {"MELON":-4.0,"STRAWBERRY":-2.0,"TOMATO":0.0,"CARROT":0.5,"WHEAT":3.0}

        for p, crop in sorted(
            desired_crop.items(),
            key=lambda kv: (crop_pr.get(kv[1], 5.0), kv[0][1], kv[0][0]),
        ):
            tile = _tile(obs, p)
            if tile is not None:
                continue
            if seed_budget.get(crop,0) <= 0:
                continue
            seed_budget[crop] -= 1
            jobs.append(_job("PLANT_"+crop, p, ["PLANT",crop], crop_pr.get(crop,3.0)))

    TELEMETRY["jobs"] += len(jobs)
    return jobs


# ---------- unit executor ----------

def _positions_inventories(obs):
    farm = _me(obs)
    positions = [tuple(farm.get("farmer"))] + [tuple(p) for p in farm.get("hands") or []]
    invs = list((obs.get("private") or {}).get("inventories") or [])
    while len(invs) < len(positions):
        invs.append({})
    return positions, [Counter(x or {}) for x in invs]


def _product_inventory(inv):
    return sum(int(inv.get(x,0) or 0) for x in PRODUCTS)


def _find_job(jobs, pred):
    candidates = [j for j in jobs if not j["taken"] and pred(j)]
    return min(candidates, key=lambda j: (j["priority"], j["pos"])) if candidates else None


def _nearest_job(pos, jobs, pred=lambda j: True):
    candidates = [j for j in jobs if not j["taken"] and pred(j)]
    if not candidates:
        return None
    return min(candidates, key=lambda j: (j["priority"] + 0.75*_dist(pos,j["pos"]), _dist(pos,j["pos"])))


def _unit_action(obs, pos, inv, jobs, shed_budget):
    # A carried animal/feed/fertilizer has a clear destination.
    for animal in ANIMALS:
        if inv.get(animal,0) > 0:
            j = _nearest_job(pos, jobs, lambda x: x["need"] and x["need"][0] == animal)
            if j:
                if pos == j["pos"]:
                    j["taken"] = True
                    return j["action"]
                j["taken"] = True
                return _step_toward(pos, j["pos"])

    if inv.get("WHEAT",0) > 0:
        j = _nearest_job(pos, jobs, lambda x: x["kind"] == "FEED")
        if j:
            if pos == j["pos"]:
                j["taken"] = True
                return ["FEED"]
            j["taken"] = True
            return _step_toward(pos, j["pos"])

    if inv.get("FERTILIZER",0) > 0:
        j = _nearest_job(pos, jobs, lambda x: x["kind"] == "FERTILIZE")
        if j:
            if pos == j["pos"]:
                j["taken"] = True
                return ["FERTILIZE"]
            j["taken"] = True
            return _step_toward(pos, j["pos"])

    # Harvested output goes home before taking unrelated work.
    if _product_inventory(inv) > 0:
        if _at_shed(obs, pos):
            for item in PRODUCTS:
                qty = int(inv.get(item,0) or 0)
                if qty > 0:
                    return ["DROP", item, qty]
        return _step_toward(pos, _nearest_shed(obs, pos))

    # Execute an immediately available job under this unit.
    here = _find_job(jobs, lambda j: j["pos"] == pos and j["need"] is None)
    if here:
        here["taken"] = True
        return here["action"]

    # At shed: pick up the input for the highest-priority outstanding job.
    if _at_shed(obs, pos):
        need_jobs = sorted(
            [j for j in jobs if not j["taken"] and j["need"]],
            key=lambda j: (j["priority"], _dist(pos,j["pos"])),
        )
        for j in need_jobs:
            item, qty = j["need"]
            available = int(shed_budget.get(item,0) or 0)
            if available <= 0:
                continue
            take = min(available, 3 if item == "WHEAT" else qty)
            shed_budget[item] -= take
            return ["PICKUP", item, take]

    # If the best job needs inventory we do not carry, head to the shed.
    best = _nearest_job(pos, jobs)
    if best:
        if best["need"] is not None:
            return _step_toward(pos, _nearest_shed(obs, pos))
        best["taken"] = True
        return _step_toward(pos, best["pos"])

    # Deposit any non-product leftovers rather than wandering.
    if sum(inv.values()) > 0:
        if _at_shed(obs, pos):
            item, qty = next((k,int(v)) for k,v in inv.items() if int(v or 0) > 0)
            return ["DROP", item, qty]
        return _step_toward(pos, _nearest_shed(obs, pos))

    return ["PASS"]


def _unit_actions(obs, jobs):
    positions, invs = _positions_inventories(obs)
    shed_budget = Counter((obs.get("private") or {}).get("shed") or {})

    actions = []
    for pos, inv in zip(positions, invs):
        actions.append(_unit_action(obs, pos, inv, jobs, shed_budget))

    return actions[0], actions[1:]


# ---------- live market policy ----------

def _market_orders(obs):
    step = int(obs.get("step",0))
    day, hour = _day_hour(obs)
    farm = _me(obs)
    private = obs.get("private") or {}
    shed = Counter(private.get("shed") or {})
    seeds = Counter(private.get("seeds") or {})
    prices = (obs.get("market") or {}).get("prices") or {}
    money = float(farm.get("money",0) or 0)

    animals = _count_animals(obs)
    animal_targets = _animal_targets(obs)
    crops = _count_crops(obs)
    structures = _count_structures(obs)
    carried = _carried(obs)

    # ----- replay-inferred staged opening -----
    # This is a policy reconstruction, not a replay tape:
    # common M-family sequence:
    #   step0: WHEAT product 5 + COW1
    #   step1: HIRE4 + COW1 + SHEEP3
    #   rest of day0: MELON seeds bought in 2-unit tranches,
    #                 WHEAT seeds accumulated gradually.
    if step == 0:
        return [
            ["BUY_PRODUCT", "WHEAT", 5],
            ["BUY_ANIMAL", "COW", 1],
        ]

    if step == 1:
        orders = []
        if int(shed.get("WHEAT", 0) or 0) > 0:
            orders.append(["SELL", "WHEAT", 1])
        orders += [["HIRE"] for _ in range(4)]
        orders += [
            ["BUY_ANIMAL", "COW", 1],
            ["BUY_ANIMAL", "SHEEP", 3],
        ]
        return orders[:10]

    orders = []
    sell_candidates = []

    herd = sum(animals[a] for a in ANIMALS)
    wheat_reserve = 0 if day >= 28 else max(2, herd)
    fert_reserve = 0 if day >= 28 else (6 if day >= 10 else 0)

    for item in PRODUCTS:
        have = int(shed.get(item,0) or 0)
        reserve = wheat_reserve if item == "WHEAT" else fert_reserve if item == "FERTILIZER" else 0
        qty = have - reserve
        if qty <= 0:
            continue
        price = float(prices.get(item,0) or 0)
        sell_candidates.append((qty*max(price,1.0), ["SELL",item,qty]))

    sell_candidates.sort(reverse=True, key=lambda x:x[0])

    # E27's expected-cash model was the last version that passed the economic gate.
    cash = money + sum(
        0.8 * o[1][2] * float(prices.get(o[1][1],0) or 0)
        for o in sell_candidates
    )

    buys = []

    # E30: early workforce is a realized-state target.
    if hour <= 2 and day < len(HANDS_BY_DAY):
        target = HANDS_BY_DAY[day]
        if day <= 2:
            current = len(farm.get("hands") or [])
            n = max(0, target-current)
            if n > 0:
                buys.extend([["HIRE"] for _ in range(n)])
                already = int(farm.get("hires_today",0) or 0)
                est = _hire_cost(already+n) - _hire_cost(already)
                cash = max(0.0, cash-est)
        else:
            already = int(farm.get("hires_today",0) or 0)
            n = min(6, max(0, target-already))
            while n > 0:
                cost = _hire_cost(already+n) - _hire_cost(already)
                if cost <= cash:
                    break
                n -= 1
            if n > 0:
                buys.extend([["HIRE"] for _ in range(n)])
                cash -= _hire_cost(already+n) - _hire_cost(already)

    # Expansion windows inferred from the current M population.
    unlocked = list(farm.get("unlocked_quadrants") or [])
    if len(unlocked) == 1 and step >= 150:
        price = LAND_PRICES[0]
        if cash >= price:
            buys.append(["BUY_LAND"])
            cash -= price
    elif len(unlocked) == 2 and step >= 220:
        price = LAND_PRICES[1]
        if cash >= price:
            buys.append(["BUY_LAND"])
            cash -= price

    # Keep enough feed in live state.
    wheat_have = int(shed.get("WHEAT",0) or 0) + int(carried.get("WHEAT",0) or 0)
    wheat_need = max(0, herd - wheat_have)
    if day < 29 and wheat_need > 0:
        buy_price = float(prices.get("WHEAT",25) or 25) + 3
        n = min(wheat_need, int(cash // max(1,buy_price)))
        if n > 0:
            buys.append(["BUY_PRODUCT","WHEAT",n])
            cash -= n*buy_price

    # One animal per turn toward the routed herd composition.
    pasture_capacity = structures["PASTURE"]
    coop_capacity = structures["COOP"]
    pasture_animals = animals["COW"] + animals["SHEEP"]

    deficits = []
    for animal in ("COW","SHEEP","GOOSE"):
        want = max(0, animal_targets[animal] - animals[animal])
        if want <= 0 or day > 16:
            continue
        deficits.append((want, animal))

    deficits.sort(reverse=True)
    for _, animal in deficits:
        if animal in ("COW","SHEEP"):
            room = max(0, pasture_capacity + 1 - pasture_animals)
        else:
            room = max(0, coop_capacity + 1 - animals["GOOSE"])

        if room <= 0 or cash < ANIMAL_COST[animal]:
            continue

        buys.append(["BUY_ANIMAL", animal, 1])
        cash -= ANIMAL_COST[animal]
        break

    # ----- staged crop capital -----
    # Buy only toward today's replay-derived footprint.
    pasture_pos, coop_pos = _desired_structure_positions(obs, animal_targets)
    desired = _desired_crop_map(obs, pasture_pos, coop_pos)
    desired_counts = Counter(desired.values())

    # Early opening batches mirror the family-wide cashflow pattern.
    if day == 0:
        priorities = ("MELON", "WHEAT")
        batch = {"MELON": 2, "WHEAT": 2}
    elif day == 1:
        priorities = ("MELON", "WHEAT")
        batch = {"MELON": 2, "WHEAT": 2}
    elif day == 2:
        priorities = ("MELON", "STRAWBERRY", "WHEAT")
        batch = {"MELON": 2, "STRAWBERRY": 1, "WHEAT": 2}
    elif day <= 13:
        priorities = ("STRAWBERRY", "WHEAT", "MELON")
        batch = {"STRAWBERRY": 2, "WHEAT": 4, "MELON": 2}
    elif day <= 20:
        priorities = ("TOMATO", "WHEAT", "STRAWBERRY")
        batch = {"TOMATO": 2, "WHEAT": 4, "STRAWBERRY": 1}
    else:
        priorities = ("CARROT", "WHEAT", "TOMATO")
        batch = {"CARROT": 3, "WHEAT": 4, "TOMATO": 1}

    for crop in priorities:
        if crop not in SEED_COST or len(buys) >= 10:
            continue
        want = int(desired_counts.get(crop,0))
        have = int(crops.get(crop,0)) + int(seeds.get(crop,0))
        deficit = max(0, want-have)
        if deficit <= 0:
            continue

        reserve = 7 if day == 0 else 0
        spendable = max(0.0, cash - reserve)
        n = min(deficit, batch.get(crop,1), int(spendable // SEED_COST[crop]))
        if n <= 0:
            continue

        buys.append(["BUY_SEED",crop,n])
        cash -= n*SEED_COST[crop]

    # Sales go first so their proceeds can fund later market orders.
    buys = buys[:10]
    sell_slots = max(0, 10-len(buys))
    sells = [x[1] for x in sell_candidates[:sell_slots]]

    TELEMETRY["market_orders"] += len(sells)+len(buys)
    return (sells+buys)[:10]


# ---------- entrypoint ----------

def agent(observation, configuration=None):
    TELEMETRY["calls"] += 1
    try:
        jobs = _build_jobs(observation)
        farmer, hands = _unit_actions(observation, jobs)
        market = _market_orders(observation)
        return {
            "farmer": farmer,
            "hands": hands,
            "market": market,
        }
    except Exception:
        TELEMETRY["fallbacks"] += 1
        farm = _me(observation)
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in farm.get("hands") or []],
            "market": [],
        }


melon_maxxer = agent
