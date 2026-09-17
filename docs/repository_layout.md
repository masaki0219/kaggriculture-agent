# Repository layout

| Path | Responsibility |
| --- | --- |
| `experiments/` | Immutable numbered experiment history and legacy v/h series |
| `evaluation/` | Experiment-independent arenas and recorded evaluation output |
| `analysis/` | Diagnostics and one-off research analysis |
| `public_agents/` | External Git submodules; paths and pinned SHAs are unchanged |
| `artifacts/` | Canonical current bundle and byte-preserved submissions/snapshots |
| `archive/` | Superseded bundles, intermediary packages, and retained duplicates |
| `data/` | Downloaded/cache data such as dated meta snapshots |
| `tools/` | Acquisition, setup, and bundle-maintenance utilities |
| `docs/` | Reorganization record, manifest, experiment index, and README TODO |

The active elite runtime is `artifacts/bundles/current/`. New strategy work must
use the next unused E number; do not rewrite an executed experiment's agent,
cache, or result.
