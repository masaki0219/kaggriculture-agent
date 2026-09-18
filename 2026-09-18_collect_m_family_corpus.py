#!/usr/bin/env python3
"""
2026-09-18 — Collect a deeper current M-family replay corpus

Put this file directly in the Kaggle repository root and run:

    python 2026-09-18_collect_m_family_corpus.py

Requires the prior live refresh directory:
    live_population_2026-09-18/scout_manifest.json

Default:
    7 M-family teams + Unknown Mother-Goose as K-control
    up to 12 recent episodes per team

Output:
    m_family_corpus_2026-09-18/
    2026-09-18_m_family_corpus.zip

Purpose
-------
Build enough current replay data to design E23 as a complete M-family strategy,
instead of guessing from two replays/team.

No agent is modified and nothing is submitted.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import time
import zipfile

ROOT = Path(__file__).resolve().parent
LIVE = ROOT / "live_population_2026-09-18"
MANIFEST = LIVE / "scout_manifest.json"

OUT = ROOT / "m_family_corpus_2026-09-18"
REPLAYS = OUT / "replays"
CORPUS_MANIFEST = OUT / "manifest.json"
REPORT = OUT / "README.md"
ZIP_OUT = ROOT / "2026-09-18_m_family_corpus.zip"
HISTORY = ROOT / "EXPERIMENT_RUN_HISTORY.md"

TARGETS = [
    "Majkel1337",
    "DSM",
    "Orbital Terraformer",
    "ymg_aq",
    "QQ",
    "Arda Ceylan",
    "kwa",
    # K-line control for contrast
    "Unknown Mother-Goose",
]

M_FAMILY = {
    "Majkel1337",
    "DSM",
    "Orbital Terraformer",
    "ymg_aq",
    "QQ",
    "Arda Ceylan",
    "kwa",
}


def run_json(cmd):
    full = ["kaggle", *cmd, "--format", "json", "-q"]
    p = subprocess.run(
        full,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(full)
            + "\n\nstdout:\n"
            + (p.stdout or "")
            + "\n\nstderr:\n"
            + (p.stderr or "")
        )

    text = (p.stdout or "").strip()
    if not text:
        return []

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for i, ch in enumerate(text):
            if ch in "[{":
                try:
                    return json.loads(text[i:])
                except Exception:
                    pass
        raise RuntimeError("Could not parse Kaggle JSON output:\n" + text[:3000])


def first_key(d, names):
    for name in names:
        if isinstance(d, dict) and name in d and d[name] is not None:
            return d[name]
    return None


def as_int(x):
    try:
        return int(x)
    except Exception:
        return None


def download_replay(episode_id, dest):
    dest.mkdir(parents=True, exist_ok=True)

    existing = list(dest.glob(f"*{episode_id}*"))
    if existing:
        return {
            "episode_id": episode_id,
            "ok": True,
            "cached": True,
            "files": [str(p.relative_to(ROOT)) for p in existing],
        }

    p = subprocess.run(
        [
            "kaggle", "competitions", "replay",
            str(episode_id),
            "-p", str(dest),
            "-q",
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    if p.returncode != 0:
        return {
            "episode_id": episode_id,
            "ok": False,
            "cached": False,
            "error": (p.stderr or p.stdout or "download failed")[-3000:],
        }

    files = list(dest.glob(f"*{episode_id}*"))
    return {
        "episode_id": episode_id,
        "ok": True,
        "cached": False,
        "files": [str(x.relative_to(ROOT)) for x in files],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes-per-team", type=int, default=12)
    ap.add_argument("--sleep", type=float, default=0.3)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if shutil.which("kaggle") is None:
        raise SystemExit("kaggle CLI not found in this venv.")
    if not MANIFEST.exists():
        raise SystemExit(
            f"Missing {MANIFEST.relative_to(ROOT)}.\n"
            "Run the live population refresh first."
        )

    source = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_name = {
        x.get("team_name"): x
        for x in source.get("teams", [])
        if x.get("team_name")
    }

    missing = [name for name in TARGETS if name not in by_name]
    if missing:
        raise SystemExit(f"Targets missing from live manifest: {missing}")

    if args.force and OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    REPLAYS.mkdir(parents=True, exist_ok=True)

    corpus = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "episodes_per_team": args.episodes_per_team,
        "targets": [],
    }

    print("=== Collect current M-family corpus ===")
    print("Episodes/team:", args.episodes_per_team)
    print()

    for idx, name in enumerate(TARGETS, start=1):
        src = by_name[name]
        submission_id = as_int(src.get("selected_submission_id"))
        team_id = as_int(src.get("team_id"))
        if submission_id is None:
            raise SystemExit(f"No selected submission ID for {name}")

        print(
            f"[{idx}/{len(TARGETS)}] {name} "
            f"teamId={team_id} submission={submission_id}",
            flush=True,
        )

        episodes = run_json([
            "competitions", "episodes",
            str(submission_id),
        ])
        if isinstance(episodes, dict):
            for key in ("rows", "episodes", "data"):
                if isinstance(episodes.get(key), list):
                    episodes = episodes[key]
                    break
        if not isinstance(episodes, list):
            episodes = []

        def sort_key(ep):
            state = str(first_key(ep, ("state", "status")) or "").lower()
            complete = 1 if state in ("complete", "completed", "finished", "success") else 0
            created = str(first_key(ep, ("createTime", "endTime", "date")) or "")
            eid = as_int(first_key(ep, ("id", "episodeId", "episode_id"))) or -1
            return (complete, created, eid)

        episodes = sorted(episodes, key=sort_key, reverse=True)

        chosen = []
        seen = set()
        for ep in episodes:
            eid = as_int(first_key(ep, ("id", "episodeId", "episode_id")))
            if eid is None or eid in seen:
                continue
            seen.add(eid)
            chosen.append(eid)
            if len(chosen) >= args.episodes_per_team:
                break

        team_dir = REPLAYS / f"{idx:02d}_{name.replace('/', '_')}"
        downloads = []
        for j, eid in enumerate(chosen, start=1):
            print(f"  [{j:02d}/{len(chosen):02d}] episode {eid}", flush=True)
            downloads.append(download_replay(eid, team_dir))
            time.sleep(args.sleep)

        corpus["targets"].append({
            "team_name": name,
            "family": "M" if name in M_FAMILY else "K-control",
            "team_id": team_id,
            "submission_id": submission_id,
            "episodes_available": len(episodes),
            "episodes_selected": chosen,
            "downloads": downloads,
        })

        CORPUS_MANIFEST.write_text(
            json.dumps(corpus, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    ok = sum(
        1
        for t in corpus["targets"]
        for d in t["downloads"]
        if d.get("ok")
    )
    errors = [
        (t["team_name"], d)
        for t in corpus["targets"]
        for d in t["downloads"]
        if not d.get("ok")
    ]

    lines = [
        "# Current M-family Corpus — 2026-09-18",
        "",
        f"- Generated: `{corpus['generated']}`",
        f"- Episodes/team target: **{args.episodes_per_team}**",
        f"- Teams: **{len(TARGETS)}**",
        f"- Successful replay downloads: **{ok}**",
        f"- Download errors: **{len(errors)}**",
        "",
        "## Targets",
        "",
        "| Team | Family | Submission | Selected | Successful |",
        "|---|---|---:|---:|---:|",
    ]

    for t in corpus["targets"]:
        success = sum(1 for d in t["downloads"] if d.get("ok"))
        lines.append(
            f"| {t['team_name']} | {t['family']} | "
            f"{t['submission_id']} | {len(t['episodes_selected'])} | {success} |"
        )

    lines += [
        "",
        "## Intended use",
        "",
        "- Mine the converged M opening and land/hands schedule.",
        "- Estimate first-3/first-4-shop production targets for cows, sheep, carrot, tomato and strawberry.",
        "- Separate invariant M-family mechanisms from team-specific market styles.",
        "- Use Unknown Mother-Goose as a K-line control.",
        "- Design E23 independently from the replay behavior; do not copy unlicensed external source code.",
        "",
    ]

    if errors:
        lines += ["## Errors", ""]
        for team, d in errors:
            lines.append(
                f"- {team}: episode {d['episode_id']} — {d.get('error','')}"
            )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(ROOT))

    if not HISTORY.exists():
        HISTORY.write_text("# Experiment Run History\n\n", encoding="utf-8")

    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(
            f"## {corpus['generated']} — Collect current M-family corpus\n\n"
            f"- Teams: {len(TARGETS)}\n"
            f"- Episodes/team: {args.episodes_per_team}\n"
            f"- Successful downloads: {ok}\n"
            f"- Bundle: `{ZIP_OUT.name}`\n"
            "- Acquisition only; no agent modification or Kaggle submission.\n\n"
        )

    print()
    print("=== M-family corpus complete ===")
    print("Successful downloads:", ok)
    print("Errors:", len(errors))
    print("Bundle:", ZIP_OUT.name)


if __name__ == "__main__":
    main()
