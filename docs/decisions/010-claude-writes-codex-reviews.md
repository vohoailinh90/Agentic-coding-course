# 010 — Claude writes the lessons; Codex reviews each batch

Status: accepted by the owner, 2026-09-27.

## Context

Claude wrote the 19-lesson minimum path. The owner then tried the reverse for four batches (ACC-0002
to ACC-0007): Codex wrote the lessons and Claude coordinated and validated them. The lessons were
good, but Codex Cloud cannot push: every batch needed the owner to find the Codex task and press
*Create PR*, and a batch whose task could not be found was lost (ACC-0002, written again as
ACC-0007). The Codex GitHub Action would open pull requests by itself, but it bills the OpenAI API
separately from the owner's ChatGPT plan; the owner declined it and keeps the `@codex` comment route
of [claude-to-codex.md](../claude-to-codex.md).

## Decision

- Claude writes each batch — about two lessons, in vi, en and ja — on a `claude/<batch>` branch and
  opens a pull request.
- Claude posts the built-in review command on the pull request; Codex reviews it, no click needed.
- Claude checks every finding against the repository, fixes the confirmed ones on the branch, and
  asks for a new review only after a push (at most two rounds per batch).
- The owner merges once CI is green and the review is settled: `main` has no branch protection, so
  Claude does not merge (claude-to-codex.md, section 20).
- Checks with a computable answer stay in `validate` and the tests; the review is for judgement —
  facts, clarity for a beginner, and whether the three languages say the same thing.

## Consequences

- No *Create PR* clicks; one *Merge* click per batch.
- Codex's review is the batch's independent review in place of a Claude subagent, so it spends
  none of Claude's budget.
- Work already with Codex: PR 8 (ACC-0006) is validated and merges as it is; ACC-0007 (issue 2) is
  used if the owner publishes it, otherwise Claude writes those two lessons.
