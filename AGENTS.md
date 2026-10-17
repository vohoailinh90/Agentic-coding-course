# Instructions for coding agents

This repository is the content store of a trilingual course (Vietnamese · English · Japanese) that
takes complete beginners to directing AI agents.

1. Read [`PROGRESS.md`](PROGRESS.md) (Vietnamese: the current state) and
   [`docs/handoff.md`](docs/handoff.md) (English: what to write next, and how to write and check a
   lesson).
2. Lessons follow [`docs/content-guide.md`](docs/content-guide.md); the rules `validate` enforces are
   in [`docs/data-model.md`](docs/data-model.md).
3. Before committing anything under `course/`: `python -m src.main build`, then
   `python -m src.main validate` (it must pass) and `python -m pytest -q`. Generated files are
   written by `build`, never by hand.
   For `system-design-101/` (the Vietnamese-only System Design store) run `python3 scripts/sd101_check.py`
   instead; it must pass too.
4. Work on the branch your task names and open a pull request; do not push to `main`. Report every
   changed file, the checks you ran with their output, and anything you could not verify.

[`CLAUDE.md`](CLAUDE.md) holds the same project rules for Claude, plus the harness that routes
Claude's own work.

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
- Before any commit that touches course/ run `python -m src.main validate`, and before any commit that touches system-design-101/ run `python3 scripts/sd101_check.py`.

Where this repository documents its own rule for one of these steps elsewhere (who merges, what gates a merge, how the review is requested, a cap on rounds), that rule governs that step; this process covers whatever the repository leaves unsaid.
<!-- team-onboarding:end -->
