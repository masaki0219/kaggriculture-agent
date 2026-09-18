# E28 — Scale-routed state-based M-family

E28 keeps the no-replay-action architecture and separates two mechanisms
observed in the 84-run current M-family corpus:

1. **total production scale trajectory**
   - crop footprint: roughly 20 -> 33/38 -> 53/57
   - herd size: 5 -> 11/12 -> 14/16
   - daily hands: 4 -> 6 -> 8/9 -> 10/11

2. **shop-conditioned composition**
   - MILK routes herd slots toward cows
   - WOOL routes herd slots toward sheep
   - EGG routes a smaller fraction toward geese
   - shop demand routes crop slots among strawberry/tomato/carrot
   - wheat fills the residual crop footprint

Market scheduling is also made explicit:
SELL -> HIRE -> LAND -> FEED -> ANIMAL -> SEED.

Hires are retried through the day and capped per turn so the 10-order market
limit cannot starve live sales/land/seed operations.

Optional CARE/fertilizer collection is suppressed while crop expansion is
materially behind the observed trajectory.

No replay action sequence is used.

SHA256: `295a1cd80b5779e152b0f6cd796a79982e3e3617b25ba3651b10c80a17a1612a`
