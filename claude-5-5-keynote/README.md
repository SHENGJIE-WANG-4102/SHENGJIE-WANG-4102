# Claude 5.5 家族 · Keynote 版

按 Zero Workflow 做的第三部片子：40 秒，16:9，60fps，中英双语。

参考了 zero（@twoclipping）的 Apple-keynote 一镜到底 prompt 和 Apple 发布会的画面惯例：暖白底、黑色 UI、一个镜头只有一个强调色，不切、不淡出，每一场都由上一场变出来。三个圆点变成 “5.5” 的小数点，小数点涨满全屏再收缩成 Opus 的标签点；Sonnet 的蓝色柱子变成黑色输入框，输入框再铺满全屏进入 Haiku；最后黑色收缩回三个点，落版。

**成片：[`claude-5-5-keynote.mp4`](claude-5-5-keynote.mp4)**（1920×1080，60fps，H.264 + AAC）

> 非官方致敬作品，与 Anthropic 无关联。

| 文件 | 说明 |
|---|---|
| `claude-5-5-keynote.mp4` | 成片 |
| `index.html` | 动画本体。每一帧都由 `seek(t)` 算出来，直接用浏览器打开就能播放（有配乐） |
| `music.m4a` | 配乐，网页播放时用 |
| `direction.md` | 第 1–6 步：参考、素材、视觉规则、Beat Map、实现方式、容易翻车的地方 |
| `storyboard/` | 第 7 步的关键帧和转场序列，`sheet.png` 是总览 |
| `frames.html`、`sheet.html` | 关键帧和总览页的源文件 |
| `fonts/` | 只含片中用到的字形的字体子集（Geist、Geist Mono、Noto Sans SC，均为 OFL） |
| `tools/` | 字体、配乐、渲染和出图脚本 |

## 自己重新渲染

需要 Node + Playwright（Chromium）、Python 3（numpy、scipy）和 ffmpeg。

```bash
python3 tools/fetch_fonts.py               # 改了画面文字后重新拉字体子集
python3 tools/music.py build/music.wav     # 合成配乐
node tools/render.mjs --out build/video.mp4                    # 逐帧渲染，60fps（可用 --from/--to 拆段并行）
node tools/render.mjs --stills 9.5,22.5 --out build/stills     # 只看几张静帧
ffmpeg -i build/video.mp4 -i build/music.wav -c:v copy -c:a aac -b:a 256k -shortest claude-5-5-keynote.mp4
```

在浏览器里看某一帧：`index.html?render=1&t=22.5`。

## 改内容

所有时间都以**拍**为单位（120 BPM，1 拍 = 0.5 秒）。`index.html` 里每个场景函数接收当前拍数 `b`，`ty(b, 进场拍, 退场拍)` 控制一行字什么时候从遮罩线升起、什么时候向上离开。`tools/music.py` 里的音效用的是同一套拍数，改了时间记得两边一起挪。
