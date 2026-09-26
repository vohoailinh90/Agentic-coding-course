"""Consistency checks for the DocumentAI routing overlay.

The overlay is a domain layer on top of `agent-routing/policy.yaml`. Its
whole value depends on properties that are cheap to assert and easy to break
by hand: that it never redefines the tier model it claims to inherit, that
every domain signal it maps lands on a base signal that actually exists, and
that no signal it declares read-only can still reach an override.

These are computable answers, so they are a script, not a review.
"""

from __future__ import annotations

import fnmatch
import os
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "agent-routing" / "policy.yaml"
BASE_AGENTS_DIR = ROOT / ".claude" / "agents"
PROFILE_DIR = ROOT / "profiles" / "documentai"
OVERLAY_PATH = PROFILE_DIR / "routing" / "documentai-overlay.yaml"
OVERLAY_AGENTS_DIR = PROFILE_DIR / "agents"
OVERLAY_CLASSIFIER = PROFILE_DIR / "skills" / "classify-requirement" / "SKILL.md"
BASE_CLASSIFIER = ROOT / ".claude" / "skills" / "classify-requirement" / "SKILL.md"
README_PATH = PROFILE_DIR / "README.md"
PROCESS_PATH = PROFILE_DIR / "PROCESS.md"

# The overlay routes by file path and function name, so it is only as good as
# its references. Point this at a DocumentAIEditor checkout to have them
# verified; without one the check skips rather than pretending to pass.
def _find_target_repo() -> Path:
    """Locate a DocumentAIEditor checkout beside this repository.

    The install block documents `../DocumentAIEditor`, but a clone made
    through tooling that lowercases the repo name lands at
    `../documentaieditor`. On a case-sensitive filesystem a single hardcoded
    spelling silently skips every target assertion for whoever followed the
    other one, so both are probed.
    """
    override = os.environ.get("DOCUMENTAI_REPO")
    if override:
        return Path(override)
    for name in ("DocumentAIEditor", "documentaieditor"):
        candidate = ROOT.parent / name
        if (candidate / "file_handlers.py").is_file():
            return candidate
    return ROOT.parent / "DocumentAIEditor"  # the documented default, for the skip message


TARGET_REPO = _find_target_repo()

# Same verb set the base taxonomy test enforces. A signal names an action; a
# bare noun is the false-positive shape the taxonomy exists to prevent.
VERBS = {
    "adds", "calls", "changes", "coordinates", "creates", "deletes",
    "drops", "executes", "exposes", "issues", "migrates", "moves",
    "reads", "requires", "rolls", "rotates", "runs", "stores", "uses",
    "writes",
}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class OverlayFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_yaml(POLICY_PATH)
        self.overlay = load_yaml(OVERLAY_PATH)
        self.domain_signals = set(self.overlay["domain_signals"])
        self.exempt = set(self.overlay["read_only_exempt"])
        self.tiers = {tier["tier"] for tier in self.policy["score_tiers"]}

    def base_signal_vocabulary(self) -> set[str]:
        vocabulary: set[str] = set()
        for override in self.policy["overrides"]:
            vocabulary.update(override.get("match_any_signal", []))
            vocabulary.update(override.get("match_all_signals", []))
        return vocabulary

    def overlay_override_vocabulary(self) -> set[str]:
        vocabulary: set[str] = set()
        for override in self.overlay["overrides"]:
            vocabulary.update(override.get("match_any_signal", []))
            vocabulary.update(override.get("match_all_signals", []))
        return vocabulary

    def defined_agents(self) -> set[str]:
        return {p.stem for p in BASE_AGENTS_DIR.glob("*.md")} | {
            p.stem for p in OVERLAY_AGENTS_DIR.glob("*.md")
        }


class InheritanceTests(OverlayFixture):
    """The overlay may add. It may not quietly fork the tier model."""

    def test_overlay_points_at_the_real_base_policy(self) -> None:
        self.assertTrue((ROOT / self.overlay["base_policy"]).is_file())

    def test_overlay_never_redefines_an_inherited_section(self) -> None:
        for section, source in self.overlay["inherits"].items():
            with self.subTest(section=section):
                self.assertEqual(source, "base")
                self.assertNotIn(
                    section,
                    self.overlay,
                    f"{section!r} is declared inherited but also redefined in the overlay",
                )

    def test_overlay_declares_every_section_that_matters_as_inherited(self) -> None:
        for section in ("scoring", "score_tiers", "profiles", "budget"):
            self.assertIn(section, self.overlay["inherits"])

    def test_overlay_minimum_tiers_exist_in_the_base_policy(self) -> None:
        for override in self.overlay["overrides"]:
            with self.subTest(override=override["id"]):
                self.assertIn(override["minimum_tier"], self.tiers)


class DomainSignalTests(OverlayFixture):
    def test_every_signal_is_verb_first(self) -> None:
        for signal in sorted(self.domain_signals | self.exempt):
            with self.subTest(signal=signal):
                self.assertIn(
                    signal.split("-", 1)[0],
                    VERBS,
                    f"{signal!r} does not begin with an action verb",
                )

    def test_read_only_signals_are_disjoint_from_domain_signals(self) -> None:
        overlap = self.domain_signals & self.exempt
        self.assertEqual(overlap, set(), f"signal is both actionable and exempt: {overlap}")

    def test_no_read_only_signal_reaches_an_override(self) -> None:
        """The exemption is meaningless if an exempt signal can still match."""
        overlap = self.exempt & (self.overlay_override_vocabulary() | set(self.overlay["signal_mapping"]))
        self.assertEqual(overlap, set(), f"read-only signals are override-eligible: {overlap}")

    def test_overlay_overrides_only_match_declared_domain_signals(self) -> None:
        undeclared = self.overlay_override_vocabulary() - self.domain_signals
        self.assertEqual(undeclared, set(), f"override matches undeclared signals: {undeclared}")

    def test_overlay_overrides_do_not_duplicate_a_base_override_id(self) -> None:
        base_ids = {override["id"] for override in self.policy["overrides"]}
        overlay_ids = {override["id"] for override in self.overlay["overrides"]}
        self.assertEqual(base_ids & overlay_ids, set())


class SignalMappingTests(OverlayFixture):
    """A mapping is only as good as the outcome it actually produces.

    Asserting that the target string appears somewhere in the base vocabulary
    is far too weak: it stays true after the base moves that signal to a
    different override, or changes that override's minimum tier, or drops the
    signal from the T2 architect condition. The overlay's documented T2/T3
    outcomes would drift while every assertion still passed. So each mapping
    declares the override and tier it relies on, and these tests resolve it
    through the base policy and check that it still holds.
    """

    def resolve(self, base_signal: str) -> list[dict]:
        """Every base override that fires on `base_signal` alone."""
        firing = []
        for override in self.policy["overrides"]:
            if base_signal in override.get("match_any_signal", []):
                firing.append(override)
            # match_all_signals needs every signal, so one mapped signal
            # cannot fire it on its own and must not be counted here.
        return firing

    def test_mapping_keys_are_declared_domain_signals(self) -> None:
        undeclared = set(self.overlay["signal_mapping"]) - self.domain_signals
        self.assertEqual(undeclared, set(), f"mapping from undeclared signals: {undeclared}")

    def test_every_mapping_resolves_to_its_declared_override_and_tier(self) -> None:
        for domain, spec in self.overlay["signal_mapping"].items():
            with self.subTest(signal=domain):
                firing = self.resolve(spec["base_signal"])
                self.assertTrue(
                    firing,
                    f"{domain!r} maps to {spec['base_signal']!r}, which no base "
                    "override matches on its own — the mapping routes nothing",
                )
                ids = {override["id"] for override in firing}
                self.assertIn(
                    spec["expected_override"],
                    ids,
                    f"{domain!r} expects override {spec['expected_override']!r}, "
                    f"but {spec['base_signal']!r} now fires {sorted(ids)}",
                )
                declared = next(
                    o for o in firing if o["id"] == spec["expected_override"]
                )
                self.assertEqual(
                    declared["minimum_tier"],
                    spec["expected_minimum_tier"],
                    f"{domain!r} relies on {spec['expected_override']!r} being "
                    f"{spec['expected_minimum_tier']}, but the base policy now "
                    f"says {declared['minimum_tier']}",
                )

    def test_declared_conditional_agent_effects_still_hold(self) -> None:
        """The bmf-endpoints architect claim rests on a separate base fact:
        the mapped signal must still appear in T2's conditional_agents."""
        for domain, spec in self.overlay["signal_mapping"].items():
            agent = spec.get("also_fires_conditional_agent")
            if agent is None:
                continue
            triggers = {
                signal
                for entry in self.policy["profiles"]["T2"]["conditional_agents"]
                if entry["agent"] == agent
                for signal in entry.get("when_any_signal", [])
            }
            with self.subTest(signal=domain, agent=agent):
                self.assertIn(
                    spec["base_signal"],
                    triggers,
                    f"{domain!r} claims it fires {agent!r}, but "
                    f"{spec['base_signal']!r} is no longer in T2's "
                    "conditional_agents when_any_signal list",
                )

    def test_mapped_signals_are_not_also_overlay_override_matches(self) -> None:
        """One route per signal: either it maps onto a base override, or the
        overlay owns it. Both means two overrides fire for one action and the
        reported rationale stops matching the tier."""
        both = set(self.overlay["signal_mapping"]) & self.overlay_override_vocabulary()
        self.assertEqual(both, set(), f"signals routed twice: {both}")


class ChangeClassTests(OverlayFixture):
    def test_class_ids_are_unique(self) -> None:
        ids = [entry["id"] for entry in self.overlay["change_classes"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_tier_floor_is_a_known_tier(self) -> None:
        for entry in self.overlay["change_classes"]:
            with self.subTest(change_class=entry["id"]):
                self.assertIn(entry["tier_floor"], self.tiers)

    def test_class_signals_are_declared(self) -> None:
        known = self.domain_signals | self.exempt
        for entry in self.overlay["change_classes"]:
            for signal in entry.get("signals", []):
                with self.subTest(change_class=entry["id"], signal=signal):
                    self.assertIn(signal, known)

    def test_named_reviewers_are_defined_agents(self) -> None:
        defined = self.defined_agents()
        for entry in self.overlay["change_classes"]:
            reviewer = entry.get("reviewer")
            if reviewer is None:
                continue
            with self.subTest(change_class=entry["id"]):
                self.assertIn(reviewer, defined)

    def test_a_class_above_t1_carries_at_least_one_signal(self) -> None:
        """T2+ has to be justified by an action, not by a path looking scary."""
        for entry in self.overlay["change_classes"]:
            if entry["tier_floor"] in {"T2", "T3"}:
                with self.subTest(change_class=entry["id"]):
                    self.assertTrue(entry.get("signals"))

    def test_a_gated_class_never_shares_a_path_with_an_ungated_one(self) -> None:
        """Classes are matched cumulatively, so an overlap promotes.

        Step 3 of the classifier collects every class a requirement matches
        and takes the maximum floor and the union of gates. So if a gated T3
        class names a file that an ungated class also names, every ordinary
        edit to that file is silently promoted to gated T3. The `release`
        class caused exactly this by naming `DocumentAIEditor_v1.spec` and
        `build_exe.bat`, which the T1 `packaging` class also matches — an
        ordinary packaging edit became a gated release. A gated class must be
        matched by an action nothing else claims.
        """
        gated, ungated = [], []
        for entry in self.overlay["change_classes"]:
            (gated if entry.get("human_gate") else ungated).append(entry)
        ungated_paths = {
            (entry["id"], path)
            for entry in ungated
            for path in entry["paths"]
        }
        for entry in gated:
            for path in entry["paths"]:
                for other_id, other_path in ungated_paths:
                    if path == other_path or fnmatch.fnmatch(path, other_path):
                        with self.subTest(gated=entry["id"], ungated=other_id):
                            self.fail(
                                f"gated class {entry['id']!r} claims {path!r}, which "
                                f"ungated class {other_id!r} also matches — every "
                                "ordinary edit there would be promoted to gated T3"
                            )

    def test_human_gated_classes_are_t3(self) -> None:
        for entry in self.overlay["change_classes"]:
            if entry.get("human_gate"):
                with self.subTest(change_class=entry["id"]):
                    self.assertEqual(entry["tier_floor"], "T3")


class ReviewerSubstitutionTests(OverlayFixture):
    """Substitution fills the reviewer slot the base profile already requires.
    If it ever costs an invocation it is an addition wearing a rename, and the
    budget the base policy enforces stops meaning anything."""

    def test_substitution_never_costs_an_invocation(self) -> None:
        for rule in self.overlay["reviewer_role_substitution"]:
            with self.subTest(substitute=rule["substitute"]):
                self.assertEqual(rule["invocation_cost"], 0)

    def test_substitute_and_replaced_roles_are_defined_agents(self) -> None:
        defined = self.defined_agents()
        for rule in self.overlay["reviewer_role_substitution"]:
            self.assertIn(rule["substitute"], defined)
            for replaced in rule["replaces"]:
                with self.subTest(replaced=replaced):
                    self.assertIn(replaced, defined)

    def test_every_replaced_role_is_a_base_profile_reviewer(self) -> None:
        required = set()
        for profile in self.policy["profiles"].values():
            required.update(profile["required_agents"])
        for rule in self.overlay["reviewer_role_substitution"]:
            for replaced in rule["replaces"]:
                with self.subTest(replaced=replaced):
                    self.assertIn(
                        replaced,
                        required,
                        f"{replaced!r} is not a required agent in any base profile, "
                        "so substituting for it does not free a slot",
                    )

    def test_substitution_triggers_are_declared_signals(self) -> None:
        for rule in self.overlay["reviewer_role_substitution"]:
            for signal in rule["when_any_signal"]:
                with self.subTest(signal=signal):
                    self.assertIn(signal, self.domain_signals)


class RequiredCheckTests(OverlayFixture):
    def test_every_check_guards_a_real_change_class(self) -> None:
        classes = {entry["id"] for entry in self.overlay["change_classes"]}
        for check in self.overlay["required_checks"]:
            for guarded in check["guards"]:
                if guarded == "always":
                    continue
                with self.subTest(check=check["id"], guards=guarded):
                    self.assertIn(guarded, classes)

    def test_every_check_is_specified_in_the_process_document(self) -> None:
        """A check named in policy but never specified is a promise, not a check."""
        process = PROCESS_PATH.read_text(encoding="utf-8")
        for check in self.overlay["required_checks"]:
            with self.subTest(check=check["id"]):
                self.assertIn(check["id"], process)

    def test_every_t2_plus_change_class_is_guarded_by_a_check(self) -> None:
        guarded = {
            entry
            for check in self.overlay["required_checks"]
            for entry in check["guards"]
        }
        for entry in self.overlay["change_classes"]:
            if entry["tier_floor"] in {"T2", "T3"} and not entry.get("human_gate"):
                with self.subTest(change_class=entry["id"]):
                    self.assertIn(
                        entry["id"],
                        guarded,
                        "a T2+ class with no deterministic check leaves verification "
                        "entirely to judgement",
                    )

    def test_every_check_declares_whether_it_exists_yet(self) -> None:
        """A check listed with no status reads as a gate that runs.

        Four of the eight originally listed had never been written, and
        `unittest discover` is silent about a module that is absent, so CI
        went green while packaging, access control and the transport ladder
        were enforced by nothing. The status field is what makes the gap
        visible; check_required_checks_exist is what makes it enforced.
        """
        for check in self.overlay["required_checks"]:
            with self.subTest(check=check["id"]):
                self.assertIn(check.get("status"), {"implemented", "planned"},
                              f"{check['id']} does not say whether it exists")

    def test_the_status_declaration_is_itself_enforced_by_a_check(self) -> None:
        """Otherwise the statuses are prose that drifts from the checks/ directory."""
        enforcer = next(
            (c for c in self.overlay["required_checks"]
             if c["id"] == "check_required_checks_exist"), None)
        self.assertIsNotNone(
            enforcer, "nothing asserts the status declarations against reality")
        self.assertEqual(enforcer.get("status"), "implemented")
        self.assertTrue(enforcer.get("always_runs"),
                        "a check that validates the check list must always run")



class HumanGateTests(OverlayFixture):
    def test_every_gate_is_a_declared_domain_signal(self) -> None:
        """No prose gates. A gate written as an English sentence is
        unreachable: the classifier fires a gate from a change class's
        human_gate flag or a surviving signal, so a sentence here reads like
        a rule and enforces nothing. An earlier revision carried
        "shipping a rebuilt EXE to users" as prose and this test skipped it,
        which meant the test certified exactly the shape it exists to
        prohibit — the release gate could never fire."""
        for gate in self.overlay["human_gates"]:
            with self.subTest(gate=gate):
                self.assertIn(
                    gate,
                    self.domain_signals,
                    f"{gate!r} is not a declared signal, so no classification "
                    "can ever match it",
                )

    def test_every_gated_signal_reaches_a_gated_change_class(self) -> None:
        """A gate also needs a route: some change class must carry the signal,
        or the fast path never surfaces it."""
        classed = {
            signal
            for entry in self.overlay["change_classes"]
            for signal in entry.get("signals", [])
        }
        for gate in self.overlay["human_gates"]:
            with self.subTest(gate=gate):
                self.assertIn(gate, classed)

    def test_no_exempt_signal_is_human_gated(self) -> None:
        """A read-only action cannot need a confirmation gate; if it does, it
        was misclassified as read-only."""
        self.assertEqual(set(self.overlay["human_gates"]) & self.exempt, set())


class TargetRepositoryReferenceTests(unittest.TestCase):
    """Every path and symbol the overlay routes by must exist in the target.

    A profile that misdescribes the code it routes is worse than no profile:
    it sends changes to a tier floor keyed on a function nobody can find, and
    the error is invisible until someone tries to use the table. Resolving a
    name against a checkout is computable, so it is a check and not a review.
    """

    @classmethod
    def setUpClass(cls) -> None:
        if not (TARGET_REPO / "file_handlers.py").is_file():
            raise unittest.SkipTest(
                f"no DocumentAIEditor checkout at {TARGET_REPO}; "
                "set DOCUMENTAI_REPO to verify overlay references"
            )
        cls.overlay = load_yaml(OVERLAY_PATH)
        cls.sources = {
            path.name: path.read_text(encoding="utf-8", errors="replace")
            for path in TARGET_REPO.glob("*.py")
        }
        cls.all_source = "\n".join(cls.sources.values())

    @staticmethod
    def _defines(body: str, symbol: str) -> bool:
        """True when `body` defines a name matching `symbol` (glob allowed)."""
        defined = re.findall(r"^\s*(?:def|class)\s+(\w+)", body, re.MULTILINE)
        defined += re.findall(r"^([A-Z_][A-Z0-9_]*)\s*=", body, re.MULTILINE)
        return any(fnmatch.fnmatch(name, symbol) for name in defined)

    def test_every_module_reference_exists(self) -> None:
        for entry in self.overlay["change_classes"]:
            for ref in entry["paths"]:
                if "::" not in ref:
                    continue
                module = ref.split("::", 1)[0]
                with self.subTest(change_class=entry["id"], module=module):
                    self.assertIn(module, self.sources)

    FILE_SUFFIXES = (".py", ".txt", ".spec", ".bat", ".xlsx")

    @classmethod
    def _is_file_reference(cls, ref: str) -> bool:
        """A path reference, literal or globbed — as opposed to a symbol.

        Keyed on the file suffix, not on the presence of `*`: symbol globs
        such as `_requests_post*` and `_httpclient_*` also carry a wildcard
        but resolve against the source, not the filesystem.
        """
        return ref.endswith(cls.FILE_SUFFIXES)

    def test_every_symbol_reference_resolves(self) -> None:
        for entry in self.overlay["change_classes"]:
            for ref in entry["paths"]:
                if " " in ref:  # prose reference, e.g. "any write to input/"
                    continue
                if "::" in ref:
                    module, symbol = ref.split("::", 1)
                    body = self.sources.get(module, "")
                elif self._is_file_reference(ref):
                    continue  # a path, checked by the file tests below
                else:
                    body, symbol = self.all_source, ref
                with self.subTest(change_class=entry["id"], symbol=ref):
                    self.assertTrue(
                        self._defines(body, symbol),
                        f"{ref!r} does not resolve in {TARGET_REPO}",
                    )

    def test_every_file_reference_matches_at_least_one_file(self) -> None:
        """Globs are expanded, not skipped.

        Skipping them let `*.bat` match zero files while all three reference
        assertions still passed — which is precisely the drift this check
        exists to catch, since the target repository evolves separately.
        """
        for entry in self.overlay["change_classes"]:
            for ref in entry["paths"]:
                if " " in ref or "::" in ref or not self._is_file_reference(ref):
                    continue
                with self.subTest(change_class=entry["id"], path=ref):
                    matches = sorted(TARGET_REPO.glob(ref))
                    self.assertTrue(
                        matches,
                        f"{ref!r} matches no file in {TARGET_REPO}",
                    )

    def test_the_packaging_class_still_covers_the_bat_launchers(self) -> None:
        """A regression guard for the specific reference that was being skipped."""
        packaging = next(
            entry for entry in self.overlay["change_classes"] if entry["id"] == "packaging"
        )
        self.assertIn("*.bat", packaging["paths"])
        self.assertTrue(sorted(TARGET_REPO.glob("*.bat")))


class ClassifierInstallationTests(OverlayFixture):
    """The overlay only routes anything if the installed classifier reads it.

    The base `classify-requirement` skill names `policy.yaml` and the base
    taxonomy as its sources and never opens the overlay — so installing it
    alongside this bundle leaves the profile inert: document-write work would
    classify as a base-only T1 with the generic reviewer, and every change
    class, mapping and substitution here would be dead text. The bundle
    therefore ships its own classifier under the same skill name, and these
    tests hold it to actually consuming the overlay.
    """

    def setUp(self) -> None:
        super().setUp()
        self.classifier = OVERLAY_CLASSIFIER.read_text(encoding="utf-8")

    def test_the_bundle_ships_a_classifier(self) -> None:
        self.assertTrue(OVERLAY_CLASSIFIER.is_file())

    def test_it_shadows_the_base_skill_name(self) -> None:
        """Same name, so `/classify-requirement` resolves to this one."""
        _, frontmatter, _ = self.classifier.split("---\n", 2)
        self.assertEqual(yaml.safe_load(frontmatter)["name"], "classify-requirement")

    def test_it_names_the_overlay_as_a_source_of_truth(self) -> None:
        self.assertIn("documentai-overlay.yaml", self.classifier)

    def test_it_consumes_every_overlay_mechanism(self) -> None:
        """A classifier that reads the overlay but skips one of its mechanisms
        silently drops that mechanism's routing."""
        for mechanism in (
            "domain_signals",
            "read_only_exempt",
            "signal_mapping",
            "discrimination_rules",
            "change_classes",
            "reviewer_role_substitution",
            "human_gates",
            "required_checks",
        ):
            with self.subTest(mechanism=mechanism):
                self.assertIn(mechanism, self.classifier)

    def test_the_base_classifier_really_does_ignore_the_overlay(self) -> None:
        """Guards the premise. If the base skill ever learns to read the
        overlay, this bundle's replacement stops being necessary and this
        whole test class should be revisited rather than left asserting a
        distinction that no longer exists."""
        if not BASE_CLASSIFIER.is_file():
            self.skipTest("base classifier not present in this checkout")
        self.assertNotIn("documentai-overlay", BASE_CLASSIFIER.read_text(encoding="utf-8"))

    def test_install_instructions_ship_it_and_warn_against_the_base_one(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn("cp -r profiles/documentai/skills/classify-requirement", readme)
        self.assertIn("Do not copy the base `classify-requirement` skill", readme)

    def test_install_source_paths_are_qualified_from_the_repository_root(self) -> None:
        """The block must run from one stated directory.

        An earlier revision mixed bare source paths (`CLAUDE.md.template`,
        valid only inside profiles/documentai) with a `../DocumentAIEditor`
        destination (valid only from the repo root), so it worked from
        neither and `mkdir` created directories in the wrong repository.
        """
        readme = README_PATH.read_text(encoding="utf-8")
        block = readme.split("```bash", 1)[1].split("```", 1)[0]
        for line in block.splitlines():
            line = line.strip()
            if not line.startswith("cp"):
                continue
            for token in line.split():
                token = token.strip('"')
                if token.startswith(("profiles/", "agent-routing/", ".claude/", "$TARGET")):
                    continue
                if token in {"cp", "-r", "\\"} or token.startswith("$"):
                    continue
                with self.subTest(line=line, token=token):
                    self.fail(
                        f"{token!r} is neither root-qualified nor under $TARGET; "
                        "the block would not run from the stated directory"
                    )

    def test_it_evaluates_conditional_agents(self) -> None:
        """required_agents is the floor, not the roster. Omitting the T2
        architect on a service-contract change was the documented failure."""
        self.assertIn("conditional_agents", self.classifier)
        self.assertIn("architect", self.classifier)
        self.assertIn("requirement-analyst", self.classifier)

    def test_it_aggregates_every_matching_change_class(self) -> None:
        """One requirement can match several classes; recording one drops the
        others' deterministic checks."""
        self.assertIn("change_classes: []", self.classifier)
        self.assertIn("union", self.classifier)

    def test_it_applies_the_inherited_parallelism_policy(self) -> None:
        """The overlay declares parallelism inherited; a classifier that never
        evaluates it leaves the emitted field an unexplained placeholder."""
        self.assertIn("prefer_concurrent_when_any", self.classifier)
        self.assertIn("prefer_strict_sequence_when_any", self.classifier)
        self.assertIn("max_agent_invocations", self.classifier)

    def test_it_includes_always_runs_checks(self) -> None:
        self.assertIn("always_runs", self.classifier)
        self.assertIn("check_no_secrets_committed", self.classifier)

    def test_it_states_that_a_tier_can_only_rise(self) -> None:
        self.assertIn("maximum", self.classifier)
        self.assertIn("only rise", self.classifier)


class OverlayAgentFrontmatterTests(unittest.TestCase):
    def test_every_overlay_agent_declares_a_turn_ceiling_and_effort(self) -> None:
        agents = sorted(OVERLAY_AGENTS_DIR.glob("*.md"))
        self.assertTrue(agents, "no overlay agent definitions found")
        for path in agents:
            _, frontmatter, _ = path.read_text(encoding="utf-8").split("---\n", 2)
            meta = yaml.safe_load(frontmatter)
            with self.subTest(agent=path.stem):
                self.assertEqual(meta.get("name"), path.stem)
                self.assertIsInstance(meta.get("maxTurns"), int)
                self.assertGreater(meta["maxTurns"], 0)
                self.assertIn(meta.get("effort"), {"low", "medium", "high", "xhigh", "max"})

    def test_no_overlay_agent_shadows_a_base_agent(self) -> None:
        base = {p.stem for p in BASE_AGENTS_DIR.glob("*.md")}
        overlay = {p.stem for p in OVERLAY_AGENTS_DIR.glob("*.md")}
        self.assertEqual(base & overlay, set())

    def test_no_overlay_agent_can_edit_code(self) -> None:
        """Every role the overlay adds is a reviewer. A reviewer that can write
        is no longer independent of the change it is reviewing."""
        for path in sorted(OVERLAY_AGENTS_DIR.glob("*.md")):
            _, frontmatter, _ = path.read_text(encoding="utf-8").split("---\n", 2)
            meta = yaml.safe_load(frontmatter)
            tools = {t.strip() for t in str(meta.get("tools", "")).split(",")}
            with self.subTest(agent=path.stem):
                self.assertNotIn("Write", tools)
                self.assertNotIn("Edit", tools)


if __name__ == "__main__":
    unittest.main()
