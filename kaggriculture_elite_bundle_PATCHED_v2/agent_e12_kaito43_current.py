"""
E12 — exact current Kaito v43 Sparse Shop Hybrid
Frozen wrapper. No strategy modification.
"""
from elite_runtime import load_agent, call_agent
_BASE = load_agent("kaito43_current")
def agent(obs, configuration=None):
    return call_agent(_BASE, obs, configuration)
melon_maxxer = agent
