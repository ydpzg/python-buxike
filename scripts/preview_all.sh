#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
for chapter in $(seq 3 15); do
  "$PYTHON" "$ROOT/scripts/build_course_video.py" --chapter "$chapter" --preview
done
