from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

MELON_SEED_COST = CROPS["MELON"]["seed"]
MELON_MAX_YIELD_DAY = CROPS["MELON"]["max_yield_day"]

# Keep v3's selling rule unchanged so this experiment isolates watering logic.
SELL_THRESHOLD = 200

# Before this age, water only when the plant has already gone one day
# without water. From this age onward, water every available day to
# maximize melon yield.
MELON_BONUS_WATER_START_DAY = MELON_MAX_YIELD_DAY // 2


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
    """Return True when this melon should be watered today."""
    if tile.get("watered_today", False):
        return False

    planted_day = tile.get("planted_day")
    if planted_day is None:
        return False

    age = day - planted_day

    # Later growth stage:
    # water every day to maximize final yield.
    if age >= MELON_BONUS_WATER_START_DAY:
        return True

    # Early growth stage:
    # save actions by watering every other day.
    #
    # .get(..., 0) keeps the bot safe even if this field is absent.
    consecutive_unwatered = tile.get("consecutive_unwatered", 0)
    return consecutive_unwatered >= 1


def _find_target_tile(farm, board_size, have_seed, day):
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

            elif tile is None and have_seed:
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

    market = []

    # Sell rule unchanged from v3.
    melons_in_shed = shed.get("MELON", 0)
    if melons_in_shed > 0 and melon_price >= SELL_THRESHOLD:
        market.append(["SELL", "MELON", melons_in_shed])

    # Buy one seed whenever we have none and can afford it.
    if (
        seeds.get("MELON", 0) == 0
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
                seeds.get("MELON", 0) > 0,
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

    elif tile is None and seeds.get("MELON", 0) > 0:
        farmer = ["PLANT", "MELON"]

    else:
        target = _find_target_tile(
            farm,
            board_size,
            seeds.get("MELON", 0) > 0,
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
