"""Validate the content store under course/ and build the Course model from it.

Every check here has a computable answer, so it is a script and a CI step, not
a review step (CLAUDE.md, "Deterministic work is not agent work"):

- course.yaml, sections.yaml, glossary.yaml and curriculum.yaml have the right
  shape, every user-facing field in every course language, unique kebab-case
  ids, and only known lesson types and glossary terms;
- every started lesson has one file per language, whose front matter, title and
  section markers agree with curriculum.yaml and sections.yaml;
- a file's status decides how complete it must be (todo < draft < review < done);
- all non-todo language files of a lesson share the same sections in the same
  order, so no translation silently drops or adds a part;
- course/OUTLINE.md is exactly what the current curriculum renders to.

Findings carry a code and parameters; the words come from src/locales/, so the
same report reads in Vietnamese, English or Japanese.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.core import yamlio
from src.core.lessonfile import LessonDoc, parse_lesson
from src.core.model import (
    ASSETS_DIR,
    COURSE_FILE,
    CURRICULUM_FILE,
    GLOSSARY_FILE,
    LANGUAGE_CODE,
    LESSON_TYPES,
    LESSONS_DIR,
    OUTLINE_FILE,
    SECTIONS_FILE,
    SLUG,
    STATUSES,
    Course,
    Lesson,
    Module,
    Section,
    Term,
    Unit,
)
from src.core.outline import render_outline
from src.utils.catalogs import translators_for

COMPLETE = ("review", "done")  # statuses that promise a finished text


@dataclass(frozen=True)
class Finding:
    level: str  # "error" or "warning"
    code: str
    params: dict


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    course: Course | None = None
    # (lesson id, language) -> parsed file, for every file that could be read
    docs: dict[tuple[str, str], LessonDoc] = field(default_factory=dict)

    def error(self, code: str, **params: object) -> None:
        self.findings.append(Finding("error", code, params))

    def warning(self, code: str, **params: object) -> None:
        self.findings.append(Finding("warning", code, params))

    @property
    def errors(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


class _Invalid(Exception):
    """A file is too broken to check further; its findings are already recorded."""


# ---------------------------------------------------------------------------
# Field checks shared by every YAML file
# ---------------------------------------------------------------------------


def _where(parent: str, child: str) -> str:
    return f"{parent}.{child}" if parent else child


class _Checker:
    """Records findings against one file, and counts whether any were added."""

    def __init__(self, report: Report, path: str) -> None:
        self.report = report
        self.path = path
        self.start = len(report.errors)

    @property
    def clean(self) -> bool:
        return len(self.report.errors) == self.start

    def error(self, code: str, **params: object) -> None:
        self.report.error(code, path=self.path, **params)

    def mapping(self, value: object, where: str) -> dict | None:
        if isinstance(value, dict):
            return value
        self.error("field_type", field=where or "(root)", expected="mapping")
        return None

    def keys(self, obj: dict, where: str, required: tuple[str, ...], optional: tuple[str, ...] = ()) -> None:
        for key in required:
            if key not in obj:
                self.error("field_missing", field=_where(where, key))
        for key in obj:
            if key not in required and key not in optional:
                self.error("field_unknown", field=_where(where, str(key)))

    def text(self, value: object, where: str, *, allow_empty: bool = False) -> str | None:
        if not isinstance(value, str):
            self.error("field_type", field=where, expected="text")
            return None
        if not allow_empty and not value.strip():
            self.error("field_empty", field=where)
            return None
        return value.strip()

    def items(self, value: object, where: str) -> list:
        if isinstance(value, list) and value:
            return value
        if isinstance(value, list):
            self.error("field_empty", field=where)
        else:
            self.error("field_type", field=where, expected="list")
        return []

    def localized(self, obj: dict, key: str, where: str, languages: tuple[str, ...]) -> dict[str, str] | None:
        """obj[key] as {language: non-empty text} for exactly the course languages."""
        name = _where(where, key)
        if key not in obj:
            return None  # reported by keys()
        value = self.mapping(obj[key], name)
        if value is None:
            return None
        result: dict[str, str] = {}
        for language in languages:
            if language not in value:
                self.error("field_missing", field=_where(name, language))
                continue
            text = self.text(value[language], _where(name, language))
            if text is not None:
                result[language] = text
        for extra in value:
            if extra not in languages:
                self.error("field_unknown", field=_where(name, str(extra)))
        return result if len(result) == len(languages) else None

    def slug(self, value: object, where: str, seen: set[str]) -> str | None:
        if not isinstance(value, str) or not SLUG.match(value):
            self.error("id_invalid", id=str(value), field=where)
            return None
        if value in seen:
            self.error("id_duplicate", id=value)
            return None
        seen.add(value)
        return value


def _load(report: Report, root: Path, relative: str) -> object:
    path = root / relative
    if not path.is_file():
        report.error("file_missing", path=relative)
        raise _Invalid
    try:
        return yamlio.loads(yamlio.read_text(path))
    except UnicodeDecodeError:
        report.error("encoding_invalid", path=relative)
    except yamlio.ContentYAMLError as exc:
        report.error("yaml_invalid", path=relative, detail=str(exc))
    raise _Invalid


def used_in_order(terms: list) -> list[str]:
    """The distinct string terms of a lesson, first occurrence first."""
    return list(dict.fromkeys(term for term in terms if isinstance(term, str)))


def _label(item: object, index: int) -> str:
    """How a list item is named in a finding: its id when it has a usable one."""
    if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]:
        return item["id"]
    if isinstance(item, dict) and isinstance(item.get("key"), str) and item["key"]:
        return item["key"]
    return str(index)


# ---------------------------------------------------------------------------
# course/course.yaml, sections.yaml, glossary.yaml, curriculum.yaml
# ---------------------------------------------------------------------------


def _course_meta(report: Report, root: Path) -> dict:
    check = _Checker(report, COURSE_FILE)
    data = check.mapping(_load(report, root, COURSE_FILE), "")
    if data is None:
        raise _Invalid
    check.keys(
        data, "",
        required=("id", "version", "languages", "source_language", "title", "tagline", "audience", "hashtags"),
    )
    languages = data.get("languages")
    if (
        not isinstance(languages, list)
        or not languages
        or not all(isinstance(code, str) and LANGUAGE_CODE.match(code) for code in languages)
    ):
        check.error("field_type", field="languages", expected="language_list")
        raise _Invalid
    if len(set(languages)) != len(languages):
        check.error("id_duplicate", id=", ".join(languages))
        raise _Invalid
    languages = tuple(languages)
    meta: dict = {"languages": languages}
    meta["id"] = check.slug(data["id"], "id", set()) if "id" in data else None
    meta["version"] = check.text(data["version"], "version") if "version" in data else None
    source = data.get("source_language")
    if "source_language" in data and source not in languages:
        check.error("value_invalid", field="source_language", value=str(source), allowed=", ".join(languages))
    meta["source_language"] = source
    for key in ("title", "tagline", "audience"):
        meta[key] = check.localized(data, key, "", languages)
    hashtags = check.mapping(data["hashtags"], "hashtags") if "hashtags" in data else None
    meta["hashtags"] = {}
    if hashtags is not None:
        for language in languages:
            tags = hashtags.get(language)
            if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.startswith("#") for tag in tags):
                check.error("field_type", field=f"hashtags.{language}", expected="list")
                continue
            meta["hashtags"][language] = tuple(tags)
        for extra in hashtags:
            if extra not in languages:
                check.error("field_unknown", field=f"hashtags.{extra}")
    if not check.clean:
        raise _Invalid
    return meta


def _sections(report: Report, root: Path, languages: tuple[str, ...]) -> tuple[Section, ...]:
    check = _Checker(report, SECTIONS_FILE)
    data = check.mapping(_load(report, root, SECTIONS_FILE), "")
    if data is None:
        raise _Invalid
    check.keys(data, "", required=("sections",))
    sections: list[Section] = []
    seen: set[str] = set()
    for index, item in enumerate(check.items(data["sections"], "sections") if "sections" in data else [], start=1):
        where = f"sections[{_label(item, index)}]"
        item = check.mapping(item, where)
        if item is None:
            continue
        check.keys(item, where, required=("key", "required_for", "heading", "hint"))
        key = check.slug(item.get("key"), _where(where, "key"), seen)
        required_for = item.get("required_for")
        if not isinstance(required_for, list):
            check.error("field_type", field=_where(where, "required_for"), expected="list")
            required_for = []
        for lesson_type in required_for:
            if lesson_type not in LESSON_TYPES:
                check.error(
                    "value_invalid", field=_where(where, "required_for"),
                    value=str(lesson_type), allowed=", ".join(LESSON_TYPES),
                )
        heading = check.localized(item, "heading", where, languages)
        hint = check.localized(item, "hint", where, languages)
        if key and heading and hint:
            sections.append(Section(key, frozenset(required_for), heading, hint))
    if not check.clean:
        raise _Invalid
    return tuple(sections)


def _glossary(report: Report, root: Path, languages: tuple[str, ...]) -> dict[str, Term]:
    check = _Checker(report, GLOSSARY_FILE)
    data = check.mapping(_load(report, root, GLOSSARY_FILE), "")
    if data is None:
        raise _Invalid
    check.keys(data, "", required=("terms",))
    glossary: dict[str, Term] = {}
    seen: set[str] = set()
    for index, item in enumerate(check.items(data["terms"], "terms") if "terms" in data else [], start=1):
        where = f"terms[{_label(item, index)}]"
        item = check.mapping(item, where)
        if item is None:
            continue
        check.keys(item, where, required=("id", *languages))
        term_id = check.slug(item.get("id"), _where(where, "id"), seen)
        entries: dict[str, dict[str, str]] = {}
        for language in languages:
            name = _where(where, language)
            entry = check.mapping(item.get(language, {}), name) if language in item else None
            if entry is None:
                continue
            check.keys(entry, name, required=("term", "definition"), optional=("reading",))
            present = [key for key in ("term", "definition", "reading") if key in entry]
            values = {key: check.text(entry[key], _where(name, key)) for key in present}
            if "term" in values and "definition" in values and None not in values.values():
                entries[language] = values
        if term_id and len(entries) == len(languages):
            glossary[term_id] = Term(term_id, entries)
    if not check.clean:
        raise _Invalid
    return glossary


def _curriculum(
    report: Report, root: Path, languages: tuple[str, ...], glossary: dict[str, Term]
) -> tuple[str, tuple[Module, ...]]:
    check = _Checker(report, CURRICULUM_FILE)
    data = check.mapping(_load(report, root, CURRICULUM_FILE), "")
    if data is None:
        raise _Invalid
    check.keys(data, "", required=("version", "modules"))
    version = check.text(data["version"], "version") if "version" in data else None
    seen: set[str] = set()  # one namespace for module, unit and lesson ids
    modules: list[Module] = []
    raw_modules = check.items(data["modules"], "modules") if "modules" in data else []
    for m_index, raw_module in enumerate(raw_modules, start=1):
        m_where = f"modules[{_label(raw_module, m_index)}]"
        raw_module = check.mapping(raw_module, m_where)
        if raw_module is None:
            continue
        check.keys(raw_module, m_where, required=("id", "title", "goal", "units"))
        module_id = check.slug(raw_module.get("id"), _where(m_where, "id"), seen)
        module_title = check.localized(raw_module, "title", m_where, languages)
        goal = check.localized(raw_module, "goal", m_where, languages)
        units: list[Unit] = []
        raw_units = check.items(raw_module["units"], _where(m_where, "units")) if "units" in raw_module else []
        for u_index, raw_unit in enumerate(raw_units, start=1):
            u_where = f"{m_where}.units[{_label(raw_unit, u_index)}]"
            raw_unit = check.mapping(raw_unit, u_where)
            if raw_unit is None:
                continue
            check.keys(raw_unit, u_where, required=("id", "title", "lessons"))
            unit_id = check.slug(raw_unit.get("id"), _where(u_where, "id"), seen)
            unit_title = check.localized(raw_unit, "title", u_where, languages)
            unit_number = f"{m_index}.{u_index}"
            lessons: list[Lesson] = []
            raw_lessons = check.items(raw_unit["lessons"], _where(u_where, "lessons")) if "lessons" in raw_unit else []
            for l_index, raw_lesson in enumerate(raw_lessons, start=1):
                l_where = f"{u_where}.lessons[{_label(raw_lesson, l_index)}]"
                raw_lesson = check.mapping(raw_lesson, l_where)
                if raw_lesson is None:
                    continue
                check.keys(raw_lesson, l_where, required=("id", "title", "type", "minutes"), optional=("terms",))
                lesson_id = check.slug(raw_lesson.get("id"), _where(l_where, "id"), seen)
                lesson_title = check.localized(raw_lesson, "title", l_where, languages)
                lesson_type = raw_lesson.get("type")
                if "type" in raw_lesson and lesson_type not in LESSON_TYPES:
                    check.error(
                        "value_invalid", field=_where(l_where, "type"),
                        value=str(lesson_type), allowed=", ".join(LESSON_TYPES),
                    )
                minutes = raw_lesson.get("minutes")
                if "minutes" in raw_lesson and (isinstance(minutes, bool) or not isinstance(minutes, int) or minutes <= 0):
                    check.error("field_type", field=_where(l_where, "minutes"), expected="positive_integer")
                terms = raw_lesson.get("terms", [])
                if not isinstance(terms, list):
                    check.error("field_type", field=_where(l_where, "terms"), expected="list")
                    terms = []
                used: set[str] = set()
                for term in terms:
                    if not isinstance(term, str) or term not in glossary:
                        check.error("term_unknown", lesson=str(raw_lesson.get("id")), term=str(term))
                    elif term in used:
                        check.error("id_duplicate", id=term)
                    else:
                        used.add(term)
                if lesson_id and lesson_title and module_id and unit_id and lesson_type in LESSON_TYPES:
                    lessons.append(Lesson(
                        lesson_id, lesson_title, str(lesson_type), minutes if isinstance(minutes, int) else 0,
                        tuple(used_in_order(terms)),
                        f"{unit_number}.{l_index}", module_id, unit_id,
                    ))
            if unit_id and unit_title:
                units.append(Unit(unit_id, unit_title, unit_number, tuple(lessons)))
        if module_id and module_title and goal:
            modules.append(Module(module_id, module_title, goal, str(m_index), tuple(units)))
    if not check.clean or version is None:
        raise _Invalid
    used_terms = {term for module in modules for unit in module.units for lesson in unit.lessons for term in lesson.terms}
    for term_id in glossary:
        if term_id not in used_terms:
            report.warning("term_unused", path=GLOSSARY_FILE, term=term_id)
    return version, tuple(modules)


# ---------------------------------------------------------------------------
# course/lessons/<lesson-id>/<language>.md
# ---------------------------------------------------------------------------


def _lessons(report: Report, root: Path, course: Course) -> None:
    folder = root / LESSONS_DIR
    if not folder.is_dir():
        return  # no lesson started yet
    known = {lesson.id: lesson for lesson in course.lessons}
    for entry in sorted(folder.iterdir()):
        relative = f"{LESSONS_DIR}/{entry.name}"
        if entry.name.startswith("."):
            continue  # .gitkeep, .DS_Store
        if not entry.is_dir():
            report.error("lesson_file_unexpected", path=relative)
        elif entry.name not in known:
            report.error("lesson_dir_unknown", path=relative)
        else:
            _lesson_folder(report, root, course, known[entry.name], entry)


def _lesson_folder(report: Report, root: Path, course: Course, lesson: Lesson, folder: Path) -> None:
    relative = f"{LESSONS_DIR}/{lesson.id}"
    expected = {f"{language}.md" for language in course.languages}
    for child in sorted(folder.iterdir()):
        if child.name.startswith("."):
            continue
        if (child.is_dir() and child.name == ASSETS_DIR) or (child.is_file() and child.name in expected):
            continue
        report.error("lesson_file_unexpected", path=f"{relative}/{child.name}")
    docs: dict[str, LessonDoc] = {}
    for language in course.languages:
        path = folder / f"{language}.md"
        if not path.is_file():
            report.error("lesson_file_missing", path=f"{relative}/{language}.md")
            continue
        doc = _lesson_file(report, course, lesson, language, path, f"{relative}/{language}.md")
        if doc is not None:
            docs[language] = doc
            report.docs[(lesson.id, language)] = doc
    _parity(report, course, relative, docs)


def _lesson_file(
    report: Report, course: Course, lesson: Lesson, language: str, path: Path, relative: str
) -> LessonDoc | None:
    check = _Checker(report, relative)
    try:
        doc = parse_lesson(yamlio.read_text(path))
    except UnicodeDecodeError:
        check.error("encoding_invalid")
        return None
    for code, params in doc.problems:
        check.error(code, **params)
    if doc.front_error is not None:
        check.error("yaml_invalid", detail=doc.front_error)
        return None
    if not doc.has_front_matter:
        check.error("front_matter_missing")
        return None
    front = check.mapping(doc.front, "front matter")
    if front is None:
        return None
    check.keys(front, "", required=("lesson", "lang", "status", "summary", "social"))
    for key, expected in (("lesson", lesson.id), ("lang", language)):
        if key in front and front[key] != expected:
            check.error("front_matter_mismatch", field=key, expected=expected, actual=str(front[key]))
    status = front.get("status")
    if "status" in front and status not in STATUSES:
        check.error("value_invalid", field="status", value=str(status), allowed=", ".join(STATUSES))
    summary = check.text(front["summary"], "summary", allow_empty=True) if "summary" in front else None
    social = check.mapping(front["social"], "social") if "social" in front else None
    hook = question = None
    if social is not None:
        check.keys(social, "social", required=("hook", "question"))
        if "hook" in social:
            hook = check.text(social["hook"], "social.hook", allow_empty=True)
        if "question" in social:
            question = check.text(social["question"], "social.question", allow_empty=True)

    if doc.title is None:
        check.error("title_missing")
    elif doc.title != lesson.title[language]:
        check.error("title_mismatch", expected=lesson.title[language], actual=doc.title)

    order = [section.key for section in course.sections]
    seen: set[str] = set()
    last_position = -1
    for block in doc.sections:
        if block.key not in order:
            check.error("section_unknown", key=block.key)
            continue
        if block.key in seen:
            check.error("section_duplicate", key=block.key)
            continue
        seen.add(block.key)
        position = order.index(block.key)
        if position < last_position:
            check.error("section_order", key=block.key)
        last_position = max(last_position, position)

    if status not in STATUSES:
        return doc
    doc.status = status
    if status != "todo":
        for section in course.sections:
            if lesson.type in section.required_for and section.key not in seen:
                check.error("section_required", key=section.key)
    if status in COMPLETE:
        for block in doc.sections:
            if block.is_empty:
                check.error("section_empty", key=block.key)
            if block.has_todo:
                check.error("todo_left", key=block.key)
        if summary == "":
            check.error("field_empty", field="summary")
    if status == "done":
        if hook == "":
            check.error("field_empty", field="social.hook")
        if question == "":
            check.error("field_empty", field="social.question")
    return doc


def _parity(report: Report, course: Course, relative: str, docs: dict[str, LessonDoc]) -> None:
    """Every language that has left `todo` must have the same sections, in the same order."""
    started = [(language, docs[language]) for language in course.languages
               if language in docs and docs[language].status not in (None, "todo")]
    if len(started) < 2:
        return
    reference_language, reference = next(
        ((language, doc) for language, doc in started if language == course.source_language), started[0]
    )
    for language, doc in started:
        if language != reference_language and doc.keys != reference.keys:
            report.error(
                "sections_differ", path=relative, lang=language, other=reference_language,
                actual=", ".join(doc.keys), expected=", ".join(reference.keys),
            )


# ---------------------------------------------------------------------------
# course/OUTLINE.md
# ---------------------------------------------------------------------------


def _outline(report: Report, root: Path, course: Course) -> None:
    path = root / OUTLINE_FILE
    expected = render_outline(course, translators_for(course.languages))
    try:
        actual = yamlio.read_text(path) if path.is_file() else None
    except UnicodeDecodeError:
        actual = None
    if actual != expected:
        report.error("outline_stale", path=OUTLINE_FILE)


# ---------------------------------------------------------------------------


def validate(root: Path, *, check_outline: bool = True) -> Report:
    """Check the whole content store; `report.course` is set only when the tree is valid."""
    report = Report()
    try:
        meta = _course_meta(report, root)
        languages = meta["languages"]
        # Each file is checked even when an earlier one failed, so one run lists
        # every broken file instead of stopping at the first.
        results = {}
        for name, loader in (
            ("sections", lambda: _sections(report, root, languages)),
            ("glossary", lambda: _glossary(report, root, languages)),
        ):
            try:
                results[name] = loader()
            except _Invalid:
                pass
        if "glossary" not in results:
            raise _Invalid
        version, modules = _curriculum(report, root, languages, results["glossary"])
        if "sections" not in results:
            raise _Invalid
    except _Invalid:
        return report
    report.course = Course(
        id=meta["id"],
        version=meta["version"],
        languages=languages,
        source_language=meta["source_language"],
        title=meta["title"],
        tagline=meta["tagline"],
        hashtags=meta["hashtags"],
        curriculum_version=version,
        modules=modules,
        glossary=results["glossary"],
        sections=results["sections"],
    )
    _lessons(report, root, report.course)
    if check_outline:
        _outline(report, root, report.course)
    return report
