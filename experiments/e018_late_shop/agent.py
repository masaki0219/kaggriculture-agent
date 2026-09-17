"""
E18 — E11 exact + one conservative late-shop reroute.

Purpose:
E11 selects one of 13 coordinated 719-turn tapes at step 144 from only
the first two unlocked shops. The environment continues unlocking shops every
3 days (default), so later demand information is ignored by the core router.

E18 keeps E11 intact and allows at most ONE later reroute when a newly unlocked
shop forms a shop pair already supported by E11's own SHOP_PLANS library.

Safety gate:
- never invent a new tape;
- target must be one of E11's own 13 plans;
- from ROUTE_STEP through the switch point, current/target tapes must have
  identical farmer actions, hand actions, and all NON-SELL market orders;
- SELL history may differ (that is the market dimension we want to adapt);
- no switching after FINAL_PLAN_STEP;
- E11's own final plan-2 transition remains untouched.

This is deliberately a causal A/B candidate, not a promoted replacement.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Project layout:
#   Kaggle/
#     agent_e18_prvsiyan_late_shop.py   <- this file
#     kaggriculture_elite_bundle_PATCHED_v2/
#       elite_runtime.py
#       public_agents/elite/...
_BUNDLE = Path(__file__).resolve().parent / "kaggriculture_elite_bundle_PATCHED_v2"
if not _BUNDLE.exists():
    raise FileNotFoundError(f"Elite bundle not found: {_BUNDLE}")
if str(_BUNDLE) not in sys.path:
    sys.path.insert(0, str(_BUNDLE))

from elite_runtime import load_agent, call_agent

_BASE = load_agent("prvsiyan_frontier")

_STATE = {}
_REPORT = {
    "new_shop_events": 0,
    "route_candidates": 0,
    "safe_switches": 0,
    "unsafe_rejects": 0,
    "same_plan": 0,
    "no_supported_pair": 0,
}


def _new_state(step, shop_count):
    return {
        "last": step,
        "shop_count": shop_count,
        "switched": False,
        "switch_step": None,
        "from_plan": None,
        "to_plan": None,
    }


def _norm_command(cmd):
    if not cmd:
        return ("PASS",)
    return tuple(cmd)


def _state_signature(action):
    """
    Physical/private-state-affecting signature.
    SELL is intentionally excluded: late-shop rerouting is meant to change
    market strategy while preserving the coordinated farm schedule.
    """
    farmer = _norm_command(action.get("farmer"))
    hands = tuple(_norm_command(x) for x in (action.get("hands") or []))
    market = tuple(
        tuple(order)
        for order in (action.get("market") or [])
        if order and order[0] != "SELL"
    )
    return farmer, hands, market


def _prefix_compatible(tapes, current_plan, target_plan, route_step, step):
    if current_plan == target_plan:
        return True
    current = tapes[current_plan]
    target = tapes[target_plan]
    end = min(step, len(current), len(target))
    for s in range(route_step, end):
        if _state_signature(current[s]) != _state_signature(target[s]):
            return False
    return True


def _latest_supported_target(shops, shop_plans):
    """
    Use the newest shop as genuinely new information.
    Pair it with prior shops in reverse chronological order and reuse E11's
    own learned SHOP_PLANS mapping. No hand-authored shop scoring.
    """
    if len(shops) < 3:
        return None, None

    newest = shops[-1]
    for i in range(len(shops) - 2, -1, -1):
        key = (shops[i], newest)
        if key in shop_plans:
            return shop_plans[key], key
    return None, None


def _maybe_switch(obs, wrapper_state):
    step = int(obs["step"])
    player = int(obs["player"])
    g = _BASE.__globals__

    route_step = int(g.get("ROUTE_STEP", 144))
    final_plan_step = int(g.get("FINAL_PLAN_STEP", 648))

    if not (route_step < step < final_plan_step):
        return
    if wrapper_state["switched"]:
        return

    policy = g.get("_POLICY")
    if policy is None or player not in policy.players:
        return

    base_state = policy.players[player]
    shops = list(obs["town"]["unlocked_shops"])
    count = len(shops)

    if count <= wrapper_state["shop_count"]:
        return

    _REPORT["new_shop_events"] += 1
    wrapper_state["shop_count"] = count

    shop_plans = g.get("SHOP_PLANS", {})
    target, key = _latest_supported_target(shops, shop_plans)

    if target is None:
        _REPORT["no_supported_pair"] += 1
        return

    _REPORT["route_candidates"] += 1
    current = int(base_state.plan)

    if target == current:
        _REPORT["same_plan"] += 1
        return

    tapes = policy.tapes
    if not _prefix_compatible(tapes, current, target, route_step, step):
        _REPORT["unsafe_rejects"] += 1
        return

    # Switch BEFORE exact E11 decides this turn, so all existing E11 overlays
    # see one internally consistent plan.
    base_state.plan = int(target)
    wrapper_state["switched"] = True
    wrapper_state["switch_step"] = step
    wrapper_state["from_plan"] = current
    wrapper_state["to_plan"] = int(target)
    _REPORT["safe_switches"] += 1


def agent(obs, configuration=None):
    step = int(obs["step"])
    player = int(obs["player"])
    shops = list(obs["town"]["unlocked_shops"])

    state = _STATE.get(player)
    if state is None or step <= state["last"]:
        state = _STATE[player] = _new_state(step, len(shops))
    else:
        state["last"] = step

    # Exact E11 initializes _POLICY on its first call. From then on we may
    # safely inspect/alter only the selected plan index.
    if _BASE.__globals__.get("_POLICY") is not None:
        _maybe_switch(obs, state)

    action = call_agent(_BASE, obs, configuration)

    # Keep shop count synchronized even before routing becomes eligible.
    state["shop_count"] = max(state["shop_count"], len(shops))
    return action


agent.telemetry = _REPORT
melon_maxxer = agent
