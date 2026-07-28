---
name: mooc2handout
description: "End-to-end MOOC → handout pipeline. Supports multiple platforms (Coursera full, edX/FutureLearn planned). Downloads subtitles + video + supplementary resources, uses AI to infer keyframe timestamps from VTT, extracts frames with ffmpeg, and scaffolds a LaTeX/Markdown handout. Auto-detects platform from URL."
allowed-tools: Bash, Read, Write, Edit
---

# mooc2handout skill

Full pipeline: MOOC subtitles → AI keyframe detection → frame extraction → structured handout.

> **How to use this skill:** Give your AI agent the prompt below. It will clone the repo,
> follow the README installation steps, and run the full pipeline automatically.
>
> ```
> Clone https://github.com/dull-bird/mooc2handout-skill
> and follow the "Quick Start" and "Usage" sections
> in README.md to set up everything from scratch:
> install opencli, install the platform adapter,
> bind Chrome, then download the course at
> <PASTE_URL> with --video --resources,
> infer keyframes, extract frames, and scaffold
> a handout. Do not skip any prerequisite step.
> ```

---

## AGENT WORKFLOW

### Phase 1 — Download subtitles & video

The dispatcher `skill/mooc.js` auto-detects the platform from the URL and calls the right adapter.

#### 1a. Check prerequisites

```bash
opencli --version 2>/dev/null || echo "MISSING"
ls ~/.opencli/clis/coursera/download.js 2>/dev/null || echo "MISSING"
ffmpeg -version 2>/dev/null | head -1 || echo "MISSING"
```

If opencli missing → install: `npm install -g @jackwener/opencli`
If adapter missing → copy from `skill/adapters/<platform>.js` to `~/.opencli/clis/<platform>/download.js`
If ffmpeg missing → `sudo apt install ffmpeg` or `brew install ffmpeg`

#### 1b. Bind Chrome

```bash
# Bind to the platform domain
opencli browser coursera bind    # for Coursera
# opencli browser edx bind       # for edX (when available)
```

#### 1c. Download

```bash
# Universal dispatcher — auto-detects platform from URL
node skill/mooc.js "https://www.coursera.org/learn/COURSE" \
  --out ./notes --video --resources --langs "en,zh-CN" --locale en

# Or call the platform adapter directly:
opencli coursera download "https://www.coursera.org/learn/COURSE" \
  --out ./notes --video --resources --langs "en,zh-CN" --locale en

# Single module
opencli coursera download "https://www.coursera.org/learn/COURSE/home/module/1" \
  --out ./notes/module-1 --video --resources --locale en
```

**Supported platforms:**

| Platform | Status | Adapter |
|----------|--------|---------|
| Coursera | Full support | `adapters/coursera.js` |
| edX | Planned | `adapters/edx.js` |
| FutureLearn | Planned | `adapters/futurelearn.js` |

Output per module:
```
module-N/
├── 01_lecture.en.vtt
├── 01_lecture.mp4
├── 01_lecture_Background_Reading.pdf   ← supplementary resource
├── 01_lecture_Supplement__Set_Theory_.pdf
├── 02_lecture.en.vtt
├── 02_lecture.mp4
└── manifest.json   (if available)
```

**Flags:**
- `--video` — also download 720p video (needed for keyframe extraction)
- `--resources` — download supplementary materials (PDFs, slides, background reading)

---

### Phase 2 — AI keyframe inference

Run `scripts/vtt_keyframes.py` to analyze VTT subtitles and predict the best timestamps for screenshots:

```bash
python3 scripts/vtt_keyframes.py \
  --vtt-dir ./notes/module-1 \
  --output ./notes/module-1/keyframes.json \
  --max-per-lecture 5 \
  --interval 60
```

**What it does:**
- Parses VTT cue text and timestamps
- Detects semantic transitions (concept shifts, definitions, examples, summaries)
- Falls back to uniform interval for flat sections
- Outputs JSON: `[{ "file": "01_lecture.mp4", "time": 45.2, "reason": "definition", "text": "..." }]`

**Options:**
| Flag | Default | Meaning |
|------|---------|---------|
| `--max-per-lecture` | 5 | Max keyframes per lecture |
| `--interval` | 60 | Fallback interval in seconds |
| `--lang` | en | VTT language suffix to match |

---

### Phase 3 — Extract frames

Run `scripts/extract_frames.py` to cut frames from video at the predicted timestamps:

```bash
python3 scripts/extract_frames.py \
  --video-dir ./notes/module-1 \
  --keyframes ./notes/module-1/keyframes.json \
  --output ./notes/module-1/frames/ \
  --format png \
  --width 1280
```

**What it does:**
- Reads keyframes.json
- For each entry, runs `ffmpeg -ss <time> -i <video> -frames:v 1 -q:v 2 <output>`
- Names files: `01_lecture_0045s_definition.png`

**Options:**
| Flag | Default | Meaning |
|------|---------|---------|
| `--format` | png | Output format (png/jpg) |
| `--width` | 1280 | Scale width (0 = original) |
| `--quality` | 2 | JPEG quality (1-31, lower = better) |

---

### Phase 4 — Generate handout

#### 4a. Prepare supplements.json

Before generating, create `supplements.json` in the data directory with AI-summarized Chinese content for each supplementary PDF:

```json
{
  "01_lecture_Background_Reading.pdf": {
    "title": "背景阅读：什么是数学？",
    "summary": [
      "第一段中文总结（可含 LaTeX 标记如 \\textbf{}）",
      "第二段中文总结",
      "第三段中文总结"
    ]
  }
}
```

The agent should read each supplementary PDF, understand it, and write 3-4 bullet-point summaries in Chinese.

#### 4b. Generate LaTeX

```bash
# Chinese output (default)
python3 scripts/generate_handout.py \
  --data-dir ./notes/module-1 \
  --course-title "数学思维导论" \
  --unit-title "第一单元：数学思维入门" \
  --course-title-en "Mathematical Thinking" \
  --unit-title-en "Module 1: Introduction" \
  --instructor "Keith Devlin" \
  --lang zh \
  --output handout.tex

# English output (no redundant subtitles)
python3 scripts/generate_handout.py \
  --data-dir ./notes/module-1 \
  --course-title "Mathematical Thinking" \
  --unit-title "Module 1: Introduction" \
  --instructor "Keith Devlin" \
  --lang en \
  --output handout_en.tex
```

**What it produces:**
- Title page: Chinese primary + English secondary (zh mode) or English only (en mode)
- Video links with duration: `观看视频：第1讲（27:59）`
- Keyframe screenshots with Chinese captions: `时间戳 671s — 核心定义`
- Supplement summaries: title outside box + bullet points inside
- Key concepts with bold formatting
- Exercises with detailed solutions

#### 4c. Compile PDF

```bash
xelatex handout.tex && xelatex handout.tex
```

**Handout guidelines** are in `references/`:
- `handout-guidelines.md` — heading rules, list policy, merge policy
- `research-inserts.md` — recent research callouts
- `ai-embodied-intelligence.md` — AI/embodied intelligence bridges
- `illustrations.md` — suggested schematic figures

---

### Phase 5 — Verify PDF output

After compiling the PDF, **always verify** these checkpoints:

```bash
# 1. Check PDF was generated and has reasonable size
ls -lh handout.pdf
# Expect: > 100KB (with keyframes), 4+ pages

# 2. Check page count
pdfinfo handout.pdf 2>/dev/null | grep Pages || python3 -c "
import subprocess
r = subprocess.run(['xelatex', '--version'], capture_output=True)
print('PDF generated')
"

# 3. Verify keyframes are embedded (not broken links)
python3 -c "
import pdfplumber
with pdfplumber.open('handout.pdf') as pdf:
    for i, page in enumerate(pdf.pages):
        imgs = page.images
        if imgs:
            print(f'Page {i+1}: {len(imgs)} image(s) embedded')
"

# 4. Verify video links are clickable
python3 -c "
import pdfplumber
with pdfplumber.open('handout.pdf') as pdf:
    for i, page in enumerate(pdf.pages):
        links = [a for a in page.annots or [] if a.get('uri')]
        if links:
            print(f'Page {i+1}: {len(links)} link(s)')
"

# 5. Check for LaTeX errors in log
grep -c "^!" handout.log && echo "ERRORS FOUND" || echo "No errors"
```

**Checklist (must all pass):**

| Check | Expected |
|-------|----------|
| PDF file exists | `handout.pdf` > 100 KB |
| Page count | ≥ 4 pages |
| Keyframe images | At least 1 image per lecture section |
| Video links | ▶ icon visible, links clickable |
| No subtitle dump | No raw VTT text blocks in content |
| Section numbering | No duplicate numbers (e.g. "2.2 2. Title") |
| Supplementary materials | PDF summaries present, not just filenames |
| Exercises | Questions + answers both present |
| LaTeX log | Zero `!` errors |

If any check fails, fix the issue and recompile before delivering.

---

## INSTALL: opencli

```bash
npm install -g @jackwener/opencli
opencli --version
```

## INSTALL: Chrome bridge

```bash
opencli doctor
# Or launch Chrome manually:
google-chrome --remote-debugging-port=9222 &
```

## INSTALL: adapter

```bash
# Coursera
mkdir -p ~/.opencli/clis/coursera
cp skill/adapters/coursera.js ~/.opencli/clis/coursera/download.js

# Future: edX
# mkdir -p ~/.opencli/clis/edx
# cp skill/adapters/edx.js ~/.opencli/clis/edx/download.js
```

Verify:
```bash
opencli coursera download --help
```

## INSTALL: ffmpeg

```bash
# Ubuntu/Debian
sudo apt install ffmpeg
# macOS
brew install ffmpeg
```

---

## TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| No modules found | Check URL and login |
| No video files | Add `--video` flag |
| ffmpeg not found | Install ffmpeg |
| Keyframes JSON empty | Check VTT files exist and are non-empty |
| Frame extraction fails | Verify video files are valid MP4 |
| No resources downloaded | Some lectures have no supplementary materials; this is normal |
