# Changelog

## v0.2.0 — 2026-09-26

- One folder per language: `course/vi/`, `course/en/`, `course/ja/` hold everything a learner reads,
  each file in one language only and opening with a 🌐 language bar; shared sources move to
  `course/data/`; `course/README.md` chooses the language. The mixed-language `course/OUTLINE.md`
  is gone, replaced by a generated course home per language.
- Infographics: specs in `course/data/diagrams/` rendered to SVG per language (templates compare,
  equation, cycle, flow) and a generated roadmap; the pilot lesson now explains with four of them.
- `python -m src.main build [--check]` replaces `outline`; the validator also checks the language
  bar, diagram references and parity, relative links and images, and stale or orphan generated files.
- ADRs 005 and 006; content guide chapter on infographics.

## v0.1.0 — 2026-09-26

- Repository seeded from `claude-agent-routing-template` (Claude Code harness, Codex protocol).
- Content store `course/`: course metadata, roadmap v0 (7 modules, 17 units, 57 lessons, 944 min),
  a 43-term Vietnamese/English/Japanese glossary, and the 11-section lesson structure.
- Pilot lesson `chatbot-to-agent` in Vietnamese, English and Japanese (status `review`).
- `python -m src.main` with `validate`, `stats`, `outline`, `scaffold` and `fb-draft`, messages in
  vi/en/ja; tests, mutation manifests and a CI step.
- Docs: content guide, data model, Facebook plan, ADRs 001–004, and the Codex brainstorm brief.
