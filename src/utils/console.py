"""Turning validator findings into sentences in the reader's language."""

from __future__ import annotations

import sys
from typing import TextIO

from src.utils.i18n import Translator


def render_finding(tr: Translator, finding) -> str:
    params = dict(finding.params)
    if finding.code == "field_type" and "expected" in params:
        params["expected"] = tr.t(f"types.{params['expected']}")
    return f"{tr.t(f'levels.{finding.level}')}: {tr.t(f'findings.{finding.code}', **params)}"


def print_findings(findings, tr: Translator, stream: TextIO | None = None) -> None:
    stream = sys.stdout if stream is None else stream
    for finding in findings:
        print(render_finding(tr, finding), file=stream)
