"""
agent_v14.py

Local experimental wrapper over the frozen v12/Seyamalam baseline.

Single hypothesis:
    The fixed COW/SHEEP mix should adapt to the town's publicly revealed demand.

Only animal species is changed. Movement, crop schedule, hiring, land,
market-sale logic, and total planned animal purchases remain the base policy.

Demand model (independently implemented from game mechanics):
- 8 total shop draws.
- 1/8 shop types consumes WOOL (YARN_STORE).
- 3/8 shop types consume MILK
  (PIZZA_SHOP, ICE_CREAM_SHOP, SMOOTHIE_SHOP).
- For undrawn shops, use those prior probabilities.
- Approximate base production value per day:
    COW:   base MILK price 160 / interval 2 = 80
    SHEEP: base WOOL price 200 / interval 3 ~= 66.7
- Only rewrite purchases from day 7 onward, and only when one estimated score
  exceeds the other by at least 10%.

This is a LOCAL DEVELOPMENT wrapper around:
    Seyamalam/Kaggriculture main.py
    SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

from collections import defaultdict, deque
import importlib.util
from pathlib import Path
from typing import Any


_BASE = (
    Path(__file__).resolve().parent
    / "public_agents"
    / "seyamalam"
    / "main.py"
)

TOTAL_SHOPS = 8
ADAPT_FROM_DAY = 7
DECISION_MARGIN = 1.10

MILK_SHOPS = {
    "PIZZA_SHOP",
    "ICE_CREAM_SHOP",
    "SMOOTHIE_SHOP",
}
WOOL_SHOP = "YARN_STORE"

# Approximate no-demand-scarcity production value per animal-day.
COW_BASE_RATE_VALUE = 160.0 / 2.0
SHEEP_BASE_RATE_VALUE = 200.0 / 3.0


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _load_base_agent():
    if not _BASE.exists():
        raise FileNotFoundError(f"Seyamalam public agent not found: {_BASE}")

    spec = importlib.util.spec_from_file_location(
        "_agent14_seyamalam_base",
        _BASE,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {_BASE}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    base = getattr(module, "agent", None)
    if base is None:
        raise AttributeError(f"{_BASE} does not expose agent(obs)")
    return base


_BASE_AGENT = _load_base_agent()


def _step(obs) -> int:
    return int(_get(obs, "day", 0) or 0) * 24 + int(_get(obs, "hour", 0) or 0)


def _demand_scores(obs) -> tuple[float, float]:
    """
    Return (cow_score, sheep_score).

    Observed shops count fully; remaining shop slots contribute their prior
    expected demand. We normalize MILK's expected shop count by 3 because
    three of eight shop types consume MILK, versus one of eight for WOOL.
    """
    town = _get(obs, "town", {}) or {}
    shops = list(_get(town, "unlocked_shops", []) or [])

    drawn = min(TOTAL_SHOPS, len(shops))
    remaining = max(0, TOTAL_SHOPS - drawn)

    observed_milk = sum(shop in MILK_SHOPS for shop in shops)
    observed_wool = sum(shop == WOOL_SHOP for shop in shops)

    expected_milk_shops = observed_milk + remaining * (3.0 / 8.0)
    expected_wool_shops = observed_wool + remaining * (1.0 / 8.0)

    # Relative demand intensity versus the normal eight-draw expectation.
    milk_intensity = expected_milk_shops / 3.0
    wool_intensity = expected_wool_shops / 1.0

    return (
        COW_BASE_RATE_VALUE * milk_intensity,
        SHEEP_BASE_RATE_VALUE * wool_intensity,
    )


def _preferred_species(obs, original: str) -> str:
    day = int(_get(obs, "day", 0) or 0)
    if day < ADAPT_FROM_DAY:
        return original

    cow_score, sheep_score = _demand_scores(obs)

    if cow_score >= sheep_score * DECISION_MARGIN:
        return "COW"
    if sheep_score >= cow_score * DECISION_MARGIN:
        return "SHEEP"
    return original


def _fresh_state():
    return {
        "last_step": -1,
        # Planned base species -> FIFO of rewritten species.
        "pickup_map": {
            "COW": deque(),
            "SHEEP": deque(),
        },
    }


_STATE = {0: _fresh_state(), 1: _fresh_state()}


def _private(obs):
    return _get(obs, "private", {}) or {}


def _shed(obs):
    return _get(_private(obs), "shed", {}) or {}


def _inventories(obs):
    return list(_get(_private(obs), "inventories", []) or [])


def _rewrite_market(action, obs, state):
    market = [list(order) for order in (action.get("market") or [])]
    rebuilt = []

    for order in market:
        if (
            len(order) >= 3
            and order[0] == "BUY_ANIMAL"
            and order[1] in ("COW", "SHEEP")
        ):
            original = str(order[1])
            quantity = max(0, int(order[2]))
            target = _preferred_species(obs, original)

            # One decision per order/observation. This preserves order count
            # and total planned animal quantity.
            for _ in range(quantity):
                state["pickup_map"][original].append(target)

            order[1] = target

        rebuilt.append(order)

    return rebuilt


def _rewrite_units(action, obs, state):
    units = [list(action.get("farmer") or ["PASS"])]
    units.extend(
        list(unit) if isinstance(unit, list) else ["PASS"]
        for unit in (action.get("hands") or [])
    )

    shed = _shed(obs)
    inventories = _inventories(obs)

    for actor, unit in enumerate(units):
        if len(unit) < 2:
            continue

        command = unit[0]
        species = unit[1]

        if command == "PICKUP" and species in ("COW", "SHEEP"):
            original = str(species)
            queue = state["pickup_map"][original]
            target = queue.popleft() if queue else original

            # If a rewritten purchase did not actually land in the shed
            # (cash/capacity failure), do not issue an impossible pickup.
            if target != original and int(shed.get(target, 0) or 0) > 0:
                unit[1] = target

        elif command == "PLACE" and species in ("COW", "SHEEP"):
            # Use the actor's *actual* inventory. This makes placement robust
            # even if a market purchase or pickup failed earlier.
            if actor < len(inventories):
                inv = inventories[actor] or {}
                cows = int(_get(inv, "COW", 0) or 0)
                sheep = int(_get(inv, "SHEEP", 0) or 0)

                if cows > 0 and sheep == 0:
                    unit[1] = "COW"
                elif sheep > 0 and cows == 0:
                    unit[1] = "SHEEP"

        units[actor] = unit

    return units[0], units[1:]


def agent(obs, config=None):
    seat = int(_get(obs, "player", 0) or 0)
    step = _step(obs)

    state = _STATE.setdefault(seat, _fresh_state())
    if step <= state["last_step"]:
        state = _fresh_state()
        _STATE[seat] = state
    state["last_step"] = step

    base_action = _BASE_AGENT(obs)
    if not isinstance(base_action, dict):
        return base_action

    action = dict(base_action)
    action["market"] = _rewrite_market(action, obs, state)
    farmer, hands = _rewrite_units(action, obs, state)
    action["farmer"] = farmer
    action["hands"] = hands
    return action


melon_maxxer = agent
