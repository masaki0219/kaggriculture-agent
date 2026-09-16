"""
Elite Kaggriculture arena.

Design:
- one GAME per fresh subprocess -> stateful public agents cannot leak state
  across seeds/games
- both seats for every seed
- cache after every single game -> safe to interrupt/resume
- primary metric W/D/L; reward margin is diagnostic
- fresh seed ranges by default (not 0..9)

Stage 1:
    python elite_arena.py
Stage 2 / deeper:
    python elite_arena.py --seeds 20 --seed-start 5000 --fresh

Optional candidate subset:
    python elite_arena.py --candidates e1,e2,e3,e5,e6
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
from pathlib import Path
import subprocess
import sys
from statistics import mean

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent
PUB = ROOT / "public_agents"

CANDIDATES = {
    "e1_kaito58": "agent_e1_kaito58",
    "e2_boatlee29": "agent_e2_boatlee29",
    "e3_shape_top10": "agent_e3_shape_top10",
    "e4_adaptive_route_v2": "agent_e4_adaptive_route_v2",
    "e5_kaito58_shift1": "agent_e5_kaito58_shift1",
    "e6_boatlee29_guard": "agent_e6_boatlee29_guard",
    "e7_tetsu_shape": "agent_e7_tetsu_shape",
    "e8_farming_v4": "agent_e8_farming_v4",
    "e9_boatlee29_tomato": "agent_e9_boatlee29_tomato",
    "e10_kaito27_current": "agent_e10_kaito27_current",
    "e11_prvsiyan_frontier": "agent_e11_prvsiyan_frontier",
    "e12_kaito43_current": "agent_e12_kaito43_current",
    "e13_kaito27_guard": "agent_e13_kaito27_guard",
}

HOLDOUTS = {
    "v15_kaito48": ("module", "agent_v15"),
    "qeinstein_champion": ("path", PUB / "qeinstein" / "scripts" / "champion_entry.py"),
    "qeinstein_candidate7": ("path", PUB / "qeinstein" / "scripts" / "candidate7_entry.py"),
    "qeinstein_portfolio": ("path", PUB / "qeinstein" / "scripts" / "frontier_portfolio_entry.py"),
}

CACHE = ROOT / "elite_arena_cache.json"
PREFIX = "@@GAME@@"

def _load_path(path: Path, unique: str):
    import importlib.util, os
    path = path.resolve()
    repo_root = path.parent.parent if path.parent.name == "scripts" else path.parent
    for p in (repo_root, repo_root / "src", path.parent):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
    old = Path.cwd()
    try:
        os.chdir(repo_root)
        spec = importlib.util.spec_from_file_location(unique, path)
        if spec is None or spec.loader is None:
            raise ImportError(path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[unique] = mod
        spec.loader.exec_module(mod)
    finally:
        os.chdir(old)
    for n in ("agent", "kaggle_submission_agent", "submission_agent",
              "c94_submission_agent", "c95_submission_agent"):
        fn = getattr(mod, n, None)
        if callable(fn):
            return fn
    raise AttributeError(f"No agent callable in {path}")

def resolve(kind: str, name: str):
    if kind == "candidate":
        mod = importlib.import_module(CANDIDATES[name])
        return mod.agent
    if kind == "holdout":
        typ, ref = HOLDOUTS[name]
        if typ == "module":
            return importlib.import_module(str(ref)).agent
        return _load_path(Path(ref), f"_hold_{name}")
    raise ValueError(kind)


def preflight_candidates(candidates):
    """Fail once, clearly, before launching any games."""
    import importlib.util

    missing = []
    for name in candidates:
        module_name = CANDIDATES[name]
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            missing.append(f"{name}: wrapper module {module_name}.py missing")
            continue

        # Map wrappers to their required downloaded public artifacts.
        required = {
            "e1_kaito58": "kaito58",
            "e2_boatlee29": "boatlee29",
            "e3_shape_top10": "shape_top10",
            "e4_adaptive_route_v2": "adaptive_route_v2",
            "e5_kaito58_shift1": "kaito58",
            "e6_boatlee29_guard": "boatlee29",
            "e7_tetsu_shape": "tetsu_shape",
            "e8_farming_v4": "farming_v4",
            "e9_boatlee29_tomato": "boatlee29",
            "e10_kaito27_current": "kaito27_current",
            "e11_prvsiyan_frontier": "prvsiyan_frontier",
            "e12_kaito43_current": "kaito43_current",
            "e13_kaito27_guard": "kaito27_current",
        }.get(name)

        if required:
            marker = ROOT / "public_agents" / "elite" / required / "entrypoint.txt"
            if not marker.exists():
                missing.append(
                    f"{name}: missing {marker.relative_to(ROOT)}"
                )

    # Holdouts required by the arena.
    for h, (typ, ref) in HOLDOUTS.items():
        if typ == "path" and not Path(ref).exists():
            missing.append(f"holdout {h}: missing {Path(ref)}")
        elif typ == "module" and importlib.util.find_spec(str(ref)) is None:
            missing.append(f"holdout {h}: module {ref}.py missing")

    if missing:
        lines = "\\n".join(f"  - {x}" for x in missing)
        raise SystemExit(
            "\\nElite arena preflight failed. Nothing was run.\\n"
            "Missing prerequisites:\\n"
            f"{lines}\\n\\n"
            "First finish artifact setup:\\n"
            "    kaggle auth login\\n"
            "    python setup_elite_candidates.py\\n\\n"
            "Also run the arena from your MAIN Kaggle project directory, "
            "or copy/symlink the existing public_agents and agent_v15.py "
            "into this bundle directory.\\n"
        )

def child_game(args):
    left = resolve(args.left_kind, args.left)
    right = resolve(args.right_kind, args.right)

    agents = [left, right]
    if args.swap:
        agents = [right, left]

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    env.run(agents)
    f = env.steps[-1]
    r0, r1 = float(f[0].reward), float(f[1].reward)

    if args.swap:
        rl, rr = r1, r0
    else:
        rl, rr = r0, r1

    rec = {
        "left_kind": args.left_kind,
        "left": args.left,
        "right_kind": args.right_kind,
        "right": args.right,
        "seed": args.seed,
        "swap": bool(args.swap),
        "left_reward": rl,
        "right_reward": rr,
        "result": "W" if rl > rr else "L" if rl < rr else "D",
        "margin": rl - rr,
    }
    print(PREFIX + json.dumps(rec, ensure_ascii=False))

def load_cache(fresh=False):
    if fresh or not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_cache(c):
    CACHE.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")

def game_key(lk,l,rk,r,seed,swap):
    return f"{lk}|{l}|{rk}|{r}|{seed}|{int(swap)}"

def launch(lk,l,rk,r,seed,swap,cache):
    key = game_key(lk,l,rk,r,seed,swap)
    if key in cache:
        return cache[key]

    cmd = [
        sys.executable, str(Path(__file__).resolve()),
        "--child",
        "--left-kind", lk, "--left", l,
        "--right-kind", rk, "--right", r,
        "--seed", str(seed),
    ]
    if swap:
        cmd.append("--swap")

    p = subprocess.run(cmd, cwd=str(ROOT), text=True,
                       capture_output=True)
    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        rec = {"error": f"exit {p.returncode}", "stdout": p.stdout[-1000:],
               "stderr": p.stderr[-2000:]}
    else:
        rec = None
        for line in p.stdout.splitlines():
            if line.startswith(PREFIX):
                rec = json.loads(line[len(PREFIX):])
        if rec is None:
            rec = {"error": "no result"}

    cache[key] = rec
    save_cache(cache)
    return rec

def pair_rows(lk,l,rk,r,seeds,cache):
    rows = []
    for seed in seeds:
        for swap in (False, True):
            rec = launch(lk,l,rk,r,seed,swap,cache)
            if "error" not in rec:
                rows.append(rec)
    return rows

def summary(rows):
    w = sum(r["result"]=="W" for r in rows)
    d = sum(r["result"]=="D" for r in rows)
    l = sum(r["result"]=="L" for r in rows)
    n = len(rows)
    return {
        "W":w,"D":d,"L":l,
        "score": (w+0.5*d)/n if n else 0,
        "margin": mean(r["margin"] for r in rows) if rows else 0,
    }

def bt_fit(all_pair_rows):
    # Simple MM Bradley-Terry; draws = half-win.
    nodes=set()
    wins={}
    games={}
    for (a,b), rows in all_pair_rows.items():
        s=summary(rows)
        nodes.update((a,b))
        wa=s["W"]+0.5*s["D"]
        wb=s["L"]+0.5*s["D"]
        wins[a]=wins.get(a,0)+wa
        wins[b]=wins.get(b,0)+wb
        games[(a,b)]=len(rows)
    nodes=sorted(nodes)
    if not nodes:
        return {}
    strength={n:1.0 for n in nodes}
    for _ in range(3000):
        new={}
        for i in nodes:
            wi=wins.get(i,0)+0.5
            den=0.0
            for (a,b),n in games.items():
                if i==a:
                    j=b
                elif i==b:
                    j=a
                else:
                    continue
                den += (n+1.0)/(strength[i]+strength[j])
            new[i]=max(1e-12, wi/max(den,1e-12))
        gm=math.exp(sum(math.log(v) for v in new.values())/len(new))
        new={k:v/gm for k,v in new.items()}
        if max(abs(math.log(new[k])-math.log(strength[k])) for k in nodes)<1e-9:
            strength=new; break
        strength=new
    return {k:1500+400*math.log10(v) for k,v in strength.items()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seeds",type=int,default=6)
    ap.add_argument("--seed-start",type=int,default=1000)
    ap.add_argument("--candidates")
    ap.add_argument("--fresh",action="store_true")

    ap.add_argument("--child",action="store_true")
    ap.add_argument("--left-kind")
    ap.add_argument("--left")
    ap.add_argument("--right-kind")
    ap.add_argument("--right")
    ap.add_argument("--seed",type=int)
    ap.add_argument("--swap",action="store_true")
    args=ap.parse_args()

    if args.child:
        child_game(args); return

    candidates=list(CANDIDATES)
    if args.candidates:
        candidates=[x.strip() for x in args.candidates.split(",") if x.strip()]
        bad=[x for x in candidates if x not in CANDIDATES]
        if bad: raise SystemExit(f"unknown candidates: {bad}")

    preflight_candidates(candidates)

    seeds=list(range(args.seed_start,args.seed_start+args.seeds))
    cache=load_cache(args.fresh)
    pair_data={}

    # Candidate round robin.
    for i,a in enumerate(candidates):
        for b in candidates[i+1:]:
            print(f"\n=== {a} vs {b} ===", flush=True)
            rows=pair_rows("candidate",a,"candidate",b,seeds,cache)
            s=summary(rows)
            print(f"{s['W']}-{s['D']}-{s['L']} score={s['score']:.1%} margin={s['margin']:+.0f}")
            pair_data[(f"C:{a}",f"C:{b}")]=rows

    # Holdouts.
    for a in candidates:
        for h in HOLDOUTS:
            print(f"\n=== {a} vs {h} ===", flush=True)
            rows=pair_rows("candidate",a,"holdout",h,seeds,cache)
            s=summary(rows)
            print(f"{s['W']}-{s['D']}-{s['L']} score={s['score']:.1%} margin={s['margin']:+.0f}")
            pair_data[(f"C:{a}",f"H:{h}")]=rows

    bt=bt_fit(pair_data)
    stats=[]
    for a in candidates:
        node=f"C:{a}"
        rows=[]
        hold=[]
        for (x,y),rs in pair_data.items():
            if x==node:
                rows += rs
                if y.startswith("H:"): hold += rs
            elif y==node:
                # reverse candidate-v-candidate perspective
                rev=[]
                for r in rs:
                    rr=dict(r)
                    rr["result"]="W" if r["result"]=="L" else "L" if r["result"]=="W" else "D"
                    rr["margin"]=-r["margin"]
                    rev.append(rr)
                rows += rev
        ss=summary(rows)
        hs=summary(hold)
        stats.append((bt.get(node,-1e9),hs["score"],ss["score"],a,ss,hs))

    stats.sort(reverse=True)
    print("\n================ ELITE RANKING ================")
    for i,(rating,hscore,score,a,ss,hs) in enumerate(stats,1):
        print(
            f"{i:2d} {a:26s} BT={rating:7.1f} "
            f"all={ss['W']}-{ss['D']}-{ss['L']} {score:6.1%} "
            f"holdout={hs['W']}-{hs['D']}-{hs['L']} {hscore:6.1%}"
        )

    report={
        "seed_start":args.seed_start,
        "seeds":args.seeds,
        "ranking":[
            {"candidate":a,"bt":rating,"all":ss,"holdout":hs}
            for rating,hscore,score,a,ss,hs in stats
        ],
    }
    Path("elite_arena_results.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8"
    )
    print("\nWrote elite_arena_results.json")

if __name__=="__main__":
    main()
