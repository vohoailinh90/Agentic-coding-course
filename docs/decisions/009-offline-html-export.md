# 009 — Offline HTML files for sharing the course without GitHub

**Date:** 2026-09-27 · **Status:** accepted

## Context

The course owner wants to share the course with colleagues who should not have to open GitHub: a
file that can be saved, sent and opened locally. The website (phase 3) is further away, and the
lessons are Markdown files whose infographics are separate SVG files, which a browser cannot show
as a lesson page without a renderer.

## Decision

`python -m src.main export` writes self-contained HTML files to `outputs/html/` (ignored by Git):

- `<course-id>.html` holds every language and opens on a language chooser; `<course-id>-<lang>.html`
  holds one language and opens on its course home. The language links of a one-language file point
  into its sibling files, so the files work together from one folder, and the all-languages file
  works alone.
- **Nothing outside the file**: the style sheet is inline, the infographics are `data:` URIs rendered
  from `course/data/` (never the committed SVGs, so an export is never out of date), and there is no
  script, so a file opens wherever HTML opens — also where scripts in local files are blocked.
- **Pages without a script**: a file is a stack of `<section class="page">` elements; CSS shows the
  one the URL fragment targets (`:target`, `:has()`), so lesson links, the Back button and bookmarks
  behave like a small website. A browser without `:has()` shows every page in order instead.
  Printing shows every page and opens the quiz answers, so *Print → Save as PDF* on a one-language
  file gives the whole course as one PDF — no PDF tool in the repository.
- **What is exported**: every lesson that is `review` or `done` in that language; `review` lessons
  carry a "draft, awaiting review" badge. A link to a lesson that is not exported keeps its text and
  loses its link.
- **Markdown is rendered by `markdown-it-py`** (CommonMark plus GitHub's tables and strikethrough),
  the first dependency besides PyYAML, now declared in `requirements.txt`. A hand-written renderer
  would have to match GitHub on the cases lessons rely on — Markdown inside the quiz answers'
  `<details>` block is the first — and would drift as lessons use more of the syntax. It is imported
  only when an export runs, so `validate` and the other commands work without it.

## Consequences

- `tests/test_course_export.py` exports the real course and requires every internal link, across
  files included, to land on an element, and every tag to be closed; `tests/mutations/course_export.yaml`
  breaks the rules above one at a time.
- The files are generated on demand, not committed: a lesson change would otherwise rewrite
  megabytes of HTML in every commit.
- Raw HTML inside a lesson is copied as it is; only Markdown links and images are rewritten.
- Phase 3 can start from the same page rendering, adding a real language toggle and progress.
