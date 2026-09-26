"""A small but complete content store in a temporary directory, for the course tests.

The real course/sections.yaml is copied in, so the tests exercise the section
rules the course actually uses; everything else is a two-lesson miniature that
each test then breaks in exactly one way.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from src.core.model import ROOT
from src.core.outline import render_outline
from src.core.validate import validate
from src.utils.catalogs import translators_for

LANGUAGES = ("vi", "en", "ja")

COURSE = {
    "id": "mini-course",
    "version": "0.0.1",
    "languages": list(LANGUAGES),
    "source_language": "vi",
    "title": {"vi": "Khóa nhỏ", "en": "Mini course", "ja": "ミニ講座"},
    "tagline": {"vi": "Thử nghiệm", "en": "A test", "ja": "テスト"},
    "audience": {"vi": "Người học", "en": "Learners", "ja": "学習者"},
    "hashtags": {"vi": ["#Thu"], "en": ["#Test"], "ja": ["#テスト"]},
}

GLOSSARY = {
    "terms": [
        {
            "id": "agent",
            "vi": {"term": "Tác tử", "definition": "Một hệ thống AI tự hành động."},
            "en": {"term": "Agent", "definition": "An AI system that acts on its own."},
            "ja": {"term": "エージェント", "definition": "自分で行動するAIシステム。"},
        },
        {
            "id": "model",
            "vi": {"term": "Mô hình", "definition": "Kết quả của huấn luyện."},
            "en": {"term": "Model", "definition": "The result of training."},
            "ja": {"term": "学習モデル", "reading": "がくしゅうモデル", "definition": "学習の結果。"},
        },
    ]
}

TITLES = {
    "alpha": {"vi": "Bài alpha", "en": "Lesson alpha", "ja": "レッスン・アルファ"},
    "beta": {"vi": "Bài beta", "en": "Lesson beta", "ja": "レッスン・ベータ"},
}

CURRICULUM = {
    "version": "0.0.1",
    "modules": [
        {
            "id": "start",
            "title": {"vi": "Bắt đầu", "en": "Start", "ja": "はじめに"},
            "goal": {"vi": "Học thử.", "en": "Try it.", "ja": "試してみる。"},
            "units": [
                {
                    "id": "basics",
                    "title": {"vi": "Cơ bản", "en": "Basics", "ja": "基本"},
                    "lessons": [
                        {"id": "alpha", "title": TITLES["alpha"], "type": "concept", "minutes": 10,
                         "terms": ["agent", "model"]},
                        {"id": "beta", "title": TITLES["beta"], "type": "hands-on", "minutes": 15},
                    ],
                }
            ],
        }
    ],
}

# The sections a finished concept lesson has, in sections.yaml order.
ALPHA_SECTIONS = ("objective", "hook", "concept", "analogy", "example", "takeaways", "quiz")


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def lesson_text(
    lesson: str,
    language: str,
    *,
    status: str = "review",
    sections: tuple[str, ...] = ALPHA_SECTIONS,
    title: str | None = None,
    summary: str = "Tóm tắt.",
    hook: str = "Hook!",
    question: str = "Question?",
    bodies: dict[str, str] | None = None,
) -> str:
    bodies = bodies or {}
    front = {
        "lesson": lesson,
        "lang": language,
        "status": status,
        "summary": summary,
        "social": {"hook": hook, "question": question},
    }
    lines = ["---", yaml.safe_dump(front, allow_unicode=True, sort_keys=False).strip(), "---", ""]
    lines += [f"# {TITLES[lesson][language] if title is None else title}", ""]
    for key in sections:
        body = bodies.get(key, f"- **Point** for {key} in {language}, see [docs](https://example.com).")
        lines += [f"<!-- section: {key} -->", f"## Heading {key}", "", body, ""]
    return "\n".join(lines)


def write_lesson(root: Path, lesson: str, language: str, **options) -> Path:
    path = root / "course" / "lessons" / lesson / f"{language}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(lesson_text(lesson, language, **options), encoding="utf-8")
    return path


def write_outline(root: Path) -> None:
    report = validate(root, check_outline=False)
    assert report.course is not None, report.errors
    (root / "course" / "OUTLINE.md").write_text(
        render_outline(report.course, translators_for(report.course.languages)), encoding="utf-8"
    )


def make_store(root: Path) -> Path:
    """A valid store: lesson `alpha` written in every language, `beta` not started."""
    course = root / "course"
    course.mkdir(parents=True, exist_ok=True)
    dump(course / "course.yaml", COURSE)
    dump(course / "glossary.yaml", GLOSSARY)
    dump(course / "curriculum.yaml", CURRICULUM)
    shutil.copy(ROOT / "course" / "sections.yaml", course / "sections.yaml")
    for language in LANGUAGES:
        write_lesson(root, "alpha", language)
    write_outline(root)
    return root
