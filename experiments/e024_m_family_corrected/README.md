# E24 — Corrected M-family replay-router

E23 failed because replay actions were aligned to the wrong state index and
donor cash-flow timing was overwritten.

E24 fixes the mechanism rather than patching outcomes:

- live step `t` uses replay action `t+1`;
- replay positions at `t` remain the start-state positions for remapping;
- donor HIRE / BUY_LAND timing is preserved;
- donor purchase ordering is preserved;
- shop-prefix route switching remains;
- invalid unit actions and impossible SELL quantities are still repaired.

This is still a complete M-family candidate, separate from E21/E22.

SHA256: `d99d0af14b5eea553aedf20d6c2f6b7f96670131406a2a4dd2c92ee64390ee98`
