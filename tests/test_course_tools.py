"""The course commands: scaffold, build, stats, fb-draft and the CLI itself."""

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
from tests.course_fixtures import language_bar, make_store, write_lesson


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
            text = (self.root / f"course/{language}/lessons/beta.md").read_text(encoding="utf-8")
            self.assertIn("status: todo", text)
            self.assertIn("<!-- section: try-it -->", text)
            self.assertIn(language_bar("beta", language), text)
        report = validate(self.root)
        self.assertEqual(report.errors, [])  # the course homes were rebuilt to link the lesson
        self.assertEqual(report.docs[("beta", "ja")].status, "todo")
        self.assertIn("course/vi/lessons/beta.md", out)
        home = (self.root / "course/en/README.md").read_text(encoding="utf-8")
        self.assertIn("[Lesson beta](lessons/beta.md)", home)

    def test_scaffold_never_overwrites(self) -> None:
        path = self.root / "course/en/lessons/alpha.md"
        before = path.read_text(encoding="utf-8")
        code, out, _ = run_cli("--root", str(self.root), "scaffold", "alpha")
        self.assertEqual(code, 0)
        self.assertEqual(path.read_text(encoding="utf-8"), before)
        self.assertIn("Skipped", out)

    def test_scaffold_rejects_an_unknown_lesson(self) -> None:
        code, _, err = run_cli("--root", str(self.root), "scaffold", "gamma")
        self.assertEqual(code, 1)
        self.assertIn("gamma", err)
        self.assertFalse((self.root / "course/vi/lessons/gamma.md").exists())

    # -- build ------------------------------------------------------------------

    def test_build_check_and_write(self) -> None:
        self.assertEqual(run_cli("--root", str(self.root), "build", "--check")[0], 0)
        (self.root / "course/vi/README.md").write_text("stale\n", encoding="utf-8")
        code, out, _ = run_cli("--root", str(self.root), "build", "--check")
        self.assertEqual(code, 1)
        self.assertIn("course/vi/README.md", out)
        self.assertEqual(run_cli("--root", str(self.root), "build")[0], 0)
        self.assertEqual(run_cli("--root", str(self.root), "build", "--check")[0], 0)

    def test_each_course_home_is_in_one_language(self) -> None:
        homes = {lang: (self.root / f"course/{lang}/README.md").read_text(encoding="utf-8")
                 for lang in ("vi", "en", "ja")}
        self.assertIn("| 1.1.2 | Bài beta | 🛠️ Thực hành | 15 phút |", homes["vi"])
        self.assertIn("| 1.1.1 | [Lesson alpha](lessons/alpha.md) | 📖 Concept | 10 min |", homes["en"])
        self.assertIn("| 1.1.2 | レッスン・ベータ | 🛠️ 実習 | 15分 |", homes["ja"])
        self.assertNotIn("Lesson beta", homes["vi"] + homes["ja"])
        self.assertTrue(homes["ja"].split("\n")[2].startswith("🌐 [Tiếng Việt](../vi/README.md) · [English](../en/README.md)"))
        self.assertIn("![学習ロードマップ](diagrams/roadmap.svg)", homes["ja"])

    def test_the_glossary_pages_define_terms_in_their_own_language(self) -> None:
        vi = (self.root / "course/vi/glossary.md").read_text(encoding="utf-8")
        self.assertIn("| **Mô hình** | Kết quả của huấn luyện. | Model | 学習モデル［がくしゅうモデル］ |", vi)
        ja = (self.root / "course/ja/glossary.md").read_text(encoding="utf-8")
        self.assertIn("| **学習モデル［がくしゅうモデル］** | 学習の結果。 | Mô hình | Model |", ja)

    def test_the_chooser_links_every_language(self) -> None:
        chooser = (self.root / "course/README.md").read_text(encoding="utf-8")
        for language, name in (("vi", "Tiếng Việt"), ("en", "English"), ("ja", "日本語")):
            self.assertIn(f"## [{name} →]({language}/README.md)", chooser)

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
        target = self.root / "outputs/facebook/alpha-vi.txt"  # outside course/, as documented
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
        (self.root / "course/en/lessons/alpha.md").unlink()
        code, out, _ = run_cli("--root", str(self.root), "validate")
        self.assertEqual(code, 1)
        self.assertIn("error: course/en/lessons/alpha.md: missing.", out)
        self.assertIn("Errors: 1.", out)


if __name__ == "__main__":
    unittest.main()
