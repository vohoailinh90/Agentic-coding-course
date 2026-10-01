# Handoff — continuing the course

For whoever writes the next lessons: Codex, Claude or a person. It gives the working state, what to
write next, and how to write and check a lesson. It points at the rules instead of repeating them:
[content-guide.md](content-guide.md) says how to write a lesson, [data-model.md](data-model.md) what
`validate` enforces. When the two disagree with this page, they win; fix this page.

## State on 2026-10-01

- **Everything is written and waiting for the owner's review:** 52 of 52 lessons in Vietnamese,
  English and Japanese, all with status `review`: the 19-lesson minimum path; `how-to-learn-this-course`,
  `programming-building-blocks`, `command-line-basics`, `ai-ml-dl`, `how-machines-learn`,
  `rag-intro`, `prompt-rag-finetune-compare`, `tokens`, `reasoning-models`, `choosing-models`,
  `traditional-vs-agentic`, `vibe-vs-agentic`, `the-agent-loop`, `tool-landscape`,
  `workflow-frameworks`, `model-plus-harness`, `context-engineering`, `prompt-engineering-for-agents`, `hooks-and-permissions`,
  `tests-and-ci-for-agents`, `memory-and-skills`, `agents-and-workflows`, `mcp`, `evals`, `project-retrospective`, `project-mcp-tool` and `capstone-your-idea`, written by Claude;
  and `security-basics`, `prompting-basics`, `next-token-prediction`, `tool-calling`,
  `what-is-software` and `project-anatomy`, written by Codex. `python -m src.main stats` shows the counts; each course home
  (`course/<lang>/README.md`) lists every lesson in order.
- **0 lessons remain** (table below). The owner decided on 2026-09-27 to write the whole
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
   does not merge. PR #21 was the exception: the owner asked Claude to repeat the review until Codex
   had no findings, and to merge once CI was green.

Codex wrote four batches before this (issues 2, 3, 4 and 6); what the trial taught is kept in the
rules below — the task id at the start of an issue title, and the standard section headings.

## What to write next

In this order — the course order of [`curriculum.yaml`](../course/data/curriculum.yaml), which is
the source if this snapshot goes stale. Lesson ids never change.

| Lesson | Unit (track) | Type | Min | Glossary terms |
|---|---|---|---:|---|

### Sketches for the next two

Starting points, not requirements; the lesson's author decides.

- All 52 lessons are written. Next: the owner reviews every lesson (status `review` → `done`), and `python -m src.main export` builds the offline HTML copy.

Review lessons learned (PR #15): Codex checks that every example spec is satisfiable and fair, that
summaries, objectives and takeaways say exactly what the body says, and that counts and dates are
right in every language — check those before opening the pull request. PR #17 added: the instruction-file
example must hold only what is true for every session; a lesson's minutes must cover reading the
whole body plus the exercise (`PROGRESS.md` then shows the new course total); and every promise about
later lessons must match the curriculum. PR #19 added: a general claim (what CI runs, when, on
what machine; what a subagent knows) must hold for every setup, or say whose setup it describes —
and once a claim is corrected, sweep the summary, takeaways, quiz, both diagrams and the changelog
for the same claim in all three languages. PR #20 added: keep a lesson body near 1,400 Vietnamese
words instead of raising its minutes; date every tool behaviour ("as of September 2026"); quiz
distractors are plausible mistakes, never jokes; real company data is ⛔ with no "approved tool"
exception; and a new technical term gets a glossary entry. PR #21 added: every exercise step must run
exactly as written — a command carries its arguments (`git restore` needs a path), a file or commit a
step relies on must exist (a new empty repository has no commit until something is committed), a break
test must change what the checker really reads, and a score says what an extra or duplicate row does;
an evidence line claims only what the steps make the learner do; and practice data is made-up data
only, never "your own data".

Token counts: `js-tiktoken` installs from the npm registry (the Python `tiktoken` cannot download its
tables here); it is how every count in `tokens` was made. Name the table and the date with a count.

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
