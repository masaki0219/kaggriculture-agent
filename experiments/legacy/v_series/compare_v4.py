from statistics import mean, median

from kaggle_environments import make

from agent_v3 import melon_maxxer as v3
from agent_v4 import melon_maxxer as v4


SEED_COUNT = 50


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

    return final[0].reward, final[1].reward


v4_wins = 0
v3_wins = 0
draws = 0

v4_rewards = []
v3_rewards = []
margins = []


for seed in range(SEED_COUNT):
    # Match A: v4 starts in seat 0.
    r_v4, r_v3 = play(v4, v3, seed)

    v4_rewards.append(r_v4)
    v3_rewards.append(r_v3)
    margins.append(r_v4 - r_v3)

    print(
        f"seed={seed:2d}   "
        f"v4={r_v4:8.0f}  "
        f"v3={r_v3:8.0f}  "
        f"diff={r_v4 - r_v3:+8.0f}"
    )

    if r_v4 > r_v3:
        v4_wins += 1
    elif r_v4 < r_v3:
        v3_wins += 1
    else:
        draws += 1

    # Match B: swap seats to reduce seat-order bias.
    r_v3, r_v4 = play(v3, v4, seed)

    v4_rewards.append(r_v4)
    v3_rewards.append(r_v3)
    margins.append(r_v4 - r_v3)

    print(
        f"seed={seed:2d}R  "
        f"v4={r_v4:8.0f}  "
        f"v3={r_v3:8.0f}  "
        f"diff={r_v4 - r_v3:+8.0f}"
    )

    if r_v4 > r_v3:
        v4_wins += 1
    elif r_v4 < r_v3:
        v3_wins += 1
    else:
        draws += 1


total_matches = SEED_COUNT * 2
decided_matches = v4_wins + v3_wins

print("\n=== RESULT ===")
print(f"matches       : {total_matches}")
print(f"v4 wins       : {v4_wins}")
print(f"v3 wins       : {v3_wins}")
print(f"draws         : {draws}")
print(f"v4 win rate   : {v4_wins / total_matches:.1%}")

if decided_matches > 0:
    print(
        f"v4 decided WR : "
        f"{v4_wins / decided_matches:.1%}"
    )

print("\n=== REWARD SUMMARY ===")
print(f"v4 mean       : {mean(v4_rewards):.1f}")
print(f"v3 mean       : {mean(v3_rewards):.1f}")
print(f"v4 median     : {median(v4_rewards):.1f}")
print(f"v3 median     : {median(v3_rewards):.1f}")
print(f"mean diff     : {mean(margins):+.1f}")
print(f"median diff   : {median(margins):+.1f}")
