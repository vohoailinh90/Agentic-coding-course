"""Parse one lesson file: front matter, language bar, title and marked sections.

A lesson file (`course/<lang>/lessons/<id>.md`) looks like this; docs/data-model.md
has the full rules:

    ---
    lesson: chatbot-to-agent
    lang: vi
    status: review
    summary: ...
    social: {hook: ..., question: ...}
    ---

    🌐 **Tiếng Việt** · [English](../../en/lessons/chatbot-to-agent.md) · [日本語](...)

    # <title, identical to curriculum.yaml>

    <!-- section: objective -->
    ## Mục tiêu bài học
    ...

Every `## ` heading must sit under a `<!-- section: key -->` marker. The marker
carries the structure all languages share; the heading text under it is free to
be localized. Fenced code blocks are skipped, so a `# comment` inside a shell
example is never mistaken for a heading, and a link inside one is not checked.

This module only reports what it cannot parse. Whether the keys, order, links
and statuses are right is the validator's business.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.core import yamlio

MARKER = re.compile(r"^<!--\s*section:\s*(?P<key>[^\s>]+)\s*-->\s*$")
H1 = re.compile(r"^# (?P<text>\S.*?)\s*$")
H2 = re.compile(r"^## (?P<text>\S.*?)\s*$")
FENCE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
TODO = re.compile(r"<!--\s*TODO\b")
IMAGE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)\s]+)\)")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\((?P<target>[^)\s]+)\)")
LANGUAGE_BAR = "🌐 "
FRONT_MATTER_FENCE = "---"


@dataclass
class SectionBlock:
    key: str
    heading: str
    line: int
    body_lines: list[str] = field(default_factory=list)
    images: list[tuple[str, str]] = field(default_factory=list)  # (alt text, target)
    links: list[str] = field(default_factory=list)  # link targets, images excluded

    @property
    def body(self) -> str:
        return "\n".join(self.body_lines).strip()

    @property
    def is_empty(self) -> bool:
        """Blank once HTML comments (TODO placeholders included) are removed."""
        return not COMMENT.sub("", self.body).strip()

    @property
    def has_todo(self) -> bool:
        return bool(TODO.search(self.body))


@dataclass
class LessonDoc:
    has_front_matter: bool = False
    front: object = None
    front_error: str | None = None
    language_bar: str | None = None
    title: str | None = None
    sections: list[SectionBlock] = field(default_factory=list)
    # (finding code, params) for lines that could not be placed in the structure
    problems: list[tuple[str, dict]] = field(default_factory=list)
    status: str | None = None  # set by the validator once the front matter checks out

    @property
    def keys(self) -> list[str]:
        return [section.key for section in self.sections]

    def section(self, key: str) -> SectionBlock | None:
        return next((section for section in self.sections if section.key == key), None)

    @property
    def diagram_layout(self) -> list[tuple[str, tuple[str, ...]]]:
        """(section key, image targets in order): what every translation must agree on."""
        return [(section.key, tuple(target for _, target in section.images)) for section in self.sections]


def split_front_matter(text: str) -> tuple[str | None, str, int]:
    """(front matter text or None, body, 1-based line number where the body starts)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != FRONT_MATTER_FENCE:
        return None, text, 1
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONT_MATTER_FENCE:
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1:]), index + 2
    return None, text, 1  # an unterminated block is no front matter at all


def parse_lesson(text: str) -> LessonDoc:
    doc = LessonDoc()
    front_text, body, first_line = split_front_matter(text)
    if front_text is not None:
        doc.has_front_matter = True
        try:
            parsed = yamlio.loads(front_text)
            doc.front = {} if parsed is None else parsed
        except yamlio.ContentYAMLError as exc:
            doc.front_error = str(exc)

    fence: str | None = None
    pending: tuple[str, int] | None = None  # a marker still waiting for its heading
    current: SectionBlock | None = None
    reported_outside = False

    def orphan(marker: tuple[str, int]) -> None:
        doc.problems.append(("section_marker_orphan", {"line": marker[1]}))

    def keep(line: str, number: int, *, code: bool = False) -> None:
        nonlocal reported_outside
        if current is not None:
            current.body_lines.append(line)
            if not code:
                current.images.extend((match.group("alt"), match.group("target")) for match in IMAGE.finditer(line))
                current.links.extend(match.group("target") for match in LINK.finditer(line))
        elif line.strip() and not COMMENT.fullmatch(line.strip()) and not reported_outside:
            doc.problems.append(("content_outside_section", {"line": number}))
            reported_outside = True

    for offset, line in enumerate(body.split("\n")):
        number = first_line + offset
        if fence is not None:
            keep(line, number, code=True)
            if line.strip().startswith(fence):
                fence = None
            continue
        opening = FENCE.match(line)
        if opening:
            if pending:
                orphan(pending)
                pending = None
            fence = opening.group("fence")
            keep(line, number, code=True)
            continue
        marker = MARKER.match(line)
        if marker:
            if pending:
                orphan(pending)
            pending = (marker.group("key"), number)
            continue
        if pending and not line.strip():
            continue  # blank lines between a marker and its heading are fine
        heading = H2.match(line)
        if heading:
            if pending:
                current = SectionBlock(pending[0], heading.group("text"), pending[1])
                doc.sections.append(current)
                pending = None
            else:
                doc.problems.append(
                    ("heading_without_marker", {"line": number, "heading": heading.group("text")})
                )
                keep(line, number)
            continue
        if pending:
            orphan(pending)
            pending = None
        if current is None and doc.title is None:
            title = H1.match(line)
            if title:
                doc.title = title.group("text")
                continue
            if line.startswith(LANGUAGE_BAR) and doc.language_bar is None:
                doc.language_bar = line.rstrip()
                continue
        keep(line, number)

    if pending:
        orphan(pending)
    return doc
