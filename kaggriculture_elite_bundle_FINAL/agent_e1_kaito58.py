"""
E1 — exact public Kaito v58
Frozen wrapper. No strategy modification.
"""
from elite_runtime import load_agent, call_agent
_BASE = load_agent("kaito58")
def agent(obs, configuration=None):
    return call_agent(_BASE, obs, configuration)
melon_maxxer = agent
