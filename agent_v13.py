"""
agent_v13.py

Controlled candidate built on the same public Seyamalam baseline as v12.

Hypothesis
----------
When the opponent is clearly ahead in production scale during the early/midgame,
bring already-planned capital spending forward.

Only one mechanism is changed:
- enable opponent-aware capital-order prioritization
- trigger when:
    * opponent animals >= our animals + 2, OR
    * opponent land >= our land + 1
    * only through day 12

COW/SHEEP type rewriting is deliberately disabled so this experiment isolates
capital timing only.

Base source:
    Seyamalam/Kaggriculture - main.py
    SPDX-License-Identifier: Apache-2.0
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


def _load_candidate_agent():
    if not _BASE.exists():
        raise FileNotFoundError(
            "Seyamalam public agent was not found at "
            f"{_BASE}. Run the public-agent clone/setup first."
        )

    spec = importlib.util.spec_from_file_location(
        "_agent13_seyamalam_base",
        _BASE,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load public agent: {_BASE}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    strategy = getattr(module, "STRATEGY", None)
    if not isinstance(strategy, dict):
        raise AttributeError(f"{_BASE} does not expose a STRATEGY dict")

    # Activate the existing observation-only overlay.
    strategy["fixed_board_adaptation"] = True

    # v13's only intended behavior change:
    # bring existing capital orders forward when the rival is scaling faster.
    strategy["adaptive_capital_priority"] = True
    strategy["adaptive_capital_max_day"] = 12
    strategy["adaptive_capital_animal_lead"] = 2
    strategy["adaptive_capital_land_lead"] = 1

    # Disable COW/SHEEP portfolio rewriting inside the same overlay.
    # This impossible day window makes adaptive animal focus never activate.
    strategy["adaptive_animal_min_day"] = 999
    strategy["adaptive_animal_max_day"] = -1

    base = getattr(module, "agent", None)
    if base is None:
        raise AttributeError(
            f"{_BASE} does not expose a top-level agent(obs) function."
        )

    return base


_CANDIDATE_AGENT = _load_candidate_agent()


def agent(obs, config=None):
    """v13 candidate: v12 baseline + conditional capital-order prioritization."""
    return _CANDIDATE_AGENT(obs)


melon_maxxer = agent
