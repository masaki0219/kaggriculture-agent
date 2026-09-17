from kaggle_environments import make

from submission import melon_maxxer as starter
from agent_v3 import melon_maxxer as v3


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


v3_wins = 0
starter_wins = 0
draws = 0

# 席順の影響も減らすため、入れ替えて対戦
for seed in range(10):

    r_v3, r_starter = play(v3, starter, seed)

    print(
        f"seed={seed:2d}  "
        f"v3={r_v3  :8.0f}  starter={r_starter:8.0f}"
    )

    if r_v3 > r_starter:
        v3_wins += 1
    elif r_v3 < r_starter:
        starter_wins += 1
    else:
        draws += 1

    r_starter, r_v3 = play(starter, v3, seed)

    print(
        f"seed={seed:2d}R "
        f"v3={r_v3:8.0f}  starter={r_starter:8.0f}"
    )

    if r_v3 > r_starter:
        v3_wins += 1
    elif r_v3 < r_starter:
        starter_wins += 1
    else:
        draws += 1


print("\n=== RESULT ===")
print(f"v3 wins      : {v3_wins}")
print(f"starter wins : {starter_wins}")
print(f"draws        : {draws}")
print(f"win rate     : {v3_wins / 20:.1%}")
