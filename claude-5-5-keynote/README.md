# Claude 5.5 家族 · Keynote 版（关键帧 v0）

按 Zero Workflow 做的第三部片子。这一版目前只做到第 7 步（Storyboard）：先出关键帧，确认后再做完整视频。

参考了 zero（@twoclipping）的 Apple-keynote 一镜到底 prompt 和 Apple 发布会的画面惯例：暖白底、黑色 UI、一个镜头只有一个强调色，不切、不淡出，每一场都由上一场变出来。

> 非官方致敬作品，与 Anthropic 无关联。

| 文件 | 说明 |
|---|---|
| `direction.md` | 第 1–6 步：参考、素材、视觉规则、Beat Map、实现方式、容易翻车的地方 |
| `storyboard/sheet.png` | 总览：Beat Map、9 个关键帧、2 条转场序列 |
| `storyboard/kf*.png` | 9 张 1920×1080 单帧 |
| `frames.html` | 关键帧本体，`frames.html?f=chart` 或 `?f=morphA&p=0.5` 可以直接在浏览器里看 |
| `sheet.html` | 总览页 |
| `tools/` | 字体子集（`fetch_fonts.py`）和出图脚本（`stills.mjs`） |

```bash
python3 tools/fetch_fonts.py        # 改了文字以后重新拉字体子集
node tools/stills.mjs               # 渲染关键帧和转场
node tools/stills.mjs --sheet       # 渲染总览图
```
