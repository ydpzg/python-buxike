#!/usr/bin/env python3
"""Generate the Python 补习课 course title card.

The visual reuses the course renderer's classroom, blackboard, chalk and
teacher primitives, so the course title stays consistent with every chapter.
"""
from pathlib import Path
import sys

from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_course_video import (  # noqa: E402
    CB, CG, CHALK, CHALK_D, CL, COURSE_SUBTITLE, COURSE_TAGLINE,
    COURSE_TITLE, CY, F_KICK, F_LEAD, F_SMALL, OUT, pf,
    chalk_accent, chalk_box, chalk_text, draw_board, draw_classroom,
    draw_teacher,
)


def build_title_card() -> Image.Image:
    img = Image.new("RGB", (1920, 1080), (240, 235, 224))
    d = ImageDraw.Draw(img, "RGBA")
    d._image = img
    draw_classroom(img, d)
    draw_board(img, d)

    chalk_text(img, (CL, 158), "PYTHON 入门课程", F_KICK, CB, 1.0)
    chalk_text(img, (CL, 204), COURSE_TAGLINE, F_KICK, CHALK_D, 0.95)

    chalk_text(img, (CL, 292), COURSE_TITLE, pf(132, 3), CHALK, 1.0)
    chalk_accent(d, CL, 464, 12, CY, 12, 1.0)
    chalk_text(img, (CL, 514), COURSE_SUBTITLE, pf(62, 2), CY, 1.0)

    chalk_box(d, [CL, 650, 1260, 790], 18, CG, 3, alpha=1.0)
    chalk_text(img, (CL + 44, 682), "第 1–15 章", F_LEAD, CHALK, 1.0)
    chalk_text(img, (CL + 360, 690), "老师 + 黑板 · 中文讲解 · 代码练习", F_SMALL, CHALK_D, 1.0)

    draw_teacher(img, d, 0.0, (630, 360))
    return img


def main() -> None:
    out = Path(OUT)
    out.mkdir(parents=True, exist_ok=True)
    assets = Path(__file__).resolve().parent.parent / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    img = build_title_card()
    img.save(out / "python-course-title.png")
    img.save(assets / "course-title.png")
    print("title card ->", out / "python-course-title.png")


if __name__ == "__main__":
    main()
