#!/usr/bin/env python3
"""
lint_handout.py — 讲义 LaTeX 成品的静默失败检查。

针对本仓库反复出现的"不报错但成品变形"问题：
1. CJK 文本中的 ASCII 直引号 " —— XeLaTeX 会把左引号全部渲染成右引号。
2. CJK 文本中的 ASCII 直省略号 ... —— 应为中文省略号 ……。
3. 编译日志中的 Missing character —— 字体缺字形，字符被静默丢弃。
4. 编译日志中的 LaTeX 错误（! 开头的行）。
5. 中文引号不成对 —— “” 与 ‘’ 数量不一致，多半是漏写或嵌套错误。
6. CJK 文本中孤立的单个 … —— 中文省略号是 ……（两个 U+2026），单个 … 多半是笔误。

用法：
    python3 scripts/lint_handout.py path/to/handout.tex [path/to/handout.log]

tex 与 log 可单独检查；任一问题以非零退出码返回。
"""

import re
import sys
from pathlib import Path

CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def lint_tex(tex_path: Path) -> list[str]:
    problems: list[str] = []
    lines = tex_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_verbatim = False
    body_lines: list[tuple[int, str]] = []  # (行号, 去注释/去数学模式后的正文)
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("\\begin{verbatim}") or stripped.startswith("\\begin{lstlisting}"):
            in_verbatim = True
            continue
        if stripped.startswith("\\end{verbatim}") or stripped.startswith("\\end{lstlisting}"):
            in_verbatim = False
            continue
        if in_verbatim or stripped.startswith("%"):
            continue
        # 去掉行尾注释
        body = re.sub(r"(?<!\\)%.*$", "", line)
        # ASCII 直引号：行内含 CJK 且引号未成对进入数学模式（$...$ 已剔除）
        no_math = re.sub(r"\$[^$]*\$", "", body)
        no_math = re.sub(r"\\\(|\\\)|\\\[|\\\]", "", no_math)
        if '"' in no_math and CJK_RE.search(no_math):
            problems.append(f"{tex_path.name}:{lineno}: CJK 文本含 ASCII 直引号 \"（左右引号会全部渲染成右引号）")
        # ASCII 单引号（排除 LaTeX 撇号用法，如 F'、x'）
        if re.search(r"(?<![A-Za-z}])'[^']*[\u4e00-\u9fff]", no_math) or re.search(r"[\u4e00-\u9fff][^']*'(?![A-Za-z(])", no_math):
            problems.append(f"{tex_path.name}:{lineno}: CJK 文本含 ASCII 单引号 '（左单引号会渲染成右单引号，应改用 ‘’）")
        # ASCII 三点省略号
        if "..." in no_math and CJK_RE.search(no_math):
            problems.append(f"{tex_path.name}:{lineno}: CJK 文本含 ASCII 省略号 ...（应为 ……）")
        body_lines.append((lineno, no_math))
    # 中文引号配对（全文统计， verbatim/注释已剔除）
    full_text = "\n".join(body for _, body in body_lines)
    for open_q, close_q in (("“", "”"), ("‘", "’")):
        open_count = full_text.count(open_q)
        close_count = full_text.count(close_q)
        if open_count != close_count:
            problems.append(
                f"{tex_path.name}: 中文引号不成对：{open_q} 出现 {open_count} 次，{close_q} 出现 {close_count} 次"
            )
    # 孤立的单个 …（中文省略号应为两个 U+2026：……）
    for lineno, body in body_lines:
        if "…" not in body or not CJK_RE.search(body):
            continue
        for m in re.finditer("…", body):
            i = m.start()
            if (i > 0 and body[i - 1] == "…") or (i + 1 < len(body) and body[i + 1] == "…"):
                continue
            problems.append(f"{tex_path.name}:{lineno}: CJK 文本含孤立的单个省略号 …（中文省略号应为 ……）")
            break  # 每行报一次即可
    return problems


def lint_log(log_path: Path) -> list[str]:
    problems: list[str] = []
    text = log_path.read_text(encoding="utf-8", errors="replace")
    errors = re.findall(r"^! .+$", text, flags=re.MULTILINE)
    for e in errors[:20]:
        problems.append(f"{log_path.name}: LaTeX 错误: {e}")
    missing = sorted(set(re.findall(r"Missing character: There is no (.+?) in font", text)))
    for ch in missing:
        problems.append(f"{log_path.name}: 缺字形被静默丢弃: {ch}")
    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    problems: list[str] = []
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            problems.append(f"{arg}: 文件不存在")
            continue
        if path.suffix == ".tex":
            problems.extend(lint_tex(path))
        elif path.suffix == ".log":
            problems.extend(lint_log(path))
        else:
            problems.append(f"{arg}: 不支持的文件类型（仅检查 .tex / .log）")
    if problems:
        print(f"发现 {len(problems)} 个问题：")
        for p in problems:
            print(" -", p)
        return 1
    print("lint 通过：未发现静默失败迹象。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
