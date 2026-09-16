from kaggle_environments import make

from agent_v4 import melon_maxxer as v4
from agent_v8_debug import agent as v8


def run_case(name, agents, seed):
    print(f"\n=== {name} seed={seed} ===")
    env = make(
        "kaggriculture",
        configuration={
            "episodeSteps": 720,
            "seed": seed,
        },
        debug=True,
    )

    try:
        env.run(agents)
    except Exception as exc:
        print(f"\nCAUGHT: {exc!r}")
        raise

    final = env.steps[-1]
    print("final rewards:", final[0].reward, final[1].reward)
    print("final status :", final[0].status, final[1].status)


# One catastrophic case from the reported benchmark:
# v8=182 vs v4=26661
run_case(
    "v8 seat0 vs v4",
    [v8, v4],
    4,
)
