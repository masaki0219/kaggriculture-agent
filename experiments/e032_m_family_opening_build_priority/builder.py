#!/usr/bin/env python3
from pathlib import Path
import textwrap

def find_root():
    candidates = [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    for p in candidates:
        if (p / "artifacts" / "bundles" / "current" / "agent_e31_m_family_opening_scheduler.py").exists():
            return p
    raise SystemExit("Could not locate repository root with E31 installed.")

ROOT = find_root()
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
SOURCE = BUNDLE / "agent_e31_m_family_opening_scheduler.py"
TARGET = BUNDLE / "agent_e32_m_family_opening_build_priority.py"
EXP = ROOT / "experiments" / "e032_m_family_opening_build_priority"

def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Patch target not found: {label}")
    return text.replace(old, new, 1)

def main():
    text = SOURCE.read_text(encoding="utf-8")
    text = text.replace(
        "E31 — M-family opening-scheduler experiment.",
        "E32 — M-family opening build-priority fix.",
        1,
    )

    # E30/E31 raised opening crop priority to MELON=-9.5 / WHEAT=-8.5,
    # while BUILD_PASTURE remained at -6.0. The trace showed workers therefore
    # abandoning the remaining three pasture targets after two were built.
    # Make construction outrank planting only during day0..2.
    text = replace_once(
        text,
        '            jobs.append(_job("BUILD_PASTURE", p, ["BUILD_PASTURE"], -6.0))\n',
        '            jobs.append(_job("BUILD_PASTURE", p, ["BUILD_PASTURE"], -12.0 if day <= 2 else -6.0))\n',
        "opening pasture priority",
    )

    compile(text, str(TARGET), "exec")
    TARGET.write_text(text, encoding="utf-8")

    EXP.mkdir(parents=True, exist_ok=True)
    (EXP / "agent.py").write_text(
        textwrap.dedent("""\
        from pathlib import Path
        import sys
        _BUNDLE = Path(__file__).resolve().parents[2] / "artifacts" / "bundles" / "current"
        sys.path.insert(0, str(_BUNDLE))
        from agent_e32_m_family_opening_build_priority import agent, melon_maxxer
        __all__ = ["agent", "melon_maxxer"]
        """),
        encoding="utf-8",
    )

    (EXP / "README.md").write_text(
        textwrap.dedent("""\
        # E32 — M-family Opening Build-Priority Fix

        Controlled successor to E31.

        Trace evidence from E31:
        - crops reached 12 by step23;
        - only two pastures were built and two cows were placed;
        - after the second pasture, workers were routed almost entirely to crop work;
        - E30/E31 opening crop priorities were raised above the unchanged E29
          BUILD_PASTURE priority.

        E32 changes exactly one mechanism:
        - during day0..2, BUILD_PASTURE priority becomes -12.0, ahead of
          MELON=-9.5 and WHEAT=-8.5.

        Everything else is inherited from E31, including:
        - one mutually-exclusive placement job per empty pasture,
        - day0 cash reserve for next-day hires,
        - E30 planting priorities,
        - E29 midgame/shop/land policy.

        This is the final generic-planner opening experiment.
        If opening fidelity still fails, move to an explicit day0 state machine.
        """),
        encoding="utf-8",
    )

    try:
        (EXP / "builder.py").write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass

    print("=== E32 installed ===")
    print("Agent:", TARGET.relative_to(ROOT))
    print("Experiment:", EXP.relative_to(ROOT))

if __name__ == "__main__":
    main()
