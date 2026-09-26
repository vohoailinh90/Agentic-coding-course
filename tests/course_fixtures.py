"""A small but complete content store in a temporary directory, for the course tests.

The real course/data/sections.yaml is copied in, so the tests exercise the
section rules the course actually uses; everything else is a two-lesson
miniature with one infographic, which each test then breaks in exactly one way.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from src.core.model import ROOT
from src.core.validate import stale_files, validate

LANGUAGES = ("vi", "en", "ja")
NAMES = {"vi": "Tiếng Việt", "en": "English", "ja": "日本語"}

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
            "icon": "🚀",
            "title": {"vi": "Bắt đầu", "en": "Start", "ja": "はじめに"},
            "goal": {"vi": "Học thử.", "en": "Try it.", "ja": "試してみる。"},
            "units": [
                {
                    "id": "basics",
                    "track": "core",
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
    "minimum_path": ["alpha"],
    "retired": [{"id": "old-alpha", "into": "alpha"}],
}

DIAGRAM_ID = "compare-demo"
DIAGRAM = {
    "template": "compare",
    "title": {"vi": "Chatbot và agent", "en": "Chatbot and agent", "ja": "チャットボットとエージェント"},
    "versus": True,
    "rows": [{"vi": "Nó làm gì", "en": "What it does", "ja": "すること"}],
    "emphasis_row": 1,
    "columns": [
        {"icon": "💬", "color": "blue", "name": {"vi": "Chatbot", "en": "Chatbot", "ja": "チャットボット"},
         "values": [{"vi": "Trả lời", "en": "Answers", "ja": "答える"}]},
        {"icon": "🤖", "color": "green", "highlight": True,
         "name": {"vi": "Agent", "en": "Agent", "ja": "エージェント"},
         "values": [{"vi": "Hành động", "en": "Acts", "ja": "行動する"}]},
    ],
    "takeaway": {"vi": "Agent hành động.", "en": "An agent acts.", "ja": "エージェントは行動する。"},
}

# The sections a finished concept lesson has, in sections.yaml order.
# The recap: a lesson summed up in one infographic of its own (sections.yaml `recap`).
RECAP_ID = "alpha-recap"
RECAP = {
    "template": "summary",
    "title": {"vi": "Tóm tắt", "en": "Recap", "ja": "まとめ"},
    "points": [
        {"icon": "💬", "color": "blue", "name": {"vi": "Chatbot trả lời", "en": "A chatbot answers", "ja": "チャットボットは答える"}},
        {"icon": "🤖", "color": "green", "name": {"vi": "Agent hành động", "en": "An agent acts", "ja": "エージェントは行動する"},
         "caption": {"vi": "Bạn kiểm tra kết quả", "en": "You check the result", "ja": "結果はあなたが確かめる"}},
        {"icon": "✅", "color": "amber", "name": {"vi": "Bạn quyết định", "en": "You decide", "ja": "決めるのはあなた"}},
    ],
}
ALPHA_SECTIONS = ("objective", "hook", "concept", "analogy", "example", "recap", "takeaways", "quiz")


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def language_bar(lesson: str, language: str) -> str:
    """Written out independently of src/core/build.py, so a format change there is noticed here."""
    parts = [f"**{NAMES[other]}**" if other == language else f"[{NAMES[other]}](../../{other}/lessons/{lesson}.md)"
             for other in LANGUAGES]
    return "🌐 " + " · ".join(parts)


def lesson_text(
    lesson: str,
    language: str,
    *,
    status: str = "review",
    sections: tuple[str, ...] = ALPHA_SECTIONS,
    title: str | None = None,
    bar: str | None = None,
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
    lines += [language_bar(lesson, language) if bar is None else bar, ""]
    lines += [f"# {TITLES[lesson][language] if title is None else title}", ""]
    for key in sections:
        default = f"- **Point** for {key} in {language}, see [docs](https://example.com)."
        if key == "concept":
            default += f"\n\n![{DIAGRAM['title'][language]}](../diagrams/{DIAGRAM_ID}.svg)"
        if key == "recap":
            default = f"![{RECAP['title'][language]}](../diagrams/{RECAP_ID}.svg)"
        body = bodies.get(key, default)
        lines += [f"<!-- section: {key} -->", f"## Heading {key}", "", body, ""]
    return "\n".join(lines)


def write_lesson(root: Path, lesson: str, language: str, **options) -> Path:
    path = root / "course" / language / "lessons" / f"{lesson}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(lesson_text(lesson, language, **options), encoding="utf-8")
    return path


def write_generated(root: Path) -> None:
    """What `python -m src.main build` does, without the console output."""
    report = validate(root, check_generated=False)
    assert report.course is not None, report.errors
    expected, stale, orphans = stale_files(root, report.course, report.started)
    for path in stale:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(expected[path], encoding="utf-8")
    for path in orphans:
        (root / path).unlink()


def make_store(root: Path) -> Path:
    """A valid store: lesson `alpha` written in every language, `beta` not started."""
    data = root / "course" / "data"
    dump(data / "course.yaml", COURSE)
    dump(data / "glossary.yaml", GLOSSARY)
    dump(data / "curriculum.yaml", CURRICULUM)
    dump(data / "diagrams" / f"{DIAGRAM_ID}.yaml", DIAGRAM)
    dump(data / "diagrams" / f"{RECAP_ID}.yaml", RECAP)
    shutil.copy(ROOT / "course" / "data" / "sections.yaml", data / "sections.yaml")
    for language in LANGUAGES:
        write_lesson(root, "alpha", language)
    write_generated(root)
    return root
