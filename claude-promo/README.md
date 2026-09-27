# Claude 前世今生 · The Story So Far

一部 91 秒的中英双语宣传短片，讲从图灵之问到 Claude 5 的这段历史：AI 发展背景 → Anthropic 创立 → Claude 各代模型 → 今天的产品。

**成片：[`claude-promo.mp4`](claude-promo.mp4)**（1920×1080，30fps，H.264 + AAC）

> 非官方致敬作品，与 Anthropic 没有关联。

## 文件

| 文件 | 说明 |
|---|---|
| `claude-promo.mp4` | 成片 |
| `index.html` | 动画本体。每一帧都由 `seek(t)` 决定，直接用浏览器打开就能播放（有配乐） |
| `music.m4a` | 配乐，网页播放时用 |
| `narration.srt` | 中英双语字幕，由 `index.html` 里的 `SUBS` 生成 |
| `script.md` | 旁白稿、分镜和片中所有事实的出处与日期 |
| `fonts/` | 只含片中用到的字形的字体子集（Noto Serif/Sans SC、Source Serif 4、Inter、JetBrains Mono，均为 OFL 协议） |
| `tools/` | 渲染用的脚本 |

## 自己重新渲染

需要 Node + Playwright（Chromium）、Python 3（numpy、scipy）和 ffmpeg。

```bash
# 1. 改了画面上的文字后，重新拉取字体子集
python3 tools/fetch_fonts.py

# 2. 合成配乐
python3 tools/music.py build/music.wav

# 3. 逐帧渲染画面（可以按时间段拆开并行跑）
node tools/render.mjs --out build/video.mp4
#   只看几张静帧：node tools/render.mjs --stills 10,40,88 --out build/stills

# 4. 合并音视频
ffmpeg -i build/video.mp4 -i build/music.wav -c:v copy -c:a aac -b:a 256k -shortest claude-promo.mp4

# 5. 字幕
python3 tools/make_srt.py > narration.srt
```

在浏览器里预览某一帧：`index.html?render=1&t=40`。

## 改内容

所有文案都在 `index.html` 的几张表里：`MILESTONES`（AI 历史）、`MODELS`（模型卡）、`PRODUCTS`（产品卡）和 `SUBS`（旁白字幕）。每段的时长由 `S1_T0/S1_STEP`、`S3_T0/S3_STEP`、`S4_T0` 控制。配乐的小节和转场是对齐的，改时长的话 `tools/music.py` 里的 `CHORDS` 要一起改。
