# E21 vs aurax V7 — Market Policy Diff

- Generated: `2026-09-18T15:29:08+09:00`
- Tetsu/E21: `artifacts/bundles/current/public_agents/elite/tetsu_market_v23_current/raw/_extract_submission_tar/main.py`
- Tetsu SHA256: `f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`
- aurax: `artifacts/bundles/current/public_agents/elite/aurax7_v7_current/raw/_extract_submission_tar/main.py`
- aurax SHA256: `e221f4875daff8b03e8f0ec7c86bd3a2a72c0768b049d4c25064abd5301a532b`
- Whole-file line similarity: **0.916**
- Market-related differing blocks: **19**

Purpose: choose an architecturally complete market-policy block for E22, not add one-off shop/seed patches.

## 1. Ranked market-related block differences

| Rank | Block | Status | Market score | Production score | E21 lines | aurax lines |
|---:|---|---|---:|---:|---:|---:|
| 1 | `FunctionDef:advance_sales#1` | aurax-only | 29 | 2 | — | 3820-3878 |
| 2 | `FunctionDef:frontload#1` | aurax-only | 26 | 0 | — | 3765-3801 |
| 3 | `FunctionDef:agent#28` | changed | 30 | 9 | 3501-3529 | 3463-3477 |
| 4 | `FunctionDef:_adv_apply#1` | tetsu-only | 24 | 0 | 3553-3601 | — |
| 5 | `FunctionDef:_adv_frontload#1` | tetsu-only | 21 | 0 | 3602-3616 | — |
| 6 | `FunctionDef:_race_lost#1` | changed | 17 | 0 | 3409-3435 | 3391-3408 |
| 7 | `FunctionDef:agent#30` | aurax-only | 12 | 3 | — | 3915-3936 |
| 8 | `FunctionDef:_simulate#1` | aurax-only | 11 | 3 | — | 3713-3762 |
| 9 | `FunctionDef:_price#1` | aurax-only | 4 | 0 | — | 3696-3704 |
| 10 | `FunctionDef:_r60_risks#1` | aurax-only | 4 | 0 | — | 3524-3535 |
| 11 | `FunctionDef:agent#29` | changed | 3 | 0 | 3617-3629 | 3604-3617 |
| 12 | `Assign:_V43_OPENING#2` | aurax-only | 4 | 3 | — | 3635-3635 |
| 13 | `Assign:_OPEN_STEP0#1` | tetsu-only | 3 | 2 | 3497-3497 | — |
| 14 | `Assign:_V43_OPENING#1` | aurax-only | 3 | 2 | — | 3629-3629 |
| 15 | `Assign:LOOKAHEAD#1` | aurax-only | 2 | 0 | — | 3816-3816 |
| 16 | `FunctionDef:_future_market#1` | aurax-only | 2 | 0 | — | 3885-3899 |
| 17 | `FunctionDef:_r60_opening_liquidity#1` | aurax-only | 4 | 6 | — | 3496-3516 |
| 18 | `FunctionDef:_adv_future#1` | tetsu-only | 1 | 0 | 3550-3552 | — |
| 19 | `FunctionDef:agent#27` | changed | 1 | 0 | 3451-3484 | 3424-3449 |

## 2. High-value diffs

The following blocks are market-heavy and are the first candidates for E22.

### 1. `FunctionDef:advance_sales#1` — aurax-only

- market_score: **29**
- production_score: **2**

**aurax-only block:**

```python
def advance_sales(obs, market, future_market, telemetry=None, max_orders=10, items=PREMIUM):
    """market: list of orders (already front-loaded or not). future_market: callable(obs) -> next step's tape market list or None.
    Returns a new list (advanced sells prepended) or the original list."""
    try:
        step = int(obs["step"])
        if step % 24 == 23 or step >= 718:
            return market
        nxt = []
        for off in range(1, LOOKAHEAD + 1):
            m_off = future_market(obs, off) if LOOKAHEAD > 1 else future_market(obs)
            if m_off:
                nxt += [o for o in m_off if isinstance(o, (list, tuple)) and o]
        if not nxt:
            return market
        want = {}
        # the parent's sale-credit overlay funds feed purchases from the FIRST order of a turn when it is a
        # non-wheat SELL; advancing that item starves the credit -> leave the first-listed sell alone
        first = next((o for o in nxt if isinstance(o, (list, tuple)) and o), None)
        protected = first[1] if first and len(first) > 2 and first[0] == "SELL" and PROTECT_FIRST else None
        for o in nxt:
            if isinstance(o, (list, tuple)) and len(o) > 2 and o[0] == "SELL" and o[1] in items and o[1] != protected:
                try: want[o[1]] = want.get(o[1], 0) + max(0, int(o[2]))
                except Exception: pass
        if not want:
            return market
        shed = obs["private"]["shed"]
        cur = [list(o) for o in (market or []) if isinstance(o, (list, tuple)) and o]
        selling_now = {}
        for o in cur:
            if len(o) > 2 and o[0] == "SELL":
                try: selling_now[o[1]] = selling_now.get(o[1], 0) + max(0, int(o[2]))
                except Exception: pass
        extra = []; merged = 0
        for item, q in want.items():
            avail = int(shed.get(item, 0)) - selling_now.get(item, 0)
            n = min(q, avail)
            if n < MIN_UNITS:
                continue
            # merge into an existing SELL of the same item (quantities are caps), else add an order
            hit = next((o for o in cur if len(o) > 2 and o[0] == "SELL" and o[1] == item), None)
            if hit is not None:
                hit[2] = int(hit[2]) + n; merged += n
            else:
                extra.append(["SELL", item, n])
        if len(cur) + len(extra) > max_orders:
            # keep only what fits (order of `want` = tape order)
            extra = extra[: max(0, max_orders - len(cur))]
            if telemetry is not None:
                telemetry["advance_declined_full"] = telemetry.get("advance_declined_full", 0) + 1
        if not extra and not merged:
            return market
        if telemetry is not None:
            telemetry["advance_turns"] = telemetry.get("advance_turns", 0) + 1
            telemetry["advance_units"] = telemetry.get("advance_units", 0) + sum(e[2] for e in extra) + merged
        return extra + cur
    except Exception:
        if telemetry is not None:
            telemetry["advance_errors"] = telemetry.get("advance_errors", 0) + 1
        return market
```

### 2. `FunctionDef:frontload#1` — aurax-only

- market_score: **26**
- production_score: **0**

**aurax-only block:**

```python
def frontload(obs, market, params=None, telemetry=None):
    """Return a reordered copy of `market` (list of orders) or the original list."""
    if not isinstance(market, list) or len(market) < 2: return market
    orders = [list(o) for o in market if isinstance(o, (list, tuple)) and o]
    if len(orders) != len(market): return market
    # groups: A = SELL that is not the sell leg of a same-item buy->sell wash;
    #         B = BUY_PRODUCT and wash SELLs (original relative order);
    #         C = everything else (original relative order)
    A, B, C = [], [], []
    for j, o in enumerate(orders):
        op = o[0]
        if op == "SELL":
            wash = any(p[0] == "BUY_PRODUCT" and len(p) > 1 and len(o) > 1 and p[1] == o[1] for p in orders[:j])
            (B if wash else A).append(o)
        elif op == "BUY_PRODUCT":
            B.append(o)
        else:
            C.append(o)
    new = A + B + C
    if new == orders: return market
    try:
        me = int(obs["player"]); farm = obs["farms"][me]; private = obs["private"]
        money = float(farm["money"]); shed_total = sum(int(v) for v in private["shed"].values())
        inv = {k: int(v) for k, v in obs["market"]["inventory"].items()}
        hires_today = int(farm.get("hires_today", 0)); n_land_extra = max(0, len(farm.get("unlocked_quadrants", ["NW"])) - 1)
        params = params or _MARKET_PARAMS
        for pressure in (0, 1):
            ok_old, _ = _simulate(orders, money, shed_total, inv, hires_today, n_land_extra, params, pressure)
            ok_new, _ = _simulate(new, money, shed_total, inv, hires_today, n_land_extra, params, pressure)
            if not ok_old or not ok_new:
                if telemetry is not None: telemetry["frontload_declined"] = telemetry.get("frontload_declined", 0) + 1
                return market
    except Exception:
        return market
    if telemetry is not None:
        telemetry["frontload_turns"] = telemetry.get("frontload_turns", 0) + 1
    return new
```

### 3. `FunctionDef:agent#28` — changed

- market_score: **30**
- production_score: **9**

```diff
--- E21:FunctionDef:agent#28
+++ aurax:FunctionDef:agent#28
@@ -2,28 +2,14 @@
     action=_OPEN_PARENT(observation,configuration)
     try:
         step=int(observation['step'])
-        if step==0:_OPEN_REPORT.update(open_turns=0,open_errors=0,open_attack=0)
+        if step==0:_OPEN_REPORT.update(open_turns=0,open_errors=0)
         standard=configuration is None or all(configuration.get(k,v)==v for k,v in [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10),('startingMoney',3000)])
         if standard and step==0 and action.get('market')==[['BUY_PRODUCT','WHEAT',5],['BUY_PRODUCT','WHEAT',10],['SELL','WHEAT',60]]:
-            action=dict(action,market=[list(o) for o in _OPEN_STEP0]);_OPEN_REPORT['open_turns']+=1
-        elif standard and step==1:
-            # EXP293: the five feed units were bought at step 0 (index 0, cheapest quotes); the tape's failing SELL 13 and
-            # its step-1 BUY 5 are removed so the shed keeps exactly the tape's five units.
+            action=dict(action,market=[['BUY_PRODUCT','WHEAT',_OPEN_UNITS],['SELL','WHEAT',_OPEN_UNITS]]);_OPEN_REPORT['open_turns']+=1
+        elif standard and step==1 and _OPEN_FEED_STEP1<5:
             market=[list(o) for o in action.get('market',[])]
             if len(market)>=2 and market[0]==['SELL','WHEAT',13] and market[1]==['BUY_PRODUCT','WHEAT',5]:
-                market=market[2:];_OPEN_REPORT['open_turns']+=1
-                # EXP293 step-1 attack: every tape of this lineage buys its five feed units at index 1 of the first market turn;
-                # a product purchase at index 0 executes before it and lifts its quotes below the tape's day-0 cash slack.
-                # The units are sold back next turn, when no tape trades; the resale meets the lifted quotes, so the trip pays for itself.
-                if _OPEN_ATTACK and float(observation['farms'][int(observation['player'])]['money'])>=_OPEN_ATTACK_MIN_CASH:
-                    player=int(observation['player']);farms=observation['farms']
-                    own_money=float(farms[player]['money']);rival_money=float(farms[1-player]['money'])
-                    attack_units=8 if abs(rival_money-own_money)<0.5 else _OPEN_ATTACK
-                    market=[['BUY_PRODUCT','WHEAT',attack_units]]+market;_OPEN_REPORT['open_attack']=attack_units
-                action=dict(action,market=market)
-        elif standard and step==2 and _OPEN_REPORT.get('open_attack'):
-            attack_units=int(_OPEN_REPORT['open_attack'])
-            action=dict(action,market=[['SELL','WHEAT',attack_units]]+[list(o) for o in action.get('market',[])][:9]);_OPEN_REPORT['open_turns']+=1
+                market[1]=['BUY_PRODUCT','WHEAT',_OPEN_FEED_STEP1];action=dict(action,market=market);_OPEN_REPORT['open_turns']+=1
     except Exception:_OPEN_REPORT['open_errors']+=1
     _OPEN_REPORT.update(getattr(_OPEN_PARENT,'telemetry',{}))
     return action
```

### 4. `FunctionDef:_adv_apply#1` — tetsu-only

- market_score: **24**
- production_score: **0**

**E21-only block:**

```python
def _adv_apply(obs,action):
    step=int(obs['step']);player=int(obs['player'])
    if step%24==23 or not _ADV_FROM<=step<_ADV_TO:return action
    native=_IMPL.chassis.players[player];debts=native['sell_state'].setdefault('r36_debts',{})
    plan=[];first=None
    for off in range(1,_ADV_LOOK+1):
        t=step+off
        if t>718:break
        for o in _adv_future(player,t):
            if not o or len(o)<3:continue
            if first is None:first=o
            if o[0]=='SELL' and o[1] in _ADV_ITEMS:
                try:q=max(0,int(o[2]))
                except Exception:q=0
                if _ADV_SUBTRACT_DEBTS:q-=debts.get(t,{}).get(o[1],0)   # already reserved by the sale-reservation layer
                if q>0:plan.append((t,o[1],q))
    protected=first[1] if _ADV_PROTECT and first is not None and first[0]=='SELL' else None
    plan=[(t,item,q) for t,item,q in plan if item!=protected]
    if not plan:return action
    market=[list(o) for o in (action.get('market') or [])]
    if any(len(o)>1 and o[0]=='BUY_PRODUCT' for o in market):return action
    stock=projected_shed(action,FarmView(obs))
    selling={}
    for o in market:
        if len(o)>=3 and o[0]=='SELL':
            try:selling[o[1]]=selling.get(o[1],0)+max(0,int(o[2]))
            except Exception:return action
    commands=[action.get('farmer') or ['PASS'],*(action.get('hands') or [])]
    picked={c[1] for c in commands if len(c)>1 and c[0]=='PICKUP'}
    prices=obs['market']['prices'];added=0;extra=[];booked=[]
    for item in sorted({it for _,it,_ in plan},key=lambda it:-int(prices.get(it,0))):
        if item in picked or int(prices.get(item,0))<2:continue
        avail=int(stock.get(item,0))-selling.get(item,0)
        if avail<1:continue
        hit=next((o for o in market if len(o)>=3 and o[0]=='SELL' and o[1]==item),None)
        if hit is None and len(market)+len(extra)>=10:continue
        n=0
        for t,it,q in plan:
            if it!=item or avail<=0:continue
            take=min(q,avail);booked.append((t,item,take));n+=take;avail-=take
        if n<1:continue
        if hit is not None:hit[2]=int(hit[2])+n
        else:extra.append(['SELL',item,n])
        added+=n
    if not added:return action
    for t,item,take in (booked if _ADV_BOOK else []):
        d=debts.setdefault(t,{});d[item]=d.get(item,0)+take
    _ADV_REPORT['adv_turns']+=1;_ADV_REPORT['adv_units']+=added
    return dict(action,market=extra+market)
```

### 5. `FunctionDef:_adv_frontload#1` — tetsu-only

- market_score: **21**
- production_score: **0**

**E21-only block:**

```python
def _adv_frontload(obs,action):
    """Final market-list order: sales first, then product purchases (with the sales of an item the same list also buys, in
    their original order), then everything else in its original order.  Sales earlier only add cash and shed room before
    purchases; a product purchase ahead of fixed-price orders meets the rival's same-item purchase at the same index or
    earlier."""
    market=[list(o) for o in (action.get('market') or []) if o]
    if len(market)<2 or int(obs['step'])<_ADV_FROM:return action
    buys={o[1] for o in market if len(o)>1 and o[0]=='BUY_PRODUCT'}
    front=[o for o in market if len(o)>=3 and o[0]=='SELL' and o[1] not in buys]
    mid=[o for o in market if len(o)>=3 and o[0]=='BUY_PRODUCT' or (len(o)>=3 and o[0]=='SELL' and o[1] in buys)]
    rest=[o for o in market if o not in front and o not in mid]
    new=front+mid+rest
    if new==market:return action
    _ADV_REPORT['front_turns']=_ADV_REPORT.get('front_turns',0)+1
    return dict(action,market=new)
```

### 6. `FunctionDef:_race_lost#1` — changed

- market_score: **17**
- production_score: **0**

```diff
--- E21:FunctionDef:_race_lost#1
+++ aurax:FunctionDef:_race_lost#1
@@ -1,27 +1,18 @@
 def _race_lost(observation,state):
-    """EXP293: True when the rival sold a race product at the previous turn while we held it unsold, the common tape
-    has no sale of it within the lineage's own lead/reservation window (5 turns) and sells it within the following
-    24 turns: the rival pre-empts the plan's own sale ahead of us."""
+    """True when the rival sold a race product at the previous turn, our shed stock of it rose at that turn
+    (a drop) and we did not sell any of it: the rival quotes at the drop while we hold."""
     prev=state.get('prev');prev_action=state.get('prev_action')
     if prev is None or prev_action is None:return False
-    step=int(observation['step']);player=int(observation['player'])
+    step=int(observation['step'])
     if step!=prev['step']+1 or step%24==0:return False
-    inv=observation['market']['inventory'];pinv=prev['inventory'];prices=prev['prices']
+    shed=observation['private']['shed'];inv=observation['market']['inventory'];pinv=prev['inventory'];prices=prev['prices']
     town=_race_town(step-1,prev['shops'])
     sold={}
     for order in prev_action.get('market',[]):
         if len(order)>=3 and order[0]=='SELL' and order[1] in _RACE_ITEMS:sold[order[1]]=1
-    native=_IMPL.chassis.players[player]
     for item in _RACE_ITEMS:
-        before=int(prev['view'].shed.get(item,0))
-        if before<=0 or item in sold or prices.get(item,0)<=1:continue
+        held=int(shed.get(item,0));before=int(prev['view'].shed.get(item,0))
+        if held<=before or item in sold or prices.get(item,0)<=1:continue
         rival=int(inv[item])-int(pinv[item])+town.get(item,0)
-        if rival<=0:continue
-        def planned(t):
-            future=_IMPL.chassis.routes[2 if t>=648 else native['route']][t]
-            return any(len(o)>=3 and o[0]=='SELL' and o[1]==item for o in future.get('market',[]))
-        # every member of this lineage sells at the scheduled turn, one turn early (sale lead) or up to four turns early
-        # (the base reservation): only a sale further ahead of the plan is a race
-        if any(planned(t) for t in range(step-1,min(719,step+5))):continue
-        if any(planned(t) for t in range(step+5,min(719,step+24))):return True
+        if rival>0:return True
     return False
```

### 7. `FunctionDef:agent#30` — aurax-only

- market_score: **12**
- production_score: **3**

**aurax-only block:**

```python
def agent(observation, configuration=None):
    action = _PARENT(observation, configuration)
    try:
        # step-0 opening: one large wheat round trip instead of the parent's split buy/buy/sell (same net effect on our
        # own farm; the single index-0 buy is what the per-index lockstep quoting sees first)
        if isinstance(action, dict) and _standard(configuration) and int(observation["step"]) == 0 and action.get("market") == _V43_OPENING:
            action = dict(action); action["market"] = [["BUY_PRODUCT", "WHEAT", OPEN_UNITS], ["SELL", "WHEAT", OPEN_UNITS]]
            TELEMETRY["open_turns"] = TELEMETRY.get("open_turns", 0) + 1
    except Exception:
        TELEMETRY["open_errors"] = TELEMETRY.get("open_errors", 0) + 1
    try:
        if isinstance(action, dict) and _standard(configuration):
            m = action.get("market")
            m = list(m) if isinstance(m, list) else []
            new = advance_sales(observation, m, _future_market, TELEMETRY)
            if len(new) > 1:
                new = frontload(observation, new, None, TELEMETRY)
            if new is not m:
                action = dict(action); action["market"] = new
    except Exception:
        TELEMETRY["wrap_errors"] = TELEMETRY.get("wrap_errors", 0) + 1
    return action
```

### 8. `FunctionDef:_simulate#1` — aurax-only

- market_score: **11**
- production_score: **3**

**aurax-only block:**

```python
def _simulate(orders, money, shed_total, inv, hires_today, n_land_extra, params, opp_pressure=0):
    """Solo execution of one market list under the interpreter's per-unit rules.
    opp_pressure>0 makes buys/sells pessimistic (inventory moves an extra unit per unit
    executed, as it would against a lockstep opponent doing the same).
    Returns (all_executed, money_after)."""
    inv = dict(inv); money = float(money); shed = int(shed_total)
    for o in orders:
        if not isinstance(o, (list, tuple)) or not o: return False, money
        op = o[0]
        if op == "HIRE":
            c = _fib(hires_today)
            if money < c: return False, money
            money -= c; hires_today += 1; continue
        if op == "BUY_LAND":
            if n_land_extra >= len(_LAND_PRICES): return False, money
            c = _LAND_PRICES[n_land_extra]
            if money < c: return False, money
            money -= c; n_land_extra += 1; continue
        if len(o) < 3: return False, money
        try: n = int(o[2])
        except Exception: return False, money
        if n <= 0: return False, money
        item = o[1]
        if op == "SELL":
            if item not in params: return False, money
            for _ in range(n):
                p = _price(item, inv[item], params)
                money += p
                if p > 1: inv[item] += 1 + opp_pressure
                shed -= 1
        elif op == "BUY_PRODUCT":
            if item not in ("WHEAT", "FERTILIZER"): return False, money
            for _ in range(n):
                p = _price(item, inv[item] - 1, params)
                if money < p or shed >= 100: return False, money
                money -= p; inv[item] -= 1 + opp_pressure; shed += 1
        elif op == "BUY_SEED":
            if item not in _SEED_COST: return False, money
            c = _SEED_COST[item] * n
            if money < c: return False, money
            money -= c
        elif op == "BUY_ANIMAL":
            if item not in _ANIMAL_COST: return False, money
            for _ in range(n):
                c = _ANIMAL_COST[item]
                if money < c or shed >= 100: return False, money
                money -= c; shed += 1
        else:
            return False, money
    return True, money
```

### 9. `FunctionDef:_price#1` — aurax-only

- market_score: **4**
- production_score: **0**

**aurax-only block:**

```python
def _price(item, inventory, params):
    p = params[item]; base = p["base"]; I0 = p["I0"]; T = p["T"]
    if inventory < I0:
        amp = p["below_target"] * base / _shape(p["below_func"], T, T)
        v = base + amp * _shape(p["below_func"], I0 - inventory, T)
    else:
        amp = p["above_target"] * base / _shape(p["above_func"], T, T)
        v = base - amp * _shape(p["above_func"], inventory - I0, T)
    return max(_PRICE_FLOOR, int(round(v)))
```

### 10. `FunctionDef:_r60_risks#1` — aurax-only

- market_score: **4**
- production_score: **0**

**aurax-only block:**

```python
def _r60_risks(obs):
    day=int(obs['step'])//24;prices=obs['market']['prices'];farm=obs['farms'][obs['player']]
    risks=[]
    for y,row in enumerate(farm['tiles']):
        for x,tile in enumerate(row):
            if not isinstance(tile,dict) or not tile.get('animal'):continue
            if tile.get('fed_today') or int(tile.get('consecutive_unfed',0))<1:continue
            animal=tile['animal'];product=_R60_ANIMAL_PRODUCT[animal]
            remaining=max(0,29-day);future=(remaining+_R60_ANIMAL_INTERVAL[animal]-1)//_R60_ANIMAL_INTERVAL[animal]
            loss=_R60_ANIMAL_COST[animal]+future*max(1,int(prices.get(product,1)))
            risks.append((loss,(x,y),animal))
    return sorted(risks,reverse=True)
```

### 11. `FunctionDef:agent#29` — changed

- market_score: **3**
- production_score: **0**

```diff
--- E21:FunctionDef:agent#29
+++ aurax:FunctionDef:agent#29
@@ -1,13 +1,14 @@
 def agent(observation,configuration=None):
-    action=_ADV_PARENT(observation,configuration)
+    result=_R60_SURVIVAL_PARENT(observation,configuration)
     try:
-        if int(observation['step'])==0:_ADV_REPORT.update(adv_turns=0,adv_units=0,adv_errors=0)
-        standard=configuration is None or all(configuration.get(k,v)==v for k,v in [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10)])
-        if standard:action=_adv_apply(observation,action)
-        if standard and _ADV_FRONT:action=_adv_frontload(observation,action)
-        # the race layer's lost-race detector must judge the final market list (advanced sales included)
-        st=_RACE_STATE.get(int(observation['player']))
-        if st is not None and st.get('prev_action') is not None and st.get('step')==int(observation['step']):st['prev_action']=action
-    except Exception:_ADV_REPORT['adv_errors']+=1
-    _ADV_REPORT.update(getattr(_ADV_PARENT,'telemetry',{}))
-    return action
+        step=int(observation['step']);player=int(observation['player']);state=_R60_SURVIVAL_STATES.get(player)
+        if state is None or step<=state.get('step',-1):
+            state=_R60_SURVIVAL_STATES[player]={'step':-1}
+            for key in _R60_SURVIVAL_REPORT:_R60_SURVIVAL_REPORT[key]=0
+        state['step']=step
+        if configuration is None or all(configuration.get(k,v)==v for k,v in [('boardSize',10),('turnsPerDay',24),('maxMarketOrdersPerTurn',10)]):
+            # opening liquidity bypassed for v41 plans
+            result=_r60_survival_guard(observation,result,state)
+    except Exception:_R60_SURVIVAL_REPORT['rescue_errors']+=1
+    _R60_SURVIVAL_COMBINED.update(getattr(_R60_SURVIVAL_PARENT,'telemetry',{}));_R60_SURVIVAL_COMBINED.update(_R60_SURVIVAL_REPORT)
+    return result
```

### 12. `Assign:_V43_OPENING#2` — aurax-only

- market_score: **4**
- production_score: **3**

**aurax-only block:**

```python
_V43_OPENING = [["BUY_PRODUCT", "WHEAT", 5], ["BUY_PRODUCT", "WHEAT", 10], ["SELL", "WHEAT", 60]]
```

## 3. E22 selection rule

- Prefer a block that changes SELL timing/ordering/price response while leaving route/farm planning untouched.
- Do not copy a block solely because aurax wins particular seeds; E21 beats aurax overall in the current screen.
- The first E22 should be a complete market-policy variant that can be toggled as a unit.
- After E22 exists, test it on fresh seeds against E21, aurax, Ahmed, and a refreshed population-representative panel.

Final objective remains population-level W/D/L / Bradley–Terry.
