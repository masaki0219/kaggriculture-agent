#!/usr/bin/env python3
"""
inspect_e11_land.py

exact E11 を SHA256 で探し、BUY_LAND が
「どのトップレベル変数の、どのリテラル位置」に埋まっているかを解析する。

ソースは変更しない。
出力:
  e11_land_inspection.txt
"""

from __future__ import annotations
from pathlib import Path
import ast
import hashlib
import sys

E11_SHA256 = "02b1fee4b0e48027d4d3baeeb99518346f4fc5a14724cdb202d09a3425b15a79"
OUT = Path("e11_land_inspection.txt")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_e11() -> Path:
    preferred = [
        Path("kaggriculture_elite_bundle_PATCHED_v2/public_agents/elite/prvsiyan_frontier/raw/main.py"),
        Path("public_agents/elite/prvsiyan_frontier/raw/main.py"),
        Path("public_agents/prvsiyan_frontier/main.py"),
    ]
    for p in preferred:
        if p.is_file() and sha256(p) == E11_SHA256:
            return p

    for p in Path(".").rglob("*.py"):
        try:
            if sha256(p) == E11_SHA256:
                return p
        except OSError:
            pass

    raise SystemExit("❌ exact E11 (SHA256一致) が見つかりません。")


def target_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, (ast.Tuple, ast.List)):
        return "(" + ",".join(target_name(x) for x in node.elts) + ")"
    return "<complex>"


def key_repr(node):
    try:
        return repr(ast.literal_eval(node))
    except Exception:
        return f"<{type(node).__name__}@L{getattr(node, 'lineno', '?')}>"


def find_literal_paths(node, needle="BUY_LAND", path=()):
    """Literal containerの中で needle が出るpathを返す。"""
    hits = []
    if isinstance(node, ast.Constant):
        if node.value == needle:
            hits.append((path, node.lineno))
        return hits

    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for i, child in enumerate(node.elts):
            hits.extend(find_literal_paths(child, needle, path + (f"[{i}]",)))
        return hits

    if isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            kr = key_repr(k) if k is not None else "**"
            hits.extend(find_literal_paths(v, needle, path + (f"[{kr}]",)))
        return hits

    # 式の中にリテラルがあるケースも拾う
    for child in ast.iter_child_nodes(node):
        hits.extend(find_literal_paths(child, needle, path + (f"<{type(child).__name__}>",)))
    return hits


def shape_hint(node, depth=0):
    if depth > 3:
        return "..."
    if isinstance(node, ast.List):
        inner = shape_hint(node.elts[0], depth+1) if node.elts else "empty"
        return f"list[{len(node.elts)}]({inner})"
    if isinstance(node, ast.Tuple):
        inner = shape_hint(node.elts[0], depth+1) if node.elts else "empty"
        return f"tuple[{len(node.elts)}]({inner})"
    if isinstance(node, ast.Dict):
        return f"dict[{len(node.keys)}]"
    return type(node).__name__


src = find_e11()
text = src.read_text(encoding="utf-8")
lines = text.splitlines()
tree = ast.parse(text, filename=str(src))

report = []
report.append("=== EXACT E11 LAND INSPECTION ===")
report.append(f"source : {src}")
report.append(f"sha256 : {sha256(src)}")
report.append(f"bytes  : {src.stat().st_size}")
report.append("")

# 1) 生テキストの BUY_LAND
raw_hits = [i for i, line in enumerate(lines, 1) if "BUY_LAND" in line]
report.append(f"BUY_LAND raw occurrences: {len(raw_hits)}")
report.append("")

for n, line_no in enumerate(raw_hits, 1):
    report.append(f"--- raw occurrence {n}: line {line_no} ---")
    lo = max(1, line_no - 8)
    hi = min(len(lines), line_no + 8)
    for j in range(lo, hi + 1):
        marker = ">>" if j == line_no else "  "
        report.append(f"{marker} {j:5d}: {lines[j-1]}")
    report.append("")

# 2) トップレベル代入ごとの literal path
report.append("=== TOP-LEVEL LITERAL PATHS CONTAINING BUY_LAND ===")
literal_hit_count = 0
for stmt in tree.body:
    name = None
    value = None
    if isinstance(stmt, ast.Assign):
        name = " = ".join(target_name(t) for t in stmt.targets)
        value = stmt.value
    elif isinstance(stmt, ast.AnnAssign):
        name = target_name(stmt.target)
        value = stmt.value
    if value is None:
        continue

    hits = find_literal_paths(value)
    if not hits:
        continue

    literal_hit_count += len(hits)
    report.append(
        f"{name}  line={getattr(stmt, 'lineno', '?')}  shape={shape_hint(value)}"
    )
    for path, line_no in hits:
        report.append(f"    line {line_no}: {''.join(path)}")
    report.append("")

report.append(f"literal BUY_LAND hits in top-level assignments: {literal_hit_count}")
report.append("")

# 3) BUY_LANDを含む関数名
report.append("=== FUNCTIONS CONTAINING BUY_LAND ===")
func_hits = []
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        segment = ast.get_source_segment(text, node) or ""
        if "BUY_LAND" in segment:
            func_hits.append((node.name, node.lineno, getattr(node, "end_lineno", None)))
for name, lo, hi in func_hits:
    report.append(f"{name}: lines {lo}-{hi}")
if not func_hits:
    report.append("(none)")
report.append("")

# 4) replay/tape/router構造の手掛かり
report.append("=== ARCHITECTURE KEYWORDS ===")
keywords = [
    "replay", "trajectory", "route", "snapshot", "expert",
    "nearest", "distance", "BUY_LAND", "market_actions",
]
for kw in keywords:
    count = text.lower().count(kw.lower())
    report.append(f"{kw:16s}: {count}")

OUT.write_text("\n".join(report) + "\n", encoding="utf-8")

print("\n".join(report))
print()
print(f"✅ 保存: {OUT}")
print("このファイルをそのままChatGPTに添付すればよいです。")
