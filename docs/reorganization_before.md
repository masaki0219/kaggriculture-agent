# Reorganization baseline

Recorded before moving project files on 2026-09-18 (Asia/Tokyo).

## Git state

- Repository: `masaki0219/kaggriculture-agent`
- HEAD: `b9533cc Add E19/E20 and population arena experiments`
- `git status --short`: clean
- Tracked entries: 429
- Existing uncommitted work at start: none

`git submodule status` reported all seven registered submodules with a leading `-`
(registered commit known, but not initialized in the superproject worktree):

```text
-6a76335397d5cd2facffa91c938f629b119ea350 public_agents/gzmcr
-839c5d2390e5eb7063ba64856ac5091c3a1a4aa6 public_agents/hbharath
-99091bce833580062f476bfe55ce8019e3a1312d public_agents/ian_turner
-774b26093ccf4246525517d48420349b841b6e50 public_agents/lonespear
-d7cc891cd04025252cb3f0b54b0fa25247ca5e04 public_agents/qeinstein
-8b8c421eb10634c756583ce10c75189f50c83a72 public_agents/seyamalam
-920ef630f2fc98784956891875f63cd3654f4bbd public_agents/straf10
```

The submodule paths and SHAs are reorganization invariants.

## Top-level state

The root mixed these responsibilities:

- project metadata: `README.md`, `.gitignore`, `.gitmodules`
- numbered agents: `agent_v2.py` through `agent_v15.py`, `agent_h1.py` through
  `agent_h4.py`, and E18 through E20
- experiment-specific arenas, caches, and results for E17 through E20
- shared evaluation: `arena.py`, `round_robin.py`, `mega_screen_v2.py`, and
  `population_arena_v1.py`
- diagnostics and analysis scripts/results
- two elite bundle directories and their zip snapshots
- submission archives and intermediary zip artifacts
- setup, acquisition, installation, and finalization scripts
- `meta_cache/` acquisition data
- `public_agents/` Git submodules

The complete pre-move inventory remains recoverable from HEAD. The main
top-level directories were `arena_results/`, `elite_arena_resilient_patch/`,
`elite_resilient_AUTO/`, `kaggriculture_elite_bundle_FINAL/`,
`kaggriculture_elite_bundle_PATCHED_v2/`, `meta_cache/`, and `public_agents/`.

## Canonical bundle determination

`kaggriculture_elite_bundle_PATCHED_v2/` was the active/canonical bundle:

- it contains E14-E17 in addition to E1-E13;
- it contains focused/final-confirmation caches and results;
- E18, E19, E20, `arena.py`, `population_arena_v1.py`, the E11 inspection and
  acquisition tools, and the final-confirmation wrapper explicitly reference it;
- `kaggriculture_elite_bundle_FINAL/` is only a fallback in old setup scripts.

Therefore `kaggriculture_elite_bundle_FINAL/` is historical, despite its old
name, and `PATCHED_v2` is the source used as the current bundle before this
reorganization.

## Frozen/exact baseline hashes

These values were captured before any move:

| Artifact | SHA256 |
| --- | --- |
| E11 Prvsiyan raw `main.py` | `02b1fee4b0e48027d4d3baeeb99518346f4fc5a14724cdb202d09a3425b15a79` |
| E11 wrapper `agent_e11_prvsiyan_frontier.py` | `939729b5ee6795969010105826e4daeb9416898218d8f466221f1c5c49054b8a` |
| E11 raw `submission.tar.gz` | `f0e698738d95ad3822d3128c814aeb8548d8b58e2e156bd1a3865a376ccdc1ad` |
| E11 bundle `submission_e11.tar.gz` | `f0e698738d95ad3822d3128c814aeb8548d8b58e2e156bd1a3865a376ccdc1ad` |
| Kaito27 raw `main.py` | `f48c21166eac68d1b05a401f04f94a2eb6154e65415af64893672365ff33c7b8` |
| Kaito27 wrapper `agent_e10_kaito27_current.py` | `1960597af6a675397347a63957d74f25e1a60aeee38cace860debae83e4cc64d` |
| Kaito27 raw `submission.tar.gz` | `9a158d0b251d18d042386d33fb31a4f4096005637c80953162e329d2eb7ff072` |
| root `submission_kaito27_current.tar.gz` | `e9ce1efb00f8cce0d51f6b8b8a37d061f5e4ec3e6446fc2f45d6d2a0e5b92e25` |

## Cache/result baseline

Excluding `.git`, `.venv`, and the external `public_agents/` submodule trees:

- files matching `*cache*.json`: 11
- files matching `*results*.json` plus files under `arena_results/`: 15

Ignored JSON files under `meta_cache/` also existed and must move with that
directory. No cache or result is to be regenerated or removed during the move.

## Duplicate evidence

Byte-identical groups established with SHA256 before moving:

- `finalize_e11.py` and `finalize_e11 2.py`:
  `854e8421edce52ccad3a721b289fb74cf5eb7f2466f99c8ddcd137d50bd3b079`
- `install_e11_challengers.py` and copies `2`, `3`, `4`:
  `0805cdc122c7ce2aba93e8dedc1b93526287d01a4cabd83e624fb75297ab8564`
- `elite_arena_resilient.py` in both patch directories:
  `a25b14201390a9eb1778bc95ef9c4ac5705c23d933b8c2b0398ae6d8239bc57f`
- `diagnose_elite_artifact.py` in both patch directories:
  `238dea6cd34c279d8bc4c4f1d46fd209b474cc4aae36f4b6483cd9f8eda70cd3`

`install_e11_challengers_FIXED.py` is not identical to the older installer and
must not be classified as a duplicate.

## Dependency and path findings

- Most legacy compare/trace scripts import sibling `agent_v*` or `agent_h*`
  modules by module name.
- Legacy wrappers v12-v15 resolve external sources relative to their own
  directory and expect a sibling `public_agents/` path.
- E18-E20 agents resolve `kaggriculture_elite_bundle_PATCHED_v2/` relative to
  their own directory. Their arenas also expect sibling bundle,
  `public_agents/`, `agent_v15.py`, cache, and results paths.
- Shared evaluation scripts used root-relative paths. `arena.py` additionally
  used the current working directory as its root.
- Shell scripts used root-relative paths for the active E11 bundle,
  `public_agents/`, and generated `candidates/` content.
- The active bundle contained symlinks to root `agent_v11.py`, `agent_v15.py`,
  and the seven `public_agents/*` repositories.
- Existing non-venv symlinks were valid before the move.

Only path-resolution edits needed to preserve these relationships are allowed;
agent strategy behavior is out of scope.

## Generated archives present at root

`e11_FINALIZE.zip`, `e11_challengers_focus.zip`,
`elite_arena_resilient_patch.zip`, `elite_resilient_AUTO.zip`,
`kaggriculture_elite_bundle_FINAL.zip`,
`kaggriculture_elite_bundle_PATCHED_v2.zip`, and
`submission_kaito27_current.tar.gz`.

Archives inside external submodules are owned by those repositories and are not
part of this reorganization.
