"""The pull-request loop (CLAUDE.md, *Pull request lifecycle*) is prose, so what a test can pin is that every piece of
it still exists and still points at the others: the mandate, the protocol sections it cites, and the wording that keeps
the loop from contradicting docs/claude-to-codex.md.

Nothing here judges the rule; it stops the rule being edited out of one place while the other place goes on citing it.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = ROOT / "CLAUDE.md"
PROTOCOL = ROOT / "docs" / "claude-to-codex.md"
HEADING = "## Pull request lifecycle"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def lifecycle() -> str:
    text = read(CLAUDE_MD)
    start = text.find(HEADING)
    if start < 0:
        return ""
    rest = re.search(r"^## ", text[start + len(HEADING):], re.MULTILINE)
    return text[start:start + len(HEADING) + rest.start()] if rest else text[start:]


class PullRequestLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.section = lifecycle()
        self.assertTrue(self.section, f"CLAUDE.md lost its {HEADING!r} section")

    def test_the_mandate_covers_every_tier(self) -> None:
        self.assertIn("at any tier", self.section)
        self.assertIn("T0 typo fix included", self.section)

    def test_the_loop_has_all_six_steps_in_order(self) -> None:
        self.assertEqual(re.findall(r"^(\d)\. \*\*", self.section, re.MULTILINE), ["1", "2", "3", "4", "5", "6"])
        markers = ("Open, then Codex review", "Validate every finding", "Fix, then have the new head reviewed",
                   "Stop when the review is clean", "Merge it yourself", "Then continue")
        positions = [self.section.find(m) for m in markers]
        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))

    def test_an_unreviewed_pr_is_never_merged_and_the_exits_remain(self) -> None:
        for phrase in ("is never merged", "BLOCKED", "do not merge", "genuine blocker (§20)",
                       "once per head SHA", "reworded or moved", "rules, not script gates",
                       "other than a P2/P3 whose recorded rejection stands"):
            self.assertIn(phrase, self.section)

    def test_a_prose_only_fix_needs_no_regression_test(self) -> None:
        self.assertIn("with a regression test where the defect has testable behavior", self.section)

    def test_no_document_still_caps_review_rounds(self) -> None:
        """The handoff and ADR 010 once said at most two review rounds; both must say the cap is gone."""
        for rel in ("docs/handoff.md", "docs/decisions/010-claude-writes-codex-reviews.md"):
            with self.subTest(path=rel):
                text = read(ROOT / rel).replace("\n", " ")
                self.assertNotIn("at most two review rounds", text)
                self.assertNotIn("(at most two rounds per batch)", text)
                self.assertIn("2026-10-12", text)

    def test_the_next_task_is_never_invented(self) -> None:
        self.assertIn("never invent work", self.section)
        self.assertIn("the user explicitly asked for", self.section)
        self.assertIn("skip it rather than stack", self.section)

    def test_the_trigger_string_ban_keeps_the_intentional_comment_exception(self) -> None:
        self.assertIn("except the intentional trigger comments the protocol authorizes", self.section)
        self.assertIn("each review request of steps 1 and 3, a security review", self.section)

    def test_every_protocol_section_it_cites_exists(self) -> None:
        protocol = read(PROTOCOL)
        cited = {int(n) for n in re.findall(r"§(\d+)", self.section)}
        self.assertTrue({3, 11, 13, 14, 16, 17, 18, 20} <= cited, f"the section stopped citing: {cited}")
        for number in cited:
            self.assertRegex(protocol, rf"(?m)^## {number}\. ",
                             f"CLAUDE.md cites §{number}; the protocol has no such section")

    def test_the_protocol_states_no_review_cap_and_the_loop(self) -> None:
        protocol = read(PROTOCOL)
        self.assertRegex(protocol, r"(?m)^- Maximum review rounds per PR: none\b")
        no_limit = protocol[protocol.index("### No review limit"):protocol.index("## 17. ")]
        for phrase in ("A disagreement.", "A genuine blocker", "substantially the same issue",
                       "Never request a review command for a head that command already reviewed",
                       "When no code change is pending there is no new head to review"):
            self.assertIn(phrase, no_limit)
        sec20 = protocol[protocol.index("## 20. "):protocol.index("## 21. ")]
        loop = sec20[sec20.index("### The loop every PR goes through"):]
        self.assertIn("a rejected P0/P1 is open until", loop)
        self.assertIn("every review command the work requires", loop)
        self.assertIn("A fix pushed after the last review is unreviewed", loop)

    def test_section_11_applies_the_same_head_rule_per_review_command(self) -> None:
        protocol = read(PROTOCOL)
        gate = protocol[protocol.index("## 11. "):protocol.index("## 12. ")]
        self.assertIn("for the review command being requested", gate)
        self.assertIn("a required security review follows the standard review", gate)
        self.assertIn("must not request the same review command again for a PR head SHA it already reviewed", gate)
        self.assertNotIn("repeated reviews for the same PR head SHA", gate)

    def test_the_delegation_section_points_at_the_lifecycle(self) -> None:
        text = read(CLAUDE_MD)
        delegation = text[text.index("## Delegating to Codex Cloud"):text.index(HEADING)]
        self.assertIn("*Pull request lifecycle*", delegation)

    def test_nothing_speaks_of_a_cap_of_three(self) -> None:
        for path in (CLAUDE_MD, PROTOCOL):
            text = read(path).replace("\n", " ")
            for phrase in ("last allowed review", "cap permitting", "Reaching the review limit",
                           "while the cap allows"):
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
