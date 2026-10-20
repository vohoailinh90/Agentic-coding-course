# 012 — A Vietnamese Generative AI store with Moda decks, built by parallel Claude sessions

**Date:** 2026-10-20 · **Status:** accepted by the owner (requested in the session of 2026-10-20)

## Context

The owner wants slide lessons about AI, built on Moda, with the content taken from
microsoft/generative-ai-for-beginners (21 lessons, MIT License), and several Claude sessions working at
once without overlapping, the way `tool-marketing-studio` built the System Design 101 decks (a board
that reserves ranges, a claim before any work, one branch per session). The owner chose this
repository as the home and three parallel sessions. The same day the owner said Codex is out of quota:
the sessions review their own work with a Claude subagent instead.

## Decision

- The programme lives in its own Vietnamese-only store, `genai-for-beginners/vi/`, outside `course/`
  (the same reason as ADR 011: the course schema needs vi, en and ja). The source is pinned to commit
  `c35bc1950f9dc56af773d2c362dafce6f76e9a56` in `source-map.json`.
- **Licence:** the source is MIT, which permits adaptation with the copyright notice; every lesson and
  the last slide of every deck credit it. Lessons are still rewritten for beginners rather than
  translated sentence by sentence, and no source image is copied.
- **No overlap:** `assignments.yaml` gives each range of lessons to exactly one branch; only the
  coordinator session edits it. `scripts/genai_check.py claim` refuses a lesson outside the current
  branch's range or held by another `origin/*` branch, and a worker session touches only its own
  lesson folders, so worker pull requests never conflict.
- **Decks** follow one style (docs/genai-slides.md): 1920x1080, 10 to 12 slides, the System Design
  brand family, the layout table that `genai_check.py` validates. Exports keep the `moda.app` badge.
- **Review:** each worker session calls one Claude subagent per lesson to check the lesson against the
  source and the slides against the style; P1 findings are fixed until none is left, P2/P3 get at most
  two rounds per lesson. No Codex review is requested for these pull requests.
- **Merge:** the owner merges, as ADR 010 says while `main` has no branch protection; the
  Codex-based self-merge rules do not apply because there is no Codex review.

## Consequences

- `scripts/genai_check.py` (run by `tests/test_genai_check.py`, hence by CI) enforces the computable
  part: folder contents, deck records, the layout table, the lesson's required sections and pinned
  source link, the PPTX and its badge, and the board. Whether a lesson is true and clear stays with
  the review subagent and the owner.
- The badged PPTX adds about 1.5 MB per lesson to the repository.
- Moda calls of three sessions share one Moda account; a rate limit stops a session, which then
  reports to the coordinator rather than retrying in a loop.
