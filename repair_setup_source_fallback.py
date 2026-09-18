from __future__ import annotations

import argparse
from pathlib import Path
import shutil

HELPER = r'''
def extract_notebook_writefiles(base: Path) -> list[Path]:
    """Extract Python payloads from notebook %%writefile cells.

    Kaggle kernels output is sometimes only a .log even though the notebook
    source contains the actual submission as ``%%writefile main.py``.  We only
    extract explicit writefile cells; we do not concatenate arbitrary notebook
    cells because that could silently benchmark a different program.
    """
    extracted: list[Path] = []
    for nb in base.rglob("*.ipynb"):
        try:
            data = json.loads(nb.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[warn] could not read notebook {nb}: {e}")
            continue
        for i, cell in enumerate(data.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            src = cell.get("source", [])
            text = "".join(src) if isinstance(src, list) else str(src)
            lines = text.splitlines()
            first_idx = next((j for j, line in enumerate(lines) if line.strip()), None)
            if first_idx is None:
                continue
            first = lines[first_idx].strip()
            if not first.startswith("%%writefile "):
                continue
            target = first[len("%%writefile "):].strip().strip("'\"")
            name = Path(target).name
            if not name.endswith(".py"):
                continue
            out = base / "_notebook_extract" / nb.stem / name
            out.parent.mkdir(parents=True, exist_ok=True)
            payload = "\n".join(lines[first_idx + 1:]) + "\n"
            try:
                compile(payload, str(out), "exec")
            except Exception as e:
                print(f"[warn] skip non-compiling %%writefile cell {nb}#{i}: {e}")
                continue
            out.write_text(payload, encoding="utf-8")
            print(f"[extract] {nb.name} cell {i} -> {out}")
            extracted.append(out)
    return extracted

'''

OLD_BLOCK = '''        # If kernel output does not contain an executable .py, pull notebook
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
                f"No executable agent .py found for {name} in {raw}.\\n"
                f"Inspect {raw} / {source_dir} and choose the actual output."
            )
'''

NEW_BLOCK = '''        # Some public notebooks expose no .py in `kernels output` (only a log),
        # while the pulled notebook source contains the exact submission in a
        # Python file or an explicit `%%writefile main.py` cell.  Fall back to
        # those two source forms only; never concatenate arbitrary cells.
        if entry is None:
            source_dir = base / "source"
            source_dir.mkdir(exist_ok=True)
            run([
                "kaggle", "kernels", "pull",
                meta["kernel"],
                "-p", source_dir,
                "-m",
            ])
            extract_archives(source_dir)
            entry = choose_entry(source_dir)
            if entry is None:
                extract_notebook_writefiles(source_dir)
                entry = choose_entry(source_dir)
            if entry is None:
                raise SystemExit(
                    f"No executable agent .py found for {name}.\\n"
                    f"Checked Kaggle output {raw}, source {source_dir}, and explicit "
                    "notebook %%writefile Python payloads."
                )
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()
    repo = Path(args.repo).expanduser().resolve()
    setup = repo / "artifacts" / "bundles" / "current" / "setup_elite_candidates.py"
    if not setup.exists():
        raise SystemExit(f"missing {setup}")

    text = setup.read_text(encoding="utf-8")
    changed = False

    if "def extract_notebook_writefiles(" not in text:
        marker = "\ndef main():\n"
        if marker not in text:
            raise SystemExit("could not locate def main() in setup script")
        text = text.replace(marker, "\n" + HELPER + "def main():\n", 1)
        changed = True

    if OLD_BLOCK in text:
        text = text.replace(OLD_BLOCK, NEW_BLOCK, 1)
        changed = True
    elif "Checked Kaggle output" not in text:
        raise SystemExit(
            "setup fallback block differs from the expected version; refusing a blind edit"
        )

    if changed:
        backup = setup.with_suffix(setup.suffix + ".pre_source_fallback")
        if not backup.exists():
            shutil.copy2(setup, backup)
            print(f"backup: {backup}")
        setup.write_text(text, encoding="utf-8")
        print(f"patch:  {setup}")
    else:
        print(f"skip:   source fallback already installed in {setup}")

    compile(setup.read_text(encoding="utf-8"), str(setup), "exec")
    print("ok: setup_elite_candidates.py compiles")


if __name__ == "__main__":
    main()
