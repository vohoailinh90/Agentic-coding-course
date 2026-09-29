# 011 — Claude merges a batch once Codex reports no findings

Status: accepted by the owner, 2026-09-29. Changes the merge step of
[ADR 010](010-claude-writes-codex-reviews.md); the rest of ADR 010 stands.

## Context

Under ADR 010 the owner pressed *Merge* on every batch, and batches waited for that click even when
Codex had nothing left to say and CI was green. On 2026-09-29 the owner asked Claude to merge a
batch by itself once Codex reports no findings, and then go on to the next batch.

`main` has no branch protection, so GitHub cannot atomically refuse a merge whose base moved after
the checks ran ([claude-to-codex.md](../claude-to-codex.md), section 20). The owner's explicit
request is the human decision that section asks for; the steps below keep the remaining risk small.

## Decision

Claude merges a batch's pull request itself when all of these hold on its current head:

- Codex's latest review is of that exact head commit and reports no findings (a 👍 reaction or a
  "didn't find any major issues" reply), and every earlier finding was fixed or answered;
- CI is green on that head, and `validate`, `build --check` and the tests pass locally;
- the base branch has not moved since those checks (if it has, merge it in, re-check, and ask Codex
  again).

The merge passes the validated head SHA to GitHub so it fails if the head has moved, and Claude
records the merge commit on the pull request. There is no fixed round limit any more: Claude asks
Codex again after each push that fixes findings, until a review comes back clean.

## Consequences

- No click needed from the owner; batches follow each other without waiting.
- The owner still reads lessons in status `review` and turns them to `done`; merging is not approval
  of the content.
- If `main` ever gets branch protection with "require branches to be up to date", Claude relies on
  it instead of the manual base check.
