# Content guide — how to write a lesson

This guide is for anyone who writes or edits lessons: Linh, Claude, Codex or a future contributor.
The structure it describes is enforced by `python -m src.main validate` (see
[data-model.md](data-model.md)); everything else here is judgement, so it is written down.

## Who we write for

A complete beginner: an office worker, a student or an engineer from another field who has used a
chatbot but never written code, often reads on a phone, and has 2–3 hours a week. Many are
Vietnamese people living or working in Japan. Every sentence should pass one test: *would this
reader understand it on the first read, without searching anything?*

## One lesson, one idea

- 7–12 minutes of reading (projects are longer). Roughly 900–1,400 words of Vietnamese.
- One main idea per lesson. If you need a second idea, it is a second lesson.
- Concrete before abstract: story or situation → example → the general idea → the term.
- Every new term is explained the first time it appears, and belongs in
  [`course/glossary.yaml`](../course/glossary.yaml).

## The sections

Every lesson is built from the sections in [`course/sections.yaml`](../course/sections.yaml), in
that order. `required` depends on the lesson type in `curriculum.yaml`.

| Key | Purpose | Required for |
|---|---|---|
| `objective` | 2–3 things the learner can *do* afterwards | every type |
| `hook` | A story or question that makes the learner care | every type |
| `read-first` | 1–3 trustworthy videos or articles, language noted | optional |
| `concept` | The one main idea, concrete → abstract, `###` for sub-points | concept, demo, hands-on |
| `analogy` | An everyday comparison — and where it breaks down | concept |
| `example` | A real situation, step by step | concept, demo |
| `try-it` | A 5–20 minute exercise with a way to self-check | hands-on, project |
| `misconceptions` | 2–4 beginner misunderstandings, corrected | optional |
| `takeaways` | 3–5 short bullets — reused verbatim in Facebook posts | every type |
| `quiz` | 3 questions × 3 options, answers with reasons in `<details>` | concept, demo, hands-on |
| `sources` | Verified sources: organization, language, date if fast-moving | optional |

Each section starts with an invisible marker, then its heading. The heading text is yours to
localize; the marker is what keeps the three languages aligned:

```markdown
<!-- section: analogy -->
## Ví dụ đời thường
```

Delete optional sections the lesson does not need — in every language, since all non-`todo`
language files of a lesson must have the same sections in the same order.

## Three languages: localize, don't translate

- **Vietnamese is the source language.** Write `vi.md` first; it decides the structure and the
  points each section makes.
- `en.md` and `ja.md` keep every section and every point, but localize what a reader in that
  language would find foreign: names, money, places, workplace habits, idioms. The pilot lesson
  turns *12,4 triệu đồng* into *$1,240* and *12万4千円*, and its quiz option "translate a sentence
  into Japanese" becomes "into Vietnamese" in the Japanese file.
- Terms follow the glossary, word for word. If a better translation comes up, change the glossary
  first, then the lessons.

### Vietnamese

- Address the reader as **bạn**; friendly, never childish. Short sentences, one idea per paragraph.
- On first use: Vietnamese term with the English in brackets — *cửa sổ ngữ cảnh (context
  window)*. When practitioners really use the English word (*agent, prompt, token, commit*), keep
  it and explain it once.
- Decimal comma and Vietnamese units: *12,4 triệu đồng*, *15 phút*.
- Examples from Vietnamese daily life: xe ôm/taxi, Zalo, chợ, Tết, bảng lương Excel.

### English

- Plain English at about B1–B2 level; no idioms that do not survive translation.
- Headings follow `sections.yaml` (Title Case); body text uses sentence case.
- Neutral, global examples: dollars, airports, spreadsheets.

### Japanese

- です・ます調, short sentences, full-width punctuation 「」、。：（）.
- Katakana terms with the English in brackets on first use when it helps: *コンテキストウィンドウ
  （context window）*. Give hard kanji a `reading` in the glossary instead of writing furigana in
  the text.
- Examples from Japanese working life: 円, 稟議, 報連相, 定例会議, 日報.

## Accuracy

- Every link is opened and checked before it is committed. Name the organization, the language
  of the source, and the date when the content ages quickly: *Anthropic — Building Effective AI
  Agents (tiếng Anh, 12/2024)*.
- No invented statistics or quotes. If a number matters, cite it; if you cannot, leave it out.
- Tool-specific steps (menus, commands, prices, plan names) change monthly. Keep them in
  `try-it` or a clearly marked paragraph with *as of YYYY-MM*, never inside the core concept.
- Never refer to another lesson or module by its number ("see Module 6"): numbers change when
  the roadmap is reordered. Refer to it by name.

## Safety in lessons

- Never show a real API key, token or password — only placeholders like `sk-...`.
- Exercises that let an agent run commands say what the agent may touch, and remind learners
  not to paste company-confidential data into AI tools — a real concern in Japanese workplaces.
- Every lesson that shows an agent at work also shows someone checking the result.

## Quiz format

```markdown
**Câu 1.** Question?

- A) ...
- B) ...
- C) ...

<details>
<summary>Xem đáp án</summary>

1. **B** — one sentence on why.

</details>
```

Three questions, three options each, one correct answer. Wrong options should be tempting
misunderstandings, not jokes.

## Front matter and Facebook fields

```yaml
---
lesson: chatbot-to-agent   # must match the folder
lang: vi                   # must match the file name
status: review             # todo → draft → review → done
summary: >-                # 2–3 sentences; also the body of the Facebook post
  ...
social:
  hook: "..."              # the post's first line: ≤ 120 characters, curiosity or a surprise
  question: ...            # ends the post and invites comments; a real question to the reader
---
```

| Status | Meaning | Checked |
|---|---|---|
| `todo` | Skeleton from `scaffold` | structure only |
| `draft` | Being written | + required sections present |
| `review` | Complete, waiting for a human read | + no empty section, no `<!-- TODO`, summary set |
| `done` | Reviewed and publishable | + `social.hook` and `social.question` set |

Only `review` and `done` lessons can become posts; `fb-draft` warns on `review`.

## Workflow

```bash
python -m src.main scaffold <lesson-id>      # 1. create vi/en/ja skeletons
# 2. write vi.md, then localize en.md and ja.md
python -m src.main validate --lang vi        # 3. fix every error
python -m src.main fb-draft <lesson-id>      # 4. once done: draft the post
```
