"""
compare_h2_v15.py

Small rescue check before any large panel:
  python compare_h2_v15.py

5 seeds x both seats = 10 games.
"""

from statistics import mean
from kaggle_environments import make

from agent_h2 import agent as h2
from agent_v15 import agent as v15


def play(a0, a1, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([a0, a1])
    final = env.steps[-1]
    return float(final[0].reward), float(final[1].reward)


def main():
    w = d = l = 0
    own = []
    opp = []
    margins = []

    for seed in range(5):
        rh, rv = play(h2, v15, seed)
        own.append(rh); opp.append(rv); margins.append(rh-rv)
        if rh > rv: w += 1
        elif rh < rv: l += 1
        else: d += 1
        print(f"seed={seed:2d}   h2={rh:9.0f} v15={rv:9.0f} diff={rh-rv:+9.0f}")

        rv, rh = play(v15, h2, seed)
        own.append(rh); opp.append(rv); margins.append(rh-rv)
        if rh > rv: w += 1
        elif rh < rv: l += 1
        else: d += 1
        print(f"seed={seed:2d}R  h2={rh:9.0f} v15={rv:9.0f} diff={rh-rv:+9.0f}")

    print(
        f"\nRESULT h2 {w}-{d}-{l}, "
        f"mean h2={mean(own):.1f}, v15={mean(opp):.1f}, "
        f"margin={mean(margins):+.1f}"
    )


if __name__ == "__main__":
    main()
