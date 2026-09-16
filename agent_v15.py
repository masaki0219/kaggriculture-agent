"""
agent_v15.py

Frozen local baseline: Kaito Fukami v48 Fast Routes.

No strategy changes are added here. This wrapper exists only to give the
new baseline a stable local name for future A/B experiments.

Expected source:
  public_agents/hbharath/agents/public/kaitofukami_v48_fast_routes.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_SOURCE = (
    Path(__file__).resolve().parent
    / "public_agents"
    / "hbharath"
    / "agents"
    / "public"
    / "kaitofukami_v48_fast_routes.py"
)

def _load():
    if not _SOURCE.exists():
        raise FileNotFoundError(
            "Kaito v48 baseline not found. Expected:\n"
            f"  {_SOURCE}\n"
            "Run setup_bulk_candidates.sh first."
        )

    spec = importlib.util.spec_from_file_location("_agent_v15_kaito_v48", _SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {_SOURCE}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    fn = getattr(module, "agent", None)
    if not callable(fn):
        raise AttributeError(f"{_SOURCE} does not expose callable agent")
    return fn

_BASE_AGENT = _load()

def agent(obs, configuration=None):
    """Behavior-identical wrapper around the frozen Kaito v48 public artifact."""
    try:
        return _BASE_AGENT(obs, configuration)
    except TypeError:
        return _BASE_AGENT(obs)

melon_maxxer = agent
