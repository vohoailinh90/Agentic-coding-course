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
