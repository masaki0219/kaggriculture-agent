from collections import defaultdict
from elite_runtime import load_agent, call_agent

_BASE = load_agent("prvsiyan_frontier")
_pending = defaultdict(int)
_age = defaultdict(int)
_prev_inv = None
_prev_price = None

BASE_PRICE = {
    "MILK": 160,
    "FERTILIZER": 100,
    "WOOL": 200,
    "STRAWBERRY": 120,
}

def _get(o, k, d=None):
    return o.get(k, d) if isinstance(o, dict) else getattr(o, k, d)

def _public_counts(farm):
    animals = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
    crops = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0}
    for row in _get(farm, "tiles", []) or []:
        for t in row or []:
            if not isinstance(t, dict):
                continue
            a = t.get("animal")
            if a in animals:
                animals[a] += 1
            if t.get("kind") == "PLANT":
                c = t.get("crop")
                if c in crops:
                    crops[c] += 1
    return animals, crops

def _clone_like(obs):
    farms = _get(obs, "farms", []) or []
    player = int(_get(obs, "player", 0) or 0)
    if len(farms) != 2:
        return False
    me = farms[player]
    opp = farms[1-player]

    ma, mc = _public_counts(me)
    oa, oc = _public_counts(opp)

    hand_gap = abs(len(_get(me, "hands", []) or []) - len(_get(opp, "hands", []) or []))
    land_gap = abs(len(_get(me, "unlocked_quadrants", []) or []) - len(_get(opp, "unlocked_quadrants", []) or []))
    animal_gap = sum(abs(ma[k]-oa[k]) for k in ma)
    crop_gap = sum(abs(mc[k]-oc[k]) for k in mc)

    return hand_gap <= 1 and land_gap == 0 and animal_gap <= 2 and crop_gap <= 5

def _overlay(obs, configuration, guarded_items, clone_only=False):
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
    shed_total = sum(
        int(v or 0)
        for v in shed.values()
        if isinstance(v, (int, float))
    )

    mkt = _get(obs, "market", {}) or {}
    inv = dict(_get(mkt, "inventory", {}) or {})
    price = dict(_get(mkt, "prices", {}) or {})

    delta = {x: 0.0 for x in guarded_items}
    pdelta = {x: 0.0 for x in guarded_items}
    if _prev_inv is not None:
        for item in guarded_items:
            delta[item] = float(inv.get(item, 0) or 0) - float(_prev_inv.get(item, 0) or 0)
            pdelta[item] = float(price.get(item, 0) or 0) - float(_prev_price.get(item, 0) or 0)

    market = list(act.get("market", []) or [])
    out = []
    released = set()

    for item in list(_pending):
        if _pending[item] > 0:
            _age[item] += 1

    endgame = day >= 27
    pressure = shed_total >= 88
    cash_critical = (
        money < 1300
        or any(
            isinstance(o, list)
            and o
            and o[0] in {"BUY_ANIMAL", "BUY_LAND", "BUY_PRODUCT"}
            for o in market
        )
    )

    gate = (not clone_only) or (day >= 7 and _clone_like(obs))

    for order in market:
        is_guarded_sell = (
            isinstance(order, list)
            and len(order) >= 3
            and order[0] == "SELL"
            and str(order[1]) in guarded_items
        )

        if not is_guarded_sell:
            out.append(order)
            continue

        item = str(order[1])

        if _pending[item] > 0:
            out.append(order)
            _pending[item] = 0
            _age[item] = 0
            released.add(item)
            continue

        base = BASE_PRICE[item]
        ratio = float(price.get(item, base) or base) / base
        saturating = delta[item] >= 4 or pdelta[item] <= -4

        if (
            gate
            and saturating
            and ratio < 1.08
            and not endgame
            and not pressure
            and not cash_critical
        ):
            try:
                qty = max(0, int(order[2]))
            except Exception:
                qty = 0
            if qty > 0:
                _pending[item] = min(80, qty)
                _age[item] = 0
                continue

        out.append(order)

    if len(out) < 10:
        for item in guarded_items:
            if len(out) >= 10:
                break
            if item in released or _pending[item] <= 0:
                continue

            have = int(shed.get(item, 0) or 0)
            recovering = delta[item] <= -2 or pdelta[item] >= 2
            must_flush = endgame or pressure or _age[item] >= 2

            if recovering or must_flush:
                qty = min(have, int(_pending[item]))
                if qty > 0:
                    out.append(["SELL", item, qty])
                _pending[item] = 0
                _age[item] = 0

    _prev_inv = inv
    _prev_price = price

    act = dict(act)
    act["market"] = out[:10]
    return act

def agent(obs, configuration=None):
    return _overlay(obs, configuration, {"MILK"}, clone_only=False)
melon_maxxer = agent
