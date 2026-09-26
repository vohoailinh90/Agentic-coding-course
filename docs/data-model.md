# Data model — the content store under `course/`

The course lives in plain files so that people and AI agents can edit it with ordinary tools and
Git keeps the history. Everything computable about those files is checked by
`python -m src.main validate`, locally and in CI (`.github/workflows/python-app.yml`), so a
broken lesson cannot reach the website or a Facebook post.

```text
course/
├── course.yaml        metadata: id, languages, source language, title, tagline, audience, hashtags
├── curriculum.yaml    the tree: modules → units → lessons, with titles, type, minutes, terms
├── sections.yaml      the sections a lesson may have, their order, headings and writing hints
├── glossary.yaml      one entry per term, in every course language
├── lessons/
│   └── <lesson-id>/
│       ├── vi.md      one file per course language
│       ├── en.md
│       ├── ja.md
│       └── assets/    optional: images for this lesson
└── OUTLINE.md         GENERATED from curriculum.yaml — never edit by hand
```

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
- Display numbers such as `4.3.2` (module.unit.lesson) are computed from position and may
  change whenever the roadmap is reordered. Do not store them anywhere.

## `course.yaml`

| Field | Type | Rule |
|---|---|---|
| `id` | slug | |
| `version` | text | the course content version |
| `languages` | list of language codes | e.g. `[vi, en, ja]`; every localized field needs all of them |
| `source_language` | code | one of `languages`; written first, reference for section parity |
| `title`, `tagline`, `audience` | localized text | |
| `hashtags` | `{language: [#tag, ...]}` | appended to every generated post |

## `curriculum.yaml`

```yaml
version: 0.1.0-draft
modules:
  - id: kickoff
    title: {...}            # localized
    goal: {...}             # localized: what the learner can do after the module
    units:
      - id: big-picture
        title: {...}
        lessons:
          - id: chatbot-to-agent
            title: {...}
            type: concept       # concept | demo | hands-on | project
            minutes: 10         # whole number > 0
            terms: [chatbot, llm, ai-agent]   # optional: glossary ids, no repeats
```

Glossary terms that no lesson uses produce a warning, not an error.

## `sections.yaml`

A list of `{key, required_for, heading, hint}`: `key` is a slug, `required_for` a list of lesson
types, `heading` and `hint` localized. The list order is the order sections must appear in a
lesson. `scaffold` writes every section with its heading and, as a `<!-- TODO: hint -->`, the
hint.

## `glossary.yaml`

```yaml
terms:
  - id: context-window
    vi: {term: ..., definition: ...}
    en: {term: ..., definition: ...}
    ja: {term: ..., reading: ..., definition: ...}   # reading: kana for the kanji, optional
```

## Lesson files: `lessons/<lesson-id>/<language>.md`

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

# <exactly the curriculum.yaml title in this language>

<!-- section: objective -->
## Mục tiêu bài học

...
```

- A lesson folder exists once the lesson is started, and then holds **every** course language.
  Nothing else may be in it except an optional `assets/` folder.
- Front matter keys are exactly `lesson`, `lang`, `status`, `summary`, `social` (`hook`,
  `question`); `lesson` and `lang` must match the path.
- The `# ` title must equal the curriculum title for that language.
- Every `## ` heading sits directly under a `<!-- section: key -->` marker (blank lines between
  are fine). Text between the title and the first section is not allowed. `###` and deeper
  headings are free. Fenced code blocks are skipped, so `# comments` in examples are safe.
- Section keys must exist in `sections.yaml`, appear once, and follow its order.
- All language files of a lesson whose status is not `todo` have the same section keys in the
  same order; the source language file is the reference.

### Status

| Status | Required sections present | No empty section, no `<!-- TODO`, summary set | `social.hook`, `social.question` set |
|---|---|---|---|
| `todo` | – | – | – |
| `draft` | ✓ | – | – |
| `review` | ✓ | ✓ | – |
| `done` | ✓ | ✓ | ✓ |

## Who reads the store

- **`python -m src.main stats`** — size of the course and per-language progress.
- **`python -m src.main fb-draft`** — a Facebook post assembled from `social.hook`, the title,
  `summary`, the `takeaways` section, the lesson's glossary terms in all languages,
  `social.question` and the hashtags ([facebook-plan.md](facebook-plan.md)).
- **The website (phase 3)** — the course tree with module/unit/lesson counts and per-learner
  progress, and a lesson page whose "On this page" table of contents is the list of `## `
  headings. Everything it needs is already in this model; the site only renders it.
