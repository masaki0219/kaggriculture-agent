#!/usr/bin/env python3
"""
Validate realized M-family opening milestones from replay state, not requested actions.

Run from repository root:

    python analysis/m_family_opening_realized.py

Input:
    data/corpora/2026-09-18/m_family.zip

Output:
    analysis/m_family_opening_realized_report.md

Purpose:
Separate requested market/unit actions from successfully realized state changes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import math
import re
import statistics
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "corpora" / "2026-09-18" / "m_family.zip"
REPORT = ROOT / "analysis" / "m_family_opening_realized_report.md"

M_FAMILY = (
    "Majkel1337",
    "DSM",
    "Orbital Terraformer",
    "ymg_aq",
    "QQ",
    "Arda Ceylan",
    "kwa",
)
M_SET = set(M_FAMILY)

def safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default

def median(xs):
    return statistics.median(xs) if xs else None

def qtile(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    if len(xs) == 1:
        return float(xs[0])
    p = (len(xs) - 1) * q
    lo, hi = math.floor(p), math.ceil(p)
    if lo == hi:
        return float(xs[lo])
    w = p - lo
    return xs[lo] * (1 - w) + xs[hi] * w

def iqr(xs):
    if not xs:
        return None
    return qtile(xs, .75) - qtile(xs, .25)

def fmt(x):
    return "n/a" if x is None else f"{x:.1f}"

def team_from_path(name):
    parts = Path(name).parts
    if "replays" not in parts:
        return None
    i = parts.index("replays")
    if i + 1 >= len(parts):
        return None
    folder = parts[i + 1]
    m = re.match(r"^\d+_(.+)$", folder)
    team = m.group(1) if m else folder
    return team if team in M_SET else None

def team_names(replay):
    info = replay.get("info") or {}
    for key in ("TeamNames", "teamNames", "team_names", "teams"):
        x = info.get(key)
        if isinstance(x, list):
            out = []
            for v in x:
                if isinstance(v, str):
                    out.append(v)
                elif isinstance(v, dict):
                    out.append(str(v.get("name") or v.get("teamName") or ""))
                else:
                    out.append(str(v))
            return out
    return []

def seat_for(replay, team):
    names = team_names(replay)
    for i, x in enumerate(names):
        if x == team:
            return i
    for i, x in enumerate(names):
        if x.casefold() == team.casefold():
            return i
    return None

def obs_of(state):
    if not isinstance(state, dict):
        return {}
    obs = state.get("observation") or {}
    if isinstance(obs, str):
        try:
            obs = json.loads(obs)
        except Exception:
            return {}
    return obs if isinstance(obs, dict) else {}

def action_of(state):
    if not isinstance(state, dict):
        return {}
    a = state.get("action") or {}
    return a if isinstance(a, dict) else {}

def me(obs, seat):
    farms = obs.get("farms") or []
    if isinstance(farms, list) and 0 <= seat < len(farms):
        f = farms[seat]
        return f if isinstance(f, dict) else {}
    return {}

def count_structures(farm):
    c = Counter()
    for row in farm.get("tiles") or []:
        if not isinstance(row, list):
            continue
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ("PASTURE", "COOP"):
                c[str(tile["kind"])] += 1
    return c

def count_crops(farm):
    c = Counter()
    for row in farm.get("tiles") or []:
        if not isinstance(row, list):
            continue
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop"):
                c[str(tile["crop"])] += 1
    return c

def count_owned_animals(obs, seat):
    farm = me(obs, seat)
    private = obs.get("private") or {}
    c = Counter()

    for row in farm.get("tiles") or []:
        if not isinstance(row, list):
            continue
        for tile in row:
            if isinstance(tile, dict) and tile.get("animal"):
                c[str(tile["animal"])] += 1

    shed = private.get("shed") or {}
    for a in ("COW", "SHEEP", "GOOSE"):
        c[a] += safe_int(shed.get(a), 0)

    for inv in private.get("inventories") or []:
        if not isinstance(inv, dict):
            continue
        for a in ("COW", "SHEEP", "GOOSE"):
            c[a] += safe_int(inv.get(a), 0)

    return c

def private_seeds(obs):
    p = obs.get("private") or {}
    s = p.get("seeds") or {}
    return Counter({str(k): safe_int(v, 0) for k, v in s.items()})

def new_plant_signatures(farm, seen):
    new = []
    for y, row in enumerate(farm.get("tiles") or []):
        if not isinstance(row, list):
            continue
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") != "PLANT" or not tile.get("crop"):
                continue
            sig = (x, y, str(tile["crop"]), safe_int(tile.get("planted_day"), -1))
            if sig not in seen:
                seen.add(sig)
                new.append(sig)
    return new

def requested_hires(action):
    n = 0
    for order in action.get("market") or []:
        if isinstance(order, (list, tuple)) and order and str(order[0]) == "HIRE":
            n += 1
    return n

def first_ge(milestones, key, value, step):
    if key not in milestones and value:
        milestones[key] = step

def analyze_run(replay, seat, team):
    states = []
    for i, pair in enumerate(replay.get("steps") or []):
        if not isinstance(pair, list) or seat >= len(pair):
            continue
        state = pair[seat]
        obs = obs_of(state)
        step = safe_int(obs.get("step"), i)
        states.append((step, state, obs))

    milestones = {}
    seen_plants = set()
    cumulative_plants = Counter()
    hire_attempt_rows = []

    prev_hands = None

    for idx, (step, state, obs) in enumerate(states):
        farm = me(obs, seat)
        hands = len(farm.get("hands") or [])
        animals = count_owned_animals(obs, seat)
        structures = count_structures(farm)
        seeds = private_seeds(obs)

        for _, _, crop, _ in new_plant_signatures(farm, seen_plants):
            cumulative_plants[crop] += 1

        # Realized hands.
        for n in (1, 2, 3, 4, 5, 6):
            first_ge(milestones, f"hands_{n}", hands >= n, step)

        # Realized owned animals.
        for n in (1, 2):
            first_ge(milestones, f"cow_owned_{n}", animals["COW"] >= n, step)
        for n in (1, 2, 3):
            first_ge(milestones, f"sheep_owned_{n}", animals["SHEEP"] >= n, step)
        first_ge(
            milestones,
            "core_2c3s",
            animals["COW"] >= 2 and animals["SHEEP"] >= 3,
            step,
        )

        # Realized built structures.
        total_struct = sum(structures.values())
        for n in (1, 2, 3, 4, 5):
            first_ge(milestones, f"structures_{n}", total_struct >= n, step)

        # Realized cumulative planting.
        for crop in ("MELON", "WHEAT", "STRAWBERRY"):
            for n in ((1, 6, 12, 14) if crop == "MELON" else (1, 10)):
                first_ge(
                    milestones,
                    f"{crop.lower()}_planted_cum_{n}",
                    cumulative_plants[crop] >= n,
                    step,
                )

        # Approximate successfully acquired seeds:
        # current seed inventory + cumulative successful plantings.
        # This avoids counting failed BUY_SEED requests.
        for crop, ns in (
            ("MELON", (1, 6, 12, 14)),
            ("WHEAT", (1, 10)),
        ):
            acquired = seeds[crop] + cumulative_plants[crop]
            for n in ns:
                first_ge(
                    milestones,
                    f"{crop.lower()}_acquired_{n}",
                    acquired >= n,
                    step,
                )

        # Compare requested hires at step t with realized hand delta at t+1.
        action = action_of(state)
        req = requested_hires(action)
        if req:
            next_hands = None
            if idx + 1 < len(states):
                nf = me(states[idx + 1][2], seat)
                next_hands = len(nf.get("hands") or [])
            delta = None if next_hands is None else next_hands - hands
            hire_attempt_rows.append({
                "step": step,
                "requested": req,
                "hands_before": hands,
                "hands_after": next_hands,
                "realized_delta": delta,
            })

        prev_hands = hands

    return {
        "team": team,
        "milestones": milestones,
        "hire_attempts": hire_attempt_rows,
    }

def summarize(runs, key):
    vals = [r["milestones"][key] for r in runs if key in r["milestones"]]
    by_team = defaultdict(list)
    for r in runs:
        if key in r["milestones"]:
            by_team[r["team"]].append(r["milestones"][key])
    return {
        "n": len(vals),
        "median": median(vals),
        "iqr": iqr(vals),
        "min": min(vals) if vals else None,
        "max": max(vals) if vals else None,
        "by_team": {t: median(xs) for t, xs in sorted(by_team.items())},
    }

def main():
    runs = []
    unresolved = []

    with zipfile.ZipFile(CORPUS, "r") as zf:
        for name in sorted(zf.namelist()):
            if "/replays/" not in name or not name.lower().endswith(".json"):
                continue
            team = team_from_path(name)
            if not team:
                continue
            replay = json.loads(zf.read(name))
            seat = seat_for(replay, team)
            if seat is None:
                unresolved.append((name, team, team_names(replay)))
                continue
            runs.append(analyze_run(replay, seat, team))

    keys = (
        "hands_4", "hands_5", "hands_6",
        "cow_owned_1", "cow_owned_2",
        "sheep_owned_1", "sheep_owned_2", "sheep_owned_3", "core_2c3s",
        "structures_1", "structures_2", "structures_3", "structures_4", "structures_5",
        "melon_acquired_1", "melon_acquired_6", "melon_acquired_12", "melon_acquired_14",
        "melon_planted_cum_1", "melon_planted_cum_6", "melon_planted_cum_12", "melon_planted_cum_14",
        "wheat_acquired_1", "wheat_acquired_10",
        "wheat_planted_cum_1", "wheat_planted_cum_10",
    )

    lines = [
        "# M-family Realized Opening Milestones",
        "",
        f"- Resolved runs: **{len(runs)}**",
        f"- Unresolved: **{len(unresolved)}**",
        "",
        "These are derived from observed state changes, not merely requested actions.",
        "",
        "| Milestone | N | Median | IQR | Min-Max | Team medians |",
        "|---|---:|---:|---:|---:|---|",
    ]

    for key in keys:
        z = summarize(runs, key)
        tm = ", ".join(f"{t}:{fmt(v)}" for t, v in z["by_team"].items())
        lines.append(
            f"| `{key}` | {z['n']} | {fmt(z['median'])} | {fmt(z['iqr'])} | "
            f"{z['min']}-{z['max']} | {tm} |"
        )

    # Hire request vs realized-delta diagnostics.
    attempts = defaultdict(list)
    for r in runs:
        for row in r["hire_attempts"]:
            attempts[row["step"]].append(row)

    lines += [
        "",
        "## Hire request vs realized state change",
        "",
        "| Action step | Runs with HIRE request | Median requested | Median realized hand delta next state | Zero-delta runs |",
        "|---:|---:|---:|---:|---:|",
    ]
    for step in sorted(attempts):
        xs = attempts[step]
        reqs = [x["requested"] for x in xs]
        deltas = [x["realized_delta"] for x in xs if x["realized_delta"] is not None]
        zero = sum(1 for x in xs if x["realized_delta"] == 0)
        lines.append(
            f"| {step} | {len(xs)} | {fmt(median(reqs))} | {fmt(median(deltas))} | {zero} |"
        )

    lines += [
        "",
        "## Decision use",
        "",
        "- If `hands_4`, `core_2c3s`, `structures_5`, and `melon_acquired_6` remain tight across all seven teams, encode them as E30 opening state-machine milestones.",
        "- Use realized `hands_5/6`, not requested HIRE actions, to decide when the opening workforce actually expands.",
        "- If `melon_planted_cum_12` is much less stable than M6, keep only M6 fixed and let later melon expansion be state-based.",
        "- Do not hard-code failed market attempts.",
        "",
    ]

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()
