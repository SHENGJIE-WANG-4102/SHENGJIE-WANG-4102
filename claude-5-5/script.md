# Claude 5.5 家族 · 分镜与数据

时长 75 秒 · 1920×1080 · 30fps · 128 BPM（1 拍 = 0.469 秒，1 小节 = 1.875 秒，共 40 小节）

这一版没有旁白字幕：画面上的大字就是旁白，每一句都跟着节拍出现。`index.html` 里每个元素的 `data-in` 写的是**拍数**，配乐脚本 `tools/music.py` 用的是同一套拍数，所以改时间时两边一起改。

| 拍 | 时间 | 画面 |
|---|---|---|
| 0–8 | 0:00–0:03.8 | 米白底，三个圆点按大小依次弹出（大 = Opus，中 = Sonnet，小 = Haiku） |
| 8–16 | 0:03.8–0:07.5 | 四个大字，每两拍硬切一次背景色：更聪明 SMARTER / 更快 FASTER / 更省 CHEAPER / 更安全 SAFER |
| 16–24 | 0:07.5–0:11.3 | 标题 “Claude 5.5”，中间的小数点每拍换一种家族色；“三个尺寸，一个家族” |
| 24–36 | 0:11.3–0:16.9 | 阵容：三栏并列，Haiku 盖上 “COMING SOON” 印章；Opus 的圆放大成满屏橙色 |
| 36–88 | 0:16.9–0:41.3 | **01 Opus 5.5**（橙）：标题 → Fable 5.1 级表现 / −40% 成本 → 三项跑分柱状图 → 输出快 30% + 快速模式竞速条 → 价格对比 → 安全审计 |
| 88–124 | 0:41.3–0:58.1 | **02 Sonnet 5.5**（蓝）：标题 → 快 30%+ / 成本 −30% → 与 Opus 5.5 正面对比（半价印章）→ 彩蛋：只看截图通关《宝可梦 红》（像素屏 + 8 枚徽章 + 8-bit 配乐） |
| 124–136 | 0:58.1–1:03.8 | **03 Haiku 5.5**（荧光绿）：空心字、打字机 “COMING SOON”、停在 72% 的加载条 |
| 136–160 | 1:03.8–1:15 | 三个圆点重新排好，“Claude 5.5” 落版，“挑一个尺寸，开始构建。”，模型 ID，非官方声明 |

## 片中用到的数据

全部来自 Anthropic 的发布页（[Opus 5.5](https://www.anthropic.com/claude-opus-5-5)，[Sonnet 5.5](https://www.anthropic.com/claude-sonnet-5-5)），2026 年 10 月初核对。

### Claude Opus 5.5 · 2026.09.22
- Claude 5.5 家族的第一个模型；“performs at the level of Claude Fable 5.1 on most work and costs 40% less to run than Opus 5”
- 输出速度比 Opus 5 快 30% 以上；快速模式（Claude Code 和 Claude Platform）最高 2.5 倍速度
- 价格（每百万 tokens）：输入 $4、输出 $20、缓存读取 $0.20（Opus 5 为 $5 / $25 / $0.50）
- 跑分（max effort）：

  | | Opus 5.5 | Fable 5.1 | Opus 5 |
  |---|---|---|---|
  | Terminal-Bench 4.0 | 66.4% | 55.8% | 52.3% |
  | OSWorld 2.1 | 81.8% | 80.7% | 74.0% |
  | Humanity’s Last Exam（含工具） | 67.7% | 65.6% | 63.6% |

- 安全：在覆盖近 2,000 个场景的自动化行为审计中，“scored better than any recent Claude model on nearly every measure of misaligned behavior”

### Claude Sonnet 5.5 · 2026.09.28
- 家族第二个模型，定位是日常任务；比 Sonnet 5 快 30% 以上，大多数工作成本最多低 30%
- 价格与 Sonnet 5 相同：输入 $2、输出 $10（每百万 tokens）
- 与 Opus 5.5 对比：Terminal-Bench 4.0 70.6% vs 66.4%；GDPval-AA v2.1 1844 vs 1846；OSWorld 2.1 80.1% vs 81.8%
- “the first Sonnet model to beat Pokémon Red working only from screenshots”

### Claude Haiku 5.5
- 已宣布、尚未发布：“built for high-volume and cost-sensitive applications, will join the Claude 5.5 family in the coming weeks”
- 还没有公布模型 ID、价格和跑分，所以片中只写了“即将推出”，结尾也没有给它编一个 ID

竞速条（Opus 5 / Opus 5.5 / 快速模式）是按 1 : 1.3 : 2.5 的速度比例画的示意动画，不是实测。

## 声明
非官方致敬短片，与 Anthropic 没有关联。片中没有使用 Anthropic 或 Claude 的官方 logo，字体是开源字体（Inter Tight、Noto Sans SC、JetBrains Mono，均为 OFL），配乐是用代码从零合成的。
