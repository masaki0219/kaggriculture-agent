from __future__ import annotations

"""
population_arena_v1.py

Purpose
-------
Evaluate candidate Kaggriculture agents against a *population* of diverse strong
opponents instead of treating E11 head-to-head as the promotion objective.

Primary outputs:
1) per-opponent W/D/L for every candidate
2) micro pairwise score: (W + 0.5D) / games
3) family-balanced score so correlated Kaito/qeinstein variants do not dominate
4) regularized local Bradley-Terry rating from all sampled pairwise games
5) matchup delta vs E11, opponent by opponent

Important:
- E11 head-to-head is diagnostic only, never an automatic reject condition.
- mean reward margin is reported only as a secondary diagnostic.
- the local BT is still a proxy because the real leaderboard population/weights
  are unknown.
"""

import argparse
import importlib
import importlib.util
import json
import math
import os
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

from elite_runtime import load_agent, call_agent

CACHE = ROOT / "population_arena_v1_cache.json"
RESULTS = ROOT / "population_arena_v1_results.json"
PREFIX = "@@POPV1GAME@@"

CANDIDATES = {
    "e11": ("module", "agent_e11_prvsiyan_frontier"),
    "e20": ("module", "agent_e20_prvsiyan_early_sw"),
    "e21": ("module", "agent_e21_prvsiyan_early_sw"),
}

# family is used for macro/family-balanced scoring.  Variants from the same
# author/strategy lineage should not get several times the weight by accident.
CORE_OPPONENTS = {
    "boatlee29": {
        "kind": "elite", "ref": "boatlee29", "family": "boatlee",
    },
    "kaito27": {
        "kind": "elite", "ref": "kaito27_current", "family": "kaito",
    },
    "kaito43": {
        "kind": "elite", "ref": "kaito43_current", "family": "kaito",
    },
    "kaito58": {
        "kind": "elite", "ref": "kaito58", "family": "kaito",
    },
    "shape_top10": {
        "kind": "elite", "ref": "shape_top10", "family": "shape",
    },
    "adaptive_route_v2": {
        "kind": "elite", "ref": "adaptive_route_v2", "family": "adaptive_route",
    },
    "kaito48_v15": {
        "kind": "module", "ref": "agent_v15", "family": "kaito",
    },
    "qeinstein_champion": {
        "kind": "path",
        "ref": PUB / "qeinstein" / "scripts" / "champion_entry.py",
        "family": "qeinstein",
    },
    "qeinstein_candidate7": {
        "kind": "path",
        "ref": PUB / "qeinstein" / "scripts" / "candidate7_entry.py",
        "family": "qeinstein",
    },
}

# Wider style coverage. These are not assumed stronger than CORE; they exist to
# reduce the risk of optimizing only against one narrow elite cluster.
WIDE_EXTRA = {
    "seyamalam_v12": {
        "kind": "module", "ref": "agent_v12", "family": "seyamalam",
    },
    "legacy_market_v11": {
        "kind": "module", "ref": "agent_v11", "family": "legacy_market",
    },
    "legacy_livestock_v10": {
        "kind": "module", "ref": "agent_v10", "family": "legacy_livestock",
    },
}


def load_path(path: Path, unique: str):
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    # qeinstein's scripts expect its repo root/src on sys.path.
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

    for name in ("agent", "kaggle_submission_agent", "submission_agent", "melon_maxxer"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    raise AttributeError(f"No agent callable in {path}")


def load_module(name: str):
    mod = importlib.import_module(name)
    for attr in ("agent", "kaggle_submission_agent", "submission_agent", "melon_maxxer"):
        fn = getattr(mod, attr, None)
        if callable(fn):
            return fn
    raise AttributeError(f"No agent callable in module {name}")


def load_elite(name: str):
    base = load_agent(name)

    def wrapped(obs, configuration=None):
        return call_agent(base, obs, configuration)

    return wrapped


def resolve_candidate(name: str):
    kind, ref = CANDIDATES[name]
    if kind == "module":
        return load_module(ref)
    raise ValueError((kind, ref))


def opponents_for(profile: str):
    out = dict(CORE_OPPONENTS)
    if profile == "wide":
        out.update(WIDE_EXTRA)
    return out


def resolve_opponent(name: str, profile: str):
    cfg = opponents_for(profile)[name]
    kind, ref = cfg["kind"], cfg["ref"]
    if kind == "elite":
        return load_elite(str(ref))
    if kind == "module":
        return load_module(str(ref))
    if kind == "path":
        return load_path(Path(ref), f"_popv1_{name}")
    raise ValueError((kind, ref))


def child(args):
    try:
        if args.lk == "candidate":
            left = resolve_candidate(args.left)
        else:
            left = resolve_opponent(args.left, args.profile)

        if args.rk == "candidate":
            right = resolve_candidate(args.right)
        else:
            right = resolve_opponent(args.right, args.profile)

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

        print(PREFIX + json.dumps({
            "left": args.left,
            "right": args.right,
            "seed": args.seed,
            "swap": bool(args.swap),
            "a": a,
            "b": b,
            "r": "W" if a > b else "L" if a < b else "D",
            "m": a - b,
        }))
    except Exception as e:
        print(PREFIX + json.dumps({
            "error": f"{type(e).__name__}: {e}",
            "left": args.left,
            "right": args.right,
            "seed": args.seed,
            "swap": bool(args.swap),
        }))


def load_cache():
    if not CACHE.exists():
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


def run_game(lk, left, rk, right, seed, swap, profile, cache):
    key = "|".join(map(str, (
        "v1", profile, lk, left, rk, right, seed, int(bool(swap))
    )))
    if key in cache and "error" not in cache[key]:
        return cache[key]

    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--lk", lk,
        "--left", left,
        "--rk", rk,
        "--right", right,
        "--seed", str(seed),
        "--profile", profile,
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
            "error": (p.stderr[-2000:] or p.stdout[-2000:] or "no result"),
            "left": left,
            "right": right,
            "seed": seed,
            "swap": bool(swap),
        }

    cache[key] = rec
    save_cache(cache)
    return rec


def pair(lk, left, rk, right, seeds, profile, cache):
    rows = []
    errors = []
    for seed in seeds:
        for swap in (False, True):
            rec = run_game(
                lk, left, rk, right, seed, swap, profile, cache
            )
            if "error" in rec:
                errors.append(rec["error"])
            else:
                rows.append(rec)
    return rows, errors


def summarize(rows):
    w = sum(r["r"] == "W" for r in rows)
    d = sum(r["r"] == "D" for r in rows)
    l = sum(r["r"] == "L" for r in rows)
    n = w + d + l
    score = (w + 0.5 * d) / n if n else float("nan")
    margin = mean(r["m"] for r in rows) if rows else float("nan")
    return {
        "W": w, "D": d, "L": l, "N": n,
        "pairwise_score": score,
        "mean_margin": margin,
    }


def _sigmoid(x):
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def fit_regularized_bt(games, names, lam=0.10, iterations=1500, lr=0.05):
    """
    Regularized Bradley-Terry logistic fit.

    games: (left_name, right_name, y), y=1 win, 0 loss, .5 draw for left.
    L2 regularization prevents infinite ratings when sampled matchups are
    perfectly separated (common in this competition's small local panels).

    Returns centered natural-logit ratings and a 400/log(10)-scaled display
    rating, analogous to Elo units but still *local BT*, not Kaggle's rating.
    """
    names = list(dict.fromkeys(names))
    r = {name: 0.0 for name in names}

    for t in range(iterations):
        grad = {name: -lam * r[name] for name in names}
        for a, b, y in games:
            p = _sigmoid(r[a] - r[b])
            e = y - p
            grad[a] += e
            grad[b] -= e

        step = lr / math.sqrt(1.0 + t / 100.0)
        for name in names:
            r[name] += step * grad[name]

        avg = sum(r.values()) / len(r)
        for name in names:
            r[name] -= avg

    scale = 400.0 / math.log(10.0)
    return {
        name: {
            "logit": r[name],
            "display": r[name] * scale,
        }
        for name in names
    }


def score_from_summary(s):
    return s["pairwise_score"]


def family_balanced(candidate_results, opponent_cfg):
    by_family = {}
    for opp, s in candidate_results.items():
        if not s or s.get("N", 0) == 0:
            continue
        family = opponent_cfg[opp]["family"]
        by_family.setdefault(family, []).append(score_from_summary(s))

    family_scores = {
        fam: sum(vals) / len(vals)
        for fam, vals in by_family.items()
    }
    macro = (
        sum(family_scores.values()) / len(family_scores)
        if family_scores else float("nan")
    )
    return macro, family_scores


def fmt_score(x):
    if isinstance(x, float) and math.isnan(x):
        return "  n/a"
    return f"{100*x:5.1f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--seed-start", type=int, default=40000)
    ap.add_argument(
        "--profile",
        choices=("core", "wide"),
        default="core",
        help="core=strong panel, wide=core + style-diverse legacy agents",
    )
    ap.add_argument(
        "--candidates",
        default="e11,e20,e21",
        help="comma-separated candidate ids",
    )

    # child-process args
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

    requested = [x.strip() for x in args.candidates.split(",") if x.strip()]
    unknown = [x for x in requested if x not in CANDIDATES]
    if unknown:
        raise SystemExit(f"Unknown candidates: {unknown}")

    seeds = list(range(args.seed_start, args.seed_start + args.seeds))
    opponent_cfg = opponents_for(args.profile)
    cache = load_cache()

    print("========== POPULATION ARENA v1 ==========")
    print(
        f"profile={args.profile} seeds={seeds[0]}..{seeds[-1]} "
        f"({len(seeds)} seeds x both seats)"
    )
    print("candidates:", ", ".join(requested))
    print("opponents :", ", ".join(opponent_cfg))
    print()

    per_candidate = {c: {} for c in requested}
    raw_games = []
    skipped = {}

    # Main population evaluation: every candidate sees the exact same opponents,
    # seeds, and both seats.
    for opp in opponent_cfg:
        print(f"--- {opp} [{opponent_cfg[opp]['family']}] ---")
        for cand in requested:
            rows, errors = pair(
                "candidate", cand, "opponent", opp,
                seeds, args.profile, cache,
            )
            s = summarize(rows)
            per_candidate[cand][opp] = s
            for row in rows:
                y = 1.0 if row["r"] == "W" else 0.0 if row["r"] == "L" else 0.5
                raw_games.append((cand, opp, y))

            if errors:
                skipped[f"{cand}__{opp}"] = errors
                err_note = f" ERR={len(errors)}"
            else:
                err_note = ""

            print(
                f"{cand:6s} "
                f"{s['W']:2d}-{s['D']:2d}-{s['L']:2d} "
                f"score={fmt_score(s['pairwise_score'])} "
                f"margin={s['mean_margin']:+8.0f}"
                f"{err_note}"
            )
        print()

    # Candidate-candidate games improve graph connectivity / non-transitivity
    # visibility, but are diagnostic only and do not enter population score.
    candidate_h2h = {}
    if len(requested) >= 2:
        print("========== CANDIDATE H2H (diagnostic) ==========")
        for i, a in enumerate(requested):
            for b in requested[i+1:]:
                rows, errors = pair(
                    "candidate", a, "candidate", b,
                    seeds, args.profile, cache,
                )
                s = summarize(rows)
                candidate_h2h[f"{a}__{b}"] = s
                for row in rows:
                    y = 1.0 if row["r"] == "W" else 0.0 if row["r"] == "L" else 0.5
                    raw_games.append((a, b, y))
                print(
                    f"{a:6s} vs {b:6s}: "
                    f"{s['W']}-{s['D']}-{s['L']} "
                    f"score={fmt_score(s['pairwise_score'])} "
                    f"margin={s['mean_margin']:+.0f}"
                )
                if errors:
                    skipped[f"{a}__{b}"] = errors
        print()

    # Aggregate metrics.
    aggregates = {}
    print("========== POPULATION SUMMARY ==========")
    for cand in requested:
        summaries = [
            s for s in per_candidate[cand].values()
            if s.get("N", 0) > 0
        ]
        total_w = sum(s["W"] for s in summaries)
        total_d = sum(s["D"] for s in summaries)
        total_l = sum(s["L"] for s in summaries)
        total_n = total_w + total_d + total_l
        micro = (total_w + 0.5*total_d) / total_n if total_n else float("nan")
        fam_macro, fam_scores = family_balanced(
            per_candidate[cand], opponent_cfg
        )
        aggregates[cand] = {
            "W": total_w, "D": total_d, "L": total_l,
            "micro_pairwise_score": micro,
            "family_balanced_score": fam_macro,
            "family_scores": fam_scores,
        }
        print(
            f"{cand:6s} "
            f"WDL={total_w}-{total_d}-{total_l} "
            f"micro={fmt_score(micro)} "
            f"familyBalanced={fmt_score(fam_macro)}"
        )

    # Local BT across candidate-vs-population plus candidate H2H edges.
    bt_names = list(requested) + list(opponent_cfg.keys())
    bt = fit_regularized_bt(raw_games, bt_names)
    print()
    print("========== LOCAL REGULARIZED BT ==========")
    for cand in sorted(requested, key=lambda x: bt[x]["display"], reverse=True):
        print(
            f"{cand:6s} BT={bt[cand]['display']:+8.1f} "
            f"(local proxy; not Kaggle leaderboard rating)"
        )

    # Opponent-by-opponent delta to E11 exposes non-transitive gains/losses.
    deltas = {}
    if "e11" in requested:
        print()
        print("========== MATCHUP DELTA vs E11 ==========")
        for cand in requested:
            if cand == "e11":
                continue
            deltas[cand] = {}
            print(cand)
            for opp in opponent_cfg:
                base = per_candidate["e11"][opp]["pairwise_score"]
                cur = per_candidate[cand][opp]["pairwise_score"]
                if any(math.isnan(x) for x in (base, cur)):
                    delta = float("nan")
                else:
                    delta = cur - base
                deltas[cand][opp] = delta
                marker = "+" if not math.isnan(delta) and delta > 1e-12 else \
                         "-" if not math.isnan(delta) and delta < -1e-12 else "="
                print(
                    f"  {marker} {opp:24s} "
                    f"E11={fmt_score(base)} {cand}={fmt_score(cur)} "
                    f"delta={delta*100:+5.1f}pp"
                    if not math.isnan(delta)
                    else f"  ? {opp:24s} n/a"
                )

    payload = {
        "version": 1,
        "profile": args.profile,
        "seed_start": args.seed_start,
        "seeds": args.seeds,
        "candidates": requested,
        "opponents": {
            name: {
                "family": cfg["family"],
                "kind": cfg["kind"],
                "ref": str(cfg["ref"]),
            }
            for name, cfg in opponent_cfg.items()
        },
        "per_candidate": per_candidate,
        "aggregates": aggregates,
        "candidate_h2h": candidate_h2h,
        "local_bt": bt,
        "matchup_delta_vs_e11": deltas,
        "skipped_errors": skipped,
    }
    RESULTS.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"saved: {RESULTS.name}")
    print()
    print("Interpretation:")
    print("- E11 H2H is diagnostic only; losing to E11 is NOT an automatic reject.")
    print("- Primary screen: population W/D/L and family-balanced pairwise score.")
    print("- Local BT is a useful proxy, not the real leaderboard rating.")
    print("- Look for opponent-specific gains/losses; non-transitivity is expected.")
    print("- If the panel is saturated (everyone near 100%), strengthen the panel instead")
    print("  of deciding from reward margin.")


if __name__ == "__main__":
    main()
