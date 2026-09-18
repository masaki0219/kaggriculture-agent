# E24 Corrected M-Family Replay-Router — Fresh Screen

- Generated: `2026-09-18T17:09:04+09:00`
- Fresh seeds: `25000..25007`
- Smoke max reward: **16803**
- Errors: **0**

E24 fixes E23's replay state/action alignment and preserves donor cash-flow timing.
Reward margin is diagnostic only.

## Per-opponent

| Opponent | W-D-L | Score | Reward mean | Margin (diag) |
|---|---:|---:|---:|---:|
| `e21` | 0-0-16 | 0.0% | 7788 | -159550 |
| `e22` | 0-0-16 | 0.0% | 7785 | -159530 |
| `aurax7_v7` | 0-0-16 | 0.0% | 1 | -166052 |
| `ahmed_v44` | 0-0-16 | 0.0% | 1 | -167004 |
| `kaito43` | 0-0-16 | 0.0% | 5257 | -143488 |
| `tetsu_shape` | 0-0-16 | 0.0% | 9808 | -145660 |

## Aggregate

- W-D-L: **0-0-96**
- Unweighted panel score: **0.0%**

## Decision gate

- If rewards are now economically normal but W/L is poor, the M-family hypothesis is being tested meaningfully and v1 can be rejected/retained on strategy grounds.
- If rewards are still near zero, E24 remains an implementation failure; do not infer anything about M-family quality.
- If E24 is competitive on several frontier opponents with a distinct W/L pattern, keep the M-family track and move to population-weighted evaluation.
- Do not patch individual seeds.
