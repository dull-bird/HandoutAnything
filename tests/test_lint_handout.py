import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LINT = ROOT / "scripts" / "lint_handout.py"


def run_lint(*paths: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LINT), *(str(p) for p in paths)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


class LintTexTests(unittest.TestCase):
    def lint(self, content: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as td:
            tex = Path(td) / "handout.tex"
            tex.write_text(content, encoding="utf-8")
            return run_lint(tex)

    def test_clean_file_passes(self):
        proc = self.lint(
            "\\section*{第 1 讲}\n"
            "他说“你好”，又补充‘确实如此’。\n"
            "后面的内容……值得细看……\n"
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("lint 通过", proc.stdout)

    def test_straight_double_quote_in_cjk_flagged(self):
        proc = self.lint('他说"你好"就走了\n')
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ASCII 直引号", proc.stdout)

    def test_straight_double_quote_without_cjk_allowed(self):
        proc = self.lint('He said "hello" loudly\n')
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_straight_single_quote_in_cjk_flagged(self):
        proc = self.lint("他说'你好'就走了\n")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ASCII 单引号", proc.stdout)

    def test_ascii_ellipsis_in_cjk_flagged(self):
        proc = self.lint("后面的内容...值得细看\n")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ASCII 省略号", proc.stdout)

    def test_unbalanced_double_quotes_flagged(self):
        proc = self.lint("他说“你好，世界。第二句“又开了一次。\n")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("引号不成对", proc.stdout)
        self.assertIn("2 次", proc.stdout)

    def test_unbalanced_single_quotes_flagged(self):
        proc = self.lint("他说‘你好。\n")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("‘ 出现 1 次，’ 出现 0 次", proc.stdout)

    def test_isolated_ellipsis_flagged(self):
        proc = self.lint("后面的内容…值得细看\n")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("孤立的单个省略号", proc.stdout)

    def test_paired_ellipsis_passes(self):
        proc = self.lint("后面的内容……值得细看\n")
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_verbatim_block_exempt(self):
        proc = self.lint(
            "正文“配对”引号。\n"
            "\\begin{verbatim}\n"
            '他说"raw"... 还有孤立…\n'
            "\\end{verbatim}\n"
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_comment_lines_exempt(self):
        proc = self.lint(
            "% 注释里\"的引号不算\n"
            "正文干净。 % 行尾注释里的...也不算\n"
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)


class LintLogTests(unittest.TestCase):
    def lint_log(self, content: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "handout.log"
            log.write_text(content, encoding="utf-8")
            return run_lint(log)

    def test_missing_character_flagged(self):
        proc = self.lint_log("Missing character: There is no ★ in font [font]\n")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("缺字形", proc.stdout)

    def test_latex_error_line_flagged(self):
        proc = self.lint_log("! Undefined control sequence.\nl.42 \\bad\n")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("LaTeX 错误", proc.stdout)

    def test_clean_log_passes(self):
        proc = self.lint_log("This is XeTeX, Version 3.14\nOutput written on handout.pdf (10 pages).\n")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("lint 通过", proc.stdout)


if __name__ == "__main__":
    unittest.main()
