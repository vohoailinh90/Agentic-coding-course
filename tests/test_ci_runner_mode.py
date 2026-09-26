from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
PICK_PATH = ROOT / "scripts" / "pick_runner.py"
SWITCH_PATH = ROOT / "scripts" / "switch_runner.py"
SYNC_PATH = ROOT / "scripts" / "sync_ci_runner.py"
WORKFLOW_DIR = ROOT / ".github" / "workflows"


def load_module(name: str, path: Path):
    """Load a script from source, never from the bytecode cache.

    A mutation check rewrites the file and re-runs the test within the same
    second, often without changing its length. Normal import machinery validates
    cached bytecode on `(mtime, size)` at one-second granularity and would hand
    back the *previous* version, so the mutation would read as caught when
    nothing had been exercised at all.
    """
    if not path.is_file():
        raise RuntimeError(f"Unable to load {path}")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)
    return module


pick = load_module("pick_runner", PICK_PATH)
switch = load_module("switch_runner", SWITCH_PATH)
sync = load_module("sync_ci_runner", SYNC_PATH)


def quota(remaining):
    return pick.Quota(remaining, "test")


def decide(**overrides):
    kwargs = dict(
        mode="auto",
        current="",
        github_label="ubuntu-latest",
        self_hosted_label="self-hosted",
        quota=quota(None),
        low_water=50,
        high_water=200,
    )
    kwargs.update(overrides)
    return pick.decide(**kwargs)


def run_cli(argv, stdin="", env=None):
    """Run pick_runner.main with a controlled stdin, returning (rc, stdout)."""
    out = io.StringIO()
    with mock.patch.object(sys, "stdin", io.StringIO(stdin)), contextlib.redirect_stdout(out):
        with mock.patch.dict(os.environ, env or {}, clear=False):
            rc = pick.main(argv)
    return rc, out.getvalue()


class DecisionTests(unittest.TestCase):
    def test_github_mode_pins_the_hosted_runner_however_low_the_quota(self):
        self.assertEqual(decide(mode="github", quota=quota(0)).runner, "ubuntu-latest")

    def test_self_hosted_mode_pins_the_vps_however_high_the_quota(self):
        self.assertEqual(decide(mode="self-hosted", quota=quota(99999)).runner, "self-hosted")

    def test_a_pinned_mode_needs_no_billing_data_at_all(self):
        # The point of pinning is that it keeps working when the probe cannot.
        for mode, expected in (("github", "ubuntu-latest"), ("self-hosted", "self-hosted")):
            with self.subTest(mode=mode):
                result = decide(mode=mode, quota=quota(None))
                self.assertEqual(result.runner, expected)
                self.assertFalse(result.undetermined)

    def test_exhausted_quota_moves_work_to_the_vps(self):
        self.assertEqual(decide(quota=quota(0)).runner, "self-hosted")

    def test_the_low_water_mark_is_inclusive(self):
        self.assertEqual(decide(quota=quota(50), low_water=50).runner, "self-hosted")

    def test_restored_quota_moves_work_back_to_github(self):
        self.assertEqual(decide(quota=quota(2000), current="self-hosted").runner, "ubuntu-latest")

    def test_the_high_water_mark_is_inclusive(self):
        self.assertEqual(decide(quota=quota(200), high_water=200, current="self-hosted").runner, "ubuntu-latest")

    def test_between_the_marks_the_standing_choice_holds(self):
        # Hysteresis: without this band a remainder hovering on one threshold
        # would rewrite the variable on every single probe.
        for current in ("ubuntu-latest", "self-hosted"):
            with self.subTest(current=current):
                result = decide(quota=quota(120), current=current)
                self.assertEqual(result.runner, current)
                self.assertFalse(result.changed)

    def test_between_the_marks_with_nothing_set_yet_leaves_it_unset(self):
        # This test used to assert the opposite, and was right to while every
        # repository fell back to a hosted runner. Once switch_runner grew
        # --fallback, the premise broke: an unset CI_RUNNER resolves to whatever
        # fallback the repository's own workflows carry, which may be
        # `self-hosted`, and this function cannot see which. Guessing
        # `ubuntu-latest` then reported "held" while returning changed=True, and
        # the first probe landing in the band would move a VPS repository's
        # every job back onto billed minutes -- the exact regression --fallback
        # exists to prevent. There is no standing choice to hold here.
        result = decide(quota=quota(120), current="")
        self.assertEqual(result.runner, "")
        self.assertFalse(result.changed)
        self.assertIn("unset", result.reason)

    def test_a_whitespace_only_variable_is_removed_not_repaired_to_hosted(self):
        # A GitHub expression treats any non-empty string as truthy, so the
        # variable resolves to the whitespace itself and every job queues
        # against a label no runner answers to. Treating it as "unset" and
        # holding left CI stuck with nothing able to unstick it.
        #
        # Repairing it to the hosted label unsticks CI and costs money: on a
        # repository converted with `--fallback self-hosted` it moves every job
        # back onto billed minutes, which is the regression the fallback flag
        # exists to prevent. Deleting the variable unsticks CI just as well and
        # restores the repository's own fallback, whatever it is -- which is
        # the standing choice the band is supposed to hold.
        result = decide(quota=quota(120), current="   ")
        self.assertTrue(result.delete)
        self.assertNotEqual(result.runner, "ubuntu-latest")
        self.assertTrue(result.changed)
        self.assertIn("whitespace", result.reason)

    def test_nothing_else_asks_for_the_variable_to_be_deleted(self):
        # `delete` discards state, so it must stay confined to the one case
        # that means it. Every other outcome names a label to write, or holds.
        for label, result in (
            ("unset in the band", decide(quota=quota(120), current="")),
            ("held in the band", decide(quota=quota(120), current="self-hosted")),
            ("decisively low", decide(quota=quota(10), current="   ")),
            ("decisively high", decide(quota=quota(900), current="   ")),
            ("quota unreadable", decide(quota=pick.Quota(None, "unreadable"), current="   ")),
            ("pinned to github", decide(mode="github", quota=quota(120), current="   ")),
            ("pinned to self-hosted", decide(mode="self-hosted", quota=quota(120), current="   ")),
        ):
            with self.subTest(case=label):
                self.assertFalse(result.delete)

    def test_stray_whitespace_around_a_real_label_is_trimmed(self):
        result = decide(quota=quota(120), current=" self-hosted ")
        self.assertEqual(result.runner, "self-hosted")
        self.assertTrue(result.changed)

    def test_an_unset_variable_still_moves_when_the_quota_is_decisive(self):
        # Holding inside the band must not become never acting at all.
        low = decide(quota=quota(10), current="")
        self.assertEqual(low.runner, "self-hosted")
        self.assertTrue(low.changed)
        high = decide(quota=quota(900), current="")
        self.assertEqual(high.runner, "ubuntu-latest")
        self.assertTrue(high.changed)

    def test_unreadable_quota_changes_nothing_and_says_so(self):
        result = decide(quota=pick.Quota(None, "payload matched no known shape"), current="self-hosted")
        self.assertEqual(result.runner, "self-hosted")
        self.assertFalse(result.changed)
        self.assertTrue(result.undetermined)
        self.assertIn("undetermined", result.reason)

    def test_changed_tracks_the_current_value_not_the_mode(self):
        self.assertFalse(decide(mode="github", current="ubuntu-latest", quota=quota(0)).changed)
        self.assertTrue(decide(mode="github", current="self-hosted", quota=quota(0)).changed)

    def test_a_custom_self_hosted_label_is_honoured(self):
        # The VPS may register under a label of its own; that must not need a
        # code change.
        result = decide(quota=quota(0), self_hosted_label="hetzner-cx22")
        self.assertEqual(result.runner, "hetzner-cx22")


class BillingParsingTests(unittest.TestCase):
    def test_legacy_payload_yields_the_remainder(self):
        result = pick.read_quota({"total_minutes_used": 1200, "included_minutes": 3000}, None)
        self.assertEqual(result.remaining, 1800)

    def test_legacy_overage_clamps_at_zero_rather_than_going_negative(self):
        result = pick.read_quota({"total_minutes_used": 3200, "included_minutes": 3000}, None)
        self.assertEqual(result.remaining, 0)

    def test_enhanced_payload_yields_a_remainder_when_the_allowance_is_supplied(self):
        payload = {
            "usageItems": [
                {"product": "actions", "sku": "actions_linux", "unitType": "minutes", "quantity": 400},
                {"product": "actions", "sku": "actions_linux", "unitType": "Minutes", "quantity": 100},
                {"product": "packages", "sku": "packages", "unitType": "GigabyteHours", "quantity": 900},
                {"product": "actions", "sku": "actions_linux", "unitType": "dollars", "quantity": 7},
            ]
        }
        result = pick.read_quota(payload, 3000)
        self.assertEqual(result.remaining, 2500)

    def test_windows_and_macos_minutes_cost_more_than_they_report(self):
        # The report states native minutes; the allowance is consumed at 2x for
        # Windows and 10x for macOS. Summing raw quantities would call this 300
        # used and overstate the remainder by 900.
        payload = {
            "usageItems": [
                {"product": "actions", "sku": "actions_linux", "unitType": "minutes", "quantity": 100},
                {"product": "actions", "sku": "actions_windows", "unitType": "minutes", "quantity": 100},
                {"product": "actions", "sku": "actions_macos", "unitType": "minutes", "quantity": 100},
            ]
        }
        self.assertEqual(pick.read_quota(payload, 3000).remaining, 3000 - (100 + 200 + 1000))

    def test_an_empty_enhanced_report_is_a_valid_zero(self):
        # Reading this as "unreadable" builds a ratchet: once CI_RUNNER is
        # self-hosted no hosted minutes are spent, so every later report is
        # legitimately empty, and holding the last decision would hold it
        # forever -- having removed the evidence that would undo it.
        for payload in ({"usageItems": []},
                        {"usageItems": [{"product": "packages", "unitType": "minutes", "quantity": 5}]}):
            with self.subTest(payload=payload):
                self.assertEqual(pick.read_quota(payload, 3000).remaining, 3000)

    def test_a_new_month_releases_a_self_hosted_repository(self):
        # The end of the ratchet, stated as the behaviour that matters.
        quota = pick.read_quota({"usageItems": []}, 3000)
        result = decide(quota=quota, current="self-hosted")
        self.assertEqual(result.runner, "ubuntu-latest")
        self.assertTrue(result.changed)

    def test_an_unconvertible_sku_refuses_to_guess(self):
        # Larger runners are billed per minute and draw nothing from the
        # allowance, so 1x is not a safe default -- no answer is.
        payload = {"usageItems": [{"product": "actions", "sku": "actions_linux_4_core",
                                   "unitType": "minutes", "quantity": 100}]}
        result = pick.read_quota(payload, 3000)
        self.assertIsNone(result.remaining)
        self.assertIn("actions_linux_4_core", result.source)

    def test_sku_matching_is_exact_not_a_substring(self):
        # "actions_linux_4_core" contains "actions_linux"; a substring test
        # would bill a larger runner against the included allowance at 1x.
        self.assertIn("actions_linux", "actions_linux_4_core")
        self.assertIsNone(pick.INCLUDED_MINUTE_RATES.get("actions_linux_4_core"))

    def test_one_unconvertible_sku_discards_the_whole_report(self):
        # A partial sum is worse than none: it looks like a real remainder.
        payload = {
            "usageItems": [
                {"product": "actions", "sku": "actions_linux", "unitType": "minutes", "quantity": 10},
                {"product": "actions", "sku": "actions_something_new", "unitType": "minutes", "quantity": 10},
            ]
        }
        self.assertIsNone(pick.read_quota(payload, 3000).remaining)

    def test_enhanced_payload_without_an_allowance_is_undetermined(self):
        # The enhanced endpoint reports consumption but not the plan allowance.
        # Inventing one would be a guess about somebody's billing plan.
        #
        # The payload must carry a convertible item. An empty one is undetermined
        # for its own reason, so it would pass this assertion even with the
        # allowance guard removed -- a mutation caught exactly that.
        payload = {"usageItems": [{"product": "actions", "sku": "actions_linux",
                                   "unitType": "minutes", "quantity": 10}]}
        self.assertIsNone(pick.read_quota(payload, None).remaining)
        self.assertEqual(pick.read_quota(payload, 3000).remaining, 2990,
                         "the same payload must yield a real remainder once an allowance is supplied")

    def test_an_unknown_payload_shape_is_undetermined(self):
        self.assertIsNone(pick.read_quota({"message": "Not Found"}, 3000).remaining)

    def test_a_non_object_payload_is_undetermined(self):
        self.assertIsNone(pick.read_quota([1, 2, 3], 3000).remaining)

    def test_boolean_minute_counts_are_rejected_as_a_broken_payload(self):
        # bool subclasses int; `True` minutes used is corruption, not a quota.
        self.assertIsNone(pick.read_quota({"total_minutes_used": True, "included_minutes": 3000}, None).remaining)

    def test_a_malformed_usage_item_does_not_sink_the_whole_payload(self):
        payload = {"usageItems": ["nonsense", {"product": "actions", "sku": "actions_linux",
                                               "unitType": "minutes", "quantity": 10}]}
        self.assertEqual(pick.read_quota(payload, 100).remaining, 90)


class PickCliTests(unittest.TestCase):
    def test_high_water_must_exceed_low_water(self):
        # Equal marks would erase the hysteresis band silently.
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                run_cli(["--low-water", "100", "--high-water", "100"])
        self.assertEqual(raised.exception.code, 2)

    def test_empty_stdin_is_undetermined_rather_than_a_crash(self):
        rc, out = run_cli(["--current", "self-hosted"], stdin="")
        self.assertEqual(rc, 0)
        self.assertIn("self-hosted", out)
        self.assertIn("undetermined", out)

    def test_invalid_json_is_undetermined_rather_than_a_crash(self):
        rc, out = run_cli(["--current", "self-hosted"], stdin="<html>502 Bad Gateway</html>")
        self.assertEqual(rc, 0)
        self.assertIn("undetermined", out)
        self.assertIn("changed: no", out)

    def test_github_output_receives_the_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "out.txt"
            target.touch()
            payload = json.dumps({"total_minutes_used": 3000, "included_minutes": 3000})
            run_cli(["--current", "ubuntu-latest"], stdin=payload, env={"GITHUB_OUTPUT": str(target)})
            written = dict(line.split("=", 1) for line in target.read_text().strip().splitlines())
        self.assertEqual(written["runner"], "self-hosted")
        self.assertEqual(written["changed"], "true")
        self.assertEqual(written["undetermined"], "false")

    def test_a_runner_label_cannot_forge_extra_output_keys(self):
        # The sibling of the reason guard. A label carrying a newline would
        # otherwise write a second `runner=` line, and the last one wins.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "out.txt"
            target.touch()
            decision = pick.Decision("self-hosted\nchanged=true", "held", False, False)
            with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(target)}):
                with contextlib.redirect_stdout(io.StringIO()):
                    pick.emit(decision)
            lines = target.read_text().strip().splitlines()
        self.assertEqual([line for line in lines if line.startswith("changed=")], ["changed=false"])
        self.assertEqual(len([line for line in lines if line.startswith("runner=")]), 1)

    def test_a_reason_cannot_forge_extra_output_keys(self):
        # Anything reaching GITHUB_OUTPUT with a newline in it can invent a key;
        # the reason text is the only free-form field here.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "out.txt"
            target.touch()
            decision = pick.Decision("self-hosted", "line one\nrunner=pwned", False, False)
            with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(target)}):
                with contextlib.redirect_stdout(io.StringIO()):
                    pick.emit(decision)
            lines = target.read_text().strip().splitlines()
        self.assertEqual([line for line in lines if line.startswith("runner=")], ["runner=self-hosted"])

    def test_the_script_runs_as_a_subprocess_with_no_third_party_imports(self):
        # It runs on the VPS with whatever python3 is there; stdlib only.
        result = subprocess.run(
            [sys.executable, str(PICK_PATH), "--mode", "self-hosted"],
            input="", capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("runner:  self-hosted", result.stdout)


class SwitchRewriteTests(unittest.TestCase):
    def test_a_hardcoded_runner_becomes_the_dynamic_form(self):
        text = "jobs:\n  build:\n    runs-on: ubuntu-latest\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual(changed, 1)
        self.assertEqual(findings, [])
        self.assertIn(f"    runs-on: {switch.DYNAMIC}", updated)

    def test_rewriting_preserves_indentation(self):
        text = "jobs:\n  build:\n        runs-on: ubuntu-latest\n"
        updated, _, _ = switch.rewrite(text, switch.DYNAMIC)
        self.assertIn(f"\n        runs-on: {switch.DYNAMIC}", updated)

    def test_rewriting_is_idempotent(self):
        once, _, _ = switch.rewrite("jobs:\n  a:\n    runs-on: ubuntu-latest\n", switch.DYNAMIC)
        twice, changed, _ = switch.rewrite(once, switch.DYNAMIC)
        self.assertEqual(twice, once)
        self.assertEqual(changed, 0)

    def test_the_switch_round_trips_back_to_github(self):
        original = "jobs:\n  a:\n    runs-on: ubuntu-latest\n"
        dynamic, _, _ = switch.rewrite(original, switch.DYNAMIC)
        back, _, _ = switch.rewrite(dynamic, switch.MODES["github"])
        self.assertEqual(back, original)

    def test_a_list_runner_is_reported_and_left_untouched(self):
        # Merging [self-hosted, linux, x64] into one label would invent intent.
        text = "jobs:\n  a:\n    runs-on: [self-hosted, linux, x64]\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual(updated, text)
        self.assertEqual(changed, 0)
        self.assertEqual(len(findings), 1)
        self.assertIn("not a scalar runner", findings[0])

    def test_a_matrix_expression_runner_is_reported_not_overwritten(self):
        # `${{ matrix.os }}` fans one job out over several runners; a single
        # label in its place would silently collapse the matrix.
        text = "jobs:\n  a:\n    runs-on: ${{ matrix.os }}\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((updated, changed), (text, 0))
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("not a scalar runner", findings[0])

    def test_an_expression_after_a_literal_prefix_is_reported_not_overwritten(self):
        text = "jobs:\n  a:\n    runs-on: linux-${{ matrix.arch }}\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((updated, changed), (text, 0))
        self.assertEqual(len(findings), 1, findings)

    def test_an_aliased_job_mapping_is_rewritten_once(self):
        # Both jobs report the same node; applying its span twice spliced the
        # target into itself and still parsed, so nothing rolled it back.
        text = "jobs:\n  a: &shared\n    runs-on: ubuntu-latest\n    steps: []\n  b: *shared\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((changed, findings), (1, []))
        self.assertEqual(switch.parsed_job_runners(updated), {"a": switch.DYNAMIC, "b": switch.DYNAMIC})

    def test_the_switch_expression_itself_can_change_fallback(self):
        text = "jobs:\n  a:\n    runs-on: " + switch.DYNAMIC + "\n"
        updated, changed, findings = switch.rewrite(text, switch.dynamic_form("self-hosted"))
        self.assertEqual((changed, findings), (1, []))
        self.assertIn(switch.dynamic_form("self-hosted"), updated)

    def test_an_inline_comment_is_kept_and_not_read_as_the_runner(self):
        # `# runner` is YAML comment, not part of the value: the switch's own
        # expression followed by one must still be recognised, converted, and
        # keep its comment.
        text = "jobs:\n  a:\n    runs-on: " + switch.DYNAMIC + "  # runner\n"
        same, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((same, changed, findings), (text, 0, []))
        back, changed, findings = switch.rewrite(text, switch.MODES["github"])
        self.assertEqual((changed, findings), (1, []))
        self.assertIn("    runs-on: ubuntu-latest  # runner\n", back)

    def test_a_rewrite_without_a_parser_does_not_claim_success(self):
        text = "on: push\njobs:\n  a: {runs-on: ubuntu-latest, steps: []}\n"
        with mock.patch.object(switch, "yaml", None):
            _, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual(changed, 0)
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("PyYAML is unavailable", findings[0])

    def test_a_quoted_scalar_continuation_line_is_not_a_runner(self):
        # YAML lets a quoted scalar continue on a line at the job's own key
        # indentation, so text inside it can look exactly like a runner.
        text = ('jobs:\n  a:\n    name: "first line\n    runs-on: ubuntu-latest"\n'
                "    runs-on: ubuntu-latest\n")
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((changed, findings), (1, []))
        self.assertIn('    runs-on: ubuntu-latest"\n', updated)
        self.assertTrue(updated.endswith(f"    runs-on: {switch.DYNAMIC}\n"))

    def test_an_anchored_or_aliased_runner_is_reported_not_rewritten(self):
        text = "jobs:\n  a:\n    runs-on: &r ubuntu-latest\n  b:\n    runs-on: *r\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((updated, changed), (text, 0))
        self.assertEqual(len(findings), 2, findings)

    def test_an_unparseable_workflow_is_reported_and_left_alone(self):
        text = "jobs:\n  a:\n    runs-on: ubuntu-latest\nbroken: [\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((updated, changed), (text, 0))
        self.assertIn("could not be parsed", findings[0])

    def test_a_runner_spanning_lines_is_reported_not_rewritten(self):
        text = "jobs:\n  a:\n    runs-on: ubuntu\n      latest\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((updated, changed), (text, 0))
        self.assertEqual(len(findings), 1, findings)

    def test_a_block_scalar_runner_is_reported_not_half_rewritten(self):
        # `runs-on: >-` puts the value on the next line; editing only the
        # indicator line would leave the continuation behind as invalid YAML.
        for indicator in (">-", "|"):
            text = f"jobs:\n  a:\n    runs-on: {indicator}\n      ubuntu-latest\n"
            updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
            self.assertEqual((updated, changed), (text, 0))
            self.assertEqual(len(findings), 1, findings)

    def test_an_empty_runner_is_filled_with_valid_yaml(self):
        # `--check` reports an empty `runs-on:` and points at this command, so
        # the fix it writes must parse.
        for line in ("    runs-on:\n", "    runs-on: # to do\n"):
            text = "jobs:\n  a:\n" + line + "    steps: []\n"
            updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
            self.assertEqual((changed, findings), (1, []))
            self.assertEqual(switch.parsed_job_runners(updated), {"a": switch.DYNAMIC})

    def test_a_rewrite_that_would_not_parse_changes_nothing(self):
        text = "jobs:\n  a:\n    runs-on: ubuntu-latest\n"
        updated, changed, findings = switch.rewrite(text, "a: b")
        self.assertEqual((updated, changed), (text, 0))
        self.assertIn("cannot be read back", findings[0])

    def test_an_already_converted_flow_job_is_left_alone_quietly(self):
        text = 'on: push\njobs:\n  a: {runs-on: "' + switch.DYNAMIC + '", steps: []}\n'
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((updated, changed, findings), (text, 0, []))

    def test_a_workflow_the_strict_loader_refuses_is_not_passed(self):
        # A duplicate key composes, so the walk sees the job, but the loader
        # that reads the result back refuses it -- which must not read as clean.
        text = "jobs:\n  a:\n    runs-on: ubuntu-latest\n    runs-on: ubuntu-latest\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((updated, changed), (text, 0))
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("cannot be read back", findings[0])

    def test_a_date_that_is_not_a_date_still_converts(self):
        # `2026-13-40` matches YAML 1.1's timestamp pattern, so SafeLoader
        # handed it to datetime and the read-back died with a ValueError
        # traceback. GitHub reads it as a string; so must the converter.
        text = "on: push\nenv: { RELEASE: 2026-13-40 }\njobs:\n  a:\n    runs-on: ubuntu-latest\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((changed, findings), (1, []))
        self.assertIn("runs-on: " + switch.DYNAMIC, updated)

    def test_a_value_the_loader_cannot_build_is_reported_not_raised(self):
        # Each raised a different builtin error: ValueError, KeyError, IndexError.
        for value in ("!!int abc", "!!bool perhaps", '!!int ""'):
            with self.subTest(value=value):
                text = ("on: push\nenv: { N: " + value + " }\njobs:\n"
                        "  a:\n    runs-on: ubuntu-latest\n")
                updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
                self.assertEqual((updated, changed), (text, 0))
                self.assertEqual(len(findings), 1, findings)
                self.assertIn("cannot be read back", findings[0])

    def test_a_jobless_workflow_is_reported_like_check_does(self):
        for text in ("on: push\n", "on: push\njobs: {}\n"):
            updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
            self.assertEqual((updated, changed), (text, 0))
            self.assertEqual(len(findings), 1, (text, findings))
            self.assertIn("no jobs", findings[0])

    def test_a_workflow_of_callers_only_converts_quietly(self):
        text = "on: push\njobs:\n  call:\n    uses: o/r/.github/workflows/x.yml@main\n"
        self.assertEqual(switch.rewrite(text, switch.DYNAMIC), (text, 0, []))

    def test_a_job_the_walk_cannot_reach_is_still_reported(self):
        # A merge key hides the runner from the node walk; the read-back of the
        # result is what keeps it from passing silently.
        text = "x: &d {runs-on: ubuntu-latest}\njobs:\n  a:\n    <<: *d\n    steps: []\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((updated, changed), (text, 0))
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("'a'", findings[0])

    def test_lines_that_merely_mention_runs_on_are_not_rewritten(self):
        text = "    # runs-on: ubuntu-latest is what this used to say\n"
        updated, changed, _ = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual(changed, 0)
        self.assertEqual(updated, text)

    def test_a_runs_on_line_inside_a_run_block_is_left_alone(self):
        # Only jobs.<id>.runs-on is a runner. A heredoc or generated YAML inside
        # `run: |` that happens to contain the same text is a command, and
        # rewriting it silently changes what the step does.
        text = ("jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: |\n          cat > gen.yml <<EOF\n"
                "          runs-on: ubuntu-latest\n          EOF\n")
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual(changed, 1)
        self.assertEqual(findings, [])
        self.assertIn(f"\n    runs-on: {switch.DYNAMIC}\n", updated)
        self.assertIn("\n          runs-on: ubuntu-latest\n", updated)

    def test_an_action_input_named_runs_on_is_left_alone(self):
        text = ("jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - uses: some/action@v1\n        with:\n          runs-on: ubuntu-latest\n")
        updated, changed, _ = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual(changed, 1)
        self.assertIn("\n          runs-on: ubuntu-latest\n", updated)

    def test_runs_on_outside_jobs_is_not_a_runner(self):
        # Same shape as a job, but not under `jobs:` -- so not a runner.
        text = "env:\n  x:\n    runs-on: ubuntu-latest\njobs:\n  a:\n    runs-on: ubuntu-latest\n"
        updated, changed, _ = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual(changed, 1)
        self.assertTrue(updated.startswith("env:\n  x:\n    runs-on: ubuntu-latest\n"))

    def test_a_quoted_runs_on_key_is_converted_and_keeps_its_spelling(self):
        text = 'jobs:\n  a:\n    "runs-on": ubuntu-latest\n'
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((changed, findings), (1, []))
        self.assertIn(f'    "runs-on": {switch.DYNAMIC}', updated)

    def test_a_flow_mapping_job_is_reported_rather_than_silently_skipped(self):
        # Zero updates and a clean exit read as success, after which `--check`
        # rejected the unchanged job and pointed back at this command.
        text = "on: push\njobs:\n  a: {runs-on: ubuntu-latest, steps: []}\n"
        updated, changed, findings = switch.rewrite(text, switch.DYNAMIC)
        self.assertEqual((updated, changed), (text, 0))
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("'a'", findings[0])
        self.assertIn("convert it by hand", findings[0])

    def test_a_run_that_leaves_a_job_unconverted_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.yml"
            path.write_text("on: push\njobs:\n  a: {runs-on: ubuntu-latest, steps: []}\n"
                            "  b:\n    runs-on: ubuntu-latest\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                rc = switch.main(["--workflow-dir", tmp])
            text = path.read_text()
        self.assertEqual(rc, 1)
        self.assertIn(f"    runs-on: {switch.DYNAMIC}", text, "convertible jobs are still written")

    def test_a_file_without_a_trailing_newline_keeps_its_shape(self):
        updated, changed, _ = switch.rewrite("jobs:\n  a:\n    runs-on: ubuntu-latest", switch.DYNAMIC)
        self.assertEqual(changed, 1)
        self.assertFalse(updated.endswith("\n"))


class SwitchCheckTests(unittest.TestCase):
    def write(self, tmp: str, name: str, body: str) -> Path:
        path = Path(tmp) / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_the_repository_tree_passes_its_own_guard(self):
        self.assertEqual(switch.check(WORKFLOW_DIR), [])

    def test_two_jobs_yaml_would_collapse_into_one_are_kept_apart(self):
        # PyYAML implements YAML 1.1, which resolves unquoted `on` and `yes` to
        # booleans -- as mapping keys too. GitHub accepts both as job ids, so
        # safe_load turned two jobs into one and the hardcoded one vanished
        # before the guard could see it. Reproduced: the guard reported clean.
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "collide.yml",
                       "on: push\njobs:\n"
                       "  on:\n    runs-on: ubuntu-latest\n    steps: []\n"
                       "  yes:\n    runs-on: " + switch.DYNAMIC + "\n    steps: []\n")
            problems = switch.check(Path(tmp))
        self.assertTrue(problems, "the hardcoded job was swallowed by key coercion")
        self.assertTrue(any("ubuntu-latest" in p for p in problems), problems)

    def test_a_value_the_loader_cannot_build_does_not_crash_the_guard(self):
        # Same ValueError as the converter's read-back, one step earlier: the
        # guard crashed in CI with a traceback instead of naming the file.
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "date.yml", "on: push\nenv: { RELEASE: 2026-13-40 }\n"
                       "jobs:\n  a:\n    runs-on: " + switch.DYNAMIC + "\n")
            self.write(tmp, "int.yml", "on: push\nenv: { N: !!int abc }\n"
                       "jobs:\n  a:\n    runs-on: " + switch.DYNAMIC + "\n")
            self.write(tmp, "bool.yml", "on: push\nenv: { N: !!bool perhaps }\n"
                       "jobs:\n  a:\n    runs-on: " + switch.DYNAMIC + "\n")
            problems = switch.check(Path(tmp))
        self.assertEqual(len(problems), 2, problems)
        self.assertEqual(sorted(Path(p.split(":")[0]).name for p in problems), ["bool.yml", "int.yml"])

    def test_the_pin_marker_only_counts_as_a_comment(self):
        # A bare substring test exempted a whole workflow on any occurrence, so
        # a step that merely printed the marker switched the guard off for it.
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "sneaky.yml",
                       "on: push\njobs:\n  a:\n    runs-on: ubuntu-latest\n"
                       '    steps:\n      - run: echo "' + switch.PIN_MARKER + '"\n')
            self.assertEqual(len(switch.check(Path(tmp))), 1)

    def test_the_guard_refuses_to_report_success_with_no_parser(self):
        # Falling back to the line scan reopened the exact hole the parsed
        # reading closes, and reported success while doing it.
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "ok.yml", "on: push\njobs:\n  a:\n    runs-on: " + switch.DYNAMIC + "\n")
            with mock.patch.object(switch, "yaml", None):
                problems = switch.check(Path(tmp))
        self.assertEqual(len(problems), 1)
        self.assertIn("PyYAML is unavailable", problems[0])

    def test_a_reintroduced_hardcoded_runner_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "new.yml", "jobs:\n  a:\n    runs-on: ubuntu-latest\n")
            problems = switch.check(Path(tmp))
        self.assertEqual(len(problems), 1)
        self.assertIn("ubuntu-latest", problems[0])

    def test_a_pinned_workflow_is_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "pinned.yml", f"# {switch.PIN_MARKER}\njobs:\n  a:\n    runs-on: self-hosted\n")
            self.assertEqual(switch.check(Path(tmp)), [])

    def test_a_workflow_with_no_runner_at_all_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "empty.yml", "name: nothing\non: push\n")
            problems = switch.check(Path(tmp))
        self.assertEqual(len(problems), 1)
        self.assertIn("no runs-on", problems[0])

    def test_a_workflow_with_no_usable_job_still_needs_a_runner(self):
        # `jobs: {}` and `jobs: {build: null}` have no runs-on and are not
        # reusable-workflow callers either, so exempting them would let a
        # workflow with no runner at all past the guard.
        for body in ("on: push\njobs: {}\n", "on: push\njobs:\n  build: null\n"):
            with self.subTest(body=body):
                self.assertTrue(switch.runs_on_required(body))

    def test_a_workflow_whose_root_is_not_a_mapping_does_not_crash(self):
        # `spec or {}` covers only a falsy root; a list or a bare string loads
        # fine and has no `.get`.
        for text in ("- a\n- list\n", "just a string\n", "42\n"):
            with self.subTest(text=text):
                self.assertTrue(switch.runs_on_required(text))

    def test_the_guard_still_works_without_a_yaml_parser(self):
        # Copied into repositories whose runners may have no PyYAML and no safe
        # way to install one. Losing the parser must fail closed: the
        # reusable-workflow exemption cannot be proved, so a runner is demanded.
        caller = "on: push\njobs:\n  call:\n    uses: o/r/.github/workflows/x.yml@main\n"
        self.assertFalse(switch.runs_on_required(caller), "sanity: normally exempt")
        with mock.patch.object(switch, "yaml", None):
            self.assertTrue(switch.runs_on_required(caller))

    def test_a_reusable_workflow_caller_needs_no_runner(self):
        # `jobs.<id>.uses` is a normal shape with no runs-on to switch, and the
        # only way to satisfy a blanket requirement would be a pin marker that
        # says something untrue about it.
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "caller.yml",
                       "on: push\njobs:\n  call:\n    uses: owner/repo/.github/workflows/x.yml@main\n")
            self.assertEqual(switch.check(Path(tmp)), [])

    def test_a_caller_mixed_with_a_normal_job_still_needs_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "mixed.yml",
                       "on: push\njobs:\n  call:\n    uses: owner/repo/.github/workflows/x.yml@main\n"
                       "  build:\n    steps: []\n")
            self.assertEqual(len(switch.check(Path(tmp))), 1)

    def test_check_honours_the_mode_the_tree_was_pinned_to(self):
        # `--mode self-hosted` is a documented way to pin, so checking a tree
        # that used it must not fail against a form it deliberately does not use.
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, "a.yml", "on: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n")
            with contextlib.redirect_stdout(io.StringIO()):
                switch.main(["--mode", "self-hosted", "--workflow-dir", tmp])
            self.assertIn("runs-on: self-hosted", path.read_text())
            self.assertEqual(switch.check(Path(tmp), switch.MODES["self-hosted"]), [])
            self.assertEqual(len(switch.check(Path(tmp))), 1, "the default form should still disagree")
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(switch.main(["--check", "--mode", "self-hosted", "--workflow-dir", tmp]), 0)

    def test_a_hardcoded_runner_spelled_another_way_is_still_caught(self):
        # `runs-on:` is one of several spellings YAML accepts for the same key.
        # The line scan matches only the plain one, and a file needed just ONE
        # recognized line to set `found` and skip the structural check -- so a
        # second job spelled `"runs-on":` kept a hardcoded runner while the
        # guard reported success. That is the exact drift this script exists to
        # catch, so the parsed document decides, not the regex.
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "mixed.yml",
                       "on: push\njobs:\n"
                       "  good:\n    runs-on: " + switch.DYNAMIC + "\n"
                       '  sneaky:\n    "runs-on": ubuntu-latest\n    steps: []\n')
            problems = switch.check(Path(tmp))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("sneaky", problems[0])
        self.assertIn("ubuntu-latest", problems[0])

    def test_a_flow_mapping_job_is_read_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "flow.yml", "on: push\njobs:\n  a: {runs-on: ubuntu-latest, steps: []}\n")
            problems = switch.check(Path(tmp))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("ubuntu-latest", problems[0])

    def test_the_guard_reads_yaml_as_well_as_yml(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "other.yaml", "jobs:\n  a:\n    runs-on: ubuntu-latest\n")
            self.assertEqual(len(switch.check(Path(tmp))), 1)

    def test_an_unparseable_workflow_is_reported_not_certified_by_the_line_scan(self):
        # The line scan needs only ONE recognized `runs-on:` line to set
        # `found`, after which the rest of the file is never examined. Falling
        # back to it when the document itself will not parse therefore reports
        # success on a file the guard did not read, and a second hardcoded job
        # can sit unread in the same file -- exactly the drift the parsed
        # reading was added to catch. Round two closed this for a MISSING
        # parser and left it open for an ERRORING one.
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "broken.yml",
                       "on: push\njobs:\n  a:\n    runs-on: " + switch.DYNAMIC + "\n"
                       "broken: [\n")
            problems = switch.check(Path(tmp))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("could not be parsed", problems[0])

    def test_a_runner_outside_jobs_does_not_certify_a_jobless_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "stray.yml", "on: push\nmetadata:\n  runs-on: " + switch.DYNAMIC + "\n")
            problems = switch.check(Path(tmp))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("no runs-on found", problems[0])

    def test_a_workflow_that_parses_but_declares_no_jobs_is_not_called_unparseable(self):
        # The fail-closed rule covers documents that cannot be READ, not ones
        # that read fine and simply declare no jobs. Those the existing
        # `runs_on_required` path already reports, and widening the new rule to
        # swallow them would blame a parse failure that never happened.
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "nojobs.yml", "on: push\n")
            problems = switch.check(Path(tmp))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("no runs-on found", problems[0])
        self.assertNotIn("could not be parsed", problems[0])

    def test_check_mode_exits_non_zero_so_ci_actually_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "bad.yml", "jobs:\n  a:\n    runs-on: ubuntu-latest\n")
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                rc = switch.main(["--check", "--workflow-dir", tmp])
        self.assertEqual(rc, 1)

    def test_a_pinned_file_is_not_rewritten_by_the_converter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, "p.yml", f"# {switch.PIN_MARKER}\n    runs-on: self-hosted\n")
            with contextlib.redirect_stdout(io.StringIO()):
                switch.main(["--workflow-dir", tmp])
            self.assertIn("runs-on: self-hosted", path.read_text())

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = "jobs:\n  a:\n    runs-on: ubuntu-latest\n"
            path = self.write(tmp, "a.yml", original)
            with contextlib.redirect_stdout(io.StringIO()):
                switch.main(["--dry-run", "--workflow-dir", tmp])
            self.assertEqual(path.read_text(), original)


class SwitchFallbackTests(unittest.TestCase):
    """A repository already running on the VPS must not be converted back to billed minutes."""

    def write(self, tmp: str, name: str, body: str) -> Path:
        path = Path(tmp) / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_a_vps_repository_keeps_the_vps_when_the_variable_is_unset(self):
        # The whole point of the fallback flag. Converting a self-hosted
        # repository with the default fallback would hand every job back to
        # billed minutes the moment CI_RUNNER lapsed -- the exact cost the
        # migration to the VPS was made to avoid, and silent when it happens.
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, "a.yml", "on: push\njobs:\n  b:\n    runs-on: self-hosted\n")
            with contextlib.redirect_stdout(io.StringIO()):
                rc = switch.main(["--workflow-dir", tmp, "--fallback", "self-hosted"])
            text = path.read_text()
        self.assertEqual(rc, 0)
        self.assertIn("runs-on: ${{ vars.CI_RUNNER || 'self-hosted' }}", text)
        self.assertNotIn("ubuntu-latest", text)

    def test_the_guard_checks_against_the_repositorys_own_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "a.yml",
                       "on: push\njobs:\n  b:\n    runs-on: " + switch.dynamic_form("self-hosted") + "\n")
            self.assertEqual(switch.check(Path(tmp), switch.dynamic_form("self-hosted")), [])
            self.assertEqual(len(switch.check(Path(tmp))), 1, "the hosted fallback should still disagree")
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(switch.main(["--check", "--workflow-dir", tmp, "--fallback", "self-hosted"]), 0)
                self.assertEqual(switch.main(["--check", "--workflow-dir", tmp]), 1)

    def test_a_fallback_with_a_trailing_newline_is_refused(self):
        with self.assertRaises(ValueError):
            switch.dynamic_form("self-hosted\n")

    def test_a_fallback_that_could_escape_the_expression_is_refused(self):
        # The value lands between single quotes inside ${{ }}. A quote would
        # close that string and inject expression syntax into every workflow
        # this script writes, so it is refused rather than escaped -- and
        # refused before anything is written.
        original = "on: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, "a.yml", original)
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                rc = switch.main(["--workflow-dir", tmp, "--fallback", "x' }} ${{ github.token "])
            self.assertEqual(rc, 1)
            self.assertIn("invalid fallback", err.getvalue())
            self.assertEqual(path.read_text(), original, "nothing may be written on a refused fallback")


class SyncTests(unittest.TestCase):
    """The cross-repository sync must decide exactly as the in-Actions probe does."""

    def test_it_asks_for_the_same_four_endpoints_as_the_probe(self):
        # The probe and the sync are two implementations of one decision. If
        # their endpoint lists drift, one of them silently reads a different
        # account shape and the two disagree about the same quota.
        now = datetime.now(timezone.utc)
        window = f"year={now.year}&month={now.month}"
        self.assertEqual(sync.billing_candidates("someone"), [
            "https://api.github.com/users/someone/settings/billing/actions",
            "https://api.github.com/orgs/someone/settings/billing/actions",
            f"https://api.github.com/users/someone/settings/billing/usage?{window}",
            f"https://api.github.com/organizations/someone/settings/billing/usage?{window}",
        ])

    def test_it_reuses_the_pickers_decision_rather_than_reimplementing_it(self):
        # Loaded twice, so the code objects are not identical; what matters is
        # that the sync runs the repository's picker rather than its own copy.
        self.assertEqual(sync.pick.decide.__code__.co_filename, str(PICK_PATH))
        self.assertEqual(sync.pick.decide.__code__.co_code, pick.decide.__code__.co_code)

    def test_it_refuses_to_run_without_a_token(self):
        # The token is read from the environment only. A flag would be visible
        # to every process on the box through `ps`.
        with mock.patch.dict(os.environ, {"CI_RUNNER_TOKEN": ""}, clear=False):
            with contextlib.redirect_stderr(io.StringIO()) as err:
                rc = sync.main(["--owner", "o", "--repo", "r"])
        self.assertEqual(rc, 1)
        self.assertIn("CI_RUNNER_TOKEN", err.getvalue())

    def test_an_unreadable_variable_is_not_read_as_unset(self):
        # Three states, not two. A 404 is information -- the variable does not
        # exist. A timeout or a 5xx is not, and "" is what decide treats as
        # having no standing choice, so conflating them lets a blip pick a label
        # from a state that was never observed.
        for status in (0, 500, 403):
            with self.subTest(status=status):
                with mock.patch.object(sync, "request", return_value=(status, {}, None)):
                    self.assertIsNone(sync.current_runner("o", "r", "t"))
        with mock.patch.object(sync, "request", return_value=(404, {}, None)):
            self.assertEqual(sync.current_runner("o", "r", "t"), "")

    def test_a_200_without_a_string_value_is_unreadable(self):
        # The docstring already called a malformed 200 unreadable; the code only
        # checked that the payload was a dict. A missing `value` became "" --
        # indistinguishable from a genuine absence -- and a null one became the
        # literal string "None", a label nothing answers to, reported as read.
        for payload in ({}, {"value": None}, {"value": 7}, {"name": "CI_RUNNER"}):
            with self.subTest(payload=payload):
                with mock.patch.object(sync, "request", return_value=(200, {}, payload)):
                    self.assertIsNone(sync.current_runner("o", "r", "t"))
        with mock.patch.object(sync, "request", return_value=(200, {}, {"value": "self-hosted"})):
            self.assertEqual(sync.current_runner("o", "r", "t"), "self-hosted")

    def test_a_repository_whose_variable_cannot_be_read_is_skipped(self):
        methods = []

        def fake_request(url, token, method="GET", body=None):
            methods.append(method)
            if "settings/billing/actions" in url and "/users/" in url:
                return 200, {}, {"total_minutes_used": 10, "included_minutes": 2000}
            if url.endswith("/variables/CI_RUNNER") and method == "GET":
                return 500, {}, None
            return 404, {}, None

        with mock.patch.dict(os.environ, {"CI_RUNNER_TOKEN": "pat"}, clear=False), \
                mock.patch.object(sync, "request", side_effect=fake_request), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            rc = sync.main(["--owner", "o", "--repo", "r"])
        self.assertEqual(rc, 1, "an unobserved repository is a failure, not a silent pass")
        self.assertIn("skipped", out.getvalue())
        self.assertNotIn("PATCH", methods)
        self.assertNotIn("POST", methods)

    def test_a_paginated_report_decides_nothing(self):
        # One page of a report is not the report: a first page with no Actions
        # items would read as zero usage and move every repository onto an
        # allowance that may already be spent.
        with mock.patch.object(sync, "request", return_value=(200, {"Link": '<x>; rel="next"'}, {})):
            self.assertIsNone(sync.fetch_billing("o", "t"))

    def test_an_unreadable_quota_writes_nothing(self):
        # `changed` alone is not enough to write: with CI_RUNNER unset an
        # unreadable quota still reports changed, and writing then would commit
        # a label the picker never decided on.
        calls = []

        def fake_request(url, token, method="GET", body=None):
            calls.append((method, url))
            if "settings/billing" in url:
                return 404, {}, None
            return 404, {}, None   # CI_RUNNER not set yet

        with mock.patch.dict(os.environ, {"CI_RUNNER_TOKEN": "pat"}, clear=False), \
                mock.patch.object(sync, "request", side_effect=fake_request), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            rc = sync.main(["--owner", "o", "--repo", "r"])
        self.assertEqual(rc, 0)
        self.assertIn("left alone", out.getvalue())
        self.assertEqual([m for m, _ in calls if m in ("PATCH", "POST")], [])

    def test_a_healthy_quota_writes_the_hosted_label(self):
        def fake_request(url, token, method="GET", body=None):
            if "settings/billing/actions" in url and "/users/" in url:
                return 200, {}, {"total_minutes_used": 10, "included_minutes": 2000}
            if url.endswith("/variables/CI_RUNNER") and method == "GET":
                return 200, {}, {"value": "self-hosted"}
            if method == "PATCH":
                return 204, {}, None
            return 404, {}, None

        with mock.patch.dict(os.environ, {"CI_RUNNER_TOKEN": "pat"}, clear=False), \
                mock.patch.object(sync, "request", side_effect=fake_request), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            rc = sync.main(["--owner", "o", "--repo", "r"])
        self.assertEqual(rc, 0)
        self.assertIn("ubuntu-latest", out.getvalue())

    def test_dry_run_writes_nothing(self):
        methods = []

        def fake_request(url, token, method="GET", body=None):
            methods.append(method)
            if "settings/billing/actions" in url and "/users/" in url:
                return 200, {}, {"total_minutes_used": 1990, "included_minutes": 2000}
            if url.endswith("/variables/CI_RUNNER") and method == "GET":
                return 200, {}, {"value": "ubuntu-latest"}
            return 404, {}, None

        with mock.patch.dict(os.environ, {"CI_RUNNER_TOKEN": "pat"}, clear=False), \
                mock.patch.object(sync, "request", side_effect=fake_request), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            rc = sync.main(["--owner", "o", "--repo", "r", "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertIn("dry run", out.getvalue())
        self.assertNotIn("PATCH", methods)
        self.assertNotIn("POST", methods)


class SetupScriptTests(unittest.TestCase):
    """The VPS bootstrap runs on the machine that also runs workflow code."""

    def script(self) -> str:
        return (ROOT / "scripts" / "setup-vps-runner.sh").read_text(encoding="utf-8")

    def test_the_pat_never_reaches_a_command_line(self):
        # /proc/<pid>/cmdline is world-readable, so `-H "Authorization: Bearer
        # $PAT"` hands a long-lived credential to anyone who runs ps while the
        # request is in flight -- on the one box that also executes untrusted
        # workflow code. sync_ci_runner.py refuses a token on argv for this
        # reason; the shell has to hold the same line.
        offenders = [line.strip() for line in self.script().splitlines()
                     if "-H" in line and "Authorization" in line
                     and not line.lstrip().startswith("#")]
        self.assertEqual(offenders, [], "the PAT is on a command line")

    def test_the_pat_is_fed_through_a_curl_config_on_stdin(self):
        text = self.script()
        self.assertIn("-K -", text, "curl must read the credential from stdin")
        self.assertIn('header = "Authorization: Bearer %s"', text)

    def test_it_refuses_to_run_as_root(self):
        # A runner executes workflow code; root would hand it the machine.
        self.assertIn('[ "$(id -u)" -ne 0 ]', self.script())

    def _first_line_containing(self, needle: str) -> int:
        lines = self.script().splitlines()
        for index, line in enumerate(lines):
            if needle in line:
                return index
        raise AssertionError(f"{needle!r} is not in the script at all")

    def test_the_runner_user_is_resolved_before_anything_irreversible(self):
        # This check used to sit just above `svc.sh install` -- after a
        # registration token had been minted and config.sh had already
        # registered the runner and written ${dir}/.runner. A misspelt
        # --runner-user therefore exited leaving a runner registered with
        # GitHub and no service, and the corrected rerun matched that same
        # .runner file, said "already configured", and skipped the repository,
        # so no service was ever installed. Rerunning cannot undo a
        # registration, which is why the order is the fix.
        validated = self._first_line_containing('id -u "${RUNNER_USER}"')
        for irreversible in ("registration-token", "./config.sh", "sudo ./svc.sh install"):
            with self.subTest(step=irreversible):
                self.assertLess(validated, self._first_line_containing(irreversible),
                                f"--runner-user must be resolved before {irreversible}")

    def test_the_service_account_must_be_able_to_traverse_the_runner_tree(self):
        # The default root lives under the invoking account's $HOME, which is
        # routinely 0700 or 0750. Chowning the runner's own directory does not
        # help when an ancestor denies traversal, and `svc.sh install` succeeds
        # anyway -- installing a service that can never start. Reported, not
        # repaired: silently widening permissions on somebody's home directory
        # is not a side effect a setup script should have.
        self.assertIn('sudo -u "${RUNNER_USER}" test -x "${RUNNER_ROOT}"', self.script())
        self.assertLess(self._first_line_containing('test -x "${RUNNER_ROOT}"'),
                        self._first_line_containing("sudo ./svc.sh install"))


class RepositoryWiringTests(unittest.TestCase):
    """The shipped workflows must actually be wired the way the docs claim."""

    def test_the_build_workflow_follows_the_switch(self):
        text = (WORKFLOW_DIR / "python-app.yml").read_text(encoding="utf-8")
        self.assertIn(f"runs-on: {switch.DYNAMIC}", text)

    def test_an_unset_variable_falls_back_to_ubuntu_latest(self):
        # The fallback is what makes this change a no-op until somebody opts in.
        self.assertIn("|| 'ubuntu-latest'", switch.DYNAMIC)

    def test_the_probe_workflow_is_pinned_and_does_not_follow_the_switch(self):
        # If the probe followed CI_RUNNER it would try to run on a hosted runner
        # during the exact outage it exists to detect -- and worse, it would sit
        # on whatever runner pull-request code runs on, holding the PAT.
        spec = yaml.safe_load((WORKFLOW_DIR / "runner-mode.yml").read_text(encoding="utf-8"))
        self.assertIn(switch.PIN_MARKER, (WORKFLOW_DIR / "runner-mode.yml").read_text(encoding="utf-8"))
        self.assertNotIn("CI_RUNNER ", str(spec["jobs"]["decide"]["runs-on"]))
        self.assertIn("CI_PROBE_LABEL", str(spec["jobs"]["decide"]["runs-on"]))

    def test_ci_runs_the_drift_guard(self):
        text = (WORKFLOW_DIR / "python-app.yml").read_text(encoding="utf-8")
        self.assertIn("switch_runner.py --check", text)


RUNNER_MODE = WORKFLOW_DIR / "runner-mode.yml"


def step_script(job: str, step_name: str) -> str:
    """The shell a named workflow step actually runs."""
    spec = yaml.safe_load(RUNNER_MODE.read_text(encoding="utf-8"))
    for step in spec["jobs"][job]["steps"]:
        if step.get("name") == step_name:
            return step["run"]
    raise AssertionError(f"no step named {step_name!r} in job {job!r}")


def run_script(script: str, cwd: Path, **env):
    environment = {"PATH": os.environ["PATH"], "HOME": str(cwd), "GITHUB_OUTPUT": str(cwd / "gh_output")}
    # The bare environment keeps CI variables away from the step, not the
    # dynamic linker. On a self-hosted runner, setup-python's interpreter loads
    # libpython through LD_LIBRARY_PATH (hosted images register it system-wide),
    # and every step under test runs python3.
    if "LD_LIBRARY_PATH" in os.environ:
        environment["LD_LIBRARY_PATH"] = os.environ["LD_LIBRARY_PATH"]
    environment.update(env)
    (cwd / "gh_output").touch()
    return subprocess.run(["bash", "-c", script], cwd=cwd, env=environment,
                          capture_output=True, text=True, check=False)


CURL_STUB = """#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
method, out, url = "GET", None, None
for i, a in enumerate(args):
    if a == "-o" and i + 1 < len(args):
        out = args[i + 1]
    if a == "-X" and i + 1 < len(args):
        method = args[i + 1]
    if a.startswith("https://"):
        url = a
with open(os.environ["STUB_LOG"], "a") as handle:
    handle.write(method + " " + str(url) + "\\n")
code = "404"
for rule in os.environ.get("STUB_RULES", "").splitlines():
    pattern, _, rule_code = rule.strip().rpartition(" ")
    if pattern and pattern in method + " " + str(url):
        code = rule_code
        break
if out:
    with open(out, "w") as handle:
        handle.write(os.environ.get("STUB_BODY", "{}") if code.startswith("2") else '{"message":"Not Found"}')
sys.stdout.write(code)
"""


def with_stub_curl(cwd: Path, rules: str = "", body: str = "{}"):
    """Put a fake `curl` first on PATH and return the env to run a step with.

    String-matching a shell script proves the text says `break 2`; it cannot
    prove `break 2` does what the loop needs. Faking the one external command
    makes the real script runnable, so the mechanics are exercised rather than
    asserted.
    """
    binary = cwd / "bin"
    binary.mkdir(exist_ok=True)
    stub = binary / "curl"
    stub.write_text(CURL_STUB, encoding="utf-8")
    stub.chmod(0o755)
    log = cwd / "curl.log"
    log.touch()
    return {
        "PATH": f"{binary}:{os.environ['PATH']}",
        "STUB_LOG": str(log),
        "STUB_RULES": rules,
        "STUB_BODY": body,
    }


def attempts(cwd: Path) -> list[str]:
    return [line for line in (cwd / "curl.log").read_text().splitlines() if line.strip()]


class RunScriptTests(unittest.TestCase):
    def test_the_bare_environment_keeps_the_dynamic_linker_path(self):
        # Without it, setup-python's interpreter on a self-hosted runner cannot
        # load libpython, and every step test there failed with exit 127 while
        # hosted runners, which register the library system-wide, stayed green.
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"LD_LIBRARY_PATH": "/opt/toolcache/lib"}):
            result = run_script('printf %s "$LD_LIBRARY_PATH"', Path(tmp))
        self.assertEqual(result.stdout, "/opt/toolcache/lib")


class WorkflowShellTests(unittest.TestCase):
    """Execute the workflow's own shell.

    Unit tests, mutation manifests, flake8 and `--check` all run *around* the
    workflow YAML and never inside it, so a defect in the step sequencing is
    invisible to every one of them. That is not hypothetical: the billing step
    used to return early without creating `billing.json`, and the next step
    redirects from that file — which bash fails whatever the preceding exit
    code — so every scheduled run would have gone red in the default
    not-yet-configured state. These tests run the steps.
    """

    def test_the_billing_step_always_leaves_a_readable_payload(self):
        # The next step redirects from this file. Bash fails a redirection from
        # a missing file regardless of `set -e`, so "no token" must still
        # produce a file, not just a clean exit code.
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_script(step_script("decide", "Fetch Actions billing"), cwd, TOKEN="", OWNER="someone")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((cwd / "billing.json").is_file(), "billing.json must exist even with no token")

    def test_the_absent_token_is_reported_to_later_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            run_script(step_script("decide", "Fetch Actions billing"), cwd, TOKEN="", OWNER="someone")
            self.assertIn("token=absent", (cwd / "gh_output").read_text())

    def test_the_pick_step_survives_an_empty_payload(self):
        # The exact handoff the step above produces when no token is set.
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "scripts").mkdir()
            (cwd / "scripts" / "pick_runner.py").write_text(PICK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            (cwd / "billing.json").touch()
            result = run_script(
                step_script("decide", "Pick the runner"), cwd,
                MODE="inherit", VAR_MODE="", CURRENT="self-hosted", GITHUB_LABEL="",
                SELF_HOSTED_LABEL="", INCLUDED="", LOW="", HIGH="",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("undetermined", result.stdout)
            self.assertIn("changed: no", result.stdout)

    def test_the_pick_step_reads_a_real_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "scripts").mkdir()
            (cwd / "scripts" / "pick_runner.py").write_text(PICK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            (cwd / "billing.json").write_text(json.dumps({"total_minutes_used": 3000, "included_minutes": 3000}))
            result = run_script(
                step_script("decide", "Pick the runner"), cwd,
                MODE="inherit", VAR_MODE="auto", CURRENT="ubuntu-latest", GITHUB_LABEL="",
                SELF_HOSTED_LABEL="hetzner", INCLUDED="", LOW="", HIGH="",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("runner:  hetzner", result.stdout)

    def test_every_curl_bounds_its_own_runtime(self):
        # The concurrency group does not cancel in progress, so one hung request
        # silently queues every later probe behind it.
        spec = yaml.safe_load(RUNNER_MODE.read_text(encoding="utf-8"))
        invocations = 0
        for job in spec["jobs"].values():
            for step in job["steps"]:
                script = step.get("run") or ""
                # Shell comments mention curl without invoking it.
                body = "\n".join(line for line in script.splitlines() if not line.lstrip().startswith("#"))
                for chunk in body.split("curl ")[1:]:
                    invocations += 1
                    command = chunk.split(";")[0]
                    self.assertIn("--max-time", command)
                    self.assertIn("--connect-timeout", command)
        self.assertEqual(invocations, 3, "expected the billing GET and both variable writes")

    def test_a_probe_that_succeeds_first_stops_immediately(self):
        # The decisive check on `break 2`. With a bare `break` the outer loop
        # would carry on to orgs and overwrite a good 200 body with a 404 --
        # while the script still contains the string the other test matches.
        payload = '{"total_minutes_used": 10, "included_minutes": 3000}'
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = with_stub_curl(cwd, rules="users/someone/settings/billing/actions 200", body=payload)
            result = run_script(step_script("decide", "Fetch Actions billing"), cwd,
                                TOKEN="pat", OWNER="someone", **env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(attempts(cwd)), 1, f"expected one attempt, got {attempts(cwd)}")
            self.assertEqual((cwd / "billing.json").read_text(), payload)

    def test_an_org_owned_repository_resolves_on_the_last_candidate(self):
        payload = '{"usageItems": []}'
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = with_stub_curl(cwd, rules="organizations/someone/settings/billing/usage 200", body=payload)
            result = run_script(step_script("decide", "Fetch Actions billing"), cwd,
                                TOKEN="pat", OWNER="someone", **env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(attempts(cwd)), 4, f"all four candidates should be tried: {attempts(cwd)}")
            self.assertIn("organizations/someone/settings/billing/usage", attempts(cwd)[-1])
            self.assertEqual((cwd / "billing.json").read_text(), payload)

    def test_every_combination_failing_leaves_an_empty_payload(self):
        # Not a 404 body: pick_runner must read this as undetermined, and a
        # `{"message": "Not Found"}` left in place parses as an unknown shape --
        # same verdict, but only by luck.
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = with_stub_curl(cwd)
            result = run_script(step_script("decide", "Fetch Actions billing"), cwd,
                                TOKEN="pat", OWNER="someone", **env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(attempts(cwd)), 4)
            self.assertEqual((cwd / "billing.json").read_text(), "")

    def test_the_reset_creates_the_variable_when_it_does_not_exist_yet(self):
        # Dispatching the escape hatch before the probe has ever run: PATCH 404s
        # because there is nothing to patch, and POST must create it.
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = with_stub_curl(cwd, rules="POST https://api.github.com/repos/o/r/actions/variables 201")
            result = run_script(step_script("reset", "Force CI_RUNNER back to the hosted runner"), cwd,
                                TOKEN="pat", REPO="o/r", RUNNER="ubuntu-latest", **env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual([line.split()[0] for line in attempts(cwd)], ["PATCH", "POST"])

    def test_the_reset_succeeds_outright_when_the_variable_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = with_stub_curl(cwd, rules="PATCH https://api.github.com/repos/o/r/actions/variables/CI_RUNNER 204")
            result = run_script(step_script("reset", "Force CI_RUNNER back to the hosted runner"), cwd,
                                TOKEN="pat", REPO="o/r", RUNNER="ubuntu-latest", **env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(attempts(cwd)), 1)

    def test_the_reset_fails_loudly_when_the_api_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = with_stub_curl(cwd, rules="PATCH https://api.github.com 403")
            result = run_script(step_script("reset", "Force CI_RUNNER back to the hosted runner"), cwd,
                                TOKEN="pat", REPO="o/r", RUNNER="ubuntu-latest", **env)
            self.assertNotEqual(result.returncode, 0, "a refused reset must not report success")

    def test_the_reset_names_the_manual_route_when_no_token_is_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result = run_script(step_script("reset", "Force CI_RUNNER back to the hosted runner"), cwd,
                                TOKEN="", REPO="o/r", RUNNER="ubuntu-latest")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("gh variable set", result.stdout + result.stderr)

    def test_a_paginated_report_is_reported_incomplete(self):
        # A Link header offering a next page means this is one page of a report,
        # and one page carrying no Actions items is not zero usage.
        payload = '{"usageItems": []}'
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = with_stub_curl(cwd, rules="users/someone/settings/billing/actions 200", body=payload)
            stub = cwd / "bin" / "curl"
            stub.write_text(stub.read_text(encoding="utf-8").replace(
                'if out:',
                'for i, a in enumerate(args):\n'
                '    if a == "-D" and i + 1 < len(args):\n'
                '        open(args[i + 1], "w").write(\'HTTP/2 200\\nLink: <x>; rel="next"\\n\')\n'
                'if out:'), encoding="utf-8")
            result = run_script(step_script("decide", "Fetch Actions billing"), cwd,
                                TOKEN="pat", OWNER="someone", **env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("incomplete", (cwd / "billing.json").read_text())

    def test_the_probe_requests_exactly_the_four_documented_endpoints(self):
        # Pins the URLs themselves, which the loop-mechanics tests cannot: they
        # tell the stub which URL returns 200, so an invented path would still
        # "work" there. Two things vary and neither is knowable from here -- the
        # owner may be a user or an org, and the account may be on the legacy or
        # the enhanced billing platform -- but the enhanced platform does not
        # mirror the legacy paths, so the combinations are not a product.
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = with_stub_curl(cwd)
            run_script(step_script("decide", "Fetch Actions billing"), cwd,
                       TOKEN="pat", OWNER="someone", **env)
            urls = [line.split(" ", 1)[1] for line in attempts(cwd)]
        now = datetime.now(timezone.utc)
        window = f"year={now.year}&month={now.month}"
        self.assertEqual(urls, [
            "https://api.github.com/users/someone/settings/billing/actions",
            "https://api.github.com/orgs/someone/settings/billing/actions",
            f"https://api.github.com/users/someone/settings/billing/usage?{window}",
            f"https://api.github.com/organizations/someone/settings/billing/usage?{window}",
        ])

    def test_the_enhanced_report_is_scoped_to_one_month(self):
        # The allowance is monthly. A year-wide report would overstate minutes
        # used, clamp the remainder to zero and pin every job to the VPS for
        # good -- a wrong decision, where a rejected request is merely no
        # decision at all.
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = with_stub_curl(cwd)
            run_script(step_script("decide", "Fetch Actions billing"), cwd,
                       TOKEN="pat", OWNER="someone", **env)
            enhanced = [line for line in attempts(cwd) if "/usage" in line]
        self.assertEqual(len(enhanced), 2)
        for line in enhanced:
            self.assertIn("month=", line)
            self.assertIn(f"year={datetime.now(timezone.utc).year}", line)


class EscapeHatchTests(unittest.TestCase):
    """The deadlock this design can otherwise reach."""

    def spec(self):
        return yaml.safe_load(RUNNER_MODE.read_text(encoding="utf-8"))

    def test_the_reset_job_runs_on_a_hosted_runner(self):
        # If CI_RUNNER names a self-hosted runner that is gone, a reset pinned to
        # that same runner could never run — which is precisely when it is needed.
        self.assertEqual(self.spec()["jobs"]["reset"]["runs-on"], "ubuntu-latest")

    def test_the_reset_job_only_runs_when_a_human_asks(self):
        self.assertIn("inputs.reset", str(self.spec()["jobs"]["reset"]["if"]))

    def test_the_reset_is_not_held_by_the_probe_lock(self):
        # The probe can sit queued for an offline self-hosted runner. A
        # workflow-level group would hold a dispatched reset behind it, and
        # GitHub keeps only one pending run per group, so the next scheduled
        # probe would displace that pending reset -- defeating the escape hatch
        # in exactly the outage it exists for.
        spec = self.spec()
        self.assertNotIn("concurrency", spec, "concurrency must not be workflow-level")
        self.assertIsNone(spec["jobs"]["reset"].get("concurrency"))
        self.assertIsNotNone(spec["jobs"]["decide"].get("concurrency"))

    def test_the_scheduled_probe_stands_down_during_a_reset(self):
        self.assertIn("!inputs.reset", str(self.spec()["jobs"]["decide"]["if"]))

    def test_the_probe_needs_a_runner_of_its_own(self):
        # The probe holds CI_RUNNER_TOKEN. A self-hosted runner is persistent and
        # its jobs share a user, so pull-request code -- `pip install` and
        # `pytest` in python-app.yml -- could read the PAT out of a later job's
        # environment. A separate label is the isolation; no default is what
        # stops it silently sharing one.
        decide = self.spec()["jobs"]["decide"]
        self.assertIn("CI_PROBE_LABEL != ''", str(decide["if"]))
        self.assertEqual(str(decide["runs-on"]).strip(), "${{ vars.CI_PROBE_LABEL }}")

    def test_the_guard_precedes_every_step_that_sees_the_token(self):
        # The invariant is ordering against the token, not against the step
        # list: checkout moved ahead of the guard when the guard became a
        # repository script, and checkout uses GITHUB_TOKEN rather than the PAT.
        steps = self.spec()["jobs"]["decide"]["steps"]
        guard = next(i for i, s in enumerate(steps)
                     if s.get("name") == "Refuse to run beside untrusted code")
        token_steps = [i for i, s in enumerate(steps)
                       if "CI_RUNNER_TOKEN" in str(s.get("env", ""))]
        self.assertTrue(token_steps, "expected at least one step to carry the PAT")
        self.assertLess(guard, min(token_steps))

    def test_a_label_every_self_hosted_runner_carries_is_not_isolation(self):
        # The class the previous three rounds each missed one instance of: a
        # label does not identify a machine. GitHub gives every self-hosted
        # runner `self-hosted` plus its OS and arch, so a probe registered as
        # `probe-runner` still answers `runs-on: self-hosted`.
        self.assertTrue(pick.probe_conflicts(probe="probe-runner", current="self-hosted",
                                             github_label="ubuntu-latest", self_hosted_label="vps"))
        self.assertTrue(pick.probe_conflicts(probe="self-hosted", current="",
                                             github_label="ubuntu-latest", self_hosted_label="vps"))
        for auto in ("Linux", "X64", "ARM64"):
            with self.subTest(auto=auto):
                self.assertTrue(pick.probe_conflicts(probe="probe", current=auto,
                                                     github_label="ubuntu-latest", self_hosted_label="vps"))
        self.assertEqual(pick.probe_conflicts(probe="probe-runner", current="vps",
                                              github_label="ubuntu-latest", self_hosted_label="vps"), [])

    def test_the_guard_compares_the_value_the_picker_will_emit(self):
        # `_one_line` turns an embedded newline into a space before the label is
        # written, so two values differing only there are one label once emitted.
        self.assertEqual(pick.normalize_label("probe\nrunner"), pick.normalize_label("probe runner"))
        self.assertTrue(pick.probe_conflicts(probe="probe runner", current="probe\nrunner",
                                             github_label="ubuntu-latest", self_hosted_label="vps"))

    def test_labels_are_folded_beyond_ascii(self):
        # `tr '[:upper:]' '[:lower:]'`, which this replaced, leaves every
        # non-ASCII letter alone while GitHub matches them case-insensitively.
        self.assertEqual(pick.normalize_label("ÄBC"), pick.normalize_label("äbc"))
        self.assertTrue(pick.probe_conflicts(probe="ÄBC", current="äbc",
                                             github_label="ubuntu-latest", self_hosted_label="vps"))

    def test_the_guard_uses_the_pickers_own_defaults(self):
        # Not a second copy of the defaults: the check is the picker's module,
        # so a default can only change in one place.
        import inspect
        signature = inspect.signature(pick.main)
        self.assertTrue(hasattr(pick, "probe_conflicts"))
        self.assertIsNotNone(signature)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "scripts").mkdir()
            (cwd / "scripts" / "pick_runner.py").write_text(PICK_PATH.read_text(encoding="utf-8"),
                                                            encoding="utf-8")
            unset = run_script(step_script("decide", "Refuse to run beside untrusted code"), cwd,
                               PROBE="self-hosted", CURRENT="", SELF_HOSTED="", HOSTED="")
            ok = run_script(step_script("decide", "Refuse to run beside untrusted code"), cwd,
                            PROBE="probe-runner", CURRENT="vps", SELF_HOSTED="vps", HOSTED="ubuntu-latest")
        self.assertNotEqual(unset.returncode, 0, "the picker's unset defaults must still be guarded")
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_a_blank_probe_label_is_rejected_rather_than_approved(self):
        # `wanted` normalizing to empty used to return "no conflicts", which the
        # CLI prints as isolation confirmed. The workflow's `!= ''` passes for a
        # whitespace-only variable, so that certified a setup whose probe job
        # queues forever against a label no runner registers.
        for blank in ("", "   ", "\t", "\n "):
            with self.subTest(blank=blank):
                self.assertTrue(pick.probe_conflicts(probe=blank, current="vps",
                                                     github_label="ubuntu-latest",
                                                     self_hosted_label="vps"))
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "scripts").mkdir()
            (cwd / "scripts" / "pick_runner.py").write_text(PICK_PATH.read_text(encoding="utf-8"),
                                                            encoding="utf-8")
            blank = run_script(step_script("decide", "Refuse to run beside untrusted code"), cwd,
                               PROBE="   ", CURRENT="vps", SELF_HOSTED="vps", HOSTED="ubuntu-latest",
                               RUNNER_OS="Linux", RUNNER_ARCH="X64")
        self.assertNotEqual(blank.returncode, 0, "a whitespace-only probe label must fail the guard")

    def test_only_the_probes_own_platform_labels_collide(self):
        # A self-hosted runner carries `self-hosted` plus ONE OS and ONE arch,
        # not the whole vocabulary. Rejecting `CI_SELF_HOSTED_LABEL=windows` for
        # a Linux probe refuses a setup that is genuinely disjoint.
        linux = dict(probe="probe-runner", current="", github_label="ubuntu-latest",
                     os_name="Linux", arch="X64")
        for disjoint in ("windows", "macos", "arm64", "arm"):
            with self.subTest(disjoint=disjoint):
                self.assertEqual(pick.probe_conflicts(self_hosted_label=disjoint, **linux), [])
        for shared in ("linux", "x64", "self-hosted"):
            with self.subTest(shared=shared):
                self.assertTrue(pick.probe_conflicts(self_hosted_label=shared, **linux))

    def test_an_unknown_probe_platform_keeps_every_candidate(self):
        # Narrowing is allowed on evidence only. Not knowing the probe's OS is
        # not evidence that `windows` names a different machine, so the unknown
        # case must stay as conservative as the version before narrowing.
        for os_name, arch in (("", ""), ("Plan9", "s390x")):
            with self.subTest(os_name=os_name, arch=arch):
                self.assertTrue(pick.probe_conflicts(probe="probe-runner", current="",
                                                     github_label="ubuntu-latest",
                                                     self_hosted_label="windows",
                                                     os_name=os_name, arch=arch))
        self.assertEqual(pick.auto_labels(os_name="Linux", arch="X64"), {"self-hosted", "linux", "x64"})
        self.assertEqual(pick.auto_labels(), pick.AUTO_SELF_HOSTED_LABELS)

    def test_os_and_arch_narrow_independently(self):
        # Review round 5 mutated the per-field narrowing into joint widening
        # (either field unreadable -> widen both) and the whole suite stayed
        # green, so nothing pinned this. The safe direction was untested, which
        # is still untested. A readable OS must keep ruling out the other two OS
        # labels even when the architecture cannot be read.
        self.assertEqual(pick.auto_labels(os_name="Linux", arch=""),
                         {"self-hosted", "linux"} | set(pick.AUTO_ARCH_LABELS))
        self.assertEqual(pick.auto_labels(os_name="", arch="X64"),
                         {"self-hosted", "x64"} | set(pick.AUTO_OS_LABELS))
        # The consequence that matters: an unreadable arch must not resurrect
        # `windows` for a machine known to be Linux.
        self.assertEqual(pick.probe_conflicts(probe="probe-runner", current="",
                                              github_label="ubuntu-latest",
                                              self_hosted_label="windows",
                                              os_name="Linux", arch=""), [])

    def test_every_documented_runner_arch_is_treated_as_shared(self):
        # A label missing from the vocabulary is not the safe "unrecognized"
        # case -- it is never treated as shared at all. `x86` was absent from
        # this set before round 5 and reported `CI_SELF_HOSTED_LABEL=x86` as
        # isolated, so the vocabulary is pinned to what RUNNER_ARCH documents.
        self.assertEqual(set(pick.AUTO_ARCH_LABELS), {"x86", "x64", "arm", "arm64"})
        for arch in ("X86", "X64", "ARM", "ARM64"):
            with self.subTest(arch=arch):
                self.assertTrue(pick.probe_conflicts(probe="probe-runner", current="",
                                                     github_label="ubuntu-latest",
                                                     self_hosted_label=arch,
                                                     os_name="Linux", arch=arch))

    def test_the_guard_reads_the_platform_of_the_machine_it_runs_on(self):
        # The narrowing is only sound because this job runs ON the probe. If the
        # step stopped passing RUNNER_OS/RUNNER_ARCH the guard would silently
        # widen back, so the wiring itself is asserted.
        script = step_script("decide", "Refuse to run beside untrusted code")
        self.assertIn("--probe-os", script)
        self.assertIn("RUNNER_OS", script)
        self.assertIn("--probe-arch", script)
        self.assertIn("RUNNER_ARCH", script)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "scripts").mkdir()
            (cwd / "scripts" / "pick_runner.py").write_text(PICK_PATH.read_text(encoding="utf-8"),
                                                            encoding="utf-8")
            disjoint = run_script(script, cwd, PROBE="probe-runner", CURRENT="",
                                  SELF_HOSTED="windows", HOSTED="ubuntu-latest",
                                  RUNNER_OS="Linux", RUNNER_ARCH="X64")
            shared = run_script(script, cwd, PROBE="probe-runner", CURRENT="",
                                SELF_HOSTED="linux", HOSTED="ubuntu-latest",
                                RUNNER_OS="Linux", RUNNER_ARCH="X64")
        self.assertEqual(disjoint.returncode, 0, disjoint.stderr)
        self.assertNotEqual(shared.returncode, 0, "the probe's own OS label must still collide")

    def test_a_paginated_report_is_not_a_report(self):
        # One page carrying no Actions items is a partial view, not zero usage.
        self.assertIsNone(pick.read_quota({"incomplete": True}, 3000).remaining)

    def test_an_undetermined_decision_never_writes_the_variable(self):
        # Otherwise `undetermined` reports that a decision was refused while the
        # variable is rewritten anyway.
        apply_step = next(s for s in self.spec()["jobs"]["decide"]["steps"]
                          if s.get("name") == "Apply the decision")
        self.assertIn("undetermined != 'true'", apply_step["if"])

    def test_no_workflow_interpolates_an_expression_into_a_shell_script(self):
        # `${{ }}` is substituted into the script text before bash sees it, so a
        # value carrying a backtick or $( ) executes. Values belong in `env:`.
        offenders = []
        for path in switch.workflow_files(WORKFLOW_DIR):
            spec = yaml.safe_load(path.read_text(encoding="utf-8"))
            for job_name, job in (spec.get("jobs") or {}).items():
                for step in job.get("steps") or []:
                    if "${{" in (step.get("run") or ""):
                        offenders.append(f"{path.name}:{job_name}:{step.get('name')}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
