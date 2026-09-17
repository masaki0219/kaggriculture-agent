# Experiment index

This index records only claims supported by the checked-in agent headers,
README, caches, and results. `unknown` is used instead of reconstructing intent
from filenames. E numbers are immutable and no missing number is collapsed.

| Experiment | Agent / purpose | Current path | Arena | Cache / results | Status |
| --- | --- | --- | --- | --- | --- |
| E1 | Kaito58 exact public agent | `artifacts/bundles/current/agent_e1_kaito58.py` | `artifacts/bundles/current/elite_arena.py` | `elite_arena_cache.json`; resilient results | historical |
| E2 | Boatlee29-R1 exact public agent | `artifacts/bundles/current/agent_e2_boatlee29.py` | elite arena / E11 confirmation | elite/focused/final-confirmation caches | historical |
| E3 | Shape-the-Shop TOP10 exact public agent | `artifacts/bundles/current/agent_e3_shape_top10.py` | elite arena | `elite_arena_cache.json` | unknown |
| E4 | Adaptive Route V2 exact public agent | `artifacts/bundles/current/agent_e4_adaptive_route_v2.py` | elite arena | `elite_arena_cache.json` | unknown |
| E5 | Kaito58 with one-turn premium-sale phase shift | `artifacts/bundles/current/agent_e5_kaito58_shift1.py` | elite arena | `elite_arena_cache.json` | unknown |
| E6 | Boatlee29 with market-collision guard | `artifacts/bundles/current/agent_e6_boatlee29_guard.py` | elite arena | `elite_arena_cache.json`; resilient results | rejected |
| E7 | Tetsu Shape benchmark wrapper | `artifacts/bundles/current/agent_e7_tetsu_shape.py` | elite arena | `elite_arena_cache.json` | unresolved (license re-check) |
| E8 | Farming Score V4 benchmark wrapper | `artifacts/bundles/current/agent_e8_farming_v4.py` | elite arena | `elite_arena_cache.json` | unresolved (license re-check) |
| E9 | Boatlee29 with town-conditioned tomato substitution | `artifacts/bundles/current/agent_e9_boatlee29_tomato.py` | elite arena | `elite_arena_cache.json` | rejected |
| E10 | Kaito27 exact public agent | `artifacts/bundles/current/agent_e10_kaito27_current.py` | elite arena / E11 confirmation | elite/final-confirmation caches | rejected as promoted candidate; retained historical exact baseline |
| E11 | Prvsiyan Frontier exact public agent | `artifacts/bundles/current/agent_e11_prvsiyan_frontier.py` | elite, focused, final-confirmation, E17-E20, population arenas | bundle caches/results and experiment caches/results | frozen baseline / submitted |
| E12 | Kaito43 Sparse Shop Hybrid exact public agent | `artifacts/bundles/current/agent_e12_kaito43_current.py` | elite arena / E11 confirmation | elite/final-confirmation caches | rejected as promoted candidate; retained historical exact baseline |
| E13 | Kaito27 with collision guard | `artifacts/bundles/current/agent_e13_kaito27_guard.py` | elite arena | `elite_arena_cache.json`; resilient results | rejected |
| E14 | E11 with MILK guard | `artifacts/bundles/current/agent_e14_prvsiyan_milkguard.py` | `e11_focused_arena.py` | `e11_focused_cache.json`; `e11_focused_results.json` | rejected |
| E15 | E11 with FERTILIZER guard | `artifacts/bundles/current/agent_e15_prvsiyan_fertguard.py` | `e11_focused_arena.py` | `e11_focused_cache.json`; `e11_focused_results.json` | rejected |
| E16 | E11 with anti-clone guard | `artifacts/bundles/current/agent_e16_prvsiyan_cloneguard.py` | `e11_focused_arena.py` | `e11_focused_cache.json`; `e11_focused_results.json` | rejected |
| E17 | E11 idle-hand crop rescue | `artifacts/bundles/current/agent_e17_prvsiyan_idle_water.py` | `artifacts/bundles/current/e17_ab_arena.py` | bundle E17 cache/results; `experiments/e017_idle_water/cache_root_fragment.json` | rejected / no-op |
| E18 | Conservative late-shop reroute using existing E11 plans | `experiments/e018_late_shop/agent.py` | `experiments/e018_late_shop/arena.py` | sibling `cache.json`; `results.json` | rejected |
| E19 | Early SW prebuild without changing the selected E11 tape | `experiments/e019_early_sw/agent.py` | `experiments/e019_early_sw/arena.py` | sibling `cache.json`; `results.json` | unresolved mechanism / not promoted |
| E20 | Early SW prebuild with native strawberry-seed prefetch | `experiments/e020_early_sw/agent.py` | `experiments/e020_early_sw/arena.py` | sibling `cache.json`; `results.json` | rejected / not promoted |

## Legacy non-E series

- `experiments/legacy/v_series/` preserves v2-v15, including diagnostics,
  compare scripts, round-robin output, and analysis JSON. v/h identifiers remain
  unchanged.
- `experiments/legacy/h_series/` preserves h1-h4, their comparisons, and economy
  traces.
- These series are historical evidence. A future strategy change must receive a
  new E number instead of repurposing one of these files.
