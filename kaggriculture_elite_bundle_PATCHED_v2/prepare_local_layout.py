"""
prepare_local_layout.py

Run from inside the extracted elite bundle when that bundle is a subdirectory
of the main Kaggle project.

It exposes the parent's existing benchmark assets without modifying them.
Existing bundle-local public_agents/elite downloads are preserved.
"""
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent


def link_or_copy(src: Path, dst: Path):
    if dst.exists() or dst.is_symlink():
        print(f"[ok] already exists: {dst}")
        return
    if not src.exists():
        print(f"[missing] {src}")
        return
    try:
        dst.symlink_to(src, target_is_directory=src.is_dir())
        print(f"[link] {dst} -> {src}")
    except Exception:
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        print(f"[copy] {src} -> {dst}")


def main():
    parent_pub = PARENT / "public_agents"
    local_pub = HERE / "public_agents"
    local_pub.mkdir(parents=True, exist_ok=True)

    # Merge individual public-agent directories. This preserves bundle-local
    # public_agents/elite created by setup_elite_candidates.py.
    if parent_pub.exists():
        for src in sorted(parent_pub.iterdir()):
            if src.name == "elite":
                continue
            link_or_copy(src, local_pub / src.name)
    else:
        print(f"[missing] {parent_pub}")

    link_or_copy(PARENT / "agent_v15.py", HERE / "agent_v15.py")
    link_or_copy(PARENT / "agent_v11.py", HERE / "agent_v11.py")

    elite = local_pub / "elite"
    elite.mkdir(parents=True, exist_ok=True)

    print("\nLayout preparation complete.")
    print("You can now authenticate/fetch elite artifacts, then run the arena.")


if __name__ == "__main__":
    main()
