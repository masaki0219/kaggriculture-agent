#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter
from pathlib import Path
import importlib, json, math, re, statistics, subprocess, sys, zipfile

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
CORPUS = ROOT / "data" / "corpora" / "2026-09-18" / "m_family.zip"
sys.path.insert(0, str(BUNDLE))

M_FAMILY = {"Majkel1337","DSM","Orbital Terraformer","ymg_aq","QQ","Arda Ceylan","kwa"}
DAYS = tuple(range(6,12))
PREFIX = "@@E32MIDMECH@@"

def med(xs): return statistics.median(xs) if xs else 0.0
def quant(xs,q):
    if not xs: return 0.0
    xs=sorted(xs)
    if len(xs)==1: return float(xs[0])
    p=q*(len(xs)-1); lo=math.floor(p); hi=math.ceil(p)
    if lo==hi: return float(xs[lo])
    return xs[lo]*(hi-p)+xs[hi]*(p-lo)
def fmt_iqr(xs): return f"{med(xs):.1f}[{quant(xs,.25):.1f},{quant(xs,.75):.1f}]"

def team_from_path(name):
    parts=Path(name).parts
    if "replays" not in parts: return None
    i=parts.index("replays")
    if i+1>=len(parts): return None
    folder=parts[i+1]
    m=re.match(r"^\d+_(.+)$",folder)
    team=m.group(1) if m else folder
    return team if team in M_FAMILY else None

def team_names(replay):
    info=replay.get("info") or {}
    for key in ("TeamNames","teamNames","team_names","teams"):
        x=info.get(key)
        if isinstance(x,list):
            out=[]
            for v in x:
                if isinstance(v,str): out.append(v)
                elif isinstance(v,dict): out.append(str(v.get("name") or v.get("teamName") or ""))
                else: out.append(str(v))
            return out
    return []

def seat_for(replay,team):
    names=team_names(replay)
    for i,x in enumerate(names):
        if x==team: return i
    for i,x in enumerate(names):
        if x.casefold()==team.casefold(): return i
    return None

def obs_of(state):
    if not isinstance(state,dict): return {}
    obs=state.get("observation") or {}
    if isinstance(obs,str):
        try: obs=json.loads(obs)
        except Exception: return {}
    return obs if isinstance(obs,dict) else {}

def action_of(state):
    if not isinstance(state,dict): return {}
    a=state.get("action") or {}
    return a if isinstance(a,dict) else {}

def unit_op(cmd):
    if not isinstance(cmd,(list,tuple)) or not cmd: return ("NONE",None)
    op=str(cmd[0])
    if op in ("NORTH","SOUTH","EAST","WEST"): return ("MOVE",None)
    if op=="PLANT": return ("PLANT",str(cmd[1]) if len(cmd)>1 else "?")
    return (op,None)

def summarize_state(obs,seat):
    farms=obs.get("farms") or []
    farm=farms[seat] if isinstance(farms,list) and seat<len(farms) else {}
    crops=Counter(); animals=Counter(); structures=Counter()
    for row in farm.get("tiles") or []:
        if not isinstance(row,list): continue
        for tile in row:
            if not isinstance(tile,dict): continue
            if tile.get("kind")=="PLANT" and tile.get("crop"): crops[str(tile["crop"])]+=1
            if tile.get("animal"): animals[str(tile["animal"])]+=1
            if tile.get("kind") in ("PASTURE","COOP"): structures[str(tile["kind"])]+=1
    return {
        "crops":sum(crops.values()),"structures":sum(structures.values()),"animals":sum(animals.values()),
        "hands":len(farm.get("hands") or []),"quadrants":len(farm.get("unlocked_quadrants") or []),
        "money":float(farm.get("money",0) or 0),"crop_mix":dict(crops),"animal_mix":dict(animals),
    }

def analyze_states(states,seat,label):
    by={d:{"unit":Counter(),"market":Counter(),"plants":Counter(),"seed_buys":Counter(),"animal_buys":Counter()} for d in DAYS}
    last={}
    for i,step_states in enumerate(states):
        if not isinstance(step_states,list) or seat>=len(step_states): continue
        state=step_states[seat]; obs=obs_of(state); step=int(obs.get("step",i) or i); day=step//24
        if day not in by: continue
        last[day]=obs; a=action_of(state)
        units=[a.get("farmer")]+list(a.get("hands") or [])
        for cmd in units:
            op,item=unit_op(cmd); by[day]["unit"][op]+=1
            if op=="PLANT" and item: by[day]["plants"][item]+=1
        for order in a.get("market") or []:
            if not isinstance(order,(list,tuple)) or not order: continue
            op=str(order[0]); by[day]["market"][op]+=1
            item=str(order[1]) if len(order)>1 else None
            try: qty=int(order[2]) if len(order)>2 else 1
            except Exception: qty=1
            qty=max(1,qty)
            if op=="BUY_SEED" and item: by[day]["seed_buys"][item]+=qty
            elif op=="BUY_ANIMAL" and item: by[day]["animal_buys"][item]+=qty
    rows=[]
    for day in DAYS:
        d=by[day]; st=summarize_state(last[day],seat) if day in last else {}
        expansion=d["unit"]["PLANT"]+d["unit"]["BUILD_PASTURE"]+d["unit"]["BUILD_COOP"]+d["unit"]["DIG"]+d["unit"]["PLACE"]
        maintenance=d["unit"]["WATER"]+d["unit"]["FEED"]+d["unit"]["CARE"]+d["unit"]["COLLECT_FERTILIZER"]+d["unit"]["HARVEST"]+d["unit"]["PICKUP"]
        rows.append({
            "label":label,"day":day,"unit":dict(d["unit"]),"market":dict(d["market"]),
            "plants":dict(d["plants"]),"seed_buys":dict(d["seed_buys"]),"animal_buys":dict(d["animal_buys"]),
            "unit_total":sum(d["unit"].values()),"expansion_actions":expansion,"maintenance_actions":maintenance,
            "move_actions":d["unit"]["MOVE"],"pass_actions":d["unit"]["PASS"],"state":st,
        })
    return rows

def load_m_rows():
    rows=[]
    with zipfile.ZipFile(CORPUS,"r") as zf:
        for name in sorted(zf.namelist()):
            if "/replays/" not in name or not name.lower().endswith(".json"): continue
            team=team_from_path(name)
            if not team: continue
            replay=json.loads(zf.read(name)); seat=seat_for(replay,team)
            if seat is None: continue
            rows.extend(analyze_states(replay.get("steps") or [],seat,team))
    return rows

def load_e32():
    mod=importlib.import_module("agent_e32_m_family_opening_build_priority")
    for name in ("agent","melon_maxxer","policy"):
        fn=getattr(mod,name,None)
        if callable(fn): return fn
    raise RuntimeError("No E32 callable")

def load_opp(name):
    if name=="e21":
        mod=importlib.import_module("agent_e21_tetsu_market_v23")
        for k in ("agent","melon_maxxer","policy"):
            fn=getattr(mod,k,None)
            if callable(fn): return fn
    if name=="aurax":
        from elite_runtime import load_agent, call_agent
        base=load_agent("aurax7_v7_current")
        return lambda obs,configuration=None: call_agent(base,obs,configuration)
    raise RuntimeError(name)

def child(opponent,seed,seat):
    from kaggle_environments import make
    e32=load_e32(); opp=load_opp(opponent); agents=[e32,opp] if seat==0 else [opp,e32]
    env=make("kaggriculture",configuration={"episodeSteps":720,"seed":seed},debug=False)
    env.run(agents)
    print(PREFIX+json.dumps(analyze_states(env.steps,seat,f"e32:{opponent}:{seed}:s{seat}"),ensure_ascii=False))

def run_e32_rows():
    rows=[]
    for opponent in ("e21","aurax"):
        for seed in (34000,34001,34002):
            for seat in (0,1):
                print(f"E32 {opponent} seed={seed} seat={seat}",flush=True)
                p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--child",opponent,str(seed),str(seat)],
                                 cwd=str(ROOT),text=True,capture_output=True)
                for line in p.stdout.splitlines():
                    if line.startswith(PREFIX):
                        rows.extend(json.loads(line[len(PREFIX):])); break
                else:
                    raise RuntimeError((p.stderr or p.stdout or "no child output")[-4000:])
    return rows

def cget(d,k): return int((d or {}).get(k,0) or 0)

def print_core(m_rows,e_rows):
    print("# Midgame mechanism: M-family vs E32\n")
    print("Values are median[Q1,Q3] per player-day.\n")
    print("| Day | Source | End crops | Structures | Animals | Hands | Q | PLANT | BUILD | FEED | WATER | CARE | MOVE | BUY_SEED qty | BUY_ANIMAL qty | BUY_LAND |")
    print("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for day in DAYS:
        for name,rows in (("M",m_rows),("E32",e_rows)):
            ss=[r for r in rows if r["day"]==day]
            state=lambda k:[float((r["state"] or {}).get(k,0) or 0) for r in ss]
            plant=[cget(r["unit"],"PLANT") for r in ss]
            build=[cget(r["unit"],"BUILD_PASTURE")+cget(r["unit"],"BUILD_COOP") for r in ss]
            feed=[cget(r["unit"],"FEED") for r in ss]
            water=[cget(r["unit"],"WATER") for r in ss]
            care=[cget(r["unit"],"CARE") for r in ss]
            move=[cget(r["unit"],"MOVE") for r in ss]
            seed_qty=[sum((r["seed_buys"] or {}).values()) for r in ss]
            animal_qty=[sum((r["animal_buys"] or {}).values()) for r in ss]
            land=[cget(r["market"],"BUY_LAND") for r in ss]
            print(f"| {day} | {name} | {fmt_iqr(state('crops'))} | {fmt_iqr(state('structures'))} | "
                  f"{fmt_iqr(state('animals'))} | {fmt_iqr(state('hands'))} | {fmt_iqr(state('quadrants'))} | "
                  f"{fmt_iqr(plant)} | {fmt_iqr(build)} | {fmt_iqr(feed)} | {fmt_iqr(water)} | {fmt_iqr(care)} | "
                  f"{fmt_iqr(move)} | {fmt_iqr(seed_qty)} | {fmt_iqr(animal_qty)} | {fmt_iqr(land)} |")

def print_crop(m_rows,e_rows):
    crops=("MELON","STRAWBERRY","WHEAT","TOMATO","CARROT")
    print("\n## Planting / seed-purchase mix\n")
    print("| Day | Source | "+" | ".join("PLANT "+c for c in crops)+" | "+" | ".join("BUY "+c for c in crops)+" |")
    print("|---:|---|"+"|".join("---:" for _ in range(len(crops)*2))+"|")
    for day in DAYS:
        for name,rows in (("M",m_rows),("E32",e_rows)):
            ss=[r for r in rows if r["day"]==day]
            pc=[fmt_iqr([cget(r["plants"],c) for r in ss]) for c in crops]
            bc=[fmt_iqr([cget(r["seed_buys"],c) for r in ss]) for c in crops]
            print(f"| {day} | {name} | "+" | ".join(pc+bc)+" |")

def print_budget(m_rows,e_rows):
    print("\n## Worker-action budget\n")
    print("| Day | Source | Expansion | Maintenance | MOVE | PASS | Total | Expansion share | Maintenance share |")
    print("|---:|---|---:|---:|---:|---:|---:|---:|---:|")
    for day in DAYS:
        for name,rows in (("M",m_rows),("E32",e_rows)):
            ss=[r for r in rows if r["day"]==day]
            exp=[r["expansion_actions"] for r in ss]; maint=[r["maintenance_actions"] for r in ss]
            move=[r["move_actions"] for r in ss]; pas=[r["pass_actions"] for r in ss]; total=[r["unit_total"] for r in ss]
            es=[r["expansion_actions"]/r["unit_total"] if r["unit_total"] else 0 for r in ss]
            ms=[r["maintenance_actions"]/r["unit_total"] if r["unit_total"] else 0 for r in ss]
            print(f"| {day} | {name} | {fmt_iqr(exp)} | {fmt_iqr(maint)} | {fmt_iqr(move)} | "
                  f"{fmt_iqr(pas)} | {fmt_iqr(total)} | {100*med(es):.1f}% | {100*med(ms):.1f}% |")

def main():
    if len(sys.argv)==5 and sys.argv[1]=="--child":
        child(sys.argv[2],int(sys.argv[3]),int(sys.argv[4])); return
    if not CORPUS.exists(): raise SystemExit(f"Missing corpus: {CORPUS}")
    print("Loading 84 M-family runs...")
    m=load_m_rows()
    print("Running 12 fresh E32 games...")
    e=run_e32_rows()
    print()
    print_core(m,e); print_crop(m,e); print_budget(m,e)
    print("\n## Decision gate\n")
    print("- E32 buys far fewer seeds -> capital allocation / seed procurement.")
    print("- Seed buys similar but PLANT much lower -> worker scheduling / movement efficiency.")
    print("- PLANT similar but crop count lower -> survival / harvest-replant policy.")
    print("- Q3 delayed because cash goes to animals/structures -> one crop-first capital schedule.")
    print("- After ONE mechanism-focused candidate, run population W/D/L; if clearly weak, stop M-family reconstruction.")

if __name__=="__main__":
    main()
