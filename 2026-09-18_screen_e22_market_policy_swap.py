#!/usr/bin/env python3
# 2026-09-18 — Fresh direct screen for E22 market-policy swap

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import argparse
import importlib
import json
import math
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
REPORT = ROOT / "2026-09-18_E22_MARKET_POLICY_SCREEN.md"
DATA = ROOT / "2026-09-18_E22_MARKET_POLICY_SCREEN.json"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"
PREFIX = "@@E22SCREEN@@"

CALLABLE_NAMES = (
    "agent",
    "kaggle_submission_agent",
    "submission_agent",
    "melon_maxxer",
    "policy",
    "kaggriculture_e776_agent",
)


def _bundle_path():
    p = str(BUNDLE)
    if p not in sys.path:
        sys.path.insert(0, p)


def _load_module(module_name):
    _bundle_path()
    mod = importlib.import_module(module_name)
    for name in CALLABLE_NAMES:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    raise AttributeError(f"No agent callable in {module_name}")


def _load_elite(name):
    _bundle_path()
    from elite_runtime import load_agent, call_agent
    base = load_agent(name)

    def wrapped(obs, configuration=None):
        return call_agent(base, obs, configuration)

    return wrapped


def resolve(name):
    if name == "e22":
        return _load_module("agent_e22_market_policy_swap")
    if name == "e21":
        return _load_module("agent_e21_tetsu_market_v23")
    if name == "aurax7_v7":
        return _load_elite("aurax7_v7_current")
    if name == "ahmed_v44":
        return _load_elite("ahmed_v44_current")
    raise KeyError(name)


def child(args):
    from kaggle_environments import make

    left = resolve(args.left)
    right = resolve(args.right)
    agents = [left, right] if args.left_seat == 0 else [right, left]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    ls = args.left_seat
    rs = 1 - ls
    lr = float(env.steps[-1][ls]["reward"])
    rr = float(env.steps[-1][rs]["reward"])

    outcome = "W" if lr > rr else "L" if lr < rr else "D"
    print(PREFIX + json.dumps({
        "left": args.left,
        "right": args.right,
        "seed": args.seed,
        "left_seat": args.left_seat,
        "left_reward": lr,
        "right_reward": rr,
        "margin": lr - rr,
        "outcome": outcome,
    }, ensure_ascii=False))


def run_game(left, right, seed, seat):
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--left", left,
        "--right", right,
        "--seed", str(seed),
        "--left-seat", str(seat),
    ]
    p = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    for line in p.stdout.splitlines():
        if line.startswith(PREFIX):
            return json.loads(line[len(PREFIX):])
    return {
        "left": left,
        "right": right,
        "seed": seed,
        "left_seat": seat,
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
    return "nan%" if isinstance(x, float) and math.isnan(x) else f"{100*x:.1f}%"


def parent(args):
    e22_path = BUNDLE / "agent_e22_market_policy_swap.py"
    if not e22_path.exists():
        raise SystemExit(
            "E22 agent not found. Run 2026-09-18_build_e22_market_policy_swap.py first."
        )

    opponents = ("e21", "aurax7_v7", "ahmed_v44")
    seeds = list(range(args.seed_start, args.seed_start + args.seeds))

    rows = []
    total = len(opponents) * len(seeds) * 2
    done = 0

    print("=== E22 fresh direct screen ===")
    print("Seeds:", f"{seeds[0]}..{seeds[-1]}")
    print("Opponents:", ", ".join(opponents))
    print("Games:", total)

    for opponent in opponents:
        pair = []
        print(f"\n--- e22 vs {opponent} ---")
        for seed in seeds:
            for seat in (0, 1):
                done += 1
                print(
                    f"[{done:>3}/{total}] e22 vs {opponent} seed={seed} e22-seat={seat}",
                    flush=True,
                )
                r = run_game("e22", opponent, seed, seat)
                rows.append(r)
                pair.append(r)

        valid = [r for r in pair if "error" not in r]
        if len(valid) == len(pair):
            w, d, l = wdl(valid)
            print(
                f"{w}-{d}-{l} score={pct(score(valid))} "
                f"margin(diag)={mean_margin(valid):+.0f}"
            )
        else:
            print("ERRORS:", len(pair) - len(valid))

    errors = [r for r in rows if "error" in r]
    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    payload = {
        "generated": generated,
        "seeds": seeds,
        "opponents": list(opponents),
        "rows": rows,
        "errors": errors,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        REPORT.write_text(
            "# E22 Market Policy Screen\n\n"
            f"- Generated: `{generated}`\n"
            f"- Status: **ABORTED**\n"
            f"- Errors: **{len(errors)}**\n",
            encoding="utf-8",
        )
        raise SystemExit(f"ABORTED: {len(errors)} errors. See {DATA.name}")

    report = [
        "# E22 Market Policy Screen",
        "",
        f"- Generated: `{generated}`",
        f"- Fresh seeds: `{seeds[0]}..{seeds[-1]}`",
        f"- Games: **{len(rows)}**",
        "- Errors: **0**",
        "",
        "E22 changes only the final ADV market-policy block relative to E21.",
        "W/D/L is primary; reward margin is diagnostic only.",
        "",
        "| Matchup | W-D-L from E22 perspective | Score | Margin (diag) |",
        "|---|---:|---:|---:|",
    ]

    for opponent in opponents:
        pair = [r for r in rows if r["right"] == opponent]
        w, d, l = wdl(pair)
        report.append(
            f"| `e22` vs `{opponent}` | {w}-{d}-{l} | "
            f"{pct(score(pair))} | {mean_margin(pair):+.0f} |"
        )

    report += [
        "",
        "## Decision rule",
        "",
        "- If E22 improves against aurax but loses materially to E21 on fresh seeds, the aurax market block is a hedge mechanism, not a new generalist baseline.",
        "- If E22 is competitive with E21 and improves against aurax/Ahmed, promote it to broader population testing.",
        "- If E22 loses broadly, reject E22 and keep E21; do not patch this experiment seed-by-seed.",
        "- Do not use reward margin as the promotion criterion.",
        "",
        "Final objective remains population-level W/D/L / Bradley–Terry.",
        "",
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {generated} — E22 fresh market-policy screen\n\n"
            f"- Seeds: `{seeds[0]}..{seeds[-1]}`\n"
            f"- Opponents: {', '.join(opponents)}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- No Kaggle submission performed.\n\n"
        )

    print("\n=== E22 screen complete ===")
    print("Report:", REPORT.name)
    print("Data:", DATA.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--seed-start", type=int, default=22000)

    ap.add_argument("--child", action="store_true")
    ap.add_argument("--left")
    ap.add_argument("--right")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--left-seat", type=int, choices=(0, 1))

    args = ap.parse_args()
    if args.child:
        child(args)
    else:
        parent(args)


if __name__ == "__main__":
    main()
