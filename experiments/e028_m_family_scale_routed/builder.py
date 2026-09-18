#!/usr/bin/env python3
"""Install E28 — scale-routed state-based M-family agent."""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import base64, hashlib, textwrap, zlib

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
TARGET = BUNDLE / "agent_e28_m_family_scale_routed.py"
EXP_DIR = ROOT / "experiments" / "e028_m_family_scale_routed"
README = EXP_DIR / "README.md"
INDEX = ROOT / "docs" / "experiment_index.md"
HISTORY = ROOT / "docs" / "experiment_run_history.md"

AGENT_B64 = """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"""
EXPECTED_SHA = "295a1cd80b5779e152b0f6cd796a79982e3e3617b25ba3651b10c80a17a1612a"

def main():
    print("=== Install E28: scale-routed M-family ===")
    print("Repository root:", ROOT)

    if not BUNDLE.exists():
        raise SystemExit(f"Missing bundle directory: {BUNDLE}")

    text = zlib.decompress(base64.b64decode(AGENT_B64)).decode("utf-8")
    compile(text, str(TARGET), "exec")
    actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if actual != EXPECTED_SHA:
        raise SystemExit(f"Hash mismatch: {actual} != {EXPECTED_SHA}")

    TARGET.write_text(text, encoding="utf-8")

    EXP_DIR.mkdir(parents=True, exist_ok=True)
    README.write_text(textwrap.dedent(f"""\
    # E28 — Scale-routed state-based M-family

    E28 keeps the no-replay-action architecture and separates two mechanisms
    observed in the 84-run current M-family corpus:

    1. **total production scale trajectory**
       - crop footprint: roughly 20 -> 33/38 -> 53/57
       - herd size: 5 -> 11/12 -> 14/16
       - daily hands: 4 -> 6 -> 8/9 -> 10/11

    2. **shop-conditioned composition**
       - MILK routes herd slots toward cows
       - WOOL routes herd slots toward sheep
       - EGG routes a smaller fraction toward geese
       - shop demand routes crop slots among strawberry/tomato/carrot
       - wheat fills the residual crop footprint

    Market scheduling is also made explicit:
    SELL -> HIRE -> LAND -> FEED -> ANIMAL -> SEED.

    Hires are retried through the day and capped per turn so the 10-order market
    limit cannot starve live sales/land/seed operations.

    Optional CARE/fertilizer collection is suppressed while crop expansion is
    materially behind the observed trajectory.

    No replay action sequence is used.

    SHA256: `{actual}`
    """), encoding="utf-8")

    if INDEX.exists():
        txt = INDEX.read_text(encoding="utf-8")
        if "| E28 |" not in txt:
            row = (
                "| E28 | Scale-routed state-based M-family | "
                "`artifacts/bundles/current/agent_e28_m_family_scale_routed.py` | "
                "smoke pending | independent M-family candidate | "
                "fixed total scale trajectory + first4 shop composition routing |\n"
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
            f"## {now} — Install E28 scale-routed M-family\n\n"
            f"- Agent: `{TARGET.relative_to(ROOT)}`\n"
            f"- SHA256: `{actual}`\n"
            "- No replay/tape actions used.\n"
            "- Separates total scale trajectory from shop-conditioned composition.\n"
            "- Reworks market slots around SELL/HIRE/LAND priority.\n"
            "- Suppresses optional animal work while crop expansion is behind.\n"
            "- E23-E27 remain immutable.\n"
            "- No Kaggle submission performed.\n\n"
        )

    print("Wrote:", TARGET.relative_to(ROOT))
    print("SHA256:", actual)
    print("Wrote:", README.relative_to(ROOT))
    print("=== E28 install complete ===")

if __name__ == "__main__":
    main()
