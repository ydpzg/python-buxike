#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 补习课｜从零开始学 Python - 第 2–15 章视频生成器
画面主题：老师 + 黑板
  · 教室墙面 + 木质黑板框 + 深绿黑板 + 粉笔槽
  · 全屏粉笔字（带粉笔颗粒质感）
  · 黑板前的手绘老师：呼吸起伏、眨眼、教鞭指向当前讲解位置
pipeline: edge-tts -> 时间轴 -> PIL 逐帧渲染 -> ffmpeg 合成
"""
import json, os, subprocess, math, sys, asyncio, random

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(PROJECT_ROOT, "content")
if CONTENT_DIR not in sys.path:
    sys.path.insert(0, CONTENT_DIR)
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
import edge_tts

ROOT   = PROJECT_ROOT
WORK   = os.path.join(ROOT, "work", "video")
OUT    = os.path.join(ROOT, "outputs")
FRAMES = os.path.join(WORK, "frames_ch02")
MP3    = os.path.join(WORK, "mp3_ch02")
AUDIO_WORK = os.path.join(WORK, "audio_ch02")
SHOTS  = os.path.join(OUT, "preview", "ch02")
for d in (WORK, FRAMES, OUT, MP3, AUDIO_WORK, SHOTS):
    os.makedirs(d, exist_ok=True)

W, H, FPS = 1920, 1080, 30
SLUG = "python-ch02"

# ---------- palette: 教室 / 黑板 / 粉笔 ----------
WALL_A   = (240, 235, 224)
WALL_B   = (219, 210, 195)
FLOOR    = (176, 160, 141)
BOARD    = (30, 57, 50)
FRAME    = (148, 102, 60)
FRAME_DK = (100, 66, 36)
FRAME_HI = (182, 134, 84)
CHALK    = (238, 241, 233)
CHALK_D  = (160, 178, 168)
CY       = (247, 212, 118)
CB       = (148, 200, 242)
CP       = (246, 166, 156)
CG       = (150, 226, 170)
INK2     = (96, 100, 112)
# 黑板上的"屏幕"（终端面板）
TP_BG    = (16, 25, 23)
TP_HD    = (29, 42, 38)
TP_LINE  = (72, 92, 84)
TP_TXT   = (228, 238, 230)
TP_DIM   = (146, 166, 156)

# ---------- fonts ----------
def pf(size, weight=1):
    idx = {0: 11, 1: 2, 2: 5, 3: 8}[weight]
    return ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", size, index=idx)
def mono(size):
    return ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", size)

F_HUGE   = pf(104, 3)
F_TITLE  = pf(70, 3)
F_QUOTE  = pf(66, 2)
F_LEAD   = pf(42, 2)
F_BODY   = pf(35, 1)
F_SUB    = pf(34, 1)
F_SMALL  = pf(28, 1)
F_TINY   = pf(23, 1)
F_KICK   = mono(24)
F_CODE   = mono(30)
F_CODE_S = mono(26)
F_CODE_COMPACT = mono(18)
F_CODE_CH12     = mono(20)
F_BADGE  = mono(26)
F_WM     = mono(280)


# ============================================================
# narration script (v2: 更口语、更短句)
# ============================================================
from remaining_chapters import CHAPTERS
from chapter2_content import SCENES as CHAPTER2_SCENES, CAPTION_OVERRIDES as CHAPTER2_CAPTIONS
from course import COURSE_TITLE, COURSE_SUBTITLE, COURSE_TAGLINE

# 保留第 2 章的原稿，使同一套黑板模板可以重新生成第 2 章。
CHAPTERS[2] = dict(title="变量、表达式与语句", scenes=CHAPTER2_SCENES,
                   captions=CHAPTER2_CAPTIONS)

CONTENT_CHAPTER = 2
CAPTION_OVERRIDES = {}


VOICE  = "zh-CN-YunxiNeural"
RATE   = "+20%"
PITCH  = "+0Hz"
GAP_BEAT  = 0.30
GAP_SCENE = 0.85
TAIL      = 1.40
HEAD      = 0.80

SCENE_COL = [CB, CY, CP, CG, CB, CY, CG, CP, CB, CY, CG, CP, CB]
CODE_BEAT_KEYS = set()

CL = 150                       # 黑板内容左边界
CR = 1380                      # 黑板内容右边界
BOARD_BOX = (64, 70, 1856, 900)
TEACHER_X, TEACHER_FY = 1700, 1006

# ============================================================
#  helpers
# ============================================================
def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(" ".join(cmd) + "\n" + p.stderr[-2000:])
    return p.stdout

def dur_of(path):
    out = run(["ffprobe","-v","error","-show_entries","format=duration",
               "-of","default=nw=1:nk=1", path])
    return float(out.strip())

def audio_stem(scene_index, beat_index):
    """Return a cache stem; selected chapter 12 feedback scenes can be refreshed."""
    suffix = ""
    if (scene_index, beat_index) in CODE_BEAT_KEYS:
        suffix += "_codefix1"
    if "--refresh-exercise" in sys.argv and scene_index == 10 and beat_index == 2:
        suffix = "_v2"
    if ("--refresh-outro" in sys.argv and CONTENT_CHAPTER == 12
            and scene_index == len(SCENES) - 1):
        suffix = "_ch12_outro_v1"
    if ("--refresh-ch12-feedback" in sys.argv and CONTENT_CHAPTER == 12
            and scene_index in (4, 10, len(SCENES) - 1)):
        suffix = "_ch12_feedback_v3"
    return f"s{scene_index}_b{beat_index}{suffix}"

TRIM = ("silenceremove=start_periods=1:start_threshold=-50dB:start_duration=0.02,"
        "areverse,"
        "silenceremove=start_periods=1:start_threshold=-50dB:start_duration=0.02,"
        "areverse")

async def _tts_one(text, mp3_path, sem):
    async with sem:
        for attempt in range(4):
            try:
                c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
                buf = bytearray()
                async for ch in c.stream():
                    if ch["type"] == "audio":
                        buf += ch["data"]
                if len(buf) < 1200:
                    raise RuntimeError("short audio")
                with open(mp3_path, "wb") as f:
                    f.write(bytes(buf))
                return
            except Exception:
                if attempt == 3:
                    raise
                await asyncio.sleep(1.2 * (attempt + 1))

def synth_all(items, reuse_audio=False):
    """items: [(text, mp3_path, wav_path)] -> 并发合成，返回时长列表"""
    if reuse_audio:
        missing = [(text, mp3, wav) for text, mp3, wav in items
                   if not os.path.isfile(mp3) or not os.path.isfile(wav)]
        if missing:
            async def regen_missing():
                sem = asyncio.Semaphore(5)
                await asyncio.gather(*[_tts_one(text, mp3, sem)
                                       for text, mp3, _ in missing])
            asyncio.run(regen_missing())
            for _, mp3, wav in missing:
                run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-af", TRIM,
                     "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", wav])
        return [dur_of(w) for _, _, w in items]

    async def go():
        sem = asyncio.Semaphore(5)
        await asyncio.gather(*[_tts_one(t, m, sem) for t, m, _ in items])
    asyncio.run(go())
    durs = []
    for _, m, w in items:
        run(["ffmpeg","-y","-v","error","-i",m,"-af",TRIM,
             "-ar","44100","-ac","1","-c:a","pcm_s16le",w])
        durs.append(dur_of(w))
    return durs

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def ease(x):
    x = clamp(x)
    return 1 - (1-x)**3

def fade(t, start, dur=0.42):
    return ease((t-start)/dur)

def wrap(d, text, font, maxw):
    lines, cur = [], ""
    # Keep closing punctuation attached to the preceding text.
    closing = "，。！？；：、）》】」』”’…"
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if d.textlength(cur+ch, font=font) > maxw and cur:
            if ch in closing:
                cur += ch
                lines.append(cur); cur = ""
            else:
                lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines

# ============================================================
#  粉笔字
# ============================================================
_NW, _NH = 2048, 384

def _noise_bank():
    rnd = random.Random(20261016)
    img = Image.new("L", (_NW, _NH))
    px = img.load()
    for y in range(_NH):
        for x in range(_NW):
            r = rnd.random()
            px[x, y] = 255 if r > 0.20 else (70 + rnd.randint(0, 130))
    return img

_NOISE = _noise_bank()
_CHALK = {}

def _noise_for(w, h, seed):
    rnd = random.Random(seed)
    cw, chh = min(w, _NW), min(h, _NH)
    ox = rnd.randrange(0, max(1, _NW - cw))
    oy = rnd.randrange(0, max(1, _NH - chh))
    tile = _NOISE.crop((ox, oy, ox+cw, oy+chh))
    if (cw, chh) == (w, h):
        return tile
    out = Image.new("L", (w, h))
    for y in range(0, h, chh):
        for x in range(0, w, cw):
            out.paste(tile, (x, y))
    return out

def _chalk_layer(s, font, fill):
    key = (getattr(font, "path", "?"), font.size, getattr(font, "index", None), s, fill)
    got = _CHALK.get(key)
    if got is not None:
        return got
    pad = 14
    tw = int(font.getlength(s)) + 2
    fh = int(font.size * 1.45) + 6
    mask = Image.new("L", (tw + pad*2, fh + pad*2), 0)
    md = ImageDraw.Draw(mask)
    md.text((pad, pad), s, font=font, fill=255, anchor="la")
    noise = _noise_for(mask.width, mask.height, hash(key) & 0xffffff)
    mask = ImageChops.multiply(mask, noise)
    rgb = Image.new("RGB", mask.size, fill)
    got = (rgb, mask, pad, tw, fh)
    _CHALK[key] = got
    return got

def chalk_text(img, xy, s, font, fill, alpha=1.0, anchor="la"):
    """在 img 上写粉笔字；anchor 支持 l/m/r + a/m/b"""
    if alpha <= 0.02 or not s:
        return
    rgb, mask, pad, tw, fh = _chalk_layer(s, font, fill)
    x, y = float(xy[0]), float(xy[1])
    ax, ay = anchor[0], (anchor[1] if len(anchor) > 1 else "a")
    if ax == "m":
        x -= pad + tw/2.0
    elif ax == "r":
        x -= pad + tw
    else:
        x -= pad
    if ay == "m":
        y -= pad + fh/2.0
    elif ay == "b":
        y -= pad + fh
    else:
        y -= pad
    if alpha < 0.995:
        mask = mask.point(lambda v: int(v*alpha))
    img.paste(rgb, (int(round(x)), int(round(y))), mask)

def chalk_box(d, box, r=16, col=CHALK_D, w=3, fill=None, alpha=1.0):
    if fill is not None:
        d.rounded_rectangle(box, radius=r, fill=fill)
    d.rounded_rectangle(box, radius=r, width=w,
                        outline=(col[0], col[1], col[2], int(235*alpha)))
    d.rounded_rectangle([box[0]+2, box[1]+2, box[2]-2, box[3]-2],
                        radius=max(3, r-3), width=1,
                        outline=(col[0], col[1], col[2], int(90*alpha)))

def chalk_accent(d, x, y, h, col, w=8, alpha=1.0):
    d.rounded_rectangle([x, y, x+w, y+h], radius=w//2,
                        fill=(col[0], col[1], col[2], int(255*alpha)))

def _limb(d, p0, p1, w, col):
    d.line([p0, p1], fill=col, width=w, joint="curve")
    r = w/2.0
    for p in (p0, p1):
        d.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], fill=col)

# ============================================================
#  背景 / 黑板
# ============================================================
def draw_classroom(img, d):
    step = 4
    for y in range(0, H, step):
        k = y / H
        c = tuple(int(WALL_A[i] + (WALL_B[i]-WALL_A[i])*k) for i in range(3))
        d.rectangle([0, y, W, y+step], fill=c)
    d.rectangle([0, 1024, W, H], fill=FLOOR)
    d.rectangle([0, 1024, W, 1030], fill=(152, 138, 120))

def draw_board(img, d):
    x0, y0, x1, y1 = BOARD_BOX
    f = 16
    d.rounded_rectangle([x0-f-4, y0-f-4, x1+f+4, y1+f+8], radius=12, fill=(196, 186, 170))
    d.rounded_rectangle([x0-f, y0-f, x1+f, y1+f], radius=10, fill=FRAME)
    d.rounded_rectangle([x0-f, y0-f, x1+f, y0-f+9], radius=6, fill=FRAME_HI)
    d.rectangle([x0-f, y1+4, x1+f, y1+f], fill=FRAME_DK)
    d.rectangle([x0, y0, x1, y1], fill=BOARD)
    # 中央柔光 + 四周暗角
    gl = Image.new("L", (96, 54), 0)
    ImageDraw.Draw(gl).ellipse([8, 4, 88, 50], fill=110)
    gl = gl.filter(ImageFilter.GaussianBlur(11)).resize((x1-x0, y1-y0), Image.BILINEAR)
    img.paste(Image.new("RGB", (x1-x0, y1-y0), (48, 80, 68)), (x0, y0), gl)
    img.paste(Image.new("RGB", (x1-x0, y1-y0), (12, 26, 22)),
              (x0, y0), gl.point(lambda v: 110 - int(v*0.9)))
    # 擦过粉笔的痕迹
    for (sx, sy, sw, sh, a) in ((260, 300, 900, 300, 0.30), (150, 620, 620, 240, 0.22),
                                (980, 180, 760, 260, 0.20)):
        sm = Image.new("L", (48, 24), 0)
        ImageDraw.Draw(sm).ellipse([4, 3, 44, 21], fill=120)
        sm = sm.filter(ImageFilter.GaussianBlur(7)).resize((sw, sh), Image.BILINEAR)
        img.paste(Image.new("RGB", (sw, sh), (150, 175, 162)), (x0+sx, y0+sy),
                  sm.point(lambda v: int(v*a)))
    # 粉笔槽
    ty = y1 + 10
    d.rounded_rectangle([x0+110, ty, x1-110, ty+28], radius=9, fill=FRAME_DK)
    d.rounded_rectangle([x0+110, ty-7, x1-110, ty+7], radius=7, fill=FRAME_HI)
    for i, c in enumerate((CHALK, CY, CP)):
        bx = x0 + 210 + i*74
        d.rounded_rectangle([bx, ty-14, bx+56, ty-4], radius=5, fill=c)
    d.rounded_rectangle([x1-450, ty-26, x1-280, ty-4], radius=7, fill=(58, 62, 70))
    d.rectangle([x1-456, ty-10, x1-274, ty-4], fill=(198, 192, 180))

# ============================================================
#  老师
# ============================================================
SKIN, SKIN_D = (243, 210, 182), (219, 183, 154)
SHIRT, SHIRT_D = (74, 122, 190), (56, 96, 158)
PANTS, SHOE = (52, 60, 82), (38, 42, 54)
HAIR = (56, 44, 40)

def draw_teacher(img, d, t, target):
    fx = TEACHER_X
    fy = TEACHER_FY + math.sin(t*1.7)*3.5
    d.ellipse([fx-132, fy-18, fx+132, fy+16], fill=(0, 0, 0, 64))
    # 腿 + 鞋
    d.rounded_rectangle([fx-74, fy-238, fx-14, fy-8], 18, fill=PANTS)
    d.rounded_rectangle([fx+14, fy-238, fx+74, fy-8], 18, fill=PANTS)
    d.rounded_rectangle([fx-88, fy-36, fx-4, fy-2], 16, fill=SHOE)
    d.rounded_rectangle([fx+4, fy-36, fx+88, fy-2], 16, fill=SHOE)
    # 身体
    d.rounded_rectangle([fx-106, fy-506, fx+106, fy-214], 46, fill=SHIRT)
    d.rounded_rectangle([fx-106, fy-506, fx+106, fy-424], 46, fill=SHIRT_D)
    d.polygon([(fx-34, fy-508), (fx, fy-462), (fx+34, fy-508)], fill=(250, 250, 248))
    # 右臂（自然下垂）
    _limb(d, (fx+86, fy-470), (fx+118, fy-300), 36, SHIRT)
    _limb(d, (fx+118, fy-302), (fx+126, fy-212), 30, SKIN)
    # 左臂 + 教鞭（指向 target 方向）
    sh = (fx-90, fy-470)
    vx, vy = target[0]-sh[0], target[1]-sh[1]
    L = math.hypot(vx, vy) or 1.0
    ux, uy = vx/L, vy/L
    hx, hy = sh[0]+ux*240, sh[1]+uy*240
    ex, ey = sh[0]+ux*126 - uy*24, sh[1]+uy*126 + ux*24
    _limb(d, sh, (ex, ey), 36, SHIRT)
    _limb(d, (ex, ey), (hx, hy), 30, SKIN)
    d.ellipse([hx-19, hy-19, hx+19, hy+19], fill=SKIN)
    px, py = hx+ux*8, hy+uy*8
    qx, qy = hx+ux*205, hy+uy*205
    d.line([(px, py), (qx, qy)], fill=(198, 160, 110), width=10)
    d.line([(px, py), (qx, qy)], fill=(234, 204, 156), width=4)
    # 脖子 + 头
    d.rounded_rectangle([fx-20, fy-544, fx+20, fy-492], 12, fill=SKIN_D)
    cy = fy - 596
    d.ellipse([fx-64, cy-68, fx+64, cy+68], fill=SKIN)
    d.ellipse([fx-74, cy-8, fx-56, cy+24], fill=SKIN)
    d.ellipse([fx+56, cy-8, fx+74, cy+24], fill=SKIN)
    d.pieslice([fx-66, cy-78, fx+66, cy+56], 180, 360, fill=HAIR)
    d.pieslice([fx-64, cy-72, fx+4, cy-2], 205, 335, fill=HAIR)
    # 眼镜 + 眼睛（会眨）
    for dx in (-26, 26):
        d.ellipse([fx+dx-21, cy-16, fx+dx+21, cy+26], outline=(72, 62, 56), width=4)
    d.line([(fx-6, cy+4), (fx+6, cy+4)], fill=(72, 62, 56), width=4)
    if (t % 3.6) < 0.13:
        for dx in (-26, 26):
            d.line([(fx+dx-11, cy+5), (fx+dx+11, cy+5)], fill=(60, 52, 48), width=4)
    else:
        for dx in (-26, 26):
            d.ellipse([fx+dx-9, cy-3, fx+dx+9, cy+15], fill=(48, 42, 40))
    d.line([(fx-42, cy-28), (fx-12, cy-34)], fill=(64, 52, 46), width=6)
    d.line([(fx+12, cy-34), (fx+42, cy-28)], fill=(64, 52, 46), width=6)
    d.arc([fx-24, cy+26, fx+24, cy+60], 20, 160, fill=(170, 98, 86), width=5)

def pointer_target(sc, bi):
    """教鞭指向当前讲解内容（v3 坐标）"""
    lay = sc["layout"]
    # Chapter 2 uses scene-specific board areas; keep the teacher's pointer
    # on the active line/card rather than reusing chapter 1 positions.
    if (sc["id"] in ("types", "statements", "operators", "precedence", "strings")
            or sc["id"].split("-/-", 1)[0].isdigit()):
        if bi < 2:
            return (640, 380 + bi*74)
        return (480, 600) if bi == 2 else (1060, 600)
    if sc["id"] in ("remainder", "input", "comments"):
        return (560, 380) if bi < 2 else (1080, 520)
    if lay == "cover":
        return (620, 336 + min(bi, 2)*78)
    if lay == "quote":
        return (560, 440) if bi <= 2 else (400, 700)
    if lay == "practice":
        if bi == 0:
            return (540, 300)
        if bi == 1:
            return (620, 350)
        if bi == 2:
            return (760, 760)
        if bi == 3:
            return (1250, 760)
        return (520, 610)
    if CONTENT_CHAPTER == 12 and sc["kicker"] == "04 / 解析 HTML":
        return (1500, 820)
    if lay == "code":
        if any(s.startswith("|") for _, s in sc["beats"][:bi+1]):
            return (1090, 470 + max(0, bi-2)*64)
        return (520, 380 + bi*84)
    if lay == "hardware":
        if bi == 0:
            return (780, 372)
        if bi <= 3:
            return [(400, 470), (820, 470), (1240, 430)][bi-1]
        return (770, 742)
    if lay == "duo":
        return (480, 330) if bi < 2 else ((480, 620) if bi == 2 else (1060, 620))
    if lay == "errors":
        return (770, 320) if bi == 0 else (770, 440 + (bi-1)*148)
    if lay == "outro":
        return (560, 400 + min(bi, 3)*84) if bi < 4 else (770, 748)
    return (1200, 420)

# ============================================================
#  render
# ============================================================
timeline, scene_starts, scene_dur, total = [], [], [], 1.0

def scene_of(t):
    cur = None
    for i, s in enumerate(scene_starts):
        if t >= s - 0.35:
            cur = i
    return cur

def beats_in(t, si):
    return [it for it in timeline if it["scene"] == si and t >= it["start"]]

def fit_code_font(text, base_size, min_size, max_width):
    """Shrink a monospace line only when its visible width needs it."""
    text = text.rstrip()
    size = base_size
    has_non_ascii = any(ord(ch) > 127 for ch in text)
    def font_at(value):
        return pf(value, 1) if has_non_ascii else mono(value)
    while size > min_size and font_at(size).getlength(text) > max_width:
        size -= 1
    return font_at(size)

def code_panel(img, d, x, y, w, lines, k, tag="terminal", h=None,
               compact=False, reveal_step=0.14):
    # Long examples use compact spacing when a scene explicitly asks for it.
    if compact:
        lh, pad, hh = 27, 16, 36
    else:
        lh, pad, hh = (38, 18, 40) if len(lines) > 8 else (50, 24, 44)
    body = pad + len(lines)*lh + pad - 10
    total_h = hh + body if h is None else h
    fill = tuple(int(BOARD[i] + (TP_BG[i]-BOARD[i])*clamp(k)) for i in range(3))
    chalk_box(d, [x, y, x+w, y+total_h], 14, CHALK_D, 3, fill=fill, alpha=clamp(k))
    if k > 0.05:
        d.rounded_rectangle([x+1, y+1, x+w-1, y+hh+12], radius=13, fill=TP_HD)
        d.rectangle([x+1, y+hh, x+w-1, y+hh+2], fill=TP_LINE)
        for i, c in enumerate((CP, CY, CG)):
            d.ellipse([x+20+i*24, y+16, x+20+i*24+12, y+28], fill=c)
        chalk_text(img, (x+100, y+12), tag, F_TINY, TP_DIM, k)
    yy = y + hh + pad
    max_width = w - (pad * 2) - 8
    for i, ln in enumerate(lines):
        kk = clamp((k - i*reveal_step) / 0.55)
        if ln.startswith(">>>") or ln.startswith("$"):
            chalk_text(img, (x+pad, yy), ln[:3], F_CODE, CB, kk)
            prompt = ln[3:].strip()
            font = fit_code_font(prompt, 30, 18, w - pad - 70)
            chalk_text(img, (x+pad+62, yy), prompt, font, TP_TXT, kk)
        elif ln.startswith(("    ", "\t")):
            base = F_CODE_CH12.size if CONTENT_CHAPTER == 12 else (18 if compact else 22)
            font = fit_code_font(ln, base, 14 if compact else 16, max_width)
            chalk_text(img, (x+pad, yy), ln, font, CG, kk)
        elif "Error" in ln or "error" in ln:
            base = 18 if compact else (F_CODE_CH12.size if CONTENT_CHAPTER == 12 else 22)
            font = fit_code_font(ln, base, 14 if compact else 16, max_width)
            chalk_text(img, (x+pad, yy), ln, font, CP, kk)
        else:
            if compact:
                base = F_CODE_COMPACT.size
            elif CONTENT_CHAPTER == 12 and len(lines) > 8:
                base = F_CODE_CH12.size
            elif len(lines) > 8:
                base = 22
            else:
                base = F_CODE_S.size if len(ln) > 30 else F_CODE.size
            font = fit_code_font(ln, base, 14 if compact else 16, max_width)
            chalk_text(img, (x+pad, yy), ln, font,
                       CG if i else TP_TXT, kk)
        yy += lh
    return total_h

def subtitle(d, t):
    cur = None
    for it in timeline:
        if it["start"] - 0.18 <= t < it["start"] + it["dur"] + 0.34:
            cur = it
    if cur is None:
        return
    a = min(fade(t, cur["start"]-0.18, 0.26), 1 - fade(t, cur["start"]+cur["dur"]+0.10, 0.22))
    caption = cur.get("caption", cur["say"])
    lines = wrap(d, caption, F_SUB, 1120)[:2]
    lh = 48
    bh = 26 + len(lines)*lh
    y2, y1 = 1062, 1062 - bh
    box = [W/2 - 600, y1, W/2 + 600, y2]
    ov = Image.new("RGBA", (int(box[2]-box[0]), int(y2-y1)), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle([0, 0, ov.width-1, ov.height-1], radius=18, fill=(255, 255, 255, 236))
    od.rounded_rectangle([0, 0, ov.width-1, ov.height-1], radius=18,
                         outline=(120, 112, 96, 90), width=2)
    ov.putalpha(ov.getchannel("A").point(lambda v: int(v*a)))
    d._image.paste(ov, (int(box[0]), int(y1)), ov)
    yy = y1 + 13
    for ln in lines:
        d.text((W/2, yy), ln, font=F_SUB, fill=(30, 34, 42, int(255*a)), anchor="ma")
        yy += lh

def ribbon(d, t, si):
    y0, hgt, gap = 92, 6, 6
    x0, _, x1, _ = BOARD_BOX
    avail = (x1-x0) - 60 - gap*(len(SCENES)-1)
    x = float(x0 + 30)
    for i, sc in enumerate(SCENES):
        wdt = avail * scene_dur[i] / total
        col = (42, 72, 62)
        if i < si:
            col = (68, 102, 90)
        elif i == si:
            col = SCENE_COL[i]
        d.rounded_rectangle([int(x), y0, int(x+wdt)+1, y0+hgt], radius=3, fill=col)
        x += wdt + gap

def chrome(d, t, si):
    d.text((96, 1036), f"{int(t)//60:02d}:{int(t)%60:02d} / "
                       f"{int(total)//60:02d}:{int(total)%60:02d}",
           font=mono(22), fill=(88, 80, 66))
    d.text((96, 26), f"共 15 章 · 第 {CONTENT_CHAPTER} 章", font=pf(22, 1), fill=INK2, anchor="la")
    if si is not None:
        sc = SCENES[si]
        col = SCENE_COL[si]
        lbl = sc["kicker"]
        tw = d.textlength(lbl, font=F_KICK)
        x2 = W - 96
        x1 = x2 - tw - 52
        d.rounded_rectangle([x1, 22, x2, 70], radius=24, fill=(col[0], col[1], col[2], 46))
        d.text(((x1+x2)/2, 46), lbl, font=F_KICK, fill=col, anchor="mm")

def scene_header(img, d, sc, t, si):
    a = fade(t, scene_starts[si]-0.15, 0.5)
    y = 152 + (1-a)*18
    num = sc["kicker"].split(" / ")[0]
    col = SCENE_COL[si]
    chalk_box(d, [CL, y, CL+74, y+70], 18, col, 3, alpha=a)
    chalk_text(img, (CL+37, y+35), num, F_BADGE, col, a, anchor="mm")
    chalk_text(img, (CL+106, y-8), sc["title"], F_TITLE, CHALK, a)
    ry = y + 100
    d.rounded_rectangle([CL+106, ry, CL+106+int(150*a), ry+7], radius=4,
                        fill=(CY[0], CY[1], CY[2], int(220*a)))
    return ry

def draw_frame(t):
    img = Image.new("RGB", (W, H), WALL_A)
    d = ImageDraw.Draw(img, "RGBA")
    d._image = img
    draw_classroom(img, d)
    draw_board(img, d)
    si = scene_of(t)
    ribbon(d, t, si if si is not None else -1)
    if si is None:
        chrome(d, t, None)
        return img
    sc = SCENES[si]
    bs = beats_in(t, si)
    lay = sc["layout"]

    # ---------------- cover ----------------
    if lay == "cover":
        a = fade(t, 0.10, 0.8)
        wm = fade(t, 0.35, 1.0)
        chalk_text(img, (CL, 160), sc["kicker"], F_KICK, CB, a)
        chalk_text(img, (CL, 214), COURSE_TAGLINE, F_KICK, CHALK_D, a*0.95)
        yy = 320 + (1-a)*22
        chalk_text(img, (CL, yy), sc["title"], F_HUGE, CHALK, a)
        d.rounded_rectangle([CL, yy+142, CL+int(240*a), yy+154], radius=6,
                            fill=(CY[0], CY[1], CY[2], int(230*a)))
        y = yy + 232
        for it in bs:
            k = fade(t, it["start"], 0.42)
            d.ellipse([CL+2, y+16, CL+22, y+36], width=3,
                      outline=(CHALK_D[0], CHALK_D[1], CHALK_D[2], int(255*k)))
            chalk_text(img, (CL+48, y), it["show"], F_LEAD, CHALK, k)
            y += 78

    # ---------------- quote ----------------
    elif lay == "quote":
        ry = scene_header(img, d, sc, t, si)
        caps = [it for i, it in enumerate(bs) if i == 0]
        if caps:
            k = fade(t, caps[0]["start"], 0.42)
            chalk_text(img, (CL+106, ry+52), caps[0]["show"], F_SMALL, CHALK_D, k)
        q = [it for i, it in enumerate(bs) if i == 2]
        if q:
            k = fade(t, q[0]["start"], 0.5)
            qx, qy = CL, ry + 150 + (1-k)*20
            chalk_accent(d, qx, qy-6, 158, CY, 8, k)
            chalk_text(img, (qx+46, qy), q[0]["show"], F_QUOTE, CHALK, k)
            chalk_text(img, (qx+46, qy+100), "— 电脑硬件问你的唯一一句话", F_TINY, CHALK_D, k*0.85)
        cards = [it for i, it in enumerate(bs) if i in (3, 4)]
        cx, cy, cw, ch, g = CL, ry+386, 580, 142, 40
        for i, it in enumerate(cards):
            k = fade(t, it["start"], 0.45)
            x = cx + i*(cw+g)
            yy = cy + (1-k)*20
            c2 = CB if i == 0 else CY
            chalk_box(d, [x, yy, x+cw, yy+ch], 16, c2, 3, alpha=k)
            chalk_accent(d, x+22, yy+34, ch-68, c2, 7, k)
            chalk_text(img, (x+56, yy+ch/2), it["show"], F_LEAD, CHALK, k, anchor="lm")

    # ---------------- code ----------------
    elif lay == "code":
        ry = scene_header(img, d, sc, t, si)
        y = ry + 64
        for it in bs:
            if it["show"].startswith("|"):
                continue
            k = fade(t, it["start"], 0.42)
            if y > 812:
                break
            chalk_accent(d, CL, y+12, 26, CY, 6, k)
            ls = wrap(d, it["show"], F_BODY, 520)
            for j, ln in enumerate(ls):
                chalk_text(img, (CL+40, y + j*46), ln, F_BODY, CHALK, k)
            y += 46*len(ls) + 30
        by = ry + 64
        for it in bs:
            if not it["show"].startswith("|"):
                continue
            k = fade(t, it["start"], 0.42)
            lines = it["show"].split("|")[1:]
            reveal_step = 0.45 / max(1, len(lines)-1) if CONTENT_CHAPTER == 12 else 0.14
            by += code_panel(img, d, 800, by, 580, lines, k,
                             reveal_step=reveal_step) + 34

    # ---------------- practice ----------------
    elif lay == "practice":
        ry = scene_header(img, d, sc, t, si)
        # Keep the exercise page instructional: task, end-to-end path, code,
        # and explicit checks are shown in separate regions of the board.
        task = bs[0] if len(bs) > 0 else None
        flow = bs[1] if len(bs) > 1 else None
        request = bs[2] if len(bs) > 2 else None
        parse = bs[3] if len(bs) > 3 else None
        check = bs[4] if len(bs) > 4 else None
        if task:
            k = fade(t, task["start"], 0.42)
            chalk_accent(d, CL, ry+38, 26, CY, 6, k)
            chalk_text(img, (CL+40, ry+26), task["show"], F_BODY, CHALK, k)
        if flow:
            k = fade(t, flow["start"], 0.42)
            chalk_text(img, (CL+40, ry+84), flow["show"], F_SMALL, CY, k)
        if request:
            k = fade(t, request["start"], 0.42)
            lines = request["show"].split("|")[1:]
            tags = sc.get("practice_tags", ("request", "parse"))
            code_panel(img, d, CL, ry+145, 620, lines, k, tag=tags[0],
                       h=410, compact=True,
                       reveal_step=0.45 / max(1, len(lines)-1))
        if parse:
            k = fade(t, parse["start"], 0.42)
            lines = parse["show"].split("|")[1:]
            tags = sc.get("practice_tags", ("request", "parse"))
            code_panel(img, d, 800, ry+145, 580, lines, k, tag=tags[1],
                       h=410, compact=True,
                       reveal_step=0.45 / max(1, len(lines)-1))
        if check:
            k = fade(t, check["start"], 0.42)
            chalk_box(d, [CL, ry+568, CR, ry+646], 16, CG, 3, alpha=k)
            chalk_text(img, (CL+30, ry+588), "验收", F_LEAD, CG, k)
            check_items = sc.get("checks", [check["show"]])
            for j, item in enumerate(check_items):
                x = CL + 210 + j*380
                chalk_text(img, (x, ry+592), item, F_TINY, CHALK, k)

    # ---------------- hardware ----------------
    elif lay == "hardware":
        ry = scene_header(img, d, sc, t, si)
        if bs:
            k = fade(t, bs[0]["start"], 0.42)
            chalk_text(img, (CL+106, ry+52), bs[0]["show"], F_SMALL, CHALK_D, k)
        nodes = [it for i, it in enumerate(bs) if i >= 1]
        boxes = [(CL, 390), (CL+420, 390), (CL+840, 350)]
        top = ry + 128
        for i, it in enumerate(nodes[:3]):
            k = fade(t, it["start"], 0.45)
            x, w = boxes[i]
            yy = top + (1-k)*22
            c2 = (CY, CB, CG)[i]
            chalk_box(d, [x, yy, x+w, yy+216], 18, c2, 3, alpha=k)
            chalk_accent(d, x+22, yy+34, 148, c2, 8, k)
            parts = it["show"].split("|")[1:]
            chalk_text(img, (x+62, yy+44), parts[0], pf(44, 3), c2, k)
            if len(parts) > 1:
                for j, ln in enumerate(wrap(d, parts[1], F_SMALL, w-112)):
                    chalk_text(img, (x+62, yy+126+j*42), ln, F_SMALL, CHALK, k)
        if len(nodes) > 3:
            it = nodes[3]
            k = fade(t, it["start"], 0.45)
            yy = top + 254 + (1-k)*22
            chalk_box(d, [CL, yy, CR, yy+168], 18, CP, 3, alpha=k)
            chalk_accent(d, CL+22, yy+32, 104, CP, 8, k)
            parts = it["show"].split("|")[1:]
            chalk_text(img, (CL+62, yy+38), parts[0], pf(44, 3), CHALK, k)
            if len(parts) > 1:
                chalk_text(img, (CL+62, yy+112), parts[1], F_SMALL, CHALK_D, k)

    # ---------------- duo ----------------
    elif lay == "duo":
        ry = scene_header(img, d, sc, t, si)
        y = ry + 54
        for it in [it for i, it in enumerate(bs) if i < 2]:
            k = fade(t, it["start"], 0.42)
            chalk_accent(d, CL, y+12, 26, CY, 6, k)
            chalk_text(img, (CL+40, y), it["show"], F_BODY, CHALK, k)
            y += 62
        cols = [it for i, it in enumerate(bs) if i >= 2]
        cx, cw, g = CL, 580, 40
        cy, ch = y + 30, 296
        for i, it in enumerate(cols):
            k = fade(t, it["start"], 0.5)
            x = cx + i*(cw+g)
            yy = cy + (1-k)*24
            c2 = CB if i == 0 else CY
            chalk_box(d, [x, yy, x+cw, yy+ch], 18, c2, 3, alpha=k)
            chalk_accent(d, x+24, yy+46, ch-92, c2, 8, k)
            show = it["show"]
            parts = [part for part in show.split("|")[1:] if part] if show.startswith("|") else [show]
            if not parts:
                parts = [show.strip("|") or show]
            if not show.startswith("|"):
                font = F_LEAD
                lines = wrap(d, parts[0], font, cw-112)
                if len(lines) > 4:
                    font = F_SMALL
                    lines = wrap(d, parts[0], font, cw-112)
                line_h = 52 if font == F_LEAD else 38
                text_y = yy + (ch-len(lines)*line_h)/2
                for j, line in enumerate(lines):
                    chalk_text(img, (x+66, text_y+j*line_h), line, font, CHALK, k)
                continue
            if len(parts) <= 3:
                chalk_text(img, (x+66, yy+48), parts[0], pf(52, 3), c2, k)
                if len(parts) > 1:
                    chalk_text(img, (x+66, yy+144), parts[1], F_LEAD, CHALK, k)
                if len(parts) > 2:
                    chalk_text(img, (x+66, yy+222), parts[2], F_SMALL, CHALK_D, k)
            else:
                # Keep longer examples inside the fixed card instead of
                # dropping lines after the third one.
                title_font = pf(46 if len(parts) <= 4 else 38, 3)
                body_font = F_SMALL if len(parts) <= 4 else F_TINY
                line_h = 58 if len(parts) <= 4 else 42
                chalk_text(img, (x+66, yy+34), parts[0], title_font, c2, k)
                for j, part in enumerate(parts[1:], 1):
                    color = CHALK if j == 1 else CHALK_D
                    chalk_text(img, (x+66, yy+34+j*line_h), part,
                               body_font, color, k)

    # ---------------- errors ----------------
    elif lay == "errors":
        ry = scene_header(img, d, sc, t, si)
        if bs:
            k = fade(t, bs[0]["start"], 0.42)
            chalk_text(img, (CL+106, ry+52), bs[0]["show"], F_SMALL, CHALK_D, k)
        rows = [it for i, it in enumerate(bs) if 1 <= i <= 3]
        y = ry + 118
        cols = (CY, CB, CG)
        for i, it in enumerate(rows):
            k = fade(t, it["start"], 0.45)
            yy = y + (1-k)*20
            chalk_box(d, [CL, yy, CR, yy+122], 16, CHALK_D, 3, alpha=k)
            d.rounded_rectangle([CL+3, yy+3, CL+13, yy+119], radius=5,
                                fill=(cols[i][0], cols[i][1], cols[i][2], int(235*k)))
            chalk_text(img, (CL+56, yy+61), f"0{i+1}", mono(40), cols[i], k, anchor="lm")
            chalk_text(img, (CL+164, yy+61), it["show"], pf(46, 3), CHALK, k, anchor="lm")
            y += 148
        last = [it for i, it in enumerate(bs) if i == 4]
        if last:
            k = fade(t, last[0]["start"], 0.5)
            chalk_text(img, (CL, y+6), last[0]["show"], pf(50, 3), CY, k)

    # ---------------- outro ----------------
    elif lay == "outro":
        ry = scene_header(img, d, sc, t, si)
        items = [it for i, it in enumerate(bs) if i <= 3]
        cx, cw, gap = CL, 580, 40
        top, card_h, row_gap = ry + 64, 154, 24
        card_cols = (CB, CY, CP, CG)
        for i, it in enumerate(items):
            k = fade(t, it["start"], 0.42)
            col = card_cols[i]
            x = cx + (i % 2) * (cw + gap)
            y = top + (i // 2) * (card_h + row_gap) + (1-k)*16
            chalk_box(d, [x, y, x+cw, y+card_h], 16, col, 3, alpha=k)
            chalk_accent(d, x+22, y+24, card_h-48, col, 7, k)
            title = it["show"]
            board = sc.get("board", [])
            body = board[it["beat"]] if it["beat"] < len(board) else it["say"]
            title_font = pf(34, 2)
            title_lines = wrap(d, title, title_font, cw-92)
            if len(title_lines) > 2:
                title_font = pf(29, 2)
                title_lines = wrap(d, title, title_font, cw-92)
            title_lines = title_lines[:2]
            for j, line in enumerate(title_lines):
                chalk_text(img, (x+54, y+22+j*35), line, title_font, col, k)
            body_y = y + 18 + len(title_lines)*35 + 6
            body_font = pf(22, 1)
            body_lines = wrap(d, body, body_font, cw-92)
            if len(body_lines) > 3:
                body_font = pf(19, 1)
                body_lines = wrap(d, body, body_font, cw-92)
            body_lines = body_lines[:3]
            for j, line in enumerate(body_lines):
                chalk_text(img, (x+54, body_y+j*26), line, body_font, CHALK, k)
        nxt = [it for i, it in enumerate(bs) if i == 4]
        if nxt:
            k = fade(t, nxt[0]["start"], 0.5)
            yy = top + 2*(card_h + row_gap) + 8 + (1-k)*18
            chalk_box(d, [CL, yy, CR, yy+132], 18, CY, 3, alpha=k)
            chalk_text(img, (CL+46, yy+36), "→", pf(42, 3), CY, k)
            chalk_text(img, (CL+116, yy+24), nxt[0]["show"], pf(42, 3), CHALK, k)
            board = sc.get("board", [])
            next_body = board[nxt[0]["beat"]] if nxt[0]["beat"] < len(board) else nxt[0]["say"]
            for j, line in enumerate(wrap(d, next_body, pf(21, 1), CR-CL-190)[:2]):
                chalk_text(img, (CL+116, yy+76+j*26), line, pf(21, 1), CHALK_D, k)

    bi = max(0, len(bs) - 1)
    draw_teacher(img, d, t, pointer_target(sc, bi))
    subtitle(d, t)
    chrome(d, t, si)
    return img

# ============================================================
#  main
# ============================================================
def main():
    global timeline, scene_starts, scene_dur, total
    print(f"== 1/4  合成中文旁白 (edge-tts / {VOICE} / {RATE}) ==", flush=True)
    items = []
    for si, sc in enumerate(SCENES):
        for bi, (say, show) in enumerate(sc["beats"]):
            stem = audio_stem(si, bi)
            items.append((say, os.path.join(MP3, f"{stem}.mp3"),
                          os.path.join(AUDIO_WORK, f"{stem}.wav")))
    durs = synth_all(items, reuse_audio="--reuse-audio" in sys.argv)
    t = HEAD
    k = 0
    for si, sc in enumerate(SCENES):
        scene_starts.append(t)
        for bi, (say, show) in enumerate(sc["beats"]):
            dd = durs[k]; k += 1
            caption = CAPTION_OVERRIDES.get((si, bi), say)
            timeline.append(dict(scene=si, beat=bi, start=t, dur=dd, say=say,
                                 caption=caption, show=show,
                                 wav=os.path.join(AUDIO_WORK, f"{audio_stem(si, bi)}.wav")))
            t += dd + GAP_BEAT
        t += GAP_SCENE
    total = t + TAIL
    for i in range(len(SCENES)):
        nxt = scene_starts[i+1] if i+1 < len(SCENES) else total
        scene_dur.append(nxt - scene_starts[i])
    speech = sum(it["dur"] for it in timeline)
    print(f"   beats={len(timeline)} speech={speech:.1f}s gaps={total-speech:.1f}s "
          f"total={total:.1f}s ({int(total//60)}:{int(total%60):02d})", flush=True)

    print("== 2/4  拼接音轨 ==", flush=True)
    parts, cursor = [], 0.0
    for item in timeline:
        if item["start"] - cursor > 0.01:
            sil = os.path.join(AUDIO_WORK, f"sil_{len(parts)}.wav")
            run(["ffmpeg","-y","-v","error","-f","lavfi","-i","anullsrc=r=44100:cl=mono",
                 "-t", f'{item["start"]-cursor:.3f}', "-c:a","pcm_s16le", sil])
            parts.append(sil)
        parts.append(item["wav"])
        cursor = item["start"] + item["dur"]
    sil = os.path.join(AUDIO_WORK, "sil_tail.wav")
    run(["ffmpeg","-y","-v","error","-f","lavfi","-i","anullsrc=r=44100:cl=mono",
         "-t", f"{total-cursor:.3f}", "-c:a","pcm_s16le", sil])
    parts.append(sil)
    with open(os.path.join(AUDIO_WORK, "concat_ch02.txt"), "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    AUDIO = os.path.join(AUDIO_WORK, "audio_ch02.wav")
    run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",
         os.path.join(AUDIO_WORK, "concat_ch02.txt"), "-c:a", "pcm_s16le", AUDIO])

    print("== 3/4  逐帧渲染 ==", flush=True)
    N = int(total*FPS)
    for f in os.listdir(FRAMES):
        if f.endswith(".png"):
            os.remove(os.path.join(FRAMES, f))
    import multiprocessing as mp
    try:
        ctx = mp.get_context("fork")
    except ValueError:
        ctx = None
    chunk = 25
    tasks = [(i, min(i+chunk, N)) for i in range(0, N, chunk)]
    if ctx is not None:
        with ctx.Pool(processes=8) as pool:
            done = 0
            for r in pool.imap_unordered(_worker, tasks):
                done += r
                if done % 500 < chunk:
                    print(f"   frame {done}/{N}", flush=True)
    else:
        for tk in tasks:
            _worker(tk)
    print(f"   rendered {N} frames", flush=True)

    print("== 4/4  合成 MP4 ==", flush=True)
    MP4 = os.path.join(OUT, f"{SLUG}.mp4")
    def has_encoder(name):
        out = subprocess.run(["ffmpeg","-hide_banner","-encoders"],
                             capture_output=True, text=True).stdout
        return name in out
    COLOR_TAGS = ["-color_range","tv","-colorspace","bt709",
                  "-color_primaries","bt709","-color_trc","bt709"]
    if has_encoder("libx264"):
        VENC = ["-c:v","libx264","-preset","medium","-crf","20"]
        VIN  = ["-pix_fmt","yuv420p"]
        VBSF = []
    else:
        VENC = ["-c:v","h264_videotoolbox","-b:v","12M","-allow_sw","1"]
        VIN  = ["-pix_fmt","nv12"]
        VBSF = ["-bsf:v","h264_metadata=colour_primaries=1:transfer_characteristics=1"
                          ":matrix_coefficients=1:video_full_range_flag=0"]
    print("   video encoder:", VENC[1], flush=True)
    run(["ffmpeg","-y","-v","error","-framerate",str(FPS),"-i",
         os.path.join(FRAMES,"%05d.png"),"-i",AUDIO] + VENC + VIN + VBSF + COLOR_TAGS +
        ["-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart", MP4])

    draw_frame(0.6).save(os.path.join(OUT, f"{SLUG}-poster.png"))
    draw_frame(total*0.34).save(os.path.join(OUT, f"{SLUG}-poster2.png"))

    with open(os.path.join(OUT, f"narration-ch{CONTENT_CHAPTER:02d}.txt"), "w") as f:
        for sc in SCENES:
            f.write(f"# {sc['kicker']}  {sc['title']}\n")
            for say, _ in sc["beats"]:
                f.write(say + "\n")
            f.write("\n")

    def ts(x):
        h=int(x//3600); m=int(x%3600//60); s=int(x%60); ms=int((x-int(x))*1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    with open(os.path.join(OUT, f"{SLUG}.srt"), "w") as f:
        for i, it in enumerate(timeline, 1):
            caption = it.get("caption", it["say"])
            f.write(f"{i}\n{ts(it['start'])} --> {ts(it['start']+it['dur'])}\n"
                    f"{caption}\n\n")

    json.dump(dict(chapter=CONTENT_CHAPTER, total=total, fps=FPS, voice=VOICE, rate=RATE, theme="teacher-blackboard",
                   scenes=[dict(id=s["id"], title=s["title"], kicker=s["kicker"]) for s in SCENES],
                   beats=[{k:v for k,v in it.items() if k != "wav"} for it in timeline]),
              open(os.path.join(OUT, f"{SLUG}-timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("done ->", MP4, f"({total:.1f}s)")

def _worker(args):
    i0, i1 = args
    for i in range(i0, i1):
        t = i / FPS
        # Hold the chapter title card through the opening narration, while
        # keeping the subtitle timed to the current spoken beat.
        if t < scene_starts[1]:
            img = draw_frame(0.6)
            if t >= HEAD:
                d = ImageDraw.Draw(img, "RGBA")
                d._image = img
                subtitle(d, t)
        else:
            img = draw_frame(t)
        img.save(os.path.join(FRAMES, f"{i:05d}.png"), compress_level=1)
    return i1 - i0

def fake_timeline(cps=5.2):
    """不需要配音的估算时间轴，用于出预览截图"""
    global timeline, scene_starts, scene_dur, total
    timeline, scene_starts, scene_dur = [], [], []
    t = HEAD
    for si, sc in enumerate(SCENES):
        scene_starts.append(t)
        for bi, (say, show) in enumerate(sc["beats"]):
            dd = max(1.3, len(say)/cps) + 0.12
            timeline.append(dict(scene=si, beat=bi, start=t, dur=dd, say=say, show=show, wav=""))
            t += dd + GAP_BEAT
        t += GAP_SCENE
    total = t + TAIL
    for i in range(len(SCENES)):
        nxt = scene_starts[i+1] if i+1 < len(SCENES) else total
        scene_dur.append(nxt - scene_starts[i])
    return total

def render_preview():
    fake_timeline()
    os.makedirs(SHOTS, exist_ok=True)
    for si, sc in enumerate(SCENES):
        its = [it for it in timeline if it["scene"] == si]
        it = its[-1]
        tt = it["start"] + it["dur"]*0.7
        safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in sc["id"])
        draw_frame(tt).save(os.path.join(SHOTS, f"v3-{si:02d}-{safe_id}.png"))
    draw_frame(0.6).save(os.path.join(SHOTS, "v3-00-cover.png"))
    draw_frame(HEAD + 0.5).save(os.path.join(SHOTS, "v3-00-cover-opening-caption.png"))
    print("preview ->", SHOTS)

if __name__ == "__main__":
    if "--chapter" in sys.argv:
        CONTENT_CHAPTER = int(sys.argv[sys.argv.index("--chapter") + 1])
    elif any(a.startswith("--chapter=") for a in sys.argv):
        CONTENT_CHAPTER = int(next(a.split("=", 1)[1] for a in sys.argv if a.startswith("--chapter=")))
    else:
        CONTENT_CHAPTER = 2
    if CONTENT_CHAPTER not in CHAPTERS:
        raise SystemExit(f"章号需为 2 到 15；收到 {CONTENT_CHAPTER}")
    SCENES = CHAPTERS[CONTENT_CHAPTER]["scenes"]
    CAPTION_OVERRIDES = CHAPTERS[CONTENT_CHAPTER].get("captions", {})
    CODE_BEAT_KEYS = {
        (si, bi)
        for si, sc in enumerate(SCENES)
        for bi, (say, _show) in enumerate(sc["beats"])
        if isinstance(say, str) and say.startswith("例如，这段代码展示了")
    }
    SLUG = f"python-ch{CONTENT_CHAPTER:02d}"
    FRAMES = os.path.join(WORK, f"frames_ch{CONTENT_CHAPTER:02d}")
    MP3 = os.path.join(WORK, f"mp3_ch{CONTENT_CHAPTER:02d}")
    AUDIO_WORK = os.path.join(WORK, f"audio_ch{CONTENT_CHAPTER:02d}")
    SHOTS = os.path.join(OUT, "preview", f"ch{CONTENT_CHAPTER:02d}")
    for d in (FRAMES, MP3, AUDIO_WORK, SHOTS):
        os.makedirs(d, exist_ok=True)
    SCENE_COL = [CB, CY, CP, CG] * ((len(SCENES) + 3) // 4)
    if "--preview" in sys.argv:
        render_preview()
    else:
        main()
