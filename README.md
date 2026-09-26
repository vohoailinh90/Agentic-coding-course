# Claude Agent Routing Template

A small, opinionated Claude Code template for routing software requirements to an execution profile based on **complexity, risk, domain, and verification needs**.

The core design is deliberately hybrid:

1. Claude performs semantic analysis of the requirement.
2. The classifier emits a structured score and signals.
3. `scripts/route.py` deterministically applies `agent-routing/policy.yaml` to that score and those signals: minimum tier, required roles, conditional agents and the agent budget.
4. Claude Code executes the matching pattern: main session, or main session plus a small, budgeted set of independent-judgement subagents.
5. Independent review/testing verifies the result.

This avoids the anti-pattern of allowing an LLM to freely decide how many agents it wants to spawn — and the budget it lands on is enforced by a `PreToolUse` hook that refuses the spawn past the ceiling, not just declared (see [Agent budget](#agent-budget)).

## Prerequisites

- Claude Code installed and authenticated.
- Python 3.10+ for the local eval runner.
- Project subagents are loaded from `.claude/agents/`.
- Project skills are loaded from `.claude/skills/<skill>/SKILL.md`.
- Agent teams are **not** used by any profile in this template, and `.claude/settings.example.json` enables nothing beyond the session-budget hooks and status line described below. Agent teams multiply token cost substantially, and every profile here is main-session-first with a hard agent budget — there is nothing for a team to parallelize. If you have `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` set from an earlier version of this template, **remove the variable** rather than setting it to `0`.

Recommended: use a current Claude Code release.

## Quick start

```bash
git clone https://github.com/vohoailinh90/claude-agent-routing-template.git
cd claude-agent-routing-template
claude
```

Inside Claude Code:

```text
/classify-requirement "Add a REST endpoint to export invoices as CSV using the existing service pattern"
```

The skill returns a routing decision including semantic dimensions, raw score, signals, final tier, strategy, required agents, parallelization, and human-gate decision.

## Routing tiers

| Tier | Score | Default strategy | Subagents | Agent budget |
|---|---:|---|---|---:|
| T0 Trivial | 0-2 | Main session only | none | 0 |
| T1 Standard | 3-5 | Main implements, reviewer verifies | code-reviewer | 1 |
| T2 Complex | 6-8 | Main plans and implements | code-reviewer, plus architect only when architecture is 2 or an external contract changes | 2 |
| T3 Critical | 9-12 | Main plans and implements, critic challenges it | architecture-critic, code-reviewer-t3, plus requirement-analyst only when ambiguity is 2 | 3 (4 with the analyst) |

The main session owns requirement analysis, architecture and implementation at every tier. `code-reviewer` (`code-reviewer-t3` at T3, for a wider turn budget) is a combined review-and-verification role: it reviews the diff *and* independently verifies behavior. `test-engineer`, `implementer` and `code-reviewer-verify` (a 24-turn reviewer that substitutes into the same slot when a review is known to be probe-heavy) remain available as escalation roles, but no tier spawns them by default; `architect` is escalation-only at T3 but fires conditionally at T2; `requirement-analyst` is the one conditional exception, firing at T3 only when ambiguity scores 2.

`budget.max_agent_invocations` in `agent-routing/policy.yaml` is a hard ceiling, counting resumed agents and anything a subagent spawns. Reaching it with work outstanding is an escalation signal, not a licence to spawn more.

Policy overrides can raise the minimum tier even when raw complexity is low. Security-sensitive work, payments, data migrations, authorization changes, irreversible operations, and cross-service changes are examples.

## Why score + overrides?

A 30-file UI refactor may have high scope but low operational risk. A three-line authorization change may have tiny scope but severe security risk. Routing only on size or token count produces poor teams.

The classifier scores six dimensions from 0 to 2:

- ambiguity
- scope
- architecture impact
- dependencies
- risk
- verification difficulty

`agent-routing/policy.yaml` then applies domain/risk overrides.

The architecture rubric intentionally scores **architectural consequence**, not infrastructure vocabulary. A local cache or additive schema/backfill inside one bounded subsystem is normally architecture `1`; architecture `2` is reserved for system/service boundaries, external contracts, cross-component consistency semantics, storage ownership, identity model, or deployment topology changes.

## Files

```text
.
├── CLAUDE.md
├── README.md
├── requirements-eval.txt
├── scripts/
│   ├── route.py                     # scores + signals -> tier, roster, budget (deterministic)
│   ├── run-routing-evals.py
│   ├── mutation_check.py
│   ├── pick_runner.py               # which runner, from quota + thresholds
│   ├── switch_runner.py             # convert every workflow, and guard the drift
│   ├── i18n_check.py                # Japanese/English catalog parity gate (CI)
│   └── hooks/
│       ├── agent_budget.py         # the agent-budget ledger and the spawn refusal
│       ├── session_budget.py       # handoff capture/replay + context nudges
│       └── statusline.py           # context, rate-limit and cache headroom
├── .claude/
│   ├── agents/
│   │   ├── requirement-analyst.md
│   │   ├── architect.md
│   │   ├── architecture-critic.md
│   │   ├── implementer.md
│   │   ├── code-reviewer.md
│   │   ├── code-reviewer-t3.md
│   │   ├── code-reviewer-verify.md
│   │   └── test-engineer.md
│   ├── skills/
│   │   ├── classify-requirement/
│   │   │   └── SKILL.md
│   │   ├── ui-kit/
│   │   │   └── SKILL.md
│   │   └── bilingual/
│   │       ├── SKILL.md
│   │       └── runtime/            # copy-ready Python + TS/React runtimes, starter catalogs
│   └── settings.example.json
├── agent-routing/
│   ├── policy.yaml
│   └── complexity-rubric.md
├── evals/
│   ├── routing-cases.yaml          # blind inputs only
│   ├── expected-routing.yaml       # evaluator-only oracle
│   ├── claude-web-blind-eval.md    # two-session web protocol
│   └── results/
├── requirements/examples/
│   └── 12 requirement fixtures (REQ-013/014 are eval-only)
├── docs/
│   ├── agent-budget.md             # the resolver, the ledger and the hook
│   ├── claude-to-codex.md
│   ├── ci-runner-mode.md           # GitHub-hosted vs self-hosted, and the switch
│   └── session-budget.md           # why a restart costs more, and the guardrails
└── artifacts/
    ├── architecture/
    ├── critiques/
    ├── handoff/                    # local session state (gitignored)
    ├── plans/
    └── reviews/
```

## Eval v2: blind classification

The classifier must not see expected labels before it commits to an answer. `evals/routing-cases.yaml` therefore contains only IDs and requirement text. Expected dimensions, raw scores, signals, tiers, strategies, agents, parallelization and human-gate values live only in `evals/expected-routing.yaml`.

The local runner uses two phases:

```text
requirements
    ↓
Phase 1: blind classification
    ↓
frozen actual results
    ↓
Phase 2: load oracle + score
```

This removes the label-leakage problem of asking one model to classify while simultaneously reading the expected answers.

## Run the local routing evals

Install the small Python dependency:

```bash
python -m pip install -r requirements-eval.txt
```

Make sure Claude Code is authenticated:

```bash
claude --version
```

Run all 18 cases once:

```bash
python scripts/run-routing-evals.py
```

Run one or more cases while tuning the classifier:

```bash
python scripts/run-routing-evals.py --case REQ-007
python scripts/run-routing-evals.py --case REQ-007 --case REQ-009
```

Measure stability by running each case several times:

```bash
python scripts/run-routing-evals.py --runs 5
```

Optionally pin the model or cap the budget per invocation:

```bash
python scripts/run-routing-evals.py --model sonnet --runs 5
python scripts/run-routing-evals.py --max-budget-usd 0.25
```

The runner first makes a disposable project copy that excludes the evaluator oracle, duplicate requirement fixtures containing expected labels, generated artifacts/results, and Git history. It then calls Claude Code from that isolated copy in non-interactive `-p` mode with `--output-format json` and `--json-schema`. It deliberately does **not** use `--bare`, because the eval must load this repository's `CLAUDE.md` and `/classify-requirement` skill. On Windows it explicitly decodes subprocess output as UTF-8 and closes stdin with `DEVNULL`.

The console report includes:

- route accuracy, and beneath it the accuracy of the route `scripts/route.py` resolves from the model's own scores and signals, plus how often the model's self-applied route matched the resolver's — so a miss is attributable to scoring or to policy application
- tier accuracy
- strategy accuracy
- agent-set accuracy
- parallelizable accuracy
- human-gate accuracy
- agent-budget accuracy, and a no-oracle check that no roster exceeds its own declared ceiling
- mean roster size vs. the oracle, and an over-routing delta in roles

Over-routing is counted in **roles requested**, not tokens: this runner classifies and never executes the routed profile. Comparing declared ceilings would measure nothing, since the ceiling is a function of the tier — any correctly tiered run reports a zero delta whatever its roster holds.
- exact raw-score/dimension/signal matches as diagnostics
- tier stability when `--runs` is greater than 1
- estimated Claude Code cost and duration when available

A timestamped JSON report is written to `evals/results/`. Generated reports are git-ignored by default.

Route correctness is based on the execution decision (`tier`, `strategy`, agent set, parallelization, human gate). Raw semantic score, dimensions, and signals are diagnostics rather than hard pass/fail criteria.

The classifier is told it may run `scripts/route.py` inside the blind workspace, and the skill instructs it to. The oracle's own routes are reproduced from its scores and signals by that script (`tests/test_route.py`), so the oracle is a checked consequence of the policy rather than a second copy of it.

## Run on Claude Code Web

For Claude Code Web, use **two separate tasks/sessions** so the classifier task never reads the oracle and a second evaluator task scores the frozen results.

Copy the prompts from:

```text
evals/claude-web-blind-eval.md
```

For stronger stability evidence, run the blind-classification task five times in five fresh sessions, then score all five frozen result files in a separate evaluator session.

## Suggested evaluation loop

Start with the 18 cases, measure blind accuracy and stability, then tune the rubric/policy based on systematic errors rather than individual prompt luck.

Useful metrics include:

- tier accuracy
- required-agent accuracy
- over-routing and under-routing rate
- routing stability across independent runs
- agent-budget accuracy (does the classifier emit the tier's ceiling?)
- mean roster size across cases — the over-routing measure
- token/cost overhead
- implementation success in a later execution eval
- escaped review defects
- test pass/fail quality

Do not optimize for "more agents". Optimize for the cheapest execution profile that reliably produces a correct result.

## Agent budget

`budget.max_agent_invocations` is a ceiling the policy enforces, not a number
it hopes for:

```bash
python3 scripts/route.py --dimensions 1,1,1,1,2,2 --signals changes-schema --record --requirement REQ-007
```

resolves the route deterministically and writes the requirement's ledger.
`scripts/hooks/agent_budget.py`, wired as a `PreToolUse` hook on `Agent|Task` (the spawn tool's name across
Claude Code releases) in `.claude/settings.example.json`, then charges every subagent spawn to the base
ceiling or to a reserve granted for that agent, and **refuses** the spawn past
it with the policy's escalation guidance. Reserves earned at run time
(`escalation_reserve`, after a reviewer formally escalates) and resumed agents
(a message, not a spawn) are recorded by hand with `grant` and `charge`.

Full reference: [`docs/agent-budget.md`](docs/agent-budget.md).

## Measured baseline

The first blind run of this corpus, committed so that the next rubric or
skill change has a number to beat rather than a hunch. Two reports, five
independent classifications per case, `--model sonnet` (Claude Code 2.1.278
resolved the alias to `claude-sonnet-5`), 2026-09-21:

- `evals/results/baseline-2026-09-21-sonnet-runs1.json` (18 classifications, $6.11)
- `evals/results/baseline-2026-09-21-sonnet-runs4.json` (72 classifications, $20.78)

| Metric (90 classifications) | Value |
|---|---:|
| Route accuracy | 46.7% |
| Route accuracy, resolved from the model's own scores by `scripts/route.py` | 47.8% |
| Policy self-applied OK (model's route == resolver's route) | 90.0% |
| Tier accuracy | 68.9% |
| Agent-set accuracy | 65.6% |
| Agent-budget accuracy | 64.4% |
| Parallelizable accuracy | 78.9% |
| Human-gate accuracy | 90.0% |
| Mean tier stability across cases | 92.2% |
| Mean roster size (oracle) | 1.39 (1.33) |
| Mean cost / duration per classification | $0.30 / 98 s |

What the numbers say, per case, across the five runs:

| Case | Oracle | Observed | Tier hit | Systematic error |
|---|---|---|---:|---|
| REQ-001..003 | T0 | T0×5 each | 15/15 | — |
| REQ-004 | T1 | T0×2, T1×2, T2×1 | 2/5 | unstable at the T0/T1 boundary |
| REQ-005 | T1 | T1×5 | 5/5 | — |
| REQ-006 | T1 | T0×5 | 0/5 | a bug fix with regression tests is scored 1, oracle says 4 |
| REQ-007 | T2 | T2×5 | 5/5 | — |
| REQ-008 | T3 | T2×3, T3×2 | 2/5 | `executes-irreversible-operation` missed 3/5; `writes-secret`, `changes-authentication-flow` missed 5/5 |
| REQ-009..012 | T2/T3 | correct ×5 each | 20/20 | route fails only on `parallelizable` (see below); `coordinates-distributed-work`, `changes-service-contract`, `changes-schema` under-emitted |
| REQ-013 | T2 | T2×5 | 5/5 | — |
| REQ-014 | T2 | T3×5 | 0/5 | every dimension scored 2 (12 vs oracle 8); `human_gate: true` invented 3/5 |
| REQ-015 | T1 | T0×2, T1×3 | 3/5 | unstable at the T0/T1 boundary |
| REQ-016 | T2 | T3×5 | 0/5 | scored 10.6 vs oracle 4: cross-tenant wording inflates scope, architecture and ambiguity; `human_gate: true` invented 4/5 |
| REQ-017 | T2 | T3×5 | 0/5 | scored 10.8 vs oracle 7: a topology split inflates scope, dependencies and verification |
| REQ-018 | T2 | T2×5 | 5/5 | — |

Three conclusions the resolver made attributable:

1. **The model applies the policy correctly.** All 9 of the 90 "policy
   self-applied" misses are the same thing: a `human_gate: true` the policy no
   longer defines. Tier, roster and budget were never misapplied. Every
   remaining route error is in scoring or signal extraction.
2. **`parallelizable` is a judgement the model almost never makes.** It emitted
   `true` once in 90 classifications against 20 in the oracle, and 14 of the
   48 route failures differ on that flag alone. It changes no roster and no
   budget, so treat it as a diagnostic until the rubric says what earns it.
3. **The scoring errors are systematic, not noise.** Tier stability is 92%:
   REQ-006, 014, 016 and 017 miss the same way every run, so they are rubric
   and skill wording to fix, not runs to repeat. Over-routing is the larger
   bias in cost terms: REQ-014/016/017 each spend a T3 roster on T2 work.

None of this was tuned before committing. The rubric, the skill and the
oracle are exactly what the runs saw.

## Session budget

`budget.max_agent_invocations` caps how many contexts a requirement builds. It
says nothing about the context that exists at every tier, T0 included: the
session itself.

A session that dies mid-requirement and is restarted costs several times what
finishing it would have — the prompt cache goes cold (a warm session re-reads
its history at ~0.1x input price; a cold one pays full price plus a cache
write), turn cost is quadratic so the same depth is paid for twice, and the
reads and test runs that produced the session's conclusions are re-run from
zero. Subagent contexts do not survive at all.

Two scripts close that gap, wired in `.claude/settings.example.json`:

```bash
cp .claude/settings.example.json .claude/settings.json       # shared with the repo
cp .claude/settings.example.json .claude/settings.local.json # or just your checkout
```

- **`scripts/hooks/statusline.py`** puts context headroom, 5h/7d rate-limit
  usage and prompt-cache warmth on screen. None of it is visible to the model;
  showing it is what makes stopping a decision rather than an accident. Context
  headroom is always available; the rate-limit and cache segments depend on plan
  and Claude Code version, and are omitted when absent rather than faked — see
  [`docs/session-budget.md`](docs/session-budget.md#status-line).
- **`scripts/hooks/session_budget.py`** captures
  `artifacts/handoff/SESSION-HANDOFF.md` on `PreCompact` and on a `rate_limit`
  `StopFailure` — the two events that fire exactly when a session is about to
  lose its context — replays it on `SessionStart`, and nudges the session to
  write its notes at ~70% context and to wrap up at ~85%.

The handoff file splits along the same line the rest of this template does:
`auto-state` (branch, HEAD, uncommitted paths, diffstat, context occupancy) is
computable, so a script computes it; `model-notes` (goal, done, remaining, next
command) is judgement, so the session writes it and every capture preserves it
verbatim.

Full reference, thresholds and configuration: [`docs/session-budget.md`](docs/session-budget.md).

## CI runner mode

GitHub-hosted minutes are billed for private repositories. When the allowance
runs out, runs stop starting — so every workflow here resolves its runner from
one repository variable instead of hardcoding one:

```yaml
runs-on: ${{ vars.CI_RUNNER || 'ubuntu-latest' }}
```

Setting `CI_RUNNER` moves every job at once, with no commit and no workflow
edit; unsetting it restores `ubuntu-latest`. `scripts/switch_runner.py` converts
workflows to that form (or hard-pins them either way), and its `--check` mode
runs in CI so a workflow added later cannot quietly hardcode a runner while the
switch appears to be on.

`.github/workflows/runner-mode.yml` makes the choice automatic: it runs on the
self-hosted runner — the one place that still works when the hosted quota is
gone, and where minutes are not billed — reads the Actions billing API, and sets
the variable. No other workflow depends on it, so a runner outage leaves CI on
the last decision rather than stalling it — with one exception, the mirror-image
deadlock documented under *Getting unstuck*, which is why a dispatch-only reset
job sits pinned to a hosted runner. The decision itself is
`scripts/pick_runner.py`, a pure function of mode, remaining quota and two
hysteresis thresholds, because *Deterministic work is not agent work* applies to
YAML expressions as much as to agents. Unreadable quota changes nothing and says
so.

Setup, token scopes, thresholds and the self-hosted security note:
[`docs/ci-runner-mode.md`](docs/ci-runner-mode.md).

## Bilingual apps and tools (Japanese/English)

Every app or tool built in a repository created from this template ships its
user-facing text in Japanese and English. `CLAUDE.md` makes that the default
and points at the `bilingual` skill, so a derived repository gets it without
asking:

```text
/bilingual "the CSV export screen"
```

What the skill brings, all under `.claude/skills/bilingual/runtime/`, copied
into the app rather than re-implemented each time:

- `python/i18n.py` — a standard-library `Translator` for CLIs, Tkinter,
  Streamlit and scripts: dotted keys, `{name}` placeholders, `_one`/`_other`
  plurals, `--lang` / `$APP_LANG` / OS-locale detection (Windows included),
  fallback and date formatting.
- `web/i18n.ts`, `web/i18n-provider.tsx`, `web/language-toggle.tsx` — the
  same runtime for the browser, a React provider shaped like the UI kit's
  `ThemeProvider`, and a 日本語 / English switch built only from UI-kit parts.
- `locales/{ja,en}.json` — starter catalogs. Both runtimes read the same
  files, so a tool with a CLI and a web UI keeps one pair.

Whether both catalogs are complete is computable, so it is a script and a CI
step, not a reviewer's job:

```bash
python3 scripts/i18n_check.py            # every locales/ dir in the repo
python3 scripts/i18n_check.py --require ja,en,vi
```

It fails on a missing locale file, a key missing from one language, an empty
message, `{placeholders}` that differ between languages, a plural form
without its partner, a key written twice, a JSON file in `locales/` not
named by a bare language code (`ja.json`, not `ja-JP.json`, which the runtimes
could never select), and a `locales` link that leads nowhere (directory links
are followed during discovery, as the runtimes follow them); it warns on text
identical in both languages. A
repository with no `locales/` directory yet passes, so the step is safe to
keep in CI from day one. The reviewer agents run it and spend their own
judgement on what it cannot see: strings that bypass the catalogs, and
translations that do not say the same thing.

## Design constraint

Every profile is main-session-first. The main session owns requirement analysis, architecture and implementation at every tier; subagents exist only to supply what the main session structurally cannot supply for itself — independent judgement on work it already did.

That is why T3 is three contexts by default, not six roles — four only when a genuinely ambiguous requirement (identity/auth model migrations, cross-service ownership migrations) needs a pre-design `requirement-analyst`, and that reserve is declared and tested independently of the base budget so it can't silently become a general fourth slot. Splitting planning, implementation and testing into separate agents forces each one to rebuild the same context from scratch, and context rebuilding is where multi-agent token cost actually goes. Parallelism changes *when* agents run, never *how many*: `budget.max_agent_invocations` is a hard ceiling that independent tracks do not raise.

## Claude Code references

- Programmatic usage: https://code.claude.com/docs/en/headless
- Skills: https://code.claude.com/docs/en/skills
- Subagents: https://code.claude.com/docs/en/sub-agents
- Hooks: https://code.claude.com/docs/en/hooks
- Status line: https://code.claude.com/docs/en/statusline
