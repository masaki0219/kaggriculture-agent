from __future__ import annotations

import argparse
from pathlib import Path
import shutil

SOURCE_BLOCK = '''    # 2026-09-18 frontier refresh.  Benchmark/base candidates for the\n    # current reactive public lineage.  Public score is not used as a\n    # promotion criterion; the family-balanced local screen decides which\n    # exact artifact is worth freezing as a new immutable experiment.\n    "aurax7_v7_current": {\n        "kernel": "aurax7/kaggriculture-shop-router-reactive-v7",\n        "license": "Apache-2.0",\n        "status": "benchmark/base candidate; keep exact downloaded hash in manifest",\n    },\n    "ahmed_v44_current": {\n        "kernel": "ahmedberatozer/kaggriculture-v44-winning-the-same-turn-sale-race",\n        "license": "Apache-2.0",\n        "status": "benchmark/base candidate; keep exact downloaded hash in manifest",\n    },\n    "tetsu_market_v23_current": {\n        "kernel": "tetsutani/market-smart-farming-kaggriculture",\n        "license": "Apache-2.0",\n        "status": "benchmark/base candidate; keep exact downloaded hash in manifest",\n    },\n'''


def same_bytes(a: Path, b: Path) -> bool:
    return a.exists() and a.read_bytes() == b.read_bytes()


def copy_checked(src: Path, dst: Path, force: bool):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not same_bytes(src, dst):
        if not force:
            raise SystemExit(
                f"Refusing to overwrite different existing file: {dst}\n"
                "Re-run with --force only after inspecting the difference."
            )
        backup = dst.with_suffix(dst.suffix + ".pre_frontier_v2")
        shutil.copy2(dst, backup)
        print(f"backup: {backup}")
    shutil.copy2(src, dst)
    print(f"write:  {dst}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", help="kaggriculture-agent repository root")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    bundle = Path(__file__).resolve().parent
    repo = Path(args.repo).expanduser().resolve()
    setup = repo / "artifacts" / "bundles" / "current" / "setup_elite_candidates.py"
    if not setup.exists():
        raise SystemExit(f"Not a kaggriculture-agent repo root: missing {setup}")

    target = repo / "evaluation" / "frontier_screen_v2"
    copy_checked(bundle / "arena.py", target / "arena.py", args.force)
    copy_checked(bundle / "README.md", target / "README.md", args.force)

    text = setup.read_text(encoding="utf-8")
    if '"aurax7_v7_current"' not in text:
        anchor = "SOURCES = {\n"
        if anchor not in text:
            raise SystemExit(f"Could not find SOURCES dictionary anchor in {setup}")
        backup = setup.with_suffix(setup.suffix + ".pre_frontier_v2")
        if not backup.exists():
            shutil.copy2(setup, backup)
            print(f"backup: {backup}")
        text = text.replace(anchor, anchor + SOURCE_BLOCK, 1)
        setup.write_text(text, encoding="utf-8")
        print(f"patch:  {setup}")
    else:
        print(f"skip:   source entries already present in {setup}")

    print("\nInstalled without assigning/changing any E number and without clearing caches.")
    print("Next:")
    print("  cd artifacts/bundles/current")
    print("  python setup_elite_candidates.py --only aurax7_v7_current")
    print("  python setup_elite_candidates.py --only ahmed_v44_current")
    print("  python setup_elite_candidates.py --only tetsu_market_v23_current")
    print("  cd ../../..")
    print("  python evaluation/frontier_screen_v2/arena.py --seeds 8 --seed-start 18000")


if __name__ == "__main__":
    main()
