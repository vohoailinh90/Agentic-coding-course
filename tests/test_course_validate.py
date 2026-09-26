"""The content-store validator: each test breaks the miniature store in one way.

tests/mutations/course_validate.yaml removes each check in turn and names the
test here that must notice.
"""

from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

from src.core.model import ROOT
from src.core.validate import validate
from tests.course_fixtures import CURRICULUM, dump, make_store, write_lesson, write_outline


def codes(report) -> list[str]:
    return [finding.code for finding in report.errors]


class ValidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_store(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def edit_curriculum(self, change) -> None:
        data = yaml.safe_load((self.root / "course/curriculum.yaml").read_text(encoding="utf-8"))
        change(data)
        dump(self.root / "course/curriculum.yaml", data)

    # -- the baseline ---------------------------------------------------------

    def test_the_fixture_store_is_valid(self) -> None:
        report = validate(self.root)
        self.assertEqual(report.errors, [])
        self.assertIsNotNone(report.course)
        self.assertEqual([lesson.number for lesson in report.course.lessons], ["1.1.1", "1.1.2"])
        self.assertEqual(len(report.docs), 3)

    def test_the_committed_content_store_is_valid(self) -> None:
        report = validate(ROOT)
        self.assertEqual([(f.code, f.params) for f in report.errors], [])

    # -- YAML files -----------------------------------------------------------

    def test_a_duplicate_yaml_key_is_an_error(self) -> None:
        path = self.root / "course/course.yaml"
        path.write_text(path.read_text(encoding="utf-8") + "id: again\n", encoding="utf-8")
        self.assertIn("yaml_invalid", codes(validate(self.root)))

    def test_a_value_split_by_a_flow_mapping_comma_is_reported(self) -> None:
        # In a flow mapping a comma ends the value, so this title parses as
        # vi="Cơ bản" plus a key "dễ hiểu" with no value — valid YAML, wrong data.
        path = self.root / "course/curriculum.yaml"
        block = "    title:\n      vi: Cơ bản\n      en: Basics\n      ja: 基本\n"
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count(block), 1)
        path.write_text(
            text.replace(block, "    title: {vi: Cơ bản, dễ hiểu, en: Basics, ja: 基本}\n"), encoding="utf-8"
        )
        report = validate(self.root)
        self.assertIn(("field_unknown", "modules[start].units[basics].title.dễ hiểu"),
                      [(f.code, f.params.get("field")) for f in report.errors])

    def test_a_missing_language_in_a_title_is_an_error(self) -> None:
        self.edit_curriculum(lambda data: data["modules"][0]["title"].pop("ja"))
        report = validate(self.root)
        self.assertIn("field_missing", codes(report))
        self.assertIsNone(report.course)

    def test_a_duplicate_id_is_an_error(self) -> None:
        def change(data):
            data["modules"][0]["units"][0]["lessons"][1]["id"] = "alpha"
        self.edit_curriculum(change)
        self.assertIn("id_duplicate", codes(validate(self.root)))

    def test_an_id_that_is_not_a_slug_is_an_error(self) -> None:
        def change(data):
            data["modules"][0]["units"][0]["id"] = "Basics Unit"
        self.edit_curriculum(change)
        self.assertIn("id_invalid", codes(validate(self.root)))

    def test_an_unknown_glossary_term_is_an_error(self) -> None:
        def change(data):
            data["modules"][0]["units"][0]["lessons"][0]["terms"].append("no-such-term")
        self.edit_curriculum(change)
        self.assertIn("term_unknown", codes(validate(self.root)))

    def test_an_unknown_lesson_type_is_an_error(self) -> None:
        def change(data):
            data["modules"][0]["units"][0]["lessons"][1]["type"] = "lecture"
        self.edit_curriculum(change)
        self.assertIn("value_invalid", codes(validate(self.root)))

    def test_minutes_must_be_a_positive_whole_number(self) -> None:
        for bad in (0, -5, 2.5, True, "10"):
            with self.subTest(minutes=bad):
                def change(data, bad=bad):
                    data["modules"][0]["units"][0]["lessons"][1]["minutes"] = bad
                self.edit_curriculum(change)
                self.assertIn("field_type", codes(validate(self.root)))

    def test_an_unused_glossary_term_is_only_a_warning(self) -> None:
        def change(data):
            data["modules"][0]["units"][0]["lessons"][0]["terms"] = ["agent"]
        self.edit_curriculum(change)
        write_outline(self.root)
        report = validate(self.root)
        self.assertEqual(report.errors, [])
        self.assertEqual([f.code for f in report.warnings], ["term_unused"])

    # -- lesson folders and files ---------------------------------------------

    def test_a_missing_language_file_is_an_error(self) -> None:
        (self.root / "course/lessons/alpha/ja.md").unlink()
        self.assertIn("lesson_file_missing", codes(validate(self.root)))

    def test_an_unknown_lesson_folder_is_an_error(self) -> None:
        (self.root / "course/lessons/gamma").mkdir()
        self.assertIn("lesson_dir_unknown", codes(validate(self.root)))

    def test_an_unexpected_file_in_a_lesson_folder_is_an_error(self) -> None:
        (self.root / "course/lessons/alpha/notes.txt").write_text("x", encoding="utf-8")
        self.assertIn("lesson_file_unexpected", codes(validate(self.root)))

    def test_an_assets_folder_is_allowed(self) -> None:
        (self.root / "course/lessons/alpha/assets").mkdir()
        self.assertEqual(validate(self.root).errors, [])

    def test_front_matter_that_disagrees_with_the_path_is_an_error(self) -> None:
        path = self.root / "course/lessons/alpha/ja.md"
        path.write_text(path.read_text(encoding="utf-8").replace("lang: ja", "lang: en"), encoding="utf-8")
        self.assertIn("front_matter_mismatch", codes(validate(self.root)))

    def test_an_unknown_front_matter_field_is_an_error(self) -> None:
        path = self.root / "course/lessons/alpha/en.md"
        path.write_text(path.read_text(encoding="utf-8").replace("status:", "tags: []\nstatus:"), encoding="utf-8")
        self.assertIn("field_unknown", codes(validate(self.root)))

    def test_a_title_that_differs_from_the_curriculum_is_an_error(self) -> None:
        write_lesson(self.root, "alpha", "en", title="A different title")
        self.assertIn("title_mismatch", codes(validate(self.root)))

    def test_a_file_saved_on_windows_is_read_the_same(self) -> None:
        path = self.root / "course/lessons/alpha/vi.md"
        text = path.read_text(encoding="utf-8")
        path.write_bytes(("﻿" + text.replace("\n", "\r\n")).encode("utf-8"))
        self.assertEqual(validate(self.root).errors, [])

    # -- sections and status ----------------------------------------------------

    def test_an_unknown_section_is_an_error(self) -> None:
        write_lesson(self.root, "alpha", "en", sections=("objective", "hook", "concept", "analogy",
                                                         "example", "takeaways", "quiz", "homework"))
        self.assertIn("section_unknown", codes(validate(self.root)))

    def test_a_section_out_of_order_is_an_error(self) -> None:
        order = ("objective", "concept", "hook", "analogy", "example", "takeaways", "quiz")
        for language in ("vi", "en", "ja"):
            write_lesson(self.root, "alpha", language, sections=order)
        self.assertIn("section_order", codes(validate(self.root)))

    def test_a_required_section_missing_from_a_draft_is_an_error(self) -> None:
        without_quiz = ("objective", "hook", "concept", "analogy", "example", "takeaways")
        for language in ("vi", "en", "ja"):
            write_lesson(self.root, "alpha", language, status="draft", sections=without_quiz)
        self.assertIn("section_required", codes(validate(self.root)))

    def test_a_skeleton_may_miss_required_sections(self) -> None:
        write_lesson(self.root, "alpha", "ja", status="todo", sections=("objective",))
        self.assertEqual(validate(self.root).errors, [])

    def test_an_empty_section_in_review_is_an_error(self) -> None:
        write_lesson(self.root, "alpha", "en", bodies={"analogy": "<!-- nothing yet -->"})
        self.assertIn("section_empty", codes(validate(self.root)))

    def test_a_todo_placeholder_left_in_review_is_an_error(self) -> None:
        write_lesson(self.root, "alpha", "en", bodies={"example": "Text.\n\n<!-- TODO: add the second step -->"})
        self.assertIn("todo_left", codes(validate(self.root)))

    def test_a_draft_may_keep_todo_placeholders(self) -> None:
        for language in ("vi", "en", "ja"):
            write_lesson(self.root, "alpha", language, status="draft", bodies={"quiz": "<!-- TODO: write it -->"})
        self.assertEqual(validate(self.root).errors, [])

    def test_a_review_file_needs_a_summary(self) -> None:
        write_lesson(self.root, "alpha", "en", summary="")
        self.assertIn("field_empty", codes(validate(self.root)))

    def test_a_done_file_needs_the_social_hook_and_question(self) -> None:
        write_lesson(self.root, "alpha", "en", status="done", hook="", question="")
        fields = [f.params.get("field") for f in validate(self.root).errors if f.code == "field_empty"]
        self.assertEqual(sorted(fields), ["social.hook", "social.question"])

    def test_sections_that_differ_between_languages_are_an_error(self) -> None:
        with_misconceptions = ("objective", "hook", "concept", "analogy", "example",
                               "misconceptions", "takeaways", "quiz")
        write_lesson(self.root, "alpha", "ja", sections=with_misconceptions)
        report = validate(self.root)
        self.assertIn("sections_differ", codes(report))
        finding = next(f for f in report.errors if f.code == "sections_differ")
        self.assertEqual((finding.params["lang"], finding.params["other"]), ("ja", "vi"))

    def test_a_skeleton_is_exempt_from_section_parity(self) -> None:
        write_lesson(self.root, "alpha", "ja", status="todo", sections=("objective", "hook"))
        self.assertEqual(validate(self.root).errors, [])

    # -- OUTLINE.md --------------------------------------------------------------

    def test_a_stale_outline_is_an_error(self) -> None:
        def change(data):
            data["modules"][0]["units"][0]["lessons"][1]["minutes"] = 20
        self.edit_curriculum(change)
        self.assertIn("outline_stale", codes(validate(self.root)))
        write_outline(self.root)
        self.assertEqual(validate(self.root).errors, [])

    def test_a_missing_outline_is_an_error(self) -> None:
        (self.root / "course/OUTLINE.md").unlink()
        self.assertIn("outline_stale", codes(validate(self.root)))

    def test_the_fixture_curriculum_is_not_shared_between_tests(self) -> None:
        # edit_curriculum works on a copy read from disk, never on the module constant
        self.assertEqual(CURRICULUM["modules"][0]["units"][0]["lessons"][1]["minutes"], 15)


if __name__ == "__main__":
    unittest.main()


# One of each shape a hand edit produces: null, empty, number, boolean, the wrong
# container, and an unhashable value inside a list.
BAD_VALUES = (None, "", 0, True, [], {}, ["x"], {"x": 1}, [{"x": 1}])


def _fast_dump(data) -> str:
    """YAML text via libyaml when PyYAML has it: the fuzz below writes a file per value."""
    return yaml.dump(data, Dumper=getattr(yaml, "CSafeDumper", yaml.SafeDumper), allow_unicode=True)


def _paths(node, prefix=()):
    """Every key path in a YAML document, the document itself excluded."""
    if prefix:
        yield prefix
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _paths(value, prefix + (key,))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _paths(value, prefix + (index,))


def _replaced(document, path, value):
    copy = deepcopy(document)
    node = copy
    for step in path[:-1]:
        node = node[step]
    node[path[-1]] = value
    return copy


class RobustnessTests(unittest.TestCase):
    """Hand-edited files will hold wrong types; the validator must report them, never crash."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_store(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def assert_never_crashes(self, path: Path, document, *, write=None) -> None:
        write = write or (lambda data: path.write_text(_fast_dump(data), encoding="utf-8"))
        original = path.read_bytes()
        try:
            for key_path in _paths(document):
                for value in BAD_VALUES:
                    write(_replaced(document, key_path, value))
                    try:
                        validate(self.root, check_outline=False)
                    except Exception as exc:  # noqa: BLE001 - any crash is the failure
                        self.fail(f"{path.name} {key_path!r} = {value!r}: {type(exc).__name__}: {exc}")
        finally:
            path.write_bytes(original)

    def test_wrong_types_in_the_yaml_files_are_reported_not_crashed_on(self) -> None:
        for name in ("course.yaml", "curriculum.yaml", "glossary.yaml"):
            with self.subTest(file=name):
                path = self.root / "course" / name
                self.assert_never_crashes(path, yaml.safe_load(path.read_text(encoding="utf-8")))
        # One entry stands for every section: each has the same shape.
        path = self.root / "course" / "sections.yaml"
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assert_never_crashes(path, {"sections": document["sections"][:1]})

    def test_wrong_types_in_lesson_front_matter_are_reported_not_crashed_on(self) -> None:
        path = self.root / "course/lessons/alpha/vi.md"
        text = path.read_text(encoding="utf-8")
        _, front, body = text.split("---\n", 2)

        def write(data) -> None:
            path.write_text("---\n" + _fast_dump(data) + "---\n" + body, encoding="utf-8")

        self.assert_never_crashes(path, yaml.safe_load(front), write=write)
