"""
compare_h1_panel.py

Quick paired screen for agent_h1.

Default:
    python compare_h1_panel.py

5 seeds x both seats = 10 games / opponent.
If promising:
    python compare_h1_panel.py --seeds 10

Every matchup is launched in a fresh Python process.
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

from agent_h1 import agent as h1


ROOT = Path(__file__).resolve().parent
PUB = ROOT / "public_agents"

OPPONENTS = {
    "v15_kaito48": {
        "kind": "module",
        "module": "agent_v15",
    },
    "boatlee_v16": {
        "kind": "path",
        "path": PUB / "hbharath" / "agents" / "public" / "boatlee_v16_rc5_r5a_8c4s_recovery.py",
    },
    "rayk_c94": {
        "kind": "path",
        "path": PUB / "hbharath" / "agents" / "public" / "rayk_c94_findings_meta.py",
    },
    "qeinstein_champion": {
        "kind": "import_file",
        "path": PUB / "qeinstein" / "scripts" / "champion_entry.py",
    },
    "qeinstein_candidate5": {
        "kind": "import_file",
        "path": PUB / "qeinstein" / "scripts" / "candidate5_entry.py",
    },
    "qeinstein_candidate7": {
        "kind": "import_file",
        "path": PUB / "qeinstein" / "scripts" / "candidate7_entry.py",
    },
    "qeinstein_portfolio": {
        "kind": "import_file",
        "path": PUB / "qeinstein" / "scripts" / "frontier_portfolio_entry.py",
    },
    "gzmcr": {
        "kind": "path",
        "path": PUB / "gzmcr" / "main.py",
    },
    "lonespear": {
        "kind": "path",
        "path": PUB / "lonespear" / "main.py",
    },
}


def load_import_file(path: Path, module_name: str):
    path = path.resolve()
    repo_root = path.parent.parent if path.parent.name in {"scripts", "agents"} else path.parent

    for p in (repo_root, repo_root / "src", path.parent):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)

    old = Path.cwd()
    try:
        os.chdir(repo_root)
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    finally:
        os.chdir(old)

    fn = getattr(module, "agent", None)
    if not callable(fn):
        raise AttributeError(f"{path} has no callable agent")
    return fn


def resolve(name):
    spec = OPPONENTS[name]
    if spec["kind"] == "module":
        module = __import__(spec["module"])
        return module.agent

    path = Path(spec["path"])
    if not path.exists():
        raise FileNotFoundError(path)

    if spec["kind"] == "path":
        return str(path.resolve())

    return load_import_file(path, f"_h1_{name}")


def play(a0, a1, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([a0, a1])
    final = env.steps[-1]
    return float(final[0].reward), float(final[1].reward)


def run_one(name, seeds):
    opp = resolve(name)
    w = d = l = 0
    own = []
    other = []
    margins = []

    print(f"\n================ h1 vs {name} ================")

    for seed in range(seeds):
        rh, ro = play(h1, opp, seed)
        own.append(rh); other.append(ro); margins.append(rh - ro)
        if rh > ro: w += 1
        elif rh < ro: l += 1
        else: d += 1
        print(f"seed={seed:2d}   h1={rh:9.0f} opp={ro:9.0f} diff={rh-ro:+9.0f}")

        ro, rh = play(opp, h1, seed)
        own.append(rh); other.append(ro); margins.append(rh - ro)
        if rh > ro: w += 1
        elif rh < ro: l += 1
        else: d += 1
        print(f"seed={seed:2d}R  h1={rh:9.0f} opp={ro:9.0f} diff={rh-ro:+9.0f}")

    games = w + d + l
    score = (w + 0.5 * d) / games

    print(
        f"RESULT {name}: h1 {w}-{d}-{l}, score={score:.1%}, "
        f"mean h1={mean(own):.1f}, opp={mean(other):.1f}, "
        f"margin={mean(margins):+.1f}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--opponent", choices=sorted(OPPONENTS))
    args = ap.parse_args()

    if args.opponent:
        run_one(args.opponent, args.seeds)
        return

    for name in OPPONENTS:
        print(f"\n\n######## {name} ########", flush=True)
        p = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--opponent", name,
                "--seeds", str(args.seeds),
            ],
            cwd=str(ROOT),
        )
        if p.returncode != 0:
            print(f"[FAILED] {name}: exit={p.returncode}")


if __name__ == "__main__":
    main()
