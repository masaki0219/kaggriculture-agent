"""
compare_h3_small.py

Small paired check only. We first need to know whether h3 actually establishes
a productive herd before spending time on a large panel.

Run:
    python compare_h3_small.py
"""

from statistics import mean
from kaggle_environments import make

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
    w=d=l=0
    own=[]; other=[]; margins=[]
    print(f"\n=== h3 vs {name} ===")
    for seed in range(5):
        rh, ro = play(h3, opp, seed)
        own.append(rh); other.append(ro); margins.append(rh-ro)
        if rh > ro: w += 1
        elif rh < ro: l += 1
        else: d += 1
        print(f"seed={seed:2d}   h3={rh:9.0f} opp={ro:9.0f} diff={rh-ro:+9.0f}")

        ro, rh = play(opp, h3, seed)
        own.append(rh); other.append(ro); margins.append(rh-ro)
        if rh > ro: w += 1
        elif rh < ro: l += 1
        else: d += 1
        print(f"seed={seed:2d}R  h3={rh:9.0f} opp={ro:9.0f} diff={rh-ro:+9.0f}")

    print(
        f"RESULT {name}: {w}-{d}-{l}, "
        f"mean h3={mean(own):.1f}, opp={mean(other):.1f}, "
        f"margin={mean(margins):+.1f}"
    )


def main():
    matchup("v11", v11)
    matchup("v15", v15)


if __name__ == "__main__":
    main()
