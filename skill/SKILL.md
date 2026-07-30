---
name: mooc2handout
description: "End-to-end MOOC → handout pipeline. Use when downloading subtitles, videos, and resources, then producing structured lecture handouts with per-lecture digests, diagram blocks, keyframe-driven visual notes, unit synthesis, discussion, and verification."
allowed-tools: Bash, Read, Write, Edit
---

# mooc2handout skill

Use this skill to turn one MOOC unit into a handout that reads like a human study note, not a transcript dump.

## Standard workflow

1. Process one lecture at a time.
2. For each lecture, extract:
   - the core idea in plain language
   - 3-5 key points
   - one diagram / flow / comparison block when the lecture is structural
   - one visual note derived from the keyframe review
3. After all lectures, add:
   - a unit synthesis that ties the lectures together
   - an extension / discussion section
   - takeaways, exercises, and answers
4. Run two checks:
   - coverage: every lecture has a usable digest
   - consistency: no cross-lecture leakage, no mixed language, no missing visual clues
5. Treat keyframes as review anchors. The image is for reading and extracting ideas, not decoration.

## Prompt reference

Use [references/handout-authoring-prompt.md](references/handout-authoring-prompt.md) when drafting or revising `content.json`.

## Pipeline

### Phase 1 — Download subtitles, video, and resources

`skill/mooc.js` auto-detects the platform and dispatches to the right adapter.

```bash
opencli browser coursera bind
node skill/mooc.js "https://www.coursera.org/learn/COURSE" \
  --out ./notes --video --resources --locale en
```

### Phase 2 — Infer keyframes from subtitle timing

`scripts/vtt_keyframes.py` should prefer structural and explanatory cues over bare transition words.

```bash
python3 scripts/vtt_keyframes.py \
  --vtt-dir ./notes/module-1 \
  --output ./notes/module-1/keyframes.json \
  --max-per-lecture 5 \
  --interval 60
```

The output should include:
- timestamp
- reason
- short transcript cue
- timing context
- a short visual hint for later frame review

### Phase 3 — Extract frames and prepare review artifacts

```bash
python3 scripts/extract_frames.py \
  --video-dir ./notes/module-1 \
  --keyframes ./notes/module-1/keyframes.json \
  --output ./notes/module-1/frames/
```

Use the extracted images to read the slide or diagram, then convert that into notes. Do not treat screenshots as the final product.

### Phase 4 — Write content.json

Prefer structured lecture entries instead of one long blob. A lecture can contain:

- `summary`
- `key_points`
- `diagram`
- `visual_notes`
- `discussion`

If a course needs an overall wrap-up, add top-level `synthesis` and `discussion`.

### Phase 5 — Generate and verify the handout

```bash
python3 scripts/generate_handout.py \
  --data-dir ./notes/module-1 \
  --course-title "课程名" \
  --unit-title "单元名" \
  --lang zh \
  --output handout.tex

xelatex handout.tex && xelatex handout.tex
```

Always check:
- every lecture section appears
- diagrams and visual notes are readable
- the unit synthesis is present
- keyframe notes match the lecture timing
- no subtitle text leaks into the wrong lecture

