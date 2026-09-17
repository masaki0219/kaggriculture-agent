"""
elite_arena_resilient.py

Resilient arena for the serious Kaggriculture candidate set.

Key changes:
- health-probe every candidate once before running games
- broken candidates are skipped once, not crashed 16 times
- one failed matchup aborts that matchup instead of spamming traces
- resumes from the existing elite_arena_cache.json
- defaults only to candidates still worth spending compute on

Default serious set:
  E2  exact Boatlee v29
  E6  Boatlee v29 + collision guard
  E10 current Kaito v27
  E11 current Prvsiyan Frontier
  E12 current Kaito v43
  E13 Kaito v27 + collision guard

Run:
    python elite_arena_resilient.py --seeds 8 --seed-start 1000

The old cache is reused, so already-finished games are not repeated.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
from statistics import mean
import sys
import traceback

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent
PUB = ROOT / "public_agents"

CANDIDATES = {
    "e1_kaito58": "agent_e1_kaito58",
    "e2_boatlee29": "agent_e2_boatlee29",
    "e3_shape_top10": "agent_e3_shape_top10",
    "e4_adaptive_route_v2": "agent_e4_adaptive_route_v2",
    "e5_kaito58_shift1": "agent_e5_kaito58_shift1",
    "e6_boatlee29_guard": "agent_e6_boatlee29_guard",
    "e7_tetsu_shape": "agent_e7_tetsu_shape",
    "e8_farming_v4": "agent_e8_farming_v4",
    "e9_boatlee29_tomato": "agent_e9_boatlee29_tomato",
    "e10_kaito27_current": "agent_e10_kaito27_current",
    "e11_prvsiyan_frontier": "agent_e11_prvsiyan_frontier",
    "e12_kaito43_current": "agent_e12_kaito43_current",
    "e13_kaito27_guard": "agent_e13_kaito27_guard",
}

DEFAULT_CANDIDATES = [
    "e2_boatlee29",
    "e6_boatlee29_guard",
    "e10_kaito27_current",
    "e11_prvsiyan_frontier",
    "e12_kaito43_current",
    "e13_kaito27_guard",
]

HOLDOUTS = {
    "v15_kaito48": ("module", "agent_v15"),
    "qeinstein_champion": ("path", PUB / "qeinstein" / "scripts" / "champion_entry.py"),
    "qeinstein_candidate7": ("path", PUB / "qeinstein" / "scripts" / "candidate7_entry.py"),
    "qeinstein_portfolio": ("path", PUB / "qeinstein" / "scripts" / "frontier_portfolio_entry.py"),
}

CACHE = ROOT / "elite_arena_cache.json"
PREFIX = "@@GAME@@"
PROBE_PREFIX = "@@PROBE@@"


def _load_path(path: Path, unique: str):
    import importlib.util

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

    for n in (
        "agent",
        "kaggle_submission_agent",
        "submission_agent",
        "c94_submission_agent",
        "c95_submission_agent",
        "melon_maxxer",
    ):
        fn = getattr(mod, n, None)
        if callable(fn):
            return fn

    raise AttributeError(f"No agent callable in {path}")


def resolve(kind: str, name: str):
    if kind == "candidate":
        mod = importlib.import_module(CANDIDATES[name])
        fn = getattr(mod, "agent", None)
        if not callable(fn):
            raise AttributeError(f"{CANDIDATES[name]} has no callable agent")
        return fn

    if kind == "holdout":
        typ, ref = HOLDOUTS[name]
        if typ == "module":
            mod = importlib.import_module(str(ref))
            fn = getattr(mod, "agent", None)
            if not callable(fn):
                raise AttributeError(f"{ref} has no callable agent")
            return fn
        return _load_path(Path(ref), f"_hold_{name}")

    raise ValueError(kind)


def child_probe(args):
    try:
        fn = resolve(args.probe_kind, args.probe_name)
        print(PROBE_PREFIX + json.dumps({
            "ok": True,
            "kind": args.probe_kind,
            "name": args.probe_name,
            "callable": getattr(fn, "__name__", type(fn).__name__),
        }))
    except Exception as e:
        print(PROBE_PREFIX + json.dumps({
            "ok": False,
            "kind": args.probe_kind,
            "name": args.probe_name,
            "error": f"{type(e).__name__}: {e}",
        }))


def child_game(args):
    try:
        left = resolve(args.left_kind, args.left)
        right = resolve(args.right_kind, args.right)

        agents = [left, right]
        if args.swap:
            agents = [right, left]

        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": args.seed},
            debug=False,
        )
        env.run(agents)
        final = env.steps[-1]
        r0, r1 = float(final[0].reward), float(final[1].reward)

        if args.swap:
            rl, rr = r1, r0
        else:
            rl, rr = r0, r1

        rec = {
            "left_kind": args.left_kind,
            "left": args.left,
            "right_kind": args.right_kind,
            "right": args.right,
            "seed": args.seed,
            "swap": bool(args.swap),
            "left_reward": rl,
            "right_reward": rr,
            "result": "W" if rl > rr else "L" if rl < rr else "D",
            "margin": rl - rr,
        }
        print(PREFIX + json.dumps(rec, ensure_ascii=False))

    except Exception as e:
        print(PREFIX + json.dumps({
            "error": f"{type(e).__name__}: {e}",
            "left_kind": args.left_kind,
            "left": args.left,
            "right_kind": args.right_kind,
            "right": args.right,
            "seed": args.seed,
            "swap": bool(args.swap),
        }, ensure_ascii=False))


def run_probe(kind, name):
    p = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--probe-kind", kind,
            "--probe-name", name,
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    rec = None
    for line in p.stdout.splitlines():
        if line.startswith(PROBE_PREFIX):
            rec = json.loads(line[len(PROBE_PREFIX):])

    if rec is None:
        return {"ok": False, "error": "probe returned no structured result"}
    return rec


def load_cache(fresh=False):
    if fresh or not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache):
    CACHE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def game_key(lk, l, rk, r, seed, swap):
    return f"{lk}|{l}|{rk}|{r}|{seed}|{int(swap)}"


def launch(lk, l, rk, r, seed, swap, cache):
    key = game_key(lk, l, rk, r, seed, swap)

    # Reuse only successful cached games. Previous error records are retried
    # after a patch instead of permanently poisoning the cache.
    if key in cache and "error" not in cache[key]:
        return cache[key]

    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--left-kind", lk,
        "--left", l,
        "--right-kind", rk,
        "--right", r,
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
        rec = {
            "error": f"child exit={p.returncode}; no structured result",
            "stderr": p.stderr[-1000:],
        }

    cache[key] = rec
    save_cache(cache)
    return rec


def pair_rows(lk, l, rk, r, seeds, cache):
    rows = []
    for seed in seeds:
        for swap in (False, True):
            rec = launch(lk, l, rk, r, seed, swap, cache)
            if "error" in rec:
                return rows, rec["error"]
            rows.append(rec)
    return rows, None


def summary(rows):
    w = sum(r["result"] == "W" for r in rows)
    d = sum(r["result"] == "D" for r in rows)
    l = sum(r["result"] == "L" for r in rows)
    n = len(rows)
    return {
        "W": w,
        "D": d,
        "L": l,
        "score": (w + 0.5*d) / n if n else 0.0,
        "margin": mean(r["margin"] for r in rows) if rows else 0.0,
    }


def bt_fit(pair_data):
    nodes = set()
    wins = {}
    games = {}

    for (a, b), rows in pair_data.items():
        if not rows:
            continue
        s = summary(rows)
        nodes.update((a, b))
        wins[a] = wins.get(a, 0) + s["W"] + 0.5*s["D"]
        wins[b] = wins.get(b, 0) + s["L"] + 0.5*s["D"]
        games[(a, b)] = len(rows)

    nodes = sorted(nodes)
    if not nodes:
        return {}

    strength = {n: 1.0 for n in nodes}

    for _ in range(3000):
        new = {}
        for i in nodes:
            wi = wins.get(i, 0) + 0.5
            den = 0.0

            for (a, b), n in games.items():
                if i == a:
                    j = b
                elif i == b:
                    j = a
                else:
                    continue
                den += (n + 1.0) / (strength[i] + strength[j])

            new[i] = max(1e-12, wi / max(den, 1e-12))

        gm = math.exp(sum(math.log(v) for v in new.values()) / len(new))
        new = {k: v/gm for k, v in new.items()}

        if max(
            abs(math.log(new[k]) - math.log(strength[k]))
            for k in nodes
        ) < 1e-9:
            strength = new
            break

        strength = new

    return {
        k: 1500 + 400*math.log10(v)
        for k, v in strength.items()
    }


def reverse_rows(rows):
    out = []
    for r in rows:
        rr = dict(r)
        rr["result"] = (
            "W" if r["result"] == "L"
            else "L" if r["result"] == "W"
            else "D"
        )
        rr["margin"] = -r["margin"]
        out.append(rr)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed-start", type=int, default=1000)
    ap.add_argument("--candidates")
    ap.add_argument("--fresh", action="store_true")

    # Child modes.
    ap.add_argument("--probe-kind")
    ap.add_argument("--probe-name")
    ap.add_argument("--left-kind")
    ap.add_argument("--left")
    ap.add_argument("--right-kind")
    ap.add_argument("--right")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--swap", action="store_true")
    args = ap.parse_args()

    if args.probe_kind:
        child_probe(args)
        return

    if args.left_kind:
        child_game(args)
        return

    candidates = list(DEFAULT_CANDIDATES)
    if args.candidates:
        candidates = [
            x.strip()
            for x in args.candidates.split(",")
            if x.strip()
        ]

    bad = [x for x in candidates if x not in CANDIDATES]
    if bad:
        raise SystemExit(f"Unknown candidates: {bad}")

    print("================ HEALTH PROBE ================")
    healthy = []

    for name in candidates:
        rec = run_probe("candidate", name)
        if rec.get("ok"):
            healthy.append(name)
            print(f"[OK]   {name}")
        else:
            print(f"[SKIP] {name}: {rec.get('error')}")

    holdouts = []
    for name in HOLDOUTS:
        rec = run_probe("holdout", name)
        if rec.get("ok"):
            holdouts.append(name)
            print(f"[OK]   holdout {name}")
        else:
            print(f"[SKIP] holdout {name}: {rec.get('error')}")

    if len(healthy) < 2:
        raise SystemExit(
            f"Only {len(healthy)} healthy candidate(s). "
            "Fix setup before running the arena."
        )

    print("\nHealthy candidates:")
    for x in healthy:
        print("  ", x)

    seeds = list(range(args.seed_start, args.seed_start + args.seeds))
    cache = load_cache(args.fresh)
    pair_data = {}
    failed_pairs = []

    # Candidate round robin.
    for i, a in enumerate(healthy):
        for b in healthy[i+1:]:
            print(f"\n=== {a} vs {b} ===", flush=True)
            rows, err = pair_rows(
                "candidate", a, "candidate", b, seeds, cache
            )
            if err:
                print(f"[PAIR SKIPPED] {err}")
                failed_pairs.append((a, b, err))
                continue

            s = summary(rows)
            print(
                f"{s['W']}-{s['D']}-{s['L']} "
                f"score={s['score']:.1%} margin={s['margin']:+.0f}"
            )
            pair_data[(f"C:{a}", f"C:{b}")] = rows

    # Holdouts.
    for a in healthy:
        for h in holdouts:
            print(f"\n=== {a} vs {h} ===", flush=True)
            rows, err = pair_rows(
                "candidate", a, "holdout", h, seeds, cache
            )
            if err:
                print(f"[PAIR SKIPPED] {err}")
                failed_pairs.append((a, h, err))
                continue

            s = summary(rows)
            print(
                f"{s['W']}-{s['D']}-{s['L']} "
                f"score={s['score']:.1%} margin={s['margin']:+.0f}"
            )
            pair_data[(f"C:{a}", f"H:{h}")] = rows

    bt = bt_fit(pair_data)
    stats = []

    for a in healthy:
        node = f"C:{a}"
        all_rows = []
        hold_rows = []

        for (x, y), rows in pair_data.items():
            if x == node:
                all_rows += rows
                if y.startswith("H:"):
                    hold_rows += rows
            elif y == node:
                all_rows += reverse_rows(rows)

        ss = summary(all_rows)
        hs = summary(hold_rows)
        stats.append((
            bt.get(node, -1e9),
            hs["score"],
            ss["score"],
            a,
            ss,
            hs,
        ))

    stats.sort(reverse=True)

    print("\n================ ELITE RANKING ================")
    for i, (rating, hscore, score, a, ss, hs) in enumerate(stats, 1):
        print(
            f"{i:2d} {a:26s} "
            f"BT={rating:7.1f} "
            f"all={ss['W']}-{ss['D']}-{ss['L']} {score:6.1%} "
            f"holdout={hs['W']}-{hs['D']}-{hs['L']} {hscore:6.1%}"
        )

    report = {
        "seed_start": args.seed_start,
        "seeds": args.seeds,
        "healthy": healthy,
        "failed_pairs": failed_pairs,
        "ranking": [
            {
                "candidate": a,
                "bt": rating,
                "all": ss,
                "holdout": hs,
            }
            for rating, hscore, score, a, ss, hs in stats
        ],
    }

    out = ROOT / "elite_arena_resilient_results.json"
    out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {out.name}")


if __name__ == "__main__":
    main()
