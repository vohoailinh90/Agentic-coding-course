from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run-routing-evals.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_routing_evals", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BlindWorkspaceTests(unittest.TestCase):
    def test_copy_keeps_classifier_inputs_and_excludes_label_sources(self) -> None:
        runner = load_runner()

        with tempfile.TemporaryDirectory() as directory:
            workspace = runner.create_blind_workspace(Path(directory))

            for relative in (
                "CLAUDE.md",
                ".claude/skills/classify-requirement/SKILL.md",
                "agent-routing/complexity-rubric.md",
                "agent-routing/policy.yaml",
                "evals/routing-cases.yaml",
            ):
                with self.subTest(included=relative):
                    self.assertTrue((workspace / relative).is_file())

            for relative in (
                ".git",
                "artifacts",
                "evals/expected-routing.yaml",
                "evals/results",
                "requirements/examples",
            ):
                with self.subTest(excluded=relative):
                    self.assertFalse((workspace / relative).exists())


class ResolverChecksTests(unittest.TestCase):
    """The runner scores the model's route AND the route policy.yaml assigns to
    the model's own scores, so a policy-application error is attributable."""

    def setUp(self) -> None:
        self.runner = load_runner()
        self.resolver = self.runner.load_resolver()
        self.policy = self.resolver.load_policy(self.runner.POLICY_PATH)
        self.expected = {
            "tier": "T2", "strategy": "main_with_architect_and_reviewer",
            "required_agents": ["code-reviewer"], "max_agent_invocations": 2,
            "parallelizable": False, "human_gate": False,
        }

    def emitted(self, **overrides):
        native = {
            "classification": {"ambiguity": 0, "scope": 1, "architecture": 0,
                               "dependencies": 0, "risk": 2, "verification": 1},
            "raw_score": 4, "signals": ["exposes-secret"], "score_tier": "T1",
            "overrides_applied": ["security-sensitive"], "final_tier": "T2",
            "strategy": "main_with_architect_and_reviewer", "required_agents": ["code-reviewer"],
            "max_agent_invocations": 2, "parallelizable": False,
            "human_gate": {"required": False, "reason": None},
        }
        native.update(overrides)
        return self.runner.normalize(native)

    def checks_for(self, actual):
        resolved = self.runner.resolved_route(self.resolver, self.policy, actual)
        return self.runner.resolver_checks(actual, self.expected, resolved)

    def test_a_correct_route_agrees_with_the_resolver_and_passes(self) -> None:
        self.assertEqual(self.checks_for(self.emitted()), {"resolver_agrees": True, "resolved_route_pass": True})

    def test_right_scores_wrongly_routed_is_a_policy_application_error(self) -> None:
        actual = self.emitted(overrides_applied=[], final_tier="T1", strategy="main_with_reviewer", max_agent_invocations=1)
        self.assertFalse(self.runner.compare(actual, self.expected)["route_pass"])
        self.assertEqual(self.checks_for(actual), {"resolver_agrees": False, "resolved_route_pass": True})

    def test_wrong_scores_correctly_routed_is_a_scoring_error(self) -> None:
        actual = self.emitted(signals=[], overrides_applied=[], final_tier="T1",
                              strategy="main_with_reviewer", max_agent_invocations=1)
        self.assertEqual(self.checks_for(actual), {"resolver_agrees": True, "resolved_route_pass": False})

    def test_the_parallelizable_judgement_stays_with_the_model(self) -> None:
        actual = self.emitted(parallelizable=True)
        self.assertEqual(self.checks_for(actual), {"resolver_agrees": True, "resolved_route_pass": False})

    def test_an_unresolvable_emission_fails_both_checks(self) -> None:
        actual = self.emitted(classification={"ambiguity": 7})
        self.assertIsNone(self.runner.resolved_route(self.resolver, self.policy, actual))
        self.assertEqual(self.checks_for(actual), {"resolver_agrees": False, "resolved_route_pass": False})

    def test_the_blind_prompt_allows_the_resolver_but_never_recording(self) -> None:
        prompt = self.runner.build_prompt("REQ-001", "x")
        self.assertIn("scripts/route.py", prompt)
        self.assertIn("never with --record", prompt)


if __name__ == "__main__":
    unittest.main()
