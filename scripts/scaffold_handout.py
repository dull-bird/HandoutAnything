#!/usr/bin/env python3
import argparse
import json
import re
from collections import OrderedDict
from pathlib import Path


TEXT = {
    "zh": {
        "docclass": r"\documentclass[UTF8,a4paper,12pt]{ctexart}",
        "abstract": "本讲义由字幕稿整理而成，重点保留课程主线、关键概念与可回看的视频链接。",
        "knowledge_map": "本单元知识地图",
        "lesson": "小节",
        "video": "回看视频",
        "overview": "一、单元总览",
        "overview_body": "这里写单元主线，先给读者一个全局判断，再进入细节。",
        "concepts": "二、核心概念",
        "exercise": "三、练习题",
        "answers": "附录：参考答案",
        "concept_a": "概念A",
        "concept_b": "概念B",
        "feature_1": "特征1",
        "feature_2": "特征2",
        "step_1": "第一步",
        "step_2": "第二步",
        "prompt_1": "题干示例【来源：第三节】",
        "prompt_2": "题干示例【综合：第二节-第四节】",
        "answer_note": "按题型给出简洁答案要点。",
    },
    "en": {
        "docclass": r"\documentclass[a4paper,12pt]{article}",
        "abstract": "This handout is organized from the captions and keeps the main line of the unit, the key concepts, and reviewable video links.",
        "knowledge_map": "Unit Knowledge Map",
        "lesson": "Section",
        "video": "Review Video",
        "overview": "1. Unit Overview",
        "overview_body": "Write the main line of the unit here, give readers a global view first, then move into details.",
        "concepts": "2. Core Concepts",
        "exercise": "3. Exercises",
        "answers": "Appendix: Answer Key",
        "concept_a": "Concept A",
        "concept_b": "Concept B",
        "feature_1": "Feature 1",
        "feature_2": "Feature 2",
        "step_1": "Step 1",
        "step_2": "Step 2",
        "prompt_1": "Sample prompt [Source: Section 3]",
        "prompt_2": "Sample prompt [Combined: Section 2-4]",
        "answer_note": "Give concise answer points by question type.",
    },
}


def group_lectures(manifest, lang):
    groups = OrderedDict()
    for item in manifest:
        lesson = item.get("lesson_en", item.get("lesson", "Untitled section")) if lang == "en" else item.get("lesson", "未命名小节")
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


def get_text(lang, key):
    return TEXT[lang][key]


def main():
    parser = argparse.ArgumentParser(description="Create a LaTeX handout scaffold from Coursera subtitle metadata.")
    parser.add_argument("--subtitle-dir", required=True)
    parser.add_argument("--course-title", required=True)
    parser.add_argument("--unit-title", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    parser.add_argument("--abstract", default="")
    args = parser.parse_args()

    subtitle_dir = Path(args.subtitle_dir)
    manifest_path = subtitle_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if args.lang == "en":
        if any(re.search(r"[\u4e00-\u9fff]", item.get("title", "")) and not item.get("title_en") for item in manifest):
            raise SystemExit("English scaffolds require English lecture titles in manifest.json")
        if any(re.search(r"[\u4e00-\u9fff]", item.get("lesson", "")) and not item.get("lesson_en") for item in manifest):
            raise SystemExit("English scaffolds require English lesson names in manifest.json")
    groups = group_lectures(manifest, args.lang)
    text = TEXT[args.lang]

    out = []
    out.append(text["docclass"])
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
    if args.lang == "en":
        out.append(r"\renewcommand{\contentsname}{Contents}")
    out.append("")
    if args.lang == "en":
        out.append(rf"\title{{{tex_escape(args.course_title)}\\{tex_escape(args.unit_title)}}}")
    else:
        out.append(rf"\title{{\heiti {tex_escape(args.course_title)}\\{tex_escape(args.unit_title)}}}")
    out.append(r"\author{}")
    out.append(r"\date{}")
    out.append("")
    out.append(r"\begin{document}")
    out.append(r"\maketitle")
    out.append("")
    out.append(r"\begin{abstract}")
    out.append(tex_escape(args.abstract or text["abstract"]))
    out.append(r"\end{abstract}")
    out.append("")
    out.append(rf"\section*{{{get_text(args.lang, 'knowledge_map')}}}")
    out.append(r"\begin{longtable}{p{4cm}p{9cm}}")
    out.append(r"\toprule")
    out.append(rf"{get_text(args.lang, 'lesson')} & {get_text(args.lang, 'video')} \\")
    out.append(r"\midrule")
    for lesson, lectures in groups.items():
        titles = [
            rf"\href{{{item['page_url']}}}{{{tex_escape(item.get('title_en', item['title']) if args.lang == 'en' else item['title'])}}}"
            for item in lectures
        ]
        out.append(rf"{tex_escape(lesson)} & " + (r"; ".join(titles) if args.lang == "en" else r"；".join(titles)) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{longtable}")
    out.append("")
    out.append(rf"\section*{{{get_text(args.lang, 'overview')}}}")
    out.append(text["overview_body"])
    out.append("")
    out.append(rf"\section*{{{get_text(args.lang, 'concepts')}}}")
    out.append(rf"\subsection*{{1. {get_text(args.lang, 'concept_a')}}}")
    out.append(r"\begin{itemize}")
    out.append(rf"\item {get_text(args.lang, 'feature_1')}")
    out.append(rf"\item {get_text(args.lang, 'feature_2')}")
    out.append(r"\end{itemize}")
    out.append("")
    out.append(rf"\subsection*{{2. {get_text(args.lang, 'concept_b')}}}")
    out.append(r"\begin{enumerate}")
    out.append(rf"\item {get_text(args.lang, 'step_1')}")
    out.append(rf"\item {get_text(args.lang, 'step_2')}")
    out.append(r"\end{enumerate}")
    out.append("")
    out.append(rf"\section*{{{get_text(args.lang, 'exercise')}}}")
    out.append(r"\begin{enumerate}")
    out.append(rf"\item {get_text(args.lang, 'prompt_1')}")
    out.append(rf"\item {get_text(args.lang, 'prompt_2')}")
    out.append(r"\end{enumerate}")
    out.append("")
    out.append(rf"\section*{{{get_text(args.lang, 'answers')}}}")
    out.append(r"\begin{itemize}")
    out.append(rf"\item {get_text(args.lang, 'answer_note')}")
    out.append(r"\end{itemize}")
    out.append(r"\end{document}")

    Path(args.output).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote scaffold to {args.output}")


if __name__ == "__main__":
    main()
