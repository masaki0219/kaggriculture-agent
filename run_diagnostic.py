from statistics import mean

from kaggle_environments import make

import agent_v4_diagnostic as diag
from agent_v4 import melon_maxxer as v4


SEEDS = range(10)


def run_one(seed):
    diag.reset_stats()

    env = make(
        "kaggriculture",
        configuration={
            "episodeSteps": 720,
            "seed": seed,
        },
        debug=True,
    )

    env.run([
        diag.melon_maxxer,
        v4,
    ])

    final = env.steps[-1]
    stats = diag.get_stats()

    reward = final[0].reward

    target_count = stats["TARGET_DISTANCE_COUNT"]
    avg_target_distance = (
        stats["TARGET_DISTANCE_SUM"] / target_count
        if target_count
        else 0.0
    )

    purpose_avgs = {}
    for purpose, data in stats["TARGET_BY_PURPOSE"].items():
        if data["count"]:
            purpose_avgs[purpose] = (
                data["distance_sum"] / data["count"]
            )
        else:
            purpose_avgs[purpose] = 0.0

    return {
        "seed": seed,
        "reward": reward,
        "stats": stats,
        "avg_target_distance": avg_target_distance,
        "purpose_avgs": purpose_avgs,
    }


results = [run_one(seed) for seed in SEEDS]

for r in results:
    s = r["stats"]

    print(
        f"seed={r['seed']:2d}  "
        f"reward={r['reward']:8.0f}  "
        f"MOVE={s['MOVE']:3d}  "
        f"WATER={s['WATER']:3d}  "
        f"PLANT={s['PLANT']:3d}  "
        f"HARVEST={s['HARVEST']:3d}  "
        f"PASS={s['PASS']:3d}  "
        f"avg_target_dist={r['avg_target_distance']:.2f}"
    )

print("\n=== AVERAGE OVER SEEDS ===")

for key in ["MOVE", "WATER", "PLANT", "HARVEST", "PASS"]:
    print(
        f"{key:8s}: "
        f"{mean(r['stats'][key] for r in results):.1f}"
    )

print(
    "avg target distance: "
    f"{mean(r['avg_target_distance'] for r in results):.2f}"
)

print("\n=== TARGET DISTANCE BY PURPOSE ===")
for purpose in ["harvest", "water", "plant"]:
    vals = [
        r["purpose_avgs"][purpose]
        for r in results
        if r["stats"]["TARGET_BY_PURPOSE"][purpose]["count"] > 0
    ]

    if vals:
        print(
            f"{purpose:8s}: "
            f"{mean(vals):.2f}"
        )
    else:
        print(f"{purpose:8s}: no targets")
