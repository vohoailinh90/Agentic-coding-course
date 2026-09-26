"""The course as the rest of the code sees it, once course/*.yaml are valid.

The validator (`src/core/validate.py`) is the only code that reads the raw YAML;
it builds these objects only after every check on the tree has passed, so the
tools that use them never have to re-check a missing title or a bad id.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

COURSE_FILE = "course/course.yaml"
CURRICULUM_FILE = "course/curriculum.yaml"
GLOSSARY_FILE = "course/glossary.yaml"
SECTIONS_FILE = "course/sections.yaml"
LESSONS_DIR = "course/lessons"
OUTLINE_FILE = "course/OUTLINE.md"

# Ids are stable handles: position in curriculum.yaml decides the order, so a
# lesson can move without its id, its folder or any post that cites it changing.
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LANGUAGE_CODE = re.compile(r"^[a-z]{2,3}$")
LESSON_TYPES = ("concept", "demo", "hands-on", "project")
# todo: skeleton only · draft: being written · review: complete, awaiting review
# · done: reviewed and publishable (the only status a post should come from).
STATUSES = ("todo", "draft", "review", "done")
ASSETS_DIR = "assets"


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


@dataclass(frozen=True)
class Unit:
    id: str
    title: dict[str, str]
    number: str
    lessons: tuple[Lesson, ...]


@dataclass(frozen=True)
class Module:
    id: str
    title: dict[str, str]
    goal: dict[str, str]
    number: str
    units: tuple[Unit, ...]


@dataclass(frozen=True)
class Course:
    id: str
    version: str
    languages: tuple[str, ...]
    source_language: str
    title: dict[str, str]
    tagline: dict[str, str]
    hashtags: dict[str, tuple[str, ...]]
    curriculum_version: str
    modules: tuple[Module, ...]
    glossary: dict[str, Term]
    sections: tuple[Section, ...]

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


def lesson_path(lesson_id: str, language: str) -> str:
    """The repository-relative path of one language file of a lesson."""
    return f"{LESSONS_DIR}/{lesson_id}/{language}.md"
