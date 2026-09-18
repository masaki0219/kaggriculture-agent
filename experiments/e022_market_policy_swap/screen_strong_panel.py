#!/usr/bin/env python3
"""
2026-09-18 — E21 vs E22 strong common-panel screen

Run from the Kaggle repository root:

    python experiments/e022_market_policy_swap/screen_strong_panel.py

Purpose
-------
Decide whether E22 deserves to remain as a second-track / hedge candidate.

Important:
The final competition objective is NOT E21-vs-E22 head-to-head.
Both candidates are evaluated against the exact same current public benchmark
panel, using the same fresh seeds and both seats.

The script will attempt to prepare missing panel artifacts through the existing
`setup_elite_candidates.py --only ...` helper when that helper knows the source.

Outputs:
    experiments/e022_market_policy_swap/strong_panel_results.md
    experiments/e022_market_policy_swap/strong_panel_results.json

No Kaggle submission is performed.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import argparse
import importlib
import json
import math
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
ELITE = BUNDLE / "public_agents" / "elite"
SETUP = BUNDLE / "setup_elite_candidates.py"

REPORT = HERE / "strong_panel_results.md"
DATA = HERE / "strong_panel_results.json"
HISTORY = ROOT / "docs" / "experiment_run_history.md"

PREFIX = "@@STRONGPANEL@@"

CANDIDATES = ("e21", "e22")

# Current / relatively recent public lines first.
# `required=False` means the screen can still run if the public artifact cannot
# be prepared, but a candidate is included only if it is available to BOTH E21
# and E22 (which is automatic because this is a common panel).
PANEL = [
    {
        "name": "aurax7_v7",
        "elite": "aurax7_v7_current",
        "setup": None,
        "tier": "frontier",
        "license": "benchmark",
        "required": True,
    },
    {
        "name": "ahmed_v44",
        "elite": "ahmed_v44_current",
        "setup": None,
        "tier": "frontier",
        "license": "benchmark",
        "required": True,
    },
    {
        "name": "kaito43",
        "elite": "kaito43_current",
        "setup": "kaito43_current",
        "tier": "frontier",
        "license": "Apache-2.0",
        "required": False,
    },
    {
        "name": "kaito27",
        "elite": "kaito27_current",
        "setup": "kaito27_current",
        "tier": "frontier",
        "license": "Apache-2.0",
        "required": False,
    },
    {
        "name": "tetsu_shape",
        "elite": "tetsu_shape",
        "setup": "tetsu_shape",
        "tier": "frontier",
        "license": "VERIFY before submission",
        "required": False,
    },
    {
        "name": "farming_v4",
        "elite": "farming_v4",
        "setup": "farming_v4",
        "tier": "frontier",
        "license": "VERIFY before submission",
        "required": False,
    },
    # Legacy but once-strong references. These are diagnostics only and do not
    # drive the primary frontier score if the frontier tier is available.
    {
        "name": "kaito58",
        "elite": "kaito58",
        "setup": "kaito58",
        "tier": "legacy",
        "license": "Apache-2.0",
        "required": False,
    },
    {
        "name": "boatlee29",
        "elite": "boatlee29",
        "setup": "boatlee29",
        "tier": "legacy",
        "license": "Apache-2.0",
        "required": False,
    },
]

CALLABLE_NAMES = (
    "agent",
    "kaggle_submission_agent",
    "submission_agent",
    "melon_maxxer",
    "policy",
    "kaggriculture_e776_agent",
)


def _put_bundle_on_path():
    s = str(BUNDLE)
    if s not in sys.path:
        sys.path.insert(0, s)


def _load_module_agent(module_name):
    _put_bundle_on_path()
    mod = importlib.import_module(module_name)
    for name in CALLABLE_NAMES:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    raise AttributeError(f"No callable agent in {module_name}")


def _load_elite(name):
    _put_bundle_on_path()
    from elite_runtime import load_agent, call_agent
    base = load_agent(name)

    def wrapped(obs, configuration=None):
        return call_agent(base, obs, configuration)

    return wrapped


def resolve(name):
    if name == "e21":
        return _load_module_agent("agent_e21_tetsu_market_v23")
    if name == "e22":
        return _load_module_agent("agent_e22_market_policy_swap")

    meta = next((x for x in PANEL if x["name"] == name), None)
    if meta is None:
        raise KeyError(name)
    return _load_elite(meta["elite"])


def elite_ready(elite_name):
    base = ELITE / elite_name
    marker = base / "entrypoint.txt"
    if not marker.exists():
        return False
    try:
        rel = marker.read_text(encoding="utf-8").strip()
        p = (base / rel).resolve()
        if not p.exists():
            return False
        compile(p.read_text(encoding="utf-8", errors="ignore"), str(p), "exec")
        return True
    except Exception:
        return False


def prepare_panel(no_prepare=False):
    available = []
    skipped = []

    for meta in PANEL:
        if elite_ready(meta["elite"]):
            available.append(meta)
            continue

        if (
            not no_prepare
            and meta["setup"]
            and SETUP.exists()
        ):
            print(f"[prepare] {meta['name']} via setup_elite_candidates.py --only {meta['setup']}", flush=True)
            p = subprocess.run(
                [sys.executable, str(SETUP), "--only", meta["setup"]],
                cwd=str(ROOT),
                text=True,
            )
            if p.returncode == 0 and elite_ready(meta["elite"]):
                available.append(meta)
                continue

        if meta["required"]:
            raise SystemExit(
                f"Required panel artifact is not ready: {meta['name']} "
                f"({meta['elite']})"
            )

        skipped.append(meta)

    frontier = [x for x in available if x["tier"] == "frontier"]
    if len(frontier) < 2:
        raise SystemExit(
            "Too few frontier-tier opponents available. "
            "Need at least aurax and Ahmed."
        )

    return available, skipped


def final_reward(env, seat):
    return float(env.steps[-1][seat].get("reward"))


def child(args):
    from kaggle_environments import make

    candidate = resolve(args.candidate)
    opponent = resolve(args.opponent)

    agents = [candidate, opponent] if args.candidate_seat == 0 else [opponent, candidate]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    cseat = args.candidate_seat
    oseat = 1 - cseat

    cr = final_reward(env, cseat)
    rr = final_reward(env, oseat)

    if cr > rr:
        outcome = "W"
    elif cr < rr:
        outcome = "L"
    else:
        outcome = "D"

    print(
        PREFIX
        + json.dumps(
            {
                "candidate": args.candidate,
                "opponent": args.opponent,
                "seed": args.seed,
                "candidate_seat": cseat,
                "candidate_reward": cr,
                "opponent_reward": rr,
                "margin": cr - rr,
                "outcome": outcome,
            },
            ensure_ascii=False,
        )
    )


def run_game(candidate, opponent, seed, seat):
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--candidate", candidate,
        "--opponent", opponent,
        "--seed", str(seed),
        "--candidate-seat", str(seat),
    ]
    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    for line in p.stdout.splitlines():
        if line.startswith(PREFIX):
            return json.loads(line[len(PREFIX):])

    return {
        "candidate": candidate,
        "opponent": opponent,
        "seed": seed,
        "candidate_seat": seat,
        "error": (p.stderr or p.stdout or "no result")[-5000:],
    }


def wdl(rows):
    c = Counter(r["outcome"] for r in rows if "outcome" in r)
    return c["W"], c["D"], c["L"]


def score(rows):
    w, d, l = wdl(rows)
    n = w + d + l
    return (w + 0.5 * d) / n if n else float("nan")


def mean_margin(rows):
    vals = [r["margin"] for r in rows if "margin" in r]
    return sum(vals) / len(vals) if vals else float("nan")


def pct(x):
    if isinstance(x, float) and math.isnan(x):
        return "n/a"
    return f"{100*x:.1f}%"


def fmt_margin(x):
    if isinstance(x, float) and math.isnan(x):
        return "n/a"
    return f"{x:+.0f}"


def parent(args):
    available, skipped = prepare_panel(no_prepare=args.no_prepare)
    frontier_names = [x["name"] for x in available if x["tier"] == "frontier"]
    legacy_names = [x["name"] for x in available if x["tier"] == "legacy"]

    seeds = list(range(args.seed_start, args.seed_start + args.seeds))

    print("=== E21 vs E22 strong common-panel screen ===")
    print("Fresh seeds:", f"{seeds[0]}..{seeds[-1]}")
    print("Frontier panel:", ", ".join(frontier_names))
    print("Legacy panel:", ", ".join(legacy_names) if legacy_names else "(none)")
    print("Skipped:", ", ".join(x["name"] for x in skipped) if skipped else "(none)")
    print()

    rows = []
    pairs = [(c, o["name"]) for c in CANDIDATES for o in available]
    total = len(pairs) * len(seeds) * 2
    done = 0

    for candidate, opponent in pairs:
        pair_rows = []
        print(f"--- {candidate} vs {opponent} ---")
        for seed in seeds:
            for seat in (0, 1):
                done += 1
                print(
                    f"[{done:>3}/{total}] {candidate} vs {opponent} "
                    f"seed={seed} candidate-seat={seat}",
                    flush=True,
                )
                r = run_game(candidate, opponent, seed, seat)
                rows.append(r)
                pair_rows.append(r)

        valid = [r for r in pair_rows if "error" not in r]
        if len(valid) == len(pair_rows):
            w, d, l = wdl(valid)
            print(
                f"  {w}-{d}-{l} score={pct(score(valid))} "
                f"margin(diag)={fmt_margin(mean_margin(valid))}"
            )
        else:
            print(f"  ERRORS: {len(pair_rows) - len(valid)}")
        print()

    errors = [r for r in rows if "error" in r]
    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    payload = {
        "generated": generated,
        "seeds": seeds,
        "available_panel": available,
        "skipped_panel": skipped,
        "rows": rows,
        "errors": errors,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        REPORT.write_text(
            "# E21 vs E22 Strong Panel\n\n"
            f"- Generated: `{generated}`\n"
            f"- Status: **ABORTED**\n"
            f"- Errors: **{len(errors)}**\n",
            encoding="utf-8",
        )
        raise SystemExit(f"{len(errors)} game errors. See {DATA.name}")

    report = [
        "# E21 vs E22 — Strong Common Panel",
        "",
        f"- Generated: `{generated}`",
        f"- Fresh seeds: `{seeds[0]}..{seeds[-1]}`",
        f"- Frontier opponents: {', '.join(f'`{x}`' for x in frontier_names)}",
        f"- Legacy opponents: {', '.join(f'`{x}`' for x in legacy_names) if legacy_names else 'none'}",
        f"- Errors: **0**",
        "",
        "Both E21 and E22 faced the exact same opponent set, seeds, and both seats.",
        "Primary comparison is the frontier-tier common panel. Legacy results are diagnostic.",
        "Reward margin is diagnostic only.",
        "",
        "## 1. Per-opponent results",
        "",
        "| Candidate | Tier | Opponent | W-D-L | Score | Margin (diag) |",
        "|---|---|---|---:|---:|---:|",
    ]

    for candidate in CANDIDATES:
        for meta in available:
            rr = [
                r for r in rows
                if r["candidate"] == candidate
                and r["opponent"] == meta["name"]
            ]
            w, d, l = wdl(rr)
            report.append(
                f"| `{candidate}` | {meta['tier']} | `{meta['name']}` | "
                f"{w}-{d}-{l} | {pct(score(rr))} | "
                f"{fmt_margin(mean_margin(rr))} |"
            )

    report += [
        "",
        "## 2. Common-panel aggregate",
        "",
        "| Candidate | Frontier W-D-L | Frontier score | Legacy W-D-L | Legacy score |",
        "|---|---:|---:|---:|---:|",
    ]

    summary = {}
    for candidate in CANDIDATES:
        fr = [
            r for r in rows
            if r["candidate"] == candidate
            and r["opponent"] in frontier_names
        ]
        lg = [
            r for r in rows
            if r["candidate"] == candidate
            and r["opponent"] in legacy_names
        ]

        fw, fd, fl = wdl(fr)
        lw, ld, ll = wdl(lg)

        summary[candidate] = {
            "frontier_score": score(fr),
            "frontier_wdl": [fw, fd, fl],
            "legacy_score": score(lg),
            "legacy_wdl": [lw, ld, ll],
        }

        report.append(
            f"| `{candidate}` | {fw}-{fd}-{fl} | {pct(score(fr))} | "
            f"{lw}-{ld}-{ll} | {pct(score(lg))} |"
        )

    # Per-opponent score delta is more interpretable than raw aggregate when
    # panel families are non-transitive.
    report += [
        "",
        "## 3. E22 minus E21 by opponent",
        "",
        "| Opponent | Tier | E21 score | E22 score | Delta |",
        "|---|---|---:|---:|---:|",
    ]

    deltas = []
    for meta in available:
        r21 = [r for r in rows if r["candidate"] == "e21" and r["opponent"] == meta["name"]]
        r22 = [r for r in rows if r["candidate"] == "e22" and r["opponent"] == meta["name"]]
        s21 = score(r21)
        s22 = score(r22)
        delta = s22 - s21
        deltas.append((meta, s21, s22, delta))
        report.append(
            f"| `{meta['name']}` | {meta['tier']} | {pct(s21)} | "
            f"{pct(s22)} | {delta:+.3f} |"
        )

    frontier_deltas = [d for d in deltas if d[0]["tier"] == "frontier"]
    better = sum(1 for _, s21, s22, _ in frontier_deltas if s22 > s21)
    worse = sum(1 for _, s21, s22, _ in frontier_deltas if s22 < s21)
    equal = len(frontier_deltas) - better - worse

    report += [
        "",
        "## 4. Decision gate",
        "",
        f"- E22 better than E21 on frontier opponents: **{better}**",
        f"- E22 worse than E21 on frontier opponents: **{worse}**",
        f"- Equal: **{equal}**",
        "",
        "- If E22 is better/equal on most frontier opponents despite losing direct H2H to E21, keep E22 as a serious second-track candidate.",
        "- If E22 is worse on most frontier opponents, reject E22; do not patch it seed-by-seed.",
        "- If results are mixed, retain E21 as the generalist and use current leaderboard/replay population evidence to decide whether E22's market regime is sufficiently prevalent to justify the second active slot.",
        "- The two final submissions are a hedge over uncertainty in population-level BT; their match-specific strengths are not combined.",
        "",
        "Final objective remains maximum leaderboard Bradley–Terry / W-D-L over the unknown active population.",
        "",
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {generated} — E21/E22 strong common-panel screen\n\n"
            f"- Fresh seeds: `{seeds[0]}..{seeds[-1]}`\n"
            f"- Frontier panel: {', '.join(frontier_names)}\n"
            f"- Legacy panel: {', '.join(legacy_names) if legacy_names else 'none'}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- No Kaggle submission performed.\n\n"
        )

    print("=== Strong-panel screen complete ===")
    print("Report:", REPORT.name)
    print("Data:", DATA.name)
    print()
    for candidate in CANDIDATES:
        print(
            candidate,
            "frontier:",
            summary[candidate]["frontier_wdl"],
            pct(summary[candidate]["frontier_score"]),
        )
    print(f"E22 per-frontier better/worse/equal: {better}/{worse}/{equal}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed-start", type=int, default=23000)
    ap.add_argument(
        "--no-prepare",
        action="store_true",
        help="Do not attempt to download missing panel artifacts.",
    )

    ap.add_argument("--child", action="store_true")
    ap.add_argument("--candidate")
    ap.add_argument("--opponent")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--candidate-seat", type=int, choices=(0, 1))

    args = ap.parse_args()

    if args.child:
        child(args)
    else:
        parent(args)


if __name__ == "__main__":
    main()
