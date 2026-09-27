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
from tests.course_fixtures import (
    CURRICULUM,
    DIAGRAM,
    DIAGRAM_ID,
    RECAP,
    RECAP_ID,
    dump,
    language_bar,
    make_store,
    quiz_body,
    write_generated,
    write_lesson,
)


def codes(report) -> list[str]:
    return [finding.code for finding in report.errors]


class StoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_store(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def edit_yaml(self, relative: str, change) -> None:
        path = self.root / relative
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        change(data)
        dump(path, data)

    def edit_curriculum(self, change) -> None:
        self.edit_yaml("course/data/curriculum.yaml", change)

    def edit_diagram(self, change) -> None:
        self.edit_yaml(f"course/data/diagrams/{DIAGRAM_ID}.yaml", change)


class ValidateTests(StoreTest):
    # -- the baseline ---------------------------------------------------------

    def test_the_fixture_store_is_valid(self) -> None:
        report = validate(self.root)
        self.assertEqual(report.errors, [])
        self.assertIsNotNone(report.course)
        self.assertEqual([lesson.number for lesson in report.course.lessons], ["1.1.1", "1.1.2"])
        self.assertEqual(len(report.docs), 3)
        self.assertEqual(report.started, {"alpha"})

    def test_the_committed_content_store_is_valid(self) -> None:
        report = validate(ROOT)
        self.assertEqual([(f.code, f.params) for f in report.errors], [])

    # -- data files -----------------------------------------------------------

    def test_a_duplicate_yaml_key_is_an_error(self) -> None:
        path = self.root / "course/data/course.yaml"
        path.write_text(path.read_text(encoding="utf-8") + "id: again\n", encoding="utf-8")
        self.assertIn("yaml_invalid", codes(validate(self.root)))

    def test_a_value_split_by_a_flow_mapping_comma_is_reported(self) -> None:
        # In a flow mapping a comma ends the value, so this title parses as
        # vi="Cơ bản" plus a key "dễ hiểu" with no value — valid YAML, wrong data.
        path = self.root / "course/data/curriculum.yaml"
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
        write_generated(self.root)
        report = validate(self.root)
        self.assertEqual(report.errors, [])
        self.assertEqual([f.code for f in report.warnings], ["term_unused"])

    def test_the_fixture_curriculum_is_not_shared_between_tests(self) -> None:
        # edit_curriculum works on a copy read from disk, never on the module constant
        self.assertEqual(CURRICULUM["modules"][0]["units"][0]["lessons"][1]["minutes"], 15)

    # -- infographic specs ----------------------------------------------------

    def test_an_unknown_template_is_an_error(self) -> None:
        self.edit_diagram(lambda spec: spec.update(template="pie"))
        self.assertIn("value_invalid", codes(validate(self.root)))

    def test_a_comparison_needs_two_to_four_columns(self) -> None:
        self.edit_diagram(lambda spec: spec["columns"].pop())
        self.assertIn("field_count", codes(validate(self.root)))

    def test_every_column_has_a_value_for_every_row(self) -> None:
        self.edit_diagram(lambda spec: spec["rows"].append({"vi": "Thêm", "en": "More", "ja": "追加"}))
        self.assertIn("field_count", codes(validate(self.root)))

    def test_a_colour_outside_the_palette_is_an_error(self) -> None:
        def change(spec):
            spec["columns"][0]["color"] = "chartreuse"
        self.edit_diagram(change)
        self.assertIn("value_invalid", codes(validate(self.root)))

    def test_versus_needs_exactly_two_columns(self) -> None:
        def change(spec):
            spec["columns"].append(deepcopy(spec["columns"][0]))
        self.edit_diagram(change)
        self.assertIn("value_invalid", codes(validate(self.root)))

    def test_the_roadmap_id_is_reserved(self) -> None:
        source = self.root / f"course/data/diagrams/{DIAGRAM_ID}.yaml"
        source.rename(self.root / "course/data/diagrams/roadmap.yaml")
        self.assertIn("id_invalid", codes(validate(self.root)))

    def test_a_diagram_missing_a_language_is_an_error(self) -> None:
        self.edit_diagram(lambda spec: spec["title"].pop("en"))
        self.assertIn("field_missing", codes(validate(self.root)))

    def test_a_diagram_with_more_text_than_its_template_can_draw_is_an_error(self) -> None:
        def text() -> dict:
            return {"vi": "một câu chú thích dài, dài hơn nhiều so với mức một sơ đồ cần có " * 2,
                    "en": "a caption that is much longer than any diagram should ever need " * 2,
                    "ja": "図に必要な長さをはるかに超える、とても長い説明の文章です。" * 2}

        steps = [{"icon": "🔁", "color": "teal", "name": text(), "caption": text(), "arrow": text()} for _ in range(6)]
        spec = {"template": "cycle", "title": text(), "steps": steps, "center": {"icon": "🤖", "name": text()}}
        dump(self.root / "course/data/diagrams/crowded.yaml", spec)
        found = {(f.code, f.params.get("path"), f.params.get("language")) for f in validate(self.root).errors}
        for language in ("vi", "en", "ja"):
            self.assertIn(("diagram_crowded", "course/data/diagrams/crowded.yaml", language), found)

    def test_a_diagram_that_cuts_a_word_in_two_is_an_error(self) -> None:
        self.edit_diagram(lambda spec: spec["columns"][0]["values"][0].update(
            {"en": "Supercalifragilisticexpialidocious-and-then-some"}))
        errors = validate(self.root).errors
        found = [f for f in errors if f.code == "diagram_word_split"]
        self.assertEqual([(f.params["language"], f.params["words"]) for f in found],
                         [("en", "Supercalifragilisticexpialidocious-and-then-some")])

    # -- tracks, the minimum path and retired ids --------------------------------

    def test_the_roadmap_fields_reach_the_course(self) -> None:
        course = validate(self.root).course
        self.assertEqual(course.minimum_path, ("alpha",))
        self.assertEqual(course.retired, {"old-alpha": "alpha"})
        self.assertEqual([lesson.track for lesson in course.lessons], ["core", "core"])

    def test_a_unit_track_outside_the_list_is_an_error(self) -> None:
        self.edit_curriculum(lambda c: c["modules"][0]["units"][0].update(track="bonus"))
        self.assertIn("value_invalid", codes(validate(self.root)))

    def test_a_minimum_path_lesson_that_does_not_exist_is_an_error(self) -> None:
        self.edit_curriculum(lambda c: c["minimum_path"].append("gamma"))
        self.assertIn("minimum_path_unknown", codes(validate(self.root)))

    def test_a_lesson_twice_on_the_minimum_path_is_an_error(self) -> None:
        self.edit_curriculum(lambda c: c["minimum_path"].append("alpha"))
        self.assertIn("id_duplicate", codes(validate(self.root)))

    def test_an_optional_lesson_on_the_minimum_path_is_an_error(self) -> None:
        self.edit_curriculum(lambda c: c["modules"][0]["units"][0].update(track="optional"))
        self.assertIn("minimum_path_track", codes(validate(self.root)))

    def test_a_minimum_path_out_of_course_order_is_an_error(self) -> None:
        self.edit_curriculum(lambda c: c.update(minimum_path=["beta", "alpha"]))
        self.assertIn("minimum_path_order", codes(validate(self.root)))

    def test_a_retired_id_still_in_use_is_an_error(self) -> None:
        self.edit_curriculum(lambda c: c["retired"].append({"id": "beta", "into": "alpha"}))
        self.assertIn("retired_in_use", codes(validate(self.root)))

    def test_a_retired_id_merged_into_an_unknown_lesson_is_an_error(self) -> None:
        self.edit_curriculum(lambda c: c["retired"][0].update(into="gamma"))
        self.assertIn("retired_target_unknown", codes(validate(self.root)))

    def test_an_id_retired_twice_is_an_error(self) -> None:
        self.edit_curriculum(lambda c: c["retired"].append({"id": "old-alpha"}))
        self.assertIn("id_duplicate", codes(validate(self.root)))

    # -- the recap infographic ---------------------------------------------------

    def test_a_finished_lesson_without_its_recap_infographic_is_an_error(self) -> None:
        write_lesson(self.root, "alpha", "vi", bodies={"recap": "- Chatbot trả lời, agent hành động."})
        self.assertIn("recap_diagram", codes(validate(self.root)))

    def test_a_recap_shows_exactly_one_infographic(self) -> None:
        both = f"![a](../diagrams/{RECAP_ID}.svg)\n\n![b](../diagrams/{RECAP_ID}.svg)"
        write_lesson(self.root, "alpha", "vi", bodies={"recap": both})
        self.assertIn("recap_diagram", codes(validate(self.root)))

    def test_a_recap_image_that_is_no_infographic_is_an_error(self) -> None:
        for target in ("https://example.com/recap.png", "../images/recap.png"):
            with self.subTest(target=target):
                write_lesson(self.root, "alpha", "vi", bodies={"recap": f"![x]({target})"})
                self.assertIn("recap_diagram", codes(validate(self.root)))

    def test_a_recap_that_repeats_a_diagram_of_the_lesson_is_an_error(self) -> None:
        for language in ("vi", "en", "ja"):
            write_lesson(self.root, "alpha", language, bodies={"recap": f"![x](../diagrams/{DIAGRAM_ID}.svg)"})
        self.assertEqual(codes(validate(self.root)), ["recap_reused"] * 3)

    def test_a_draft_may_leave_its_recap_for_later(self) -> None:
        for language in ("vi", "en", "ja"):
            write_lesson(self.root, "alpha", language, status="draft", bodies={"recap": "<!-- TODO: recap -->"})
        self.assertEqual(validate(self.root).errors, [])

    def test_a_lesson_without_a_recap_section_is_an_error(self) -> None:
        sections = ("objective", "hook", "concept", "analogy", "example", "takeaways", "quiz")
        write_lesson(self.root, "alpha", "vi", sections=sections)
        self.assertIn("section_required", codes(validate(self.root)))

    # -- course folders and lesson files ---------------------------------------

    def test_a_missing_language_file_is_an_error(self) -> None:
        (self.root / "course/ja/lessons/alpha.md").unlink()
        self.assertIn("lesson_file_missing", codes(validate(self.root)))

    def test_an_unknown_lesson_file_is_an_error(self) -> None:
        (self.root / "course/vi/lessons/gamma.md").write_text("x", encoding="utf-8")
        self.assertIn("lesson_file_unknown", codes(validate(self.root)))

    def test_unexpected_entries_in_the_course_folders_are_errors(self) -> None:
        for relative in ("course/notes.md", "course/vi/notes.md", "course/data/extra.yaml",
                         "course/vi/lessons/notes.txt"):
            with self.subTest(path=relative):
                (self.root / relative).write_text("x", encoding="utf-8")
                self.assertIn(("entry_unexpected", relative),
                              [(f.code, f.params.get("path")) for f in validate(self.root).errors])
                (self.root / relative).unlink()

    def test_an_images_folder_is_allowed(self) -> None:
        (self.root / "course/vi/images").mkdir()
        self.assertEqual(validate(self.root).errors, [])

    def test_front_matter_that_disagrees_with_the_path_is_an_error(self) -> None:
        path = self.root / "course/ja/lessons/alpha.md"
        path.write_text(path.read_text(encoding="utf-8").replace("lang: ja", "lang: en"), encoding="utf-8")
        self.assertIn("front_matter_mismatch", codes(validate(self.root)))

    def test_an_unknown_front_matter_field_is_an_error(self) -> None:
        path = self.root / "course/en/lessons/alpha.md"
        path.write_text(path.read_text(encoding="utf-8").replace("status:", "tags: []\nstatus:"), encoding="utf-8")
        self.assertIn("field_unknown", codes(validate(self.root)))

    def test_a_title_that_differs_from_the_curriculum_is_an_error(self) -> None:
        write_lesson(self.root, "alpha", "en", title="A different title")
        self.assertIn("title_mismatch", codes(validate(self.root)))

    def test_a_wrong_or_missing_language_bar_is_an_error(self) -> None:
        wrong = language_bar("alpha", "vi").replace("**Tiếng Việt**", "[Tiếng Việt](x.md)")
        for bar in (wrong, "", language_bar("alpha", "en")):
            with self.subTest(bar=bar):
                write_lesson(self.root, "alpha", "vi", bar=bar)
                self.assertIn("language_bar", codes(validate(self.root)))

    def test_a_file_saved_on_windows_is_read_the_same(self) -> None:
        path = self.root / "course/vi/lessons/alpha.md"
        text = path.read_text(encoding="utf-8")
        path.write_bytes(("﻿" + text.replace("\n", "\r\n")).encode("utf-8"))
        self.assertEqual(validate(self.root).errors, [])

    # -- images and links --------------------------------------------------------

    def test_an_image_that_is_no_diagram_is_an_error(self) -> None:
        write_lesson(self.root, "alpha", "vi", bodies={"concept": "Text.\n\n![Sơ đồ](../diagrams/nope.svg)"})
        self.assertIn("diagram_unknown", codes(validate(self.root)))

    def test_an_image_needs_alt_text(self) -> None:
        write_lesson(self.root, "alpha", "vi", bodies={"concept": f"Text.\n\n![](../diagrams/{DIAGRAM_ID}.svg)"})
        self.assertIn("image_alt_missing", codes(validate(self.root)))

    def test_a_broken_relative_link_is_an_error(self) -> None:
        body = f"See [the glossary](../glossary.md) and [missing](../nowhere.md).\n\n![x](../diagrams/{DIAGRAM_ID}.svg)"
        write_lesson(self.root, "alpha", "vi", bodies={"concept": body})
        report = validate(self.root)
        self.assertEqual([(f.code, f.params.get("target")) for f in report.errors],
                         [("link_broken", "../nowhere.md")])

    def test_a_missing_image_file_is_an_error(self) -> None:
        body = f"![Ảnh](../images/photo.png)\n\n![x](../diagrams/{DIAGRAM_ID}.svg)"
        write_lesson(self.root, "alpha", "vi", bodies={"concept": body})
        self.assertIn("link_broken", codes(validate(self.root)))

    def test_links_inside_code_blocks_are_not_checked(self) -> None:
        body = f"```markdown\n[example](../nowhere.md)\n```\n\n![x](../diagrams/{DIAGRAM_ID}.svg)"
        write_lesson(self.root, "alpha", "vi", bodies={"concept": body})
        self.assertEqual(validate(self.root).errors, [])

    # -- sections, status and parity -------------------------------------------

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

    def test_diagrams_that_differ_between_languages_are_an_error(self) -> None:
        write_lesson(self.root, "alpha", "en", bodies={"concept": "No picture here."})
        self.assertIn("diagrams_differ", codes(validate(self.root)))

    def test_a_skeleton_is_exempt_from_parity(self) -> None:
        write_lesson(self.root, "alpha", "ja", status="todo", sections=("objective", "hook"))
        self.assertEqual(validate(self.root).errors, [])

    # -- quizzes, and pointing at other lessons -------------------------------------

    def test_a_quiz_answered_differently_in_another_language_is_an_error(self) -> None:
        write_lesson(self.root, "alpha", "ja", bodies={"quiz": quiz_body("BAC")})
        report = validate(self.root)
        self.assertEqual(codes(report), ["quiz_key_differs"])
        params = report.errors[0].params
        self.assertEqual((params["lang"], params["other"], params["actual"], params["expected"]),
                         ("ja", "vi", "BAC", "BCA"))

    def test_a_quiz_missing_an_option_or_an_answer_is_an_error(self) -> None:
        no_third_answer = quiz_body().replace("\n3. **A** — why.", "")
        for body in (quiz_body(letters="AB"), quiz_body("BC"), quiz_body("BCD"), no_third_answer):
            with self.subTest(body=body):
                write_lesson(self.root, "alpha", "en", bodies={"quiz": body})
                self.assertEqual(codes(validate(self.root)), ["quiz_shape"])

    def test_a_quiz_needs_three_numbered_questions_with_their_own_options(self) -> None:
        valid = quiz_body()
        all_options_under_one = "\n".join(
            line for line in valid.splitlines()
            if not line.startswith("**Question 2.") and not line.startswith("**Question 3.")
        ).replace("<details>", "**Question 2.** Question 2?\n\n**Question 3.** Question 3?\n\n<details>")
        cases = (
            "\n".join(line for line in valid.splitlines() if not line.startswith("**Question")),
            all_options_under_one,
            valid.replace("**Question 2.** Question 2?", "**Question 1.** Question 2?"),
            valid.replace("**Question 2.** Question 2?", "**Question 3.** Question 2?")
                 .replace("**Question 3.** Question 3?", "**Question 2.** Question 3?"),
        )
        for body in cases:
            with self.subTest(body=body):
                write_lesson(self.root, "alpha", "en", bodies={"quiz": body})
                self.assertEqual(codes(validate(self.root)), ["quiz_shape"])

    def test_a_quiz_whose_answers_are_all_one_letter_is_a_warning(self) -> None:
        for language in ("vi", "en", "ja"):
            write_lesson(self.root, "alpha", language, bodies={"quiz": quiz_body("BBB")})
        report = validate(self.root)
        self.assertEqual(report.errors, [])
        letters = [f.params["letter"] for f in report.warnings if f.code == "quiz_one_letter"]
        self.assertEqual(letters, ["B"] * 3)

    def test_a_draft_may_leave_its_quiz_unfinished(self) -> None:
        for language in ("vi", "en", "ja"):
            write_lesson(self.root, "alpha", language, status="draft", bodies={"quiz": quiz_body(letters="AB")})
        self.assertEqual(validate(self.root).errors, [])

    def test_a_lesson_pointed_at_by_number_or_position_is_an_error(self) -> None:
        cases = {
            "vi": (("Như đã thấy ở bài trước, agent đọc file.", "ở bài trước"),
                   ("Xem bài tiếp để biết thêm.", "bài tiếp"),
                   ("Bài vừa qua đã giải thích agent.", "Bài vừa qua")),
            "en": (("As in Lesson 4, the agent reads files.", "Lesson 4"),
                   ("See previous lesson for details.", "previous lesson"),
                   ("The following module explains agents.", "The following module")),
            "ja": (("次のレッスンで詳しく見ます。", "次のレッスン"),
                   ("前回のレッスンを見てください。", "前回のレッスン"),
                   ("次回のモジュールで説明します。", "次回のモジュール")),
        }
        for language, sentences in cases.items():
            for sentence, text in sentences:
                with self.subTest(language=language, sentence=sentence):
                    path = write_lesson(self.root, "alpha", language, bodies={"hook": sentence})
                    line = path.read_text(encoding="utf-8").split("\n").index(sentence) + 1
                    report = validate(self.root)
                    self.assertEqual(codes(report), ["lesson_by_position"])
                    finding = report.errors[0]
                    self.assertEqual((finding.params["text"], finding.params["line"]), (text, line))
                    write_lesson(self.root, "alpha", language)

    def test_later_lessons_steps_and_code_blocks_point_at_no_lesson(self) -> None:
        bodies = {
            "vi": "Thẻ này đi cùng bạn ở các bài sau. Bước 1: mở thư mục. Làm bài trước khi xem đáp án."
                  " Tối nay Mai ôn bài kế toán."
                  "\n\n```text\nXem bài 3\n```",
            "en": "You will use it in later lessons. Step 1: open the folder. Read the answer later."
                  "\n\n```text\nsee previous lesson and lesson 3\n```",
            "ja": "この先のレッスンでも使います。手順1：フォルダを開く。あとで答えを読みます。"
                  "\n\n```text\n前回のレッスンとレッスン3\n```",
        }
        for language, body in bodies.items():
            write_lesson(self.root, "alpha", language, bodies={"hook": body})
        self.assertEqual(validate(self.root).errors, [])

    # -- generated files ----------------------------------------------------------

    def test_a_stale_generated_file_is_an_error(self) -> None:
        def change(data):
            data["modules"][0]["units"][0]["lessons"][1]["minutes"] = 20
        self.edit_curriculum(change)
        stale = {f.params["path"] for f in validate(self.root).errors if f.code == "build_stale"}
        self.assertIn("course/vi/README.md", stale)
        self.assertIn("course/ja/diagrams/roadmap.svg", stale)
        write_generated(self.root)
        self.assertEqual(validate(self.root).errors, [])

    def test_a_missing_generated_file_is_an_error(self) -> None:
        (self.root / "course/en/glossary.md").unlink()
        self.assertIn("build_stale", codes(validate(self.root)))

    def test_an_orphan_diagram_is_an_error_and_build_removes_it(self) -> None:
        orphan = self.root / "course/vi/diagrams/old.svg"
        orphan.write_text("<svg/>", encoding="utf-8")
        self.assertIn(("build_stale", "course/vi/diagrams/old.svg"),
                      [(f.code, f.params.get("path")) for f in validate(self.root).errors])
        write_generated(self.root)
        self.assertFalse(orphan.exists())

    def test_the_diagram_svg_follows_its_spec(self) -> None:
        self.edit_diagram(lambda spec: spec["title"].update(vi="Tiêu đề mới"))
        stale = {f.params["path"] for f in validate(self.root).errors if f.code == "build_stale"}
        self.assertEqual(stale, {f"course/vi/diagrams/{DIAGRAM_ID}.svg"})
        write_generated(self.root)
        self.assertIn("Tiêu đề mới", (self.root / f"course/vi/diagrams/{DIAGRAM_ID}.svg").read_text(encoding="utf-8"))


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


class RobustnessTests(StoreTest):
    """Hand-edited files will hold wrong types; the validator must report them, never crash."""

    def assert_never_crashes(self, path: Path, document, *, write=None) -> None:
        write = write or (lambda data: path.write_text(_fast_dump(data), encoding="utf-8"))
        original = path.read_bytes()
        try:
            for key_path in _paths(document):
                for value in BAD_VALUES:
                    write(_replaced(document, key_path, value))
                    try:
                        validate(self.root, check_generated=False)
                    except Exception as exc:  # noqa: BLE001 - any crash is the failure
                        self.fail(f"{path.name} {key_path!r} = {value!r}: {type(exc).__name__}: {exc}")
        finally:
            path.write_bytes(original)

    def test_wrong_types_in_the_yaml_files_are_reported_not_crashed_on(self) -> None:
        for name in ("course.yaml", "curriculum.yaml", "glossary.yaml", f"diagrams/{DIAGRAM_ID}.yaml"):
            with self.subTest(file=name):
                path = self.root / "course" / "data" / name
                self.assert_never_crashes(path, yaml.safe_load(path.read_text(encoding="utf-8")))
        # One entry stands for every section: each has the same shape.
        path = self.root / "course" / "data" / "sections.yaml"
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assert_never_crashes(path, {"sections": document["sections"][:1]})

    def test_wrong_types_in_every_diagram_template_are_reported_not_crashed_on(self) -> None:
        path = self.root / "course" / "data" / "diagrams" / f"{DIAGRAM_ID}.yaml"
        for name in ("agent-formula", "agent-loop"):
            with self.subTest(template=name):
                spec = yaml.safe_load((ROOT / "course/data/diagrams" / f"{name}.yaml").read_text(encoding="utf-8"))
                self.assert_never_crashes(path, spec)
        with self.subTest(template="summary"):
            self.assert_never_crashes(path, RECAP)
        # No course diagram is a flow yet.
        text = {"vi": "Bước", "en": "Step", "ja": "ステップ"}
        flow = {"template": "flow", "title": text, "direction": "vertical",
                "steps": [{"icon": "1️⃣", "color": "blue", "name": text, "caption": text, "arrow": text},
                          {"icon": "2️⃣", "color": "green", "name": text}]}
        with self.subTest(template="flow"):
            self.assert_never_crashes(path, flow)

    def test_wrong_types_in_lesson_front_matter_are_reported_not_crashed_on(self) -> None:
        path = self.root / "course/vi/lessons/alpha.md"
        text = path.read_text(encoding="utf-8")
        _, front, body = text.split("---\n", 2)

        def write(data) -> None:
            path.write_text("---\n" + _fast_dump(data) + "---\n" + body, encoding="utf-8")

        self.assert_never_crashes(path, yaml.safe_load(front), write=write)

    def test_the_fixture_diagram_is_untouched(self) -> None:
        self.assertEqual(DIAGRAM["columns"][0]["color"], "blue")


if __name__ == "__main__":
    unittest.main()
