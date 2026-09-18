"""
E21 — exact Tetsu Market-Smart Farming V23.

Frozen exact public baseline.
No strategy modification.

Purpose:
Replace E11 as the current frontier reference for subsequent experiments.

Important:
This is NOT a final-submission decision.
"""

from elite_runtime import load_agent, call_agent

_BASE = load_agent("tetsu_market_v23_current")


def agent(obs, configuration=None):
    return call_agent(_BASE, obs, configuration)


melon_maxxer = agent
