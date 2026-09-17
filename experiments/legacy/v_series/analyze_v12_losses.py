"""
analyze_v12_losses.py

Purpose
-------
Find *why v12 loses*, rather than optimizing proxy metrics.

The script:
1. Runs v12 against several structurally different public holdouts.
2. Swaps seats for every seed.
3. Keeps only real W/L outcomes as the primary metric.
4. For every game, records:
   - bank
   - daily hired hands
   - unlocked land
   - COW / SHEEP / GOOSE
   - crop footprint
   - private shed inventory (offline diagnostic only)
   - actually executed SELL units / revenue / mean sale price
5. Prints aggregate feature deltas separately for wins and losses.
6. Writes a JSON report for deeper follow-up.

Important
---------
Opponent private state is read only after the local simulation for diagnosis.
This is NOT information the live agent may use.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import contextmanager
import importlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import sys
from typing import Any, Iterator

from kaggle_environments import make

from agent_v12 import agent as v12


ROOT = Path(__file__).resolve().parent

DEFAULT_OPPONENTS = {
    "gzmcr": ROOT / "public_agents" / "gzmcr" / "main.py",
    "lonespear": ROOT / "public_agents" / "lonespear" / "main.py",
    # Clone with:
    # git clone https://github.com/qeinstein/kaggriculture.git public_agents/qeinstein
    "qeinstein_portfolio": (
        ROOT / "public_agents" / "qeinstein" / "scripts" / "frontier_portfolio_entry.py"
    ),
    # Clone with:
    # git clone https://github.com/ian-turner/kaggriculture.git public_agents/ian_turner
    "ian_turner": ROOT / "public_agents" / "ian_turner" / "main.py",
}

CHECKPOINT_DAYS = (5, 10, 15, 20, 25, 29)
CHECKPOINT_HOUR = 12

FEATURES = (
    "money",
    "hands",
    "land",
    "COW",
    "SHEEP",
    "GOOSE",
    "WHEAT",
    "CARROT",
    "TOMATO",
    "STRAWBERRY",
    "MELON",
    "shed_total",
)

PRODUCTS = (
    "MILK",
    "WOOL",
    "EGG",
    "MELON",
    "STRAWBERRY",
    "TOMATO",
    "CARROT",
    "WHEAT",
)


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _module_root_for(path: Path) -> Path:
    """Best-effort repository root for public agents with internal imports."""
    path = path.resolve()
    if path.parent.name in {"scripts", "agents"}:
        return path.parent.parent
    return path.parent


def load_agent_file(path: Path, module_name: str):
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

    fn = getattr(module, "agent", None)
    if fn is None:
        raise AttributeError(f"{path} does not expose agent(obs)")
    return fn


@contextmanager
def capture_sell_ledger() -> Iterator[list[dict[str, Any]]]:
    """Capture only successful unit SELL commits from the official engine."""
    engine = importlib.import_module(
        "kaggle_environments.envs.kaggriculture.kaggriculture"
    )
    original_process = engine._process_market  # noqa: SLF001
    original_commit = engine._commit_unit  # noqa: SLF001

    events: list[dict[str, Any]] = []
    current: dict[str, Any] = {}

    def commit(op, item, price, farm, private, market, shed_capacity=100):
        player = current.get("players", {}).get(id(farm))
        ok = original_commit(
            op, item, price, farm, private, market, shed_capacity
        )
        if ok and op == "SELL" and player is not None:
            events.append(
                {
                    "step": int(current.get("step", -1)),
                    "player": int(player),
                    "product": str(item),
                    "price": float(price),
                }
            )
        return ok

    def process(state, env):
        obs = state[0].observation
        farms = _get(obs, "farms", []) or []
        current["step"] = int(_get(obs, "step", -1) or -1)
        current["players"] = {id(farm): i for i, farm in enumerate(farms)}
        return original_process(state, env)

    engine._commit_unit = commit  # type: ignore[attr-defined]  # noqa: SLF001
    engine._process_market = process  # type: ignore[attr-defined]  # noqa: SLF001
    try:
        yield events
    finally:
        engine._process_market = original_process  # type: ignore[attr-defined]  # noqa: SLF001
        engine._commit_unit = original_commit  # type: ignore[attr-defined]  # noqa: SLF001


def farm_features(states, seat: int) -> dict[str, float]:
    shared_obs = states[0].observation
    farms = _get(shared_obs, "farms", []) or []
    farm = farms[seat]

    # Each seat owns its own private observation.
    private = _get(states[seat].observation, "private", {}) or {}
    shed = _get(private, "shed", {}) or {}

    out: dict[str, float] = {
        "money": float(_get(farm, "money", 0) or 0),
        "hands": float(len(_get(farm, "hands", []) or [])),
        "land": float(len(_get(farm, "unlocked_quadrants", []) or [])),
        "hires_today": float(_get(farm, "hires_today", 0) or 0),
        "shed_total": float(sum(float(v or 0) for v in shed.values())),
    }

    for k in ("COW", "SHEEP", "GOOSE"):
        out[k] = 0.0
    for k in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
        out[k] = 0.0

    for row in _get(farm, "tiles", []) or []:
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            animal = tile.get("animal")
            if animal in ("COW", "SHEEP", "GOOSE"):
                out[animal] += 1.0
            if tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                if crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
                    out[crop] += 1.0

    for product in PRODUCTS:
        out[f"shed_{product}"] = float(shed.get(product, 0) or 0)

    return out


def checkpoint_snapshot(env, candidate_seat: int) -> dict[str, Any]:
    wanted = {
        day: day * 24 + CHECKPOINT_HOUR
        for day in CHECKPOINT_DAYS
    }
    snapshots: dict[str, Any] = {}

    by_step = {}
    for states in env.steps:
        step = int(_get(states[0].observation, "step", -1))
        by_step[step] = states

    for day, target in wanted.items():
        if target not in by_step:
            # Be robust to horizon/version edge cases.
            available = [s for s in by_step if s <= target]
            if not available:
                continue
            target = max(available)

        states = by_step[target]
        opponent_seat = 1 - candidate_seat
        cand = farm_features(states, candidate_seat)
        opp = farm_features(states, opponent_seat)

        snapshots[str(day)] = {
            "step": target,
            "candidate": cand,
            "opponent": opp,
            "delta": {
                key: cand.get(key, 0.0) - opp.get(key, 0.0)
                for key in set(cand) | set(opp)
            },
        }

    return snapshots


def daily_max_hands(env, seat: int) -> dict[str, int]:
    maxima = defaultdict(int)
    for states in env.steps:
        obs = states[0].observation
        day = int(_get(obs, "day", 0) or 0)
        farms = _get(obs, "farms", []) or []
        if seat < len(farms):
            maxima[day] = max(
                maxima[day],
                len(_get(farms[seat], "hands", []) or []),
            )
    return {str(k): int(v) for k, v in sorted(maxima.items())}


def sales_summary(events: list[dict[str, Any]], seat: int) -> dict[str, Any]:
    groups: dict[str, list[float]] = defaultdict(list)
    for e in events:
        if e["player"] == seat:
            groups[e["product"]].append(float(e["price"]))

    result = {}
    for product in PRODUCTS:
        prices = groups.get(product, [])
        result[product] = {
            "units": len(prices),
            "revenue": float(sum(prices)),
            "mean_price": float(statistics.mean(prices)) if prices else 0.0,
            "floor_units": sum(p <= 1.0 for p in prices),
        }
    return result


def play(candidate, opponent, seed: int, candidate_seat: int) -> dict[str, Any]:
    agents = [None, None]
    agents[candidate_seat] = candidate
    agents[1 - candidate_seat] = opponent

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )

    with capture_sell_ledger() as ledger:
        env.run(agents)

    final = env.steps[-1]
    cand_reward = float(final[candidate_seat].reward)
    opp_reward = float(final[1 - candidate_seat].reward)

    if cand_reward > opp_reward:
        outcome = "W"
    elif cand_reward < opp_reward:
        outcome = "L"
    else:
        outcome = "D"

    return {
        "seed": seed,
        "candidate_seat": candidate_seat,
        "outcome": outcome,
        "candidate_reward": cand_reward,
        "opponent_reward": opp_reward,
        "margin": cand_reward - opp_reward,
        "checkpoints": checkpoint_snapshot(env, candidate_seat),
        "candidate_daily_max_hands": daily_max_hands(env, candidate_seat),
        "opponent_daily_max_hands": daily_max_hands(env, 1 - candidate_seat),
        "candidate_sales": sales_summary(ledger, candidate_seat),
        "opponent_sales": sales_summary(ledger, 1 - candidate_seat),
    }


def mean_or_zero(values):
    return statistics.mean(values) if values else 0.0


def aggregate_games(games: list[dict[str, Any]], outcomes: set[str]) -> dict[str, Any]:
    chosen = [g for g in games if g["outcome"] in outcomes]
    result: dict[str, Any] = {"games": len(chosen), "checkpoints": {}, "sales": {}}

    for day in map(str, CHECKPOINT_DAYS):
        rows = [g["checkpoints"][day] for g in chosen if day in g["checkpoints"]]
        result["checkpoints"][day] = {
            feature: mean_or_zero(
                [row["delta"].get(feature, 0.0) for row in rows]
            )
            for feature in FEATURES
        }

    for product in PRODUCTS:
        unit_delta = []
        revenue_delta = []
        price_delta = []
        for g in chosen:
            c = g["candidate_sales"][product]
            o = g["opponent_sales"][product]
            unit_delta.append(c["units"] - o["units"])
            revenue_delta.append(c["revenue"] - o["revenue"])
            price_delta.append(c["mean_price"] - o["mean_price"])

        result["sales"][product] = {
            "units_delta": mean_or_zero(unit_delta),
            "revenue_delta": mean_or_zero(revenue_delta),
            "mean_price_delta": mean_or_zero(price_delta),
        }

    return result


def print_aggregate(label: str, agg: dict[str, Any]):
    print(f"\n--- {label} ({agg['games']} games) ---")
    if not agg["games"]:
        return

    print("checkpoint mean delta = v12 - opponent")
    print("day  bank     hands land cows sheep straw melon shed")
    for day in map(str, CHECKPOINT_DAYS):
        x = agg["checkpoints"][day]
        print(
            f"{int(day):>3} "
            f"{x['money']:>+8.0f} "
            f"{x['hands']:>+5.1f} "
            f"{x['land']:>+4.1f} "
            f"{x['COW']:>+4.1f} "
            f"{x['SHEEP']:>+5.1f} "
            f"{x['STRAWBERRY']:>+5.1f} "
            f"{x['MELON']:>+5.1f} "
            f"{x['shed_total']:>+5.1f}"
        )

    print("\nsales mean delta = v12 - opponent")
    print("product      units   revenue   avg_price")
    for product in PRODUCTS:
        x = agg["sales"][product]
        if (
            abs(x["units_delta"]) < 1e-9
            and abs(x["revenue_delta"]) < 1e-9
            and abs(x["mean_price_delta"]) < 1e-9
        ):
            continue
        print(
            f"{product:<11} "
            f"{x['units_delta']:>+6.1f} "
            f"{x['revenue_delta']:>+9.0f} "
            f"{x['mean_price_delta']:>+10.1f}"
        )


def print_loss_details(name: str, losses: list[dict[str, Any]], limit: int):
    if not losses:
        print(f"\n{name}: no losses in this screen.")
        return

    print(f"\n{name}: first {min(limit, len(losses))} losses")
    for g in losses[:limit]:
        print(
            f"LOSS seed={g['seed']} seat={g['candidate_seat']} "
            f"v12={g['candidate_reward']:.0f} opp={g['opponent_reward']:.0f} "
            f"margin={g['margin']:+.0f}"
        )
        for day in ("10", "15", "20", "25"):
            if day not in g["checkpoints"]:
                continue
            d = g["checkpoints"][day]["delta"]
            print(
                f"  d{day}: bank {d['money']:+.0f}, "
                f"hands {d['hands']:+.0f}, land {d['land']:+.0f}, "
                f"cow {d['COW']:+.0f}, sheep {d['SHEEP']:+.0f}, "
                f"straw {d['STRAWBERRY']:+.0f}, melon {d['MELON']:+.0f}"
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seeds",
        type=int,
        default=10,
        help="number of seeds; each seed is played from both seats",
    )
    parser.add_argument(
        "--loss-limit",
        type=int,
        default=10,
        help="max individual losses printed per opponent",
    )
    parser.add_argument(
        "--output",
        default="v12_loss_analysis.json",
        help="JSON output path",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="optional opponent names to run",
    )
    args = parser.parse_args()

    opponents = {}
    for name, path in DEFAULT_OPPONENTS.items():
        if args.only and name not in args.only:
            continue
        if not path.exists():
            print(f"[SKIP] {name}: {path} not found")
            continue
        try:
            opponents[name] = load_agent_file(path, f"_holdout_{name}")
        except Exception as exc:
            print(f"[SKIP] {name}: load failed: {exc}")

    if not opponents:
        raise SystemExit("No opponents available.")

    report = {
        "candidate": "agent_v12",
        "seeds": args.seeds,
        "opponents": {},
    }

    for name, opponent in opponents.items():
        print(f"\n================ {name} ================")
        games = []

        for seed in range(args.seeds):
            for candidate_seat in (0, 1):
                g = play(v12, opponent, seed, candidate_seat)
                games.append(g)
                print(
                    f"seed={seed:2d} seat={candidate_seat} "
                    f"{g['outcome']} "
                    f"v12={g['candidate_reward']:9.0f} "
                    f"opp={g['opponent_reward']:9.0f} "
                    f"diff={g['margin']:+9.0f}"
                )

        wins = sum(g["outcome"] == "W" for g in games)
        draws = sum(g["outcome"] == "D" for g in games)
        losses = sum(g["outcome"] == "L" for g in games)
        score = (wins + 0.5 * draws) / len(games)

        print(
            f"\nRESULT {name}: v12 {wins}-{draws}-{losses}, "
            f"score={score:.1%}"
        )

        win_agg = aggregate_games(games, {"W"})
        loss_agg = aggregate_games(games, {"L"})
        print_aggregate("WINS", win_agg)
        print_aggregate("LOSSES", loss_agg)

        loss_games = [g for g in games if g["outcome"] == "L"]
        print_loss_details(name, loss_games, args.loss_limit)

        report["opponents"][name] = {
            "W": wins,
            "D": draws,
            "L": losses,
            "score": score,
            "wins": win_agg,
            "losses": loss_agg,
            "games": games,
        }

    Path(args.output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
