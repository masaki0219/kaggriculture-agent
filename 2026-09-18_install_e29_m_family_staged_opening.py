#!/usr/bin/env python3
"""Install E29 — staged-opening state-based M-family agent."""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import base64, hashlib, textwrap, zlib

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
TARGET = BUNDLE / "agent_e29_m_family_staged_opening.py"
EXP_DIR = ROOT / "experiments" / "e029_m_family_staged_opening"
README = EXP_DIR / "README.md"
INDEX = ROOT / "docs" / "experiment_index.md"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"

AGENT_B64 = """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"""
EXPECTED_SHA = "3fc5bf1fce809adc9aab3747b99990d2d2b2dcf35f037552b35fc8be7e0a7de0"

def main():
    print("=== Install E29: staged-opening M-family ===")
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
    # E29 — Staged-opening state-based M-family

    E29 returns to E27, the last economically viable state-based baseline, and
    fixes the opening using direct population evidence.

    Key reconstructed mechanism:

    - `4H / 2C3S / M6 / W~10` is a **day-0 aggregate**, not a single-turn buy.
    - common opening starts with `BUY_PRODUCT WHEAT 5 + COW 1`;
    - next turn adds `HIRE x4 + COW 1 + SHEEP 3`;
    - melon seed is accumulated in 2-unit tranches;
    - wheat seed is accumulated gradually with remaining cash;
    - later capital remains independent from whether the full hand target was met.

    Replay-derived crop checkpoints:
    - step23: crops ~15.5
    - step47: crops ~19.5
    - step71: crops ~20
    - step143: crops ~20
    - step167: crops ~33
    - step215: crops ~38
    - step239: crops ~53
    - step287: crops ~58.5

    From day6 onward, total production scale is separated from first-four-shop
    composition routing.

    No replay action sequence is used.

    SHA256: `{actual}`
    """), encoding="utf-8")

    if INDEX.exists():
        txt = INDEX.read_text(encoding="utf-8")
        if "| E29 |" not in txt:
            row = (
                "| E29 | Staged-opening state-based M-family | "
                "`artifacts/bundles/current/agent_e29_m_family_staged_opening.py` | "
                "opening-fidelity smoke pending | independent M-family candidate | "
                "E27 economics + inferred staged M opening + scale/composition routing |\n"
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
            f"## {now} — Install E29 staged-opening M-family\n\n"
            f"- Agent: `{TARGET.relative_to(ROOT)}`\n"
            f"- SHA256: `{actual}`\n"
            "- Based on E27, not E28.\n"
            "- Reconstructs M opening as staged cashflow rather than lump purchase.\n"
            "- No replay action routing used.\n"
            "- E23-E28 remain immutable.\n"
            "- No Kaggle submission performed.\n\n"
        )

    print("Wrote:", TARGET.relative_to(ROOT))
    print("SHA256:", actual)
    print("Wrote:", README.relative_to(ROOT))
    print("=== E29 install complete ===")

if __name__ == "__main__":
    main()
