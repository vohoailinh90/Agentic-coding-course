# Data model — the content store under `course/`

The course lives in plain files so that people and AI agents can edit it with ordinary tools and
Git keeps the history. Everything computable about those files is checked by
`python -m src.main validate`, locally and in CI (`.github/workflows/python-app.yml`), so a broken
lesson cannot reach the website or a Facebook post.

```text
course/
├── README.md                 GENERATED — language chooser
├── data/                     sources that hold every language at once (edited by hand)
│   ├── course.yaml           id, languages, source language, title, tagline, audience, hashtags
│   ├── curriculum.yaml       the tree: modules → units → lessons
│   ├── sections.yaml         the sections a lesson may have, their order, headings and hints
│   ├── glossary.yaml         one entry per term, in every course language
│   └── diagrams/<id>.yaml    infographic specs
├── vi/                       everything a Vietnamese learner reads — Vietnamese only
│   ├── README.md             GENERATED — course home: tagline, roadmap, outline with links
│   ├── glossary.md           GENERATED — the glossary, explained in Vietnamese
│   ├── lessons/<id>.md       hand-written lessons
│   ├── diagrams/<id>.svg     GENERATED — infographics, plus roadmap.svg
│   └── images/               optional hand-made images
├── en/                       the same, in English
└── ja/                       the same, in Japanese
```

Run `python -m src.main build` after changing anything under `course/data/` or adding a lesson;
`validate` fails with `build_stale` while a generated file differs from what `build` would write,
and when a generated diagram no longer has a spec.

## Common rules

- Files are UTF-8. A BOM or Windows line endings are accepted and ignored.
- YAML is parsed strictly: a key written twice in one mapping is an error (PyYAML would silently
  keep the last one).
- Prefer block style in YAML. In a flow mapping such as `{vi: a, en: b}`, a comma ends the value,
  so `{vi: Cơ bản, dễ hiểu, en: ...}` quietly becomes two keys. Unknown keys are therefore always
  reported, which is how this mistake surfaces.
- **Localized fields** are mappings with exactly the languages in `course.yaml` `languages`, each
  non-empty text: `title: {vi: ..., en: ..., ja: ...}` (written in block style).
- **Ids** are kebab-case slugs (`^[a-z0-9]+(-[a-z0-9]+)*$`), unique across modules, units and
  lessons together. An id never changes once a lesson has files or posts; order comes from
  position in `curriculum.yaml` ([ADR 003](decisions/003-stable-slug-ids.md)).
- Display numbers such as `4.3.2` (module.unit.lesson) are computed from position and may change
  whenever the roadmap is reordered. Do not store them anywhere.
- Nothing else may sit in `course/`, `course/data/`, a language folder or its `lessons/` folder.

## `data/course.yaml`

| Field | Type | Rule |
|---|---|---|
| `id` | slug | |
| `version` | text | the course content version |
| `languages` | list of language codes | e.g. `[vi, en, ja]`; one folder each; every localized field needs all of them |
| `source_language` | code | one of `languages`; written first, reference for parity |
| `title`, `tagline`, `audience` | localized text | shown on the course homes and the chooser |
| `hashtags` | `{language: [#tag, ...]}` | appended to every generated post |

## `data/curriculum.yaml`

```yaml
version: 1.0.0-draft
modules:
  - id: first-win
    icon: "🚀"              # optional: one emoji, shown on the roadmap and course homes
    title: {...}            # localized
    goal: {...}             # localized: what the learner can do after the module
    units:
      - id: what-agents-do
        track: core         # optional: core (default) | optional | advanced
        title: {...}
        lessons:
          - id: chatbot-to-agent
            title: {...}
            type: concept       # concept | demo | hands-on | project
            minutes: 8          # whole number > 0
            terms: [chatbot, llm, ai-agent]   # optional: glossary ids, no repeats
minimum_path:               # optional: the lessons a learner takes first, in order
  - chatbot-to-agent
retired:                    # optional: ids that were lessons once and are never reused
  - id: cli-for-agents
    into: command-line-basics   # optional: the lesson that now teaches its content
```

- Glossary terms that no lesson uses produce a warning, not an error.
- `minimum_path` takes each lesson once, only lessons of `core` units, and in course order — so a
  learner who goes through the course in order never meets a lesson before one the path puts ahead
  of it. The course homes list it first and mark its lessons ⭐; the roadmap counts them per module.
- A `retired` id may not appear anywhere in the tree, and `into` must be a current lesson. A lesson
  file for a retired id is reported like any file for an unknown lesson.

## `data/sections.yaml`

A list of `{key, required_for, heading, hint}`: `key` is a slug, `required_for` a list of lesson
types, `heading` and `hint` localized. The list order is the order sections must appear in a
lesson. `scaffold` writes every section with its heading and, as a `<!-- TODO: hint -->`, the hint.

## `data/glossary.yaml`

```yaml
terms:
  - id: context-window
    vi: {term: ..., definition: ...}
    en: {term: ..., definition: ...}
    ja: {term: ..., reading: ..., definition: ...}   # reading: kana for the kanji, optional
```

## `data/diagrams/<id>.yaml` — infographics

The file name is the diagram's id (a slug; `roadmap` is reserved for the generated journey map).
Every text field is localized; `icon` is one emoji; `color` is one of `blue`, `violet`, `green`,
`amber`, `rose`, `teal`, `orange`, `indigo`, `pink`, `slate`. Common keys: `template` and `title`
(required), `subtitle` and `takeaway` (optional, the takeaway is the one sentence in the amber box).

| Template | Shows | Keys |
|---|---|---|
| `compare` | 2–4 options side by side over shared rows | `rows` (1–6 labels), `columns` (2–4 × `icon`, `color`, `name`, `values` — one per row — optional `highlight`, `badge`), optional `versus` (2 columns), `emphasis_row` (1-based) |
| `equation` | parts that add up to a whole | `terms` (2–4 × `icon`, `color`, `name`, optional `caption`), `result` (same shape) |
| `cycle` | a loop that repeats | `steps` (3–6 × `icon`, `color`, `name`, optional `caption`, `arrow` — the label on the arrow leaving the step), `center` (`icon`, `name`, optional `color`) |
| `flow` | steps in order | `steps` (2–6, as in `cycle`), optional `direction` (`horizontal` up to 4 steps by default, else `vertical`) |
| `summary` | a lesson's recap: its key points | `points` (3–6 × `icon`, `color`, `name`, optional `caption`), drawn as numbered cards: 3 in a row, 2×2, 3 + 2 or 3×2 |

`validate` also draws every diagram in every language and fails with `diagram_crowded` when its text
cannot be laid out without boxes overlapping (in practice: a cycle of 5–6 steps with long captions).

A lesson shows a diagram with an image in the language folder's `diagrams/`:
`![<alt text in the lesson's language>](../diagrams/<id>.svg)`.

## Lesson files: `<lang>/lessons/<lesson-id>.md`

```markdown
---
lesson: chatbot-to-agent
lang: vi
status: review
summary: >-
  ...
social:
  hook: "..."
  question: ...
---

🌐 **Tiếng Việt** · [English](../../en/lessons/chatbot-to-agent.md) · [日本語](../../ja/lessons/chatbot-to-agent.md)

# <exactly the curriculum.yaml title in this language>

<!-- section: objective -->
## Mục tiêu bài học

...
```

- A lesson is started once any language has its file; it then needs a file in every language
  folder (`scaffold` creates them all).
- Front matter keys are exactly `lesson`, `lang`, `status`, `summary`, `social` (`hook`,
  `question`); `lesson` and `lang` must match the path.
- The language bar comes first, exactly as generated: this language in bold, the others linked, in
  the order of `languages`. Then the `# ` title, equal to the curriculum title for this language.
- Every `## ` heading sits directly under a `<!-- section: key -->` marker (blank lines between are
  fine). No other text may come before the first section. `###` and deeper headings are free.
  Fenced code blocks are skipped, so `# comments` and example links in them are safe.
- Section keys must exist in `sections.yaml`, appear once, and follow its order.
- Every image needs alt text; an image in `../diagrams/` must name a diagram spec; every other
  relative image or link must point to a file that exists.
- Every lesson type requires the `recap` section ([ADR 008](decisions/008-a-recap-infographic-in-every-lesson.md)).
  From status `review`, it shows exactly one image, a diagram, and that diagram appears nowhere else in
  the lesson: the recap sums up the whole lesson in a picture of its own (usually a `summary`).
- All language files of a lesson whose status is not `todo` have the same section keys in the same
  order and show the same diagrams in the same sections; the source language file is the reference.
- From status `review`, a `quiz` section has three questions with the options `A)`, `B)`, `C)` and an
  answer key `1. **B** — …` for each (`quiz_shape`). Every language has the same key, because the
  options are in the same order (`quiz_key_differs`); a key that is one letter three times is a
  warning (`quiz_one_letter`).
- Outside code blocks, no lesson is pointed at by its number or position — *lesson 3*, *ở bài trước*,
  *次のレッスン* (`lesson_by_position`); a reordered roadmap would make it wrong.

### Status

| Status | Required sections present | No empty section, no `<!-- TODO`, summary set | `social.hook`, `social.question` set |
|---|---|---|---|
| `todo` | – | – | – |
| `draft` | ✓ | – | – |
| `review` | ✓ | ✓, and the recap shows its own infographic | – |
| `done` | ✓ | ✓, and the recap shows its own infographic | ✓ |

## Who reads the store

- **`python -m src.main stats`** — size of the course and per-language progress.
- **`python -m src.main fb-draft`** — a Facebook post assembled from `social.hook`, the title,
  `summary`, the `takeaways` section, the lesson's glossary terms in all languages,
  `social.question` and the hashtags ([facebook-plan.md](facebook-plan.md)).
- **GitHub, today** — each language folder is the whole course in that language, and the language
  bar switches between them.
- **`python -m src.main export`** — self-contained HTML files for reading offline, one with every
  language and one per language, holding every lesson that is `review` or `done` in that language
  ([ADR 009](decisions/009-offline-html-export.md)).
- **The website (phase 3)** — the same tree with a real language toggle, module/unit/lesson counts
  and per-learner progress; a lesson's "On this page" contents are its `## ` headings. Everything it
  needs is already in this model; the site only renders it.
