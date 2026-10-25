"""The team-dispatch workflow: the web-side door to the VPS team pipeline.

A Claude Code web session has no route to the VPS, so GitHub Actions is the only
door. The workflow's limits (never push, force, wait or create a feature) live in
the root-owned wrapper on the VPS, not here; what this file pins is what the
workflow itself owes: it is opt-in, runs on a runner of its own, executes no
repository code, and turns four inputs into exactly one `sudo -u team` call
without ever splicing an input into shell text.

The step's own shell is executed here with a fake `sudo` on PATH, because nothing
that runs around the YAML can see a defect inside it.
"""

import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "team-dispatch.yml"


def load():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def triggers(spec):
    # PyYAML reads the bare key `on` as the boolean True.
    return spec.get("on", spec.get(True))


def dispatch_script():
    steps = load()["jobs"]["dispatch"]["steps"]
    (step,) = [s for s in steps if s.get("name") == "Dispatch"]
    return step["run"]


class WorkflowShapeTests(unittest.TestCase):
    def test_it_is_pinned_so_it_never_follows_the_ci_runner_switch(self):
        self.assertRegex(WORKFLOW.read_text(encoding="utf-8").splitlines()[0], r"^#\s*ci-runner-mode:\s*pinned\s*$")

    def test_it_is_dispatch_only(self):
        # A push or pull_request trigger would hand a branch author a shell on the VPS.
        self.assertEqual(set(triggers(load())), {"workflow_dispatch"})

    def test_it_runs_on_its_own_label_and_not_at_all_without_one(self):
        job = load()["jobs"]["dispatch"]
        self.assertEqual(job["runs-on"], "${{ vars.TEAM_DISPATCH_LABEL }}")
        self.assertIn("vars.TEAM_DISPATCH_LABEL != ''", job["if"])

    def test_it_never_shares_the_ordinary_ci_runner_variables(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for name in ("CI_RUNNER", "CI_SELF_HOSTED_LABEL", "CI_PROBE_LABEL"):
            self.assertNotRegex(text.split("\nname:", 1)[1], rf"vars\.{name}\b")

    def test_it_executes_nothing_from_the_repository(self):
        steps = load()["jobs"]["dispatch"]["steps"]
        self.assertTrue(all("uses" not in s for s in steps), "a checkout or action would run repository-controlled code")

    def test_it_holds_no_token_permissions(self):
        self.assertEqual(load()["permissions"], {})

    def test_it_has_no_concurrency_group_that_would_swallow_a_dispatch(self):
        spec = load()
        self.assertNotIn("concurrency", spec)
        self.assertNotIn("concurrency", spec["jobs"]["dispatch"])

    def test_no_input_is_spliced_into_shell_text(self):
        # Inputs must arrive through env:, never as ${{ }} inside the script.
        self.assertNotIn("${{", dispatch_script())

    def test_only_the_registered_teams_are_offered(self):
        options = triggers(load())["workflow_dispatch"]["inputs"]["team"]["options"]
        self.assertEqual(options, ["team", "team-codex"])

    def test_push_is_not_an_action(self):
        options = triggers(load())["workflow_dispatch"]["inputs"]["action"]["options"]
        self.assertEqual(sorted(options), ["queue", "run", "status"])


class DispatchShellTests(unittest.TestCase):
    """Run the step with a fake `sudo` that records its arguments."""

    def run_step(self, **env):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            bindir = tmp / "bin"
            bindir.mkdir()
            fake = bindir / "sudo"
            fake.write_text(
                '#!/bin/bash\nprintf "%s\\n" "$@" > "$CALLS"\necho "fake team output"\nexit "${FAKE_RC:-0}"\n',
                encoding="utf-8",
            )
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            calls = tmp / "calls"
            summary = tmp / "summary"
            full = {
                "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}",
                "CALLS": str(calls),
                "GITHUB_STEP_SUMMARY": str(summary),
                "TEAM": "team", "ACTION": "status", "FEATURE": "", "FROM": "",
            }
            full.update(env)
            result = subprocess.run(
                ["bash", "-c", dispatch_script()], env=full, capture_output=True, text=True, cwd=tmp,
            )
            argv = calls.read_text(encoding="utf-8").split("\n")[:-1] if calls.exists() else None
            text = summary.read_text(encoding="utf-8") if summary.exists() else ""
            return result, argv, text

    def test_status_calls_the_wrapper_as_user_team_by_absolute_path(self):
        result, argv, _ = self.run_step(ACTION="status", FEATURE="F12")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(argv, ["-n", "-u", "team", "--", "/usr/local/bin/team", "status", "F12"])

    def test_run_always_joins_the_queue(self):
        result, argv, _ = self.run_step(ACTION="run", FEATURE="F12")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(argv[-3:], ["run", "F12", "--queue"])

    def test_run_can_resume_from_a_step(self):
        _, argv, _ = self.run_step(ACTION="run", FEATURE="F12", FROM="verdict")
        self.assertEqual(argv[-5:], ["run", "F12", "--from", "verdict", "--queue"])

    def test_the_codex_team_uses_its_own_wrapper(self):
        _, argv, _ = self.run_step(TEAM="team-codex", ACTION="queue")
        self.assertEqual(argv[-2:], ["/usr/local/bin/team-codex", "queue"])

    def test_queue_needs_no_feature(self):
        result, argv, _ = self.run_step(ACTION="queue")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(argv[-2:], ["/usr/local/bin/team", "queue"])

    def test_a_shell_metacharacter_in_the_feature_never_reaches_sudo(self):
        for bad in ("F12; rm -rf /", "$(id)", "F12 --force", "../x", "-F12", "a" * 65, "F 12"):
            with self.subTest(feature=bad):
                result, argv, _ = self.run_step(ACTION="run", FEATURE=bad)
                self.assertNotEqual(result.returncode, 0)
                self.assertIsNone(argv, "sudo must not be called for an invalid feature id")

    def test_actions_beyond_the_three_are_refused(self):
        for action in ("push", "dequeue", "new", "work", "drain", "doctor", ""):
            with self.subTest(action=action):
                result, argv, _ = self.run_step(ACTION=action, FEATURE="F12")
                self.assertNotEqual(result.returncode, 0)
                self.assertIsNone(argv)

    def test_an_unknown_team_is_refused(self):
        result, argv, _ = self.run_step(TEAM="team-video", ACTION="queue")
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(argv)

    def test_an_unknown_step_is_refused(self):
        result, argv, _ = self.run_step(ACTION="run", FEATURE="F12", FROM="push --force")
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(argv)

    def test_from_is_refused_outside_run(self):
        result, argv, _ = self.run_step(ACTION="status", FEATURE="F12", FROM="coder")
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(argv)

    def test_a_missing_feature_is_refused_for_run_and_status(self):
        for action in ("run", "status"):
            with self.subTest(action=action):
                result, argv, _ = self.run_step(ACTION=action)
                self.assertNotEqual(result.returncode, 0)
                self.assertIsNone(argv)

    def test_a_failing_pipeline_fails_the_job_and_still_reaches_the_summary(self):
        result, _, summary = self.run_step(ACTION="run", FEATURE="F12", FAKE_RC="3")
        self.assertEqual(result.returncode, 3)
        self.assertIn("(exit 3)", summary)
        self.assertIn("fake team output", summary)

    def test_the_feature_pattern_matches_what_team_py_accepts(self):
        # Spot-check the boundary of the 64-character id shape.
        self.assertTrue(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", "a" * 64))
        result, argv, _ = self.run_step(ACTION="status", FEATURE="a" * 64)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(argv[-1], "a" * 64)


if __name__ == "__main__":
    unittest.main()
