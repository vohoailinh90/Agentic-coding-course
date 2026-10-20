"""scripts/agents_check.py: the AI Agents slide store rules, on fixtures and on the real store."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import yaml

from scripts import agents_check as check

REAL_STORE = Path(__file__).resolve().parent.parent / "ai-agents-for-beginners" / "vi"
SOURCE_URL = "https://github.com/microsoft/ai-agents-for-beginners/blob/abc/01-intro-to-ai-agents/README.md"
LESSON = ("# AI agent\n\n## Từ viết tắt\n\n- **AI** (Artificial Intelligence) — trí tuệ nhân tạo.\n\n"
          "## Ý chính\n\nNội dung.\n\n## Nhìn hình trả lời\n\nCâu hỏi?\n\n<details><summary>Đáp án</summary>Đáp.</details>\n\n"
          f"## Nguồn đối chiếu\n\n- [Bài gốc]({SOURCE_URL})\n\nDựa trên bài 01 của microsoft/ai-agents-for-beginners "
          "(MIT License, © Microsoft Corporation).\n")
# ag-01: the first concept's signature kind is LAYOUT_KINDS[1 % 12] = flow
LAYOUTS = ["one-highlighted-sentence", "card-grid", "flow", "two-column-comparison", "layers", "numbered-rows",
           "lookup-table", "timeline", "card-grid", "lookup-table"]
DONE = {"id": "ag-01", "status": "done", "owner": "claude/agents-slides-w1", "session": "session_x",
        "claimed_at": "2026-10-20T09:00:00Z", "done_at": "2026-10-20T12:00:00Z",
        "moda_canvas": "cvs_" + "A" * 24, "moda_url": "https://moda.app/canvas/abc", "slide_count": 10,
        "size": "1920x1080", "exports": "pending", "review": "passed",
        "layouts": {"slides": LAYOUTS, "first_concept": 3}}
BOARD = [{"range": "ag-01..ag-02", "branch": "claude/agents-slides-w1", "status": "assigned"}]


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
        lessons = [{"id": f"ag-0{n}", "number": n, "title_vi": f"Bài {n}", "source_url": SOURCE_URL}
                   for n in (1, 2)]
        (self.store / "source-map.json").write_text(json.dumps({"lessons": lessons}), encoding="utf-8")
        self.write_board(BOARD)
        self.folder = self.store / "lessons" / "ag-01"
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

    def test_doing_lesson_may_be_a_draft(self) -> None:
        self.write_record({"id": "ag-01", "status": "doing", "owner": "claude/agents-slides-w1",
                           "session": "session_x", "claimed_at": "2026-10-20T09:00:00Z"})
        (self.folder / "lesson.md").write_text("bản nháp, chưa có mục nào\n", encoding="utf-8")
        self.assertEqual(self.problems(), [])
        (self.folder / "01.png").write_bytes(b"x")
        self.assertProblem("01.png does not belong")

    def test_lesson_must_credit_the_source(self) -> None:
        (self.folder / "lesson.md").write_text(LESSON.replace("MIT License", "giấy phép"), encoding="utf-8")
        self.assertProblem("must credit the source")

    def test_check_section_needs_question_and_answer(self) -> None:
        empty = LESSON.replace("Câu hỏi?\n\n<details><summary>Đáp án</summary>Đáp.</details>\n\n", "\n")
        (self.folder / "lesson.md").write_text(empty, encoding="utf-8")
        self.assertProblem("must hold a question (`?`) and its answer in <details>")
        no_answer = LESSON.replace("<details><summary>Đáp án</summary>Đáp.</details>", "Đáp.")
        (self.folder / "lesson.md").write_text(no_answer, encoding="utf-8")
        self.assertProblem("must hold a question (`?`) and its answer in <details>")
        empty_answer = LESSON.replace("<details><summary>Đáp án</summary>Đáp.</details>",
                                      "<details><summary>Đáp án</summary> </details>")
        (self.folder / "lesson.md").write_text(empty_answer, encoding="utf-8")
        self.assertProblem("must hold a question (`?`) and its answer in <details>")

    def test_lesson_title_must_not_be_empty(self) -> None:
        (self.folder / "lesson.md").write_text(LESSON.replace("# AI agent\n", "# \n", 1), encoding="utf-8")
        self.assertProblem("must start with a `# ` title")

    def test_credit_needs_the_whole_attribution(self) -> None:
        text = LESSON.replace(" (MIT License, © Microsoft Corporation)", " MIT")
        (self.folder / "lesson.md").write_text(text, encoding="utf-8")
        self.assertProblem("must credit the source")
        wrapped = LESSON.replace("(MIT License, © Microsoft Corporation)", "(MIT License, © Microsoft\nCorporation)")
        (self.folder / "lesson.md").write_text(wrapped, encoding="utf-8")
        self.assertEqual(self.problems(), [])

    def test_fence_closes_only_on_a_long_enough_line(self) -> None:
        fenced = "````md\n```\n## Nhìn hình trả lời\n```\n````\n\n"
        text = LESSON.replace("## Ý chính", fenced + "## Ý chính").replace("## Nhìn hình trả lời\n\nCâu", "## Hỏi\n\nCâu")
        (self.folder / "lesson.md").write_text(text, encoding="utf-8")
        self.assertProblem("`## Nhìn hình trả lời` is missing")

    def test_inline_triple_backticks_are_not_a_fence(self) -> None:
        text = LESSON.replace("Nội dung.", "Viết ```x``` trong một dòng.")
        (self.folder / "lesson.md").write_text(text, encoding="utf-8")
        self.assertEqual(self.problems(), [])
        (self.folder / "lesson.md").write_text(LESSON + "\n```python\nprint(1)\n", encoding="utf-8")
        self.assertProblem("leaves a code fence open")

    def test_cannot_names_only_kinds_passed_over(self) -> None:
        self.write_record(self.done(layouts={"slides": LAYOUTS, "first_concept": 3, "cannot": {"timeline": "x"}}))
        self.assertProblem("cannot must name no kind and names timeline")

    def test_first_concept_range(self) -> None:
        self.write_record(self.done(layouts={"slides": LAYOUTS, "first_concept": 10}))
        self.assertProblem("first_concept must be the number of the first concept's slide, from 3 to 9")
        self.write_record(self.done(layouts={"slides": LAYOUTS, "first_concept": 2}))
        self.assertProblem("first_concept must be the number of the first concept's slide, from 3 to 9")

    def test_doing_record_without_lesson_passes(self) -> None:
        (self.folder / "lesson.md").unlink()
        self.write_record({"id": "ag-01", "status": "doing", "owner": "claude/agents-slides-w1",
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
        write_pptx(self.folder / "ag-01.pptx", 10, 10)
        self.assertProblem("does not say exports: badged")
        self.write_record(self.done(exports="badged"))
        self.assertEqual(self.problems(), [])

    def test_badged_pptx_checked(self) -> None:
        self.write_record(self.done(exports="badged"))
        self.assertProblem("ag-01.pptx is missing")
        write_pptx(self.folder / "ag-01.pptx", 9, 9)
        self.assertProblem("has 9 slides")
        write_pptx(self.folder / "ag-01.pptx", 10, 8)
        self.assertProblem("2 slides lack the moda.app badge")
        (self.folder / "ag-01.pptx").write_bytes(b"not a zip")
        self.assertProblem("not a ZIP archive")

    def test_board_overlap_and_unknown(self) -> None:
        self.write_board(BOARD + [{"range": "ag-02..ag-03", "branch": "claude/other", "status": "assigned"}])
        self.assertProblem("ag-02 is in rows 1 and 2")
        self.assertProblem("ag-03 is not in source-map.json")

    def test_folder_not_in_source_map(self) -> None:
        shutil.copytree(self.folder, self.store / "lessons" / "ag-09")
        self.assertProblem("lessons/ag-09: not a lesson of source-map.json")


class ClaimCase(unittest.TestCase):
    def test_claim_rules(self) -> None:
        branch = "claude/agents-slides-w1"
        self.assertIsNone(check.claim_problem("ag-01", branch, BOARD, []))
        self.assertIn("assigned to claude/agents-slides-w1", check.claim_problem("ag-01", "claude/other", BOARD, []))
        self.assertIn("no row", check.claim_problem("ag-05", branch, BOARD, []))
        held = [("origin/claude/other", {"owner": "claude/other", "status": "doing"})]
        self.assertIn("already held by claude/other", check.claim_problem("ag-01", branch, BOARD, held))
        mine = [("origin/" + branch, {"owner": branch, "status": "doing"})]
        self.assertIsNone(check.claim_problem("ag-01", branch, BOARD, mine))
        done = [{**BOARD[0], "status": "done"}]
        self.assertIn("takes no more work", check.claim_problem("ag-01", branch, done, []))

    def test_take_over_yields_doing_never_done(self) -> None:
        branch = "claude/agents-slides-w1"
        doing = [("origin/claude/dead", {"owner": "claude/dead", "status": "doing"})]
        self.assertIn("--take-over", check.claim_problem("ag-01", branch, BOARD, doing))
        self.assertIsNone(check.claim_problem("ag-01", branch, BOARD, doing, take_over=True))
        done = [("origin/claude/dead", {"owner": "claude/dead", "status": "done"})]
        self.assertIn("already done by claude/dead", check.claim_problem("ag-01", branch, BOARD, done, take_over=True))
        unreadable = [("origin/claude/dead", check.parse_held("id: [", "origin/claude/dead"))]
        self.assertIn("only a readable `doing` record",
                      check.claim_problem("ag-01", branch, BOARD, unreadable, take_over=True))

    def test_unreadable_record_holds_its_lesson(self) -> None:
        record = check.parse_held("id: [unclosed", "origin/claude/other")
        self.assertIn("already held by an unreadable deck.yaml on origin/claude/other",
                      check.claim_problem("ag-01", "claude/agents-slides-w1", BOARD, [("origin/claude/other", record)]))

    def test_scope(self) -> None:
        paths = ["ai-agents-for-beginners/vi/lessons/ag-01/deck.yaml", "ai-agents-for-beginners/vi/lessons/ag-03/lesson.md",
                 "ai-agents-for-beginners/vi/assignments.yaml"]
        self.assertEqual(check.scope_problems(paths, ["ag-01", "ag-02"]),
                         ["ai-agents-for-beginners/vi/lessons/ag-03/lesson.md is outside this branch's lesson folders",
                          "ai-agents-for-beginners/vi/assignments.yaml is outside this branch's lesson folders"])

    def test_expand_range(self) -> None:
        self.assertEqual(check.expand_range("ag-08..ag-10"), ["ag-08", "ag-09", "ag-10"])
        self.assertIsNone(check.expand_range("ag-10..ag-08"))
        self.assertIsNone(check.expand_range("ag-1..ag-2"))


GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


class GitFlowCase(unittest.TestCase):
    """claim, status and scope against a real bare remote with two worker clones."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.run_git(self.tmp, "init", "-q", "--bare", "-b", "main", "remote.git")
        seed = self.clone("seed")
        store = seed / check.STORE_REL
        store.mkdir(parents=True)
        lessons = [{"id": f"ag-0{n}", "number": n, "title_vi": f"Bài {n}", "source_url": SOURCE_URL} for n in (1, 2)]
        (store / "source-map.json").write_text(json.dumps({"lessons": lessons}), encoding="utf-8")
        self.board = [{"range": "ag-01..ag-01", "branch": "w1", "status": "assigned"},
                      {"range": "ag-02..ag-02", "branch": "w2", "status": "assigned"}]
        (store / "assignments.yaml").write_text(yaml.safe_dump(self.board), encoding="utf-8")
        self.run_git(seed, "add", "-A")
        self.run_git(seed, "commit", "-q", "-m", "seed")
        self.run_git(seed, "push", "-q", "origin", "main")

    def run_git(self, cwd: Path, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=cwd, env=GIT_ENV, check=True, capture_output=True,
                              text=True).stdout

    def clone(self, name: str, branch: str | None = None) -> Path:
        self.run_git(self.tmp, "clone", "-q", "remote.git", name)
        if branch:
            self.run_git(self.tmp / name, "checkout", "-q", "-b", branch)
        return self.tmp / name

    def tool(self, root: Path, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with mock.patch.object(check, "ROOT", root), mock.patch.object(check, "STORE", root / check.STORE_REL), \
                mock.patch.dict(os.environ, GIT_ENV), contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = check.main(list(argv))
        return code, out.getvalue()

    def push(self, root: Path, branch: str) -> None:
        self.run_git(root, "add", "-A")
        self.run_git(root, "commit", "-q", "-m", "claim")
        self.run_git(root, "push", "-q", "origin", branch)

    def test_claims_never_overlap_and_take_over_follows_the_board(self) -> None:
        w1 = self.clone("w1", "w1")
        self.assertEqual(self.tool(w1, "claim", "ag-01", "--session", "s1")[0], 0)
        self.push(w1, "w1")
        self.assertEqual(self.tool(w1, "claim", "ag-02", "--session", "s1")[0], 1)  # w2's range
        w2 = self.clone("w2", "w2")
        code, out = self.tool(w2, "claim", "ag-01", "--session", "s2")
        self.assertEqual(code, 1)
        self.assertIn("assigned to w1", out)
        code, out = self.tool(w2, "status")
        self.assertIn("ag-01  doing by w1", out)
        # the coordinator moves ag-01 to w2 (w1's session died): a plain claim still yields to the pushed record
        board = [{**self.board[0], "branch": "w2"}, self.board[1]]
        (w2 / check.STORE_REL / "assignments.yaml").write_text(yaml.safe_dump(board), encoding="utf-8")
        code, out = self.tool(w2, "claim", "ag-01", "--session", "s2")
        self.assertEqual(code, 1)
        self.assertIn("already held by w1", out)
        self.assertEqual(self.tool(w2, "claim", "ag-01", "--session", "s2", "--take-over")[0], 0)
        record = yaml.safe_load((w2 / check.STORE_REL / "lessons/ag-01/deck.yaml").read_text(encoding="utf-8"))
        self.assertEqual((record["owner"], record["session"]), ("w2", "s2"))

    def test_status_reports_an_unreadable_record_as_held(self) -> None:
        unreadable = check.parse_held("[: not yaml", "origin/claude/x")
        self.assertEqual(check.lesson_state([("origin/claude/x", unreadable)]),
                         "held by an unreadable deck.yaml on origin/claude/x")
        self.assertEqual(check.lesson_state([]), "free")

    def test_claims_pushed_after_a_clone_are_fetched(self) -> None:
        self.run_git(self.tmp, "clone", "-q", "--single-branch", "remote.git", "late")  # tracks main only
        late = self.tmp / "late"
        w1 = self.clone("w1", "w1")
        self.tool(w1, "claim", "ag-01", "--session", "s1")
        self.push(w1, "w1")
        self.assertIn("ag-01  free", self.tool(late, "--no-fetch", "status")[1])
        self.assertIn("ag-01  doing by w1", self.tool(late, "status")[1])

    def test_scope_flags_shared_files(self) -> None:
        w1 = self.clone("w1", "w1")
        self.tool(w1, "claim", "ag-01", "--session", "s1")
        self.push(w1, "w1")
        code, out = self.tool(w1, "scope")
        self.assertEqual(code, 0, out)
        (w1 / check.STORE_REL / "README.md").write_text("x", encoding="utf-8")
        self.push(w1, "w1")
        code, out = self.tool(w1, "scope")
        self.assertEqual(code, 1)
        self.assertIn("README.md is outside", out)

    def test_scope_ignores_lessons_merged_in_from_main(self) -> None:
        self.run_git(self.tmp / "seed", "push", "-q", "origin", "main:claude/gallant-cannon-hdn047")  # setup still exists
        w1 = self.clone("w1", "w1")
        self.tool(w1, "claim", "ag-01", "--session", "s1")
        self.push(w1, "w1")
        w2 = self.clone("w2", "w2")
        self.tool(w2, "claim", "ag-02", "--session", "s2")
        self.run_git(w2, "add", "-A")
        self.run_git(w2, "commit", "-q", "-m", "claim")
        self.run_git(w2, "push", "-q", "origin", "w2:main")  # w2's range merged into main first
        self.run_git(w1, "fetch", "-q", "origin")
        self.run_git(w1, "merge", "-q", "--no-edit", "origin/main")
        code, out = self.tool(w1, "scope")
        self.assertEqual(code, 0, out)
        self.assertIn("1 changed path(s)", out)

    def test_scope_sees_an_edit_made_in_a_merge_resolution(self) -> None:
        w1 = self.clone("w1", "w1")
        self.tool(w1, "claim", "ag-01", "--session", "s1")
        self.push(w1, "w1")
        main = self.clone("main2")
        (main / "notes.md").write_text("from main", encoding="utf-8")
        self.run_git(main, "add", "-A")
        self.run_git(main, "commit", "-q", "-m", "main moves")
        self.run_git(main, "push", "-q", "origin", "main")
        self.run_git(w1, "fetch", "-q", "origin")
        self.run_git(w1, "merge", "-q", "--no-commit", "origin/main")
        (w1 / "notes.md").write_text("edited while merging", encoding="utf-8")
        self.run_git(w1, "add", "-A")
        self.run_git(w1, "commit", "-q", "--no-edit")
        code, out = self.tool(w1, "scope")
        self.assertEqual(code, 1, out)
        self.assertIn("notes.md is outside", out)

    def test_scope_sees_both_paths_of_a_rename(self) -> None:
        w1 = self.clone("w1", "w1")
        (w1 / "notes.md").write_text("x", encoding="utf-8")
        self.run_git(w1, "add", "-A")
        self.run_git(w1, "commit", "-q", "-m", "notes")
        self.run_git(w1, "push", "-q", "origin", "w1:main")
        self.tool(w1, "claim", "ag-01", "--session", "s1")
        self.run_git(w1, "mv", "notes.md", f"{check.STORE_REL}/lessons/ag-01/notes.md")
        self.push(w1, "w1")
        code, out = self.tool(w1, "scope")
        self.assertEqual(code, 1, out)
        self.assertIn("notes.md is outside", out)

    def test_claim_without_remote_refs_or_git_exits_2(self) -> None:
        bare = self.tmp / "plain"
        shutil.copytree(self.tmp / "seed" / "ai-agents-for-beginners", bare / "ai-agents-for-beginners")
        self.assertEqual(self.tool(bare, "claim", "ag-01", "--session", "s")[0], 2)


class RealStoreCase(unittest.TestCase):
    def test_real_store_passes(self) -> None:
        self.assertEqual(check.check(REAL_STORE), [])

    def test_source_map_has_18_lessons_and_board_covers_them(self) -> None:
        source = check.load_source_map(REAL_STORE)
        self.assertEqual(list(source), [f"ag-{n:02d}" for n in range(1, 19)])
        board = check.load_board(REAL_STORE)
        covered = [lesson_id for row in board for lesson_id in check.expand_range(row["range"])]
        self.assertEqual(sorted(covered), list(source))


if __name__ == "__main__":
    unittest.main()
