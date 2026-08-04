#!/usr/bin/env python3
"""
review_handout.py — 讲义结构审查（references/handout-methodology.md §5/§6 的代码化）。

把讲义 .tex 按学习单元切块（每个单元恰含一个 \\textbf{核心问题}），
第一个核心问题之前是卷首（front matter），\\section*{参考答案} 起是卷尾（back matter）。

ERROR（存在即退出码 1）：
  - 卷首缺少"开始前"章节
  - 每个单元块必须含 今日自测（或收尾单元的 总检验）
  - 卷尾必须有 \\section*{参考答案}
  - 收尾呼应：参考答案之后必须出现"讲给别人听"（keyconcept 收尾框）
  - 单元数必须在 5–9（方法论 7±2）

WARNING（打印但不影响退出码）：
  - 卷首应有 边界声明 与 依赖（单元依赖关系图）
  - 卷尾应有 参考文献 与 拓展阅读（方法论 §5.5 出处与拓展阅读）
  - 每个单元应有 优先级 / 难度 / 用时 标注
  - 每个单元应提及 易错 或 失效边界
  - 每个单元的 今日自测 题数应在 2–4（按 exercise 环境内 \\item 计数）
  - 每个单元的 用时 应形如"约 N 分钟"

用法：
    python3 scripts/review_handout.py path/to/handout.tex [--min-units N] [--max-units M]

--min-units / --max-units 默认 5/9（方法论 7±2，对应"一周讲义"）；
总量不足 8 小时的短讲义（单元叫"第 N 讲"）可按实际讲数收窄，如 --min-units 2 --max-units 4。
"""

import re
import sys
from pathlib import Path

CORE_Q = "\\textbf{核心问题}"
ANSWERS_SECTION = "\\section*{参考答案}"
HEADER_LOOKBACK = 8  # 核心问题之前多少行内算单元头部（优先级/难度/用时标注所在）


def split_units(lines: list[str]) -> tuple[list[str], list[tuple[int, list[str]]], list[str]]:
    """返回 (卷首行, [(核心问题行号, 单元块行)], 卷尾行)。行号均为 1-based。"""
    core_lines = [i for i, line in enumerate(lines) if CORE_Q in line]
    answers_idx = next((i for i, line in enumerate(lines) if ANSWERS_SECTION in line), None)

    front = lines[: core_lines[0]] if core_lines else lines
    back = lines[answers_idx:] if answers_idx is not None else []

    units: list[tuple[int, list[str]]] = []
    for pos, start in enumerate(core_lines):
        end = core_lines[pos + 1] if pos + 1 < len(core_lines) else (answers_idx if answers_idx is not None else len(lines))
        units.append((start + 1, lines[start:end]))
    return front, units, back


def self_test_item_counts(block: list[str]) -> list[int]:
    """单元块内每个 [今日自测] exercise 环境的 \\item 数。"""
    counts: list[int] = []
    in_self_test = False
    current = 0
    for line in block:
        if re.search(r"\\begin\{exercise\}\[今日自测\]", line):
            in_self_test = True
            current = 0
        elif in_self_test and "\\end{exercise}" in line:
            counts.append(current)
            in_self_test = False
        elif in_self_test and "\\item" in line:
            current += 1
    return counts


def review(tex_path: Path, min_units: int = 5, max_units: int = 9) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    lines = tex_path.read_text(encoding="utf-8", errors="replace").splitlines()
    front, units, back = split_units(lines)
    front_text = "\n".join(front)

    # ── ERROR：卷首"开始前" ──
    if "开始前" not in front_text:
        errors.append("卷首缺少「开始前」章节（\\section*{开始前…}）")

    # ── ERROR：单元数在指定范围（默认 5–9，方法论 7±2） ──
    if not (min_units <= len(units) <= max_units):
        errors.append(f"学习单元数为 {len(units)}，方法论要求 {min_units}–{max_units}（可用 --min-units/--max-units 调整）")

    # ── ERROR：卷尾参考答案 ──
    if not back:
        errors.append("卷尾缺少 \\section*{参考答案}")
    elif "讲给别人听" not in "\n".join(back):
        errors.append("收尾呼应缺失：\\section*{参考答案} 之后未出现「讲给别人听」（keyconcept 收尾框）")

    # ── WARNING：卷首边界声明 / 依赖 ──
    if "边界声明" not in front_text:
        warnings.append("卷首缺少「边界声明」（本讲义覆盖/未覆盖什么）")
    if "依赖" not in front_text:
        warnings.append("卷首缺少单元「依赖」关系说明（依赖关系图）")

    # ── WARNING：卷尾出处与拓展阅读（方法论 §5.5）──
    back_text = "\n".join(back)
    if back and "参考文献" not in back_text:
        warnings.append("卷尾缺少「参考文献」章节（出处编号文献，方法论 §5.5）")
    if back and "拓展阅读" not in back_text and "延伸阅读" not in back_text:
        warnings.append("卷尾缺少「拓展阅读」路线（分层指引读者深造，方法论 §5.5）")

    # ── 逐单元检查 ──
    missing_meta: dict[str, list[int]] = {"优先级": [], "难度": [], "用时": []}
    missing_pitfall: list[int] = []
    bad_time_format: list[int] = []
    for n, (core_lineno, block) in enumerate(units, 1):
        header_start = max(0, core_lineno - 1 - HEADER_LOOKBACK)
        header = lines[header_start : core_lineno - 1]
        header_text = "\n".join(header)
        block_text = "\n".join(block)

        # ERROR：今日自测（收尾单元的总检验也算）
        if "今日自测" not in block_text and "总检验" not in block_text:
            errors.append(f"第 {n} 单元（核心问题在第 {core_lineno} 行）缺少「今日自测」（\\begin{{exercise}}[今日自测]）")

        # WARNING：优先级 / 难度 / 用时
        for marker in missing_meta:
            if marker not in header_text:
                missing_meta[marker].append(n)
        # WARNING：用时格式
        if "用时" in header_text and not re.search(r"约\s*\d+\s*分钟", header_text):
            bad_time_format.append(n)
        # WARNING：易错 / 失效边界
        if "易错" not in block_text and "失效边界" not in block_text:
            missing_pitfall.append(n)
        # WARNING：自测题数 2–4
        for count in self_test_item_counts(block):
            if not (2 <= count <= 4):
                warnings.append(f"第 {n} 单元（第 {core_lineno} 行起）今日自测题数为 {count}，方法论要求 2–4 题")

    for marker, unit_ids in missing_meta.items():
        if unit_ids:
            warnings.append(f"缺少「{marker}」标注的单元：{', '.join(map(str, unit_ids))}")
    if bad_time_format:
        warnings.append(f"「用时」未按「约 N 分钟」格式标注的单元：{', '.join(map(str, bad_time_format))}")
    if missing_pitfall:
        warnings.append(f"未提及「易错」或「失效边界」的单元：{', '.join(map(str, missing_pitfall))}")

    return errors, warnings


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="讲义结构审查（references/handout-methodology.md §5/§6 的代码化）"
    )
    parser.add_argument("tex_path", help="讲义 .tex 文件路径")
    parser.add_argument("--min-units", type=int, default=5, help="学习单元数下限（默认 5，方法论 7±2）")
    parser.add_argument("--max-units", type=int, default=9, help="学习单元数上限（默认 9，方法论 7±2）")
    args = parser.parse_args()

    tex_path = Path(args.tex_path)
    if not tex_path.exists():
        print(f"{tex_path}: 文件不存在")
        return 2
    errors, warnings = review(tex_path, min_units=args.min_units, max_units=args.max_units)
    print(f"讲义结构审查：{tex_path}")
    if errors:
        print("错误：")
        for e in errors:
            print(" -", e)
    if warnings:
        print("警告：")
        for w in warnings:
            print(" -", w)
    if errors:
        print(f"review: {len(errors)} errors, {len(warnings)} warnings")
        return 1
    if warnings:
        print(f"review: 0 errors, {len(warnings)} warnings（警告不阻断，但每条都应有意识地为它找到理由）")
    else:
        print("review 通过：0 errors, 0 warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
