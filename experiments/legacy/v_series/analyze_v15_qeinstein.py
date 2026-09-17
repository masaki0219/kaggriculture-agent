"""
analyze_v15_qeinstein.py

Diagnose why agent_v15 (Kaito v48) sometimes beats but usually loses to a
qeinstein strong reference agent.

Default:
    python analyze_v15_qeinstein.py

Examples:
    python analyze_v15_qeinstein.py --opponent candidate7
    python analyze_v15_qeinstein.py --opponent champion
    python analyze_v15_qeinstein.py --opponent portfolio

The script compares winning vs losing games using:
- town shop sequence
- checkpoint bank / hands / land
- animal and crop counts
- market prices / inventory
- v15 issued market-order mix
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
import sys

from kaggle_environments import make
from agent_v15 import agent as v15

ROOT = Path(__file__).resolve().parent
QROOT = ROOT / "public_agents" / "qeinstein"

OPPONENT_PATHS = {
    "champion": QROOT / "scripts" / "champion_entry.py",
    "candidate5": QROOT / "scripts" / "candidate5_entry.py",
    "candidate7": QROOT / "scripts" / "candidate7_entry.py",
    "portfolio": QROOT / "scripts" / "frontier_portfolio_entry.py",
}

CHECKPOINTS = {(5, 12), (10, 12), (15, 12), (20, 12), (25, 12), (29, 12)}
PRODUCTS = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER",
)

def get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def plain(obj):
    if isinstance(obj, dict):
        return {str(k): plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [plain(v) for v in obj]
    if hasattr(obj, "items"):
        try:
            return {str(k): plain(v) for k, v in obj.items()}
        except Exception:
            pass
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    try:
        return copy.deepcopy(obj)
    except Exception:
        return repr(obj)

def load_agent_file(path: Path, module_name: str):
    path = path.resolve()
    repo_root = path.parent.parent if path.parent.name in {"scripts", "agents"} else path.parent

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

    fn = getattr(module, "agent", None)
    if not callable(fn):
        raise AttributeError(f"{path} does not expose agent(obs)")
    return fn

def tile_counts(farm):
    animals = Counter()
    crops = Counter()
    weeds = 0

    for row in get(farm, "tiles", []) or []:
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "PLANT":
                crop = tile.get("crop")
                if crop:
                    crops[str(crop)] += 1
            elif kind == "WEED":
                weeds += 1
            elif kind in ("PASTURE", "COOP"):
                animal = tile.get("animal")
                if animal:
                    animals[str(animal)] += 1
    return animals, crops, weeds

def public_farm(obs, player):
    farms = get(obs, "farms", []) or []
    farm = farms[player]
    animals, crops, weeds = tile_counts(farm)
    return {
        "money": float(get(farm, "money", 0) or 0),
        "hands": len(get(farm, "hands", []) or []),
        "land": len(get(farm, "unlocked_quadrants", []) or []),
        "animals": dict(animals),
        "crops": dict(crops),
        "weeds": weeds,
    }

def private_self(obs, player):
    out = public_farm(obs, player)
    private = get(obs, "private", {}) or {}
    shed = get(private, "shed", {}) or {}
    seeds = get(private, "seeds", {}) or {}
    out["shed_total"] = int(sum(shed.values()))
    out["shed"] = {k: int(v) for k, v in shed.items() if v}
    out["seeds"] = {k: int(v) for k, v in seeds.items() if v}
    return out

def delta(a, b):
    d = {
        "money": a.get("money", 0) - b.get("money", 0),
        "hands": a.get("hands", 0) - b.get("hands", 0),
        "land": a.get("land", 0) - b.get("land", 0),
        "weeds": a.get("weeds", 0) - b.get("weeds", 0),
    }
    for x in ("COW", "SHEEP", "GOOSE"):
        d[x] = a.get("animals", {}).get(x, 0) - b.get("animals", {}).get(x, 0)
    for x in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
        d[x] = a.get("crops", {}).get(x, 0) - b.get("crops", {}).get(x, 0)
    return d

def market_view(obs):
    market = get(obs, "market", {}) or {}
    prices = get(market, "prices", {}) or {}
    inv = get(market, "inventory", {}) or {}
    return {
        "prices": {p: float(get(prices, p, 0) or 0) for p in PRODUCTS},
        "inventory": {p: float(get(inv, p, 0) or 0) for p in PRODUCTS},
        "params": plain(get(market, "params", {}) or {}),
    }

def shops(obs):
    town = get(obs, "town", {}) or {}
    return list(get(town, "unlocked_shops", []) or [])

class Probe:
    def __init__(self, fn, seat):
        self.fn = fn
        self.seat = seat
        self.checkpoints = {}
        self.order_units = Counter()
        self.town_by_day = {}
        self.initial_market = None

    def __call__(self, obs, configuration=None):
        day = int(get(obs, "day", 0) or 0)
        hour = int(get(obs, "hour", 0) or 0)

        if self.initial_market is None:
            self.initial_market = market_view(obs)

        self.town_by_day[str(day)] = shops(obs)

        if (day, hour) in CHECKPOINTS:
            me = private_self(obs, self.seat)
            opp = public_farm(obs, 1 - self.seat)
            self.checkpoints[f"d{day}h{hour}"] = {
                "self": me,
                "opp": opp,
                "delta": delta(me, opp),
                "market": market_view(obs),
                "shops": shops(obs),
            }

        try:
            action = self.fn(obs, configuration)
        except TypeError:
            action = self.fn(obs)

        if isinstance(action, dict):
            for order in action.get("market", []) or []:
                if not isinstance(order, list) or not order:
                    continue
                op = str(order[0])
                item = str(order[1]) if len(order) >= 2 else ""
                key = f"{op}:{item}" if item else op
                qty = 1
                if len(order) >= 3:
                    try:
                        qty = int(order[2])
                    except Exception:
                        qty = 1
                self.order_units[key] += max(0, qty)

        return action

def run_game(opponent, seed, seat):
    probe = Probe(v15, seat)
    agents = [None, None]
    agents[seat] = probe
    agents[1 - seat] = opponent

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run(agents)

    final = env.steps[-1]
    rv15 = float(final[seat].reward)
    ropp = float(final[1 - seat].reward)
    result = "W" if rv15 > ropp else "L" if rv15 < ropp else "D"

    obs = final[seat].observation
    me = private_self(obs, seat)
    opp = public_farm(obs, 1 - seat)

    return {
        "seed": seed,
        "seat": seat,
        "result": result,
        "v15_reward": rv15,
        "opp_reward": ropp,
        "margin": rv15 - ropp,
        "checkpoints": probe.checkpoints,
        "town_by_day": probe.town_by_day,
        "initial_market": probe.initial_market,
        "order_units": dict(probe.order_units),
        "final_self": me,
        "final_opp": opp,
        "final_delta": delta(me, opp),
        "final_market": market_view(obs),
        "final_shops": shops(obs),
    }

def print_seed_table(games):
    print("\n--- per-seed signature ---")
    by_seed = defaultdict(list)
    for g in games:
        by_seed[g["seed"]].append(g)

    for seed in sorted(by_seed):
        gs = sorted(by_seed[seed], key=lambda x: x["seat"])
        result = "".join(g["result"] for g in gs)
        margins = ", ".join(f"{g['margin']:+.0f}" for g in gs)
        print(
            f"seed={seed:2d} result={result:<2} "
            f"margins=[{margins}] shops={gs[0]['final_shops']}"
        )

def print_group(label, games):
    print(f"\n--- {label} ({len(games)} games) ---")
    if not games:
        return

    print(
        f"mean v15={mean(g['v15_reward'] for g in games):.1f}, "
        f"opp={mean(g['opp_reward'] for g in games):.1f}, "
        f"margin={mean(g['margin'] for g in games):+.1f}"
    )

    keys = ("money", "hands", "land", "COW", "SHEEP", "GOOSE",
            "WHEAT", "STRAWBERRY", "MELON", "weeds")

    for cp in ("d5h12", "d10h12", "d15h12", "d20h12", "d25h12", "d29h12"):
        ds = [g["checkpoints"][cp]["delta"] for g in games if cp in g["checkpoints"]]
        if not ds:
            continue
        av = {k: mean(d.get(k, 0) for d in ds) for k in keys}
        print(
            f"{cp}: bank={av['money']:+8.0f} hands={av['hands']:+4.1f} "
            f"land={av['land']:+3.1f} C={av['COW']:+4.1f} "
            f"S={av['SHEEP']:+4.1f} G={av['GOOSE']:+4.1f} "
            f"W={av['WHEAT']:+5.1f} St={av['STRAWBERRY']:+5.1f} "
            f"M={av['MELON']:+5.1f} weeds={av['weeds']:+4.1f}"
        )

    units = Counter()
    for g in games:
        units.update(g["order_units"])
    print("v15 issued market units mean/game:")
    for key, total in units.most_common():
        print(f"  {key:<28} {total / len(games):8.1f}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--opponent", choices=sorted(OPPONENT_PATHS), default="candidate7")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--output")
    args = ap.parse_args()

    path = OPPONENT_PATHS[args.opponent]
    if not path.exists():
        raise SystemExit(f"Missing opponent: {path}")

    opponent = load_agent_file(path, f"_diag_{args.opponent}")

    games = []
    w = d = l = 0

    print(f"================ v15 vs qeinstein:{args.opponent} ================")

    for seed in range(args.seeds):
        for seat in (0, 1):
            g = run_game(opponent, seed, seat)
            games.append(g)
            if g["result"] == "W":
                w += 1
            elif g["result"] == "D":
                d += 1
            else:
                l += 1

            suffix = "" if seat == 0 else "R"
            print(
                f"seed={seed:2d}{suffix:<1} {g['result']} "
                f"v15={g['v15_reward']:9.0f} opp={g['opp_reward']:9.0f} "
                f"diff={g['margin']:+9.0f}"
            )

    score = (w + 0.5 * d) / len(games)
    print(f"\nRESULT v15: {w}-{d}-{l}, score={score:.1%}")

    print_seed_table(games)
    print_group("WINS", [g for g in games if g["result"] == "W"])
    print_group("LOSSES", [g for g in games if g["result"] == "L"])

    out = args.output or f"v15_vs_{args.opponent}_analysis.json"
    Path(out).write_text(
        json.dumps(
            {"opponent": args.opponent, "W": w, "D": d, "L": l,
             "score": score, "games": games},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {out}")

if __name__ == "__main__":
    main()
