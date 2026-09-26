# 002 — Content as code: Markdown and YAML in Git, validated by CI

**Date:** 2026-09-26 · **Status:** accepted

## Decision

Lessons are Markdown files and the course structure is YAML, all in this repository. A validator
(`python -m src.main validate`) runs in CI and rejects any change that breaks the structure.

## Why

- People and AI agents (Claude, Codex) can both read and edit plain files with ordinary tools.
- Git gives history, review through pull requests, and a free backup.
- One source feeds every channel: Facebook posts now, the website later.
- Structure checks are computable, so a script does them rather than a reviewer's eyes
  (CLAUDE.md, "Deterministic work is not agent work").

## Alternatives considered

- **A CMS or Notion.** Friendlier editor, but no validation, harder for agents to edit, and the
  content would be locked into a service.
- **A database.** Overkill for about sixty lessons, and much harder to review.

## Consequences

Authors need a text editor (VS Code, or GitHub's web editor) and must keep the file format. The
validator's messages are in Vietnamese, English or Japanese to make that easier.
