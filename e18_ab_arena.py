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

# Keep the historical project layout intact: active agents/compare scripts live
# at project root; the elite bundle is a frozen dependency.
if not BUNDLE.exists():
    raise FileNotFoundError(f"Elite bundle not found: {BUNDLE}")
if str(BUNDLE) not in sys.path:
    sys.path.insert(0, str(BUNDLE))
CACHE = ROOT / "e18_ab_cache.json"
PREFIX = "@@E18GAME@@"

CANDIDATES = {
    "e11": "agent_e11_prvsiyan_frontier",
    "e18_late_shop": "agent_e18_prvsiyan_late_shop",
}

OPPONENTS = {
    "e2_boatlee29": ("module", "agent_e2_boatlee29"),
    "v15_kaito48": ("path", ROOT / "agent_v15.py"),
    "qeinstein_champion": ("path", PUB / "qeinstein" / "scripts" / "champion_entry.py"),
    "qeinstein_candidate7": ("path", PUB / "qeinstein" / "scripts" / "candidate7_entry.py"),
}


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
    for n in ("agent", "kaggle_submission_agent", "submission_agent"):
        fn = getattr(mod, n, None)
        if callable(fn):
            return fn
    raise AttributeError(path)


def resolve(kind, name):
    if kind == "candidate":
        return importlib.import_module(CANDIDATES[name]).agent
    typ, ref = OPPONENTS[name]
    if typ == "module":
        return importlib.import_module(ref).agent
    return load_path(Path(ref), f"_e18_{name}")


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
        try:
            if args.lk == "candidate":
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
    except Exception as e:
        print(PREFIX + json.dumps({"error": f"{type(e).__name__}: {e}"}))


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
    p = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    rec = None
    for line in p.stdout.splitlines():
        if line.startswith(PREFIX):
            rec = json.loads(line[len(PREFIX):])
    if rec is None:
        rec = {"error": p.stderr[-1500:] or "no result"}
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
    w = sum(x["r"] == "W" for x in rows)
    d = sum(x["r"] == "D" for x in rows)
    l = sum(x["r"] == "L" for x in rows)
    return w, d, l, mean(x["m"] for x in rows) if rows else 0.0


def telemetry_sum(rows):
    keys = ("new_shop_events", "route_candidates", "safe_switches",
            "unsafe_rejects", "same_plan", "no_supported_pair")
    out = {k: 0 for k in keys}
    for row in rows:
        t = row.get("telemetry") or {}
        for k in keys:
            out[k] += int(t.get(k, 0) or 0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed-start", type=int, default=31000)
    ap.add_argument("--lk")
    ap.add_argument("--left")
    ap.add_argument("--rk")
    ap.add_argument("--right")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--swap", action="store_true")
    args = ap.parse_args()

    if args.lk:
        child(args)
        return

    seeds = range(args.seed_start, args.seed_start + args.seeds)
    cache = load_cache()

    print("========== E11 vs E18 DIRECT ==========")
    rows, err = pair("candidate", "e18_late_shop", "candidate", "e11", seeds, cache)
    if err:
        raise SystemExit(err)
    w, d, l, m = summary(rows)
    print(f"E18 vs E11: {w}-{d}-{l} meanMargin={m:+.0f}")
    print("telemetry:", json.dumps(telemetry_sum(rows), ensure_ascii=False))

    print("\n========== STRONG HOLDOUTS ==========")
    results = {
        "e18_vs_e11": {
            "W": w, "D": d, "L": l, "mean_margin": m,
            "telemetry": telemetry_sum(rows),
        }
    }

    for opponent in OPPONENTS:
        e11_rows, err = pair("candidate", "e11", "opponent", opponent, seeds, cache)
        if err:
            print(f"[SKIP] e11 vs {opponent}: {err}")
            continue

        e18_rows, err = pair("candidate", "e18_late_shop", "opponent", opponent, seeds, cache)
        if err:
            print(f"[SKIP] e18 vs {opponent}: {err}")
            continue

        s11 = summary(e11_rows)
        s18 = summary(e18_rows)
        tel = telemetry_sum(e18_rows)

        print(
            f"{opponent:24s} "
            f"E11={s11[0]}-{s11[1]}-{s11[2]} {s11[3]:+8.0f}   "
            f"E18={s18[0]}-{s18[1]}-{s18[2]} {s18[3]:+8.0f}   "
            f"switches={tel['safe_switches']}"
        )

        results[opponent] = {
            "e11": {"W": s11[0], "D": s11[1], "L": s11[2], "mean_margin": s11[3]},
            "e18": {"W": s18[0], "D": s18[1], "L": s18[2], "mean_margin": s18[3]},
            "telemetry": tel,
        }

    Path("e18_ab_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nInterpretation:")
    print("- safe_switches=0 => this safety gate proves the tapes cannot be late-switched this way; reject mechanism.")
    print("- switches>0 but E18==E11 => switch has no useful terminal effect on sampled games.")
    print("- Any direct/holdout W-D-L regression => reject.")
    print("- Only a reproducible W-D-L improvement justifies larger confirmation.")


if __name__ == "__main__":
    main()
