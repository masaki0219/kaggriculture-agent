from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from statistics import mean
from kaggle_environments import make

ROOT = Path(__file__).resolve().parent
PUB = ROOT / "public_agents"
CACHE = ROOT / "e11_focused_cache.json"
PREFIX = "@@E11GAME@@"

CANDIDATES = {
    "e11": "agent_e11_prvsiyan_frontier",
    "e14_milk": "agent_e14_prvsiyan_milkguard",
    "e15_fert": "agent_e15_prvsiyan_fertguard",
    "e16_clone": "agent_e16_prvsiyan_cloneguard",
}

OPPONENTS = {
    "e2_boatlee29": ("module", "agent_e2_boatlee29"),
    "v15_kaito48": ("module", "agent_v15"),
    "qeinstein_champion": ("path", PUB / "qeinstein" / "scripts" / "champion_entry.py"),
    "qeinstein_candidate7": ("path", PUB / "qeinstein" / "scripts" / "candidate7_entry.py"),
}

def load_path(path: Path, unique: str):
    path = path.resolve()
    repo_root = path.parent.parent if path.parent.name == "scripts" else path.parent
    for p in (repo_root, repo_root / "src", path.parent):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
    import os
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
    for n in ("agent","kaggle_submission_agent","submission_agent"):
        fn = getattr(mod, n, None)
        if callable(fn):
            return fn
    raise AttributeError(path)

def resolve(kind, name):
    if kind == "candidate":
        return importlib.import_module(CANDIDATES[name]).agent
    typ, ref = OPPONENTS[name]
    if typ == "module":
        return importlib.import_module(ref).agent
    return load_path(Path(ref), f"_focus_{name}")

def child(args):
    try:
        left = resolve(args.lk, args.left)
        right = resolve(args.rk, args.right)
        agents = [left, right] if not args.swap else [right, left]
        env = make(
            "kaggriculture",
            configuration={"episodeSteps":720, "seed":args.seed},
            debug=False,
        )
        env.run(agents)
        f = env.steps[-1]
        a, b = float(f[0].reward), float(f[1].reward)
        if args.swap:
            a, b = b, a
        print(PREFIX + json.dumps({
            "left":args.left, "right":args.right,
            "seed":args.seed, "swap":args.swap,
            "a":a, "b":b,
            "r":"W" if a>b else "L" if a<b else "D",
            "m":a-b,
        }))
    except Exception as e:
        print(PREFIX + json.dumps({"error":f"{type(e).__name__}: {e}"}))

def load_cache():
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return {}

def save_cache(c):
    CACHE.write_text(json.dumps(c,indent=2),encoding="utf-8")

def run_game(lk,l,rk,r,seed,swap,cache):
    k=f"{lk}|{l}|{rk}|{r}|{seed}|{int(swap)}"
    if k in cache and "error" not in cache[k]:
        return cache[k]
    cmd=[
        sys.executable,str(Path(__file__).resolve()),
        "--lk",lk,"--left",l,"--rk",rk,"--right",r,
        "--seed",str(seed)
    ]
    if swap: cmd.append("--swap")
    p=subprocess.run(cmd,cwd=str(ROOT),text=True,capture_output=True)
    rec=None
    for line in p.stdout.splitlines():
        if line.startswith(PREFIX):
            rec=json.loads(line[len(PREFIX):])
    if rec is None:
        rec={"error":p.stderr[-1000:] or "no result"}
    cache[k]=rec
    save_cache(cache)
    return rec

def pair(lk,l,rk,r,seeds,cache):
    rows=[]
    for seed in seeds:
        for swap in (False,True):
            rec=run_game(lk,l,rk,r,seed,swap,cache)
            if "error" in rec:
                return rows,rec["error"]
            rows.append(rec)
    return rows,None

def summary(rows):
    w=sum(x["r"]=="W" for x in rows)
    d=sum(x["r"]=="D" for x in rows)
    l=sum(x["r"]=="L" for x in rows)
    return w,d,l,mean(x["m"] for x in rows) if rows else 0

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seeds",type=int,default=12)
    ap.add_argument("--seed-start",type=int,default=10000)
    ap.add_argument("--lk")
    ap.add_argument("--left")
    ap.add_argument("--rk")
    ap.add_argument("--right")
    ap.add_argument("--seed",type=int)
    ap.add_argument("--swap",action="store_true")
    args=ap.parse_args()
    if args.lk:
        child(args); return

    seeds=range(args.seed_start,args.seed_start+args.seeds)
    cache=load_cache()
    results={}
    names=list(CANDIDATES)

    print("========== E11 FAMILY ROUND ROBIN ==========")
    for i,a in enumerate(names):
        for b in names[i+1:]:
            print(f"\n=== {a} vs {b} ===",flush=True)
            rows,err=pair("candidate",a,"candidate",b,seeds,cache)
            if err:
                print("[SKIP]",err); continue
            s=summary(rows)
            print(f"{s[0]}-{s[1]}-{s[2]} margin={s[3]:+.0f}")
            results[f"{a}__{b}"]=s

    print("\n========== STRONG HOLDOUTS ==========")
    for a in names:
        for h in OPPONENTS:
            print(f"\n=== {a} vs {h} ===",flush=True)
            rows,err=pair("candidate",a,"opponent",h,seeds,cache)
            if err:
                print("[SKIP]",err); continue
            s=summary(rows)
            print(f"{s[0]}-{s[1]}-{s[2]} margin={s[3]:+.0f}")
            results[f"{a}__{h}"]=s

    print("\n========== DECISION SUMMARY ==========")
    for a in names:
        wr=dr=lr=0
        margins=[]
        for k,s in results.items():
            if k.startswith(a+"__"):
                wr+=s[0]; dr+=s[1]; lr+=s[2]; margins.append(s[3])
            elif k.endswith("__"+a):
                wr+=s[2]; dr+=s[1]; lr+=s[0]; margins.append(-s[3])
        avg=mean(margins) if margins else 0
        print(f"{a:12s} total={wr}-{dr}-{lr} pairMeanMargin={avg:+.0f}")

    Path("e11_focused_results.json").write_text(
        json.dumps(results,ensure_ascii=False,indent=2),
        encoding="utf-8",
    )

if __name__=="__main__":
    main()
