# E26 — State-based M-family agent

This is the strategy the E23→E25 work was intended to reach.

**No replay action sequence is used.**

The agent implements M-family mechanisms inferred from the 84-run corpus:

- opening family: 4 hands / 2 cows / 3 sheep / 6 melons / ~10 wheat;
- second land after shop 2 (~step 150);
- third land after shop 3 (~step 220);
- MILK demand changes cow target;
- WOOL demand changes sheep target;
- EGG demand changes goose target;
- strawberry / tomato / carrot acreage changes with shop demand;
- wheat fills residual acreage;
- current state determines BUILD / BUY / PLANT / FEED / CARE / HARVEST jobs;
- nearest available units execute jobs;
- market orders use live state only.

E23/E24/E25 remain immutable historical experiments.

SHA256: `7d73f68353dcd7cd868e1e72b552acae9026e39894064f56a2243ed3cd69c967`
