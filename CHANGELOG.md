# Changelog

## Unreleased

- Two more lessons by Claude in vi, en and ja (status `review`): `agents-and-workflows` (workflows
  versus agents; climb the complexity ladder one step at a time; three reasons a subagent helps, and what
  every added agent costs) and `mcp` (an MCP server exposes a system's tools to any MCP client; the app running
  the agent, not MCP, decides whether a call that changes data asks first; only connect servers you trust). The course now has 48 of 52 lessons.
- Two more lessons by Claude in vi, en and ja (status `review`): `tests-and-ci-for-agents` (tests the
  agent runs itself, CI that runs the tests it is set up to run, at the moments it is set up for, and never changing an expected answer
  just to turn a test green) and `memory-and-skills` (what the agent remembers between sessions versus
  procedures it loads when needed; a repeated procedure packaged as a skill). The course now has 46 of
  52 lessons.
- Two more lessons by Claude in vi, en and ja (status `review`): `prompt-engineering-for-agents` (three
  layers of instructions; five ways to write instructions an agent can follow; test an instruction in a
  new session) and `hooks-and-permissions` (advice versus locks — permission rules and hooks are enforced
  by the tool). `context-engineering` now takes 20 minutes. The course now has 44 of 52 lessons.
- Two more lessons by Claude in vi, en and ja (status `review`): `model-plus-harness` (agent = model +
  harness — tools, context and instructions, guardrails, checks; diagnose a weak agent by symptom and fix
  the harness first) and `context-engineering` (three drawers — always, when needed, never; a five-line
  instruction file tested in a new session). The course now has 42 of 52 lessons.
- Two more lessons by Claude in vi, en and ja (status `review`): `tool-landscape` (four shapes of AI
  tool — web chat, editor assistant, local agent, cloud agent — chosen by four questions about your
  environment, not by rankings) and `workflow-frameworks` (add a plan, tests first or a separate review
  only when the task's risk calls for it). The course now has 40 of 52 lessons.
- Two more lessons by Claude in vi, en and ja (status `review`): `vibe-vs-agentic` (vibe coding keeps
  whatever seems to work; agentic coding adds a goal, boundaries, a check and a review — and the
  question "if it is wrong and nobody notices, who gets hurt?" decides which one a task needs) and
  `the-agent-loop` (Mai's report fix traced turn by turn: read the context, pick a tool, the tool runs,
  the result comes back; when a loop ends, when it only pauses for a decision, and when to interrupt). The course now has 38 of
  52 lessons.
- Two more lessons by Claude in vi, en and ja (status `review`): `choosing-models` (small,
  mid-size and large models trade capability, speed and cost; try effort before switching; an
  exercise that compares two setups — two models or two effort levels — on the learner's own task
  against a criterion written first, plus two made-up tasks with known answers) and
  `traditional-vs-agentic` (the agent runs the write–run–fix loop, you give it a goal and a check and
  review the evidence). The course now has 36 of 52 lessons.
- Two more lessons by Claude in vi, en and ja (status `review`): `tokens` (one sentence in three
  languages cut into tokens; every count made with the open-source tiktoken tokenizer and dated) and
  `reasoning-models` (thinking first helps multi-step work, costs time and tokens, and the visible
  reasoning is no guarantee). New glossary term `reasoning-model`. The course now has 34 of 52 lessons.
- Thirteen more lessons in vi, en and ja (status `review`): `how-to-learn-this-course`,
  `programming-building-blocks`, `command-line-basics`, `ai-ml-dl`, `how-machines-learn`,
  `rag-intro` and `prompt-rag-finetune-compare` by Claude; `security-basics`, `prompting-basics`,
  `next-token-prediction`, `tool-calling`, `what-is-software` and `project-anatomy` by Codex. From
  now on Claude writes each batch and Codex reviews its pull request (ADR 010).
- `validate` checks each finished lesson's quiz: three questions with options A–C and an answer key,
  the same key in every language (`quiz_key_differs`), and a warning when all three answers are one
  letter; and it reports a lesson pointed at by its number or position (`lesson_by_position`: *lesson
  3*, *ở bài trước*, *次のレッスン*), outside code blocks.

## v0.5.0 — 2026-09-27

- **The minimum path is written:** all 19 lessons in vi, en and ja (status `review`), each with an
  explanatory infographic and a recap — from watching an agent build a page and choosing a safe setup,
  through specs, the explore → plan → build → verify workflow, paths, diffs, checks and debugging, to
  two projects (a personal web page; an automated monthly sales report whose right answers are given
  in advance). Tool facts are dated September 2026 and cite Anthropic's documentation.
- `validate` reports `diagram_word_split` when a word is wider than its box and the drawing has to cut
  it in two (Latin and katakana words; kanji may break anywhere), with messages in vi, en and ja.

## v0.4.0 — 2026-09-27

- **`python -m src.main export`**: the course as self-contained HTML files to share without GitHub
  (ADR 009) — one file with every language opening on a language chooser, and one per language;
  infographics embedded, no script, pages switched by the URL fragment, and printing a one-language
  file to PDF gives the whole course with the quiz answers. Only `review` and `done` lessons are
  exported; `review` ones carry a draft badge.
- `requirements.txt` declares the course tools' dependencies: PyYAML and, for the export only,
  markdown-it-py.
- The owner decided that the whole course is written now, in all three languages, without a native
  Japanese review (ADR 007); the content guide gains the conventions every lesson shares.

## v0.3.1 — 2026-09-26

- Codex brainstorm round 2 ([brainstorm/round-2.md](brainstorm/round-2.md)), all five findings
  applied: `files-folders-paths` moves ahead of `reviewing-agent-changes`; `data-formats` joins the
  minimum path (now 19 lessons, 347 min); `agent-parts-and-loop` no longer says an LLM "only writes
  text" or "chooses the tool" — it produces output, possibly a tool request, that the agent's software
  allows and carries out; the agent column of `ai-three-levels` checks its work "when its tools
  allow"; the English and Japanese birthday example uses a local name.

## v0.3.0 — 2026-09-26

- **Roadmap v1** from Codex brainstorm round 1 and the owner's decisions (ADR 007): 6 modules,
  17 units, 52 lessons, 893 min; hands-on from the first sitting; `optional` and `advanced` units;
  a **minimum path** of 18 lessons (337 min) listed first on every course home, ⭐ on its lessons and
  counted per module on the roadmap; 9 v0 lessons merged or cut, recorded as `retired` so their ids
  are never reused. Tagline and audience now promise "enough to supervise AI that writes code".
- **Every lesson ends with a recap infographic** (ADR 008): a new `recap` section, required for every
  lesson type, showing from `review` on exactly one diagram of its own; a new `summary` template draws
  3–6 numbered key points.
- The pilot lesson is split: `chatbot-to-agent` (who does the steps?) and the new
  `agent-parts-and-loop` (brain, tools and the loop), each with two diagrams and a recap, in vi/en/ja.
- `validate` checks `track`, `minimum_path` (known core lessons, once each, in course order) and
  `retired`; `stats` reports the minimum path.
- Fixed: `validate` crashed instead of printing a finding about a section (missing, empty, out of
  order…) because the message's `{key}` placeholder collided with the translator's own argument; a
  test now renders every finding in every language.
- A test checks that no line of text runs out of its box in any diagram.

## v0.2.0 — 2026-09-26

- One folder per language: `course/vi/`, `course/en/`, `course/ja/` hold everything a learner reads,
  each file in one language only and opening with a 🌐 language bar; shared sources move to
  `course/data/`; `course/README.md` chooses the language. The mixed-language `course/OUTLINE.md`
  is gone, replaced by a generated course home per language.
- Infographics: specs in `course/data/diagrams/` rendered to SVG per language (templates compare,
  equation, cycle, flow) and a generated roadmap; the pilot lesson now explains with four of them.
- `python -m src.main build [--check]` replaces `outline`; the validator also checks the language
  bar, diagram references and parity, relative links and images, and stale or orphan generated files.
- Infographic layout: nothing is drawn over anything else. Flow labels are measured before they
  are placed; a cycle's ring grows until its cards clear each other and the centre, and each arrow
  label moves to the nearest free spot. A diagram whose text no layout can fit fails `validate` with
  `diagram_crowded`. Checked on stress specs for every template in every language.
- `scripts/mutation_check.py` (from the template) drops the target's cached bytecode after each
  write: a mutation that kept the file size, written in the same second as the baseline run, was
  never executed and was reported as SURVIVED.
- ADRs 005 and 006; content guide chapter on infographics.

## v0.1.0 — 2026-09-26

- Repository seeded from `claude-agent-routing-template` (Claude Code harness, Codex protocol).
- Content store `course/`: course metadata, roadmap v0 (7 modules, 17 units, 57 lessons, 944 min),
  a 43-term Vietnamese/English/Japanese glossary, and the 11-section lesson structure.
- Pilot lesson `chatbot-to-agent` in Vietnamese, English and Japanese (status `review`).
- `python -m src.main` with `validate`, `stats`, `outline`, `scaffold` and `fb-draft`, messages in
  vi/en/ja; tests, mutation manifests and a CI step.
- Docs: content guide, data model, Facebook plan, ADRs 001–004, and the Codex brainstorm brief.
