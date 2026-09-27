# Handoff — continuing the course

For whoever writes the next lessons: Codex, Claude or a person. It gives the working state, what to
write next, and how to write and check a lesson. It points at the rules instead of repeating them:
[content-guide.md](content-guide.md) says how to write a lesson, [data-model.md](data-model.md) what
`validate` enforces. When the two disagree with this page, they win; fix this page.

## State on 2026-09-27

- **32 of 52 lessons are written** in Vietnamese, English and Japanese, all with status `review`
  (waiting for the owner's read): the 19-lesson minimum path; `how-to-learn-this-course`,
  `programming-building-blocks`, `command-line-basics`, `ai-ml-dl`, `how-machines-learn`,
  `rag-intro` and `prompt-rag-finetune-compare`, written by Claude; and `security-basics`,
  `prompting-basics`, `next-token-prediction`, `tool-calling`, `what-is-software` and
  `project-anatomy`, written by Codex. `python -m src.main stats` shows the counts; each course home
  (`course/<lang>/README.md`) lists every lesson in order.
- **20 lessons remain** (table below). The owner decided on 2026-09-27 to write the whole
  course now, in all three languages, with no native Japanese review
  ([ADR 007](decisions/007-roadmap-v1.md), last section).
- The tooling is done and tested. `validate` also checks every finished quiz (three questions,
  options A–C, the same answer key in every language) and rejects a lesson named by its number or
  position ("lesson 3", "ở bài trước", "次のレッスン").

## Working model

Since 2026-09-27 ([ADR 010](decisions/010-claude-writes-codex-reviews.md)) **Claude writes the
lessons and Codex reviews them**:

1. Claude writes a batch of about two lessons, in all three languages, on a `claude/<batch>` branch,
   runs every check below, and opens a pull request.
2. Claude asks Codex for a review on the pull request (the built-in review command of
   [claude-to-codex.md](claude-to-codex.md)); Codex posts its findings there.
3. Claude checks each finding against the repository, fixes the confirmed ones and pushes (at most
   two review rounds). The owner merges once CI is green: `main` has no branch protection, so Claude
   does not merge.

Codex wrote four batches before this (issues 2, 3, 4 and 6); what the trial taught is kept in the
rules below — the task id at the start of an issue title, and the standard section headings.

## What to write next

In this order — the course order of [`curriculum.yaml`](../course/data/curriculum.yaml), which is
the source if this snapshot goes stale. Lesson ids never change.

| Lesson | Unit (track) | Type | Min | Glossary terms |
|---|---|---|---:|---|
| `tokens` | model-literacy (optional) | demo | 8 | token |
| `reasoning-models` | model-literacy (optional) | concept | 10 | llm |
| `choosing-models` | model-literacy (optional) | hands-on | 10 | token, model |
| `traditional-vs-agentic` | agentic-work-as-a-system (core) | concept | 8 | agentic-coding |
| `vibe-vs-agentic` | agentic-work-as-a-system (core) | concept | 8 | vibe-coding, agentic-coding |
| `the-agent-loop` | agentic-work-as-a-system (core) | demo | 10 | agent-loop, tool |
| `tool-landscape` | agentic-work-as-a-system (core) | concept | 10 | – |
| `workflow-frameworks` | agentic-work-as-a-system (core) | concept | 10 | test |
| `model-plus-harness` | minimum-harness (core) | concept | 10 | harness, model |
| `context-engineering` | minimum-harness (core) | hands-on | 12 | context-engineering, context-window |
| `prompt-engineering-for-agents` | minimum-harness (core) | hands-on | 12 | prompt |
| `hooks-and-permissions` | minimum-harness (core) | hands-on | 12 | hook |
| `tests-and-ci-for-agents` | minimum-harness (core) | demo | 12 | test, ci |
| `memory-and-skills` | advanced-practice (advanced) | hands-on | 15 | – |
| `agents-and-workflows` | advanced-practice (advanced) | concept | 12 | subagent |
| `mcp` | advanced-practice (advanced) | demo | 12 | mcp |
| `evals` | advanced-practice (advanced) | hands-on | 15 | eval |
| `project-retrospective` | office-outcome (core) | hands-on | 15 | – |
| `project-mcp-tool` | advanced-projects (advanced) | project | 90 | mcp |
| `capstone-your-idea` | advanced-projects (advanced) | project | 120 | – |

### Sketches for the next two

Starting points, not requirements; the lesson's author decides.

- **`tokens`** (demo) — a model reads and writes in tokens, small pieces of text (a word, part of a
  word, a punctuation mark), and the context window, limits and usage are counted in them. Watch one
  sentence split into tokens, in more than one language, and count; link
  [`next-token-prediction`](../course/en/lessons/next-token-prediction.md) and
  [`context-window`](../course/en/lessons/context-window.md) rather than re-teaching them. Cite only
  counts you produced yourself or found in a source you opened; name no prices.
- **`reasoning-models`** — some models can work through a problem in steps before they answer
  ("thinking"), which helps with multi-step tasks and costs time and tokens. When it is worth it,
  and why the steps you can see are not a guarantee of a right answer. Anthropic's thinking
  documentation (platform.claude.com, *thinking* and *extended thinking*) is reachable; date what
  you cite, since it changes fast. A `compare` infographic fits (answer at once vs. think first).

## How to write one lesson

1. `python -m src.main scaffold <lesson-id>` — creates the file in `course/vi|en|ja/lessons/` with
   the language bar, the title and the sections the lesson type needs. Keep the bar and title as
   they are.
2. **Write Vietnamese first.** Follow [content-guide.md](content-guide.md): one idea, concrete before
   abstract, 7–12 minutes (about 900–1,400 Vietnamese words; projects longer), short paragraphs.
   Read a finished lesson of the same type first and match its tone and length:
   `context-window` (concept), `watch-an-agent-build` (demo), `writing-good-specs` (hands-on),
   `project-office-automation` (project).
3. **Infographics:** one explanatory diagram where the lesson compares, adds up, repeats or walks
   through steps, plus the recap `<lesson-id>-recap.yaml` (a `summary` of 3–6 points) — specs in
   `course/data/diagrams/`, keys in [data-model.md](data-model.md). Templates: `compare`,
   `equation`, `cycle`, `flow`, `summary`. Colours: blue, violet, green, amber, rose, teal, orange,
   indigo, pink, slate (tools are amber, the agent green, across the course). Use emoji that show as
   colour emoji by default; ⚖️ ↩️ ⚙️ 🛡️ 🕵️ render as plain text in some browsers and 📎 is faint.
4. **Localize English and Japanese** in the same pass: every section, point and diagram, with the
   quiz options in the same order (the answer key must match). Localize names of dishes, money,
   places and workplace habits; the cast keeps its names (ja: マイ, トゥアン, ハナ, フイ).
5. `python -m src.main build`, then `python -m src.main validate` — it must print `Content store
   OK`. It also fails on crowded diagrams and on words a box has to cut in two.
6. Look at each new SVG in all three languages (`course/<lang>/diagrams/`); `validate` catches
   overlaps and cut words, not a layout that reads badly. If you cannot view images, say so.
7. `python -m pytest -q` (the committed store is itself a test) and `python -m src.main build
   --check`. One commit per lesson: `Write <lesson-id>: <the lesson's idea in a few words>`.

Setup: Python 3.10+, `python -m pip install -r requirements.txt` (PyYAML; markdown-it-py is needed
only by `export`).

## Rules that are easy to miss

- **Facts:** cite only sources you opened, naming the organization, the language and, when it ages
  fast, the date. Never invent a statistic or a quote; if a number cannot be cited, leave it out.
  Tool steps (menus, plan names, commands) are dated "as of September 2026" and never carry prices.
  If a documentation site cannot be reached, do not cite it.
- **Safety in exercises:** everything happens in the practice folder `ai-practice`, with made-up
  data; the three kinds of action are ✅ safe, ✋ ask first, ⛔ never (real company or customer
  data, passwords and API keys, getting around a company computer's rules). Hands-on lessons and
  projects end with the three-line evidence (*I can show… / I checked… / I would not use this
  when…*).
- **References to other lessons:** by name, with a link — never by number or position.
- **Quiz:** three questions × three options, tempting wrong options, answers with a reason in
  `<details>`, and the right letter varied across the questions.
- **Public repository:** no personal information about the owner or anyone real.
- **Generated files** — course homes, glossary pages, `course/<lang>/diagrams/*.svg` — are written by
  `build`; never edit them by hand. Do not change lesson ids or the order in `curriculum.yaml`.
- Keep the section headings `scaffold` writes: they come from `course/data/sections.yaml`, in every
  language. The hook's heading is not the place for the lesson's own title.
- When a fix changes what a lesson claims, change its front-matter `summary` and `social` lines too:
  exports and Facebook drafts reuse them, and a review will find the old claim there.
- A content task does not change `src/`, `tests/` or `scripts/`. If a check blocks correct content,
  report it instead of working around it.

## When a batch is done

Update [PROGRESS.md](../PROGRESS.md) (Vietnamese) and the changelog, run `python -m src.main export`
for fresh offline HTML files, and report what was written, the checks you ran and their output,
and anything you could not verify.
