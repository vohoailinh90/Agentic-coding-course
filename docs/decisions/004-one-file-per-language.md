# 004 — One file per language, aligned by section markers; Vietnamese is the source

**Date:** 2026-09-26 · **Status:** accepted

## Decision

Each lesson is a folder with one Markdown file per course language (`vi.md`, `en.md`, `ja.md`).
Sections are introduced by invisible markers (`<!-- section: analogy -->`) followed by a heading
whose text is localized. Vietnamese is the source language: it is written first and is the
reference the other files' sections must match.

## Why

- Each file reads naturally on GitHub and can be written and reviewed by someone who knows only
  that language.
- Markers make the structure machine-checkable across languages without forcing English headings
  on Vietnamese or Japanese readers.
- Linh thinks and teaches best in Vietnamese, and the first audience is Vietnamese.

## Alternatives considered

- **All three languages side by side in one file.** Hard to read, and every edit touches every
  language.
- **Translation keys or a CMS with locales.** Built for UI strings, not for long-form teaching text
  that must be localized rather than translated sentence by sentence.

## Consequences

Parity is only enforced once a language file leaves `todo`, so a lesson can be started in
Vietnamese while the other files are still skeletons.
