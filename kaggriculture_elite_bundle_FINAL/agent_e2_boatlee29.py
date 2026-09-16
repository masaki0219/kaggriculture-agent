"""
E2 — exact public Boatlee v29-R1
Frozen wrapper. No strategy modification.
"""
from elite_runtime import load_agent, call_agent
_BASE = load_agent("boatlee29")
def agent(obs, configuration=None):
    return call_agent(_BASE, obs, configuration)
melon_maxxer = agent
