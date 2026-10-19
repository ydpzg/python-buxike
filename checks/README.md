# 输出检查

`scripts/check_outputs.py` 用来检查成片目录。默认检查第 1–15 章的 MP4、SRT 和 timeline。

```bash
python scripts/check_outputs.py --output-dir outputs --min-seconds 180 --max-seconds 420
```

如果只有第 3–15 章，可将输出目录指向对应目录。练习页和回顾页需要由内容数据提供；第 1、2 章使用各自的历史内容格式，检查器会报告这两章缺少统一 practice 场景。
