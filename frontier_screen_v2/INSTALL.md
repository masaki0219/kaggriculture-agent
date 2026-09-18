# Install Frontier Screen V2

The cleanest route is to copy these two files into the repo:

```text
evaluation/frontier_screen_v2/arena.py
evaluation/frontier_screen_v2/README.md
```

Then add the three `SOURCES` entries from `setup_sources.diff` to:

```text
artifacts/bundles/current/setup_elite_candidates.py
```

No existing E number is changed. No cache/result file is cleared.

After setup, download only the three new exact public artifacts:

```bash
cd artifacts/bundles/current
python setup_elite_candidates.py --only aurax7_v7_current
python setup_elite_candidates.py --only ahmed_v44_current
python setup_elite_candidates.py --only tetsu_market_v23_current
cd ../../..
```

Then run:

```bash
python evaluation/frontier_screen_v2/arena.py --seeds 8 --seed-start 18000
```

The screen writes `evaluation/frontier_screen_v2/results.json` and retains a per-game cache.
Do not assign E21 until this screen (plus live evidence) identifies the base worth freezing.
