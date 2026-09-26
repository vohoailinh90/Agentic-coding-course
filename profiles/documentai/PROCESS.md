# DocumentAIEditor — Development Process

Companion to `routing/documentai-overlay.yaml`. The tier model, budgets and
profiles are the base policy's (`agent-routing/policy.yaml`) and are used
unchanged. This document says how a change moves through them *in this
codebase*.

## 0. What we are working on

`vohoailinh90/DocumentAIEditor` — a Windows desktop tool (Python 3.10+,
Tkinter, shipped as a PyInstaller EXE) that reviews PPTX/DOCX/XLSX/PDF
deliverables: it extracts content, sends it to a Bosch Model Farm LLM
deployment, parses the model's correction blocks, and writes the corrections
back into the document. ~6,700 lines across six modules.

| Module | Lines | Role | Risk character |
|---|---:|---|---|
| `ppt_editor.py` | 3,636 | Tkinter GUI + all orchestration | Monolith; one `App` class holds UI, prompt versioning, access control and Outlook COM |
| `bmf_client.py` | 1,071 | LLM gateway client, 6 endpoint families | Corporate proxy/TLS fallback ladder; API key on disk |
| `file_handlers.py` | 913 | PPT/Word/Excel/PDF read+write | **The customer-deliverable write path** |
| `ai_parser.py` | 282 | Parses model output into a change list | Regex over non-deterministic input; weak match scoring |
| `customer_db.py` | 276 | Customer xlsx + Prompt-Update allow-list | Client-side authorisation |
| `footer_checker.py` | 147 | Footer/date/letter-number validation | Pure, fully table-testable |

Baseline as found: one commit (`Add files via upload`), no tests, no CI, no
`.gitignore`, no branches. Everything below assumes that is fixed first —
see §6.

## 1. The loop

```
intake → classify → execute → verify → gate → release
```

### 1.1 Intake

State the change as an action, in one sentence, before scoring anything:
*"this change rewrites the footer date on every slide"*, not *"this change is
about footers"*. The whole routing model depends on that phrasing — signals
are verbs, and a noun-shaped requirement produces noun-shaped signals, which
produce false overrides.

### 1.2 Classify

Two paths, and they must agree:

- **Fast path.** Look the change up in `change_classes` in the overlay. That
  gives a tier floor in one step for the cases this repo sees weekly.
- **Full path.** Run `/classify-requirement`, score the six rubric
  dimensions, extract domain signals, drop the read-only ones, apply
  `signal_mapping`, then apply base overrides and overlay overrides.

Scoring may raise the tier above the class floor. It may never lower it. If
the two paths disagree in the other direction, the fast path is wrong and the
class table needs a new entry — fix the table in the same PR.

Before you attach a signal, run it past `discrimination_rules`. The three
recurring false positives in this codebase are:

- editing the mail body vs. changing who receives it (T1 vs T3),
- calling BMF with a loaded key vs. changing how the key is stored (exempt vs T2),
- reading a document vs. writing one (exempt vs T2).

### 1.3 Execute

Per the base profile for the final tier. Main session analyses, designs and
implements; subagents supply only what the main session structurally cannot
supply for itself. Roster per tier, with the DocumentAI substitution applied:

| Tier | Main session | Subagents | Budget |
|---|---|---|---|
| T0 | everything | none | 0 |
| T1 | analysis + implementation | `code-reviewer` | 1 |
| T2 | analysis + design + implementation | `code-reviewer` *or* `document-fidelity-reviewer`; `architect` only if architecture scored 2 or a `when_any_signal` entry fires | 2 (+1 escalation reserve) |
| T3 | analysis + design + implementation | `architecture-critic`, `code-reviewer-t3` *or* `document-fidelity-reviewer`; `requirement-analyst` if ambiguity is 2 | 3 (+1 analyst, +1 escalation) |

`document-fidelity-reviewer` **replaces** the tier's generic reviewer on
document-write changes. It is never invoked alongside it. One reviewer slot,
one occupant, budget unchanged.

### 1.4 Verify

Tier minimum from the base policy, plus these repository-specific gates:

| Tier | Required evidence |
|---|---|
| T0 | Launch the app, exercise the changed widget, `python -m py_compile` on touched files |
| T1 | The deterministic checks guarding the touched class, plus independent diff review |
| T2 | The above, plus the round-trip corpus on any document-write change, plus independent review **and** verification by the reviewer |
| T3 | The above, plus an end-to-end run on a real deck, an explicit rollback statement, and — for `outlook-send` — a dry-run that produces a draft and sends nothing |

**Never** report a check as passing that you did not execute. Never mark a
document-write change verified on the strength of "the text came out right":
the failure mode is formatting, not text.

### 1.5 Gate

Confirm with the user *before* acting, every time, for anything in
`human_gates`: a change that sends Outlook mail, overwrites a source file,
deletes a user document, alters credential storage, or ships a rebuilt EXE.

These gate the **change**, not the running tool. The product invariants —
never write to `input/`, never overwrite the user's source file, never delete
a user document — hold unconditionally; a gate exists for the case where
someone deliberately proposes a code path that would breach one, and clearing
it for that change never relaxes the invariant anywhere else.

### 1.6 Release

1. Bump the version string in the module headers and `README_startup.txt`.
2. Run every deterministic check offline.
3. `build_exe.bat`, then launch the built EXE — not the script — and confirm
   `_base_dir()` / `_find_src()` resolve `src/`, `prompts/`, `input/`,
   `output/` correctly when frozen. This is the most common way a change that
   works for the developer is broken for every user.
4. Record what changed in a CHANGELOG entry.

## 2. Deterministic work is not agent work

Every one of these has a computable answer, so every one of them belongs in
the repository as a script, not in the roster as a role. A model comparing two
formatting attributes can be wrong; a script cannot.

Not all of them are written yet, and that distinction is enforced rather than
narrated: each entry in the overlay's `required_checks` carries
`status: implemented | planned`, and `check_required_checks_exist` asserts the
declaration against the `checks/` directory in both directions. Without it the
list read as a set of active gates while half of it was a plan —
`unittest discover` runs the files it finds and says nothing about the ones it
does not, so CI stayed green over four checks that did not exist.

| Check | Guards | Asserts |
|---|---|---|
| `check_endpoint_matrix` | `bmf-endpoints` | For every deployment in `BMF_MODELS`: `_build_url` produces the URL family its `endpoint` declares, `_build_headers` uses the right auth header (`Authorization: Bearer` vs `genaiplatform-farm-subscription-key`), `_build_body` produces the declared body shape, and `_parse_response` reads the matching field. Pure functions, no network. |
| `check_parser_fixtures` | `ai-contract` | Over a corpus of recorded model outputs in `fixtures/ai_output/`: `AIContentParser.parse` returns exactly the expected change records. Two groups, both required. **Syntax**: full-width `∣`, missing `[`, duplicated STEP 2 sections, Copilot commentary after 修正後. **Targeting** — the group that guards §3 risks 5 and 6: fixtures where several candidate paragraphs on one slide share nearly the same character set but differ in word order (`_text_sim` is Jaccard over character *sets*, so it cannot tell them apart), asserting the intended paragraph is chosen or that the parser declines to match; plus a fixture whose 修正前 matches nothing, asserting that no actionable record with `shape_id: 0` reaches a handler. Zero model calls. |
| `check_document_roundtrip` | `document-write`, `new-format-handler` | Open a fixture document, apply a change set, save, reopen. Slide/paragraph counts unchanged; `%...%` placeholder fields still placeholders; for every **untouched** paragraph the run count and each run's bold/italic/size/colour/language are byte-identical. **And, on the edited paragraph itself:** the fixture must contain a paragraph of mixed formatting (e.g. bold lead-in + regular body + a differently-sized fragment), and after reopen its run boundaries and per-run attributes must still be there, with change permitted only inside the targeted text span. Asserting merely that the edited paragraph "keeps its first run's formatting" is the one thing this check must **not** do — collapsing a mixed paragraph into a single run styled like run 0 is exactly what `_set_paragraph_text` does today (§3 risk 4), so that weaker assertion would certify the profile's central silent-corruption risk as safe. **This is the check that makes the write path safe to change.** |
| `check_checker_tables` | `checker-logic` | Table-driven cases over `footer_checker.analyze_all`, `LETTER_RE`, `check_letter_numbers`, `CustomerDB` prefix/separator extraction. One row per rule, including the negative rows. |
| `check_packaging_manifest` | `packaging` | Every third-party module imported anywhere in the source appears in `requirements.txt`; every module and data directory the app loads at runtime is covered by `DocumentAIEditor_v1.spec` (`hiddenimports` / `datas`); `_base_dir()` resolves under both `sys.frozen` and script mode. |
| `check_access_control_matrix` | `access-control` | Table-driven over `check_prompt_update_access`: missing sheet → deny; empty column → deny; exact match → allow; `ntid1x` against allowed `ntid1` → deny; `DOMAIN\\ntid1` → allow; `ntid1@bosch.com` → allow; unreadable username → deny. **Every negative row is the point** — this function must stay fail-closed, and a change that makes it permit on an empty list is a critical finding. |
| `check_transport_fallback_ladder` | `bmf-transport` | Every `verify=False` and `ssl._create_unverified_context` site in `bmf_client.py` matches a committed allowlist of known locations, so introducing a new one fails the check until the allowlist is deliberately updated; and the attempt ladder in `_call_like_pptx_reviewer` tries `verify=True` before any unverified attempt. A no-silent-weakening ratchet, not a correctness proof. |
| `check_no_secrets_committed` | always | No file matching the credential shape (`ntid:` / `api_key:`), no real `@bosch.com` address outside the anonymized workbook, and `input/`, `output/`, `dist/`, `build/`, `__pycache__/` are all git-ignored. The scan covers the blobs the branch introduces, not only the tip, since a key added and deleted before pushing is still retrievable; and a `SECRETS_SCAN_BASE` the checkout cannot resolve fails the check rather than falling back to a ref that equals `HEAD`, which would inspect nothing and pass. |
| `check_required_checks_exist` | always | Every `required_checks` entry states a `status`; every entry marked `implemented` has a `checks/<id>.py` that imports and defines at least one `TestCase`; every `checks/check_*.py` file is declared in the overlay; and no entry still marked `planned` already exists. Both directions matter: the first stops policy from advertising a gate that does not run, the second stops a gate from running outside the policy that is supposed to govern it. |

Write them as plain `unittest` files runnable with
`python -m unittest discover`, so they work on a machine with nothing
installed beyond `requirements.txt`. Wire them into CI on push.

## 3. Standing risks the process must keep visible

These are properties of the codebase as it stands. They are not bugs to fix
in passing — each is a scoped piece of work with a tier already assigned.

| # | Risk | Where | Class / tier |
|---|---|---|---|
| 1 | API key stored in plaintext at `input/User_info.txt`, next to the EXE | `bmf_client.BMFCredentials` | `credentials` / T2 |
| 2 | TLS verification disabled in several fallback paths (`verify=False`, `ssl._create_unverified_context`) | `bmf_client` transport ladder | `bmf-transport` / T2 |
| 3 | Prompt-Update authorisation is `getpass.getuser()` against a spreadsheet column — client-side, trivially bypassed. It is correctly **fail-closed**; keep it that way. | `customer_db.check_prompt_update_access` | `access-control` / T2 |
| 4 | `_replace_in_para` flattens multi-run formatting on every edit (`_set_paragraph_text` has the same flaw but is dead code — nothing calls it) | `file_handlers.PPTHandler` | `document-write` / T2 |
| 5 | `AIContentParser._text_sim` is Jaccard over *character sets* — order-insensitive and easily fooled on Japanese text; a wrong match writes a correction into the wrong paragraph | `ai_parser` | `ai-contract` / T2 |
| 6 | No-match branch emits a synthetic change with `shape_id: 0` that later code treats as real | `ai_parser.parse` | `ai-contract` / T2 |
| 9 | `WordHandler.apply_changes` replaces only inside a single run, so a correction spanning two runs is dropped — a lost correction, not lost formatting. No longer *silent*: the handler reports it through `skipped_changes` and the correction log marks it 未適用, so the drop is visible while the fix is still outstanding | `file_handlers.WordHandler` | `document-write` / T2 |
| 7 | `ppt_editor.App` is 3,636 lines and mixes UI, orchestration, authorisation and COM | `ppt_editor` | see §5 |
| 8 | No `.gitignore`; `input/User_info.txt` is one careless `git add` from being committed | repo root | §6, do first |

## 4. The UI question

`.claude/skills/ui-kit/SKILL.md` (shadcn/Radix/Tailwind, web) does **not**
apply here. DocumentAIEditor is Tkinter and already has its own established
style system — `ACCENT_BLUE`, `TEXT_MUTED`, `FONT_SMALL`, `_btn`, `_card`,
`_sep`, `_scrollable`. That is exactly the skill's own
"existing UI system" exception. Extend those helpers; do not fetch the kit,
and do not introduce a second visual vocabulary. Revisit only if the user
explicitly asks for a web front end.

## 5. Refactoring `ppt_editor.py`

The monolith is real, but "split the God class" is not a routable
requirement — it is an unbounded rewrite of the only module that has no test
coverage, and it would be a T3 with no verification story.

Do it incrementally, and only ever as a side effect of work that was already
going to touch the region:

1. Extract leaf-pure helpers first (`ts_name`, `fmt_icon`, `_extract_step1`,
   version-number computation). T0/T1, each with a table test.
2. Extract the prompt-versioning and Outlook subsystems into their own
   modules behind a narrow interface. T2, `outlook-send` gate applies.
3. Leave widget construction (`_build_*`) alone. It is long, it is boring, and
   it is not where the defects are.

Never open a PR whose only content is a refactor of this file.

## 6. Do these first

Ordered by dependency, and five of the six are T0/T1 — the cheapest risk
reduction available in the repository. Item 5 is the exception and is
labelled T2 below: do not batch it with the others, because it needs a
designed fixture corpus rather than a table of cases.

1. **`.gitignore`** — `input/`, `output/`, `dist/`, `build/`, `__pycache__/`,
   `*.pyc`, `User_info.txt`. (T0)
2. **`check_no_secrets_committed`** + CI on push. (T1)
3. **Branch discipline** — stop committing to `main` via "Add files via
   upload"; one branch per change, with the tier named in the PR body. (T0)
4. **`check_checker_tables`** — the highest coverage per line of test code in
   the repo, because `footer_checker` is pure. (T1)
5. **`check_document_roundtrip` + fixture documents** — the check that turns
   the whole `document-write` class from unverifiable into routine. (T2; this
   is where `test-engineer` and `budget.escalation_reserve` legitimately
   apply, because the harness genuinely needs designing.)
6. **`check_endpoint_matrix`** — the BMF matrix is documented in a docstring
   today; make the docstring executable. (T1)

Everything else in §3 is safe to schedule after these six, because after
these six a mistake is visible.
