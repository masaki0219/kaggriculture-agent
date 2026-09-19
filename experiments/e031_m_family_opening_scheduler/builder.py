#!/usr/bin/env python3
from pathlib import Path
import textwrap

def find_root():
    candidates = [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    for p in candidates:
        if (p / "artifacts" / "bundles" / "current" / "agent_e30_m_family_opening_executor.py").exists():
            return p
    raise SystemExit("Could not locate repository root with E30 installed.")

ROOT = find_root()
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
SOURCE = BUNDLE / "agent_e30_m_family_opening_executor.py"
TARGET = BUNDLE / "agent_e31_m_family_opening_scheduler.py"
EXP = ROOT / "experiments" / "e031_m_family_opening_scheduler"

def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Patch target not found: {label}")
    return text.replace(old, new, 1)

def main():
    text = SOURCE.read_text(encoding="utf-8")
    text = text.replace(
        "E30 — M-family opening-executor experiment.",
        "E31 — M-family opening-scheduler experiment.",
        1,
    )

    text = replace_once(
        text,
        "    build_slots = 1 if day <= 2 else 2\n",
        "    build_slots = 2\n",
        "restore two concurrent opening structure targets",
    )

    old_place = '''    # 3. Place purchased animals into empty structures.
    for y, row in enumerate(farm.get("tiles") or []):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            if tile.get("animal"):
                continue
            if tile.get("kind") == "PASTURE":
                # Cows first when milk demand is stronger, sheep otherwise.
                d = _shop_demand(obs)
                first = "COW" if d.get("MILK",0) >= d.get("WOOL",0) else "SHEEP"
                second = "SHEEP" if first == "COW" else "COW"
                jobs.append(_job(
                    "PLACE_"+first, (x,y), ["PLACE", first], -7.0 if day <= 2 else -5.5,
                    need=(first,1),
                ))
                jobs.append(_job(
                    "PLACE_"+second, (x,y), ["PLACE", second], -6.5 if day <= 2 else -5.0,
                    need=(second,1),
                ))
            elif tile.get("kind") == "COOP":
                jobs.append(_job(
                    "PLACE_GOOSE", (x,y), ["PLACE","GOOSE"], -5.0,
                    need=("GOOSE",1),
                ))
'''

    new_place = '''    # 3. Place purchased animals into empty structures.
    #
    # E29/E30 emitted TWO mutually-exclusive jobs for every empty pasture.
    # During day0..2 E31 emits exactly one placement job per empty pasture.
    if day <= 2:
        owned = _count_animals(obs)
        placed = Counter()
        for row in farm.get("tiles") or []:
            for tile in row:
                if isinstance(tile, dict) and tile.get("animal") in ANIMALS:
                    placed[tile["animal"]] += 1

        remaining_to_place = {
            "COW": max(0, min(2, owned["COW"]) - placed["COW"]),
            "SHEEP": max(0, min(3, owned["SHEEP"]) - placed["SHEEP"]),
            "GOOSE": max(0, owned["GOOSE"] - placed["GOOSE"]),
        }

        for y, row in enumerate(farm.get("tiles") or []):
            for x, tile in enumerate(row):
                if not isinstance(tile, dict) or tile.get("animal"):
                    continue

                if tile.get("kind") == "PASTURE":
                    animal = None
                    if remaining_to_place["COW"] > 0:
                        animal = "COW"
                    elif remaining_to_place["SHEEP"] > 0:
                        animal = "SHEEP"

                    if animal is not None:
                        jobs.append(_job(
                            "PLACE_"+animal, (x,y), ["PLACE", animal], -8.0,
                            need=(animal,1),
                        ))
                        remaining_to_place[animal] -= 1

                elif tile.get("kind") == "COOP" and remaining_to_place["GOOSE"] > 0:
                    jobs.append(_job(
                        "PLACE_GOOSE", (x,y), ["PLACE","GOOSE"], -8.0,
                        need=("GOOSE",1),
                    ))
                    remaining_to_place["GOOSE"] -= 1

    else:
        for y, row in enumerate(farm.get("tiles") or []):
            for x, tile in enumerate(row):
                if not isinstance(tile, dict):
                    continue
                if tile.get("animal"):
                    continue
                if tile.get("kind") == "PASTURE":
                    d = _shop_demand(obs)
                    first = "COW" if d.get("MILK",0) >= d.get("WOOL",0) else "SHEEP"
                    second = "SHEEP" if first == "COW" else "COW"
                    jobs.append(_job(
                        "PLACE_"+first, (x,y), ["PLACE", first], -5.5,
                        need=(first,1),
                    ))
                    jobs.append(_job(
                        "PLACE_"+second, (x,y), ["PLACE", second], -5.0,
                        need=(second,1),
                    ))
                elif tile.get("kind") == "COOP":
                    jobs.append(_job(
                        "PLACE_GOOSE", (x,y), ["PLACE","GOOSE"], -5.0,
                        need=("GOOSE",1),
                    ))
'''
    text = replace_once(text, old_place, new_place, "opening animal placement de-duplication")

    old_seed_afford = '''        n = min(deficit, batch.get(crop,1), int(cash // SEED_COST[crop]))
        if n <= 0:
            continue

        buys.append(["BUY_SEED",crop,n])
        cash -= n*SEED_COST[crop]
'''
    new_seed_afford = '''        reserve = 7 if day == 0 else 0
        spendable = max(0.0, cash - reserve)
        n = min(deficit, batch.get(crop,1), int(spendable // SEED_COST[crop]))
        if n <= 0:
            continue

        buys.append(["BUY_SEED",crop,n])
        cash -= n*SEED_COST[crop]
'''
    text = replace_once(text, old_seed_afford, new_seed_afford, "day0 next-day hire reserve")

    compile(text, str(TARGET), "exec")
    TARGET.write_text(text, encoding="utf-8")

    EXP.mkdir(parents=True, exist_ok=True)
    (EXP / "agent.py").write_text(
        textwrap.dedent(
            '''\
            from pathlib import Path
            import sys
            _BUNDLE = Path(__file__).resolve().parents[2] / "artifacts" / "bundles" / "current"
            sys.path.insert(0, str(_BUNDLE))
            from agent_e31_m_family_opening_scheduler import agent, melon_maxxer
            __all__ = ["agent", "melon_maxxer"]
            '''
        ),
        encoding="utf-8",
    )

    (EXP / "README.md").write_text(
        textwrap.dedent(
            '''\
            # E31 — M-family Opening Scheduler

            Controlled successor to E30.

            E30 result:
            - step23 crops improved from E29's ~4 to 13
            - structures/animals fell to 2/2 because construction was serialized
            - day1 hands still fell to 3

            E31 keeps E30's planting priorities and changes only:
            1. two concurrent structure targets,
            2. one mutually-exclusive animal placement job per empty pasture on day0..2,
            3. seven-coin day0 reserve for next-day HIRE4.

            Midgame/shop/land policy remains inherited from E30/E29.
            Fidelity first; no population W/L unless opening and midgame both pass.
            '''
        ),
        encoding="utf-8",
    )

    try:
        (EXP / "builder.py").write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass

    print("=== E31 installed ===")
    print("Agent:", TARGET.relative_to(ROOT))
    print("Experiment:", EXP.relative_to(ROOT))

if __name__ == "__main__":
    main()
