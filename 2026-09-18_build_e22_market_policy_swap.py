#!/usr/bin/env python3
# 2026-09-18 — Build E22: E21 farm + aurax market-policy swap

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import importlib.util
import os
import sys
import uuid

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "artifacts" / "bundles" / "current"
ELITE = BUNDLE / "public_agents" / "elite"

TETSU_BASE = ELITE / "tetsu_market_v23_current"
AURAX_BASE = ELITE / "aurax7_v7_current"

E21_SHA = "f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2"
AURAX_SHA = "e221f4875daff8b03e8f0ec7c86bd3a2a72c0768b049d4c25064abd5301a532b"

TARGET = BUNDLE / "agent_e22_market_policy_swap.py"
EXP_DIR = ROOT / "experiments" / "e022_market_policy_swap"
EXP_README = EXP_DIR / "README.md"
INDEX = ROOT / "docs" / "experiment_index.md"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"


def fail(msg: str) -> None:
    raise SystemExit(f"\nERROR: {msg}\n")


def entrypoint(base: Path) -> Path:
    marker = base / "entrypoint.txt"
    if not marker.exists():
        fail(f"Missing entrypoint marker: {marker}")
    rel = marker.read_text(encoding="utf-8").strip()
    p = (base / rel).resolve()
    if not p.exists():
        fail(f"Missing entrypoint: {p}")
    return p


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_module(path: Path, prefix: str):
    for p in (path.parent, path.parent.parent, path.parent.parent.parent, BUNDLE):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)

    name = f"{prefix}_{uuid.uuid4().hex}"
    old = Path.cwd()
    try:
        os.chdir(path.parent)
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            fail(f"Could not import {path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        os.chdir(old)


def main() -> None:
    print("=== Build E22: E21 farm + aurax market-policy swap ===")
    print("Repository root:", ROOT)

    if not BUNDLE.exists():
        fail("artifacts/bundles/current not found. Put this script in Kaggle root.")
    if not INDEX.exists():
        fail(f"Missing experiment index: {INDEX}")

    tetsu_path = entrypoint(TETSU_BASE)
    aurax_path = entrypoint(AURAX_BASE)

    t_sha = sha256(tetsu_path)
    a_sha = sha256(aurax_path)

    print("E21/Tetsu:", tetsu_path.relative_to(ROOT))
    print("  SHA256:", t_sha)
    print("aurax:", aurax_path.relative_to(ROOT))
    print("  SHA256:", a_sha)

    if t_sha != E21_SHA:
        fail(
            "Tetsu artifact hash changed.\n"
            f"Expected: {E21_SHA}\n"
            f"Actual:   {t_sha}"
        )

    if a_sha != AURAX_SHA:
        fail(
            "aurax artifact hash changed.\n"
            f"Expected: {AURAX_SHA}\n"
            f"Actual:   {a_sha}"
        )

    tetsu = import_module(tetsu_path, "_e22_probe_tetsu")
    aurax = import_module(aurax_path, "_e22_probe_aurax")

    required_tetsu = ("_ADV_PARENT", "_IMPL", "_RACE_STATE")
    required_aurax = ("advance_sales", "frontload")

    missing_t = [x for x in required_tetsu if not hasattr(tetsu, x)]
    missing_a = [x for x in required_aurax if not hasattr(aurax, x)]

    if missing_t:
        fail(f"E21 missing required internals: {missing_t}")
    if missing_a:
        fail(f"aurax missing required market helpers: {missing_a}")

    if not callable(tetsu._ADV_PARENT):
        fail("E21 _ADV_PARENT is not callable.")
    if not callable(aurax.advance_sales) or not callable(aurax.frontload):
        fail("aurax market helpers are not callable.")

    target_text = f'''# E22 — E21 farm/route + aurax market-policy swap
#
# Frozen E21 SHA256: {E21_SHA}
# Frozen aurax SHA256: {AURAX_SHA}
#
# Keeps E21 through `_ADV_PARENT` and replaces only the final ADV market
# policy with aurax `advance_sales + frontload`.
# Local experiment only; not yet a standalone final-submission bundle.

from __future__ import annotations

from pathlib import Path
import importlib.util
import os
import sys
import uuid

_ROOT = Path(__file__).resolve().parent
_ELITE = _ROOT / "public_agents" / "elite"

_TETSU_NAME = "tetsu_market_v23_current"
_AURAX_NAME = "aurax7_v7_current"

TELEMETRY = {{
    "calls": 0,
    "errors": 0,
    "market_changed": 0,
}}


def _entrypoint(name):
    base = _ELITE / name
    marker = base / "entrypoint.txt"
    rel = marker.read_text(encoding="utf-8").strip()
    return (base / rel).resolve()


def _load_module(name):
    path = _entrypoint(name)

    for p in (path.parent, path.parent.parent, path.parent.parent.parent, _ROOT):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)

    module_name = f"_e22_{{name}}_{{uuid.uuid4().hex}}"
    old = Path.cwd()
    try:
        os.chdir(path.parent)
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        os.chdir(old)


_TETSU = _load_module(_TETSU_NAME)
_AURAX = _load_module(_AURAX_NAME)

# Critical isolation point: parent immediately before E21 final ADV wrapper.
_BASE = _TETSU._ADV_PARENT


def _standard(configuration):
    if configuration is None:
        return True
    try:
        for k, v in (
            ("boardSize", 10),
            ("turnsPerDay", 24),
            ("shedCapacity", 100),
            ("maxMarketOrdersPerTurn", 10),
            ("farmHandCostMult", 1),
        ):
            if configuration.get(k, v) != v:
                return False
        if configuration.get("marketParams", None):
            return False
    except Exception:
        return False
    return True


def _future_market(observation, offset=1):
    try:
        step = int(observation["step"]) + int(offset)
        if step >= 719:
            return None

        players = _TETSU._IMPL.chassis.players
        native = players.get(int(observation["player"])) if isinstance(players, dict) else None
        route = 2 if step >= 648 else (native or {{}}).get("route")
        if route is None:
            return None

        action = _TETSU._IMPL.chassis.routes[route][step]
        return action.get("market") if isinstance(action, dict) else None
    except Exception:
        return None


def _update_race_state(observation, action):
    try:
        player = int(observation["player"])
        step = int(observation["step"])
        st = _TETSU._RACE_STATE.get(player)
        if (
            st is not None
            and st.get("prev_action") is not None
            and st.get("step") == step
        ):
            st["prev_action"] = action
    except Exception:
        pass


def agent(observation, configuration=None):
    action = _BASE(observation, configuration)
    TELEMETRY["calls"] += 1

    try:
        if isinstance(action, dict) and _standard(configuration):
            market = action.get("market")
            market = list(market) if isinstance(market, list) else []

            new_market = _AURAX.advance_sales(
                observation,
                market,
                _future_market,
                TELEMETRY,
            )

            if len(new_market) > 1:
                new_market = _AURAX.frontload(
                    observation,
                    new_market,
                    None,
                    TELEMETRY,
                )

            if new_market != market:
                action = dict(action)
                action["market"] = new_market
                TELEMETRY["market_changed"] += 1

        _update_race_state(observation, action)

    except Exception:
        TELEMETRY["errors"] += 1
        _update_race_state(observation, action)

    return action


melon_maxxer = agent
'''

    compile(target_text, str(TARGET), "exec")
    TARGET.write_text(target_text, encoding="utf-8")
    print("Wrote:", TARGET.relative_to(ROOT))

    e22 = import_module(TARGET, "_e22_validation")
    if not callable(getattr(e22, "agent", None)):
        fail("Generated E22 does not expose callable agent.")
    if e22._BASE is not e22._TETSU._ADV_PARENT:
        fail("Generated E22 did not bind E21 _ADV_PARENT.")

    print("Validated: E22 imports and uses E21 _ADV_PARENT.")

    EXP_DIR.mkdir(parents=True, exist_ok=True)
    exp_text = f'''# E22 — Market Policy Swap

## Hypothesis

Failure-regime analysis showed E21 and aurax V7 realize nearly identical farms
even where E21 loses. The candidate causal difference is market execution.

E22 keeps E21 through `_ADV_PARENT` and replaces only the final E21 ADV market
block:

- removed from E22 path: `_adv_apply`, `_adv_frontload`
- inserted: aurax `advance_sales`, `frontload`

No route, crop, herd, opening, or shop-specific patch is introduced.

## Frozen artifacts

- E21/Tetsu SHA256: `{t_sha}`
- aurax V7 SHA256: `{a_sha}`
- E22 agent: `artifacts/bundles/current/agent_e22_market_policy_swap.py`

## Interpretation

E22 is a mechanism-isolation experiment for a complete market-policy family.
A positive result must survive fresh seeds and population-representative
evaluation, not only E21/aurax head-to-head.
'''
    EXP_README.write_text(exp_text, encoding="utf-8")
    print("Wrote:", EXP_README.relative_to(ROOT))

    index_text = INDEX.read_text(encoding="utf-8")
    row = (
        "| E22 | E21 pre-ADV strategy + aurax advance_sales/frontload market-policy swap | "
        "`artifacts/bundles/current/agent_e22_market_policy_swap.py` | "
        "fresh direct screen pending | "
        "mechanism-isolation experiment | "
        "keeps E21 production/route/opening; swaps only final ADV market block |\n"
    )

    if "| E22 |" not in index_text:
        marker = "\n## Legacy non-E series"
        if marker in index_text:
            index_text = index_text.replace(marker, "\n" + row + marker)
        else:
            index_text = index_text.rstrip() + "\n" + row
        INDEX.write_text(index_text, encoding="utf-8")
        print("Updated:", INDEX.relative_to(ROOT))
    else:
        print("E22 already exists in experiment index; index left unchanged.")

    now = datetime.now().astimezone().isoformat(timespec="seconds")

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")

    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {now} — Build E22 market-policy swap\n\n"
            f"- E21/Tetsu SHA256: `{t_sha}`\n"
            f"- aurax V7 SHA256: `{a_sha}`\n"
            f"- Agent: `{TARGET.relative_to(ROOT)}`\n"
            "- Kept E21 route/production/opening/race chain through `_ADV_PARENT`.\n"
            "- Replaced only final ADV market wrapper with aurax `advance_sales + frontload`.\n"
            "- Import validation: PASS.\n"
            "- No Kaggle submission performed.\n\n"
        )

    print()
    print("=== E22 build complete ===")
    print("Agent:", TARGET.relative_to(ROOT))
    print("Experiment:", EXP_README.relative_to(ROOT))
    print("Next: fresh-seed screening of E22 vs E21 / aurax / Ahmed.")


if __name__ == "__main__":
    main()
