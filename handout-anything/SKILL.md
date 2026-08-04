---
name: handout-anything
description: "Turn any LOCAL knowledge material — textbook/PDF (digital or scanned), local video with subtitles, audio/podcast recordings, Markdown/text/blog exports, papers (single or a mixed corpus on one theme) — into a structured, first-principles study handout (讲义) with unit planning, hub-concept identification, Feynman-style explanations, exercises with answers, quantitatively consistent figures, and delivery verification. Use when the user provides local files or folders and wants them converted into a handout, 讲义, study notes, or teaching document. NOT for downloading MOOC platforms (use the dedicated coursera tool for that)."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# HandoutAnything skill

把用户给定的**本地材料**变成一份结构化的讲义。本 skill 只管"本地已有材料 → 讲义"，不负责网课平台下载（Coursera 等请用专用工具）。

**开工前必读** [references/handout-methodology.md](references/handout-methodology.md)——适用性边界、知识量标定、拆解流程、讲解原则、结构模板、验证清单都在那里定义，本文件只做路由与流程编排。

> 本文件中所有相对路径（`references/`、`scripts/`）均相对于本 skill 目录自身——本 skill 是自包含的，单独拷贝/上传整个 `handout-anything/` 目录即可正常工作。

## 第 0 步：适用性判断（先做，不可跳过）

按方法论 §0 做绿灯/黄灯/红灯判断，并用一句话写出"这份材料为什么适合做讲义"。

- 红灯（虚构作品欣赏目的、无概念结构的材料、密度过低）：停止，向用户说明理由并建议替代产物（书评、导读、单页摘要）。
- 黄灯（虚构作品用于研究、混合语料、过剩材料）：与用户确认重新定义后的目标与边界，再继续。

## 第 1 步：输入路由（本地材料）

| 输入形式 | 提取路径 |
|---|---|
| 教材 / 书籍 PDF（数字版） | `pdftotext` 提取全文 |
| 教材 / 书籍 PDF（扫描件） | `pdfinfo` + 试取确认后，放弃文本管道：关键页 `pdftoppm` 渲染后视觉读取，或局部 OCR |
| 本地视频 + 字幕文件 | 字幕（VTT/SRT/TXT）按时间戳切分主题段；需要画面时 `scripts/extract_frames.py` 截帧后视觉读取 |
| 本地视频（无字幕） | 先转写（whisper 类工具）得到带时间戳文本，再按上一条处理 |
| 音频 / 播客文件 | 先转写为文本，再按文本处理 |
| Markdown / TXT / 博客导出 | 直接读取；多篇时标注来源 |
| 论文 PDF（单篇） | 提取全文；按方法论 §2.3 的论文框架拆解（背景→主张→方法→证据→局限），警惕一面之词 |
| 论文集 / 主题语料（文件夹） | 先建问题树，材料映射到问题节点，单元按问题而非按材料划分 |

**起飞前检查**（每个输入必做）：可提取性、版本/版次（目录页是最快指纹）、结构化程度（已编排 / 原始堆积）。

## 第 2 步：拆解与规划

1. 结构提取（目录 / 章节 / 字幕段落）→ 概念清单（定义、公式、符号口径、适用条件）。
2. 与用户确认**目标读者**（决定读者差集）与**时间盒**（如一周 7±2 单元）。
3. 概念地图 + 枢纽概念打分（方法论 §3.1）。
4. 输出**单元规划**给用户确认后再动笔：每个单元一行——标题、核心概念、支撑要点、所属类型（计算/思辨/阅读/技能）。知识量标定按方法论 §2 执行；超量先砍非枢纽概念。

## 第 3 步：写作

按方法论 §4（讲解原则）与 §5（结构模板）写作：

- 每单元：核心问题 → 第一性讲解 → 公式/图象/推导 → 易错点与失效边界 → 自测。
- 图示遵守 §5.4 三条规范（定量自洽、由构造保证、记号有交代）。
- 排版实现：首选 LaTeX（ctexart + tcolorbox + TikZ，风格参照本仓库 examples/physics-handout / examples/math-handout）；纯文本字幕类材料也可用 `scripts/generate_handout.py` 流水线（参照 examples/feynman-technique/）。

## 第 4 步：验证与交付

逐项执行方法论 §6 验证清单。硬指标：

- 编译 0 错误；日志无 `Missing character`；
- **lint 通过**：`python3 scripts/lint_handout.py handout.tex handout.log`（ASCII 直引号、ASCII 省略号、中文引号配对、孤立单个 …、缺字形、编译错误）；
- **review 通过**：`python3 scripts/review_handout.py handout.tex`（开始前/今日自测/参考答案/收尾呼应/单元数 5–9 等结构硬指标）；要求 0 errors，warnings 每条都必须有意识地为它找到理由；
- 每单元已按方法论 §2.5 公式标注实际工作量（写完再报，禁止先报时间再凑内容）；
- 每单元已标优先级与难度，"开始前"页有依赖关系图；
- 逐页目检（渲染 PNG 抽查全部图页）；
- 概念清单中【全新】概念每个都有落点；
- 收尾"能讲给别人听的 N 句话"与开篇呼应。

## LaTeX 编译环境

本仓库讲义统一用 `xelatex` 编译（ctexart + tcolorbox + TikZ）。用户机器没有 LaTeX 环境时按以下指引：

- **Windows（推荐 MiKTeX）**：初始安装仅约 300–500 MB。安装时选 "Install missing packages on-the-fly = Yes"，首次编译会自动联网补齐 ctex、xecjk、tcolorbox 等全部依赖（第一次编译较慢属正常）；建议将包仓库源切到国内镜像（MiKTeX Console → Packages → Change package repository）。中文字体用 Windows 自带宋体/黑体即可，无需另装。
- **Windows 备选**：磁盘充裕可装 TeX Live 完整版（约 8 GB），一劳永逸。不推荐 TeX Live basic——xelatex 与中文宏包都需手动 `tlmgr install` 补齐，包清单易随讲义依赖演进而腐坏。
- **本机（Linux）**：已有 xelatex/latexmk；各讲义目录下的本地 `texmf/` 用于补齐系统缺的宏包（如 tcolorbox）。

## 已有实例（本仓库可直接参考）

- `examples/physics-handout/`：教材 PDF → 7 天物理讲义（LaTeX 手写 + TikZ 矢量图）
- `examples/math-handout/`：教材 PDF（新版 + 扫描旧版对照）→ 9 天数学讲义
- `examples/feynman-technique/`：视频字幕转录 → 费曼学习法讲义（generate_handout.py 流水线）
