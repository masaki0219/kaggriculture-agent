from pathlib import Path
from statistics import mean

from kaggle_environments import make

from agent_v4 import melon_maxxer as v4
from agent_v10 import agent as v10
from agent_v11 import agent as v11

ROOT = Path(__file__).resolve().parent
SEEDS = range(10)

OPPONENTS = {
    "v10": v10,
    "v4": v4,
    "starter": "starter",
    "gzmcr": str(ROOT / "public_agents" / "gzmcr" / "main.py"),
    "lonespear": str(ROOT / "public_agents" / "lonespear" / "main.py"),
    "seyamalam": str(ROOT / "public_agents" / "seyamalam" / "main.py"),
}


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
    total_w = total_d = total_l = 0

    for name, opp in OPPONENTS.items():
        if isinstance(opp, str) and opp != "starter" and not Path(opp).exists():
            print(f"[SKIP] {name}: {opp} not found")
            continue

        wins = draws = losses = 0
        own = []
        other = []
        margins = []

        print(f"\n=== v11 vs {name} ===")

        for seed in SEEDS:
            r11, ro = play(v11, opp, seed)
            own.append(r11)
            other.append(ro)
            margins.append(r11 - ro)

            if r11 > ro:
                wins += 1
            elif r11 < ro:
                losses += 1
            else:
                draws += 1

            print(
                f"seed={seed:2d}   "
                f"v11={r11:9.0f}  {name}={ro:9.0f}  "
                f"diff={r11-ro:+9.0f}"
            )

            ro, r11 = play(opp, v11, seed)
            own.append(r11)
            other.append(ro)
            margins.append(r11 - ro)

            if r11 > ro:
                wins += 1
            elif r11 < ro:
                losses += 1
            else:
                draws += 1

            print(
                f"seed={seed:2d}R  "
                f"v11={r11:9.0f}  {name}={ro:9.0f}  "
                f"diff={r11-ro:+9.0f}"
            )

        games = wins + draws + losses
        score = (wins + 0.5 * draws) / games

        total_w += wins
        total_d += draws
        total_l += losses

        print(
            f"RESULT: v11 {wins}-{draws}-{losses} {name}  "
            f"score={score:.1%}"
        )
        print(
            f"mean reward: v11={mean(own):.1f}, "
            f"{name}={mean(other):.1f}, "
            f"mean margin={mean(margins):+.1f}"
        )
        print(
            f"v11 min/max reward: {min(own):.0f} / {max(own):.0f}"
        )

    games = total_w + total_d + total_l
    score = (total_w + 0.5 * total_d) / games if games else 0.0

    print("\n=== TOTAL ===")
    print(f"v11 W-D-L = {total_w}-{total_d}-{total_l}")
    print(f"v11 score  = {score:.1%}")


if __name__ == "__main__":
    main()
