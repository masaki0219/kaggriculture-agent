from kaggle_environments import make

from submission import melon_maxxer as starter
from agent_v2 import melon_maxxer as v2


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


v2_wins = 0
starter_wins = 0
draws = 0

# 席順の影響も減らすため、入れ替えて対戦
for seed in range(10):

    r_v2, r_starter = play(v2, starter, seed)

    print(
        f"seed={seed:2d}  "
        f"v2={r_v2:8.0f}  starter={r_starter:8.0f}"
    )

    if r_v2 > r_starter:
        v2_wins += 1
    elif r_v2 < r_starter:
        starter_wins += 1
    else:
        draws += 1

    r_starter, r_v2 = play(starter, v2, seed)

    print(
        f"seed={seed:2d}R "
        f"v2={r_v2:8.0f}  starter={r_starter:8.0f}"
    )

    if r_v2 > r_starter:
        v2_wins += 1
    elif r_v2 < r_starter:
        starter_wins += 1
    else:
        draws += 1


print("\n=== RESULT ===")
print(f"v2 wins      : {v2_wins}")
print(f"starter wins : {starter_wins}")
print(f"draws        : {draws}")
print(f"win rate     : {v2_wins / 20:.1%}")
