# Reorganization manifest

Reorganization date: 2026-09-18. Paths are relative to the repository root.
Unless a row explicitly says `path fix`, the move was byte-preserving. Directory
rows cover all files recursively; the frozen hashes below identify the most
important exact sources and submissions independently.

## Project-level map

| Old path | New path | Purpose | Experiment | Status | Origin | Mutability | Related cache/result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | `README.md` | historical project narrative | all | active documentation; moved links only | self | modifiable documentation | n/a |
| `.gitmodules` | `.gitmodules` | seven public-agent submodules | n/a | unchanged | external | frozen paths/SHAs for this task | n/a |
| `public_agents/` | `public_agents/` | external repositories | n/a | unchanged | external | do not modify here | external-owned |
| `meta_cache/` | `data/meta_cache/` | downloaded meta/replay data | n/a | historical data | external-derived | append-only/history | dated JSON + manifests |
| `kaggriculture_elite_bundle_PATCHED_v2/` | `artifacts/bundles/current/` | canonical elite runtime, E1-E17, raw exact sources, evaluation history | E1-E17 | current bundle | mixed external/self | frozen agents/raw/submissions; tooling path fixes only | all bundle caches/results |
| `kaggriculture_elite_bundle_FINAL/` | `archive/bundles/kaggriculture_elite_bundle_FINAL/` | superseded pre-patch bundle | E1-E13 | archived | mixed external/self | frozen history | `elite_arena_cache.json` |
| `kaggriculture_elite_bundle_PATCHED_v2.zip` | `artifacts/bundles/current_snapshot.zip` | original bundle zip snapshot | E1-E13 snapshot | artifact | mixed | frozen bytes | n/a |
| `kaggriculture_elite_bundle_FINAL.zip` | `archive/bundles/kaggriculture_elite_bundle_FINAL.zip` | superseded bundle zip | E1-E13 | archived | mixed | frozen bytes | n/a |

## Numbered experiments

| Old path | New path | SHA256 | Role | Experiment | Status | Origin | Mutability | Related history |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `e17_ab_cache.json` | `experiments/e017_idle_water/cache_root_fragment.json` | `044193390c76ed5dec2d367b5c7ba0db79b94bed29645fafe25ec68d52d41331` | separate root cache fragment | E17 | historical | self | frozen | canonical E17 history remains in current bundle |
| `agent_e18_prvsiyan_late_shop.py` | `experiments/e018_late_shop/agent.py` | `24c6864678023bfbba016d5cdaab14a482632987aeea4dca3b9637a549c7b330` | agent | E18 | rejected | self wrapper over external E11 | frozen | sibling cache/results |
| `e18_ab_arena.py` | `experiments/e018_late_shop/arena.py` | `88609d85a32a7126cec088b863e46420cc3afe6619c3d8a7110a0ad5059d3e4f` | arena | E18 | historical | self | modifiable tooling only | cache/results below |
| `e18_ab_cache.json` | `experiments/e018_late_shop/cache.json` | `8e329ab2240fb1aadb3bcf3e33336681bc3d6f86caa2b1425c55c4adbbc3e80b` | cache | E18 | historical | generated | frozen history | `results.json` |
| `e18_ab_results.json` | `experiments/e018_late_shop/results.json` | `8c566a3cde6dd1f7c76e4933ca051982ef5ad496d1141e7a10ac3bf58abc32d5` | results | E18 | historical | generated | frozen history | `cache.json` |
| `agent_e19_prvsiyan_early_sw.py` | `experiments/e019_early_sw/agent.py` | `899bfe8f065f1714da7ec6d9a5907efc242746406df2abdf4160b7255d15e8ea` | agent | E19 | unresolved/not promoted | self wrapper over external E11 | frozen | sibling cache/results |
| `e19_ab_arena.py` | `experiments/e019_early_sw/arena.py` | `c37e05be4cdd1815d577e77e5ba446f85dc8fd5e7bdbb8346bcf7b6b711cc073` | arena | E19 | historical | self | modifiable tooling only | cache/results below |
| `e19_ab_cache.json` | `experiments/e019_early_sw/cache.json` | `5ed28e5d2c530f30f3daf9977c02d0fd163a10157497f85eae178842731a9a07` | cache | E19 | historical | generated | frozen history | `results.json` |
| `e19_ab_results.json` | `experiments/e019_early_sw/results.json` | `e179b3220fd6e6f733d4fc707be9eab7640d433f249c55e0af70c9f652f0c91f` | results | E19 | historical | generated | frozen history | `cache.json` |
| `agent_e20_prvsiyan_early_sw.py` | `experiments/e020_early_sw/agent.py` | `0f027507e8ebe05cfa89d206bfc96072cd3affee0620b1250dc89bc7005c93ca` | agent | E20 | rejected/not promoted | self wrapper over external E11 | frozen | sibling cache/results |
| `e20_ab_arena.py` | `experiments/e020_early_sw/arena.py` | `5f9473678e0cb03d4d76c5fe2d43a2e9ab0e97a87088d4fddbe6b3beac0831ca` | arena | E20 | historical | self | modifiable tooling only | cache/results below |
| `e20_ab_cache.json` | `experiments/e020_early_sw/cache.json` | `4de8fb371d8664604fa206fa7db66fbbf82bb94bb45282a82834897c7d144b00` | cache | E20 | historical | generated | frozen history | `results.json` |
| `e20_ab_results.json` | `experiments/e020_early_sw/results.json` | `80d635c504663ba897cab68c146127167c91bda26a4b5c89d078ec12b786ede9` | results | E20 | historical | generated | frozen history | `cache.json` |

E18-E20 compatibility symlinks retain the old module/cache/result names plus
the old sibling bundle/public-agent expectations. This keeps every agent and
arena byte-identical while making `agent.py`, `arena.py`, `cache.json`, and
`results.json` canonical.

## Legacy series

| Old path(s) | New path(s) | Purpose | Identifier | Status | Origin | Mutability | Related history |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `agent_v2.py` … `agent_v15.py` | `experiments/legacy/v_series/` (same filenames) | legacy agents | v2-v15 | historical | mixed self/external wrappers | frozen experiment code | compare scripts and JSON in same directory |
| `compare.py`, `compare_v*.py`, `round_robin.py`, `run_match.py` | `experiments/legacy/v_series/` | v-series evaluation | v-series | historical | self | tooling | `round_robin_results.csv` |
| `agent_v4_diagnostic.py`, `agent_v8_debug.py`, `debug_v8.py`, `run_diagnostic.py` | `experiments/legacy/v_series/` | diagnostics | v4/v8 | historical | self | frozen agents; tooling otherwise | n/a |
| `analyze_v12_losses.py`, `analyze_v15_qeinstein.py` | `experiments/legacy/v_series/` | analysis | v12/v15 | historical | self | tooling | `v12_loss_analysis.json`, `v15_vs_candidate7_analysis.json` |
| `agent_h1.py` … `agent_h4.py` | `experiments/legacy/h_series/` (same filenames) | independent heuristic agents | h1-h4 | historical | self | frozen experiment code | sibling compare/trace scripts |
| `compare_h*.py`, `trace_h*.py` | `experiments/legacy/h_series/` | h-series evaluation/analysis | h1-h4 | historical | self | tooling | console-output experiments |

The v/h identifiers and individual files are not combined. Compatibility
symlinks only expose unchanged dependencies (`public_agents`, v11, and v15).

## Shared evaluation and analysis

| Old path | New path | Purpose | Status | Related cache/result | Change type |
| --- | --- | --- | --- | --- | --- |
| `arena.py` | `evaluation/arena.py` | general discovery/BT arena | active | `evaluation/arena_results/` | path fix: repository and output roots |
| `arena_results/` | `evaluation/arena_results/` | arena CSV/text output | historical | self | byte-preserving move |
| `mega_screen_v2.py` | `evaluation/mega_screen_v2/arena.py` | large candidate screen | historical/available | sibling `cache.json`, `results.json` | byte-preserving move + compatibility symlinks |
| `mega_screen_v2_cache.json` | `evaluation/mega_screen_v2/cache.json` | cache | historical | mega screen | byte-preserving move |
| `mega_screen_v2_results.json` | `evaluation/mega_screen_v2/results.json` | results | historical | mega screen | byte-preserving move |
| `population_arena_v1.py` | `evaluation/population_arena_v1/arena.py` | population/family-balanced BT evaluation | active | sibling `cache.json`, `results.json` | byte-preserving move + compatibility symlinks |
| `population_arena_v1_cache.json` | `evaluation/population_arena_v1/cache.json` | cache | historical | population arena | byte-preserving move |
| `population_arena_v1_results.json` | `evaluation/population_arena_v1/results.json` | results | historical | population arena | byte-preserving move |
| `run_e11_final_confirmation.py` | `evaluation/e11_final_confirmation.py` | final-confirmation launcher | historical/available | bundle cache | path fix only |
| `inspect_e11_land.py` | `analysis/e11/inspect_e11_land.py` | exact-source diagnostic | E11 | `e11_land_inspection.txt` | output/source path fix only |
| `make_e12_land_early.py` | `analysis/e11/make_e12_land_early.py` | historical candidate generator | historical E12-named work | generated file not run | path fix only |
| `e11_land_inspection.txt` | `analysis/e11/e11_land_inspection.txt` | recorded diagnostic | E11 | n/a | byte-preserving move |

## Artifacts, archive, and tools

| Old path | New path | SHA256 / classification | Purpose | Status |
| --- | --- | --- | --- | --- |
| `submission_kaito27_current.tar.gz` | `artifacts/submissions/submission_kaito27_current.tar.gz` | `e9ce1efb00f8cce0d51f6b8b8a37d061f5e4ec3e6446fc2f45d6d2a0e5b92e25` | submission artifact | frozen bytes |
| `e11_FINALIZE.zip` | `archive/bundles/intermediate/e11_FINALIZE.zip` | unique archive | old packaging step | archived/frozen |
| `e11_challengers_focus.zip` | `archive/bundles/intermediate/e11_challengers_focus.zip` | unique archive | old packaging step | archived/frozen |
| `elite_arena_resilient_patch{,.zip}` | `archive/bundles/intermediate/` | intermediate package | resilient arena patch | archived/frozen |
| `elite_resilient_AUTO{,.zip}` | `archive/bundles/intermediate/` | intermediate package | resilient arena auto bundle | archived/frozen |
| `check_latest.sh` | `tools/acquisition/check_latest.sh` | path fix | acquire/check Prvsiyan | active tool |
| `get_public_candidates.sh` | `tools/acquisition/get_public_candidates.sh` | path fix | acquire public candidates | active tool |
| `setup_bulk_candidates.sh` | `tools/setup/setup_bulk_candidates.sh` | path fix | public repository setup | active tool |
| `finalize_e11.py` | `tools/bundle/finalize_e11.py` | original SHA `854e8421edce52ccad3a721b289fb74cf5eb7f2466f99c8ddcd137d50bd3b079`; current SHA `6c6a14ee0258d0d51481e38097357fe9351bd962d621b56dbe4075b8bedd0718` | bundle finalizer | canonical tool |
| `install_e11_challengers_FIXED.py` | `tools/bundle/install_e11_challengers.py` | distinct file; current SHA `775c60244b1ee910ed5c2917bbe45425ee4d5e2314586434564f43f55d124f2c` | corrected challenger installer | canonical tool |
| `install_e11_challengers.py` | `archive/setup/install_e11_challengers_original.py` | `0805cdc122c7ce2aba93e8dedc1b93526287d01a4cabd83e624fb75297ab8564` | superseded original installer | archived canonical of old bytes |

## Byte-identical duplicates

Duplicates were identified before movement with SHA256; none was deleted.

| Old path | New path | SHA256 | Classification | Purpose |
| --- | --- | --- | --- | --- |
| `finalize_e11.py` | `tools/bundle/finalize_e11.py` | original `854e8421edce52ccad3a721b289fb74cf5eb7f2466f99c8ddcd137d50bd3b079` | canonical; later path-fixed | finalizer |
| `finalize_e11 2.py` | `archive/duplicates/finalize_e11_2.py` | `854e8421edce52ccad3a721b289fb74cf5eb7f2466f99c8ddcd137d50bd3b079` | duplicate of original canonical bytes | retained copy |
| `install_e11_challengers.py` | `archive/setup/install_e11_challengers_original.py` | `0805cdc122c7ce2aba93e8dedc1b93526287d01a4cabd83e624fb75297ab8564` | canonical old installer bytes | superseded setup |
| `install_e11_challengers 2.py` | `archive/duplicates/install_e11_challengers_2.py` | `0805cdc122c7ce2aba93e8dedc1b93526287d01a4cabd83e624fb75297ab8564` | duplicate | retained copy |
| `install_e11_challengers 3.py` | `archive/duplicates/install_e11_challengers_3.py` | `0805cdc122c7ce2aba93e8dedc1b93526287d01a4cabd83e624fb75297ab8564` | duplicate | retained copy |
| `install_e11_challengers 4.py` | `archive/duplicates/install_e11_challengers_4.py` | `0805cdc122c7ce2aba93e8dedc1b93526287d01a4cabd83e624fb75297ab8564` | duplicate | retained copy |
| patch `elite_arena_resilient.py` copies | preserved under `archive/bundles/intermediate/` and active bundle | `a25b14201390a9eb1778bc95ef9c4ac5705c23d933b8c2b0398ae6d8239bc57f` | expected package duplicate | resilient arena |
| patch `diagnose_elite_artifact.py` copies | both preserved under `archive/bundles/intermediate/` | `238dea6cd34c279d8bc4c4f1d46fd209b474cc4aae36f4b6483cd9f8eda70cd3` | duplicate; AUTO copy treated as canonical in that archived package | artifact diagnostic |
| E11 raw `submission.tar.gz` | same relative path under current bundle | `f0e698738d95ad3822d3128c814aeb8548d8b58e2e156bd1a3865a376ccdc1ad` | canonical published archive | exact submission |
| bundle `submission_e11.tar.gz` | same relative path under current bundle | `f0e698738d95ad3822d3128c814aeb8548d8b58e2e156bd1a3865a376ccdc1ad` | intentional duplicate | exact submission convenience copy |

E1-E13 wrappers and raw assets also occur in both the archived old bundle and
the current bundle. They remain inside each versioned bundle to preserve bundle
integrity rather than being factored out or replaced by links.

## Frozen hash invariants after the move

| Frozen item | Current path | SHA256 |
| --- | --- | --- |
| E11 raw source | `artifacts/bundles/current/public_agents/elite/prvsiyan_frontier/raw/main.py` | `02b1fee4b0e48027d4d3baeeb99518346f4fc5a14724cdb202d09a3425b15a79` |
| E11 wrapper | `artifacts/bundles/current/agent_e11_prvsiyan_frontier.py` | `939729b5ee6795969010105826e4daeb9416898218d8f466221f1c5c49054b8a` |
| E11 submission | `artifacts/bundles/current/public_agents/elite/prvsiyan_frontier/raw/submission.tar.gz` | `f0e698738d95ad3822d3128c814aeb8548d8b58e2e156bd1a3865a376ccdc1ad` |
| Kaito27 raw source | `artifacts/bundles/current/public_agents/elite/kaito27_current/raw/main.py` | `f48c21166eac68d1b05a401f04f94a2eb6154e65415af64893672365ff33c7b8` |
| Kaito27 wrapper | `artifacts/bundles/current/agent_e10_kaito27_current.py` | `1960597af6a675397347a63957d74f25e1a60aeee38cace860debae83e4cc64d` |
| Kaito27 raw submission | `artifacts/bundles/current/public_agents/elite/kaito27_current/raw/submission.tar.gz` | `9a158d0b251d18d042386d33fb31a4f4096005637c80953162e329d2eb7ff072` |

## Path-only code changes

Only these code/configuration files were edited for the new layout:

- `evaluation/arena.py`
- `evaluation/e11_final_confirmation.py`
- `analysis/e11/inspect_e11_land.py`
- `analysis/e11/make_e12_land_early.py`
- `artifacts/bundles/current/prepare_local_layout.py`
- `tools/bundle/finalize_e11.py`
- `tools/bundle/install_e11_challengers.py`
- `tools/acquisition/check_latest.sh`
- `tools/acquisition/get_public_candidates.sh`
- `tools/setup/setup_bulk_candidates.sh`
- `.gitignore`
- moved-path references in `README.md`
- tracked symlink targets inside `artifacts/bundles/current/`

No numbered agent strategy source was edited. No cache, result, zip, tarball, or
external raw source was regenerated.
