"""The course as self-contained HTML files that open in any browser, offline.

    <course-id>.html          every language, opening on a language chooser
    <course-id>-<lang>.html   one language, opening on its course home

They are for sharing the course with people who will not browse a Git
repository: a file opens with a double-click and needs no network and no other
file. The infographics are embedded as data: URIs, the style sheet is inline,
and there is no script. `python -m src.main export` writes them
(src/tools/export.py).

A file is a stack of pages (`<section class="page">`): the course homes, the
lessons and the glossaries. The style sheet shows only the page the URL
fragment points at (`:target`), so links between lessons behave like a small
website and the browser's Back button works; a browser without `:has()` shows
every page one after another. Printing shows every page, so printing a
one-language file to PDF gives the whole course in one PDF.

A lesson is exported in a language once its file there is finished (status
review or done); one still in review carries a badge. A link to a lesson that
is not in the export keeps its text and loses its link, and a link to another
language points into that language's file, which is written alongside. The
infographics are rendered from course/data/, not read from the generated SVG
files, so an export never shows an out-of-date picture. Raw HTML in a lesson
(the quiz answers' <details>) is copied as it is.
"""

from __future__ import annotations

import base64
import html
import mimetypes
import posixpath
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from src.core.build import TYPE_ICONS, language_name, roadmap_svg, term_label, totals
from src.core.infographics import render
from src.core.lessonfile import LessonDoc
from src.core.model import CHOOSER_FILE, COURSE_DIR, ROADMAP, Course, Lesson, Module, Unit, lesson_path
from src.core.validate import COMPLETE
from src.utils.catalogs import translators_for
from src.utils.i18n import format_date

if TYPE_CHECKING:  # markdown-it-py is imported when an export runs, so the other commands work without it
    from markdown_it import MarkdownIt
    from markdown_it.token import Token

EXTERNAL = ("http://", "https://", "mailto:")
CHOOSER = "languages"  # the anchor of the language chooser in the all-languages file


def file_name(course: Course, language: str | None = None) -> str:
    """The all-languages file, or the file of one language."""
    return f"{course.id}.html" if language is None else f"{course.id}-{language}.html"


def home_anchor(language: str) -> str:
    return f"{language}-home"


def glossary_anchor(language: str) -> str:
    return f"{language}-glossary"


def lesson_anchor(language: str, lesson_id: str) -> str:
    return f"{language}-lesson-{lesson_id}"


def term_anchor(language: str, term_id: str) -> str:
    return f"{language}-term-{term_id}"


def data_uri(content: bytes, media_type: str) -> str:
    return f"data:{media_type};base64,{base64.b64encode(content).decode('ascii')}"


@lru_cache(maxsize=1)
def markdown() -> MarkdownIt:
    """CommonMark plus GitHub's tables and strikethrough: lessons render as they do on GitHub."""
    from markdown_it import MarkdownIt

    return MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


@dataclass(frozen=True)
class ExportedFile:
    name: str
    languages: tuple[str, ...]
    lessons: int  # lesson pages in the file, over all its languages
    html: str


class _Sources:
    """What every file of one export is rendered from."""

    def __init__(self, course: Course, docs: dict[tuple[str, str], LessonDoc], root: Path, today: date) -> None:
        self.course = course
        self.docs = docs
        self.root = root
        self.today = today
        self.translators = translators_for(course.languages)
        # language -> the lessons exported in it, in course order
        self.included: dict[str, tuple[Lesson, ...]] = {
            language: tuple(lesson for lesson in course.lessons if self._finished(lesson.id, language))
            for language in course.languages
        }
        self.places: dict[str, tuple[Module, Unit]] = {
            lesson.id: (module, unit) for module in course.modules for unit in module.units for lesson in unit.lessons
        }
        self._svgs: dict[tuple[str, str], str] = {}

    def _finished(self, lesson_id: str, language: str) -> bool:
        doc = self.docs.get((lesson_id, language))
        return doc is not None and doc.status in COMPLETE

    def has(self, language: str, lesson_id: str) -> bool:
        return any(lesson.id == lesson_id for lesson in self.included[language])

    def svg(self, diagram_id: str, language: str) -> str | None:
        """An infographic rendered from its spec, or None when there is no such diagram."""
        key = (diagram_id, language)
        if key not in self._svgs:
            if diagram_id == ROADMAP:
                self._svgs[key] = roadmap_svg(self.course, language, self.translators[language])
            elif diagram_id in self.course.diagrams:
                self._svgs[key] = render(self.course.diagrams[diagram_id], language)
            else:
                return None
        return self._svgs[key]


class _Document:
    """One HTML file: the pages of `languages`, linking into the other files for the rest."""

    def __init__(self, sources: _Sources, languages: tuple[str, ...]) -> None:
        self.sources = sources
        self.course = sources.course
        self.languages = languages

    # -- links ---------------------------------------------------------------

    def href(self, language: str, anchor: str) -> str:
        """A page of `language`: in this file, or in that language's own file."""
        if language in self.languages:
            return f"#{anchor}"
        return f"{file_name(self.course, language)}#{anchor}"

    def _lesson_or_home(self, language: str, lesson_id: str) -> str:
        if self.sources.has(language, lesson_id):
            return lesson_anchor(language, lesson_id)
        return home_anchor(language)

    def _target(self, source: str, target: str, language: str) -> str | None:
        """Where a link in the lesson file `source` goes in the export; None drops the link."""
        if target.startswith(EXTERNAL):
            return target
        path = posixpath.normpath(posixpath.join(posixpath.dirname(source), target.split("#", 1)[0]))
        if target.startswith("#") or path == source:
            return None  # headings carry no anchors in the export
        if path == CHOOSER_FILE:
            return f"#{CHOOSER}" if len(self.languages) > 1 else self.href(language, home_anchor(language))
        for other in self.course.languages:
            folder = f"{COURSE_DIR}/{other}/"
            if path == f"{folder}README.md":
                return self.href(other, home_anchor(other))
            if path == f"{folder}glossary.md":
                return self.href(other, glossary_anchor(other))
            if path.startswith(f"{folder}lessons/") and path.endswith(".md"):
                lesson_id = path[len(f"{folder}lessons/"): -len(".md")]
                if self.sources.has(other, lesson_id):
                    return self.href(other, lesson_anchor(other, lesson_id))
                return None
        return None  # outside the course: nothing to point at offline

    def _image(self, source: str, target: str) -> str:
        """An image as a data: URI, so the file needs no other file."""
        if target.startswith(EXTERNAL):
            return target
        path = posixpath.normpath(posixpath.join(posixpath.dirname(source), target.split("#", 1)[0]))
        folder, name = posixpath.split(path)
        parent, kind = posixpath.split(folder)
        language = posixpath.basename(parent)
        in_course = language in self.course.languages and parent == f"{COURSE_DIR}/{language}"
        if in_course and kind == "diagrams" and name.endswith(".svg"):
            svg = self.sources.svg(name[: -len(".svg")], language)
            if svg is not None:
                return data_uri(svg.encode("utf-8"), "image/svg+xml")
        file = self.sources.root / path
        if file.is_file():
            media_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
            return data_uri(file.read_bytes(), media_type)
        return target

    def _rewrite(self, children: list[Token], source: str, language: str) -> None:
        dropped = False
        for token in children:
            if token.type == "image":
                token.attrSet("src", self._image(source, str(token.attrGet("src"))))
            elif token.type == "link_open":
                target = self._target(source, str(token.attrGet("href")), language)
                if target is None:
                    _drop(token)
                    dropped = True
                else:
                    token.attrSet("href", target)
                    if target.startswith(("http://", "https://")):
                        token.attrSet("target", "_blank")
                        token.attrSet("rel", "noopener noreferrer")
            elif token.type == "link_close" and dropped:
                _drop(token)
                dropped = False

    def markdown(self, text: str, source: str, language: str) -> str:
        parser = markdown()
        tokens = parser.parse(text)
        for token in tokens:
            if token.type == "inline" and token.children:
                self._rewrite(token.children, source, language)
        rendered = parser.renderer.render(tokens, parser.options, {})
        return rendered.replace("<table>", '<div class="table"><table>').replace("</table>", "</table></div>")

    # -- pages ---------------------------------------------------------------

    def _bar(self, language: str, anchor_for: Callable[[str], str]) -> str:
        """Home and glossary of this language, and the same page in the others."""
        tr = self.sources.translators[language]
        languages = " · ".join(
            f'<strong lang="{other}">{_escape(language_name(other))}</strong>' if other == language
            else f'<a lang="{other}" href="{_escape(self.href(other, anchor_for(other)))}">'
                 f"{_escape(language_name(other))}</a>"
            for other in self.course.languages
        )
        return (
            '<nav class="bar">'
            f'<span><a href="{self.href(language, home_anchor(language))}">{_escape(tr.t("export.home"))}</a>'
            f' · <a href="{self.href(language, glossary_anchor(language))}">{_escape(tr.t("home.glossary"))}</a></span>'
            f'<span class="languages">🌐 {languages}</span>'
            "</nav>"
        )

    def _lesson_link(self, lesson: Lesson, language: str) -> str:
        title = _escape(lesson.title[language])
        if self.sources.has(language, lesson.id):
            return f'<a href="{self.href(language, lesson_anchor(language, lesson.id))}">{title}</a>'
        return f'<span class="soon">{title}</span>'

    def _home(self, language: str, *, landing: bool) -> str:
        course, tr = self.course, self.sources.translators[language]
        roadmap = data_uri((self.sources.svg(ROADMAP, language) or "").encode("utf-8"), "image/svg+xml")
        parts = [
            self._bar(language, home_anchor),
            f"<h1>{_escape(course.title[language])}</h1>",
            f'<p class="tagline">{_escape(course.tagline[language])}</p>',
            f"<p><strong>{_escape(tr.t('home.audience'))}</strong> {_escape(course.audience[language])}</p>",
            f'<p><strong>{_escape(totals(course, tr))}</strong> · '
            f'<a href="{self.href(language, glossary_anchor(language))}">{_escape(tr.t("home.glossary"))}</a></p>',
            f'<p><img src="{roadmap}" alt="{_escape(tr.t("roadmap.title"))}"></p>',
            f'<p class="note">{_escape(tr.t("home.legend"))}</p>',
        ]
        minimum = course.minimum_path_lessons
        if minimum:
            parts += [
                f"<h2>{_escape(tr.t('home.minimum_heading'))}</h2>",
                "<p>" + _escape(tr.t(
                    "home.minimum_intro", lessons=len(minimum), minutes=sum(lesson.minutes for lesson in minimum),
                )) + "</p>",
                '<ol class="path">' + "".join(
                    f"<li>{self._lesson_link(lesson, language)} — "
                    f"{_escape(tr.t('home.minutes', minutes=lesson.minutes))}</li>"
                    for lesson in minimum
                ) + "</ol>",
            ]
        header = (
            f"<thead><tr><th>#</th><th>{_escape(tr.t('home.lesson'))}</th><th>{_escape(tr.t('home.type'))}</th>"
            f"<th>{_escape(tr.t('home.time'))}</th></tr></thead>"
        )
        for module in course.modules:
            parts += [
                f"<h2>{_escape(module.number)}. {_escape(module.icon)} {_escape(module.title[language])}</h2>",
                f"<p>🎯 {_escape(module.goal[language])}</p>",
            ]
            for unit in module.units:
                track = "" if unit.track == "core" else (
                    f' <span class="track">{_escape(tr.t(f"home.track_{unit.track}"))}</span>'
                )
                rows = []
                for lesson in unit.lessons:
                    star = "⭐ " if lesson.id in course.minimum_path else ""
                    kind = f"{TYPE_ICONS[lesson.type]} {tr.t(f'lesson_types.{lesson.type}')}"
                    rows.append(
                        f"<tr><td>{_escape(lesson.number)}</td><td>{star}{self._lesson_link(lesson, language)}</td>"
                        f"<td>{_escape(kind)}</td><td>{_escape(tr.t('home.minutes', minutes=lesson.minutes))}</td></tr>"
                    )
                parts += [
                    f"<h3>{_escape(unit.number)} {_escape(unit.title[language])}{track}</h3>",
                    f'<div class="table"><table class="lessons">{header}<tbody>{"".join(rows)}</tbody></table></div>',
                ]
        ready = len(self.sources.included[language])
        parts += [
            f'<p class="print-tip">{_escape(tr.t("export.print_tip"))}</p>',
            '<footer class="foot">' + _escape(tr.t(
                "export.footer", date=format_date(self.sources.today, language), ready=ready,
                total=len(course.lessons),
            )) + "</footer>",
        ]
        return _page(home_anchor(language), language, "home landing" if landing else "home", parts)

    def _lesson(self, language: str, lesson: Lesson, previous: Lesson | None, following: Lesson | None) -> str:
        course, tr = self.course, self.sources.translators[language]
        doc = self.sources.docs[(lesson.id, language)]
        module, unit = self.sources.places[lesson.id]
        source = lesson_path(lesson.id, language)
        facts = [
            f"{TYPE_ICONS[lesson.type]} {tr.t(f'lesson_types.{lesson.type}')}",
            tr.t("home.minutes", minutes=lesson.minutes),
        ]
        if lesson.id in course.minimum_path:
            facts.append(tr.t("home.minimum_heading"))
        badge = f' <span class="badge">{_escape(tr.t("export.in_review"))}</span>' if doc.status == "review" else ""
        parts = [
            self._bar(language, lambda other: self._lesson_or_home(other, lesson.id)),
            f'<p class="crumbs">{_escape(module.icon)} {_escape(module.number)}. {_escape(module.title[language])}'
            f" › {_escape(unit.number)} {_escape(unit.title[language])}</p>",
            f"<h1>{_escape(lesson.title[language])}</h1>",
            f'<p class="facts">{" · ".join(_escape(fact) for fact in facts)}{badge}</p>',
        ]
        for block in doc.sections:
            heading = markdown().renderInline(block.heading)
            body = self.markdown(block.body, source, language)
            parts.append(f'<section class="part part-{_escape(block.key)}">\n<h2>{heading}</h2>\n{body}</section>')
        if lesson.terms:
            items = []
            for term_id in lesson.terms:
                term = course.glossary[term_id]
                others = " · ".join(
                    f'<span lang="{other}">{_escape(term_label(term.entries[other]))}</span>'
                    for other in course.languages if other != language
                )
                name = _escape(term_label(term.entries[language]))
                link = f'<a href="#{term_anchor(language, term_id)}">{name}</a>'
                items.append(f"<li>{link} — {others}</li>" if others else f"<li>{link}</li>")
            parts.append(f'<aside class="terms"><h2>{_escape(tr.t("export.terms"))}</h2><ul>{"".join(items)}</ul></aside>')
        pager = []
        if previous is not None:
            pager.append(f'<a class="previous" href="#{lesson_anchor(language, previous.id)}">'
                         f'{_escape(tr.t("export.previous"))}<span>{_escape(previous.title[language])}</span></a>')
        if following is not None:
            pager.append(f'<a class="next" href="#{lesson_anchor(language, following.id)}">'
                         f'{_escape(tr.t("export.next"))}<span>{_escape(following.title[language])}</span></a>')
        if pager:
            parts.append(f'<nav class="pager">{"".join(pager)}</nav>')
        return _page(lesson_anchor(language, lesson.id), language, "lesson", parts)

    def _glossary(self, language: str) -> str:
        course, tr = self.course, self.sources.translators[language]
        others = [other for other in course.languages if other != language]
        header = "".join(
            [f"<th>{_escape(tr.t('glossary.term'))}</th>", f"<th>{_escape(tr.t('glossary.definition'))}</th>"]
            + [f'<th lang="{other}">{_escape(language_name(other))}</th>' for other in others]
        )
        rows = []
        for term in course.glossary.values():
            entry = term.entries[language]
            cells = [f"<td><strong>{_escape(term_label(entry))}</strong></td>", f"<td>{_escape(entry['definition'])}</td>"]
            cells += [f'<td lang="{other}">{_escape(term_label(term.entries[other]))}</td>' for other in others]
            rows.append(f'<tr id="{term_anchor(language, term.id)}">{"".join(cells)}</tr>')
        parts = [
            self._bar(language, glossary_anchor),
            f"<h1>{_escape(tr.t('glossary.title'))}</h1>",
            f"<p>{_escape(tr.t('glossary.intro'))}</p>",
            f'<div class="table"><table><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
        ]
        return _page(glossary_anchor(language), language, "glossary", parts)

    def _chooser(self) -> str:
        translators = self.sources.translators
        titles = {translators[language].t("chooser.title"): language for language in reversed(self.languages)}
        heading = " · ".join(
            f'<span class="nowrap" lang="{language}">{_escape(title)}</span>' for title, language in reversed(titles.items())
        )
        parts = [f"<h1>🌐 {heading}</h1>"]
        for language in self.languages:
            tr = translators[language]
            home, glossary = f"#{home_anchor(language)}", f"#{glossary_anchor(language)}"
            parts.append(
                f'<article class="choice" lang="{language}">'
                f'<h2><a href="{home}">{_escape(language_name(language))} →</a></h2>'
                f"<p><strong>{_escape(self.course.title[language])}</strong> — {_escape(self.course.tagline[language])}</p>"
                f'<p><a href="{home}">{_escape(tr.t("chooser.open"))}</a> · '
                f'<a href="{glossary}">{_escape(tr.t("home.glossary"))}</a></p>'
                "</article>"
            )
        return _page(CHOOSER, None, "chooser landing", parts)

    def render(self) -> str:
        several = len(self.languages) > 1
        pages = [self._chooser()] if several else []
        for language in self.languages:
            pages.append(self._home(language, landing=not several))
            lessons = self.sources.included[language]
            for index, lesson in enumerate(lessons):
                previous = lessons[index - 1] if index else None
                following = lessons[index + 1] if index + 1 < len(lessons) else None
                pages.append(self._lesson(language, lesson, previous, following))
            pages.append(self._glossary(language))
        title = " · ".join(self.course.title[language] for language in self.languages)
        first = self.course.source_language if several else self.languages[0]
        return "\n".join([
            "<!DOCTYPE html>",
            f'<html lang="{first}">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_escape(title)}</title>",
            f"<style>{STYLE}</style>",
            "</head>",
            "<body>",
            "<main>",
            *pages,
            "</main>",
            "</body>",
            "</html>",
            "",
        ])


def _drop(token: Token) -> None:
    """Turn one end of a link into nothing, so the link text stays and the link goes."""
    token.type, token.tag, token.content, token.attrs = "html_inline", "", "", {}


def _page(anchor: str, language: str | None, kind: str, parts: list[str]) -> str:
    lang = f' lang="{language}"' if language else ""
    return f'<section class="page {kind}" id="{anchor}"{lang}>\n' + "\n".join(parts) + "\n</section>"


def export_files(
    course: Course, docs: dict[tuple[str, str], LessonDoc], root: Path, today: date
) -> list[ExportedFile]:
    """The all-languages file first, then one file per language, in course.languages order."""
    sources = _Sources(course, docs, root, today)
    sets: list[tuple[str | None, tuple[str, ...]]] = [(None, course.languages)]
    sets += [(language, (language,)) for language in course.languages]
    return [
        ExportedFile(
            name=file_name(course, language),
            languages=languages,
            lessons=sum(len(sources.included[each]) for each in languages),
            html=_Document(sources, languages).render(),
        )
        for language, languages in sets
    ]


STYLE = """
:root {
  --ink: #1f2937; --muted: #64748b; --paper: #ffffff; --wash: #f1f5f9; --line: #e2e8f0;
  --brand: #4338ca; --soft: #eef2ff; --note: #fef3c7; --note-ink: #92400e;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e5e7eb; --muted: #94a3b8; --paper: #111827; --wash: #0b1120; --line: #273449;
    --brand: #a5b4fc; --soft: #1e1b4b; --note: #422006; --note-ink: #fcd34d;
    color-scheme: dark;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--wash); color: var(--ink);
  font: 17px/1.7 system-ui, "Segoe UI", "Noto Sans", "Helvetica Neue", Arial, "Hiragino Sans",
    "Yu Gothic UI", Meiryo, "Noto Sans JP", sans-serif;
}
:lang(ja) {
  font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Yu Gothic", Meiryo,
    "Noto Sans JP", "Noto Sans CJK JP", system-ui, sans-serif;
  line-break: strict;
}
main { max-width: 860px; margin: 0 auto; padding: 16px; }
.page {
  background: var(--paper); border: 1px solid var(--line); border-radius: 18px;
  padding: 18px 28px 28px; margin: 0 0 24px; overflow-wrap: anywhere;
}
a { color: var(--brand); }
h1 { font-size: 1.75rem; line-height: 1.35; margin: 0.4em 0 0.3em; }
h2 { font-size: 1.3rem; line-height: 1.4; margin: 1.6em 0 0.5em; }
h3 { font-size: 1.1rem; margin: 1.4em 0 0.4em; }
img { max-width: 100%; height: auto; }
p > img:only-child { display: block; margin: 8px auto; }
.table { max-width: 100%; overflow-x: auto; margin: 12px 0; }
table { width: 100%; border-collapse: collapse; font-size: 0.93rem; }
.lessons td:first-child, .lessons td:nth-child(3), .lessons td:nth-child(4), .nowrap { white-space: nowrap; }
.nowrap { display: inline-block; }
th, td { border-bottom: 1px solid var(--line); padding: 7px 10px; text-align: left; vertical-align: top; }
th { background: var(--wash); }
tr:target { background: var(--soft); }
blockquote { margin: 0; padding: 2px 16px; border-left: 4px solid var(--brand); color: var(--muted); }
code { background: var(--wash); border-radius: 6px; padding: 1px 5px; font-size: 0.92em; }
pre { background: var(--wash); border-radius: 12px; padding: 12px 16px; overflow-x: auto; }
pre code { background: none; padding: 0; }
.bar {
  display: flex; flex-wrap: wrap; justify-content: space-between; gap: 6px 18px;
  font-size: 0.9rem; padding-bottom: 10px; margin-bottom: 8px; border-bottom: 1px solid var(--line);
}
.bar a { text-decoration: none; }
.tagline { font-size: 1.1rem; color: var(--muted); }
.note, .crumbs, .facts, .foot, .print-tip { color: var(--muted); font-size: 0.93rem; }
.crumbs { margin: 14px 0 0; }
.soon { color: var(--muted); }
.track, .badge {
  display: inline-block; border-radius: 999px; padding: 0 10px; font-size: 0.85rem; font-weight: normal;
  vertical-align: middle;
}
.track { background: var(--soft); color: var(--brand); }
.badge { background: var(--note); color: var(--note-ink); }
.part-objective, .part-takeaways, .terms {
  background: var(--soft); border-radius: 14px; padding: 2px 20px 8px; margin: 18px 0;
}
.part-objective h2, .part-takeaways h2, .terms h2 { margin-top: 0.8em; }
.part-recap img { border-radius: 14px; }
.part-sources { font-size: 0.93rem; }
details {
  border: 1px solid var(--line); border-radius: 12px; padding: 8px 16px; margin: 12px 0; background: var(--wash);
}
summary { cursor: pointer; font-weight: 600; color: var(--brand); }
.pager {
  display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px;
  margin-top: 28px; padding-top: 14px; border-top: 1px solid var(--line);
}
.pager a { text-decoration: none; font-weight: 600; max-width: 48%; }
.pager .next { margin-left: auto; text-align: right; }
.pager span { display: block; font-weight: normal; color: var(--muted); font-size: 0.9rem; line-height: 1.45; }
.choice { border-top: 1px solid var(--line); padding-top: 6px; }
.foot { margin-top: 18px; }
@supports selector(:has(*)) {
  .page { display: none; }
  .page:target, .page:has(:target), main:not(:has(:target)) > .landing { display: block; }
}
@media (max-width: 600px) {
  body { font-size: 16px; }
  main { padding: 8px; }
  .page { padding: 12px 16px 20px; border-radius: 14px; }
  .pager a { max-width: 100%; }
}
@media print {
  :root { --ink: #000000; --paper: #ffffff; --wash: #f1f5f9; color-scheme: light; }
  body { background: #ffffff; font-size: 11pt; }
  main { max-width: none; padding: 0; }
  .page { display: block !important; border: 0; border-radius: 0; padding: 0; margin: 0; break-before: page; }
  .page:first-child { break-before: auto; }
  .bar, .pager, .print-tip { display: none; }
  a { color: inherit; text-decoration: none; }
  img, tr, details { break-inside: avoid; }
  h1, h2, h3 { break-after: avoid; }
  details::details-content { content-visibility: visible; display: block; }
}
""".strip()
