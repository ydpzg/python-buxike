# Repository instructions

This repository builds Chinese technical course videos in a teacher-and-blackboard style.

## Before editing

1. Read `README.md`, `workflow/production-checklist.md`, and `workflow/lessons-learned.md`.
2. Read `skills/teacher-blackboard-video/SKILL.md` before changing video content or layout.
3. Inspect the target chapter in `content/remaining_chapters.py` or `content/chapter2_content.py`.

## Content invariants

- A beat is `(旁白, 板书)`.
- The first element is spoken narration; it must never contain raw pipe-delimited code.
- The second element is board content; code starts with `|`.
- The opening frame contains chapter number, title, and teacher.
- The opening frame lasts through the opening narration; subtitles begin with the first spoken beat.
- Exercise scenes use `layout="practice"` and include task, flow, code, and acceptance checks.
- The outro names concrete concepts, validation boundaries, exercise title, and next chapter.

## Build

```bash
python scripts/build_ch02.py --chapter N --preview
python scripts/build_ch02.py --chapter N --reuse-audio
```

Never reuse an old audio cache after changing narration unless the cache version has changed.

## Review

Run:

```bash
python scripts/check_outputs.py --output-dir outputs --min-seconds 180 --max-seconds 420
```

Also inspect at least the cover, first subtitle, practice page, terminal indentation, and outro. Use subagents for large reviews only when the user asks; assign 2–3 chapters per review.

## Publishing

Do not commit MP4, WAV, MP3, AIFF, frame dumps, or other large generated media. Publish videos through YouTube, object storage, or GitHub Releases. Keep source, docs, metadata, and small example screenshots in Git.
