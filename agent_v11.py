"""Kaggriculture v11-market

Market-aware scaled livestock baseline.

Changes from v10:
- LOCKED cells are passable for movement, matching the official engine;
- stop unconditional MILK/WOOL dumping;
- hold premium animal products when prices are depressed;
- sell under shed pressure so inventory does not overflow;
- force liquidation in the endgame.

No new land or crop type is added yet.  This isolates routing correctness and
shared-market timing before diversification.
"""

from collections import deque


WHEAT_SEED_COST = 10
COW_COST = 400
SHEEP_COST = 500

WHEAT_TARGET = 10
COW_TARGET = 8
SHEEP_TARGET = 6
HAND_TARGET = 8

LAST_ANIMAL_BUY_DAY = 16
LAST_WHEAT_PLANT_DAY = 25
ENDGAME_DUMP_DAY = 28

BASE_PRICE = {
    "WHEAT": 25,
    "MILK": 160,
    "WOOL": 200,
}
PREMIUM_SELL_FLOOR = 0.55
SHED_PRESSURE = 70

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

            # Movement through LOCKED cells is legal in the official engine.
            # Only tile operations are forbidden there.
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
    """Scale only after the fast wheat bootstrap has had time to pay."""
    if day < 4:
        return {"COW": 0, "SHEEP": 0}
    if day < 7:
        return {"COW": 2, "SHEEP": 0}
    if day < 10:
        return {"COW": 4, "SHEEP": 2}
    if day < 13:
        return {"COW": 6, "SHEEP": 4}
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
    # Premium livestock goods have steep glut curves.  Against another
    # livestock-heavy agent, unconditional selling destroys our own price.
    # Wait for recovery unless the shed is getting full or the season is ending.
    milk = int(shed.get("MILK", 0) or 0)
    wool = int(shed.get("WOOL", 0) or 0)
    wheat = int(shed.get("WHEAT", 0) or 0)

    shed_total = sum(
        int(v or 0)
        for v in shed.values()
        if isinstance(v, (int, float))
    )
    pressure = shed_total >= SHED_PRESSURE
    endgame = day >= ENDGAME_DUMP_DAY

    def maybe_sell_premium(item, qty, drip=8):
        if qty <= 0:
            return

        px = int(prices.get(item, BASE_PRICE[item]) or BASE_PRICE[item])
        floor = PREMIUM_SELL_FLOOR * BASE_PRICE[item]

        if endgame or pressure:
            orders.append(["SELL", item, qty])
        elif px >= floor:
            orders.append(["SELL", item, min(qty, drip)])

    maybe_sell_premium("MILK", milk, 8)
    maybe_sell_premium("WOOL", wool, 8)

    # Wheat has a much gentler glut curve and is also required for feeding.
    placed_animals = counts["COW"] + counts["SHEEP"]
    wheat_reserve = (
        0
        if endgame
        else placed_animals + 3
    )

    if wheat > wheat_reserve:
        orders.append([
            "SELL",
            "WHEAT",
            min(wheat - wheat_reserve, 8),
        ])

    # --- LABOUR -----------------------------------------------------------
    # Exact Fibonacci hire schedule.  Eight hands cost 54/day,
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
    # Scale the herd, but never spend the operating runway.  The reserve rises
    # automatically when a strong opponent drives up the wheat price.
    if day <= LAST_ANIMAL_BUY_DAY and counts["EMPTY_PASTURE"] > 0:
        animal_choice = None
        need = 0

        if owned["COW"] < goals["COW"]:
            animal_choice = "COW"
            need = goals["COW"] - owned["COW"]
        elif owned["SHEEP"] < goals["SHEEP"]:
            animal_choice = "SHEEP"
            need = goals["SHEEP"] - owned["SHEEP"]

        if animal_choice is not None and need > 0:
            unit_cost = COW_COST if animal_choice == "COW" else SHEEP_COST
            wheat_px = max(25, int(prices.get("WHEAT", 25) or 25))
            herd_now = (
                owned["COW"]
                + owned["SHEEP"]
            )

            # Protect roughly one feeding round plus a fixed cash buffer.
            operating_reserve = 700 + wheat_px * (herd_now + 2)

            max_qty = min(
                2,
                need,
                counts["EMPTY_PASTURE"],
            )

            affordable = 0
            for qty in range(1, max_qty + 1):
                if money >= qty * unit_cost + operating_reserve:
                    affordable = qty

            if affordable > 0:
                orders.append([
                    "BUY_ANIMAL",
                    animal_choice,
                    affordable,
                ])
                money -= affordable * unit_cost

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

    # A tile can execute only one meaningful field operation per turn.
    # v9 claimed (tag, target), so FEED and HARVEST on the same animal could be
    # assigned to two different workers in the same turn.  Claim by cell.
    claimed_cells = set()

    # Planned pickup bookkeeping prevents all hands asking for the same last item.
    planned_shed = {
        "WHEAT": int(shed.get("WHEAT", 0) or 0),
        "COW": int(shed.get("COW", 0) or 0),
        "SHEEP": int(shed.get("SHEEP", 0) or 0),
    }

    def free_tasks(required=None):
        out = []
        for t in tasks:
            if t["target"] in claimed_cells:
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
            claimed_cells.add(t["target"])

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
                claimed_cells.add(t["target"])

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
            claimed_cells.add(t["target"])

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
