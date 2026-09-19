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
REPORT = HERE / "results.md"
DATA = HERE / "results.json"
PREFIX = "@@E31FID@@"
CHECKPOINTS = (23,47,71,143,167,215,239,287)

MODULES = {
    "e31": "agent_e31_m_family_opening_scheduler",
    "e21": "agent_e21_tetsu_market_v23",
}
ELITE = {"aurax7_v7": "aurax7_v7_current"}
CALLABLES = (
    "agent","kaggle_submission_agent","submission_agent",
    "melon_maxxer","policy","kaggriculture_e776_agent",
)

def _bundle_path():
    p = str(BUNDLE)
    if p not in sys.path:
        sys.path.insert(0,p)

def _load_module(name):
    _bundle_path()
    mod = importlib.import_module(name)
    for key in CALLABLES:
        fn = getattr(mod,key,None)
        if callable(fn):
            return fn
    raise AttributeError(name)

def _load_elite(name):
    _bundle_path()
    from elite_runtime import load_agent, call_agent
    base = load_agent(name)
    def wrapped(obs, configuration=None):
        return call_agent(base, obs, configuration)
    return wrapped

def resolve(name):
    if name in MODULES:
        return _load_module(MODULES[name])
    if name in ELITE:
        return _load_elite(ELITE[name])
    raise KeyError(name)

def diag_at(env, seat, step):
    st = env.steps[min(step,len(env.steps)-1)][seat]
    obs = st.get("observation") or {}
    farm = (obs.get("farms") or [{}])[seat]
    crops=Counter(); animals=Counter(); structures=Counter()
    for row in farm.get("tiles") or []:
        if not isinstance(row,list):
            continue
        for tile in row:
            if not isinstance(tile,dict):
                continue
            if tile.get("kind")=="PLANT" and tile.get("crop"):
                crops[str(tile["crop"])] += 1
            if tile.get("animal"):
                animals[str(tile["animal"])] += 1
            if tile.get("kind") in ("PASTURE","COOP"):
                structures[str(tile["kind"])] += 1
    return {
        "step":step,
        "money":float(farm.get("money",0) or 0),
        "hands":len(farm.get("hands") or []),
        "quadrants":len(farm.get("unlocked_quadrants") or []),
        "crop_total":sum(crops.values()),
        "structure_total":sum(structures.values()),
        "animal_total":sum(animals.values()),
        "crops":dict(crops),
        "structures":dict(structures),
        "animals":dict(animals),
    }

def child(args):
    from kaggle_environments import make
    e31=resolve("e31")
    opp=resolve(args.opponent)
    agents=[e31,opp] if args.e31_seat==0 else [opp,e31]
    env=make("kaggriculture",configuration={"episodeSteps":720,"seed":args.seed},debug=False)
    env.run(agents)
    a=float(env.steps[-1][args.e31_seat].get("reward"))
    b=float(env.steps[-1][1-args.e31_seat].get("reward"))
    print(PREFIX+json.dumps({
        "opponent":args.opponent,
        "seed":args.seed,
        "e31_seat":args.e31_seat,
        "e31_reward":a,
        "opponent_reward":b,
        "outcome":"W" if a>b else "L" if a<b else "D",
        "trajectory":{str(s):diag_at(env,args.e31_seat,s) for s in CHECKPOINTS},
    },ensure_ascii=False))

def run_one(opponent,seed,seat):
    p=subprocess.run(
        [sys.executable,str(Path(__file__).resolve()),"--child",
         "--opponent",opponent,"--seed",str(seed),"--e31-seat",str(seat)],
        cwd=str(ROOT),text=True,capture_output=True,
    )
    for line in p.stdout.splitlines():
        if line.startswith(PREFIX):
            return json.loads(line[len(PREFIX):])
    return {
        "opponent":opponent,"seed":seed,"e31_seat":seat,
        "error":(p.stderr or p.stdout or "no result")[-5000:],
    }

def run_block(seeds):
    rows=[]
    opponents=("e21","aurax7_v7")
    total=len(seeds)*2*len(opponents)
    done=0
    for opp in opponents:
        for seed in seeds:
            for seat in (0,1):
                done+=1
                print(f"[{done}/{total}] E31 vs {opp} seed={seed} seat={seat}",flush=True)
                rows.append(run_one(opp,seed,seat))
    return rows

def medians(rows):
    valid=[r for r in rows if "error" not in r]
    out={}
    for s in CHECKPOINTS:
        vals=[r["trajectory"][str(s)] for r in valid]
        out[str(s)]={
            "money":statistics.median(v["money"] for v in vals),
            "hands":statistics.median(v["hands"] for v in vals),
            "quadrants":statistics.median(v["quadrants"] for v in vals),
            "crops":statistics.median(v["crop_total"] for v in vals),
            "structures":statistics.median(v["structure_total"] for v in vals),
            "animals":statistics.median(v["animal_total"] for v in vals),
        }
    return out

def at(m,s,k):
    return m.get(str(s),{}).get(k,0)

def opening_pass(m,errors):
    return (
        not errors
        and 13 <= at(m,23,"crops") <= 18
        and at(m,23,"structures")==5
        and at(m,23,"animals")>=4
        and at(m,23,"hands")>=4
        and 17 <= at(m,47,"crops") <= 22
        and at(m,47,"structures")==5
        and at(m,47,"animals")>=4
        and at(m,47,"hands")>=4
        and 18 <= at(m,71,"crops") <= 22
        and at(m,71,"structures")==5
        and at(m,71,"animals")>=4
        and at(m,71,"hands")>=5
        and 18 <= at(m,143,"crops") <= 24
        and at(m,143,"structures")==5
        and at(m,143,"animals")>=4
        and at(m,143,"hands")>=5
    )

def mid_pass(m,errors):
    return (
        not errors
        and at(m,167,"crops")>=28 and at(m,167,"structures")>=9
        and at(m,167,"animals")>=9 and at(m,167,"hands")>=7
        and at(m,167,"quadrants")>=2
        and at(m,215,"crops")>=33 and at(m,215,"structures")>=10
        and at(m,215,"animals")>=10 and at(m,215,"hands")>=8
        and at(m,215,"quadrants")>=2
        and at(m,239,"crops")>=45 and at(m,239,"structures")>=11
        and at(m,239,"animals")>=11 and at(m,239,"hands")>=9
        and at(m,239,"quadrants")>=3
        and at(m,287,"crops")>=50 and at(m,287,"structures")>=12
        and at(m,287,"animals")>=12 and at(m,287,"hands")>=10
        and at(m,287,"quadrants")>=3
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
    opening=run_block(list(range(args.seed_start,args.seed_start+2)))
    errors=[r for r in opening if "error" in r]
    om=medians(opening)
    opass=opening_pass(om,errors)

    payload={
        "status":"opening_pass" if opass else "opening_failed",
        "opening":opening,
        "opening_medians":om,
        "errors":errors,
    }

    lines=[
        "# E31 Fidelity Screen","",
        f"- Opening fidelity: **{'PASS' if opass else 'FAIL'}**","",
        "## Opening medians","",
    ]
    add_table(lines,om,(23,47,71,143))

    if not opass:
        lines += ["","Stop here. Do not run population W/L while opening fidelity fails."]
        REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
        DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
        print("\n".join(lines))
        raise SystemExit(2)

    mid=run_block(list(range(args.mid_seed_start,args.mid_seed_start+3)))
    mid_errors=[r for r in mid if "error" in r]
    mm=medians(mid)
    mpass=mid_pass(mm,mid_errors)

    payload.update({
        "status":"fidelity_pass" if mpass else "midgame_failed",
        "midgame":mid,
        "midgame_medians":mm,
        "midgame_errors":mid_errors,
    })
    DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")

    lines += ["","## Midgame medians",""]
    add_table(lines,mm,(167,215,239,287))
    lines += [
        "",
        f"- Midgame fidelity: **{'PASS' if mpass else 'FAIL'}**",
        "",
        "No population W/L screen is run here.",
    ]
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))

    if not mpass:
        raise SystemExit(3)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed-start",type=int,default=32000)
    ap.add_argument("--mid-seed-start",type=int,default=32010)
    ap.add_argument("--child",action="store_true")
    ap.add_argument("--opponent")
    ap.add_argument("--seed",type=int)
    ap.add_argument("--e31-seat",type=int,choices=(0,1))
    args=ap.parse_args()
    if args.child:
        child(args)
    else:
        parent(args)

if __name__=="__main__":
    main()
