# Python 补习课｜从零开始学 Python

这里是「Python 补习课」的完整视频创造代码。它用 Python 和 PIL 生成老师站在黑板前讲解的中文教学视频：旁白、字幕、板书、代码终端、练习题和章节回顾都由同一份内容数据生成。

本仓库包含第 1–15 章的课程标题、分章封面、章节内容、字幕与时间轴生成流程，以及可复用的 Codex skill。


## 第 1–15 章封面

以下封面直接从各章成片首屏抽取，展示章节号、章节名和老师。

| 章节 | 章节 |
|---|---|
| <strong>第 01 章</strong><br><sub>开始这段旅程</sub><br><img src="assets/covers/ch01.png" width="560" alt="第 01 章 开始这段旅程封面"> | <strong>第 02 章</strong><br><sub>变量、表达式与语句</sub><br><img src="assets/covers/ch02.png" width="560" alt="第 02 章 变量、表达式与语句封面"> |
| <strong>第 03 章</strong><br><sub>条件判断</sub><br><img src="assets/covers/ch03.png" width="560" alt="第 03 章 条件判断封面"> | <strong>第 04 章</strong><br><sub>函数</sub><br><img src="assets/covers/ch04.png" width="560" alt="第 04 章 函数封面"> |
| <strong>第 05 章</strong><br><sub>循环与迭代</sub><br><img src="assets/covers/ch05.png" width="560" alt="第 05 章 循环与迭代封面"> | <strong>第 06 章</strong><br><sub>字符串</sub><br><img src="assets/covers/ch06.png" width="560" alt="第 06 章 字符串封面"> |
| <strong>第 07 章</strong><br><sub>文件</sub><br><img src="assets/covers/ch07.png" width="560" alt="第 07 章 文件封面"> | <strong>第 08 章</strong><br><sub>列表</sub><br><img src="assets/covers/ch08.png" width="560" alt="第 08 章 列表封面"> |
| <strong>第 09 章</strong><br><sub>字典</sub><br><img src="assets/covers/ch09.png" width="560" alt="第 09 章 字典封面"> | <strong>第 10 章</strong><br><sub>元组</sub><br><img src="assets/covers/ch10.png" width="560" alt="第 10 章 元组封面"> |
| <strong>第 11 章</strong><br><sub>正则表达式</sub><br><img src="assets/covers/ch11.png" width="560" alt="第 11 章 正则表达式封面"> | <strong>第 12 章</strong><br><sub>网络程序</sub><br><img src="assets/covers/ch12.png" width="560" alt="第 12 章 网络程序封面"> |
| <strong>第 13 章</strong><br><sub>Python 与 Web 服务</sub><br><img src="assets/covers/ch13.png" width="560" alt="第 13 章 Python 与 Web 服务封面"> | <strong>第 14 章</strong><br><sub>对象与类</sub><br><img src="assets/covers/ch14.png" width="560" alt="第 14 章 对象与类封面"> |
| <strong>第 15 章</strong><br><sub>Python 与数据库</sub><br><img src="assets/covers/ch15.png" width="560" alt="第 15 章 Python 与数据库封面"> | &nbsp; |

## 已完成的成片

第 1–15 章视频，合计约 61 分钟。每章包含 MP4、SRT、timeline 和封面图；时长、文件大小见 [checks/video-manifest.json](checks/video-manifest.json)。

- 第 1 章：3:33
- 第 2 章：4:38
- 第 3–15 章：3:35–4:39
- 字幕原始代码标记：0
- 第 3–15 章：每章 12 个场景、49 个 beat、独立练习页和具体回顾页

## 这套工程解决什么

- 用一份 `(旁白, 板书)` 数据同时驱动 TTS、字幕、黑板和老师教鞭。
- 章节首屏保持“章节号 + 标题 + 老师”到开场旁白结束，字幕从第一句开始。
- 代码保留缩进，超长行自动缩小字号，不越出黑板。
- 练习题单独成页，板书展示题目、流程、左右代码面板和验收标准。
- 片尾回顾显示本章具体概念、验证边界、练习名和下一章。
- 时间轴 JSON、SRT 与 MP4 同一次生成，便于后续剪辑和上传。
- 提供字幕与布局检查脚本，先拦截原始代码管道符、过长视频和缺失文件。

## 快速开始

### 依赖

- Python 3.11+
- Pillow
- edge-tts
- ffmpeg 与 ffprobe
- macOS 字体：PingFang 和 SF Mono

安装 Python 依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 配置路径

`scripts/build_course_video.py` 默认读取同目录的 `content/`。如果你的目录结构不同，修改脚本顶部的 `ROOT`：

```python
ROOT = "/path/to/python-buxike"
```

### 生成一章

```bash
python scripts/build_course_video.py --chapter 12 --reuse-audio
```

第一次生成会调用 edge-tts 合成缺失音频。修改旁白后，如需重新配音，请更换缓存名或删除对应的 `work/mp3_chXX/` 缓存。

只生成用于审阅的静帧：

```bash
python scripts/build_course_video.py --chapter 12 --preview
```

输出：

```text
outputs/python-ch12.mp4
outputs/python-ch12.srt
outputs/python-ch12-timeline.json
outputs/python-ch12-poster.png
outputs/narration-ch12.txt
```

## 内容格式

每一章由 `content/remaining_chapters.py` 中的 `CHAPTERS` 提供。`content/chapter2_content.py` 是第 2 章的独立内容文件。

核心结构：

```python
_scene(
    "03 / urllib 与网页",
    "用库处理网络细节",
    "code",
    [
        ("Python 的 urllib 可以发起网页请求、读取响应内容。", "urllib.request 获取网页"),
        ("读取后按正确编码解析。", "文字编码 · 二进制内容"),
        ("|from urllib.request import urlopen|data = response.read()", "读取响应"),
        ("下载前要遵守网站规则。", "访问频率 · 使用规则"),
    ],
)
```

每个 beat 的第一个值是旁白，第二个值是板书。以 `|` 开头的板书是代码，`|` 只负责分隔黑板行，不应进入旁白或 SRT。

## 制作规范

### 画面

- 首屏必须是带章节号、章节名和老师的封面黑板。
- 标题画面至少持续到开场旁白结束，再进入正文。
- 字幕从开场旁白开始，不能空白。
- 老师人物位于右侧，教鞭指向当前讲解区域。
- 正文保留概念、关系和例子；黑板上不能只有标题。

### 旁白与字幕

- 旁白先解释概念，再说明例子和结果。
- 字幕读的是解释，不是代码标点。
- 中英文和数字之间保留空格。
- CPU 主频写作 `3.0 GHz` 或“三点零吉赫兹”，不能写“三点零吉”。
- 中文句末问号直接跟在句子后；不要为了换行另起一个 `?`。
- 代码块的 `|` 不能出现在 SRT。

### 练习题

练习页必须包含：

1. 题目。
2. 解决流程。
3. 左右两个代码面板。
4. 可执行的验收标准。

练习标题要与片尾回顾一致，并出现在板书上。

### 片尾

片尾不要只写“把概念变成程序”或“本章关键概念”。应列出：

- 本章具体概念和关系。
- 验证边界。
- 本章练习名。
- 下一章主题。

### 时长

入门章节建议 3–5 分钟。每章至少包含：

- 1 个封面。
- 4 个核心知识场景。
- 5–6 个扩展场景。
- 1 个完整练习页。
- 1 个具体回顾页。

若成片只有 1 分多钟，检查扩展场景是否被 `EXTENDED_SCENES` 合并、音频是否错误复用，以及 `SCENES` 是否缺少场景。

## 检查

运行仓库检查：

```bash
python scripts/check_outputs.py --output-dir outputs --min-seconds 180
```

检查内容包括：

- MP4、SRT、timeline 是否齐全。
- 每章时长是否达到下限。
- SRT 是否出现 `|`、连续问号或异常换行。
- timeline 的 `show` 与 `say` 是否都有效。
- 每章是否包含练习页和回顾页。

## 可复用 Codex skill

[skills/teacher-blackboard-video/SKILL.md](skills/teacher-blackboard-video/SKILL.md) 记录了下一套视频的完整工作流和验收清单。把 `skills/` 下的目录安装到 Codex 技能目录后，可以让下一个视频任务直接复用这些规则。

直接启动下一个视频时，使用 [workflow/next-video-prompt.md](workflow/next-video-prompt.md) 中的提示词。

## 目录

```text
scripts/        视频生成器与输出检查器
content/        第 2–15 章内容与共享章节数据
skills/         可复用 Codex skill
workflow/       制作流程、审查清单、问题记录
metadata/       YouTube 播放列表、标题和简介
assets/         封面、练习页、片尾示例
checks/         本仓库输出检查结果
```

## 经验

详见 [workflow/lessons-learned.md](workflow/lessons-learned.md)。最重要的几条：

- 一份数据驱动所有输出，避免旁白和板书各写一套。
- 先做预览页，再渲染整章；一页布局错误会放大成数千帧。
- 音频缓存要和文案版本绑定，否则旧旁白会被复用。
- 把代码和解释分开存，避免 TTS 读管道符。
- 每章都要有可检查的练习和具体回顾，不能只靠通用片尾。
- 成片验收看字幕、静帧、时长，不只确认“命令成功”。

## 许可证

代码使用 MIT License。课程文案、品牌和视频素材的使用权由项目所有者负责确认。

## 视频归档

仓库只保存可复用的生成代码和文档。15 章成片、SRT 和 timeline 保留在本地交付目录：

`python-chapters-01-15/`

大文件建议发布到 GitHub Release 或对象存储，不要直接提交到普通 Git 历史。
