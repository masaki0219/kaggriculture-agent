"""
Download current public Kaggriculture elite artifacts with the Kaggle CLI.

Run from the Kaggle project root:
    python setup_elite_candidates.py

Requires:
    kaggle CLI authenticated for public kernel access.

The script does not submit anything.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "public_agents" / "elite"

SOURCES = {
    # 2026-09-18 frontier refresh.  Benchmark/base candidates for the
    # current reactive public lineage.  Public score is not used as a
    # promotion criterion; the family-balanced local screen decides which
    # exact artifact is worth freezing as a new immutable experiment.
    "aurax7_v7_current": {
        "kernel": "aurax7/kaggriculture-shop-router-reactive-v7",
        "license": "Apache-2.0",
        "status": "benchmark/base candidate; keep exact downloaded hash in manifest",
    },
    "ahmed_v44_current": {
        "kernel": "ahmedberatozer/kaggriculture-v44-winning-the-same-turn-sale-race",
        "license": "Apache-2.0",
        "status": "benchmark/base candidate; keep exact downloaded hash in manifest",
    },
    "tetsu_market_v23_current": {
        "kernel": "tetsutani/market-smart-farming-kaggriculture",
        "license": "Apache-2.0",
        "status": "benchmark/base candidate; keep exact downloaded hash in manifest",
    },
    "kaito27_current": {
        "kernel": "kaitofukami/44-46-strict-future-top-30-v22-price-impact",
        "license": "Apache-2.0",
        "status": "submit-safe subject to Kaggle competition rules / attribution",
        "expected_main_sha256": "f48c21166eac68d1b05a401f04f94a2eb6154e65415af64893672365ff33c7b8",
    },
    "prvsiyan_frontier": {
        "kernel": "prvsiyan/kaggriculture-frontier-the-moon-counts-melons",
        "license": "Apache-2.0",
        "status": "submit-safe subject to Kaggle competition rules / attribution",
    },
    "kaito43_current": {
        "kernel": "kaitofukami/103-128-fresh-public-v43-sparse-shop-hybrid",
        "license": "Apache-2.0",
        "status": "submit-safe subject to Kaggle competition rules / attribution",
    },
    # exact public output, hash-pinned independently by qeinstein
    "kaito58": {
        "kernel": "kaitofukami/238-238-known-streams-v58-minimax-closed-loop",
        "license": "Apache-2.0",
        "status": "submit-safe subject to Kaggle competition rules / attribution",
        "expected_main_sha256": "b041058ec187a8d0a01edc0eab8de068b53deca3e6c1973faf74ace6916ddcb9",
    },
    # public notebook currently marked Apache-2.0 on Kaggle
    "boatlee29": {
        "kernel": "boatlee/v29-r1-adaptive-market-hysteresis",
        "license": "Apache-2.0",
        "status": "submit-safe subject to Kaggle competition rules / attribution",
    },
    "shape_top10": {
        "kernel": "indarkarhana/shape-the-shop-work-the-pasture-top-10",
        "license": "Apache-2.0",
        "status": "submit-safe subject to Kaggle competition rules / attribution",
    },
    "adaptive_route_v2": {
        "kernel": "reyhanksatria/adaptive-route-agent-v2",
        "license": "Apache-2.0",
        "status": "submit-safe subject to Kaggle competition rules / attribution",
    },
    # Strong benchmark; license needs re-check before final submission.
    "tetsu_shape": {
        "kernel": "tetsutani/shape-the-shop-work-the-pasture-kaggriculture",
        "license": "VERIFY",
        "status": "benchmark first; do not submit until license is confirmed",
    },
    # Recent high public-score line; benchmark first because current license
    # was not independently verified in this research pass.
    "farming_v4": {
        "kernel": "lynnsakurai/farming-score-v4-a-better-shop",
        "license": "VERIFY",
        "status": "benchmark first; do not submit until license is confirmed",
    },
}

CALLABLE_TOKENS = (
    "def agent(",
    "def kaggle_submission_agent(",
    "def submission_agent(",
    "def melon_maxxer(",
)

def run(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    try:
        subprocess.run(list(map(str, cmd)), check=True)
    except subprocess.CalledProcessError as e:
        cmd0 = str(cmd[0]) if cmd else ""
        if cmd0 == "kaggle":
            raise SystemExit(
                "\nKaggle CLI command failed.\n"
                "If the message above says Authentication required, run:\n\n"
                "    kaggle auth login\n\n"
                "Complete the browser login, then rerun:\n\n"
                "    python setup_elite_candidates.py\n\n"
                "Already completed candidates will be skipped automatically."
            ) from e
        raise

def extract_archives(base: Path):
    # Recursively unpack likely submission archives into deterministic dirs.
    for p in list(base.rglob("*")):
        if not p.is_file():
            continue
        low = p.name.lower()
        try:
            if low.endswith((".tar.gz", ".tgz", ".tar")):
                out = p.parent / f"_extract_{p.stem.replace('.', '_')}"
                out.mkdir(exist_ok=True)
                with tarfile.open(p, "r:*") as tf:
                    tf.extractall(out)
            elif low.endswith(".zip"):
                out = p.parent / f"_extract_{p.stem}"
                out.mkdir(exist_ok=True)
                with zipfile.ZipFile(p) as zf:
                    zf.extractall(out)
        except Exception as e:
            print(f"[warn] could not extract {p}: {e}")

def looks_like_agent(path: Path) -> bool:
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return any(tok in txt for tok in CALLABLE_TOKENS)

def choose_entry(base: Path) -> Path | None:
    py = [p for p in base.rglob("*.py") if "__MACOSX" not in p.parts]
    if not py:
        return None

    preferred = []
    for p in py:
        score = 0
        if p.name == "main.py": score += 100
        if p.name == "submission.py": score += 90
        if looks_like_agent(p): score += 50
        # Prefer extracted/submission payloads over helper scripts.
        if "_extract_" in str(p): score += 10
        if "test" in p.name.lower(): score -= 50
        preferred.append((score, -len(p.parts), p))

    preferred.sort(reverse=True, key=lambda x: (x[0], x[1], str(x[2])))
    best = preferred[0][2]
    return best if preferred[0][0] > 0 else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=sorted(SOURCES))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--all", action="store_true", help="also fetch benchmark-only VERIFY-license artifacts")
    args = ap.parse_args()

    if shutil.which("kaggle") is None:
        raise SystemExit(
            "kaggle CLI not found. Install it in this venv first, e.g.\n"
            "  python -m pip install kaggle\n"
            "Then authenticate and rerun."
        )

    DEST.mkdir(parents=True, exist_ok=True)
    manifest = {}

    if args.only:
        names = [args.only]
    elif args.all:
        names = list(SOURCES)
    else:
        names = [
            name for name, meta in SOURCES.items()
            if meta.get("license") != "VERIFY"
        ]
    for name in names:
        meta = SOURCES[name]
        base = DEST / name
        raw = base / "raw"

        if args.force and base.exists():
            shutil.rmtree(base)

        # Resume safely: if this candidate already has a valid entrypoint,
        # do not redownload it unless --force was requested.
        marker = base / "entrypoint.txt"
        if marker.exists() and not args.force:
            try:
                rel = marker.read_text(encoding="utf-8").strip()
                existing = (base / rel).resolve()
                if existing.exists():
                    compile(existing.read_text(encoding="utf-8", errors="ignore"),
                            str(existing), "exec")
                    print(f"[skip] {name}: already ready -> {rel}")
                    manifest[name] = {
                        **meta,
                        "entrypoint": rel,
                        "sha256": None,
                    }
                    continue
            except Exception:
                pass

        raw.mkdir(parents=True, exist_ok=True)

        print(f"\n========== {name}: {meta['kernel']} ==========")
        run([
            "kaggle", "kernels", "output",
            meta["kernel"],
            "-p", raw,
            "-o",
        ])

        extract_archives(raw)
        entry = choose_entry(raw)

        # If kernel output does not contain an executable .py, pull notebook
        # source as diagnostic material. We do not try to magically turn a
        # notebook into a submission because that can select the wrong cell.
        if entry is None:
            source_dir = base / "source"
            source_dir.mkdir(exist_ok=True)
            try:
                run([
                    "kaggle", "kernels", "pull",
                    meta["kernel"],
                    "-p", source_dir,
                    "-m",
                ])
            except Exception:
                pass
            raise SystemExit(
                f"No executable agent .py found for {name} in {raw}.\n"
                f"Inspect {raw} / {source_dir} and choose the actual output."
            )

        rel = entry.relative_to(base)
        (base / "entrypoint.txt").write_text(str(rel), encoding="utf-8")

        digest = None
        if entry.name == "main.py":
            import hashlib
            digest = hashlib.sha256(entry.read_bytes()).hexdigest()

        expected = meta.get("expected_main_sha256")
        if expected and digest != expected:
            raise SystemExit(
                f"{name}: main.py hash changed.\n"
                f" expected {expected}\n"
                f" got      {digest}\n"
                "Do not silently benchmark a different artifact."
            )

        compile(entry.read_text(encoding="utf-8", errors="ignore"),
                str(entry), "exec")

        manifest[name] = {
            **meta,
            "entrypoint": str(rel),
            "sha256": digest,
        }
        print(f"[ok] {name} -> {rel}")

    out = DEST / "manifest.json"
    old = {}
    if out.exists():
        try:
            old = json.loads(out.read_text(encoding="utf-8"))
        except Exception:
            old = {}
    old.update(manifest)
    out.write_text(json.dumps(old, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\nWrote {out}")

if __name__ == "__main__":
    main()
