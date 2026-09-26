# Changelog

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
