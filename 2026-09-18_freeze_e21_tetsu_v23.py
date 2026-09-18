#!/usr/bin/env python3
"""
2026-09-18 — Freeze E21: Tetsu Market-Smart Farming V23

Place this file directly in the Kaggle repository root and run:

    python 2026-09-18_freeze_e21_tetsu_v23.py

What it does:
1. Verifies the downloaded Tetsu V23 artifact.
2. Computes its SHA256.
3. Creates artifacts/bundles/current/agent_e21_tetsu_market_v23.py
4. Adds E21 to docs/experiment_index.md if needed.
5. Appends a record to EXPERIMENT_RUN_HISTORY.md

This does not submit anything to Kaggle.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parent

SOURCE = (
    ROOT / "artifacts" / "bundles" / "current"
    / "public_agents" / "elite" / "tetsu_market_v23_current"
    / "raw" / "_extract_submission_tar" / "main.py"
)

WRAPPER = (
    ROOT / "artifacts" / "bundles" / "current"
    / "agent_e21_tetsu_market_v23.py"
)

INDEX = ROOT / "docs" / "experiment_index.md"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"


def fail(msg: str) -> None:
    raise SystemExit(f"\nERROR: {msg}\n")


def main() -> None:
    print("=== Freeze E21: Tetsu Market-Smart Farming V23 ===")
    print("Repository root:", ROOT)

    if not (ROOT / "artifacts").exists():
        fail("artifacts/ not found. Put this script in the Kaggle repository root.")

    if not SOURCE.exists():
        fail(f"Tetsu V23 artifact not found:\n  {SOURCE}")

    if not INDEX.exists():
        fail(f"experiment index not found: {INDEX}")

    sha256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

    print("Source:", SOURCE.relative_to(ROOT))
    print("SHA256:", sha256)

    wrapper_text = '''"""
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
'''

    WRAPPER.parent.mkdir(parents=True, exist_ok=True)
    WRAPPER.write_text(wrapper_text, encoding="utf-8")
    print("Wrote:", WRAPPER.relative_to(ROOT))

    index_text = INDEX.read_text(encoding="utf-8")
    row = (
        "| E21 | Tetsu Market-Smart Farming V23 exact public agent; "
        "new frontier baseline | "
        "`artifacts/bundles/current/agent_e21_tetsu_market_v23.py` | "
        "`evaluation/frontier_screen_v2/arena.py` | "
        "frontier screen seeds 18000-18007, both seats | "
        "frozen frontier baseline / not yet final-submission decision |\n"
    )

    if "| E21 |" not in index_text:
        marker = "\n## Legacy non-E series"
        if marker not in index_text:
            fail("Could not find insertion point in docs/experiment_index.md")
        index_text = index_text.replace(marker, "\n" + row + marker)
        INDEX.write_text(index_text, encoding="utf-8")
        print("Updated:", INDEX.relative_to(ROOT))
    else:
        print("E21 already exists in experiment index; left unchanged.")

    if not HISTORY.exists():
        HISTORY.write_text(
            "# Experiment Run History\n\n"
            "Root-level lightweight execution history.\n\n",
            encoding="utf-8",
        )

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    history_entry = f'''## {now} — Freeze E21: Tetsu Market-Smart Farming V23

- Action: froze exact public Tetsu Market-Smart Farming V23 as E21 baseline.
- Source: `artifacts/bundles/current/public_agents/elite/tetsu_market_v23_current/raw/_extract_submission_tar/main.py`
- SHA256: `{sha256}`
- Wrapper: `artifacts/bundles/current/agent_e21_tetsu_market_v23.py`
- Evaluation basis: Frontier Screen V2, seeds 18000-18007, both seats.
- Interpretation: E21 becomes the current frontier reference; this is not a final-submission decision.
- No Kaggle submission was performed.

'''

    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(history_entry)

    print("Appended history:", HISTORY.relative_to(ROOT))
    print("\nE21 frozen successfully.")


if __name__ == "__main__":
    main()
