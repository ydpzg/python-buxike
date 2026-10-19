#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python for Everybody - 第 1 章 中文解说视频（历史脚本）
保留为第 1 章原始内容和首版生成流程的参考；新章节请使用 build_ch02.py。
"""
import json, os, subprocess, math, sys
from PIL import Image, ImageDraw, ImageFont

ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORK   = os.path.join(ROOT, "work", "video")
OUT    = os.path.join(ROOT, "outputs")
FRAMES = os.path.join(WORK, "frames")
for d in (WORK, FRAMES, OUT):
    os.makedirs(d, exist_ok=True)

W, H, FPS = 1920, 1080, 30
SLUG = "python-ch01"

# ---------- palette (python-ish, cool dark) ----------
INK    = (16, 19, 26)
INK2   = (23, 27, 36)
PANEL  = (25, 30, 40)
LINE   = (42, 49, 62)
CREAM  = (238, 241, 246)
DIM    = (176, 185, 199)
MUTED  = (132, 142, 158)
YEL    = (255, 199, 44)     # python yellow  -> primary accent
BLU    = (86, 156, 214)     # python blue
TEAL   = (77, 182, 172)
RED    = (233, 96, 82)
GRN    = (140, 200, 120)

# ---------- fonts ----------
def pf(size, weight=1):
    idx = {0: 11, 1: 2, 2: 5, 3: 8}[weight]   # light / regular / medium / semibold
    return ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", size, index=idx)
def mono(size):
    return ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", size)

F_TITLE  = pf(76, 3)
F_TITLE2 = pf(60, 3)
F_HUGE   = pf(112, 3)
F_QUOTE  = pf(72, 2)
F_LEAD   = pf(44, 2)
F_BODY   = pf(36, 1)
F_SUB    = pf(34, 1)
F_SMALL  = pf(28, 1)
F_TINY   = pf(24, 1)
F_KICK   = mono(24)
F_CODE   = mono(30)
F_CODE_S = mono(26)
F_NUM    = mono(34)
F_WM     = mono(300)

# ============================================================
#  narration script
# ============================================================
SCENES = [
 dict(id="cover", kicker="第 1 章", title="开始这段旅程", layout="cover",
      sub="Python for Everybody · 中文章节精讲",
      beats=[
        ("你好，欢迎来到这套 Python 快速入门课。这是第一章，开始这段旅程。",
         "第 1 章 · 开始这段旅程"),
        ("这一章我们不背语法，只回答三个问题：为什么值得学，电脑是什么，怎么跟它说话。",
         "为什么值得学 · 电脑是什么 · 怎么跟它说话"),
        ("看完这一章，你会对「编程」这件事，有一个完整的整体印象。",
         "先看全局，再抠细节"),
      ]),

 dict(id="why", kicker="01 / 为什么要学编程", title="电脑，是你请来的助手", layout="quote",
      beats=[
        ("我们身边的电脑，从笔记本到手机，本质上都是你的私人助手。",
         "电脑 = 你的私人助手"),
        ("它的硬件，一直在反复问你同一个问题。",
         "它一直在问你："),
        ("接下来，你想让我做什么？",
         "接下来，你想让我做什么？"),
        ("它算得飞快，记性极好，唯一的缺点是听不懂人话。",
         "快 · 记性好 · 听不懂人话"),
        ("人擅长创造，电脑擅长重复。学会它的语言，你就多了一个不知疲倦的搭档。",
         "人：创造      电脑：重复"),
      ]),

 dict(id="example", kicker="02 / 一个真实的例子", title="数一数，哪个词出现最多？", layout="code",
      beats=[
        ("请你数一数，这一章前三段里，出现最多的词是哪个，出现了几次？",
         "前三段里，出现最多的词是哪个？"),
        ("读一遍只要几秒，可真的动手去数，非常痛苦。",
         "人：读得快，数得痛苦"),
        ("对电脑来说刚好相反：读文本很难，数词却轻而易举。",
         "电脑：数词 = 轻而易举"),
        ("运行 words 点 py，输入文件名，它立刻回答：to，十六次。",
         "|$ python words.py|Enter file: words.txt|to 16"),
        ("这件人做起来很痛苦、电脑做起来很轻松的事，正是编程最值得的地方。",
         "把无聊的事，交给电脑"),
      ]),

 dict(id="hardware", kicker="03 / 电脑的构造", title="电脑里面有什么？", layout="hardware",
      beats=[
        ("要指挥一台电脑，先要认识它的五个主要部件。",
         "五个主要部件"),
        ("CPU，中央处理器。如果主频是三点零吉赫兹，它每秒会问三十亿次：接下来做什么？",
         "|CPU|中央处理器 · 每秒问 30 亿次「下一步？」"),
        ("主内存。它存放 CPU 急着要用的数据，速度几乎和 CPU 一样快，但一断电就清空。",
         "|主内存|快 · 断电即失"),
        ("二级存储，比如硬盘和 U 盘。它慢得多，但断电也不会丢，可以长期保存。",
         "|二级存储|慢 · 能长期保存"),
        ("输入输出设备，就是键盘、屏幕、鼠标和麦克风，它们是你和电脑对话的通道。",
         "|输入 / 输出设备|你和电脑对话的通道"),
      ]),

 dict(id="interp", kicker="04 / 两种翻译器", title="解释器 和 编译器", layout="duo",
      beats=[
        ("CPU 真正听得懂的，只有机器语言，也就是一堆零和一。",
         "CPU 只懂：0 和 1"),
        ("没人愿意直接写零和一，所以我们发明了翻译器，把高级语言翻译成机器码。",
         "于是，我们发明了翻译器"),
        ("解释器，一边读一边执行。Python 就是解释器，所以它可以和你实时对话。",
         "|解释器|一边读，一边执行|Python 就是这样"),
        ("编译器，先把整个程序翻译成机器码，再一次性运行。C 和 C++ 就是这样。",
         "|编译器|先全部翻译，再一次性运行|C / C++ 就是这样"),
      ]),

 dict(id="first", kicker="05 / 第一次对话", title="和 Python 说第一句话", layout="code",
      beats=[
        ("打开 Python，你会看到三个尖括号。那是它在问你：接下来想让我做什么？",
         ">>> 就是在问你：接下来做什么？"),
        ("说错了也没关系。把 print 拼成 primt，它会立刻报语法错误。",
         "|>>> primt 'Hello world!'|  SyntaxError: invalid syntax"),
        ("写对了，它就照做。输入 print 括号 Hello world，它就把这句话还给你。",
         "|>>> print('Hello world!')|Hello world!"),
        ("注意，Python 并不聪明。它只是在非常严格地，执行你写下的每一个字。",
         "Python 不聪明，只是很严格"),
      ]),

 dict(id="vars", kicker="06 / 变量", title="变量，就是给数据起个名字", layout="code",
      beats=[
        ("有些话是在告诉 Python：帮我把这个值记下来，以后还要用。",
         "让 Python 记住一个值"),
        ("我们给这个值起个名字，以后就能用这个名字把它取出来。这个名字，就叫变量。",
         "名字 = 变量"),
        ("比如写 x 等于 43，就是让 Python 记住 43，并贴上 x 这个标签。",
         "|>>> x = 43|记住 43，标签是 x"),
        ("然后写 x 等于 x 加 1。右边先算出 44，再存回左边的 x。",
         "|>>> x = x + 1|>>> print(x)|44"),
        ("这看起来像数学方程，其实不是。这是一条赋值语句：先算完，再存回去。",
         "不是方程，是赋值"),
      ]),

 dict(id="errors", kicker="07 / 三种错误", title="程序出错，只有三种", layout="errors",
      beats=[
        ("程序报错的时候，其实只有三种情况。认清它们，你就不会再慌。",
         "三种错误"),
        ("第一种，语法错误。你的句子不合 Python 的语法，它根本听不懂。",
         "语法错误 · 句子不合法"),
        ("第二种，逻辑错误。语法没问题，但顺序错了，就像先拧上瓶盖，再往里装水。",
         "逻辑错误 · 顺序不对"),
        ("第三种，语义错误。语法全对，顺序也对，但意思不是你想要的那个。",
         "语义错误 · 意思错了"),
        ("但请记住，无论哪一种，Python 都只是在尽全力，做你让它做的事。",
         "它只是在照你说的做"),
      ]),

 dict(id="journey", kicker="08 / 学习之旅", title="别急，慢慢来", layout="outro",
      beats=[
        ("第一次看不懂，太正常了。学母语的时候，你也先说了好几年咕噜声。",
         "看不懂，很正常"),
        ("所以别指望一次就懂。可以往前翻，也可以往后跳，读书要读得轻一点。",
         "往前翻 · 往后跳 · 读轻一点"),
        ("卡住的时候千万别熬夜。出去走走，睡一觉，再回来看，往往就通了。",
         "卡住 → 休息 → 再回来"),
        ("某一天，你会突然「啊哈」一下，所有碎片一下子串成一条线。",
         "「啊哈！」时刻"),
        ("这就是第一章。下一章，我们正式开始使用变量。",
         "下一章 · 变量"),
      ]),
]

VOICE = "Tingting"
RATE  = "180"
GAP_BEAT  = 0.34
GAP_SCENE = 1.00
TAIL      = 1.60
HEAD      = 0.80

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

def synth(text, path_aiff, path_wav):
    run(["say","-v",VOICE,"-r",RATE,"-o",path_aiff,text])
    run(["ffmpeg","-y","-v","error","-i",path_aiff,"-ar","44100","-ac","1",
         "-c:a","pcm_s16le",path_wav])
    return dur_of(path_wav)

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def ease(x):
    x = clamp(x)
    return 1 - (1-x)**3

def fade(t, start, dur=0.55):
    return ease((t-start)/dur)

def text_at(d, xy, s, font, fill, alpha=1.0, anchor="la"):
    if alpha <= 0.012 or not s:
        return
    a = int(255*clamp(alpha))
    d.text(xy, s, font=font, fill=(fill[0], fill[1], fill[2], a), anchor=anchor)

def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if d.textlength(cur+ch, font=font) > maxw and cur:
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines

def rrect(d, box, r, **kw):
    d.rounded_rectangle(box, radius=r, **kw)

# ============================================================
#  render
# ============================================================
timeline, scene_starts, total = [], [], 1.0

def scene_of(t):
    cur = None
    for i, s in enumerate(scene_starts):
        if t >= s - 0.45:
            cur = i
    return cur

def beats_in(t, si):
    return [it for it in timeline if it["scene"] == si and t >= it["start"]]

def grid(d):
    for x in range(0, W, 80):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 5))
    for y in range(0, H, 80):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 5))

def code_panel(d, x, y, w, lines, k, tag="terminal", h=None):
    """terminal-style code block; returns its height"""
    lh, pad = 52, 26
    body = pad + len(lines)*lh + pad - 12
    hh = 46
    total_h = hh + body if h is None else h
    rrect(d, [x, y, x+w, y+total_h], 14, fill=PANEL, outline=LINE, width=2)
    d.rounded_rectangle([x, y, x+w, y+hh+14], radius=14, fill=(33, 39, 51))
    d.rectangle([x, y+hh, x+w, y+hh+2], fill=LINE)
    for i, c in enumerate([RED, YEL, GRN]):
        d.ellipse([x+22+i*26, y+17, x+22+i*26+13, y+30], fill=c)
    text_at(d, (x+108, y+13), tag, F_TINY, MUTED, k)
    yy = y + hh + pad
    for i, ln in enumerate(lines):
        kk = fade_beat_line(k, i)
        if ln.startswith(">>>") or ln.startswith("$"):
            text_at(d, (x+pad, yy), ln[:3], F_CODE, BLU, kk)
            text_at(d, (x+pad+int(d.textlength("   ", font=F_CODE)), yy), ln[3:].strip(), F_CODE, CREAM, kk)
        elif "Error" in ln or "error" in ln:
            text_at(d, (x+pad, yy), ln, F_CODE_S, RED, kk)
        elif ln.startswith("  "):
            text_at(d, (x+pad, yy), ln.strip(), F_CODE_S, RED, kk)
        else:
            text_at(d, (x+pad, yy), ln, F_CODE_S if len(ln) > 34 else F_CODE, GRN if i else CREAM, kk)
        yy += lh
    return total_h

def fade_beat_line(k, i):
    # k in 0..1 : reveal lines progressively
    return clamp((k - i*0.14) / 0.55)

def subtitle(d, t):
    cur = None
    for it in timeline:
        if it["start"] - 0.18 <= t < it["start"] + it["dur"] + 0.34:
            cur = it
    if cur is None:
        return
    a = min(fade(t, cur["start"]-0.18, 0.30), 1 - fade(t, cur["start"]+cur["dur"]+0.10, 0.24))
    lines = wrap(d, cur["say"], F_SUB, 1500)
    if len(lines) > 2:
        lines = lines[:2]
    bh = 34 + len(lines)*50
    y2 = H - 104
    y1 = y2 - bh
    box = [W/2 - 830, y1, W/2 + 830, y2]
    ov = Image.new("RGBA", (int(box[2]-box[0]), int(y2-y1)), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle([0, 0, ov.width-1, ov.height-1], radius=16, fill=(9, 11, 16, 208))
    # clip alpha by a
    ov.putalpha(ov.getchannel("A").point(lambda v: int(v*a)))
    d._image.paste(ov, (int(box[0]), int(y1)), ov)
    yy = y1 + 14
    for ln in lines:
        text_at(d, (W/2, yy), ln, F_SUB, CREAM, a, anchor="ma")
        yy += 50

def chrome(d, t, si):
    text_at(d, (96, 54), "PYTHON 入门 · 第 1 章", F_KICK, MUTED, 0.9)
    if si is not None:
        text_at(d, (W-96, 54), SCENES[si]["kicker"], F_KICK, YEL, 0.95, anchor="ra")
    p = clamp(t/total)
    d.rectangle([0, H-5, W, H], fill=LINE)
    d.rectangle([0, H-5, int(W*p), H], fill=YEL)
    mm, ss = int(t)//60, int(t) % 60
    tm, ts = int(total)//60, int(total) % 60
    text_at(d, (96, H-58), f"{mm:02d}:{ss:02d} / {tm:02d}:{ts:02d}", mono(22), MUTED, 0.75)
    text_at(d, (W-96, H-58), "共 15 章 · 第 1 章", mono(22), MUTED, 0.6, anchor="ra")

def scene_header(d, sc, t, si, lines=1):
    a = fade(t, scene_starts[si]-0.15, 0.7)
    y = 148 + (1-a)*20
    for i, ln in enumerate(sc["title"].split("\n")):
        text_at(d, (96, y + i*92), ln, F_TITLE, CREAM, a)
    ry = y + lines*92 + 20
    d.rectangle([96, ry, 96+int(130*a), ry+5], fill=YEL)
    return ry

def draw_frame(t):
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img, "RGBA")
    d._image = img
    grid(d)
    si = scene_of(t)
    if si is None:
        chrome(d, t, None)
        return img
    sc = SCENES[si]
    bs = beats_in(t, si)
    lay = sc["layout"]

    # ---------------- cover ----------------
    if lay == "cover":
        a = fade(t, 0.10, 0.9)
        wm = fade(t, 0.30, 1.2)
        text_at(d, (W-100, H/2-40), "01", F_WM, (30, 35, 47), wm, anchor="rm")
        yy = 300 + (1-a)*24
        text_at(d, (100, yy-96), "PYTHON FOR EVERYBODY · 中文章节精讲", F_KICK, BLU, a*0.95)
        text_at(d, (100, yy), sc["title"], F_HUGE, CREAM, a)
        d.rectangle([100, yy+150, 100+int(190*a), yy+158], fill=YEL)
        y = yy + 230
        for it in bs:
            k = fade(t, it["start"], 0.55)
            d.rectangle([100, y+16, 108, y+24], fill=YEL)
            text_at(d, (132, y), it["show"], F_LEAD, DIM, k)
            y += 78

    # ---------------- quote ----------------
    elif lay == "quote":
        ry = scene_header(d, sc, t, si)
        caps = [it for i, it in enumerate(bs) if i == 0]
        if caps:
            k = fade(t, caps[0]["start"], 0.5)
            text_at(d, (100, ry+54), caps[0]["show"], F_SMALL, MUTED, k)
        q = [it for i, it in enumerate(bs) if i == 2]
        if q:
            k = fade(t, q[0]["start"], 0.6)
            qx, qy = 100, ry + 150 + (1-k)*22
            d.rectangle([qx, qy-8, qx+7, qy+150], fill=YEL if k > 0.02 else LINE)
            text_at(d, (qx+40, qy), q[0]["show"], F_QUOTE, CREAM, k)
            text_at(d, (qx+40, qy+104), "— 电脑硬件问你的唯一一句话", F_TINY, MUTED, k*0.8)
        cards = [it for i, it in enumerate(bs) if i in (3, 4)]
        cx, cy, cw, ch, g = 100, ry+372, 800, 132, 40
        for i, it in enumerate(cards):
            k = fade(t, it["start"], 0.55)
            x = cx + i*(cw+g)
            yy = cy + (1-k)*22
            col = BLU if i == 0 else YEL
            rrect(d, [x, yy, x+cw, yy+ch], 14, fill=(255, 255, 255, 9), outline=LINE, width=2)
            d.rectangle([x, yy, x+6, yy+ch], fill=col)
            text_at(d, (x+34, yy+ch/2), it["show"], F_LEAD, CREAM, k, anchor="lm")

    # ---------------- code (left narration + right terminal) ----------------
    elif lay == "code":
        ry = scene_header(d, sc, t, si)
        y = ry + 66
        for it in bs:
            if it["show"].startswith("|"):
                continue
            k = fade(t, it["start"], 0.5)
            if y > 840:
                break
            d.rectangle([100, y+14, 106, y+20], fill=YEL)
            for j, ln in enumerate(wrap(d, it["show"], F_BODY, 720)):
                text_at(d, (132, y + j*48), ln, F_BODY, CREAM, k)
            y += 48*len(wrap(d, it["show"], F_BODY, 720)) + 30
        blocks = [it for it in bs if it["show"].startswith("|")]
        by = ry + 66
        for it in blocks:
            k = fade(t, it["start"], 0.5)
            lines = it["show"].split("|")[1:]
            hh = code_panel(d, 1000, by, 820, lines, k)
            by += hh + 34

    # ---------------- hardware ----------------
    elif lay == "hardware":
        ry = scene_header(d, sc, t, si)
        if bs:
            k = fade(t, bs[0]["start"], 0.5)
            text_at(d, (100, ry+54), bs[0]["show"], F_SMALL, MUTED, k)
        nodes = [it for i, it in enumerate(bs) if i >= 1]
        boxes = [(100, 560), (760, 500), (1300, 520)]
        top = ry + 128
        for i, it in enumerate(nodes[:3]):
            k = fade(t, it["start"], 0.55)
            x, w = boxes[i]
            yy = top + (1-k)*24
            col = [YEL, BLU, TEAL][i]
            rrect(d, [x, yy, x+w, yy+210], 16, fill=(255, 255, 255, 9), outline=LINE, width=2)
            d.rectangle([x, yy, x+w, yy+6], fill=col)
            parts = it["show"].split("|")[1:]
            text_at(d, (x+30, yy+44), parts[0], pf(46, 3), col, k)
            if len(parts) > 1:
                for j, ln in enumerate(wrap(d, parts[1], F_SMALL, w-60)):
                    text_at(d, (x+30, yy+118+j*42), ln, F_SMALL, DIM, k)
        if len(nodes) > 3:
            it = nodes[3]
            k = fade(t, it["start"], 0.55)
            yy = top + 250 + (1-k)*24
            rrect(d, [100, yy, W-100, yy+168], 16, fill=(255, 255, 255, 9), outline=LINE, width=2)
            d.rectangle([100, yy, W-100, yy+6], fill=RED)
            parts = it["show"].split("|")[1:]
            text_at(d, (130, yy+40), parts[0], pf(46, 3), CREAM, k)
            if len(parts) > 1:
                text_at(d, (130, yy+112), parts[1], F_SMALL, DIM, k)

    # ---------------- duo ----------------
    elif lay == "duo":
        ry = scene_header(d, sc, t, si)
        caps = [it for i, it in enumerate(bs) if i < 2]
        y = ry + 56
        for it in caps:
            k = fade(t, it["start"], 0.5)
            d.rectangle([100, y+14, 106, y+20], fill=YEL)
            text_at(d, (132, y), it["show"], F_BODY, CREAM, k)
            y += 66
        cols = [it for i, it in enumerate(bs) if i >= 2]
        cx, cw, g = 100, 800, 40
        cy = y + 30
        ch = 300
        for i, it in enumerate(cols):
            k = fade(t, it["start"], 0.6)
            x = cx + i*(cw+g)
            yy = cy + (1-k)*26
            col = BLU if i == 0 else YEL
            rrect(d, [x, yy, x+cw, yy+ch], 18, fill=(255, 255, 255, 9), outline=LINE, width=2)
            d.rectangle([x, yy, x+cw, yy+7], fill=col)
            parts = it["show"].split("|")[1:]
            text_at(d, (x+40, yy+52), parts[0], pf(56, 3), col, k)
            if len(parts) > 1:
                text_at(d, (x+40, yy+146), parts[1], F_LEAD, CREAM, k)
            if len(parts) > 2:
                text_at(d, (x+40, yy+222), parts[2], F_SMALL, MUTED, k)

    # ---------------- errors ----------------
    elif lay == "errors":
        ry = scene_header(d, sc, t, si)
        if bs:
            k = fade(t, bs[0]["start"], 0.5)
            text_at(d, (100, ry+54), bs[0]["show"], F_SMALL, MUTED, k)
        rows = [it for i, it in enumerate(bs) if 1 <= i <= 3]
        y = ry + 132
        cols = [YEL, BLU, TEAL]
        for i, it in enumerate(rows):
            k = fade(t, it["start"], 0.55)
            yy = y + (1-k)*22
            rrect(d, [100, yy, W-100, yy+124], 14, fill=(255, 255, 255, 8), outline=LINE, width=2)
            d.rectangle([100, yy, 107, yy+124], fill=cols[i])
            text_at(d, (150, yy+62), f"0{i+1}", mono(40), cols[i], k, anchor="lm")
            text_at(d, (250, yy+62), it["show"], pf(50, 3), CREAM, k, anchor="lm")
            y += 148
        last = [it for i, it in enumerate(bs) if i == 4]
        if last:
            k = fade(t, last[0]["start"], 0.6)
            yy = y + 6
            text_at(d, (100, yy), last[0]["show"], pf(52, 3), YEL, k)

    # ---------------- outro ----------------
    elif lay == "outro":
        ry = scene_header(d, sc, t, si)
        items = [it for i, it in enumerate(bs) if i <= 3]
        cx, cw, gap = 100, 560, 40
        top, card_h, row_gap = ry + 64, 154, 24
        card_cols = (BLU, YEL, RED, TEAL)
        for i, it in enumerate(items):
            k = fade(t, it["start"], 0.5)
            col = card_cols[i]
            x = cx + (i % 2) * (cw + gap)
            y = top + (i // 2) * (card_h + row_gap) + (1-k)*18
            rrect(d, [x, y, x+cw, y+card_h], 16, fill=(255, 255, 255, 8), outline=col, width=2)
            d.rectangle([x, y, x+7, y+card_h], fill=col)
            title_font = pf(34, 2)
            title_lines = wrap(d, it["show"], title_font, cw-74)
            if len(title_lines) > 2:
                title_font = pf(29, 2)
                title_lines = wrap(d, it["show"], title_font, cw-74)
            title_lines = title_lines[:2]
            for j, line in enumerate(title_lines):
                text_at(d, (x+34, y+18+j*35), line, title_font, col, k)
            body_y = y + 16 + len(title_lines)*35 + 6
            body_font = pf(22, 1)
            body_lines = wrap(d, it["say"], body_font, cw-74)
            if len(body_lines) > 3:
                body_font = pf(19, 1)
                body_lines = wrap(d, it["say"], body_font, cw-74)
            for j, line in enumerate(body_lines[:3]):
                text_at(d, (x+34, body_y+j*26), line, body_font, CREAM, k)
        nxt = [it for i, it in enumerate(bs) if i == 4]
        if nxt:
            k = fade(t, nxt[0]["start"], 0.6)
            yy = top + 2*(card_h + row_gap) + 8 + (1-k)*20
            rrect(d, [100, yy, W-100, yy+132], 16, fill=(255, 255, 255, 10), outline=YEL, width=2)
            text_at(d, (140, yy+34), "→", pf(44, 3), YEL, k)
            text_at(d, (204, yy+22), nxt[0]["show"], pf(42, 3), CREAM, k)
            for j, line in enumerate(wrap(d, nxt[0]["say"], pf(21, 1), W-350)[:2]):
                text_at(d, (204, yy+76+j*26), line, pf(21, 1), DIM, k)

    subtitle(d, t)
    chrome(d, t, si)
    return img

# ============================================================
#  main
# ============================================================
def main():
    global timeline, scene_starts, total
    print("== 1/4  合成中文旁白 (macOS say / Tingting) ==", flush=True)
    t = HEAD
    for si, sc in enumerate(SCENES):
        scene_starts.append(t)
        for bi, (say, show) in enumerate(sc["beats"]):
            a = os.path.join(WORK, f"s{si}_b{bi}.aiff")
            w = os.path.join(WORK, f"s{si}_b{bi}.wav")
            d = synth(say, a, w)
            timeline.append(dict(scene=si, beat=bi, start=t, dur=d, say=say, show=show, wav=w))
            t += d + GAP_BEAT
        t += GAP_SCENE
    total = t + TAIL
    print(f"   beats={len(timeline)}  total={total:.1f}s ({int(total//60)}:{int(total%60):02d})", flush=True)

    print("== 2/4  拼接音轨 ==", flush=True)
    parts, cursor = [], 0.0
    for item in timeline:
        if item["start"] - cursor > 0.01:
            sil = os.path.join(WORK, f"sil_{len(parts)}.wav")
            run(["ffmpeg","-y","-v","error","-f","lavfi","-i","anullsrc=r=44100:cl=mono",
                 "-t", f'{item["start"]-cursor:.3f}', "-c:a","pcm_s16le", sil])
            parts.append(sil)
        parts.append(item["wav"])
        cursor = item["start"] + item["dur"]
    sil = os.path.join(WORK, "sil_tail.wav")
    run(["ffmpeg","-y","-v","error","-f","lavfi","-i","anullsrc=r=44100:cl=mono",
         "-t", f"{total-cursor:.3f}", "-c:a","pcm_s16le", sil])
    parts.append(sil)
    with open(os.path.join(WORK, "concat.txt"), "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    AUDIO = os.path.join(WORK, "audio.wav")
    run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",
         os.path.join(WORK, "concat.txt"), "-c:a", "pcm_s16le", AUDIO])

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
                if done % 250 < chunk:
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

    # NOTE: /usr/local/bin/ffmpeg 7.1.1 (--disable-x86asm) has a BROKEN
    # swscale RGB24->yuv420p path (magenta bg / green text). Use nv12 with
    # VideoToolbox; tag VUI via h264_metadata bsf.
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

    draw_frame(0.4).save(os.path.join(OUT, f"{SLUG}-poster.png"))
    draw_frame(total*0.34).save(os.path.join(OUT, f"{SLUG}-poster2.png"))

    with open(os.path.join(OUT, "narration.txt"), "w") as f:
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
            f.write(f"{i}\n{ts(it['start'])} --> {ts(it['start']+it['dur'])}\n{it['say']}\n\n")

    json.dump(dict(chapter=1, total=total, fps=FPS, voice=VOICE, rate=RATE,
                   scenes=[dict(id=s["id"], title=s["title"], kicker=s["kicker"]) for s in SCENES],
                   beats=[{k:v for k,v in it.items() if k != "wav"} for it in timeline]),
              open(os.path.join(OUT, f"{SLUG}-timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("done ->", MP4, f"({total:.1f}s)")

def _worker(args):
    i0, i1 = args
    for i in range(i0, i1):
        draw_frame(i/FPS).save(os.path.join(FRAMES, f"{i:05d}.png"), compress_level=1)
    return i1 - i0

if __name__ == "__main__":
    main()
