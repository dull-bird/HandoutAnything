#!/usr/bin/env python3
"""
vtt_keyframes.py — AI-style keyframe inference from VTT subtitles.

Analyzes VTT cue text to detect semantically important moments
(concept shifts, definitions, examples, summaries) and outputs
a JSON list of recommended timestamps for screenshot extraction.

Usage:
    python3 vtt_keyframes.py --vtt-dir ./module-1 --output keyframes.json
    python3 vtt_keyframes.py --vtt-dir ./module-1 --output keyframes.json --max-per-lecture 5 --interval 60
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ── VTT parser ────────────────────────────────────────────────────────────────

def parse_vtt_timestamp(ts: str) -> float:
    """Convert VTT timestamp (HH:MM:SS.mmm or MM:SS.mmm) to seconds."""
    ts = ts.strip()
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        raise ValueError(f"Invalid VTT timestamp: {ts}")


def parse_vtt(path: Path):
    """Parse a VTT file into a list of (start_sec, end_sec, text) cues."""
    content = path.read_text(encoding="utf-8", errors="replace")
    cues = []
    # Match WEBVTT timestamp lines: HH:MM:SS.mmm --> HH:MM:SS.mmm
    cue_re = re.compile(
        r"(\d{1,2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}\.\d{3})"
    )
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        m = cue_re.match(lines[i])
        if m:
            start = parse_vtt_timestamp(m.group(1))
            end = parse_vtt_timestamp(m.group(2))
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip():
                # Strip VTT tags like <c>, <b>, etc.
                clean = re.sub(r"<[^>]+>", "", lines[i])
                text_lines.append(clean.strip())
                i += 1
            text = " ".join(text_lines)
            if text:
                cues.append((start, end, text))
        else:
            i += 1
    return cues


# ── Semantic detectors ────────────────────────────────────────────────────────

# Chinese patterns
ZH_CONCEPT_SHIFT = [
    r"但是", r"然而", r"不过", r"接下来", r"下面", r"然后",
    r"现在", r"我们来看", r"换一个", r"另一个", r"不同的",
]
ZH_DEFINITION = [
    r"所谓", r"是指", r"定义为", r"叫做", r"也就是说",
    r"意思是", r"换句话说", r"即", r"称之为",
]
ZH_EXAMPLE = [
    r"举个例子", r"比如", r"例如", r"比方说", r"拿.*来说",
    r"一个例子", r"具体来", r"来看一个",
]
ZH_SUMMARY = [
    r"总结一下", r"回顾", r"小结", r"总之", r"综上所述",
    r"总的来说", r"要点是", r"核心就是",
]

# English patterns
EN_CONCEPT_SHIFT = [
    r"\bbut\b", r"\bhowever\b", r"\bnow\b", r"\bnext\b",
    r"\blet'?s (?:look at|turn to|move on)\b", r"\banother\b",
    r"\bdifferent\b", r"\bon the other hand\b", r"\bin contrast\b",
]
EN_DEFINITION = [
    r"\b(?:is |are |was |were )?(?:defined|called|known) as\b",
    r"\bmeans that\b", r"\bin other words\b", r"\bthat is to say\b",
    r"\brefers to\b", r"\bwe call (?:this|it)\b",
]
EN_EXAMPLE = [
    r"\bfor example\b", r"\bfor instance\b", r"\bsuch as\b",
    r"\blet'?s (?:say|imagine|consider|look at)\b",
    r"\ba case in point\b", r"\bto illustrate\b",
]
EN_SUMMARY = [
    r"\bto summarize\b", r"\bin summary\b", r"\bto recap\b",
    r"\bthe key (?:point|takeaway)\b", r"\ball in all\b",
    r"\bthe main (?:point|idea| takeaway)\b", r"\breview\b",
]


def detect_reason(text: str):
    """Return (reason, match) or (None, None)."""
    # Try Chinese first, then English
    for patterns, reason in [
        (ZH_DEFINITION, "definition"), (ZH_EXAMPLE, "example"),
        (ZH_SUMMARY, "summary"), (ZH_CONCEPT_SHIFT, "concept_shift"),
        (EN_DEFINITION, "definition"), (EN_EXAMPLE, "example"),
        (EN_SUMMARY, "summary"), (EN_CONCEPT_SHIFT, "concept_shift"),
    ]:
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return reason, m.group(0)
    return None, None


# ── Keyframe inference ────────────────────────────────────────────────────────

def infer_keyframes(cues, max_per_lecture=5, interval=60):
    """
    Given a list of (start, end, text) cues, return a list of
    { "time": float, "reason": str, "text": str } dicts.
    """
    if not cues:
        return []

    total_duration = cues[-1][1]  # end of last cue
    candidates = []

    # 1. Semantic detection pass
    seen_times = set()
    for start, end, text in cues:
        reason, match = detect_reason(text)
        if reason:
            # Use the midpoint of the cue as the keyframe time
            t = round((start + end) / 2, 1)
            # Avoid duplicates within 5 seconds
            if not any(abs(t - st) < 5 for st in seen_times):
                candidates.append({"time": t, "reason": reason, "text": text[:120]})
                seen_times.add(t)

    # 2. Sort by time
    candidates.sort(key=lambda c: c["time"])

    # 3. If we have enough, trim to max
    if len(candidates) >= max_per_lecture:
        # Prioritize: definition > concept_shift > example > summary
        priority = {"definition": 0, "concept_shift": 1, "example": 2, "summary": 3}
        candidates.sort(key=lambda c: priority.get(c["reason"], 4))
        candidates = candidates[:max_per_lecture]
        candidates.sort(key=lambda c: c["time"])
        return candidates

    # 4. Fill gaps with uniform interval
    if candidates:
        # Find gaps > interval seconds
        filled = [candidates[0]]
        for i in range(1, len(candidates)):
            gap = candidates[i]["time"] - candidates[i - 1]["time"]
            if gap > interval * 1.5:
                # Insert intermediate frames
                n_extra = int(gap / interval)
                for j in range(1, n_extra + 1):
                    t = round(candidates[i - 1]["time"] + j * (gap / (n_extra + 1)), 1)
                    if not any(abs(t - c["time"]) < 5 for c in candidates):
                        filled.append({"time": t, "reason": "interval", "text": ""})
            filled.append(candidates[i])
        candidates = filled

    # Add interval frames at the beginning if needed
    if candidates and candidates[0]["time"] > interval:
        t = round(interval, 1)
        candidates.insert(0, {"time": t, "reason": "interval", "text": ""})

    # Final trim
    if len(candidates) > max_per_lecture:
        step = len(candidates) / max_per_lecture
        candidates = [candidates[int(i * step)] for i in range(max_per_lecture)]

    return candidates


# ── Main ──────────────────────────────────────────────────────────────────────

def find_matching_video(vtt_path: Path, video_dir: Path) -> str | None:
    """Find the .mp4 file that matches a VTT file by shared prefix."""
    stem = vtt_path.stem
    # Remove language suffix: 01_lecture.en -> 01_lecture
    base = re.sub(r"\.(en|zh-CN|zh-TW|ja|ko|fr|de|es|pt|ar)$", "", stem)
    mp4 = video_dir / f"{base}.mp4"
    if mp4.exists():
        return mp4.name
    # Fallback: find any mp4 with the same numeric prefix
    prefix = base.split("_")[0]
    for f in sorted(video_dir.glob("*.mp4")):
        if f.stem.startswith(prefix):
            return f.name
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Infer keyframe timestamps from VTT subtitles."
    )
    parser.add_argument("--vtt-dir", required=True, help="Directory with .vtt files")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--max-per-lecture", type=int, default=5)
    parser.add_argument("--interval", type=int, default=60, help="Fallback interval (seconds)")
    parser.add_argument("--lang", default="en", help="VTT language suffix to match (e.g. en, zh-CN)")
    parser.add_argument("--video-dir", default=None, help="Video directory (defaults to --vtt-dir)")
    args = parser.parse_args()

    vtt_dir = Path(args.vtt_dir)
    video_dir = Path(args.video_dir) if args.video_dir else vtt_dir
    output = Path(args.output)

    if not vtt_dir.is_dir():
        print(f"Error: {vtt_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Find VTT files for the target language
    lang_suffix = f".{args.lang}.vtt"
    vtt_files = sorted(vtt_dir.glob(f"*{lang_suffix}"))

    if not vtt_files:
        # Fallback: use any VTT files
        vtt_files = sorted(vtt_dir.glob("*.vtt"))
        # Filter out non-language VTTs (like .en.vtt already matched)
        if not vtt_files:
            print(f"Error: no VTT files found in {vtt_dir}", file=sys.stderr)
            sys.exit(1)
        print(f"Warning: no .{args.lang}.vtt files, using all VTT files", file=sys.stderr)

    all_keyframes = []

    for vtt_file in vtt_files:
        cues = parse_vtt(vtt_file)
        if not cues:
            continue

        video_name = find_matching_video(vtt_file, video_dir)
        keyframes = infer_keyframes(cues, args.max_per_lecture, args.interval)

        for kf in keyframes:
            entry = {
                "vtt": vtt_file.name,
                "time": kf["time"],
                "reason": kf["reason"],
                "text": kf["text"],
            }
            if video_name:
                entry["video"] = video_name
            all_keyframes.append(entry)

    # Sort by video then time
    all_keyframes.sort(key=lambda k: (k.get("video", ""), k["time"]))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(all_keyframes, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(all_keyframes)} keyframes to {output}")


if __name__ == "__main__":
    main()
