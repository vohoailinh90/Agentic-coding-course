"""`outline`: print, write or check course/OUTLINE.md (rendering lives in src/core/outline.py)."""

from __future__ import annotations

import sys

from src.core import yamlio
from src.core.model import OUTLINE_FILE
from src.core.outline import render_outline
from src.core.validate import Finding, validate
from src.utils.catalogs import translators_for
from src.utils.console import print_findings, render_finding
from src.utils.i18n import Translator


def run(root, tr: Translator, *, write: bool = False, check: bool = False) -> int:
    report = validate(root, check_outline=False)
    if report.course is None:
        print_findings(report.errors, tr, sys.stderr)
        print(tr.t("cli.fix_errors_first"), file=sys.stderr)
        return 1
    text = render_outline(report.course, translators_for(report.course.languages))
    path = root / OUTLINE_FILE
    if write:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(tr.t("outline.written", path=OUTLINE_FILE))
        return 0
    if check:
        current = yamlio.read_text(path) if path.is_file() else None
        if current == text:
            print(tr.t("outline.up_to_date", path=OUTLINE_FILE))
            return 0
        print(render_finding(tr, Finding("error", "outline_stale", {"path": OUTLINE_FILE})))
        return 1
    sys.stdout.write(text)
    return 0
