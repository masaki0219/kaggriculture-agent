"""
E7 — Tetsu Shape benchmark wrapper (license verify before submission)
Frozen wrapper. No strategy modification.
"""
from elite_runtime import load_agent, call_agent
_BASE = load_agent("tetsu_shape")
def agent(obs, configuration=None):
    return call_agent(_BASE, obs, configuration)
melon_maxxer = agent
