"""
agent_v12.py

Public-agent baseline for our next Kaggriculture development line.

Base:
    Seyamalam/Kaggriculture - main.py
    Copyright (c) 2026 Touhidul Alam Seyam
    MIT License

This wrapper intentionally delegates to the locally cloned public agent without
modifying its behavior.  It gives us a clean `agent_v12.py` name for subsequent
controlled changes while preserving the original public agent separately under:

    public_agents/seyamalam/main.py

IMPORTANT:
- This wrapper is for LOCAL DEVELOPMENT / BENCHMARKING.
- Before Kaggle submission, vendor the MIT-licensed implementation into a
  self-contained `agent_v12.py` (with copyright/license notice retained),
  because Kaggle will not have the local `public_agents/` directory.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


_BASE = (
    Path(__file__).resolve().parent
    / "public_agents"
    / "seyamalam"
    / "main.py"
)


def _load_base_agent():
    if not _BASE.exists():
        raise FileNotFoundError(
            "Seyamalam public agent was not found at "
            f"{_BASE}. Run the public-agent clone/setup first."
        )

    spec = importlib.util.spec_from_file_location(
        "_agent12_seyamalam_base",
        _BASE,
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load public agent: {_BASE}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    base = getattr(module, "agent", None)
    if base is None:
        raise AttributeError(
            f"{_BASE} does not expose a top-level agent(obs) function."
        )

    return base


_BASE_AGENT = _load_base_agent()


def agent(obs, config=None):
    """
    v12 baseline.

    For now this is intentionally behavior-identical to the public Seyamalam
    agent.  Future v12.x experiments should change one mechanism at a time.
    """
    return _BASE_AGENT(obs)


# Compatibility with our earlier local comparison scripts.
melon_maxxer = agent
