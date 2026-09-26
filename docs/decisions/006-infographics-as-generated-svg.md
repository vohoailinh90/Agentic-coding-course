# 006 — Infographics are SVG generated from one spec per diagram

**Date:** 2026-09-26 · **Status:** accepted

## Decision

Each infographic is a YAML spec in `course/data/diagrams/<id>.yaml` holding the text in every
language, rendered by `python -m src.main build` into `course/<lang>/diagrams/<id>.svg`. A handful
of templates cover the lessons: `compare`, `equation`, `cycle`, `flow`, plus the course roadmap drawn
from `curriculum.yaml`.

## Why

- **One drawing, three languages.** A diagram drawn by hand three times drifts; a spec cannot.
- **SVG is text:** it diffs in Git, stays sharp at any size, renders in GitHub Markdown, and CI can
  prove a committed file matches its spec.
- **Lively without breaking:** light CSS motion (flowing arrows, a pulsing result) that stops under
  prefers-reduced-motion; every colour is an attribute, so the static picture is complete wherever
  CSS is ignored.
- **Readable everywhere:** a solid light card background survives GitHub's dark theme.

## Alternatives considered

- **Hand-made images (Canva, Figma, AI image generators).** Prettier one-offs, but three copies per
  diagram, binary diffs, and text that cannot be corrected in one place.
- **Mermaid in Markdown.** Rendered by GitHub, but plain diagram styling, not infographics, and no
  control over colour, icons or motion.
- **HTML rendered to PNG in a browser.** Richer layout, but binary files and a browser in CI.

## Consequences

- Text wrapping uses per-character width estimates (CJK, Latin, emoji, Japanese line-break rules);
  real fonts differ slightly by OS, so estimates are deliberately generous and boxes grow in height.
- New kinds of picture need a new template in `src/core/infographics.py`.
- Facebook needs PNG: exporting the SVGs at 2x is part of the Facebook automation (phase 2).
