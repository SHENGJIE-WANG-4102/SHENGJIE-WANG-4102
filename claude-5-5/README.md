# Claude 5.5 家族 · The Family

一部 75 秒的中英双语介绍短片，讲 Claude 5.5 家族的三个成员：Opus 5.5、Sonnet 5.5，以及即将推出的 Haiku 5.5。

风格和 [`../claude-promo`](../claude-promo) 那部《前世今生》刻意反着来：浅色底、大字、纯色块，每个镜头都卡在 128 BPM 的拍子上硬切。每个模型有自己的颜色，用一个圆放大成满屏来转场。

**成片：[`claude-5-5.mp4`](claude-5-5.mp4)**（1920×1080，30fps，H.264 + AAC）

> 非官方致敬作品，与 Anthropic 没有关联。

## 文件

| 文件 | 说明 |
|---|---|
| `claude-5-5.mp4` | 成片 |
| `index.html` | 动画本体。每一帧都由 `seek(t)` 决定，直接用浏览器打开就能播放（有配乐） |
| `music.m4a` | 配乐，网页播放时用 |
| `script.md` | 分镜，以及片中每个数字的出处 |
| `fonts/` | 只含片中用到的字形的字体子集（Inter Tight、Noto Sans SC、JetBrains Mono，均为 OFL） |
| `tools/` | 字体、配乐和渲染脚本 |

## 自己重新渲染

需要 Node + Playwright（Chromium）、Python 3（numpy、scipy）和 ffmpeg。

```bash
python3 tools/fetch_fonts.py               # 改了画面文字后重新拉字体子集
python3 tools/music.py build/music.wav     # 合成配乐
node tools/render.mjs --out build/video.mp4                    # 逐帧渲染（可用 --from/--to 拆段并行）
node tools/render.mjs --stills 10,20,40 --out build/stills     # 只看几张静帧
ffmpeg -i build/video.mp4 -i build/music.wav -c:v copy -c:a aac -b:a 256k -shortest claude-5-5.mp4
```

在浏览器里预览某一帧：`index.html?render=1&t=40`。

## 改内容

文案直接写在 `index.html` 的各个 `<section class="scene">` 里。每个元素的出场时间是 `data-in`，单位是**拍**（1 拍 = 60/128 秒），动效由 `data-fx` 决定（`rise`、`slam`、`pop`、`count`、`type` 等）。`tools/music.py` 里的音效用的是同一套拍数，改了出场时间记得把对应的音效一起挪。
