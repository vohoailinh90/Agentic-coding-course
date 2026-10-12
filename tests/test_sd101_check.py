"""scripts/sd101_check.py: the Vietnamese System Design store rules, on fixtures and on the real store."""

from __future__ import annotations

import contextlib
import copy
import datetime
import io
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import sd101_check as check

SNAPSHOT = "https://github.com/ByteByteGoHq/system-design-101/blob/abc123/data/guides/one.md"
BODY = f"# Bài một\n\nNội dung.\n\n## Liên hệ nguồn\n\n[bài nguồn]({SNAPSHOT}).\n"
META = {
    "id": "sd-01-001",
    "title_vi": "Bài một",
    "content_status": "drafted",
    "verification": {"source_read": "done", "claims": "pending", "technical": "pending", "mobile": "pending"},
    "learner_test": "pending",
    "image_evidence": [],
}
README = "# Kho\n\n| ID | Bài |\n|---|---|\n| [sd-01-001](lessons/sd-01-001/lesson.md) | Bài một |\n"


class StoreCase(unittest.TestCase):
    """A one-lesson store in a temp directory; each test breaks one thing."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.store = self.root / "store"
        self.source_map = self.root / "source-map.json"
        self.write_source_map({"sd-01-001": ("Bài một", SNAPSHOT)})
        self.write_lesson("sd-01-001")
        self.write_readme(README)

    def write_source_map(self, lessons: dict[str, tuple[str, str]]) -> None:
        data = {"categories": [{"id": "sd-01", "lessons": [
            {"id": lesson_id, "title_vi": title, "source_snapshot_url": snapshot}
            for lesson_id, (title, snapshot) in lessons.items()]}]}
        self.source_map.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def write_lesson(self, lesson_id: str, *, meta: dict | None = None, body: str | None = None) -> Path:
        lesson_dir = self.store / "lessons" / lesson_id
        lesson_dir.mkdir(parents=True, exist_ok=True)
        data = copy.deepcopy(META if meta is None else meta)
        (lesson_dir / "lesson.yaml").write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        (lesson_dir / "lesson.md").write_text(BODY if body is None else body, encoding="utf-8")
        return lesson_dir

    def write_readme(self, text: str) -> None:
        self.store.mkdir(parents=True, exist_ok=True)
        (self.store / "README.md").write_text(text, encoding="utf-8")

    def problems(self) -> list[str]:
        return [str(problem) for problem in check.check_store(self.store, self.source_map)]

    def meta(self, **changes: object) -> dict:
        data = copy.deepcopy(META)
        data.update(changes)
        return data

    def assertProblem(self, fragment: str) -> None:
        found = self.problems()
        self.assertTrue(any(fragment in line for line in found), f"{fragment!r} not in {found}")


class RealStoreTests(unittest.TestCase):
    def test_the_real_store_passes_every_rule(self) -> None:
        problems = check.check_store(check.DEFAULT_STORE, check.DEFAULT_SOURCE_MAP)
        self.assertEqual([], [str(problem) for problem in problems])


class LessonYamlRuleTests(StoreCase):
    def test_a_valid_store_has_no_problems(self) -> None:
        self.assertEqual([], self.problems())

    def test_a_missing_file_is_reported(self) -> None:
        (self.store / "lessons" / "sd-01-001" / "lesson.yaml").unlink()
        self.assertProblem("lesson.yaml is missing")

    def test_unknown_or_missing_keys_are_reported(self) -> None:
        data = self.meta()
        data["status"] = "drafted"
        self.write_lesson("sd-01-001", meta=data)
        self.assertProblem("keys are")

    def test_an_id_that_is_not_the_directory_name_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(id="sd-01-002"))
        self.assertProblem("expected the directory name")

    def test_an_id_missing_from_the_source_map_is_reported(self) -> None:
        self.write_source_map({"sd-09-009": ("Khác", SNAPSHOT)})
        self.assertProblem("not in the source map")

    def test_a_title_that_differs_from_the_source_map_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(title_vi="Tiêu đề khác"))
        self.assertProblem("title_vi differs")

    def test_a_null_title_that_matches_a_null_source_map_title_is_reported(self) -> None:
        self.write_source_map({"sd-01-001": (None, SNAPSHOT)})
        self.write_lesson("sd-01-001", meta=self.meta(title_vi=None))
        self.assertProblem("title_vi must be a non-empty string")

    def test_an_empty_title_is_reported(self) -> None:
        self.write_source_map({"sd-01-001": ("", SNAPSHOT)})
        self.write_lesson("sd-01-001", meta=self.meta(title_vi="  "))
        self.assertProblem("title_vi must be a non-empty string")

    def test_a_status_outside_the_vocabulary_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(content_status="done"))
        self.assertProblem("content_status")

    def test_a_verification_state_outside_the_vocabulary_is_reported(self) -> None:
        data = self.meta()
        data["verification"]["claims"] = "ok"
        self.write_lesson("sd-01-001", meta=data)
        self.assertProblem("claims 'ok'")

    def test_approved_with_a_pending_check_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(content_status="approved"))
        self.assertProblem("approved needs every verification field")

    def test_approved_is_allowed_only_when_every_check_and_the_learner_test_are_done(self) -> None:
        data = self.meta(content_status="approved", learner_test="done")
        data["verification"] = {name: "done" for name in check.VERIFICATION_KEYS}
        self.write_lesson("sd-01-001", meta=data)
        self.assertEqual([], self.problems())

    def test_a_learner_test_that_is_still_pending_blocks_approved(self) -> None:
        data = self.meta(content_status="approved")
        data["verification"] = {name: "done" for name in check.VERIFICATION_KEYS}
        self.write_lesson("sd-01-001", meta=data)
        self.assertProblem("approved needs every verification field")

    def test_image_evidence_with_real_values_is_accepted_as_a_string_or_a_date(self) -> None:
        entry = {"url": "https://assets.bytebytego.com/d/1.png", "sha256": "a" * 64, "retrieved_on": "2026-10-12"}
        self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[entry]))
        self.assertEqual([], self.problems())
        # yaml.safe_dump writes a date unquoted and safe_load reads it back as a datetime.date
        self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[{**entry, "retrieved_on": datetime.date(2026, 10, 12)}]))
        self.assertEqual([], self.problems())

    def test_image_evidence_values_must_be_real(self) -> None:
        good = {"url": "https://assets.bytebytego.com/d/1.png", "sha256": "a" * 64, "retrieved_on": "2026-10-12"}
        bad = {"null url": {**good, "url": None}, "not an http url": {**good, "url": "ftp://x/y.png"},
               "empty digest": {**good, "sha256": ""}, "short digest": {**good, "sha256": "a" * 63},
               "non-hex digest": {**good, "sha256": "z" * 64}, "null date": {**good, "retrieved_on": None},
               "not a date": {**good, "retrieved_on": "yesterday"}, "url without a host": {**good, "url": "https://"},
               "month 99": {**good, "retrieved_on": "2026-99-99"}, "february 30": {**good, "retrieved_on": "2026-02-30"}}
        for name, entry in bad.items():
            with self.subTest(entry=name):
                self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[entry]))
                self.assertProblem("each image_evidence entry needs")

    def test_an_image_evidence_entry_without_a_digest_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[{"url": "https://x/y.png"}]))
        self.assertProblem("image_evidence entry needs")


class LessonMarkdownRuleTests(StoreCase):
    def test_an_unclosed_code_fence_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n```mermaid\nflowchart TB\n")
        self.assertProblem("unclosed code fence")

    def test_details_with_attributes_is_a_balanced_details_block(self) -> None:
        block = "<details open>\n<summary>x</summary>\n\nnội dung\n\n</details>"
        self.write_lesson("sd-01-001", body=BODY + "\n" + block + "\n")
        self.assertEqual([], self.problems())

    def test_a_details_tag_in_a_code_block_a_code_span_or_a_comment_is_not_counted(self) -> None:
        for name, text in {"code block": "```html\n<details>\n```", "code span": "Gõ `<details>` để mở.",
                           "comment": "<!-- <details> -->"}.items():
            with self.subTest(where=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + text + "\n")
                self.assertEqual([], self.problems())

    def test_a_stray_closing_details_tag_is_reported_even_when_a_later_block_balances_the_count(self) -> None:
        block = "<details>\n<summary>x</summary>\n\nnội dung\n\n</details>"
        forms = {"close then an open block left open": "</details>\n\n<details>\n<summary>x</summary>\n\nnội dung\n",
                 "close then a balanced block": "</details>\n\n" + block,
                 "close only": "</details>"}
        for name, text in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + text + "\n")
                self.assertProblem("unbalanced <details>")

    def test_nested_details_blocks_are_balanced(self) -> None:
        inner = "<details>\n<summary>trong</summary>\n\nb\n\n</details>"
        outer = f"<details>\n<summary>ngoài</summary>\n\n{inner}\n\n</details>"
        self.write_lesson("sd-01-001", body=BODY + "\n" + outer + "\n")
        self.assertEqual([], self.problems())

    def test_a_missing_local_image_is_reported_in_every_form(self) -> None:
        forms = {"inline": "![sơ đồ](missing.svg)", "reference": "![sơ đồ][i]\n\n[i]: missing.svg",
                 "html img": '<img src="missing.svg" alt="sơ đồ">'}
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                self.assertProblem("'missing.svg' does not resolve")

    def test_a_local_svg_figure_is_accepted_in_every_form_and_in_any_case(self) -> None:
        forms = {"inline": "![sơ đồ](diagram.svg)", "reference": "![sơ đồ][i]\n\n[i]: diagram.svg",
                 "html img": '<img src="diagram.svg" alt="sơ đồ">', "upper case": "![sơ đồ](FIGURE.SVG)"}
        for name, form in forms.items():
            with self.subTest(form=name):
                lesson_dir = self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                (lesson_dir / "diagram.svg").write_text("<svg/>", encoding="utf-8")
                (lesson_dir / "FIGURE.SVG").write_text("<svg/>", encoding="utf-8")
                self.assertEqual([], self.problems())

    def test_an_image_that_is_not_a_local_svg_is_reported(self) -> None:
        forms = {"local png": "![x](diagram.png)", "local jpeg in html": '<img src="diagram.jpg">',
                 "remote svg": "![x](https://example.com/a.svg)", "remote png": "![x](https://example.com/a.png)"}
        for name, form in forms.items():
            with self.subTest(form=name):
                lesson_dir = self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                (lesson_dir / "diagram.png").write_bytes(b"\x89PNG")
                (lesson_dir / "diagram.jpg").write_bytes(b"\xff\xd8")
                self.assertProblem("must be a local .svg file")

    def test_an_image_must_sit_directly_in_the_lesson_directory(self) -> None:
        self.write_source_map({"sd-01-001": ("Bài một", SNAPSHOT), "sd-01-002": ("Bài hai", SNAPSHOT)})
        other = self.write_lesson("sd-01-002", meta=self.meta(id="sd-01-002", title_vi="Bài hai"))
        (other / "figure.svg").write_text("<svg/>", encoding="utf-8")
        mine = self.write_lesson("sd-01-001", body=BODY + "\n![x](./figure.svg)\n")
        (mine / "figure.svg").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], [line for line in self.problems() if line.startswith("sd-01-001")])
        forms = {"another lesson": "../sd-01-002/figure.svg", "the same lesson by a detour": "../sd-01-001/figure.svg",
                 "encoded": "..%2Fsd-01-002%2Ffigure.svg", "a subdirectory": "figures/figure.svg",
                 "an absolute path": "/figure.svg"}
        for name, destination in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + f"\n![x]({destination})\n")
                self.assertProblem("directly inside the lesson directory")

    def test_a_lesson_directory_may_hold_only_lesson_files_and_svg_figures(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001")
        (lesson_dir / "diagram.svg").write_text("<svg/>", encoding="utf-8")
        (lesson_dir / "FIGURE.SVG").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], self.problems())
        for name in ("diagram.png", "photo.JPG", "notes.txt", "diagram.svg.png"):
            with self.subTest(file=name):
                (lesson_dir / name).write_bytes(b"x")
                self.assertProblem(f"{name} is not allowed")
                (lesson_dir / name).unlink()
        (lesson_dir / "assets").mkdir()
        self.assertProblem("assets is not allowed")
        (lesson_dir / "folder.svg").mkdir()
        self.assertProblem("folder.svg is not allowed")

    def test_an_svg_file_must_be_a_drawing_not_a_renamed_picture(self) -> None:
        png = "data:image/png;base64,iVBORw0KGgo="
        svgs = {
            "a renamed png": (b"\x89PNG\r\n\x1a\n\x00\x00", "is not well-formed XML"),
            "an empty file": (b"", "is not well-formed XML"),
            "xml with another root": (b"<html/>", "does not have an <svg> root"),
            "an embedded raster": (f'<svg><image href="{png}"/></svg>'.encode(), "embeds a picture with <image>"),
            "a linked raster": (b'<svg><image href="source.png"/></svg>', "embeds a picture with <image>"),
            "a namespaced image": (b'<svg xmlns="http://www.w3.org/2000/svg"><image/></svg>', "<image>"),
            "an html img inside foreignObject": (
                b'<svg xmlns="http://www.w3.org/2000/svg"><foreignObject>'
                b'<img xmlns="http://www.w3.org/1999/xhtml" src="a.png"/></foreignObject></svg>', "<img>"),
            "a feImage that loads the source host": (
                b'<svg xmlns="http://www.w3.org/2000/svg"><filter><feImage href="https://assets.bytebytego.com/'
                b'source.png"/></filter></svg>', "assets.bytebytego.com"),
            "a feImage that loads another picture": (
                b'<svg xmlns="http://www.w3.org/2000/svg"><filter><feImage href="#a"/></filter></svg>', "<feimage>"),
            "the source host in a label": (b"<svg><text>assets.bytebytego.com</text></svg>", "assets.bytebytego.com"),
            "an href to another file": (b'<svg><use href="other.svg#a"/></svg>', "outside the drawing"),
            "an href to a web page": (b'<svg><a href="https://example.com/">x</a></svg>', "outside the drawing"),
            "a namespaced xlink:href": (
                b'<svg xmlns:xlink="http://www.w3.org/1999/xlink"><use xlink:href="https://example.com/a.svg"/></svg>',
                "outside the drawing"),
            "a data uri in an href": (f'<svg><use href="{png}"/></svg>'.encode(), "outside the drawing"),
            "a url() to a file in an attribute": (b'<svg><rect style="fill:url(https://example.com/a.png)"/></svg>',
                                                  "url() or @import"),
            "a data uri in a url() in an attribute": (f'<svg><rect style="fill:url({png})"/></svg>'.encode(),
                                                      "url() or @import"),
            "a quoted url() in an attribute": (b'<svg><rect style="fill:url( \'a.png\' )"/></svg>',
                                               "url() or @import"),
            "a url() in a style element": (f"<svg><style>.a{{background:url({png})}}</style></svg>".encode(),
                                           "url() or @import"),
            "an @import in a style element": (b'<svg><style>@import "fonts.css";</style></svg>', "url() or @import"),
        }
        lesson_dir = self.write_lesson("sd-01-001")
        for name, (content, reason) in svgs.items():
            with self.subTest(file=name):
                (lesson_dir / "figure.svg").write_bytes(content)
                self.assertProblem(f"figure.svg")
                self.assertProblem(reason)

    def test_a_real_looking_svg_drawing_is_accepted(self) -> None:
        drawing = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                   'viewBox="0 0 10 10" aria-label="Data: sơ đồ"><title>Data: sơ đồ</title>'
                   '<defs><style>.a::after{content:"data: chữ"}</style>'
                   '<marker id="m"/><linearGradient id="g"/></defs>'
                   '<rect fill="url(\'#g\')" style="marker-end:url( #m )"/><use href="#a"/><use xlink:href="#a"/>'
                   '<text>Data: chữ</text></svg>')
        lesson_dir = self.write_lesson("sd-01-001")
        (lesson_dir / "figure.svg").write_text(drawing, encoding="utf-8")
        self.assertEqual([], self.problems())

    def test_a_lone_opening_fence_at_the_end_of_the_file_is_reported(self) -> None:
        for name, ending in {"backticks": "```", "tildes": "~~~", "long backticks": "````",
                             "backticks and a newline": "```\n", "an info string": "```mermaid"}.items():
            with self.subTest(ending=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + ending)
                self.assertProblem("unclosed code fence")

    def test_an_empty_fenced_block_is_not_unclosed(self) -> None:
        for name, block in {"backticks": "```\n```", "tildes": "~~~\n~~~", "an info string": "```text\n```\n"}.items():
            with self.subTest(block=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + block + "\n")
                self.assertEqual([], self.problems())

    def test_an_unclosed_tilde_fence_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n~~~mermaid\nflowchart TB\n")
        self.assertProblem("unclosed code fence")

    def test_closed_fences_of_either_marker_and_any_length_are_accepted(self) -> None:
        for name, fence in {"backticks": "```mermaid\nx\n```", "tildes": "~~~\nx\n~~~",
                            "long backticks": "````\nx\n````",
                            "a long fence may contain a short one": "````\n```\nx\n```\n````"}.items():
            with self.subTest(fence=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + fence + "\n")
                self.assertEqual([], self.problems())

    def test_a_closing_fence_shorter_than_the_opening_one_does_not_close_it(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n````\ncode\n```\n")
        self.assertProblem("unclosed code fence")

    def test_unbalanced_details_tags_are_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n<details>\n<summary>x</summary>\n")
        self.assertProblem("unbalanced <details>")

    def test_a_relative_link_that_does_not_resolve_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[thiếu](nowhere.md)\n")
        self.assertProblem("does not resolve")

    def test_a_relative_link_that_resolves_is_accepted(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[meta](lesson.yaml)\n")
        self.assertEqual([], self.problems())

    def test_a_broken_reference_style_relative_link_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[tài liệu][ref]\n\n[ref]: missing.md\n")
        self.assertProblem("'missing.md' does not resolve")

    def test_a_broken_relative_html_anchor_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + '\n<a href="missing.md">tài liệu</a>\n')
        self.assertProblem("'missing.md' does not resolve")

    def test_a_reference_style_relative_link_that_resolves_is_accepted(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[meta][ref]\n\n[ref]: lesson.yaml\n")
        self.assertEqual([], self.problems())

    def test_a_relative_link_with_a_fragment_or_query_is_checked_by_its_path(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[a](lesson.yaml#id) [b](lesson.yaml?x=1)\n")
        self.assertEqual([], self.problems())
        self.write_lesson("sd-01-001", body=BODY + "\n[c](missing.md#id)\n")
        self.assertProblem("'missing.md#id' does not resolve")

    def test_anchors_urls_and_mail_links_are_not_relative_links(self) -> None:
        links = "[a](#phan-nguon) [b](https://example.com/x) [c](mailto:a@b.vn) [d](//example.com/x)"
        self.write_lesson("sd-01-001", body=BODY + "\n" + links + "\n")
        self.assertEqual([], self.problems())

    def test_a_link_shaped_text_in_a_code_block_is_not_checked(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n```\n[x](missing.md)\n```\n")
        self.assertEqual([], self.problems())

    def test_a_relative_link_with_non_ascii_letters_resolves(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001", body=BODY + "\n[hình](<sơ đồ.svg>)\n")
        (lesson_dir / "sơ đồ.svg").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], self.problems())

    def test_a_lesson_that_does_not_link_the_pinned_snapshot_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body="# Bài một\n\nKhông có nguồn.\n")
        self.assertProblem("pinned source snapshot")

    def test_a_mention_of_a_lesson_without_a_directory_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\nĐọc cùng sd-01-011.\n")
        self.assertProblem("mentions sd-01-011")

    def test_a_mention_of_an_existing_lesson_or_of_itself_is_accepted(self) -> None:
        self.write_source_map({"sd-01-001": ("Bài một", SNAPSHOT), "sd-01-002": ("Bài hai", SNAPSHOT)})
        self.write_lesson("sd-01-002", meta=self.meta(id="sd-01-002", title_vi="Bài hai"))
        self.write_readme(README + "| [sd-01-002](lessons/sd-01-002/lesson.md) | Bài hai |\n")
        self.write_lesson("sd-01-001", body=BODY + "\nXem sd-01-002 và chính sd-01-001.\n")
        self.assertEqual([], self.problems())


    def test_a_snapshot_url_in_a_code_block_is_not_a_link(self) -> None:
        self.write_lesson("sd-01-001", body=f"# Bài một\n\n```\n{SNAPSHOT}\n```\n")
        self.assertProblem("pinned source snapshot")

    def test_a_snapshot_url_in_an_html_comment_is_not_a_link(self) -> None:
        for name, comment in {"markdown link": f"<!-- [nguồn]({SNAPSHOT}) -->",
                              "html anchor": f'<!-- <a href="{SNAPSHOT}">nguồn</a> -->'}.items():
            with self.subTest(comment=name):
                self.write_lesson("sd-01-001", body=f"# Bài một\n\n{comment}\n")
                self.assertProblem("pinned source snapshot")

    def test_a_snapshot_url_in_plain_text_is_not_a_link(self) -> None:
        self.write_lesson("sd-01-001", body=f"# Bài một\n\nNguồn: {SNAPSHOT}\n")
        self.assertProblem("pinned source snapshot")

    def test_a_snapshot_given_as_an_html_anchor_is_a_link(self) -> None:
        self.write_lesson("sd-01-001", body=f'# Bài một\n\n<a href="{SNAPSHOT}">nguồn</a>\n')
        self.assertEqual([], self.problems())

    def test_href_text_inside_another_attribute_is_not_a_link(self) -> None:
        for name, tag in {"title": f"<a title='href=\"{SNAPSHOT}\"'>nguồn</a>",
                          "no href": f'<a data-x="{SNAPSHOT}">nguồn</a>',
                          "other tag": f'<span href="{SNAPSHOT}">nguồn</span>'}.items():
            with self.subTest(tag=name):
                self.write_lesson("sd-01-001", body=f"# Bài một\n\n{tag}\n")
                self.assertProblem("pinned source snapshot")

    def test_an_upper_case_or_single_quoted_html_anchor_is_a_link(self) -> None:
        for name, tag in {"upper case": f'<A HREF="{SNAPSHOT}">nguồn</A>',
                          "single quotes": f"<a href='{SNAPSHOT}'>nguồn</a>"}.items():
            with self.subTest(tag=name):
                self.write_lesson("sd-01-001", body=f"# Bài một\n\n{tag}\n")
                self.assertEqual([], self.problems())

    def test_a_snapshot_given_as_a_reference_style_link_is_a_link(self) -> None:
        self.write_lesson("sd-01-001", body=f"# Bài một\n\n[nguồn][s]\n\n[s]: {SNAPSHOT}\n")
        self.assertEqual([], self.problems())

    def test_every_form_of_source_image_embed_is_reported(self) -> None:
        url = "https://assets.bytebytego.com/diagrams/0001-x.png"
        forms = {
            "inline image": f"![]({url})",
            "reference-style image": f"![x][img]\n\n[img]: {url}",
            "html img": f'<img src="{url}">',
            "html picture": f'<picture><source srcset="{url}"></picture>',
            "bare url": url,
            "upper case host": "HTTPS://ASSETS.BYTEBYTEGO.COM/diagrams/0001-x.png",
            "plain mention of the host": "Ảnh nguồn ở assets.bytebytego.com chưa được mở.",
        }
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                self.assertProblem("lessons must not use source images")

    def test_a_src_attribute_on_a_tag_other_than_img_is_not_an_image(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + '\nH<sub src="missing.png">2</sub>O\n')
        self.assertEqual([], self.problems())

    def test_a_missing_or_non_svg_image_in_an_img_srcset_is_reported(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001", body=BODY + '\n<img srcset="one.svg 1x, two.svg 2x" alt="x">\n')
        (lesson_dir / "one.svg").write_text("<svg/>", encoding="utf-8")
        self.assertProblem("'two.svg' does not resolve")
        (lesson_dir / "two.svg").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], self.problems())
        self.write_lesson("sd-01-001", body=BODY + '\n<img srcset="one.svg 1x, two.png 2x" alt="x">\n')
        (lesson_dir / "two.png").write_bytes(b"x")
        self.assertProblem("'two.png' must be a local .svg file")

    def test_srcset_urls_are_split_like_the_html_spec_splits_them(self) -> None:
        cases = {
            "a.svg": ["a.svg"],
            "a.svg 1x, b.svg 2x": ["a.svg", "b.svg"],
            "a.svg, b.svg": ["a.svg", "b.svg"],
            "a.svg 1x,b.svg 2x": ["a.svg", "b.svg"],
            "a.svg,b.svg": ["a.svg,b.svg"],
            "  a.svg 100w ,  b.svg 200w  ": ["a.svg", "b.svg"],
            "a,b.svg 1x": ["a,b.svg"],
            "": [],
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(expected, check.srcset_urls(value))

    def test_raw_html_outside_the_allow_list_is_reported(self) -> None:
        forms = {
            "picture": '<picture><source srcset="a.svg"></picture>',
            "inline svg": '<svg><image href="a.png"/></svg>',
            "object": '<object data="a.svg"></object>',
            "video": '<video poster="a.png"></video>',
            "iframe": '<iframe src="https://example.com"></iframe>',
            "script": "<script>alert(1)</script>",
            "div": "<div>chữ</div>",
            "a closing tag without its opener": "</div>",
            "an inline closing tag without its opener": "chữ</span> nữa",
        }
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                self.assertProblem("raw HTML is limited to")

    def test_the_allowed_html_tags_are_accepted(self) -> None:
        body = (BODY + "\nH<sub>2</sub>O, x<sup>2</sup>, <kbd>Ctrl</kbd><br>dòng sau\n\n"
                "<details open>\n<summary>Gợi ý</summary>\n\nĐáp án.\n\n</details>\n")
        self.write_lesson("sd-01-001", body=body)
        self.assertEqual([], self.problems())

    def test_html_tags_inside_code_are_not_raw_html(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n`<div>`\n\n```html\n<picture></picture>\n```\n")
        self.assertEqual([], self.problems())

    def test_a_local_image_is_not_a_source_image(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001", body=BODY + "\n![sơ đồ](diagram.svg)\n")
        (lesson_dir / "diagram.svg").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], self.problems())

class ReadmeRuleTests(StoreCase):
    def test_a_lesson_missing_from_the_readme_is_reported(self) -> None:
        self.write_readme("# Kho\n")
        self.assertProblem("does not link lessons/sd-01-001/lesson.md")

    def test_a_readme_row_left_behind_for_a_deleted_lesson_is_reported(self) -> None:
        self.write_readme(README + "| [sd-01-009](lessons/sd-01-009/lesson.md) | Bài đã xóa |\n")
        self.assertProblem("relative link 'lessons/sd-01-009/lesson.md' does not resolve")
        self.write_readme(README + "[x][ref]\n\n[ref]: lessons/sd-01-009/lesson.md#phan-1\n")
        self.assertProblem("relative link 'lessons/sd-01-009/lesson.md#phan-1' does not resolve")
        self.write_readme(README + '<a href="lessons/sd-01-009/lesson.md">x</a>\n')
        self.assertProblem("'lessons/sd-01-009/lesson.md' does not resolve")

    def test_readme_links_that_are_not_relative_paths_are_not_looked_up(self) -> None:
        self.write_readme(README + "[web](https://example.com/x) [mail](mailto:a@b.c) [top](#kho)\n"
                          "[again](lessons/sd-01-001/lesson.md#phan-1)\n")
        self.assertEqual([], self.problems())

    def test_a_missing_readme_is_reported(self) -> None:
        (self.store / "README.md").unlink()
        self.assertProblem("README.md: is missing")

    def test_a_status_word_in_a_readme_row_is_reported(self) -> None:
        row = "| [sd-01-001](lessons/sd-01-001/lesson.md) | Bài một | drafted |\n"
        self.write_readme("# Kho\n\n| ID | Bài | Trạng thái |\n|---|---|---|\n" + row)
        self.assertProblem("repeats a lesson status")

    def test_a_formatted_or_capitalised_status_in_a_readme_row_is_reported(self) -> None:
        forms = {"bold": "**approved**", "code": "`drafted`", "capital": "Approved", "html": "<b>planned</b>",
                 "trailing dot": "drafted.", "emphasis": "_drafted_"}
        for name, cell in forms.items():
            with self.subTest(form=name):
                row = f"| [sd-01-001](lessons/sd-01-001/lesson.md) | Bài một | {cell} |\n"
                self.write_readme("# Kho\n\n| ID | Bài | Ghi chú |\n|---|---|---|\n" + row)
                self.assertProblem("repeats a lesson status")

    def test_a_status_in_a_row_whose_lesson_link_is_a_reference_is_reported(self) -> None:
        row = "| [sd-01-001][one] | Bài một | drafted |\n\n[one]: lessons/sd-01-001/lesson.md\n"
        self.write_readme("# Kho\n\n| ID | Bài | Ghi chú |\n|---|---|---|\n" + row)
        found = self.problems()
        self.assertTrue(any("repeats a lesson status" in line for line in found), found)
        self.assertFalse(any("does not link" in line for line in found), found)

    def test_an_html_anchor_whose_title_mentions_the_path_is_not_a_readme_link(self) -> None:
        path = "lessons/sd-01-001/lesson.md"
        self.write_readme(f"# Kho\n\n<a title='href=\"{path}\"'>bài một</a>\n")
        self.assertProblem("does not link lessons/sd-01-001/lesson.md")

    def test_a_table_without_outer_pipes_or_with_an_indented_row_is_still_inspected(self) -> None:
        link = "[sd-01-001](lessons/sd-01-001/lesson.md)"
        forms = {"no outer pipes": f"ID | Bài | Ghi chú\n--- | --- | ---\n{link} | Bài một | drafted",
                 "indented rows": f"  | ID | Bài | Ghi chú |\n  |---|---|---|\n  | {link} | Bài một | drafted |"}
        for name, table in forms.items():
            with self.subTest(table=name):
                self.write_readme(f"# Kho\n\n{table}\n")
                self.assertProblem("repeats a lesson status")

    def test_a_table_shown_inside_a_code_block_is_not_a_readme_table(self) -> None:
        self.write_readme(README + "\n```\n| ID | Ghi chú |\n|---|---|\n| sd-01-001 | drafted |\n```\n")
        self.assertEqual([], self.problems())

    def test_a_readme_link_with_a_fragment_a_query_or_encoding_still_links_the_lesson(self) -> None:
        forms = {"fragment": "lessons/sd-01-001/lesson.md#vi-du", "query": "lessons/sd-01-001/lesson.md?x=1",
                 "encoded": "lessons/sd%2D01%2D001/lesson.md"}
        for name, target in forms.items():
            with self.subTest(link=name):
                self.write_readme(f"# Kho\n\n[bài một]({target})\n")
                self.assertEqual([], self.problems())

    def test_a_status_word_inside_a_longer_title_is_not_a_status(self) -> None:
        row = "| [sd-01-001](lessons/sd-01-001/lesson.md) | Bài đã drafted xong |\n"
        self.write_readme("# Kho\n\n| ID | Bài |\n|---|---|\n" + row)
        self.assertEqual([], self.problems())

    def test_a_readme_path_in_a_comment_a_code_block_or_prose_is_not_a_link(self) -> None:
        path = "lessons/sd-01-001/lesson.md"
        forms = {"html comment": f"<!-- [x]({path}) -->", "code block": f"```\n[x]({path})\n```",
                 "plain prose": f"Xem {path} nhé."}
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_readme(f"# Kho\n\n{form}\n")
                self.assertProblem("does not link lessons/sd-01-001/lesson.md")

    def test_a_readme_link_as_an_html_anchor_or_a_reference_or_with_dot_slash_counts(self) -> None:
        path = "lessons/sd-01-001/lesson.md"
        forms = {"html anchor": f'<a href="{path}">bài một</a>', "reference": f"[bài một][s]\n\n[s]: {path}",
                 "dot slash": f"[bài một](./{path})"}
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_readme(f"# Kho\n\n{form}\n")
                self.assertEqual([], self.problems())


class CommandLineTests(StoreCase):
    def run_main(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check.main(["--store", str(self.store), "--source-map", str(self.source_map)])
        return code, out.getvalue()

    def test_a_clean_store_exits_zero_and_says_how_many_lessons(self) -> None:
        code, output = self.run_main()
        self.assertEqual(0, code)
        self.assertIn("1 lesson(s), 0 problem(s)", output)

    def test_a_broken_store_exits_one_and_prints_the_problem(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(content_status="done"))
        code, output = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("sd-01-001: content_status", output)


if __name__ == "__main__":
    unittest.main()
