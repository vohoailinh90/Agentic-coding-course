"""`export`: save the course as HTML files that open offline, to share it without GitHub.

Writes into --out (default: outputs/html/, which Git ignores):

    <course-id>.html          every language, opening on a language chooser
    <course-id>-<lang>.html   one per language, opening on its course home

src/core/export.py says what goes into them. The content store must validate
first, so an export never carries a broken link or a half-checked lesson.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from src.core.export import export_files, file_name
from src.core.validate import validate
from src.utils.console import print_findings
from src.utils.i18n import Translator

OUT = Path("outputs") / "html"  # under the repository root


def run(root: Path, tr: Translator, out: Path | None = None, today: date | None = None) -> int:
    report = validate(root, check_generated=False)
    if report.course is None or report.errors:
        print_findings(report.errors, tr, sys.stderr)
        print(tr.t("cli.fix_errors_first"), file=sys.stderr)
        return 1
    try:
        import markdown_it  # noqa: F401 - only checks that it is installed
    except ImportError:
        print(tr.t("export.missing_dependency"), file=sys.stderr)
        return 1
    folder = out if out is not None else root / OUT
    files = export_files(report.course, report.docs, root, today or date.today())
    folder.mkdir(parents=True, exist_ok=True)
    for exported in files:
        (folder / exported.name).write_text(exported.html, encoding="utf-8", newline="\n")
    print(tr.t("export.written", files=len(files), folder=str(folder)))
    for exported in files:
        print("  " + tr.t("export.file", file=exported.name, lessons=exported.lessons))
    print(tr.t("export.open_hint", combined=file_name(report.course)))
    return 0
