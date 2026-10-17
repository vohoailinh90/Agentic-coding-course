# Agentic Coding Course — Claude instructions

## This repository

A trilingual (Vietnamese · English · Japanese) course that takes complete beginners from "what is
software?" to directing AI agents. It is the course's **content store**: the single source for
Facebook posts now and the course website later. Everything below *The template harness* comes
from `claude-agent-routing-template` (see `TEMPLATE.md`) and governs how engineering work here is
routed.

- **Read `PROGRESS.md` first** at the start of every session; keep it current, and record
  significant decisions as `docs/decisions/NNN-*.md`.
- **Content lives in `course/`**: one folder per language (`course/vi|en|ja/` — every file in it
  in that language only, starting with the 🌐 language bar) and the shared sources in
  `course/data/` (`course.yaml`, `curriculum.yaml`, `sections.yaml`, `glossary.yaml`,
  `diagrams/<id>.yaml`). Its rules are in `docs/data-model.md`; how to write a lesson and its
  infographics is in `docs/content-guide.md`. Vietnamese is the source language; English and
  Japanese are localized in the same pass (the owner's 2026-09-27 decision in
  `docs/decisions/007-roadmap-v1.md`) and never mixed into another language's folder.
- **The roadmap is v1** (`docs/decisions/007-roadmap-v1.md`): write lessons in the order of
  `minimum_path`. **Every lesson ends with a recap infographic** of its own in the `recap` section
  (`docs/decisions/008-a-recap-infographic-in-every-lesson.md`); `validate` enforces it.
- **`python -m src.main validate` must pass** before any commit that touches `course/`. After
  editing anything in `course/data/` or adding a lesson, run `python -m src.main build`: course
  homes, glossary pages and infographic SVGs are generated — never edit them by hand.
- **`python -m src.main export`** writes self-contained HTML copies of the course to
  `outputs/html/` (ignored by Git) for sharing without GitHub
  (`docs/decisions/009-offline-html-export.md`); `tests/test_course_export.py` checks on the real
  course that every link in them lands on a page.
- **`python3 scripts/sd101_check.py` must pass** before any commit that touches `system-design-101/`
  (the Vietnamese-only System Design store, `docs/decisions/011-system-design-store.md`; its rules are
  in `brainstorm/system-design-101-vi/DECISIONS.md`). `pytest` runs it too.
- **Never refer to a lesson by its number** in content; numbers change when the roadmap is
  reordered. Lesson ids never change and are never reused; a lesson taken out goes to `retired`.
- **Verify every source link** before committing it, and never invent statistics.
- The course CLI's user-facing text is in **vi, en and ja** (`src/locales/`), which extends the
  bilingual rule below; `python3 scripts/i18n_check.py src/locales --require vi,en,ja` is its gate.
- **Roadmap brainstorming with Codex** happens in GitHub issues following `docs/claude-to-codex.md`;
  the brief and the per-round conclusions are in `brainstorm/`.

# The template harness

## Purpose

This repository is an evaluation harness for selecting the **smallest effective Claude Code execution profile** for a software requirement.

Your primary job is not to maximize the number of agents. Your job is to select the lowest-cost profile that safely handles the requirement.

## Routing source of truth

- Routing policy: `agent-routing/policy.yaml`
- Scoring rubric: `agent-routing/complexity-rubric.md`
- Requirement classifier: `.claude/skills/classify-requirement/SKILL.md`
- Blind requirement fixtures: `evals/routing-cases.yaml`

## Evaluation data

`evals/expected-routing.yaml` is evaluator-only oracle data. A valid blind run freezes the actual classifications before the oracle is used for comparison. Previous result files and git history are likewise excluded from the classification phase.

`requirements/examples/*.md` are documentation-only convenience copies of the blind cases for interactive use. They must never carry an expected-tier answer, and a blind classification run must never treat them as an oracle.

Do not invent a different tier model unless the user explicitly asks to change the policy.

## Mandatory routing flow

For non-trivial feature/change requests:

1. Understand the requirement and inspect relevant repository context when available.
2. Score the six dimensions defined by the rubric.
3. Extract domain/risk signals as **actions the change performs**, never as nouns the requirement mentions. A read-only signal from `signal_taxonomy.read_only_exempt` never feeds an override.
4. Run `scripts/route.py` on the scores and signals. It applies the overrides, selects the profile, fires the conditional agents and adds up the budget from `agent-routing/policy.yaml`; do not apply those rules by hand.
5. When the session will execute the requirement, run it again with `--record` so the agent budget is enforced (below).
6. Execute only the roles required by that profile, staying inside `budget.max_agent_invocations`.
7. Verify independently before declaring success.
8. If the work ships as a pull request, run it through *Pull request lifecycle* (below): Codex review until every review command the work requires is clean on the current head, merge, then the next task.

The semantic analysis may be probabilistic; policy enforcement must not be — which is why steps 4–5 are a script and a hook, not instructions to the model. See `docs/agent-budget.md`.

## Execution profiles

### T0 — trivial

Use the main session only. Do not spawn subagents unless the requirement unexpectedly reveals additional risk or scope.

Good examples: copy changes, typo fixes, obvious local validation, tiny isolated refactors.

Agent budget: **0**.

### T1 — standard

The main session implements. One subagent verifies:

- `code-reviewer`

Do not spawn a separate `implementer` — the main session already holds the requirement and the code, and handing it to a subagent buys nothing except a second context that must rebuild both. The reviewer must inspect the resulting diff independently; the session that wrote the code cannot be its own only verification.

Agent budget: **1**.

### T2 — complex

The main session analyzes, designs and implements, recording its plan as an artifact. Then:

- `code-reviewer` — reviews the diff **and** independently verifies behavior (this is the combined review/test role)
- `architect` — **only** when the architecture dimension scored 2, or a signal in the profile's `when_any_signal` list fires (`changes-service-contract`, `changes-event-contract`, `changes-storage-ownership`, `changes-canonical-model`). These are two independently-sufficient conditions (OR, never AND) — either alone fires the architect — and both are machine-checkable on purpose: a condition the classifier cannot evaluate is prose, not policy.

An architect agent that would restate a design the main session can already state is not worth a context. Spawn it when the design genuinely needs authoring by someone not already committed to an implementation path.

Agent budget: **2** by default, plus a reserved invocation for verification escalation described below.

### T3 — critical

The main session analyzes, designs and implements. Two subagents supply what it cannot supply for itself:

- `architecture-critic` — challenges the main session's design before implementation
- `code-reviewer-t3` — the T3 variant of `code-reviewer` (16 turns, high effort instead of 12/medium): it reviews the diff and independently verifies behavior, and the combined remit does not fit the standard budget on payment/auth/migration-scale work without review crowding out verification

Critique is **one round** by default. A second round is allowed only when round 1 left unresolved critical or high findings, and it must **resume the round-1 critic**, never spawn a new one. A fresh critic re-reads the requirement, the design and the diff from zero, so a spawned round 2 costs more than round 1 did; a resumed one costs the delta.

`requirement-analyst` fires **conditionally**, not by default: when the requirement scores ambiguity `2`, invoke it before architecture begins. The critic reviews a design the main session already authored; the analyst is what keeps an open product decision from silently becoming a technical assumption before that design is written, and the critic cannot structurally substitute for it. `architect`, `implementer`, `test-engineer` and `code-reviewer-verify` remain available for escalation only.

Before implementation, resolve high-severity architecture objections. Escalate to the user only for a genuine blocker (the task cannot proceed without a decision only a human can make) or a change to the original requirement — including for irreversible or destructive changes. See `docs/claude-to-codex.md` §20 for the standing autonomous-completion-and-merge policy.

Agent budget: **3** by default (critic, reviewer, and one slot for a resumed critique round), **4** when ambiguity `2` fires the conditional `requirement-analyst`, plus a reserved invocation described below that either case may additionally earn.

A T3 worst case spends all three base slots on critique alone — critic, resumed critic, reviewer. A T2 worst case spends both base slots the same way, on the conditional architect plus the reviewer. In either case, if that reviewer then escalates because verification needs its own design work, that escalation would be a forbidden extra invocation and the requirement could never reach its own definition of done. `budget.escalation_reserve` grants exactly one additional invocation for that path at T2 and T3, available only to `test-engineer` and only after the reviewer has formally reported that verification needs designing. It may not be spent on another critique round, and it does not exist at T0-T1 — T0 does no independent verification, and T1's risk domains are already forced to T2+ by the policy overrides, so no T1 case can produce the finding this reserve exists to unblock. `budget.analyst_reserve` is the T3-only equivalent for the ambiguity-2 path — it fires before review even starts, so the two reserves are independent and a T3 requirement that is both ambiguous and later found to need designed verification can spend both (3 base + 1 analyst + 1 escalation = 5). Report base and reserve consumption separately rather than as one number.

## Agent budget

`budget.max_agent_invocations` in `agent-routing/policy.yaml` is a ceiling, not a target. It counts every subagent invocation for the requirement — resumed agents included, and anything a subagent itself spawns.

It is enforced, not advised: `scripts/route.py --record` writes the requirement's ledger to `artifacts/handoff/agent-budget.json`, and `scripts/hooks/agent_budget.py` (a `PreToolUse` hook matching `Agent|Task`, the spawn tool's name across Claude Code releases, wired in `.claude/settings.example.json`) charges every spawn to the base or to a reserve granted for that agent and refuses the one past the ceiling. A resumed agent is a message rather than a spawn, so charge it by hand with `agent_budget.py charge`; a reviewer's formal escalation is granted with `agent_budget.py grant escalation_reserve --agent test-engineer`. Details in `docs/agent-budget.md`.

Reaching the ceiling with work outstanding is an escalation signal. Report the partial result and the remaining risk; do not spawn past the cap because the work felt unfinished. The one exception is `budget.escalation_reserve` at T2 and T3, under the condition stated there. Parallelism changes when agents run, never how many: independent tracks do not raise the budget.

## Session budget

The agent budget caps how many contexts a requirement builds. It says nothing
about the one context that always exists: the session itself. A run that dies
mid-requirement — auto-compaction, or a rate limit — and is restarted from
scratch costs several times what finishing it would have, and the reasons are
structural rather than incidental:

- **The prompt cache goes cold.** A live session re-reads its history at roughly
  0.1x input price; a cold restart pays full price *plus* a cache write. That is
  the single largest multiplier, and a rate-limit wait guarantees it.
- **Turn cost is quadratic.** Every turn resends the whole conversation, so
  reaching the same depth twice costs the integral twice.
- **Re-derivation is the expensive part.** The reading, grepping and test runs
  that produced the session's conclusions are gone; the conclusions go with them.
- **Subagent contexts do not survive at all.** A T3 requirement that dies after
  three invocations rebuilds all three. Only what reached disk survives.

So treat the session like the roster: bounded, and instrumented.

`scripts/hooks/session_budget.py` and `scripts/hooks/statusline.py` are wired in
`.claude/settings.example.json`. Copy it to `.claude/settings.json` to enable
them; `docs/session-budget.md` documents the thresholds and the payload fields
they read.

### Handoff protocol

`artifacts/handoff/SESSION-HANDOFF.md` is the session's equivalent of the
artifact protocol: the stable output a restart reads instead of rebuilding. It
holds two blocks, and the split is the point.

- **`auto-state`** is regenerated on every capture from git and the transcript —
  branch, HEAD, uncommitted paths, diffstat, recent commits, context occupancy,
  the last request. All of it computable, none of it judgement, per
  *Deterministic work is not agent work* below.
- **`model-notes`** is authored by the session and preserved verbatim across
  every capture. Goal, what is done, what remains, the next command, decisions
  not worth re-litigating. A script cannot write this block, which is exactly
  why the session must.

Keep `model-notes` current whenever the work reaches a state worth resuming
from, and always when the hook asks for it (~70% of the context window) or tells
you to wrap up (~85%). Being cut off having written nothing is the failure this
protocol exists to prevent. Commit working code before that point too — a
handoff that points at an uncommitted working tree is a weaker checkpoint than
one that points at a commit.

On `SessionStart`, an existing handoff is replayed into the new session. Read it
before re-deriving anything.

## Deterministic work is not agent work

If the correct answer to a check is computable, compute it. Do not route it to a model.

This covers counting (records, rows, files, diff lines), hash/checksum/fingerprint comparison, schema and contract conformance a validator can assert, presence/expiry/referential-integrity checks over known data, and lint/format/type/test runs whose output is already a verdict.

Write a script or a CI check and commit it to the repository. A model comparing two SHA-256 values can be wrong; a script cannot. The reliability argument here is stronger than the cost argument, and the cost argument is already strong: prefer adding a check to the repository over adding a role to the roster.

**Mutation checking is the worked example.** A passing test proves nothing on its own; a test that would still pass with the behavior removed reports safety that is not there. The only thing that settles it is to break the behavior and require the test to notice — and that loop is computable: edit a file, run a test, read an exit code. It costs a reviewer three tool calls per behavior and scales with the number of behaviors, so no subagent turn ceiling can hold it, which is precisely why it is not a reason to enlarge one.

`scripts/mutation_check.py` owns that loop, driven by manifests in `tests/mutations/`. Each entry names a behavior, the edit that breaks it, and the test that must fail as a result; an entry whose `find` no longer matches exactly one site fails as drift rather than silently proving nothing. When you ship a fix with a test, add the mutation that would have caught it.

## Artifact protocol

For T2/T3, use artifacts so roles communicate through stable outputs rather than free-form debate:

- architecture proposal → `artifacts/architecture/<requirement-id>.md`
- critique → `artifacts/critiques/<requirement-id>.md`
- implementation plan → `artifacts/plans/<requirement-id>.md`
- final review → `artifacts/reviews/<requirement-id>.md`

Artifacts must record unresolved issues explicitly.

Artifacts are a compression channel, not a record of everything considered. Every downstream agent reads them, so length multiplies across the roster. `budget.max_artifact_lines` caps them: architecture 200 lines, critique 80, plan 120, review 120. An artifact over its cap must be **cut down**, not split across more files. A critique lists critical and high findings; low-severity observations belong in a closing sentence, not their own section.

## Escalation rules

Escalate to a higher tier when implementation discovers:

- hidden cross-service coupling
- auth/security implications
- schema/data migration
- irreversible operations
- distributed consistency requirements
- external dependency uncertainty
- materially harder verification than originally scored

Never downgrade below a policy override.

## Stop conditions

Do not keep agents debating until they "agree". Stop the architecture loop when:

- all critical/high objections are either accepted and addressed, or explicitly rejected with evidence;
- remaining disagreements are low severity; and
- the implementation plan has a verifiable acceptance criterion.

Maximum default architecture critique rounds: **1**. A second round requires unresolved critical/high findings and must resume the round-1 critic rather than spawning a new one. Escalate to the user instead of looping indefinitely when a critical product decision remains unresolved.

## Verification rule

Implementation is not complete because code was written. Completion requires evidence appropriate to the tier:

- T0: local sanity check, in the main session
- T1: relevant tests/lint, plus an independent diff review by `code-reviewer`
- T2: targeted tests and integration considerations, plus independent review and verification by `code-reviewer`
- T3: integration/e2e or migration/security verification as applicable, rollback consideration, plus independent review and verification by `code-reviewer-t3`

At T2 and T3 the reviewer both reads the diff and runs verification. Splitting those into two agents doubles the context cost to check one change; keep them in one role and escalate to `test-engineer` only when verification genuinely needs its own design work (failure injection, migration rehearsal, concurrency harnesses).

When a review's remit is known up front to be probe-heavy — probes that must be designed and run rather than an existing suite re-run — the reviewer slot may instead be filled by `code-reviewer-verify` (24 turns, high effort). It is a **substitution**, not an addition: it replaces `code-reviewer`/`code-reviewer-t3` in the one slot the profile already requires, so the budget is unchanged. No tier spawns it automatically, and that is deliberate: the two reviews that exhausted their ceiling here did so on mutation checking (now a script, above) and on diff size, which nothing can know at classification time. A `verification 2` trigger would have moved a third of the eval corpus onto the most expensive reviewer without evidence, which is the cost this repository exists to avoid. Registered in `escalation_only_agents` in `agent-routing/policy.yaml`.

Whatever the tier, a check whose answer is computable belongs in a script — see *Deterministic work is not agent work*.

## UI implementation source

When a requirement (any tier) involves building or restyling a UI screen or
component, use `.claude/skills/ui-kit/SKILL.md` before hand-building
anything, *within* whatever execution profile the requirement already
scored to per the mandatory routing flow — this section changes what the
implementation step reuses, not who performs it. It points at
`vohoailinh90/Automation-UI-Kit`, a catalog of free/MIT, copy-paste-ready
shadcn/ui-style components (Radix UI + Tailwind CSS v4 + Recharts +
lucide-react) plus full page patterns (dashboard, task table, data table,
settings form) and a layout shell. Whoever does the implementation for the
selected profile — the main session itself for T0 (which stays main-session
only per its profile; there is no `implementer` subagent to route to), the
`implementer` subagent for T1+ — must check it: reuse a matching component
instead of writing one from scratch, and only fall back to a custom
component when nothing in the kit fits, or when the target project already
has its own established UI system, per that skill's guardrails.

Fetching the kit (`add_repo`/`register_repo_root`) is always a main-session
step — for T0 that's simply part of doing the work in the main session; for
T1+ it must happen before delegating, since the `implementer` subagent
can't do it with its own tool list. Check the skill's existing-UI-system
exception *first*: if the target project already has its own established,
non-kit UI system **and the user hasn't explicitly asked to use or migrate
to this kit**, skip the kit entirely — the skill's own exception carves the
explicit-request case back out, so an explicit ask still needs the kit
fetched even then. Otherwise, fetch it, then (T1+ only) hand the
`implementer` the local workspace path.

## Bilingual apps and tools (Japanese/English)

Every app or tool built in a repository created from this template ships its
user-facing text in Japanese **and** English, unless the requirement
explicitly asks for one language. When a requirement (any tier) adds or
changes user-facing text — UI labels, CLI output and `--help`, error
messages, notifications, generated reports, exports or e-mails — use
`.claude/skills/bilingual/SKILL.md`. Like the UI-kit rule above, it changes
what the implementation step reuses, not who performs it: it adds no role,
raises no rubric dimension, and whoever implements for the selected profile
applies it.

- Strings live in `locales/ja.json` and `locales/en.json` beside the code,
  never hard-coded, and both change in the same commit. The runtimes to copy
  (Python stdlib; TypeScript + React with a UI-kit language switch) ship
  inside the skill, under `runtime/`.
- `python3 scripts/i18n_check.py` is the verdict on key parity, empty
  messages, placeholder parity and plural pairs, and CI runs it. That part is
  computable, so a reviewer runs the script rather than comparing catalogs by
  eye; the reviewer's judgement goes to what the script cannot see — a string
  that bypasses the catalogs, and Japanese and English that do not say the
  same thing.
- This template's own harness (`scripts/`, hooks, evals, agent and skill
  files) is developer tooling and stays English.

## Delegating to Codex Cloud

`docs/claude-to-codex.md` is the only approved protocol for delegating work to Codex Cloud (the `@codex` GitHub mention). Claude must read that file in full before posting any GitHub comment that mentions `@codex`, and must follow it exactly — task contract, comment tracking marker, GitHub location rules, duplicate-call and loop prevention, and response-validation steps included. Requesting a Codex review as soon as a PR is open is mandatory for every PR you create; the full loop from review to merge to the next task is *Pull request lifecycle*, below. Do not invent a different Codex invocation path (API, GitHub Action, CLI, SDK, or browser automation) — the file explicitly forbids all of those.

## Pull request lifecycle

Every pull request you create or drive for a requirement goes through the loop below — at any tier, a T0 typo fix included. It is a standing rule, not a judgement call, and a requirement never has to ask for it. The rule starts when a PR exists; it does not authorize opening one, so a PR is still opened only when the user asks for it or the flow calls for it.

1. **Open, then Codex review — immediately.** The first action after the PR exists is the Codex review. The review request of `docs/claude-to-codex.md` §11, posted when no request is unanswered and that review command has not yet reviewed this head. Codex never reviews a PR on its own here, so nothing arrives unless you ask. A PR with no Codex review is not done and is never merged.
2. **Validate every finding before acting.** Per §14 and §13: check it against the code. A confirmed finding is fixed; a wrong one is answered on its thread with the evidence, never silently skipped, and never "fixed" speculatively.
3. **Fix, then have the new head reviewed.** Fix each confirmed finding — with a regression test where the defect has testable behavior; a prose-only fix (a fact, a clarity or a translation correction) keeps the repository's normal content checks instead — run the repository's checks, push, and request the next review on the new head SHA — each review command once per head, with no request still unanswered (§11, §16).
4. **Stop when the review is clean.** Clean means every review command the work requires — the standard review, and a security review where the change touches authentication, authorization, secrets, payments or personal data (§12) — has a review of the *current* head that carries no finding (other than a P2/P3 whose recorded rejection stands, see the last bullet below), every earlier finding was fixed or rejected with evidence, CI and the required checks are green, and there is no merge conflict. A fix pushed after the last review is unreviewed, so it is not clean — review it with every command the work requires.
5. **Merge it yourself.** A clean PR is merged under `docs/claude-to-codex.md` §20 (branch-protection precondition, merge scoped to the validated head SHA, base unchanged) without waiting for or asking the user for approval. Record the merge commit SHA and a one-line summary on the PR. Where this repository's decision records say who merges, they decide and this step adds nothing to them: ADR 010 (the owner merges while `main` has no branch protection) and ADR 011 (Claude merges the System Design lesson PRs once Codex reports none, pinned to the reviewed head SHA).
6. **Then continue.** Do not stop after the merge to ask what is next. Start the next outstanding task from the latest default branch (a merged branch is finished; never stack new commits on it), through the full routing flow again under a new requirement id. An outstanding task is one the user explicitly asked for and that is not done yet, as recorded in this session or the session task list; never invent work or pick up an item the user did not ask for. A task that needs the code of a PR that is not merged (blocked, or waiting on the owner) waits: skip it rather than stack on that branch. When none remains, report what merged and stop.

The loop adds to the tier's verification and replaces none of it: `code-reviewer` still runs as the profile says, except where a decision record says Codex's review stands in for a Claude subagent: for course lesson batches ADR 010 does, so there Codex's review is the batch's independent review and no `code-reviewer` is spawned. A Codex review is not a Claude subagent, so T0 stays main-session. The PR description never mentions Codex (§16), and no comment or commit message carries the literal trigger string except the intentional trigger comments the protocol authorizes — each review request of steps 1 and 3, a security review, an authorized retry, each task-contract request (BRAINSTORM, INVESTIGATE, AUDIT, IMPLEMENT, FIX) or a delegated merge command (§3, §7–§13, §20).

What the loop does not change:

- **No review cap.** The owner removed the cap on review rounds (two per batch under ADR 010) on 2026-10-12, so the loop runs until every review command the work requires is clean on the current head. A review is still bounded by §16's other rules: each review command (standard, security) once per head SHA — a required security review may follow the standard one on the same head, never while a request is unanswered, never before the previous response was validated. Two exits remain: a finding you reject with evidence — a P2/P3 stands at once and blocks nothing, even if Codex raises it again; a P0/P1 is a disagreement unless a review drops it: when other fixes make a new head, push it and let the next review decide (raised again, unchanged or reworded or moved when it is substantially the same issue, means escalate; not raised again means closed), and when no code change is pending escalate at once — report it to the repository owner and do not merge until they decide — and a genuine blocker (§20). Those brakes are rules, not script gates: nothing computable sees both the PR head and Codex's reaction. The brainstorm and correction round limits of §16 are unchanged.
- **Codex unreachable.** A trigger failure past its one retry, a stalled or failed task, or a wrong account (§17, §18) makes the PR BLOCKED, not merged unreviewed and not worked around with the API, an Action, the SDK or browser automation. Report it once, leave the PR open and continue with the next task that does not depend on it (step 6). Handing the work to another agent moves who does the work and never waives the PR's Codex review: the PR stays BLOCKED until Codex has reviewed its head.
- **The merge preconditions.** Branches required to be up to date, and a merging identity that cannot bypass the rule (§20; read the base branch's protection to confirm both). Where they are missing, merging is a genuine blocker: escalate, do not merge — except for the PRs an accepted decision record lets Claude merge without them (ADR 011: the System Design lesson PRs).
- **Who may stop the loop.** A human is needed only for §20's two cases — a genuine blocker, or a change to the original requirement.

## Repository layout

The repository root holds only what a user needs to run the app: README and
the agent instruction files, dependency files, and at most three Python entry-point
launchers (a `.bat`/`.sh` shortcut that starts one is not counted). Tests go in `tests/`, the app's modules in its package, developer
tooling in `scripts/`. When a change adds a Python file, test or module, or
restructures the repository, follow `.claude/skills/repo-layout/SKILL.md`.

- `python3 scripts/layout_check.py` is the verdict: a test file or test
  directory in the root, a root `.py` that has neither an
  `if __name__ == "__main__":` guard nor a `# layout: entry-point` comment in
  its first lines (a library module; a Streamlit app declares itself with the
  marker), or more than three Python entry points in the root fails it. Run it before
  reporting done; reviewers run the script rather than judging the tree by eye.
- Moving existing files is a restructure, not a typo fix: `git mv` to keep
  history, fix every import and path, and prove the test suite still collects
  the same number of tests from its new place.

<!-- team-onboarding:start -->
## Team agent process

`vohoailinh90/Agentic-coding-course` is registered with the free-model team: `team` (Claude leads) and `team-codex` (Codex leads), with free models writing the tests, the code and a pre-review. The details are in `docs/TEAM.md`; the settings that differ per repository live in `repos.conf` on the VPS, not here.

- Base branch `main`; sensitivity `public`; gates setup `python3 -m venv --system-site-packages .venv && .venv/bin/pip install -q -r requirements.txt`; suggested test commands `.venv/bin/python -m pytest -q`.
- If you are a team worker (tester, coder or reviewer), follow the handoff files you are given and touch only the files the task names. Never edit CI (`.github/`), agent instructions (`CLAUDE.md`, `AGENTS.md`, `.claude/`, `.codex/`), lockfiles or `repos.conf` unless the task says so.

If you are Claude Code or Codex working on this repository directly (a spec, an audit or an ordinary change), this is the pull-request process:

- When your work here is ready to ship, open the pull request yourself; do not wait to be asked, unless the user asked for a local change only or this repository's own rules say a pull request is opened only on request.
- As soon as it is open, ask Codex for a review with one comment on the PR: `@codex review` (add `@codex security review` where this repository's rules, or the change itself, call for one: authentication, authorization, secrets, payments, personal data). Codex never reviews on its own here. Ask once per head commit for each review command, never while a request is unanswered, and never mention Codex in the PR description or a commit message. Where the repository has `scripts/codex_round_count.py`, run it before each request.
- Check each finding against the code. Confirmed: fix it, with a regression test where the defect has testable behavior (a prose-only fix keeps the repository's normal checks instead), push, and ask again on the new head. Wrong: answer on its thread with the evidence. There is no cap on rounds; a rejected P2/P3 stands and blocks nothing; a P0/P1 you cannot settle goes to the repository owner and the PR is not merged.
- Merge it yourself, without waiting for approval, once all of these hold on the current head: every review this change requires (the standard review, plus the security review where it touches authentication, authorization, secrets, payments or personal data) has been requested of that exact commit and has no finding left (a bare thumbs-up is not a review, unless this repository's own rules accept one for that exact request), CI is green, there is no merge conflict, and the base branch's protection (or a merge queue) requires branches to be up to date and applies to admins, and the identity that merges has no bypass of it (ruleset bypass list, custom role or app privilege). Immediately before merging, re-read the PR head and the base head: if the PR head moved, review it again; if the base moved, merge it in and re-validate. Merge scoped to the validated head SHA. If that protection is missing, do not merge: leave the PR open, say it is clean and why it was not merged, and tell the owner.
- If Codex gives no sign of life within 10 minutes, retry once per head; an explicit error or usage-limit reply needs no wait before that one retry. If it acknowledges but never delivers a review, or its task fails, do not retry: the PR is BLOCKED. The PR is also BLOCKED when the retry gets no answer. A BLOCKED PR stays open and is reported once; never merge it unreviewed, and never use another route (API, CLI, Action) to get a review.

Exceptions in this repository, which replace the matching rule above:

- Who merges is decided by the decision records, and the merge step above applies only as they allow: ADR 010 (the owner merges while main has no branch protection) and ADR 011 (Claude merges the System Design lesson pull requests once the review reports no finding, pinned to the reviewed head SHA).
- Before any commit that touches course/ run `python -m src.main build`, then `python -m src.main validate` (it must pass) and `python -m pytest -q`; before any commit that touches system-design-101/ run `python3 scripts/sd101_check.py`.

Where this repository documents its own rule for one of these steps elsewhere (who merges, what gates a merge, how the review is requested, a cap on rounds), that rule governs that step; this process covers whatever the repository leaves unsaid.
<!-- team-onboarding:end -->
