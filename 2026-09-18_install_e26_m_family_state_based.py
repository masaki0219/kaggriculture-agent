#!/usr/bin/env python3
"""Install E26 — state-based M-family agent."""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import base64, hashlib, textwrap, zlib

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
TARGET = BUNDLE / "agent_e26_m_family_state_based.py"
EXP_DIR = ROOT / "experiments" / "e026_m_family_state_based"
README = EXP_DIR / "README.md"
INDEX = ROOT / "docs" / "experiment_index.md"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"

AGENT_B64 = """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"""
EXPECTED_SHA = "7d73f68353dcd7cd868e1e72b552acae9026e39894064f56a2243ed3cd69c967"

def main():
    print("=== Install E26: state-based M-family agent ===")
    print("Repository root:", ROOT)

    if not BUNDLE.exists():
        raise SystemExit("Run from the Kaggle repository root.")

    text = zlib.decompress(base64.b64decode(AGENT_B64)).decode("utf-8")
    compile(text, str(TARGET), "exec")
    actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if actual != EXPECTED_SHA:
        raise SystemExit(f"Hash mismatch: {actual} != {EXPECTED_SHA}")

    TARGET.write_text(text, encoding="utf-8")

    EXP_DIR.mkdir(parents=True, exist_ok=True)
    README.write_text(textwrap.dedent(f"""\
    # E26 — State-based M-family agent

    This is the strategy the E23→E25 work was intended to reach.

    **No replay action sequence is used.**

    The agent implements M-family mechanisms inferred from the 84-run corpus:

    - opening family: 4 hands / 2 cows / 3 sheep / 6 melons / ~10 wheat;
    - second land after shop 2 (~step 150);
    - third land after shop 3 (~step 220);
    - MILK demand changes cow target;
    - WOOL demand changes sheep target;
    - EGG demand changes goose target;
    - strawberry / tomato / carrot acreage changes with shop demand;
    - wheat fills residual acreage;
    - current state determines BUILD / BUY / PLANT / FEED / CARE / HARVEST jobs;
    - nearest available units execute jobs;
    - market orders use live state only.

    E23/E24/E25 remain immutable historical experiments.

    SHA256: `{actual}`
    """), encoding="utf-8")

    if INDEX.exists():
        txt = INDEX.read_text(encoding="utf-8")
        if "| E26 |" not in txt:
            row = (
                "| E26 | State-based M-family planner/executor; no replay actions | "
                "`artifacts/bundles/current/agent_e26_m_family_state_based.py` | "
                "smoke pending | independent M-family candidate | "
                "84-run policy inference: 4H/2C3S/M6, shop-conditioned targets, live planner |\n"
            )
            marker = "\n## Legacy non-E series"
            if marker in txt:
                txt = txt.replace(marker, "\n"+row+marker)
            else:
                txt = txt.rstrip()+"\n"+row
            INDEX.write_text(txt, encoding="utf-8")

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {now} — Install E26 state-based M-family agent\n\n"
            f"- Agent: `{TARGET.relative_to(ROOT)}`\n"
            f"- SHA256: `{actual}`\n"
            "- No replay/tape actions used.\n"
            "- Targets inferred from 84 M-family replay runs.\n"
            "- Current observation drives planning/execution/market.\n"
            "- E23/E24/E25 are not overwritten.\n"
            "- No Kaggle submission performed.\n\n"
        )

    print("Wrote:", TARGET.relative_to(ROOT))
    print("SHA256:", actual)
    print("Wrote:", README.relative_to(ROOT))
    print("=== E26 install complete ===")

if __name__ == "__main__":
    main()
