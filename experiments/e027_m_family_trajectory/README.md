# E27 — Trajectory-corrected state-based M-family

E27 keeps the no-replay-action architecture of E26, but fixes policy
translation errors found by comparing E26 to the 84-run M corpus.

Key corrections:
- shop-conditioned targets use only the first four shops;
- M6 is treated as the day-0 seed tranche, not total melon production;
- opening trajectory targets ~12 melon / 6 wheat / 2 strawberry;
- strawberry grows ~2 -> 8 -> shop-conditioned rather than jumping to 17+ on day2;
- structure count follows the observed trajectory (~5 -> 12 -> 16 -> <=20);
- structure construction is paced (max 2 new builds planned at once);
- herd size is capped near the observed distribution;
- goose response is conservative;
- animal and premium-seed purchases are paced rather than filling the full target gap instantly.

No replay action sequence is used.

SHA256: `8fa05ceb5ea7da79330b2ee4b23835f5b2395ada04b62dcd14a395d6fc76270a`
