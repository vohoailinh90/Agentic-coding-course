"""scripts/genai_check.py: the Generative AI slide store rules, on fixtures and on the real store."""
from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from scripts import genai_check as check

REAL_STORE = Path(__file__).resolve().parent.parent / "genai-for-beginners" / "vi"
SOURCE_URL = "https://github.com/microsoft/generative-ai-for-beginners/blob/abc/01-introduction-to-genai/README.md"
LESSON = ("# AI tạo sinh\n\n## Từ viết tắt\n\n- **AI** (Artificial Intelligence) — trí tuệ nhân tạo.\n\n"
          "## Ý chính\n\nNội dung.\n\n## Nhìn hình trả lời\n\nCâu hỏi?\n\n"
          f"## Nguồn đối chiếu\n\n- [Bài gốc]({SOURCE_URL})\n")
# ga-01: the first concept's signature kind is LAYOUT_KINDS[1 % 12] = flow
LAYOUTS = ["one-highlighted-sentence", "card-grid", "flow", "two-column-comparison", "layers", "numbered-rows",
           "lookup-table", "timeline", "card-grid", "lookup-table"]
DONE = {"id": "ga-01", "status": "done", "owner": "claude/genai-slides-w1", "session": "session_x",
        "claimed_at": "2026-10-20T09:00:00Z", "done_at": "2026-10-20T12:00:00Z",
        "moda_canvas": "cvs_" + "A" * 24, "moda_url": "https://moda.app/canvas/abc", "slide_count": 10,
        "size": "1920x1080", "exports": "pending", "review": "passed",
        "layouts": {"slides": LAYOUTS, "first_concept": 3}}
BOARD = [{"range": "ga-01..ga-02", "branch": "claude/genai-slides-w1", "status": "assigned"}]


def write_pptx(path: Path, slides: int, badged: int) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("ppt/presentation.xml", "<p:presentation/>")
        for number in range(1, slides + 1):
            mark = "moda-export-watermark" if number <= badged else "plain"
            archive.writestr(f"ppt/slides/slide{number}.xml", f"<p:sld>{mark}</p:sld>")


class StoreCase(unittest.TestCase):
    """A two-lesson store in a temp directory; each test breaks one thing."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Path(tmp.name)
        lessons = [{"id": f"ga-0{n}", "number": n, "title_vi": f"Bài {n}", "source_url": SOURCE_URL}
                   for n in (1, 2)]
        (self.store / "source-map.json").write_text(json.dumps({"lessons": lessons}), encoding="utf-8")
        self.write_board(BOARD)
        self.folder = self.store / "lessons" / "ga-01"
        self.folder.mkdir(parents=True)
        self.write_record(DONE)
        (self.folder / "lesson.md").write_text(LESSON, encoding="utf-8")

    def write_board(self, board: object) -> None:
        (self.store / "assignments.yaml").write_text(yaml.safe_dump(board), encoding="utf-8")

    def write_record(self, record: dict) -> None:
        (self.folder / "deck.yaml").write_text(yaml.safe_dump(record, allow_unicode=True), encoding="utf-8")

    def done(self, **changes: object) -> dict:
        record = copy.deepcopy(DONE)
        record.update(changes)
        return record

    def problems(self) -> list[str]:
        return check.check(self.store)

    def assertProblem(self, fragment: str) -> None:
        problems = self.problems()
        self.assertTrue(any(fragment in problem for problem in problems), f"{fragment!r} not in {problems}")

    def test_fixture_passes(self) -> None:
        self.assertEqual(self.problems(), [])

    def test_doing_record_without_lesson_passes(self) -> None:
        (self.folder / "lesson.md").unlink()
        self.write_record({"id": "ga-01", "status": "doing", "owner": "claude/genai-slides-w1",
                           "session": "session_x", "claimed_at": "2026-10-20T09:00:00Z"})
        self.assertEqual(self.problems(), [])

    def test_done_needs_lesson(self) -> None:
        (self.folder / "lesson.md").unlink()
        self.assertProblem("lesson.md is missing")

    def test_review_must_have_passed(self) -> None:
        self.write_record(self.done(review="pending"))
        self.assertProblem("review must be passed")

    def test_slide_count_range(self) -> None:
        self.write_record(self.done(slide_count=9, layouts={"slides": LAYOUTS[:9], "first_concept": 3}))
        self.assertProblem("slide_count must be between 10 and 12")

    def test_adjacent_kinds(self) -> None:
        slides = LAYOUTS[:]
        slides[4] = slides[3]
        self.write_record(self.done(layouts={"slides": slides, "first_concept": 3}))
        self.assertProblem("same kind on adjacent slides 4 and 5")

    def test_signature_layout_needs_named_fallback(self) -> None:
        slides = LAYOUTS[:]
        slides[2] = "lookup-table"  # flow, two-column-comparison, 2x2-matrix passed over without a reason
        slides[6] = "timeline"
        slides[7] = "flow"
        self.write_record(self.done(layouts={"slides": slides, "first_concept": 3}))
        self.assertProblem("cannot must name flow, two-column-comparison, 2x2-matrix")
        reasons = {"flow": "a", "two-column-comparison": "b", "2x2-matrix": "c"}
        self.write_record(self.done(layouts={"slides": slides, "first_concept": 3, "cannot": reasons}))
        self.assertEqual(self.problems(), [])

    def test_too_few_kinds(self) -> None:
        slides = ["flow", "card-grid"] * 5
        self.write_record(self.done(layouts={"slides": slides, "first_concept": 3}))
        self.assertProblem("a deck uses at least 5")

    def test_lesson_sections(self) -> None:
        (self.folder / "lesson.md").write_text(LESSON.replace("## Từ viết tắt", "## Mở đầu"), encoding="utf-8")
        self.assertProblem("first section must be `## Từ viết tắt`")
        (self.folder / "lesson.md").write_text(LESSON.replace(SOURCE_URL, "https://example.com"), encoding="utf-8")
        self.assertProblem("must link the pinned source")

    def test_heading_inside_code_fence_is_not_a_section(self) -> None:
        text = LESSON.replace("## Ý chính", "```text\n## Nhìn hình trả lời\n```\n\n## Ý chính")
        text = text.replace("## Nhìn hình trả lời\n\nCâu hỏi?", "## Hỏi\n\nCâu hỏi?")
        (self.folder / "lesson.md").write_text(text, encoding="utf-8")
        self.assertProblem("`## Nhìn hình trả lời` is missing")

    def test_stray_file(self) -> None:
        (self.folder / "01.png").write_bytes(b"x")
        self.assertProblem("01.png does not belong")

    def test_pptx_only_when_badged(self) -> None:
        write_pptx(self.folder / "ga-01.pptx", 10, 10)
        self.assertProblem("does not say exports: badged")
        self.write_record(self.done(exports="badged"))
        self.assertEqual(self.problems(), [])

    def test_badged_pptx_checked(self) -> None:
        self.write_record(self.done(exports="badged"))
        self.assertProblem("ga-01.pptx is missing")
        write_pptx(self.folder / "ga-01.pptx", 9, 9)
        self.assertProblem("has 9 slides")
        write_pptx(self.folder / "ga-01.pptx", 10, 8)
        self.assertProblem("2 slides lack the moda.app badge")
        (self.folder / "ga-01.pptx").write_bytes(b"not a zip")
        self.assertProblem("not a ZIP archive")

    def test_board_overlap_and_unknown(self) -> None:
        self.write_board(BOARD + [{"range": "ga-02..ga-03", "branch": "claude/other", "status": "assigned"}])
        self.assertProblem("ga-02 is in rows 1 and 2")
        self.assertProblem("ga-03 is not in source-map.json")

    def test_folder_not_in_source_map(self) -> None:
        shutil.copytree(self.folder, self.store / "lessons" / "ga-09")
        self.assertProblem("lessons/ga-09: not a lesson of source-map.json")


class ClaimCase(unittest.TestCase):
    def test_claim_rules(self) -> None:
        branch = "claude/genai-slides-w1"
        self.assertIsNone(check.claim_problem("ga-01", branch, BOARD, []))
        self.assertIn("assigned to claude/genai-slides-w1", check.claim_problem("ga-01", "claude/other", BOARD, []))
        self.assertIn("no row", check.claim_problem("ga-05", branch, BOARD, []))
        held = [("origin/claude/other", {"owner": "claude/other", "status": "doing"})]
        self.assertIn("already held by claude/other", check.claim_problem("ga-01", branch, BOARD, held))
        mine = [("origin/" + branch, {"owner": branch, "status": "doing"})]
        self.assertIsNone(check.claim_problem("ga-01", branch, BOARD, mine))
        done = [{**BOARD[0], "status": "done"}]
        self.assertIn("takes no more work", check.claim_problem("ga-01", branch, done, []))

    def test_expand_range(self) -> None:
        self.assertEqual(check.expand_range("ga-08..ga-10"), ["ga-08", "ga-09", "ga-10"])
        self.assertIsNone(check.expand_range("ga-10..ga-08"))
        self.assertIsNone(check.expand_range("ga-1..ga-2"))


class RealStoreCase(unittest.TestCase):
    def test_real_store_passes(self) -> None:
        self.assertEqual(check.check(REAL_STORE), [])

    def test_source_map_has_21_lessons_and_board_covers_them(self) -> None:
        source = check.load_source_map(REAL_STORE)
        self.assertEqual(list(source), [f"ga-{n:02d}" for n in range(1, 22)])
        board = check.load_board(REAL_STORE)
        covered = [lesson_id for row in board for lesson_id in check.expand_range(row["range"])]
        self.assertEqual(sorted(covered), list(source))


if __name__ == "__main__":
    unittest.main()
