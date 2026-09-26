"""The course as the rest of the code sees it, once the files under course/ are valid.

The validator (`src/core/validate.py`) is the only code that reads the raw YAML;
it builds these objects only after every check on the tree has passed, so the
tools that use them never have to re-check a missing title or a bad id.

Layout (docs/data-model.md):

    course/README.md                  generated language chooser
    course/data/*.yaml                shared sources, every language inside
    course/data/diagrams/<id>.yaml    infographic specs
    course/<lang>/README.md           generated course home, one language
    course/<lang>/glossary.md         generated glossary page
    course/<lang>/lessons/<id>.md     hand-written lessons, one language
    course/<lang>/diagrams/<id>.svg   generated infographics
    course/<lang>/images/             optional hand-made images
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

COURSE_DIR = "course"
DATA_DIR = "course/data"
COURSE_FILE = "course/data/course.yaml"
CURRICULUM_FILE = "course/data/curriculum.yaml"
GLOSSARY_FILE = "course/data/glossary.yaml"
SECTIONS_FILE = "course/data/sections.yaml"
DIAGRAMS_DIR = "course/data/diagrams"
CHOOSER_FILE = "course/README.md"

# What may sit directly in course/ and in each language folder.
LANGUAGE_ENTRIES = ("README.md", "glossary.md", "lessons", "diagrams", "images")
ROADMAP = "roadmap"  # the generated journey map; no spec may use this id

# Ids are stable handles: position in curriculum.yaml decides the order, so a
# lesson can move without its id, its files or any post that cites it changing.
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LANGUAGE_CODE = re.compile(r"^[a-z]{2,3}$")
LESSON_TYPES = ("concept", "demo", "hands-on", "project")
# core: the main path; optional: background a learner may skip; advanced: after the course.
TRACKS = ("core", "optional", "advanced")
# todo: skeleton only · draft: being written · review: complete, awaiting review
# · done: reviewed and publishable (the only status a post should come from).
STATUSES = ("todo", "draft", "review", "done")


@dataclass(frozen=True)
class Section:
    key: str
    required_for: frozenset[str]
    heading: dict[str, str]
    hint: dict[str, str]


@dataclass(frozen=True)
class Term:
    id: str
    # language -> {"term": ..., "definition": ..., optional "reading": ...}
    entries: dict[str, dict[str, str]]


@dataclass(frozen=True)
class Lesson:
    id: str
    title: dict[str, str]
    type: str
    minutes: int
    terms: tuple[str, ...]
    number: str  # "2.1.3": display only, derived from position
    module_id: str
    unit_id: str
    track: str = "core"  # its unit's track


@dataclass(frozen=True)
class Unit:
    id: str
    title: dict[str, str]
    number: str
    lessons: tuple[Lesson, ...]
    track: str = "core"


@dataclass(frozen=True)
class Module:
    id: str
    title: dict[str, str]
    goal: dict[str, str]
    number: str
    units: tuple[Unit, ...]
    icon: str = "📘"

    @property
    def lessons(self) -> list[Lesson]:
        return [lesson for unit in self.units for lesson in unit.lessons]


@dataclass(frozen=True)
class Course:
    id: str
    version: str
    languages: tuple[str, ...]
    source_language: str
    title: dict[str, str]
    tagline: dict[str, str]
    audience: dict[str, str]
    hashtags: dict[str, tuple[str, ...]]
    curriculum_version: str
    modules: tuple[Module, ...]
    glossary: dict[str, Term]
    sections: tuple[Section, ...]
    diagrams: dict[str, dict] = field(default_factory=dict)  # id -> validated spec
    minimum_path: tuple[str, ...] = ()  # lesson ids, in the order a learner takes them
    retired: dict[str, str | None] = field(default_factory=dict)  # retired id -> the lesson that took over

    @property
    def units(self) -> list[Unit]:
        return [unit for module in self.modules for unit in module.units]

    @property
    def lessons(self) -> list[Lesson]:
        return [lesson for unit in self.units for lesson in unit.lessons]

    def lesson(self, lesson_id: str) -> Lesson | None:
        return next((lesson for lesson in self.lessons if lesson.id == lesson_id), None)

    @property
    def total_minutes(self) -> int:
        return sum(lesson.minutes for lesson in self.lessons)

    @property
    def minimum_path_lessons(self) -> list[Lesson]:
        by_id = {lesson.id: lesson for lesson in self.lessons}
        return [by_id[lesson_id] for lesson_id in self.minimum_path]


def language_dir(language: str) -> str:
    return f"{COURSE_DIR}/{language}"


def lessons_dir(language: str) -> str:
    return f"{COURSE_DIR}/{language}/lessons"


def lesson_path(lesson_id: str, language: str) -> str:
    """The repository-relative path of one language file of a lesson."""
    return f"{COURSE_DIR}/{language}/lessons/{lesson_id}.md"


def diagram_path(diagram_id: str, language: str) -> str:
    return f"{COURSE_DIR}/{language}/diagrams/{diagram_id}.svg"


def relative_link(source: str, target: str) -> str:
    """How a Markdown file at `source` links to `target` (both repository-relative)."""
    return posixpath.relpath(target, posixpath.dirname(source))
