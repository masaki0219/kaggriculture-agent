# Reorganization verification

Verified on 2026-09-18 without running large arenas or regenerating caches,
results, bundles, or submissions.

## Checks passed

- Python syntax: every `.py` outside `.git`, `.venv`, and external submodules
  compiled in memory successfully.
- Shell syntax: all active `.sh` files under `tools/` passed `bash -n`.
- JSON: every project-owned JSON file parsed successfully.
- Arena smoke: `--help` succeeded for the general arena, mega screen,
  population arena, E18-E20 arenas, current elite arena, focused E11 arena,
  and final-confirmation launcher.
- General arena discovery: `evaluation/arena.py --dry-run` completed without
  running matches.
- Agent import smoke: E11, Kaito27, E18, E19, E20, representative v-series
  agents, h1, and the mega/population compatibility imports succeeded.
- Symlinks: no broken symlink was found outside `.git` and `.venv`.
- Archives: all project-owned zip files passed `unzip -t`; all project-owned
  tar.gz files passed `gzip -t`.
- Submodules: the seven registered paths and SHAs exactly match the pre-move
  record. Their leading `-` (uninitialized status) is also unchanged.
- Git index: 429 tracked entries before and after; no staged delete exists.
- Cache count: 11 before, 11 after.
- Result count: 15 before, 15 after.
- Meta data: all 10 ignored dated JSON files moved to `data/meta_cache/`.

## Frozen hashes

The following post-move values exactly match the pre-move baseline:

| Item | SHA256 |
| --- | --- |
| E11 raw source | `02b1fee4b0e48027d4d3baeeb99518346f4fc5a14724cdb202d09a3425b15a79` |
| E11 wrapper | `939729b5ee6795969010105826e4daeb9416898218d8f466221f1c5c49054b8a` |
| E11 raw and bundle submission archives | `f0e698738d95ad3822d3128c814aeb8548d8b58e2e156bd1a3865a376ccdc1ad` |
| Kaito27 raw source | `f48c21166eac68d1b05a401f04f94a2eb6154e65415af64893672365ff33c7b8` |
| Kaito27 wrapper | `1960597af6a675397347a63957d74f25e1a60aeee38cace860debae83e4cc64d` |
| Kaito27 raw submission | `9a158d0b251d18d042386d33fb31a4f4096005637c80953162e329d2eb7ff072` |
| Root Kaito27 submission moved to artifacts | `e9ce1efb00f8cce0d51f6b8b8a37d061f5e4ec3e6446fc2f45d6d2a0e5b92e25` |

Direct HEAD-to-worktree comparisons also matched for the moved current-bundle
zip, Kaito27 submission, E18 agent/cache/results, E19 agent, and E20 agent.

## Deliberately unresolved

- `evaluation/population_arena_v1/arena.py` contains an E21 candidate entry,
  but no E21 agent exists in the recorded repository. It remains untouched;
  creating E21 would be strategy work, not reorganization.
- Historical cache/result text contains old absolute or relative paths. These
  records were not rewritten because doing so would mutate experiment history.
- The byte-preserved `artifacts/bundles/current_snapshot.zip` is the former
  `PATCHED_v2.zip`; it was not rebuilt to mirror later contents of the current
  directory.
- Git reports submodules as uninitialized (`-`) both before and after. No
  initialization or SHA update was attempted.
- `analysis/e11/make_e12_land_early.py` is a historical generator with an old
  E12 output name. It was path-fixed but not run; it must not be used to create
  new work under the already-consumed E12 number.
- Strategy-language updates remain in `docs/readme_update_todo.md` for the
  separate README rewrite requested later.
