# Handoff — continuing the course

For whoever writes the next lessons: Codex, Claude or a person. It gives the working state, what to
write next, and how to write and check a lesson. It points at the rules instead of repeating them:
[content-guide.md](content-guide.md) says how to write a lesson, [data-model.md](data-model.md) what
`validate` enforces. When the two disagree with this page, they win; fix this page.

## State on 2026-09-27

- **20 of 52 lessons are written** in Vietnamese, English and Japanese, all with status `review`
  (waiting for the owner's read): the 19-lesson minimum path, plus `how-to-learn-this-course`.
  `python -m src.main stats` shows the counts; each course home (`course/<lang>/README.md`) lists
  every lesson in order.
- **32 lessons remain** (table below). The owner decided on 2026-09-27 to write the whole course now,
  in all three languages, with no native Japanese review
  ([ADR 007](decisions/007-roadmap-v1.md), last section).
- The tooling is done and tested. `validate` also checks every finished quiz (three questions,
  options A–C, the same answer key in every language) and rejects a lesson named by its number or
  position ("lesson 3", "ở bài trước", "次のレッスン").

## What to write next

In this order — the course order of [`curriculum.yaml`](../course/data/curriculum.yaml), which is
the source if this snapshot goes stale. Lesson ids never change.

| Lesson | Unit (track) | Type | Min | Glossary terms |
|---|---|---|---:|---|
| `what-is-software` | files-and-projects (core) | concept | 8 | software, program, code |
| `project-anatomy` | files-and-projects (core) | concept | 10 | api |
| `programming-building-blocks` | code-and-history (core) | concept | 12 | program, code |
| `command-line-basics` | code-and-history (core) | hands-on | 15 | terminal |
| `security-basics` | security-essentials (core) | concept | 12 | api-key |
| `prompting-basics` | asking-and-grounding (core) | hands-on | 12 | prompt |
| `next-token-prediction` | asking-and-grounding (core) | concept | 10 | llm, token |
| `tool-calling` | asking-and-grounding (core) | demo | 10 | function-calling, tool |
| `ai-ml-dl` | ai-foundations (optional) | concept | 8 | machine-learning, deep-learning, generative-ai, foundation-model |
| `how-machines-learn` | ai-foundations (optional) | concept | 10 | model, training |
| `rag-intro` | ai-foundations (optional) | demo | 10 | rag |
| `prompt-rag-finetune-compare` | ai-foundations (optional) | concept | 10 | prompt, rag, fine-tuning |
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

- **`what-is-software`** — main character Mai (the accountant who lives in Excel). A program is a
  recipe: exact steps, carried out literally. A cook can follow "salt to taste" (vi *nêm vừa ăn*,
  ja *塩少々*); a computer cannot guess, so every step must be exact. Explanatory infographic: a
  `compare` of recipe and program over shared rows — written in, what goes in, who follows it
  (the `emphasis_row`: a cook guesses, a computer does exactly what is written), what comes out.
  Example: Mai's `=SUM(...)` is already a one-line program; the same job as a few commented lines
  of Python; and the tip that she never has to write it — she can ask the agent to explain code
  line by line in plain words. The weekly task card from
  [`first-agent-session`](../course/en/lessons/first-agent-session.md) is software the learner
  already made (open it in a text editor to see its code).
- **`project-anatomy`** — frontend, backend, database and API as the parts of one app, with the
  glossary's own analogy for an API (the menu a restaurant hands its customers). Explanatory
  infographic: a `flow` of one request, from the screen to the data and back, with labelled
  arrows. Why a beginner needs it: to tell an agent which part to change ("only the page, not the
  data") and to recognise the parts in a diff by their folders.

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
- A content task does not change `src/`, `tests/` or `scripts/`. If a check blocks correct content,
  report it instead of working around it.

## When a batch is done

Update [PROGRESS.md](../PROGRESS.md) (Vietnamese) and the changelog, run `python -m src.main export`
for fresh offline HTML files, and report what was written, the checks you ran and their output,
and anything you could not verify.
