
from kaggle_environments import make
from submission import melon_maxxer

# Kaggriculture環境を作成
env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 720,
        "seed": 42,
    },
    debug=True,
)

print("Match start")

# Starter Agent vs Starter Agent
env.run([
    melon_maxxer,
    melon_maxxer,
])

# 最終状態
final = env.steps[-1]

print("\n=== RESULT ===")

for i, player in enumerate(final):
    print(
        f"Player {i}: "
        f"reward={player.reward}, "
        f"status={player.status}"
    )
