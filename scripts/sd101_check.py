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
  - image_evidence is a list, and each entry has url, sha256 and retrieved_on
  - lesson.md: code fences and <details> are balanced, every relative link
    (inline, reference-style or <a href>) resolves,
    it links the pinned source snapshot (as a real Markdown or HTML link, not text
    in a code block or a comment), it mentions no lesson id that has no lesson
    directory, and it never contains assets.bytebytego.com, the host of every
    source image, in any form: ![]() , ![x][ref], <img>, <picture>, a bare URL
And once for the store: README.md links every lesson directory (as a real link, not a
path in a comment or a code block) and carries no status words in its table (status
lives only in lesson.yaml).

Not checked, because it is not computable here: whether a claim is true, whether a
figure reads well, and the Mermaid text-size estimate (needs a browser).

Usage:
    python3 scripts/sd101_check.py
    python3 scripts/sd101_check.py --store system-design-101/vi --source-map path.json
Exit status is 1 when any problem is found.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import posixpath
import re
import sys
from dataclasses import dataclass
from urllib.parse import unquote

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
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
SOURCE_IMAGE_HOST = "assets.bytebytego.com"
HTML_LINK = re.compile(r"""<a\b[^>]*?\bhref\s*=\s*["']?([^"'\s>]+)""", re.IGNORECASE)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass(frozen=True)
class Problem:
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


def load_source_map(path: pathlib.Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {lesson["id"]: lesson for category in data["categories"] for lesson in category["lessons"]}


def link_destinations(text: str) -> set[str]:
    """Destinations of the links Markdown would render: [x](url), [x][ref] and <a href>.

    A URL in a code block, an HTML comment or plain prose is not a link, so it is not returned.
    """
    found: set[str] = set()
    for token in MarkdownIt("commonmark").parse(text):
        for item in [token, *(token.children or [])]:
            if item.type == "link_open":
                found.add(item.attrGet("href") or "")
            elif item.type in ("html_inline", "html_block"):
                found.update(HTML_LINK.findall(HTML_COMMENT.sub("", item.content)))
    return found


def relative_target(destination: str) -> str | None:
    """The path part of a relative link destination; None for an anchor, a URL or a mail link."""
    if destination.startswith(("#", "//")) or SCHEME.match(destination):
        return None
    return unquote(destination.split("#")[0].split("?")[0]) or None


def check_yaml(lesson_id: str, meta: object, entries: dict[str, dict]) -> list[Problem]:
    if not isinstance(meta, dict):
        return [Problem(lesson_id, "lesson.yaml is not a mapping")]
    problems: list[Problem] = []
    if set(meta) != KEYS:
        problems.append(Problem(lesson_id, f"lesson.yaml keys are {sorted(meta)}, expected {sorted(KEYS)}"))
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
    if status not in CONTENT_STATUS:
        problems.append(Problem(lesson_id, f"content_status {status!r} is not one of {sorted(CONTENT_STATUS)}"))
    verification = meta.get("verification")
    states = {"learner_test": meta.get("learner_test")}
    if not isinstance(verification, dict) or set(verification) != VERIFICATION_KEYS:
        problems.append(Problem(lesson_id, f"verification must have exactly {sorted(VERIFICATION_KEYS)}"))
    else:
        states.update(verification)
    for name, value in states.items():
        if value not in CHECK_STATE:
            problems.append(Problem(lesson_id, f"{name} {value!r} is not one of {sorted(CHECK_STATE)}"))
    if status == "approved" and any(value != "done" for value in states.values()):
        problems.append(Problem(lesson_id, "approved needs every verification field and learner_test to be done"))

    evidence = meta.get("image_evidence")
    if not isinstance(evidence, list):
        problems.append(Problem(lesson_id, "image_evidence must be a list"))
    else:
        for item in evidence:
            if not isinstance(item, dict) or set(item) != IMAGE_EVIDENCE_KEYS:
                problems.append(Problem(lesson_id, f"each image_evidence entry needs {sorted(IMAGE_EVIDENCE_KEYS)}"))
    return problems


def check_markdown(lesson_id: str, text: str, lesson_dir: pathlib.Path, entries: dict[str, dict],
                   lesson_ids: set[str]) -> list[Problem]:
    problems: list[Problem] = []
    if text.count("```") % 2:
        problems.append(Problem(lesson_id, "lesson.md has an unclosed code fence"))
    if text.count("<details>") != text.count("</details>"):
        problems.append(Problem(lesson_id, "lesson.md has unbalanced <details> tags"))
    for destination in sorted(link_destinations(text)):
        target = relative_target(destination)
        if target is not None and not (lesson_dir / target).exists():
            problems.append(Problem(lesson_id, f"relative link {destination!r} does not resolve"))
    snapshot = entries.get(lesson_id, {}).get("source_snapshot_url")
    if snapshot and snapshot not in link_destinations(text):
        problems.append(Problem(lesson_id, "lesson.md does not link the pinned source snapshot"))
    for mentioned in sorted(set(LESSON_ID.findall(text))):
        if mentioned not in lesson_ids:
            problems.append(Problem(lesson_id, f"mentions {mentioned}, which has no lesson directory"))
    if SOURCE_IMAGE_HOST in text.lower():
        problems.append(Problem(lesson_id, f"contains {SOURCE_IMAGE_HOST}; lessons must not use source images"))
    return problems


def check_readme(store: pathlib.Path, lesson_ids: set[str]) -> list[Problem]:
    readme = store / "README.md"
    if not readme.exists():
        return [Problem("README.md", "is missing")]
    text = readme.read_text(encoding="utf-8")
    linked = {posixpath.normpath(destination) for destination in link_destinations(text)}
    problems = [Problem("README.md", f"does not link lessons/{lesson_id}/lesson.md")
                for lesson_id in sorted(lesson_ids) if f"lessons/{lesson_id}/lesson.md" not in linked]
    for row in (line for line in text.splitlines() if line.startswith("|") and "lessons/" in line):
        cells = {cell.strip() for cell in row.strip("|").split("|")}
        if cells & CONTENT_STATUS:
            problems.append(Problem("README.md", "repeats a lesson status; it lives only in lesson.yaml"))
    return problems


def check_store(store: pathlib.Path, source_map: pathlib.Path) -> list[Problem]:
    entries = load_source_map(source_map)
    lessons_dir = store / "lessons"
    lesson_dirs = sorted(path for path in lessons_dir.iterdir() if path.is_dir()) if lessons_dir.is_dir() else []
    lesson_ids = {path.name for path in lesson_dirs}
    problems: list[Problem] = []
    for lesson_dir in lesson_dirs:
        lesson_id = lesson_dir.name
        markdown, meta_file = lesson_dir / "lesson.md", lesson_dir / "lesson.yaml"
        for required in (markdown, meta_file):
            if not required.exists():
                problems.append(Problem(lesson_id, f"{required.name} is missing"))
        if meta_file.exists():
            try:
                meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            except yaml.YAMLError as error:
                problems.append(Problem(lesson_id, f"lesson.yaml does not parse: {error}"))
            else:
                problems.extend(check_yaml(lesson_id, meta, entries))
        if markdown.exists():
            text = markdown.read_text(encoding="utf-8")
            problems.extend(check_markdown(lesson_id, text, lesson_dir, entries, lesson_ids))
    problems.extend(check_readme(store, lesson_ids))
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
