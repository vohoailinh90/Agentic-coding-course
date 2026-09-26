from __future__ import annotations

import contextlib
import io
import os
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PROTECT_PATH = ROOT / "scripts" / "protect_branches.py"


def load_module(name: str, path: Path):
    """Load a script from source, never from the bytecode cache.

    Same reason as tests/test_ci_runner_mode.py: a mutation check rewrites the
    file and re-runs within the same second, and cached bytecode validated on
    `(mtime, size)` would hand back the previous version, reading as caught
    when nothing was exercised.
    """
    if not path.is_file():
        raise RuntimeError(f"Unable to load {path}")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)
    return module


protect = load_module("protect_branches", PROTECT_PATH)


class DesiredProtectionTests(unittest.TestCase):
    """What gets written has to be exactly what §20 asks for."""

    def test_it_requires_branches_to_be_up_to_date(self):
        # The "up to date before merging" half. Without `strict`, a branch
        # validated against an older base can still merge, which is the race
        # §20 says no amount of re-checking can close.
        payload = protect.desired_protection(("build",))
        self.assertTrue(payload["required_status_checks"]["strict"])

    def test_it_includes_administrators(self):
        # The "cannot bypass" half. A rule the merging identity is exempt from
        # is not a rule; §20 rejects the repository outright in that case.
        self.assertTrue(protect.desired_protection(("build",))["enforce_admins"])

    def test_it_requires_at_least_one_check(self):
        # `strict` means "up to date with respect to the required checks". With
        # no check required there is nothing to be up to date with, and GitHub
        # lets the merge through.
        payload = protect.desired_protection(("build", "guard"))
        self.assertEqual(payload["required_status_checks"]["contexts"], ["build", "guard"])

    def test_it_does_not_require_human_review(self):
        # Deliberate, and load-bearing. A required approval cannot be supplied
        # without a person, so requiring one makes §20's autonomous merge
        # impossible -- the exact wait §20 exists to remove.
        self.assertIsNone(protect.desired_protection(("build",))["required_pull_request_reviews"])

    def test_it_refuses_force_pushes_and_deletion(self):
        payload = protect.desired_protection(("build",))
        self.assertFalse(payload["allow_force_pushes"])
        self.assertFalse(payload["allow_deletions"])


class ShortfallTests(unittest.TestCase):
    """The §20 verdict, read off what GitHub actually returns."""

    def satisfying(self):
        return {"required_status_checks": {"strict": True, "contexts": ["build"]},
                "enforce_admins": {"enabled": True}}

    def test_a_satisfying_protection_has_no_shortfalls(self):
        self.assertEqual(protect.shortfalls(self.satisfying()), [])

    def test_absent_protection_is_a_shortfall(self):
        self.assertEqual(len(protect.shortfalls(None)), 1)
        self.assertEqual(len(protect.shortfalls({})), 1)

    def test_non_strict_checks_are_caught(self):
        p = self.satisfying()
        p["required_status_checks"]["strict"] = False
        self.assertTrue(any("not strict" in r for r in protect.shortfalls(p)))

    def test_exempt_administrators_are_caught(self):
        # The one that matters most: GitHub nests this as
        # `enforce_admins.enabled`, so a checker reading `enforce_admins`
        # as a plain truthy dict would pass every repository, including the
        # ones where admins are exempt.
        p = self.satisfying()
        p["enforce_admins"] = {"enabled": False}
        self.assertTrue(any("bypass" in r for r in protect.shortfalls(p)))

    def test_strict_with_no_context_is_vacuous_and_reported(self):
        p = self.satisfying()
        p["required_status_checks"]["contexts"] = []
        self.assertTrue(any("vacuous" in r for r in protect.shortfalls(p)))

    def test_the_checks_array_form_counts_as_contexts(self):
        # GitHub returns required checks under `checks` as well as the older
        # `contexts`. Reading only one spelling reports a correctly protected
        # branch as vacuous.
        p = {"required_status_checks": {"strict": True, "contexts": [],
                                        "checks": [{"context": "build", "app_id": None}]},
             "enforce_admins": {"enabled": True}}
        self.assertEqual(protect.shortfalls(p), [])

    def test_what_it_writes_is_what_it_would_accept(self):
        # The payload and the verdict must agree, or --apply reports a gap it
        # just closed, or closes one it still reports as open.
        self.assertEqual(protect.shortfalls(protect.desired_protection(("build",))), [])


class CoverageTests(unittest.TestCase):

    def test_every_unprotected_repository_has_a_required_check_list(self):
        # A repository with no list cannot be protected: `strict` needs a
        # check, and guessing a context that never arrives blocks every pull
        # request in that repository instead.
        expected = {"claude-agent-routing-template", "Excel-to-planner", "office_translator",
                    "Email_Bridge", "Shipping_Inspection", "Customer-tcd-sync"}
        self.assertEqual(set(protect.REQUIRED_CHECKS), expected)
        for repo, contexts in protect.REQUIRED_CHECKS.items():
            with self.subTest(repo=repo):
                self.assertTrue(contexts, f"{repo} has an empty check list")

    def test_the_already_protected_repositories_are_not_overwritten_by_default(self):
        # Their rules were set by hand and this script has never read them.
        # Silently replacing them would be a worse outcome than the gap the
        # report makes visible.
        for repo in protect.ALREADY_PROTECTED:
            with self.subTest(repo=repo):
                self.assertNotIn(repo, protect.REQUIRED_CHECKS)


if __name__ == "__main__":
    unittest.main()


class ContextDriftTests(unittest.TestCase):
    """A branch can satisfy §20 and still be deadlocked."""

    def protection(self, contexts):
        return {"required_status_checks": {"strict": True, "contexts": list(contexts)},
                "enforce_admins": {"enabled": True}}

    def test_a_renamed_check_still_satisfies_section_20(self):
        # Not a bug in `shortfalls` -- the rule really is strict, admin-bound
        # and non-empty. It is why drift needs its own question: folding it
        # into the §20 verdict would make that verdict claim something §20
        # does not say.
        self.assertEqual(protect.shortfalls(self.protection(["old-name"])), [])

    def test_drift_reports_the_stale_context_that_blocks_every_pull_request(self):
        stale, missing = protect.context_drift(self.protection(["old-name"]), ("build",))
        self.assertEqual(stale, ["old-name"])
        self.assertEqual(missing, ["build"])

    def test_matching_contexts_are_not_drift(self):
        self.assertEqual(protect.context_drift(self.protection(["build"]), ("build",)), ([], []))

    def test_order_does_not_count_as_drift(self):
        drift = protect.context_drift(self.protection(["b", "a"]), ("a", "b"))
        self.assertEqual(drift, ([], []))

    def test_no_expectation_reports_no_drift(self):
        # A repository this script does not own the check list for. Comparing
        # against nothing would call every configured context stale.
        self.assertEqual(protect.context_drift(self.protection(["x"]), None), ([], []))

    def test_configured_contexts_reads_both_spellings(self):
        self.assertEqual(protect.configured_contexts(self.protection(["b", "a"])), ["a", "b"])
        checks_form = {"required_status_checks": {"strict": True, "contexts": [],
                                                  "checks": [{"context": "a"}, {"context": "b"}]}}
        self.assertEqual(protect.configured_contexts(checks_form), ["a", "b"])
        self.assertEqual(protect.configured_contexts(None), [])


class FakeGitHub:
    """Records calls so a test can assert what was, and was not, written."""

    def __init__(self, protection=None, protection_status=200, branch_status=200):
        self.protection = protection
        self.protection_status = protection_status
        self.branch_status = branch_status
        self.calls = []

    def __call__(self, url, token, method="GET", body=None):
        self.calls.append((method, url, body))
        if url.endswith("/protection"):
            if method == "PUT":
                self.protection = {"required_status_checks":
                                   {"strict": body["required_status_checks"]["strict"],
                                    "contexts": body["required_status_checks"]["contexts"]},
                                   "enforce_admins": {"enabled": body["enforce_admins"]}}
                return 200, self.protection
            return self.protection_status, self.protection
        return self.branch_status, ({} if self.branch_status == 200 else None)

    def puts(self):
        return [c for c in self.calls if c[0] == "PUT"]


class MainFlowTests(unittest.TestCase):
    """The two paths Codex found, exercised through main()."""

    def run_main(self, fake, argv):
        buf = io.StringIO()
        with mock.patch.dict(os.environ, {"CI_ADMIN_TOKEN": "t"}), \
             mock.patch.object(protect, "request", fake), \
             contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = protect.main(argv)
        return code, buf.getvalue()

    def drifted(self):
        return FakeGitHub(protection={"required_status_checks":
                                      {"strict": True, "contexts": ["renamed-away"]},
                                      "enforce_admins": {"enabled": True}})

    def test_a_drifted_branch_is_written_instead_of_called_satisfied(self):
        # The first P1. `shortfalls` returns [] for a strict, admin-bound
        # branch whatever it requires, so the early return skipped the write
        # and the one tool that can reconcile a branch reported success while
        # changing nothing.
        fake = self.drifted()
        code, out = self.run_main(
            fake, ["--owner", "o", "--repo", "claude-agent-routing-template", "--apply"])
        self.assertNotIn("already satisfies", out)
        self.assertIn("drifted", out)
        self.assertEqual(len(fake.puts()), 1, "the missing context was never added")
        self.assertEqual(code, 0)

    def test_the_default_write_preserves_a_context_the_table_does_not_name(self):
        # The second P1, and a regression the first fix introduced: the PUT
        # sends the whole contexts array, so writing only the table's list
        # deleted anything else the branch required.
        fake = self.drifted()
        self.run_main(fake, ["--owner", "o", "--repo", "claude-agent-routing-template", "--apply"])
        written = fake.puts()[0][2]["required_status_checks"]["contexts"]
        self.assertEqual(written, ["build", "renamed-away"])

    def test_a_preserving_write_is_reported_as_success(self):
        # Guards the post-write comparison, which asserting on the PUT body
        # cannot: that check changes only what the run REPORTS, never what it
        # writes. Compared against the table instead of against the contexts
        # actually intended, every successful preserving write comes back
        # "WROTE, BUT STILL SHORT" and the run exits non-zero -- having done
        # exactly the right thing.
        fake = self.drifted()
        code, out = self.run_main(
            fake, ["--owner", "o", "--repo", "claude-agent-routing-template", "--apply"])
        self.assertEqual(code, 0)
        self.assertIn("protected: strict checks build, renamed-away", out)

    def test_drop_unlisted_is_what_clears_a_renamed_context(self):
        # The deadlock escape hatch, and the only way to remove anything.
        fake = self.drifted()
        self.run_main(fake, ["--owner", "o", "--repo", "claude-agent-routing-template",
                             "--apply", "--drop-unlisted"])
        self.assertEqual(fake.puts()[0][2]["required_status_checks"]["contexts"], ["build"])

    def test_an_operator_added_gate_is_not_touched_at_all(self):
        # A branch that already requires everything the table names, plus a
        # control somebody added. Nothing is missing, so nothing is written --
        # the strongest form of preserving it.
        fake = FakeGitHub(protection={"required_status_checks":
                                      {"strict": True, "contexts": ["build", "security-scan"]},
                                      "enforce_admins": {"enabled": True}})
        code, out = self.run_main(
            fake, ["--owner", "o", "--repo", "claude-agent-routing-template", "--apply"])
        self.assertEqual(fake.puts(), [], "an unowned required check was rewritten")
        self.assertIn("already satisfies", out)
        self.assertIn("security-scan", out)
        self.assertIn("--drop-unlisted", out)
        self.assertEqual(code, 0)

    def test_drop_unlisted_will_remove_an_operator_added_gate(self):
        # Stated as a test rather than left implicit: the flag cannot tell a
        # deliberate control from a rename leftover, and removes both. That is
        # why it is opt-in.
        fake = FakeGitHub(protection={"required_status_checks":
                                      {"strict": True, "contexts": ["build", "security-scan"]},
                                      "enforce_admins": {"enabled": True}})
        self.run_main(fake, ["--owner", "o", "--repo", "claude-agent-routing-template",
                             "--apply", "--drop-unlisted"])
        self.assertEqual(fake.puts()[0][2]["required_status_checks"]["contexts"], ["build"])

    def test_a_matching_branch_is_left_alone(self):
        fake = FakeGitHub(protection={"required_status_checks":
                                      {"strict": True, "contexts": ["build"]},
                                      "enforce_admins": {"enabled": True}})
        code, out = self.run_main(
            fake, ["--owner", "o", "--repo", "claude-agent-routing-template", "--apply"])
        self.assertIn("already satisfies", out)
        self.assertEqual(fake.puts(), [], "nothing should be written to a correct branch")
        self.assertEqual(code, 0)

    def test_an_invisible_repository_is_not_reported_as_unprotected(self):
        # The P2. GitHub answers 404 both for "no protection" and for "no such
        # repository or branch, or none you can see". Reading the second as the
        # first tells the operator a repository is unprotected when the script
        # simply could not look at it -- and exits zero saying so.
        fake = FakeGitHub(protection_status=404, branch_status=404)
        code, out = self.run_main(
            fake, ["--owner", "o", "--repo", "claude-agent-routing-template"])
        self.assertIn("cannot read", out)
        self.assertNotIn("no branch protection at all", out)
        self.assertEqual(code, 1)

    def test_a_real_unprotected_branch_is_still_reported_as_unprotected(self):
        # The fix must not swallow the case it is disambiguating from.
        fake = FakeGitHub(protection_status=404, branch_status=200)
        code, out = self.run_main(
            fake, ["--owner", "o", "--repo", "claude-agent-routing-template"])
        self.assertIn("no branch protection at all", out)
        self.assertIn("would require: build", out)
        self.assertEqual(fake.puts(), [], "report mode must not write")

    def test_report_mode_writes_nothing_even_when_drifted(self):
        fake = FakeGitHub(protection={"required_status_checks":
                                      {"strict": True, "contexts": ["renamed-away"]},
                                      "enforce_admins": {"enabled": True}})
        _, out = self.run_main(fake, ["--owner", "o", "--repo", "claude-agent-routing-template"])
        self.assertIn("drifted", out)
        self.assertIn("re-run with --apply", out)
        self.assertEqual(fake.puts(), [])
