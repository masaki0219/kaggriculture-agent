# Public market flow reconstruction

The V224 timing work exposed both benefits from selling ahead of a rival and losses from selling before town consumption. A possible next direction is to condition timing on recent rival market activity. No new candidate or predictor has been built from this observation yet.

For a completed transition from observation t to t+1, let S be our shed projected after our known worker actions, S' our next observed shed, I and I' the public market inventories, and D the known town consumption during the transition. Away from automatic dawn returns and floor sales:

    own net market supply = S - S'
    rival net market supply = I' - I + D - (S - S')

This uses our own private shed and actions, public market inventories, and shops now publicly visible. It reconstructs the preceding turn when t+1 arrives. It cannot be used at t to read future activity. Research IDs, rival identities, hidden seeds, rival private inventories, and rival actions are not inputs.

The initial test failed: 928 mismatches in 89,208 product transitions across 24 existing full games. The engine's `_commit_unit` adds supply only when a sale price exceeds $1. Floor sales dispose of goods without adding market inventory. Counting them as supply is wrong. The rejected audit is retained in `results/public-market-flow-naive-rejected-20260909.json`.

The corrected target is market-impacting net supply: non-floor sales minus purchases. The observer excludes dawn transitions because automatic inventory returns change the shed. When our action sells an item, it also abstains if market inventory plus our projected item stock plus a full 100-unit rival shed could reach the $1 floor. This conservative bound uses public market pricing parameters. Purchases reduce market supply before goods can be resold. Cases with no own sale of the item do not have this own-floor ambiguity.

The corrected check matched all 86,268 included product transitions, including 2,994 nonzero rival flows, with 2,940 ambiguous item transitions excluded. These are old trajectories from 24 games, comprising eight capacity diagnostics, eight labor discovery games, and eight earlier market diagnostics. They include related and repeated strategy families. This is deterministic accounting validation, not an independent sample, prediction score, win rate, or admission evidence.

Reproduce with `tools/audit_public_market_flow.py`; output `results/public-market-flow-reconstruction-20260909.json`. It reads hash-checked observations and own actions to compute the estimate, then uses independently captured executed unit events only as offline ground truth. The lightweight own-shed projection is inherited from the published V221B helper. Configuration assumptions are the pinned 1.32.7 default 100-unit shed, 24-step day, four-step shop demand and 24-step town-center demand; a reusable runtime observer must explicitly handle other configurations or abstain.

Before adding this to a policy, freeze a causal predictor and check it sequentially: features may use only already observed transitions; the heldout decision must precede the sale it predicts. Report coverage and errors separately for floor-adjacent goods, low and high supply, and opponent families. A reconstructed past flow is not evidence that a rival will repeat it next turn. Do not retrofit a trigger solely around the V224 discovery wins or the rank-three regression.
