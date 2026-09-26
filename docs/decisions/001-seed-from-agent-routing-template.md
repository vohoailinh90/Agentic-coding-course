# 001 — Seed the course repository from claude-agent-routing-template

**Date:** 2026-09-26 · **Status:** accepted

## Decision

The repository starts as a copy of `vohoailinh90/claude-agent-routing-template` at
`2a65b510358cd3f05011176bc0c8382b0f7b8e1d` (files only, no history — what GitHub's "Use this
template" does), with the course added on top. The template's own README is kept as `TEMPLATE.md`.

## Why

- Every Claude Code session here gets the same routing policy, agents, skills and session-budget
  hooks as Linh's other repositories.
- The Codex brainstorm needs `docs/claude-to-codex.md`, the only approved way to delegate to Codex.
- The course website (phase 3) will need the `ui-kit` and `bilingual` skills that ship with it.

## Alternatives considered

- **A lean content-only repository.** Cleaner at the root, but it would lose the harness and the
  Codex protocol, and diverge from how Linh's other projects are set up.
- **Course content inside the template repository.** Rejected: it would pollute the template that
  every other project is created from.

## Consequences

The root holds harness folders (`agent-routing/`, `evals/`, `profiles/`, `scripts/`) next to the
course. Course content stays in `course/`, `brainstorm/` and `docs/`; course code in `src/`.
