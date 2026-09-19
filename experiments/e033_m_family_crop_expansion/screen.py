#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter
from pathlib import Path
import importlib, json, statistics, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
sys.path.insert(0, str(BUNDLE))
PREFIX = "@@E33@@"
CHECKPOINTS = (23,47,71,143,167,215,239,287,719)


def load_module(name):
    mod = importlib.import_module(name)
    for k in ("agent","melon_maxxer","policy"):
        fn = getattr(mod,k,None)
        if callable(fn):
            return fn
    raise RuntimeError(name)


def load_elite():
    from elite_runtime import load_agent, call_agent
    base = load_agent("aurax7_v7_current")
    return lambda obs, configuration=None: call_agent(base, obs, configuration)


def resolve(name):
    if name == "e33": return load_module("agent_e33_m_family_crop_expansion")
    if name == "e21": return load_module("agent_e21_tetsu_market_v23")
    if name == "aurax": return load_elite()
    raise KeyError(name)


def diag(env, seat, step):
    st = env.steps[min(step, len(env.steps)-1)][seat]
    obs = st.get("observation") or {}
    farm = (obs.get("farms") or [{}])[seat]
    crops=Counter(); structures=Counter(); animals=Counter()
    for row in farm.get("tiles") or []:
        if not isinstance(row,list): continue
        for tile in row:
            if not isinstance(tile,dict): continue
            if tile.get("kind") == "PLANT" and tile.get("crop"): crops[str(tile["crop"])]+=1
            if tile.get("kind") in ("PASTURE","COOP"): structures[str(tile["kind"])]+=1
            if tile.get("animal"): animals[str(tile["animal"])]+=1
    return {
        "crops":sum(crops.values()), "structures":sum(structures.values()),
        "animals":sum(animals.values()), "hands":len(farm.get("hands") or []),
        "q":len(farm.get("unlocked_quadrants") or []), "money":float(farm.get("money",0) or 0),
    }


def child(opp, seed, seat):
    from kaggle_environments import make
    a=resolve("e33"); b=resolve(opp); agents=[a,b] if seat==0 else [b,a]
    env=make("kaggriculture", configuration={"episodeSteps":720,"seed":seed}, debug=False)
    env.run(agents)
    ar=float(env.steps[-1][seat].get("reward")); br=float(env.steps[-1][1-seat].get("reward"))
    print(PREFIX+json.dumps({
        "opp":opp,"seed":seed,"seat":seat,
        "outcome":"W" if ar>br else "L" if ar<br else "D",
        "reward":ar,"opp_reward":br,
        "traj":{str(s):diag(env,seat,s) for s in CHECKPOINTS},
    }))


def run_one(opp, seed, seat):
    p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--child",opp,str(seed),str(seat)],
                     cwd=str(ROOT),text=True,capture_output=True)
    for line in p.stdout.splitlines():
        if line.startswith(PREFIX): return json.loads(line[len(PREFIX):])
    return {"error":(p.stderr or p.stdout or "no output")[-4000:]}


def main():
    if len(sys.argv)==5 and sys.argv[1]=="--child":
        child(sys.argv[2],int(sys.argv[3]),int(sys.argv[4])); return

    rows=[]; seeds=(35000,35001,35002); n=0; total=12
    for opp in ("e21","aurax"):
        for seed in seeds:
            for seat in (0,1):
                n+=1; print(f"[{n}/{total}] E33 vs {opp} seed={seed} seat={seat}",flush=True)
                rows.append(run_one(opp,seed,seat))

    errs=[r for r in rows if "error" in r]
    if errs:
        print(errs[0]["error"]); raise SystemExit(2)

    print("\n# E33 Fidelity\n")
    print("| Step | Crops | Structures | Animals | Hands | Q | Money |")
    print("|---:|---:|---:|---:|---:|---:|---:|")
    for s in CHECKPOINTS:
        vals=[r["traj"][str(s)] for r in rows]
        d={k:statistics.median(v[k] for v in vals) for k in ("crops","structures","animals","hands","q","money")}
        print(f"| {s} | {d['crops']} | {d['structures']} | {d['animals']} | {d['hands']} | {d['q']} | {d['money']} |")

    c=Counter(r["outcome"] for r in rows)
    print(f"\nDiagnostic W-D-L: {c['W']}-{c['D']}-{c['L']}")
    print("Median reward:",statistics.median(r["reward"] for r in rows))
    print("\nReference: 167 crops33/Q2, 215 crops38/Q2, 239 crops53/Q3, 287 crops58.5/Q3.")
    print("If midgame fidelity improves materially, next run a proper population panel. Otherwise stop M-family reconstruction.")


if __name__ == "__main__":
    main()
