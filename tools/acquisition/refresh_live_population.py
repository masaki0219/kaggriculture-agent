#!/usr/bin/env python3
"""
2026-09-18 — Refresh live Kaggriculture leaderboard population

Run from the Kaggle repository root:

    python tools/acquisition/refresh_live_population.py

Default:
    - snapshot top 30 leaderboard rows
    - scout top 20 teams
    - choose each team's highest-publicScore active submission
    - download up to 2 recent replays per team

Outputs in Kaggle root:
    data/replays/2026-09-18/live_population/
    data/replays/2026-09-18/live_population.zip

Purpose
-------
Update the *actual current leaderboard population* before deciding whether
E21 or E22 is the better final portfolio component.

This script does not modify agents and does not submit anything.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse
import json
import math
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "replays" / "2026-09-18" / "live_population"
REPLAYS = OUT / "replays"
LEADERBOARD_JSON = OUT / "leaderboard_top.json"
MANIFEST_JSON = OUT / "scout_manifest.json"
REPORT_MD = OUT / "README.md"
ZIP_OUT = ROOT / "data" / "replays" / "2026-09-18" / "live_population.zip"
HISTORY = ROOT / "docs" / "experiment_run_history.md"


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
        # Some Kaggle CLI versions may print a prefix line before JSON.
        starts = [i for i, ch in enumerate(text) if ch in "[{"]
        for i in starts:
            try:
                return json.loads(text[i:])
            except Exception:
                pass
        raise RuntimeError(
            "Could not parse Kaggle JSON output:\n" + text[:3000]
        )


def first_key(d, names):
    for name in names:
        if name in d and d[name] is not None:
            return d[name]
    return None


def as_float(x, default=float("-inf")):
    try:
        return float(x)
    except Exception:
        return default


def as_int(x):
    try:
        return int(x)
    except Exception:
        return None


def parse_time(x):
    # ISO strings sort correctly enough for Kaggle timestamps when normalized.
    return str(x or "")


def download_replay(episode_id, dest):
    dest.mkdir(parents=True, exist_ok=True)

    before = {p.resolve() for p in dest.glob("*")}
    cmd = [
        "kaggle", "competitions", "replay",
        str(episode_id),
        "-p", str(dest),
        "-q",
    ]
    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    if p.returncode != 0:
        return {
            "ok": False,
            "episode_id": episode_id,
            "error": (p.stderr or p.stdout or "download failed")[-3000:],
        }

    after = {p.resolve() for p in dest.glob("*")}
    new_files = sorted(after - before)

    # If file already existed, locate the standard episode filename.
    if not new_files:
        matches = sorted(dest.glob(f"*{episode_id}*"))
        new_files = [m.resolve() for m in matches]

    return {
        "ok": True,
        "episode_id": episode_id,
        "files": [str(Path(x).relative_to(ROOT)) for x in new_files],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leaderboard-top", type=int, default=30)
    ap.add_argument("--teams", type=int, default=20)
    ap.add_argument("--replays-per-team", type=int, default=2)
    ap.add_argument("--sleep", type=float, default=0.35)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if shutil.which("kaggle") is None:
        raise SystemExit(
            "kaggle CLI not found in this venv.\n"
            "Install/authenticate Kaggle CLI, then rerun."
        )

    if args.force and OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    REPLAYS.mkdir(parents=True, exist_ok=True)

    print("=== Live Kaggriculture population refresh ===")
    print("Repository root:", ROOT)
    print("Leaderboard rows:", args.leaderboard_top)
    print("Teams to scout:", args.teams)
    print("Replays/team:", args.replays_per_team)
    print()

    leaderboard = run_json([
        "competitions", "leaderboard", "kaggriculture",
        "--show",
        "--page-size", str(args.leaderboard_top),
    ])

    if isinstance(leaderboard, dict):
        # Be tolerant of a wrapper object in future CLI versions.
        for key in ("rows", "leaderboard", "submissions", "data"):
            if isinstance(leaderboard.get(key), list):
                leaderboard = leaderboard[key]
                break

    if not isinstance(leaderboard, list) or not leaderboard:
        raise SystemExit("Leaderboard command returned no rows.")

    leaderboard = leaderboard[:args.leaderboard_top]
    LEADERBOARD_JSON.write_text(
        json.dumps(leaderboard, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Saved leaderboard:", LEADERBOARD_JSON.relative_to(ROOT))
    print()

    manifest = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "settings": {
            "leaderboard_top": args.leaderboard_top,
            "teams": args.teams,
            "replays_per_team": args.replays_per_team,
        },
        "leaderboard_rows": leaderboard,
        "teams": [],
    }

    target_rows = leaderboard[: min(args.teams, len(leaderboard))]

    for idx, row in enumerate(target_rows, start=1):
        team_id = as_int(first_key(row, ("teamId", "team_id", "id")))
        team_name = first_key(row, ("teamName", "team_name", "name"))
        score = first_key(row, ("score", "publicScore", "rating"))

        print(
            f"[{idx:>2}/{len(target_rows)}] "
            f"{team_name!s} teamId={team_id} score={score}"
        )

        rec = {
            "leaderboard_index": idx,
            "team_id": team_id,
            "team_name": team_name,
            "leaderboard_score": score,
            "leaderboard_row": row,
            "submissions": [],
            "selected_submission": None,
            "episodes": [],
            "downloads": [],
            "errors": [],
        }

        if team_id is None:
            rec["errors"].append("Could not identify teamId from leaderboard row.")
            manifest["teams"].append(rec)
            continue

        try:
            submissions = run_json([
                "competitions", "team-submissions",
                str(team_id),
            ])
            if isinstance(submissions, dict):
                for key in ("rows", "submissions", "data"):
                    if isinstance(submissions.get(key), list):
                        submissions = submissions[key]
                        break

            if not isinstance(submissions, list):
                submissions = []

            rec["submissions"] = submissions

            usable = []
            for sub in submissions:
                sid = as_int(first_key(sub, ("id", "submissionId", "submission_id")))
                pscore = first_key(sub, ("publicScore", "score", "rating"))
                date = first_key(sub, ("dateSubmitted", "submissionDate", "date", "createTime"))
                if sid is not None:
                    usable.append((as_float(pscore), parse_time(date), sid, sub))

            if not usable:
                rec["errors"].append("No active submission ID found.")
                manifest["teams"].append(rec)
                continue

            # Highest public score; newest breaks ties.
            usable.sort(key=lambda x: (x[0], x[1]), reverse=True)
            _, _, submission_id, selected = usable[0]
            rec["selected_submission"] = selected
            rec["selected_submission_id"] = submission_id

            time.sleep(args.sleep)

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

            # Prefer completed/recent episodes.
            def ep_sort_key(ep):
                state = str(first_key(ep, ("state", "status")) or "").lower()
                complete = 1 if state in ("complete", "completed", "finished", "success") else 0
                created = parse_time(first_key(ep, ("createTime", "endTime", "date")))
                eid = as_int(first_key(ep, ("id", "episodeId", "episode_id"))) or -1
                return (complete, created, eid)

            episodes = sorted(episodes, key=ep_sort_key, reverse=True)
            rec["episodes"] = episodes

            chosen_eps = []
            for ep in episodes:
                eid = as_int(first_key(ep, ("id", "episodeId", "episode_id")))
                if eid is None:
                    continue
                chosen_eps.append(eid)
                if len(chosen_eps) >= args.replays_per_team:
                    break

            for eid in chosen_eps:
                team_dir = REPLAYS / f"{idx:02d}_{team_id}"
                d = download_replay(eid, team_dir)
                rec["downloads"].append(d)
                if not d["ok"]:
                    rec["errors"].append(
                        f"Replay {eid} download failed: {d.get('error','')}"
                    )
                time.sleep(args.sleep)

        except Exception as e:
            rec["errors"].append(f"{type(e).__name__}: {e}")

        manifest["teams"].append(rec)
        MANIFEST_JSON.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    MANIFEST_JSON.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    ok_downloads = sum(
        1
        for team in manifest["teams"]
        for d in team.get("downloads", [])
        if d.get("ok")
    )
    teams_with_replay = sum(
        1
        for team in manifest["teams"]
        if any(d.get("ok") for d in team.get("downloads", []))
    )
    error_teams = [
        team for team in manifest["teams"]
        if team.get("errors")
    ]

    lines = [
        "# Live Kaggriculture Population Refresh — 2026-09-18",
        "",
        f"- Generated: `{manifest['generated']}`",
        f"- Leaderboard rows captured: **{len(leaderboard)}**",
        f"- Teams scouted: **{len(manifest['teams'])}**",
        f"- Teams with >=1 replay: **{teams_with_replay}**",
        f"- Replays downloaded: **{ok_downloads}**",
        f"- Teams with errors/warnings: **{len(error_teams)}**",
        "",
        "## Top leaderboard snapshot",
        "",
        "| Pos | Team | Score | Team ID | Selected submission | Replays |",
        "|---:|---|---:|---:|---:|---:|",
    ]

    for team in manifest["teams"]:
        downloads = sum(1 for d in team["downloads"] if d.get("ok"))
        lines.append(
            f"| {team['leaderboard_index']} | "
            f"{str(team.get('team_name') or '').replace('|','/')} | "
            f"{team.get('leaderboard_score')} | "
            f"{team.get('team_id')} | "
            f"{team.get('selected_submission_id','')} | "
            f"{downloads} |"
        )

    lines += [
        "",
        "## Notes",
        "",
        "- This is an acquisition snapshot, not a strategy ranking.",
        "- A small replay sample per team is for population/family mapping, not exact win-rate estimation.",
        "- Final objective remains population-level W/D/L / Bradley–Terry.",
        "",
    ]

    if error_teams:
        lines += ["## Errors / warnings", ""]
        for team in error_teams:
            lines.append(
                f"- {team.get('team_name')} ({team.get('team_id')}): "
                + "; ".join(team["errors"])
            )
        lines.append("")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

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
            f"## {manifest['generated']} — Refresh live leaderboard population\n\n"
            f"- Leaderboard rows: {len(leaderboard)}\n"
            f"- Teams scouted: {len(manifest['teams'])}\n"
            f"- Teams with replay: {teams_with_replay}\n"
            f"- Replays downloaded: {ok_downloads}\n"
            f"- Bundle: `{ZIP_OUT.name}`\n"
            "- Acquisition only; no agent modification or Kaggle submission.\n\n"
        )

    print()
    print("=== Refresh complete ===")
    print("Teams with replay:", teams_with_replay)
    print("Replays downloaded:", ok_downloads)
    print("Teams with warnings:", len(error_teams))
    print("Report:", REPORT_MD.relative_to(ROOT))
    print("Manifest:", MANIFEST_JSON.relative_to(ROOT))
    print("Bundle:", ZIP_OUT.name)


if __name__ == "__main__":
    main()
