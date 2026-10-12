#!/usr/bin/env python3
"""Check the Vietnamese System Design store against the rules in its DECISIONS.md.

Per `deterministic_work` in agent-routing/policy.yaml, "does this lesson.yaml match
the schema, does every lesson id exist in the source map, does a lesson point at a
lesson that has not been written" are computable, so they are a script and a CI
check rather than something a reviewer re-derives by eye for each of ~400 lessons.
It was written after three lessons had each been checked by hand with the same
ad hoc commands.

What is checked, per lesson directory `<store>/lessons/<id>/`:
  - lesson.md and lesson.yaml exist
  - lesson.yaml is a mapping with exactly: id, title_vi, content_status,
    verification (source_read, claims, technical, mobile), learner_test,
    image_evidence
  - id equals the directory name and exists in the source map; title_vi is a
    non-empty string equal to the source map's title_vi (a null there is not a title)
  - content_status is planned | drafted | approved; each verification field and
    learner_test is pending | done; `approved` needs all of them `done`
  - image_evidence is a list, and each entry has an http(s) url with a host, a 64-hex
    sha256 and a real retrieved_on date
  - the directory holds only lesson.md, lesson.yaml and .svg figures drawn for the lesson
    (a downloaded PNG or JPG is refused whatever it shows), and each .svg is a self-contained
    drawing: it parses as XML with an <svg> root, uses only plain drawing elements (no <image>,
    <foreignObject>, <script>, <a>, animation, CSS @keyframes/animation/transition) and no processing
    instruction (<?xml-stylesheet?>),
    links to nothing but its own #fragments (href, url(), @import), and never mentions the source
    image host, so a renamed PNG or an SVG that wraps or
    loads a raster is refused too
  - lesson.md: no code fence (``` or ~~~) is left open, raw HTML is limited to a short list of tags
    (details, summary, br, a, img, sub, sup, kbd), <details> tags nest properly (<details open> too),
    every relative link and image source (inline, reference-style, <a href>, <img src>, <img srcset>)
    resolves, every image is a .svg file directly inside the lesson's own directory,
    it links the pinned source snapshot (as a real Markdown or HTML link, not text
    in a code block or a comment; a #fragment on it is fine), it mentions no lesson id that has no lesson
    directory, and it never contains assets.bytebytego.com, the host of every
    source image, in any form: ![]() , ![x][ref], <img>, <picture>, a bare URL
And once for the store: it holds only README.md and lessons/, and lessons/ holds only lesson
directories (an image dropped beside the README is refused like one in a lesson); README.md embeds
no image and only the allowed raw HTML tags (so no HTML table can hide a status), links every
lesson directory (as a real link, not a path in a comment or a code block)
in source-map order, every relative link in it resolves (a row left behind for a deleted lesson is an error), and it
carries no status words in its table, however formatted (status lives only in lesson.yaml).

This guards against honest mistakes while ~400 lessons are written; it is not a security
boundary. Markup crafted to slip past a rule on purpose is out of scope.

Not checked, because it is not computable here: whether a claim is true, whether a
figure reads well, and the Mermaid text-size estimate (needs a browser).

Usage:
    python3 scripts/sd101_check.py
    python3 scripts/sd101_check.py --store system-design-101/vi --source-map path.json
Exit status is 1 when any problem is found.
"""

from __future__ import annotations

import argparse
import datetime
import ipaddress
import json
import pathlib
import posixpath
import re
import sys
import xml.etree.ElementTree as ElementTree
import xml.parsers.expat as expat
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

import yaml
from markdown_it import MarkdownIt

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_STORE = ROOT / "system-design-101" / "vi"
DEFAULT_SOURCE_MAP = ROOT / "brainstorm" / "system-design-101-vi" / "source-map.json"

KEYS = {"id", "title_vi", "content_status", "verification", "learner_test", "image_evidence"}
VERIFICATION_KEYS = {"source_read", "claims", "technical", "mobile"}
CONTENT_STATUS = {"planned", "drafted", "approved"}
CHECK_STATE = {"pending", "done"}
IMAGE_EVIDENCE_KEYS = {"url", "sha256", "retrieved_on"}

LESSON_ID = re.compile(r"\bsd-\d{2}-\d{3}\b")
SHA256 = re.compile(r"[0-9a-fA-F]{64}")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
BLOCKQUOTE_PREFIX = re.compile(r"^(?:\s*>)+")
HOSTNAME = re.compile(r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.?")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
SOURCE_IMAGE_HOST = "assets.bytebytego.com"
ALLOWED_FILES = {"lesson.md", "lesson.yaml"}
STORE_ENTRIES = {"README.md", "lessons"}
LESSON_LINK = re.compile(r"lessons/(sd-\d{2}-\d{3})/lesson\.md")
ALLOWED_HTML = {"details", "summary", "br", "a", "img", "sub", "sup", "kbd"}
RASTER_ELEMENTS = {"image", "feimage", "img"}
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
# The elements of a plain drawing. Anything else (foreignObject and the HTML inside it, script, a, animation,
# image) is refused rather than hunted one by one: each is a way to carry or load something that is not drawn.
SVG_ELEMENTS = {
    "svg", "g", "defs", "symbol", "use", "title", "desc", "style",
    "path", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "text", "tspan", "textpath", "marker", "pattern", "mask", "clippath", "lineargradient", "radialgradient", "stop",
    "filter", "feblend", "fecolormatrix", "fecomposite", "fedropshadow", "fegaussianblur", "feflood", "feoffset",
    "femerge", "femergenode",
}
ANIMATION = re.compile(r"@keyframes|\banimation(?:-[a-z-]+)?\s*:|\btransition(?:-[a-z-]+)?\s*:", re.IGNORECASE)
URL_CALL = re.compile(r"url\(\s*['\"]?\s*([^)'\"\s]*)", re.IGNORECASE)


@dataclass(frozen=True)
class Problem:
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


def load_source_map(path: pathlib.Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {lesson["id"]: lesson for category in data["categories"] for lesson in category["lessons"]}


def srcset_urls(value: str) -> list[str]:
    """The URLs of an <img srcset> value: each candidate is a URL, then optional descriptors, comma separated."""
    urls: list[str] = []
    position = 0
    while True:
        match = re.compile(r"[\s,]*(\S+)").match(value, position)
        if match is None:
            return urls
        url, position = match.group(1), match.end()
        if url.endswith(","):
            url = url.rstrip(",")
        else:
            comma = value.find(",", position)
            position = len(value) if comma == -1 else comma + 1
        urls.append(url)


class StrictLoader(yaml.SafeLoader):
    """A safe YAML loader that refuses a mapping naming the same key twice (safe_load keeps the last one)."""

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            seen = set()
            for key_node, _value in node.value:
                if key_node.tag == "tag:yaml.org,2002:merge":  # `<<: *anchor`; an explicit key may override it
                    continue
                key = self.construct_object(key_node, deep=True)
                try:
                    duplicate = key in seen
                except TypeError:  # an unhashable key; the base class reports it
                    continue
                if duplicate:
                    raise yaml.constructor.ConstructorError("while constructing a mapping", node.start_mark,
                                                            f"found duplicate key {key!r}", key_node.start_mark)
                seen.add(key)
        return super().construct_mapping(node, deep=deep)


class HtmlScan(HTMLParser):
    """Facts about the HTML tags in a piece of HTML: which tags, each <a href>, each <img src> and srcset URL,
    <details> nesting.

    Comments and attribute text are not tags, so a quoted "href=..." or a commented-out tag counts for nothing.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: set[str] = set()
        self.hrefs: list[str] = []
        self.srcs: list[str] = []
        self.details_depth = 0
        self.stray_details_close = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.add(tag)
        if tag == "a":
            self.hrefs.extend(value for name, value in attrs if name == "href" and value)
        elif tag == "img":
            sources = [value for name, value in attrs if name == "src" and value]
            for name, value in attrs:
                if name == "srcset" and value:
                    sources.extend(srcset_urls(value))
            self.srcs.extend(sources or [""])
        elif tag == "details":
            self.details_depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """A self-closing tag is a start tag: in HTML <details/> still opens a details element."""
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        self.tags.add(tag)
        if tag == "details":
            if self.details_depth:
                self.details_depth -= 1
            else:
                self.stray_details_close = True


def markdown_tokens(text: str) -> list:
    """Every token Markdown (CommonMark plus GFM tables) produces for text, inline children included."""
    tokens: list = []
    for token in MarkdownIt("commonmark").enable("table").parse(text):
        tokens.append(token)
        tokens.extend(token.children or [])
    return tokens


def html_scan(text: str) -> HtmlScan:
    """Scan only the HTML Markdown would render: not code blocks, code spans or comments."""
    scan = HtmlScan()
    for token in markdown_tokens(text):
        if token.type in ("html_inline", "html_block"):
            scan.feed(token.content)
    return scan


def has_unclosed_fence(text: str) -> bool:
    """True when a code fence (``` or ~~~, any length) is still open at the end of the file."""
    lines = text.split("\n")
    for token in markdown_tokens(text):
        if token.type == "fence" and token.map:
            last = token.map[1] - 1
            closing = BLOCKQUOTE_PREFIX.sub("", lines[last]).strip() if token.map[0] < last < len(lines) else ""
            if not (closing and set(closing) == {token.markup[0]} and len(closing) >= len(token.markup)):
                return True
    return False


def link_sequence(text: str) -> list[str]:
    """Destinations of the links Markdown would render, in the order a reader meets them:
    [x](url), [x][ref] and <a href>.

    A URL in a code block, an HTML comment or plain prose is not a link, so it is not returned.
    """
    found: list[str] = []
    for token in markdown_tokens(text):
        if token.type == "link_open":
            found.append(token.attrGet("href") or "")
        elif token.type in ("html_inline", "html_block"):
            scan = HtmlScan()
            scan.feed(token.content)
            found.extend(scan.hrefs)
    return found


def link_destinations(text: str) -> set[str]:
    """The distinct destinations of the links Markdown would render."""
    return set(link_sequence(text))


def image_sources(text: str) -> set[str]:
    """Sources of the images Markdown would render: ![x](src), ![x][ref] and <img src>."""
    found = {token.attrGet("src") or "" for token in markdown_tokens(text) if token.type == "image"}
    return found | set(html_scan(text).srcs)


def table_cells(text: str) -> list[str]:
    """The text shown in every cell of every table Markdown would render, with or without outer pipes.

    It is read from the inline tokens, so link syntax, emphasis marks, HTML tags and entities are gone.
    """
    tokens = markdown_tokens(text)
    return ["".join(child.content for child in following.children or []
                    if child.type in ("text", "text_special", "code_inline"))
            for token, following in zip(tokens, tokens[1:])
            if token.type in ("th_open", "td_open") and following.type == "inline"]


def relative_target(destination: str) -> str | None:
    """The path part of a relative link destination; None for an anchor, a URL or a mail link."""
    if destination.startswith(("#", "//")) or SCHEME.match(destination):
        return None
    return unquote(destination.split("#")[0].split("?")[0]) or None


def exists(path: pathlib.Path) -> bool:
    """path.exists(), but a name the filesystem rejects (too long, embedded NUL) simply does not exist."""
    try:
        return path.exists()
    except (OSError, ValueError):
        return False


def valid_host(host: str | None) -> bool:
    """A DNS name (ASCII labels, as in a copied address bar) or an IP address; not empty, not '.' or '-a'."""
    if not host:
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return HOSTNAME.fullmatch(host) is not None
    return True


def valid_url(url: object) -> bool:
    """An http(s) URL with a real host and a readable port, no whitespace or control characters."""
    if not isinstance(url, str) or any(char.isspace() or not char.isprintable() for char in url):
        return False
    try:
        parsed = urlparse(url)
        parsed.port
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and valid_host(parsed.hostname)


def one_of(value: object, vocabulary: set[str]) -> bool:
    """True when value is a string in the vocabulary; a list or mapping from YAML is simply not."""
    return isinstance(value, str) and value in vocabulary


def valid_date(when: object) -> bool:
    """A real calendar date: a date object (YAML turns an unquoted 2026-10-12 into one; a timestamp is not one)
    or a YYYY-MM-DD string."""
    if isinstance(when, datetime.date):
        return not isinstance(when, datetime.datetime)
    if not isinstance(when, str) or ISO_DATE.fullmatch(when) is None:
        return False
    try:
        datetime.date.fromisoformat(when)
    except ValueError:
        return False
    return True


def valid_image_evidence(item: object) -> bool:
    """An entry has an http(s) url with a host, a 64-hex sha256 and a real date."""
    if not isinstance(item, dict) or set(item) != IMAGE_EVIDENCE_KEYS:
        return False
    digest = item["sha256"]
    return (valid_url(item["url"]) and isinstance(digest, str) and SHA256.fullmatch(digest) is not None
            and valid_date(item["retrieved_on"]))


def local_name(name: object) -> str:
    """The lower-case local part of an XML name: '{namespace}feImage' -> 'feimage'."""
    return name.rsplit("}", 1)[-1].lower() if isinstance(name, str) else ""


def reaches_outside(value: str) -> bool:
    """True when a CSS or attribute value has an @import or a url() that is not a #fragment of the drawing."""
    return "@import" in value.lower() or any(not target.startswith("#") for target in URL_CALL.findall(value))


def namespace_of(tag: object) -> str:
    """The namespace of an ElementTree tag such as '{http://www.w3.org/2000/svg}rect'; '' when it has none."""
    return tag[1:].split("}", 1)[0] if isinstance(tag, str) and tag.startswith("{") else ""


def processing_instructions(raw: bytes) -> list[str]:
    """The targets of the processing instructions in an XML document (the XML declaration is not one)."""
    found: list[str] = []
    parser = expat.ParserCreate()
    parser.ProcessingInstructionHandler = lambda target, data: found.append(target)
    parser.Parse(raw, True)  # ElementTree has already read this file, so it is well-formed
    return found


def svg_problem(path: pathlib.Path) -> str | None:
    """Why a file named *.svg is not a self-contained drawing made for the lesson, or None."""
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError, LookupError):
        return "is not well-formed XML, so it is not an SVG"
    if root.tag.rsplit("}", 1)[-1] != "svg":
        return "does not have an <svg> root element"
    if SOURCE_IMAGE_HOST in path.read_text(encoding="utf-8", errors="replace").lower():
        return f"contains {SOURCE_IMAGE_HOST}; figures must not use source images"
    if found := processing_instructions(path.read_bytes()):
        return f"has a processing instruction (<?{found[0]} ...?>), which can load a stylesheet or other file"
    for element in root.iter():
        name = local_name(element.tag)
        if name in RASTER_ELEMENTS:
            return f"embeds a picture with <{name}>"
        if name not in SVG_ELEMENTS or namespace_of(element.tag) not in ("", SVG_NAMESPACE):
            return f"uses <{name}>, which is not an element of a plain SVG drawing"
        values = list(element.attrib.items())
        if name == "style":
            values.append(("style", element.text or ""))
        for attribute, value in values:
            if local_name(attribute) == "href" and not value.strip().startswith("#"):
                return f"links to {value.strip()!r}, outside the drawing"
            if reaches_outside(value):
                return "refers to something outside the drawing with url() or @import"
            if ANIMATION.search(value):
                return "uses a CSS animation or transition, but a figure is static"
    return None


def check_yaml(lesson_id: str, meta: object, entries: dict[str, dict]) -> list[Problem]:
    if not isinstance(meta, dict):
        return [Problem(lesson_id, "lesson.yaml is not a mapping")]
    problems: list[Problem] = []
    if set(meta) != KEYS:
        problems.append(Problem(lesson_id, f"lesson.yaml keys are {sorted(map(str, meta))}, expected {sorted(KEYS)}"))
    if meta.get("id") != lesson_id:
        problems.append(Problem(lesson_id, f"id is {meta.get('id')!r}, expected the directory name"))
    entry = entries.get(lesson_id)
    title = meta.get("title_vi")
    if entry is None:
        problems.append(Problem(lesson_id, "id is not in the source map"))
    if not isinstance(title, str) or not title.strip():
        problems.append(Problem(lesson_id, "title_vi must be a non-empty string"))
    elif entry is not None and title != entry.get("title_vi"):
        problems.append(Problem(lesson_id, "title_vi differs from the source map"))

    status = meta.get("content_status")
    if not one_of(status, CONTENT_STATUS):
        problems.append(Problem(lesson_id, f"content_status {status!r} is not one of {sorted(CONTENT_STATUS)}"))
    verification = meta.get("verification")
    states = {"learner_test": meta.get("learner_test")}
    if not isinstance(verification, dict) or set(verification) != VERIFICATION_KEYS:
        problems.append(Problem(lesson_id, f"verification must have exactly {sorted(VERIFICATION_KEYS)}"))
    else:
        states.update(verification)
    for name, value in states.items():
        if not one_of(value, CHECK_STATE):
            problems.append(Problem(lesson_id, f"{name} {value!r} is not one of {sorted(CHECK_STATE)}"))
    if status == "approved" and any(value != "done" for value in states.values()):
        problems.append(Problem(lesson_id, "approved needs every verification field and learner_test to be done"))

    evidence = meta.get("image_evidence")
    if not isinstance(evidence, list):
        problems.append(Problem(lesson_id, "image_evidence must be a list"))
    else:
        for item in evidence:
            if not valid_image_evidence(item):
                problems.append(Problem(lesson_id, "each image_evidence entry needs an http(s) url, a 64-hex sha256 "
                                                   "and a retrieved_on date"))
    return problems


def check_markdown(lesson_id: str, text: str, lesson_dir: pathlib.Path, entries: dict[str, dict],
                   lesson_ids: set[str]) -> list[Problem]:
    problems: list[Problem] = []
    if has_unclosed_fence(text):
        problems.append(Problem(lesson_id, "lesson.md has an unclosed code fence"))
    scan = html_scan(text)
    if scan.stray_details_close or scan.details_depth:
        problems.append(Problem(lesson_id, "lesson.md has unbalanced <details> tags"))
    for tag in sorted(scan.tags - ALLOWED_HTML):
        problems.append(Problem(lesson_id, f"lesson.md uses <{tag}>; raw HTML is limited to "
                                           f"{', '.join(sorted(ALLOWED_HTML))}"))
    sources = image_sources(text)
    for destination in sorted(link_destinations(text) | sources):
        target = relative_target(destination)
        if target is not None and not exists(lesson_dir / target):
            problems.append(Problem(lesson_id, f"relative link {destination!r} does not resolve"))
    for source in sorted(sources):
        target = relative_target(source)
        if target is None or not target.lower().endswith(".svg") or posixpath.dirname(posixpath.normpath(target)):
            problems.append(Problem(lesson_id, f"image {source!r} must be a local .svg file drawn for the lesson, "
                                               "directly inside the lesson directory"))
    if lesson_id in entries:
        snapshot = entries[lesson_id].get("source_snapshot_url")
        if not isinstance(snapshot, str) or not snapshot.strip():
            problems.append(Problem(lesson_id, "the source map has no source_snapshot_url for this lesson"))
        elif snapshot not in {destination.split("#")[0] for destination in link_destinations(text)}:
            problems.append(Problem(lesson_id, "lesson.md does not link the pinned source snapshot"))
    for mentioned in sorted(set(LESSON_ID.findall(text))):
        if mentioned not in lesson_ids:
            problems.append(Problem(lesson_id, f"mentions {mentioned}, which has no lesson directory"))
    if SOURCE_IMAGE_HOST in text.lower():
        problems.append(Problem(lesson_id, f"contains {SOURCE_IMAGE_HOST}; lessons must not use source images"))
    return problems


def plain_cell(cell: str) -> str:
    """What a table cell shows, compared with the vocabulary: no stray emphasis marks or edge punctuation, lower case."""
    return re.sub(r"[*_`~]", "", cell).strip(" .,;:").lower()


def check_readme(store: pathlib.Path, lesson_ids: set[str], entries: dict[str, dict]) -> list[Problem]:
    readme = store / "README.md"
    if not readme.is_file():
        return [Problem("README.md", "is missing")]
    try:
        text = readme.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [Problem("README.md", "is not valid UTF-8 text")]
    destinations = {destination: relative_target(destination) for destination in link_sequence(text)}
    linked = {posixpath.normpath(target) for target in destinations.values() if target}
    listed: list[str] = []
    for target in destinations.values():
        match = LESSON_LINK.fullmatch(posixpath.normpath(target)) if target else None
        if match and match.group(1) in lesson_ids and match.group(1) not in listed:
            listed.append(match.group(1))
    in_source_order = [lesson_id for lesson_id in entries if lesson_id in listed]
    problems = [Problem("README.md", f"does not link lessons/{lesson_id}/lesson.md")
                for lesson_id in sorted(lesson_ids) if f"lessons/{lesson_id}/lesson.md" not in linked]
    problems.extend(Problem("README.md", f"uses <{tag}>; raw HTML is limited to {', '.join(sorted(ALLOWED_HTML))}")
                    for tag in sorted(html_scan(text).tags - ALLOWED_HTML))
    problems.extend(Problem("README.md", f"embeds the image {source!r}; the index has no figures")
                    for source in sorted(image_sources(text)))
    problems.extend(Problem("README.md", f"relative link {destination!r} does not resolve")
                    for destination, target in sorted(destinations.items())
                    if target and not exists(store / target))
    if listed != in_source_order:
        problems.append(Problem("README.md", "lists the lessons out of source order; the source map order is "
                                             + ", ".join(in_source_order)))
    if any(plain_cell(cell) in CONTENT_STATUS for cell in table_cells(text)):
        problems.append(Problem("README.md", "repeats a lesson status; it lives only in lesson.yaml"))
    return problems


def check_store(store: pathlib.Path, source_map: pathlib.Path) -> list[Problem]:
    entries = load_source_map(source_map)
    lessons_dir = store / "lessons"
    lesson_dirs = sorted(path for path in lessons_dir.iterdir() if path.is_dir()) if lessons_dir.is_dir() else []
    lesson_ids = {path.name for path in lesson_dirs}
    problems: list[Problem] = []
    for path in sorted(store.iterdir()) if store.is_dir() else []:
        if path.name not in STORE_ENTRIES:
            problems.append(Problem(path.name, "is not allowed in the store, which holds only README.md and lessons/"))
    for path in sorted(lessons_dir.iterdir()) if lessons_dir.is_dir() else []:
        if not path.is_dir():
            problems.append(Problem("lessons", f"{path.name} is not a lesson directory"))
    for lesson_dir in lesson_dirs:
        lesson_id = lesson_dir.name
        markdown, meta_file = lesson_dir / "lesson.md", lesson_dir / "lesson.yaml"
        for path in sorted(lesson_dir.iterdir()):
            if path.name not in ALLOWED_FILES and not (path.is_file() and path.suffix.lower() == ".svg"):
                problems.append(Problem(lesson_id, f"{path.name} is not allowed; a lesson directory holds only "
                                                   "lesson.md, lesson.yaml and .svg figures drawn for it"))
            elif path.is_file() and path.suffix.lower() == ".svg" and (reason := svg_problem(path)):
                problems.append(Problem(lesson_id, f"{path.name} {reason}"))
        for required in (markdown, meta_file):
            if not required.is_file():
                problems.append(Problem(lesson_id, f"{required.name} is missing"))
        if meta_file.is_file():
            try:
                meta = yaml.load(meta_file.read_text(encoding="utf-8"), Loader=StrictLoader)  # noqa: S506
            except (yaml.YAMLError, ValueError) as error:
                problems.append(Problem(lesson_id, f"lesson.yaml does not parse: {error}"))
            else:
                problems.extend(check_yaml(lesson_id, meta, entries))
        if markdown.is_file():
            try:
                text = markdown.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                problems.append(Problem(lesson_id, "lesson.md is not valid UTF-8 text"))
            else:
                problems.extend(check_markdown(lesson_id, text, lesson_dir, entries, lesson_ids))
    problems.extend(check_readme(store, lesson_ids, entries))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--store", type=pathlib.Path, default=DEFAULT_STORE)
    parser.add_argument("--source-map", type=pathlib.Path, default=DEFAULT_SOURCE_MAP)
    arguments = parser.parse_args(argv)
    problems = check_store(arguments.store, arguments.source_map)
    for problem in problems:
        print(problem)
    lessons_dir = arguments.store / "lessons"
    count = sum(1 for path in lessons_dir.iterdir() if path.is_dir()) if lessons_dir.is_dir() else 0
    print(f"sd101_check: {count} lesson(s), {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
