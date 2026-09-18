#!/usr/bin/env python3
"""
2026-09-18 — Repair Ahmed V44 exact local artifact

Place this file directly in the Kaggle repository root and run:

    python 2026-09-18_repair_ahmed_v44.py

Purpose
-------
Reconstruct the exact executable submission source from the downloaded
Ahmed V44 Kaggle notebook source.

Why:
The earlier extraction selected a notebook build cell rather than the generated
submission file, causing `NameError: WORKDIR is not defined`.

This script:
1. Reads the downloaded Ahmed V44 .ipynb.
2. Replays code cells in a controlled local build directory.
3. Rewrites notebook WORKDIR assignments to that local directory.
4. Skips notebook magics/shell lines.
5. Collects generated .py files and large Python source strings.
6. Selects an executable agent candidate conservatively.
7. Writes entrypoint.txt.
8. Imports the chosen file and verifies a known agent callable exists.
9. Writes a root-level diagnostic report and run history.

It does NOT submit anything to Kaggle.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import ast
import builtins
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import traceback

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "artifacts" / "bundles" / "current" / "public_agents" / "elite" / "ahmed_v44_current"
SOURCE_DIR = BASE / "source"
BUILD_DIR = BASE / "notebook_rebuild"
ENTRYPOINT = BASE / "entrypoint.txt"
REPORT = ROOT / "2026-09-18_AHMED_V44_REPAIR_REPORT.md"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"

CALLABLE_NAMES = (
    "agent",
    "kaggle_submission_agent",
    "submission_agent",
    "melon_maxxer",
    "policy",
    "kaggriculture_e776_agent",
)

DANGEROUS_CALL_NAMES = {
    "rmtree",
    "unlink",
    "remove",
    "removedirs",
    "system",
    "popen",
    "run",
    "call",
    "check_call",
    "check_output",
}

def strip_magics(code: str) -> str:
    out = []
    for line in code.splitlines():
        s = line.lstrip()
        if s.startswith(("!", "%", "?")):
            out.append("# stripped notebook magic/shell: " + line)
        elif "get_ipython()" in line:
            out.append("# stripped get_ipython call")
        else:
            out.append(line)
    return "\n".join(out)

class WorkdirTransformer(ast.NodeTransformer):
    """Redirect obvious WORKDIR assignments into our local build directory."""

    def __init__(self):
        super().__init__()
        self.rewrites = 0

    def _is_workdir_target(self, target):
        return isinstance(target, ast.Name) and target.id == "WORKDIR"

    def visit_Assign(self, node):
        self.generic_visit(node)
        if any(self._is_workdir_target(t) for t in node.targets):
            self.rewrites += 1
            node.value = ast.Name(id="_LOCAL_WORKDIR", ctx=ast.Load())
        return node

    def visit_AnnAssign(self, node):
        self.generic_visit(node)
        if self._is_workdir_target(node.target):
            self.rewrites += 1
            node.value = ast.Name(id="_LOCAL_WORKDIR", ctx=ast.Load())
        return node

def has_agent_token(text: str) -> bool:
    return any(
        re.search(rf"\bdef\s+{re.escape(name)}\s*\(", text)
        for name in CALLABLE_NAMES
    )

def compile_ok(text: str) -> bool:
    try:
        compile(text, "<candidate>", "exec")
        return True
    except Exception:
        return False

def static_risk_reasons(tree: ast.AST):
    reasons = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = None
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            if name in DANGEROUS_CALL_NAMES:
                # We allow Path.write_text / file writing indirectly because the
                # whole point is to reconstruct generated submission source.
                if name in {"run", "call", "check_call", "check_output", "system", "popen"}:
                    reasons.append(f"external-process call: {name}")
                elif name in {"rmtree", "unlink", "remove", "removedirs"}:
                    reasons.append(f"destructive filesystem call: {name}")
    return sorted(set(reasons))

def candidate_info(path: Path, origin: str):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    if not has_agent_token(text) or not compile_ok(text):
        return None
    return {
        "path": path,
        "origin": origin,
        "size": len(text.encode("utf-8")),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text": text,
    }

def import_validate(path: Path):
    parent = str(path.parent)
    bundle = str(ROOT / "artifacts" / "bundles" / "current")
    for p in (parent, bundle):
        if p not in sys.path:
            sys.path.insert(0, p)

    name = "_ahmed_v44_validation"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not build import spec")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)

    found = []
    for callable_name in CALLABLE_NAMES:
        obj = getattr(mod, callable_name, None)
        if callable(obj):
            found.append(callable_name)
    if not found:
        raise AttributeError(f"no known callable found in {path}")
    return found

def main():
    print("=== Repair Ahmed V44 exact local artifact ===")
    print("Repository root:", ROOT)

    notebooks = sorted(SOURCE_DIR.rglob("*.ipynb"))
    if len(notebooks) != 1:
        raise SystemExit(f"Expected exactly 1 Ahmed notebook, got {len(notebooks)}: {notebooks}")

    nb_path = notebooks[0]
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    print("Notebook:", nb_path.relative_to(ROOT))

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # Controlled namespace. We intentionally do not try to fake Kaggle itself.
    ns = {
        "__name__": "__ahmed_v44_rebuild__",
        "__file__": str(nb_path),
        "_LOCAL_WORKDIR": BUILD_DIR,
        "WORKDIR": BUILD_DIR,
        "Path": Path,
    }

    cell_log = []
    string_candidates = []

    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue

        raw = "".join(cell.get("source", []))
        clean = strip_magics(raw)

        try:
            tree = ast.parse(clean, filename=f"{nb_path.name}:cell{i}")
        except SyntaxError as e:
            cell_log.append({
                "cell": i,
                "status": "syntax-skip",
                "detail": str(e),
            })
            continue

        risks = static_risk_reasons(tree)
        # Do not execute cells that launch external processes or delete files.
        if risks:
            cell_log.append({
                "cell": i,
                "status": "risk-skip",
                "detail": "; ".join(risks),
            })
            continue

        transformer = WorkdirTransformer()
        tree = transformer.visit(tree)
        ast.fix_missing_locations(tree)

        before_keys = set(ns)

        try:
            code = compile(tree, f"{nb_path.name}:cell{i}", "exec")
            exec(code, ns, ns)
            status = "ok"
            detail = f"WORKDIR rewrites={transformer.rewrites}"
        except Exception as e:
            status = "exec-error"
            detail = f"{type(e).__name__}: {e}"

        # Enforce local workdir even if notebook code changed it indirectly.
        ns["WORKDIR"] = BUILD_DIR
        ns["_LOCAL_WORKDIR"] = BUILD_DIR

        new_keys = sorted(set(ns) - before_keys)
        for key in new_keys:
            value = ns.get(key)
            if isinstance(value, str) and len(value) >= 1000 and has_agent_token(value) and compile_ok(value):
                p = BUILD_DIR / f"namespace_{i}_{re.sub(r'[^A-Za-z0-9_.-]+', '_', key)}.py"
                p.write_text(value, encoding="utf-8")
                string_candidates.append((p, f"namespace:{key}@cell{i}"))

        # Also scan all current namespace strings because builders sometimes
        # mutate/reassign an existing variable rather than create a new one.
        for key, value in list(ns.items()):
            if (
                isinstance(value, str)
                and len(value) >= 10000
                and has_agent_token(value)
                and compile_ok(value)
            ):
                p = BUILD_DIR / f"namespace_latest_{re.sub(r'[^A-Za-z0-9_.-]+', '_', key)}.py"
                p.write_text(value, encoding="utf-8")

        cell_log.append({
            "cell": i,
            "status": status,
            "detail": detail,
            "first_line": next((x.strip() for x in raw.splitlines() if x.strip()), "")[:180],
        })

    # Collect generated files first. They are much more trustworthy than raw cells.
    candidates = []
    seen_sha = set()

    for p in sorted(BUILD_DIR.rglob("*.py")):
        info = candidate_info(p, "generated/build")
        if info and info["sha256"] not in seen_sha:
            seen_sha.add(info["sha256"])
            candidates.append(info)

    for p, origin in string_candidates:
        info = candidate_info(p, origin)
        if info and info["sha256"] not in seen_sha:
            seen_sha.add(info["sha256"])
            candidates.append(info)

    # Last-resort: exact code-cell candidates, but rank below generated files.
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        raw = strip_magics("".join(cell.get("source", [])))
        if has_agent_token(raw) and compile_ok(raw):
            p = BUILD_DIR / f"raw_cell_{i}.py"
            p.write_text(raw, encoding="utf-8")
            info = candidate_info(p, f"raw-cell:{i}")
            if info and info["sha256"] not in seen_sha:
                seen_sha.add(info["sha256"])
                candidates.append(info)

    if not candidates:
        REPORT.write_text(
            "# Ahmed V44 Repair Report\n\nNo executable agent candidate was reconstructed.\n",
            encoding="utf-8",
        )
        raise SystemExit(f"No executable candidate found. See {REPORT.name}")

    def rank(c):
        generated = 1 if c["origin"].startswith(("generated/", "namespace:")) else 0
        # Prefer real generated source, then larger complete source.
        return (generated, c["size"])

    candidates.sort(key=rank, reverse=True)

    validations = []
    chosen = None
    for c in candidates:
        try:
            found = import_validate(c["path"])
            validations.append((c, True, ", ".join(found)))
            if chosen is None:
                chosen = c
                chosen["callables"] = found
        except Exception as e:
            validations.append((c, False, f"{type(e).__name__}: {e}"))

    now = datetime.now().astimezone().isoformat(timespec="seconds")

    report = [
        "# Ahmed V44 Repair Report",
        "",
        f"- Generated: `{now}`",
        f"- Notebook: `{nb_path.relative_to(ROOT)}`",
        f"- Build dir: `{BUILD_DIR.relative_to(ROOT)}`",
        f"- Candidates: **{len(candidates)}**",
        "",
        "## Cell replay",
        "",
        "| Cell | Status | Detail | First line |",
        "|---:|---|---|---|",
    ]
    for rec in cell_log:
        report.append(
            f"| {rec['cell']} | {rec['status']} | "
            f"{str(rec.get('detail','')).replace('|','/')} | "
            f"{str(rec.get('first_line','')).replace('|','/')} |"
        )

    report += [
        "",
        "## Candidate validation",
        "",
        "| Rank | Origin | Relative path | Bytes | SHA256 | Import | Detail |",
        "|---:|---|---|---:|---|---|---|",
    ]
    for idx, (c, ok, detail) in enumerate(validations, start=1):
        try:
            rel = c["path"].relative_to(ROOT)
        except Exception:
            rel = c["path"]
        report.append(
            f"| {idx} | {c['origin']} | `{rel}` | {c['size']} | "
            f"`{c['sha256']}` | {'OK' if ok else 'FAIL'} | "
            f"{detail.replace('|','/')} |"
        )

    if chosen is None:
        report += [
            "",
            "## Result",
            "",
            "**FAILED:** candidates were found but none imported with a known agent callable.",
            "",
        ]
        REPORT.write_text("\n".join(report), encoding="utf-8")
        raise SystemExit(f"Ahmed repair failed import validation. See {REPORT.name}")

    final_dir = BASE / "notebook_extract"
    final_dir.mkdir(parents=True, exist_ok=True)
    final_path = final_dir / "main.py"
    final_path.write_text(chosen["text"], encoding="utf-8")

    # Validate the final copy, not only the build candidate.
    final_callables = import_validate(final_path)

    ENTRYPOINT.write_text(
        str(final_path.relative_to(BASE)),
        encoding="utf-8",
    )

    report += [
        "",
        "## Result",
        "",
        "**SUCCESS**",
        "",
        f"- Chosen origin: `{chosen['origin']}`",
        f"- Final entrypoint: `{final_path.relative_to(BASE)}`",
        f"- SHA256: `{hashlib.sha256(final_path.read_bytes()).hexdigest()}`",
        f"- Callables: {', '.join(f'`{x}`' for x in final_callables)}",
        "",
        "The artifact is now ready for a fresh frontier-screen smoke test.",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {now} — Repair Ahmed V44 artifact\n\n"
            f"- Notebook: `{nb_path.relative_to(ROOT)}`\n"
            f"- Final entrypoint: `{final_path.relative_to(ROOT)}`\n"
            f"- SHA256: `{hashlib.sha256(final_path.read_bytes()).hexdigest()}`\n"
            f"- Callables: {', '.join(final_callables)}\n"
            f"- Report: `{REPORT.name}`\n"
            "- No Kaggle submission performed.\n\n"
        )

    print()
    print("=== Ahmed V44 repair complete ===")
    print("Entrypoint:", final_path.relative_to(BASE))
    print("SHA256:", hashlib.sha256(final_path.read_bytes()).hexdigest())
    print("Callables:", ", ".join(final_callables))
    print("Report:", REPORT.name)

if __name__ == "__main__":
    main()
