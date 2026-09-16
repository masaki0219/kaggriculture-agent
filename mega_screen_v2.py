"""
mega_screen_v2.py

Bulk Kaggriculture baseline selection with:
1) candidate-vs-candidate round robin
2) candidate-vs-external strong holdouts
3) Bradley-Terry ranking
4) automatic top-N final
5) resume cache after every matchup

Stage 1 default:
  9 candidates
  - candidate round robin: C(9,2) * 3 seeds * 2 seats = 216 games
  - vs 6 external holdouts: 9 * 6 * 3 seeds * 2 seats = 324 games
  - total = 540 games

Stage 2 default:
  top 3 candidates
  - candidate round robin: C(3,2) * 10 seeds * 2 seats = 60 games
  - vs 6 external holdouts: 3 * 6 * 10 seeds * 2 seats = 360 games
  - total = 420 games

Grand total = 960 games.

Expected layout:
  agent_v12.py
  public_agents/
    straf10/
    hbharath/
    qeinstein/
    gzmcr/
    lonespear/

Run:
    python mega_screen_v2.py

Useful:
    python mega_screen_v2.py --screen-seeds 3 --final-seeds 10 --top 3
    python mega_screen_v2.py --fresh   # ignore old cache
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from statistics import mean
from typing import Any

from kaggle_environments import make


ROOT = Path(__file__).resolve().parent
PUB = ROOT / "public_agents"

CANDIDATES = {
    "v12": {"kind": "module", "module": "agent_v12", "callable": "agent"},
    "straf10_current": {"kind": "straf10"},
    "boatlee_v16": {
        "kind": "path",
        "path": PUB / "hbharath" / "agents" / "public" / "boatlee_v16_rc5_r5a_8c4s_recovery.py",
    },
    "boatlee_v20": {
        "kind": "path",
        "path": PUB / "hbharath" / "agents" / "public" / "boatlee_v20_adaptive_r1_multi_route.py",
    },
    "kaito_v27": {
        "kind": "path",
        "path": PUB / "hbharath" / "agents" / "public" / "kaitofukami_v27_midgame_meta_reset.py",
    },
    "kaito_v48": {
        "kind": "path",
        "path": PUB / "hbharath" / "agents" / "public" / "kaitofukami_v48_fast_routes.py",
    },
    "rayk_c92": {
        "kind": "path",
        "path": PUB / "hbharath" / "agents" / "public" / "rayk_c92_findings_meta.py",
    },
    "rayk_c94": {
        "kind": "path",
        "path": PUB / "hbharath" / "agents" / "public" / "rayk_c94_findings_meta.py",
    },
    "rayk_c95": {
        "kind": "path",
        "path": PUB / "hbharath" / "agents" / "public" / "rayk_c95_findings_meta.py",
    },
}

EXTERNAL_HOLDOUTS = {
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
    "gzmcr": {"kind": "path", "path": PUB / "gzmcr" / "main.py"},
    "lonespear": {"kind": "path", "path": PUB / "lonespear" / "main.py"},
}

RESULT_PREFIX = "@@RESULT@@"
CACHE_DEFAULT = "mega_screen_v2_cache.json"
REPORT_DEFAULT = "mega_screen_v2_results.json"


def _module_root_for(path: Path) -> Path:
    path = path.resolve()
    if path.parent.name in {"scripts", "agents"}:
        return path.parent.parent
    return path.parent


def _load_import_file(path: Path, module_name: str):
    path = path.resolve()
    repo_root = _module_root_for(path)

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

    for name in (
        "agent",
        "kaggle_submission_agent",
        "c94_submission_agent",
        "c95_submission_agent",
    ):
        fn = getattr(module, name, None)
        if callable(fn):
            return fn

    raise AttributeError(f"{path} exposes no recognized agent callable")


def _load_straf10():
    repo = (PUB / "straf10").resolve()
    if not repo.exists():
        raise FileNotFoundError(repo)

    repo_s = str(repo)
    if repo_s not in sys.path:
        sys.path.insert(0, repo_s)

    old_cwd = Path.cwd()
    try:
        os.chdir(repo)
        module = importlib.import_module("agent.policy")
    finally:
        os.chdir(old_cwd)

    return module.agent


def resolve(spec: dict[str, Any], unique: str):
    kind = spec["kind"]

    if kind == "module":
        module = importlib.import_module(spec["module"])
        return getattr(module, spec.get("callable", "agent"))

    if kind == "path":
        path = Path(spec["path"]).resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        # File-path execution best matches the Kaggle runner for extracted notebooks.
        return str(path)

    if kind == "import_file":
        path = Path(spec["path"]).resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        return _load_import_file(path, unique)

    if kind == "straf10":
        return _load_straf10()

    raise ValueError(kind)


def spec_for(group: str, name: str):
    if group == "candidate":
        return CANDIDATES[name]
    if group == "external":
        return EXTERNAL_HOLDOUTS[name]
    raise ValueError(group)


def play(a0, a1, seed: int):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([a0, a1])
    final = env.steps[-1]
    return float(final[0].reward), float(final[1].reward)


def run_matchup(
    left_group: str,
    left_name: str,
    right_group: str,
    right_name: str,
    seeds: int,
) -> dict[str, Any]:
    left = resolve(spec_for(left_group, left_name), f"_left_{left_name}")
    right = resolve(spec_for(right_group, right_name), f"_right_{right_name}")

    wins = draws = losses = 0
    left_rewards, right_rewards, margins = [], [], []

    print(
        f"\n=== {left_name} vs {right_name} "
        f"({seeds} seeds x 2 seats) ==="
    )

    for seed in range(seeds):
        rl, rr = play(left, right, seed)
        left_rewards.append(rl)
        right_rewards.append(rr)
        margins.append(rl - rr)

        if rl > rr:
            wins += 1
        elif rl < rr:
            losses += 1
        else:
            draws += 1

        print(
            f"seed={seed:2d}   "
            f"L={rl:9.0f} R={rr:9.0f} diff={rl-rr:+9.0f}"
        )

        rr, rl = play(right, left, seed)
        left_rewards.append(rl)
        right_rewards.append(rr)
        margins.append(rl - rr)

        if rl > rr:
            wins += 1
        elif rl < rr:
            losses += 1
        else:
            draws += 1

        print(
            f"seed={seed:2d}R  "
            f"L={rl:9.0f} R={rr:9.0f} diff={rl-rr:+9.0f}"
        )

    games = wins + draws + losses
    score = (wins + 0.5 * draws) / games

    result = {
        "left_group": left_group,
        "left": left_name,
        "right_group": right_group,
        "right": right_name,
        "seeds": seeds,
        "W": wins,
        "D": draws,
        "L": losses,
        "score": score,
        "mean_left_reward": mean(left_rewards),
        "mean_right_reward": mean(right_rewards),
        "mean_margin": mean(margins),
    }

    print(
        f"RESULT {left_name} vs {right_name}: "
        f"{wins}-{draws}-{losses}, score={score:.1%}, "
        f"margin={result['mean_margin']:+.1f}"
    )
    print(RESULT_PREFIX + json.dumps(result, ensure_ascii=False))
    return result


def child_main(args):
    try:
        run_matchup(
            args.left_group,
            args.left,
            args.right_group,
            args.right,
            args.seeds,
        )
    except Exception as exc:
        result = {
            "left_group": args.left_group,
            "left": args.left,
            "right_group": args.right_group,
            "right": args.right,
            "seeds": args.seeds,
            "error": f"{type(exc).__name__}: {exc}",
        }
        print(
            f"[ERROR] {args.left} vs {args.right}: "
            f"{result['error']}"
        )
        print(RESULT_PREFIX + json.dumps(result, ensure_ascii=False))
        raise


def cache_key(
    stage: str,
    left_group: str,
    left: str,
    right_group: str,
    right: str,
    seeds: int,
) -> str:
    return "|".join(
        [stage, left_group, left, right_group, right, str(seeds)]
    )


def load_cache(path: Path, fresh: bool) -> dict[str, Any]:
    if fresh or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(path: Path, cache: dict[str, Any]):
    path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def launch(
    stage: str,
    left_group: str,
    left: str,
    right_group: str,
    right: str,
    seeds: int,
    cache: dict[str, Any],
    cache_path: Path,
) -> dict[str, Any]:
    key = cache_key(
        stage, left_group, left, right_group, right, seeds
    )

    if key in cache:
        print(f"\n[CACHE] {left} vs {right} ({stage})")
        return cache[key]

    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--left-group", left_group,
        "--left", left,
        "--right-group", right_group,
        "--right", right,
        "--seeds", str(seeds),
    ]

    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    if p.stdout:
        print(p.stdout, end="")
    if p.stderr:
        print(p.stderr, file=sys.stderr, end="")

    result = None
    for line in p.stdout.splitlines():
        if line.startswith(RESULT_PREFIX):
            result = json.loads(line[len(RESULT_PREFIX):])

    if result is None:
        result = {
            "left_group": left_group,
            "left": left,
            "right_group": right_group,
            "right": right,
            "seeds": seeds,
            "error": f"child exited {p.returncode} without result",
        }

    cache[key] = result
    save_cache(cache_path, cache)
    return result


def stage_pairings(candidates: list[str]):
    # Candidate round robin: every unordered pair once.
    for a, b in itertools.combinations(candidates, 2):
        yield ("candidate", a, "candidate", b)

    # Every candidate vs every external holdout.
    for c in candidates:
        for h in EXTERNAL_HOLDOUTS:
            yield ("candidate", c, "external", h)


def bradley_terry(
    results: list[dict[str, Any]],
    prior: float = 0.5,
    max_iter: int = 10000,
    tol: float = 1e-10,
) -> dict[str, float]:
    """
    MM fit of Bradley-Terry strengths.

    Draw = half-win to each side.
    A small symmetric prior per observed pair prevents infinite strengths when
    a screen contains 6-0 / 20-0 sweeps.
    """
    valid = [r for r in results if "error" not in r]

    nodes = set()
    pair_games: dict[tuple[str, str], float] = {}
    wins: dict[str, float] = {}

    def node_name(group: str, name: str) -> str:
        return f"{group}:{name}"

    for r in valid:
        a = node_name(r["left_group"], r["left"])
        b = node_name(r["right_group"], r["right"])
        nodes.add(a)
        nodes.add(b)

        # Fractional wins for draws.
        wa = float(r["W"]) + 0.5 * float(r["D"])
        wb = float(r["L"]) + 0.5 * float(r["D"])

        wins[a] = wins.get(a, 0.0) + wa
        wins[b] = wins.get(b, 0.0) + wb

        key = tuple(sorted((a, b)))
        pair_games[key] = pair_games.get(key, 0.0) + wa + wb

    nodes = sorted(nodes)
    if not nodes:
        return {}

    # Symmetric pseudo-results only on observed edges.
    adj: dict[str, dict[str, float]] = {n: {} for n in nodes}
    adjusted_wins = {n: wins.get(n, 0.0) for n in nodes}

    for (a, b), n in pair_games.items():
        adj[a][b] = adj[a].get(b, 0.0) + n + 2.0 * prior
        adj[b][a] = adj[b].get(a, 0.0) + n + 2.0 * prior
        adjusted_wins[a] += prior
        adjusted_wins[b] += prior

    strength = {n: 1.0 for n in nodes}

    for _ in range(max_iter):
        new_strength = {}
        for i in nodes:
            denom = 0.0
            for j, nij in adj[i].items():
                denom += nij / max(
                    strength[i] + strength[j],
                    1e-15,
                )

            if denom <= 0:
                new_strength[i] = strength[i]
            else:
                new_strength[i] = max(
                    adjusted_wins[i] / denom,
                    1e-12,
                )

        # Remove arbitrary scale using geometric mean.
        log_mean = sum(math.log(x) for x in new_strength.values()) / len(nodes)
        scale = math.exp(log_mean)
        for n in nodes:
            new_strength[n] /= scale

        delta = max(
            abs(math.log(new_strength[n]) - math.log(strength[n]))
            for n in nodes
        )
        strength = new_strength
        if delta < tol:
            break

    # Elo-like reporting scale: 400 * log10(strength), centered at 1500.
    return {
        n: 1500.0 + 400.0 * math.log10(max(s, 1e-12))
        for n, s in strength.items()
    }


def candidate_stats(
    candidates: list[str],
    results: list[dict[str, Any]],
    bt: dict[str, float],
):
    stats = {}

    for c in candidates:
        rows = [
            r for r in results
            if "error" not in r
            and r["left_group"] == "candidate"
            and r["left"] == c
        ]

        # Candidate can also appear on right in candidate-vs-candidate pairings.
        right_rows = [
            r for r in results
            if "error" not in r
            and r["right_group"] == "candidate"
            and r["right"] == c
        ]

        w = d = l = 0
        ext_w = ext_d = ext_l = 0
        cand_w = cand_d = cand_l = 0

        for r in rows:
            w += r["W"]; d += r["D"]; l += r["L"]
            if r["right_group"] == "external":
                ext_w += r["W"]; ext_d += r["D"]; ext_l += r["L"]
            else:
                cand_w += r["W"]; cand_d += r["D"]; cand_l += r["L"]

        for r in right_rows:
            # Reverse perspective.
            w += r["L"]; d += r["D"]; l += r["W"]
            cand_w += r["L"]; cand_d += r["D"]; cand_l += r["W"]

        games = w + d + l
        score = (w + 0.5 * d) / games if games else 0.0

        ext_games = ext_w + ext_d + ext_l
        ext_score = (
            (ext_w + 0.5 * ext_d) / ext_games
            if ext_games else 0.0
        )

        cand_games = cand_w + cand_d + cand_l
        cand_score = (
            (cand_w + 0.5 * cand_d) / cand_games
            if cand_games else 0.0
        )

        stats[c] = {
            "bt": bt.get(f"candidate:{c}", float("-inf")),
            "score": score,
            "W": w, "D": d, "L": l,
            "external_score": ext_score,
            "external_W": ext_w,
            "external_D": ext_d,
            "external_L": ext_l,
            "candidate_score": cand_score,
            "candidate_W": cand_w,
            "candidate_D": cand_d,
            "candidate_L": cand_l,
        }

    return stats


def print_ranking(
    title: str,
    candidates: list[str],
    results: list[dict[str, Any]],
):
    bt = bradley_terry(results)
    stats = candidate_stats(candidates, results, bt)

    ranked = sorted(
        candidates,
        key=lambda c: (
            stats[c]["bt"],
            stats[c]["external_score"],
            stats[c]["candidate_score"],
        ),
        reverse=True,
    )

    print(f"\n\n================ {title} ================")
    print(
        "rank candidate             BT     all W-D-L   "
        "cand W-D-L  external W-D-L"
    )

    for i, c in enumerate(ranked, 1):
        x = stats[c]
        print(
            f"{i:>4} {c:<21} "
            f"{x['bt']:>7.1f}  "
            f"{x['W']:>3}-{x['D']:<3}-{x['L']:<3}  "
            f"{x['candidate_W']:>3}-{x['candidate_D']:<3}-{x['candidate_L']:<3}  "
            f"{x['external_W']:>3}-{x['external_D']:<3}-{x['external_L']:<3}"
        )

    print("\nExternal holdout BT:")
    external_rows = []
    for h in EXTERNAL_HOLDOUTS:
        external_rows.append(
            (h, bt.get(f"external:{h}", float("-inf")))
        )
    for name, rating in sorted(
        external_rows,
        key=lambda x: x[1],
        reverse=True,
    ):
        print(f"  {name:<24} {rating:7.1f}")

    return ranked, stats, bt


def run_stage(
    stage: str,
    candidates: list[str],
    seeds: int,
    cache: dict[str, Any],
    cache_path: Path,
):
    results = []
    pairings = list(stage_pairings(candidates))
    total = len(pairings)

    for idx, (lg, ln, rg, rn) in enumerate(pairings, 1):
        print(
            f"\n\n######## {stage} {idx}/{total}: "
            f"{ln} vs {rn} ########"
        )
        result = launch(
            stage,
            lg, ln,
            rg, rn,
            seeds,
            cache,
            cache_path,
        )
        results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--screen-seeds", type=int, default=3)
    parser.add_argument("--final-seeds", type=int, default=10)
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--cache", default=CACHE_DEFAULT)
    parser.add_argument("--output", default=REPORT_DEFAULT)
    parser.add_argument("--fresh", action="store_true")

    parser.add_argument("--child", action="store_true")
    parser.add_argument("--left-group", choices=("candidate", "external"))
    parser.add_argument("--left")
    parser.add_argument("--right-group", choices=("candidate", "external"))
    parser.add_argument("--right")
    parser.add_argument("--seeds", type=int)

    args = parser.parse_args()

    if args.child:
        child_main(args)
        return

    cache_path = ROOT / args.cache
    cache = load_cache(cache_path, args.fresh)

    all_candidates = list(CANDIDATES)

    print("Candidates:")
    for c in all_candidates:
        print(" ", c)

    print("\nExternal holdouts:")
    for h in EXTERNAL_HOLDOUTS:
        print(" ", h)

    stage1_pairs = (
        len(all_candidates) * (len(all_candidates) - 1) // 2
        + len(all_candidates) * len(EXTERNAL_HOLDOUTS)
    )
    stage1_games = stage1_pairs * args.screen_seeds * 2

    print(
        f"\nStage 1: {stage1_pairs} matchups, "
        f"{stage1_games} games"
    )

    stage1_results = run_stage(
        "stage1",
        all_candidates,
        args.screen_seeds,
        cache,
        cache_path,
    )

    stage1_ranked, stage1_stats, stage1_bt = print_ranking(
        "STAGE 1 RANKING",
        all_candidates,
        stage1_results,
    )

    finalists = stage1_ranked[: max(1, args.top)]

    final_pairs = (
        len(finalists) * (len(finalists) - 1) // 2
        + len(finalists) * len(EXTERNAL_HOLDOUTS)
    )
    final_games = final_pairs * args.final_seeds * 2

    print("\nFinalists:", ", ".join(finalists))
    print(
        f"Stage 2: {final_pairs} matchups, "
        f"{final_games} games"
    )

    stage2_results = run_stage(
        "stage2",
        finalists,
        args.final_seeds,
        cache,
        cache_path,
    )

    stage2_ranked, stage2_stats, stage2_bt = print_ranking(
        "FINAL RANKING",
        finalists,
        stage2_results,
    )

    report = {
        "screen_seeds": args.screen_seeds,
        "final_seeds": args.final_seeds,
        "top_n": args.top,
        "candidates": all_candidates,
        "external_holdouts": list(EXTERNAL_HOLDOUTS),
        "stage1": {
            "results": stage1_results,
            "ranking": stage1_ranked,
            "stats": stage1_stats,
            "bt": stage1_bt,
        },
        "stage2": {
            "finalists": finalists,
            "results": stage2_results,
            "ranking": stage2_ranked,
            "stats": stage2_stats,
            "bt": stage2_bt,
        },
    }

    out = ROOT / args.output
    out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nWrote {out.name}")
    print(f"Cache: {cache_path.name}")

    if stage2_ranked:
        print(f"\nTOP CANDIDATE: {stage2_ranked[0]}")
        print(
            "Promotion decision should inspect both candidate-round-robin "
            "and external-holdout records, not mean reward."
        )


if __name__ == "__main__":
    main()
