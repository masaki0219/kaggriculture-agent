# Frontier Failure Regimes

- Generated: `2026-09-18T15:07:46+09:00`
- Source: `2026-09-18_CURRENT_FRONTIER_SCREEN.json`
- Seeds: `20000..20015`
- Fresh replay games: **32**
- Errors: **0**

Purpose: explain *where* E21 loses to aurax V7 before defining E22.

## 1. Failure-seed overlap from the completed frontier screen

- E21 trouble seeds vs Ahmed (`LL` or `WL`): `20002`, `20003`, `20005`, `20014`
- E21 trouble seeds vs aurax (`LL` or `WL`): `20002`, `20003`, `20005`, `20007`, `20010`, `20011`, `20014`
- Overlap: `20002`, `20003`, `20005`, `20014`

The overlap is evidence for environment/regime sensitivity, not proof of causality.

## 2. Seed-level shop regime and E21 result

| Seed | vs Ahmed | vs aurax | first 4 shops | E21 C/S/G | E21 C/T/S/M/W plants | aurax C/S/G | aurax C/T/S/M/W plants |
|---:|---|---|---|---|---|---|---|
| 20000 | WW | WW | `PET_CAFE → FARMERS_MARKET → YARN_STORE → ICE_CREAM_SHOP` | 6/6/5 | 31/0/33/12/162 | 6/6/5 | 31/0/33/12/162 |
| 20001 | WW | WW | `BRUNCH_SPOT → SMOOTHIE_SHOP → SMOOTHIE_SHOP → ICE_CREAM_SHOP` | 8/6/3 | 31/0/33/12/162 | 8/6/3 | 31/0/33/12/162 |
| 20002 | WL | WL | `YARN_STORE → FARMERS_MARKET → SMOOTHIE_SHOP → SMOOTHIE_SHOP` | 6/10/0 | 31/0/32/12/162 | 6/10/0 | 31/0/33/12/162 |
| 20003 | LL | LL | `BRUNCH_SPOT → FARMERS_MARKET → FARMERS_MARKET → BAKERY` | 8/4/5 | 31/0/33/12/162 | 8/4/5 | 31/0/33/12/162 |
| 20004 | WW | WW | `SMOOTHIE_SHOP → ICE_CREAM_SHOP → SMOOTHIE_SHOP → BRUNCH_SPOT` | 9/5/3 | 31/0/33/12/162 | 9/5/3 | 31/0/33/12/162 |
| 20005 | LL | LL | `BAKERY → PIZZA_SHOP → PET_CAFE → FARMERS_MARKET` | 8/6/3 | 31/10/33/12/162 | 8/6/3 | 31/10/33/12/161 |
| 20006 | WW | WW | `YARN_STORE → PET_CAFE → BRUNCH_SPOT → BAKERY` | 6/11/0 | 31/0/33/12/159 | 6/10/0 | 31/0/33/12/159 |
| 20007 | WW | LL | `YARN_STORE → PIZZA_SHOP → PIZZA_SHOP → BRUNCH_SPOT` | 6/11/0 | 31/10/33/12/162 | 6/11/0 | 31/10/33/12/162 |
| 20008 | WW | WW | `YARN_STORE → FARMERS_MARKET → ICE_CREAM_SHOP → YARN_STORE` | 6/16/0 | 31/0/33/12/161 | 6/16/0 | 31/0/33/12/162 |
| 20009 | WW | WW | `PET_CAFE → FARMERS_MARKET → ICE_CREAM_SHOP → YARN_STORE` | 6/6/5 | 31/0/33/12/162 | 6/6/5 | 31/0/33/12/162 |
| 20010 | WW | LL | `PIZZA_SHOP → BRUNCH_SPOT → FARMERS_MARKET → BAKERY` | 8/6/3 | 31/10/33/12/162 | 8/6/3 | 31/10/33/12/162 |
| 20011 | WW | LL | `FARMERS_MARKET → FARMERS_MARKET → BAKERY → BAKERY` | 6/6/5 | 31/10/33/12/162 | 6/6/5 | 31/10/33/12/162 |
| 20012 | WW | WW | `PET_CAFE → SMOOTHIE_SHOP → YARN_STORE → PIZZA_SHOP` | 8/6/3 | 31/0/33/12/162 | 8/6/3 | 31/0/33/12/162 |
| 20013 | WW | WW | `PET_CAFE → BRUNCH_SPOT → SMOOTHIE_SHOP → PET_CAFE` | 6/6/5 | 31/0/33/12/162 | 6/6/5 | 31/0/33/12/162 |
| 20014 | WL | WL | `BAKERY → ICE_CREAM_SHOP → ICE_CREAM_SHOP → PIZZA_SHOP` | 8/6/3 | 31/0/32/12/162 | 8/6/3 | 31/0/33/12/162 |
| 20015 | WW | WW | `SMOOTHIE_SHOP → BRUNCH_SPOT → ICE_CREAM_SHOP → YARN_STORE` | 9/5/3 | 31/0/33/12/162 | 9/5/3 | 31/0/33/12/162 |

## 3. E21 vs aurax behavior by outcome regime

Averages use both seat orientations.

| Regime | Agent | N | Cow | Sheep | Goose | Carrot | Tomato | Strawberry | Melon | Wheat | Hands | Sell orders | Sell qty |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| aurax_sweep_loss | `e21` | 10 | 7.2 | 6.6 | 3.2 | 31.0 | 8.0 | 33.0 | 12.0 | 161.9 | 13.6 | 339.8 | 80456.2 |
| aurax_sweep_loss | `aurax7_v7` | 10 | 7.2 | 6.6 | 3.2 | 31.0 | 8.0 | 33.0 | 12.0 | 161.9 | 13.6 | 338.6 | 80450.8 |
| seat_sensitive | `e21` | 4 | 7.0 | 8.0 | 1.5 | 31.0 | 0.0 | 32.5 | 12.0 | 162.0 | 12.0 | 346.8 | 87628.0 |
| seat_sensitive | `aurax7_v7` | 4 | 7.0 | 8.0 | 1.5 | 31.0 | 0.0 | 32.5 | 12.0 | 162.0 | 12.0 | 344.2 | 87618.5 |
| aurax_sweep_win | `e21` | 18 | 7.1 | 7.4 | 3.0 | 31.0 | 0.0 | 33.0 | 12.0 | 161.6 | 11.9 | 342.4 | 80853.6 |
| aurax_sweep_win | `aurax7_v7` | 18 | 7.1 | 7.3 | 3.0 | 31.0 | 0.0 | 33.0 | 12.0 | 161.6 | 11.9 | 339.9 | 80841.7 |

## 4. Market differences on E21 sweep-loss seeds

| Seed | E21 seat | Outcome | Margin | E21 sell orders | aurax sell orders | E21 sell qty | aurax sell qty |
|---:|---:|---|---:|---:|---:|---:|---:|
| 20003 | 0 | L | -174 | 280 | 279 | 75345 | 75336 |
| 20003 | 1 | L | -174 | 280 | 279 | 75345 | 75336 |
| 20005 | 0 | L | -86 | 349 | 350 | 75502 | 75508 |
| 20005 | 1 | L | -246 | 349 | 350 | 75502 | 75508 |
| 20007 | 0 | L | -269 | 367 | 366 | 99906 | 99895 |
| 20007 | 1 | L | -269 | 367 | 366 | 99906 | 99895 |
| 20010 | 0 | L | -16 | 343 | 339 | 75491 | 75479 |
| 20010 | 1 | L | -16 | 343 | 339 | 75491 | 75479 |
| 20011 | 0 | L | -196 | 360 | 359 | 76037 | 76036 |
| 20011 | 1 | L | -196 | 360 | 359 | 76037 | 76036 |

## 5. E22 decision gate

- If E21 and aurax realize nearly identical production on E21-loss seeds but market-order behavior differs, E22 should target a **market regime** rather than crop routing.
- If aurax changes production materially on the same loss seeds, E22 can target that complete production-routing mechanism.
- If the shared Ahmed/aurax trouble seeds cluster around a small set of early-shop patterns, use those patterns as a regime trigger only if a larger seed sample confirms it.
- Do not optimize only against aurax. Any E22 must later be re-evaluated against a refreshed population panel / replay census.

Final objective remains population-level W/D/L / Bradley–Terry.
