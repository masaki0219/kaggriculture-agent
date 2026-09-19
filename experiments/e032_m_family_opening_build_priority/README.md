# E32 — M-family Opening Build-Priority Fix

Controlled successor to E31.

Trace evidence from E31:
- crops reached 12 by step23;
- only two pastures were built and two cows were placed;
- after the second pasture, workers were routed almost entirely to crop work;
- E30/E31 opening crop priorities were raised above the unchanged E29
  BUILD_PASTURE priority.

E32 changes exactly one mechanism:
- during day0..2, BUILD_PASTURE priority becomes -12.0, ahead of
  MELON=-9.5 and WHEAT=-8.5.

Everything else is inherited from E31, including:
- one mutually-exclusive placement job per empty pasture,
- day0 cash reserve for next-day hires,
- E30 planting priorities,
- E29 midgame/shop/land policy.

This is the final generic-planner opening experiment.
If opening fidelity still fails, move to an explicit day0 state machine.
