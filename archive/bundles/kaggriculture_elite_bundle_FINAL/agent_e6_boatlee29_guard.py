"""
E6 — Boatlee v29 + opponent-aware market collision guard.

Public-only signal:
- if shared inventory just rose / price just fell, another seller (or our own
  previous dump) is saturating the book.
- suppress a non-critical premium SELL for a short cooldown, then release on a
  base sell or into a draining/recovering book.

Never evicts a base market order.
"""
from collections import defaultdict
from elite_runtime import load_agent, call_agent

_BASE = load_agent("boatlee29")
PREMIUM = {"MILK", "WOOL", "STRAWBERRY", "FERTILIZER"}
BASE_PRICE = {"MILK": 160, "WOOL": 200, "STRAWBERRY": 120, "FERTILIZER": 100}

_prev_inv = None
_prev_price = None
_pending = defaultdict(int)
_age = defaultdict(int)

def _get(o, k, d=None):
    return o.get(k, d) if isinstance(o, dict) else getattr(o, k, d)

def agent(obs, configuration=None):
    global _prev_inv, _prev_price, _pending, _age

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

    mkt = _get(obs, "market", {}) or {}
    inv = dict(_get(mkt, "inventory", {}) or {})
    price = dict(_get(mkt, "prices", {}) or {})

    delta = {x: 0.0 for x in PREMIUM}
    pdelta = {x: 0.0 for x in PREMIUM}
    if _prev_inv is not None:
        for item in PREMIUM:
            delta[item] = float(inv.get(item, 0) or 0) - float(_prev_inv.get(item, 0) or 0)
            pdelta[item] = float(price.get(item, 0) or 0) - float(_prev_price.get(item, 0) or 0)

    market = list(act.get("market", []) or [])
    out = []
    released = set()

    for item in list(_pending):
        if _pending[item] > 0:
            _age[item] += 1

    endgame = day >= 27
    pressure = shed_total >= 84
    cash_critical = (
        money < 1500
        or any(
            isinstance(o, list) and o
            and o[0] in {"BUY_ANIMAL", "BUY_LAND", "BUY_PRODUCT"}
            for o in market
        )
    )

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

        # Natural base sell releases held goods without consuming a new slot.
        if _pending[item] > 0:
            out.append(order)
            _pending[item] = 0
            _age[item] = 0
            released.add(item)
            continue

        ratio = float(price.get(item, BASE_PRICE[item]) or BASE_PRICE[item]) / BASE_PRICE[item]
        saturating = delta[item] >= 3 or pdelta[item] <= -3

        if (
            saturating
            and ratio < 1.10
            and not endgame
            and not pressure
            and not cash_critical
        ):
            try:
                qty = max(0, int(order[2]))
            except Exception:
                qty = 0
            _pending[item] = min(100, qty)
            _age[item] = 0
            continue

        out.append(order)

    # Opportunistic release only into a visibly recovering/draining book and
    # only if there is a truly free slot.
    if len(out) < 10:
        for item in PREMIUM:
            if len(out) >= 10:
                break
            if item in released or _pending[item] <= 0:
                continue

            ratio = float(price.get(item, BASE_PRICE[item]) or BASE_PRICE[item]) / BASE_PRICE[item]
            draining = delta[item] <= -2 or pdelta[item] >= 2
            must_flush = endgame or pressure or _age[item] >= 4

            if (draining and ratio >= 0.35) or must_flush:
                have = int(shed.get(item, 0) or 0)
                qty = min(have, int(_pending[item]), 24 if not endgame else 100)
                if qty > 0:
                    out.append(["SELL", item, qty])
                _pending[item] = 0
                _age[item] = 0

    _prev_inv = inv
    _prev_price = price

    act = dict(act)
    act["market"] = out[:10]
    return act

melon_maxxer = agent
