"""The course commands: scaffold, outline, stats, fb-draft and the CLI itself."""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.core.validate import validate
from src.main import main
from src.tools.fb_draft import plain
from src.tools.stats import progress
from tests.course_fixtures import make_store, write_lesson


def run_cli(*arguments: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
            mock.patch.dict(os.environ, {"APP_LANG": "en", "LC_ALL": "", "LC_MESSAGES": "", "LANG": ""}):
        code = main(list(arguments))
    return code, out.getvalue(), err.getvalue()


class CommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_store(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- scaffold ---------------------------------------------------------------

    def test_scaffold_creates_skeletons_that_validate(self) -> None:
        code, out, _ = run_cli("--root", str(self.root), "scaffold", "beta")
        self.assertEqual(code, 0)
        for language in ("vi", "en", "ja"):
            text = (self.root / f"course/lessons/beta/{language}.md").read_text(encoding="utf-8")
            self.assertIn("status: todo", text)
            self.assertIn("<!-- section: try-it -->", text)
        report = validate(self.root)
        self.assertEqual(report.errors, [])
        self.assertEqual(report.docs[("beta", "ja")].status, "todo")
        self.assertIn("course/lessons/beta/vi.md", out)

    def test_scaffold_never_overwrites(self) -> None:
        path = self.root / "course/lessons/alpha/en.md"
        before = path.read_text(encoding="utf-8")
        code, out, _ = run_cli("--root", str(self.root), "scaffold", "alpha")
        self.assertEqual(code, 0)
        self.assertEqual(path.read_text(encoding="utf-8"), before)
        self.assertIn("Skipped", out)

    def test_scaffold_rejects_an_unknown_lesson(self) -> None:
        code, _, err = run_cli("--root", str(self.root), "scaffold", "gamma")
        self.assertEqual(code, 1)
        self.assertIn("gamma", err)
        self.assertFalse((self.root / "course/lessons/gamma").exists())

    # -- outline ----------------------------------------------------------------

    def test_outline_check_and_write(self) -> None:
        self.assertEqual(run_cli("--root", str(self.root), "outline", "--check")[0], 0)
        (self.root / "course/OUTLINE.md").write_text("stale\n", encoding="utf-8")
        self.assertEqual(run_cli("--root", str(self.root), "outline", "--check")[0], 1)
        self.assertEqual(run_cli("--root", str(self.root), "outline", "--write")[0], 0)
        self.assertEqual(run_cli("--root", str(self.root), "outline", "--check")[0], 0)
        text = (self.root / "course/OUTLINE.md").read_text(encoding="utf-8")
        self.assertIn("| 1.1.2 | Bài beta | Lesson beta | レッスン・ベータ | 🛠️ hands-on | 15 |", text)

    # -- stats ------------------------------------------------------------------

    def test_progress_counts_each_status(self) -> None:
        write_lesson(self.root, "alpha", "ja", status="done")
        report = validate(self.root)
        counts = progress(report.course, report.docs)
        self.assertEqual(counts["ja"]["done"], 1)
        self.assertEqual(counts["vi"]["review"], 1)
        self.assertEqual(counts["vi"]["missing"], 1)  # beta is not started

    def test_stats_prints_the_structure(self) -> None:
        code, out, _ = run_cli("--root", str(self.root), "stats")
        self.assertEqual(code, 0)
        self.assertIn("Modules: 1 · Units: 1 · Lessons: 2 · Total time: 25 min", out)

    # -- fb-draft ---------------------------------------------------------------

    def test_fb_draft_assembles_the_post_from_the_store(self) -> None:
        code, out, err = run_cli("--root", str(self.root), "fb-draft", "alpha", "--post-lang", "ja")
        self.assertEqual(code, 0)
        self.assertIn("still in review", err)  # messages follow --lang/APP_LANG, the post follows --post-lang
        self.assertTrue(out.startswith("Hook!\n\n📘 レッスン 1.1.1：レッスン・アルファ\n"))
        self.assertIn("📌 まとめ：\n• Point for takeaways in ja, see docs (https://example.com).", out)
        self.assertIn("• 学習モデル［がくしゅうモデル］ — VI: Mô hình · EN: Model", out)
        self.assertIn("💬 Question?", out)
        self.assertTrue(out.rstrip().endswith("#テスト"))
        self.assertNotIn("**", out)

    def test_fb_draft_refuses_an_unfinished_lesson(self) -> None:
        for language in ("vi", "en", "ja"):
            write_lesson(self.root, "alpha", language, status="draft")
        code, out, err = run_cli("--root", str(self.root), "fb-draft", "alpha")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn('"draft"', err)

    def test_fb_draft_refuses_a_lesson_with_errors(self) -> None:
        write_lesson(self.root, "alpha", "vi", title="Wrong title")
        code, out, err = run_cli("--root", str(self.root), "fb-draft", "alpha")
        self.assertEqual(code, 1)
        self.assertIn("Wrong title", err)

    def test_fb_draft_writes_to_a_file(self) -> None:
        target = self.root / "outputs/facebook/alpha-vi.txt"
        code, _, _ = run_cli("--root", str(self.root), "fb-draft", "alpha", "--out", str(target))
        self.assertEqual(code, 0)
        self.assertIn("📘 Bài 1.1.1: Bài alpha", target.read_text(encoding="utf-8"))

    def test_plain_text_for_facebook(self) -> None:
        self.assertEqual(
            plain("- **Bold** and *italic* with `code`\n1. See [the guide](https://x.y/z)\n<!-- hidden -->"),
            "• Bold and italic with code\n• See the guide (https://x.y/z)",
        )
        self.assertEqual(plain("a snake_case_name stays"), "a snake_case_name stays")

    # -- the CLI ----------------------------------------------------------------

    def test_validate_speaks_the_chosen_language_before_or_after_the_command(self) -> None:
        for arguments in (("--lang", "ja", "validate"), ("validate", "--lang", "ja")):
            with self.subTest(arguments=arguments):
                code, out, _ = run_cli("--root", str(self.root), *arguments)
                self.assertEqual(code, 0)
                self.assertIn("コンテンツに問題はありません", out)
        code, out, _ = run_cli("--root", str(self.root), "--lang", "vi", "validate")
        self.assertIn("Kho nội dung hợp lệ", out)

    def test_validate_fails_with_a_readable_report(self) -> None:
        (self.root / "course/lessons/alpha/en.md").unlink()
        code, out, _ = run_cli("--root", str(self.root), "validate")
        self.assertEqual(code, 1)
        self.assertIn("error: course/lessons/alpha/en.md: missing.", out)
        self.assertIn("Errors: 1.", out)


if __name__ == "__main__":
    unittest.main()
