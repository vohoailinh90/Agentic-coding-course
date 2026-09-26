# 003 — Stable slug ids; order comes from position

**Date:** 2026-09-26 · **Status:** accepted

## Decision

Modules, units and lessons are identified by kebab-case slugs (`chatbot-to-agent`), unique across
the whole tree. Their order and display numbers (`1.1.1`) come only from their position in
`course/data/curriculum.yaml`.

## Why

The roadmap is a draft that the Codex brainstorm is expected to reshuffle. With positional ids
(`m1-u2-l3`), every reorder would rename lesson folders and break links from published posts and
learners' saved progress. With slugs, a lesson can move anywhere and keep its id, its files and
every reference to it.

## Consequences

- Content never refers to a lesson by number ("see Module 6"); it uses the lesson's name.
- An id is never reused for a different lesson, even after the original is deleted.
