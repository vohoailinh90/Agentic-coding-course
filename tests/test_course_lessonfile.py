"""Parsing a lesson file into front matter, title and marked sections."""

from __future__ import annotations

import unittest

from src.core.lessonfile import parse_lesson

LESSON = """---
lesson: alpha
lang: en
status: draft
summary: One line.
social: {hook: "", question: ""}
---

# Lesson alpha

<!-- section: objective -->
## Lesson Objective

- Learn **one** thing.

<!-- section: example -->

## Real Example

```bash
# a shell comment, not a title
## not a heading either
ls
```

Done.
"""


class ParseTests(unittest.TestCase):
    def test_front_matter_title_and_sections(self) -> None:
        doc = parse_lesson(LESSON)
        self.assertTrue(doc.has_front_matter)
        self.assertEqual(doc.front["lesson"], "alpha")
        self.assertEqual(doc.title, "Lesson alpha")
        self.assertEqual(doc.keys, ["objective", "example"])
        self.assertEqual(doc.section("objective").heading, "Lesson Objective")
        self.assertEqual(doc.problems, [])

    def test_headings_inside_a_code_block_are_body_text(self) -> None:
        doc = parse_lesson(LESSON)
        self.assertEqual(doc.problems, [])  # no phantom "heading without marker"
        self.assertEqual(doc.keys, ["objective", "example"])
        body = doc.section("example").body
        self.assertIn("# a shell comment, not a title", body)
        self.assertIn("## not a heading either", body)
        self.assertTrue(body.endswith("Done."))

    def test_a_marker_without_a_heading_is_reported(self) -> None:
        doc = parse_lesson("---\nlesson: a\n---\n# T\n\n<!-- section: hook -->\nText.\n")
        # The marker opened no section, so the text under it is also homeless.
        self.assertEqual(doc.problems, [
            ("section_marker_orphan", {"line": 6}),
            ("content_outside_section", {"line": 7}),
        ])

    def test_a_heading_without_a_marker_is_reported(self) -> None:
        doc = parse_lesson("---\nlesson: a\n---\n# T\n\n<!-- section: hook -->\n## Hook\n\n## Stray\n")
        self.assertEqual(doc.problems, [("heading_without_marker", {"line": 9, "heading": "Stray"})])

    def test_text_before_the_first_section_is_reported(self) -> None:
        doc = parse_lesson("---\nlesson: a\n---\n# T\n\nIntro text.\n\n<!-- section: hook -->\n## Hook\n")
        self.assertEqual(doc.problems, [("content_outside_section", {"line": 6})])

    def test_comments_before_the_first_section_are_fine(self) -> None:
        doc = parse_lesson("---\nlesson: a\n---\n# T\n\n<!-- a note -->\n\n<!-- section: hook -->\n## Hook\n")
        self.assertEqual(doc.problems, [])

    def test_an_unterminated_front_matter_block_is_no_front_matter(self) -> None:
        doc = parse_lesson("---\nlesson: a\n# T\n")
        self.assertFalse(doc.has_front_matter)

    def test_invalid_front_matter_yaml_is_kept_as_an_error(self) -> None:
        doc = parse_lesson("---\nlesson: [a\n---\n# T\n")
        self.assertIsNotNone(doc.front_error)

    def test_an_empty_or_comment_only_section_counts_as_empty(self) -> None:
        doc = parse_lesson("---\nx: 1\n---\n# T\n<!-- section: hook -->\n## Hook\n\n<!-- TODO: write -->\n")
        section = doc.section("hook")
        self.assertTrue(section.is_empty)
        self.assertTrue(section.has_todo)


if __name__ == "__main__":
    unittest.main()
