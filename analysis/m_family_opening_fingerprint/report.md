# M-family Opening Fingerprint

- Generated: `2026-09-18T21:06:47+09:00`
- Corpus: `data/corpora/2026-09-18/m_family.zip`
- Resolved M-family player-runs: **84**
- Unresolved seats: **0**
- Malformed replay files: **0**

Final objective: identify reusable mechanisms that can improve an independent leaderboard candidate; exact replay imitation is not the objective.

## 1. Coverage

| Team | Runs |
|---|---:|
| Majkel1337 | 12 |
| DSM | 12 |
| Orbital Terraformer | 12 |
| ymg_aq | 12 |
| QQ | 12 |
| Arda Ceylan | 12 |
| kwa | 12 |

## 2. Opening state checkpoints

Medians with interquartile range across resolved M-family player-runs.

| Step | Crops | Structures | Animals | Hands | Q | Money |
|---:|---:|---:|---:|---:|---:|---:|
| 23 | 15.5 [15.0, 16.0] | 5.0 [5.0, 5.0] | 5.0 [5.0, 5.0] | 4.0 [4.0, 4.0] | 1.0 [1.0, 1.0] | 7.0 [5.0, 8.2] |
| 47 | 19.0 [19.0, 20.0] | 5.0 [5.0, 5.0] | 5.0 [5.0, 5.0] | 4.0 [4.0, 4.0] | 1.0 [1.0, 1.0] | 60.0 [32.0, 61.2] |
| 71 | 20.0 [20.0, 20.0] | 5.0 [5.0, 5.0] | 5.0 [5.0, 5.0] | 6.0 [6.0, 6.0] | 1.0 [1.0, 1.0] | 19.0 [16.0, 20.2] |
| 143 | 20.0 [20.0, 20.0] | 5.0 [5.0, 5.0] | 5.0 [5.0, 5.0] | 6.0 [6.0, 6.0] | 1.0 [1.0, 1.0] | 792.5 [727.0, 841.8] |

## 3. Window-level semantic agreement

Execution collapses NORTH/SOUTH/EAST/WEST into MOVE and ignores SELL orders. Economic additionally drops MOVE/PASS, so it asks whether the same productive/market program is being executed even when routing differs.

| Window | Execution mean top-share | Economic mean top-share | Economic team agreement | Economic steps >=50% |
|---|---:|---:|---:|---:|
| 0-23 | 54.8% | 54.8% | 53.6% | 7/24 |
| 24-47 | 34.9% | 38.0% | 46.4% | 1/24 |
| 48-71 | 41.4% | 43.3% | 56.5% | 7/24 |

## 4. Selected milestone timing

Tight IQR means the event occurs at nearly the same time across runs. A wide range with a tight team-specific median suggests subfamily behavior rather than one universal script.

| Milestone | N | Median step | IQR | Min-Max | Team medians |
|---|---:|---:|---:|---:|---|
| `hire_1` | 84 | 2.0 | 0.0 | 2-2 | Arda Ceylan:2.0, DSM:2.0, Majkel1337:2.0, Orbital Terraformer:2.0, QQ:2.0, kwa:2.0, ymg_aq:2.0 |
| `hire_2` | 84 | 2.0 | 0.0 | 2-2 | Arda Ceylan:2.0, DSM:2.0, Majkel1337:2.0, Orbital Terraformer:2.0, QQ:2.0, kwa:2.0, ymg_aq:2.0 |
| `hire_3` | 84 | 2.0 | 0.0 | 2-2 | Arda Ceylan:2.0, DSM:2.0, Majkel1337:2.0, Orbital Terraformer:2.0, QQ:2.0, kwa:2.0, ymg_aq:2.0 |
| `hire_4` | 84 | 2.0 | 0.0 | 2-2 | Arda Ceylan:2.0, DSM:2.0, Majkel1337:2.0, Orbital Terraformer:2.0, QQ:2.0, kwa:2.0, ymg_aq:2.0 |
| `hire_5` | 84 | 25.0 | 0.0 | 25-25 | Arda Ceylan:25.0, DSM:25.0, Majkel1337:25.0, Orbital Terraformer:25.0, QQ:25.0, kwa:25.0, ymg_aq:25.0 |
| `hire_6` | 84 | 25.0 | 0.0 | 25-25 | Arda Ceylan:25.0, DSM:25.0, Majkel1337:25.0, Orbital Terraformer:25.0, QQ:25.0, kwa:25.0, ymg_aq:25.0 |
| `cow_buy_1` | 84 | 1.0 | 0.0 | 1-1 | Arda Ceylan:1.0, DSM:1.0, Majkel1337:1.0, Orbital Terraformer:1.0, QQ:1.0, kwa:1.0, ymg_aq:1.0 |
| `cow_buy_2` | 84 | 2.0 | 0.0 | 2-2 | Arda Ceylan:2.0, DSM:2.0, Majkel1337:2.0, Orbital Terraformer:2.0, QQ:2.0, kwa:2.0, ymg_aq:2.0 |
| `sheep_buy_1` | 84 | 2.0 | 0.0 | 2-2 | Arda Ceylan:2.0, DSM:2.0, Majkel1337:2.0, Orbital Terraformer:2.0, QQ:2.0, kwa:2.0, ymg_aq:2.0 |
| `sheep_buy_2` | 84 | 2.0 | 0.0 | 2-2 | Arda Ceylan:2.0, DSM:2.0, Majkel1337:2.0, Orbital Terraformer:2.0, QQ:2.0, kwa:2.0, ymg_aq:2.0 |
| `sheep_buy_3` | 84 | 2.0 | 0.0 | 2-2 | Arda Ceylan:2.0, DSM:2.0, Majkel1337:2.0, Orbital Terraformer:2.0, QQ:2.0, kwa:2.0, ymg_aq:2.0 |
| `pasture_build_1` | 84 | 3.0 | 0.0 | 3-3 | Arda Ceylan:3.0, DSM:3.0, Majkel1337:3.0, Orbital Terraformer:3.0, QQ:3.0, kwa:3.0, ymg_aq:3.0 |
| `pasture_build_2` | 84 | 5.0 | 0.0 | 5-6 | Arda Ceylan:5.0, DSM:5.0, Majkel1337:5.0, Orbital Terraformer:5.0, QQ:5.0, kwa:6.0, ymg_aq:5.0 |
| `pasture_build_3` | 84 | 6.0 | 0.0 | 6-7 | Arda Ceylan:6.0, DSM:6.0, Majkel1337:6.0, Orbital Terraformer:6.0, QQ:6.0, kwa:7.0, ymg_aq:6.0 |
| `pasture_build_4` | 84 | 7.0 | 0.0 | 7-8 | Arda Ceylan:7.0, DSM:7.0, Majkel1337:8.0, Orbital Terraformer:7.0, QQ:7.0, kwa:7.0, ymg_aq:7.0 |
| `pasture_build_5` | 84 | 8.0 | 0.0 | 8-9 | Arda Ceylan:8.0, DSM:8.0, Majkel1337:9.0, Orbital Terraformer:8.0, QQ:8.0, kwa:8.0, ymg_aq:8.0 |
| `melon_seed_1` | 84 | 7.0 | 0.0 | 4-7 | Arda Ceylan:7.0, DSM:7.0, Majkel1337:4.0, Orbital Terraformer:7.0, QQ:7.0, kwa:7.0, ymg_aq:7.0 |
| `melon_seed_6` | 84 | 12.0 | 0.0 | 9-12 | Arda Ceylan:12.0, DSM:12.0, Majkel1337:12.0, Orbital Terraformer:12.0, QQ:12.0, kwa:9.0, ymg_aq:12.0 |
| `melon_seed_12` | 83 | 58.0 | 3.0 | 35-228 | Arda Ceylan:58.0, DSM:58.0, Majkel1337:60.0, Orbital Terraformer:61.0, QQ:58.0, kwa:62.0, ymg_aq:58.0 |
| `melon_seed_14` | 33 | 134.0 | 187.0 | 38-290 | Arda Ceylan:38.0, DSM:61.0, Majkel1337:61.0, Orbital Terraformer:58.0, QQ:133.5, ymg_aq:248.0 |
| `melon_plant_1` | 84 | 11.0 | 1.0 | 9-11 | Arda Ceylan:11.0, DSM:11.0, Majkel1337:10.0, Orbital Terraformer:11.0, QQ:11.0, kwa:9.0, ymg_aq:11.0 |
| `melon_plant_6` | 84 | 14.0 | 0.0 | 13-15 | Arda Ceylan:14.0, DSM:14.0, Majkel1337:15.0, Orbital Terraformer:14.0, QQ:14.0, kwa:13.0, ymg_aq:14.0 |
| `melon_plant_12` | 84 | 39.0 | 25.2 | 37-177 | Arda Ceylan:39.0, DSM:39.0, Majkel1337:65.5, Orbital Terraformer:37.5, QQ:38.0, kwa:65.0, ymg_aq:37.0 |
| `melon_plant_14` | 59 | 62.0 | 3.0 | 62-230 | Arda Ceylan:62.0, DSM:62.0, Orbital Terraformer:62.5, QQ:62.0, ymg_aq:65.0 |
| `wheat_seed_1` | 84 | 14.0 | 1.0 | 13-14 | Arda Ceylan:14.0, DSM:14.0, Majkel1337:13.0, Orbital Terraformer:14.0, QQ:14.0, kwa:13.0, ymg_aq:14.0 |
| `wheat_seed_10` | 84 | 22.0 | 87.0 | 20-224 | Arda Ceylan:20.0, DSM:22.0, Majkel1337:22.0, Orbital Terraformer:20.0, QQ:22.0, kwa:218.0, ymg_aq:107.0 |
| `wheat_plant_1` | 84 | 16.0 | 2.0 | 14-17 | Arda Ceylan:17.0, DSM:16.0, Majkel1337:15.0, Orbital Terraformer:17.0, QQ:16.0, kwa:15.0, ymg_aq:16.0 |
| `wheat_plant_10` | 84 | 22.0 | 10.2 | 22-254 | Arda Ceylan:22.0, DSM:22.0, Majkel1337:23.0, Orbital Terraformer:22.0, QQ:22.0, kwa:233.5, ymg_aq:22.0 |

## 5. What is actually done in each 24-step block

| Window | `HIRE` median[IQR] | `BUY_ANIMAL:COW` median[IQR] | `BUY_ANIMAL:SHEEP` median[IQR] | `BUY_SEED:MELON` median[IQR] | `BUY_SEED:WHEAT` median[IQR] | `BUILD_PASTURE` median[IQR] | `PLANT:MELON` median[IQR] | `PLANT:WHEAT` median[IQR] | `WATER` median[IQR] | `MOVE` median[IQR] | `PASS` median[IQR] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0-23 | 4.0[4.0,4.0] | 2.0[2.0,2.0] | 3.0[3.0,3.0] | 6.0[6.0,6.0] | 10.0[9.0,11.0] | 5.0[5.0,5.0] | 8.0[6.0,8.0] | 11.0[9.8,11.0] | 18.0[18.0,19.0] | 42.0[41.0,43.0] | 4.0[3.8,6.0] |
| 24-47 | 6.0[5.0,9.0] | 0.0[0.0,0.0] | 0.0[0.0,0.0] | 4.5[4.0,5.0] | 0.0[0.0,0.0] | 0.0[0.0,0.0] | 4.0[4.0,4.0] | 0.0[0.0,0.0] | 23.0[21.0,25.0] | 58.0[56.0,60.0] | 6.0[4.8,9.0] |
| 48-71 | 6.0[6.0,6.0] | 0.0[0.0,0.0] | 0.0[0.0,0.0] | 2.0[2.0,2.0] | 0.0[0.0,0.0] | 0.0[0.0,0.0] | 2.0[2.0,2.0] | 0.0[0.0,0.0] | 28.0[27.0,32.0] | 90.0[86.0,92.0] | 8.0[6.0,9.2] |

## 6. Highest-agreement economic steps

| Step | Top share | Team agreement | Modal semantic action |
|---:|---:|---:|---|
| 0 | 100.0% | 7/7 | `units[-] market[-]` |
| 2 | 100.0% | 7/7 | `units[PICKUP:COWx1] market[BUY_ANIMAL:COW:1x1,BUY_ANIMAL:SHEEP:3x1,HIREx4]` |
| 1 | 85.7% | 6/7 | `units[-] market[BUY_ANIMAL:COW:1x1,BUY_PRODUCT:WHEAT:5x1]` |
| 26 | 83.3% | 6/7 | `units[PLACE:FERTILIZERx1] market[-]` |
| 51 | 79.8% | 6/7 | `units[COLLECT_FERTILIZERx1] market[-]` |
| 5 | 76.2% | 5/7 | `units[BUILD_PASTUREx1,PICKUP:WHEATx1] market[BUY_PRODUCT:WHEAT:1x1]` |
| 3 | 71.4% | 5/7 | `units[BUILD_PASTUREx1,PICKUP:COWx1,PICKUP:SHEEPx3] market[-]` |
| 4 | 71.4% | 5/7 | `units[PLACE:COWx1] market[BUY_PRODUCT:WHEAT:1x1]` |
| 6 | 71.4% | 5/7 | `units[BUILD_PASTUREx1,FEEDx1,PLACE:SHEEPx1] market[BUY_PRODUCT:WHEAT:1x1]` |
| 49 | 71.4% | 5/7 | `units[COLLECT_FERTILIZERx1] market[BUY_PRODUCT:WHEAT:1x1,HIREx6]` |
| 58 | 60.7% | 5/7 | `units[CAREx1,WATERx2] market[BUY_SEED:MELON:1x1]` |
| 48 | 59.5% | 5/7 | `units[-] market[-]` |
| 55 | 58.3% | 5/7 | `units[PICKUP:WHEATx1,WATERx1] market[-]` |
| 50 | 50.0% | 4/7 | `units[PICKUP:WHEATx1,PLACE:FERTILIZERx1] market[-]` |
| 71 | 50.0% | 5/7 | `units[-] market[-]` |
| 16 | 47.6% | 3/7 | `units[PLANT:WHEATx1,WATERx1] market[BUY_SEED:WHEAT:1x1]` |
| 17 | 46.4% | 3/7 | `units[PLANT:WHEATx3,WATERx1] market[BUY_SEED:WHEAT:1x1]` |
| 18 | 46.4% | 3/7 | `units[PLANT:WHEATx1,WATERx3] market[BUY_SEED:WHEAT:1x1]` |
| 19 | 46.4% | 3/7 | `units[PLANT:WHEATx1,WATERx1] market[BUY_SEED:WHEAT:1x1]` |
| 20 | 46.4% | 3/7 | `units[PLANT:WHEATx2,WATERx1] market[BUY_SEED:WHEAT:1x1]` |
| 21 | 46.4% | 3/7 | `units[WATERx2] market[BUY_SEED:WHEAT:1x1]` |
| 52 | 46.4% | 4/7 | `units[COLLECT_FERTILIZERx1,FEEDx1] market[-]` |
| 53 | 46.4% | 4/7 | `units[CAREx1,COLLECT_FERTILIZERx1,PLACE:FERTILIZERx1] market[-]` |
| 23 | 45.2% | 3/7 | `units[PLANT:WHEATx1,WATERx2] market[-]` |

## 7. Lowest-agreement economic steps

| Step | Top share | Team agreement | Modal semantic action |
|---:|---:|---:|---|
| 61 | 19.0% | 1/7 | `units[CAREx1,HARVESTx1,WATERx1] market[BUY_SEED:STRAWBERRY:1x1]` |
| 68 | 26.2% | 3/7 | `units[WATERx2] market[-]` |
| 22 | 27.4% | 2/7 | `units[PLANT:WHEATx1] market[-]` |
| 37 | 27.4% | 2/7 | `units[PLANT:MELONx1,WATERx1] market[-]` |
| 59 | 27.4% | 3/7 | `units[FEEDx1,PLACE:FERTILIZERx1,WATERx2] market[-]` |
| 65 | 28.6% | 3/7 | `units[PLANT:STRAWBERRYx1,WATERx3] market[BUY_SEED:STRAWBERRY:1x1]` |
| 70 | 28.6% | 3/7 | `units[WATERx4] market[-]` |
| 24 | 29.8% | 2/7 | `units[-] market[-]` |
| 32 | 29.8% | 3/7 | `units[PICKUP:WHEATx1,PLACE:FERTILIZERx1,WATERx1] market[-]` |
| 36 | 29.8% | 3/7 | `units[FEEDx2,PLANT:MELONx1,WATERx1] market[BUY_SEED:MELON:2x1]` |
| 38 | 29.8% | 3/7 | `units[CAREx1,PLANT:MELONx1,WATERx1] market[-]` |
| 39 | 29.8% | 3/7 | `units[PLANT:MELONx1,WATERx2] market[-]` |
| 35 | 31.0% | 3/7 | `units[PLANT:MELONx1] market[-]` |
| 42 | 31.0% | 3/7 | `units[WATERx1] market[-]` |
| 47 | 31.0% | 3/7 | `units[WATERx1] market[-]` |
| 63 | 32.1% | 5/7 | `units[HARVESTx1,WATERx4] market[-]` |
| 67 | 32.1% | 4/7 | `units[WATERx2] market[-]` |
| 69 | 32.1% | 4/7 | `units[WATERx2] market[-]` |
| 33 | 33.3% | 3/7 | `units[FEEDx1,PLACE:FERTILIZERx1] market[BUY_SEED:MELON:2x1]` |
| 40 | 34.5% | 4/7 | `units[WATERx2] market[-]` |
| 62 | 34.5% | 2/7 | `units[FEEDx1,PLANT:MELONx1,WATERx2] market[BUY_SEED:STRAWBERRY:1x1]` |
| 34 | 36.9% | 3/7 | `units[FEEDx1,PLANT:MELONx1] market[-]` |
| 45 | 38.1% | 4/7 | `units[WATERx1] market[-]` |
| 46 | 38.1% | 3/7 | `units[WATERx2] market[-]` |

## 8. Interpretation gate

- The first 24 steps have materially higher semantic agreement than the later blocks. This supports a **fixed/semi-fixed opening module followed by more state-dependent execution**.
- If hires / 2C3S / five pastures / melon planting milestones have tight timing across all seven teams, E30 should encode those milestones as a small opening state machine.
- If timing is tight only within particular teams, do not force one universal tape; keep a shared target system with subfamily/state branches.
- If plant milestones are tight but action consensus is low, the E29 bottleneck is likely **routing / parallel execution**, not missing economic targets.
- Only after opening fidelity improves should the next candidate be screened for population W/D/L.

## 9. Data quality

- Unresolved: 0
- Malformed: 0
