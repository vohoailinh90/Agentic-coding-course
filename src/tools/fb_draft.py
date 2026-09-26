"""`fb-draft`: turn a finished lesson into a Facebook post draft.

The post is assembled from the data store, never written by hand, so a
correction to a lesson or to the glossary reaches every future post:

    hook (front matter social.hook)
    📘 Lesson <number>: <title>            (curriculum.yaml)
    summary (front matter)
    📌 Key takeaways (the lesson's takeaways section)
    🗣️ Terms in 3 languages (the lesson's terms, from glossary.yaml)
    💬 question (front matter social.question)
    hashtags (course.yaml)

Facebook shows no Markdown, so emphasis marks are removed, links become
"text (url)" and list items become "• " bullets. A human still reviews and
posts it; docs/facebook-plan.md describes the cadence.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from src.core.lessonfile import COMMENT, LessonDoc
from src.core.model import LESSONS_DIR, Course, Lesson, Term, lesson_path
from src.core.validate import COMPLETE, validate
from src.utils.catalogs import translator_for
from src.utils.console import print_findings
from src.utils.i18n import LANGUAGE_NAMES, Translator

LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
# `_` is deliberately not treated as emphasis: it would eat snake_case names.
EMPHASIS = re.compile(r"(\*\*|\*|`)(?=\S)(.+?)(?<=\S)\1")
BULLET = re.compile(r"^(?:[-*+]|\d+[.)])\s+")


def plain(markdown: str) -> str:
    """Markdown as plain text that reads well where Markdown is not rendered."""
    text = COMMENT.sub("", markdown)
    text = LINK.sub(r"\1 (\2)", text)
    for _ in range(2):  # **bold *with italic* inside**
        text = EMPHASIS.sub(r"\2", text)
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if BULLET.match(line):
            line = "• " + BULLET.sub("", line, count=1)
        lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _term_label(entry: dict[str, str]) -> str:
    reading = entry.get("reading")
    return f"{entry['term']}［{reading}］" if reading else entry["term"]


def term_line(term: Term, language: str, languages: tuple[str, ...]) -> str:
    others = " · ".join(
        f"{other.upper()}: {_term_label(term.entries[other])}" for other in languages if other != language
    )
    return f"• {_term_label(term.entries[language])} — {others}" if others else f"• {_term_label(term.entries[language])}"


def build_post(course: Course, lesson: Lesson, doc: LessonDoc, language: str) -> str:
    post_tr = translator_for(language)
    social = doc.front.get("social", {}) if isinstance(doc.front, dict) else {}
    parts: list[str] = []
    if social.get("hook", "").strip():
        parts.append(social["hook"].strip())
    parts.append(post_tr.t("fb.lesson_line", number=lesson.number, title=lesson.title[language]))
    summary = plain(str(doc.front.get("summary", "")))
    if summary:
        parts.append(summary)
    takeaways = doc.section("takeaways")
    if takeaways is not None and not takeaways.is_empty:
        parts.append(post_tr.t("fb.takeaways") + "\n" + plain(takeaways.body))
    if lesson.terms:
        lines = [term_line(course.glossary[term], language, course.languages) for term in lesson.terms]
        parts.append(post_tr.t("fb.terms") + "\n" + "\n".join(lines))
    if social.get("question", "").strip():
        parts.append("💬 " + social["question"].strip())
    if course.hashtags.get(language):
        parts.append(" ".join(course.hashtags[language]))
    return "\n\n".join(parts) + "\n"


def _belongs_to(finding, lesson_id: str) -> bool:
    path = str(finding.params.get("path", ""))
    folder = f"{LESSONS_DIR}/{lesson_id}"
    return path == folder or path.startswith(folder + "/")


def run(root, tr: Translator, lesson_id: str, post_language: str | None = None, out: Path | None = None) -> int:
    report = validate(root, check_outline=False)
    if report.course is None:
        print_findings(report.errors, tr, sys.stderr)
        print(tr.t("cli.fix_errors_first"), file=sys.stderr)
        return 1
    course = report.course
    language = post_language or course.source_language
    lesson = course.lesson(lesson_id)
    if lesson is None:
        print(tr.t("scaffold.unknown_lesson", lesson=lesson_id), file=sys.stderr)
        return 1
    if language not in course.languages:
        print(tr.t(
            "findings.value_invalid", path="--post-lang", field="--post-lang",
            value=language, allowed=", ".join(course.languages),
        ), file=sys.stderr)
        return 1
    problems = [finding for finding in report.errors if _belongs_to(finding, lesson.id)]
    if problems:
        print_findings(problems, tr, sys.stderr)
        print(tr.t("cli.fix_errors_first"), file=sys.stderr)
        return 1
    doc = report.docs.get((lesson.id, language))
    if doc is None:
        print(tr.t(
            "fb.not_started", lesson=lesson.id, language=LANGUAGE_NAMES.get(language, language)
        ), file=sys.stderr)
        return 1
    path = lesson_path(lesson.id, language)
    if doc.status not in COMPLETE:
        print(tr.t("fb.not_ready", path=path, status=doc.status), file=sys.stderr)
        return 1
    if doc.status == "review":
        print(tr.t("fb.review_warning", path=path), file=sys.stderr)
    post = build_post(course, lesson, doc, language)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(post, encoding="utf-8", newline="\n")
        print(tr.t("fb.written", path=str(out)))
    else:
        sys.stdout.write(post)
    return 0
