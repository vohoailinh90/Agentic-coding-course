"""The offline HTML export: self-contained files in which every link lands on a page."""

from __future__ import annotations

import base64
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from src.core.export import export_files
from src.core.infographics import render
from src.core.model import ROOT
from src.core.validate import validate
from tests.course_fixtures import COURSE, DIAGRAM, RECAP, RECAP_ID, dump, make_store, write_lesson, write_generated
from tests.test_course_tools import run_cli

TODAY = date(2026, 9, 27)
EXTERNAL = ("http://", "https://", "mailto:")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
BETA_SECTIONS = ("objective", "hook", "concept", "try-it", "recap", "takeaways", "quiz")


class Page(HTMLParser):
    """The ids, links and images of one HTML file, and whether its tags nest."""

    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[str] = []
        self.images: list[str] = []
        self.tags: list[str] = []
        self.stack: list[str] = []
        self.problems: list[str] = []
        self.feed(text)
        self.close()
        if self.stack:
            self.problems.append(f"never closed: {self.stack}")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        self.tags.append(tag)
        if attributes.get("id"):
            self.ids.append(str(attributes["id"]))
        if tag == "a" and attributes.get("href") is not None:
            self.links.append(str(attributes["href"]))
        if tag == "img":
            self.images.append(str(attributes.get("src")))
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.problems.append(f"</{tag}> closes <{self.stack[-1] if self.stack else '-'}>")
        else:
            self.stack.pop()


def dead_links(files: dict[str, str]) -> list[str]:
    """Links that do not land on an element of the export: another file's, or their own."""
    pages = {name: Page(text) for name, text in files.items()}
    dead = []
    for name, page in pages.items():
        for href in page.links:
            if href.startswith(EXTERNAL):
                continue
            target, _, fragment = href.partition("#")
            other = pages.get(target or name)
            if other is None or fragment not in other.ids:
                dead.append(f"{name}: {href}")
    return dead


def bar(text: str, anchor: str) -> str:
    """The navigation bar at the top of one page."""
    start = text.index(f'id="{anchor}"')
    return text[text.index('<nav class="bar">', start): text.index("</nav>", start)]


def decoded(uri: str) -> str:
    prefix = "data:image/svg+xml;base64,"
    assert uri.startswith(prefix), uri[:40]
    return base64.b64decode(uri[len(prefix):]).decode("utf-8")


class ExportTests(unittest.TestCase):
    """Lesson alpha is finished in every language; beta is in review in vi, a draft in en, done in ja."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_store(Path(self._tmp.name))
        write_lesson(self.root, "alpha", "vi", bodies={
            "hook": "Xem [bài beta](beta.md), [bản tiếng Anh của beta](../../en/lessons/beta.md), "
                    "[thuật ngữ](../glossary.md), [trang chính](../README.md) và [tài liệu](https://example.com).",
        })
        write_lesson(self.root, "alpha", "en", bodies={"hook": "See [lesson beta](beta.md)."})
        for language, status in (("vi", "review"), ("en", "draft"), ("ja", "done")):
            write_lesson(self.root, "beta", language, status=status, sections=BETA_SECTIONS)
        write_generated(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def export(self) -> dict[str, str]:
        report = validate(self.root)
        self.assertEqual(report.errors, [])
        return {exported.name: exported.html for exported in export_files(report.course, report.docs, self.root, TODAY)}

    def test_there_is_a_file_with_every_language_and_one_per_language(self) -> None:
        report = validate(self.root)
        files = export_files(report.course, report.docs, self.root, TODAY)
        self.assertEqual([exported.name for exported in files], [
            "mini-course.html", "mini-course-vi.html", "mini-course-en.html", "mini-course-ja.html",
        ])
        self.assertEqual([exported.lessons for exported in files], [5, 2, 1, 2])
        self.assertEqual([exported.languages for exported in files], [("vi", "en", "ja"), ("vi",), ("en",), ("ja",)])

    def test_every_link_lands_on_a_page_of_the_export(self) -> None:
        files = self.export()
        self.assertEqual(dead_links(files), [])
        for name, text in files.items():
            page = Page(text)
            self.assertEqual(page.problems, [], name)
            self.assertEqual(len(page.ids), len(set(page.ids)), f"{name}: an id is used twice")

    def test_a_file_needs_nothing_from_outside_itself(self) -> None:
        for name, text in self.export().items():
            page = Page(text)
            self.assertNotIn("script", page.tags, name)
            self.assertNotIn("link", page.tags, name)  # no external style sheet
            self.assertTrue(page.images)
            for source in page.images:
                self.assertTrue(source.startswith("data:image/"), f"{name}: {source[:60]}")
            for href in page.links:
                self.assertFalse(href.endswith(".md") or "../" in href or ".md#" in href, f"{name}: {href}")

    def test_each_file_opens_on_one_landing_page(self) -> None:
        files = self.export()
        self.assertIn('<section class="page chooser landing" id="languages">', files["mini-course.html"])
        self.assertNotIn('class="page home landing"', files["mini-course.html"])
        for language in ("vi", "en", "ja"):
            text = files[f"mini-course-{language}.html"]
            self.assertEqual(text.count(" landing\""), 1, language)
            self.assertIn(f'<section class="page home landing" id="{language}-home" lang="{language}">', text)
            self.assertIn(f'<html lang="{language}">', text)

    def test_infographics_are_rendered_from_their_specs(self) -> None:
        text = self.export()["mini-course-ja.html"]
        shown = [decoded(source) for source in Page(text).images]
        self.assertIn(render(RECAP, "ja"), shown)
        self.assertIn(render(DIAGRAM, "ja"), shown)
        self.assertNotIn(render(RECAP, "vi"), shown)
        self.assertTrue(any('lang="ja"' in svg and "<svg" in svg for svg in shown))  # the roadmap

    def test_only_finished_lessons_are_exported(self) -> None:
        files = self.export()
        self.assertIn('id="vi-lesson-beta"', files["mini-course-vi.html"])
        self.assertIn('id="ja-lesson-beta"', files["mini-course-ja.html"])
        english = files["mini-course-en.html"]
        self.assertNotIn('id="en-lesson-beta"', english)
        self.assertIn('<span class="soon">Lesson beta</span>', english)  # listed on the home, not linked
        self.assertNotIn('id="en-lesson-beta"', files["mini-course.html"])

    def test_a_link_to_a_lesson_that_is_not_exported_keeps_only_its_text(self) -> None:
        files = self.export()
        english = files["mini-course-en.html"]
        self.assertIn("See lesson beta.", english)
        vietnamese = files["mini-course-vi.html"]
        self.assertIn('<a href="#vi-lesson-beta">bài beta</a>', vietnamese)
        self.assertIn(", bản tiếng Anh của beta, ", vietnamese)
        self.assertIn('<a href="#vi-glossary">thuật ngữ</a>', vietnamese)
        self.assertIn('<a href="#vi-home">trang chính</a>', vietnamese)
        self.assertIn('<a href="https://example.com" target="_blank" rel="noopener noreferrer">tài liệu</a>', vietnamese)

    def test_links_to_another_language_point_into_its_file(self) -> None:
        files = self.export()
        vietnamese = bar(files["mini-course-vi.html"], "vi-lesson-beta")
        everything = bar(files["mini-course.html"], "vi-lesson-beta")
        self.assertIn('<a lang="ja" href="mini-course-ja.html#ja-lesson-beta">', vietnamese)
        self.assertIn('<a lang="ja" href="#ja-lesson-beta">', everything)
        # beta is only a draft in English, so its page sends English readers to their course home
        self.assertIn('<a lang="en" href="mini-course-en.html#en-home">', vietnamese)
        self.assertIn('<a lang="en" href="#en-home">', everything)

    def test_a_lesson_in_review_carries_a_badge(self) -> None:
        files = self.export()
        badge = '<span class="badge">'
        vietnamese = files["mini-course-vi.html"]
        self.assertEqual(vietnamese.count(badge), 2)  # alpha and beta are both in review in Vietnamese
        japanese = files["mini-course-ja.html"]
        self.assertEqual(japanese.count(badge), 1)  # beta is done in Japanese
        self.assertIn("下書き（確認待ち）", japanese)

    def test_lessons_link_to_their_neighbours(self) -> None:
        text = self.export()["mini-course-vi.html"]
        self.assertIn('<a class="next" href="#vi-lesson-beta">', text)
        self.assertIn('<a class="previous" href="#vi-lesson-alpha">', text)
        self.assertEqual(text.count('class="next"') + text.count('class="previous"'), 2)

    def test_lesson_terms_link_to_the_glossary(self) -> None:
        text = self.export()["mini-course-ja.html"]
        self.assertIn('<a href="#ja-term-model">学習モデル［がくしゅうモデル］</a>', text)
        self.assertIn('<tr id="ja-term-model">', text)
        self.assertIn('<span lang="vi">Mô hình</span>', text)

    def test_text_from_the_data_is_escaped(self) -> None:
        course = {**COURSE, "title": {**COURSE["title"], "en": 'Mini <b>course</b> & "more"'}}
        dump(self.root / "course" / "data" / "course.yaml", course)
        write_generated(self.root)
        text = self.export()["mini-course-en.html"]
        self.assertIn("Mini &lt;b&gt;course&lt;/b&gt; &amp; &quot;more&quot;", text)
        self.assertNotIn("<b>course</b>", text)

    def test_the_export_does_not_change_between_runs(self) -> None:
        self.assertEqual(self.export(), self.export())


class ExportCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_store(Path(self._tmp.name) / "repo")
        self.out = Path(self._tmp.name) / "out"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_the_command_writes_every_file(self) -> None:
        code, out, err = run_cli("--root", str(self.root), "export", "--out", str(self.out))
        self.assertEqual(code, 0, err)
        written = sorted(path.name for path in self.out.iterdir())
        self.assertEqual(written, ["mini-course-en.html", "mini-course-ja.html", "mini-course-vi.html", "mini-course.html"])
        self.assertIn("Wrote 4 HTML files", out)
        self.assertIn("mini-course-vi.html — lessons: 1", out)
        self.assertIn("mini-course.html alone holds all three languages", out)

    def test_the_default_folder_is_outputs_html(self) -> None:
        code, _, err = run_cli("--root", str(self.root), "export")
        self.assertEqual(code, 0, err)
        self.assertTrue((self.root / "outputs" / "html" / "mini-course.html").is_file())

    def test_only_export_needs_markdown_it(self) -> None:
        """markdown-it-py is imported when an export runs: without it, validate works and export says why."""
        script = (
            "import sys; sys.modules['markdown_it'] = None\n"  # any `import markdown_it` now fails
            "from src.main import main\n"
            f"code = main(['--lang', 'en', '--root', {str(self.root)!r}, 'validate'])\n"
            f"sys.exit(code * 10 + main(['--lang', 'en', '--root', {str(self.root)!r}, 'export', '--out', {str(self.out)!r}]))\n"
        )
        result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1, result.stderr)  # validate 0, export 1
        self.assertIn("export needs the markdown-it-py library", result.stderr)
        self.assertFalse(self.out.exists())

    def test_a_store_with_errors_is_not_exported(self) -> None:
        (self.root / "course" / "data" / "diagrams" / f"{RECAP_ID}.yaml").unlink()
        code, out, err = run_cli("--root", str(self.root), "export", "--out", str(self.out))
        self.assertEqual(code, 1)
        self.assertFalse(self.out.exists())
        self.assertIn("python -m src.main validate", err)


class RealCourseExportTests(unittest.TestCase):
    def test_the_course_exports_with_every_link_landing_and_every_tag_closed(self) -> None:
        report = validate(ROOT, check_generated=False)
        self.assertEqual(report.errors, [])
        files = {exported.name: exported.html for exported in export_files(report.course, report.docs, ROOT, TODAY)}
        self.assertEqual(dead_links(files), [])
        for name, text in files.items():
            self.assertEqual(Page(text).problems, [], name)
        finished = sum(doc.status in ("review", "done") for doc in report.docs.values())
        self.assertEqual(files[f"{report.course.id}.html"].count('<section class="page lesson"'), finished)


if __name__ == "__main__":
    unittest.main()
