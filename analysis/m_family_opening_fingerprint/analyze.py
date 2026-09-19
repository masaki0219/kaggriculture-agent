#!/usr/bin/env python3
"""
M-family opening fingerprint analysis.

Run from repository root:

    python analysis/m_family_opening_fingerprint/analyze.py

Input:
    data/corpora/2026-09-18/m_family.zip

Outputs:
    analysis/m_family_opening_fingerprint/report.md
    analysis/m_family_opening_fingerprint/results.json

Goal:
Determine whether the strong M-family shares a fixed/semi-fixed opening program
during steps 0..71, and where behavior becomes state-dependent.

This is read-only strategy analysis. It does not modify an agent or submit.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import json
import math
import re
import statistics
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "corpora" / "2026-09-18" / "m_family.zip"
REPORT = HERE / "report.md"
DATA = HERE / "results.json"

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

WINDOWS = ((0, 23), (24, 47), (48, 71))
CHECKPOINTS = (23, 47, 71, 143)

MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
IGNORE_MARKET = {"SELL"}

SELECTED_MILESTONES = (
    "hire_1", "hire_2", "hire_3", "hire_4", "hire_5", "hire_6",
    "cow_buy_1", "cow_buy_2",
    "sheep_buy_1", "sheep_buy_2", "sheep_buy_3",
    "pasture_build_1", "pasture_build_2", "pasture_build_3",
    "pasture_build_4", "pasture_build_5",
    "melon_seed_1", "melon_seed_6", "melon_seed_12", "melon_seed_14",
    "melon_plant_1", "melon_plant_6", "melon_plant_12", "melon_plant_14",
    "wheat_seed_1", "wheat_seed_10",
    "wheat_plant_1", "wheat_plant_10",
)

def safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default

def median(vals):
    return statistics.median(vals) if vals else None

def qtile(vals, q):
    if not vals:
        return None
    xs = sorted(vals)
    if len(xs) == 1:
        return float(xs[0])
    pos = (len(xs) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(xs[lo])
    w = pos - lo
    return xs[lo] * (1 - w) + xs[hi] * w

def iqr(vals):
    if not vals:
        return None
    return qtile(vals, 0.75) - qtile(vals, 0.25)

def fmt(x, digits=1):
    if x is None:
        return "n/a"
    if isinstance(x, float) and math.isnan(x):
        return "n/a"
    if isinstance(x, (int, float)):
        return f"{x:.{digits}f}"
    return str(x)

def replay_members(zf):
    for name in sorted(zf.namelist()):
        if "/replays/" not in name or not name.lower().endswith(".json"):
            continue
        yield name

def target_from_path(name):
    parts = Path(name).parts
    try:
        idx = parts.index("replays")
        folder = parts[idx + 1]
    except (ValueError, IndexError):
        return None
    m = re.match(r"^\d+_(.+)$", folder)
    target = m.group(1) if m else folder
    return target if target in M_SET else None

def episode_id(replay, name):
    info = replay.get("info") or {}
    for key in ("EpisodeId", "episodeId", "episode_id", "id"):
        if key in info:
            return safe_int(info[key], 0)
    m = re.search(r"(\d{6,})", Path(name).name)
    return safe_int(m.group(1), 0) if m else 0

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

def resolve_seat(replay, target):
    names = team_names(replay)
    exact = [i for i, x in enumerate(names) if x == target]
    if len(exact) == 1:
        return exact[0], "TeamNames"
    folded = [i for i, x in enumerate(names) if x.casefold() == target.casefold()]
    if len(folded) == 1:
        return folded[0], "TeamNames-casefold"
    return None, "unresolved"

def get_obs(state):
    if not isinstance(state, dict):
        return {}
    obs = state.get("observation") or {}
    if isinstance(obs, str):
        try:
            obs = json.loads(obs)
        except Exception:
            return {}
    return obs if isinstance(obs, dict) else {}

def get_action(state):
    if not isinstance(state, dict):
        return {}
    a = state.get("action") or {}
    return a if isinstance(a, dict) else {}

def op_token(cmd, collapse_moves=True):
    if not isinstance(cmd, (list, tuple)) or not cmd:
        return "NONE"
    op = str(cmd[0])
    if collapse_moves and op in MOVES:
        return "MOVE"
    if op in ("PLANT", "PICKUP", "PLACE") and len(cmd) > 1:
        return f"{op}:{cmd[1]}"
    return op

def market_token(order):
    if not isinstance(order, (list, tuple)) or not order:
        return None
    op = str(order[0])
    if op in IGNORE_MARKET:
        return None
    if op in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL"):
        item = str(order[1]) if len(order) > 1 else "?"
        qty = safe_int(order[2], 1) if len(order) > 2 else 1
        return f"{op}:{item}:{qty}"
    return op

def action_signature(action, level):
    farmer = action.get("farmer")
    hands = action.get("hands") or []
    market = action.get("market") or []

    units = [farmer] + list(hands if isinstance(hands, list) else [])
    unit_tokens = []

    for cmd in units:
        tok = op_token(cmd, collapse_moves=True)
        if level == "economic" and tok in ("NONE", "PASS", "MOVE"):
            continue
        unit_tokens.append(tok)

    market_tokens = []
    if isinstance(market, list):
        for order in market:
            tok = market_token(order)
            if tok:
                market_tokens.append(tok)

    return (
        tuple(sorted(Counter(unit_tokens).items())),
        tuple(sorted(Counter(market_tokens).items())),
    )

def signature_label(sig):
    units, market = sig
    u = ",".join(f"{k}x{n}" for k, n in units) or "-"
    m = ",".join(f"{k}x{n}" for k, n in market) or "-"
    return f"units[{u}] market[{m}]"

def farm_at(obs, seat):
    farms = obs.get("farms") or []
    if isinstance(farms, list) and 0 <= seat < len(farms):
        f = farms[seat]
        return f if isinstance(f, dict) else {}
    return {}

def farm_diag(obs, seat):
    farm = farm_at(obs, seat)
    crops = Counter()
    animals = Counter()
    structures = Counter()
    for row in farm.get("tiles") or []:
        if not isinstance(row, list):
            continue
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT" and tile.get("crop"):
                crops[str(tile["crop"])] += 1
            if tile.get("animal"):
                animals[str(tile["animal"])] += 1
            if tile.get("kind") in ("PASTURE", "COOP"):
                structures[str(tile["kind"])] += 1

    town = obs.get("town") or {}
    return {
        "money": float(farm.get("money", 0) or 0),
        "hands": len(farm.get("hands") or []),
        "quadrants": len(farm.get("unlocked_quadrants") or []),
        "crop_total": sum(crops.values()),
        "structure_total": sum(structures.values()),
        "animal_total": sum(animals.values()),
        "crops": dict(crops),
        "animals": dict(animals),
        "structures": dict(structures),
        "shops": list(town.get("unlocked_shops") or []),
    }

def obs_step(obs, fallback):
    return safe_int(obs.get("step"), fallback)

def expand_market_counts(counter, order, step, milestones):
    if not isinstance(order, (list, tuple)) or not order:
        return
    op = str(order[0])
    item = str(order[1]) if len(order) > 1 else None
    qty = safe_int(order[2], 1) if len(order) > 2 else 1
    qty = max(1, qty)

    if op == "HIRE":
        counter["hire"] += 1
        milestones[f"hire_{counter['hire']}"] = step
    elif op == "BUY_ANIMAL" and item:
        key = f"{item.lower()}_buy"
        for _ in range(qty):
            counter[key] += 1
            milestones[f"{key}_{counter[key]}"] = step
    elif op == "BUY_SEED" and item:
        key = f"{item.lower()}_seed"
        for _ in range(qty):
            counter[key] += 1
            milestones[f"{key}_{counter[key]}"] = step
    elif op == "BUY_LAND":
        counter["land_buy"] += 1
        milestones[f"land_buy_{counter['land_buy']}"] = step

def analyze_run(replay, seat, target, member):
    steps = replay.get("steps") or []
    eid = episode_id(replay, member)
    run = {
        "team": target,
        "episode_id": eid,
        "seat": seat,
        "member": member,
        "team_names": team_names(replay),
        "steps": [],
        "checkpoints": {},
        "milestones": {},
        "window_events": {},
    }

    counters = Counter()
    milestone = {}
    event_by_step = {}

    for list_idx, states in enumerate(steps):
        if not isinstance(states, list) or seat >= len(states):
            continue
        state = states[seat]
        obs = get_obs(state)
        action = get_action(state)
        step = obs_step(obs, list_idx)

        execution_sig = action_signature(action, "execution")
        economic_sig = action_signature(action, "economic")
        event_by_step[step] = {
            "execution": execution_sig,
            "economic": economic_sig,
            "action": action,
        }

        market = action.get("market") or []
        if isinstance(market, list):
            for order in market:
                expand_market_counts(counters, order, step, milestone)

        units = [action.get("farmer")] + list(action.get("hands") or [])
        for cmd in units:
            if not isinstance(cmd, (list, tuple)) or not cmd:
                continue
            op = str(cmd[0])
            if op == "BUILD_PASTURE":
                counters["pasture_build"] += 1
                milestone[f"pasture_build_{counters['pasture_build']}"] = step
            elif op == "BUILD_COOP":
                counters["coop_build"] += 1
                milestone[f"coop_build_{counters['coop_build']}"] = step
            elif op == "PLANT" and len(cmd) > 1:
                crop = str(cmd[1]).lower()
                counters[f"{crop}_plant"] += 1
                milestone[f"{crop}_plant_{counters[f'{crop}_plant']}"] = step

        run["steps"].append({
            "step": step,
            "list_index": list_idx,
            "execution_sig": execution_sig,
            "economic_sig": economic_sig,
        })

        if step in CHECKPOINTS:
            run["checkpoints"][str(step)] = farm_diag(obs, seat)

    run["milestones"] = milestone

    for a, b in WINDOWS:
        c = Counter()
        for st in run["steps"]:
            s = st["step"]
            if not (a <= s <= b):
                continue
            action = event_by_step[s]["action"]
            for order in action.get("market") or []:
                if not isinstance(order, (list, tuple)) or not order:
                    continue
                op = str(order[0])
                item = str(order[1]) if len(order) > 1 else ""
                qty = safe_int(order[2], 1) if len(order) > 2 else 1
                if op == "HIRE":
                    c["HIRE"] += 1
                elif op == "BUY_LAND":
                    c["BUY_LAND"] += 1
                elif op in ("BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT"):
                    c[f"{op}:{item}"] += max(1, qty)
            units = [action.get("farmer")] + list(action.get("hands") or [])
            for cmd in units:
                if not isinstance(cmd, (list, tuple)) or not cmd:
                    continue
                op = str(cmd[0])
                if op == "PLANT" and len(cmd) > 1:
                    c[f"PLANT:{cmd[1]}"] += 1
                else:
                    c[op if op not in MOVES else "MOVE"] += 1
        run["window_events"][f"{a}-{b}"] = dict(c)

    return run

def consensus_rows(runs, key):
    by_step = defaultdict(list)
    team_by_step = defaultdict(lambda: defaultdict(list))
    for r in runs:
        for st in r["steps"]:
            if st["step"] > 71:
                continue
            sig = st[key]
            by_step[st["step"]].append(sig)
            team_by_step[st["step"]][r["team"]].append(sig)

    rows = []
    for step in range(72):
        vals = by_step.get(step, [])
        if not vals:
            continue
        c = Counter(vals)
        top_sig, top_n = c.most_common(1)[0]

        team_modes = {}
        for team, xs in team_by_step[step].items():
            cc = Counter(xs)
            team_modes[team] = cc.most_common(1)[0][0]
        team_agree = sum(1 for x in team_modes.values() if x == top_sig)

        rows.append({
            "step": step,
            "n": len(vals),
            "top_share": top_n / len(vals),
            "team_agree": team_agree,
            "teams": len(team_modes),
            "top_signature": signature_label(top_sig),
        })
    return rows

def summarize_checkpoint(runs, step):
    vals = [r["checkpoints"].get(str(step)) for r in runs]
    vals = [v for v in vals if isinstance(v, dict)]
    if not vals:
        return {}
    keys = ("money", "hands", "quadrants", "crop_total", "structure_total", "animal_total")
    return {
        k: {
            "median": median([v[k] for v in vals]),
            "q1": qtile([v[k] for v in vals], 0.25),
            "q3": qtile([v[k] for v in vals], 0.75),
        }
        for k in keys
    }

def summarize_milestones(runs):
    names = set()
    for r in runs:
        names.update(r["milestones"])
    out = {}
    for name in sorted(names):
        vals = [r["milestones"][name] for r in runs if name in r["milestones"]]
        by_team = defaultdict(list)
        for r in runs:
            if name in r["milestones"]:
                by_team[r["team"]].append(r["milestones"][name])
        out[name] = {
            "n": len(vals),
            "median": median(vals),
            "iqr": iqr(vals),
            "min": min(vals) if vals else None,
            "max": max(vals) if vals else None,
            "team_medians": {t: median(xs) for t, xs in sorted(by_team.items())},
        }
    return out

def summarize_window(runs, label):
    keys = set()
    for r in runs:
        keys.update((r["window_events"].get(label) or {}).keys())
    out = {}
    for key in sorted(keys):
        vals = [safe_int((r["window_events"].get(label) or {}).get(key), 0) for r in runs]
        out[key] = {
            "median": median(vals),
            "q1": qtile(vals, 0.25),
            "q3": qtile(vals, 0.75),
        }
    return out

def window_consensus(rows, a, b):
    xs = [r["top_share"] for r in rows if a <= r["step"] <= b]
    ta = [r["team_agree"] / max(1, r["teams"]) for r in rows if a <= r["step"] <= b]
    return {
        "mean_top_share": sum(xs) / len(xs) if xs else None,
        "median_top_share": median(xs),
        "mean_team_agreement": sum(ta) / len(ta) if ta else None,
        "steps_ge_0_5": sum(x >= 0.5 for x in xs),
        "n_steps": len(xs),
    }

def main():
    HERE.mkdir(parents=True, exist_ok=True)
    if not CORPUS.exists():
        raise SystemExit(f"Missing corpus: {CORPUS.relative_to(ROOT)}")

    runs = []
    unresolved = []
    malformed = []

    with zipfile.ZipFile(CORPUS, "r") as zf:
        members = list(replay_members(zf))
        for member in members:
            target = target_from_path(member)
            if target is None:
                continue
            try:
                replay = json.loads(zf.read(member))
            except Exception as e:
                malformed.append({"member": member, "error": repr(e)})
                continue

            seat, source = resolve_seat(replay, target)
            if seat is None:
                unresolved.append({
                    "member": member,
                    "target": target,
                    "team_names": team_names(replay),
                })
                continue

            rec = analyze_run(replay, seat, target, member)
            rec["seat_source"] = source
            runs.append(rec)

    if not runs:
        raise SystemExit("No M-family player-runs could be resolved.")

    execution = consensus_rows(runs, "execution_sig")
    economic = consensus_rows(runs, "economic_sig")

    checkpoints = {str(s): summarize_checkpoint(runs, s) for s in CHECKPOINTS}
    milestones = summarize_milestones(runs)
    windows = {f"{a}-{b}": summarize_window(runs, f"{a}-{b}") for a, b in WINDOWS}

    consensus_windows = {
        f"{a}-{b}": {
            "execution": window_consensus(execution, a, b),
            "economic": window_consensus(economic, a, b),
        }
        for a, b in WINDOWS
    }

    by_team = Counter(r["team"] for r in runs)
    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    payload = {
        "generated": generated,
        "corpus": str(CORPUS.relative_to(ROOT)),
        "runs": len(runs),
        "runs_by_team": dict(by_team),
        "unresolved": unresolved,
        "malformed": malformed,
        "checkpoints": checkpoints,
        "windows": windows,
        "milestones": milestones,
        "consensus_windows": consensus_windows,
        "execution_consensus": execution,
        "economic_consensus": economic,
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# M-family Opening Fingerprint",
        "",
        f"- Generated: `{generated}`",
        f"- Corpus: `{CORPUS.relative_to(ROOT)}`",
        f"- Resolved M-family player-runs: **{len(runs)}**",
        f"- Unresolved seats: **{len(unresolved)}**",
        f"- Malformed replay files: **{len(malformed)}**",
        "",
        "Final objective: identify reusable mechanisms that can improve an independent leaderboard candidate; exact replay imitation is not the objective.",
        "",
        "## 1. Coverage",
        "",
        "| Team | Runs |",
        "|---|---:|",
    ]
    for team in M_FAMILY:
        lines.append(f"| {team} | {by_team.get(team, 0)} |")

    lines += [
        "",
        "## 2. Opening state checkpoints",
        "",
        "Medians with interquartile range across resolved M-family player-runs.",
        "",
        "| Step | Crops | Structures | Animals | Hands | Q | Money |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in CHECKPOINTS:
        d = checkpoints.get(str(s), {})
        def cell(k):
            z = d.get(k, {})
            return f"{fmt(z.get('median'))} [{fmt(z.get('q1'))}, {fmt(z.get('q3'))}]"
        lines.append(
            f"| {s} | {cell('crop_total')} | {cell('structure_total')} | "
            f"{cell('animal_total')} | {cell('hands')} | {cell('quadrants')} | {cell('money')} |"
        )

    lines += [
        "",
        "## 3. Window-level semantic agreement",
        "",
        "Execution collapses NORTH/SOUTH/EAST/WEST into MOVE and ignores SELL orders. Economic additionally drops MOVE/PASS, so it asks whether the same productive/market program is being executed even when routing differs.",
        "",
        "| Window | Execution mean top-share | Economic mean top-share | Economic team agreement | Economic steps >=50% |",
        "|---|---:|---:|---:|---:|",
    ]
    for a, b in WINDOWS:
        label = f"{a}-{b}"
        x = consensus_windows[label]["execution"]
        e = consensus_windows[label]["economic"]
        lines.append(
            f"| {label} | {fmt(100*x['mean_top_share'])}% | "
            f"{fmt(100*e['mean_top_share'])}% | {fmt(100*e['mean_team_agreement'])}% | "
            f"{e['steps_ge_0_5']}/{e['n_steps']} |"
        )

    lines += [
        "",
        "## 4. Selected milestone timing",
        "",
        "Tight IQR means the event occurs at nearly the same time across runs. A wide range with a tight team-specific median suggests subfamily behavior rather than one universal script.",
        "",
        "| Milestone | N | Median step | IQR | Min-Max | Team medians |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name in SELECTED_MILESTONES:
        z = milestones.get(name)
        if not z:
            continue
        tm = ", ".join(f"{k}:{fmt(v)}" for k, v in z["team_medians"].items())
        lines.append(
            f"| `{name}` | {z['n']} | {fmt(z['median'])} | {fmt(z['iqr'])} | "
            f"{z['min']}-{z['max']} | {tm} |"
        )

    lines += [
        "",
        "## 5. What is actually done in each 24-step block",
        "",
    ]
    focus = (
        "HIRE", "BUY_ANIMAL:COW", "BUY_ANIMAL:SHEEP",
        "BUY_SEED:MELON", "BUY_SEED:WHEAT",
        "BUILD_PASTURE", "PLANT:MELON", "PLANT:WHEAT",
        "WATER", "MOVE", "PASS",
    )
    lines += [
        "| Window | " + " | ".join(f"`{x}` median[IQR]" for x in focus) + " |",
        "|---|" + "|".join("---:" for _ in focus) + "|",
    ]
    for a, b in WINDOWS:
        label = f"{a}-{b}"
        w = windows[label]
        cells = []
        for key in focus:
            z = w.get(key, {"median": 0, "q1": 0, "q3": 0})
            cells.append(f"{fmt(z['median'])}[{fmt(z['q1'])},{fmt(z['q3'])}]")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "## 6. Highest-agreement economic steps",
        "",
        "| Step | Top share | Team agreement | Modal semantic action |",
        "|---:|---:|---:|---|",
    ]
    for r in sorted(economic, key=lambda x: (-x["top_share"], x["step"]))[:24]:
        lines.append(
            f"| {r['step']} | {100*r['top_share']:.1f}% | "
            f"{r['team_agree']}/{r['teams']} | `{r['top_signature']}` |"
        )

    lines += [
        "",
        "## 7. Lowest-agreement economic steps",
        "",
        "| Step | Top share | Team agreement | Modal semantic action |",
        "|---:|---:|---:|---|",
    ]
    for r in sorted(economic, key=lambda x: (x["top_share"], x["step"]))[:24]:
        lines.append(
            f"| {r['step']} | {100*r['top_share']:.1f}% | "
            f"{r['team_agree']}/{r['teams']} | `{r['top_signature']}` |"
        )

    first = consensus_windows["0-23"]["economic"]["mean_top_share"]
    second = consensus_windows["24-47"]["economic"]["mean_top_share"]
    third = consensus_windows["48-71"]["economic"]["mean_top_share"]

    lines += [
        "",
        "## 8. Interpretation gate",
        "",
    ]

    if first is not None and second is not None and third is not None:
        if first >= second + 0.10 and first >= third + 0.10:
            lines.append(
                "- The first 24 steps have materially higher semantic agreement than the later blocks. This supports a **fixed/semi-fixed opening module followed by more state-dependent execution**."
            )
        elif min(first, second, third) >= 0.50:
            lines.append(
                "- Semantic agreement stays high through step 71. This supports a **longer family-wide program**, not just a tiny bootstrap."
            )
        else:
            lines.append(
                "- Step-level semantic agreement is not high enough by itself to justify a hard-coded opening. Use the milestone IQRs: if milestones are tight while exact steps vary, implement a **state-gated sequence of opening milestones**, not a replay tape."
            )

    lines += [
        "- If hires / 2C3S / five pastures / melon planting milestones have tight timing across all seven teams, E30 should encode those milestones as a small opening state machine.",
        "- If timing is tight only within particular teams, do not force one universal tape; keep a shared target system with subfamily/state branches.",
        "- If plant milestones are tight but action consensus is low, the E29 bottleneck is likely **routing / parallel execution**, not missing economic targets.",
        "- Only after opening fidelity improves should the next candidate be screened for population W/D/L.",
        "",
        "## 9. Data quality",
        "",
        f"- Unresolved: {len(unresolved)}",
        f"- Malformed: {len(malformed)}",
    ]
    if unresolved:
        for x in unresolved[:10]:
            lines.append(f"- unresolved `{x['member']}`: target={x['target']} TeamNames={x['team_names']}")
    if malformed:
        for x in malformed[:10]:
            lines.append(f"- malformed `{x['member']}`: {x['error']}")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("=== M-family opening fingerprint complete ===")
    print("Resolved runs:", len(runs))
    print("Runs by team:", dict(by_team))
    print("Unresolved:", len(unresolved), "Malformed:", len(malformed))
    print()
    print(REPORT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
