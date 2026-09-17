"""
E20 — E11 exact + early SW prebuild with native strawberry-seed prefetch.

Hypothesis:
E11's opening is strong, but its third-quadrant / first SW strawberry
development may be too late. Test only that timing while preserving the
selected E11 tape.

Safety:
- never switch E11 plans/tapes;
- infer at most two SW cells that the selected native tape itself will later
  PLANT with STRAWBERRY;
- simulate future native HIREs and day resets when locating those cells;
- buy only the third quadrant early (Day 9-10);
- if no STRAWBERRY seed exists, advance the tape's own next native
  BUY_SEED STRAWBERRY order, then cancel the same quantity later;
- add one temporary hand only AFTER the tape's last native HIRE of that day,
  so all native hand indices remain unchanged;
- use only that appended extra hand;
- hands reset at dawn, so no extra hand survives into the next day;
- after early third-land activation, suppress pre-Day18 native BUY_LAND orders
  that would otherwise become an accidental fourth-land purchase;
- do not touch late fourth-land logic.

This is an E20 A/B candidate, not a promoted replacement.
"""

from __future__ import annotations

from pathlib import Path
import copy
import sys

_BUNDLE = Path(__file__).resolve().parent / "kaggriculture_elite_bundle_PATCHED_v2"
if not _BUNDLE.exists():
    raise FileNotFoundError(f"Elite bundle not found: {_BUNDLE}")
if str(_BUNDLE) not in sys.path:
    sys.path.insert(0, str(_BUNDLE))

from elite_runtime import load_agent, call_agent

_BASE = load_agent("prvsiyan_frontier")

DAY = 24
EARLY_START = 9 * DAY
EARLY_END = 11 * DAY          # Day 9-10 only
NATIVE_SW_SCAN_END = 14 * DAY
SUPPRESS_NATIVE_LAND_END = 18 * DAY
MIN_AFTER_LAND_CASH = 750
THIRD_LAND_COST = 2000
MAX_TARGETS = 2

_STATE = {}
_REPORT = {
    "eligible_games": 0,
    "early_land_requests": 0,
    "early_land_activated": 0,
    "activation_failures": 0,
    "extra_hires": 0,
    "seed_prefetch_requests": 0,
    "seed_prefetch_activated": 0,
    "native_seed_suppressed": 0,
    "no_future_seed_order": 0,
    "preplants": 0,
    "waters": 0,
    "native_land_suppressed": 0,
    "redundant_native_plants_suppressed": 0,
    "no_targets": 0,
    "no_seed": 0,
    "cash_waits": 0,
    "market_full": 0,
}


def _new_state(step):
    return {
        "last": step,
        "eligible_counted": False,
        "targets": None,
        "land_requested": False,
        "land_activated": False,
        "baseline_quadrants": None,
        "activation_failure_counted": False,
        "extra_hired_day": None,
        "seed_prefetch_pending": False,
        "seed_prefetch_before": 0,
        "seed_prefetch_qty": 0,
        "seed_suppress_remaining": 0,
        "pending_plant": None,
        "pending_water": None,
        "done_targets": set(),
    }


def _farm(obs):
    return obs["farms"][int(obs["player"])]


def _quadrant_count(farm):
    value = farm.get("unlocked_quadrants")
    if isinstance(value, (list, tuple, set, dict)):
        return len(value)
    return 0


def _default_spawn(board_size):
    half = board_size // 2
    return (half - 1, half - 1)


def _shed_access_tiles(board_size):
    half = board_size // 2
    return [
        (half - 1, half - 1),
        (half, half - 1),
        (half - 1, half),
        (half, half),
    ]


def _spawn_hand_sim(farmer, hands, board_size):
    """
    Match the engine's _spawn_hand rule:
    least-occupied shed-access tile; NWSE order breaks ties.
    """
    access = _shed_access_tiles(board_size)
    occupants = {tile: 0 for tile in access}
    for pos in [farmer, *hands]:
        pos = tuple(pos)
        if pos in occupants:
            occupants[pos] += 1
    return min(access, key=lambda tile: (occupants[tile], access.index(tile)))


def _move(pos, command):
    x, y = pos
    op = command[0] if command else "PASS"
    if op == "WEST":
        x -= 1
    elif op == "EAST":
        x += 1
    elif op == "NORTH":
        y -= 1
    elif op == "SOUTH":
        y += 1
    return (x, y)


def _step_toward(pos, target):
    x, y = pos
    tx, ty = target
    if x > tx:
        return ["WEST"]
    if x < tx:
        return ["EAST"]
    if y > ty:
        return ["NORTH"]
    if y < ty:
        return ["SOUTH"]
    return None


def _is_sw(pos, board_size):
    half = board_size // 2
    x, y = pos
    return x < half and y >= half


def _native_hires(action):
    return sum(
        1 for order in (action.get("market") or [])
        if order and order[0] == "HIRE"
    )


def _planned_sw_targets(obs, policy, plan):
    """
    Replay only worker geometry from the current observation through the
    selected native tape.

    Crucial details matched to the official engine:
    1) worker actions happen before market orders;
    2) HIRE therefore creates a hand for subsequent turns, not this turn;
    3) new hands spawn on the least-occupied shed-access tile;
    4) all hands disappear at dawn and the main farmer resets to NW shed access.

    We do not simulate crops/economy; this function only identifies coordinates
    where E11's own tape later issues PLANT STRAWBERRY in SW.
    """
    step = int(obs["step"])
    farm = _farm(obs)
    board_size = len(farm.get("tiles") or []) or 10
    farmer = tuple(farm["farmer"])
    hands = [tuple(p) for p in (farm.get("hands") or [])]
    tape = policy.tapes[int(plan)]
    targets = []

    end = min(NATIVE_SW_SCAN_END, len(tape))
    for s in range(step + 1, end):
        action = tape[s]
        commands = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
        positions = [farmer, *hands]

        # Unit actions occur first. Commands for not-yet-existing hands are ignored.
        for i in range(min(len(positions), len(commands))):
            cmd = commands[i] or ["PASS"]
            pos = positions[i]
            if (
                len(cmd) >= 2
                and cmd[0] == "PLANT"
                and cmd[1] == "STRAWBERRY"
                and _is_sw(pos, board_size)
            ):
                if pos not in targets:
                    targets.append(pos)
                    if len(targets) >= MAX_TARGETS:
                        return targets

            new_pos = _move(pos, cmd)
            if i == 0:
                farmer = new_pos
            else:
                hands[i - 1] = new_pos

        # Market runs after unit actions. Native HIREs append hands now.
        for _ in range(_native_hires(action)):
            hands.append(_spawn_hand_sim(farmer, hands, board_size))

        # Engine dawn reset after the last turn of each day.
        if (s + 1) % DAY == 0:
            farmer = _default_spawn(board_size)
            hands = []

    return targets


def _future_native_hire_today(policy, plan, step):
    """
    Extra E19 hand is only appended after E11's final native HIRE of this day.
    That guarantees all existing native hand indices remain unchanged.
    """
    tape = policy.tapes[int(plan)]
    day_end = min(((step // DAY) + 1) * DAY, len(tape))
    for s in range(step, day_end):
        if _native_hires(tape[s]) > 0:
            return True
    return False


def _seed_count(obs):
    seeds = (obs.get("private") or {}).get("seeds") or {}
    return int(seeds.get("STRAWBERRY", 0) or 0)


def _future_native_strawberry_seed_order(policy, plan, step):
    """
    Find E11's own next BUY_SEED STRAWBERRY order.
    We advance exactly that order; we do not invent a new quantity.
    """
    tape = policy.tapes[int(plan)]
    end = min(NATIVE_SW_SCAN_END, len(tape))
    for s in range(step + 1, end):
        for order in (tape[s].get("market") or []):
            if not order or order[0] != "BUY_SEED" or len(order) < 2:
                continue
            if order[1] != "STRAWBERRY":
                continue
            qty = int(order[2]) if len(order) >= 3 else 1
            if qty > 0:
                return s, qty
    return None, 0


def _action_has_strawberry_seed_buy(action):
    for order in (action.get("market") or []):
        if (
            order
            and order[0] == "BUY_SEED"
            and len(order) >= 2
            and order[1] == "STRAWBERRY"
        ):
            return True
    return False


def _suppress_native_strawberry_seed(action, qty):
    """
    Remove up to qty from native BUY_SEED STRAWBERRY orders.
    Return the quantity actually suppressed.
    """
    if qty <= 0:
        return 0
    remaining = int(qty)
    removed = 0
    new_market = []
    for order in (action.get("market") or []):
        if (
            remaining > 0
            and order
            and order[0] == "BUY_SEED"
            and len(order) >= 2
            and order[1] == "STRAWBERRY"
        ):
            current = int(order[2]) if len(order) >= 3 else 1
            take = min(current, remaining)
            current -= take
            remaining -= take
            removed += take
            if current > 0:
                updated = list(order)
                if len(updated) >= 3:
                    updated[2] = current
                else:
                    updated.append(current)
                new_market.append(updated)
            continue
        new_market.append(order)
    action["market"] = new_market
    return removed


def _tile(obs, pos):
    x, y = pos
    tiles = _farm(obs).get("tiles") or []
    if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
        return tiles[y][x]
    return None


def _is_strawberry(tile):
    return (
        isinstance(tile, dict)
        and tile.get("kind") == "PLANT"
        and tile.get("crop") == "STRAWBERRY"
    )


def _has_strawberry_seed(obs):
    seeds = (obs.get("private") or {}).get("seeds") or {}
    return int(seeds.get("STRAWBERRY", 0) or 0) > 0


def _cash(obs):
    try:
        return float(_farm(obs).get("money", 0))
    except Exception:
        return 0.0


def _market_has(action, op):
    return any(order and order[0] == op for order in (action.get("market") or []))


def _remove_all_market(action, op):
    original = list(action.get("market") or [])
    kept = [order for order in original if not (order and order[0] == op)]
    removed = len(original) - len(kept)
    if removed:
        action["market"] = kept
    return removed


def _confirm_pending(obs, state):
    if state["seed_prefetch_pending"]:
        now = _seed_count(obs)
        before = int(state["seed_prefetch_before"])
        if now > before:
            activated = min(int(state["seed_prefetch_qty"]), now - before)
            state["seed_suppress_remaining"] += activated
            _REPORT["seed_prefetch_activated"] += 1
        state["seed_prefetch_pending"] = False

    if state["pending_plant"] is not None:
        pos = state["pending_plant"]
        if _is_strawberry(_tile(obs, pos)):
            _REPORT["preplants"] += 1
            state["done_targets"].add(pos)
        state["pending_plant"] = None

    if state["pending_water"] is not None:
        pos = state["pending_water"]
        tile = _tile(obs, pos)
        if _is_strawberry(tile):
            _REPORT["waters"] += 1
        state["pending_water"] = None


def _choose_target(obs, state):
    targets = state.get("targets") or []
    for pos in targets:
        if not _is_strawberry(_tile(obs, pos)):
            return pos
    # All planted: water the first target if time remains.
    return targets[0] if targets else None


def _overlay(obs, action, state):
    step = int(obs["step"])
    day = step // DAY
    farm = _farm(obs)
    q = _quadrant_count(farm)

    if state["land_requested"] and not state["land_activated"]:
        if (
            state["baseline_quadrants"] is not None
            and q > state["baseline_quadrants"]
        ):
            state["land_activated"] = True
            _REPORT["early_land_activated"] += 1
        elif step >= EARLY_END and not state["activation_failure_counted"]:
            state["activation_failure_counted"] = True
            _REPORT["activation_failures"] += 1

    # After early third-land activation, every pre-Day18 native BUY_LAND would
    # advance to the fourth quadrant. Suppress those duplicates; late logic stays.
    if state["land_activated"] and EARLY_END <= step < SUPPRESS_NATIVE_LAND_END:
        removed = _remove_all_market(action, "BUY_LAND")
        _REPORT["native_land_suppressed"] += removed

    # If E19 successfully advanced E11's own strawberry-seed purchase, cancel
    # the equivalent native quantity when it later appears in the tape.
    if state["seed_suppress_remaining"] > 0:
        removed = _suppress_native_strawberry_seed(
            action, state["seed_suppress_remaining"]
        )
        if removed:
            state["seed_suppress_remaining"] -= removed
            _REPORT["native_seed_suppressed"] += removed

    if not (EARLY_START <= step < EARLY_END):
        return action

    g = _BASE.__globals__
    policy = g.get("_POLICY")
    player = int(obs["player"])
    if policy is None or player not in policy.players:
        return action

    base_state = policy.players[player]
    plan = int(base_state.plan)

    if not state["eligible_counted"]:
        state["eligible_counted"] = True
        _REPORT["eligible_games"] += 1

    if state["targets"] is None:
        state["targets"] = _planned_sw_targets(obs, policy, plan)
        if not state["targets"]:
            _REPORT["no_targets"] += 1

    if not state["targets"]:
        return action

    # Buy SW (third quadrant) early only while still at exactly two quadrants.
    if q == 2 and not state["land_requested"]:
        # Keep a small liquidity buffer after the $2000 third-land purchase.
        if _cash(obs) < THIRD_LAND_COST + MIN_AFTER_LAND_CASH:
            _REPORT["cash_waits"] += 1
            return action
        if len(action.get("market") or []) >= 10:
            _REPORT["market_full"] += 1
            return action
        if _market_has(action, "BUY_LAND"):
            return action
        action.setdefault("market", []).append(["BUY_LAND"])
        state["land_requested"] = True
        state["baseline_quadrants"] = q
        _REPORT["early_land_requests"] += 1
        return action

    if q < 3:
        return action

    target = _choose_target(obs, state)
    if target is None:
        return action

    # Do not hire a hand that cannot plant. If there is no strawberry seed,
    # advance E11's own next native strawberry-seed purchase and wait for the
    # next observation to confirm that the purchase succeeded.
    if not _has_strawberry_seed(obs):
        _REPORT["no_seed"] += 1

        # Parent may already be buying strawberry seed this turn. In that case
        # simply wait; duplicating it would change total resources.
        if _action_has_strawberry_seed_buy(action):
            return action

        if state["seed_prefetch_pending"]:
            return action

        _, qty = _future_native_strawberry_seed_order(policy, plan, step)
        if qty <= 0:
            _REPORT["no_future_seed_order"] += 1
            return action

        if len(action.get("market") or []) >= 10:
            _REPORT["market_full"] += 1
            return action

        action.setdefault("market", []).append(["BUY_SEED", "STRAWBERRY", qty])
        state["seed_prefetch_pending"] = True
        state["seed_prefetch_before"] = _seed_count(obs)
        state["seed_prefetch_qty"] = qty
        _REPORT["seed_prefetch_requests"] += 1
        return action

    native_hands = list(action.get("hands") or [])
    actual_hands = list(farm.get("hands") or [])

    # We can safely append our hand only after all native HIREs for this day.
    # If already appended, it must be exactly one position beyond native commands.
    extra_exists = (
        state["extra_hired_day"] == day
        and len(actual_hands) == len(native_hands) + 1
    )

    if not extra_exists:
        if state["extra_hired_day"] == day:
            # Any geometry mismatch means the safety assumption failed. Do nothing.
            return action
        if _future_native_hire_today(policy, plan, step):
            return action
        if _market_has(action, "HIRE"):
            return action
        if len(action.get("market") or []) >= 10:
            _REPORT["market_full"] += 1
            return action
        action.setdefault("market", []).append(["HIRE"])
        state["extra_hired_day"] = day
        _REPORT["extra_hires"] += 1
        return action

    extra_idx = len(actual_hands) - 1
    extra_pos = tuple(actual_hands[extra_idx])

    hands = list(native_hands)
    hands.append(["PASS"])

    move = _step_toward(extra_pos, target)
    if move is not None:
        hands[-1] = move
        action["hands"] = hands
        return action

    tile = _tile(obs, target)
    if not _is_strawberry(tile):
        if not _has_strawberry_seed(obs):
            _REPORT["no_seed"] += 1
            return action
        hands[-1] = ["PLANT", "STRAWBERRY"]
        state["pending_plant"] = target
        action["hands"] = hands
        return action

    hands[-1] = ["WATER"]
    state["pending_water"] = target
    action["hands"] = hands
    return action


def agent(obs, configuration=None):
    step = int(obs["step"])
    player = int(obs["player"])

    state = _STATE.get(player)
    if state is None or step <= state["last"]:
        state = _STATE[player] = _new_state(step)
    else:
        state["last"] = step

    _confirm_pending(obs, state)

    # Exact E11 call; E19 only overlays the returned action.
    action = call_agent(_BASE, obs, configuration)
    return _overlay(obs, copy.deepcopy(action), state)


agent.telemetry = _REPORT
melon_maxxer = agent
