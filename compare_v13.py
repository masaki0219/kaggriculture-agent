from statistics import mean

from kaggle_environments import make

from agent_v12 import agent as v12
from agent_v13 import agent as v13

SEEDS = range(10)


def play(a0, a1, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=True,
    )
    env.run([a0, a1])
    final = env.steps[-1]
    return float(final[0].reward), float(final[1].reward)


def main():
    wins = draws = losses = 0
    own = []
    other = []
    margins = []

    for seed in SEEDS:
        r13, r12 = play(v13, v12, seed)
        own.append(r13)
        other.append(r12)
        margins.append(r13 - r12)

        if r13 > r12:
            wins += 1
        elif r13 < r12:
            losses += 1
        else:
            draws += 1

        print(
            f"seed={seed:2d}   "
            f"v13={r13:9.0f}  v12={r12:9.0f}  "
            f"diff={r13-r12:+9.0f}"
        )

        r12, r13 = play(v12, v13, seed)
        own.append(r13)
        other.append(r12)
        margins.append(r13 - r12)

        if r13 > r12:
            wins += 1
        elif r13 < r12:
            losses += 1
        else:
            draws += 1

        print(
            f"seed={seed:2d}R  "
            f"v13={r13:9.0f}  v12={r12:9.0f}  "
            f"diff={r13-r12:+9.0f}"
        )

    games = wins + draws + losses
    score = (wins + 0.5 * draws) / games

    print("\n=== RESULT ===")
    print(f"v13 {wins}-{draws}-{losses} v12")
    print(f"score={score:.1%}")
    print(
        f"mean reward: v13={mean(own):.1f}, "
        f"v12={mean(other):.1f}, "
        f"mean margin={mean(margins):+.1f}"
    )
    print(f"v13 min/max reward: {min(own):.0f} / {max(own):.0f}")


if __name__ == "__main__":
    main()
