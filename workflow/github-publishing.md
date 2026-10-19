# GitHub 发布

## 推荐结构

公开仓库放：

- 生成脚本。
- 内容数据。
- Codex skill。
- 制作清单。
- YouTube 标题和简介。
- 少量示例截图。

不要直接提交：

- 每章 100 MB 左右的 MP4。
- 整章逐帧 PNG。
- 原始 TTS 缓存。
- 未确认版权的课程素材。

## 大文件

视频适合放在：

- GitHub Release assets。
- 对象存储，如 S3、COS、R2。
- YouTube 本身。

GitHub Release 单文件有限制，普通仓库也不适合把多个大视频塞进 Git 历史。Release 或对象存储链接应写入 README 和 metadata。

## 推送

```bash
git init
git add .
git commit -m "Build reusable teacher-blackboard video pipeline"
git branch -M main
git remote add origin git@github.com:USER/REPO.git
# 若 22 端口被网络阻断，可改用：
# git remote add origin git@ssh.github.com:USER/REPO.git
git push -u origin main
```
