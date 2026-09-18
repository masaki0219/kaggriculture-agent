# Frontier Screen V2 — 2026-09-18

## Purpose

This screen answers one narrow question before creating E21:

> Which currently available strong public strategy is the best **base / yardstick** for the present Kaggriculture population?

It does **not** optimize raw bank, does **not** use E11 H2H as a gate, and does **not** automatically promote or submit anything.

Primary ranking is the mean W/D/L score across **strategy families**. This avoids giving three nearly-related public reactive agents three times the population weight.

## Candidates

- `e11` — current frozen Prvsiyan baseline
- `shape_top10` — existing Shape reference
- `adaptive_route_v2` — existing Adaptive Route V2
- `aurax7_v7` — 2026-09-17 reactive/public successor
- `ahmed_v44` — same-turn sale-race branch
- `tetsu_market_v23` — Market-Smart branch

The last three are grouped into `reactive_public_frontier` for family-balanced scoring because their lineage overlaps heavily.

## Extra holdouts

- Kaito58
- Boatlee29
- qeinstein champion
- qeinstein candidate7

qeinstein variants share one family weight.

## Setup

Apply the companion patch to `artifacts/bundles/current/setup_elite_candidates.py`, then from that directory:

```bash
python setup_elite_candidates.py --only aurax7_v7_current
python setup_elite_candidates.py --only ahmed_v44_current
python setup_elite_candidates.py --only tetsu_market_v23_current
```

The setup script records the downloaded `main.py` SHA256 in its manifest. Keep that manifest with the results so the screen remains reproducible.

Existing `shape_top10`, `adaptive_route_v2`, `kaito58`, and `boatlee29` artifacts plus the qeinstein submodule must also be present.

## First screen

From the repository root:

```bash
python evaluation/frontier_screen_v2/arena.py --seeds 8 --seed-start 18000
```

This is 16 games per matchup because both seats are tested.

If the top 2 are close, use a fresh seed range:

```bash
python evaluation/frontier_screen_v2/arena.py \
  --candidates <candidate1>,<candidate2>,e11 \
  --seeds 24 \
  --seed-start 24000 \
  --fresh
```

Do not reuse the first seed range as a claimed holdout.

## Decision rule

Promote a base to E21 only when:

1. it does not crash;
2. its mechanism actually runs;
3. family-balanced W/D/L is strong;
4. its worst-family result is not catastrophic;
5. its matchup vector is useful for the final two-submission portfolio;
6. live leaderboard evidence does not contradict the local screen.

Raw reward margin is reported only as a diagnostic.

## Two-submission portfolio diagnostic

The result file also contains `portfolio_pairs`. For each pair of candidates, it aligns only scenarios with the **same opponent, seed, and candidate seat**, then reports:

- `both_loss_rate`: how often both agents lose the same scenario;
- `loss_correlation`: correlation of their loss indicators;
- `family_balanced_oracle`: per-family average of the better result from the two agents.

This is a complementarity diagnostic, not an automatic final-pair selector. A pair still needs both members to be individually strong enough for the real leaderboard.
