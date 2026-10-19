#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
for chapter in $(seq 3 15); do
  echo "=== chapter ${chapter} ==="
  "$PYTHON" "$ROOT/scripts/build_course_video.py" --chapter "$chapter" --reuse-audio
done
