#!/usr/bin/env python3
"""
2026-09-18 — Probe E21 realized shop response

Run from the Kaggle repository root:

    python experiments/e021_tetsu_market_v23/probe_shop_response.py

Default:
    12 seeds x 2 opponents x both seats = 48 fresh games

Outputs:
    experiments/e021_tetsu_market_v23/realized_shop_response.md
    experiments/e021_tetsu_market_v23/realized_shop_response.json

Purpose
-------
Measure what E21 ACTUALLY produces in completed games, instead of counting
commands in its static route tapes.

For each run this tracks:
- first 2 / 3 / 4 unlocked shops
- unique successful plant instances by crop
- unique successfully placed animals by type
- maximum farm-hand count
- final reward

It then measures shop-demand -> realized-production correlations.

The script does not modify any agent and does not submit anything.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import argparse
import importlib
import json
import math
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
REPORT = HERE / "realized_shop_response.md"
DATA = HERE / "realized_shop_response.json"
HISTORY = ROOT / "docs" / "experiment_run_history.md"

PREFIX = "@@E21REALIZED@@"

SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("COW", "SHEEP", "GOOSE")
TRACK_PRODUCTS = ("MILK", "WOOL", "CARROT", "TOMATO", "STRAWBERRY", "WHEAT")


def _put_bundle_on_path():
    p = str(BUNDLE)
    if p not in sys.path:
        sys.path.insert(0, p)


def _load_module_agent(module_name):
    _put_bundle_on_path()
    mod = importlib.import_module(module_name)
    for name in (
        "agent",
        "kaggle_submission_agent",
        "submission_agent",
        "melon_maxxer",
        "policy",
        "kaggriculture_e776_agent",
    ):
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
    if name == "e11":
        return _load_module_agent("agent_e11_prvsiyan_frontier")
    if name == "aurax7_v7":
        return _load_elite("aurax7_v7_current")
    if name == "kaito58":
        return _load_elite("kaito58")
    raise ValueError(name)


def _obs_from_state(state):
    obs = state.get("observation") if isinstance(state, dict) else None
    if isinstance(obs, str):
        try:
            obs = json.loads(obs)
        except Exception:
            return None
    return obs if isinstance(obs, dict) else None


def _shops(obs):
    town = obs.get("town", {}) if isinstance(obs, dict) else {}
    shops = town.get("unlocked_shops", []) or []
    return tuple(str(x) for x in shops)


def _farm(obs, seat):
    farms = obs.get("farms", []) if isinstance(obs, dict) else []
    if not isinstance(farms, list) or not (0 <= seat < len(farms)):
        return None
    return farms[seat]


def _track_run(env, seat):
    first = {2: None, 3: None, 4: None}
    seen_plants = set()
    seen_animals = set()
    plants = Counter()
    animals = Counter()
    max_hands = 0
    min_locked = None
    max_shops = ()

    for step_states in env.steps:
        if not isinstance(step_states, list) or seat >= len(step_states):
            continue
        obs = _obs_from_state(step_states[seat])
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

        hands = farm.get("hands", []) or []
        max_hands = max(max_hands, len(hands))

        tiles = farm.get("tiles", []) or []
        locked = 0

        for y, row in enumerate(tiles):
            if not isinstance(row, list):
                continue
            for x, tile in enumerate(row):
                if tile == "LOCKED":
                    locked += 1
                    continue
                if not isinstance(tile, dict):
                    continue

                if tile.get("kind") == "PLANT" and tile.get("crop") in CROPS:
                    crop = str(tile["crop"])
                    planted_day = tile.get("planted_day", None)
                    sig = (x, y, crop, planted_day)
                    if sig not in seen_plants:
                        seen_plants.add(sig)
                        plants[crop] += 1

                animal = tile.get("animal")
                if animal in ANIMALS:
                    animal = str(animal)
                    placed_day = tile.get("placed_day", None)
                    sig = (x, y, animal, placed_day)
                    if sig not in seen_animals:
                        seen_animals.add(sig)
                        animals[animal] += 1

        min_locked = locked if min_locked is None else min(min_locked, locked)

    final_reward = None
    final_status = None
    if env.steps and seat < len(env.steps[-1]):
        st = env.steps[-1][seat]
        try:
            final_reward = float(st.get("reward"))
        except Exception:
            final_reward = None
        final_status = st.get("status")

    return {
        "shops2": list(first[2]) if first[2] is not None else None,
        "shops3": list(first[3]) if first[3] is not None else None,
        "shops4": list(first[4]) if first[4] is not None else None,
        "all_shops": list(max_shops),
        "plants": {p: int(plants.get(p, 0)) for p in CROPS},
        "animals": {a: int(animals.get(a, 0)) for a in ANIMALS},
        "max_hands": int(max_hands),
        "min_locked_tiles": min_locked,
        "reward": final_reward,
        "status": final_status,
    }


def child(args):
    from kaggle_environments import make

    e21 = resolve("e21")
    opp = resolve(args.opponent)

    if args.seat == 0:
        agents = [e21, opp]
    else:
        agents = [opp, e21]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)

    rec = {
        "seed": args.seed,
        "seat": args.seat,
        "opponent": args.opponent,
        **_track_run(env, args.seat),
    }
    print(PREFIX + json.dumps(rec, ensure_ascii=False))


def demand(shops, k):
    d = Counter()
    if not shops:
        return d
    for shop in shops[:k]:
        for p in SHOP_PRODUCTS.get(shop, ()):
            d[p] += 1
    return d


def corr(xs, ys):
    if len(xs) < 3:
        return float("nan")
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def fmt(x):
    if x is None:
        return "n/a"
    if isinstance(x, float) and math.isnan(x):
        return "n/a"
    return f"{x:.3f}" if isinstance(x, float) else str(x)


def enriched(rows, k):
    out = []
    for r in rows:
        shops = r.get(f"shops{k}")
        if not shops:
            continue
        d = demand(shops, k)
        out.append({
            **r,
            **{f"d_{p}": int(d.get(p, 0)) for p in TRACK_PRODUCTS},
        })
    return out


def relationship_table(rows, k):
    rr = enriched(rows, k)
    tests = [
        ("MILK demand → cows", "MILK", lambda r: r["animals"]["COW"]),
        ("WOOL demand → sheep", "WOOL", lambda r: r["animals"]["SHEEP"]),
        ("CARROT demand → carrot plants", "CARROT", lambda r: r["plants"]["CARROT"]),
        ("TOMATO demand → tomato plants", "TOMATO", lambda r: r["plants"]["TOMATO"]),
        ("STRAWBERRY demand → strawberry plants", "STRAWBERRY", lambda r: r["plants"]["STRAWBERRY"]),
        ("WHEAT demand → wheat plants", "WHEAT", lambda r: r["plants"]["WHEAT"]),
    ]
    result = []
    for label, prod, yfn in tests:
        xs = [r[f"d_{prod}"] for r in rr]
        ys = [yfn(r) for r in rr]
        result.append((label, corr(xs, ys), len(rr)))
    return result


def bucket_lines(rows, k, product, target_name, target_fn):
    rr = enriched(rows, k)
    buckets = defaultdict(list)
    for r in rr:
        buckets[r[f"d_{product}"]].append(target_fn(r))
    out = [f"### first {k}: {product} → `{target_name}`", ""]
    if not buckets:
        out.append("- no data")
        out.append("")
        return out
    for d in sorted(buckets):
        vals = buckets[d]
        out.append(
            f"- demand {d}: mean {sum(vals)/len(vals):.2f}, "
            f"min {min(vals)}, max {max(vals)}, n={len(vals)}"
        )
    out.append("")
    return out


def run_one(seed, seat, opponent):
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--seed", str(seed),
        "--seat", str(seat),
        "--opponent", opponent,
    ]
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
        err = (p.stderr or p.stdout or "no result")[-4000:]
        return {
            "seed": seed,
            "seat": seat,
            "opponent": opponent,
            "error": err,
        }
    return rec


def parent(args):
    opponents = [x.strip() for x in args.opponents.split(",") if x.strip()]
    seeds = list(range(args.seed_start, args.seed_start + args.seeds))

    rows = []
    total = len(opponents) * len(seeds) * 2
    done = 0

    print("=== E21 realized shop-response probe ===")
    print("Seeds:", f"{seeds[0]}..{seeds[-1]}")
    print("Opponents:", ", ".join(opponents))
    print("Games:", total)
    print()

    for opponent in opponents:
        for seed in seeds:
            for seat in (0, 1):
                done += 1
                print(f"[{done:>3}/{total}] E21 vs {opponent} seed={seed} seat={seat}", flush=True)
                rows.append(run_one(seed, seat, opponent))

    errors = [r for r in rows if "error" in r]
    valid = [r for r in rows if "error" not in r]

    payload = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "seed_start": args.seed_start,
        "seeds": args.seeds,
        "opponents": opponents,
        "rows": rows,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# E21 Realized Shop Response",
        "",
        f"- Generated: `{payload['generated']}`",
        f"- Seeds: `{seeds[0]}..{seeds[-1]}`",
        f"- Opponents: {', '.join(f'`{x}`' for x in opponents)}",
        f"- Games requested: **{total}**",
        f"- Valid games: **{len(valid)}**",
        f"- Errors: **{len(errors)}**",
        "",
        "This report counts unique plant/animal instances observed in actual completed games.",
        "It is intentionally different from counting commands in static route tapes.",
        "",
    ]

    if errors:
        report += ["## Errors", ""]
        counts = Counter(r["error"] for r in errors)
        for err, n in counts.most_common():
            report.append(f"- {n}× `{err[:500]}`")
        report.append("")

    report += ["## 1. Realized shop-demand correlations", ""]
    for k in (2, 3, 4):
        report += [
            f"### First {k} shops",
            "",
            "| Relationship | Correlation | N |",
            "|---|---:|---:|",
        ]
        for label, c, n in relationship_table(valid, k):
            report.append(f"| {label} | {fmt(c)} | {n} |")
        report.append("")

    report += ["## 2. By-opponent correlations", ""]
    for opponent in opponents:
        subset = [r for r in valid if r["opponent"] == opponent]
        report.append(f"### vs `{opponent}`")
        report.append("")
        report.append("| Window | Relationship | Correlation | N |")
        report.append("|---|---|---:|---:|")
        for k in (2, 3, 4):
            for label, c, n in relationship_table(subset, k):
                report.append(f"| first {k} | {label} | {fmt(c)} | {n} |")
        report.append("")

    report += ["## 3. Demand buckets from first 4 shops", ""]
    bucket_specs = [
        ("MILK", "cow", lambda r: r["animals"]["COW"]),
        ("WOOL", "sheep", lambda r: r["animals"]["SHEEP"]),
        ("CARROT", "carrot", lambda r: r["plants"]["CARROT"]),
        ("TOMATO", "tomato", lambda r: r["plants"]["TOMATO"]),
        ("STRAWBERRY", "strawberry", lambda r: r["plants"]["STRAWBERRY"]),
        ("WHEAT", "wheat", lambda r: r["plants"]["WHEAT"]),
    ]
    for prod, target, fn in bucket_specs:
        report += bucket_lines(valid, 4, prod, target, fn)

    report += [
        "## 4. Production ranges",
        "",
        "| Metric | Min | Median-ish | Max |",
        "|---|---:|---:|---:|",
    ]

    metrics = [
        ("COW placements", lambda r: r["animals"]["COW"]),
        ("SHEEP placements", lambda r: r["animals"]["SHEEP"]),
        ("GOOSE placements", lambda r: r["animals"]["GOOSE"]),
        ("CARROT plants", lambda r: r["plants"]["CARROT"]),
        ("TOMATO plants", lambda r: r["plants"]["TOMATO"]),
        ("STRAWBERRY plants", lambda r: r["plants"]["STRAWBERRY"]),
        ("MELON plants", lambda r: r["plants"]["MELON"]),
        ("WHEAT plants", lambda r: r["plants"]["WHEAT"]),
        ("max hands", lambda r: r["max_hands"]),
    ]
    for label, fn in metrics:
        vals = sorted(fn(r) for r in valid)
        if not vals:
            continue
        mid = vals[len(vals)//2]
        report.append(f"| {label} | {vals[0]} | {mid} | {vals[-1]} |")

    report += [
        "",
        "## 5. E22 decision rule",
        "",
        "- If first-3/first-4 CARROT/TOMATO/STRAWBERRY correlations become strong in realized games, E21 already contains later-shop production adaptation; E22 should target another failure mode.",
        "- If milk/wool remain responsive but crop correlations remain weak, E22 should be a coherent later-shop crop-routing family rather than an E21 market-threshold patch.",
        "- If response changes strongly by opponent, production and market overlays are coupled; E22 should be tested as a separate full system, not a local graft.",
        "",
        "Final selection must still use population-level W/D/L / Bradley–Terry evidence.",
        "",
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {payload['generated']} — Probe E21 realized shop response\n\n"
            f"- Seeds: `{seeds[0]}..{seeds[-1]}`\n"
            f"- Opponents: {', '.join(opponents)}\n"
            f"- Valid games: {len(valid)}/{total}\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Data: `{DATA.name}`\n"
            "- Read-only; no agent modification or submission.\n\n"
        )

    print()
    print("=== Probe complete ===")
    print("Valid:", len(valid), "/", total)
    print("Errors:", len(errors))
    print("Report:", REPORT.name)
    print("Data:", DATA.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--seed-start", type=int, default=19000)
    ap.add_argument("--opponents", default="e11,aurax7_v7")

    ap.add_argument("--child", action="store_true")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--seat", type=int, choices=(0, 1))
    ap.add_argument("--opponent")

    args = ap.parse_args()

    if args.child:
        child(args)
    else:
        parent(args)


if __name__ == "__main__":
    main()
