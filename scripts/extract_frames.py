#!/usr/bin/env python3
"""
extract_frames.py — Extract video frames at keyframe timestamps.

Reads a keyframes.json (produced by vtt_keyframes.py) and uses ffmpeg
to extract one frame per timestamp from the corresponding video file.

Usage:
    python3 extract_frames.py \
        --video-dir ./module-1 \
        --keyframes ./module-1/keyframes.json \
        --output ./module-1/frames/

    python3 extract_frames.py \
        --video-dir ./module-1 \
        --keyframes ./module-1/keyframes.json \
        --output ./module-1/frames/ \
        --format jpg --width 1280 --quality 2
"""

import argparse
import json
import re
import sys
from pathlib import Path
from subprocess import run, PIPE


def seconds_to_label(sec: float) -> str:
    """Convert seconds to a human-readable label like 01h02m30s or 0045s."""
    sec = int(sec)
    if sec >= 3600:
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        return f"{h:02d}h{m:02d}m{s:02d}s"
    elif sec >= 60:
        m = sec // 60
        s = sec % 60
        return f"{m:02d}m{s:02d}s"
    else:
        return f"{sec:04d}s"


def sanitize_filename(name: str) -> str:
    """Remove characters that are problematic in filenames."""
    return re.sub(r'[^\w\u4e00-\u9fff\-]', '', name).strip()[:40]


def extract_frame(video_path: Path, time_sec: float, output_path: Path,
                  fmt: str = "png", width: int = 0, quality: int = 2):
    """Extract a single frame from a video at the given timestamp."""
    cmd = ["ffmpeg", "-y", "-ss", str(time_sec), "-i", str(video_path)]

    if width > 0:
        cmd += ["-vf", f"scale={width}:-1"]

    cmd += ["-frames:v", "1"]

    if fmt == "jpg":
        cmd += ["-q:v", str(quality)]
    # png is lossless, no quality flag needed

    cmd.append(str(output_path))

    result = run(cmd, stdout=PIPE, stderr=PIPE, timeout=30)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Extract video frames at keyframe timestamps."
    )
    parser.add_argument("--video-dir", required=True, help="Directory with video files")
    parser.add_argument("--keyframes", required=True, help="Path to keyframes.json")
    parser.add_argument("--output", required=True, help="Output directory for frames")
    parser.add_argument("--format", default="png", choices=["png", "jpg"],
                        help="Output image format (default: png)")
    parser.add_argument("--width", type=int, default=0,
                        help="Scale width (0 = original size)")
    parser.add_argument("--quality", type=int, default=2,
                        help="JPEG quality 1-31, lower = better (default: 2)")
    args = parser.parse_args()

    video_dir = Path(args.video_dir)
    keyframes_path = Path(args.keyframes)
    output_dir = Path(args.output)

    if not video_dir.is_dir():
        print(f"Error: {video_dir} is not a directory", file=sys.stderr)
        sys.exit(1)
    if not keyframes_path.exists():
        print(f"Error: {keyframes_path} not found", file=sys.stderr)
        sys.exit(1)

    keyframes = json.loads(keyframes_path.read_text(encoding="utf-8"))
    if not keyframes:
        print("Warning: keyframes.json is empty, nothing to extract", file=sys.stderr)
        sys.exit(0)

    output_dir.mkdir(parents=True, exist_ok=True)

    ext = "jpg" if args.format == "jpg" else "png"
    success = 0
    failed = 0

    # Group by video file for cleaner naming
    for i, kf in enumerate(keyframes):
        video_name = kf.get("video")
        time_sec = kf["time"]
        reason = kf.get("reason", "frame")
        text = kf.get("text", "")

        if not video_name:
            # Try to infer from vtt filename
            vtt_name = kf.get("vtt", "")
            base = re.sub(r"\.(en|zh-CN|zh-TW|ja|ko|fr|de|es|pt|ar)$", "", vtt_name)
            # Find matching video
            prefix = base.split("_")[0] if "_" in base else base[:2]
            matches = sorted(video_dir.glob(f"{prefix}*.mp4"))
            if matches:
                video_name = matches[0].name
            else:
                print(f"  Skip: no video found for {vtt_name}", file=sys.stderr)
                failed += 1
                continue

        video_path = video_dir / video_name
        if not video_path.exists():
            print(f"  Skip: {video_path} not found", file=sys.stderr)
            failed += 1
            continue

        # Build output filename: 01_lecture_0045s_definition.png
        video_stem = video_path.stem
        time_label = seconds_to_label(time_sec)
        reason_label = sanitize_filename(reason)
        out_name = f"{video_stem}_{time_label}_{reason_label}.{ext}"
        out_path = output_dir / out_name

        ok = extract_frame(video_path, time_sec, out_path,
                          fmt=args.format, width=args.width, quality=args.quality)

        if ok and out_path.exists() and out_path.stat().st_size > 0:
            size_kb = out_path.stat().st_size / 1024
            print(f"  [{i+1}/{len(keyframes)}] {out_name} ({size_kb:.0f}K)")
            success += 1
        else:
            print(f"  [{i+1}/{len(keyframes)}] FAILED: {out_name}", file=sys.stderr)
            failed += 1

    print(f"\nDone: {success} frames extracted, {failed} failed")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
