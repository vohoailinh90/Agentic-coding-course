"""Validate the content store under course/ and build the Course model from it.

Every check here has a computable answer, so it is a script and a CI step, not
a review step (CLAUDE.md, "Deterministic work is not agent work"):

- course/data/*.yaml and the infographic specs have the right shape, every
  user-facing field in every course language, unique kebab-case ids, and only
  known lesson types, glossary terms, templates and colours;
- nothing unexpected sits in course/, a language folder or its lessons/;
- every started lesson has a file in every language folder, whose front matter,
  language bar, title and section markers agree with the data files;
- a file's status decides how complete it must be (todo < draft < review < done);
- all non-todo translations of a lesson share the same sections and show the
  same diagrams in the same places, so no translation drops or adds a part;
- every image and relative link in a lesson points at something that exists;
- every generated file (course homes, glossary pages, infographics) is exactly
  what `python -m src.main build` renders now.

Findings carry a code and parameters; the words come from src/locales/, so the
same report reads in Vietnamese, English or Japanese.
"""

from __future__ import annotations

import posixpath
from dataclasses import dataclass, field
from pathlib import Path

from src.core import yamlio
from src.core.build import generated_files, lesson_language_bar
from src.core.infographics import PALETTE, TEMPLATES
from src.core.lessonfile import LessonDoc, parse_lesson
from src.core.model import (
    COURSE_DIR,
    COURSE_FILE,
    CURRICULUM_FILE,
    DATA_DIR,
    DIAGRAMS_DIR,
    GLOSSARY_FILE,
    LANGUAGE_CODE,
    LANGUAGE_ENTRIES,
    LESSON_TYPES,
    ROADMAP,
    SECTIONS_FILE,
    SLUG,
    STATUSES,
    Course,
    Lesson,
    Module,
    Section,
    Term,
    Unit,
    language_dir,
    lesson_path,
    lessons_dir,
)

COMPLETE = ("review", "done")  # statuses that promise a finished text
DATA_ENTRIES = ("course.yaml", "curriculum.yaml", "sections.yaml", "glossary.yaml", "diagrams")
EXTERNAL = ("http://", "https://", "mailto:", "#")


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
    started: set[str] = field(default_factory=set)  # ids of lessons that have files

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

    def items(self, value: object, where: str, *, minimum: int = 1, maximum: int | None = None) -> list:
        if not isinstance(value, list):
            self.error("field_type", field=where, expected="list")
            return []
        if not value and minimum:
            self.error("field_empty", field=where)
            return []
        if len(value) < minimum or (maximum is not None and len(value) > maximum):
            self.error("field_count", field=where, min=minimum, max=maximum if maximum is not None else "∞")
            return []
        return value

    def localized_value(self, value: object, name: str, languages: tuple[str, ...]) -> dict[str, str] | None:
        """`value` as {language: non-empty text} for exactly the course languages."""
        value = self.mapping(value, name)
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

    def localized(self, obj: dict, key: str, where: str, languages: tuple[str, ...]) -> dict[str, str] | None:
        if key not in obj:
            return None  # reported by keys()
        return self.localized_value(obj[key], _where(where, key), languages)

    def slug(self, value: object, where: str, seen: set[str]) -> str | None:
        if not isinstance(value, str) or not SLUG.match(value):
            self.error("id_invalid", id=str(value), field=where)
            return None
        if value in seen:
            self.error("id_duplicate", id=value)
            return None
        seen.add(value)
        return value

    def icon(self, obj: dict, where: str) -> None:
        if "icon" in obj:
            icon = self.text(obj["icon"], _where(where, "icon"))
            if icon is not None and len(icon) > 8:
                self.error("value_invalid", field=_where(where, "icon"), value=icon, allowed="≤ 8")

    def color(self, obj: dict, where: str) -> None:
        if "color" in obj and not (isinstance(obj["color"], str) and obj["color"] in PALETTE):
            self.error("value_invalid", field=_where(where, "color"), value=str(obj["color"]),
                       allowed=", ".join(PALETTE))

    def flag(self, obj: dict, key: str, where: str) -> None:
        if key in obj and not isinstance(obj[key], bool):
            self.error("value_invalid", field=_where(where, key), value=str(obj[key]), allowed="true, false")


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
# course/data/: course.yaml, sections.yaml, glossary.yaml, curriculum.yaml
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
    if "data" in languages:  # would collide with course/data/
        check.error("value_invalid", field="languages", value="data", allowed="language codes")
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
            # Only the valid types: an unhashable entry was reported above, and must not crash here.
            valid_types = frozenset(t for t in required_for if isinstance(t, str) and t in LESSON_TYPES)
            sections.append(Section(key, valid_types, heading, hint))
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
        check.keys(raw_module, m_where, required=("id", "title", "goal", "units"), optional=("icon",))
        module_id = check.slug(raw_module.get("id"), _where(m_where, "id"), seen)
        module_title = check.localized(raw_module, "title", m_where, languages)
        goal = check.localized(raw_module, "goal", m_where, languages)
        check.icon(raw_module, m_where)
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
            icon = raw_module.get("icon") if isinstance(raw_module.get("icon"), str) else "📘"
            modules.append(Module(module_id, module_title, goal, str(m_index), tuple(units), icon.strip() or "📘"))
    if not check.clean or version is None:
        raise _Invalid
    used_terms = {term for module in modules for unit in module.units for lesson in unit.lessons for term in lesson.terms}
    for term_id in glossary:
        if term_id not in used_terms:
            report.warning("term_unused", path=GLOSSARY_FILE, term=term_id)
    return version, tuple(modules)


# ---------------------------------------------------------------------------
# course/data/diagrams/<id>.yaml — infographic specs
# ---------------------------------------------------------------------------

# template -> (required keys, optional keys) besides the common ones
_TEMPLATE_KEYS = {
    "compare": (("rows", "columns"), ("versus", "emphasis_row")),
    "equation": (("terms", "result"), ()),
    "cycle": (("steps", "center"), ()),
    "flow": (("steps",), ("direction",)),
}
_COMMON_REQUIRED = ("template", "title")
_COMMON_OPTIONAL = ("subtitle", "takeaway")


def _visual(check: _Checker, item: object, where: str, languages: tuple[str, ...], *,
            optional: tuple[str, ...] = (), localized: tuple[str, ...] = (), color: bool = True) -> dict | None:
    """One card: icon, colour and name, plus the given optional keys."""
    item = check.mapping(item, where)
    if item is None:
        return None
    required = ("icon", "color", "name") if color else ("icon", "name")
    check.keys(item, where, required=required, optional=optional + (() if color else ("color",)))
    check.icon(item, where)
    check.color(item, where)
    check.localized(item, "name", where, languages)
    for key in localized:
        if key in item:
            check.localized(item, key, where, languages)
    return item


def _diagram(report: Report, relative: str, spec: object, languages: tuple[str, ...]) -> dict | None:
    check = _Checker(report, relative)
    spec = check.mapping(spec, "")
    if spec is None:
        return None
    template = spec.get("template")
    if template not in TEMPLATES:
        check.error("value_invalid", field="template", value=str(template), allowed=", ".join(TEMPLATES))
        return None
    required, optional = _TEMPLATE_KEYS[template]
    check.keys(spec, "", required=_COMMON_REQUIRED + required, optional=_COMMON_OPTIONAL + optional)
    for key in ("title", *_COMMON_OPTIONAL):
        if key in spec:
            check.localized(spec, key, "", languages)
    if template == "compare":
        rows = check.items(spec["rows"], "rows", maximum=6) if "rows" in spec else []
        for index, row in enumerate(rows, start=1):
            check.localized_value(row, f"rows[{index}]", languages)
        columns = check.items(spec["columns"], "columns", minimum=2, maximum=4) if "columns" in spec else []
        for index, column in enumerate(columns, start=1):
            where = f"columns[{index}]"
            column = _visual(check, column, where, languages, optional=("values", "highlight", "badge"),
                             localized=("badge",))
            if column is None:
                continue
            if "values" not in column:
                check.error("field_missing", field=_where(where, "values"))
                continue
            values = check.items(column["values"], _where(where, "values"), minimum=len(rows), maximum=len(rows))
            for v_index, value in enumerate(values, start=1):
                check.localized_value(value, f"{where}.values[{v_index}]", languages)
            check.flag(column, "highlight", where)
        check.flag(spec, "versus", "")
        if spec.get("versus") is True and len(columns) != 2:
            check.error("value_invalid", field="versus", value="true", allowed="true (2 columns), false")
        if "emphasis_row" in spec:
            row = spec["emphasis_row"]
            if isinstance(row, bool) or not isinstance(row, int) or not 1 <= row <= max(1, len(rows)):
                check.error("value_invalid", field="emphasis_row", value=str(row), allowed=f"1–{len(rows)}")
    elif template == "equation":
        terms = check.items(spec["terms"], "terms", minimum=2, maximum=4) if "terms" in spec else []
        for index, term in enumerate(terms, start=1):
            _visual(check, term, f"terms[{index}]", languages, optional=("caption",), localized=("caption",))
        if "result" in spec:
            _visual(check, spec["result"], "result", languages, optional=("caption",), localized=("caption",))
    else:
        if template == "cycle":
            steps = check.items(spec["steps"], "steps", minimum=3, maximum=6) if "steps" in spec else []
            if "center" in spec:
                _visual(check, spec["center"], "center", languages, color=False)
        else:
            steps = check.items(spec["steps"], "steps", minimum=2, maximum=6) if "steps" in spec else []
            if "direction" in spec and spec["direction"] not in ("horizontal", "vertical"):
                check.error("value_invalid", field="direction", value=str(spec["direction"]),
                            allowed="horizontal, vertical")
        for index, step in enumerate(steps, start=1):
            _visual(check, step, f"steps[{index}]", languages, optional=("caption", "arrow"),
                    localized=("caption", "arrow"))
    return spec if check.clean else None


def _diagrams(report: Report, root: Path, languages: tuple[str, ...]) -> dict[str, dict]:
    folder = root / DIAGRAMS_DIR
    specs: dict[str, dict] = {}
    if not folder.is_dir():
        return specs
    start = len(report.errors)
    for entry in sorted(folder.iterdir()):
        relative = f"{DIAGRAMS_DIR}/{entry.name}"
        if entry.name.startswith("."):
            continue
        if not entry.is_file() or entry.suffix != ".yaml":
            report.error("entry_unexpected", path=relative, allowed="<diagram-id>.yaml")
            continue
        if not SLUG.match(entry.stem) or entry.stem == ROADMAP:
            report.error("id_invalid", path=relative, id=entry.stem)
            continue
        try:
            raw = _load(report, root, relative)
        except _Invalid:
            continue
        spec = _diagram(report, relative, raw, languages)
        if spec is not None:
            specs[entry.stem] = spec
    if len(report.errors) != start:
        raise _Invalid
    return specs


# ---------------------------------------------------------------------------
# course/, course/<lang>/ and course/<lang>/lessons/
# ---------------------------------------------------------------------------


def _tree(report: Report, root: Path, course: Course) -> None:
    """Report anything that has no place in the course folders."""
    allowed_root = ("README.md", "data", *course.languages)
    for entry in sorted((root / COURSE_DIR).iterdir()):
        if not entry.name.startswith(".") and entry.name not in allowed_root:
            report.error("entry_unexpected", path=f"{COURSE_DIR}/{entry.name}", allowed=", ".join(allowed_root))
    for entry in sorted((root / DATA_DIR).iterdir()):
        if not entry.name.startswith(".") and entry.name not in DATA_ENTRIES:
            report.error("entry_unexpected", path=f"{DATA_DIR}/{entry.name}", allowed=", ".join(DATA_ENTRIES))
    for language in course.languages:
        folder = root / language_dir(language)
        if not folder.is_dir():
            continue  # its generated README is then reported as stale
        for entry in sorted(folder.iterdir()):
            if not entry.name.startswith(".") and entry.name not in LANGUAGE_ENTRIES:
                report.error("entry_unexpected", path=f"{language_dir(language)}/{entry.name}",
                             allowed=", ".join(LANGUAGE_ENTRIES))


def _lessons(report: Report, root: Path, course: Course) -> None:
    known = {lesson.id: lesson for lesson in course.lessons}
    for language in course.languages:
        folder = root / lessons_dir(language)
        if not folder.is_dir():
            continue
        for entry in sorted(folder.iterdir()):
            relative = f"{lessons_dir(language)}/{entry.name}"
            if entry.name.startswith("."):
                continue
            if not entry.is_file() or entry.suffix != ".md":
                report.error("entry_unexpected", path=relative, allowed="<lesson-id>.md")
            elif entry.stem not in known:
                report.error("lesson_file_unknown", path=relative)
            else:
                report.started.add(entry.stem)
    for lesson in course.lessons:
        if lesson.id not in report.started:
            continue
        docs: dict[str, LessonDoc] = {}
        for language in course.languages:
            relative = lesson_path(lesson.id, language)
            if not (root / relative).is_file():
                report.error("lesson_file_missing", path=relative)
                continue
            doc = _lesson_file(report, root, course, lesson, language, relative)
            if doc is not None:
                docs[language] = doc
                report.docs[(lesson.id, language)] = doc
        _parity(report, course, lesson, docs)


def _references(check: _Checker, root: Path, course: Course, relative: str, doc: LessonDoc) -> None:
    """Every image and relative link in the lesson points at something that exists."""
    folder = posixpath.dirname(relative)
    for block in doc.sections:
        for alt, target in block.images:
            if not alt.strip():
                check.error("image_alt_missing", target=target)
            if target.startswith(EXTERNAL):
                continue
            resolved = posixpath.normpath(posixpath.join(folder, target.split("#", 1)[0]))
            diagrams = posixpath.join(posixpath.dirname(folder), "diagrams")
            if posixpath.dirname(resolved) == diagrams and resolved.endswith(".svg"):
                diagram_id = posixpath.basename(resolved)[: -len(".svg")]
                if diagram_id != ROADMAP and diagram_id not in course.diagrams:
                    check.error("diagram_unknown", target=target)
                continue  # generated: its presence is the build check's business
            if not (root / resolved).exists():
                check.error("link_broken", target=target)
        for target in block.links:
            if target.startswith(EXTERNAL):
                continue
            resolved = posixpath.normpath(posixpath.join(folder, target.split("#", 1)[0]))
            if not (root / resolved).exists():
                check.error("link_broken", target=target)


def _lesson_file(
    report: Report, root: Path, course: Course, lesson: Lesson, language: str, relative: str
) -> LessonDoc | None:
    check = _Checker(report, relative)
    try:
        doc = parse_lesson(yamlio.read_text(root / relative))
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

    expected_bar = lesson_language_bar(course, lesson.id, language)
    if doc.language_bar != expected_bar:
        check.error("language_bar", expected=expected_bar)
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
    _references(check, root, course, relative, doc)

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


def _parity(report: Report, course: Course, lesson: Lesson, docs: dict[str, LessonDoc]) -> None:
    """Every language that has left `todo` has the same sections and diagrams, in the same order."""
    started = [(language, docs[language]) for language in course.languages
               if language in docs and docs[language].status not in (None, "todo")]
    if len(started) < 2:
        return
    reference_language, reference = next(
        ((language, doc) for language, doc in started if language == course.source_language), started[0]
    )
    for language, doc in started:
        if language == reference_language:
            continue
        path = lesson_path(lesson.id, language)
        if doc.keys != reference.keys:
            report.error(
                "sections_differ", path=path, lang=language, other=reference_language,
                actual=", ".join(doc.keys), expected=", ".join(reference.keys),
            )
        elif doc.diagram_layout != reference.diagram_layout:
            report.error(
                "diagrams_differ", path=path, lang=language, other=reference_language,
                actual=_shown(doc.diagram_layout), expected=_shown(reference.diagram_layout),
            )


def _shown(layout: list[tuple[str, tuple[str, ...]]]) -> str:
    """A diagram layout as one line: `concept: ../diagrams/a.svg + ../diagrams/b.svg, analogy: …`."""
    return ", ".join(f"{key}: {' + '.join(targets)}" for key, targets in layout if targets) or "–"


# ---------------------------------------------------------------------------
# Generated files
# ---------------------------------------------------------------------------


def stale_files(root: Path, course: Course, started: set[str]) -> tuple[dict[str, str], list[str], list[str]]:
    """(expected files, paths whose content differs or is missing, orphan paths to delete)."""
    expected = generated_files(course, started)
    stale = []
    for path, content in expected.items():
        try:
            actual = yamlio.read_text(root / path) if (root / path).is_file() else None
        except UnicodeDecodeError:
            actual = None
        if actual != content:
            stale.append(path)
    orphans = []
    for language in course.languages:
        folder = root / language_dir(language) / "diagrams"
        if folder.is_dir():
            for entry in sorted(folder.iterdir()):
                path = f"{language_dir(language)}/diagrams/{entry.name}"
                if not entry.name.startswith(".") and path not in expected:
                    orphans.append(path)
    return expected, stale, orphans


def _generated(report: Report, root: Path, course: Course) -> None:
    _, stale, orphans = stale_files(root, course, report.started)
    for path in stale + orphans:
        report.error("build_stale", path=path)


# ---------------------------------------------------------------------------


def validate(root: Path, *, check_generated: bool = True) -> Report:
    """Check the whole content store; `report.course` is set only when course/data/ is valid."""
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
            ("diagrams", lambda: _diagrams(report, root, languages)),
        ):
            try:
                results[name] = loader()
            except _Invalid:
                pass
        if "glossary" not in results:
            raise _Invalid
        version, modules = _curriculum(report, root, languages, results["glossary"])
        if "sections" not in results or "diagrams" not in results:
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
        audience=meta["audience"],
        hashtags=meta["hashtags"],
        curriculum_version=version,
        modules=modules,
        glossary=results["glossary"],
        sections=results["sections"],
        diagrams=results["diagrams"],
    )
    _tree(report, root, report.course)
    _lessons(report, root, report.course)
    if check_generated:
        _generated(report, root, report.course)
    return report
