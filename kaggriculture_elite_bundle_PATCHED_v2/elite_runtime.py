from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parent
ELITE_ROOT = ROOT / "public_agents" / "elite"

CALLABLE_NAMES = (
    "agent",
    "kaggle_submission_agent",
    "submission_agent",
    "melon_maxxer",
    "policy",
)

def _entrypoint(name: str) -> Path:
    base = ELITE_ROOT / name
    marker = base / "entrypoint.txt"
    if not marker.exists():
        raise FileNotFoundError(
            f"{marker} not found. Run setup_elite_candidates.py first."
        )
    rel = marker.read_text(encoding="utf-8").strip()
    path = (base / rel).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return path

def load_agent(name: str):
    path = _entrypoint(name)
    artifact_root = path.parent

    for p in (artifact_root, artifact_root.parent, artifact_root.parent.parent):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)

    module_name = f"_elite_{name}_{uuid.uuid4().hex}"
    old = Path.cwd()
    try:
        os.chdir(artifact_root)
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not import {path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
    finally:
        os.chdir(old)

    for fn_name in CALLABLE_NAMES:
        fn = getattr(mod, fn_name, None)
        if callable(fn):
            return fn

    raise AttributeError(
        f"{path} exposes none of {CALLABLE_NAMES}"
    )

def call_agent(fn, obs, configuration=None):
    try:
        return fn(obs, configuration)
    except TypeError:
        return fn(obs)
