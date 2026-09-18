# E21 Structure Report — Tetsu Market-Smart Farming V23

- Generated: `2026-09-18T14:16:57+09:00`
- Source: `artifacts/bundles/current/public_agents/elite/tetsu_market_v23_current/raw/_extract_submission_tar/main.py`
- SHA256: `f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`
- Source lines: **3631**
- Purpose: identify architectural seams before creating E22.
- Static analysis only; strategic causality still requires games.

## 1. Whole-source strategic footprint

- **production**: 712 lexical hits
- **executor**: 680 lexical hits
- **market**: 597 lexical hits
- **shop-routing**: 208 lexical hits
- **endgame**: 103 lexical hits
- **opponent**: 46 lexical hits

## 2. Top-level definitions

| Definition | Kind | Lines | Categories |
|---|---|---:|---|
| `_get` | FunctionDef | 284-291 (8) | none |
| `_int` | FunctionDef | 294-298 (5) | none |
| `_fib` | FunctionDef | 301-305 (5) | none |
| `_step_of` | FunctionDef | 308-312 (5) | none |
| `_shed_adjacent` | FunctionDef | 315-319 (5) | none |
| `_tile_at` | FunctionDef | 322-327 (6) | none |
| `_is_noop` | FunctionDef | 330-375 (46) | production:10 |
| `_View` | ClassDef | 378-402 (25) | market:3, opponent:1 |
| `Chassis` | ClassDef | 406-906 (501) | market:105, executor:104, production:42, endgame:7, opponent:4 |
| `make_agent` | FunctionDef | 910-938 (29) | executor:2, market:1 |
| `_router` | FunctionDef | 952-962 (11) | executor:3, shop-routing:3 |
| `agent` | FunctionDef | 971-977 (7) | executor:2, market:1 |
| `agent` | FunctionDef | 982-996 (15) | executor:6, market:4 |
| `_parent_liquidate` | FunctionDef | 1013-1021 (9) | executor:5, market:5, endgame:1 |
| `_shadow_terminal` | FunctionDef | 1025-1052 (28) | executor:7, market:7 |
| `agent` | FunctionDef | 1054-1102 (49) | market:1 |
| `agent` | FunctionDef | 1110-1132 (23) | executor:6, market:5 |
| `agent` | FunctionDef | 1206-1211 (6) | market:1 |
| `FarmView` | ClassDef | 1217-1219 (3) | market:1 |
| `projected_shed` | FunctionDef | 1220-1220 (1) | executor:2 |
| `_v219_fib` | FunctionDef | 1236-1239 (4) | none |
| `_v219_native_day` | FunctionDef | 1242-1244 (3) | executor:1 |
| `_v219_qualifies` | FunctionDef | 1247-1267 (21) | production:8, shop-routing:4, market:2, executor:1 |
| `_v219_walk` | FunctionDef | 1270-1274 (5) | executor:2 |
| `_v219_home` | FunctionDef | 1277-1278 (2) | none |
| `_v219_request` | FunctionDef | 1281-1336 (56) | production:26, market:21, executor:17, endgame:2, opponent:1 |
| `_v219_worker` | FunctionDef | 1339-1391 (53) | production:37, executor:13, endgame:3, market:1 |
| `agent` | FunctionDef | 1394-1446 (53) | production:20, executor:17, market:5 |
| `_shadow_terminal` | FunctionDef | 1457-1459 (3) | none |
| `agent` | FunctionDef | 1468-1475 (8) | executor:4, market:1 |
| `_v224_sales_first` | FunctionDef | 1478-1494 (17) | market:7, executor:4 |
| `agent` | FunctionDef | 1498-1505 (8) | executor:4, market:1 |
| `agent` | FunctionDef | 1512-1520 (9) | executor:2, market:1 |
| `_v231_new_state` | FunctionDef | 1530-1534 (5) | production:3 |
| `_v231_controller` | FunctionDef | 1536-1618 (83) | production:43, market:24, shop-routing:8, executor:2 |
| `agent` | FunctionDef | 1620-1632 (13) | executor:4, production:3 |
| `_r36_native_lead` | FunctionDef | 1644-1646 (3) | executor:4 |
| `_r36_suppress` | FunctionDef | 1648-1655 (8) | market:10, executor:3 |
| `_r36_reserve` | FunctionDef | 1660-1704 (45) | executor:10, market:10, production:2, endgame:1 |
| `agent` | FunctionDef | 1706-1718 (13) | executor:6 |
| `_r37_shape` | FunctionDef | 1733-1746 (14) | none |
| `_r37_market_price` | FunctionDef | 1748-1762 (15) | market:7 |
| `_r37_similarity` | FunctionDef | 1764-1778 (15) | opponent:3, production:2 |
| `_r37_quote_priority` | FunctionDef | 1781-1804 (24) | production:12, market:9, opponent:4 |
| `_r37_reorder_sales` | FunctionDef | 1807-1826 (20) | executor:7, market:5 |
| `_r44_before` | FunctionDef | 1835-1848 (14) | opponent:4 |
| `_r44_after` | FunctionDef | 1850-1857 (8) | market:4, executor:3 |
| `agent` | FunctionDef | 1870-1903 (34) | executor:5 |
| `agent` | FunctionDef | 1913-1927 (15) | market:1 |
| `_v233_eligible` | FunctionDef | 1943-1953 (11) | production:6, shop-routing:3, market:2 |
| `_v233_request` | FunctionDef | 1955-1996 (42) | executor:13, production:12, market:11 |
| `_v233_worker` | FunctionDef | 1998-2029 (32) | production:19, executor:8 |
| `_v234_rescue` | FunctionDef | 2031-2051 (21) | executor:12, production:8, market:3 |
| `agent` | FunctionDef | 2053-2100 (48) | production:12, executor:7, market:7 |
| `_shadow_terminal` | FunctionDef | 2105-2107 (3) | none |
| `agent` | FunctionDef | 2109-2119 (11) | market:1 |
| `_r51_input_forecast` | FunctionDef | 2130-2159 (30) | executor:11, production:11, endgame:1, market:1 |
| `_r51_input_gain` | FunctionDef | 2161-2165 (5) | executor:10, production:5 |
| `_r51_input_path` | FunctionDef | 2167-2196 (30) | production:19, executor:9, market:3, opponent:1 |
| `_r51_input_control` | FunctionDef | 2198-2259 (62) | production:21, executor:20, market:8 |
| `agent` | FunctionDef | 2261-2275 (15) | executor:4, production:2, market:1 |
| `_r51_close_warehouse` | FunctionDef | 2283-2332 (50) | production:14, executor:13, market:11, shop-routing:4 |
| `agent` | FunctionDef | 2334-2340 (7) | none |
| `_r53_labor_assignment` | FunctionDef | 2347-2374 (28) | executor:16, production:9, endgame:4, market:2 |
| `agent` | FunctionDef | 2377-2382 (6) | none |
| `_r62_input_start` | FunctionDef | 2388-2400 (13) | executor:4, market:1 |
| `_r68_joint_plans` | FunctionDef | 2404-2423 (20) | executor:8, production:7, market:5, endgame:4 |
| `_r70_parent_fert_qty` | FunctionDef | 2430-2448 (19) | market:5, executor:3, production:2 |
| `_r70_before` | FunctionDef | 2450-2464 (15) | production:1 |
| `_r70_after` | FunctionDef | 2466-2480 (15) | production:4, executor:3 |
| `agent` | FunctionDef | 2484-2493 (10) | none |
| `_r79_tomato_fertilizer_worthwhile` | FunctionDef | 2498-2513 (16) | production:11, market:9, executor:2 |
| `_r85_feed` | FunctionDef | 2525-2548 (24) | production:12, executor:6, market:1 |
| `_r85_reserve` | FunctionDef | 2550-2575 (26) | executor:7, production:6, market:3 |
| `_r85_fertilizer` | FunctionDef | 2577-2589 (13) | market:9, executor:7, production:3 |
| `agent` | FunctionDef | 2591-2607 (17) | none |
| `_r86_next_feed` | FunctionDef | 2615-2643 (29) | production:11, executor:6, market:4 |
| `_r88_feed_bonus_cost` | FunctionDef | 2653-2670 (18) | none |
| `_r95_reserve` | FunctionDef | 2680-2700 (21) | shop-routing:10, executor:4, production:4, market:3 |
| `_r95_replenish` | FunctionDef | 2702-2726 (25) | executor:9, market:4, production:4 |
| `agent` | FunctionDef | 2728-2738 (11) | none |
| `_r97_market_stock` | FunctionDef | 2748-2757 (10) | market:4 |
| `_r97_delivery` | FunctionDef | 2759-2767 (9) | none |
| `_r97_budget` | FunctionDef | 2769-2784 (16) | production:10, market:9, opponent:1 |
| `_r97_supply` | FunctionDef | 2786-2856 (71) | production:23, executor:15, endgame:12, market:11, shop-routing:4 |
| `agent` | FunctionDef | 2858-2868 (11) | none |
| `_r124_labor_reserve` | FunctionDef | 2878-2880 (3) | market:1 |
| `_r124_seed_budget` | FunctionDef | 2882-2897 (16) | market:15, executor:6, production:5 |
| `_r124_atomic` | FunctionDef | 2899-2920 (22) | executor:7, shop-routing:5, production:3 |
| `agent` | FunctionDef | 2922-2944 (23) | production:2, executor:1, market:1 |
| `_r127_fields` | FunctionDef | 2955-2965 (11) | shop-routing:4, executor:3, production:2 |
| `_r127_last_hour` | FunctionDef | 2967-2987 (21) | executor:7, production:6 |
| `_r127_prefix_bound` | FunctionDef | 2989-2993 (5) | market:5, production:3, opponent:1 |
| `_r127_priority` | FunctionDef | 2995-3023 (29) | executor:12, production:8, market:3 |
| `agent` | FunctionDef | 3025-3041 (17) | production:1 |
| `_r128_commands` | FunctionDef | 3050-3051 (2) | executor:3 |
| `_r128_future` | FunctionDef | 3053-3055 (3) | executor:1 |
| `_r128_sale_credit` | FunctionDef | 3057-3065 (9) | market:8, executor:3, production:1 |
| `_r128_next_need` | FunctionDef | 3067-3074 (8) | market:3, production:1 |
| `_r128_field_safe` | FunctionDef | 3076-3094 (19) | endgame:2, production:2, market:1 |
| `_r128_food_need` | FunctionDef | 3096-3106 (11) | production:4 |
| `_r128_service` | FunctionDef | 3108-3156 (49) | production:9, executor:2 |
| `_r128_credit_supply` | FunctionDef | 3158-3172 (15) | executor:12, market:6, endgame:2, production:2 |
| `agent` | FunctionDef | 3174-3189 (16) | production:1 |
| `_r148_same_stock` | FunctionDef | 3202-3203 (2) | none |
| `_r148_overflow` | FunctionDef | 3206-3241 (36) | executor:9, endgame:8, market:8 |
| `_r148_atomic` | FunctionDef | 3244-3267 (24) | executor:6, production:4, shop-routing:4, endgame:1 |
| `_r148_seed_prefund` | FunctionDef | 3270-3307 (38) | executor:10, market:10, production:2, opponent:1, shop-routing:1 |
| `agent` | FunctionDef | 3310-3327 (18) | executor:6 |
| `_r149_deepcopy` | FunctionDef | 3337-3353 (17) | none |
| `_R149CopyProxy` | ClassDef | 3355-3357 (3) | none |
| `_race_positions_equal` | FunctionDef | 3388-3390 (3) | opponent:3 |
| `_race_clone` | FunctionDef | 3392-3397 (6) | none |
| `_race_town` | FunctionDef | 3399-3407 (9) | shop-routing:2 |
| `_race_lost` | FunctionDef | 3409-3435 (27) | market:12, opponent:4, shop-routing:2, executor:1 |
| `_race_snapshot` | FunctionDef | 3437-3439 (3) | market:6, shop-routing:2 |
| `_r36_reserve` | FunctionDef | 3441-3449 (9) | executor:3, endgame:1 |
| `agent` | FunctionDef | 3451-3484 (34) | opponent:4, endgame:3, executor:3 |
| `agent` | FunctionDef | 3501-3529 (29) | market:21, executor:11, production:9 |
| `_adv_future` | FunctionDef | 3550-3552 (3) | executor:1, market:1 |
| `_adv_apply` | FunctionDef | 3553-3601 (49) | market:14, executor:11 |
| `_adv_frontload` | FunctionDef | 3602-3616 (15) | market:16, executor:5, opponent:2, endgame:1 |
| `agent` | FunctionDef | 3617-3629 (13) | executor:7, endgame:1, market:1 |

## 3. Class methods

| Method | Lines | Categories |
|---|---:|---|
| `_View.__init__` | 381-396 (16) | market:3, opponent:1 |
| `_View.inv` | 398-399 (2) | none |
| `_View.in_hands` | 401-402 (2) | none |
| `Chassis.__init__` | 416-424 (9) | endgame:1, executor:1, market:1 |
| `Chassis._state` | 427-434 (8) | executor:1 |
| `Chassis._route_action` | 436-440 (5) | executor:2 |
| `Chassis.future_sells` | 442-457 (16) | executor:5, market:3 |
| `Chassis.act` | 460-504 (45) | executor:30, market:4 |
| `Chassis._hand_align` | 507-514 (8) | executor:5 |
| `Chassis._weed_repair` | 517-562 (46) | executor:12, production:10 |
| `Chassis._projected_shed` | 565-598 (34) | executor:3, market:1 |
| `Chassis._apply_suppression` | 602-616 (15) | market:18, endgame:4, executor:3 |
| `Chassis._add_sell` | 619-629 (11) | market:13, executor:2 |
| `Chassis._sell_lead` | 631-660 (30) | market:7, executor:5, production:4, shop-routing:2 |
| `Chassis._front_run` | 662-690 (29) | market:11, executor:5, production:4, opponent:2, endgame:1 |
| `Chassis._block_requirements` | 693-749 (57) | production:15, executor:2, market:1 |
| `Chassis._budget_guard` | 751-796 (46) | market:18, executor:8 |
| `Chassis._room_guard` | 799-852 (54) | production:8, executor:7, market:6 |
| `Chassis._clamp_sells` | 856-876 (21) | market:7, executor:3, opponent:1, production:1 |
| `Chassis._dead_stock` | 879-897 (19) | market:8, executor:7 |
| `Chassis._terminal_liquidation` | 900-906 (7) | market:4, executor:2, endgame:1 |
| `FarmView.__init__` | 1218-1218 (1) | none |
| `FarmView.inventory` | 1219-1219 (1) | market:1 |
| `_R149CopyProxy.__getattr__` | 3357-3357 (1) | none |

## 4. Candidate architectural seams

Relatively concentrated functions/methods. Inspect these first when separating production planning from market execution.

- `agent` lines 1054-1102: dominant **market**, purity=1.00; market:1
- `_is_noop` lines 330-375: dominant **production**, purity=1.00; production:10
- `agent` lines 1870-1903: dominant **executor**, purity=1.00; executor:5
- `agent` lines 3310-3327: dominant **executor**, purity=1.00; executor:6
- `agent` lines 3025-3041: dominant **production**, purity=1.00; production:1
- `agent` lines 3174-3189: dominant **production**, purity=1.00; production:1
- `_r37_market_price` lines 1748-1762: dominant **market**, purity=1.00; market:7
- `agent` lines 1913-1927: dominant **market**, purity=1.00; market:1
- `_r70_before` lines 2450-2464: dominant **production**, purity=1.00; production:1
- `_r44_before` lines 1835-1848: dominant **opponent**, purity=1.00; opponent:4
- `agent` lines 1706-1718: dominant **executor**, purity=1.00; executor:6
- `agent` lines 2109-2119: dominant **market**, purity=1.00; market:1
- `_r128_food_need` lines 3096-3106: dominant **production**, purity=1.00; production:4
- `_r97_market_stock` lines 2748-2757: dominant **market**, purity=1.00; market:4
- `_race_town` lines 3399-3407: dominant **shop-routing**, purity=1.00; shop-routing:2
- `Chassis._state` lines 427-434: dominant **executor**, purity=1.00; executor:1
- `Chassis._hand_align` lines 507-514: dominant **executor**, purity=1.00; executor:5
- `agent` lines 1206-1211: dominant **market**, purity=1.00; market:1
- `_v219_walk` lines 1270-1274: dominant **executor**, purity=1.00; executor:2
- `_v231_new_state` lines 1530-1534: dominant **production**, purity=1.00; production:3
- `Chassis._route_action` lines 436-440: dominant **executor**, purity=1.00; executor:2
- `Chassis.act` lines 460-504: dominant **executor**, purity=0.88; executor:30, market:4
- `Chassis._add_sell` lines 619-629: dominant **market**, purity=0.87; market:13, executor:2
- `Chassis._block_requirements` lines 693-749: dominant **production**, purity=0.83; production:15, executor:2, market:1
- `_r128_service` lines 3108-3156: dominant **production**, purity=0.82; production:9, executor:2
- `_r62_input_start` lines 2388-2400: dominant **executor**, purity=0.80; executor:4, market:1
- `agent` lines 1468-1475: dominant **executor**, purity=0.80; executor:4, market:1
- `agent` lines 1498-1505: dominant **executor**, purity=0.80; executor:4, market:1
- `agent` lines 3617-3629: dominant **executor**, purity=0.78; executor:7, endgame:1, market:1
- `_r36_suppress` lines 1648-1655: dominant **market**, purity=0.77; market:10, executor:3

## 5. Cross-coupling hotspots

These units mix several concerns. Avoid threshold-only patches inside them unless the complete policy interaction is understood.

- `Chassis` lines 406-906: market:105, executor:104, production:42, endgame:7, opponent:4, shop-routing:2
- `_v231_controller` lines 1536-1618: production:43, market:24, shop-routing:8, executor:2
- `_v219_request` lines 1281-1336: production:26, market:21, executor:17, endgame:2
- `_r97_supply` lines 2786-2856: production:23, executor:15, endgame:12, market:11, shop-routing:4
- `_v219_worker` lines 1339-1391: production:37, executor:13, endgame:3
- `_r51_input_control` lines 2198-2259: production:21, executor:20, market:8
- `agent` lines 1394-1446: production:20, executor:17, market:5
- `_r51_close_warehouse` lines 2283-2332: production:14, executor:13, market:11, shop-routing:4
- `agent` lines 3501-3529: market:21, executor:11, production:9
- `_v233_request` lines 1955-1996: executor:13, production:12, market:11
- `_r51_input_path` lines 2167-2196: production:19, executor:9, market:3
- `_r53_labor_assignment` lines 2347-2374: executor:16, production:9, endgame:4, market:2
- `agent` lines 2053-2100: production:12, executor:7, market:7
- `_r124_seed_budget` lines 2882-2897: market:15, executor:6, production:5
- `_r148_overflow` lines 3206-3241: executor:9, endgame:8, market:8
- `_r37_quote_priority` lines 1781-1804: production:12, market:9, opponent:4
- `Chassis._apply_suppression` lines 602-616: market:18, endgame:4, executor:3
- `_r68_joint_plans` lines 2404-2423: executor:8, production:7, market:5, endgame:4
- `_r127_priority` lines 2995-3023: executor:12, production:8, market:3
- `_v234_rescue` lines 2031-2051: executor:12, production:8, market:3
- `_adv_frontload` lines 3602-3616: market:16, executor:5, opponent:2
- `_r36_reserve` lines 1660-1704: executor:10, market:10, production:2
- `_r148_seed_prefund` lines 3270-3307: executor:10, market:10, production:2
- `Chassis._front_run` lines 662-690: market:11, executor:5, production:4, opponent:2
- `_r79_tomato_fertilizer_worthwhile` lines 2498-2513: production:11, market:9, executor:2

## 6. High-frequency calls

- `get`: 552
- `int`: 234
- `len`: 229
- `max`: 160
- `sum`: 77
- `min`: 70
- `range`: 54
- `append`: 54
- `any`: 53
- `update`: 47
- `items`: 46
- `_get`: 45
- `dict`: 45
- `isinstance`: 42
- `_int`: 39
- `list`: 39
- `deepcopy`: 33
- `enumerate`: 29
- `values`: 25
- `abs`: 24
- `pop`: 22
- `getattr`: 20
- `tuple`: 19
- `set`: 15
- `FarmView`: 14
- `all`: 14
- `_r97_budget`: 13
- `projected_shed`: 12
- `bool`: 11
- `float`: 11
- `setdefault`: 11
- `_v219_walk`: 11
- `index`: 10
- `_r37_market_price`: 10
- `_r97_market_stock`: 9
- `_r97_delivery`: 9
- `_r127_fields`: 9
- `add`: 8
- `count`: 8
- `_r128_commands`: 8

## 7. Important keyword locations

- `SELL`: 98, 232, 233, 236, 237, 238, 266, 270, 279, 424, 431, 442, 443, 444, 453, 455, 480, 481, 484, 485, 486, 489, 494, 495, 600, 602, 603, 604, 606, 610 ... (155 lines)
- `BUY`: 731, 736, 739, 742, 756, 802, 827, 833, 834, 837, 859, 874, 964, 1265, 1311, 1313, 1323, 1324, 1325, 1480, 1488, 1531, 1540, 1546, 1587, 1605, 1676, 1690, 1939, 1951 ... (95 lines)
- `market`: 6, 226, 245, 261, 389, 390, 407, 452, 500, 566, 608, 614, 616, 620, 622, 626, 628, 645, 648, 672, 673, 679, 722, 762, 764, 794, 795, 796, 826, 828 ... (254 lines)
- `price`: 245, 254, 257, 279, 390, 653, 665, 677, 710, 733, 734, 736, 737, 740, 755, 771, 777, 778, 783, 786, 789, 791, 804, 841, 845, 881, 894, 896, 993, 1004 ... (86 lines)
- `shop`: 6, 17, 18, 20, 246, 635, 946, 950, 954, 955, 957, 979, 983, 1004, 1023, 1137, 1139, 1148, 1152, 1253, 1588, 1595, 1596, 1599, 1946, 2698, 3273, 3382, 3383, 3399 ... (34 lines)
- `town`: 246, 632, 954, 1253, 1588, 1946, 2698, 3375, 3399, 3418, 3426, 3439 (12 lines)
- `route`: 6, 17, 20, 223, 225, 227, 237, 407, 409, 410, 416, 417, 418, 424, 430, 436, 437, 442, 443, 444, 446, 455, 469, 470, 471, 472, 473, 479, 486, 488 ... (107 lines)
- `target`: 518, 1004, 1270, 1271, 1342, 1360, 1361, 1363, 1364, 1365, 1366, 1381, 1387, 1388, 1400, 1414, 1415, 1416, 1417, 1418, 1422, 1423, 1730, 1756, 1760, 1998, 2007, 2010, 2014, 2015 ... (62 lines)
- `cow`: 255, 256, 944, 1002, 1324, 1542, 1549, 1558, 1563, 1571, 1573, 1574, 1578, 1581, 1583, 1589, 1593, 1594, 1601, 1604, 1605, 1794, 1985, 2537, 2540, 2650, 2782 (27 lines)
- `sheep`: 255, 256, 1002, 1324, 1568, 1573, 1577, 1583, 1589, 1593, 1594, 1599, 1601, 1637, 1794, 1933, 1937, 1938, 1939, 1940, 1941, 1948, 1951, 1952, 1957, 1973, 1985, 1988, 1990, 1993 ... (53 lines)
- `goose`: 255, 256, 1002, 1324, 1573, 1583, 1593, 1594, 1794, 1985, 2537, 2540, 2650, 2782 (14 lines)
- `strawberry`: 253, 254, 259, 664, 1002, 1325, 1730, 1793, 1986, 2783, 2895, 3381, 3382, 3383, 3548 (15 lines)
- `tomato`: 253, 254, 1002, 1214, 1224, 1233, 1251, 1257, 1259, 1262, 1266, 1302, 1311, 1325, 1346, 1362, 1363, 1365, 1369, 1371, 1372, 1374, 1384, 1385, 1389, 1439, 1441, 1442, 1444, 1445 ... (42 lines)
- `carrot`: 253, 254, 1002, 1325, 1730, 1793, 1986, 2123, 2128, 2170, 2173, 2178, 2188, 2195, 2196, 2244, 2258, 2268, 2406, 2408, 2783, 2895, 3381, 3383, 3548 (25 lines)
- `melon`: 253, 254, 259, 664, 1002, 1325, 1730, 1793, 1986, 2783, 2895, 3381, 3492, 3548 (14 lines)
- `wheat`: 253, 254, 370, 634, 650, 714, 715, 739, 859, 964, 1002, 1325, 1682, 1730, 1793, 1946, 1973, 1977, 1986, 2011, 2012, 2021, 2035, 2040, 2041, 2044, 2046, 2048, 2123, 2128 ... (122 lines)
- `milk`: 253, 259, 664, 1002, 1532, 1534, 1566, 1595, 1599, 1600, 1607, 1609, 1610, 1613, 1615, 1629, 1730, 1794, 2540, 3381, 3382, 3383, 3548 (23 lines)
- `wool`: 253, 259, 664, 1002, 1600, 1730, 1794, 1940, 1946, 2004, 2058, 2068, 2072, 2094, 2099, 2540, 3381, 3382, 3548 (19 lines)
- `egg`: 253, 944, 1002, 1730, 1794, 2540, 3381, 3382, 3548 (9 lines)
- `fertilizer`: 253, 364, 371, 372, 634, 650, 717, 718, 739, 820, 1002, 1004, 1302, 1306, 1308, 1312, 1313, 1320, 1328, 1347, 1351, 1352, 1355, 1356, 1357, 1368, 1369, 1378, 1413, 1414 ... (86 lines)
- `terminal`: 15, 18, 238, 272, 498, 499, 899, 900, 901, 948, 969, 995, 1004, 1007, 1009, 1010, 1025, 1058, 1059, 1060, 1061, 1062, 1066, 1072, 1073, 1081, 1083, 1087, 1089, 1093 ... (40 lines)
- `horizon`: 1004, 1666, 1865, 1878, 1884, 1888, 1889, 1892, 2649, 2662, 3365, 3373, 3376, 3378, 3379, 3380, 3385, 3442, 3443, 3444, 3447, 3448, 3457, 3458, 3459, 3465, 3471, 3472, 3473 (29 lines)
- `front`: 233, 259, 267, 413, 480, 487, 488, 600, 662, 674, 755, 948, 3545, 3602, 3610, 3612, 3613, 3615, 3623 (19 lines)
- `liquid`: 238, 272, 498, 499, 899, 900, 948, 1004, 1013, 1023, 1041, 1080, 1149, 1317 (14 lines)
- `worker`: 1004, 1224, 1229, 1261, 1289, 1291, 1305, 1307, 1308, 1328, 1339, 1399, 1407, 1413, 1414, 1415, 1416, 1418, 1419, 1421, 1426, 1429, 1432, 1434, 1454, 1524, 1557, 1559, 1585, 1638 ... (53 lines)
- `hand`: 226, 230, 241, 261, 264, 394, 401, 476, 477, 506, 507, 508, 509, 512, 513, 514, 525, 529, 562, 574, 704, 780, 809, 913, 932, 933, 948, 977, 990, 1002 ... (122 lines)

## 8. Top-level state/constants

`PRODUCTS`, `SEED_PRICE`, `ANIMAL_COST`, `ANIMAL_STRUCTURE`, `LAND_PRICES`, `MOVES`, `FRONT_RUN_ITEMS`, `LAST_ACT_STEP`, `PASS_ACTION`, `DEFAULT_SETTINGS`, `_R108_DATA`, `_ROUTES`, `_R108_SHOP_ROUTES`, `_SETTINGS`, `_R110_OLD_SHOPS`, `_R42_OPENING`, `_IMPL`, `_SHOP_PARENT`, `_UNIT_NS`, `_PLANNER_NS`, `_PRE_TERMINAL_AGENT`, `_TERMINAL_PLANS`, `_TERMINAL_PREVIOUS`, `_UPGRADE_STATS`, `_PRE_ROOM_AGENT`, `_ROOM_STATS`, `_V28_CORE`, `MAX_ORDERS`, `CROP_MIN_PRICE`, `_V219_PARENT`, `_V219_FERTILIZE`, `_V219_STATES`, `_V219_REPORT`, `_ORIGINAL_SHADOW_TERMINAL`, `APPLY_TIMING`, `_EXPERIMENT_PARENT`, `_ORDER_PARENT`, `_V31_CORE`, `_V231_PARENT`, `_V231_CAP`, `_V231_STATES`, `_V231_REPORT`, `_R36_SALE_PARENT`, `_R36_NATIVE_LEAD`, `_R36_NATIVE_SUPPRESS`, `_R36_SALE_REPORT`, `agent`, `_R37_MARKET_PARAMS`, `_R37_PRICE_FLOOR`, `_R37_HINGE_GAIN`, `_R44_PROBES`, `_R44_REPORT`, `_R37_ADAPTIVE`, `_R37_QUOTE`, `_R37_PARENT`, `_R37_PLAYERS`, `_R37_HORIZONS`, `_R37_REPORT`, `_R37_STATS`, `_RELEASE_PARENT`, `_RELEASE_REPORT`, `_RELEASE_ERRORS`, `agent`, `_V233_PARENT`, `_V233_STATES`, `_V233_REPORT`, `_R46_SHEEP_AGENT`, `_R46_SHADOW_PARENT`, `_R46_REPORT`, `agent`, `_R51_INPUT_PARENT`, `_R51_INPUT_STATES`, `_R51_INPUT_REPORT`, `_R51_INPUT_MAX_WORKERS`, `_R51_INPUT_CROPS`, `agent`, `_R51_WAREHOUSE_PARENT`, `_R51_WAREHOUSE_REPORT`, `agent`, `_R53_LABOR_REPORT`, `_R53_LABOR_PARENT`, `_R53_LABOR_COMBINED`, `agent`, `agent`, `agent`, `_R70_STATES`, `_R70_REPORT`, `_R70_PARENT`, `agent`, `agent`, `_R85_FEED`, `_R85_FERT`, `_R85_PARENT`, `_R85_STATES`, `_R85_REPORT`, `agent`, `_R86_FEED_CACHE`, `agent`, `_R88_PHASE`, `_R88_HORIZON`, `_R88_ANIMAL_DAYS`, `agent`, `_R95_PARENT`, `_R95_REPORT`, `_R95_RESERVES`, `agent`, `_R97_PARENT`, `_R97_REPORT`, `_R97_LAST`, `agent`, `_R124_PARENT`, `_R124_STATES`, `_R124_REPORT`, `agent`, `_R127_PARENT`, `_R127_STATES`, `_R127_REPORT`, `agent`, `_R128_PARENT`, `_R128_STATES`, `_R128_REPORT`, `agent`, `_R148_OVERFLOW`, `_R148_SEEDS`, `_R148_PARENT`, `_R148_REPORT`, `_R148_PENDING`, `agent`, `_R149_COPY`, `_R149_ATOMIC`, `_R149_MISSING`, `copy`, `agent`, `agent`, `_RACE_PARENT`, `_RACE_HORIZON_CLONE`, `_RACE_HORIZON_ESCALATED`, `_RACE_HORIZON_MIRROR`, `_RACE_ITEMS`, `_RACE_SHOPS`, `_RACE_STATE`, `_RACE_REPORT`, `_RACE_ORIG_RESERVE`, `agent`, `_OPEN_PARENT`, `_OPEN_UNITS`, `_OPEN_FEED_STEP1`, `_OPEN_STEP0`, `_OPEN_ATTACK`, `_OPEN_ATTACK_MIN_CASH`, `_OPEN_REPORT`, `agent`, `_ADV_PARENT`, `_ADV_LOOK`, `_ADV_FROM`, `_ADV_TO`, `_ADV_PROTECT`, `_ADV_FRONT`, `_ADV_BOOK`, `_ADV_SUBTRACT_DEBTS`, `_ADV_ITEMS`, `_ADV_REPORT`, `agent`

## 9. E22 design rule

Do **not** create E22 by changing one threshold only because it improves E21 head-to-head. E22 must represent a complete strategy hypothesis.

The intended next hypothesis is: preserve frontier-grade market execution while introducing a coherent shop-conditioned production policy, then judge it on population-level W/D/L rather than E21 head-to-head alone.

The next step is to inspect the highest-value seams/hotspots above and choose the smallest architecturally complete block that can support a separate shop-routed production policy.
