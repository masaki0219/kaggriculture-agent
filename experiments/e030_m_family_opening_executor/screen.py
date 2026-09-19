#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import importlib
import json
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
DATA = HERE / "results.json"
REPORT = HERE / "results.md"
PREFIX = "@@E30@@"
CHECKPOINTS = (23,47,71,143,167,215,239,287)

MODULES = {
    "e30": "agent_e30_m_family_opening_executor",
    "e21": "agent_e21_tetsu_market_v23",
}
ELITE = {"aurax7_v7": "aurax7_v7_current"}
CALLABLES = (
    "agent","kaggle_submission_agent","submission_agent",
    "melon_maxxer","policy","kaggriculture_e776_agent",
)

def resolve(name):
    p = str(BUNDLE)
    if p not in sys.path:
        sys.path.insert(0,p)
    if name in MODULES:
        mod = importlib.import_module(MODULES[name])
        for k in CALLABLES:
            fn = getattr(mod,k,None)
            if callable(fn):
                return fn
        raise RuntimeError(name)
    from elite_runtime import load_agent, call_agent
    base = load_agent(ELITE[name])
    return lambda obs, configuration=None: call_agent(base, obs, configuration)

def diag(env, seat, step):
    st = env.steps[min(step,len(env.steps)-1)][seat]
    obs = st.get("observation") or {}
    farm = (obs.get("farms") or [{}])[seat]
    crops=Counter()
    animals=Counter()
    structures=Counter()
    for row in farm.get("tiles") or []:
        if not isinstance(row,list):
            continue
        for tile in row:
            if not isinstance(tile,dict):
                continue
            if tile.get("kind")=="PLANT" and tile.get("crop"):
                crops[tile["crop"]] += 1
            if tile.get("animal"):
                animals[tile["animal"]] += 1
            if tile.get("kind") in ("PASTURE","COOP"):
                structures[tile["kind"]] += 1
    return {
        "money": float(farm.get("money",0) or 0),
        "hands": len(farm.get("hands") or []),
        "quadrants": len(farm.get("unlocked_quadrants") or []),
        "crops": sum(crops.values()),
        "structures": sum(structures.values()),
        "animals": sum(animals.values()),
        "crop_detail": dict(crops),
    }

def child(args):
    from kaggle_environments import make
    a = resolve("e30")
    b = resolve(args.opponent)
    agents = [a,b] if args.seat==0 else [b,a]
    env = make(
        "kaggriculture",
        configuration={"episodeSteps":720,"seed":args.seed},
        debug=False,
    )
    env.run(agents)
    ra = float(env.steps[-1][args.seat].get("reward"))
    rb = float(env.steps[-1][1-args.seat].get("reward"))
    print(PREFIX + json.dumps({
        "opponent":args.opponent,
        "seed":args.seed,
        "seat":args.seat,
        "reward":ra,
        "opponent_reward":rb,
        "trajectory":{str(s):diag(env,args.seat,s) for s in CHECKPOINTS},
    }, ensure_ascii=False))

def run_one(opp,seed,seat):
    p = subprocess.run(
        [
            sys.executable,str(Path(__file__).resolve()),
            "--child","--opponent",opp,
            "--seed",str(seed),"--seat",str(seat),
        ],
        cwd=str(ROOT),text=True,capture_output=True,
    )
    for line in p.stdout.splitlines():
        if line.startswith(PREFIX):
            return json.loads(line[len(PREFIX):])
    return {
        "opponent":opp,"seed":seed,"seat":seat,
        "error":(p.stderr or p.stdout or "no result")[-5000:],
    }

def run_block(seeds):
    rows=[]
    total=len(seeds)*4
    n=0
    for opp in ("e21","aurax7_v7"):
        for seed in seeds:
            for seat in (0,1):
                n += 1
                print(f"[{n}/{total}] E30 vs {opp} seed={seed} seat={seat}", flush=True)
                rows.append(run_one(opp,seed,seat))
    return rows

def meds(rows):
    valid=[r for r in rows if "error" not in r]
    out={}
    for s in CHECKPOINTS:
        xs=[r["trajectory"][str(s)] for r in valid]
        if not xs:
            continue
        out[str(s)] = {
            k:statistics.median(x[k] for x in xs)
            for k in ("money","hands","quadrants","crops","structures","animals")
        }
    return out

def val(m,s,k):
    return m.get(str(s),{}).get(k,0)

def opening_ok(m,errors):
    return (
        not errors
        and 13 <= val(m,23,"crops") <= 18
        and val(m,23,"structures")==5
        and val(m,23,"animals")>=4
        and val(m,23,"hands")>=4
        and 17 <= val(m,47,"crops") <= 22
        and val(m,47,"structures")==5
        and val(m,47,"animals")>=4
        and val(m,47,"hands")>=4
        and 18 <= val(m,71,"crops") <= 22
        and val(m,71,"hands")>=5
        and 18 <= val(m,143,"crops") <= 24
    )

def mid_ok(m,errors):
    return (
        not errors
        and val(m,167,"crops")>=28 and val(m,167,"quadrants")>=2
        and val(m,215,"crops")>=33 and val(m,215,"quadrants")>=2
        and val(m,239,"crops")>=45 and val(m,239,"quadrants")>=3
        and val(m,287,"crops")>=50 and val(m,287,"quadrants")>=3
    )

def add_table(lines,m,steps):
    lines += [
        "| Step | Crops | Structures | Animals | Hands | Q | Money |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in steps:
        d=m.get(str(s),{})
        lines.append(
            f"| {s} | {d.get('crops','')} | {d.get('structures','')} | "
            f"{d.get('animals','')} | {d.get('hands','')} | "
            f"{d.get('quadrants','')} | {d.get('money','')} |"
        )

def parent(args):
    if not (BUNDLE/"agent_e30_m_family_opening_executor.py").exists():
        raise SystemExit("Run e30_builder.py first.")

    opening = run_block([args.seed_start,args.seed_start+1])
    oe=[r for r in opening if "error" in r]
    om=meds(opening)
    opass=opening_ok(om,oe)

    payload={
        "opening":opening,
        "opening_medians":om,
        "opening_pass":opass,
        "opening_errors":oe,
    }
    lines=[
        "# E30 Fidelity Screen",
        "",
        f"- Opening fidelity: **{'PASS' if opass else 'FAIL'}**",
        "",
        "## Opening medians",
        "",
    ]
    add_table(lines,om,(23,47,71,143))

    if not opass:
        payload["status"]="opening_failed"
        DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
        lines += [
            "",
            "Stop here. Do not run population W/L while opening fidelity fails.",
        ]
        REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("\n".join(lines))
        return

    mid = run_block([args.seed_start+10,args.seed_start+11,args.seed_start+12])
    me=[r for r in mid if "error" in r]
    mm=meds(mid)
    mpass=mid_ok(mm,me)
    payload.update({
        "status":"fidelity_pass" if mpass else "midgame_failed",
        "midgame":mid,
        "midgame_medians":mm,
        "midgame_pass":mpass,
        "midgame_errors":me,
    })
    DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    lines += [
        "",
        f"- Midgame fidelity: **{'PASS' if mpass else 'FAIL'}**",
        "",
        "## Midgame medians",
        "",
    ]
    add_table(lines,mm,(167,215,239,287))
    lines += ["","No population W/L screen was run."]
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed-start",type=int,default=31000)
    ap.add_argument("--child",action="store_true")
    ap.add_argument("--opponent")
    ap.add_argument("--seed",type=int)
    ap.add_argument("--seat",type=int,choices=(0,1))
    args=ap.parse_args()
    if args.child:
        child(args)
    else:
        parent(args)

if __name__=="__main__":
    main()
