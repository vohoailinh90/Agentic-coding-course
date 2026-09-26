"""`stats`: how big the course is, and how far the writing has got in each language."""

from __future__ import annotations

import sys

from src.core.model import STATUSES, Course
from src.core.validate import validate
from src.utils.console import print_findings
from src.utils.i18n import LANGUAGE_NAMES, Translator

MISSING = "missing"  # no readable file for that language yet


def progress(course: Course, docs: dict) -> dict[str, dict[str, int]]:
    """language -> {status or "missing": number of lessons}."""
    counts = {language: dict.fromkeys((*STATUSES, MISSING), 0) for language in course.languages}
    for lesson in course.lessons:
        for language in course.languages:
            doc = docs.get((lesson.id, language))
            status = doc.status if doc is not None and doc.status in STATUSES else MISSING
            counts[language][status] += 1
    return counts


def run(root, tr: Translator) -> int:
    report = validate(root, check_generated=False)
    if report.course is None:
        print_findings(report.errors, tr, sys.stderr)
        print(tr.t("cli.fix_errors_first"), file=sys.stderr)
        return 1
    course = report.course
    shown = tr.locale if tr.locale in course.languages else course.source_language
    print(tr.t("stats.heading", title=course.title[shown], version=course.curriculum_version))
    print(tr.t(
        "stats.structure",
        modules=len(course.modules), units=len(course.units),
        lessons=len(course.lessons), minutes=course.total_minutes,
    ))
    print(tr.t("stats.progress_heading"))
    total = len(course.lessons)
    for language, counts in progress(course, report.docs).items():
        percent = round(100 * counts["done"] / total) if total else 0
        print("  " + tr.t(
            "stats.progress_line",
            language=LANGUAGE_NAMES.get(language, language), percent=percent, **counts,
        ))
    if report.errors:
        print(tr.t("cli.fix_errors_first"), file=sys.stderr)
        return 1
    return 0
