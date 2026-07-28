---
name: mooc2handout
description: "End-to-end MOOC → handout pipeline. Downloads Coursera subtitles + video, uses AI to infer keyframe timestamps from VTT, extracts frames with ffmpeg, and scaffolds a LaTeX/Markdown handout. Handles full setup (opencli, adapter, ffmpeg) for first-time users."
allowed-tools: Bash, Read, Write, Edit
---

# mooc2handout skill

Full pipeline: Coursera subtitles → AI keyframe detection → frame extraction → structured handout.

---

## AGENT WORKFLOW

### Phase 1 — Download subtitles & video

#### 1a. Check prerequisites

```bash
opencli --version 2>/dev/null || echo "MISSING"
ls ~/.opencli/clis/coursera/download.js 2>/dev/null || echo "MISSING"
ffmpeg -version 2>/dev/null | head -1 || echo "MISSING"
```

If opencli missing → install: `npm install -g @jackwener/opencli`
If adapter missing → write `skill/download.js` to `~/.opencli/clis/coursera/download.js`
If ffmpeg missing → `sudo apt install ffmpeg` or `brew install ffmpeg`

#### 1b. Bind Chrome

```bash
opencli browser coursera bind
```

#### 1c. Download

```bash
# Full course with video (needed for keyframe extraction)
opencli coursera download "https://www.coursera.org/learn/COURSE" \
  --out ./notes --video --langs "en,zh-CN" --locale en

# Single module
opencli coursera download "https://www.coursera.org/learn/COURSE/home/module/1" \
  --out ./notes/module-1 --video --locale en
```

Output per module:
```
module-N/
├── 01_lecture.en.vtt
├── 01_lecture.mp4
├── 02_lecture.en.vtt
├── 02_lecture.mp4
└── manifest.json   (if available)
```

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

### Phase 4 — Scaffold handout

```bash
python3 scripts/scaffold_handout.py \
  --subtitle-dir ./notes/module-1 \
  --course-title "课程名" \
  --unit-title "单元名" \
  --output ./handout.tex
```

Then use AI to fill the scaffold with summarized content, insert keyframe images via `\includegraphics`, add exercises, and compile to PDF.

**Handout guidelines** are in `references/`:
- `handout-guidelines.md` — heading rules, list policy, merge policy
- `research-inserts.md` — recent research callouts
- `ai-embodied-intelligence.md` — AI/embodied intelligence bridges
- `illustrations.md` — suggested schematic figures

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

Write `skill/download.js` (from this repo) to `~/.opencli/clis/coursera/download.js`.

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
