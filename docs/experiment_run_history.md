# Experiment Run History

Lightweight execution history for the repository.

## 2026-09-18T11:00:12+09:00 — Freeze E21: Tetsu Market-Smart Farming V23

- Action: froze exact public Tetsu Market-Smart Farming V23 as E21 baseline.
- Source: `artifacts/bundles/current/public_agents/elite/tetsu_market_v23_current/raw/_extract_submission_tar/main.py`
- SHA256: `f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`
- Wrapper: `artifacts/bundles/current/agent_e21_tetsu_market_v23.py`
- Evaluation basis: Frontier Screen V2, seeds 18000-18007, both seats.
- Interpretation: E21 becomes the current frontier reference; this is not a final-submission decision.
- No Kaggle submission was performed.

## 2026-09-18T14:30:49+09:00 — Analyze E21 shop routes

- Source SHA256: `f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`
- Report: `experiments/e021_tetsu_market_v23/shop_route_report.md`
- Route table: `_ROUTES` (41 routes)
- Shop maps: _R108_SHOP_ROUTES
- Read-only; no agent modification or submission.

## 2026-09-18T14:37:15+09:00 — Probe E21 realized shop response

- Seeds: `19000..19011`
- Opponents: e11, aurax7_v7
- Valid games: 48/48
- Report: `experiments/e021_tetsu_market_v23/realized_shop_response.md`
- Data: `experiments/e021_tetsu_market_v23/realized_shop_response.json`
- Read-only; no agent modification or submission.

## 2026-09-18T14:40:51+09:00 — Repair Ahmed V44 artifact

- Notebook: `artifacts/bundles/current/public_agents/elite/ahmed_v44_current/source/kaggriculture-v44-winning-the-same-turn-sale-race.ipynb`
- Final entrypoint: `artifacts/bundles/current/public_agents/elite/ahmed_v44_current/notebook_extract/main.py`
- SHA256: `fe370bd8a9d0f3770e61cff4d9e60e19198e058a0fa1fb0adeb873a9d89c6640`
- Callables: agent
- Report: `artifacts/bundles/current/public_agents/elite/ahmed_v44_current/REPAIR_REPORT.md`
- No Kaggle submission performed.

## 2026-09-18T15:02:22+09:00 — Current frontier screen

- Candidates: e21, ahmed_v44, aurax7_v7
- Direct RR seeds: `20000..20015`
- Fixed panel seeds: `21000..21007`
- Report: `evaluation/frontier_screen_v2/current_results.md`
- Data: `evaluation/frontier_screen_v2/current_results.json`
- No Kaggle submission performed.

## 2026-09-18T15:07:46+09:00 — Analyze frontier failure regimes

- Source screen: `evaluation/frontier_screen_v2/current_results.json`
- Fresh replays: 32
- Report: `analysis/frontier_failure_regimes/report.md`
- Data: `analysis/frontier_failure_regimes/results.json`
- Read-only; no agent modification or Kaggle submission.

## 2026-09-18T15:29:08+09:00 — Diff E21 vs aurax market policy

- E21 SHA256: `f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`
- aurax SHA256: `e221f4875daff8b03e8f0ec7c86bd3a2a72c0768b049d4c25064abd5301a532b`
- Market-related differing blocks: 19
- Report: `experiments/e021_tetsu_market_v23/aurax_market_diff.md`
- Data: `experiments/e021_tetsu_market_v23/aurax_market_diff.json`
- Read-only; no agent modification or Kaggle submission.

## 2026-09-18T15:36:19+09:00 — Build E22 market-policy swap

- E21/Tetsu SHA256: `f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`
- aurax V7 SHA256: `e221f4875daff8b03e8f0ec7c86bd3a2a72c0768b049d4c25064abd5301a532b`
- Agent: `artifacts/bundles/current/agent_e22_market_policy_swap.py`
- Kept E21 route/production/opening/race chain through `_ADV_PARENT`.
- Replaced only final ADV market wrapper with aurax `advance_sales + frontload`.
- Import validation: PASS.
- No Kaggle submission performed.

## 2026-09-18T15:40:03+09:00 — E22 fresh market-policy screen

- Seeds: `22000..22011`
- Opponents: e21, aurax7_v7, ahmed_v44
- Report: `experiments/e022_market_policy_swap/market_policy_results.md`
- Data: `experiments/e022_market_policy_swap/market_policy_results.json`
- No Kaggle submission performed.

## 2026-09-18T15:58:57+09:00 — E21/E22 strong common-panel screen

- Fresh seeds: `23000..23007`
- Frontier panel: aurax7_v7, ahmed_v44, kaito43, kaito27, tetsu_shape, farming_v4
- Legacy panel: kaito58, boatlee29
- Report: `experiments/e022_market_policy_swap/strong_panel_results.md`
- Data: `experiments/e022_market_policy_swap/strong_panel_results.json`
- No Kaggle submission performed.

## 2026-09-18T16:04:35+09:00 — Refresh live leaderboard population

- Leaderboard rows: 30
- Teams scouted: 20
- Teams with replay: 20
- Replays downloaded: 40
- Bundle: `data/replays/2026-09-18/live_population.zip`
- Acquisition only; no agent modification or Kaggle submission.

## 2026-09-18T16:18:00+09:00 — Collect current M-family corpus

- Teams: 8
- Episodes/team: 12
- Successful downloads: 96
- Bundle: `data/corpora/2026-09-18/m_family.zip`
- Acquisition only; no agent modification or Kaggle submission.

## 2026-09-18T16:58:06+09:00 — Install E23 M-family replay-router v1

- Agent: `artifacts/bundles/current/agent_e23_m_family_v1.py`
- SHA256: `407a19a6db3109c5c7e5648bdc668284f06493fdb16f0cf1b0d7cc2a5ea3b6db`
- Route library: 24 public-replay-derived Majkel1337/Arda Ceylan routes.
- No competitor source code embedded.
- No Kaggle submission performed.

## 2026-09-18T17:03:04+09:00 — E23 M-family v1 fresh screen

- Seeds: `24000..24007`
- Opponents: e21, e22, aurax7_v7, ahmed_v44, kaito43, tetsu_shape
- Aggregate W-D-L: 0-0-96
- Report: `experiments/e023_m_family_v1/results.md`
- Data: `experiments/e023_m_family_v1/results.json`
- No Kaggle submission performed.

## 2026-09-18T17:08:34+09:00 — Install E24 corrected M-family replay-router

- Agent: `artifacts/bundles/current/agent_e24_m_family_corrected.py`
- SHA256: `d99d0af14b5eea553aedf20d6c2f6b7f96670131406a2a4dd2c92ee64390ee98`
- Fixes E23 replay action/state off-by-one.
- Preserves donor HIRE/BUY_LAND/purchase ordering.
- E23 is not overwritten.
- No Kaggle submission performed.

## 2026-09-18T17:09:04+09:00 — E24 corrected M-family screen

- Smoke max reward: 16803
- Fresh seeds: `25000..25007`
- Aggregate W-D-L: 0-0-96
- Report: `experiments/e024_m_family_corrected/results.md`
- Data: `experiments/e024_m_family_corrected/results.json`
- No Kaggle submission performed.

## 2026-09-18T17:42:11+09:00 — Install E26 state-based M-family agent

- Agent: `artifacts/bundles/current/agent_e26_m_family_state_based.py`
- SHA256: `7d73f68353dcd7cd868e1e72b552acae9026e39894064f56a2243ed3cd69c967`
- No replay/tape actions used.
- Targets inferred from 84 M-family replay runs.
- Current observation drives planning/execution/market.
- E23/E24/E25 are not overwritten.
- No Kaggle submission performed.

## 2026-09-18T17:54:11+09:00 — Install E27 trajectory-corrected M-family

- Agent: `artifacts/bundles/current/agent_e27_m_family_trajectory.py`
- SHA256: `8fa05ceb5ea7da79330b2ee4b23835f5b2395ada04b62dcd14a395d6fc76270a`
- No replay/tape actions used.
- Fixes E26 first4-vs-all-shops target drift.
- Fixes M6 initial-tranche vs total-melon confusion.
- Adds replay-derived structure/crop growth trajectory.
- E23-E26 remain immutable.
- No Kaggle submission performed.

## 2026-09-18T18:07:54+09:00 — Install E28 scale-routed M-family

- Agent: `artifacts/bundles/current/agent_e28_m_family_scale_routed.py`
- SHA256: `295a1cd80b5779e152b0f6cd796a79982e3e3617b25ba3651b10c80a17a1612a`
- No replay/tape actions used.
- Separates total scale trajectory from shop-conditioned composition.
- Reworks market slots around SELL/HIRE/LAND priority.
- Suppresses optional animal work while crop expansion is behind.
- E23-E27 remain immutable.
- No Kaggle submission performed.

## 2026-09-18T18:25:10+09:00 — Install E29 staged-opening M-family

- Agent: `artifacts/bundles/current/agent_e29_m_family_staged_opening.py`
- SHA256: `3fc5bf1fce809adc9aab3747b99990d2d2b2dcf35f037552b35fc8be7e0a7de0`
- Based on E27, not E28.
- Reconstructs M opening as staged cashflow rather than lump purchase.
- No replay action routing used.
- E23-E28 remain immutable.
- No Kaggle submission performed.
## 2026-09-19T10:00:05+09:00 — Refresh live leaderboard population

- Leaderboard rows: 30
- Teams scouted: 20
- Teams with replay: 20
- Replays downloaded: 80
- Bundle: `live_population.zip`
- Acquisition only; no agent modification or Kaggle submission.

