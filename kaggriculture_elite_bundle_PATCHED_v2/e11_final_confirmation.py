from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from statistics import mean
import sys

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent
PUB = ROOT / "public_agents"
CACHE = ROOT / "e11_final_confirmation_cache.json"
PREFIX = "@@FINAL@@"

OPPONENTS = {
    "e2_boatlee29": ("module", "agent_e2_boatlee29"),
    "e12_kaito43_current": ("module", "agent_e12_kaito43_current"),
    "v15_kaito48": ("module", "agent_v15"),
    "qeinstein_champion": ("path", PUB / "qeinstein" / "scripts" / "champion_entry.py"),
    "qeinstein_candidate7": ("path", PUB / "qeinstein" / "scripts" / "candidate7_entry.py"),
    "qeinstein_portfolio": ("path", PUB / "qeinstein" / "scripts" / "frontier_portfolio_entry.py"),
}


def load_path(path: Path, unique: str):
    path = path.resolve()
    repo_root = path.parent.parent if path.parent.name == "scripts" else path.parent

    for p in (repo_root, repo_root / "src", path.parent):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)

    old = Path.cwd()
    try:
        os.chdir(repo_root)
        spec = importlib.util.spec_from_file_location(unique, path)
        if spec is None or spec.loader is None:
            raise ImportError(path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[unique] = mod
        spec.loader.exec_module(mod)
    finally:
        os.chdir(old)

    for name in ("agent", "kaggle_submission_agent", "submission_agent"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn

    raise AttributeError(f"No agent callable in {path}")


def load_opp(name: str):
    typ, ref = OPPONENTS[name]
    if typ == "module":
        return importlib.import_module(ref).agent
    return load_path(Path(ref), f"_final_{name}")


def child(args):
    try:
        e11 = importlib.import_module("agent_e11_prvsiyan_frontier").agent
        opp = load_opp(args.opp)

        agents = [e11, opp] if not args.swap else [opp, e11]

        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": args.seed},
            debug=False,
        )
        env.run(agents)

        final = env.steps[-1]
        r0, r1 = float(final[0].reward), float(final[1].reward)
        ours, theirs = (r1, r0) if args.swap else (r0, r1)

        print(PREFIX + json.dumps({
            "opp": args.opp,
            "seed": args.seed,
            "swap": args.swap,
            "ours": ours,
            "theirs": theirs,
            "result": "W" if ours > theirs else "L" if ours < theirs else "D",
            "margin": ours - theirs,
        }))

    except Exception as e:
        print(PREFIX + json.dumps({
            "error": f"{type(e).__name__}: {e}",
            "opp": args.opp,
            "seed": args.seed,
            "swap": args.swap,
        }))


def load_cache():
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache):
    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def run_game(opp, seed, swap, cache):
    key = f"{opp}|{seed}|{int(swap)}"

    if key in cache and "error" not in cache[key]:
        return cache[key]

    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--opp", opp,
        "--seed", str(seed),
    ]
    if swap:
        cmd.append("--swap")

    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    rec = None
    for line in p.stdout.splitlines():
        if line.startswith(PREFIX):
            rec = json.loads(line[len(PREFIX):])

    if rec is None:
        rec = {"error": p.stderr[-1500:] or "no structured result"}

    cache[key] = rec
    save_cache(cache)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--seed-start", type=int, default=20000)
    ap.add_argument("--opp")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--swap", action="store_true")
    args = ap.parse_args()

    if args.opp:
        child(args)
        return

    cache = load_cache()
    all_rows = []

    print("========== E11 FINAL CONFIRMATION ==========")
    print(
        f"fresh seeds {args.seed_start}.."
        f"{args.seed_start + args.seeds - 1}, both seats"
    )

    for opp in OPPONENTS:
        rows = []
        err = None

        for seed in range(args.seed_start, args.seed_start + args.seeds):
            for swap in (False, True):
                rec = run_game(opp, seed, swap, cache)
                if "error" in rec:
                    err = rec["error"]
                    break
                rows.append(rec)
            if err:
                break

        print(f"\n=== E11 vs {opp} ===")

        if err:
            print("[SKIP]", err)
            continue

        w = sum(r["result"] == "W" for r in rows)
        d = sum(r["result"] == "D" for r in rows)
        l = sum(r["result"] == "L" for r in rows)
        margin = mean(r["margin"] for r in rows)

        print(
            f"{w}-{d}-{l} "
            f"score={(w + 0.5*d) / len(rows):.1%} "
            f"margin={margin:+.0f}"
        )

        all_rows += rows

    if all_rows:
        w = sum(r["result"] == "W" for r in all_rows)
        d = sum(r["result"] == "D" for r in all_rows)
        l = sum(r["result"] == "L" for r in all_rows)
        margin = mean(r["margin"] for r in all_rows)

        print("\n========== TOTAL ==========")
        print(
            f"E11 {w}-{d}-{l} "
            f"score={(w + 0.5*d) / len(all_rows):.1%} "
            f"margin={margin:+.0f}"
        )


if __name__ == "__main__":
    main()
