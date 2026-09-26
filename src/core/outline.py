"""Render course/OUTLINE.md: the whole course tree, readable on GitHub in all languages.

The file is generated so it can never disagree with curriculum.yaml; the
validator re-renders it and fails when the committed copy differs. It carries
structure only — no writing status — so editing a lesson never makes it stale.
"""

from __future__ import annotations

from src.core.model import Course
from src.utils.i18n import LANGUAGE_NAMES, Translator

TYPE_ICONS = {"concept": "📖", "demo": "🎬", "hands-on": "🛠️", "project": "🚀"}
GENERATED_NOTE = (
    "<!-- Generated from course/curriculum.yaml by `python -m src.main outline --write`. "
    "Do not edit by hand: CI fails when this file and curriculum.yaml disagree. -->"
)


def _cell(text: str) -> str:
    """Text that is safe inside a Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ")


def render_outline(course: Course, translators: dict[str, Translator]) -> str:
    languages = course.languages

    def each(key: str, **params: object) -> list[str]:
        return [translators[language].t(key, **params) for language in languages]

    def joined(key: str, **params: object) -> str:
        return " · ".join(dict.fromkeys(each(key, **params)))

    lines = [GENERATED_NOTE, "", f"# {joined('outline.title')}", ""]

    lines += ["| | |", "|---|---|"]
    totals = each(
        "outline.totals",
        modules=len(course.modules),
        units=len(course.units),
        lessons=len(course.lessons),
        minutes=course.total_minutes,
    )
    for language, total in zip(languages, totals):
        name = LANGUAGE_NAMES.get(language, language)
        lines.append(f"| {name} | **{_cell(course.title[language])}** — {_cell(total)} |")
    lines += ["", f"{joined('outline.version')}: `{course.curriculum_version}`", ""]

    header = (
        f"| {translators[languages[0]].t('outline.number')} | "
        + " | ".join(LANGUAGE_NAMES.get(language, language) for language in languages)
        + f" | {joined('outline.type')} | {joined('outline.minutes')} |"
    )
    divider = "|" + "---|" * (len(languages) + 3)

    for module in course.modules:
        first, *others = languages
        lines += [f"## {module.number}. {module.title[first]}", ""]
        if others:
            lines += [" · ".join(module.title[language] for language in others), ""]
        lines += [f"- 🎯 {module.goal[language]}" for language in languages]
        lines.append("")
        for unit in module.units:
            titles = " · ".join(dict.fromkeys(unit.title[language] for language in languages))
            lines += [f"### {unit.number} {titles}", "", header, divider]
            for lesson in unit.lessons:
                cells = [lesson.number]
                cells += [_cell(lesson.title[language]) for language in languages]
                cells += [f"{TYPE_ICONS.get(lesson.type, '')} {lesson.type}".strip(), str(lesson.minutes)]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"
