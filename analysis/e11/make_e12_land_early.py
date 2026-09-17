#!/usr/bin/env python3
"""
make_e12_land_early.py

Exact E11 (Prvsiyan Frontier) から、
「第3区画の解禁日だけ」を前倒しした E12 候補を生成する。

変更:
    LAND_OPEN_DAYS = (5, 9)
                     ↓
    LAND_OPEN_DAYS = (5, 7)

それ以外は一切変更しない。

使い方:
    python make_e12_land_early.py

出力:
    agent_e12_land_early.py
"""

from pathlib import Path
import hashlib
import sys

E11_SHA256 = "02b1fee4b0e48027d4d3baeeb99518346f4fc5a14724cdb202d09a3425b15a79"
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]

CANDIDATES = [
    PROJECT_ROOT / "artifacts/bundles/current/public_agents/elite/prvsiyan_frontier/raw/main.py",
    PROJECT_ROOT / "artifacts/bundles/current/public_agents/elite/prvsiyan_frontier/raw/_extract_submission_tar/main.py",
]

OLD = "LAND_OPEN_DAYS = (5, 9)"
NEW = "LAND_OPEN_DAYS = (5, 7)"
OUT = HERE / "agent_e12_land_early.py"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_e11():
    checked = []
    for p in CANDIDATES:
        if p.is_file():
            digest = sha256(p)
            checked.append((p, digest))
            if digest == E11_SHA256:
                return p

    for p in PROJECT_ROOT.rglob("main.py"):
        try:
            digest = sha256(p)
        except OSError:
            continue
        if digest == E11_SHA256:
            return p

    print("❌ exact E11 が見つかりません。")
    if checked:
        print("確認した候補:")
        for p, d in checked:
            print(f"  {p}  {d}")
    sys.exit(1)


src = find_e11()
text = src.read_text(encoding="utf-8")

if OLD not in text:
    print(f"❌ E11内に `{OLD}` が見つかりません。")
    print("安全のため自動変更を中止しました。")
    sys.exit(2)

if text.count(OLD) != 1:
    print(f"❌ `{OLD}` が {text.count(OLD)} 箇所あります。")
    print("安全のため自動変更を中止しました。")
    sys.exit(3)

new_text = text.replace(OLD, NEW, 1)
OUT.write_text(new_text, encoding="utf-8")

print("=== E12 land-early candidate ===")
print(f"E11 source : {src}")
print(f"E11 SHA    : {sha256(src)}")
print(f"output     : {OUT}")
print(f"change     : {OLD}")
print(f"          -> {NEW}")
print(f"E12 SHA    : {sha256(OUT)}")
print()
print("✅ 第3区画の解禁だけを前倒ししました。")
print("   作付け・家畜・SELL・作業員ロジックは変更していません。")
