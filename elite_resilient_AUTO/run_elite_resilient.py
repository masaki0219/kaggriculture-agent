"""
run_elite_resilient.py

Self-locating launcher for the Kaggriculture elite arena.

You may run this file from its own small patch directory.
It automatically finds the sibling/base directory that actually contains:
- agent_e2_boatlee29.py
- agent_e10_kaito27_current.py
- public_agents/
- elite_arena_cache.json (if already created)

Then it copies/uses elite_arena_resilient.py there and launches it.

Typical:
    python run_elite_resilient.py --seeds 8 --seed-start 1000
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent


def looks_like_base(p: Path) -> bool:
    required = [
        p / "agent_e2_boatlee29.py",
        p / "agent_e6_boatlee29_guard.py",
        p / "agent_e10_kaito27_current.py",
        p / "agent_e11_prvsiyan_frontier.py",
        p / "agent_e12_kaito43_current.py",
        p / "agent_e13_kaito27_guard.py",
        p / "public_agents",
    ]
    return all(x.exists() for x in required)


def find_base() -> Path:
    candidates = []

    # Current directory first.
    candidates.append(HERE)

    # Siblings under the main Kaggle directory.
    parent = HERE.parent
    candidates.extend([
        parent / "kaggriculture_elite_bundle_PATCHED_v2",
        parent / "kaggriculture_elite_bundle_PATCHED",
        parent / "kaggriculture_elite_bundle_FINAL",
    ])

    # Any sibling that looks like a full elite bundle.
    try:
        candidates.extend(
            p for p in parent.iterdir()
            if p.is_dir() and "kaggriculture_elite_bundle" in p.name
        )
    except Exception:
        pass

    # Parent itself in case files were copied into the main Kaggle root.
    candidates.append(parent)

    seen = set()
    for p in candidates:
        try:
            p = p.resolve()
        except Exception:
            continue
        if p in seen:
            continue
        seen.add(p)
        if looks_like_base(p):
            return p

    checked = "\n".join(f"  - {p}" for p in seen)
    raise SystemExit(
        "Could not find the full elite bundle automatically.\n\n"
        "I looked in:\n"
        f"{checked}\n\n"
        "The base directory must contain agent_e2_boatlee29.py, "
        "agent_e10_kaito27_current.py and public_agents/."
    )


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed-start", type=int, default=1000)
    ap.add_argument("--candidates")
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()

    base = find_base()
    print(f"[base] {base}")

    src = HERE / "elite_arena_resilient.py"
    if not src.exists():
        raise SystemExit(f"Missing {src}")

    dst = base / "elite_arena_resilient.py"
    if src.resolve() != dst.resolve():
        shutil.copy2(src, dst)
        print(f"[copy] {src.name} -> {dst}")

    cmd = [
        sys.executable,
        str(dst),
        "--seeds", str(args.seeds),
        "--seed-start", str(args.seed_start),
    ]
    if args.candidates:
        cmd += ["--candidates", args.candidates]
    if args.fresh:
        cmd.append("--fresh")

    print("+", " ".join(cmd))
    raise SystemExit(subprocess.call(cmd, cwd=str(base)))


if __name__ == "__main__":
    main()
