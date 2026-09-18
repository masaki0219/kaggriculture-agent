#!/usr/bin/env python3
"""
2026-09-18 — Analyze current-frontier failure regimes

Run from the Kaggle repository root:

    python analysis/frontier_failure_regimes/analyze.py

Input:
    evaluation/frontier_screen_v2/current_results.json

Outputs:
    analysis/frontier_failure_regimes/report.md
    analysis/frontier_failure_regimes/results.json

Purpose
-------
Use the already-completed current-frontier round robin to identify the seeds
where E21 is weak, then replay only those 16 RR seeds with E21 vs aurax V7
(both seat orientations) and measure:

- first 2 / 3 / 4 / all town shops
- realized crops / animals / max hands
- market order counts and sell quantities by product
- reward / W-L outcome

This is intended to reveal environment/shop regimes where E21's frontier
market policy loses to aurax, before creating E22.

This script does NOT modify any agent and does NOT submit anything.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import argparse
import importlib
import json
import math
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
SCREEN = ROOT / "evaluation" / "frontier_screen_v2" / "current_results.json"
REPORT = HERE / "report.md"
DATA = HERE / "results.json"
HISTORY = ROOT / "docs" / "experiment_run_history.md"

PREFIX = "@@FAILREGIME@@"

CALLABLE_NAMES = (
    "agent",
    "kaggle_submission_agent",
    "submission_agent",
    "melon_maxxer",
    "policy",
    "kaggriculture_e776_agent",
)

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("COW", "SHEEP", "GOOSE")
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "MILK", "WOOL", "EGG")


def _bundle_path():
    p = str(BUNDLE)
    if p not in sys.path:
        sys.path.insert(0, p)


def _load_module_agent(module_name):
    _bundle_path()
    mod = importlib.import_module(module_name)
    for name in CALLABLE_NAMES:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    raise AttributeError(f"{module_name} exposes none of {CALLABLE_NAMES}")


def _load_elite(name):
    _bundle_path()
    from elite_runtime import load_agent, call_agent
    base = load_agent(name)

    def wrapped(obs, configuration=None):
        return call_agent(base, obs, configuration)

    return wrapped


def resolve(name):
    if name == "e21":
        return _load_module_agent("agent_e21_tetsu_market_v23")
    if name == "aurax7_v7":
        return _load_elite("aurax7_v7_current")
    raise KeyError(name)


def _obs(state):
    if not isinstance(state, dict):
        return None
    obs = state.get("observation")
    if isinstance(obs, str):
        try:
            obs = json.loads(obs)
        except Exception:
            return None
    return obs if isinstance(obs, dict) else None


def _shops(obs):
    town = obs.get("town", {}) if isinstance(obs, dict) else {}
    x = town.get("unlocked_shops", []) or []
    return tuple(str(v) for v in x)


def _farm(obs, seat):
    farms = obs.get("farms", []) if isinstance(obs, dict) else []
    if isinstance(farms, list) and 0 <= seat < len(farms):
        return farms[seat]
    return None


def _track_agent(env, seat):
    first = {2: None, 3: None, 4: None}
    max_shops = ()

    plants = Counter()
    animals = Counter()
    seen_plants = set()
    seen_animals = set()
    max_hands = 0

    market_ops = Counter()
    sells = Counter()
    sell_qty = Counter()
    buys = Counter()

    for step_states in env.steps:
        if not isinstance(step_states, list) or seat >= len(step_states):
            continue
        state = step_states[seat]

        # Requested actions.
        action = state.get("action") if isinstance(state, dict) else None
        if isinstance(action, dict):
            for order in action.get("market", []) or []:
                if not isinstance(order, (list, tuple)) or not order:
                    continue
                op = str(order[0])
                item = str(order[1]) if len(order) > 1 and order[1] is not None else ""
                try:
                    qty = int(order[2]) if len(order) > 2 else 1
                except Exception:
                    qty = 1

                market_ops[op] += 1
                if op == "SELL":
                    sells[item] += 1
                    sell_qty[item] += max(0, qty)
                elif op.startswith("BUY"):
                    buys[item or op] += max(0, qty)

        obs = _obs(state)
        if not obs:
            continue

        shops = _shops(obs)
        if len(shops) > len(max_shops):
            max_shops = shops
        for k in (2, 3, 4):
            if first[k] is None and len(shops) >= k:
                first[k] = shops[:k]

        farm = _farm(obs, seat)
        if not isinstance(farm, dict):
            continue

        max_hands = max(max_hands, len(farm.get("hands", []) or []))

        tiles = farm.get("tiles", []) or []
        for y, row in enumerate(tiles):
            if not isinstance(row, list):
                continue
            for x, tile in enumerate(row):
                if not isinstance(tile, dict):
                    continue

                if tile.get("kind") == "PLANT" and tile.get("crop") in CROPS:
                    crop = str(tile["crop"])
                    sig = (x, y, crop, tile.get("planted_day"))
                    if sig not in seen_plants:
                        seen_plants.add(sig)
                        plants[crop] += 1

                animal = tile.get("animal")
                if animal in ANIMALS:
                    animal = str(animal)
                    sig = (x, y, animal, tile.get("placed_day"))
                    if sig not in seen_animals:
                        seen_animals.add(sig)
                        animals[animal] += 1

    final = env.steps[-1][seat]
    reward = float(final.get("reward"))

    return {
        "shops2": list(first[2]) if first[2] else None,
        "shops3": list(first[3]) if first[3] else None,
        "shops4": list(first[4]) if first[4] else None,
        "all_shops": list(max_shops),
        "plants": {p: int(plants.get(p, 0)) for p in CROPS},
        "animals": {a: int(animals.get(a, 0)) for a in ANIMALS},
        "max_hands": int(max_hands),
        "market_ops": dict(market_ops),
        "sell_orders": {p: int(sells.get(p, 0)) for p in PRODUCTS},
        "sell_qty": {p: int(sell_qty.get(p, 0)) for p in PRODUCTS},
        "buy_qty": dict(buys),
        "reward": reward,
        "status": final.get("status"),
    }


def child(args):
    from kaggle_environments import make

    e21 = resolve("e21")
    aurax = resolve("aurax7_v7")

    # left_seat is E21 seat
    agents = [e21, aurax] if args.left_seat == 0 else [aurax, e21]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    e21_seat = args.left_seat
    aurax_seat = 1 - e21_seat
    e21_rec = _track_agent(env, e21_seat)
    aurax_rec = _track_agent(env, aurax_seat)

    if e21_rec["reward"] > aurax_rec["reward"]:
        outcome = "W"
    elif e21_rec["reward"] < aurax_rec["reward"]:
        outcome = "L"
    else:
        outcome = "D"

    result = {
        "seed": args.seed,
        "e21_seat": e21_seat,
        "outcome": outcome,
        "margin": e21_rec["reward"] - aurax_rec["reward"],
        "e21": e21_rec,
        "aurax7_v7": aurax_rec,
    }
    print(PREFIX + json.dumps(result, ensure_ascii=False))


def run_one(seed, seat):
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--seed", str(seed),
        "--left-seat", str(seat),
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
        "seed": seed,
        "e21_seat": seat,
        "error": (p.stderr or p.stdout or "no result")[-5000:],
    }


def seed_status_from_screen(screen, left, right):
    rows = [
        r for r in screen["round_robin"]
        if r.get("left") == left and r.get("right") == right
    ]
    by = defaultdict(list)
    for r in rows:
        by[int(r["seed"])].append(r["outcome"])

    out = {}
    for seed, vals in by.items():
        if vals.count("W") == 2:
            out[seed] = "WW"
        elif vals.count("L") == 2:
            out[seed] = "LL"
        elif "W" in vals and "L" in vals:
            out[seed] = "WL"
        else:
            out[seed] = "/".join(vals)
    return out


def mean(vals):
    return sum(vals) / len(vals) if vals else float("nan")


def fmt(x, digits=1):
    if isinstance(x, float) and math.isnan(x):
        return "n/a"
    return f"{x:.{digits}f}"


def summarize_group(rows):
    if not rows:
        return {}
    out = {}
    for agent_name in ("e21", "aurax7_v7"):
        vals = rows
        prefix = {}
        for crop in CROPS:
            prefix[f"plant_{crop}"] = mean([r[agent_name]["plants"][crop] for r in vals])
        for animal in ANIMALS:
            prefix[f"animal_{animal}"] = mean([r[agent_name]["animals"][animal] for r in vals])
        prefix["max_hands"] = mean([r[agent_name]["max_hands"] for r in vals])
        prefix["sell_orders"] = mean([
            sum(r[agent_name]["sell_orders"].values()) for r in vals
        ])
        prefix["sell_qty"] = mean([
            sum(r[agent_name]["sell_qty"].values()) for r in vals
        ])
        out[agent_name] = prefix
    return out


def parent():
    if not SCREEN.exists():
        raise SystemExit(f"Missing: {SCREEN.name}")

    screen = json.loads(SCREEN.read_text(encoding="utf-8"))
    e21_ahmed = seed_status_from_screen(screen, "e21", "ahmed_v44")
    e21_aurax = seed_status_from_screen(screen, "e21", "aurax7_v7")

    seeds = sorted(e21_aurax)
    if not seeds:
        raise SystemExit("No E21 vs aurax RR rows found in current frontier screen.")

    rows = []
    total = len(seeds) * 2
    print("=== Frontier failure-regime replay ===")
    print("Seeds:", f"{seeds[0]}..{seeds[-1]}")
    print("Games:", total)
    print()

    done = 0
    for seed in seeds:
        for seat in (0, 1):
            done += 1
            print(f"[{done:>2}/{total}] seed={seed} E21-seat={seat}", flush=True)
            rows.append(run_one(seed, seat))

    errors = [r for r in rows if "error" in r]
    valid = [r for r in rows if "error" not in r]

    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    payload = {
        "generated": generated,
        "source_screen": SCREEN.name,
        "screen_seed_status": {
            "e21_vs_ahmed_v44": {str(k): v for k, v in e21_ahmed.items()},
            "e21_vs_aurax7_v7": {str(k): v for k, v in e21_aurax.items()},
        },
        "replays": rows,
        "errors": errors,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        REPORT.write_text(
            "# Frontier Failure Regimes\n\n"
            f"- Generated: `{generated}`\n"
            f"- Status: **ABORTED**\n"
            f"- Errors: **{len(errors)}**\n",
            encoding="utf-8",
        )
        raise SystemExit(f"{len(errors)} replay errors. See {DATA.name}")

    # Categorize seeds using original screen.
    seed_class = {}
    for seed in seeds:
        a = e21_aurax.get(seed)
        h = e21_ahmed.get(seed)
        if a == "LL":
            cls = "aurax_sweep_loss"
        elif a == "WL":
            cls = "seat_sensitive"
        else:
            cls = "aurax_sweep_win"
        seed_class[seed] = cls

    report = [
        "# Frontier Failure Regimes",
        "",
        f"- Generated: `{generated}`",
        f"- Source: `{SCREEN.name}`",
        f"- Seeds: `{seeds[0]}..{seeds[-1]}`",
        f"- Fresh replay games: **{len(valid)}**",
        f"- Errors: **0**",
        "",
        "Purpose: explain *where* E21 loses to aurax V7 before defining E22.",
        "",
        "## 1. Failure-seed overlap from the completed frontier screen",
        "",
    ]

    ahmed_trouble = [s for s, v in e21_ahmed.items() if v != "WW"]
    aurax_trouble = [s for s, v in e21_aurax.items() if v != "WW"]
    overlap = sorted(set(ahmed_trouble) & set(aurax_trouble))

    report += [
        f"- E21 trouble seeds vs Ahmed (`LL` or `WL`): "
        + ", ".join(f"`{x}`" for x in ahmed_trouble),
        f"- E21 trouble seeds vs aurax (`LL` or `WL`): "
        + ", ".join(f"`{x}`" for x in aurax_trouble),
        f"- Overlap: " + ", ".join(f"`{x}`" for x in overlap),
        "",
        "The overlap is evidence for environment/regime sensitivity, not proof of causality.",
        "",
        "## 2. Seed-level shop regime and E21 result",
        "",
        "| Seed | vs Ahmed | vs aurax | first 4 shops | E21 C/S/G | E21 C/T/S/M/W plants | aurax C/S/G | aurax C/T/S/M/W plants |",
        "|---:|---|---|---|---|---|---|---|",
    ]

    # Use seat0 fresh replay as shop/production representative; shop draw is shared.
    by_seed = defaultdict(list)
    for r in valid:
        by_seed[r["seed"]].append(r)

    for seed in seeds:
        rs = sorted(by_seed[seed], key=lambda r: r["e21_seat"])
        r = rs[0]
        shops4 = r["e21"]["shops4"] or r["e21"]["all_shops"][:4]

        e = r["e21"]
        a = r["aurax7_v7"]

        e_anim = f"{e['animals']['COW']}/{e['animals']['SHEEP']}/{e['animals']['GOOSE']}"
        a_anim = f"{a['animals']['COW']}/{a['animals']['SHEEP']}/{a['animals']['GOOSE']}"

        order = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "WHEAT")
        e_plant = "/".join(str(e["plants"][p]) for p in order)
        a_plant = "/".join(str(a["plants"][p]) for p in order)

        report.append(
            f"| {seed} | {e21_ahmed.get(seed,'?')} | {e21_aurax.get(seed,'?')} | "
            f"`{' → '.join(shops4 or [])}` | {e_anim} | {e_plant} | "
            f"{a_anim} | {a_plant} |"
        )

    report += [
        "",
        "## 3. E21 vs aurax behavior by outcome regime",
        "",
        "Averages use both seat orientations.",
        "",
        "| Regime | Agent | N | Cow | Sheep | Goose | Carrot | Tomato | Strawberry | Melon | Wheat | Hands | Sell orders | Sell qty |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for cls in ("aurax_sweep_loss", "seat_sensitive", "aurax_sweep_win"):
        group = [r for r in valid if seed_class[r["seed"]] == cls]
        sm = summarize_group(group)
        for agent in ("e21", "aurax7_v7"):
            x = sm.get(agent, {})
            report.append(
                f"| {cls} | `{agent}` | {len(group)} | "
                f"{fmt(x.get('animal_COW', float('nan')))} | "
                f"{fmt(x.get('animal_SHEEP', float('nan')))} | "
                f"{fmt(x.get('animal_GOOSE', float('nan')))} | "
                f"{fmt(x.get('plant_CARROT', float('nan')))} | "
                f"{fmt(x.get('plant_TOMATO', float('nan')))} | "
                f"{fmt(x.get('plant_STRAWBERRY', float('nan')))} | "
                f"{fmt(x.get('plant_MELON', float('nan')))} | "
                f"{fmt(x.get('plant_WHEAT', float('nan')))} | "
                f"{fmt(x.get('max_hands', float('nan')))} | "
                f"{fmt(x.get('sell_orders', float('nan')))} | "
                f"{fmt(x.get('sell_qty', float('nan')))} |"
            )

    report += [
        "",
        "## 4. Market differences on E21 sweep-loss seeds",
        "",
        "| Seed | E21 seat | Outcome | Margin | E21 sell orders | aurax sell orders | E21 sell qty | aurax sell qty |",
        "|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for r in valid:
        if seed_class[r["seed"]] != "aurax_sweep_loss":
            continue
        e_orders = sum(r["e21"]["sell_orders"].values())
        a_orders = sum(r["aurax7_v7"]["sell_orders"].values())
        e_qty = sum(r["e21"]["sell_qty"].values())
        a_qty = sum(r["aurax7_v7"]["sell_qty"].values())
        report.append(
            f"| {r['seed']} | {r['e21_seat']} | {r['outcome']} | "
            f"{r['margin']:+.0f} | {e_orders} | {a_orders} | {e_qty} | {a_qty} |"
        )

    report += [
        "",
        "## 5. E22 decision gate",
        "",
        "- If E21 and aurax realize nearly identical production on E21-loss seeds but market-order behavior differs, E22 should target a **market regime** rather than crop routing.",
        "- If aurax changes production materially on the same loss seeds, E22 can target that complete production-routing mechanism.",
        "- If the shared Ahmed/aurax trouble seeds cluster around a small set of early-shop patterns, use those patterns as a regime trigger only if a larger seed sample confirms it.",
        "- Do not optimize only against aurax. Any E22 must later be re-evaluated against a refreshed population panel / replay census.",
        "",
        "Final objective remains population-level W/D/L / Bradley–Terry.",
        "",
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {generated} — Analyze frontier failure regimes\n\n"
            f"- Source screen: `{SCREEN.name}`\n"
            f"- Fresh replays: {len(valid)}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- Read-only; no agent modification or Kaggle submission.\n\n"
        )

    print()
    print("=== Failure-regime analysis complete ===")
    print("Ahmed trouble seeds:", ahmed_trouble)
    print("Aurax trouble seeds:", aurax_trouble)
    print("Overlap:", overlap)
    print("Report:", REPORT.name)
    print("Data:", DATA.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--left-seat", type=int, choices=(0, 1))
    args = ap.parse_args()

    if args.child:
        child(args)
    else:
        parent()


if __name__ == "__main__":
    main()
