import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "handout-anything" / "scripts" / "review_handout.py"


def run_review(tex_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REVIEW), str(tex_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def build_unit(n: int, with_self_test: bool = True, with_refs: bool = True) -> str:
    parts = [
        f"\\daytitle{{第 {n} 讲}}{{标题 {n}}}",
        "\\noindent\\textbf{优先级}：必看\\quad|\\quad\\textbf{难度}：$\\star$\\quad|\\quad\\textbf{用时}：约 20 分钟",
        f"\\textbf{{核心问题}}：第 {n} 讲解决什么困惑？",
        "讲解正文。易错点：别把定义当结论。",
    ]
    if with_self_test:
        parts += [
            "\\begin{exercise}[今日自测]",
            "\\begin{enumerate}",
            "  \\item 第一题",
            "  \\item 第二题",
            "\\end{enumerate}",
            "\\end{exercise}",
        ]
    if with_refs:
        parts += [
            "\\begin{reading}",
            "\\textbf{本单元出处}：本单元内容为讲义原创讲解。",
            "\\textbf{拓展阅读}：《某书》第 2 章。",
            "\\end{reading}",
        ]
    return "\n".join(parts)


def build_handout(
    unit_count: int = 5,
    with_opening: bool = True,
    with_answers: bool = True,
    with_closing_echo: bool = True,
    with_boundary: bool = True,
    with_dependency: bool = True,
    unit_without_self_test: int | None = None,
    unit_without_refs: int | None = None,
) -> str:
    lines = ["\\documentclass{ctexart}", "\\begin{document}"]
    if with_opening:
        lines.append("\\section*{开始前：导读}")
    lines.append("这份材料在讲什么的说明。")
    if with_boundary:
        lines.append("\\textbf{边界声明}：本讲义只覆盖前五讲。")
    if with_dependency:
        lines.append("依赖：第 2 讲依赖第 1 讲。")
    for n in range(1, unit_count + 1):
        lines.append(
            build_unit(
                n,
                with_self_test=(n != unit_without_self_test),
                with_refs=(n != unit_without_refs),
            )
        )
    if with_answers:
        lines.append("\\section*{参考答案}")
        lines.append("各讲答案要点。")
    if with_closing_echo:
        lines.append("\\begin{keyconcept}[学完后，你应该能讲给别人听的三句话]")
        lines.append("三句话。")
        lines.append("\\end{keyconcept}")
    lines.append("\\end{document}")
    return "\n".join(lines) + "\n"


class ReviewHandoutTests(unittest.TestCase):
    def review(self, content: str, with_handover_md: bool = True) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as td:
            tex = Path(td) / "handout.tex"
            tex.write_text(content, encoding="utf-8")
            if with_handover_md:
                (Path(td) / "README.md").write_text("交接说明：参考资料清单与重编译方式。", encoding="utf-8")
            return run_review(tex)

    def test_minimal_handout_passes(self):
        proc = self.review(build_handout())
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("review 通过", proc.stdout)
        self.assertIn("0 errors, 0 warnings", proc.stdout)

    def test_missing_opening_section_is_error(self):
        proc = self.review(build_handout(with_opening=False))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("开始前", proc.stdout)

    def test_unit_without_self_test_is_error(self):
        proc = self.review(build_handout(unit_without_self_test=3))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("今日自测", proc.stdout)
        self.assertIn("第 3 单元", proc.stdout)

    def test_missing_answers_section_is_error(self):
        proc = self.review(build_handout(with_answers=False))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("参考答案", proc.stdout)

    def test_missing_closing_echo_is_error(self):
        proc = self.review(build_handout(with_closing_echo=False))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("讲给别人听", proc.stdout)

    def test_too_few_units_is_error(self):
        proc = self.review(build_handout(unit_count=2))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("单元数为 2", proc.stdout)

    def test_warnings_only_still_exit_zero(self):
        proc = self.review(build_handout(with_boundary=False, with_dependency=False))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("0 errors", proc.stdout)
        self.assertNotIn("review 通过", proc.stdout)
        self.assertIn("边界声明", proc.stdout)
        self.assertIn("依赖", proc.stdout)
        self.assertIn("warnings", proc.stdout)

    def test_missing_unit_refs_is_warning(self):
        proc = self.review(build_handout(unit_without_refs=3))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("0 errors", proc.stdout)
        self.assertIn("出处与拓展阅读", proc.stdout)
        self.assertIn("3", proc.stdout)

    def test_inline_src_tag_satisfies_unit_refs(self):
        content = build_handout(unit_without_refs=2)
        content = content.replace(
            "\\textbf{核心问题}：第 2 讲解决什么困惑？",
            "\\textbf{核心问题}：第 2 讲解决什么困惑？\n定理出处：\\src{《某书》 §2.1}",
        )
        proc = self.review(content)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertNotIn("出处与拓展阅读", proc.stdout)

    def test_missing_handover_md_is_warning(self):
        proc = self.review(build_handout(), with_handover_md=False)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("0 errors", proc.stdout)
        self.assertIn("交接说明 md", proc.stdout)

    def test_custom_unit_range_allows_short_handout(self):
        with tempfile.TemporaryDirectory() as td:
            tex = Path(td) / "handout.tex"
            tex.write_text(build_handout(unit_count=4), encoding="utf-8")
            (Path(td) / "README.md").write_text("交接说明。", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(REVIEW), str(tex), "--min-units", "2", "--max-units", "4"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("0 errors", proc.stdout)

    def test_custom_unit_range_still_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            tex = Path(td) / "handout.tex"
            tex.write_text(build_handout(unit_count=5), encoding="utf-8")
            (Path(td) / "README.md").write_text("交接说明。", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(REVIEW), str(tex), "--min-units", "2", "--max-units", "4"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("单元数为 5", proc.stdout)


if __name__ == "__main__":
    unittest.main()
