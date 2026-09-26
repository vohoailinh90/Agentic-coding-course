# Brainstorm brief — the learning path (roadmap v0 → v1)

> **Tóm tắt (vi):** Tài liệu này là "đề bài" gửi Codex để brainstorm lộ trình học. Nó mô tả người học,
> các ràng buộc, lý do đằng sau lộ trình v0 do Claude soạn, những điểm yếu đã thấy, 10 câu hỏi cần
> trả lời và định dạng kết quả mong muốn. Kết quả từng vòng được ghi ở [README.md](README.md).

## 1. What this brainstorm must decide

The learning path that is **easiest to understand, most engaging and most effective** for people
who know nothing about AI — before about fifty more lessons are written in three languages. The
path is the order in which ideas and hands-on work appear, what is in the minimum path that ships
first, and what is optional.

Roadmap v0 is Claude's draft. It is meant to be challenged, not polished.

## 2. The learners

All four have used a chatbot at most, have never directed an AI agent, and discover content on
Facebook.

| Persona | Background | Wants | Risk |
|---|---|---|---|
| **Mai**, 32, accountant in Ho Chi Minh City | Excel every day, never wrote code | automate her monthly reports | quits if it feels like "IT school" |
| **Tuấn**, 28, mechanical engineer in Japan | CAD, reads Japanese at work, locked-down company Windows laptop | small tools for his team | cannot install much; confidential data |
| **Hana**, 24, office worker in Tokyo | non-engineer, curious about 生成AI, reads the Japanese version | understand what agents mean for her job | jargon; long texts |
| **Huy**, 20, second-year student | a little Python | keep up with the industry | bored by basics he half-knows |

Common constraints: 2–3 hours a week, often on a phone, mostly Windows, and many will not pay for
an AI subscription until they see value.

## 3. Constraints on the course

- **Format.** Self-paced lessons of 7–12 minutes (projects longer) that can each be cut into three
  Facebook posts a week ([docs/facebook-plan.md](../docs/facebook-plan.md)); a website later.
- **Three languages, never mixed.** One folder per language (`course/vi|en|ja/`), every learner page
  in one language with a 🌐 bar to switch; Vietnamese is the source, English and Japanese are
  localized with identical section structure ([docs/data-model.md](../docs/data-model.md)), and one
  trilingual glossary ([course/data/glossary.yaml](../course/data/glossary.yaml)).
- **Infographics first.** Lessons explain with colourful diagrams "you understand at a glance":
  generated SVGs from one spec per diagram, in four templates — compare, equation, cycle, flow
  ([docs/content-guide.md](../docs/content-guide.md#infographics)). The pilot lesson has four.
- **Lesson template.** Eleven sections in a fixed order ([course/data/sections.yaml](../course/data/sections.yaml));
  the pilot lesson shows the intended tone ([course/en/lessons/chatbot-to-agent.md](../course/en/lessons/chatbot-to-agent.md),
  also in [vi](../course/vi/lessons/chatbot-to-agent.md) and [ja](../course/ja/lessons/chatbot-to-agent.md)).
- **Production capacity.** One part-time author (Linh) with AI help. The roadmap must be
  producible, which is why a minimum path matters.
- **Tools change monthly; concepts do not.** Tool-specific steps must be easy to replace.

## 4. The principles behind v0 (challenge them)

1. **Play the whole game first** (Perkins, *Making Learning Whole*): the kick-off shows the whole
   journey — including an agent building software — before any theory.
2. **Just enough foundations, just in time:** software basics framed as "what you need to supervise
   an agent", not a computer-science course.
3. **Spiral:** context, tools and verification come back three times — intuition, mechanism,
   engineering.
4. **One lesson = one idea = one post series.**
5. **Concrete before abstract:** every concept lesson has an everyday analogy and a real example.
6. **Learn by doing:** hands-on lessons along the way, projects at the end.
7. **Verification mindset from lesson one:** whoever assigns the work checks the result.
8. **Three languages as a feature:** learners pick up English and Japanese technical vocabulary
   while they learn AI — valuable for Vietnamese people working with Japan.

## 5. Roadmap v0 at a glance

The full tree is on each language's course home — [English](../course/en/README.md),
[Vietnamese](../course/vi/README.md), [Japanese](../course/ja/README.md) — generated from
[course/data/curriculum.yaml](../course/data/curriculum.yaml).

| # | Module | Lessons | Minutes |
|---|---|---:|---:|
| 1 | Kick-off: Welcome to the World of AI Agents | 3 | 30 |
| 2 | Software Foundations — Just Enough to Lead an Agent | 10 | 114 |
| 3 | AI and Machine Learning Foundations | 8 | 84 |
| 4 | Agentic Coding: Building Software with AI Agents | 10 | 119 |
| 5 | LLM and Model Foundations | 7 | 70 |
| 6 | Harness Engineering | 15 | 167 |
| 7 | Real Projects | 4 | 360 |
| | **Total** | **57** | **944** |

The order follows the owner's own framing — software concepts → machine learning → agentic coding
→ LLMs → harness — with LLM internals deliberately *after* the first agentic-coding module, so that
learners use agents before they study how models work, and the LLM module then motivates harness
engineering (context window → context engineering, tool calling → MCP, hallucination →
verification).

### Weaknesses already visible in v0 — be harsher than this

- The first session with a real agent (`first-agent-session`, 4.3.2) is lesson **30 of 57**.
  Apart from the demo in 1.1.2, learners read 29 lessons before they direct an agent themselves.
- Modules 2 and 3 are 18 lessons of foundations before agentic coding starts: a dropout risk.
- Projects only appear at the very end; no module ends with a small build.
- Harness Engineering is the largest module (15 lessons) and may be too deep for this audience —
  perhaps an advanced track.
- No setup or onboarding lesson: accounts, costs, installing tools on Windows, what to do on a
  locked-down company PC.
- Safety beyond "security basics" is thin: confidential company data, privacy, licensing — a real
  concern for learners working in Japanese companies.
- Terminology: *agentic engineering* is emerging (2026) as the professional term next to *agentic
  coding*. Should the course introduce it, and where?

## 6. Questions — answer each under its own heading

1. **Sequencing.** Is v0's order right for these learners? Compare it with (a) strictly linear
   foundations-first and (b) an earlier-hands-on spiral. Where should the LLM internals go?
2. **The first win.** Where should the first hands-on session with a real agent happen, and what
   exactly should the learner build in under 30 minutes, free or cheap, on Windows?
3. **Scope and the minimum path.** Which 15–20 lessons form the minimum path that ships first?
   What should be cut, merged, split, or moved to an optional advanced track?
4. **Engagement.** What keeps a self-paced, phone-first, Facebook-driven audience going: a recurring
   case study or characters, challenges, streaks, community prompts? What works on Facebook for
   Vietnamese and Japanese beginners?
5. **Effectiveness.** How should practice and assessment work without a learning platform —
   quizzes, projects, self-checks, spaced repetition through posts?
6. **Hands-on constraints.** Which tools should beginners start with (free vs paid; Claude Code,
   Codex, Cursor, GitHub Copilot, Gemini CLI…), on Windows and on locked-down company PCs, and
   how do we keep an agent that runs commands safe? Give a recommended setup path and a fallback
   for learners with no paid plan.
7. **Trilingual strategy.** Vietnamese as the source language: how should examples be localized
   for Japan and for Vietnam, and how should the glossary teach English and Japanese vocabulary?
   What are the risks?
8. **The pilot lesson.** Review `course/{vi,en,ja}/lessons/chatbot-to-agent.md` and
   `course/data/sections.yaml`: tone, length, template, analogies, infographics. What should change
   before fifty more lessons are written?
9. **Staying current.** How should evergreen concepts be separated from tool-specific steps, and
   how often should lessons be reviewed?
10. **Data model gaps.** What does the website or the Facebook series need that the schema lacks —
    for example prerequisites, difficulty, learning outcomes, estimated effort, or a minimum-path
    flag?
11. **Infographics.** For the lessons of the minimum path, which idea deserves a diagram, with which
    template (compare, equation, cycle, flow — or a new one), and what should it show?

## 7. What to deliver

1. **Verdict on v0** in at most ten bullets, each citing a repository file path.
2. **Roadmap v1:** module → unit → lesson with English titles; for every lesson a one-sentence
   objective, a type (`concept`, `demo`, `hands-on` or `project`) and minutes. Mark every lesson
   against v0 with **KEEP / MOVE / MERGE / SPLIT / NEW / CUT**, using the v0 lesson ids; every v0
   id must appear exactly once.
3. **The minimum path:** an ordered list of lesson ids.
4. **Answers to questions 1–11.**
5. **Top risks and open questions** for the course owner.
6. **A five-line summary in Vietnamese** at the end (Tóm tắt).
