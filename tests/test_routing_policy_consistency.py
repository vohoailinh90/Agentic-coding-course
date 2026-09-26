"""Deterministic consistency checks across policy, oracle and classifier schema.

These three files encode the same routing contract in three places. When they
drift, the eval fails in ways that look like classifier error but are not — a
strategy renamed in policy.yaml but not in the schema enum rejects every valid
classification. That is a computable check, so it belongs in a test rather than
in a reviewer's reading. See CLAUDE.md, "Deterministic work is not agent work".
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run-routing-evals.py"
POLICY_PATH = ROOT / "agent-routing" / "policy.yaml"
ORACLE_PATH = ROOT / "evals" / "expected-routing.yaml"
CASES_PATH = ROOT / "evals" / "routing-cases.yaml"
AGENTS_DIR = ROOT / ".claude" / "agents"


def agent_frontmatter(name: str) -> dict:
    """Parse one agent definition's YAML frontmatter."""
    _, frontmatter, _ = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8").split("---\n", 2)
    return yaml.safe_load(frontmatter)


def load_runner():
    spec = importlib.util.spec_from_file_location("run_routing_evals", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class PolicyOracleSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_yaml(POLICY_PATH)
        self.oracle = load_yaml(ORACLE_PATH)["expected"]
        self.runner = load_runner()
        self.schema = self.runner.CLASSIFICATION_SCHEMA["properties"]

    def test_every_oracle_strategy_is_accepted_by_the_classifier_schema(self) -> None:
        allowed = set(self.schema["strategy"]["enum"])
        for case in self.oracle:
            with self.subTest(case=case["id"]):
                self.assertIn(case["strategy"], allowed)

    def test_policy_and_schema_agree_on_strategy_names(self) -> None:
        policy_strategies = {
            profile["strategy"] for profile in self.policy["profiles"].values()
        }
        self.assertEqual(policy_strategies, set(self.schema["strategy"]["enum"]))

    def _ambiguity_thresholds_by_tier(self) -> dict[str, int]:
        """Tiers whose conditional_agents fires on an ambiguity threshold.

        Derived from policy data rather than hardcoded, so a future tier that
        gains the same kind of conditional analyst is covered automatically.
        """

        thresholds: dict[str, int] = {}
        for tier, profile in self.policy["profiles"].items():
            for entry in profile.get("conditional_agents", []):
                threshold = entry.get("when_ambiguity_dimension_at_least")
                if threshold is not None:
                    thresholds[tier] = threshold
        return thresholds

    def test_oracle_budget_matches_the_policy_ceiling_for_its_tier(self) -> None:
        """The ceiling is the base per-tier budget, plus analyst_reserve when
        the oracle's own ambiguity score meets the conditional's threshold.

        Escalation_reserve is not added here: it is only ever granted after a
        reviewer reads a diff and formally escalates, which no static oracle
        fixture can encode — the oracle documents the classification-time
        ceiling, not what a live run might additionally earn mid-review.
        """

        ceilings = self.policy["budget"]["max_agent_invocations"]
        analyst_reserve = self.policy["budget"].get("analyst_reserve", {})
        thresholds = self._ambiguity_thresholds_by_tier()
        for case in self.oracle:
            with self.subTest(case=case["id"]):
                expected = ceilings[case["tier"]]
                threshold = thresholds.get(case["tier"])
                if (
                    threshold is not None
                    and case["tier"] in analyst_reserve
                    and case["semantic_hints"]["ambiguity"] >= threshold
                ):
                    expected += analyst_reserve[case["tier"]]
                self.assertEqual(case["max_agent_invocations"], expected)

    def test_no_oracle_roster_exceeds_its_own_budget(self) -> None:
        for case in self.oracle:
            with self.subTest(case=case["id"]):
                self.assertLessEqual(
                    len(case["required_agents"]), case["max_agent_invocations"]
                )

    def test_oracle_rosters_contain_the_profile_floor(self) -> None:
        for case in self.oracle:
            floor = set(self.policy["profiles"][case["tier"]]["required_agents"])
            with self.subTest(case=case["id"]):
                self.assertTrue(floor.issubset(set(case["required_agents"])))

    def test_oracle_agents_are_defined_and_schema_known(self) -> None:
        defined = {path.stem for path in AGENTS_DIR.glob("*.md")}
        for case in self.oracle:
            for agent in case["required_agents"]:
                with self.subTest(case=case["id"], agent=agent):
                    self.assertIn(agent, defined)
                    self.assertIn(agent, self.runner.AGENT_NAMES)

    def test_oracle_covers_every_blind_case_exactly_once(self) -> None:
        case_ids = [case["id"] for case in load_yaml(CASES_PATH)["cases"]]
        oracle_ids = [case["id"] for case in self.oracle]
        self.assertEqual(sorted(case_ids), sorted(oracle_ids))
        self.assertEqual(len(oracle_ids), len(set(oracle_ids)))


class SignalTaxonomyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_yaml(POLICY_PATH)
        self.oracle = load_yaml(ORACLE_PATH)["expected"]
        self.exempt = set(self.policy["signal_taxonomy"]["read_only_exempt"])

    def override_vocabulary(self) -> set[str]:
        vocabulary: set[str] = set()
        for override in self.policy["overrides"]:
            vocabulary.update(override.get("match_any_signal", []))
            vocabulary.update(override.get("match_all_signals", []))
        return vocabulary

    def test_no_read_only_signal_appears_in_any_override(self) -> None:
        """The exemption is meaningless if a read-only signal can still match."""

        overlap = self.exempt & self.override_vocabulary()
        self.assertEqual(overlap, set(), f"read-only signals are override-eligible: {overlap}")

    def test_no_oracle_case_emits_a_read_only_signal(self) -> None:
        for case in self.oracle:
            with self.subTest(case=case["id"]):
                self.assertEqual(set(case["signals"]) & self.exempt, set())

    def test_every_signal_is_verb_first(self) -> None:
        """A signal names an action. A bare noun is the false-positive shape.

        There are no exceptions to this. An earlier revision allowlisted two
        noun signals it could not phrase as verbs, which made the test certify
        the exact vocabulary shape it exists to prohibit — and, because the
        check was a prefix match, silently admitted anything extending them
        (`distributed-coordination-documentation` would have passed). Matching
        the first word exactly closes both holes.
        """

        verbs = {
            "adds", "calls", "changes", "coordinates", "creates", "deletes",
            "drops", "executes", "exposes", "issues", "migrates", "moves",
            "reads", "requires", "rolls", "rotates", "runs", "stores", "uses",
            "writes",
        }
        vocabulary = self.override_vocabulary() | self.exempt
        for case in self.oracle:
            vocabulary.update(case["signals"])

        self.assertTrue(vocabulary, "no signals found to check")
        for signal in sorted(vocabulary):
            with self.subTest(signal=signal):
                head = signal.split("-", 1)[0]
                self.assertIn(
                    head,
                    verbs,
                    f"{signal!r} does not begin with an action verb; nouns cause the "
                    "override false positives this taxonomy exists to prevent",
                )


class AgentBudgetFrontmatterTests(unittest.TestCase):
    def test_every_agent_declares_a_turn_ceiling_and_effort(self) -> None:
        agents = sorted(AGENTS_DIR.glob("*.md"))
        self.assertTrue(agents, "no agent definitions found")
        for path in agents:
            meta = agent_frontmatter(path.stem)
            with self.subTest(agent=path.stem):
                self.assertIsInstance(meta.get("maxTurns"), int)
                self.assertGreater(meta["maxTurns"], 0)
                self.assertIn(meta.get("effort"), {"low", "medium", "high", "xhigh", "max"})


class SettingsExampleTests(unittest.TestCase):
    def test_example_settings_never_enable_agent_teams(self) -> None:
        """Agent teams multiply token cost; no profile here uses them."""

        text = (ROOT / ".claude" / "settings.example.json").read_text(encoding="utf-8")
        self.assertNotIn("AGENT_TEAMS", text)


class ConditionalAgentTests(unittest.TestCase):
    """A condition the classifier cannot evaluate is prose, not policy."""

    def setUp(self) -> None:
        self.policy = load_yaml(POLICY_PATH)
        self.oracle = load_yaml(ORACLE_PATH)["expected"]

    def conditionals(self):
        for tier, profile in self.policy["profiles"].items():
            for entry in profile.get("conditional_agents", []):
                yield tier, entry

    def test_conditions_are_machine_checkable(self) -> None:
        for tier, entry in self.conditionals():
            with self.subTest(tier=tier, agent=entry["agent"]):
                self.assertTrue(
                    entry.get("when_any_signal")
                    or entry.get("when_architecture_dimension_at_least")
                    or entry.get("when_ambiguity_dimension_at_least"),
                    "a conditional agent needs a signal list or a dimension threshold, "
                    "not a prose predicate the classifier cannot evaluate",
                )

    def test_condition_signals_exist_in_the_override_vocabulary(self) -> None:
        vocabulary: set[str] = set()
        for override in self.policy["overrides"]:
            vocabulary.update(override.get("match_any_signal", []))
            vocabulary.update(override.get("match_all_signals", []))
        for tier, entry in self.conditionals():
            for signal in entry.get("when_any_signal", []):
                with self.subTest(tier=tier, signal=signal):
                    self.assertIn(signal, vocabulary)

    def test_every_conditional_agent_is_exercised_by_a_fixture(self) -> None:
        """An untested branch of the policy is an unverified claim about it."""

        for tier, entry in self.conditionals():
            agent = entry["agent"]
            fired = [
                case["id"]
                for case in self.oracle
                if case["tier"] == tier and agent in case["required_agents"]
            ]
            with self.subTest(tier=tier, agent=agent):
                self.assertTrue(
                    fired,
                    f"no {tier} fixture fires the conditional {agent}; add one or the "
                    "condition is never verified",
                )


class EscalationReserveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_yaml(POLICY_PATH)
        self.budget = self.policy["budget"]

    def test_reserve_never_exists_at_tiers_that_cannot_produce_the_finding(self) -> None:
        """T0 does no independent verification; T1's risk domains are already
        forced to T2+ by the policy overrides, so neither tier can produce a
        verification-design escalation for this reserve to unblock."""

        self.assertEqual(set(self.budget["escalation_reserve"]) & {"T0", "T1"}, set())

    def _worst_case_base_consumption(self, tier: str) -> int:
        """Every invocation the base budget must cover before any reserve.

        Required agents and mandatory extra critique/architecture rounds are
        always counted. A conditional agent is counted once per distinct
        agent name, not once per conditional_agents entry — an agent with
        multiple independently-sufficient entries (OR across arms) is still
        only one invocation when any arm fires — and only if that agent is
        not already paid for by its own separate reserve (e.g.
        requirement-analyst's analyst_reserve), since that budget is
        independent of this one.
        """

        profile = self.policy["profiles"][tier]
        reserved_agents: set[str] = set()
        analyst_reserve = self.budget.get("analyst_reserve", {})
        if tier in analyst_reserve:
            reserved_agents.update(analyst_reserve.get("grantable_agents", []))
        worst_case = len(profile["required_agents"])
        worst_case += profile.get("max_architecture_critique_rounds", 0)
        conditional_agent_names = {
            entry["agent"]
            for entry in profile.get("conditional_agents", [])
            if entry["agent"] not in reserved_agents
        }
        worst_case += len(conditional_agent_names)
        return worst_case

    def test_every_reserved_tier_leaves_room_to_escalate_after_its_worst_case(self) -> None:
        """Whatever combination of required/conditional agents can legally
        consume a reserved tier's base budget, the reserve must still leave
        at least one more invocation for the escalation it exists to unblock.
        """

        for tier, reserve in self.budget["escalation_reserve"].items():
            if tier not in self.policy["profiles"]:
                continue
            with self.subTest(tier=tier):
                worst_case = self._worst_case_base_consumption(tier)
                ceiling = self.budget["max_agent_invocations"][tier]
                self.assertEqual(
                    worst_case,
                    ceiling,
                    f"{tier}: worst-case base consumption no longer equals the "
                    "ceiling; re-derive whether this reserve is still needed",
                )
                self.assertGreaterEqual(
                    ceiling + reserve - worst_case,
                    1,
                    f"{tier}: a reviewer that escalates for verification design "
                    "would exceed the budget",
                )

    def test_reserve_cannot_be_spent_on_another_critique_round(self) -> None:
        grantable = set(self.budget["escalation_reserve"]["grantable_agents"])
        self.assertNotIn("architecture-critic", grantable)


class ConditionArmIndependenceTests(unittest.TestCase):
    """When one agent has multiple conditional_agents entries, each entry is
    an independently-sufficient arm (OR across entries, never AND). A
    fixture that happens to satisfy every arm at once cannot distinguish the
    two readings — REQ-014 satisfies both of the T2 architect's arms, so it
    alone cannot catch a regression that turns this OR into an AND. This
    class requires, for every multi-arm condition, at least one fixture that
    satisfies each arm without also satisfying the others.
    """

    def setUp(self) -> None:
        self.policy = load_yaml(POLICY_PATH)
        self.oracle = load_yaml(ORACLE_PATH)["expected"]

    @staticmethod
    def _entry_holds(entry: dict, case: dict) -> bool:
        arch_threshold = entry.get("when_architecture_dimension_at_least")
        if arch_threshold is not None:
            return case["semantic_hints"]["architecture"] >= arch_threshold
        ambiguity_threshold = entry.get("when_ambiguity_dimension_at_least")
        if ambiguity_threshold is not None:
            return case["semantic_hints"]["ambiguity"] >= ambiguity_threshold
        signals = set(entry.get("when_any_signal", []))
        return bool(signals & set(case["signals"]))

    def test_each_arm_of_a_multi_arm_condition_is_exercised_alone(self) -> None:
        entries_by_agent: dict[tuple[str, str], list[dict]] = {}
        for tier, profile in self.policy["profiles"].items():
            for entry in profile.get("conditional_agents", []):
                entries_by_agent.setdefault((tier, entry["agent"]), []).append(entry)

        for (tier, agent), entries in entries_by_agent.items():
            if len(entries) < 2:
                continue
            tier_cases = [case for case in self.oracle if case["tier"] == tier]
            for index, entry in enumerate(entries):
                others = entries[:index] + entries[index + 1 :]
                isolating = [
                    case["id"]
                    for case in tier_cases
                    if self._entry_holds(entry, case)
                    and not any(self._entry_holds(other, case) for other in others)
                ]
                with self.subTest(tier=tier, agent=agent, arm=index):
                    self.assertTrue(
                        isolating,
                        f"no {tier} fixture satisfies this {agent} condition arm "
                        "alone; an AND-instead-of-OR regression across the arms "
                        "would be invisible",
                    )


class AnalystReserveTests(unittest.TestCase):
    """analyst_reserve and its triggering conditional_agents entry must agree.

    The two are declared in different places in policy.yaml (budget vs.
    profiles) precisely so a reviewer can check them independently; a test
    that only reads one of them would miss the other drifting.
    """

    def setUp(self) -> None:
        self.policy = load_yaml(POLICY_PATH)
        self.budget = self.policy["budget"]

    def test_reserve_exists_only_where_a_conditional_analyst_is_defined(self) -> None:
        tier_names = set(self.policy["profiles"])
        reserved_tiers = set(self.budget.get("analyst_reserve", {})) & tier_names
        conditional_tiers = {
            tier
            for tier, profile in self.policy["profiles"].items()
            for entry in profile.get("conditional_agents", [])
            if entry.get("agent") == "requirement-analyst"
            and entry.get("when_ambiguity_dimension_at_least") is not None
        }
        self.assertEqual(
            reserved_tiers,
            conditional_tiers,
            "analyst_reserve and the requirement-analyst conditional_agents "
            "entry must name exactly the same tiers, or one can fire without "
            "the budget to pay for it (or vice versa)",
        )

    def test_reserve_cannot_be_spent_on_another_critique_round(self) -> None:
        grantable = set(self.budget["analyst_reserve"]["grantable_agents"])
        self.assertNotIn("architecture-critic", grantable)


class EscalationOnlyAgentTests(unittest.TestCase):
    """"Escalation only" is a claim about the policy, so the policy is asserted.

    A role listed here costs nothing until someone deliberately invokes it. The
    moment it appears in a profile it is no longer escalation-only, and the cost
    argument that justified listing it here is silently void.
    """

    def setUp(self) -> None:
        self.policy = load_yaml(POLICY_PATH)
        self.oracle = load_yaml(ORACLE_PATH)["expected"]
        self.runner = load_runner()
        self.entries = self.policy["escalation_only_agents"]
        self.names = {entry["agent"] for entry in self.entries}

    def test_every_escalation_only_agent_is_defined_and_schema_known(self) -> None:
        defined = {path.stem for path in AGENTS_DIR.glob("*.md")}
        for name in sorted(self.names):
            with self.subTest(agent=name):
                self.assertIn(name, defined)
                self.assertIn(name, self.runner.AGENT_NAMES)

    def test_no_profile_spawns_an_escalation_only_agent(self) -> None:
        """The invariant that makes the label true."""
        for tier, profile in self.policy["profiles"].items():
            spawned = set(profile["required_agents"])
            spawned.update(entry["agent"] for entry in profile.get("conditional_agents", []))
            with self.subTest(tier=tier):
                self.assertEqual(
                    spawned & self.names, set(),
                    "an escalation-only agent listed in a profile is spawned by default; "
                    "either remove it from the profile or stop calling it escalation-only",
                )

    def test_no_oracle_case_expects_an_escalation_only_agent(self) -> None:
        """Classification cannot predict a deliberate escalation, so no fixture may."""
        for case in self.oracle:
            with self.subTest(case=case["id"]):
                self.assertEqual(set(case["required_agents"]) & self.names, set())

    def test_a_substituting_agent_replaces_a_role_some_profile_requires(self) -> None:
        """Substituting for a role no tier requires would replace nothing."""
        required: set[str] = set()
        for profile in self.policy["profiles"].values():
            required.update(profile["required_agents"])

        for entry in self.entries:
            replaced = entry.get("substitutes_for")
            if not replaced:
                continue
            with self.subTest(agent=entry["agent"]):
                self.assertTrue(set(replaced) & required, f"{replaced} is required by no tier")

    def test_a_substitution_never_costs_an_invocation(self) -> None:
        """One slot, one occupant. A substitution that adds a slot is an addition."""
        for entry in self.entries:
            if not entry.get("substitutes_for"):
                continue
            with self.subTest(agent=entry["agent"]):
                self.assertEqual(entry.get("invocation_cost"), 0)

    def test_a_substituting_reviewer_has_a_wider_ceiling_than_what_it_replaces(self) -> None:
        """Otherwise substituting it buys nothing and the roster grew for no reason."""
        for entry in self.entries:
            replaced = entry.get("substitutes_for")
            if not replaced:
                continue
            ceiling = agent_frontmatter(entry["agent"])["maxTurns"]
            for name in replaced:
                with self.subTest(agent=entry["agent"], replaces=name):
                    self.assertGreater(ceiling, agent_frontmatter(name)["maxTurns"])


class ExemptionCoverageTests(unittest.TestCase):
    """The exemption must be exercised, not merely declared.

    Every routing outcome in the original 12 fixtures was identical before and
    after the taxonomy change, so none of them could distinguish the two. A
    fixture that reads a sensitive resource AND acts on it is the only thing
    that proves the exempt read is dropped while the action still escalates.
    """

    def setUp(self) -> None:
        self.policy = load_yaml(POLICY_PATH)
        self.oracle = load_yaml(ORACLE_PATH)["expected"]

    def test_a_fixture_escalates_on_an_action_beside_an_exempt_read(self) -> None:
        def resource(signal: str) -> str:
            """The thing acted on, ignoring the verb and any qualifier.

            `reads-secret-config` and `exposes-secret` both name the secret.
            """

            parts = signal.split("-")
            return parts[1] if len(parts) > 1 else signal

        exempt_resources = {
            resource(signal)
            for signal in self.policy["signal_taxonomy"]["read_only_exempt"]
        }
        candidates = [
            case["id"]
            for case in self.oracle
            if case["tier"] != case["score_tier"]
            and any(resource(signal) in exempt_resources for signal in case["signals"])
        ]
        self.assertTrue(
            candidates,
            "no fixture pairs an exempt read with an escalating action on the same "
            "resource, so nothing verifies that the exemption drops the read without "
            "also dropping the action",
        )


if __name__ == "__main__":
    unittest.main()
