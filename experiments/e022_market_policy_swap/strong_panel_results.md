# E21 vs E22 — Strong Common Panel

- Generated: `2026-09-18T15:58:57+09:00`
- Fresh seeds: `23000..23007`
- Frontier opponents: `aurax7_v7`, `ahmed_v44`, `kaito43`, `kaito27`, `tetsu_shape`, `farming_v4`
- Legacy opponents: `kaito58`, `boatlee29`
- Errors: **0**

Both E21 and E22 faced the exact same opponent set, seeds, and both seats.
Primary comparison is the frontier-tier common panel. Legacy results are diagnostic.
Reward margin is diagnostic only.

## 1. Per-opponent results

| Candidate | Tier | Opponent | W-D-L | Score | Margin (diag) |
|---|---|---|---:|---:|---:|
| `e21` | frontier | `aurax7_v7` | 15-0-1 | 93.8% | +1073 |
| `e21` | frontier | `ahmed_v44` | 14-0-2 | 87.5% | +1286 |
| `e21` | frontier | `kaito43` | 16-0-0 | 100.0% | +29342 |
| `e21` | frontier | `kaito27` | 16-0-0 | 100.0% | +32332 |
| `e21` | frontier | `tetsu_shape` | 14-0-2 | 87.5% | +15656 |
| `e21` | frontier | `farming_v4` | 16-0-0 | 100.0% | +4208 |
| `e21` | legacy | `kaito58` | 16-0-0 | 100.0% | +16837 |
| `e21` | legacy | `boatlee29` | 16-0-0 | 100.0% | +20536 |
| `e22` | frontier | `aurax7_v7` | 15-0-1 | 93.8% | +586 |
| `e22` | frontier | `ahmed_v44` | 14-0-2 | 87.5% | +1230 |
| `e22` | frontier | `kaito43` | 16-0-0 | 100.0% | +29392 |
| `e22` | frontier | `kaito27` | 16-0-0 | 100.0% | +32382 |
| `e22` | frontier | `tetsu_shape` | 14-0-2 | 87.5% | +15772 |
| `e22` | frontier | `farming_v4` | 16-0-0 | 100.0% | +4047 |
| `e22` | legacy | `kaito58` | 16-0-0 | 100.0% | +16761 |
| `e22` | legacy | `boatlee29` | 16-0-0 | 100.0% | +20513 |

## 2. Common-panel aggregate

| Candidate | Frontier W-D-L | Frontier score | Legacy W-D-L | Legacy score |
|---|---:|---:|---:|---:|
| `e21` | 91-0-5 | 94.8% | 32-0-0 | 100.0% |
| `e22` | 91-0-5 | 94.8% | 32-0-0 | 100.0% |

## 3. E22 minus E21 by opponent

| Opponent | Tier | E21 score | E22 score | Delta |
|---|---|---:|---:|---:|
| `aurax7_v7` | frontier | 93.8% | 93.8% | +0.000 |
| `ahmed_v44` | frontier | 87.5% | 87.5% | +0.000 |
| `kaito43` | frontier | 100.0% | 100.0% | +0.000 |
| `kaito27` | frontier | 100.0% | 100.0% | +0.000 |
| `tetsu_shape` | frontier | 87.5% | 87.5% | +0.000 |
| `farming_v4` | frontier | 100.0% | 100.0% | +0.000 |
| `kaito58` | legacy | 100.0% | 100.0% | +0.000 |
| `boatlee29` | legacy | 100.0% | 100.0% | +0.000 |

## 4. Decision gate

- E22 better than E21 on frontier opponents: **0**
- E22 worse than E21 on frontier opponents: **0**
- Equal: **6**

- If E22 is better/equal on most frontier opponents despite losing direct H2H to E21, keep E22 as a serious second-track candidate.
- If E22 is worse on most frontier opponents, reject E22; do not patch it seed-by-seed.
- If results are mixed, retain E21 as the generalist and use current leaderboard/replay population evidence to decide whether E22's market regime is sufficiently prevalent to justify the second active slot.
- The two final submissions are a hedge over uncertainty in population-level BT; their match-specific strengths are not combined.

Final objective remains maximum leaderboard Bradley–Terry / W-D-L over the unknown active population.
