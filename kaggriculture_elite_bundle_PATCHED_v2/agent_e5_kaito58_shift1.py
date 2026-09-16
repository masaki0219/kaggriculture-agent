"""
E5 — Kaito v58 + one-turn premium-sale phase shift.

Only market SELL timing is changed. Unit/farm actions and all non-SELL market
orders remain untouched.

A suppressed premium sell is reintroduced on the next turn if possible. If the
base itself sells that item on the next turn, that order becomes the release,
avoiding duplicate orders and preserving the 10-order budget.
"""
from collections import defaultdict
from elite_runtime import load_agent, call_agent

_BASE = load_agent("kaito58")
PREMIUM = {"MILK", "WOOL", "STRAWBERRY", "FERTILIZER"}
_pending = defaultdict(int)
_age = defaultdict(int)

def _get(o, k, d=None):
    return o.get(k, d) if isinstance(o, dict) else getattr(o, k, d)

def agent(obs, configuration=None):
    global _pending, _age
    act = call_agent(_BASE, obs, configuration)
    if not isinstance(act, dict):
        return act

    day = int(_get(obs, "day", 0) or 0)
    player = int(_get(obs, "player", 0) or 0)
    farms = _get(obs, "farms", []) or []
    farm = farms[player] if 0 <= player < len(farms) else {}
    money = float(_get(farm, "money", 0) or 0)

    private = _get(obs, "private", {}) or {}
    shed = _get(private, "shed", {}) or {}
    shed_total = sum(int(v or 0) for v in shed.values()
                     if isinstance(v, (int, float)))

    market = list(act.get("market", []) or [])
    out = []
    released = set()

    cash_critical = (
        money < 1600
        or any(
            isinstance(o, list) and o
            and o[0] in {"BUY_ANIMAL", "BUY_LAND", "BUY_PRODUCT"}
            for o in market
        )
    )
    pressure = shed_total >= 82
    endgame = day >= 27
    safe_to_delay = not cash_critical and not pressure and not endgame

    for item in list(_pending):
        if _pending[item] > 0:
            _age[item] += 1

    for order in market:
        is_sell = (
            isinstance(order, list)
            and len(order) >= 3
            and order[0] == "SELL"
            and str(order[1]) in PREMIUM
        )

        if not is_sell:
            out.append(order)
            continue

        item = str(order[1])

        # A base sell on the following turn is the cleanest possible release:
        # no new market slot and no duplicated request.
        if _pending[item] > 0:
            out.append(order)
            _pending[item] = 0
            _age[item] = 0
            released.add(item)
            continue

        if safe_to_delay:
            try:
                qty = max(0, int(order[2]))
            except Exception:
                qty = 0
            _pending[item] = min(100, qty)
            _age[item] = 0
            continue

        out.append(order)

    # If the base did not naturally sell next turn, release one-turn-old pending
    # only when there is a spare market slot. Never evict a base order.
    if len(out) < 10:
        for item in PREMIUM:
            if len(out) >= 10:
                break
            if item in released or _pending[item] <= 0:
                continue
            if _age[item] < 1 and not endgame:
                continue
            have = int(shed.get(item, 0) or 0)
            qty = min(have, int(_pending[item]))
            if qty > 0:
                out.append(["SELL", item, qty])
            _pending[item] = 0
            _age[item] = 0

    act = dict(act)
    act["market"] = out[:10]
    return act

melon_maxxer = agent
