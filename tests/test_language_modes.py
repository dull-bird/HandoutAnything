import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run(cmd, cwd):
    return subprocess.run(
        [sys.executable, *cmd],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


class LanguageModeTests(unittest.TestCase):
    def test_generate_handout_en_uses_english_assets(self):
        with tempfile.TemporaryDirectory() as td:
            data_dir = Path(td)
            (data_dir / "frames").mkdir()
            write_json(
                data_dir / "manifest.json",
                [
                    {
                        "title": "Introduction",
                        "lesson": "Module 1",
                        "page_url": "https://example.com/lecture-1",
                        "video": "lecture-1.mp4",
                        "en_vtt": "lecture-1.en.vtt",
                        "duration": "05:00",
                        "resources": ["reading.pdf"],
                    }
                ],
            )
            write_json(
                data_dir / "content.json",
                {
                    "overview": "中文总览",
                    "lectures": {"lecture-1": "中文讲解"},
                    "key_takeaways": ["中文要点"],
                    "exercises": {"choice": [], "truefalse": ["中文判断题"], "shortanswer": []},
                    "answers": {},
                },
            )
            write_json(
                data_dir / "content_en.json",
                {
                    "overview": "English overview",
                    "lectures": {"lecture-1": "English lecture summary"},
                    "key_takeaways": ["English takeaway"],
                    "exercises": {"choice": [], "truefalse": ["English true/false question"], "shortanswer": []},
                    "answers": {},
                },
            )
            write_json(
                data_dir / "supplements_en.json",
                {
                    "reading.pdf": {
                        "title": "Background Reading",
                        "summary": ["First point", "Second point"],
                    }
                },
            )
            output = data_dir / "out.tex"
            run(
                [
                    "handout-anything/scripts/generate_handout.py",
                    "--data-dir",
                    str(data_dir),
                    "--course-title",
                    "中文课程",
                    "--unit-title",
                    "中文单元",
                    "--course-title-en",
                    "English Course",
                    "--unit-title-en",
                    "English Unit",
                    "--instructor",
                    "Instructor",
                    "--lang",
                    "en",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
            )
            tex = output.read_text(encoding="utf-8")
            self.assertIn(r"\documentclass[a4paper,11pt]{article}", tex)
            self.assertIn("English overview", tex)
            self.assertIn("English lecture summary", tex)
            self.assertIn("Background Reading", tex)
            self.assertIn(r"\begin{supplement}{Summary}", tex)
            self.assertIn(r"(\quad)", tex)
            self.assertIn("Contents", tex)
            self.assertIn(r"\addcontentsline{toc}{section}{0. Overview}", tex)
            self.assertIn(r"\addcontentsline{toc}{section}{1. Introduction}", tex)
            self.assertNotIn("中文总览", tex)
            self.assertNotIn("补充材料", tex)
            self.assertNotIn("（\\quad）", tex)

    def test_generate_handout_en_uses_content_titles(self):
        with tempfile.TemporaryDirectory() as td:
            data_dir = Path(td)
            (data_dir / "frames").mkdir()
            write_json(
                data_dir / "manifest.json",
                [
                    {
                        "title": "中文标题",
                        "lesson": "Module 1",
                        "page_url": "https://example.com/lecture-1",
                        "video": "lecture-1.mp4",
                        "en_vtt": "lecture-1.en.vtt",
                    }
                ],
            )
            write_json(
                data_dir / "content_en.json",
                {
                    "lecture_titles": {"lecture-1": "English Lecture Title"},
                    "overview": "English overview",
                    "lectures": {"lecture-1": "English lecture summary"},
                },
            )
            output = data_dir / "out.tex"
            run(
                [
                    "handout-anything/scripts/generate_handout.py",
                    "--data-dir",
                    str(data_dir),
                    "--course-title",
                    "中文课程",
                    "--unit-title",
                    "中文单元",
                    "--course-title-en",
                    "English Course",
                    "--unit-title-en",
                    "English Unit",
                    "--instructor",
                    "Instructor",
                    "--lang",
                    "en",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
            )
            tex = output.read_text(encoding="utf-8")
            self.assertIn("English Lecture Title", tex)
            self.assertNotIn("中文标题", tex)

    def test_generate_handout_en_hides_non_english_resource_names(self):
        with tempfile.TemporaryDirectory() as td:
            data_dir = Path(td)
            (data_dir / "frames").mkdir()
            resource = data_dir / "背景阅读.pdf"
            resource.write_bytes(b"%PDF-1.4\n% fake\n")
            write_json(
                data_dir / "manifest.json",
                [
                    {
                        "title": "Introduction",
                        "lesson": "Module 1",
                        "page_url": "https://example.com/lecture-1",
                        "video": "lecture-1.mp4",
                        "en_vtt": "lecture-1.en.vtt",
                        "resources": [resource.name],
                    }
                ],
            )
            write_json(
                data_dir / "content_en.json",
                {
                    "overview": "English overview",
                    "lectures": {"lecture-1": "English lecture summary"},
                },
            )
            output = data_dir / "out.tex"
            run(
                [
                    "handout-anything/scripts/generate_handout.py",
                    "--data-dir",
                    str(data_dir),
                    "--course-title",
                    "English Course",
                    "--unit-title",
                    "English Unit",
                    "--course-title-en",
                    "English Course",
                    "--unit-title-en",
                    "English Unit",
                    "--instructor",
                    "Instructor",
                    "--lang",
                    "en",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
            )
            tex = output.read_text(encoding="utf-8")
            self.assertIn("Supplementary material", tex)
            self.assertNotIn("背景阅读", tex)

    def test_generate_handout_en_rejects_chinese_titles(self):
        with tempfile.TemporaryDirectory() as td:
            data_dir = Path(td)
            (data_dir / "frames").mkdir()
            write_json(
                data_dir / "manifest.json",
                [
                    {
                        "title": "中文标题",
                        "lesson": "中文小节",
                        "page_url": "https://example.com/lecture-1",
                        "video": "lecture-1.mp4",
                        "en_vtt": "lecture-1.en.vtt",
                    }
                ],
            )
            write_json(data_dir / "content_en.json", {"overview": "English overview"})
            proc = subprocess.run(
                [
                    sys.executable,
                    "handout-anything/scripts/generate_handout.py",
                    "--data-dir",
                    str(data_dir),
                    "--course-title",
                    "中文课程",
                    "--unit-title",
                    "中文单元",
                    "--lang",
                    "en",
                    "--output",
                    str(data_dir / "out.tex"),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("English output requires English course and unit titles", proc.stderr)

    def test_generate_handout_en_auto_summarizes_subtitles(self):
        with tempfile.TemporaryDirectory() as td:
            data_dir = Path(td)
            (data_dir / "frames").mkdir()
            vtt_path = data_dir / "lecture-1.en.vtt"
            vtt_path.write_text(
                """WEBVTT\n\n00:00:00.000 --> 00:00:03.000\nToday we define the problem clearly and distinguish assumptions from conclusions.\n\n00:00:03.000 --> 00:00:06.000\nA counterexample matters because it shows a general claim can fail.\n\n00:00:06.000 --> 00:00:09.000\nThe summary is that proof needs explicit premises.\n""",
                encoding="utf-8",
            )
            write_json(
                data_dir / "manifest.json",
                [
                    {
                        "title": "Introduction to Proof",
                        "lesson": "Module 1",
                        "page_url": "https://example.com/lecture-1",
                        "video": "lecture-1.mp4",
                        "en_vtt": vtt_path.name,
                        "duration": "08:00",
                    }
                ],
            )
            write_json(
                data_dir / "content_en.json",
                {
                    "lectures": {
                        "lecture-1": "Short manual summary."
                    }
                },
            )
            output = data_dir / "out.tex"
            run(
                [
                    "handout-anything/scripts/generate_handout.py",
                    "--data-dir",
                    str(data_dir),
                    "--course-title",
                    "English Course",
                    "--unit-title",
                    "English Unit",
                    "--course-title-en",
                    "English Course",
                    "--unit-title-en",
                    "English Unit",
                    "--instructor",
                    "Instructor",
                    "--lang",
                    "en",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
            )
            tex = output.read_text(encoding="utf-8")
            self.assertIn("Short manual summary.", tex)
            self.assertIn("Auto-generated digest", tex)
            self.assertIn(r"\textbf{Formal definitions}", tex)
            self.assertIn(r"\textbf{Example}", tex)
            self.assertIn(r"\textbf{Proof arc}", tex)
            self.assertNotIn("Hello, I’m Keith Devlin", tex)
            self.assertNotIn("Hello, I'm Keith Devlin", tex)
            self.assertNotIn("define the problem clearly", tex)
            self.assertNotIn("counterexample matters", tex)
            self.assertNotIn("content_en.json", tex)

    def test_generate_handout_zh_keeps_manifest_titles(self):
        with tempfile.TemporaryDirectory() as td:
            data_dir = Path(td)
            (data_dir / "frames").mkdir()
            write_json(
                data_dir / "manifest.json",
                [
                    {
                        "title": "Introduction to Perception",
                        "lesson": "Module 1",
                        "page_url": "https://example.com/lecture-1",
                        "video": "lecture-1.mp4",
                        "en_vtt": "lecture-1.en.vtt",
                    }
                ],
            )
            write_json(
                data_dir / "content.json",
                {
                    "overview": "中文总览",
                    "lectures": {"lecture-1": "中文讲解"},
                },
            )
            output = data_dir / "out.tex"
            run(
                [
                    "handout-anything/scripts/generate_handout.py",
                    "--data-dir",
                    str(data_dir),
                    "--course-title",
                    "课程标题",
                    "--unit-title",
                    "单元标题",
                    "--course-title-en",
                    "Course Title",
                    "--unit-title-en",
                    "Unit Title",
                    "--lang",
                    "zh",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
            )
            tex = output.read_text(encoding="utf-8")
            self.assertIn("中文总览", tex)
            self.assertIn("Introduction to Perception", tex)
            self.assertIn("授课教师：", tex)


if __name__ == "__main__":
    unittest.main()
