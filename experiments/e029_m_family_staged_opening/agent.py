"""Forward to the frozen canonical E29 agent in the current bundle."""

from pathlib import Path
import sys

_BUNDLE = Path(__file__).resolve().parents[2] / "artifacts" / "bundles" / "current"
sys.path.insert(0, str(_BUNDLE))

from agent_e29_m_family_staged_opening import agent, melon_maxxer  # noqa: E402

__all__ = ["agent", "melon_maxxer"]
