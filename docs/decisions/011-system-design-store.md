# 011 — A Vietnamese-only System Design 101 store beside the course

**Date:** 2026-10-12 · **Status:** accepted by the owner

## Context

The owner wants a second, Vietnamese-only programme: System Design learned from diagrams, following
the 15 groups and 404 entries of the public ByteByteGo `system-design-101` list. The existing course
schema in `course/` requires every localized field in vi, en and ja, so the new programme cannot live
there without bending it. The source is licensed CC BY-NC-ND 4.0 and this repository is public.

## Decision

- The programme lives in its own store, `system-design-101/vi/`, outside `course/`. The Agentic
  Coding course, its generator and `validate` are untouched.
- [`brainstorm/system-design-101-vi/DECISIONS.md`](../../brainstorm/system-design-101-vi/DECISIONS.md)
  is the canonical record of the detail (order, density, lesson schema, mobile thresholds, evidence
  limits). This record only fixes the points that cross the repository:
  - Every one of the 404 entries keeps its place and order; entries that share a source stay separate.
  - Each lesson's progress lives only in its own `lesson.yaml`: `content_status`, independent
    verification fields and `learner_test`. `approved` needs all of them `done`.
  - **Licence:** lessons are written independently, in own words, with new diagrams; no close
    translation and no source images. The owner deferred resolving the right to use the source until
    publication. Whether following the source's topics and order counts as an adaptation is an open
    legal question, not a permission.
- Each lesson goes in its own pull request. Claude requests the Codex review, fixes the confirmed
  findings and re-requests a review after each push until Codex reports none. The owner told Claude
  on 2026-10-12 to merge then (as for PR #21), even though `main` has no branch protection; Claude
  checks CI, the head SHA Codex reviewed and the base SHA first, and merges pinned to that head SHA.

## Consequences

- No generator and no `validate` for the new store yet; a small checker comes after the first lessons
  show the schema is stable.
- Claims in the lessons are checked against the RFC and HTML specifications only where those can be
  reached; where they cannot, `claims` stays `pending` and the lesson says so.
- The licence question can still stop publication; drafts must not be posted to Facebook or a website
  before it is resolved.
