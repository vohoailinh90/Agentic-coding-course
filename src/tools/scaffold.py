"""`scaffold`: create the language files of a lesson, ready to be written.

Each file gets the front matter at status `todo`, the title from
curriculum.yaml and every section from sections.yaml, each with a TODO hint.
Authors delete the optional sections a lesson does not need. Existing files are
never overwritten.
"""

from __future__ import annotations

import sys

from src.core.model import LESSONS_DIR, Course, Lesson, lesson_path
from src.core.validate import validate
from src.utils.console import print_findings
from src.utils.i18n import LANGUAGE_NAMES, Translator


def skeleton(course: Course, lesson: Lesson, language: str) -> str:
    lines = [
        "---",
        f"lesson: {lesson.id}",
        f"lang: {language}",
        "status: todo",
        'summary: ""',
        "social:",
        '  hook: ""',
        '  question: ""',
        "---",
        "",
        f"# {lesson.title[language]}",
        "",
    ]
    for section in course.sections:
        lines += [
            f"<!-- section: {section.key} -->",
            f"## {section.heading[language]}",
            "",
            f"<!-- TODO: {section.hint[language]} -->",
            "",
        ]
    return "\n".join(lines).rstrip("\n") + "\n"


def run(root, tr: Translator, lesson_id: str) -> int:
    report = validate(root, check_outline=False)
    if report.course is None:
        print_findings(report.errors, tr, sys.stderr)
        print(tr.t("cli.fix_errors_first"), file=sys.stderr)
        return 1
    course = report.course
    lesson = course.lesson(lesson_id)
    if lesson is None:
        print(tr.t("scaffold.unknown_lesson", lesson=lesson_id), file=sys.stderr)
        return 1
    folder = root / LESSONS_DIR / lesson.id
    folder.mkdir(parents=True, exist_ok=True)
    for language in course.languages:
        path = folder / f"{language}.md"
        relative = lesson_path(lesson.id, language)
        if path.exists():
            print(tr.t("scaffold.exists", path=relative))
            continue
        path.write_text(skeleton(course, lesson, language), encoding="utf-8", newline="\n")
        print(tr.t("scaffold.created", path=relative))
    source = course.source_language
    print(tr.t("scaffold.next", language=LANGUAGE_NAMES.get(source, source)))
    return 0
