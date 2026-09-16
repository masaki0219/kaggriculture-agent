from __future__ import annotations

import csv
import itertools
import subprocess
from collections import defaultdict
from pathlib import Path
from statistics import mean

from kaggle_environments import make

from agent_v4 import melon_maxxer as v4
from agent_v7 import melon_maxxer as v7


ROOT = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT / "public_agents"

# 10 seeds × both seat orders × C(6, 2) = 300 games.
SEEDS = range(10)

PUBLIC_REPOS = {
    "gzmcr": {
        "url": "https://github.com/GzmCR/Kaggriculture.git",
        "dir": PUBLIC_DIR / "gzmcr",
        "agent_file": "main.py",
    },
    "lonespear": {
        "url": "https://github.com/lonespear/kaggriculture.git",
        "dir": PUBLIC_DIR / "lonespear",
        "agent_file": "main.py",
    },
    "seyamalam": {
        "url": "https://github.com/Seyamalam/Kaggriculture.git",
        "dir": PUBLIC_DIR / "seyamalam",
        "agent_file": "main.py",
    },
}


def run_cmd(args, cwd=None):
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def setup_public_agents():
    PUBLIC_DIR.mkdir(exist_ok=True)

    available = {}

    for name, info in PUBLIC_REPOS.items():
        repo_dir = info["dir"]

        try:
            if not repo_dir.exists():
                print(f"[clone] {name}")
                run_cmd([
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    info["url"],
                    str(repo_dir),
                ])
            else:
                print(f"[update] {name}")
                # Keep the comparison set reasonably current without
                # modifying any public agent source ourselves.
                run_cmd([
                    "git",
                    "-C",
                    str(repo_dir),
                    "pull",
                    "--ff-only",
                ])

            commit = run_cmd([
                "git",
                "-C",
                str(repo_dir),
                "rev-parse",
                "--short",
                "HEAD",
            ]).stdout.strip()

            agent_path = repo_dir / info["agent_file"]
            if not agent_path.exists():
                raise FileNotFoundError(agent_path)

            available[name] = str(agent_path)
            print(f"  -> {name}: {commit} ({agent_path})")

        except Exception as exc:
            print(f"[SKIP] {name}: {exc}")

    return available


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

    r0 = final[0].reward
    r1 = final[1].reward
    s0 = final[0].status
    s1 = final[1].status

    if r0 is None or r1 is None:
        raise RuntimeError(
            f"missing reward: status0={s0}, status1={s1}"
        )

    return float(r0), float(r1), s0, s1


def add_result(overall, name_a, name_b, reward_a, reward_b):
    overall[name_a]["games"] += 1
    overall[name_b]["games"] += 1

    overall[name_a]["rewards"].append(reward_a)
    overall[name_b]["rewards"].append(reward_b)

    if reward_a > reward_b:
        overall[name_a]["wins"] += 1
        overall[name_b]["losses"] += 1
        return "A"
    elif reward_a < reward_b:
        overall[name_b]["wins"] += 1
        overall[name_a]["losses"] += 1
        return "B"
    else:
        overall[name_a]["draws"] += 1
        overall[name_b]["draws"] += 1
        return "D"


def main():
    public_agents = setup_public_agents()

    agents = {
        "v4": v4,
        "v7": v7,
        "starter": "starter",
        **public_agents,
    }

    names = list(agents)

    print("\n=== AGENTS ===")
    for name in names:
        print(f"- {name}")

    pair_stats = {}
    overall = defaultdict(
        lambda: {
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "games": 0,
            "rewards": [],
            "errors": 0,
        }
    )

    errors = []

    for name_a, name_b in itertools.combinations(names, 2):
        a = agents[name_a]
        b = agents[name_b]

        stats = {
            "a_wins": 0,
            "b_wins": 0,
            "draws": 0,
            "games": 0,
            "a_rewards": [],
            "b_rewards": [],
        }

        print(f"\n=== {name_a} vs {name_b} ===")

        for seed in SEEDS:
            # A in seat 0, B in seat 1
            try:
                ra, rb, sa, sb = play(a, b, seed)
                result = add_result(
                    overall,
                    name_a,
                    name_b,
                    ra,
                    rb,
                )

                stats["games"] += 1
                stats["a_rewards"].append(ra)
                stats["b_rewards"].append(rb)

                if result == "A":
                    stats["a_wins"] += 1
                elif result == "B":
                    stats["b_wins"] += 1
                else:
                    stats["draws"] += 1

                print(
                    f"seed={seed:2d}   "
                    f"{name_a}={ra:9.0f}  "
                    f"{name_b}={rb:9.0f}"
                )

            except Exception as exc:
                overall[name_a]["errors"] += 1
                overall[name_b]["errors"] += 1
                errors.append(
                    f"{name_a} vs {name_b}, seed={seed}: {exc}"
                )
                print(
                    f"seed={seed:2d}   ERROR: {exc}"
                )

            # Swap seats
            try:
                rb, ra, sb, sa = play(b, a, seed)
                result = add_result(
                    overall,
                    name_a,
                    name_b,
                    ra,
                    rb,
                )

                stats["games"] += 1
                stats["a_rewards"].append(ra)
                stats["b_rewards"].append(rb)

                if result == "A":
                    stats["a_wins"] += 1
                elif result == "B":
                    stats["b_wins"] += 1
                else:
                    stats["draws"] += 1

                print(
                    f"seed={seed:2d}R  "
                    f"{name_a}={ra:9.0f}  "
                    f"{name_b}={rb:9.0f}"
                )

            except Exception as exc:
                overall[name_a]["errors"] += 1
                overall[name_b]["errors"] += 1
                errors.append(
                    f"{name_b} vs {name_a}, seed={seed}R: {exc}"
                )
                print(
                    f"seed={seed:2d}R  ERROR: {exc}"
                )

        pair_stats[(name_a, name_b)] = stats

        if stats["games"]:
            score_a = (
                stats["a_wins"] + 0.5 * stats["draws"]
            ) / stats["games"]

            print(
                f"PAIR RESULT: {name_a} "
                f"{stats['a_wins']}-{stats['draws']}-"
                f"{stats['b_wins']} {name_b}  "
                f"{name_a} score={score_a:.1%}"
            )

    print("\n\n==============================")
    print("=== OVERALL ROUND ROBIN ===")
    print("==============================")

    ranking = []

    for name in names:
        s = overall[name]
        games = s["games"]

        score = (
            (s["wins"] + 0.5 * s["draws"]) / games
            if games
            else 0.0
        )

        avg_reward = (
            mean(s["rewards"])
            if s["rewards"]
            else 0.0
        )

        ranking.append(
            (
                score,
                name,
                s["wins"],
                s["draws"],
                s["losses"],
                avg_reward,
                s["errors"],
            )
        )

    ranking.sort(reverse=True)

    for rank, item in enumerate(ranking, start=1):
        (
            score,
            name,
            wins,
            draws,
            losses,
            avg_reward,
            error_count,
        ) = item

        print(
            f"{rank:2d}. {name:12s} "
            f"score={score:6.1%}  "
            f"W-D-L={wins:3d}-{draws:3d}-{losses:3d}  "
            f"avg_reward={avg_reward:10.1f}  "
            f"errors={error_count}"
        )

    print("\n=== HEAD-TO-HEAD MATRIX ===")
    print("cell = row agent's score vs column agent")

    width = 12
    print("".ljust(width), end="")
    for col in names:
        print(col[:10].rjust(width), end="")
    print()

    for row in names:
        print(row[:10].ljust(width), end="")

        for col in names:
            if row == col:
                text = "-"
            else:
                key = (row, col)
                reverse = False

                if key not in pair_stats:
                    key = (col, row)
                    reverse = True

                st = pair_stats[key]

                if not st["games"]:
                    text = "ERR"
                else:
                    if not reverse:
                        score = (
                            st["a_wins"] + 0.5 * st["draws"]
                        ) / st["games"]
                    else:
                        score = (
                            st["b_wins"] + 0.5 * st["draws"]
                        ) / st["games"]

                    text = f"{score:.0%}"

            print(text.rjust(width), end="")

        print()

    out_csv = ROOT / "round_robin_results.csv"

    with out_csv.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.writer(f)
        writer.writerow([
            "agent_a",
            "agent_b",
            "games",
            "a_wins",
            "draws",
            "b_wins",
            "a_score",
            "a_mean_reward",
            "b_mean_reward",
        ])

        for (name_a, name_b), st in pair_stats.items():
            games = st["games"]

            score_a = (
                (
                    st["a_wins"]
                    + 0.5 * st["draws"]
                ) / games
                if games
                else 0.0
            )

            writer.writerow([
                name_a,
                name_b,
                games,
                st["a_wins"],
                st["draws"],
                st["b_wins"],
                score_a,
                mean(st["a_rewards"])
                if st["a_rewards"]
                else "",
                mean(st["b_rewards"])
                if st["b_rewards"]
                else "",
            ])

    print(f"\nCSV saved: {out_csv}")

    if errors:
        error_file = ROOT / "round_robin_errors.txt"
        error_file.write_text(
            "\n".join(errors),
            encoding="utf-8",
        )
        print(f"Errors saved: {error_file}")


if __name__ == "__main__":
    main()
