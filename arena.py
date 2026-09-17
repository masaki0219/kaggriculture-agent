#!/usr/bin/env python3
"""
Kaggriculture Local Arena

目的:
- E11 1体だけへの相性で判断しない
- 強豪パネル全体との W/D/L を見る
- finalist 同士を round-robin する
- tie=0.5 win として Local Bradley-Terry を計算する
- 非推移的な 3すくみ (A>B, B>C, C>A) も検出する

使い方:
    python arena.py

追加候補を明示:
    python arena.py path/to/main.py another_agent.py

軽く確認:
    python arena.py --dry-run

デフォルト:
- screen: 2 fresh seeds × both seats × 強豪パネル
  → パネル5体なら各候補およそ20戦
- confirm: finalist + 強豪パネルで 6 fresh seeds × both seats の総当たり
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from kaggle_environments import make
except Exception as exc:
    print("❌ kaggle_environments を import できません。")
    print("   先に: pip install -U kaggle-environments")
    raise


ROOT = Path.cwd()
OUTDIR = ROOT / "arena_results"

# 以前使った 10000/20000/30000 帯と分離
SCREEN_SEED_BASE = 41000
CONFIRM_SEED_BASE = 42000

CURRENT_E11_SHA256 = "02b1fee4b0e48027d4d3baeeb99518346f4fc5a14724cdb202d09a3425b15a79"

# 既知の強豪ファミリを優先してパネルに入れる
PANEL_KEYWORDS = [
    "prvsiyan",
    "qeinstein_portfolio",
    "qeinstein_candidate7",
    "qeinstein_champion",
    "qeinstein",
    "kaito",
    "boatlee",
    "seyamalam",
]

DISCOVERY_DIRS = [
    ROOT / "kaggriculture_elite_bundle_PATCHED_v2" / "public_agents" / "elite",
    ROOT / "candidates",
    ROOT / "public_agents",
]


@dataclass(frozen=True)
class Agent:
    name: str
    path: Path
    sha256: str


@dataclass
class Game:
    stage: str
    seed: int
    seat_a: int
    a: str
    b: str
    reward_a: Optional[float]
    reward_b: Optional[float]
    status_a: str
    status_b: str
    outcome_a: Optional[float]  # win=1, tie=.5, loss=0, error=None
    error: str = ""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(path: Path) -> str:
    # main.py なら親ディレクトリ名を使う
    if path.name == "main.py":
        parent = path.parent.name
        grand = path.parent.parent.name if path.parent.parent else ""
        if parent in {"raw", "extracted", "output"} and grand:
            return grand
        return parent or "main"
    return path.stem


def discover_paths(explicit: List[str], include_root_agents: bool) -> List[Path]:
    paths: List[Path] = []

    # Current E11 exact path first
    e11 = ROOT / "kaggriculture_elite_bundle_PATCHED_v2" / "public_agents" / "elite" / "prvsiyan_frontier" / "raw" / "main.py"
    if e11.is_file():
        paths.append(e11)

    # Public elite / candidates
    for d in DISCOVERY_DIRS:
        if d.is_dir():
            paths.extend(sorted(d.rglob("main.py")))

    # 明示された候補
    for item in explicit:
        p = Path(item).expanduser()
        if not p.is_absolute():
            p = ROOT / p
        if p.is_file():
            paths.append(p.resolve())
        else:
            print(f"⚠️ 追加候補が見つかりません: {item}")

    # 古い実験版まで見たい時だけ
    if include_root_agents:
        paths.extend(sorted(ROOT.glob("agent_*.py")))
        paths.extend(sorted(ROOT.glob("raw_e*.py")))

    # まずパス重複除去
    uniq: List[Path] = []
    seen = set()
    for p in paths:
        try:
            rp = p.resolve()
        except Exception:
            continue
        if rp in seen or not rp.is_file():
            continue
        seen.add(rp)
        uniq.append(rp)
    return uniq


def build_agents(paths: List[Path]) -> Tuple[List[Agent], List[Tuple[Path, Path]]]:
    agents: List[Agent] = []
    by_hash: Dict[str, Agent] = {}
    duplicates: List[Tuple[Path, Path]] = []
    used_names: Dict[str, int] = {}

    for p in paths:
        try:
            digest = sha256_file(p)
        except Exception as exc:
            print(f"⚠️ hash失敗: {p}: {exc}")
            continue

        if digest in by_hash:
            duplicates.append((p, by_hash[digest].path))
            continue

        base = safe_name(p)
        n = used_names.get(base, 0)
        used_names[base] = n + 1
        name = base if n == 0 else f"{base}_{n+1}"

        agent = Agent(name=name, path=p, sha256=digest)
        agents.append(agent)
        by_hash[digest] = agent

    return agents, duplicates


def find_e11(agents: List[Agent]) -> Optional[Agent]:
    for a in agents:
        if a.sha256 == CURRENT_E11_SHA256:
            return a
    for a in agents:
        text = (a.name + " " + str(a.path)).lower()
        if "prvsiyan" in text or "e11" in text:
            return a
    return None


def panel_priority(a: Agent) -> Tuple[int, str]:
    text = (a.name + " " + str(a.path)).lower()
    for i, kw in enumerate(PANEL_KEYWORDS):
        if kw in text:
            return (i, a.name.lower())
    return (999, a.name.lower())


def choose_panel(agents: List[Agent], e11: Optional[Agent], max_panel: int) -> List[Agent]:
    chosen: List[Agent] = []

    def add(a: Agent):
        if a not in chosen:
            chosen.append(a)

    if e11:
        add(e11)

    for a in sorted(agents, key=panel_priority):
        if panel_priority(a)[0] < 999:
            add(a)
        if len(chosen) >= max_panel:
            break

    # 強豪名が少なければ、残りから補充
    for a in agents:
        if len(chosen) >= max_panel:
            break
        add(a)

    return chosen[:max_panel]


def run_one(a: Agent, b: Agent, seed: int, seat_a: int, stage: str) -> Game:
    # seat_a=0 -> [a,b], seat_a=1 -> [b,a]
    players = [str(a.path), str(b.path)] if seat_a == 0 else [str(b.path), str(a.path)]
    try:
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        env.run(players)
        final = env.steps[-1]

        ia = seat_a
        ib = 1 - seat_a
        sa = final[ia]
        sb = final[ib]

        status_a = str(sa.status)
        status_b = str(sb.status)
        reward_a = float(sa.reward) if sa.reward is not None else None
        reward_b = float(sb.reward) if sb.reward is not None else None

        # DONE以外は戦略成績に混ぜない
        if status_a != "DONE" or status_b != "DONE" or reward_a is None or reward_b is None:
            return Game(
                stage, seed, seat_a, a.name, b.name,
                reward_a, reward_b, status_a, status_b, None,
                f"bad status: {status_a}/{status_b}",
            )

        if reward_a > reward_b:
            out = 1.0
        elif reward_a < reward_b:
            out = 0.0
        else:
            out = 0.5

        return Game(
            stage, seed, seat_a, a.name, b.name,
            reward_a, reward_b, status_a, status_b, out, "",
        )
    except Exception as exc:
        return Game(
            stage, seed, seat_a, a.name, b.name,
            None, None, "ERROR", "ERROR", None,
            f"{type(exc).__name__}: {exc}",
        )


def play_series(
    a: Agent,
    b: Agent,
    seeds: Iterable[int],
    stage: str,
    games: List[Game],
    quiet: bool = False,
) -> None:
    w = d = l = err = 0
    margins: List[float] = []

    for seed in seeds:
        for seat_a in (0, 1):
            g = run_one(a, b, seed, seat_a, stage)
            games.append(g)
            if g.outcome_a is None:
                err += 1
                symbol = "ERR"
            elif g.outcome_a == 1.0:
                w += 1
                symbol = "W"
            elif g.outcome_a == 0.5:
                d += 1
                symbol = "D"
            else:
                l += 1
                symbol = "L"

            if g.reward_a is not None and g.reward_b is not None:
                margins.append(g.reward_a - g.reward_b)

            if not quiet:
                diff = (
                    f"{(g.reward_a-g.reward_b):+.0f}"
                    if g.reward_a is not None and g.reward_b is not None
                    else "NA"
                )
                print(
                    f"  {stage:<7} {a.name} vs {b.name} "
                    f"seed={seed} seat={seat_a} {symbol} diff={diff}"
                )

    valid = w + d + l
    score = (w + 0.5 * d) / valid if valid else float("nan")
    margin = sum(margins) / len(margins) if margins else float("nan")
    print(
        f"  → {a.name} vs {b.name}: "
        f"{w}-{d}-{l} score={score:.1%} "
        f"meanΔ={margin:+,.0f} errors={err}"
        if valid
        else f"  → {a.name} vs {b.name}: NO VALID GAMES errors={err}"
    )


def aggregate_pairwise(games: List[Game], allowed_names: Optional[set] = None):
    # key = sorted name pair
    data: Dict[Tuple[str, str], Dict[str, float]] = {}
    for g in games:
        if g.outcome_a is None:
            continue
        if allowed_names is not None and (g.a not in allowed_names or g.b not in allowed_names):
            continue

        x, y = sorted([g.a, g.b])
        key = (x, y)
        rec = data.setdefault(
            key,
            {
                "games": 0,
                "x_points": 0.0,
                "y_points": 0.0,
                "x_wins": 0,
                "ties": 0,
                "y_wins": 0,
                "margin_x_sum": 0.0,
            },
        )

        rec["games"] += 1

        if g.a == x:
            x_out = g.outcome_a
            margin_x = (g.reward_a - g.reward_b) if g.reward_a is not None and g.reward_b is not None else 0.0
        else:
            x_out = 1.0 - g.outcome_a if g.outcome_a in (0.0, 1.0) else 0.5
            margin_x = (g.reward_b - g.reward_a) if g.reward_a is not None and g.reward_b is not None else 0.0

        rec["x_points"] += x_out
        rec["y_points"] += 1.0 - x_out
        rec["margin_x_sum"] += margin_x

        if x_out == 1.0:
            rec["x_wins"] += 1
        elif x_out == 0.5:
            rec["ties"] += 1
        else:
            rec["y_wins"] += 1
    return data


def pair_score(pairwise, a: str, b: str) -> Optional[float]:
    x, y = sorted([a, b])
    rec = pairwise.get((x, y))
    if not rec or rec["games"] <= 0:
        return None
    sx = rec["x_points"] / rec["games"]
    return sx if a == x else 1.0 - sx


def score_agent_vs_panel(games: List[Game], name: str, panel_names: set) -> Tuple[float, int, int]:
    pts = 0.0
    n = 0
    errs = 0
    for g in games:
        if g.stage != "screen":
            continue

        involved = False
        outcome = None
        opponent = None

        if g.a == name:
            involved = True
            outcome = g.outcome_a
            opponent = g.b
        elif g.b == name:
            involved = True
            opponent = g.a
            if g.outcome_a is None:
                outcome = None
            elif g.outcome_a == 0.5:
                outcome = 0.5
            else:
                outcome = 1.0 - g.outcome_a

        if not involved or opponent not in panel_names:
            continue

        if outcome is None:
            errs += 1
            continue

        pts += outcome
        n += 1

    return ((pts / n) if n else float("-inf"), n, errs)


def fit_bradley_terry(names: List[str], pairwise) -> Dict[str, float]:
    """
    Standard Bradley-Terry MM fit.
    Tie is split into 0.5 win for each side, matching Kaggle staff clarification.
    Values are converted to a relative log10 rating; only differences/ranking matter.

    Complete separation can make exact MLE diverge, so a vanishing epsilon is used
    only for numerical stability. W/D/L table remains the primary evidence.
    """
    if not names:
        return {}

    idx = {n: i for i, n in enumerate(names)}
    m = len(names)
    wins = [0.0] * m
    nij = [[0.0] * m for _ in range(m)]

    for (x, y), rec in pairwise.items():
        if x not in idx or y not in idx:
            continue
        i, j = idx[x], idx[y]
        n = rec["games"]
        if n <= 0:
            continue
        wins[i] += rec["x_points"]
        wins[j] += rec["y_points"]
        nij[i][j] += n
        nij[j][i] += n

    theta = [1.0] * m
    eps = 1e-12

    for _ in range(10000):
        new = [0.0] * m
        for i in range(m):
            denom = 0.0
            for j in range(m):
                if i == j or nij[i][j] <= 0:
                    continue
                denom += nij[i][j] / max(theta[i] + theta[j], eps)
            if denom <= 0:
                new[i] = theta[i]
            else:
                new[i] = max(wins[i], eps) / denom

        # identifiability: geometric mean = 1
        logs = [math.log(max(v, eps)) for v in new]
        gm = math.exp(sum(logs) / m)
        new = [max(v / gm, eps) for v in new]

        delta = max(abs(math.log(max(new[i], eps)) - math.log(max(theta[i], eps))) for i in range(m))
        theta = new
        if delta < 1e-10:
            break

    # Elo-like display scale; not Kaggle live score.
    ratings = {names[i]: 400.0 * math.log10(max(theta[i], eps)) for i in range(m)}
    mean = sum(ratings.values()) / len(ratings)
    return {k: v - mean for k, v in ratings.items()}


def find_cycles(names: List[str], pairwise, threshold: float = 0.55):
    cycles = []
    for a, b, c in itertools.combinations(names, 3):
        # permutations of triangle direction
        perms = [
            (a, b, c),
            (a, c, b),
        ]
        for x, y, z in perms:
            sxy = pair_score(pairwise, x, y)
            syz = pair_score(pairwise, y, z)
            szx = pair_score(pairwise, z, x)
            if sxy is None or syz is None or szx is None:
                continue
            if sxy > threshold and syz > threshold and szx > threshold:
                cycles.append((x, y, z, sxy, syz, szx))
    # Deduplicate rotations by frozenset
    out = []
    seen = set()
    for row in cycles:
        key = frozenset(row[:3])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def error_counts(games: List[Game]) -> Dict[str, int]:
    errs: Dict[str, int] = {}
    for g in games:
        if g.outcome_a is not None:
            continue
        # Conservative: both agents in an invalid episode get flagged for manual review.
        errs[g.a] = errs.get(g.a, 0) + 1
        errs[g.b] = errs.get(g.b, 0) + 1
    return errs


def write_outputs(
    agents: List[Agent],
    games: List[Game],
    confirm_names: List[str],
    bt: Dict[str, float],
    pairwise,
    cycles,
):
    OUTDIR.mkdir(parents=True, exist_ok=True)

    with (OUTDIR / "agents.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "sha256", "path"])
        for a in agents:
            w.writerow([a.name, a.sha256, str(a.path)])

    with (OUTDIR / "games.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "stage", "seed", "seat_a", "a", "b",
            "reward_a", "reward_b", "status_a", "status_b",
            "outcome_a", "error",
        ])
        for g in games:
            w.writerow([
                g.stage, g.seed, g.seat_a, g.a, g.b,
                g.reward_a, g.reward_b, g.status_a, g.status_b,
                g.outcome_a, g.error,
            ])

    with (OUTDIR / "pairwise.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "agent_x", "agent_y", "games",
            "x_wins", "ties", "y_wins",
            "x_score", "mean_margin_x",
        ])
        for (x, y), rec in sorted(pairwise.items()):
            n = rec["games"]
            w.writerow([
                x, y, int(n),
                int(rec["x_wins"]), int(rec["ties"]), int(rec["y_wins"]),
                rec["x_points"] / n if n else "",
                rec["margin_x_sum"] / n if n else "",
            ])

    ranked = sorted(bt.items(), key=lambda kv: kv[1], reverse=True)
    with (OUTDIR / "bt.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "agent", "local_bt_relative"])
        for i, (name, rating) in enumerate(ranked, 1):
            w.writerow([i, name, rating])

    with (OUTDIR / "summary.txt").open("w", encoding="utf-8") as f:
        print("Kaggriculture Local Arena", file=f)
        print("========================", file=f)
        print(file=f)
        print("Confirmed Local Bradley-Terry (relative; NOT Kaggle live score)", file=f)
        for i, (name, rating) in enumerate(ranked, 1):
            print(f"{i:>2}. {name:<32} {rating:+8.1f}", file=f)
        print(file=f)
        print("Non-transitive cycles (>55% each edge)", file=f)
        if not cycles:
            print("none detected", file=f)
        for x, y, z, sxy, syz, szx in cycles:
            print(
                f"{x} > {y} ({sxy:.1%}), "
                f"{y} > {z} ({syz:.1%}), "
                f"{z} > {x} ({szx:.1%})",
                file=f,
            )


def print_matrix(names: List[str], pairwise):
    if not names:
        return
    width = max(8, min(18, max(len(n) for n in names) + 1))
    short = {n: (n[:width-1]) for n in names}

    print("\n=== Pairwise match score (row vs column) ===")
    print(" " * width + "".join(f"{short[n]:>{width}}" for n in names))
    for a in names:
        cells = []
        for b in names:
            if a == b:
                cell = "-"
            else:
                s = pair_score(pairwise, a, b)
                cell = "NA" if s is None else f"{s:.0%}"
            cells.append(f"{cell:>{width}}")
        print(f"{short[a]:<{width}}" + "".join(cells))


def main():
    ap = argparse.ArgumentParser(description="Kaggriculture local meta arena")
    ap.add_argument("agents", nargs="*", help="追加agent .py path")
    ap.add_argument("--panel-size", type=int, default=5)
    ap.add_argument("--top", type=int, default=4, help="screen後にconfirmへ進める上位候補数")
    ap.add_argument("--screen-seeds", type=int, default=2)
    ap.add_argument("--confirm-seeds", type=int, default=6)
    ap.add_argument("--include-root-agents", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="各ゲーム行を省略")
    args = ap.parse_args()

    paths = discover_paths(args.agents, args.include_root_agents)
    agents, duplicates = build_agents(paths)

    if len(agents) < 2:
        print("❌ 比較可能なagentが2体未満です。")
        print("   public_agents/elite や candidates 以下、または引数で .py を指定してください。")
        sys.exit(2)

    e11 = find_e11(agents)
    panel = choose_panel(agents, e11, max(2, args.panel_size))

    print("=== Kaggriculture Local Arena ===")
    print(f"discovered unique agents : {len(agents)}")
    print(f"duplicate byte-identical : {len(duplicates)}")
    print(f"E11                      : {e11.name if e11 else 'not found'}")
    print("panel                     : " + ", ".join(a.name for a in panel))
    print()

    print("Agents:")
    for a in agents:
        flag = " [E11]" if e11 and a.sha256 == e11.sha256 else ""
        print(f"  {a.name:<34} {a.sha256[:12]}  {a.path}{flag}")

    if duplicates:
        print("\nSHA duplicates (skip):")
        for dup, original in duplicates[:20]:
            print(f"  {dup} == {original}")
        if len(duplicates) > 20:
            print(f"  ... +{len(duplicates)-20}")

    if args.dry_run:
        print("\n✅ dry-run完了。対戦はしていません。")
        return

    games: List[Game] = []
    panel_names = {a.name for a in panel}

    # ---------- Stage 1: screen ----------
    print("\n=== Stage 1: META SCREEN ===")
    screen_seeds = list(range(SCREEN_SEED_BASE, SCREEN_SEED_BASE + args.screen_seeds))
    candidates = [a for a in agents if a.name not in panel_names]

    if not candidates:
        # 全員がpanelなら、その中を候補扱いにしてconfirmへ
        candidates = list(agents)

    for cand in candidates:
        for opp in panel:
            if cand.sha256 == opp.sha256:
                continue
            play_series(cand, opp, screen_seeds, "screen", games, quiet=args.quiet)

    screen_rows = []
    for cand in candidates:
        score, n, errs = score_agent_vs_panel(games, cand.name, panel_names)
        screen_rows.append((cand, score, n, errs))

    # エラー候補は上位に上げない
    screen_rows.sort(key=lambda r: (r[3] == 0, r[1], r[2]), reverse=True)

    print("\n=== Screen ranking ===")
    for i, (a, score, n, errs) in enumerate(screen_rows, 1):
        s = "NA" if not math.isfinite(score) else f"{score:.1%}"
        verdict = "INVALID" if errs else ""
        print(f"{i:>2}. {a.name:<32} score={s:>6} n={n:<3} errors={errs:<2} {verdict}")

    finalists = [a for a, score, n, errs in screen_rows if errs == 0 and n > 0][: args.top]

    # confirm は panel + finalist。hashは既にunique
    confirm_agents: List[Agent] = []
    for a in panel + finalists:
        if a not in confirm_agents:
            confirm_agents.append(a)

    # 最低でも2体
    if len(confirm_agents) < 2:
        confirm_agents = agents[: min(len(agents), max(2, args.top + 1))]

    # ---------- Stage 2: confirm round robin ----------
    print("\n=== Stage 2: CONFIRM ROUND ROBIN ===")
    print("agents: " + ", ".join(a.name for a in confirm_agents))
    confirm_seeds = list(range(CONFIRM_SEED_BASE, CONFIRM_SEED_BASE + args.confirm_seeds))

    for a, b in itertools.combinations(confirm_agents, 2):
        play_series(a, b, confirm_seeds, "confirm", games, quiet=args.quiet)

    confirm_names = [a.name for a in confirm_agents]
    confirm_pairwise = aggregate_pairwise(
        [g for g in games if g.stage == "confirm"],
        set(confirm_names),
    )

    # invalid episodeを持つagentはBT順位から除外
    errs = error_counts([g for g in games if g.stage == "confirm"])
    valid_names = [n for n in confirm_names if errs.get(n, 0) == 0]

    bt = fit_bradley_terry(valid_names, confirm_pairwise)
    ranked = sorted(bt.items(), key=lambda kv: kv[1], reverse=True)

    print_matrix(valid_names, confirm_pairwise)

    print("\n=== Local Bradley-Terry ===")
    print("(relative rating; Kaggle live scoreとは別物)")
    for i, (name, rating) in enumerate(ranked, 1):
        print(f"{i:>2}. {name:<32} {rating:+8.1f}")

    if errs:
        print("\n=== INVALID / needs review ===")
        for name, n in sorted(errs.items(), key=lambda kv: kv[1], reverse=True):
            print(f"  {name:<32} invalid episodes={n}")

    cycles = find_cycles(valid_names, confirm_pairwise, threshold=0.55)
    print("\n=== Non-transitive cycles (>55% each edge) ===")
    if not cycles:
        print("  none detected")
    else:
        for x, y, z, sxy, syz, szx in cycles:
            print(
                f"  {x} > {y} ({sxy:.1%}), "
                f"{y} > {z} ({syz:.1%}), "
                f"{z} > {x} ({szx:.1%})"
            )

    write_outputs(agents, games, confirm_names, bt, confirm_pairwise, cycles)

    print("\n=== DONE ===")
    print(f"結果保存: {OUTDIR}")
    print("  summary.txt   ← まずこれ")
    print("  bt.csv        ← Local BT")
    print("  pairwise.csv  ← 相性")
    print("  games.csv     ← 全試合")
    print()
    if ranked:
        print(f"Local BT 1位: {ranked[0][0]}")
    if e11 and e11.name in bt:
        rank = [n for n, _ in ranked].index(e11.name) + 1
        print(f"E11 rank      : {rank}/{len(ranked)}")
    print()
    print("次にChatGPTへ arena_results/summary.txt を貼ればよいです。")


if __name__ == "__main__":
    main()
