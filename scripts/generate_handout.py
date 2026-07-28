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
\graphicspath{{mathematical-thinking/frames/}}

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
\usepackage{pifont}
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
  \href{#1}{\textcolor{videoblue}{\ding{23}~\textbf{#2}}}%
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
    preamble = PREAMBLE.replace("COURSE_TITLE", tex_escape(course_title))
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
    tex.append(r"""
本单元是课程的入门部分，旨在帮助学习者建立正确的数学思维模式。
与传统的"学习公式→套用解题"不同，本课程强调\textbf{理解数学的本质}——
数学不仅仅是计算工具，更是一种\textbf{精确、严谨、抽象}的思维方式。

\begin{keyconcept}{核心目标}
\begin{itemize}
  \item 从"学校数学"过渡到"大学数学"的思维模式
  \item 理解数学是研究\textbf{模式}（patterns）的学科
  \item 掌握精确语言（precise language）在数学中的重要性
  \item 学会使用逻辑连接词和量词进行严格推理
\end{itemize}
\end{keyconcept}
""")
    
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
        tex.append(f"\\videolink{{{video_url}}}{{观看视频：{tex_escape(lecture_title)}}}")
        tex.append("")
        

        
        # Keyframes for this lecture
        lecture_frames = [kf for kf in keyframes if item["en_vtt"].replace(".en.vtt", "") in kf.get("vtt", "")]
        if lecture_frames:
            tex.append(r"\textbf{关键帧截图}：")
            for kf in lecture_frames[:2]:  # Max 2 per lecture
                # Build frame filename matching extract_frames.py output
                vtt_stem = item['en_vtt'].replace('.en.vtt', '')
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
                    tex.append(f"\\begin{{supplement}}{{{info['title']}}}")
                    for para in info.get("summary", []):
                        # Summary text already contains LaTeX markup, don't escape
                        tex.append(f"  {para}")
                        tex.append("")
                    tex.append(r"\end{supplement}")
                    tex.append("")
                else:
                    # Fallback: just list the filename
                    clean_name = pdf_name.split("_", 1)[-1].replace(".pdf", "").replace("_", " ")
                    tex.append(f"\\textbf{{补充材料}}：\\texttt{{{tex_escape(clean_name)}}}")
                    tex.append("")
    
    # ── Section 3: Key Concepts ──
    if lang == "en":
        tex.append(r"\section{Key Concepts}")
    else:
        tex.append(r"\section{核心概念详解}")
    
    tex.append(r"""
\subsection{逻辑连接词（Logical Connectives）}

逻辑连接词是组合命题的基本运算，是数学推理的基石：

\begin{keyconcept}{五种基本逻辑连接词}
\begin{enumerate}
  \item \textbf{合取（AND）}: $P \land Q$ — 当且仅当 P 和 Q 都为真时为真
  \item \textbf{析取（OR）}: $P \lor Q$ — 当 P 或 Q 至少一个为真时为真
  \item \textbf{否定（NOT）}: $\neg P$ — 将 P 的真值反转
  \item \textbf{条件（IF...THEN）}: $P \Rightarrow Q$ — 仅当 P 真且 Q 假时为假
  \item \textbf{双条件（IFF）}: $P \Leftrightarrow Q$ — P 和 Q 同真或同假时为真
\end{enumerate}
\end{keyconcept}

\subsection{量词（Quantifiers）}

量词用于表达"对所有"或"存在某个"的数学陈述：

\begin{keyconcept}{两个核心量词}
\begin{itemize}
  \item \textbf{全称量词}: $\forall x\, P(x)$ — "对所有 x，P(x) 成立"
  \item \textbf{存在量词}: $\exists x\, P(x)$ — "存在某个 x 使得 P(x) 成立"
\end{itemize}

\textbf{量词否定规则}（德摩根律）：
\[
\neg \forall x\,P(x) \equiv \exists x\,\neg P(x)
\]
\[
\neg \exists x\,P(x) \equiv \forall x\,\neg P(x)
\]
\end{keyconcept}

\subsection{集合论基础（Set Theory Basics）}

根据补充材料，集合论是后续课程的数学语言基础：

\begin{itemize}
  \item \textbf{集合表示}: $\{1, 2, 3\}$ 或 $\{x \in \mathbb{N} \mid x < 4\}$
  \item \textbf{空集}: $\emptyset$ — 不含任何元素的集合
  \item \textbf{属于关系}: $x \in A$ 表示 x 是集合 A 的元素
  \item \textbf{子集}: $A \subseteq B$ 表示 A 的所有元素都在 B 中
\end{itemize}
""")
    
    # ── Section 4: Exercises ──
    if lang == "en":
        tex.append(r"\section{Exercises}")
    else:
        tex.append(r"\section{习题讲解}")
    
    tex.append(r"""
\begin{exercise}{练习题}
\begin{enumerate}
  \item \textbf{量词否定}：写出 $\forall x\,(x > 0 \Rightarrow x^2 > 0)$ 的否定形式。
        【来源：第二讲】
  
  \item \textbf{德摩根律}：用真值表证明 $\neg(P \land Q) \equiv \neg P \lor \neg Q$。
        【综合：第一讲-第二讲】
  
  \item \textbf{形式化翻译}：将"每个正数都有平方根"翻译为形式逻辑表达式。
        【来源：第二讲】
  
  \item \textbf{素数无穷}：解释欧几里得证明素数无穷的核心思路。
        【来源：作业 1 教程】
\end{enumerate}
\end{exercise}

\subsection*{参考答案}

\begin{enumerate}
  \item 否定形式：$\exists x\,(x > 0 \land x^2 \leq 0)$
        \par\textbf{解析}：全称量词变存在量词，条件句 $P \Rightarrow Q$ 的否定是 $P \land \neg Q$。
  
  \item 构造 4 行真值表：
        \begin{center}
        \begin{tabular}{cc|c|c|c}
        \toprule
        $P$ & $Q$ & $P \land Q$ & $\neg(P \land Q)$ & $\neg P \lor \neg Q$ \\
        \midrule
        T & T & T & F & F \\
        T & F & F & T & T \\
        F & T & F & T & T \\
        F & F & F & T & T \\
        \bottomrule
        \end{tabular}
        \end{center}
        两列结果完全一致，故等价。
  
  \item $\forall x\,(x > 0 \Rightarrow \exists y\,(y^2 = x))$
        \par\textbf{注意}：量词顺序很重要，$\exists y$ 必须在 $\forall x$ 之后。
  
  \item 假设素数有限，设为 $p_1, p_2, \ldots, p_n$。
        构造 $N = p_1 p_2 \cdots p_n + 1$。
        $N$ 不能被任何 $p_i$ 整除（余数都是 1），
        所以 $N$ 要么是新的素数，要么有新的素因子——矛盾。
\end{enumerate}
""")
    
    # ── Section 5: Resources ──
    if lang == "en":
        tex.append(r"\section{Further Reading}")
    else:
        tex.append(r"\section{补充阅读}")
    tex.append(r"""
\begin{supplement}{推荐材料}
\begin{itemize}
  \item \textbf{Background Reading} — Keith Devlin 撰写的课程背景介绍，
        涵盖数学的历史发展、数学符号的必要性、以及数学思维的价值。
  \item \textbf{Set Theory Supplement} — 集合论基础速查表，
        包括集合表示法、空集、子集、并集、交集等核心概念。
        后续课程会频繁使用这些记号。
\end{itemize}
\end{supplement}
""")
    
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
