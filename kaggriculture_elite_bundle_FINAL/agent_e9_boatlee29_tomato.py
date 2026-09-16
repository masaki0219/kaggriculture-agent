"""
E9 — Boatlee v29 + town-conditioned STRAWBERRY -> TOMATO substitution.

Independent implementation of a mechanism supported by public engine logic and
large external experiments:
- preserve the base route/tile/worker schedule;
- when the first three revealed shops imply weak strawberry demand, replace a
  bounded day-11 strawberry cohort with tomato;
- tomato and strawberry are both ongoing crops, so later WATER/HARVEST visits
  remain valid without rerouting workers.

No source from another implementation is copied here.
"""
from elite_runtime import load_agent, call_agent

_BASE = load_agent("boatlee29")
STRAW_SHOPS = {
    "BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"
}

_initialized = False
_swap_limit = 0
_seed_swapped = 0
_plant_swapped = 0

def _get(o, k, d=None):
    return o.get(k, d) if isinstance(o, dict) else getattr(o, k, d)

def _init_gate(obs):
    global _initialized, _swap_limit
    if _initialized:
        return
    day = int(_get(obs, "day", 0) or 0)
    hour = int(_get(obs, "hour", 0) or 0)
    if day < 10:
        return

    shops = list(_get(_get(obs, "town", {}) or {}, "unlocked_shops", []) or [])
    first3 = shops[:3]
    n = sum(s in STRAW_SHOPS for s in first3)

    # Conservative schedule: biggest replacement only when none of the first
    # three shops consume strawberry; a small replacement for one-shop towns.
    _swap_limit = 17 if n == 0 else 4 if n == 1 else 0
    _initialized = True

def _rewrite_seed_orders(market):
    global _seed_swapped
    out = []
    base_len = len(market)

    for order in market:
        if (
            isinstance(order, list)
            and len(order) >= 3
            and order[0] == "BUY_SEED"
            and order[1] == "STRAWBERRY"
            and _seed_swapped < _swap_limit
        ):
            try:
                qty = int(order[2])
            except Exception:
                out.append(order)
                continue

            remaining = _swap_limit - _seed_swapped
            take = min(max(0, qty), remaining)

            if take <= 0:
                out.append(order)
                continue

            # Whole-order replacement costs exactly one slot.
            if take == qty:
                out.append(["BUY_SEED", "TOMATO", take])
                _seed_swapped += take
                continue

            # Partial replacement requires one additional order. Only do this
            # if the base action had a genuinely free market slot. Otherwise
            # leave the base order unchanged rather than evict a later order.
            if base_len < 10:
                out.append(["BUY_SEED", "TOMATO", take])
                out.append(["BUY_SEED", "STRAWBERRY", qty - take])
                _seed_swapped += take
            else:
                out.append(order)
        else:
            out.append(order)

    # This should never truncate a base order. The only possible +1 split above
    # is allowed only when base_len < 10.
    return out[:10]

def _rewrite_unit(a, private, step):
    global _plant_swapped
    if not isinstance(a, list) or len(a) < 2:
        return a

    # Day-11 cohort window. The public schedule's first relevant seed/plant
    # activity begins late day 10; stop after day 12 to avoid touching later cohorts.
    if not (263 <= step < 312):
        return a

    if (
        a[0] == "PLANT"
        and a[1] == "STRAWBERRY"
        and _plant_swapped < min(_swap_limit, _seed_swapped)
    ):
        seeds = _get(private, "seeds", {}) or {}
        if int(_get(seeds, "TOMATO", 0) or 0) > 0:
            _plant_swapped += 1
            return ["PLANT", "TOMATO"]
    return a

def agent(obs, configuration=None):
    _init_gate(obs)
    act = call_agent(_BASE, obs, configuration)
    if not isinstance(act, dict) or _swap_limit <= 0:
        return act

    day = int(_get(obs, "day", 0) or 0)
    hour = int(_get(obs, "hour", 0) or 0)
    step = day * 24 + hour
    private = _get(obs, "private", {}) or {}

    out = dict(act)

    # Seed substitution starts at the day-10 decision point.
    if 240 <= step < 312:
        out["market"] = _rewrite_seed_orders(list(act.get("market", []) or []))

    out["farmer"] = _rewrite_unit(act.get("farmer", ["PASS"]), private, step)
    out["hands"] = [
        _rewrite_unit(a, private, step)
        for a in (act.get("hands", []) or [])
    ]
    return out

melon_maxxer = agent
