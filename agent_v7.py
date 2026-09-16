from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

MELON_SEED_COST = CROPS["MELON"]["seed"]
MELON_MAX_YIELD_DAY = CROPS["MELON"]["max_yield_day"]

WHEAT_SEED_COST = CROPS["WHEAT"]["seed"]
WHEAT_MAX_YIELD_DAY = CROPS["WHEAT"]["max_yield_day"]

MELON_SELL_THRESHOLD = 200

# v7 crop mix
MELON_TARGET = 10
WHEAT_TARGET = 4


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


def _max_yield_day(crop):
    return CROPS[crop]["max_yield_day"]


def _needs_water(tile, day):
    if tile.get("watered_today", False):
        return False

    planted_day = tile.get("planted_day")
    crop = tile.get("crop")

    if planted_day is None or crop not in ("MELON", "WHEAT"):
        return False

    age = day - planted_day
    bonus_start = (_max_yield_day(crop) + 1) // 2

    # During the second half of a one-time crop's growth period,
    # water every day to maximize harvest yield.
    if age >= bonus_start:
        return True

    # Before that, water only when a second consecutive dry day
    # would otherwise occur.
    consecutive_unwatered = tile.get("consecutive_unwatered", 0)
    return consecutive_unwatered >= 1


def _count_crop(farm, crop):
    count = 0
    for row in farm["tiles"]:
        for tile in row:
            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
                and tile.get("crop") == crop
            ):
                count += 1
    return count


def _plant_choice(farm, seeds):
    melon_count = _count_crop(farm, "MELON")
    wheat_count = _count_crop(farm, "WHEAT")

    if melon_count < MELON_TARGET and seeds.get("MELON", 0) > 0:
        return "MELON"

    if wheat_count < WHEAT_TARGET and seeds.get("WHEAT", 0) > 0:
        return "WHEAT"

    return None


def _find_target_tile(farm, board_size, seeds, day):
    fx, fy = farm["farmer"]

    melon_count = _count_crop(farm, "MELON")
    wheat_count = _count_crop(farm, "WHEAT")

    candidates = []

    for y in range(board_size):
        for x in range(board_size):
            tile = farm["tiles"][y][x]

            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
                and tile.get("crop") in ("MELON", "WHEAT")
            ):
                crop = tile["crop"]
                planted_day = tile.get("planted_day")
                purpose = None

                if planted_day is not None:
                    age = day - planted_day

                    if (
                        age >= _max_yield_day(crop)
                        and tile.get("yield_units", 0) > 0
                    ):
                        purpose = "harvest"

                if purpose is None and _needs_water(tile, day):
                    purpose = "water"

                if purpose:
                    candidates.append((x, y, purpose, crop))

            elif tile is None:
                if melon_count < MELON_TARGET and seeds.get("MELON", 0) > 0:
                    candidates.append((x, y, "plant", "MELON"))
                elif wheat_count < WHEAT_TARGET and seeds.get("WHEAT", 0) > 0:
                    candidates.append((x, y, "plant", "WHEAT"))

    if not candidates:
        return None

    # Keep the same broad structure as v4:
    # harvest first, then water, then plant.
    priority = {
        "harvest": 0,
        "water": 1,
        "plant": 2,
    }

    # Within the same task type, choose the nearest target.
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

    melon_count = _count_crop(farm, "MELON")
    wheat_count = _count_crop(farm, "WHEAT")

    market = []

    # Melon selling rule unchanged from v4.
    melons_in_shed = shed.get("MELON", 0)
    if melons_in_shed > 0 and melon_price >= MELON_SELL_THRESHOLD:
        market.append(["SELL", "MELON", melons_in_shed])

    # Wheat is the secondary crop, so realize its value immediately.
    wheat_in_shed = shed.get("WHEAT", 0)
    if wheat_in_shed > 0:
        market.append(["SELL", "WHEAT", wheat_in_shed])

    # Keep enough seed flow to maintain the target mix.
    if (
        melon_count < MELON_TARGET
        and seeds.get("MELON", 0) == 0
        and farm["money"] >= MELON_SEED_COST
    ):
        market.append(["BUY_SEED", "MELON", 1])

    if (
        wheat_count < WHEAT_TARGET
        and seeds.get("WHEAT", 0) == 0
        and farm["money"] >= WHEAT_SEED_COST
    ):
        market.append(["BUY_SEED", "WHEAT", 1])

    farmer = ["PASS"]

    if (
        isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") in ("MELON", "WHEAT")
    ):
        crop = tile["crop"]
        planted_day = tile.get("planted_day")
        age = day - planted_day if planted_day is not None else -1

        if (
            age >= _max_yield_day(crop)
            and tile.get("yield_units", 0) > 0
        ):
            farmer = ["HARVEST"]

        elif _needs_water(tile, day):
            farmer = ["WATER"]

        else:
            target = _find_target_tile(
                farm,
                board_size,
                seeds,
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

    elif tile is None:
        crop_to_plant = _plant_choice(farm, seeds)

        if crop_to_plant:
            farmer = ["PLANT", crop_to_plant]
        else:
            target = _find_target_tile(
                farm,
                board_size,
                seeds,
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

    else:
        target = _find_target_tile(
            farm,
            board_size,
            seeds,
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
