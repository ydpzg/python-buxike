#!/usr/bin/env python3
"""Compatibility entry point for older commands.

The canonical course renderer is `build_course_video.py`. This wrapper keeps
the previous `--chapter` command working.
"""
from pathlib import Path
import runpy

runpy.run_path(
    str(Path(__file__).with_name("build_course_video.py")),
    run_name="__main__",
)
