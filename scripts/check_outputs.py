#!/usr/bin/env python3
"""Static checks for rendered teacher-and-blackboard course videos."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--min-seconds", type=float, default=180)
    parser.add_argument("--max-seconds", type=float, default=420)
    parser.add_argument("--skip-practice-check", action="store_true")
    parser.add_argument("--min-scenes", type=int, default=8)
    args = parser.parse_args()

    out = Path(args.output_dir)
    errors: list[str] = []
    rows: list[tuple[str, float, int, int, int]] = []

    for chapter in range(1, 16):
        stem = f"python-ch{chapter:02d}"
        mp4, srt, timeline = (
            out / f"{stem}.mp4",
            out / f"{stem}.srt",
            out / f"{stem}-timeline.json",
        )
        for path in (mp4, srt, timeline):
            if not path.exists():
                errors.append(f"{stem}: missing {path.name}")
        if not all(path.exists() for path in (mp4, srt, timeline)):
            continue

        seconds = duration(mp4)
        if not args.min_seconds <= seconds <= args.max_seconds:
            errors.append(
                f"{stem}: duration {seconds:.1f}s outside "
                f"{args.min_seconds:.0f}-{args.max_seconds:.0f}s"
            )

        text = srt.read_text(encoding="utf-8")
        pipe_lines = sum(
            1 for line in text.splitlines()
            if line.startswith("|") and not line.isdigit()
        )
        malformed = re.findall(r"\?{2,}|[，。！？]\s*\n\s*[？?]", text)
        if pipe_lines:
            errors.append(f"{stem}: {pipe_lines} SRT lines begin with a code pipe")
        if malformed:
            errors.append(f"{stem}: {len(malformed)} malformed punctuation sequences")

        data = json.loads(timeline.read_text(encoding="utf-8"))
        beats = data.get("beats", [])
        empty_show = sum(1 for beat in beats if not str(beat.get("show", "")).strip())
        empty_say = sum(1 for beat in beats if not str(beat.get("say", "")).strip())
        scenes = data.get("scenes", [])
        practice = sum(
            1 for scene in scenes
            if "练习" in scene.get("title", "") or "练习" in scene.get("kicker", "")
        )
        if empty_show or empty_say:
            errors.append(
                f"{stem}: empty board/speech beats ({empty_show}/{empty_say})"
            )
        if len(scenes) < args.min_scenes:
            errors.append(f"{stem}: only {len(scenes)} scenes")
        if practice < 1 and not args.skip_practice_check:
            errors.append(f"{stem}: no exercise scene")
        rows.append((stem, seconds, len(scenes), len(beats), pipe_lines))

    print("chapter  duration  scenes  beats  raw_code_in_srt")
    for stem, seconds, scene_count, beat_count, pipes in rows:
        print(f"{stem:8} {seconds:7.1f}s {scene_count:7} {beat_count:6} {pipes:17}")

    if errors:
        print("\nFAILED")
        for error in errors:
            print("-", error)
        return 1
    print("\nOK: all outputs passed static checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
