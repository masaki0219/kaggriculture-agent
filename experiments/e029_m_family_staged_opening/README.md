# E29 — Staged-opening state-based M-family

E29 returns to E27, the last economically viable state-based baseline, and
fixes the opening using direct population evidence.

Key reconstructed mechanism:

- `4H / 2C3S / M6 / W~10` is a **day-0 aggregate**, not a single-turn buy.
- common opening starts with `BUY_PRODUCT WHEAT 5 + COW 1`;
- next turn adds `HIRE x4 + COW 1 + SHEEP 3`;
- melon seed is accumulated in 2-unit tranches;
- wheat seed is accumulated gradually with remaining cash;
- later capital remains independent from whether the full hand target was met.

Replay-derived crop checkpoints:
- step23: crops ~15.5
- step47: crops ~19.5
- step71: crops ~20
- step143: crops ~20
- step167: crops ~33
- step215: crops ~38
- step239: crops ~53
- step287: crops ~58.5

From day6 onward, total production scale is separated from first-four-shop
composition routing.

No replay action sequence is used.

SHA256: `3fc5bf1fce809adc9aab3747b99990d2d2b2dcf35f037552b35fc8be7e0a7de0`
