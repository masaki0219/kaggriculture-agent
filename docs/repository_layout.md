# Repository layout

| Path | Responsibility |
| --- | --- |
| `experiments/` | Immutable numbered experiment history and legacy v/h series |
| `evaluation/` | Experiment-independent arenas and recorded evaluation output |
| `analysis/` | Diagnostics and one-off research analysis |
| `public_agents/` | External Git submodules; paths and pinned SHAs are unchanged |
| `artifacts/` | Canonical current bundle and byte-preserved submissions/snapshots |
| `archive/` | Superseded bundles, intermediary packages, and retained duplicates |
| `data/` | Downloaded/cache data and dated compressed replay corpora |
| `tools/` | Acquisition, setup, and bundle-maintenance utilities |
| `docs/` | Current project records, cleanup reports, and dated history |

The active elite runtime is `artifacts/bundles/current/`. For E21-E29, each
experiment directory contains its builder/screen/results and a lightweight
`agent.py` forwarding module for the frozen canonical agent in that runtime
bundle. New strategy work must use the next unused E number; do not rewrite an
executed experiment's agent, cache, or result.

## Canonical files for the next README update

| Role | Canonical path |
| --- | --- |
| Current frozen frontier reference | `artifacts/bundles/current/agent_e21_tetsu_market_v23.py` |
| Historical strong baseline | `artifacts/bundles/current/agent_e11_prvsiyan_frontier.py` |
| Current M-family research snapshot | `artifacts/bundles/current/agent_e29_m_family_staged_opening.py` |
| Latest evaluated experiment | `experiments/e029_m_family_staged_opening/` |
| Experiment history | `docs/experiment_run_history.md` |
| Experiment index | `docs/experiment_index.md` |
| Live-population replay archive | `data/replays/2026-09-18/live_population.zip` |
| M-family replay archive | `data/corpora/2026-09-18/m_family.zip` |

No E30 file is present. Do not describe E30 as executed or evaluated.
