from __future__ import annotations

from pathlib import Path
from statistics import mean

from kaggle_environments import make

from agent_v4 import melon_maxxer as v4
from agent_v8 import agent as v8


ROOT = Path(__file__).resolve().parent
SEEDS = range(10)

OPPONENTS = {
    "v4": v4,
    "starter": "starter",
    "gzmcr": str(ROOT / "public_agents" / "gzmcr" / "main.py"),
    "lonespear": str(ROOT / "public_agents" / "lonespear" / "main.py"),
    "seyamalam": str(ROOT / "public_agents" / "seyamalam" / "main.py"),
}


def play(agent0, agent1, seed):
    env = make(
        "kaggriculture",
        configuration={
            "episodeSteps": 720,
            "seed": seed,
        },
        debug=True,
    )
    env.run([agent0, agent1])
    final = env.steps[-1]
    return float(final[0].reward), float(final[1].reward)


def main():
    print("=== v8-core benchmark ===")

    total_wins = 0
    total_losses = 0
    total_draws = 0

    for name, opponent in OPPONENTS.items():
        if isinstance(opponent, str) and opponent != "starter":
            if not Path(opponent).exists():
                print(f"\n[SKIP] {name}: {opponent} not found")
                continue

        wins = losses = draws = 0
        v8_rewards = []
        opp_rewards = []
        margins = []

        print(f"\n=== v8 vs {name} ===")

        for seed in SEEDS:
            r8, ro = play(v8, opponent, seed)
            v8_rewards.append(r8)
            opp_rewards.append(ro)
            margins.append(r8 - ro)

            if r8 > ro:
                wins += 1
            elif r8 < ro:
                losses += 1
            else:
                draws += 1

            print(
                f"seed={seed:2d}   "
                f"v8={r8:9.0f}  {name}={ro:9.0f}  "
                f"diff={r8-ro:+9.0f}"
            )

            ro, r8 = play(opponent, v8, seed)
            v8_rewards.append(r8)
            opp_rewards.append(ro)
            margins.append(r8 - ro)

            if r8 > ro:
                wins += 1
            elif r8 < ro:
                losses += 1
            else:
                draws += 1

            print(
                f"seed={seed:2d}R  "
                f"v8={r8:9.0f}  {name}={ro:9.0f}  "
                f"diff={r8-ro:+9.0f}"
            )

        games = wins + losses + draws
        score = (wins + 0.5 * draws) / games if games else 0.0

        total_wins += wins
        total_losses += losses
        total_draws += draws

        print(
            f"RESULT: v8 {wins}-{draws}-{losses} {name}  "
            f"score={score:.1%}"
        )
        print(
            f"mean reward: v8={mean(v8_rewards):.1f}, "
            f"{name}={mean(opp_rewards):.1f}, "
            f"mean margin={mean(margins):+.1f}"
        )

    total = total_wins + total_losses + total_draws
    score = (
        (total_wins + 0.5 * total_draws) / total
        if total
        else 0.0
    )

    print("\n=== TOTAL ===")
    print(
        f"v8 W-D-L = "
        f"{total_wins}-{total_draws}-{total_losses}"
    )
    print(f"v8 score  = {score:.1%}")


if __name__ == "__main__":
    main()
