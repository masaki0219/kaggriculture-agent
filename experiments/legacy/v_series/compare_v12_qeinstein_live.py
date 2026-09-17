"""
compare_v12_qeinstein_live.py

Compare frozen v12 against several qeinstein policy lines that had substantially
better Kaggle live results than the newer local-only Frontier Portfolio.

Each opponent is run in a FRESH PYTHON PROCESS because qeinstein entry scripts
set environment variables and import stateful modules at import time. Running
multiple entries in one interpreter can contaminate the comparison.

Usage:
    python compare_v12_qeinstein_live.py

Optional:
    python compare_v12_qeinstein_live.py --opponent champion
    python compare_v12_qeinstein_live.py --opponent candidate5
    python compare_v12_qeinstein_live.py --opponent candidate7
    python compare_v12_qeinstein_live.py --opponent portfolio
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
from statistics import mean
import sys

from kaggle_environments import make

from agent_v12 import agent as v12


ROOT = Path(__file__).resolve().parent
QROOT = ROOT / "public_agents" / "qeinstein"
SEEDS = range(10)

OPPONENT_PATHS = {
    "champion": QROOT / "scripts" / "champion_entry.py",
    "candidate5": QROOT / "scripts" / "candidate5_entry.py",
    "candidate7": QROOT / "scripts" / "candidate7_entry.py",
    "portfolio": QROOT / "scripts" / "frontier_portfolio_entry.py",
}


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


def play(a0, a1, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([a0, a1])
    final = env.steps[-1]
    return float(final[0].reward), float(final[1].reward)


def run_one(name: str):
    path = OPPONENT_PATHS[name]
    if not path.exists():
        raise SystemExit(f"Missing opponent: {path}")

    opponent = load_agent_file(path, f"_qe_{name}")

    wins = draws = losses = 0
    own, other, margins = [], [], []

    print(f"\n================ v12 vs qeinstein:{name} ================")

    for seed in SEEDS:
        rv12, ropp = play(v12, opponent, seed)
        own.append(rv12)
        other.append(ropp)
        margins.append(rv12 - ropp)

        if rv12 > ropp:
            wins += 1
        elif rv12 < ropp:
            losses += 1
        else:
            draws += 1

        print(
            f"seed={seed:2d}   "
            f"v12={rv12:9.0f}  {name}={ropp:9.0f}  "
            f"diff={rv12-ropp:+9.0f}"
        )

        ropp, rv12 = play(opponent, v12, seed)
        own.append(rv12)
        other.append(ropp)
        margins.append(rv12 - ropp)

        if rv12 > ropp:
            wins += 1
        elif rv12 < ropp:
            losses += 1
        else:
            draws += 1

        print(
            f"seed={seed:2d}R  "
            f"v12={rv12:9.0f}  {name}={ropp:9.0f}  "
            f"diff={rv12-ropp:+9.0f}"
        )

    games = wins + draws + losses
    score = (wins + 0.5 * draws) / games

    print(f"\nRESULT {name}: v12 {wins}-{draws}-{losses}, score={score:.1%}")
    print(
        f"mean reward: v12={mean(own):.1f}, "
        f"{name}={mean(other):.1f}, "
        f"mean margin={mean(margins):+.1f}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--opponent", choices=sorted(OPPONENT_PATHS))
    args = parser.parse_args()

    if args.opponent:
        run_one(args.opponent)
        return

    # Fresh process per qeinstein entry to avoid environment/module-state leakage.
    for name in ("champion", "candidate5", "candidate7", "portfolio"):
        print(f"\n\n######## launching isolated matchup: {name} ########", flush=True)
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--opponent", name],
            cwd=str(ROOT),
        )
        if completed.returncode != 0:
            print(f"[FAILED] {name}: exit code {completed.returncode}")


if __name__ == "__main__":
    main()
