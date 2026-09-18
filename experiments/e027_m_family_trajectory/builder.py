#!/usr/bin/env python3
"""Install E27 trajectory-corrected state-based M-family agent."""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import base64, hashlib, textwrap, zlib

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
TARGET = BUNDLE / "agent_e27_m_family_trajectory.py"
EXP_DIR = ROOT / "experiments" / "e027_m_family_trajectory"
README = EXP_DIR / "README.md"
INDEX = ROOT / "docs" / "experiment_index.md"
HISTORY = ROOT / "docs" / "experiment_run_history.md"

AGENT_B64 = """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"""
EXPECTED_SHA = "8fa05ceb5ea7da79330b2ee4b23835f5b2395ada04b62dcd14a395d6fc76270a"

def main():
    print("=== Install E27: trajectory-corrected M-family ===")
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
    # E27 — Trajectory-corrected state-based M-family

    E27 keeps the no-replay-action architecture of E26, but fixes policy
    translation errors found by comparing E26 to the 84-run M corpus.

    Key corrections:
    - shop-conditioned targets use only the first four shops;
    - M6 is treated as the day-0 seed tranche, not total melon production;
    - opening trajectory targets ~12 melon / 6 wheat / 2 strawberry;
    - strawberry grows ~2 -> 8 -> shop-conditioned rather than jumping to 17+ on day2;
    - structure count follows the observed trajectory (~5 -> 12 -> 16 -> <=20);
    - structure construction is paced (max 2 new builds planned at once);
    - herd size is capped near the observed distribution;
    - goose response is conservative;
    - animal and premium-seed purchases are paced rather than filling the full target gap instantly.

    No replay action sequence is used.

    SHA256: `{actual}`
    """), encoding="utf-8")

    if INDEX.exists():
        txt = INDEX.read_text(encoding="utf-8")
        if "| E27 |" not in txt:
            row = (
                "| E27 | Trajectory-corrected state-based M-family | "
                "`artifacts/bundles/current/agent_e27_m_family_trajectory.py` | "
                "smoke pending | independent M-family candidate | "
                "first4 routing; 12-melon trajectory; staged structures/crops |\n"
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
            f"## {now} — Install E27 trajectory-corrected M-family\n\n"
            f"- Agent: `{TARGET.relative_to(ROOT)}`\n"
            f"- SHA256: `{actual}`\n"
            "- No replay/tape actions used.\n"
            "- Fixes E26 first4-vs-all-shops target drift.\n"
            "- Fixes M6 initial-tranche vs total-melon confusion.\n"
            "- Adds replay-derived structure/crop growth trajectory.\n"
            "- E23-E26 remain immutable.\n"
            "- No Kaggle submission performed.\n\n"
        )

    print("Wrote:", TARGET.relative_to(ROOT))
    print("SHA256:", actual)
    print("Wrote:", README.relative_to(ROOT))
    print("=== E27 install complete ===")

if __name__ == "__main__":
    main()
