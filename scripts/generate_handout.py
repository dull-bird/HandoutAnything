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
    insert_keyframes: bool = False,
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
    
    # ── Load content.json ──
    content_json_path = data_dir / "content.json"
    content_data = {}
    if content_json_path.exists():
        content_data = json.loads(content_json_path.read_text(encoding="utf-8"))

    # ── Knowledge Map ──
    knowledge_map = content_data.get("knowledge_map", [])
    if knowledge_map:
        if lang == "en":
            tex.append(r"\section*{Knowledge Map}")
        else:
            tex.append(r"\section*{本单元知识地图}")
        tex.append(r"\begin{longtable}{p{3.1cm}p{10.2cm}}")
        tex.append(r"\toprule")
        if lang == "en":
            tex.append(r"Topic & Core Question \\")
        else:
            tex.append(r"主题 & 核心问题 \\")
        tex.append(r"\midrule")
        for row in knowledge_map:
            topic = row.get("topic", "")
            question = row.get("question", "")
            tex.append(f"{topic} & {question} \\\\")
        tex.append(r"\bottomrule")
        tex.append(r"\end{longtable}")
        tex.append("")

    # ── Section 0: Overview ──
    overview = content_data.get("overview", "")
    if lang == "en":
        tex.append(r"\section*{0. Overview}")
    else:
        tex.append(r"\section*{0. 概要}")
    if overview:
        tex.append(overview)
    else:
        if lang == "en":
            tex.append(r"This unit covers the core concepts of the course.")
        else:
            tex.append(r"本单元涵盖课程的核心概念。")
    tex.append("")

    # ── Per-lecture sections ──
    lecture_summaries = content_data.get("lectures", {})
    for i, item in enumerate(manifest):
        lecture_title = item["title"]
        section_num = i + 1

        tex.append(f"\\section*{{{section_num}. {tex_escape(lecture_title)}}}")

        # Video link with duration
        video_url = item.get("page_url", "")
        duration = item.get("duration", "")
        dur_str = f"（{duration}）" if duration else ""
        if video_url:
            if lang == "en":
                tex.append(f"\\noindent\\textbf{{Review: }}\\videolink{{{video_url}}}{{{tex_escape(lecture_title)}}}{dur_str}")
            else:
                tex.append(f"\\noindent\\textbf{{回看：}}\\videolink{{{video_url}}}{{{tex_escape(lecture_title)}}}{dur_str}")
        tex.append("")

        # Per-lecture content from content.json
        video_stem_key = item.get("video", "").replace(".mp4", "") if item.get("video") else ""
        vtt_stem_key = re.sub(r"\.(en|zh-CN|zh-TW|ja|ko|fr|de|es|pt|ar)$", "", item["en_vtt"].replace(".vtt", ""))
        lecture_content = lecture_summaries.get(video_stem_key) or lecture_summaries.get(vtt_stem_key) or ""
        if lecture_content:
            tex.append(lecture_content)
            tex.append("")

        # Supplementary materials
        if item.get("resources"):
            supplements_path = data_dir / "supplements.json"
            supplements_data = {}
            if supplements_path.exists():
                supplements_data = json.loads(supplements_path.read_text(encoding="utf-8"))
            for res_name in item["resources"]:
                if res_name in supplements_data:
                    info = supplements_data[res_name]
                    tex.append(f"\\textbf{{📎 {info['title']}}}")
                    escaped_name = tex_escape(res_name)
                    tex.append(f"\\hfill{{\\small\\texttt{{{escaped_name}}}}}")
                    tex.append("")
                    tex.append(r"\begin{supplement}{内容摘要}")
                    tex.append(r"\begin{itemize}")
                    for para in info.get("summary", []):
                        tex.append(f"  \\item {para}")
                    tex.append(r"\end{itemize}")
                    tex.append(r"\end{supplement}")
                    tex.append("")
                else:
                    clean_name = res_name.split("_", 1)[-1] if "_" in res_name else res_name
                    tex.append(f"\\textbf{{补充材料}}：\\texttt{{{tex_escape(clean_name)}}}")
                    tex.append("")

        # Keyframes (optional)
        if insert_keyframes:
            video_stem = item.get("video", "").replace(".mp4", "") if item.get("video") else ""
            lecture_frames = [kf for kf in keyframes if (video_stem and video_stem in kf.get("video", "")) or (vtt_stem_key and vtt_stem_key in kf.get("vtt", ""))]
            if lecture_frames:
                reason_map = {
                    'concept_shift': '概念转折', 'definition': '核心定义',
                    'example': '示例讲解', 'summary': '总结回顾', 'interval': '内容节选',
                }
                for kf in lecture_frames[:2]:
                    time_label = f"{int(kf['time']):04d}s" if kf['time'] < 60 else f"{int(kf['time'])//60:02d}m{int(kf['time'])%60:02d}s"
                    frame_file = f"{vtt_stem_key}_{time_label}_{kf['reason']}.png"
                    frame_path = data_dir / "frames" / frame_file
                    if frame_path.exists():
                        reason_cn = reason_map.get(kf['reason'], kf['reason'])
                        caption = f"时间戳 {int(kf['time'])}s — {reason_cn}"
                        tex.append(f"\\keyframe{{{frame_file}}}{{{caption}}}")
                tex.append("")

    # ── Key Takeaways ──
    key_takeaways = content_data.get("key_takeaways", [])
    if key_takeaways:
        takeaway_num = len(manifest) + 1
        if lang == "en":
            tex.append(f"\\section*{{{takeaway_num}. Key Takeaways}}")
        else:
            n = len(key_takeaways)
            cn_num = {3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}.get(n, str(n))
            tex.append(f"\\section*{{{takeaway_num}. 本单元最该记住的{cn_num}句话}}")
        tex.append(r"\begin{enumerate}")
        for t in key_takeaways:
            tex.append(f"  \\item {t}")
        tex.append(r"\end{enumerate}")
        tex.append("")

    # ── Exercises ──
    exercises = content_data.get("exercises", {})
    answers = content_data.get("answers", {})
    if exercises:
        ex_num = len(manifest) + (2 if key_takeaways else 1)
        if lang == "en":
            tex.append(f"\\section*{{{ex_num}. Exercises}}")
        else:
            tex.append(f"\\section*{{{ex_num}. 练习题}}")

        # A. Multiple choice
        choice = exercises.get("choice", [])
        if choice:
            if lang == "en":
                tex.append(f"\\subsection*{{A. Multiple Choice ({len(choice)} questions)}}")
            else:
                tex.append(f"\\subsection*{{A. 选择题（{len(choice)}题）}}")
            tex.append(r"\begin{enumerate}")
            for q in choice:
                tex.append(f"  \\item {q['q']}\\\\")
                options = " \\quad ".join(q.get("options", []))
                tex.append(f"  {options}")
                tex.append("")
            tex.append(r"\end{enumerate}")
            tex.append("")

        # B. True/False
        truefalse = exercises.get("truefalse", [])
        if truefalse:
            if lang == "en":
                tex.append(f"\\subsection*{{B. True/False ({len(truefalse)} questions)}}")
            else:
                tex.append(f"\\subsection*{{B. 判断题（{len(truefalse)}题）}}")
            tex.append(r"\begin{enumerate}")
            for q in truefalse:
                tex.append(f"  \\item {q}（\\quad）")
            tex.append(r"\end{enumerate}")
            tex.append("")

        # C. Short answer
        shortanswer = exercises.get("shortanswer", [])
        if shortanswer:
            if lang == "en":
                tex.append(f"\\subsection*{{C. Short Answer ({len(shortanswer)} questions)}}")
            else:
                tex.append(f"\\subsection*{{C. 简答题（{len(shortanswer)}题）}}")
            tex.append(r"\begin{enumerate}")
            for q in shortanswer:
                tex.append(f"  \\item {q}")
            tex.append(r"\end{enumerate}")
            tex.append("")

    # ── Answers ──
    if answers:
        ans_num = len(manifest) + (3 if key_takeaways else 2)
        if lang == "en":
            tex.append(f"\\section*{{{ans_num}. Answer Key}}")
        else:
            tex.append(f"\\section*{{{ans_num}. 参考答案}}")

        if answers.get("choice"):
            if lang == "en":
                tex.append(r"\subsection*{Multiple Choice}")
            else:
                tex.append(r"\subsection*{选择题答案}")
            tex.append(answers["choice"])
            tex.append("")

        if answers.get("truefalse"):
            if lang == "en":
                tex.append(r"\subsection*{True/False}")
            else:
                tex.append(r"\subsection*{判断题答案}")
            tex.append(answers["truefalse"])
            tex.append("")

        if answers.get("shortanswer"):
            if lang == "en":
                tex.append(r"\subsection*{Short Answer Key Points}")
            else:
                tex.append(r"\subsection*{简答题要点}")
            tex.append(r"\begin{enumerate}")
            for a in answers["shortanswer"]:
                tex.append(f"  \\item {a}")
            tex.append(r"\end{enumerate}")
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
    parser.add_argument("--keyframes", action="store_true", default=False, help="Insert keyframe screenshots (default: off)")
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
        insert_keyframes=args.keyframes,
    )


if __name__ == "__main__":
    main()
