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
4. Work on the branch your task names and open a pull request; do not push to `main`. Report every
   changed file, the checks you ran with their output, and anything you could not verify.

[`CLAUDE.md`](CLAUDE.md) holds the same project rules for Claude, plus the harness that routes
Claude's own work.

## Repository layout

The repository root holds only what a user needs to run the app: README and
the agent instruction files, dependency files, and at most three entry-point
launchers. Tests go in `tests/`, the app's modules in its package, developer
tooling in `scripts/`. When a change adds a Python file, test or module, or
restructures the repository, follow `.claude/skills/repo-layout/SKILL.md`.

- `python3 scripts/layout_check.py` is the verdict: a test file or test
  directory in the root, a root `.py` that has no
  `if __name__ == "__main__":` guard and is not a Streamlit app (a library
  module), or more than three root entry points fails it. Run it before
  reporting done; reviewers run the script rather than judging the tree by eye.
- Moving existing files is a restructure, not a typo fix: `git mv` to keep
  history, fix every import and path, and prove the test suite still collects
  the same number of tests from its new place.
