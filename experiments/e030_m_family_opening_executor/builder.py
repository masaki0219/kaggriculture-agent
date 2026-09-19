#!/usr/bin/env python3
from pathlib import Path
import textwrap

def find_root():
    candidates = [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    for p in candidates:
        if (p / "artifacts" / "bundles" / "current" / "agent_e29_m_family_staged_opening.py").exists():
            return p
    raise SystemExit("Could not locate repository root.")

ROOT = find_root()
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
SOURCE = BUNDLE / "agent_e29_m_family_staged_opening.py"
TARGET = BUNDLE / "agent_e30_m_family_opening_executor.py"
EXP = ROOT / "experiments" / "e030_m_family_opening_executor"

def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Patch target not found: {label}")
    return text.replace(old, new, 1)

def main():
    text = SOURCE.read_text(encoding="utf-8")
    text = text.replace(
        "E29 — staged-opening state-based M-family agent.",
        "E30 — M-family opening-executor experiment.",
        1,
    )

    text = replace_once(
        text,
        "    build_slots = 2\n",
        "    build_slots = 1 if day <= 2 else 2\n",
        "opening build slots",
    )

    old_water = """                    pr = -5.0 if must else 3.0
                    if tile.get("crop") == "MELON":
                        pr -= 2.0
"""
    new_water = """                    if day <= 2:
                        pr = -10.0 if must else -4.0
                    else:
                        pr = -5.0 if must else 3.0
                        if tile.get("crop") == "MELON":
                            pr -= 2.0
"""
    text = replace_once(text, old_water, new_water, "opening water priority")

    text = replace_once(
        text,
        '                jobs.append(_job("CARE", p, ["CARE"], 1.5))\n',
        '                jobs.append(_job("CARE", p, ["CARE"], 4.0 if day <= 2 else 1.5))\n',
        "opening care priority",
    )

    text = replace_once(
        text,
        '                    "PLACE_"+first, (x,y), ["PLACE", first], -5.5,\n',
        '                    "PLACE_"+first, (x,y), ["PLACE", first], -7.0 if day <= 2 else -5.5,\n',
        "first animal placement priority",
    )
    text = replace_once(
        text,
        '                    "PLACE_"+second, (x,y), ["PLACE", second], -5.0,\n',
        '                    "PLACE_"+second, (x,y), ["PLACE", second], -6.5 if day <= 2 else -5.0,\n',
        "second animal placement priority",
    )

    old_crop = '        crop_pr = {"MELON":-4.0,"STRAWBERRY":-2.0,"TOMATO":0.0,"CARROT":0.5,"WHEAT":3.0}\n'
    new_crop = """        if day <= 2:
            crop_pr = {"MELON":-9.5,"STRAWBERRY":-8.0,"TOMATO":-7.5,"CARROT":-7.5,"WHEAT":-8.5}
        else:
            crop_pr = {"MELON":-4.0,"STRAWBERRY":-2.0,"TOMATO":0.0,"CARROT":0.5,"WHEAT":3.0}
"""
    text = replace_once(text, old_crop, new_crop, "opening crop priority")

    old_hire = """    # Hires remain independent from seed/feed investment: no hard
    # "full workforce or do nothing" gate.
    if hour <= 2 and day < len(HANDS_BY_DAY):
        already = int(farm.get("hires_today",0) or 0)
        target = HANDS_BY_DAY[day]
        n = min(6, max(0, target-already))
        while n > 0:
            cost = _hire_cost(already+n) - _hire_cost(already)
            if cost <= cash:
                break
            n -= 1
        if n > 0:
            buys.extend([["HIRE"] for _ in range(n)])
            cash -= _hire_cost(already+n) - _hire_cost(already)
"""
    new_hire = """    # E30: early workforce is a realized-state target.
    if hour <= 2 and day < len(HANDS_BY_DAY):
        target = HANDS_BY_DAY[day]
        if day <= 2:
            current = len(farm.get("hands") or [])
            n = max(0, target-current)
            if n > 0:
                buys.extend([["HIRE"] for _ in range(n)])
                already = int(farm.get("hires_today",0) or 0)
                est = _hire_cost(already+n) - _hire_cost(already)
                cash = max(0.0, cash-est)
        else:
            already = int(farm.get("hires_today",0) or 0)
            n = min(6, max(0, target-already))
            while n > 0:
                cost = _hire_cost(already+n) - _hire_cost(already)
                if cost <= cash:
                    break
                n -= 1
            if n > 0:
                buys.extend([["HIRE"] for _ in range(n)])
                cash -= _hire_cost(already+n) - _hire_cost(already)
"""
    text = replace_once(text, old_hire, new_hire, "early hire policy")

    compile(text, str(TARGET), "exec")
    TARGET.write_text(text, encoding="utf-8")

    EXP.mkdir(parents=True, exist_ok=True)
    (EXP / "agent.py").write_text(
        textwrap.dedent(
            """\
            from pathlib import Path
            import sys
            _BUNDLE = Path(__file__).resolve().parents[2] / "artifacts" / "bundles" / "current"
            sys.path.insert(0, str(_BUNDLE))
            from agent_e30_m_family_opening_executor import agent, melon_maxxer
            __all__ = ["agent", "melon_maxxer"]
            """
        ),
        encoding="utf-8",
    )

    (EXP / "README.md").write_text(
        textwrap.dedent(
            """\
            # E30 — M-family Opening Executor

            Controlled modification of E29.

            Evidence from 84 M-family runs:
            - 4 hands / 2C3S / five structures / M6 are highly synchronized.
            - step23 crop footprint is about 15.5.
            - E29 matched the early herd/structure state but had only about 4 crops at step23.

            E30 changes only opening execution priorities and early workforce realization.
            Midgame strategy, shop routing and land timing remain E29-derived.

            Evaluation order:
            1. opening fidelity
            2. midgame fidelity
            3. only then population W/D/L
            """
        ),
        encoding="utf-8",
    )

    try:
        (EXP / "builder.py").write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass

    print("=== E30 installed ===")
    print("Agent:", TARGET.relative_to(ROOT))
    print("Experiment:", EXP.relative_to(ROOT))

if __name__ == "__main__":
    main()
