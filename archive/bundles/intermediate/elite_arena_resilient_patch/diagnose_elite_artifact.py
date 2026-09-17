"""
diagnose_elite_artifact.py

Usage:
    python diagnose_elite_artifact.py shape_top10

Prints:
- selected entrypoint
- all Python files
- top-level function/class names in each file
This is for fixing unusual Kaggle submission packages without guessing.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
name = sys.argv[1] if len(sys.argv) > 1 else "shape_top10"
base = ROOT / "public_agents" / "elite" / name

marker = base / "entrypoint.txt"
print("base:", base)
print("entrypoint:", marker.read_text(encoding="utf-8").strip() if marker.exists() else "MISSING")

for p in sorted(base.rglob("*.py")):
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(text)
    except Exception as e:
        print(f"\n{p.relative_to(base)}  [parse error: {e}]")
        continue

    funcs = [
        n.name for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    classes = [
        n.name for n in tree.body
        if isinstance(n, ast.ClassDef)
    ]

    print(f"\n{p.relative_to(base)}")
    print("  funcs  :", funcs)
    print("  classes:", classes)
