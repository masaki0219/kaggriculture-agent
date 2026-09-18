# E21 Realized Shop Response

- Generated: `2026-09-18T14:37:15+09:00`
- Seeds: `19000..19011`
- Opponents: `e11`, `aurax7_v7`
- Games requested: **48**
- Valid games: **48**
- Errors: **0**

This report counts unique plant/animal instances observed in actual completed games.
It is intentionally different from counting commands in static route tapes.

## 1. Realized shop-demand correlations

### First 2 shops

| Relationship | Correlation | N |
|---|---:|---:|
| MILK demand → cows | 0.818 | 48 |
| WOOL demand → sheep | n/a | 48 |
| CARROT demand → carrot plants | n/a | 48 |
| TOMATO demand → tomato plants | 0.239 | 48 |
| STRAWBERRY demand → strawberry plants | n/a | 48 |
| WHEAT demand → wheat plants | 0.027 | 48 |

### First 3 shops

| Relationship | Correlation | N |
|---|---:|---:|
| MILK demand → cows | 0.674 | 48 |
| WOOL demand → sheep | 0.135 | 48 |
| CARROT demand → carrot plants | n/a | 48 |
| TOMATO demand → tomato plants | 0.638 | 48 |
| STRAWBERRY demand → strawberry plants | n/a | 48 |
| WHEAT demand → wheat plants | -0.043 | 48 |

### First 4 shops

| Relationship | Correlation | N |
|---|---:|---:|
| MILK demand → cows | 0.482 | 48 |
| WOOL demand → sheep | 0.135 | 48 |
| CARROT demand → carrot plants | n/a | 48 |
| TOMATO demand → tomato plants | 0.540 | 48 |
| STRAWBERRY demand → strawberry plants | n/a | 48 |
| WHEAT demand → wheat plants | 0.091 | 48 |

## 2. By-opponent correlations

### vs `e11`

| Window | Relationship | Correlation | N |
|---|---|---:|---:|
| first 2 | MILK demand → cows | 0.818 | 24 |
| first 2 | WOOL demand → sheep | n/a | 24 |
| first 2 | CARROT demand → carrot plants | n/a | 24 |
| first 2 | TOMATO demand → tomato plants | 0.239 | 24 |
| first 2 | STRAWBERRY demand → strawberry plants | n/a | 24 |
| first 2 | WHEAT demand → wheat plants | 0.027 | 24 |
| first 3 | MILK demand → cows | 0.674 | 24 |
| first 3 | WOOL demand → sheep | 0.135 | 24 |
| first 3 | CARROT demand → carrot plants | n/a | 24 |
| first 3 | TOMATO demand → tomato plants | 0.638 | 24 |
| first 3 | STRAWBERRY demand → strawberry plants | n/a | 24 |
| first 3 | WHEAT demand → wheat plants | -0.043 | 24 |
| first 4 | MILK demand → cows | 0.482 | 24 |
| first 4 | WOOL demand → sheep | 0.135 | 24 |
| first 4 | CARROT demand → carrot plants | n/a | 24 |
| first 4 | TOMATO demand → tomato plants | 0.540 | 24 |
| first 4 | STRAWBERRY demand → strawberry plants | n/a | 24 |
| first 4 | WHEAT demand → wheat plants | 0.091 | 24 |

### vs `aurax7_v7`

| Window | Relationship | Correlation | N |
|---|---|---:|---:|
| first 2 | MILK demand → cows | 0.818 | 24 |
| first 2 | WOOL demand → sheep | n/a | 24 |
| first 2 | CARROT demand → carrot plants | n/a | 24 |
| first 2 | TOMATO demand → tomato plants | 0.239 | 24 |
| first 2 | STRAWBERRY demand → strawberry plants | n/a | 24 |
| first 2 | WHEAT demand → wheat plants | 0.027 | 24 |
| first 3 | MILK demand → cows | 0.674 | 24 |
| first 3 | WOOL demand → sheep | 0.135 | 24 |
| first 3 | CARROT demand → carrot plants | n/a | 24 |
| first 3 | TOMATO demand → tomato plants | 0.638 | 24 |
| first 3 | STRAWBERRY demand → strawberry plants | n/a | 24 |
| first 3 | WHEAT demand → wheat plants | -0.043 | 24 |
| first 4 | MILK demand → cows | 0.482 | 24 |
| first 4 | WOOL demand → sheep | 0.135 | 24 |
| first 4 | CARROT demand → carrot plants | n/a | 24 |
| first 4 | TOMATO demand → tomato plants | 0.540 | 24 |
| first 4 | STRAWBERRY demand → strawberry plants | n/a | 24 |
| first 4 | WHEAT demand → wheat plants | 0.091 | 24 |

## 3. Demand buckets from first 4 shops

### first 4: MILK → `cow`

- demand 0: mean 6.00, min 6, max 6, n=4
- demand 1: mean 8.00, min 8, max 8, n=12
- demand 2: mean 7.20, min 6, max 8, n=20
- demand 3: mean 8.67, min 8, max 9, n=12

### first 4: WOOL → `sheep`

- demand 0: mean 5.82, min 5, max 6, n=44
- demand 1: mean 6.00, min 6, max 6, n=4

### first 4: CARROT → `carrot`

- demand 0: mean 31.00, min 31, max 31, n=4
- demand 1: mean 31.00, min 31, max 31, n=20
- demand 2: mean 31.00, min 31, max 31, n=20
- demand 3: mean 31.00, min 31, max 31, n=4

### first 4: TOMATO → `tomato`

- demand 0: mean 0.00, min 0, max 0, n=12
- demand 1: mean 0.00, min 0, max 0, n=20
- demand 2: mean 5.00, min 0, max 10, n=16

### first 4: STRAWBERRY → `strawberry`

- demand 1: mean 33.00, min 33, max 33, n=20
- demand 2: mean 33.00, min 33, max 33, n=8
- demand 3: mean 33.00, min 33, max 33, n=20

### first 4: WHEAT → `wheat`

- demand 1: mean 162.00, min 162, max 162, n=8
- demand 2: mean 161.90, min 161, max 162, n=20
- demand 3: mean 162.00, min 162, max 162, n=12
- demand 4: mean 162.00, min 162, max 162, n=8

## 4. Production ranges

| Metric | Min | Median-ish | Max |
|---|---:|---:|---:|
| COW placements | 6 | 8 | 9 |
| SHEEP placements | 5 | 6 | 6 |
| GOOSE placements | 3 | 3 | 5 |
| CARROT plants | 31 | 31 | 31 |
| TOMATO plants | 0 | 0 | 10 |
| STRAWBERRY plants | 33 | 33 | 33 |
| MELON plants | 12 | 12 | 12 |
| WHEAT plants | 161 | 162 | 162 |
| max hands | 11 | 12 | 14 |

## 5. E22 decision rule

- If first-3/first-4 CARROT/TOMATO/STRAWBERRY correlations become strong in realized games, E21 already contains later-shop production adaptation; E22 should target another failure mode.
- If milk/wool remain responsive but crop correlations remain weak, E22 should be a coherent later-shop crop-routing family rather than an E21 market-threshold patch.
- If response changes strongly by opponent, production and market overlays are coupled; E22 should be tested as a separate full system, not a local graft.

Final selection must still use population-level W/D/L / Bradley–Terry evidence.
