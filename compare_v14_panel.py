"""
compare_v14_panel.py

20-game paired screen for the demand-adaptive herd candidate.

Primary promotion logic:
- qeinstein_portfolio: v12 was 0-20. We want meaningful recovery.
- gzmcr/lonespear: v12 was 20-0. We do not want to give those wins back.
- v12 direct: sanity check for regressions / market-interaction effects.

Run:
    python compare_v14_panel.py
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from statistics import mean
import sys

from kaggle_environments import make

from agent_v12 import agent as v12
from agent_v14 import agent as v14


ROOT = Path(__file__).resolve().parent
SEEDS = range(10)


def load_agent_file(path: Path, module_name: str):
    path = path.resolve()
    repo_root = path.parent.parent if path.parent.name in {"scripts", "agents"} else path.parent

    for p in (repo_root, repo_root / "src", path.parent):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)

    old_cwd = Path.cwd()
    try:
        os.chdir(repo_root)
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    finally:
        os.chdir(old_cwd)

    fn = getattr(module, "agent", None)
    if fn is None:
        raise AttributeError(f"{path} does not expose agent(obs)")
    return fn


def resolve_opponents():
    opponents = {"v12": v12}

    q = ROOT / "public_agents" / "qeinstein" / "scripts" / "frontier_portfolio_entry.py"
    if q.exists():
        try:
            opponents["qeinstein_portfolio"] = load_agent_file(q, "_v14_qeinstein")
        except Exception as exc:
            print(f"[SKIP] qeinstein_portfolio load failed: {exc}")

    g = ROOT / "public_agents" / "gzmcr" / "main.py"
    if g.exists():
        opponents["gzmcr"] = str(g)

    l = ROOT / "public_agents" / "lonespear" / "main.py"
    if l.exists():
        opponents["lonespear"] = str(l)

    return opponents


def play(a0, a1, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([a0, a1])
    final = env.steps[-1]
    return float(final[0].reward), float(final[1].reward)


def run_matchup(name, opponent):
    wins = draws = losses = 0
    own, other, margins = [], [], []

    print(f"\n================ v14 vs {name} ================")

    for seed in SEEDS:
        r14, ro = play(v14, opponent, seed)
        own.append(r14)
        other.append(ro)
        margins.append(r14 - ro)

        if r14 > ro:
            wins += 1
        elif r14 < ro:
            losses += 1
        else:
            draws += 1

        print(
            f"seed={seed:2d}   "
            f"v14={r14:9.0f}  {name}={ro:9.0f}  diff={r14-ro:+9.0f}"
        )

        ro, r14 = play(opponent, v14, seed)
        own.append(r14)
        other.append(ro)
        margins.append(r14 - ro)

        if r14 > ro:
            wins += 1
        elif r14 < ro:
            losses += 1
        else:
            draws += 1

        print(
            f"seed={seed:2d}R  "
            f"v14={r14:9.0f}  {name}={ro:9.0f}  diff={r14-ro:+9.0f}"
        )

    games = wins + draws + losses
    score = (wins + 0.5 * draws) / games

    print(
        f"RESULT: v14 {wins}-{draws}-{losses} {name}  "
        f"score={score:.1%}"
    )
    print(
        f"mean reward: v14={mean(own):.1f}, "
        f"{name}={mean(other):.1f}, "
        f"mean margin={mean(margins):+.1f}"
    )

    return wins, draws, losses


def main():
    opponents = resolve_opponents()
    results = {}

    for name, opponent in opponents.items():
        results[name] = run_matchup(name, opponent)

    print("\n================ SUMMARY ================")
    for name, (w, d, l) in results.items():
        games = w + d + l
        score = (w + 0.5 * d) / games
        print(f"{name:<22} {w:2d}-{d:2d}-{l:2d}  score={score:.1%}")

    print("\nInterpretation:")
    print("- qeinstein_portfolio: any recovery from v12's 0-20 is informative.")
    print("- gzmcr/lonespear: losses are regressions versus v12's old 20-0 screen.")
    print("- v12: direct matchup is only a sanity check, not the final objective.")


if __name__ == "__main__":
    main()
