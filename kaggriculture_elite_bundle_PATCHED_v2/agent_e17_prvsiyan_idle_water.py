"""
E17 — E11 exact + conservative idle-hand crop rescue.

E11 itself remains frozen. This candidate only replaces qualifying hand PASS
windows with a short round-trip WATER rescue, then returns the hand to the exact
original tile before native tape work resumes.

Why:
- E11 uses one of 13 complete 719-turn action tapes.
- Only the first two shops select the route at step 144.
- Replay analysis showed materially more PASS than the top sample.
- Existing E11 already contains a conservative farmer-only rescue for unfed animals,
  but no generic idle-hand rescue for a plant that is about to weed.

This wrapper does NOT retime BUY_LAND. Native land purchase and the physical work
after it are coordinated inside the tape; moving only the market order is unsafe.

Activation:
- Days 6..17
- Hours 16..21
- actor is a farm hand, not the farmer
- final E11 action is PASS
- native tape is PASS for the whole round trip
- actor has no queued weed-repair work
- actor carries nothing
- target is a PLANT, not watered today, consecutive_unwatered >= 1
- native tape does not appear to WATER the same tile later that day
- route length <= 7 commands
- actor returns to exact starting tile
"""

from __future__ import annotations

import copy

from elite_runtime import load_agent, call_agent

_BASE = load_agent("prvsiyan_frontier")

_START_STEP = 6 * 24
_STOP_STEP = 18 * 24
_FIRST_HOUR = 16
_LAST_HOUR = 21
_MAX_COMMANDS = 7
_MAX_RESCUES_PER_DAY = 2

_MOVES = {
    "EAST": (1, 0),
    "WEST": (-1, 0),
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
}
_OPPOSITE = {
    "EAST": "WEST",
    "WEST": "EAST",
    "NORTH": "SOUTH",
    "SOUTH": "NORTH",
}

_STATE = {}
_REPORT = {
    "rescue_plans": 0,
    "water_commands": 0,
    "aborts": 0,
    "no_safe_target": 0,
}


def _new_state(step: int):
    return {
        "last": step,
        "day": step // 24,
        "used": 0,
        "task": None,
    }


def _workers(action):
    return [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]


def _hand_command(action, actor: int):
    index = actor - 1
    hands = action.get("hands") or []
    if 0 <= index < len(hands):
        return hands[index] or ["PASS"]
    return ["PASS"]


def _native_hand(tape, step: int, actor: int):
    hands = tape[step].get("hands") or []
    index = actor - 1
    if 0 <= index < len(hands):
        return hands[index] or ["PASS"]
    return ["PASS"]


def _apply_move(pos, command):
    if command and command[0] in _MOVES:
        dx, dy = _MOVES[command[0]]
        return (pos[0] + dx, pos[1] + dy)
    return pos


def _path(start, target, tiles):
    """Match E11's deterministic x-then-y walking convention."""
    x, y = start
    tx, ty = target
    result = []
    legs = (
        ("EAST", 1, 0, max(0, tx - x)),
        ("WEST", -1, 0, max(0, x - tx)),
        ("SOUTH", 0, 1, max(0, ty - y)),
        ("NORTH", 0, -1, max(0, y - ty)),
    )
    for name, dx, dy, count in legs:
        for _ in range(count):
            x += dx
            y += dy
            if not (0 <= y < len(tiles) and 0 <= x < len(tiles[y])):
                return None
            if tiles[y][x] == "LOCKED":
                return None
            result.append([name])
    return result


def _return_path(go):
    return [[_OPPOSITE[command[0]]] for command in reversed(go)]


def _positions(start, commands):
    positions = []
    pos = tuple(start)
    for command in commands:
        positions.append(pos)
        pos = _apply_move(pos, command)
    return positions, pos


def _future_native_water_targets(obs, action, tape, step):
    """Reserve tiles the native tape seems scheduled to WATER later today."""
    farm = obs["farms"][obs["player"]]
    positions = [tuple(farm["farmer"]), *[tuple(p) for p in farm["hands"]]]

    current = _workers(action)
    for actor in range(min(len(positions), len(current))):
        positions[actor] = _apply_move(positions[actor], current[actor])

    reserved = set()
    end = min(((step // 24) + 1) * 24, len(tape))
    for future_step in range(step + 1, end):
        planned = tape[future_step]
        commands = [
            planned.get("farmer") or ["PASS"],
            *(planned.get("hands") or []),
        ]
        for actor in range(min(len(positions), len(commands))):
            command = commands[actor] or ["PASS"]
            if command == ["WATER"]:
                reserved.add(positions[actor])
            positions[actor] = _apply_move(positions[actor], command)
    return reserved


def _safe_pass_window(tape, step: int, actor: int, length: int):
    end = min(((step // 24) + 1) * 24, len(tape))
    if step + length > end:
        return False
    return all(
        _native_hand(tape, s, actor) == ["PASS"]
        for s in range(step, step + length)
    )


def _choose_task(obs, action, base_state, wrapper_state):
    step = int(obs["step"])
    hour = step % 24

    if not (_START_STEP <= step < _STOP_STEP):
        return None
    if not (_FIRST_HOUR <= hour <= _LAST_HOUR):
        return None
    if wrapper_state["used"] >= _MAX_RESCUES_PER_DAY:
        return None

    module_globals = _BASE.__globals__
    policy = module_globals.get("_POLICY")
    if policy is None:
        return None

    tape = policy.tapes[base_state.plan]
    farm = obs["farms"][obs["player"]]
    tiles = farm["tiles"]
    positions = [farm["farmer"], *farm["hands"]]
    inventories = obs["private"]["inventories"]

    reserved = _future_native_water_targets(obs, action, tape, step)

    targets = []
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") != "PLANT":
                continue
            if tile.get("watered_today"):
                continue
            if int(tile.get("consecutive_unwatered", 0) or 0) < 1:
                continue
            if (x, y) in reserved:
                continue
            targets.append((x, y, int(tile.get("yield_units", 0) or 0)))

    if not targets:
        return None

    candidates = []
    workers = _workers(action)

    for actor in range(1, len(positions)):
        if actor >= len(workers) or workers[actor] != ["PASS"]:
            continue
        if base_state.queues.get(actor):
            continue

        inventory = inventories[actor] if actor < len(inventories) else {}
        if any(int(v or 0) > 0 for v in inventory.values()):
            continue

        start = tuple(positions[actor])

        for x, y, yield_units in targets:
            go = _path(start, (x, y), tiles)
            if go is None:
                continue

            commands = go + [["WATER"]] + _return_path(go)

            if len(commands) > _MAX_COMMANDS:
                continue
            if not _safe_pass_window(tape, step, actor, len(commands)):
                continue

            expected, final_pos = _positions(start, commands)
            if final_pos != start:
                continue

            candidates.append(
                (
                    len(commands),
                    -yield_units,
                    actor,
                    y,
                    x,
                    commands,
                    expected,
                )
            )

    if not candidates:
        return None

    _, _, actor, y, x, commands, expected = min(candidates)
    return {
        "step": step,
        "day": step // 24,
        "plan": base_state.plan,
        "actor": actor,
        "target": (x, y),
        "commands": commands,
        "positions": expected,
    }


def _run_task(obs, action, base_state, wrapper_state, task):
    step = int(obs["step"])
    offset = step - task["step"]

    if not 0 <= offset < len(task["commands"]):
        wrapper_state["task"] = None
        return action

    actor = task["actor"]
    farm = obs["farms"][obs["player"]]
    positions = [farm["farmer"], *farm["hands"]]

    if actor >= len(positions):
        wrapper_state["task"] = None
        _REPORT["aborts"] += 1
        return action

    if tuple(positions[actor]) != task["positions"][offset]:
        wrapper_state["task"] = None
        _REPORT["aborts"] += 1
        return action

    if base_state.plan != task["plan"]:
        wrapper_state["task"] = None
        _REPORT["aborts"] += 1
        return action

    if _hand_command(action, actor) != ["PASS"]:
        wrapper_state["task"] = None
        _REPORT["aborts"] += 1
        return action

    command = list(task["commands"][offset])

    if command == ["WATER"]:
        x, y = task["target"]
        tile = farm["tiles"][y][x]

        if (
            not isinstance(tile, dict)
            or tile.get("kind") != "PLANT"
            or tile.get("watered_today")
        ):
            command = ["PASS"]
        else:
            _REPORT["water_commands"] += 1

    result = copy.deepcopy(action)
    hands = list(result.get("hands") or [])
    needed = len(farm["hands"])

    if len(hands) < needed:
        hands.extend([["PASS"] for _ in range(needed - len(hands))])

    hands[actor - 1] = command
    result["hands"] = hands
    return result


def agent(obs, configuration=None):
    # Exact E11 decides first.
    action = call_agent(_BASE, obs, configuration)

    step = int(obs["step"])
    player = int(obs["player"])

    state = _STATE.get(player)

    if state is None or step <= state["last"]:
        state = _STATE[player] = _new_state(step)
    else:
        state["last"] = step
        day = step // 24
        if day != state["day"]:
            state["day"] = day
            state["used"] = 0
            state["task"] = None

    policy = _BASE.__globals__.get("_POLICY")
    if policy is None or player not in policy.players:
        return action

    base_state = policy.players[player]

    task = state.get("task")
    if task is not None and step >= task["step"] + len(task["commands"]):
        state["task"] = None
        task = None

    if task is None:
        task = _choose_task(obs, action, base_state, state)
        if task is not None:
            state["task"] = task
            state["used"] += 1
            _REPORT["rescue_plans"] += 1
        elif (
            _START_STEP <= step < _STOP_STEP
            and _FIRST_HOUR <= step % 24 <= _LAST_HOUR
        ):
            _REPORT["no_safe_target"] += 1

    if task is None:
        return action

    return _run_task(obs, action, base_state, state, task)


agent.telemetry = _REPORT
melon_maxxer = agent
