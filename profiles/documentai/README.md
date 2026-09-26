# DocumentAI execution profile

A routing overlay, a development process and a one-role roster addition for
`vohoailinh90/DocumentAIEditor`, derived from this repository's T0–T3 model.

```
profiles/documentai/
├── README.md                        this file — what was added, and what was not
├── PROCESS.md                       the development process
├── routing/documentai-overlay.yaml  domain signals, mapping, 2 overrides, change classes
├── agents/document-fidelity-reviewer.md      the one new role
├── skills/classify-requirement/SKILL.md      overlay-aware classifier (REPLACES the base one)
└── CLAUDE.md.template               drop-in CLAUDE.md for DocumentAIEditor
```

## Install into DocumentAIEditor

Run this from **the root of this repository**, with the target checked out
beside it. Every source path is qualified from that root and every directory
is created under the destination, so the block runs as written from one
stated directory — copy-pasting it from `profiles/documentai/` instead would
create directories in the wrong repository and resolve the target under
`profiles/`.

```bash
TARGET=../DocumentAIEditor   # adjust if your checkout lives elsewhere

mkdir -p "$TARGET"/.claude/agents "$TARGET"/.claude/skills \
         "$TARGET"/agent-routing "$TARGET"/docs

# the profile
cp    profiles/documentai/CLAUDE.md.template               "$TARGET"/CLAUDE.md
cp    profiles/documentai/routing/documentai-overlay.yaml  "$TARGET"/agent-routing/
cp    profiles/documentai/PROCESS.md                       "$TARGET"/docs/
cp    profiles/documentai/agents/document-fidelity-reviewer.md \
                                                           "$TARGET"/.claude/agents/
cp -r profiles/documentai/skills/classify-requirement      "$TARGET"/.claude/skills/

# the base layer the overlay inherits
cp agent-routing/policy.yaml agent-routing/complexity-rubric.md "$TARGET"/agent-routing/
for role in architect architecture-critic requirement-analyst implementer \
            code-reviewer code-reviewer-t3 test-engineer; do
  cp ".claude/agents/$role.md" "$TARGET"/.claude/agents/
done
```

The overlay is meaningless without that base layer; it declares
`inherits: base` for every section it does not redefine. Note that the role
loop copies exactly seven agents by name rather than `.claude/agents/*.md` —
copying the directory wholesale would be harmless today but would silently
pull in any future agent this repository adds for its own use.

⚠️ **Do not copy the base `classify-requirement` skill.** It reads only
`policy.yaml` and the base signal taxonomy — it never opens the overlay, never
applies `signal_mapping`, never enforces a change-class floor and never
substitutes the reviewer. Installing it would leave the whole profile inert:
`/classify-requirement` would answer document-write work with a base-only T1
and the generic reviewer, exactly as if this bundle did not exist. The
overlay-aware version in `skills/` takes its place under the same name, so
`/classify-requirement` resolves to it.

## Roster decision record

The team is **the seven inherited base roles plus one**. That is the
deliverable, and the restraint is the point: this repository exists to
select the smallest effective profile, so a proposal that answers "design a
team" with eight new agents would be arguing against its own thesis.

### Added: `document-fidelity-reviewer` (1 role)

DocumentAIEditor's output is a customer deliverable, and its worst failure is
silent. `_set_paragraph_text` collapsing a multi-run paragraph, a `%...%`
footer field flattened to literal text, a correction landing in the wrong
paragraph because `_text_sim` compares character *sets* — none of these raise
an exception, fail a text-equality test, or look wrong in a diff to a
reviewer who does not know `python-pptx`. That is judgement a generic
reviewer cannot supply and a script cannot fully replace.

It **substitutes for** the tier's generic reviewer rather than joining it.
One reviewer slot, one occupant. The base policy already establishes this
pattern — T3 fills the same slot with `code-reviewer-t3`. Budget unchanged.

### Considered and rejected

Each of these looked like a role and turned out to be a script, an existing
role, or nothing.

| Candidate | Why not |
|---|---|
| `bmf-integration-verifier` | The endpoint matrix is a table. URL family, auth header, body shape and response field per deployment are all computable from `BMF_MODELS` — that is `check_endpoint_matrix`, not an agent. |
| `prompt-parser-contract-reviewer` | Parser correctness is golden-fixture testable against recorded model outputs (`check_parser_fixtures`). What is left — "will the model still obey the edited prompt" — needs live calls, so it is an eval, not a review. Neither half is a standing role. |
| `packaging-engineer` | "Is every import in the spec, is every runtime path resolvable when frozen" is a script (`check_packaging_manifest`). The remaining work is a manual smoke test on Windows, which is a release step. |
| `japanese-language-reviewer` | The style rules in `SpellCheckEngine.check_ja` are regexes. Extending them is `checker-logic` work, table-tested. Genuine linguistic review is the human customer's job, not an agent's. |
| `security-auditor` | The base overrides already route credential storage, TLS verification and the Prompt-Update allow-list to T2, where the reviewer's remit explicitly covers security. A separate auditor would duplicate a reviewer that is already required. |
| `ui-reviewer` | Tkinter, with an established in-repo style system. `.claude/skills/ui-kit/SKILL.md`'s existing-UI-system exception applies; there is nothing to route. |
| `document-corpus-engineer` | This is `test-engineer`, and `budget.escalation_reserve` already funds exactly this escalation when the reviewer reports that verification needs designing. |
| a dedicated `implementer` at T1 | The base policy already rejects this: the main session holds the requirement and the code, and handing it off buys a second context that must rebuild both. |

Half of the rejected candidates resolved to a committed check rather than a
role, and the security auditor partly did too. That ratio is the expected one
for this codebase — footer rules, letter-number formats, endpoint shapes,
import manifests, allow-list decisions and formatting preservation all have
computable answers, and the policy is explicit that computable answers get
scripts.

The overlay's own consistency test (`tests/test_documentai_overlay.py`)
applies the same rule to this bundle: it caught two T2 change classes with no
deterministic guard while this profile was being written, which is why
`check_access_control_matrix` and `check_transport_fallback_ladder` exist.

It also resolves every file and function name in `change_classes` against a
DocumentAIEditor checkout — a profile that misdescribes the code it routes is
worse than no profile, and the error is otherwise invisible until someone
tries to use the table. Point it at a checkout with `DOCUMENTAI_REPO=...`, or
put one beside this repository as `../documentaieditor`; without one those
three assertions skip rather than pretending to pass.

## What the overlay changes, and what it does not

**Does not touch:** the tier model, the score ranges, the six rubric
dimensions, the profiles, `max_agent_invocations`, either reserve, or the
parallelism rules. All inherited unchanged.

**Adds:**

- 12 domain signals in this codebase's verb-first vocabulary, plus 5
  read-only exemptions.
- A `signal_mapping` table routing 7 of those onto existing base signals, so
  base overrides fire without the base policy being edited. Preferred over
  new overrides — it reuses overrides that are already tested.
- 2 overrides the base vocabulary cannot express: `document-write-path` (the
  deliverable-corruption surface) and `ai-output-contract` (a contract whose
  other party is a model).
- 13 change classes mapping file paths to tier floors — a lookup that reaches
  the same answer as full rubric scoring for the cases this repo sees weekly.
- 3 discrimination rules for the recurring false positives: composing a mail
  vs. sending one, calling BMF vs. storing its key, reading a document vs.
  writing one.
- 8 required deterministic checks, specified with their exact assertions in
  `PROCESS.md` §2.
- An overlay-aware `classify-requirement` skill that replaces the base one.
  Note what this is *not*: it is a skill, not a role. The gap it closes —
  the installed classifier ignoring the overlay — was a routing bug, and the
  fix is the same shape as every other fix here: put the knowledge where the
  process already looks, rather than adding someone to consult.

## Where to start

`PROCESS.md` §6 lists six ordered tasks, all T0/T1. They exist because the
repository currently has one commit, no tests, no CI and no `.gitignore` —
which means today a mistake in the write path is invisible until a customer
finds it. After those six, it is visible in CI.
