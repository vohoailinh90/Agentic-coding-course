---
name: classify-requirement
description: Classify a DocumentAIEditor requirement into a T0-T3 execution profile using the base scoring rubric, the base routing policy, and the DocumentAI routing overlay. Use before choosing subagents for non-trivial engineering work in this repository.
argument-hint: "[requirement text]"
---

Classify this requirement:

$ARGUMENTS

Sources of truth, all three, in this order:

1. `agent-routing/complexity-rubric.md` — the six scoring dimensions
2. `agent-routing/policy.yaml` — tiers, profiles, budgets, base overrides
3. `agent-routing/documentai-overlay.yaml` — the DocumentAI domain layer

The overlay is **not optional**. It is where this repository's signals, change
classes, reviewer substitution and discrimination rules live. Classifying with
the base policy alone produces a base-only tier and roster that ignores every
domain risk this repository actually has — a document-write change would come
back as an ordinary T1.

## Procedure

1. Parse the requirement semantically. State what the change **does**, as one
   verb-first sentence, before scoring anything.
2. Inspect enough repository context to avoid a clearly wrong score.
3. **Fast path.** Look the change up in the overlay's `change_classes` by the
   files and functions it touches, and collect **every** class it matches —
   not the first or the most obvious one. A requirement that touches both
   `AIContentParser` and `file_handlers.apply_changes` matches `ai-contract`
   *and* `document-write`; recording one would silently drop the other's
   deterministic check. Take the **maximum** `tier_floor` across the matches,
   and the **union** of their `signals`, `reviewer` names, `human_gate` flags
   and guarded checks.
4. **Full path.** Score each dimension 0-2: ambiguity, scope, architecture,
   dependencies, risk, verification. Sum the raw score (0-12) and read the
   score-based tier from `score_tiers`.
5. Extract signals as **actions the change performs**, using the base
   `signal_taxonomy` vocabulary plus the overlay's `domain_signals`. Ask "what
   does this change do?", not "what does this requirement mention?".
6. Run every candidate signal past the overlay's `discrimination_rules` before
   keeping it. The three that matter here: composing a mail vs. changing who
   receives it; calling BMF vs. changing how its key is stored; reading a
   document vs. writing one.
7. Drop every signal listed in the base `signal_taxonomy.read_only_exempt` or
   the overlay's `read_only_exempt`. A read-only signal never raises a tier
   and never appears in an override match. If it genuinely adds risk, that
   belongs in the risk or verification score, where it can be weighed.
8. Apply the overlay's `signal_mapping` to translate domain signals into base
   signals. Report both names — the domain signal is what the change does, the
   base signal is what routes it.
9. Apply every matching override: base overrides first, then the overlay's.
   The final tier is the **maximum** of the score-based tier, the change-class
   floor from step 3, and every matching override's `minimum_tier`. A tier can
   only rise.
10. Select the profile's strategy and `required_agents` — the floor.

    Then evaluate the profile's `conditional_agents`, which are **not** part
    of that floor and are easy to miss. Each entry fires on its own: a
    dimension threshold (`when_architecture_dimension_at_least`,
    `when_ambiguity_dimension_at_least`) or a matched signal
    (`when_any_signal`). Where the same agent has more than one entry they are
    independently sufficient — OR across entries, never AND. Two that apply
    here in practice:

    - `architect` at T2 when architecture scored 2, **or** when a signal in
      that entry's list fired. A `changes-bmf-endpoint-contract` change maps
      to `changes-service-contract`, which is in that list — so it requires
      the architect, and omitting it is the documented failure this step
      exists to prevent.
    - `requirement-analyst` at T3 when ambiguity scored 2.

    A signal that fires a conditional agent through `signal_mapping` counts:
    check the mapped base signal against the condition, not the domain name.

    Finally apply the overlay's `reviewer_role_substitution`: if any of its
    `when_any_signal` entries fired, the tier's reviewer slot is filled by the
    substitute instead of the role it `replaces`. This is a rename of one
    slot, not an extra agent — never emit both.
11. Read `budget.max_agent_invocations` for the final tier as the base ceiling.
    Add `analyst_reserve` when a dimension threshold fired the conditional
    `requirement-analyst` at T3. Never add `escalation_reserve` here: it is
    granted only after a reviewer formally escalates mid-review, which
    classification time cannot know.
12. Set `human_gate.required` if **any** matched change class carries
    `human_gate: true`, or any surviving signal appears in the overlay's
    `human_gates`. Every entry in `human_gates` is a declared signal, so this
    match is total — if you ever find a prose entry there, it is a bug in the
    overlay, not something to interpret by hand.
13. List the overlay's `required_checks` whose `guards` include **any** of the
    matched change classes, **or** whose `always_runs` flag is true.
    `check_no_secrets_committed` is guarded on `credentials` but runs on every
    change — dropping it because the class did not match is how a credential
    leak ships. These are deterministic checks that must run; they are not
    agent work and do not consume budget.
14. Decide `parallelizable` from the base policy's `parallelism` section,
    which the overlay inherits unchanged: `prefer_concurrent_when_any`
    (multiple independent components, competing hypotheses, independent
    research tracks, cross-layer workstreams) against
    `prefer_strict_sequence_when_any` (architecture must precede
    implementation, destructive migration, single shared hotspot). Sequencing
    wins where both apply. Parallelism changes **when** agents run, never how
    many: it must not raise `max_agent_invocations`. Do not leave the field
    at its placeholder — an unevaluated `false` looks like a decision and is
    not one.

## Output format

Return exactly one YAML block with this shape:

```yaml
requirement_summary: "..."
change_classes: []
classification:
  ambiguity: 0
  scope: 0
  architecture: 0
  dependencies: 0
  risk: 0
  verification: 0
raw_score: 0
domain_signals: []
mapped_base_signals: []
dropped_read_only_signals: []
score_tier: T0
change_class_floor: null
overrides_applied: []
final_tier: T0
strategy: main_session
required_agents: []
conditional_agents_fired: []
reviewer_substituted: null
max_agent_invocations: 0
required_checks: []
parallelizable: false
human_gate:
  required: false
  reason: null
rationale:
  - "..."
```

## Guardrails

- Do not inflate scores because the requirement uses sophisticated terminology.
- Do not lower risk because the code change is small. In this repository the
  most dangerous changes are the smallest ones: a one-line edit to
  `_set_paragraph_text` can strip formatting from every customer deliverable
  the tool produces, and nothing raises, fails or looks wrong in the diff.
- Signals must be verb-first actions. `outlook` is not a signal;
  `executes-outlook-send` and `reads-office-document` are, and only the first
  can raise a tier.
- Never emit more required agents than the budget allows, and never emit a
  substituted reviewer alongside the role it replaces.
- Do not add a role for work that is deterministic. If the verification is
  counting, hashing, or conformance checking, the answer is a script from
  `required_checks`, not an agent.
- If the change class and the rubric score disagree such that the score is
  *lower*, the floor wins. If the score is higher, the score wins. If you
  believe the floor is wrong, say so in `rationale` and fix the class table in
  the same change — do not silently route below it.
