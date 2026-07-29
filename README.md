# mooc2handout-skill

一站式 MOOC → 讲义流水线：下载字幕 → AI 推断关键帧 → 提取画面 → 生成结构化讲义。

## 功能

| 阶段 | 工具 | 说明 |
|------|------|------|
| 1. 下载字幕 + 视频 | `skill/mooc.js` + `adapters/` | 多平台支持（Coursera/edX/...），自动检测，补充材料 |
| 2. AI 推断关键帧 | `scripts/vtt_keyframes.py` | 从 VTT 字幕语义分析，推断最佳课件截图时间戳 |
| 3. 提取关键帧 | `scripts/extract_frames.py` | ffmpeg 按时间戳从视频中截取画面 |
| 4. 生成讲义 | `scripts/scaffold_handout.py` + AI | 字幕 + 关键帧 → LaTeX/Markdown 结构化讲义 |

## 目录结构

```
mooc2handout-skill/
├── README.md
├── skill/
│   ├── SKILL.md              ← AI agent skill（全流程自动配置）
│   ├── mooc.js               ← 通用入口（自动检测平台，分发到对应 adapter）
│   └── adapters/
│       └── coursera.js       ← Coursera adapter（字幕/视频/补充材料下载）
│       └── (edx.js)          ← edX adapter（planned）
├── scripts/
│   ├── vtt_keyframes.py      ← AI 从 VTT 推断关键帧时间戳
│   ├── extract_frames.py     ← ffmpeg 按时间戳提取画面
│   └── scaffold_handout.py   ← 从字幕 manifest 生成 LaTeX 讲义骨架
└── references/
    ├── handout-guidelines.md
    ├── research-inserts.md
    ├── ai-embodied-intelligence.md
    └── illustrations.md
```

## 快速开始

### 方式一：手动安装

```bash
# 1. 安装 opencli
npm install -g @jackwener/opencli

# 2. 安装 adapter（按需安装对应平台）
mkdir -p ~/.opencli/clis/coursera
cp skill/adapters/coursera.js ~/.opencli/clis/coursera/download.js

# 3. 验证
opencli coursera download --help
```

### 方式二：让 AI 自动配置（推荐）

把下面这段提示词发给你的 AI agent（Gemini / Claude / 任何支持工具调用的 agent）：

```
Clone https://github.com/dull-bird/mooc2handout-skill
and follow the "Quick Start" and "Usage" sections
in README.md to set up everything from scratch:
install opencli, install the platform adapter,
bind Chrome, then download the course at
<PASTE_URL> with --video --resources,
infer keyframes, extract frames, and scaffold
a handout. Do not skip any prerequisite step.
```

AI 会自动完成：安装依赖 → 配置 adapter → 绑定 Chrome → 下载字幕/视频/补充材料 → 推断关键帧 → 提取画面 → 生成讲义。

## 使用流程

```bash
# ① 绑定 Chrome（需已登录 coursera.org）
opencli browser coursera bind

# ② 下载字幕 + 视频（通用入口，自动检测平台）
node skill/mooc.js "https://www.coursera.org/learn/COURSE" \
  --out ./notes --video --resources --locale en
# 或直接调用平台 adapter：
opencli coursera download "URL" --out ./notes --video --resources

# ③ AI 推断关键帧时间戳
python3 scripts/vtt_keyframes.py \
  --vtt-dir ./notes/module-1 \
  --output ./notes/module-1/keyframes.json

# ④ 从视频中提取关键帧
python3 scripts/extract_frames.py \
  --video-dir ./notes/module-1 \
  --keyframes ./notes/module-1/keyframes.json \
  --output ./notes/module-1/frames/

# ⑤ 生成讲义骨架
python3 scripts/scaffold_handout.py \
  --subtitle-dir ./notes/module-1 \
  --course-title "课程名" \
  --unit-title "单元名" \
  --lang zh \
  --output ./handout.tex
```

English handouts require `content_en.json` and, when supplementary PDFs exist, `supplements_en.json`. English mode does not fall back to Chinese content.

## 关键帧推断原理

`vtt_keyframes.py` 分析 VTT 字幕文本，基于以下规则推断关键帧：

1. **概念转折** — "但是"、"然而"、"接下来" 等转折/过渡词
2. **定义出现** — "所谓"、"是指"、"定义为" 等定义性表述
3. **示例切换** — "举个例子"、"比如" 等示例引入
4. **总结回顾** — "总结一下"、"回顾" 等总结性表述
5. **均匀分布** — 无明显语义转折时，按固定间隔补充关键帧

每个候选时间戳标注原因（concept_shift / definition / example / summary / interval）。

## 依赖

- Node.js ≥ 18
- opencli
- Python ≥ 3.8
- ffmpeg（关键帧提取）
- Chrome / Chromium（字幕下载）

## License

MIT
