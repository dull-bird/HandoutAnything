#!/usr/bin/env python3
import argparse
import json
from collections import OrderedDict
from pathlib import Path


def group_lectures(manifest):
    groups = OrderedDict()
    for item in manifest:
        lesson = item.get("lesson", "未命名小节")
        groups.setdefault(lesson, []).append(item)
    return groups


def tex_escape(text):
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


def main():
    parser = argparse.ArgumentParser(description="Create a LaTeX handout scaffold from Coursera subtitle metadata.")
    parser.add_argument("--subtitle-dir", required=True)
    parser.add_argument("--course-title", required=True)
    parser.add_argument("--unit-title", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--abstract", default="本讲义由字幕稿整理而成，重点保留课程主线、关键概念与可回看的视频链接。")
    args = parser.parse_args()

    subtitle_dir = Path(args.subtitle_dir)
    manifest_path = subtitle_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    groups = group_lectures(manifest)

    out = []
    out.append(r"\documentclass[UTF8,a4paper,12pt]{ctexart}")
    out.append(r"\usepackage{geometry}")
    out.append(r"\geometry{margin=2.4cm}")
    out.append(r"\usepackage{hyperref}")
    out.append(r"\usepackage{longtable}")
    out.append(r"\usepackage{booktabs}")
    out.append(r"\usepackage{enumitem}")
    out.append(r"\usepackage{setspace}")
    out.append(r"\setstretch{1.15}")
    out.append(r"\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}")
    out.append(r"\setlist[itemize]{leftmargin=2em}")
    out.append(r"\setlist[enumerate]{leftmargin=2em}")
    out.append(r"\pagestyle{plain}")
    out.append("")
    out.append(rf"\title{{\heiti {tex_escape(args.course_title)}\\{tex_escape(args.unit_title)}}}")
    out.append(r"\author{}")
    out.append(r"\date{}")
    out.append("")
    out.append(r"\begin{document}")
    out.append(r"\maketitle")
    out.append("")
    out.append(r"\begin{abstract}")
    out.append(tex_escape(args.abstract))
    out.append(r"\end{abstract}")
    out.append("")
    out.append(r"\section*{本单元知识地图}")
    out.append(r"\begin{longtable}{p{4cm}p{9cm}}")
    out.append(r"\toprule")
    out.append(r"小节 & 回看视频 \\")
    out.append(r"\midrule")
    for lesson, lectures in groups.items():
        titles = [rf"\href{{{item['page_url']}}}{{{tex_escape(item['title'])}}}" for item in lectures]
        out.append(rf"{tex_escape(lesson)} & " + r"；".join(titles) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{longtable}")
    out.append("")
    out.append(r"\section*{一、单元总览}")
    out.append(r"这里写单元主线，先给读者一个全局判断，再进入细节。")
    out.append("")
    out.append(r"\section*{二、核心概念}")
    out.append(r"\subsection*{1. 概念A}")
    out.append(r"\begin{itemize}")
    out.append(r"\item 特征1")
    out.append(r"\item 特征2")
    out.append(r"\end{itemize}")
    out.append("")
    out.append(r"\subsection*{2. 概念B}")
    out.append(r"\begin{enumerate}")
    out.append(r"\item 第一步")
    out.append(r"\item 第二步")
    out.append(r"\end{enumerate}")
    out.append("")
    out.append(r"\section*{三、练习题}")
    out.append(r"\begin{enumerate}")
    out.append(r"\item 题干示例【来源：第三节】")
    out.append(r"\item 题干示例【综合：第二节-第四节】")
    out.append(r"\end{enumerate}")
    out.append("")
    out.append(r"\section*{附录：参考答案}")
    out.append(r"\begin{itemize}")
    out.append(r"\item 按题型给出简洁答案要点。")
    out.append(r"\end{itemize}")
    out.append(r"\end{document}")

    Path(args.output).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote scaffold to {args.output}")


if __name__ == "__main__":
    main()
