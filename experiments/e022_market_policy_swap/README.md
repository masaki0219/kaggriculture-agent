# E22 — Market Policy Swap

## Hypothesis

Failure-regime analysis showed E21 and aurax V7 realize nearly identical farms
even where E21 loses. The candidate causal difference is market execution.

E22 keeps E21 through `_ADV_PARENT` and replaces only the final E21 ADV market
block:

- removed from E22 path: `_adv_apply`, `_adv_frontload`
- inserted: aurax `advance_sales`, `frontload`

No route, crop, herd, opening, or shop-specific patch is introduced.

## Frozen artifacts

- E21/Tetsu SHA256: `f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`
- aurax V7 SHA256: `e221f4875daff8b03e8f0ec7c86bd3a2a72c0768b049d4c25064abd5301a532b`
- E22 agent: `artifacts/bundles/current/agent_e22_market_policy_swap.py`

## Interpretation

E22 is a mechanism-isolation experiment for a complete market-policy family.
A positive result must survive fresh seeds and population-representative
evaluation, not only E21/aurax head-to-head.
