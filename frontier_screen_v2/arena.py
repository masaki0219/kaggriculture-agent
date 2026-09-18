from __future__ import annotations

"""
Frontier Screen V2 — 2026-09-18

Purpose
-------
Pick the best *current public frontier base* before assigning a new immutable
experiment number. This is deliberately population/family-centered:

- same seeds
- both seats
- fresh subprocess per game
- W/D/L primary
- family-balanced score primary
- micro score / local BT secondary
- reward margin diagnostic only

It does NOT promote anything automatically and does NOT submit to Kaggle.

Expected repo layout
--------------------
<repo>/evaluation/frontier_screen_v2/arena.py
<repo>/artifacts/bundles/current/elite_runtime.py
<repo>/artifacts/bundles/current/agent_e11_prvsiyan_frontier.py
<repo>/artifacts/bundles/current/public_agents/elite/<artifact>/entrypoint.txt
<repo>/public_agents/qeinstein/...
"""

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from collections import defaultdict
from statistics import mean

from kaggle_environments import make

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BUNDLE = REPO / "artifacts" / "bundles" / "current"
PUB = REPO / "public_agents"

if str(BUNDLE) not in sys.path:
    sys.path.insert(0, str(BUNDLE))

from elite_runtime import load_agent, call_agent  # noqa: E402

CACHE = HERE / "cache.json"
RESULTS = HERE / "results.json"
PREFIX = "@@FRONTIER_V2_GAME@@"

# Candidate families are intentionally coarse.  The three newly added public
# agents share a lot of lineage, so they get ONE family weight rather than
# three votes in the family-balanced metric.
CANDIDATES = {
    "e11": {
        "kind": "path",
        "ref": BUNDLE / "agent_e11_prvsiyan_frontier.py",
        "family": "e11_prvsiyan",
        "artifact": "prvsiyan_frontier",
    },
    "shape_top10": {
        "kind": "elite",
        "ref": "shape_top10",
        "family": "shape_router",
        "artifact": "shape_top10",
    },
    "adaptive_route_v2": {
        "kind": "elite",
        "ref": "adaptive_route_v2",
        "family": "adaptive_route",
        "artifact": "adaptive_route_v2",
    },
    "aurax7_v7": {
        "kind": "elite",
        "ref": "aurax7_v7_current",
        "family": "reactive_public_frontier",
        "artifact": "aurax7_v7_current",
    },
    "ahmed_v44": {
        "kind": "elite",
        "ref": "ahmed_v44_current",
        "family": "reactive_public_frontier",
        "artifact": "ahmed_v44_current",
    },
    "tetsu_market_v23": {
        "kind": "elite",
        "ref": "tetsu_market_v23_current",
        "family": "reactive_public_frontier",
        "artifact": "tetsu_market_v23_current",
    },
}

# Extra holdouts are intentionally fewer than the old population arena's many
# correlated Kaito variants.  Candidate-v-candidate games already cover the
# current public frontier families; these holdouts broaden lineage coverage.
HOLDOUTS = {
    "kaito58": {
        "kind": "elite",
        "ref": "kaito58",
        "family": "kaito_public",
        "artifact": "kaito58",
    },
    "boatlee29": {
        "kind": "elite",
        "ref": "boatlee29",
        "family": "boatlee",
        "artifact": "boatlee29",
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


def _load_path(path: Path, unique: str):
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    # qeinstein scripts expect repo root/src on sys.path.  Ordinary wrappers
    # are happy with just their own directory.
    if path.parent.name == "scripts":
        repo_root = path.parent.parent
        extra = (repo_root, repo_root / "src", path.parent)
    else:
        repo_root = path.parent
        extra = (path.parent,)

    for p in extra:
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

    for name in (
        "agent",
        "kaggle_submission_agent",
        "submission_agent",
        "melon_maxxer",
        "policy",
    ):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    raise AttributeError(f"No supported callable in {path}")


def _load_spec(name: str, table: dict):
    cfg = table[name]
    if cfg["kind"] == "elite":
        base = load_agent(str(cfg["ref"]))

        def wrapped(obs, configuration=None):
            return call_agent(base, obs, configuration)

        return wrapped
    if cfg["kind"] == "path":
        return _load_path(Path(cfg["ref"]), f"_frontier_v2_{name}")
    raise ValueError(cfg)


def _marker(artifact: str) -> Path:
    return BUNDLE / "public_agents" / "elite" / artifact / "entrypoint.txt"


def preflight(candidate_names: list[str]):
    missing: list[str] = []

    for name in candidate_names:
        cfg = CANDIDATES[name]
        if cfg["kind"] == "path":
            if not Path(cfg["ref"]).exists():
                missing.append(f"candidate {name}: missing {cfg['ref']}")
        elif cfg["kind"] == "elite":
            marker = _marker(str(cfg["artifact"]))
            if not marker.exists():
                missing.append(f"candidate {name}: missing {marker.relative_to(REPO)}")

    for name, cfg in HOLDOUTS.items():
        if cfg["kind"] == "path":
            if not Path(cfg["ref"]).exists():
                missing.append(f"holdout {name}: missing {cfg['ref']}")
        elif cfg["kind"] == "elite":
            marker = _marker(str(cfg["artifact"]))
            if not marker.exists():
                missing.append(f"holdout {name}: missing {marker.relative_to(REPO)}")

    if missing:
        lines = "\n".join(f"  - {x}" for x in missing)
        raise SystemExit(
            "Frontier screen preflight failed; no games were run.\n"
            f"{lines}\n\n"
            "Set up the public artifacts first from artifacts/bundles/current, e.g.\n"
            "  python setup_elite_candidates.py --only aurax7_v7_current\n"
            "  python setup_elite_candidates.py --only ahmed_v44_current\n"
            "  python setup_elite_candidates.py --only tetsu_market_v23_current\n"
            "and make sure the existing elite/qeinstein artifacts are present."
        )


def _resolve(kind: str, name: str):
    if kind == "candidate":
        return _load_spec(name, CANDIDATES)
    if kind == "holdout":
        return _load_spec(name, HOLDOUTS)
    raise ValueError(kind)


def child(args):
    try:
        left = _resolve(args.left_kind, args.left)
        right = _resolve(args.right_kind, args.right)
        agents = [left, right] if not args.swap else [right, left]

        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": args.seed},
            debug=False,
        )
        env.run(agents)
        final = env.steps[-1]
        a = float(final[0].reward)
        b = float(final[1].reward)
        if args.swap:
            a, b = b, a

        print(
            PREFIX
            + json.dumps(
                {
                    "left_kind": args.left_kind,
                    "left": args.left,
                    "right_kind": args.right_kind,
                    "right": args.right,
                    "seed": args.seed,
                    "swap": bool(args.swap),
                    "a": a,
                    "b": b,
                    "r": "W" if a > b else "L" if a < b else "D",
                    "m": a - b,
                },
                ensure_ascii=False,
            )
        )
    except Exception as exc:
        print(
            PREFIX
            + json.dumps(
                {
                    "error": f"{type(exc).__name__}: {exc}",
                    "left_kind": args.left_kind,
                    "left": args.left,
                    "right_kind": args.right_kind,
                    "right": args.right,
                    "seed": args.seed,
                    "swap": bool(args.swap),
                },
                ensure_ascii=False,
            )
        )


def load_cache(fresh: bool):
    if fresh or not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache):
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def game_key(lk, left, rk, right, seed, swap):
    return "|".join(map(str, ("frontier-v2", lk, left, rk, right, seed, int(bool(swap)))))


def run_game(lk, left, rk, right, seed, swap, cache):
    key = game_key(lk, left, rk, right, seed, swap)
    if key in cache and "error" not in cache[key]:
        return cache[key]

    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--left-kind",
        lk,
        "--left",
        left,
        "--right-kind",
        rk,
        "--right",
        right,
        "--seed",
        str(seed),
    ]
    if swap:
        cmd.append("--swap")

    proc = subprocess.run(cmd, cwd=str(REPO), text=True, capture_output=True)
    rec = None
    for line in proc.stdout.splitlines():
        if line.startswith(PREFIX):
            rec = json.loads(line[len(PREFIX) :])
    if rec is None:
        rec = {
            "error": proc.stderr[-2000:] or proc.stdout[-2000:] or f"exit {proc.returncode}",
            "left_kind": lk,
            "left": left,
            "right_kind": rk,
            "right": right,
            "seed": seed,
            "swap": bool(swap),
        }

    cache[key] = rec
    save_cache(cache)
    return rec


def pair(lk, left, rk, right, seeds, cache):
    rows = []
    errors = []
    for seed in seeds:
        for swap in (False, True):
            rec = run_game(lk, left, rk, right, seed, swap, cache)
            if "error" in rec:
                errors.append(rec)
            else:
                rows.append(rec)
    return rows, errors


def summarize(rows):
    w = sum(r["r"] == "W" for r in rows)
    d = sum(r["r"] == "D" for r in rows)
    l = sum(r["r"] == "L" for r in rows)
    n = w + d + l
    return {
        "W": w,
        "D": d,
        "L": l,
        "N": n,
        "score": (w + 0.5 * d) / n if n else float("nan"),
        "mean_margin": mean(r["m"] for r in rows) if rows else float("nan"),
    }


def reverse_rows(rows):
    out = []
    for r in rows:
        rr = dict(r)
        rr["a"], rr["b"] = r["b"], r["a"]
        rr["m"] = -r["m"]
        rr["r"] = "W" if r["r"] == "L" else "L" if r["r"] == "W" else "D"
        out.append(rr)
    return out


def _sigmoid(x):
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def fit_regularized_bt(games, names, lam=0.10, iterations=1500, lr=0.05):
    names = list(dict.fromkeys(names))
    rating = {n: 0.0 for n in names}
    for t in range(iterations):
        grad = {n: -lam * rating[n] for n in names}
        for a, b, y in games:
            p = _sigmoid(rating[a] - rating[b])
            err = y - p
            grad[a] += err
            grad[b] -= err
        step = lr / math.sqrt(1.0 + t / 100.0)
        for n in names:
            rating[n] += step * grad[n]
        avg = sum(rating.values()) / len(rating)
        for n in names:
            rating[n] -= avg

    scale = 400.0 / math.log(10.0)
    return {n: rating[n] * scale for n in names}


def opponent_family(kind: str, name: str):
    table = CANDIDATES if kind == "candidate" else HOLDOUTS
    return str(table[name]["family"])


def candidate_view(candidate: str, pair_data):
    by_opponent = {}
    family_scores = defaultdict(list)
    all_rows = []

    for key, rows in pair_data.items():
        lk, left, rk, right = key
        if lk == "candidate" and left == candidate:
            perspective = rows
            opp_kind, opp = rk, right
        elif rk == "candidate" and right == candidate:
            perspective = reverse_rows(rows)
            opp_kind, opp = lk, left
        else:
            continue

        s = summarize(perspective)
        family = opponent_family(opp_kind, opp)
        by_opponent[f"{opp_kind}:{opp}"] = {**s, "family": family}
        family_scores[family].append(s["score"])
        all_rows.extend(perspective)

    family_summary = {
        family: mean(scores)
        for family, scores in sorted(family_scores.items())
        if scores
    }
    family_balanced = mean(family_summary.values()) if family_summary else float("nan")
    worst_family = min(family_summary.values()) if family_summary else float("nan")
    coverage_50 = sum(v >= 0.5 for v in family_summary.values())
    coverage_60 = sum(v >= 0.6 for v in family_summary.values())

    return {
        "all": summarize(all_rows),
        "family_balanced": family_balanced,
        "worst_family": worst_family,
        "coverage_ge_50": coverage_50,
        "coverage_ge_60": coverage_60,
        "family_scores": family_summary,
        "by_opponent": by_opponent,
    }



def candidate_scenarios(candidate: str, pair_data):
    """Return normalized per-scenario W/D/L scores for one candidate.

    Scenario key = (opponent kind, opponent name, seed, candidate seat).
    This lets two candidates be compared on the exact same opponent/seed/seat
    rather than correlating aggregate matchup rates.
    """
    out = {}
    for (lk, left, rk, right), rows in pair_data.items():
        if lk == "candidate" and left == candidate:
            opp_kind, opp = rk, right
            for r in rows:
                seat = 1 if r["swap"] else 0
                score = 1.0 if r["r"] == "W" else 0.0 if r["r"] == "L" else 0.5
                out[(opp_kind, opp, int(r["seed"]), seat)] = score
        elif rk == "candidate" and right == candidate:
            opp_kind, opp = lk, left
            for r in rows:
                # Original left candidate is seat 0 when swap=False, so the
                # right candidate is seat 1; swap=True reverses that.
                seat = 0 if r["swap"] else 1
                score = 1.0 if r["r"] == "L" else 0.0 if r["r"] == "W" else 0.5
                out[(opp_kind, opp, int(r["seed"]), seat)] = score
    return out


def _corr_binary(xs, ys):
    if not xs or len(xs) != len(ys):
        return float("nan")
    mx, my = mean(xs), mean(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def portfolio_pair_metrics(candidates, pair_data):
    scenarios = {c: candidate_scenarios(c, pair_data) for c in candidates}
    rows = []
    for i, a in enumerate(candidates):
        for b in candidates[i + 1 :]:
            common = sorted(set(scenarios[a]) & set(scenarios[b]))
            if not common:
                continue

            family_best = defaultdict(list)
            a_losses, b_losses = [], []
            either_wins = 0
            both_losses = 0
            best_scores = []

            for key in common:
                sa, sb = scenarios[a][key], scenarios[b][key]
                best = max(sa, sb)
                best_scores.append(best)
                either_wins += best == 1.0
                both_losses += sa == 0.0 and sb == 0.0
                a_losses.append(1.0 if sa == 0.0 else 0.0)
                b_losses.append(1.0 if sb == 0.0 else 0.0)
                family = opponent_family(key[0], key[1])
                family_best[family].append(best)

            family_scores = {k: mean(v) for k, v in sorted(family_best.items())}
            rows.append(
                {
                    "a": a,
                    "b": b,
                    "N_common": len(common),
                    "oracle_pair_score": mean(best_scores),
                    "either_win_rate": either_wins / len(common),
                    "both_loss_rate": both_losses / len(common),
                    "loss_correlation": _corr_binary(a_losses, b_losses),
                    "family_balanced_oracle": mean(family_scores.values()),
                    "family_scores": family_scores,
                }
            )

    rows.sort(
        key=lambda r: (
            r["family_balanced_oracle"],
            -r["both_loss_rate"],
            r["oracle_pair_score"],
        ),
        reverse=True,
    )
    return rows


def baseline_deltas(candidate_views, baseline="e11"):
    base = candidate_views.get(baseline, {}).get("by_opponent", {})
    out = {}
    for cand, view in candidate_views.items():
        if cand == baseline:
            continue
        deltas = {}
        for opp, row in view["by_opponent"].items():
            if opp in base:
                deltas[opp] = row["score"] - base[opp]["score"]
        out[cand] = deltas
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed-start", type=int, default=18000)
    ap.add_argument("--candidates", help="comma-separated subset")
    ap.add_argument("--fresh", action="store_true")

    ap.add_argument("--child", action="store_true")
    ap.add_argument("--left-kind")
    ap.add_argument("--left")
    ap.add_argument("--right-kind")
    ap.add_argument("--right")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--swap", action="store_true")
    args = ap.parse_args()

    if args.child:
        child(args)
        return

    candidates = list(CANDIDATES)
    if args.candidates:
        candidates = [x.strip() for x in args.candidates.split(",") if x.strip()]
        unknown = [x for x in candidates if x not in CANDIDATES]
        if unknown:
            raise SystemExit(f"unknown candidates: {unknown}")

    preflight(candidates)
    seeds = list(range(args.seed_start, args.seed_start + args.seeds))
    cache = load_cache(args.fresh)
    pair_data = {}
    errors = []

    # 1) Current-base round robin.  This is useful because each candidate is
    # itself a representative of one active/public strategy region.
    for i, left in enumerate(candidates):
        for right in candidates[i + 1 :]:
            print(f"\n=== {left} vs {right} ===", flush=True)
            rows, errs = pair("candidate", left, "candidate", right, seeds, cache)
            pair_data[("candidate", left, "candidate", right)] = rows
            errors.extend(errs)
            s = summarize(rows)
            print(
                f"{s['W']}-{s['D']}-{s['L']} score={s['score']:.1%} "
                f"margin={s['mean_margin']:+.0f}"
            )

    # 2) Fewer, lineage-diverse external holdouts.
    for left in candidates:
        for right in HOLDOUTS:
            print(f"\n=== {left} vs {right} ===", flush=True)
            rows, errs = pair("candidate", left, "holdout", right, seeds, cache)
            pair_data[("candidate", left, "holdout", right)] = rows
            errors.extend(errs)
            s = summarize(rows)
            print(
                f"{s['W']}-{s['D']}-{s['L']} score={s['score']:.1%} "
                f"margin={s['mean_margin']:+.0f}"
            )

    views = {c: candidate_view(c, pair_data) for c in candidates}
    portfolios = portfolio_pair_metrics(candidates, pair_data)

    # Local BT is intentionally secondary.  It is fit on the same screen only;
    # it is NOT an estimate of Kaggle's final BT without a population model.
    bt_games = []
    bt_names = set()
    for (lk, left, rk, right), rows in pair_data.items():
        a = f"{lk}:{left}"
        b = f"{rk}:{right}"
        bt_names.update((a, b))
        for r in rows:
            y = 1.0 if r["r"] == "W" else 0.0 if r["r"] == "L" else 0.5
            bt_games.append((a, b, y))
    bt = fit_regularized_bt(bt_games, sorted(bt_names)) if bt_games else {}

    ranking = []
    for c in candidates:
        v = views[c]
        ranking.append(
            {
                "candidate": c,
                "family": CANDIDATES[c]["family"],
                "family_balanced": v["family_balanced"],
                "worst_family": v["worst_family"],
                "coverage_ge_50": v["coverage_ge_50"],
                "coverage_ge_60": v["coverage_ge_60"],
                "micro_score": v["all"]["score"],
                "W": v["all"]["W"],
                "D": v["all"]["D"],
                "L": v["all"]["L"],
                "local_bt": bt.get(f"candidate:{c}", float("nan")),
                "mean_margin": v["all"]["mean_margin"],
            }
        )

    # Primary sort follows project objective better than raw margin or one H2H:
    # broad family coverage first, then downside, then micro W/D/L.
    ranking.sort(
        key=lambda r: (
            r["family_balanced"],
            r["worst_family"],
            r["micro_score"],
        ),
        reverse=True,
    )

    print("\n================ FRONTIER SCREEN V2 ================")
    for i, row in enumerate(ranking, 1):
        print(
            f"{i:2d} {row['candidate']:20s} "
            f"family={row['family_balanced']:.1%} "
            f"worst={row['worst_family']:.1%} "
            f"coverage50={row['coverage_ge_50']} "
            f"micro={row['W']}-{row['D']}-{row['L']} {row['micro_score']:.1%} "
            f"BT(local)={row['local_bt']:+.0f} "
            f"margin(diag)={row['mean_margin']:+.0f}"
        )

    print("\nPer-family scores:")
    for row in ranking:
        c = row["candidate"]
        parts = "  ".join(
            f"{fam}={score:.1%}" for fam, score in views[c]["family_scores"].items()
        )
        print(f"{c:20s} {parts}")

    print("\nTop two-agent portfolio diagnostics (oracle over same scenarios):")
    for row in portfolios[:10]:
        corr = row["loss_correlation"]
        corr_txt = "nan" if math.isnan(corr) else f"{corr:+.2f}"
        print(
            f"{row['a']} + {row['b']}: "
            f"family-best={row['family_balanced_oracle']:.1%} "
            f"both-loss={row['both_loss_rate']:.1%} "
            f"either-win={row['either_win_rate']:.1%} "
            f"loss-corr={corr_txt} N={row['N_common']}"
        )

    report = {
        "version": "frontier_screen_v2_2026-09-18",
        "seed_start": args.seed_start,
        "seeds": args.seeds,
        "candidate_families": {k: v["family"] for k, v in CANDIDATES.items()},
        "holdout_families": {k: v["family"] for k, v in HOLDOUTS.items()},
        "ranking": ranking,
        "candidate_views": views,
        "delta_vs_e11": baseline_deltas(views),
        "portfolio_pairs": portfolios,
        "errors": errors,
        "notes": [
            "family_balanced is the primary local screen metric",
            "local_bt is only a screen-local diagnostic, not final Kaggle BT",
            "mean_margin is diagnostic only",
            "portfolio_pairs use same-opponent same-seed same-seat common scenarios; they are diagnostics for complementarity",
            "do not assign/promote E21 from this screen alone if leaderboard evidence contradicts it",
        ],
    }
    RESULTS.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {RESULTS}")


if __name__ == "__main__":
    main()
