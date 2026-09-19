#!/usr/bin/env python3
from pathlib import Path
import textwrap


def find_root():
    candidates = [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    for p in candidates:
        if (p / "artifacts" / "bundles" / "current" / "agent_e32_m_family_opening_build_priority.py").exists():
            return p
    raise SystemExit("Could not locate repository root with E32 installed.")


ROOT = find_root()
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
SOURCE = BUNDLE / "agent_e32_m_family_opening_build_priority.py"
TARGET = BUNDLE / "agent_e33_m_family_crop_expansion.py"
EXP = ROOT / "experiments" / "e033_m_family_crop_expansion"


NEW_DESIRED = r'''
def _desired_crop_map(obs, pasture_positions, coop_positions):
    """E33 midgame crop-expansion controller.

    New crop targets are only allocated onto actually empty unlocked tiles.
    This prevents phantom targets that consume the target count but cannot
    produce PLANT jobs.

    Observed M-family expansion phases:
      day 6..8  : strawberry-led expansion
      day 9..11 : wheat-led scale expansion
    """
    day, _ = _day_hour(obs)
    targets = _crop_targets(obs)
    reserved = set(pasture_positions) | set(coop_positions)
    desired = {}

    # Preserve currently live crops. Once harvested, their empty tile can be
    # reassigned by the current phase on a later turn.
    for y, row in enumerate(_me(obs).get("tiles") or []):
        for x, tile in enumerate(row):
            p = (x, y)
            if p in reserved:
                continue
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop"):
                desired[p] = tile["crop"]

    def add_empty(crop, target_count, order=None):
        current = sum(1 for c in desired.values() if c == crop)
        need = max(0, int(target_count) - current)
        if need <= 0:
            return
        coords = order if order is not None else _crop_order(obs, crop, reserved)
        for p in coords:
            if need <= 0:
                break
            if p in reserved or p in desired or not _unlocked(obs, p):
                continue
            if _tile(obs, p) is not None:
                continue
            desired[p] = crop
            need -= 1

    def fill_empty(crop, total_target):
        if len(desired) >= total_target:
            return
        for p in _crop_order(obs, crop, reserved):
            if len(desired) >= total_target:
                break
            if p in reserved or p in desired or not _unlocked(obs, p):
                continue
            if _tile(obs, p) is not None:
                continue
            desired[p] = crop

    # Opening retained from E32.
    if day == 0:
        add_empty("MELON", 6, MELON_OPENING)
        fill_empty("WHEAT", 15)
        return desired
    if day == 1:
        add_empty("MELON", 10, MELON_OPENING)
        fill_empty("WHEAT", 19)
        return desired
    if day == 2:
        add_empty("MELON", 12, MELON_OPENING)
        add_empty("STRAWBERRY", 2)
        fill_empty("WHEAT", 20)
        return desired
    if day <= 5:
        add_empty("MELON", 12, MELON_OPENING)
        add_empty("STRAWBERRY", 8)
        return desired

    total_target = CROP_TOTAL_BY_DAY[min(day, len(CROP_TOTAL_BY_DAY)-1)]

    # Main E33 mechanism.
    if 6 <= day <= 8:
        add_empty("STRAWBERRY", min(targets["STRAWBERRY"], total_target))
        fill_empty("WHEAT", total_target)
        return desired

    if 9 <= day <= 11:
        fill_empty("WHEAT", total_target)
        return desired

    # Later strategic routing stays close to E32.
    if day <= 13:
        add_empty("STRAWBERRY", min(targets["STRAWBERRY"], total_target))
        fill_empty("WHEAT", total_target)
        return desired
    if day <= 20:
        add_empty("TOMATO", min(targets["TOMATO"], total_target))
        fill_empty("WHEAT", total_target)
        return desired
    if day <= 27:
        add_empty("CARROT", min(targets["CARROT"], total_target))
        fill_empty("WHEAT", total_target)
        return desired

    return desired
'''


def patch_between(text, start_marker, end_marker, replacement):
    a = text.find(start_marker)
    b = text.find(end_marker, a)
    if a < 0 or b < 0:
        raise SystemExit(f"Could not patch section: {start_marker}")
    return text[:a] + replacement.strip() + "\n\n\n" + text[b:]


def main():
    text = SOURCE.read_text(encoding="utf-8")
    text = text.replace(
        "E32 — M-family opening build-priority fix.",
        "E33 — M-family crop-expansion controller.",
        1,
    )

    text = patch_between(
        text,
        "def _desired_crop_map(obs, pasture_positions, coop_positions):",
        "# ---------- job planner ----------",
        NEW_DESIRED,
    )

    # Make days 6..11 expansion planting competitive with routine maintenance.
    marker = "        for p, crop in sorted(\n"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("Could not find crop planning loop.")
    insert = '''        if 6 <= day <= 11:\n            crop_pr.update({\"MELON\": -5.0, \"STRAWBERRY\": -5.0, \"TOMATO\": -4.0, \"CARROT\": -4.0, \"WHEAT\": -5.0})\n\n'''
    text = text[:idx] + insert + text[idx:]

    # Realize the observed workforce trajectory through day11 instead of
    # shrinking it with a conservative expected-cash pre-check.
    start = text.find("    if hour <= 2 and day < len(HANDS_BY_DAY):")
    end = text.find("    # Expansion windows inferred from the current M population.", start)
    if start < 0 or end < 0:
        raise SystemExit("Could not find hire block.")

    hire_block = '''    if hour <= 2 and day < len(HANDS_BY_DAY):\n        current_hands = len(farm.get(\"hands\") or [])\n        target = HANDS_BY_DAY[day]\n\n        if day <= 11:\n            n = min(10, max(0, target - current_hands))\n            if n > 0:\n                buys.extend([[\"HIRE\"] for _ in range(n)])\n        else:\n            already = int(farm.get(\"hires_today\",0) or 0)\n            n = min(6, max(0, target-already))\n            while n > 0:\n                cost = _hire_cost(already+n) - _hire_cost(already)\n                if cost <= cash:\n                    break\n                n -= 1\n            if n > 0:\n                buys.extend([[\"HIRE\"] for _ in range(n)])\n                cash -= _hire_cost(already+n) - _hire_cost(already)\n\n'''
    text = text[:start] + hire_block + text[end:]

    compile(text, str(TARGET), "exec")
    TARGET.write_text(text, encoding="utf-8")

    EXP.mkdir(parents=True, exist_ok=True)
    (EXP / "agent.py").write_text(textwrap.dedent('''\
        from pathlib import Path
        import sys
        _BUNDLE = Path(__file__).resolve().parents[2] / "artifacts" / "bundles" / "current"
        sys.path.insert(0, str(_BUNDLE))
        from agent_e33_m_family_crop_expansion import agent, melon_maxxer
        __all__ = ["agent", "melon_maxxer"]
    '''), encoding="utf-8")

    (EXP / "README.md").write_text(textwrap.dedent('''\
        # E33 — M-family Crop Expansion Controller

        Final mechanism-focused M-family reconstruction candidate.

        Evidence:
        - day6 M: BUY_SEED ~14, PLANT ~13, end crops ~33
        - day6 E32: BUY_SEED ~12, PLANT ~0.5, end crops ~20
        - day7 M hands=9, E32 hands=6
        - day9 M: Q3 and WHEAT-led expansion; E32 remained Q2 and strawberry-led

        E33 changes one coherent module: midgame crop expansion.

        Changes:
        1. future crop targets only occupy actually empty tiles;
        2. day6-8 expansion is strawberry-led;
        3. day9-11 expansion is wheat-led;
        4. day6-11 workforce targets are requested directly;
        5. expansion PLANT jobs get competitive priority.

        If this does not materially improve midgame fidelity / W-D-L,
        stop the M-family reconstruction track.
    '''), encoding="utf-8")

    try:
        (EXP / "builder.py").write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass

    print("=== E33 installed ===")
    print("Agent:", TARGET.relative_to(ROOT))
    print("Experiment:", EXP.relative_to(ROOT))


if __name__ == "__main__":
    main()
