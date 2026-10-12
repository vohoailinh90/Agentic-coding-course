"""scripts/sd101_check.py: the Vietnamese System Design store rules, on fixtures and on the real store."""

from __future__ import annotations

import contextlib
import copy
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

    def test_an_image_evidence_entry_without_a_digest_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[{"url": "https://x/y.png"}]))
        self.assertProblem("image_evidence entry needs")


class LessonMarkdownRuleTests(StoreCase):
    def test_an_unclosed_code_fence_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n```mermaid\nflowchart TB\n")
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

    def test_a_local_image_is_not_a_source_image(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001", body=BODY + "\n![sơ đồ](diagram.svg)\n")
        (lesson_dir / "diagram.svg").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], self.problems())

class ReadmeRuleTests(StoreCase):
    def test_a_lesson_missing_from_the_readme_is_reported(self) -> None:
        self.write_readme("# Kho\n")
        self.assertProblem("does not link lessons/sd-01-001/lesson.md")

    def test_a_missing_readme_is_reported(self) -> None:
        (self.store / "README.md").unlink()
        self.assertProblem("README.md: is missing")

    def test_a_status_word_in_a_readme_row_is_reported(self) -> None:
        row = "| [sd-01-001](lessons/sd-01-001/lesson.md) | Bài một | drafted |\n"
        self.write_readme("# Kho\n\n| ID | Bài | Trạng thái |\n|---|---|---|\n" + row)
        self.assertProblem("repeats a lesson status")

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
