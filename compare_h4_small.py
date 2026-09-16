"""
compare_h4_small.py

Gate for the independent heuristic line.

Run:
    python compare_h4_small.py

5 seeds x both seats against:
- h3 (must improve on its predecessor)
- v11 (must preserve the breakthrough)
- v15 / Kaito v48 (the real target)

If h4 still cannot materially close the v15 gap, stop this line and return to
the stronger public-baseline route.
"""

from statistics import mean
from kaggle_environments import make

from agent_h4 import agent as h4
from agent_h3 import agent as h3
from agent_v11 import agent as v11
from agent_v15 import agent as v15


def play(a0, a1, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([a0, a1])
    f = env.steps[-1]
    return float(f[0].reward), float(f[1].reward)


def matchup(name, opp):
    w = d = l = 0
    own, other, margins = [], [], []
    print(f"\n=== h4 vs {name} ===")

    for seed in range(5):
        rh, ro = play(h4, opp, seed)
        own.append(rh); other.append(ro); margins.append(rh-ro)
        if rh > ro: w += 1
        elif rh < ro: l += 1
        else: d += 1
        print(f"seed={seed:2d}   h4={rh:9.0f} opp={ro:9.0f} diff={rh-ro:+9.0f}")

        ro, rh = play(opp, h4, seed)
        own.append(rh); other.append(ro); margins.append(rh-ro)
        if rh > ro: w += 1
        elif rh < ro: l += 1
        else: d += 1
        print(f"seed={seed:2d}R  h4={rh:9.0f} opp={ro:9.0f} diff={rh-ro:+9.0f}")

    print(
        f"RESULT {name}: {w}-{d}-{l}, "
        f"mean h4={mean(own):.1f}, opp={mean(other):.1f}, "
        f"margin={mean(margins):+.1f}"
    )


def main():
    matchup("h3", h3)
    matchup("v11", v11)
    matchup("v15", v15)


if __name__ == "__main__":
    main()
