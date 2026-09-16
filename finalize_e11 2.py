from pathlib import Path
import textwrap

HERE=Path(__file__).resolve().parent

def looks_like_base(p):
    p=Path(p)
    return (p/"agent_e11_prvsiyan_frontier.py").exists() and (p/"public_agents"/"elite"/"prvsiyan_frontier").exists()

def find_base():
    parent=HERE.parent
    candidates=[
        HERE,
        HERE/"kaggriculture_elite_bundle_PATCHED_v2",
        HERE/"kaggriculture_elite_bundle_PATCHED",
        HERE/"kaggriculture_elite_bundle_FINAL",
        parent/"kaggriculture_elite_bundle_PATCHED_v2",
        parent/"kaggriculture_elite_bundle_PATCHED",
        parent/"kaggriculture_elite_bundle_FINAL",
        parent,
    ]
    for root in (HERE,parent):
        try:
            candidates += [p for p in root.iterdir() if p.is_dir() and "kaggriculture_elite_bundle" in p.name]
        except Exception:
            pass
    seen=set()
    for p in candidates:
        try: p=p.resolve()
        except Exception: continue
        if p in seen: continue
        seen.add(p)
        if looks_like_base(p): return p
    raise SystemExit("Could not find full elite bundle.")

CONFIRM='\nfrom __future__ import annotations\nimport argparse, importlib, importlib.util, json, os, subprocess, sys\nfrom pathlib import Path\nfrom statistics import mean\nfrom kaggle_environments import make\n\nROOT=Path(__file__).resolve().parent\nPUB=ROOT/"public_agents"\nCACHE=ROOT/"e11_final_confirmation_cache.json"\nPREFIX="@@FINAL@@"\n\nOPPONENTS={\n    "e2_boatlee29":("module","agent_e2_boatlee29"),\n    "e12_kaito43_current":("module","agent_e12_kaito43_current"),\n    "v15_kaito48":("module","agent_v15"),\n    "qeinstein_champion":("path",PUB/"qeinstein"/"scripts"/"champion_entry.py"),\n    "qeinstein_candidate7":("path",PUB/"qeinstein"/"scripts"/"candidate7_entry.py"),\n    "qeinstein_portfolio":("path",PUB/"qeinstein"/"scripts"/"frontier_portfolio_entry.py"),\n}\n\ndef load_path(path,unique):\n    path=Path(path).resolve()\n    repo_root=path.parent.parent if path.parent.name=="scripts" else path.parent\n    for p in (repo_root,repo_root/"src",path.parent):\n        s=str(p)\n        if s not in sys.path: sys.path.insert(0,s)\n    old=Path.cwd()\n    try:\n        os.chdir(repo_root)\n        spec=importlib.util.spec_from_file_location(unique,path)\n        if spec is None or spec.loader is None: raise ImportError(path)\n        mod=importlib.util.module_from_spec(spec)\n        sys.modules[unique]=mod\n        spec.loader.exec_module(mod)\n    finally:\n        os.chdir(old)\n    for n in ("agent","kaggle_submission_agent","submission_agent"):\n        fn=getattr(mod,n,None)\n        if callable(fn): return fn\n    raise AttributeError(path)\n\ndef load_opp(name):\n    typ,ref=OPPONENTS[name]\n    if typ=="module": return importlib.import_module(ref).agent\n    return load_path(ref,f"_final_{name}")\n\ndef child(args):\n    try:\n        e11=importlib.import_module("agent_e11_prvsiyan_frontier").agent\n        opp=load_opp(args.opp)\n        agents=[e11,opp] if not args.swap else [opp,e11]\n        env=make("kaggriculture",configuration={"episodeSteps":720,"seed":args.seed},debug=False)\n        env.run(agents)\n        f=env.steps[-1]\n        r0,r1=float(f[0].reward),float(f[1].reward)\n        ours,theirs=(r1,r0) if args.swap else (r0,r1)\n        print(PREFIX+json.dumps({\n            "opp":args.opp,"seed":args.seed,"swap":args.swap,\n            "ours":ours,"theirs":theirs,\n            "result":"W" if ours>theirs else "L" if ours<theirs else "D",\n            "margin":ours-theirs\n        }))\n    except Exception as e:\n        print(PREFIX+json.dumps({"error":f"{type(e).__name__}: {e}"}))\n\ndef load_cache():\n    if not CACHE.exists(): return {}\n    try: return json.loads(CACHE.read_text(encoding="utf-8"))\n    except Exception: return {}\n\ndef save_cache(c):\n    CACHE.write_text(json.dumps(c,indent=2),encoding="utf-8")\n\ndef game(opp,seed,swap,cache):\n    k=f"{opp}|{seed}|{int(swap)}"\n    if k in cache and "error" not in cache[k]: return cache[k]\n    cmd=[sys.executable,str(Path(__file__).resolve()),"--opp",opp,"--seed",str(seed)]\n    if swap: cmd.append("--swap")\n    p=subprocess.run(cmd,cwd=str(ROOT),text=True,capture_output=True)\n    rec=None\n    for line in p.stdout.splitlines():\n        if line.startswith(PREFIX):\n            rec=json.loads(line[len(PREFIX):])\n    if rec is None:\n        rec={"error":p.stderr[-1200:] or "no structured result"}\n    cache[k]=rec; save_cache(cache); return rec\n\ndef main():\n    ap=argparse.ArgumentParser()\n    ap.add_argument("--seeds",type=int,default=40)\n    ap.add_argument("--seed-start",type=int,default=20000)\n    ap.add_argument("--opp"); ap.add_argument("--seed",type=int); ap.add_argument("--swap",action="store_true")\n    args=ap.parse_args()\n    if args.opp: child(args); return\n\n    cache=load_cache(); all_rows=[]\n    print("========== E11 FINAL CONFIRMATION ==========")\n    for opp in OPPONENTS:\n        rows=[]; err=None\n        for seed in range(args.seed_start,args.seed_start+args.seeds):\n            for swap in (False,True):\n                rec=game(opp,seed,swap,cache)\n                if "error" in rec: err=rec["error"]; break\n                rows.append(rec)\n            if err: break\n        print(f"\\n=== E11 vs {opp} ===")\n        if err:\n            print("[SKIP]",err); continue\n        w=sum(r["result"]=="W" for r in rows); d=sum(r["result"]=="D" for r in rows); l=sum(r["result"]=="L" for r in rows)\n        m=mean(r["margin"] for r in rows)\n        print(f"{w}-{d}-{l} score={(w+0.5*d)/len(rows):.1%} margin={m:+.0f}")\n        all_rows+=rows\n    if all_rows:\n        w=sum(r["result"]=="W" for r in all_rows); d=sum(r["result"]=="D" for r in all_rows); l=sum(r["result"]=="L" for r in all_rows)\n        m=mean(r["margin"] for r in all_rows)\n        print("\\n========== TOTAL ==========")\n        print(f"E11 {w}-{d}-{l} score={(w+0.5*d)/len(all_rows):.1%} margin={m:+.0f}")\n\nif __name__=="__main__":\n    main()\n'
BUILDER='\nfrom __future__ import annotations\nimport hashlib, shutil, tarfile\nfrom pathlib import Path\n\nROOT=Path(__file__).resolve().parent\nBASE=ROOT/"public_agents"/"elite"/"prvsiyan_frontier"\nOUT=ROOT/"submission_e11_exact.tar.gz"\n\ndef sha256(path):\n    h=hashlib.sha256()\n    with Path(path).open("rb") as f:\n        for chunk in iter(lambda:f.read(1024*1024),b""):\n            h.update(chunk)\n    return h.hexdigest()\n\ndef main():\n    archives=sorted(BASE.rglob("submission.tar.gz"),key=lambda p:(len(p.parts),str(p)))\n    if not archives:\n        raise SystemExit(f"No submission.tar.gz found under {BASE}")\n    src=archives[0]\n    print("[source]",src)\n    print("[source sha256]",sha256(src))\n    with tarfile.open(src,"r:gz") as tf:\n        names=tf.getnames()\n        print("[archive files]")\n        for n in names: print(" ",n)\n        mains=[n for n in names if Path(n).name=="main.py"]\n        if not mains: raise SystemExit("Archive contains no main.py")\n        fh=tf.extractfile(mains[0])\n        if fh is None: raise SystemExit("Could not read main.py")\n        compile(fh.read().decode("utf-8"),mains[0],"exec")\n    shutil.copy2(src,OUT)\n    if sha256(src)!=sha256(OUT): raise SystemExit("Copy hash mismatch")\n    print("\\n[output]",OUT)\n    print("[output sha256]",sha256(OUT))\n    print("Exact published archive copied byte-for-byte.")\n\nif __name__=="__main__":\n    main()\n'

def main():
    base=find_base()
    print("[base]",base)
    for name,content in {
        "e11_final_confirmation.py":CONFIRM,
        "build_e11_exact_submission.py":BUILDER,
    }.items():
        p=base/name
        text=textwrap.dedent(content).lstrip()
        p.write_text(text,encoding="utf-8")
        compile(text,str(p),"exec")
        print("[write]",p)
    print("\nRun:")
    print(f"  cd {base}")
    print("  python e11_final_confirmation.py --seeds 40 --seed-start 20000")
    print("  python build_e11_exact_submission.py")

if __name__=="__main__":
    main()
