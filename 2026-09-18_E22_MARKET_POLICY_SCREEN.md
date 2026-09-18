# E22 Market Policy Screen

- Generated: `2026-09-18T15:40:03+09:00`
- Fresh seeds: `22000..22011`
- Games: **72**
- Errors: **0**

E22 changes only the final ADV market-policy block relative to E21.
W/D/L is primary; reward margin is diagnostic only.

| Matchup | W-D-L from E22 perspective | Score | Margin (diag) |
|---|---:|---:|---:|
| `e22` vs `e21` | 6-0-18 | 25.0% | -251 |
| `e22` vs `aurax7_v7` | 24-0-0 | 100.0% | +34 |
| `e22` vs `ahmed_v44` | 24-0-0 | 100.0% | +557 |

## Decision rule

- If E22 improves against aurax but loses materially to E21 on fresh seeds, the aurax market block is a hedge mechanism, not a new generalist baseline.
- If E22 is competitive with E21 and improves against aurax/Ahmed, promote it to broader population testing.
- If E22 loses broadly, reject E22 and keep E21; do not patch this experiment seed-by-seed.
- Do not use reward margin as the promotion criterion.

Final objective remains population-level W/D/L / Bradley–Terry.
