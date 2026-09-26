# 005 — One folder per language, and a language bar on every page

**Date:** 2026-09-26 · **Status:** accepted · supersedes the layout of [004](004-one-file-per-language.md)

## Decision

Everything a learner reads lives in one folder per language — `course/vi/`, `course/en/`,
`course/ja/` — and every file in it is in that language only: the course home (`README.md`, with
the outline), the glossary page, the lessons (`lessons/<id>.md`) and the infographics
(`diagrams/<id>.svg`). The sources that hold all languages at once move to `course/data/`, and
`course/README.md` is only a language chooser.

Every learner page starts with a language bar, `🌐 **Tiếng Việt** · [English](…) · [日本語](…)`,
linking the same page in the other languages. It is generated for the homes and glossaries, written
by `scaffold` for lessons, and checked exactly by `validate`.

## Why

- Linh asked for it after seeing the first outline: a table with Vietnamese, English and Japanese
  titles side by side is hard to read. A learner should see one language and switch when they want.
- On GitHub, a folder per language is the whole course in that language, browsable on its own.
- The bar gives the "click to change language" experience today, before the website exists.

## Alternatives considered

- **A website with a toggle button only.** The right end state (phase 3), but it would leave the
  repository — where the content is written, reviewed and linked from posts — mixed-language.
- **Keeping `lessons/<id>/{vi,en,ja}.md`.** Each file was single-language already, but browsing
  the course in one language meant opening a folder per lesson.

## Consequences

Section and diagram parity between translations is unchanged (004). Generated pages list every
lesson and link only those that exist, so `scaffold` rebuilds them.
