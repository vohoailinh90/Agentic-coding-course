"""scripts/sd101_check.py: the Vietnamese System Design store rules, on fixtures and on the real store."""

from __future__ import annotations

import contextlib
import copy
import datetime
import io
import json
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import yaml

from scripts import sd101_check as check

COMMIT = "b28380a4710c5ec9638ec037d4168e288f334cba"
SOURCE_PATH = "data/guides/one.md"
PIN = {"source_repository": "ByteByteGoHq/system-design-101", "source_commit_sha": COMMIT}
SNAPSHOT = f"https://github.com/ByteByteGoHq/system-design-101/blob/{COMMIT}/{SOURCE_PATH}"


def source_entry(lesson_id: str = "sd-01-001", title: str | None = "Bài một", snapshot: object = SNAPSHOT,
                 **changes: object) -> dict:
    """A complete source-map entry, as the real map records one."""
    entry = {"id": lesson_id, "title_vi": title, "title_source": "One", "source_url": "https://bytebytego.com/guides/one",
             "source_path": SOURCE_PATH, "source_body_reviewed": False, "source_blob_sha": "a" * 40,
             "source_snapshot_url": snapshot}
    entry.update(changes)
    return entry
BODY = f"# Bài một\n\nNội dung.\n\n## Liên hệ nguồn\n\n[bài nguồn]({SNAPSHOT}).\n"
META = {
    "id": "sd-01-001",
    "title_vi": "Bài một",
    "content_status": "drafted",
    "verification": {"source_read": "done", "claims": "pending", "technical": "pending", "mobile": "pending"},
    "learner_test": "pending",
    "image_evidence": [],
}
README = "# Kho\n\n| ID | Bài |\n|---|---|\n| [sd-01-001](lessons/sd-01-001/lesson.md) | Bài một |\n"


class StoreCase(unittest.TestCase):
    """A one-lesson store in a temp directory; each test breaks one thing."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.store = self.root / "store"
        self.source_map = self.root / "source-map.json"
        self.write_source_map({"sd-01-001": ("Bài một", SNAPSHOT)})
        self.write_lesson("sd-01-001")
        self.write_readme(README)

    def write_source_map(self, lessons: dict[str, tuple[str, str]]) -> None:
        # the fixture lessons share one source file, so when there are several they name each other
        data = {**PIN, "categories": [{"id": "sd-01", "lessons": [
            source_entry(lesson_id, title, snapshot,
                         **({"same_source_as": [other for other in lessons if other != lesson_id]}
                            if len(lessons) > 1 else {}))
            for lesson_id, (title, snapshot) in lessons.items()]}]}
        self.source_map.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def write_lesson(self, lesson_id: str, *, meta: dict | None = None, body: str | None = None) -> Path:
        lesson_dir = self.store / "lessons" / lesson_id
        lesson_dir.mkdir(parents=True, exist_ok=True)
        data = copy.deepcopy(META if meta is None else meta)
        (lesson_dir / "lesson.yaml").write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        (lesson_dir / "lesson.md").write_text(BODY if body is None else body, encoding="utf-8")
        return lesson_dir

    def write_readme(self, text: str) -> None:
        self.store.mkdir(parents=True, exist_ok=True)
        (self.store / "README.md").write_text(text, encoding="utf-8")

    def problems(self) -> list[str]:
        return [str(problem) for problem in check.check_store(self.store, self.source_map)]

    def meta(self, **changes: object) -> dict:
        data = copy.deepcopy(META)
        data.update(changes)
        return data

    def assertProblem(self, fragment: str) -> None:
        found = self.problems()
        self.assertTrue(any(fragment in line for line in found), f"{fragment!r} not in {found}")


class RealStoreTests(unittest.TestCase):
    def test_the_real_store_passes_every_rule(self) -> None:
        problems = check.check_store(check.DEFAULT_STORE, check.DEFAULT_SOURCE_MAP, pin_roster=True)
        self.assertEqual([], [str(problem) for problem in problems])


class SourceMapPinTests(unittest.TestCase):
    """The real source map, altered one way at a time: the roster and the pinned URLs are guarded."""

    def check(self, change, *, pin_roster: bool = True) -> list[str]:
        data = json.loads(check.DEFAULT_SOURCE_MAP.read_text(encoding="utf-8"))
        change(data)
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp) / "source-map.json"
            altered.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            problems = check.check_store(check.DEFAULT_STORE, altered, pin_roster=pin_roster)
        return [str(problem) for problem in problems if str(problem).startswith("source map")]

    def test_the_unaltered_source_map_has_no_problem(self) -> None:
        self.assertEqual([], self.check(lambda data: None))

    def test_removing_an_unwritten_entry_is_reported(self) -> None:
        def remove(data):
            del data["categories"][0]["lessons"][3]  # sd-01-004
        found = self.check(remove)
        self.assertTrue(any("first difference: ('sd-01', 49) instead of ('sd-01', 50)" in line for line in found), found)
        self.assertTrue(any("sd-01-005 should be sd-01-004" in line for line in found), found)

    def test_the_other_ways_to_change_the_roster_are_reported(self) -> None:
        def drop_last(data):
            data["categories"][-1]["lessons"].pop()

        def drop_group(data):
            data["categories"].pop(2)

        def add_entry(data):
            extra = dict(data["categories"][0]["lessons"][-1], id="sd-01-051")
            data["categories"][0]["lessons"].append(extra)

        def swap(data):
            lessons = data["categories"][1]["lessons"]
            lessons[0], lessons[1] = lessons[1], lessons[0]

        def renumber(data):
            data["categories"][4]["lessons"][0]["id"] = "sd-05-009"

        def empty(data):
            data["categories"] = []

        def rename_a_group_and_its_ids(data):
            group = data["categories"][-1]
            group["id"] = "sd-99"
            for number, lesson in enumerate(group["lessons"], 1):
                lesson["id"] = f"sd-99-{number:03d}"

        def rename_a_group_only(data):
            data["categories"][5]["id"] = "sd-66"

        def swap_two_groups(data):
            data["categories"][2], data["categories"][3] = data["categories"][3], data["categories"][2]

        def renumber_a_group_as_another(data):
            for number, lesson in enumerate(data["categories"][0]["lessons"], 1):
                lesson["id"] = f"sd-02-{number:03d}"
            data["categories"][0]["id"] = "sd-02"

        for name, change in {"the last entry removed": drop_last, "a group removed": drop_group,
                             "an entry added": add_entry, "two entries swapped": swap, "an id renumbered": renumber,
                             "no groups": empty, "a group and its ids renamed": rename_a_group_and_its_ids,
                             "a group renamed, its ids kept": rename_a_group_only, "two groups swapped": swap_two_groups,
                             "a group renumbered as another": renumber_a_group_as_another}.items():
            with self.subTest(change=name):
                self.assertTrue(self.check(change), name)

    def test_the_roster_is_pinned_only_for_the_real_source_map(self) -> None:
        def remove(data):
            del data["categories"][0]["lessons"][3]
        self.assertEqual([], self.check(remove, pin_roster=False))

    def test_the_command_line_pins_the_default_source_map_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "source-map.json"
            copy.write_bytes(check.DEFAULT_SOURCE_MAP.read_bytes())
            with mock.patch.object(check, "EXPECTED_GROUPS", (("sd-01", 1),)), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(1, check.main([]))
                self.assertEqual(1, check.main(["--source-map", str(check.DEFAULT_SOURCE_MAP.parent / ".." /
                                                                   check.DEFAULT_SOURCE_MAP.parent.name /
                                                                   check.DEFAULT_SOURCE_MAP.name)]))
                self.assertEqual(0, check.main(["--source-map", str(copy)]))

    def test_a_moving_snapshot_url_is_reported_even_if_the_lesson_links_it(self) -> None:
        def moving(data):
            entry = data["categories"][0]["lessons"][0]
            entry["source_snapshot_url"] = f"https://github.com/ByteByteGoHq/system-design-101/blob/main/{entry['source_path']}"
        found = self.check(moving)
        self.assertTrue(any("sd-01-001: source_snapshot_url is not" in line for line in found), found)

    def test_every_other_wrong_snapshot_url_is_reported(self) -> None:
        def entry_of(data):
            return data["categories"][0]["lessons"][1]

        def set_url(url):
            return lambda data: entry_of(data).update(source_snapshot_url=url)

        path, commit = "data/guides/x.md", COMMIT
        for name, change in {
            "another repository": set_url(f"https://github.com/someone/else/blob/{commit}/{path}"),
            "another commit": set_url(f"https://github.com/ByteByteGoHq/system-design-101/blob/{'0' * 40}/{path}"),
            "a short commit": set_url(f"https://github.com/ByteByteGoHq/system-design-101/blob/b28380a/{path}"),
            "another path": set_url(f"https://github.com/ByteByteGoHq/system-design-101/blob/{commit}/data/other.md"),
            "a tree URL": set_url(f"https://github.com/ByteByteGoHq/system-design-101/tree/{commit}/{path}"),
            "a raw URL": set_url(f"https://raw.githubusercontent.com/ByteByteGoHq/system-design-101/{commit}/{path}"),
            "a trailing fragment": lambda data: entry_of(data).update(
                source_snapshot_url=entry_of(data)["source_snapshot_url"] + "#L1"),
            "no URL": lambda data: entry_of(data).pop("source_snapshot_url"),
            "a null URL": set_url(None),
            "a null source path with a matching tail": lambda data: entry_of(data).update(
                source_path=None, source_snapshot_url=f"https://github.com/ByteByteGoHq/system-design-101/blob/{commit}/None"),
            "an empty source path": lambda data: entry_of(data).update(
                source_path="", source_snapshot_url=f"https://github.com/ByteByteGoHq/system-design-101/blob/{commit}/"),
        }.items():
            with self.subTest(change=name):
                self.assertTrue(any("sd-01-002: source_snapshot_url is not" in line
                                    for line in self.check(change, pin_roster=False)), name)

    def test_the_map_needs_its_own_pinned_commit_and_repository(self) -> None:
        for name, change in {
            "no commit": lambda data: data.pop("source_commit_sha"),
            "a short commit": lambda data: data.update(source_commit_sha="b28380a"),
            "an upper-case commit": lambda data: data.update(source_commit_sha=data["source_commit_sha"].upper()),
            "a branch name": lambda data: data.update(source_commit_sha="main"),
            "no repository": lambda data: data.pop("source_repository"),
            "a repository without an owner": lambda data: data.update(source_repository="system-design-101"),
            "a null commit": lambda data: data.update(source_commit_sha=None),
        }.items():
            with self.subTest(change=name):
                self.assertTrue(any("needs a source_repository" in line
                                    for line in self.check(change, pin_roster=False)), name)

    def entry(self, data, number=1):
        return data["categories"][0]["lessons"][number]  # sd-01-002 by default

    def test_a_missing_entry_field_is_reported(self) -> None:
        for key in sorted(check.SOURCE_ENTRY_KEYS - {"id"}):
            with self.subTest(key=key):
                found = self.check(lambda data: self.entry(data).pop(key), pin_roster=False)
                self.assertTrue(any(f"sd-01-002 is missing {key}" in line or f"sd-01-002: source_snapshot_url" in line
                                    for line in found), found)

    def test_an_entry_field_of_the_wrong_kind_is_reported(self) -> None:
        cases = {
            "source_body_reviewed": ["yes", 1, 0, None, "true", []],
            "source_blob_sha": ["a" * 39, "A" * 40, "g" * 40, None, 5, "", ["a" * 40]],
            "title_source": ["", "  ", None, 5, ["x"]],
            "source_path": ["", "  ", None, 5],
            "source_url": ["", "not a url", "ftp://bytebytego.com/x", None, 5, "https://"],
            "title_vi": ["", "  ", 5, ["x"], {"a": 1}, True],
        }
        for key, values in cases.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    found = self.check(lambda data: self.entry(data).update({key: value}), pin_roster=False)
                    self.assertTrue(any(line.startswith("source map: sd-01-002 ") or "sd-01-002:" in line
                                        for line in found), found)

    def test_a_null_title_vi_is_allowed_and_a_string_is_too(self) -> None:
        self.assertEqual([], self.check(lambda data: self.entry(data).update(title_vi=None), pin_roster=False))
        self.assertEqual([], self.check(lambda data: self.entry(data).update(title_vi="Tiêu đề"), pin_roster=False))
        self.assertEqual([], self.check(lambda data: self.entry(data).update(source_body_reviewed=True),
                                        pin_roster=False))

    def test_progress_fields_do_not_belong_in_the_source_map(self) -> None:
        for key in ("status", "content_status", "verification", "learner_test"):
            with self.subTest(key=key):
                found = self.check(lambda data: self.entry(data).update({key: "drafted"}), pin_roster=False)
                self.assertTrue(any(f"sd-01-002 has unknown keys {key}" in line for line in found), found)

    def test_same_source_entries_must_name_each_other(self) -> None:
        def entry_of(data, lesson_id):
            return next(lesson for category in data["categories"] for lesson in category["lessons"]
                        if lesson["id"] == lesson_id)

        cases = {
            "one side dropped": (lambda data: entry_of(data, "sd-10-023").pop("same_source_as"),
                                 "sd-01-045: same_source_as names sd-10-023, which does not name sd-01-045 back"),
            "a missing partner": (lambda data: entry_of(data, "sd-01-045").update(same_source_as=["sd-99-999"]),
                                  "sd-01-045: same_source_as names sd-99-999, which is not another entry"),
            "itself": (lambda data: entry_of(data, "sd-01-045").update(same_source_as=["sd-01-045"]),
                       "sd-01-045: same_source_as names sd-01-045, which is not another entry"),
            "another source path": (lambda data: entry_of(data, "sd-10-023").update(
                source_path="data/guides/other.md",
                source_snapshot_url=f"https://github.com/ByteByteGoHq/system-design-101/blob/{data['source_commit_sha']}/data/guides/other.md"),
                                    "sd-01-045: same_source_as names sd-10-023, which has another source_path"),
            "not a list": (lambda data: entry_of(data, "sd-01-045").update(same_source_as="sd-10-023"),
                           "sd-01-045: same_source_as must be a non-empty list of ids"),
            "an empty list": (lambda data: entry_of(data, "sd-01-045").update(same_source_as=[]),
                              "sd-01-045: same_source_as must be a non-empty list of ids"),
            "a list of numbers": (lambda data: entry_of(data, "sd-01-045").update(same_source_as=[5]),
                                  "sd-01-045: same_source_as must be a non-empty list of ids"),
        }
        for name, (change, expected) in cases.items():
            with self.subTest(change=name):
                found = self.check(change, pin_roster=False)
                self.assertTrue(any(expected in line for line in found), found)

    def test_two_entries_sharing_a_source_file_must_say_so(self) -> None:
        def share(data):
            first, second = data["categories"][0]["lessons"][4], data["categories"][0]["lessons"][5]
            second["source_path"] = first["source_path"]
            second["source_snapshot_url"] = first["source_snapshot_url"]
        found = self.check(share, pin_roster=False)
        self.assertTrue(any("sd-01-005: shares its source_path with sd-01-006 but does not list them" in line
                            for line in found), found)
        self.assertTrue(any("sd-01-006: shares its source_path with sd-01-005 but does not list them" in line
                            for line in found), found)

    ODD = [None, True, 0, 1.5, "", " ", "sd-01-001", "x" * 300, [], [None], [{}], [[1]], [5], ["sd-01-001"],
           {}, {"a": 1}, [{"a": 1}]]

    def load(self, change, *, pin_roster: bool = True) -> list[str]:
        """Only the source-map rules, on an altered copy of the real map (fast enough to sweep)."""
        data = json.loads(check.DEFAULT_SOURCE_MAP.read_text(encoding="utf-8"))
        change(data)
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp) / "source-map.json"
            altered.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return [str(problem) for problem in check.load_source_map(altered, pin_roster)[1]]

    def test_an_odd_value_in_any_source_map_field_is_reported_not_raised(self) -> None:
        keys = sorted(check.SOURCE_ENTRY_KEYS) + ["same_source_as", "unknown"]
        for key in keys:
            for value in self.ODD:
                for lesson in (1, 44):  # sd-01-002, and sd-01-045 which has a same-source partner
                    with self.subTest(key=key, value=value, lesson=lesson):
                        self.load(lambda data: self.entry(data, lesson).update({key: value}))

    def test_an_odd_value_for_a_map_level_field_or_a_group_is_reported_not_raised(self) -> None:
        for key in ("source_repository", "source_commit_sha", "categories", "schema_version"):
            for value in self.ODD:
                with self.subTest(key=key, value=value):
                    self.load(lambda data: data.update({key: value}))
        for key in ("id", "lessons", "extra"):
            for value in self.ODD:
                with self.subTest(group=key, value=value):
                    self.load(lambda data: data["categories"][0].update({key: value}))

    def test_an_odd_group_or_entry_is_reported_not_raised(self) -> None:
        for value in self.ODD:
            with self.subTest(value=value):
                self.load(lambda data: data["categories"].insert(3, value))
                self.load(lambda data: data["categories"][0]["lessons"].insert(5, value))
                self.load(lambda data: data["categories"][0]["lessons"].__setitem__(2, value))

    def test_an_odd_value_in_the_entry_of_a_written_lesson_is_reported_not_raised(self) -> None:
        for key in ("id", "title_vi", "source_path", "source_snapshot_url", "same_source_as"):
            for value in self.ODD:
                with self.subTest(key=key, value=value):
                    self.check(lambda data: self.entry(data, 0).update({key: value}))

    def check_text(self, text: str, *, pin_roster: bool = True) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp) / "source-map.json"
            altered.write_text(text, encoding="utf-8")
            return [str(problem) for problem in check.load_source_map(altered, pin_roster)[1]]

    def test_a_key_named_twice_in_the_source_map_is_reported(self) -> None:
        text = check.DEFAULT_SOURCE_MAP.read_text(encoding="utf-8")
        data = json.loads(text)
        commit, blob = data["source_commit_sha"], data["categories"][0]["lessons"][0]["source_blob_sha"]
        for name, (old, new) in {
            "the pinned commit": (f'"source_commit_sha": "{commit}"', f'"source_commit_sha": "{"0" * 40}", "source_commit_sha": "{commit}"'),
            "a blob id": (f'"source_blob_sha": "{blob}"', f'"source_blob_sha": "{blob}", "source_blob_sha": "{blob}"'),
            "the schema version": ('"schema_version": 1', '"schema_version": 1, "schema_version": 1'),
        }.items():
            with self.subTest(key=name):
                self.assertEqual(1, text.count(old))
                found = self.check_text(text.replace(old, new, 1))
                self.assertTrue(any("cannot be read: duplicate key" in line for line in found), found)

    def test_a_source_path_that_a_url_would_read_differently_is_reported(self) -> None:
        for path in ["../README.md", "/data/x.md", "data//x.md", "./data/x.md", "data/./x.md", "data/../x.md",
                     "data/x.md/", "data/a b.md", "data/a#b.md", "data/a?b.md", "data\\a.md", "data/a\tb.md", "..",
                     ".", "/", "./", "data/.", "data/..", "data/", "data/a\x7fb.md"]:
            def change(data, path=path):
                entry = self.entry(data)
                entry["source_path"] = path
                entry["source_snapshot_url"] = f"https://github.com/{data['source_repository']}/blob/{data['source_commit_sha']}/{path}"
            with self.subTest(path=path):
                found = self.check(change, pin_roster=False)
                self.assertTrue(any("sd-01-002 source_path must be a normalised path" in line for line in found), found)

    def test_the_real_source_paths_with_an_apostrophe_or_a_plus_are_fine(self) -> None:
        data = json.loads(check.DEFAULT_SOURCE_MAP.read_text(encoding="utf-8"))
        paths = [lesson["source_path"] for category in data["categories"] for lesson in category["lessons"]]
        self.assertTrue(any("'" in path for path in paths) and any("+" in path for path in paths))
        self.assertEqual([], self.check(lambda data: None))

    @staticmethod
    def move_to_another_repository(data) -> None:
        old = data["source_repository"]
        data["source_repository"] = "someone/else"
        for category in data["categories"]:
            for lesson in category["lessons"]:
                lesson["source_snapshot_url"] = lesson["source_snapshot_url"].replace(old, "someone/else")

    def test_the_top_level_records_of_the_real_map_are_pinned(self) -> None:
        cases = {
            "no schema version": lambda data: data.pop("schema_version"),
            "another schema version": lambda data: data.update(schema_version=2),
            "a boolean schema version": lambda data: data.update(schema_version=True),
            "another language": lambda data: data.update(language="en"),
            "another repository": self.move_to_another_repository,
            "no tree sha": lambda data: data.pop("source_tree_sha"),
            "a short tree sha": lambda data: data.update(source_tree_sha="7c914cc"),
            "a corrupted readme blob sha": lambda data: data.update(source_readme_blob_sha="z" * 40),
            "no readme blob sha": lambda data: data.pop("source_readme_blob_sha"),
            "no observation date": lambda data: data.pop("observed_on"),
            "an impossible observation date": lambda data: data.update(observed_on="2026-02-30"),
            "a free-text observation date": lambda data: data.update(observed_on="yesterday"),
            "a numeric observation date": lambda data: data.update(observed_on=20261012),
            "no note": lambda data: data.pop("note"),
            "an empty note": lambda data: data.update(note="  "),
            "an unknown top-level key": lambda data: data.update(status="drafted"),
        }
        for name, change in cases.items():
            with self.subTest(change=name):
                found = self.check(change)
                self.assertTrue(any(("top-level" in line or "must be" in line) for line in found), found)
                self.assertEqual([], self.check(change, pin_roster=False), "only the real map is held to its top-level records")

    def test_the_groups_of_the_real_map_are_pinned(self) -> None:
        cases = {
            "no title_vi": lambda data: data["categories"][2].pop("title_vi"),
            "an empty title_vi": lambda data: data["categories"][2].update(title_vi=""),
            "a null title_vi": lambda data: data["categories"][2].update(title_vi=None),
            "no title_source": lambda data: data["categories"][2].pop("title_source"),
            "an empty title_source": lambda data: data["categories"][2].update(title_source=""),
            "a blank title_source": lambda data: data["categories"][2].update(title_source="  "),
            "a numeric title_source": lambda data: data["categories"][2].update(title_source=5),
            "an unknown group key": lambda data: data["categories"][2].update(status="drafted"),
        }
        for name, change in cases.items():
            with self.subTest(change=name):
                found = self.check(change)
                self.assertTrue(any("group sd-03 needs exactly" in line for line in found), found)

    def test_re_pinning_every_entry_and_the_map_to_one_new_commit_is_allowed(self) -> None:
        new = "0123456789abcdef0123456789abcdef01234567"

        def repin(data):
            old = data["source_commit_sha"]
            data["source_commit_sha"] = new
            for category in data["categories"]:
                for lesson in category["lessons"]:
                    lesson["source_snapshot_url"] = lesson["source_snapshot_url"].replace(old, new)
        self.assertEqual([], self.check(repin))


class LessonYamlRuleTests(StoreCase):
    def test_a_valid_store_has_no_problems(self) -> None:
        self.assertEqual([], self.problems())

    def test_a_missing_file_is_reported(self) -> None:
        (self.store / "lessons" / "sd-01-001" / "lesson.yaml").unlink()
        self.assertProblem("lesson.yaml is missing")

    def test_a_lesson_yaml_that_does_not_parse_is_reported_not_raised(self) -> None:
        lesson_dir = self.store / "lessons" / "sd-01-001"
        evidence = ("image_evidence:\n- url: https://example.com/a.png\n  sha256: " + "a" * 64
                    + "\n  retrieved_on: {date}\n")
        base = yaml.safe_dump({key: value for key, value in META.items() if key != "image_evidence"},
                              allow_unicode=True)
        broken = {"invalid syntax": "id: [unclosed\n", "an impossible day": evidence.format(date="2026-02-30"),
                  "an impossible month": evidence.format(date="2026-13-01"),
                  "an impossible time": evidence.format(date="2026-10-12 25:00:00")}
        for name, tail in broken.items():
            with self.subTest(file=name):
                (lesson_dir / "lesson.yaml").write_text(base + tail if name != "invalid syntax" else tail,
                                                        encoding="utf-8")
                self.assertProblem("lesson.yaml does not parse")
        with self.subTest(file="not utf-8"):
            (lesson_dir / "lesson.yaml").write_bytes(b"id: \xff\xfe\n")
            self.assertProblem("lesson.yaml does not parse")

    def test_a_key_named_twice_in_lesson_yaml_is_reported(self) -> None:
        lesson_dir = self.store / "lessons" / "sd-01-001"
        base = yaml.safe_dump(META, allow_unicode=True, sort_keys=False)
        evidence = ("\nimage_evidence:\n- url: https://example.com/a.png\n  sha256: " + "a" * 64
                    + "\n  retrieved_on: '2026-10-12'\n  {extra}\n")
        twice = {
            "a top-level key with another value": base + "content_status: approved\n",
            "a top-level key with the same value": base + "content_status: drafted\n",
            "a verification key": base.replace("  claims: pending\n", "  claims: pending\n  claims: done\n"),
            "an evidence key": base.replace("image_evidence: []\n", "").rstrip("\n") + evidence.format(extra="url: https://b.example/"),
            "a quoted and an unquoted spelling": base + "'content_status': approved\n",
        }
        for name, text in twice.items():
            with self.subTest(file=name):
                (lesson_dir / "lesson.yaml").write_text(text, encoding="utf-8")
                self.assertProblem("duplicate key")

    def test_a_yaml_merge_key_and_repeated_values_are_not_duplicate_keys(self) -> None:
        lesson_dir = self.store / "lessons" / "sd-01-001"
        text = yaml.safe_dump(META, allow_unicode=True, sort_keys=False).replace(
            "verification:\n", "verification: &v\n", 1) + "extra: {<<: *v, claims: done}\n"
        (lesson_dir / "lesson.yaml").write_text(text, encoding="utf-8")
        self.assertFalse(any("does not parse" in line for line in self.problems()), self.problems())

    def test_text_that_is_not_utf8_is_reported_not_raised(self) -> None:
        (self.store / "lessons" / "sd-01-001" / "lesson.md").write_bytes(BODY.encode() + b"\xff\xfe")
        self.assertProblem("lesson.md is not valid UTF-8 text")
        self.write_lesson("sd-01-001")
        (self.store / "README.md").write_bytes(README.encode() + b"\xff\xfe")
        self.assertProblem("README.md: is not valid UTF-8 text")

    def test_unknown_or_missing_keys_are_reported(self) -> None:
        data = self.meta()
        data["status"] = "drafted"
        self.write_lesson("sd-01-001", meta=data)
        self.assertProblem("keys are")

    def test_an_id_that_is_not_the_directory_name_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(id="sd-01-002"))
        self.assertProblem("expected the directory name")

    def test_an_id_missing_from_the_source_map_is_reported(self) -> None:
        self.write_source_map({"sd-09-009": ("Khác", SNAPSHOT)})
        self.assertProblem("not in the source map")

    def test_a_title_that_differs_from_the_source_map_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(title_vi="Tiêu đề khác"))
        self.assertProblem("title_vi differs")

    def test_a_null_title_that_matches_a_null_source_map_title_is_reported(self) -> None:
        self.write_source_map({"sd-01-001": (None, SNAPSHOT)})
        self.write_lesson("sd-01-001", meta=self.meta(title_vi=None))
        self.assertProblem("title_vi must be a non-empty string")

    def test_an_empty_title_is_reported(self) -> None:
        self.write_source_map({"sd-01-001": ("", SNAPSHOT)})
        self.write_lesson("sd-01-001", meta=self.meta(title_vi="  "))
        self.assertProblem("title_vi must be a non-empty string")

    def test_a_status_outside_the_vocabulary_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(content_status="done"))
        self.assertProblem("content_status")

    def test_a_verification_state_outside_the_vocabulary_is_reported(self) -> None:
        data = self.meta()
        data["verification"]["claims"] = "ok"
        self.write_lesson("sd-01-001", meta=data)
        self.assertProblem("claims 'ok'")

    def test_approved_with_a_pending_check_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(content_status="approved"))
        self.assertProblem("approved needs every verification field")

    def test_approved_is_allowed_only_when_every_check_and_the_learner_test_are_done(self) -> None:
        data = self.meta(content_status="approved", learner_test="done")
        data["verification"] = {name: "done" for name in check.VERIFICATION_KEYS}
        self.write_lesson("sd-01-001", meta=data)
        self.assertEqual([], self.problems())

    def test_a_learner_test_that_is_still_pending_blocks_approved(self) -> None:
        data = self.meta(content_status="approved")
        data["verification"] = {name: "done" for name in check.VERIFICATION_KEYS}
        self.write_lesson("sd-01-001", meta=data)
        self.assertProblem("approved needs every verification field")

    def test_image_evidence_with_real_values_is_accepted_as_a_string_or_a_date(self) -> None:
        entry = {"url": "https://assets.bytebytego.com/d/1.png", "sha256": "a" * 64, "retrieved_on": "2026-10-12"}
        self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[entry]))
        self.assertEqual([], self.problems())
        # yaml.safe_dump writes a date unquoted and safe_load reads it back as a datetime.date
        self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[{**entry, "retrieved_on": datetime.date(2026, 10, 12)}]))
        self.assertEqual([], self.problems())

    def test_image_evidence_values_must_be_real(self) -> None:
        good = {"url": "https://assets.bytebytego.com/d/1.png", "sha256": "a" * 64, "retrieved_on": "2026-10-12"}
        bad = {"null url": {**good, "url": None}, "not an http url": {**good, "url": "ftp://x/y.png"},
               "empty digest": {**good, "sha256": ""}, "short digest": {**good, "sha256": "a" * 63},
               "non-hex digest": {**good, "sha256": "z" * 64}, "null date": {**good, "retrieved_on": None},
               "not a date": {**good, "retrieved_on": "yesterday"}, "url without a host": {**good, "url": "https://"},
               "month 99": {**good, "retrieved_on": "2026-99-99"}, "february 30": {**good, "retrieved_on": "2026-02-30"}}
        for name, entry in bad.items():
            with self.subTest(entry=name):
                self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[entry]))
                self.assertProblem("each image_evidence entry needs")

    def evidence_problems(self, url: str) -> list[str]:
        evidence = [{"url": url, "sha256": "a" * 64, "retrieved_on": "2026-10-12"}]
        self.write_lesson("sd-01-001", meta=self.meta(image_evidence=evidence))
        return [line for line in self.problems() if "image_evidence" in line]

    def test_an_evidence_url_needs_a_real_host_and_a_readable_port(self) -> None:
        for url in ["https://@/image.png", "https://user@/image.png", "https://:443/image.png", "https://./a.png",
                    "https://-a.com/x", "https://a-.com/x", "https://a..b/x", "https://a_b.com/x", "https://host:abc/x",
                    "https://host:99999/x", "https://tên.vn/x", "http://", "https:///x", "ftp://example.com/x",
                    "https://" + "a" * 64 + ".com/x", "https://1.2.3/x extra", "https://example.com/a b.png",
                    "https://example.com/a\tb", "https://example.com/a\x01b", "https://example.com/\u200bb"]:
            with self.subTest(url=url):
                self.assertTrue(self.evidence_problems(url), f"{url!r} was accepted")

    def test_ordinary_evidence_urls_are_accepted(self) -> None:
        for url in ["https://user@example.com/a.png", "https://example.com:8443/a", "http://127.0.0.1/a",
                    "https://[::1]/a", "https://example.com./a", "https://sub-1.example.co.uk/a?b=c#d",
                    "https://localhost/a", "https://EXAMPLE.com/a", "https://xn--tn-qla.vn/a"]:
            with self.subTest(url=url):
                self.assertEqual([], self.evidence_problems(url))

    def test_a_timestamp_is_not_a_retrieval_date(self) -> None:
        good = {"url": "https://example.com/a.png", "sha256": "a" * 64}
        for name, when in {"datetime": datetime.datetime(2026, 10, 12, 12, 34, 56),
                           "datetime at midnight": datetime.datetime(2026, 10, 12),
                           "a quoted timestamp": "2026-10-12 12:34:56", "an ISO timestamp": "2026-10-12T12:34:56Z"}.items():
            with self.subTest(value=name):
                self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[{**good, "retrieved_on": when}]))
                self.assertTrue([line for line in self.problems() if "image_evidence" in line])
        self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[{**good, "retrieved_on": datetime.date(2026, 10, 12)}]))
        self.assertEqual([], self.problems())

    def test_an_image_evidence_entry_without_a_digest_is_reported(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(image_evidence=[{"url": "https://x/y.png"}]))
        self.assertProblem("image_evidence entry needs")


class LessonMarkdownRuleTests(StoreCase):
    def test_an_unclosed_code_fence_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n```mermaid\nflowchart TB\n")
        self.assertProblem("unclosed code fence")

    def test_details_with_attributes_is_a_balanced_details_block(self) -> None:
        block = "<details open>\n<summary>x</summary>\n\nnội dung\n\n</details>"
        self.write_lesson("sd-01-001", body=BODY + "\n" + block + "\n")
        self.assertEqual([], self.problems())

    def test_a_details_tag_in_a_code_block_a_code_span_or_a_comment_is_not_counted(self) -> None:
        for name, text in {"code block": "```html\n<details>\n```", "code span": "Gõ `<details>` để mở.",
                           "comment": "<!-- <details> -->"}.items():
            with self.subTest(where=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + text + "\n")
                self.assertEqual([], self.problems())

    def test_a_self_closing_details_tag_opens_a_block_as_it_does_in_html(self) -> None:
        for name, tag in {"slash": "<details/>", "space and slash": "<details />", "attribute": "<details open/>"}.items():
            with self.subTest(tag=name):
                self.write_lesson("sd-01-001", body=BODY + f"\n{tag}\n<summary>x</summary>\n\nchữ\n")
                self.assertProblem("unbalanced <details> tags")
        self.write_lesson("sd-01-001", body=BODY + "\n<details/>\n<summary>x</summary>\n\nchữ\n\n</details>\n")
        self.assertEqual([], self.problems())

    def test_self_closing_void_tags_are_fine(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\ndòng<br/>sau<br />nữa\n")
        self.assertEqual([], self.problems())

    def test_a_stray_closing_details_tag_is_reported_even_when_a_later_block_balances_the_count(self) -> None:
        block = "<details>\n<summary>x</summary>\n\nnội dung\n\n</details>"
        forms = {"close then an open block left open": "</details>\n\n<details>\n<summary>x</summary>\n\nnội dung\n",
                 "close then a balanced block": "</details>\n\n" + block,
                 "close only": "</details>"}
        for name, text in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + text + "\n")
                self.assertProblem("unbalanced <details>")

    def test_nested_details_blocks_are_balanced(self) -> None:
        inner = "<details>\n<summary>trong</summary>\n\nb\n\n</details>"
        outer = f"<details>\n<summary>ngoài</summary>\n\n{inner}\n\n</details>"
        self.write_lesson("sd-01-001", body=BODY + "\n" + outer + "\n")
        self.assertEqual([], self.problems())

    def test_a_missing_local_image_is_reported_in_every_form(self) -> None:
        forms = {"inline": "![sơ đồ](missing.svg)", "reference": "![sơ đồ][i]\n\n[i]: missing.svg",
                 "html img": '<img src="missing.svg" alt="sơ đồ">'}
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                self.assertProblem("'missing.svg' does not resolve")

    def test_a_local_svg_figure_is_accepted_in_every_form_and_in_any_case(self) -> None:
        forms = {"inline": "![sơ đồ](diagram.svg)", "reference": "![sơ đồ][i]\n\n[i]: diagram.svg",
                 "html img": '<img src="diagram.svg" alt="sơ đồ">', "upper case": "![sơ đồ](FIGURE.SVG)"}
        for name, form in forms.items():
            with self.subTest(form=name):
                lesson_dir = self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                (lesson_dir / "diagram.svg").write_text("<svg/>", encoding="utf-8")
                (lesson_dir / "FIGURE.SVG").write_text("<svg/>", encoding="utf-8")
                self.assertEqual([], self.problems())

    def test_an_image_that_is_not_a_local_svg_is_reported(self) -> None:
        forms = {"local png": "![x](diagram.png)", "local jpeg in html": '<img src="diagram.jpg">',
                 "remote svg": "![x](https://example.com/a.svg)", "remote png": "![x](https://example.com/a.png)"}
        for name, form in forms.items():
            with self.subTest(form=name):
                lesson_dir = self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                (lesson_dir / "diagram.png").write_bytes(b"\x89PNG")
                (lesson_dir / "diagram.jpg").write_bytes(b"\xff\xd8")
                self.assertProblem("must be a local .svg file")

    def test_an_image_must_sit_directly_in_the_lesson_directory(self) -> None:
        self.write_source_map({"sd-01-001": ("Bài một", SNAPSHOT), "sd-01-002": ("Bài hai", SNAPSHOT)})
        other = self.write_lesson("sd-01-002", meta=self.meta(id="sd-01-002", title_vi="Bài hai"))
        (other / "figure.svg").write_text("<svg/>", encoding="utf-8")
        mine = self.write_lesson("sd-01-001", body=BODY + "\n![x](./figure.svg)\n")
        (mine / "figure.svg").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], [line for line in self.problems() if line.startswith("sd-01-001")])
        forms = {"another lesson": "../sd-01-002/figure.svg", "the same lesson by a detour": "../sd-01-001/figure.svg",
                 "encoded": "..%2Fsd-01-002%2Ffigure.svg", "a subdirectory": "figures/figure.svg",
                 "an absolute path": "/figure.svg"}
        for name, destination in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + f"\n![x]({destination})\n")
                self.assertProblem("directly inside the lesson directory")

    @unittest.skipUnless(hasattr(os, "symlink"), "needs symbolic links")
    def test_a_symbolic_link_is_not_a_lesson_file(self) -> None:
        elsewhere = self.root / "shared.svg"
        elsewhere.write_text("<svg/>", encoding="utf-8")
        lesson_dir = self.write_lesson("sd-01-001", body=BODY + "\n![x](shared.svg)\n")
        (lesson_dir / "shared.svg").symlink_to(elsewhere)
        self.assertProblem("shared.svg is a symbolic link")
        (lesson_dir / "shared.svg").unlink()
        lesson_md = lesson_dir / "lesson.md"
        real = self.root / "real.md"
        real.write_text(BODY, encoding="utf-8")
        lesson_md.unlink()
        lesson_md.symlink_to(real)
        self.assertProblem("lesson.md is a symbolic link")

    @unittest.skipUnless(hasattr(os, "symlink"), "needs symbolic links")
    def test_a_symbolic_link_for_a_lesson_directory_the_readme_or_lessons_is_reported(self) -> None:
        copy = self.root / "elsewhere"
        copy.mkdir()
        (copy / "lesson.md").write_text(BODY, encoding="utf-8")
        (copy / "lesson.yaml").write_text(yaml.safe_dump(META), encoding="utf-8")
        (self.store / "lessons" / "sd-01-002").symlink_to(copy, target_is_directory=True)
        found = self.problems()
        self.assertTrue(any("lessons: sd-01-002 is not a lesson directory" in line for line in found), found)
        self.assertFalse(any(line.startswith("sd-01-002:") for line in found), "the linked directory is not checked as a lesson")
        (self.store / "lessons" / "sd-01-002").unlink()
        readme = self.store / "README.md"
        real = self.root / "README.real"
        real.write_text(README, encoding="utf-8")
        readme.unlink()
        readme.symlink_to(real)
        self.assertProblem("README.md: is a symbolic link")
        readme.unlink()
        self.write_readme(README)
        moved = self.root / "lessons-real"
        (self.store / "lessons").rename(moved)
        (self.store / "lessons").symlink_to(moved, target_is_directory=True)
        self.assertProblem("lessons: is a symbolic link")

    def test_a_lesson_directory_may_hold_only_lesson_files_and_svg_figures(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001")
        (lesson_dir / "diagram.svg").write_text("<svg/>", encoding="utf-8")
        (lesson_dir / "FIGURE.SVG").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], self.problems())
        for name in ("diagram.png", "photo.JPG", "notes.txt", "diagram.svg.png"):
            with self.subTest(file=name):
                (lesson_dir / name).write_bytes(b"x")
                self.assertProblem(f"{name} is not allowed")
                (lesson_dir / name).unlink()
        (lesson_dir / "assets").mkdir()
        self.assertProblem("assets is not allowed")
        (lesson_dir / "folder.svg").mkdir()
        self.assertProblem("folder.svg is not allowed")

    def test_an_svg_file_must_be_a_drawing_not_a_renamed_picture(self) -> None:
        png = "data:image/png;base64,iVBORw0KGgo="
        svgs = {
            "a renamed png": (b"\x89PNG\r\n\x1a\n\x00\x00", "is not well-formed XML"),
            "an empty file": (b"", "is not well-formed XML"),
            "xml with another root": (b"<html/>", "does not have an <svg> root"),
            "an embedded raster": (f'<svg><image href="{png}"/></svg>'.encode(), "embeds a picture with <image>"),
            "a linked raster": (b'<svg><image href="source.png"/></svg>', "embeds a picture with <image>"),
            "a namespaced image": (b'<svg xmlns="http://www.w3.org/2000/svg"><image/></svg>',
                                   "embeds a picture with <image>"),
            "a bare html img": (b'<svg><img xmlns="http://www.w3.org/1999/xhtml" src="a.png"/></svg>',
                                "embeds a picture with <img>"),
            "an html img inside foreignObject": (
                b'<svg xmlns="http://www.w3.org/2000/svg"><foreignObject>'
                b'<img xmlns="http://www.w3.org/1999/xhtml" src="a.png"/></foreignObject></svg>',
                "uses <foreignobject>"),
            "an html object holding a data uri inside foreignObject": (
                f'<svg xmlns="http://www.w3.org/2000/svg"><foreignObject><object xmlns="http://www.w3.org/1999/xhtml" '
                f'data="{png}"/></foreignObject></svg>'.encode(), "uses <foreignobject>"),
            "a bare object holding a data uri": (f'<svg><object data="{png}"/></svg>'.encode(), "uses <object>"),
            "an embed": (b'<svg><embed src="a.png"/></svg>', "uses <embed>"),
            "an iframe": (b'<svg><iframe src="a.html"/></svg>', "uses <iframe>"),
            "a script": (b"<svg><script>alert(1)</script></svg>", "uses <script>"),
            "an animation that sets an href": (b'<svg><use href="#a"><set attributeName="href" to="x.svg"/></use></svg>',
                                              "uses <set>"),
            "an animate": (b'<svg><rect><animate attributeName="x" to="9"/></rect></svg>', "uses <animate>"),
            "a link element": (b'<svg><a href="#a"><rect/></a></svg>', "uses <a>"),
            "an inkscape element": (b'<svg xmlns:s="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"><s:namedview/></svg>',
                                    "uses <namedview>"),
            "a svg-named element in another namespace": (b'<svg><rect xmlns="http://www.w3.org/1999/xhtml"/></svg>',
                                                         "uses <rect>"),
            "a feImage that loads the source host": (
                b'<svg xmlns="http://www.w3.org/2000/svg"><filter><feImage href="https://assets.bytebytego.com/'
                b'source.png"/></filter></svg>', "assets.bytebytego.com"),
            "a feImage that loads another picture": (
                b'<svg xmlns="http://www.w3.org/2000/svg"><filter><feImage href="#a"/></filter></svg>',
                "embeds a picture with <feimage>"),
            "the source host in a label": (b"<svg><text>assets.bytebytego.com</text></svg>", "assets.bytebytego.com"),
            "an href to another file": (b'<svg><use href="other.svg#a"/></svg>', "outside the drawing"),
            "an href to a web page": (b'<svg><use href="https://example.com/a.svg"/></svg>', "outside the drawing"),
            "a namespaced xlink:href": (
                b'<svg xmlns:xlink="http://www.w3.org/1999/xlink"><use xlink:href="https://example.com/a.svg"/></svg>',
                "outside the drawing"),
            "a data uri in an href": (f'<svg><use href="{png}"/></svg>'.encode(), "outside the drawing"),
            "a url() to a file in an attribute": (b'<svg><rect style="fill:url(https://example.com/a.png)"/></svg>',
                                                  "url() or @import"),
            "a data uri in a url() in an attribute": (f'<svg><rect style="fill:url({png})"/></svg>'.encode(),
                                                      "url() or @import"),
            "a quoted url() in an attribute": (b'<svg><rect style="fill:url( \'a.png\' )"/></svg>',
                                               "url() or @import"),
            "a url() in a style element": (f"<svg><style>.a{{background:url({png})}}</style></svg>".encode(),
                                           "url() or @import"),
            "an @import in a style element": (b'<svg><style>@import "fonts.css";</style></svg>', "url() or @import"),
        }
        lesson_dir = self.write_lesson("sd-01-001")
        for name, (content, reason) in svgs.items():
            with self.subTest(file=name):
                (lesson_dir / "figure.svg").write_bytes(content)
                self.assertProblem(f"figure.svg")
                self.assertProblem(reason)

    def test_the_elements_of_an_ordinary_drawing_are_accepted(self) -> None:
        names = ["g", "defs", "symbol", "use", "title", "desc", "style", "path", "rect", "circle", "ellipse", "line",
                 "polyline", "polygon", "text", "tspan", "textPath", "marker", "pattern", "mask", "clipPath",
                 "linearGradient", "radialGradient", "stop", "filter", "feBlend", "feColorMatrix", "feComposite",
                 "feDropShadow", "feGaussianBlur", "feFlood", "feOffset", "feMerge", "feMergeNode"]
        lesson_dir = self.write_lesson("sd-01-001")
        for name in names:
            with self.subTest(element=name):
                (lesson_dir / "figure.svg").write_text(
                    f'<svg xmlns="http://www.w3.org/2000/svg"><svg><{name}/></svg></svg>', encoding="utf-8")
                self.assertEqual([], self.problems())

    def test_an_svg_with_a_processing_instruction_is_reported(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001")
        for name, svg in {"a stylesheet in the prolog": '<?xml-stylesheet href="https://example.com/s.css"?><svg/>',
                          "a stylesheet after the declaration":
                              '<?xml version="1.0"?>\n<?xml-stylesheet href="s.css" type="text/css"?>\n<svg/>',
                          "an instruction inside the drawing": "<svg><g><?php echo 1 ?></g></svg>",
                          "an instruction after the drawing": "<svg/><?xpacket end='w'?>"}.items():
            with self.subTest(file=name):
                (lesson_dir / "figure.svg").write_text(svg, encoding="utf-8")
                self.assertProblem("has a processing instruction")

    def test_css_animation_and_transition_in_an_svg_are_reported(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001")
        cases = {
            "keyframes in a style element": "<svg><style>@keyframes x{from{opacity:0}to{opacity:1}} rect{animation:x 1s}</style></svg>",
            "an entity-escaped keyframes": "<svg><style>@keyframes x&#123;from&#123;opacity:0&#125;&#125;</style></svg>",
            "an animation in a style attribute": '<svg><rect style="animation: spin 1s infinite"/></svg>',
            "an animation-name property": '<svg><rect style="animation-name:spin"/></svg>',
            "a prefixed animation": '<svg><rect style="-webkit-animation: spin 1s"/></svg>',
            "a transition": '<svg><rect style="transition: all 1s"/></svg>',
            "an upper-case property": '<svg><rect style="ANIMATION : spin 1s"/></svg>',
        }
        for name, svg in cases.items():
            with self.subTest(file=name):
                (lesson_dir / "figure.svg").write_text(svg, encoding="utf-8")
                self.assertProblem("uses a CSS animation or transition")

    def test_words_that_only_look_like_animation_are_fine(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001")
        (lesson_dir / "figure.svg").write_text(
            '<svg><style>.animal{fill:red} .a{transform:rotate(3deg)}</style><title>animation: demo</title>'
            '<text>animation: transition: @keyframes</text><rect class="animation"/></svg>', encoding="utf-8")
        self.assertEqual([], self.problems())

    def test_an_svg_with_a_doctype_is_reported(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001")
        cases = {
            "an external DTD": '<!DOCTYPE svg SYSTEM "https://example.com/svg.dtd"><svg/>',
            "the W3C SVG 1.1 DTD": '<?xml version="1.0"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
                                   '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"><svg/>',
            "an internal subset with an entity": '<!DOCTYPE svg [<!ENTITY a "x">]><svg>&a;</svg>',
            "a bare DOCTYPE": "<!DOCTYPE svg><svg/>",
            "a DOCTYPE after a comment": "<!-- c --><!DOCTYPE svg><svg/>",
        }
        for name, svg in cases.items():
            with self.subTest(file=name):
                (lesson_dir / "figure.svg").write_text(svg, encoding="utf-8")
                self.assertProblem("has a DOCTYPE declaration")

    def test_the_xml_declaration_is_not_a_processing_instruction(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001")
        (lesson_dir / "figure.svg").write_text('<?xml version="1.0" encoding="UTF-8" standalone="no"?><svg/>',
                                               encoding="utf-8")
        self.assertEqual([], self.problems())

    def test_a_real_looking_svg_drawing_is_accepted(self) -> None:
        drawing = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                   'viewBox="0 0 10 10" aria-label="Data: sơ đồ"><title>Data: sơ đồ</title>'
                   '<defs><style>.a::after{content:"data: chữ"}</style>'
                   '<marker id="m"/><linearGradient id="g"/></defs>'
                   '<rect fill="url(\'#g\')" style="marker-end:url( #m )"/><use href="#a"/><use xlink:href="#a"/>'
                   '<text>Data: chữ</text></svg>')
        lesson_dir = self.write_lesson("sd-01-001")
        (lesson_dir / "figure.svg").write_text(drawing, encoding="utf-8")
        self.assertEqual([], self.problems())

    def test_a_closed_fence_inside_a_blockquote_or_a_list_is_closed(self) -> None:
        forms = {"blockquote": "> ```\n> flowchart TB\n> ```", "nested blockquote": "> > ~~~\n> > a\n> > ~~~",
                 "blockquote without a space": ">```\n>a\n>```", "list item": "- mục\n\n  ```\n  a\n  ```",
                 "blockquote in a list": "- mục\n\n  > ```\n  > a\n  > ```"}
        for name, block in forms.items():
            with self.subTest(block=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + block + "\n")
                self.assertEqual([], self.problems())

    def test_an_unclosed_fence_inside_a_blockquote_is_reported(self) -> None:
        for name, block in {"unclosed": "> ```\n> flowchart TB", "closed by a shorter fence": "> ````\n> a\n> ```"}.items():
            with self.subTest(block=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + block + "\n")
                self.assertProblem("unclosed code fence")

    def test_a_lone_opening_fence_at_the_end_of_the_file_is_reported(self) -> None:
        for name, ending in {"backticks": "```", "tildes": "~~~", "long backticks": "````",
                             "backticks and a newline": "```\n", "an info string": "```mermaid"}.items():
            with self.subTest(ending=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + ending)
                self.assertProblem("unclosed code fence")

    def test_an_empty_fenced_block_is_not_unclosed(self) -> None:
        for name, block in {"backticks": "```\n```", "tildes": "~~~\n~~~", "an info string": "```text\n```\n"}.items():
            with self.subTest(block=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + block + "\n")
                self.assertEqual([], self.problems())

    def test_an_unclosed_tilde_fence_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n~~~mermaid\nflowchart TB\n")
        self.assertProblem("unclosed code fence")

    def test_closed_fences_of_either_marker_and_any_length_are_accepted(self) -> None:
        for name, fence in {"backticks": "```mermaid\nx\n```", "tildes": "~~~\nx\n~~~",
                            "long backticks": "````\nx\n````",
                            "a long fence may contain a short one": "````\n```\nx\n```\n````"}.items():
            with self.subTest(fence=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + fence + "\n")
                self.assertEqual([], self.problems())

    def test_a_closing_fence_shorter_than_the_opening_one_does_not_close_it(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n````\ncode\n```\n")
        self.assertProblem("unclosed code fence")

    def test_unbalanced_details_tags_are_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n<details>\n<summary>x</summary>\n")
        self.assertProblem("unbalanced <details>")

    def test_a_relative_link_that_does_not_resolve_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[thiếu](nowhere.md)\n")
        self.assertProblem("does not resolve")

    def test_a_root_relative_link_is_not_looked_up_on_the_machine_running_the_check(self) -> None:
        on_this_machine = self.root / "exists.md"
        on_this_machine.write_text("x", encoding="utf-8")
        for name, destination in {"a file on this machine": str(on_this_machine), "a directory": str(self.root),
                                  "the filesystem root": "/", "a missing one": "/no/such/file",
                                  "a file inside the store, by its absolute path": str(self.store / "README.md")}.items():
            with self.subTest(destination=name):
                self.write_lesson("sd-01-001", body=BODY + f"\n[x]({destination})\n")
                self.assertProblem(f"relative link '{destination}' does not resolve")

    def test_a_relative_link_that_resolves_is_accepted(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[meta](lesson.yaml)\n")
        self.assertEqual([], self.problems())

    def test_a_broken_reference_style_relative_link_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[tài liệu][ref]\n\n[ref]: missing.md\n")
        self.assertProblem("'missing.md' does not resolve")

    def test_a_broken_relative_html_anchor_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + '\n<a href="missing.md">tài liệu</a>\n')
        self.assertProblem("'missing.md' does not resolve")

    def test_a_reference_style_relative_link_that_resolves_is_accepted(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[meta][ref]\n\n[ref]: lesson.yaml\n")
        self.assertEqual([], self.problems())

    def test_a_relative_link_with_a_fragment_or_query_is_checked_by_its_path(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[a](lesson.yaml#id) [b](lesson.yaml?x=1)\n")
        self.assertEqual([], self.problems())
        self.write_lesson("sd-01-001", body=BODY + "\n[c](missing.md#id)\n")
        self.assertProblem("'missing.md#id' does not resolve")

    def test_anchors_urls_and_mail_links_are_not_relative_links(self) -> None:
        links = "[a](#phan-nguon) [b](https://example.com/x) [c](mailto:a@b.vn) [d](//example.com/x)"
        self.write_lesson("sd-01-001", body=BODY + "\n" + links + "\n")
        self.assertEqual([], self.problems())

    def test_a_link_shaped_text_in_a_code_block_is_not_checked(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n```\n[x](missing.md)\n```\n")
        self.assertEqual([], self.problems())

    def test_a_relative_link_with_non_ascii_letters_resolves(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001", body=BODY + "\n[hình](<sơ đồ.svg>)\n")
        (lesson_dir / "sơ đồ.svg").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], self.problems())

    def test_a_source_map_entry_without_a_snapshot_url_is_reported(self) -> None:
        missing = object()
        for name, value in {"null": None, "empty": "", "blank": "  ", "a number": 5, "a list": [SNAPSHOT],
                            "missing": missing}.items():
            with self.subTest(entry=name):
                entry = source_entry()
                if value is missing:
                    del entry["source_snapshot_url"]
                else:
                    entry["source_snapshot_url"] = value
                data = {**PIN, "categories": [{"id": "sd-01", "lessons": [entry]}]}
                self.source_map.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                self.assertProblem("the source map has no source_snapshot_url for this lesson")

    def test_a_lesson_that_is_not_in_the_source_map_is_not_also_missing_a_snapshot(self) -> None:
        self.write_source_map({})
        found = self.problems()
        self.assertTrue(any("id is not in the source map" in line for line in found), found)
        self.assertFalse(any("snapshot" in line for line in found), found)

    def test_a_lesson_that_does_not_link_the_pinned_snapshot_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body="# Bài một\n\nKhông có nguồn.\n")
        self.assertProblem("pinned source snapshot")

    def test_a_mention_of_a_lesson_without_a_directory_is_reported(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\nĐọc cùng sd-01-011.\n")
        self.assertProblem("mentions sd-01-011")

    def test_a_mention_of_an_existing_lesson_or_of_itself_is_accepted(self) -> None:
        self.write_source_map({"sd-01-001": ("Bài một", SNAPSHOT), "sd-01-002": ("Bài hai", SNAPSHOT)})
        self.write_lesson("sd-01-002", meta=self.meta(id="sd-01-002", title_vi="Bài hai"))
        self.write_readme(README + "| [sd-01-002](lessons/sd-01-002/lesson.md) | Bài hai |\n")
        self.write_lesson("sd-01-001", body=BODY + "\nXem sd-01-002 và chính sd-01-001.\n")
        self.assertEqual([], self.problems())


    def test_a_snapshot_url_in_a_code_block_is_not_a_link(self) -> None:
        self.write_lesson("sd-01-001", body=f"# Bài một\n\n```\n{SNAPSHOT}\n```\n")
        self.assertProblem("pinned source snapshot")

    def test_a_snapshot_url_in_an_html_comment_is_not_a_link(self) -> None:
        for name, comment in {"markdown link": f"<!-- [nguồn]({SNAPSHOT}) -->",
                              "html anchor": f'<!-- <a href="{SNAPSHOT}">nguồn</a> -->'}.items():
            with self.subTest(comment=name):
                self.write_lesson("sd-01-001", body=f"# Bài một\n\n{comment}\n")
                self.assertProblem("pinned source snapshot")

    def test_a_snapshot_url_in_plain_text_is_not_a_link(self) -> None:
        self.write_lesson("sd-01-001", body=f"# Bài một\n\nNguồn: {SNAPSHOT}\n")
        self.assertProblem("pinned source snapshot")

    def test_a_link_to_a_section_of_the_pinned_snapshot_is_a_link_to_it(self) -> None:
        for name, body in {"markdown": f"# Bài một\n\n[nguồn]({SNAPSHOT}#phan-1)\n",
                           "html": f'# Bài một\n\n<a href="{SNAPSHOT}#phan-1">nguồn</a>\n',
                           "reference": f"# Bài một\n\n[nguồn][s]\n\n[s]: {SNAPSHOT}#L10-L20\n"}.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=body)
                self.assertEqual([], self.problems())

    def test_a_link_to_another_file_with_a_fragment_is_not_the_snapshot(self) -> None:
        self.write_lesson("sd-01-001", body=f"# Bài một\n\n[nguồn]({SNAPSHOT}x#phan-1)\n")
        self.assertProblem("does not link the pinned source snapshot")

    def test_a_snapshot_given_as_an_html_anchor_is_a_link(self) -> None:
        self.write_lesson("sd-01-001", body=f'# Bài một\n\n<a href="{SNAPSHOT}">nguồn</a>\n')
        self.assertEqual([], self.problems())

    def test_href_text_inside_another_attribute_is_not_a_link(self) -> None:
        for name, tag in {"title": f"<a title='href=\"{SNAPSHOT}\"'>nguồn</a>",
                          "no href": f'<a data-x="{SNAPSHOT}">nguồn</a>',
                          "other tag": f'<span href="{SNAPSHOT}">nguồn</span>'}.items():
            with self.subTest(tag=name):
                self.write_lesson("sd-01-001", body=f"# Bài một\n\n{tag}\n")
                self.assertProblem("pinned source snapshot")

    def test_an_upper_case_or_single_quoted_html_anchor_is_a_link(self) -> None:
        for name, tag in {"upper case": f'<A HREF="{SNAPSHOT}">nguồn</A>',
                          "single quotes": f"<a href='{SNAPSHOT}'>nguồn</a>"}.items():
            with self.subTest(tag=name):
                self.write_lesson("sd-01-001", body=f"# Bài một\n\n{tag}\n")
                self.assertEqual([], self.problems())

    def test_a_snapshot_given_as_a_reference_style_link_is_a_link(self) -> None:
        self.write_lesson("sd-01-001", body=f"# Bài một\n\n[nguồn][s]\n\n[s]: {SNAPSHOT}\n")
        self.assertEqual([], self.problems())

    def test_every_form_of_source_image_embed_is_reported(self) -> None:
        url = "https://assets.bytebytego.com/diagrams/0001-x.png"
        forms = {
            "inline image": f"![]({url})",
            "reference-style image": f"![x][img]\n\n[img]: {url}",
            "html img": f'<img src="{url}">',
            "html picture": f'<picture><source srcset="{url}"></picture>',
            "bare url": url,
            "upper case host": "HTTPS://ASSETS.BYTEBYTEGO.COM/diagrams/0001-x.png",
            "plain mention of the host": "Ảnh nguồn ở assets.bytebytego.com chưa được mở.",
        }
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                self.assertProblem("lessons must not use source images")

    def test_a_src_attribute_on_a_tag_other_than_img_is_not_an_image(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + '\nH<sub src="missing.png">2</sub>O\n')
        self.assertEqual([], self.problems())

    def test_an_html_image_without_a_source_is_reported(self) -> None:
        forms = {"no attributes": "<img>", "only alt": '<img alt="sơ đồ">', "empty src": '<img src="" alt="x">',
                 "empty single-quoted src": "<img src=''>", "empty srcset": '<img srcset="" alt="x">',
                 "only a width": '<img width="100">'}
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                self.assertProblem("must be a local .svg file")

    def test_an_html_image_with_only_a_srcset_is_a_source(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001", body=BODY + '\n<img srcset="a.svg 1x" alt="x">\n')
        (lesson_dir / "a.svg").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], self.problems())

    def test_a_missing_or_non_svg_image_in_an_img_srcset_is_reported(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001", body=BODY + '\n<img srcset="one.svg 1x, two.svg 2x" alt="x">\n')
        (lesson_dir / "one.svg").write_text("<svg/>", encoding="utf-8")
        self.assertProblem("'two.svg' does not resolve")
        (lesson_dir / "two.svg").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], self.problems())
        self.write_lesson("sd-01-001", body=BODY + '\n<img srcset="one.svg 1x, two.png 2x" alt="x">\n')
        (lesson_dir / "two.png").write_bytes(b"x")
        self.assertProblem("'two.png' must be a local .svg file")

    def test_srcset_urls_are_split_like_the_html_spec_splits_them(self) -> None:
        cases = {
            "a.svg": ["a.svg"],
            "a.svg 1x, b.svg 2x": ["a.svg", "b.svg"],
            "a.svg, b.svg": ["a.svg", "b.svg"],
            "a.svg 1x,b.svg 2x": ["a.svg", "b.svg"],
            "a.svg,b.svg": ["a.svg,b.svg"],
            "  a.svg 100w ,  b.svg 200w  ": ["a.svg", "b.svg"],
            "a,b.svg 1x": ["a,b.svg"],
            "": [],
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(expected, check.srcset_urls(value))

    def test_raw_html_outside_the_allow_list_is_reported(self) -> None:
        forms = {
            "picture": '<picture><source srcset="a.svg"></picture>',
            "inline svg": '<svg><image href="a.png"/></svg>',
            "object": '<object data="a.svg"></object>',
            "video": '<video poster="a.png"></video>',
            "iframe": '<iframe src="https://example.com"></iframe>',
            "script": "<script>alert(1)</script>",
            "div": "<div>chữ</div>",
            "a closing tag without its opener": "</div>",
            "an inline closing tag without its opener": "chữ</span> nữa",
        }
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_lesson("sd-01-001", body=BODY + "\n" + form + "\n")
                self.assertProblem("raw HTML is limited to")

    def test_the_allowed_html_tags_are_accepted(self) -> None:
        body = (BODY + "\nH<sub>2</sub>O, x<sup>2</sup>, <kbd>Ctrl</kbd><br>dòng sau\n\n"
                "<details open>\n<summary>Gợi ý</summary>\n\nĐáp án.\n\n</details>\n")
        self.write_lesson("sd-01-001", body=body)
        self.assertEqual([], self.problems())

    def test_html_tags_inside_code_are_not_raw_html(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n`<div>`\n\n```html\n<picture></picture>\n```\n")
        self.assertEqual([], self.problems())

    def test_a_local_image_is_not_a_source_image(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001", body=BODY + "\n![sơ đồ](diagram.svg)\n")
        (lesson_dir / "diagram.svg").write_text("<svg/>", encoding="utf-8")
        self.assertEqual([], self.problems())

class RobustnessTests(StoreCase):
    """Whatever an author types, the checker reports problems and keeps going; it never raises."""

    ODD_VALUES = [None, True, 0, 1.5, "", " ", "drafted", "x" * 400, [], ["drafted"], [[1]], {}, {"a": 1}, [{"a": 1}],
                  datetime.date(2026, 1, 1)]

    def run_checker(self, data: object, *, raw: str | None = None) -> list[str]:
        lesson_dir = self.write_lesson("sd-01-001")
        text = raw if raw is not None else yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
        (lesson_dir / "lesson.yaml").write_text(text, encoding="utf-8")
        return self.problems()

    def test_an_odd_value_for_any_lesson_yaml_field_is_reported_not_raised(self) -> None:
        for key in sorted(check.KEYS):
            for value in self.ODD_VALUES:
                with self.subTest(key=key, value=value):
                    self.run_checker(self.meta(**{key: value}))

    def test_an_odd_value_inside_verification_or_an_evidence_entry_is_reported_not_raised(self) -> None:
        good = {"url": "https://example.com/a.png", "sha256": "a" * 64, "retrieved_on": "2026-10-12"}
        for value in self.ODD_VALUES:
            for key in sorted(check.VERIFICATION_KEYS):
                with self.subTest(verification=key, value=value):
                    self.run_checker(self.meta(verification={**META["verification"], key: value}))
            for key in sorted(check.IMAGE_EVIDENCE_KEYS):
                with self.subTest(evidence=key, value=value):
                    self.run_checker(self.meta(image_evidence=[{**good, key: value}]))
            with self.subTest(evidence_item=value):
                self.run_checker(self.meta(image_evidence=[value]))

    def test_a_lesson_yaml_that_is_not_a_mapping_or_has_odd_keys_is_reported_not_raised(self) -> None:
        for name, raw in {"a list": "- a\n- b\n", "a string": "hello\n", "empty": "", "a number": "3\n",
                          "mixed key types": "1: a\nid: x\n", "a null key": "null: a\nid: x\n",
                          "a boolean key": "true: a\n", "a date key": "2026-10-12: a\n"}.items():
            with self.subTest(file=name):
                self.run_checker(None, raw=raw)

    def test_a_malformed_evidence_url_is_a_problem(self) -> None:
        for url in ["https://[", "http://[::1", "https://[x]/a.png", "https://a b/c", "//", ":", "http://exa\x00mple.com"]:
            with self.subTest(url=url):
                data = self.meta(image_evidence=[{"url": url, "sha256": "a" * 64, "retrieved_on": "2026-10-12"}])
                self.assertTrue(any("image_evidence" in line for line in self.run_checker(data)))

    def test_odd_svg_files_are_reported_not_raised(self) -> None:
        laughs = ('<?xml version="1.0"?><!DOCTYPE l [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;">'
                  '<!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;"><!ENTITY d "&c;&c;&c;&c;&c;&c;&c;&c;">]><svg>&d;</svg>')
        odd = {"invalid utf-8": b"\xff\xfe<svg/>", "unknown encoding": b'<?xml version="1.0" encoding="nope"?><svg/>',
               "entity expansion": laughs.encode(), "deep nesting": b"<svg>" + b"<g>" * 3000 + b"</g>" * 3000 + b"</svg>",
               "a null byte": b"<svg>\x00</svg>", "a bom": b"\xef\xbb\xbf<svg/>", "only a comment": b"<!-- x -->"}
        lesson_dir = self.write_lesson("sd-01-001")
        for name, content in odd.items():
            with self.subTest(file=name):
                (lesson_dir / "figure.svg").write_bytes(content)
                self.assertIsInstance(self.problems(), list)

    def test_a_lesson_file_that_is_a_directory_is_reported_not_raised(self) -> None:
        lesson_dir = self.write_lesson("sd-01-001")
        for name in ("lesson.md", "lesson.yaml"):
            with self.subTest(name=name):
                (lesson_dir / name).unlink()
                (lesson_dir / name).mkdir()
                self.assertProblem(f"{name} is missing")
                (lesson_dir / name).rmdir()
                self.write_lesson("sd-01-001")

    def test_pathological_markdown_is_reported_not_raised(self) -> None:
        deep = {"nested quotes": "> " * 3000 + "x", "nested lists": "".join("  " * i + "- a\n" for i in range(400)),
                "unmatched brackets": "[" * 20000, "unmatched emphasis": "*_" * 20000, "a long line": "a" * 200_000,
                "many fences": "```\n" * 5000, "many tags": "<details>" * 5000, "nul bytes": "a\x00b\x00",
                "empty": "", "only whitespace": " \n\t\n", "crlf": "# a\r\n\r\n```\r\nx\r\n```\r\n"}
        for name, body in deep.items():
            with self.subTest(markdown=name):
                self.write_lesson("sd-01-001", body=body)
                self.write_readme(body)
                self.assertIsInstance(self.problems(), list)

    def test_a_readme_that_is_a_directory_is_reported_not_raised(self) -> None:
        (self.store / "README.md").unlink()
        (self.store / "README.md").mkdir()
        self.assertProblem("README.md: is missing")

    def test_odd_links_and_paths_in_lesson_md_and_readme_are_reported_not_raised(self) -> None:
        destinations = ["a" * 300 + ".md", "x/" + "b" * 300 + ".svg", "%00", "a%00b.md", "..", "../..", "/", "//",
                        "http://[", "mailto:", "#", "?x", "<>", " ", "\\"]
        for destination in destinations:
            with self.subTest(destination=destination):
                self.write_lesson("sd-01-001", body=BODY + f"\n[x](<{destination}>) ![y](<{destination}>)\n"
                                  f'<a href="{destination}">z</a> <img src="{destination}" srcset="{destination} 1x">\n')
                self.write_readme(README + f"\n[x](<{destination}>)\n")
                self.assertIsInstance(self.problems(), list)


class SourceMapRuleTests(StoreCase):
    """A hand-edited source-map.json that is wrong is a problem to report, not a traceback."""

    def test_a_source_map_that_cannot_be_read_is_reported_not_raised(self) -> None:
        cases = {"invalid json": b"{", "invalid utf-8": b"\xff\xfe{}", "empty": b"", "a list": b"[]",
                 "a string": b'"x"', "null": b"null", "no categories": b"{}",
                 "categories is an object": b'{"categories": {}}', "categories is null": b'{"categories": null}'}
        for name, content in cases.items():
            with self.subTest(source_map=name):
                self.source_map.write_bytes(content)
                self.assertProblem("source map: ")

    def test_a_missing_source_map_is_reported_not_raised(self) -> None:
        self.source_map.unlink()
        self.assertProblem("source map: cannot be read")

    def test_a_malformed_category_or_lesson_entry_is_reported_not_raised(self) -> None:
        good = source_entry()
        cases = {"a category that is not an object": [1], "a category with no lessons": [{"id": "sd-01"}],
                 "lessons that are not a list": [{"lessons": {}}], "a lesson that is not an object": [{"lessons": [5]}],
                 "a lesson without an id": [{"lessons": [{"title_vi": "x"}]}],
                 "an id that is null": [{"lessons": [{"id": None}]}], "an id that is a number": [{"lessons": [{"id": 5}]}],
                 "an id that is a list": [{"lessons": [{"id": ["sd-01-001"]}]}],
                 "a lesson listed twice": [{"lessons": [good, good]}],
                 "a lesson listed in two categories": [{"lessons": [good]}, {"lessons": [good]}]}
        for name, categories in cases.items():
            with self.subTest(entry=name):
                self.source_map.write_text(json.dumps({**PIN, "categories": categories}), encoding="utf-8")
                self.assertProblem("source map: ")

    def test_the_rest_of_the_store_is_still_checked_when_the_source_map_is_malformed(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n```\nopen\n")
        self.source_map.write_text("{", encoding="utf-8")
        found = self.problems()
        self.assertTrue(any(line.startswith("source map: ") for line in found), found)
        self.assertTrue(any("unclosed code fence" in line for line in found), found)

    def test_a_good_source_map_with_two_categories_is_fine(self) -> None:
        data = {**PIN, "categories": [{"id": "a", "lessons": [source_entry()]}, {"id": "b", "lessons": []}]}
        self.source_map.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertEqual([], self.problems())


class ReadmeRuleTests(StoreCase):
    def test_a_lesson_missing_from_the_readme_is_reported(self) -> None:
        self.write_readme("# Kho\n")
        self.assertProblem("does not link lessons/sd-01-001/lesson.md")

    def three_lessons(self) -> None:
        titles = {"sd-01-001": "Bài một", "sd-01-002": "Bài hai", "sd-01-003": "Bài ba"}
        self.write_source_map({lesson_id: (title, SNAPSHOT) for lesson_id, title in titles.items()})
        for lesson_id, title in titles.items():
            self.write_lesson(lesson_id, meta=self.meta(id=lesson_id, title_vi=title))

    def row(self, lesson_id: str) -> str:
        return f"| [{lesson_id}](lessons/{lesson_id}/lesson.md) | Bài |\n"

    def readme_of(self, *rows: str) -> str:
        return "# Kho\n\n| ID | Bài |\n|---|---|\n" + "".join(rows)

    def test_lessons_listed_in_source_order_are_accepted(self) -> None:
        self.three_lessons()
        self.write_readme(self.readme_of(*(self.row(f"sd-01-00{n}") for n in (1, 2, 3))))
        self.assertEqual([], self.problems())

    def test_lessons_listed_out_of_source_order_are_reported(self) -> None:
        self.three_lessons()
        for order in ((2, 1, 3), (1, 3, 2), (3, 2, 1)):
            with self.subTest(order=order):
                self.write_readme(self.readme_of(*(self.row(f"sd-01-00{n}") for n in order)))
                self.assertProblem("lists the lessons out of source order")

    def test_source_order_holds_across_markdown_html_and_reference_links(self) -> None:
        self.three_lessons()
        self.write_readme(self.readme_of(
            '| <a href="lessons/sd-01-002/lesson.md">sd-01-002</a> | Bài |\n', "| [sd-01-001][one] | Bài |\n",
            self.row("sd-01-003")) + "\n[one]: lessons/sd-01-001/lesson.md\n")
        self.assertProblem("lists the lessons out of source order")
        self.write_readme(self.readme_of("| [sd-01-001][one] | Bài |\n",
                                         '| <a href="lessons/sd-01-002/lesson.md">sd-01-002</a> | Bài |\n',
                                         self.row("sd-01-003")) + "\n[one]: lessons/sd-01-001/lesson.md\n")
        self.assertEqual([], self.problems())

    def test_a_lesson_linked_twice_counts_where_it_is_first_linked(self) -> None:
        self.three_lessons()
        self.write_readme(self.readme_of(*(self.row(f"sd-01-00{n}") for n in (1, 2, 3))) + "\n[lại](lessons/sd-01-001/lesson.md#a)\n")
        self.assertEqual([], self.problems())

    def test_a_missing_lesson_is_reported_as_missing_not_as_out_of_order(self) -> None:
        self.three_lessons()
        self.write_readme(self.readme_of(self.row("sd-01-001"), self.row("sd-01-003")))
        found = self.problems()
        self.assertTrue(any("does not link lessons/sd-01-002/lesson.md" in line for line in found), found)
        self.assertFalse(any("out of source order" in line for line in found), found)

    def test_a_readme_row_left_behind_for_a_deleted_lesson_is_reported(self) -> None:
        self.write_readme(README + "| [sd-01-009](lessons/sd-01-009/lesson.md) | Bài đã xóa |\n")
        self.assertProblem("relative link 'lessons/sd-01-009/lesson.md' does not resolve")
        self.write_readme(README + "[x][ref]\n\n[ref]: lessons/sd-01-009/lesson.md#phan-1\n")
        self.assertProblem("relative link 'lessons/sd-01-009/lesson.md#phan-1' does not resolve")
        self.write_readme(README + '<a href="lessons/sd-01-009/lesson.md">x</a>\n')
        self.assertProblem("'lessons/sd-01-009/lesson.md' does not resolve")

    def test_readme_links_that_are_not_relative_paths_are_not_looked_up(self) -> None:
        self.write_readme(README + "[web](https://example.com/x) [mail](mailto:a@b.c) [top](#kho)\n"
                          "[again](lessons/sd-01-001/lesson.md#phan-1)\n")
        self.assertEqual([], self.problems())

    def test_the_store_holds_only_the_readme_and_the_lessons_directory(self) -> None:
        for name in ("copied-source.png", "notes.md", ".DS_Store", "figure.svg"):
            with self.subTest(file=name):
                (self.store / name).write_bytes(b"x")
                self.assertProblem(f"{name}: is not allowed in the store")
                (self.store / name).unlink()
        (self.store / "images").mkdir()
        self.assertProblem("images: is not allowed in the store")

    def test_lessons_holds_only_lesson_directories(self) -> None:
        (self.store / "lessons" / "copied-source.png").write_bytes(b"x")
        self.assertProblem("lessons: copied-source.png is not a lesson directory")

    def test_raw_html_outside_the_allow_list_in_the_readme_is_reported(self) -> None:
        for name, html in {"a table": "<table><tr><td>drafted</td></tr></table>", "a div": "<div>drafted</div>",
                           "a closing tag": "</table>", "a span": "<span>drafted</span>"}.items():
            with self.subTest(html=name):
                self.write_readme(README + "\n" + html + "\n")
                self.assertProblem("README.md: uses <")

    def test_the_allowed_raw_html_in_the_readme_is_fine(self) -> None:
        self.write_readme(README + '\n<details><summary>Thêm</summary>\n\nchữ<br/>\n\n</details>\n'
                          '<a href="lessons/sd-01-001/lesson.md">x</a>\n')
        self.assertEqual([], self.problems())

    def test_the_readme_embeds_no_image(self) -> None:
        (self.store / "copied-source.png").write_bytes(b"x")
        (self.store / "figure.svg").write_text("<svg/>", encoding="utf-8")
        forms = {"inline png": "![source](copied-source.png)", "inline svg": "![f](figure.svg)",
                 "reference": "![f][i]\n\n[i]: figure.svg", "html img": '<img src="figure.svg" alt="f">',
                 "html srcset": '<img srcset="figure.svg 1x" alt="f">', "html img without a source": "<img alt='f'>"}
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_readme(README + "\n" + form + "\n")
                self.assertProblem("README.md: embeds the image")

    def test_a_readme_may_link_to_an_image_without_embedding_it(self) -> None:
        (self.store / "figure.svg").write_text("<svg/>", encoding="utf-8")
        self.write_readme(README + "\n[hình](figure.svg)\n")
        self.assertFalse(any("embeds the image" in line for line in self.problems()), self.problems())

    def test_a_link_that_climbs_out_of_the_store_is_reported(self) -> None:
        outside = self.root / "exists.md"
        outside.write_text("x", encoding="utf-8")
        self.write_lesson("sd-01-001", body=BODY + "\n[x](../../../exists.md)\n")
        self.assertProblem("relative link '../../../exists.md' does not resolve")
        self.write_readme(README + "\n[x](../exists.md)\n")
        self.assertProblem("README.md: relative link '../exists.md' does not resolve")

    def test_a_link_that_climbs_far_out_of_the_store_is_reported_even_if_the_file_exists(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[x](" + "../" * 40 + "etc/hostname)\n")
        self.assertProblem("does not resolve")

    def test_a_link_that_climbs_and_comes_back_into_the_store_is_fine(self) -> None:
        self.write_lesson("sd-01-001", body=BODY + "\n[x](../../lessons/sd-01-001/lesson.yaml)\n")
        self.write_readme(README + "\n[x](lessons/../README.md)\n")
        self.assertEqual([], self.problems())

    def test_a_root_relative_readme_link_is_reported(self) -> None:
        (self.root / "exists.md").write_text("x", encoding="utf-8")
        for destination in (self.root / "exists.md", self.store / "lessons" / "sd-01-001" / "lesson.md"):
            with self.subTest(destination=str(destination)):
                self.write_readme(README + f"\n[x]({destination})\n")
                self.assertProblem("README.md: relative link")

    def test_a_missing_readme_is_reported(self) -> None:
        (self.store / "README.md").unlink()
        self.assertProblem("README.md: is missing")

    def test_a_status_word_in_a_readme_row_is_reported(self) -> None:
        row = "| [sd-01-001](lessons/sd-01-001/lesson.md) | Bài một | drafted |\n"
        self.write_readme("# Kho\n\n| ID | Bài | Trạng thái |\n|---|---|---|\n" + row)
        self.assertProblem("repeats a lesson status")

    def test_a_formatted_or_capitalised_status_in_a_readme_row_is_reported(self) -> None:
        forms = {"bold": "**approved**", "code": "`drafted`", "capital": "Approved", "html": "<b>planned</b>",
                 "trailing dot": "drafted.", "emphasis": "_drafted_", "link": "[drafted](https://example.com)",
                 "bold link": "[**approved**](lessons/sd-01-001/lesson.md)", "reference link": "[planned][s]",
                 "entity": "&#100;rafted", "image alt": "![x](a.svg) drafted",
                 "strikethrough": "~~drafted~~", "escaped asterisks": "\\*approved\\*"}
        for name, cell in forms.items():
            with self.subTest(form=name):
                row = f"| [sd-01-001](lessons/sd-01-001/lesson.md) | Bài một | {cell} |\n"
                self.write_readme("# Kho\n\n| ID | Bài | Ghi chú |\n|---|---|---|\n" + row
                                  + "\n[s]: https://example.com\n")
                self.assertProblem("repeats a lesson status")

    def test_a_status_in_a_row_whose_lesson_link_is_a_reference_is_reported(self) -> None:
        row = "| [sd-01-001][one] | Bài một | drafted |\n\n[one]: lessons/sd-01-001/lesson.md\n"
        self.write_readme("# Kho\n\n| ID | Bài | Ghi chú |\n|---|---|---|\n" + row)
        found = self.problems()
        self.assertTrue(any("repeats a lesson status" in line for line in found), found)
        self.assertFalse(any("does not link" in line for line in found), found)

    def test_an_html_anchor_whose_title_mentions_the_path_is_not_a_readme_link(self) -> None:
        path = "lessons/sd-01-001/lesson.md"
        self.write_readme(f"# Kho\n\n<a title='href=\"{path}\"'>bài một</a>\n")
        self.assertProblem("does not link lessons/sd-01-001/lesson.md")

    def test_a_table_without_outer_pipes_or_with_an_indented_row_is_still_inspected(self) -> None:
        link = "[sd-01-001](lessons/sd-01-001/lesson.md)"
        forms = {"no outer pipes": f"ID | Bài | Ghi chú\n--- | --- | ---\n{link} | Bài một | drafted",
                 "indented rows": f"  | ID | Bài | Ghi chú |\n  |---|---|---|\n  | {link} | Bài một | drafted |"}
        for name, table in forms.items():
            with self.subTest(table=name):
                self.write_readme(f"# Kho\n\n{table}\n")
                self.assertProblem("repeats a lesson status")

    def test_a_table_shown_inside_a_code_block_is_not_a_readme_table(self) -> None:
        self.write_readme(README + "\n```\n| ID | Ghi chú |\n|---|---|\n| sd-01-001 | drafted |\n```\n")
        self.assertEqual([], self.problems())

    def test_a_readme_link_with_a_fragment_a_query_or_encoding_still_links_the_lesson(self) -> None:
        forms = {"fragment": "lessons/sd-01-001/lesson.md#vi-du", "query": "lessons/sd-01-001/lesson.md?x=1",
                 "encoded": "lessons/sd%2D01%2D001/lesson.md"}
        for name, target in forms.items():
            with self.subTest(link=name):
                self.write_readme(f"# Kho\n\n[bài một]({target})\n")
                self.assertEqual([], self.problems())

    def test_a_status_word_inside_a_longer_cell_is_a_status(self) -> None:
        for cell in ["Bài đã drafted xong", "Trạng thái: drafted", "drafted!", "(approved)", "status=planned", "[drafted]",
                     "đang PLANNED", "Approved/Drafted", "_drafted_", "\\_approved\\_", "drafted, approved", "tiếng\u00a0drafted"]:
            with self.subTest(cell=cell):
                row = f"| [sd-01-001](lessons/sd-01-001/lesson.md) | {cell} |\n"
                self.write_readme("# Kho\n\n| ID | Bài |\n|---|---|\n" + row)
                self.assertProblem("repeats a lesson status")

    def test_a_word_that_merely_contains_a_status_word_is_not_a_status(self) -> None:
        for cell in ["undrafted", "redrafted", "disapproved", "approvedly", "planned2", "2planned", "unplanned",
                     "overdrafted", "Bài về kế hoạch", "approval", "drafting", "plan"]:
            with self.subTest(cell=cell):
                row = f"| [sd-01-001](lessons/sd-01-001/lesson.md) | {cell} |\n"
                self.write_readme("# Kho\n\n| ID | Bài |\n|---|---|\n" + row)
                self.assertEqual([], self.problems())

    def test_a_status_word_outside_a_table_is_not_checked(self) -> None:
        self.write_readme(README + "\nMọi bài ở trạng thái drafted hoặc approved được ghi trong lesson.yaml.\n")
        self.assertEqual([], self.problems())

    def test_a_readme_path_in_a_comment_a_code_block_or_prose_is_not_a_link(self) -> None:
        path = "lessons/sd-01-001/lesson.md"
        forms = {"html comment": f"<!-- [x]({path}) -->", "code block": f"```\n[x]({path})\n```",
                 "plain prose": f"Xem {path} nhé."}
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_readme(f"# Kho\n\n{form}\n")
                self.assertProblem("does not link lessons/sd-01-001/lesson.md")

    def test_a_readme_link_as_an_html_anchor_or_a_reference_or_with_dot_slash_counts(self) -> None:
        path = "lessons/sd-01-001/lesson.md"
        forms = {"html anchor": f'<a href="{path}">bài một</a>', "reference": f"[bài một][s]\n\n[s]: {path}",
                 "dot slash": f"[bài một](./{path})"}
        for name, form in forms.items():
            with self.subTest(form=name):
                self.write_readme(f"# Kho\n\n{form}\n")
                self.assertEqual([], self.problems())


class CommandLineTests(StoreCase):
    def run_main(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check.main(["--store", str(self.store), "--source-map", str(self.source_map)])
        return code, out.getvalue()

    def test_a_clean_store_exits_zero_and_says_how_many_lessons(self) -> None:
        code, output = self.run_main()
        self.assertEqual(0, code)
        self.assertIn("1 lesson(s), 0 problem(s)", output)

    def test_a_broken_store_exits_one_and_prints_the_problem(self) -> None:
        self.write_lesson("sd-01-001", meta=self.meta(content_status="done"))
        code, output = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("sd-01-001: content_status", output)


if __name__ == "__main__":
    unittest.main()
