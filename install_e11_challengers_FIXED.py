from __future__ import annotations
from pathlib import Path
import textwrap

HERE = Path(__file__).resolve().parent

def looks_like_base(p: Path) -> bool:
    return (
        (p / "agent_e11_prvsiyan_frontier.py").exists()
        and (p / "elite_runtime.py").exists()
        and (p / "public_agents" / "elite" / "prvsiyan_frontier" / "entrypoint.txt").exists()
    )

def find_base() -> Path:
    parent = HERE.parent
    candidates = [
        HERE,
        HERE / "kaggriculture_elite_bundle_PATCHED_v2",
        HERE / "kaggriculture_elite_bundle_PATCHED",
        HERE / "kaggriculture_elite_bundle_FINAL",
        parent / "kaggriculture_elite_bundle_PATCHED_v2",
        parent / "kaggriculture_elite_bundle_PATCHED",
        parent / "kaggriculture_elite_bundle_FINAL",
        parent,
    ]

    # Search both the directory containing this installer and its parent.
    for root in (HERE, parent):
        try:
            candidates += [
                p for p in root.iterdir()
                if p.is_dir() and "kaggriculture_elite_bundle" in p.name
            ]
        except Exception:
            pass

    seen = set()
    for p in candidates:
        try:
            p = p.resolve()
        except Exception:
            continue
        if p in seen:
            continue
        seen.add(p)
        if looks_like_base(p):
            return p

    raise SystemExit(
        "Could not find the full elite bundle. "
        "Expected agent_e11_prvsiyan_frontier.py and downloaded prvsiyan_frontier."
    )

COMMON = r'''
from collections import defaultdict
from elite_runtime import load_agent, call_agent

_BASE = load_agent("prvsiyan_frontier")
_pending = defaultdict(int)
_age = defaultdict(int)
_prev_inv = None
_prev_price = None

BASE_PRICE = {
    "MILK": 160,
    "FERTILIZER": 100,
    "WOOL": 200,
    "STRAWBERRY": 120,
}

def _get(o, k, d=None):
    return o.get(k, d) if isinstance(o, dict) else getattr(o, k, d)

def _public_counts(farm):
    animals = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
    crops = {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0}
    for row in _get(farm, "tiles", []) or []:
        for t in row or []:
            if not isinstance(t, dict):
                continue
            a = t.get("animal")
            if a in animals:
                animals[a] += 1
            if t.get("kind") == "PLANT":
                c = t.get("crop")
                if c in crops:
                    crops[c] += 1
    return animals, crops

def _clone_like(obs):
    farms = _get(obs, "farms", []) or []
    player = int(_get(obs, "player", 0) or 0)
    if len(farms) != 2:
        return False
    me = farms[player]
    opp = farms[1-player]

    ma, mc = _public_counts(me)
    oa, oc = _public_counts(opp)

    hand_gap = abs(len(_get(me, "hands", []) or []) - len(_get(opp, "hands", []) or []))
    land_gap = abs(len(_get(me, "unlocked_quadrants", []) or []) - len(_get(opp, "unlocked_quadrants", []) or []))
    animal_gap = sum(abs(ma[k]-oa[k]) for k in ma)
    crop_gap = sum(abs(mc[k]-oc[k]) for k in mc)

    return hand_gap <= 1 and land_gap == 0 and animal_gap <= 2 and crop_gap <= 5

def _overlay(obs, configuration, guarded_items, clone_only=False):
    global _prev_inv, _prev_price, _pending, _age

    act = call_agent(_BASE, obs, configuration)
    if not isinstance(act, dict):
        return act

    day = int(_get(obs, "day", 0) or 0)
    player = int(_get(obs, "player", 0) or 0)
    farms = _get(obs, "farms", []) or []
    farm = farms[player] if 0 <= player < len(farms) else {}
    money = float(_get(farm, "money", 0) or 0)

    private = _get(obs, "private", {}) or {}
    shed = _get(private, "shed", {}) or {}
    shed_total = sum(
        int(v or 0)
        for v in shed.values()
        if isinstance(v, (int, float))
    )

    mkt = _get(obs, "market", {}) or {}
    inv = dict(_get(mkt, "inventory", {}) or {})
    price = dict(_get(mkt, "prices", {}) or {})

    delta = {x: 0.0 for x in guarded_items}
    pdelta = {x: 0.0 for x in guarded_items}
    if _prev_inv is not None:
        for item in guarded_items:
            delta[item] = float(inv.get(item, 0) or 0) - float(_prev_inv.get(item, 0) or 0)
            pdelta[item] = float(price.get(item, 0) or 0) - float(_prev_price.get(item, 0) or 0)

    market = list(act.get("market", []) or [])
    out = []
    released = set()

    for item in list(_pending):
        if _pending[item] > 0:
            _age[item] += 1

    endgame = day >= 27
    pressure = shed_total >= 88
    cash_critical = (
        money < 1300
        or any(
            isinstance(o, list)
            and o
            and o[0] in {"BUY_ANIMAL", "BUY_LAND", "BUY_PRODUCT"}
            for o in market
        )
    )

    gate = (not clone_only) or (day >= 7 and _clone_like(obs))

    for order in market:
        is_guarded_sell = (
            isinstance(order, list)
            and len(order) >= 3
            and order[0] == "SELL"
            and str(order[1]) in guarded_items
        )

        if not is_guarded_sell:
            out.append(order)
            continue

        item = str(order[1])

        if _pending[item] > 0:
            out.append(order)
            _pending[item] = 0
            _age[item] = 0
            released.add(item)
            continue

        base = BASE_PRICE[item]
        ratio = float(price.get(item, base) or base) / base
        saturating = delta[item] >= 4 or pdelta[item] <= -4

        if (
            gate
            and saturating
            and ratio < 1.08
            and not endgame
            and not pressure
            and not cash_critical
        ):
            try:
                qty = max(0, int(order[2]))
            except Exception:
                qty = 0
            if qty > 0:
                _pending[item] = min(80, qty)
                _age[item] = 0
                continue

        out.append(order)

    if len(out) < 10:
        for item in guarded_items:
            if len(out) >= 10:
                break
            if item in released or _pending[item] <= 0:
                continue

            have = int(shed.get(item, 0) or 0)
            recovering = delta[item] <= -2 or pdelta[item] >= 2
            must_flush = endgame or pressure or _age[item] >= 2

            if recovering or must_flush:
                qty = min(have, int(_pending[item]))
                if qty > 0:
                    out.append(["SELL", item, qty])
                _pending[item] = 0
                _age[item] = 0

    _prev_inv = inv
    _prev_price = price

    act = dict(act)
    act["market"] = out[:10]
    return act
'''

E14 = COMMON + r'''
def agent(obs, configuration=None):
    return _overlay(obs, configuration, {"MILK"}, clone_only=False)
melon_maxxer = agent
'''

E15 = COMMON + r'''
def agent(obs, configuration=None):
    return _overlay(obs, configuration, {"FERTILIZER"}, clone_only=False)
melon_maxxer = agent
'''

E16 = COMMON + r'''
def agent(obs, configuration=None):
    return _overlay(
        obs,
        configuration,
        {"MILK", "FERTILIZER"},
        clone_only=True,
    )
melon_maxxer = agent
'''

ARENA = r'''
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
'''

def main():
    base = find_base()
    print(f"[base] {base}")
    payloads = {
        "agent_e14_prvsiyan_milkguard.py": E14,
        "agent_e15_prvsiyan_fertguard.py": E15,
        "agent_e16_prvsiyan_cloneguard.py": E16,
        "e11_focused_arena.py": ARENA,
    }

    for name, content in payloads.items():
        path = base / name
        text = textwrap.dedent(content).lstrip()
        path.write_text(text, encoding="utf-8")
        compile(text, str(path), "exec")
        print(f"[write] {path}")

    print("\nRun:")
    print(f"  cd {base}")
    print("  python e11_focused_arena.py --seeds 12 --seed-start 10000")
    print("\nThen, only if a variant survives:")
    print("  python e11_focused_arena.py --seeds 40 --seed-start 20000")

if __name__ == "__main__":
    main()
