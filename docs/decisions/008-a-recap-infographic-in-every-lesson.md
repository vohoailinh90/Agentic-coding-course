# 008 — Every lesson ends with a recap infographic

**Date:** 2026-09-26 · **Status:** accepted

## Decision

Every lesson has a `recap` section — "Tóm tắt bằng hình" · "The Lesson in One Picture" ·
"1枚でわかるこのレッスン" — just before its takeaways. Once a lesson is in review it shows exactly one
infographic there, one of its own: a picture that sums up the whole lesson, not a diagram already used
in the lesson. It is usually drawn with the `summary` template: 3–6 numbered key points on coloured
cards, with the one sentence to remember underneath. `validate` enforces all of this.

## Why

- The course owner asked for it: learners should be able to look at one picture and remember the
  lesson.
- It is the image for the lesson's Facebook post, and a visual signature the whole course shares.
- A section of its own shows up in the page's "On this page" contents and can be checked by a script.

## Alternatives considered

- **The picture inside `takeaways`.** No entry in the contents, and a rule that is harder to state.
- **Reusing one of the lesson's diagrams.** It covers only part of the lesson.
- **Hand-made summary images.** Three copies per lesson that drift apart; see
  [ADR 006](006-infographics-as-generated-svg.md).

## Consequences

- The lesson template has twelve sections; round 1 of the brainstorm asked for fewer. The recap is
  fast to read, and the takeaways stay short because they restate its points in words (for readers
  who cannot see the picture, and for the post text).
- A new template, `summary`, lays out the points on a grid (3 → one row, 4 → 2×2, 5 → 3 + 2, 6 → 3×2).
- `scaffold` adds the section with a hint; writing the recap spec is part of writing the lesson.
