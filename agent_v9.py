"""Kaggriculture v9-stable

Stabilized livestock baseline.

Changes from v8-core:
- do NOT buy livestock immediately;
- bootstrap with wheat cashflow first;
- stage herd growth over days 4-16;
- require an empty pasture before buying an animal;
- reserve operating cash before livestock purchases;
- account for BUY_PRODUCT wheat in the same-turn budget;
- stage pasture construction with the herd target.

The purpose is stability first: no seed should collapse to near-zero bank.
"""

from collections import deque


WHEAT_SEED_COST = 10
COW_COST = 400
SHEEP_COST = 500

WHEAT_TARGET = 10
COW_TARGET = 3
SHEEP_TARGET = 2
HAND_TARGET = 4

LAST_ANIMAL_BUY_DAY = 16
LAST_WHEAT_PLANT_DAY = 25
ENDGAME_DUMP_DAY = 28

WHEAT_MAX_DAY = 4
WHEAT_MAX_YIELD = 6

PRODUCE_ITEMS = ("MILK", "WOOL")
ANIMAL_ITEMS = ("COW", "SHEEP")

# Lower = more urgent.
P_RESCUE = 0
P_FEED = 1
P_HARVEST = 2
P_CARE = 3
P_WATER = 4
P_PLACE = 5
P_BUILD = 6
P_PLANT = 7
P_DIG = 8

MOVES = (
    ("NORTH", 0, -1),
    ("WEST", -1, 0),
    ("SOUTH", 0, 1),
    ("EAST", 1, 0),
)


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
    queue = deque([source])
    parent = {source: None}
    move_used = {}

    while queue:
        x, y = queue.popleft()

        for name, dx, dy in MOVES:
            nx, ny = x + dx, y + dy

            if not (0 <= nx < n and 0 <= ny < n):
                continue

            nxt = (nx, ny)

            if nxt in parent:
                continue

            if tiles[ny][nx] == "LOCKED":
                continue

            parent[nxt] = (x, y)
            move_used[nxt] = name

            if nxt == target:
                queue.clear()
                break

            queue.append(nxt)

    if target not in parent:
        return None

    cur = target
    while parent[cur] != source:
        cur = parent[cur]
        if cur is None:
            return None

    return move_used[cur]


def _count_farm(farm):
    counts = {
        "WHEAT": 0,
        "COW": 0,
        "SHEEP": 0,
        "PASTURE": 0,
        "EMPTY_PASTURE": 0,
    }

    for row in farm.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue

            kind = tile.get("kind")

            if kind == "PLANT" and tile.get("crop") == "WHEAT":
                counts["WHEAT"] += 1

            elif kind == "PASTURE":
                counts["PASTURE"] += 1
                animal = tile.get("animal")
                if animal in ("COW", "SHEEP"):
                    counts[animal] += 1
                elif not animal:
                    counts["EMPTY_PASTURE"] += 1

    return counts


def _inventory_sum(inventories, item):
    return sum(int((inv or {}).get(item, 0) or 0) for inv in inventories)


def _owned_animals(farm, private):
    counts = _count_farm(farm)
    inventories = list(private.get("inventories", []) or [])
    shed = private.get("shed", {}) or {}

    return {
        "COW": (
            counts["COW"]
            + int(shed.get("COW", 0) or 0)
            + _inventory_sum(inventories, "COW")
        ),
        "SHEEP": (
            counts["SHEEP"]
            + int(shed.get("SHEEP", 0) or 0)
            + _inventory_sum(inventories, "SHEEP")
        ),
    }


def _produce_load(inv):
    return sum(int((inv or {}).get(item, 0) or 0) for item in PRODUCE_ITEMS)


def _all_wheat_stock(private):
    shed = private.get("shed", {}) or {}
    inventories = list(private.get("inventories", []) or [])

    return (
        int(shed.get("WHEAT", 0) or 0)
        + _inventory_sum(inventories, "WHEAT")
    )



def _animal_goals(day):
    """Stage capital-intensive livestock behind the first wheat cash cycle."""
    if day < 4:
        return {"COW": 0, "SHEEP": 0}
    if day < 8:
        return {"COW": 1, "SHEEP": 0}
    if day < 12:
        return {"COW": 2, "SHEEP": 1}
    if day <= LAST_ANIMAL_BUY_DAY:
        return {"COW": COW_TARGET, "SHEEP": SHEEP_TARGET}
    return {"COW": 0, "SHEEP": 0}

def _build_tasks(obs, farm, private):
    day = int(obs.get("day", 0) or 0)
    tiles = farm["tiles"]
    n = len(tiles)

    counts = _count_farm(farm)
    seeds = private.get("seeds", {}) or {}
    shed = private.get("shed", {}) or {}
    inventories = list(private.get("inventories", []) or [])

    available_animals = {
        a: (
            int(shed.get(a, 0) or 0)
            + _inventory_sum(inventories, a)
        )
        for a in ANIMAL_ITEMS
    }

    tasks = []
    empty_cells = []

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

            elif kind == "PLANT" and tile.get("crop") == "WHEAT":
                planted = tile.get("planted_day")
                age = day - planted if planted is not None else 0
                units = int(tile.get("yield_units", 0) or 0)

                ready = (
                    units >= WHEAT_MAX_YIELD
                    or (units > 0 and age > WHEAT_MAX_DAY)
                )

                if ready:
                    tasks.append({
                        "priority": P_HARVEST,
                        "target": (x, y),
                        "action": ["HARVEST"],
                        "requires": None,
                        "tag": "harvest_wheat",
                    })
                else:
                    # Early wheat only needs rescue watering.  From age 2,
                    # daily watering increases final one-time yield.
                    needs_water = (
                        not tile.get("watered_today", False)
                        and age <= WHEAT_MAX_DAY
                        and (
                            age >= 2
                            or int(tile.get("consecutive_unwatered", 0) or 0) >= 1
                        )
                    )

                    if needs_water:
                        pri = (
                            P_RESCUE
                            if int(tile.get("consecutive_unwatered", 0) or 0) >= 1
                            else P_WATER
                        )

                        tasks.append({
                            "priority": pri,
                            "target": (x, y),
                            "action": ["WATER"],
                            "requires": None,
                            "tag": "water_wheat",
                        })

            elif kind == "PASTURE":
                animal = tile.get("animal")

                if not animal:
                    for a in ("COW", "SHEEP"):
                        if available_animals[a] > 0:
                            tasks.append({
                                "priority": P_PLACE,
                                "target": (x, y),
                                "action": ["PLACE", a],
                                "requires": a,
                                "tag": f"place_{a}",
                            })
                            available_animals[a] -= 1
                            break

                elif animal in ("COW", "SHEEP"):
                    if not tile.get("fed_today", False):
                        pri = (
                            P_RESCUE
                            if int(tile.get("consecutive_unfed", 0) or 0) >= 1
                            else P_FEED
                        )
                        tasks.append({
                            "priority": pri,
                            "target": (x, y),
                            "action": ["FEED"],
                            "requires": "WHEAT",
                            "tag": "feed",
                        })

                    units = int(tile.get("yield_units", 0) or 0)
                    harvest_at = 4 if animal == "COW" else 4

                    if units >= harvest_at or (day >= 28 and units > 0):
                        tasks.append({
                            "priority": P_HARVEST,
                            "target": (x, y),
                            "action": ["HARVEST"],
                            "requires": None,
                            "tag": f"harvest_{animal}",
                        })

                    if (
                        tile.get("fed_today", False)
                        and not tile.get("cared_today", False)
                    ):
                        tasks.append({
                            "priority": P_CARE,
                            "target": (x, y),
                            "action": ["CARE"],
                            "requires": None,
                            "tag": "care",
                        })

    # Structures are staged with the herd plan.  v8 built all five on day 0,
    # which consumed early labour before the wheat economy was established.
    goals = _animal_goals(day)
    desired_pastures = goals["COW"] + goals["SHEEP"]
    build_need = max(0, desired_pastures - counts["PASTURE"])

    if build_need > 0:
        shed_cells = _shed_cells(n, tiles)
        empty_cells.sort(
            key=lambda p: min(_distance(p, s) for s in shed_cells)
        )

        for cell in empty_cells[:build_need]:
            tasks.append({
                "priority": P_BUILD,
                "target": cell,
                "action": ["BUILD_PASTURE"],
                "requires": None,
                "tag": "build_pasture",
            })

        empty_cells = empty_cells[build_need:]

    # Then maintain the wheat quota.
    if day <= LAST_WHEAT_PLANT_DAY:
        need_wheat = max(0, WHEAT_TARGET - counts["WHEAT"])
        seed_count = int(seeds.get("WHEAT", 0) or 0)
        plant_n = min(need_wheat, seed_count, len(empty_cells))

        shed_cells = _shed_cells(n, tiles)
        empty_cells.sort(
            key=lambda p: min(_distance(p, s) for s in shed_cells)
        )

        for cell in empty_cells[:plant_n]:
            tasks.append({
                "priority": P_PLANT,
                "target": cell,
                "action": ["PLANT", "WHEAT"],
                "requires": None,
                "tag": "plant_wheat",
            })

    return tasks


def _market_actions(obs, farm, private):
    day = int(obs.get("day", 0) or 0)
    hour = int(obs.get("hour", 0) or 0)

    money = int(farm.get("money", 0) or 0)
    hands = list(farm.get("hands", []) or [])
    hires_today = int(farm.get("hires_today", 0) or 0)

    market = obs.get("market", {}) or {}
    prices = market.get("prices", {}) or {}

    shed = private.get("shed", {}) or {}
    seeds = private.get("seeds", {}) or {}

    counts = _count_farm(farm)
    owned = _owned_animals(farm, private)
    goals = _animal_goals(day)

    orders = []

    # --- SALES ------------------------------------------------------------
    # Sell products already safely in the shed.  Wheat keeps an operating
    # reserve for the herd; milk/wool have town demand and are sold in volume.
    milk = int(shed.get("MILK", 0) or 0)
    wool = int(shed.get("WOOL", 0) or 0)
    wheat = int(shed.get("WHEAT", 0) or 0)

    if milk > 0:
        orders.append(["SELL", "MILK", min(milk, 8)])

    if wool > 0:
        orders.append(["SELL", "WOOL", min(wool, 8)])

    placed_animals = counts["COW"] + counts["SHEEP"]
    wheat_reserve = (
        0
        if day >= ENDGAME_DUMP_DAY
        else placed_animals + 3
    )

    if wheat > wheat_reserve:
        orders.append([
            "SELL",
            "WHEAT",
            min(wheat - wheat_reserve, 8),
        ])

    # --- LABOUR -----------------------------------------------------------
    # Exact Fibonacci hire schedule.  Four hands cost only 1+1+2+3 = 7/day,
    # but still respect the live cash budget.
    if hour <= 2:
        fib = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610)
        current = len(hands)
        desired = max(0, HAND_TARGET - current)
        affordable = 0
        running = 0

        for count in range(desired):
            idx = hires_today + count
            if idx >= len(fib):
                break
            running += fib[idx]
            if running <= money:
                affordable = count + 1
            else:
                break

        if affordable:
            orders.extend([["HIRE"] for _ in range(affordable)])
            money -= sum(fib[hires_today:hires_today + affordable])

    # --- SEEDS ------------------------------------------------------------
    # Cheap wheat bootstrap comes before livestock.
    if day <= LAST_WHEAT_PLANT_DAY:
        wheat_need = max(
            0,
            WHEAT_TARGET
            - counts["WHEAT"]
            - int(seeds.get("WHEAT", 0) or 0),
        )

        if wheat_need > 0:
            qty = min(
                wheat_need,
                max(0, (money - 200) // WHEAT_SEED_COST),
            )
            if qty > 0:
                orders.append(["BUY_SEED", "WHEAT", qty])
                money -= qty * WHEAT_SEED_COST

    # --- FEED -------------------------------------------------------------
    # Feeding is an operating expense and takes precedence over buying another
    # $400-$500 animal.  v8 did not subtract this order from its internal
    # same-turn budget.
    total_wheat = _all_wheat_stock(private)
    unfed = 0
    for row in farm.get("tiles", []):
        for tile in row:
            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PASTURE"
                and tile.get("animal") in ("COW", "SHEEP")
                and not tile.get("fed_today", False)
            ):
                unfed += 1

    feed_gap = max(0, unfed + 2 - total_wheat)

    if feed_gap > 0 and day < 29:
        wheat_px = max(1, int(prices.get("WHEAT", 25) or 25))
        qty = min(feed_gap, 8)
        estimated_cost = qty * wheat_px

        if money >= estimated_cost + 300:
            orders.append(["BUY_PRODUCT", "WHEAT", qty])
            money -= estimated_cost

    # --- LIVESTOCK --------------------------------------------------------
    # Only buy an animal when:
    # 1) its staged target says we need it,
    # 2) an EMPTY PASTURE already exists,
    # 3) at least $1500 remains after the purchase.
    #
    # This intentionally delays herd growth.  The earlier v8 reserve of $150
    # allowed seed-dependent starvation spirals.
    if day <= LAST_ANIMAL_BUY_DAY and counts["EMPTY_PASTURE"] > 0:
        animal_choice = None

        if owned["COW"] < goals["COW"]:
            animal_choice = "COW"
        elif owned["SHEEP"] < goals["SHEEP"]:
            animal_choice = "SHEEP"

        if animal_choice is not None:
            cost = COW_COST if animal_choice == "COW" else SHEEP_COST
            operating_reserve = 1500

            if money >= cost + operating_reserve:
                orders.append(["BUY_ANIMAL", animal_choice, 1])
                money -= cost

    # Final liquidation.
    if day >= ENDGAME_DUMP_DAY:
        remaining_wheat = int(shed.get("WHEAT", 0) or 0)

        # If no earlier WHEAT order was emitted, dump all remaining wheat.
        already_selling_wheat = any(
            o and o[0] == "SELL" and len(o) > 1 and o[1] == "WHEAT"
            for o in orders
        )

        if remaining_wheat > 0 and not already_selling_wheat:
            orders.append(["SELL", "WHEAT", remaining_wheat])

    return orders[:10]


def _unit_actions(obs, farm, private):
    tiles = farm["tiles"]
    n = len(tiles)
    day = int(obs.get("day", 0) or 0)
    hour = int(obs.get("hour", 0) or 0)

    positions = [tuple(farm["farmer"])] + [
        tuple(p) for p in (farm.get("hands", []) or [])
    ]

    inventories = list(private.get("inventories", []) or [])
    while len(inventories) < len(positions):
        inventories.append({})

    shed = dict(private.get("shed", {}) or {})
    tasks = _build_tasks(obs, farm, private)

    actions = [["PASS"] for _ in positions]
    claimed = set()

    # Planned pickup bookkeeping prevents all hands asking for the same last item.
    planned_shed = {
        "WHEAT": int(shed.get("WHEAT", 0) or 0),
        "COW": int(shed.get("COW", 0) or 0),
        "SHEEP": int(shed.get("SHEEP", 0) or 0),
    }

    def task_key(t):
        return (t["tag"], t["target"])

    def free_tasks(required=None):
        out = []
        for t in tasks:
            key = task_key(t)
            if key in claimed:
                continue
            if required is not None and t["requires"] != required:
                continue
            out.append(t)
        return out

    for i, pos in enumerate(positions):
        inv = inventories[i] or {}
        shed_cells = _shed_cells(n, tiles)
        at_shed = pos in shed_cells

        # Ferry output to the shed before it is lost at end-of-day.
        load = _produce_load(inv)
        must_return = (
            load >= 4
            or (day >= ENDGAME_DUMP_DAY and load > 0)
            or (hour >= 22 and load > 0)
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

        # Urgent animal feeding: carriers fetch a few wheat at a time.
        feed_tasks = [
            t for t in free_tasks()
            if t["tag"] == "feed"
        ]

        if feed_tasks and int(inv.get("WHEAT", 0) or 0) > 0:
            t = min(
                feed_tasks,
                key=lambda x: (
                    x["priority"],
                    _distance(pos, x["target"]),
                ),
            )
            claimed.add(task_key(t))

            if pos == t["target"]:
                actions[i] = t["action"]
            else:
                step = _bfs_first_step(tiles, pos, t["target"])
                if step:
                    actions[i] = [step]
            continue

        if (
            feed_tasks
            and int(inv.get("WHEAT", 0) or 0) == 0
            and planned_shed["WHEAT"] > 0
        ):
            if at_shed:
                take = min(3, planned_shed["WHEAT"], len(feed_tasks))
                if take > 0:
                    actions[i] = ["PICKUP", "WHEAT", take]
                    planned_shed["WHEAT"] -= take
                    continue
            else:
                target = _nearest_shed(pos, n, tiles)
                step = _bfs_first_step(tiles, pos, target)
                if step:
                    actions[i] = [step]
                    continue

        # Place purchased animals.
        carried_animal = None
        for a in ANIMAL_ITEMS:
            if int(inv.get(a, 0) or 0) > 0:
                carried_animal = a
                break

        if carried_animal:
            place_tasks = [
                t for t in free_tasks(carried_animal)
                if t["tag"] == f"place_{carried_animal}"
            ]

            if place_tasks:
                t = min(
                    place_tasks,
                    key=lambda x: _distance(pos, x["target"]),
                )
                claimed.add(task_key(t))

                if pos == t["target"]:
                    actions[i] = t["action"]
                else:
                    step = _bfs_first_step(tiles, pos, t["target"])
                    if step:
                        actions[i] = [step]
                continue

        # If a pasture is waiting and an animal is in the shed, fetch it.
        place_tasks = [
            t for t in free_tasks()
            if t["tag"].startswith("place_")
        ]

        pickup_animal = None
        for t in sorted(place_tasks, key=lambda x: x["priority"]):
            a = t["requires"]
            if planned_shed.get(a, 0) > 0:
                pickup_animal = a
                break

        if pickup_animal:
            if at_shed:
                actions[i] = ["PICKUP", pickup_animal, 1]
                planned_shed[pickup_animal] -= 1
                continue
            else:
                target = _nearest_shed(pos, n, tiles)
                step = _bfs_first_step(tiles, pos, target)
                if step:
                    actions[i] = [step]
                    continue

        # Generic work that does not require carried inventory.
        candidates = [
            t for t in free_tasks()
            if t["requires"] is None
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
            claimed.add(task_key(t))

            if pos == t["target"]:
                actions[i] = t["action"]
            else:
                step = _bfs_first_step(tiles, pos, t["target"])
                if step:
                    actions[i] = [step]

    return actions


def agent(obs, config=None):
    try:
        farms = obs.get("farms", []) or []
        player = int(obs.get("player", 0) or 0)

        if not (0 <= player < len(farms)):
            return {
                "farmer": ["PASS"],
                "hands": [],
                "market": [],
            }

        farm = farms[player]
        private = obs.get("private", {}) or {}

        acts = _unit_actions(obs, farm, private)

        return {
            "farmer": acts[0] if acts else ["PASS"],
            "hands": acts[1:],
            "market": _market_actions(obs, farm, private),
        }

    except Exception:
        farms = obs.get("farms", []) if hasattr(obs, "get") else []
        player = int(obs.get("player", 0)) if hasattr(obs, "get") else 0

        hand_count = (
            len(farms[player].get("hands", []) or [])
            if 0 <= player < len(farms)
            else 0
        )

        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in range(hand_count)],
            "market": [],
        }


# Compatibility with the earlier local naming convention.
melon_maxxer = agent
