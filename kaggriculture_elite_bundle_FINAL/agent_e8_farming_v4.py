"""
E8 — Farming Score V4 benchmark wrapper (license verify before submission)
Frozen wrapper. No strategy modification.
"""
from elite_runtime import load_agent, call_agent
_BASE = load_agent("farming_v4")
def agent(obs, configuration=None):
    return call_agent(_BASE, obs, configuration)
melon_maxxer = agent
