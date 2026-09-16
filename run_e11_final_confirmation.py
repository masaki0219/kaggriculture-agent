"""
Run directly from the main Kaggle directory:

    python run_e11_final_confirmation.py --seeds 40 --seed-start 20000
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def looks_like_base(p: Path) -> bool:
    return (
        (p / "agent_e11_prvsiyan_frontier.py").exists()
        and (p / "public_agents" / "elite" / "prvsiyan_frontier").exists()
    )


def find_base() -> Path:
    candidates = [
        HERE / "kaggriculture_elite_bundle_PATCHED_v2",
        HERE / "kaggriculture_elite_bundle_PATCHED",
        HERE / "kaggriculture_elite_bundle_FINAL",
        HERE,
    ]

    try:
        candidates += [
            p for p in HERE.iterdir()
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
        "Could not find kaggriculture_elite_bundle_PATCHED_v2 "
        "under the current Kaggle directory."
    )


FINAL_SCRIPT = '\nfrom __future__ import annotations\n\nimport argparse\nimport importlib\nimport importlib.util\nimport json\nimport os\nfrom pathlib import Path\nimport subprocess\nfrom statistics import mean\nimport sys\n\nfrom kaggle_environments import make\n\nROOT = Path(__file__).resolve().parent\nPUB = ROOT / "public_agents"\nCACHE = ROOT / "e11_final_confirmation_cache.json"\nPREFIX = "@@FINAL@@"\n\nOPPONENTS = {\n    "e2_boatlee29": ("module", "agent_e2_boatlee29"),\n    "e12_kaito43_current": ("module", "agent_e12_kaito43_current"),\n    "v15_kaito48": ("module", "agent_v15"),\n    "qeinstein_champion": ("path", PUB / "qeinstein" / "scripts" / "champion_entry.py"),\n    "qeinstein_candidate7": ("path", PUB / "qeinstein" / "scripts" / "candidate7_entry.py"),\n    "qeinstein_portfolio": ("path", PUB / "qeinstein" / "scripts" / "frontier_portfolio_entry.py"),\n}\n\n\ndef load_path(path: Path, unique: str):\n    path = path.resolve()\n    repo_root = path.parent.parent if path.parent.name == "scripts" else path.parent\n\n    for p in (repo_root, repo_root / "src", path.parent):\n        s = str(p)\n        if s not in sys.path:\n            sys.path.insert(0, s)\n\n    old = Path.cwd()\n    try:\n        os.chdir(repo_root)\n        spec = importlib.util.spec_from_file_location(unique, path)\n        if spec is None or spec.loader is None:\n            raise ImportError(path)\n        mod = importlib.util.module_from_spec(spec)\n        sys.modules[unique] = mod\n        spec.loader.exec_module(mod)\n    finally:\n        os.chdir(old)\n\n    for name in ("agent", "kaggle_submission_agent", "submission_agent"):\n        fn = getattr(mod, name, None)\n        if callable(fn):\n            return fn\n\n    raise AttributeError(f"No agent callable in {path}")\n\n\ndef load_opp(name: str):\n    typ, ref = OPPONENTS[name]\n    if typ == "module":\n        return importlib.import_module(ref).agent\n    return load_path(Path(ref), f"_final_{name}")\n\n\ndef child(args):\n    try:\n        e11 = importlib.import_module("agent_e11_prvsiyan_frontier").agent\n        opp = load_opp(args.opp)\n\n        agents = [e11, opp] if not args.swap else [opp, e11]\n\n        env = make(\n            "kaggriculture",\n            configuration={"episodeSteps": 720, "seed": args.seed},\n            debug=False,\n        )\n        env.run(agents)\n\n        final = env.steps[-1]\n        r0, r1 = float(final[0].reward), float(final[1].reward)\n        ours, theirs = (r1, r0) if args.swap else (r0, r1)\n\n        print(PREFIX + json.dumps({\n            "opp": args.opp,\n            "seed": args.seed,\n            "swap": args.swap,\n            "ours": ours,\n            "theirs": theirs,\n            "result": "W" if ours > theirs else "L" if ours < theirs else "D",\n            "margin": ours - theirs,\n        }))\n\n    except Exception as e:\n        print(PREFIX + json.dumps({\n            "error": f"{type(e).__name__}: {e}",\n            "opp": args.opp,\n            "seed": args.seed,\n            "swap": args.swap,\n        }))\n\n\ndef load_cache():\n    if not CACHE.exists():\n        return {}\n    try:\n        return json.loads(CACHE.read_text(encoding="utf-8"))\n    except Exception:\n        return {}\n\n\ndef save_cache(cache):\n    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")\n\n\ndef run_game(opp, seed, swap, cache):\n    key = f"{opp}|{seed}|{int(swap)}"\n\n    if key in cache and "error" not in cache[key]:\n        return cache[key]\n\n    cmd = [\n        sys.executable,\n        str(Path(__file__).resolve()),\n        "--opp", opp,\n        "--seed", str(seed),\n    ]\n    if swap:\n        cmd.append("--swap")\n\n    p = subprocess.run(\n        cmd,\n        cwd=str(ROOT),\n        text=True,\n        capture_output=True,\n    )\n\n    rec = None\n    for line in p.stdout.splitlines():\n        if line.startswith(PREFIX):\n            rec = json.loads(line[len(PREFIX):])\n\n    if rec is None:\n        rec = {"error": p.stderr[-1500:] or "no structured result"}\n\n    cache[key] = rec\n    save_cache(cache)\n    return rec\n\n\ndef main():\n    ap = argparse.ArgumentParser()\n    ap.add_argument("--seeds", type=int, default=40)\n    ap.add_argument("--seed-start", type=int, default=20000)\n    ap.add_argument("--opp")\n    ap.add_argument("--seed", type=int)\n    ap.add_argument("--swap", action="store_true")\n    args = ap.parse_args()\n\n    if args.opp:\n        child(args)\n        return\n\n    cache = load_cache()\n    all_rows = []\n\n    print("========== E11 FINAL CONFIRMATION ==========")\n    print(\n        f"fresh seeds {args.seed_start}.."\n        f"{args.seed_start + args.seeds - 1}, both seats"\n    )\n\n    for opp in OPPONENTS:\n        rows = []\n        err = None\n\n        for seed in range(args.seed_start, args.seed_start + args.seeds):\n            for swap in (False, True):\n                rec = run_game(opp, seed, swap, cache)\n                if "error" in rec:\n                    err = rec["error"]\n                    break\n                rows.append(rec)\n            if err:\n                break\n\n        print(f"\\n=== E11 vs {opp} ===")\n\n        if err:\n            print("[SKIP]", err)\n            continue\n\n        w = sum(r["result"] == "W" for r in rows)\n        d = sum(r["result"] == "D" for r in rows)\n        l = sum(r["result"] == "L" for r in rows)\n        margin = mean(r["margin"] for r in rows)\n\n        print(\n            f"{w}-{d}-{l} "\n            f"score={(w + 0.5*d) / len(rows):.1%} "\n            f"margin={margin:+.0f}"\n        )\n\n        all_rows += rows\n\n    if all_rows:\n        w = sum(r["result"] == "W" for r in all_rows)\n        d = sum(r["result"] == "D" for r in all_rows)\n        l = sum(r["result"] == "L" for r in all_rows)\n        margin = mean(r["margin"] for r in all_rows)\n\n        print("\\n========== TOTAL ==========")\n        print(\n            f"E11 {w}-{d}-{l} "\n            f"score={(w + 0.5*d) / len(all_rows):.1%} "\n            f"margin={margin:+.0f}"\n        )\n\n\nif __name__ == "__main__":\n    main()\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--seed-start", type=int, default=20000)
    args = ap.parse_args()

    base = find_base()
    print(f"[base] {base}")

    target = base / "e11_final_confirmation.py"
    target.write_text(FINAL_SCRIPT.lstrip(), encoding="utf-8")
    compile(target.read_text(encoding="utf-8"), str(target), "exec")

    print(f"[write] {target}")

    cmd = [
        sys.executable,
        str(target),
        "--seeds", str(args.seeds),
        "--seed-start", str(args.seed_start),
    ]

    print("+", " ".join(cmd))
    raise SystemExit(subprocess.call(cmd, cwd=str(base)))


if __name__ == "__main__":
    main()
