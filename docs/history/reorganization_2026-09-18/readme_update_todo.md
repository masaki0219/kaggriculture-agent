# README strategy update TODO

This file intentionally records work for a later strategy-documentation pass.
The reorganization only corrected moved paths in `README.md`; it did not rewrite
the strategy narrative.

The next README update must reconcile the current document with all of the
following points:

- E11 is an important frozen baseline, but is not the final objective itself.
- Direct E11 head-to-head must not be an absolute candidate acceptance gate.
- The objective is to maximize Bradley-Terry performance against the unknown
  leaderboard population.
- Mean margin is a supporting diagnostic, not the final objective.
- A saturated panel, where both candidates already win 100% against the same
  opponents, cannot establish strength from margin alone.
- Evaluation-system development is a tool for finding stronger agents, not an
  end in itself.
- Avoid an endless sequence of one-location micro-patches; explore multiple,
  meaningfully different strategy families in parallel.
- Adaptability is not intrinsically the objective; win rate against the unknown
  population is.
- Kaito27 exact's historical leaderboard strength and its value against the
  current population have diverged.
- In the latest meta, no single fixed route should be treated as a permanent
  answer merely because it was previously current best.
- E numbers are immutable experiment history. New logic requires E21, E22, and
  so on; past E agents are not rewritten or renumbered.
- Caches and results are experiment history and must remain preserved.

Known passages requiring review include the absolute direct-E11 rejection rule,
the `Current Best` wording, E19's stale next-test status, and the closing claim
that every change must be justified by direct E11 improvement. Preserve the
historical record while clearly separating past decisions from current policy.
