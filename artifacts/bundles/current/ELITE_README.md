# Kaggriculture elite candidate pack

Goal: maximize final W/D/L / Bradley-Terry, not raw reward.

## Candidate set

- E1 `agent_e1_kaito58.py` — exact Kaito v58, Apache-2.0.
- E2 `agent_e2_boatlee29.py` — exact Boatlee v29-R1, Apache-2.0.
- E3 `agent_e3_shape_top10.py` — exact Shape-the-Shop TOP10, Apache-2.0.
- E4 `agent_e4_adaptive_route_v2.py` — exact Adaptive Route V2, Apache-2.0.
- E5 `agent_e5_kaito58_shift1.py` — Kaito v58 with narrow 1-turn premium-sale phase shift.
- E6 `agent_e6_boatlee29_guard.py` — Boatlee v29 with public-state market collision guard.
- E7 `agent_e7_tetsu_shape.py` — strong benchmark, license re-check before submission.
- E8 `agent_e8_farming_v4.py` — recent high-score benchmark, license re-check before submission.
- E9 `agent_e9_boatlee29_tomato.py` — Boatlee v29 + town-conditioned day-11 tomato substitution.
- E10 `agent_e10_kaito27_current.py` — exact current Kaito v27, Apache-2.0, currently very high public score.
- E11 `agent_e11_prvsiyan_frontier.py` — exact current Prvsiyan Frontier, Apache-2.0.
- E12 `agent_e12_kaito43_current.py` — exact current Kaito v43 Sparse Shop Hybrid, Apache-2.0.
- E13 `agent_e13_kaito27_guard.py` — current Kaito v27 + public-state market-collision guard.

## Setup

```bash
python -m pip install kaggle
python setup_elite_candidates.py
```

If the CLI is already installed/authenticated, only the second command is needed.

## Serious first screen

Start with the strongest / most informative submit-safe set:

```bash
python elite_arena.py \
  --candidates e1_kaito58,e2_boatlee29,e3_shape_top10,e6_boatlee29_guard,e9_boatlee29_tomato,e10_kaito27_current,e11_prvsiyan_frontier,e12_kaito43_current,e13_kaito27_guard \
  --seeds 8 \
  --seed-start 1000
```

This is deliberately expensive. Every game runs in a fresh process and both
seats are tested.

Optional benchmark-only candidates E7/E8 can be added after their licenses are
re-checked.

## Confirmation

After the top 2–3 are known:

```bash
python elite_arena.py \
  --candidates e2_boatlee29,e3_shape_top10,e6_boatlee29_guard \
  --seeds 20 \
  --seed-start 5000
```

The arena runs every game in a fresh process and caches each game.

## Promotion rule

Do not promote from reward mean alone.
Primary:
1. paired W/D/L,
2. holdout W/D/L,
3. Bradley-Terry,
4. reward margin only as diagnostic.

Do not call seeds used for tuning "holdout" again.


## If the bundle is inside your existing Kaggle project

Before setup, run:

```bash
python prepare_local_layout.py
```

This exposes your existing `public_agents/` and `agent_v15.py` to the arena
without modifying the originals.

## Kaggle CLI authentication

If setup prints `Authentication required`, run:

```bash
kaggle auth login
```

Complete the browser login, then:

```bash
python setup_elite_candidates.py
```

Setup is resumable: successfully prepared candidates are skipped on rerun.
Do **not** run `elite_arena.py` until setup completes.
