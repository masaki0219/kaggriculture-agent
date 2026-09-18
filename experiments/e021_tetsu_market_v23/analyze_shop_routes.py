#!/usr/bin/env python3
"""
2026-09-18 — Analyze E21 shop-conditioned routes

Run from the Kaggle repository root:

    python experiments/e021_tetsu_market_v23/analyze_shop_routes.py

Output:
    experiments/e021_tetsu_market_v23/shop_route_report.md

Read-only analysis. Does not modify agents or submit.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import hashlib
import importlib.util
import math
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT / "artifacts" / "bundles" / "current"
    / "public_agents" / "elite" / "tetsu_market_v23_current"
    / "raw" / "_extract_submission_tar" / "main.py"
)
REPORT = HERE / "shop_route_report.md"
HISTORY = ROOT / "docs" / "experiment_run_history.md"

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
TRACK = ("MILK", "WOOL", "CARROT", "TOMATO", "STRAWBERRY", "WHEAT")

def load_module(path):
    p = str(path.parent)
    if p not in sys.path:
        sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location("_e21_shop_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

def norm_key(key):
    if isinstance(key, str):
        return (key,)
    if isinstance(key, (list, tuple)):
        return tuple(str(x) for x in key)
    return (str(key),)

def summarize_route(tape):
    out = {
        "hires": 0,
        "land": 0,
        "animals": Counter(),
        "seed_buys": Counter(),
        "plants": Counter(),
    }
    if not isinstance(tape, (list, tuple)):
        return out
    for action in tape:
        if not isinstance(action, dict):
            continue
        for order in action.get("market", []) or []:
            if not isinstance(order, (list, tuple)) or not order:
                continue
            op = order[0]
            item = order[1] if len(order) > 1 else None
            try:
                qty = max(0, int(order[2])) if len(order) > 2 else 1
            except Exception:
                qty = 1
            if op == "HIRE":
                out["hires"] += 1
            elif op == "BUY_LAND":
                out["land"] += 1
            elif op == "BUY_ANIMAL" and item:
                out["animals"][str(item)] += qty
            elif op == "BUY_SEED" and item:
                out["seed_buys"][str(item)] += qty
        units = [action.get("farmer")] + list(action.get("hands", []) or [])
        for cmd in units:
            if isinstance(cmd, (list, tuple)) and len(cmd) > 1 and cmd[0] == "PLANT":
                out["plants"][str(cmd[1])] += 1
    return out

def demand(shops):
    d = Counter()
    for shop in shops:
        for p in SHOP_PRODUCTS.get(shop, ()):
            d[p] += 1
    return d

def corr(xs, ys):
    if len(xs) < 3:
        return float("nan")
    mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
    vx = sum((x-mx)**2 for x in xs)
    vy = sum((y-my)**2 for y in ys)
    if vx == 0 or vy == 0:
        return float("nan")
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys)) / math.sqrt(vx*vy)

def fmt(x):
    return "n/a" if isinstance(x, float) and math.isnan(x) else f"{x:.3f}"

def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing E21 source: {SOURCE}")
    sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    mod = load_module(SOURCE)

    route_dicts = {}
    for name, val in vars(mod).items():
        if isinstance(val, dict) and val and ("ROUTES" in name.upper() or name in ("routes", "ROUTES")):
            if all(isinstance(v, (list, tuple)) for v in val.values()):
                route_dicts[name] = val
    if not route_dicts:
        raise SystemExit("No route table found.")
    routes_name, routes = max(route_dicts.items(), key=lambda kv: len(kv[1]))

    shop_maps = {}
    for name, val in vars(mod).items():
        if isinstance(val, dict) and val and "SHOP" in name.upper() and "ROUTE" in name.upper():
            shop_maps[name] = val

    summaries = {rid: summarize_route(tape) for rid, tape in routes.items()}

    lines = []
    lines += [
        "# E21 Shop-Route Report",
        "",
        f"- Generated: `{datetime.now().astimezone().isoformat(timespec='seconds')}`",
        f"- Exact source SHA256: `{sha}`",
        f"- Route table: `{routes_name}` with **{len(routes)} routes**",
        f"- Shop maps: {', '.join(f'`{x}`' for x in shop_maps) or 'none'}",
        "",
        "## 1. Route production signatures",
        "",
        "| Route | Hires | Land | COW | SHEEP | GOOSE | Seeds W/C/T/S/M | Plants W/C/T/S/M |",
        "|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for rid in sorted(routes, key=lambda x: str(x)):
        s = summaries[rid]
        seeds = "/".join(str(s["seed_buys"].get(p,0)) for p in ("WHEAT","CARROT","TOMATO","STRAWBERRY","MELON"))
        plants = "/".join(str(s["plants"].get(p,0)) for p in ("WHEAT","CARROT","TOMATO","STRAWBERRY","MELON"))
        lines.append(
            f"| `{rid}` | {s['hires']} | {s['land']} | "
            f"{s['animals'].get('COW',0)} | {s['animals'].get('SHEEP',0)} | {s['animals'].get('GOOSE',0)} | "
            f"{seeds} | {plants} |"
        )

    rows = []
    for map_name, mp in shop_maps.items():
        lines += ["", f"## 2. `{map_name}`", "", f"Entries: **{len(mp)}**", ""]
        lines += [
            "| Shops | Route | COW | SHEEP | GOOSE | Plant C/T/S/M |",
            "|---|---:|---:|---:|---:|---|",
        ]
        for key, rid in sorted(mp.items(), key=lambda kv: str(kv[0])):
            shops = norm_key(key)
            s = summaries.get(rid)
            if s is None:
                lines.append(f"| `{' → '.join(shops)}` | `{rid}` | ? | ? | ? | ? |")
                continue
            lines.append(
                f"| `{' → '.join(shops)}` | `{rid}` | "
                f"{s['animals'].get('COW',0)} | {s['animals'].get('SHEEP',0)} | {s['animals'].get('GOOSE',0)} | "
                f"{s['plants'].get('CARROT',0)}/{s['plants'].get('TOMATO',0)}/"
                f"{s['plants'].get('STRAWBERRY',0)}/{s['plants'].get('MELON',0)} |"
            )
            d = demand(shops)
            rows.append({
                "map": map_name,
                "route": rid,
                **{f"d_{p}": d.get(p,0) for p in TRACK},
                "cow": s["animals"].get("COW",0),
                "sheep": s["animals"].get("SHEEP",0),
                "carrot": s["plants"].get("CARROT",0),
                "tomato": s["plants"].get("TOMATO",0),
                "strawberry": s["plants"].get("STRAWBERRY",0),
                "wheat": s["plants"].get("WHEAT",0),
            })

    lines += [
        "",
        "## 3. Shop-demand → production response",
        "",
        "Correlation across shop-map entries. This measures encoded routing response, not gameplay quality.",
        "",
        "| Relationship | Correlation |",
        "|---|---:|",
    ]
    tests = [
        ("MILK demand → cows", "MILK", "cow"),
        ("WOOL demand → sheep", "WOOL", "sheep"),
        ("CARROT demand → carrot plants", "CARROT", "carrot"),
        ("TOMATO demand → tomato plants", "TOMATO", "tomato"),
        ("STRAWBERRY demand → strawberry plants", "STRAWBERRY", "strawberry"),
        ("WHEAT demand → wheat plants", "WHEAT", "wheat"),
    ]
    for label, prod, target in tests:
        c = corr([r[f"d_{prod}"] for r in rows], [r[target] for r in rows])
        lines.append(f"| {label} | {fmt(c)} |")

    lines += ["", "## 4. Demand-bucket means", ""]
    for prod, target in [(x[1], x[2]) for x in tests]:
        buckets = defaultdict(list)
        for r in rows:
            buckets[r[f"d_{prod}"]].append(r[target])
        if not buckets:
            continue
        lines.append(f"### {prod} → `{target}`")
        lines.append("")
        for k in sorted(buckets):
            vals = buckets[k]
            lines.append(f"- demand {k}: mean {sum(vals)/len(vals):.2f}, min {min(vals)}, max {max(vals)}, n={len(vals)}")
        lines.append("")

    lines += [
        "## 5. Decision gate",
        "",
        "- If E21 already strongly changes cows/sheep/crops with shop demand, do not make E22 merely 'shop-conditioned production'.",
        "- If route IDs change but production signatures barely move, E22 can test a genuinely production-sensitive router.",
        "- If only some product dimensions react, E22 should target the missing dimensions as one coherent routing family.",
        "",
        "Final objective remains population-level W/D/L / Bradley–Terry, not route diversity itself.",
        "",
    ]

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {datetime.now().astimezone().isoformat(timespec='seconds')} — Analyze E21 shop routes\n\n"
            f"- Source SHA256: `{sha}`\n"
            f"- Report: `{REPORT.name}`\n"
            f"- Route table: `{routes_name}` ({len(routes)} routes)\n"
            f"- Shop maps: {', '.join(shop_maps) or 'none'}\n"
            "- Read-only; no agent modification or submission.\n\n"
        )

    print("=== E21 shop-route analysis complete ===")
    print("Exact source SHA256:", sha)
    print("Route table:", routes_name, f"({len(routes)} routes)")
    print("Shop maps:", ", ".join(shop_maps) or "none")
    print("Report:", REPORT.name)

if __name__ == "__main__":
    main()
