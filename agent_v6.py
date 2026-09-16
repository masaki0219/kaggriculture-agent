from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

MELON_SEED_COST = CROPS["MELON"]["seed"]
MELON_MAX_YIELD_DAY = CROPS["MELON"]["max_yield_day"]

SELL_THRESHOLD = 200
MELON_BONUS_WATER_START_DAY = MELON_MAX_YIELD_DAY // 2

# v6: do not fill every available tile with melons.
# Adjust the active melon target using current market price and
# the opponent's visible melon supply.
MELON_TARGET_MIN = 8
MELON_TARGET_BASE = 10
MELON_TARGET_MAX = 12


def _step_toward(fx, fy, tx, ty):
    if fx > tx:
        return "WEST"
    if fx < tx:
        return "EAST"
    if fy > ty:
        return "NORTH"
    if fy < ty:
        return "SOUTH"
    return None


def _needs_water(tile, day):
    if tile.get("watered_today", False):
        return False

    planted_day = tile.get("planted_day")
    if planted_day is None:
        return False

    age = day - planted_day

    if age >= MELON_BONUS_WATER_START_DAY:
        return True

    consecutive_unwatered = tile.get("consecutive_unwatered", 0)
    return consecutive_unwatered >= 1


def _count_own_melons(farm):
    count = 0
    for row in farm["tiles"]:
        for tile in row:
            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
                and tile.get("crop") == "MELON"
            ):
                count += 1
    return count


def _count_opponent_melons(obs):
    player = obs.get("player", 0)
    count = 0

    for i, farm in enumerate(obs.get("farms", [])):
        if i == player:
            continue

        for row in farm.get("tiles", []):
            for tile in row:
                if (
                    isinstance(tile, dict)
                    and tile.get("kind") == "PLANT"
                    and tile.get("crop") == "MELON"
                ):
                    count += 1

    return count


def _melon_target(obs):
    market_prices = (obs.get("market", {}) or {}).get("prices", {})
    melon_price = market_prices.get("MELON", 250)

    opponent_melons = _count_opponent_melons(obs)

    # Strong market + little visible competition:
    # allow a few more melon tiles.
    if melon_price >= 300 and opponent_melons <= 5:
        return MELON_TARGET_MAX

    # Weak market or heavy opponent supply:
    # cut melon production.
    if melon_price <= 170 or opponent_melons >= 12:
        return MELON_TARGET_MIN

    if opponent_melons >= 9:
        return MELON_TARGET_BASE - 1

    return MELON_TARGET_BASE


def _find_target_tile(
    farm,
    board_size,
    can_plant,
    day,
):
    fx, fy = farm["farmer"]
    candidates = []

    for y in range(board_size):
        for x in range(board_size):
            tile = farm["tiles"][y][x]

            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
                and tile.get("crop") == "MELON"
            ):
                purpose = None

                planted_day = tile.get("planted_day")
                if planted_day is not None:
                    age = day - planted_day

                    if (
                        age >= MELON_MAX_YIELD_DAY
                        and tile.get("yield_units", 0) > 0
                    ):
                        purpose = "harvest"

                if purpose is None and _needs_water(tile, day):
                    purpose = "water"

                if purpose:
                    candidates.append((x, y, purpose))

            elif tile is None and can_plant:
                candidates.append((x, y, "plant"))

    if not candidates:
        return None

    priority = {
        "harvest": 0,
        "water": 1,
        "plant": 2,
    }

    candidates.sort(
        key=lambda c: (
            priority[c[2]],
            abs(c[0] - fx) + abs(c[1] - fy),
        )
    )

    return candidates[0]


def melon_maxxer(obs):
    farms = obs.get("farms", [])
    player = obs.get("player", 0)
    private = obs.get("private", {}) or {}

    if not farms or player >= len(farms):
        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [],
        }

    farm = farms[player]
    board_size = len(farm["tiles"])
    fx, fy = farm["farmer"]
    tile = farm["tiles"][fy][fx]
    day = obs.get("day", 0)

    seeds = private.get("seeds", {})
    shed = private.get("shed", {})

    market_prices = (obs.get("market", {}) or {}).get("prices", {})
    melon_price = market_prices.get("MELON", 0)

    own_melons = _count_own_melons(farm)
    melon_target = _melon_target(obs)

    # Only plant while below the current target.
    can_plant = (
        own_melons < melon_target
        and seeds.get("MELON", 0) > 0
    )

    market = []

    # Selling logic unchanged from v4.
    melons_in_shed = shed.get("MELON", 0)
    if melons_in_shed > 0 and melon_price >= SELL_THRESHOLD:
        market.append(["SELL", "MELON", melons_in_shed])

    # Only buy another seed when we actually want another melon tile.
    if (
        own_melons < melon_target
        and seeds.get("MELON", 0) == 0
        and farm["money"] >= MELON_SEED_COST
    ):
        market.append(["BUY_SEED", "MELON", 1])

    farmer = ["PASS"]

    if (
        isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == "MELON"
    ):
        planted_day = tile.get("planted_day")
        age = day - planted_day if planted_day is not None else -1

        if (
            age >= MELON_MAX_YIELD_DAY
            and tile.get("yield_units", 0) > 0
        ):
            farmer = ["HARVEST"]

        elif _needs_water(tile, day):
            farmer = ["WATER"]

        else:
            target = _find_target_tile(
                farm,
                board_size,
                can_plant,
                day,
            )

            if target:
                step = _step_toward(
                    fx,
                    fy,
                    target[0],
                    target[1],
                )

                if step:
                    farmer = [step]

    elif tile is None and can_plant:
        farmer = ["PLANT", "MELON"]

    else:
        target = _find_target_tile(
            farm,
            board_size,
            can_plant,
            day,
        )

        if target:
            step = _step_toward(
                fx,
                fy,
                target[0],
                target[1],
            )

            if step:
                farmer = [step]

    return {
        "farmer": farmer,
        "hands": [],
        "market": market,
    }
