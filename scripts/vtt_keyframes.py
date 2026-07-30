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
import math
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

CATEGORY_PATTERNS = [
    (
        "architecture",
        [
            r"\bdiagram\b",
            r"\blooks like this\b",
            r"\blook like this\b",
            r"\bhere'?s what happens\b",
            r"\bwalk through\b",
            r"\bstep by step\b",
            r"\bflowchart\b",
            r"\bflow\b",
            r"\bcomponent\b",
            r"\binterface\b",
            r"\baccess point\b",
            r"\btransport agnostic\b",
            r"\bside detour\b",
            r"\bclient and server\b",
            r"\bserver and client\b",
            r"图",
            r"框图",
            r"流程图",
            r"架构",
            r"示意",
            r"图示",
            r"关系图",
        ],
    ),
    (
        "definition",
        [
            r"\bthe purpose of\b",
            r"\bwhat (?:we|this|it) want(?:s)? to do is\b",
            r"\bwhat this means is\b",
            r"\bthis means\b",
            r"\bin other words\b",
            r"\bthat is(?: to say)?\b",
            r"\bthe idea here is\b",
            r"\byou can think of\b",
            r"\bbasically\b",
            r"\bin essence\b",
            r"\bthe point here is\b",
            r"\bto be clear\b",
            r"\bdefined as\b",
            r"\bcalled\b",
            r"\bknown as\b",
            r"所谓",
            r"是指",
            r"定义为",
            r"也就是说",
            r"换句话说",
            r"意思是",
            r"本质上",
            r"可以把.*看作",
        ],
    ),
    (
        "comparison",
        [
            r"\binstead of\b",
            r"\brather than\b",
            r"\bon the other hand\b",
            r"\bcompared to\b",
            r"\bdifferent\b",
            r"\bdifference\b",
            r"\bcontrast\b",
            r"\bversus\b",
            r"\bwhat makes .* different\b",
            r"\bnot .* but\b",
            r"不同",
            r"区别",
            r"对比",
            r"相比",
        ],
    ),
    (
        "workflow",
        [
            r"\bfirst\b",
            r"\bthen\b",
            r"\bnext\b",
            r"\bafter that\b",
            r"\bbefore\b",
            r"\bwe are going to\b",
            r"\blet'?s\b",
            r"\bset up\b",
            r"\brun\b",
            r"\binspect\b",
            r"\brequest\b",
            r"\brespond\b",
            r"\bupdate\b",
            r"\bcall\b",
            r"\bfrom here\b",
            r"\bthe remainder\b",
            r"先",
            r"然后",
            r"接着",
            r"再",
            r"最后",
            r"步骤",
            r"流程",
            r"运行",
            r"检查",
        ],
    ),
    (
        "example",
        [
            r"\bfor example\b",
            r"\bfor instance\b",
            r"\bsuch as\b",
            r"\blet'?s (?:say|imagine|consider|look at)\b",
            r"\ba case in point\b",
            r"\bto illustrate\b",
            r"举个例子",
            r"比如",
            r"例如",
            r"比方说",
            r"拿.*来说",
        ],
    ),
    (
        "summary",
        [
            r"\bto summarize\b",
            r"\bin summary\b",
            r"\bto recap\b",
            r"\bthe key (?:point|takeaway)\b",
            r"\ball in all\b",
            r"\bthe main (?:point|idea| takeaway)\b",
            r"\breview\b",
            r"总结一下",
            r"回顾",
            r"小结",
            r"总之",
            r"综上所述",
            r"要点是",
            r"核心就是",
        ],
    ),
    (
        "concept_shift",
        [
            r"\bbut\b",
            r"\bhowever\b",
            r"\bnow\b",
            r"\bnext\b",
            r"\blet'?s (?:look at|turn to|move on)\b",
            r"\banother\b",
            r"\bon the other hand\b",
            r"\bin contrast\b",
            r"但是",
            r"然而",
            r"不过",
            r"接下来",
            r"下面",
            r"然后",
            r"现在",
            r"我们来看",
            r"换一个",
            r"另一个",
            r"不同的",
        ],
    ),
]

CATEGORY_PRIORITY = {
    "architecture": 0,
    "definition": 1,
    "comparison": 2,
    "workflow": 3,
    "example": 4,
    "summary": 5,
    "concept_shift": 6,
    "interval": 7,
}

TOPIC_TERMS = [
    "client",
    "server",
    "tool",
    "resource",
    "prompt",
    "protocol",
    "message",
    "request",
    "response",
    "transport",
    "session",
    "discover",
    "subscribe",
    "notification",
    "capability",
]

HINTS = {
    "architecture": {
        "en": "Look for a flow, diagram, or component split.",
        "zh": "留意流程图、框图或组件分工。",
    },
    "definition": {
        "en": "Look for the sentence that defines the idea.",
        "zh": "留意给出定义或解释的那一句。",
    },
    "comparison": {
        "en": "Look for the contrast or before/after split.",
        "zh": "留意对比、差异或前后变化。",
    },
    "workflow": {
        "en": "Look for the step order or process view.",
        "zh": "留意步骤顺序或流程视图。",
    },
    "example": {
        "en": "Look for the concrete example or scenario.",
        "zh": "留意具体例子或场景。",
    },
    "summary": {
        "en": "Look for the recap or takeaway slide.",
        "zh": "留意总结或回顾性画面。",
    },
    "concept_shift": {
        "en": "Look for the transition into a new subtopic.",
        "zh": "留意切换到新小节的过渡点。",
    },
    "interval": {
        "en": "Look for a representative excerpt from the lecture.",
        "zh": "留意这一段的代表性画面。",
    },
}


def detect_reasons(text: str) -> list[str]:
    """Return matching semantic categories in priority order."""
    lowered = text.lower()
    matched: list[str] = []
    for reason, patterns in CATEGORY_PATTERNS:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                matched.append(reason)
                break
    if not matched:
        return ["interval"]
    matched.sort(key=lambda reason: CATEGORY_PRIORITY.get(reason, 99))
    # Keep the strongest reason first, but preserve any useful secondary matches.
    deduped: list[str] = []
    for reason in matched:
        if reason not in deduped:
            deduped.append(reason)
    return deduped


def reason_label(reason: str) -> str:
    labels = {
        "architecture": "architecture",
        "definition": "definition",
        "comparison": "comparison",
        "workflow": "workflow",
        "example": "example",
        "summary": "summary",
        "concept_shift": "concept_shift",
        "interval": "interval",
    }
    return labels.get(reason, "interval")


def reason_hint(reason: str, lang: str) -> str:
    hint = HINTS.get(reason, HINTS["interval"])
    if lang.startswith("zh"):
        return hint["zh"]
    return hint["en"]


def compact_text(text: str, max_len: int = 160) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    cut_points = [text.rfind(p, 0, max_len) for p in ["。", "！", "？", "；", ".", "!", "?", ";", ",", "，", ":"]]
    cut = max(cut_points)
    if cut < max_len // 2:
        cut = max_len
    text = text[:cut].rstrip()
    return text + ("…" if not text.endswith("…") else "")


def score_cue(text: str, reasons: list[str], position: float, duration: float, total_duration: float) -> float:
    """Score how likely a cue should become a keyframe."""
    lower = text.lower()
    score = 0.0
    primary = reasons[0]
    score += {
        "architecture": 10.0,
        "definition": 9.0,
        "comparison": 8.0,
        "workflow": 7.5,
        "example": 6.5,
        "summary": 6.0,
        "concept_shift": 3.0,
        "interval": 1.0,
    }.get(primary, 1.0)

    if len(reasons) > 1:
        score += min(2.0, 0.75 * (len(reasons) - 1))

    word_count = len(re.findall(r"\w+|[\u4e00-\u9fff]", text))
    if 8 <= word_count <= 35:
        score += 1.5
    elif word_count > 35:
        score += 0.5
    elif word_count < 4:
        score -= 1.5

    if duration >= 3.5:
        score += 1.0
    elif duration < 1.5:
        score -= 0.5

    if any(term in lower for term in TOPIC_TERMS):
        score += 1.5

    if position <= 0.15 or position >= 0.85:
        score += 0.75

    if any(mark in text for mark in [":", "：", "->", "→", "—", "-", "/"]):
        score += 0.5

    if total_duration and total_duration >= 300 and duration >= 2:
        score += 0.25

    return score


def build_candidate(cue: dict, index: int, total_duration: float, lang: str) -> dict:
    start = cue["start"]
    end = cue["end"]
    text = cue["text"]
    duration = max(0.1, end - start)
    position = (start + duration / 2) / total_duration if total_duration else 0.0
    reasons = detect_reasons(text)
    primary = reasons[0]
    score = score_cue(text, reasons, position, duration, total_duration)
    return {
        "cue_index": index,
        "cue_start": round(start, 3),
        "cue_end": round(end, 3),
        "duration": round(duration, 3),
        "position": round(position, 3),
        "reasons": reasons,
        "reason": reason_label(primary),
        "hint": reason_hint(primary, lang),
        "score": round(score, 3),
        "cue_text": text,
        "text": compact_text(text, 160),
        "context_before": "",
        "context_after": "",
        "context": "",
    }


# ── Keyframe inference ────────────────────────────────────────────────────────

def infer_keyframes(cues, max_per_lecture=5, interval=60, lang="en"):
    """Infer keyframes from subtitle cues using scoring and timing coverage."""
    if not cues:
        return []

    total_duration = cues[-1]["end"]
    candidates = [build_candidate(cue, index, total_duration, lang) for index, cue in enumerate(cues)]
    if not candidates:
        return []

    bucket_width = max(float(interval), total_duration / max(1, max_per_lecture))
    bucket_count = max(1, min(max_per_lecture, int(math.ceil(total_duration / bucket_width))))
    buckets: dict[int, dict] = {}

    for candidate in candidates:
        bucket_index = min(int(candidate["cue_start"] // bucket_width), bucket_count - 1)
        candidate = dict(candidate)
        candidate["bucket"] = bucket_index
        current = buckets.get(bucket_index)
        if current is None:
            buckets[bucket_index] = candidate
            continue
        current_key = (-current["score"], CATEGORY_PRIORITY.get(current["reason"], 99), current["cue_start"])
        candidate_key = (-candidate["score"], CATEGORY_PRIORITY.get(candidate["reason"], 99), candidate["cue_start"])
        if candidate_key < current_key:
            buckets[bucket_index] = candidate

    selected = [buckets[idx] for idx in sorted(buckets)]

    # Fill gaps with the strongest remaining cues if some buckets stayed empty.
    selected_ids = {cand["cue_index"] for cand in selected}
    min_gap = max(8.0, float(interval) * 0.45)
    if len(selected) < min(max_per_lecture, len(candidates)):
        for candidate in sorted(candidates, key=lambda c: (-c["score"], c["cue_start"])):
            if candidate["cue_index"] in selected_ids:
                continue
            if any(abs(candidate["cue_start"] - chosen["cue_start"]) < min_gap for chosen in selected):
                continue
            selected.append(candidate)
            selected_ids.add(candidate["cue_index"])
            if len(selected) >= max_per_lecture:
                break

    selected.sort(key=lambda c: c["cue_start"])

    # Attach context windows now that the final ordering is known.
    for idx, candidate in enumerate(selected):
        prev_text = selected[idx - 1]["cue_text"] if idx > 0 else ""
        next_text = selected[idx + 1]["cue_text"] if idx + 1 < len(selected) else ""
        candidate["context_before"] = compact_text(prev_text, 110)
        candidate["context_after"] = compact_text(next_text, 110)
        candidate["context"] = compact_text(
            " ".join(part for part in [candidate["context_before"], candidate["cue_text"], candidate["context_after"]] if part),
            260,
        )
        candidate["time"] = round((candidate["cue_start"] + candidate["cue_end"]) / 2, 1)

    return [
        {
            "time": candidate["time"],
            "reason": candidate["reason"],
            "reasons": candidate["reasons"],
            "hint": candidate["hint"],
            "text": candidate["text"],
            "cue_text": candidate["cue_text"],
            "context_before": candidate["context_before"],
            "context_after": candidate["context_after"],
            "context": candidate["context"],
            "cue_index": candidate["cue_index"],
            "cue_start": candidate["cue_start"],
            "cue_end": candidate["cue_end"],
            "duration": candidate["duration"],
            "position": candidate["position"],
            "score": candidate["score"],
        }
        for candidate in selected[:max_per_lecture]
    ]


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
        keyframes = infer_keyframes(cues, args.max_per_lecture, args.interval, args.lang)

        for kf in keyframes:
            entry = {
                "vtt": vtt_file.name,
                "time": kf["time"],
                "reason": kf["reason"],
                "reasons": kf.get("reasons", []),
                "hint": kf.get("hint", ""),
                "text": kf["text"],
                "cue_text": kf.get("cue_text", ""),
                "context_before": kf.get("context_before", ""),
                "context_after": kf.get("context_after", ""),
                "context": kf.get("context", ""),
                "cue_index": kf.get("cue_index"),
                "cue_start": kf.get("cue_start"),
                "cue_end": kf.get("cue_end"),
                "duration": kf.get("duration"),
                "position": kf.get("position"),
                "score": kf.get("score"),
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
