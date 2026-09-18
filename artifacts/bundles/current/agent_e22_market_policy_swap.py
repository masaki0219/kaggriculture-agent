# E22 — E21 farm/route + aurax market-policy swap
#
# Frozen E21 SHA256: f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2
# Frozen aurax SHA256: e221f4875daff8b03e8f0ec7c86bd3a2a72c0768b049d4c25064abd5301a532b
#
# Keeps E21 through `_ADV_PARENT` and replaces only the final ADV market
# policy with aurax `advance_sales + frontload`.
# Local experiment only; not yet a standalone final-submission bundle.

from __future__ import annotations

from pathlib import Path
import importlib.util
import os
import sys
import uuid

_ROOT = Path(__file__).resolve().parent
_ELITE = _ROOT / "public_agents" / "elite"

_TETSU_NAME = "tetsu_market_v23_current"
_AURAX_NAME = "aurax7_v7_current"

TELEMETRY = {
    "calls": 0,
    "errors": 0,
    "market_changed": 0,
}


def _entrypoint(name):
    base = _ELITE / name
    marker = base / "entrypoint.txt"
    rel = marker.read_text(encoding="utf-8").strip()
    return (base / rel).resolve()


def _load_module(name):
    path = _entrypoint(name)

    for p in (path.parent, path.parent.parent, path.parent.parent.parent, _ROOT):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)

    module_name = f"_e22_{name}_{uuid.uuid4().hex}"
    old = Path.cwd()
    try:
        os.chdir(path.parent)
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        os.chdir(old)


_TETSU = _load_module(_TETSU_NAME)
_AURAX = _load_module(_AURAX_NAME)

# Critical isolation point: parent immediately before E21 final ADV wrapper.
_BASE = _TETSU._ADV_PARENT


def _standard(configuration):
    if configuration is None:
        return True
    try:
        for k, v in (
            ("boardSize", 10),
            ("turnsPerDay", 24),
            ("shedCapacity", 100),
            ("maxMarketOrdersPerTurn", 10),
            ("farmHandCostMult", 1),
        ):
            if configuration.get(k, v) != v:
                return False
        if configuration.get("marketParams", None):
            return False
    except Exception:
        return False
    return True


def _future_market(observation, offset=1):
    try:
        step = int(observation["step"]) + int(offset)
        if step >= 719:
            return None

        players = _TETSU._IMPL.chassis.players
        native = players.get(int(observation["player"])) if isinstance(players, dict) else None
        route = 2 if step >= 648 else (native or {}).get("route")
        if route is None:
            return None

        action = _TETSU._IMPL.chassis.routes[route][step]
        return action.get("market") if isinstance(action, dict) else None
    except Exception:
        return None


def _update_race_state(observation, action):
    try:
        player = int(observation["player"])
        step = int(observation["step"])
        st = _TETSU._RACE_STATE.get(player)
        if (
            st is not None
            and st.get("prev_action") is not None
            and st.get("step") == step
        ):
            st["prev_action"] = action
    except Exception:
        pass


def agent(observation, configuration=None):
    action = _BASE(observation, configuration)
    TELEMETRY["calls"] += 1

    try:
        if isinstance(action, dict) and _standard(configuration):
            market = action.get("market")
            market = list(market) if isinstance(market, list) else []

            new_market = _AURAX.advance_sales(
                observation,
                market,
                _future_market,
                TELEMETRY,
            )

            if len(new_market) > 1:
                new_market = _AURAX.frontload(
                    observation,
                    new_market,
                    None,
                    TELEMETRY,
                )

            if new_market != market:
                action = dict(action)
                action["market"] = new_market
                TELEMETRY["market_changed"] += 1

        _update_race_state(observation, action)

    except Exception:
        TELEMETRY["errors"] += 1
        _update_race_state(observation, action)

    return action


melon_maxxer = agent
