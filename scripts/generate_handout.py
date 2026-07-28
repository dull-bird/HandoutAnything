#!/usr/bin/env python3
"""
generate_handout.py — Generate a polished LaTeX handout from downloaded MOOC materials.

This script is the final step of the mooc2handout pipeline. It reads:
  - VTT subtitles (for lecture content)
  - Supplementary PDFs (extracted text)
  - Keyframe screenshots (for visual references)
  - keyframes.json (for timestamp metadata)

And produces a publication-quality LaTeX handout with:
  - Beautiful typographic design
  - Video links with ▶ symbol for each lecture
  - Bold key concepts
  - Supplementary material summaries
  - Exercise walkthroughs
  - Keyframe screenshots embedded

Usage:
    python3 generate_handout.py \
        --data-dir /tmp/mooc-demo/mathematical-thinking \
        --course-title "Mathematical Thinking" \
        --unit-title "Module 1: Introduction" \
        --instructor "Keith Devlin" \
        --output handout.tex

    # Then compile:
    xelatex handout.tex && xelatex handout.tex
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ── LaTeX Template ────────────────────────────────────────────────────────────

PREAMBLE = r"""\documentclass[UTF8,a4paper,11pt]{ctexart}

% ── Page geometry ──
\usepackage[margin=2.2cm,top=2.5cm,bottom=2.5cm]{geometry}

% ── Typography ──
\usepackage{fontspec}
\usepackage{setspace}
\setstretch{1.2}

% ── Graphics ──
\usepackage{graphicx}
\graphicspath{{FRAMES_DIR/}}

% ── Colors ──
\usepackage{xcolor}
\definecolor{accent}{HTML}{1a73e8}
\definecolor{darkgray}{HTML}{333333}
\definecolor{lightgray}{HTML}{f5f5f5}
\definecolor{keyframebg}{HTML}{fafafa}
\definecolor{videoblue}{HTML}{065fd4}
\definecolor{notebg}{HTML}{e8f0fe}
\definecolor{warnbg}{HTML}{fef7e0}

% ── Links ──
\usepackage{hyperref}
\hypersetup{
  colorlinks=true,
  linkcolor=accent,
  urlcolor=videoblue,
  citecolor=accent,
  pdftitle={COURSE_TITLE},
  pdfauthor={INSTRUCTOR}
}

% ── Layout ──
\usepackage{enumitem}
\setlist[itemize]{leftmargin=1.8em,itemsep=2pt}
\setlist[enumerate]{leftmargin=1.8em,itemsep=2pt}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{tcolorbox}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{lastpage}
\usepackage{amssymb}

% ── Header/Footer ──
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textcolor{darkgray}{COURSE_TITLE}}
\fancyhead[R]{\small\textcolor{darkgray}{UNIT_TITLE}}
\fancyfoot[C]{\small\textcolor{darkgray}{\thepage\ / \pageref{LastPage}}}
\renewcommand{\headrulewidth}{0.4pt}

% ── Section styling ──
\titleformat{\section}
  {\Large\bfseries\color{accent}}
  {\thesection}{1em}{}
\titleformat{\subsection}
  {\large\bfseries\color{darkgray}}
  {\thesubsection}{1em}{}

% ── Custom environments ──
\newtcolorbox{keyconcept}{
  colback=notebg, colframe=accent,
  fonttitle=\bfseries, boxrule=0.5pt,
  left=8pt, right=8pt, top=6pt, bottom=6pt
}
\newtcolorbox{supplement}{
  colback=lightgray, colframe=darkgray,
  fonttitle=\bfseries, boxrule=0.3pt,
  left=8pt, right=8pt, top=6pt, bottom=6pt
}
\newtcolorbox{exercise}{
  colback=warnbg, colframe=orange,
  fonttitle=\bfseries, boxrule=0.5pt,
  left=8pt, right=8pt, top=6pt, bottom=6pt
}

% ── Video link command ──
\newcommand{\videolink}[2]{%
  \href{#1}{\textcolor{videoblue}{\textbf{#2}}}%
}

% ── Keyframe figure command ──
\newcommand{\keyframe}[2]{%
  \begin{center}
    \fcolorbox{lightgray}{keyframebg}{%
      \includegraphics[width=0.75\linewidth]{#1}%
    }
    \par\vspace{2pt}
    {\small\textcolor{darkgray}{#2}}
  \end{center}
}

\begin{document}
"""

TITLE_PAGE = r"""
\begin{center}
  \vspace*{2cm}
  {\Huge\bfseries\color{accent} COURSE_TITLE_CN}\\[0.3cm]
  {\small\textcolor{darkgray}{COURSE_TITLE_EN}}\\[0.8cm]
  {\LARGE UNIT_TITLE_CN}\\[0.3cm]
  {\small\textcolor{darkgray}{UNIT_TITLE_EN}}\\[1.2cm]
  {\large 授课教师：INSTRUCTOR}\\[0.5cm]
  {\large\textcolor{darkgray}{由 mooc2handout 自动生成}}\\[0.3cm]
  {\small\textcolor{darkgray}{DATE}}
  \vfill
  {\small 本讲义由课程字幕、补充材料与 AI 推断关键帧自动生成。}
\end{center}
\newpage
"""

TOC = r"""
\tableofcontents
\newpage
"""


# ── Content extraction ────────────────────────────────────────────────────────

def extract_vtt_text(vtt_path: Path) -> str:
    """Extract clean text from a VTT file."""
    text = vtt_path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"WEBVTT.*?\n\n", "", text, flags=re.DOTALL)
    text = re.sub(r"\d{1,2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}\.\d{3}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return " ".join(lines)


def extract_pdf_text(pdf_path: Path, max_pages: int = 5) -> str:
    """Extract text from a PDF file."""
    try:
        import pdfplumber
        texts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:max_pages]:
                t = page.extract_text()
                if t:
                    texts.append(t)
        return "\n\n".join(texts)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def tex_escape(text: str) -> str:
    """Escape special LaTeX characters."""
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


# ── Handout generation ────────────────────────────────────────────────────────

def generate_handout(
    data_dir: Path,
    course_title: str,
    unit_title: str,
    instructor: str,
    output: Path,
    course_title_en: str = "",
    unit_title_en: str = "",
    lang: str = "zh",
):
    """Generate a complete LaTeX handout."""
    
    # Load manifest
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"Error: {manifest_path} not found", file=sys.stderr)
        sys.exit(1)
    
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    # Load keyframes
    keyframes_path = data_dir / "keyframes.json"
    keyframes = []
    if keyframes_path.exists():
        keyframes = json.loads(keyframes_path.read_text(encoding="utf-8"))
    
    # Build LaTeX
    tex = []
    
    # Preamble
    # Set frames directory (relative to where xelatex runs)
    frames_dir = data_dir / "frames"
    preamble = PREAMBLE.replace("FRAMES_DIR", str(frames_dir))
    preamble = preamble.replace("COURSE_TITLE", tex_escape(course_title))
    preamble = preamble.replace("UNIT_TITLE", tex_escape(unit_title))
    preamble = preamble.replace("INSTRUCTOR", tex_escape(instructor))
    tex.append(preamble)
    
    # Title page
    if lang == "en":
        # English mode: no secondary subtitle
        title = TITLE_PAGE.replace("COURSE_TITLE_CN", tex_escape(course_title_en or course_title))
        title = title.replace("COURSE_TITLE_EN", "")
        title = title.replace("UNIT_TITLE_CN", tex_escape(unit_title_en or unit_title))
        title = title.replace("UNIT_TITLE_EN", "")
        # Remove the empty small lines
        title = title.replace(r"{\small\textcolor{darkgray}{}}\\[0.8cm]", "")
        title = title.replace(r"{\small\textcolor{darkgray}{}}\\[1.2cm]", "")
    else:
        # Chinese mode: primary CN + secondary EN
        title = TITLE_PAGE.replace("COURSE_TITLE_CN", tex_escape(course_title))
        title = title.replace("COURSE_TITLE_EN", tex_escape(course_title_en or course_title))
        title = title.replace("UNIT_TITLE_CN", tex_escape(unit_title))
        title = title.replace("UNIT_TITLE_EN", tex_escape(unit_title_en or unit_title))
    title = title.replace("INSTRUCTOR", tex_escape(instructor))
    title = title.replace("DATE", r"\today")
    tex.append(title)
    
    # TOC
    tex.append(TOC)
    
    # ── Section 1: Overview ──
    if lang == "en":
        tex.append(r"\section{Overview}")
    else:
        tex.append(r"\section{单元概览}")
    
    # Read overview from content.json
    content_json_path = data_dir / "content.json"
    content_data = {}
    if content_json_path.exists():
        content_data = json.loads(content_json_path.read_text(encoding="utf-8"))
    
    overview = content_data.get("overview", "")
    if overview:
        tex.append(overview)
    else:
        if lang == "en":
            tex.append(r"This unit covers the core concepts of the course. Key topics are summarized below with video references and keyframe screenshots.")
        else:
            tex.append(r"本单元涵盖课程的核心概念。以下按讲次列出要点，附带视频链接与关键帧截图。")
    tex.append("")
    
    # ── Section 2: Lectures ──
    if lang == "en":
        tex.append(r"\section{Lecture Notes}")
    else:
        tex.append(r"\section{课程讲义}")
    
    for i, item in enumerate(manifest):
        lecture_title = item["title"]
        lecture_num = item["number"]
        
        # Video link
        video_url = item.get("page_url", "https://www.coursera.org/learn/mathematical-thinking")
        
        tex.append(f"\\subsection{{{tex_escape(lecture_title)}}}")
        duration = item.get("duration", "")
        dur_str = f"（{duration}）" if duration else ""
        if lang == "en":
            tex.append(f"\\videolink{{{video_url}}}{{Watch: {tex_escape(lecture_title)}}}{dur_str}")
        else:
            tex.append(f"\\videolink{{{video_url}}}{{观看视频：{tex_escape(lecture_title)}}}{dur_str}")
        tex.append("")
        

        
        # Keyframes for this lecture
        # Match keyframes by video filename stem (language-agnostic)
        video_stem = item.get("video", "").replace(".mp4", "") if item.get("video") else ""
        vtt_stem_base = re.sub(r"\.(en|zh-CN|zh-TW|ja|ko|fr|de|es|pt|ar)$", "", item["en_vtt"].replace(".vtt", ""))
        lecture_frames = [kf for kf in keyframes if (video_stem and video_stem in kf.get("video", "")) or (vtt_stem_base and vtt_stem_base in kf.get("vtt", ""))]
        if lecture_frames:
            tex.append(r"\textbf{关键帧截图}：")
            for kf in lecture_frames[:2]:  # Max 2 per lecture
                # Build frame filename matching extract_frames.py output
                vtt_stem = re.sub(r"\.(en|zh-CN|zh-TW|ja|ko|fr|de|es|pt|ar)$", "", item['en_vtt'].replace('.vtt', ''))
                time_label = f"{int(kf['time']):04d}s" if kf['time'] < 60 else f"{int(kf['time'])//60:02d}m{int(kf['time'])%60:02d}s"
                frame_file = f"{vtt_stem}_{time_label}_{kf['reason']}.png"
                # Check if frame exists
                frame_path = data_dir / "frames" / frame_file
                if frame_path.exists():
                    reason_map = {
                        'concept_shift': '概念转折',
                        'definition': '核心定义',
                        'example': '示例讲解',
                        'summary': '总结回顾',
                        'interval': '内容节选',
                    }
                    reason_cn = reason_map.get(kf['reason'], kf['reason'])
                    caption = f"时间戳 {int(kf['time'])}s — {reason_cn}"
                    tex.append(f"\\keyframe{{{frame_file}}}{{{caption}}}")
            tex.append("")
        
        # Supplementary materials — read from supplements.json (AI-summarized)
        if item.get("resources"):
            supplements_path = data_dir / "supplements.json"
            supplements_data = {}
            if supplements_path.exists():
                supplements_data = json.loads(supplements_path.read_text(encoding="utf-8"))
            for pdf_name in item["resources"]:
                if pdf_name in supplements_data:
                    info = supplements_data[pdf_name]
                    # Title outside the box
                    tex.append(f"\\textbf{{📎 {info['title']}}}")
                    escaped_name = tex_escape(pdf_name)
                    tex.append(f"\\hfill{{\\small\\texttt{{{escaped_name}}}}}")
                    tex.append("")
                    # Content inside the box with bullets
                    tex.append(r"\begin{supplement}{内容摘要}")
                    tex.append(r"\begin{itemize}")
                    for para in info.get("summary", []):
                        tex.append(f"  \\item {para}")
                    tex.append(r"\end{itemize}")
                    tex.append(r"\end{supplement}")
                    tex.append("")
                else:
                    # Fallback: just list the filename
                    clean_name = pdf_name.split("_", 1)[-1].replace(".pdf", "").replace("_", " ")
                    tex.append(f"\\textbf{{补充材料}}：\\texttt{{{tex_escape(clean_name)}}}")
                    tex.append("")
    
    # ── Section 3: Key Concepts ──
    key_concepts = content_data.get("key_concepts", "")
    if key_concepts:
        if lang == "en":
            tex.append(r"\section{Key Concepts}")
        else:
            tex.append(r"\section{核心概念详解}")
        tex.append(key_concepts)
        tex.append("")
    
    # ── Section 4: Exercises ──
    exercises = content_data.get("exercises", "")
    if exercises:
        if lang == "en":
            tex.append(r"\section{Exercises}")
        else:
            tex.append(r"\section{习题讲解}")
        tex.append(exercises)
        tex.append("")
    
    # ── Section 5: Resources ──
    further_reading = content_data.get("further_reading", "")
    if further_reading:
        if lang == "en":
            tex.append(r"\section{Further Reading}")
        else:
            tex.append(r"\section{补充阅读}")
        tex.append(further_reading)
        tex.append("")
    
    # End document
    tex.append(r"\end{document}")
    
    # Write output
    output.write_text("\n".join(tex), encoding="utf-8")
    print(f"Generated: {output}")
    print(f"  Lectures: {len(manifest)}")
    print(f"  Keyframes: {len(keyframes)}")
    print(f"  Compile with: xelatex {output.name} && xelatex {output.name}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a polished LaTeX handout.")
    parser.add_argument("--data-dir", required=True, help="Directory with VTT/PDF/frames")
    parser.add_argument("--course-title", required=True, help="Course title (primary language)")
    parser.add_argument("--unit-title", required=True, help="Unit title (primary language)")
    parser.add_argument("--course-title-en", default="", help="Course title (English, shown smaller in zh mode)")
    parser.add_argument("--unit-title-en", default="", help="Unit title (English, shown smaller in zh mode)")
    parser.add_argument("--instructor", default="")
    parser.add_argument("--lang", default="zh", choices=["zh", "en"], help="Output language (default: zh)")
    parser.add_argument("--output", required=True, help="Output .tex file")
    args = parser.parse_args()
    
    generate_handout(
        data_dir=Path(args.data_dir),
        course_title=args.course_title,
        unit_title=args.unit_title,
        instructor=args.instructor,
        output=Path(args.output),
        course_title_en=args.course_title_en,
        unit_title_en=args.unit_title_en,
        lang=args.lang,
    )


if __name__ == "__main__":
    main()
