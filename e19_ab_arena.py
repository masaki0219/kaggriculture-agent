from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from statistics import mean

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "kaggriculture_elite_bundle_PATCHED_v2"
PUB = ROOT / "public_agents"

if not BUNDLE.exists():
    raise FileNotFoundError(f"Elite bundle not found: {BUNDLE}")
if str(BUNDLE) not in sys.path:
    sys.path.insert(0, str(BUNDLE))

CACHE = ROOT / "e19_ab_cache.json"
PREFIX = "@@E19GAME@@"

CANDIDATES = {
    "e11": "agent_e11_prvsiyan_frontier",
    "e19_early_sw": "agent_e19_prvsiyan_early_sw",
}

OPPONENTS = {
    "e2_boatlee29": ("module", "agent_e2_boatlee29"),
    "v15_kaito48": ("path", ROOT / "agent_v15.py"),
    "qeinstein_champion": ("path", PUB / "qeinstein" / "scripts" / "champion_entry.py"),
    "qeinstein_candidate7": ("path", PUB / "qeinstein" / "scripts" / "candidate7_entry.py"),
}

TELEMETRY_KEYS = (
    "eligible_games",
    "early_land_requests",
    "early_land_activated",
    "activation_failures",
    "extra_hires",
    "preplants",
    "waters",
    "native_land_suppressed",
    "redundant_native_plants_suppressed",
    "no_targets",
    "no_seed",
    "cash_waits",
    "market_full",
)


def load_path(path: Path, unique: str):
    path = path.resolve()
    repo_root = path.parent.parent if path.parent.name == "scripts" else path.parent
    for p in (repo_root, repo_root / "src", path.parent):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
    import os
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
    raise AttributeError(path)


def resolve(kind, name):
    if kind == "candidate":
        return importlib.import_module(CANDIDATES[name]).agent
    typ, ref = OPPONENTS[name]
    if typ == "module":
        return importlib.import_module(ref).agent
    return load_path(Path(ref), f"_e19_{name}")


def child(args):
    try:
        left = resolve(args.lk, args.left)
        right = resolve(args.rk, args.right)
        agents = [left, right] if not args.swap else [right, left]
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": args.seed},
            debug=False,
        )
        env.run(agents)
        final = env.steps[-1]
        a, b = float(final[0].reward), float(final[1].reward)
        if args.swap:
            a, b = b, a

        telemetry = {}
        if args.lk == "candidate":
            try:
                mod = importlib.import_module(CANDIDATES[args.left])
                telemetry = dict(getattr(mod.agent, "telemetry", {}) or {})
            except Exception:
                pass

        print(PREFIX + json.dumps({
            "left": args.left,
            "right": args.right,
            "seed": args.seed,
            "swap": args.swap,
            "a": a,
            "b": b,
            "r": "W" if a > b else "L" if a < b else "D",
            "m": a - b,
            "telemetry": telemetry,
        }))
    except Exception as exc:
        print(PREFIX + json.dumps({"error": f"{type(exc).__name__}: {exc}"}))


def load_cache():
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return {}


def save_cache(cache):
    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def run_game(lk, left, rk, right, seed, swap, cache):
    key = f"{lk}|{left}|{rk}|{right}|{seed}|{int(swap)}"
    if key in cache and "error" not in cache[key]:
        return cache[key]
    cmd = [
        sys.executable, str(Path(__file__).resolve()),
        "--lk", lk, "--left", left, "--rk", rk, "--right", right,
        "--seed", str(seed),
    ]
    if swap:
        cmd.append("--swap")
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    rec = None
    for line in proc.stdout.splitlines():
        if line.startswith(PREFIX):
            rec = json.loads(line[len(PREFIX):])
    if rec is None:
        rec = {"error": proc.stderr[-1500:] or "no result"}
    cache[key] = rec
    save_cache(cache)
    return rec


def pair(lk, left, rk, right, seeds, cache):
    rows = []
    for seed in seeds:
        for swap in (False, True):
            rec = run_game(lk, left, rk, right, seed, swap, cache)
            if "error" in rec:
                return rows, rec["error"]
            rows.append(rec)
    return rows, None


def summary(rows):
    w = sum(row["r"] == "W" for row in rows)
    d = sum(row["r"] == "D" for row in rows)
    l = sum(row["r"] == "L" for row in rows)
    return w, d, l, mean(row["m"] for row in rows) if rows else 0.0


def telemetry_sum(rows):
    out = {key: 0 for key in TELEMETRY_KEYS}
    for row in rows:
        telemetry = row.get("telemetry") or {}
        for key in TELEMETRY_KEYS:
            out[key] += int(telemetry.get(key, 0) or 0)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--seed-start", type=int, default=32000)
    parser.add_argument("--direct-only", action="store_true")
    parser.add_argument("--lk")
    parser.add_argument("--left")
    parser.add_argument("--rk")
    parser.add_argument("--right")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--swap", action="store_true")
    args = parser.parse_args()

    if args.lk:
        child(args)
        return

    seeds = range(args.seed_start, args.seed_start + args.seeds)
    cache = load_cache()

    print("========== E11 vs E19 DIRECT ==========")
    rows, err = pair("candidate", "e19_early_sw", "candidate", "e11", seeds, cache)
    if err:
        raise SystemExit(err)
    w, d, l, margin = summary(rows)
    telemetry = telemetry_sum(rows)
    print(f"E19 vs E11: {w}-{d}-{l} meanMargin={margin:+.0f}")
    print("telemetry:", json.dumps(telemetry, ensure_ascii=False))

    results = {
        "e19_vs_e11": {
            "W": w, "D": d, "L": l, "mean_margin": margin,
            "telemetry": telemetry,
        }
    }

    mechanism_live = (
        telemetry["early_land_activated"] > 0
        and telemetry["preplants"] > 0
        and telemetry["waters"] > 0
    )
    if not mechanism_live:
        print("\nSTOP: E19 mechanism did not fully activate (land + plant + water required).")
        print("Inspect telemetry before any larger evaluation.")
        Path("e19_ab_results.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return

    if args.direct_only:
        Path("e19_ab_results.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return

    print("\n========== STRONG HOLDOUTS ==========")
    for opponent in OPPONENTS:
        e11_rows, err = pair("candidate", "e11", "opponent", opponent, seeds, cache)
        if err:
            print(f"[SKIP] e11 vs {opponent}: {err}")
            continue

        e19_rows, err = pair("candidate", "e19_early_sw", "opponent", opponent, seeds, cache)
        if err:
            print(f"[SKIP] e19 vs {opponent}: {err}")
            continue

        s11 = summary(e11_rows)
        s19 = summary(e19_rows)
        tel = telemetry_sum(e19_rows)
        print(
            f"{opponent:24s} "
            f"E11={s11[0]}-{s11[1]}-{s11[2]} {s11[3]:+8.0f}   "
            f"E19={s19[0]}-{s19[1]}-{s19[2]} {s19[3]:+8.0f}   "
            f"land={tel['early_land_activated']} plant={tel['preplants']} water={tel['waters']}"
        )
        results[opponent] = {
            "e11": {"W": s11[0], "D": s11[1], "L": s11[2], "mean_margin": s11[3]},
            "e19": {"W": s19[0], "D": s19[1], "L": s19[2], "mean_margin": s19[3]},
            "telemetry": tel,
        }

    Path("e19_ab_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nInterpretation:")
    print("- land/plant/water telemetry must all activate; otherwise fix the mechanism first.")
    print("- Any reproducible direct or strong-holdout W-D-L regression rejects E19.")
    print("- Mean margin alone does not promote E19.")
    print("- If non-regressive, expand to fresh seeds/opponent panel before promotion.")


if __name__ == "__main__":
    main()
