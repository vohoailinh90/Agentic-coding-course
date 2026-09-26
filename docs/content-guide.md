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
  [`course/data/glossary.yaml`](../course/data/glossary.yaml).
- **Show before you tell.** Wherever a lesson compares options, adds parts up, repeats a loop or
  walks through steps, draw it as an infographic (below) and let the prose explain the picture.

## The sections

Every lesson is built from the sections in [`course/data/sections.yaml`](../course/data/sections.yaml),
in that order. `required` depends on the lesson type in `curriculum.yaml`.

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
| `recap` | The whole lesson in one infographic of its own (see *Infographics*) | every type |
| `takeaways` | 3–5 short bullets that say the recap's points in words — reused in Facebook posts | every type |
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

Each language has its own folder — `course/vi/`, `course/en/`, `course/ja/` — and every file in it
is in that language only. A lesson is `course/<lang>/lessons/<lesson-id>.md`, and starts with the
language bar that links the same lesson in the other languages (`scaffold` writes it; keep it as
it is).

- **Vietnamese is the source language.** Write `course/vi/lessons/<id>.md` first; it decides the
  structure and the points each section makes.
- The English and Japanese files keep every section, every point and every diagram, but localize
  what a reader in that language would find foreign: names, money, places, workplace habits, idioms. The pilot lesson
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

## Conventions every lesson shares

Fifty lessons written in three languages stay one course only if they share a small world.

- **The cast** comes from [brainstorm/BRIEF.md](../brainstorm/BRIEF.md): **Mai** (an accountant in
  Ho Chi Minh City who lives in Excel), **Tuấn** (a mechanical engineer in Japan on a locked-down
  company laptop), **Hana** (an office worker in Tokyo, new to AI) and **Huy** (a second-year student
  who knows a little Python). Pick one main character per lesson. They keep their names in every
  language (ja: マイ, トゥアン, ハナ, フイ); one-off examples are localized as usual.
- **The practice folder** `ai-practice` is where every exercise happens. Start from a known-good copy,
  and remember that a folder is a boundary for you, not a sandbox for the agent.
- **Three kinds of action**, taught in `data-safety-and-permissions` and reused everywhere:
  ✅ safe (made-up data, files inside `ai-practice`), ✋ ask first (installing, deleting, sending,
  anything outside the folder), ⛔ never (real company or customer data, passwords and API keys,
  getting around a company computer's rules).
- **Evidence** closes every hands-on exercise and project, in three lines: *I can show… / I checked…
  / I would not use this when…* (vi: *Tôi cho xem được… / Tôi đã kiểm tra… / Tôi sẽ không dùng cách
  này khi…*; ja: *見せられるもの… / 確かめたこと… / 使わないほうがいい場面…*).
- **Running artifacts** carry over: the one-file weekly task card from `first-agent-session`, the
  personal page from `project-personal-page`, and Mai's monthly sales report from
  `project-office-automation`.
- **Tools** are named only as dated examples ("as of September 2026"), never with prices.
- **Pictures:** usually one explanatory infographic plus the recap.
- **Length:** 5–10 minutes of reading; short paragraphs and bullets, one idea per lesson.

## Infographics

A good diagram lets a beginner understand the idea before reading a word of the lesson. Each one is
a spec in `course/data/diagrams/<id>.yaml` with its text in all three languages; `python -m src.main
build` draws it into every language folder ([data-model.md](data-model.md) has every key).

| Template | Use it when the lesson… | Example |
|---|---|---|
| `compare` | contrasts 2–4 options | chatbot vs copilot vs agent; Google Maps vs taxi |
| `equation` | builds a whole from parts | LLM + tools + loop = agent |
| `cycle` | describes something that repeats | think → act → observe |
| `flow` | walks through steps in order | explore → plan → build → verify |
| `summary` | sums up a whole lesson (the recap) | 3–6 numbered key points of the lesson |

- **Draw the difference, not the names.** A comparison shares its rows across columns, so the eye
  lands on what changes; `emphasis_row` marks the row the lesson turns on, `highlight` the option it
  recommends.
- **Labels, not sentences:** 2–6 words per value, a short caption at most. Explanations belong in
  the lesson text around the picture; the `takeaway` is the one sentence worth remembering.
- **Label the arrows** in `cycle` and `flow` (`arrow:`): "picks a tool" says what moves along it.
- **One emoji per card** as its icon, one colour per idea. Keep the colour of an idea the same
  across the lessons (tools are amber, the agent is green).
- Embed it where it helps, with alt text in the lesson's language — usually the diagram's title:

  ```markdown
  ![Chatbot như Google Maps, agent như tài xế taxi](../diagrams/maps-vs-taxi.svg)
  ```

- Every translation shows the same diagrams in the same sections (`validate` checks it).
- **Every lesson ends with a recap** ([ADR 008](decisions/008-a-recap-infographic-in-every-lesson.md)):
  the `recap` section, just before the takeaways, shows one infographic that sums up the whole
  lesson — usually a `summary` of 3–6 key points, named `<lesson-id>-recap.yaml`. It must be its own
  picture, not a diagram the lesson already showed; the takeaways then say the same points in words.
  The recap is also the image posted with the lesson on Facebook.
- Look at the result in all three languages before committing: open the SVG in a browser. Boxes
  grow to fit wrapped text; if a label wraps into three lines, shorten it.
- Nothing is ever drawn over something else: a cycle's ring grows and its labels move to free
  space. When a language's text is too long for any layout that fits the width, `validate` fails with
  `diagram_crowded` — shorten the captions or arrow labels, or use fewer steps.

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
python -m src.main scaffold <lesson-id>      # 1. create the file in course/vi, course/en, course/ja
# 2. write course/vi/lessons/<id>.md, add its diagrams and its recap to course/data/diagrams/, then localize
python -m src.main build                     # 3. draw the diagrams, refresh the course homes
python -m src.main validate --lang vi        # 4. fix every error
python -m src.main fb-draft <lesson-id>      # 5. once done: draft the post
```

Write lessons in the order of the minimum path (the course home lists it first). For the minimum-path
pilot, the Japanese text waits until the Vietnamese lessons have been tried with learners; the `ja`
files stay `todo` until then ([ADR 007](decisions/007-roadmap-v1.md)).
