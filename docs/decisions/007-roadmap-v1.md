# 007 — Roadmap v1: hands-on first, a minimum path, optional depth

**Date:** 2026-09-26 · **Status:** accepted (Codex round 2 may refine it)

## Decision

`course/data/curriculum.yaml` is roadmap v1, adopted from the first Codex brainstorm
([brainstorm/round-1.md](../../brainstorm/round-1.md)): 6 modules, 17 units, 52 lessons, 893 minutes.

- **Hands-on from the first sitting.** Learners see an agent work, choose a safe setup, and build a
  one-file page before any theory; software and AI concepts come when a task needs them.
- **A minimum path** of 18 core lessons (337 minutes, two projects) ships first, in course order.
- **Tracks:** units are `core`, `optional` (AI foundations, model literacy) or `advanced` (deeper
  harness practice, advanced projects).
- **Retired ids:** 8 v0 lessons were merged into others and 1 cut; `retired` records where their
  content went, and their ids are never reused. No lesson id changed.

The course owner decided on 2026-09-26, as Claude suggested in round 1:

1. The first practice may use a browser-based (hosted) tool, with a personal-PC route alongside.
2. Japanese follows once the Vietnamese pilot has been tried with learners.
3. The course promises "learn enough to supervise AI that writes code", not "coding without code"
   (`course.yaml` tagline and audience).
4. The office project may use Python — the agent writes it, the learner runs and checks it — with a
   spreadsheet-only route.

## Where v1 departs from Codex's proposal

- Codex's minimum path put `project-personal-page` after files, Git, hallucination and context window,
  against its own module order. v1 keeps the module order (the project right after
  `errors-and-debugging`) and the validator requires the minimum path to follow the course, so a
  learner going through the course in order never meets a lesson out of sequence. It gives an early
  visible result, and Git then fixes the manual copy the learner has just made.
- The pilot lesson was split as proposed, but its four diagrams were kept: two per lesson.
- Only `track`, `minimum_path` and `retired` were added to the data model. Prerequisites, outcomes,
  artifacts, evidence and review dates wait until the lessons that need them are written.

## Defaults until the owner says otherwise

Codex's other open questions go ahead on Claude's suggestions: projects assume a personal computer
with a watch-only route; publishing the personal page is an optional challenge; a native speaker
reads the first Japanese lessons before more are written; every exercise forbids real company or
customer data, passwords and API keys, commands outside the practice folder, and working around a
company PC's restrictions; the advanced track is written after the minimum path has learners;
"agentic engineering" is named once, after the first project.

## Consequences

- Facebook posts follow the minimum path first ([facebook-plan.md](../facebook-plan.md)).
- The course homes list the minimum path first and mark optional and advanced units.
- Lessons are written in the order of the minimum path; `en` and `ja` files are created by `scaffold`
  but the Japanese text waits for the Vietnamese pilot (point 2).
