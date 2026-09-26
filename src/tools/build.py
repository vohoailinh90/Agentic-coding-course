"""`build`: write every generated file, or check that none is out of date.

Generated: course/README.md, course/<lang>/README.md, course/<lang>/glossary.md
and course/<lang>/diagrams/*.svg (see src/core/build.py). Files that the data no
longer produces — the SVG of a deleted diagram, say — are removed.
"""

from __future__ import annotations

import sys

from src.core.validate import Finding, stale_files, validate
from src.utils.console import print_findings, render_finding
from src.utils.i18n import Translator


def run(root, tr: Translator, *, check: bool = False) -> int:
    report = validate(root, check_generated=False)
    if report.course is None:
        print_findings(report.errors, tr, sys.stderr)
        print(tr.t("cli.fix_errors_first"), file=sys.stderr)
        return 1
    expected, stale, orphans = stale_files(root, report.course, report.started)
    if check:
        if not stale and not orphans:
            print(tr.t("build.up_to_date", files=len(expected)))
            return 0
        for path in stale + orphans:
            print(render_finding(tr, Finding("error", "build_stale", {"path": path})))
        return 1
    for path in stale:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(expected[path], encoding="utf-8", newline="\n")
    for path in orphans:
        (root / path).unlink()
    print(tr.t("build.written", files=len(expected), written=len(stale), removed=len(orphans)))
    return 0
