# Current Frontier Screen

- Generated: `2026-09-18T15:02:22+09:00`
- Candidates: `e21`, `ahmed_v44`, `aurax7_v7`
- RR seeds: `20000..20015`
- Fixed-panel seeds: `21000..21007`
- Errors: **0**

Primary purpose: identify the strongest current public baseline before E22.
Reward margin is diagnostic only; W/D/L score is primary.

## 1. Direct current-frontier round robin

| Matchup | W-D-L from left perspective | Score | Margin (diag) |
|---|---:|---:|---:|
| `e21` vs `ahmed_v44` | 26-0-6 | 81.2% | +426 |
| `e21` vs `aurax7_v7` | 20-0-12 | 62.5% | +227 |
| `ahmed_v44` vs `aurax7_v7` | 1-0-31 | 3.1% | -812 |

## 2. Direct-round-robin candidate summary

Each candidate is evaluated only on the two direct frontier opponents.

| Candidate | W-D-L | Score |
|---|---:|---:|
| `e21` | 46-0-18 | 71.9% |
| `ahmed_v44` | 7-0-57 | 10.9% |
| `aurax7_v7` | 43-0-21 | 67.2% |

## 3. Common fixed panel

All candidates face the exact same opponents, seeds, and both seats.

| Candidate | W-D-L | Score | Worst opponent score | Margin (diag) |
|---|---:|---:|---:|---:|
| `e21` | 80-0-0 | 100.0% | 100.0% | +49184 |
| `ahmed_v44` | 80-0-0 | 100.0% | 100.0% | +49850 |
| `aurax7_v7` | 80-0-0 | 100.0% | 100.0% | +50024 |

## 4. Per-opponent common-panel score

| Candidate | e11 | shape_top10 | kaito58 | boatlee29 | adaptive_route_v2 |
|---|---:|---:|---:|---:|---:|
| `e21` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| `ahmed_v44` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| `aurax7_v7` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

## 5. Baseline decision gate

- Local direct-RR order for this screen: `e21` > `aurax7_v7` > `ahmed_v44`
- Use this only to choose the **development baseline**, not as a final-leaderboard prediction.
- If one candidate clearly leads direct RR and is not worse on the common panel, freeze it as the new frontier baseline.
- If the direct RR is mixed/non-transitive, keep multiple frontier baselines and design E22 against their shared failure modes.
- Final objective remains population-level W/D/L / Bradley–Terry over the unknown active leaderboard population.
