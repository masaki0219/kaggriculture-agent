from statistics import mean, median

from kaggle_environments import make

from agent_v4 import melon_maxxer as v4
from agent_v5 import melon_maxxer as v5


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


v5_wins = 0
v4_wins = 0
draws = 0

v5_rewards = []
v4_rewards = []
margins = []


for seed in range(SEED_COUNT):
    r_v5, r_v4 = play(v5, v4, seed)

    v5_rewards.append(r_v5)
    v4_rewards.append(r_v4)
    margins.append(r_v5 - r_v4)

    print(
        f"seed={seed:2d}   "
        f"v5={r_v5:8.0f}  "
        f"v4={r_v4:8.0f}  "
        f"diff={r_v5 - r_v4:+8.0f}"
    )

    if r_v5 > r_v4:
        v5_wins += 1
    elif r_v5 < r_v4:
        v4_wins += 1
    else:
        draws += 1

    r_v4, r_v5 = play(v4, v5, seed)

    v5_rewards.append(r_v5)
    v4_rewards.append(r_v4)
    margins.append(r_v5 - r_v4)

    print(
        f"seed={seed:2d}R  "
        f"v5={r_v5:8.0f}  "
        f"v4={r_v4:8.0f}  "
        f"diff={r_v5 - r_v4:+8.0f}"
    )

    if r_v5 > r_v4:
        v5_wins += 1
    elif r_v5 < r_v4:
        v4_wins += 1
    else:
        draws += 1


total_matches = SEED_COUNT * 2
decided_matches = v5_wins + v4_wins

print("\n=== RESULT ===")
print(f"matches       : {total_matches}")
print(f"v5 wins       : {v5_wins}")
print(f"v4 wins       : {v4_wins}")
print(f"draws         : {draws}")
print(f"v5 win rate   : {v5_wins / total_matches:.1%}")

if decided_matches > 0:
    print(
        f"v5 decided WR : "
        f"{v5_wins / decided_matches:.1%}"
    )

print("\n=== REWARD SUMMARY ===")
print(f"v5 mean       : {mean(v5_rewards):.1f}")
print(f"v4 mean       : {mean(v4_rewards):.1f}")
print(f"v5 median     : {median(v5_rewards):.1f}")
print(f"v4 median     : {median(v4_rewards):.1f}")
print(f"mean diff     : {mean(margins):+.1f}")
print(f"median diff   : {median(margins):+.1f}")
