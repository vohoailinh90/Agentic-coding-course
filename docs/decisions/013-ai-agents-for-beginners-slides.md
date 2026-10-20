# 013 — A Vietnamese AI Agents store with Moda decks, built by two parallel Claude sessions

**Date:** 2026-10-20 · **Status:** accepted by the owner (requested in the session of 2026-10-20)

## Context

The owner asked for Moda slide lessons about AI from a free repository, built by two Claude sessions
at once without overlap, the way `tool-marketing-studio` built the System Design 101 decks. Another
coordinator session had already set up `genai-for-beginners/vi/` (ADR 012, branch
`claude/genai-slides-setup`) and given all 21 lessons of microsoft/generative-ai-for-beginners to
three worker branches. So that the two new sessions duplicate none of that work, the owner chose the
next repository of the same list: microsoft/ai-agents-for-beginners (MIT License). The owner also chose
Sonnet with high effort for the two worker sessions.

## Decision

- The programme lives in its own Vietnamese-only store, `ai-agents-for-beginners/vi/`, with ids `ag-01`
  to `ag-18` (lessons 01 to 18 of the source; `00-course-setup` only installs the course's own
  environment). The source is pinned to commit `9923c54bcc2df67e7119945e12cd2d45944da2f6`.
- **The same process as ADR 012**, in files of its own so that neither programme's pull request touches
  the other's: `docs/agents-slides.md`, `scripts/agents_check.py` (a copy of `genai_check.py` with this
  store's paths, id prefix and credit line), its tests and mutation manifest. Worker branches are
  `claude/agents-slides-w1` (`ag-01..ag-09`) and `claude/agents-slides-w2` (`ag-10..ag-18`).
- **Licence:** MIT; every lesson and the last slide of every deck credit microsoft/ai-agents-for-beginners.
  Lessons are rewritten for beginners rather than translated sentence by sentence; no source image is copied.
- **Review:** one Claude subagent per lesson, as in ADR 012 (Codex is out of quota). **Merge:** the owner
  merges (ADR 010, while `main` has no branch protection).

## Consequences

- Two checkers exist with the same logic. Once both programmes have merged, they can become one script
  with a store argument; doing it now would edit the other session's unmerged files.
- Five sessions (three for ADR 012, two here) share one Moda account; a rate limit stops a session,
  which then reports to its coordinator rather than retrying in a loop.
- The badged PPTX adds about 1.5 MB per lesson to the repository.
