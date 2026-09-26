# Vòng 1 — câu trả lời của Codex (nguyên văn)

> Bản sao nguyên văn, không sửa, của [bình luận 5846845480](https://github.com/vohoailinh90/Agentic-coding-course/issues/1#issuecomment-5846845480)
> trong issue #1 (Codex, 2026-09-26 13:57 UTC), trả lời yêu cầu ACC-0001 trên commit
> `9c28f454f4e3789bcc344556daf902ca7e312d57`. Phần kiểm chứng và kết luận của Claude nằm ở
> [round-1.md](round-1.md); đọc file đó trước.

---

# Roadmap v1 proposal

## Summary

I independently reviewed the repository at target SHA **`9c28f454f4e3789bcc344556daf902ca7e312d57`**.

My recommendation is an **earlier-hands-on spiral**, not the v0 foundations-first sequence:

1. See an agent work.
2. Learn the safety boundary.
3. Build something small in the first sitting.
4. Learn the minimum workflow for supervising it.
5. Add software and AI concepts only when a task creates the need.
6. Finish a useful office project.
7. Keep model internals and most harness engineering as optional depth.

This turns the minimum release into **18 lessons, approximately 5 hours including two projects**, rather than asking beginners to traverse the entire 944-minute roadmap before reaching projects.

---

# Evidence and verdict on v0

## Verdict on v0

1. **Keep the “whole game first” opening, but convert the demo into immediate participation.** The current opening establishes chatbot versus agent and then shows an agent building software, which is a strong conceptual hook, but the learner still does not operate an agent. 

2. **The first real session is much too late.** The brief confirms that `first-agent-session` is lesson 30, after 29 primarily conceptual lessons, despite learners having only 2–3 hours per week and being at risk of dropping out when material feels like IT school. 

3. **Modules 2 and 3 should be dismantled as prerequisite blocks.** V0 puts ten software-foundation lessons and eight AI-foundation lessons before the agentic-coding module; these subjects are useful, but most should be introduced just in time or offered as optional explainers. 

4. **Verification is correctly emphasized, but not yet practiced early enough.** The pilot repeatedly says that the human must check the result, including in the analogy, takeaways, and quiz; v1 should turn that message into an observable checklist in the first build. 

5. **The pilot lesson carries too many concepts for “one lesson, one idea.”** It simultaneously distinguishes three AI levels, introduces the agent formula, explains the agent loop, defines agentic coding, supplies an analogy, and compares two build workflows.  This conflicts with the content guide’s one-main-idea rule. 

6. **The template is structurally sound but too heavy as a universal reading experience.** Eleven possible sections and three-question quizzes support consistency, yet requiring every concept lesson to carry objective, hook, core idea, analogy, example, takeaways, and quiz encourages long pages for phone readers. 

7. **Projects should be distributed through the path rather than isolated at the end.** V0 reserves all four projects for the final module, including the highly approachable personal page.  A first-session micro-build and an early personal-page project would provide visible progress.

8. **Harness engineering is overrepresented for this audience.** Fifteen harness lessons exceed the size of every other non-project module, while the target learners include non-programmers, phone readers, and people on locked-down computers.  The essential ideas are context, permissions, tools, persistence, and verification; implementation mechanisms can form an advanced track.

9. **The trilingual architecture is a strong foundation worth preserving.** The repository already uses one learner-facing folder per language, stable lesson IDs, aligned sections, and centralized glossary entries.  The risk is production cost, not information architecture.

10. **The Facebook plan has an effective rhythm but needs learning-state metadata.** It already proposes a weekly lesson, a midweek term/visual, and a Friday quiz, followed by monthly review of saves and comments.  The curriculum does not yet identify minimum-path status, prerequisites, update sensitivity, or the artifact produced by a lesson. 

---

# Roadmap v1

## How to read the roadmap

- **KEEP** — same role and roughly the same location.
- **MOVE** — survives under its existing stable v0 ID, but changes position or track.
- **MERGE** — its teaching content is absorbed into the named surviving lesson; it is not produced as a separate lesson.
- **SPLIT** — the original ID retains one focused idea and a new ID takes the other.
- **CUT** — not planned as a standalone course lesson.
- **NEW** — not present in v0.

Stable IDs should be preserved because the repository explicitly makes order positional and IDs permanent. 

---

## Module 1 — Start Safely and Get a First Win

### Unit 1.1 — What agents do

1. **`chatbot-to-agent` — From Chatbot to AI Agent**  
   **SPLIT · concept · 8 min.** Distinguish an answering chatbot from an acting agent by asking who performs and verifies the steps.

2. **`agent-parts-and-loop` — Brain, Tools and the Agent Loop**  
   **NEW · concept · 8 min.** Explain how a model, tools, and a repeated act–observe–check loop combine into an agent.

3. **`watch-an-agent-build` — Watch an Agent Build and Check a Tiny Web Page**  
   **KEEP · demo · 10 min.** Predict each step while watching an agent create, run, inspect, and revise a one-file web page.

### Unit 1.2 — Choose a safe route

4. **`choose-your-learning-setup` — Choose Your Setup: Browser, Personal PC or Work PC**  
   **NEW · hands-on · 10 min.** Select a supported learning route based on installation rights, budget, device, and company-data restrictions.

5. **`data-safety-and-permissions` — Before You Let an Agent Act**  
   **NEW · concept · 10 min.** Classify data and actions as safe, ask-first, or prohibited before granting an agent access.

### Unit 1.3 — First build

6. **`first-agent-session` — Your First Agent Session: Build a One-File Task Card**  
   **MOVE · hands-on · 25 min.** Direct an agent to create a local single-file HTML task card, verify three visible acceptance criteria, and request one revision.

7. **`how-to-learn-this-course` — Choose Your Path and Keep Your Learning Log**  
   **MOVE · hands-on · 8 min.** Choose the minimum or extended path and record the artifact, evidence, and one unanswered question from each session.

---

## Module 2 — Direct, Check and Improve an Agent

### Unit 2.1 — Give clear work

8. **`lead-not-typist` — Be the Lead, Not the Typist**  
   **MOVE · concept · 8 min.** Separate the human responsibilities of intent, constraints, judgment, and approval from the agent’s execution work.

9. **`writing-good-specs` — Write a Small Spec and Definition of Done**  
   **MOVE · hands-on · 12 min.** Turn a vague request into a goal, constraints, examples, and observable acceptance checks.

10. **`explore-plan-build-verify` — Explore, Plan, Build, Verify**  
    **MOVE · hands-on · 12 min.** Use a four-stage checkpoint workflow and pause before potentially risky actions.

### Unit 2.2 — Inspect the result

11. **`reviewing-agent-changes` — Review What the Agent Changed**  
    **MOVE · hands-on · 15 min.** Inspect a before/after change view, connect each change to the specification, and reject unexplained work.

12. **`testing-basics` — Turn “Looks Right” into Checks**  
    **MOVE · hands-on · 12 min.** Convert acceptance criteria into repeatable examples and simple tests.

13. **`errors-and-debugging` — Read Errors and Ask for Evidence**  
    **MOVE · hands-on · 12 min.** Use an error message and a minimal reproduction to guide one evidence-based repair.

### Unit 2.3 — First meaningful artifact

14. **`project-personal-page` — Project: Publishable Personal Page**  
    **MOVE · project · 60 min.** Build and verify a small personal page while preserving a clean original and a review checklist.

---

## Module 3 — Software Literacy Just in Time

### Unit 3.1 — Files and projects

15. **`what-is-software` — Software Is Instructions, Data and a Running Environment**  
    **MOVE · concept · 8 min.** Identify the instructions, data, and environment involved in the learner’s first artifact.

16. **`files-folders-paths` — Find the Files Your Agent Touched**  
    **MOVE · hands-on · 10 min.** Locate a project folder, interpret a path, and distinguish the learner’s files from system files.

17. **`project-anatomy` — Read a Project Map**  
    **MOVE · concept · 10 min.** Identify entry points, user interface, data, services, and checks without needing to understand every line.

18. **`data-formats` — Read CSV, JSON and YAML Without Fear**  
    **MOVE · hands-on · 10 min.** Recognize rows, fields, nesting, and configuration values in three common data formats.

### Unit 3.2 — Code and history

19. **`programming-building-blocks` — Read the Four Patterns in Generated Code**  
    **MOVE · concept · 12 min.** Locate values, reusable actions, decisions, and repetition in code produced by an agent.

20. **`git-version-control` — Save a Checkpoint and Undo Safely with Git**  
    **MOVE · hands-on · 15 min.** Create a checkpoint, inspect changed files, and restore a known-good version.

21. **`command-line-basics` — Use Five Safe Terminal Commands**  
    **MOVE · hands-on · 15 min.** Navigate, list, create, inspect, and run within a dedicated practice folder.

### Unit 3.3 — Security essentials

22. **`security-basics` — Secrets, Personal Data and Third-Party Code**  
    **MOVE · concept · 12 min.** Keep credentials and confidential data out of prompts and repositories while checking where generated code came from.

23. **`cli-for-agents` — How an Agent Uses the Command Line**  
    **MERGE → `command-line-basics` · concept · 0 additional min.** Add an annotated “agent command / effect / risk” column to the terminal exercise.

24. **`api-for-agents` — How an Agent Talks to Services**  
    **MERGE → `project-anatomy` · concept · 0 additional min.** Introduce APIs as one project boundary rather than a separate beginner lesson.

---

## Module 4 — The AI Mental Models You Actually Need

### Unit 4.1 — Asking and grounding

25. **`prompting-basics` — Give AI Context, Task, Constraints and Examples**  
    **MOVE · hands-on · 12 min.** Improve a weak prompt using four reusable ingredients and compare the results.

26. **`hallucination` — Why Fluent Answers Still Need Evidence**  
    **MOVE · concept · 10 min.** Recognize unsupported claims and require citations, tests, or direct inspection according to the task.

27. **`context-window` — What the Agent Can See Right Now**  
    **MOVE · concept · 10 min.** Predict what information an agent can use, what has fallen out of view, and what must be supplied again.

28. **`next-token-prediction` — Why Language Models Generate Plausible Text**  
    **MOVE · concept · 10 min.** Connect next-token prediction to both useful generation and confident-looking mistakes.

29. **`tool-calling` — How a Model Requests a Real Action**  
    **MOVE · demo · 10 min.** Trace one tool request from model choice through permission, execution, returned result, and final response.

### Unit 4.2 — Optional AI foundations

30. **`ai-ml-dl` — The AI Family Tree in One Picture**  
    **MOVE · concept · 8 min.** Place machine learning, deep learning, generative AI, language models, and agents in one practical map.

31. **`how-machines-learn` — Data, Training and Models**  
    **MOVE · concept · 10 min.** Explain at a high level how examples shape a model without implying that it stores a rulebook.

32. **`predictive-vs-generative` — Prediction and Generation**  
    **MERGE → `ai-ml-dl` · concept · 0 additional min.** Show predictive and generative systems as task-oriented branches in the family-tree visual.

33. **`foundation-models` — Foundation Models**  
    **MERGE → `ai-ml-dl` · concept · 0 additional min.** Add foundation model as the reusable model layer beneath applications.

34. **`rag-intro` — Let AI Look Up Trusted Material**  
    **MOVE · demo · 10 min.** Compare an answer from model memory with one grounded in a small supplied document set.

35. **`prompt-rag-finetune-compare` — Prompt, Retrieve or Train?**  
    **MOVE · concept · 10 min.** Choose among clearer instructions, retrieval, and additional training using a simple decision tree.

36. **`fine-tuning-intro` — Fine-Tuning as a Standalone Beginner Lesson**  
    **CUT · concept · 0 min.** Retain only a concise definition and decision boundary inside `prompt-rag-finetune-compare`.

### Unit 4.3 — Optional model literacy

37. **`tokens` — Tokens, Limits and Cost**  
    **MOVE · demo · 8 min.** Observe how ordinary text is divided into model input units and why input size matters.

38. **`reasoning-models` — When More Deliberation Helps**  
    **MOVE · concept · 10 min.** Match more deliberate model behavior to tasks that benefit from planning and checking.

39. **`choosing-models` — Choose by Risk, Capability, Speed and Cost**  
    **MOVE · hands-on · 10 min.** Select a model using task risk and evaluation results rather than leaderboard reputation.

---

## Module 5 — Reliable Agent Work

### Unit 5.1 — Agentic work as a system

40. **`traditional-vs-agentic` — Manual Coding and Agentic Coding**  
    **MOVE · concept · 8 min.** Compare who writes, runs, inspects, and approves each step in manual and agent-assisted work.

41. **`vibe-vs-agentic` — Vibe Coding and Disciplined Agentic Work**  
    **MOVE · concept · 8 min.** Distinguish exploratory prompting from work governed by explicit checks and ownership.

42. **`the-agent-loop` — Trace an Agent Loop**  
    **MOVE · demo · 10 min.** Inspect a transcript and label every plan, action, observation, decision, and stop condition.

43. **`tool-landscape` — Choose a Tool by Environment, Not Hype**  
    **MOVE · concept · 10 min.** Choose among browser, editor, terminal, and hosted-workspace experiences using a maintained comparison card.

44. **`workflow-frameworks` — Add Structure Only When the Task Needs It**  
    **MOVE · concept · 10 min.** Choose a lightweight plan, test-first loop, or review gate according to task uncertainty and risk.

### Unit 5.2 — The minimum useful harness

45. **`model-plus-harness` — Model + Harness = Working Agent**  
    **MOVE · concept · 10 min.** Explain how instructions, context, tools, permissions, state, and checks turn a model into a usable agent.

46. **`context-and-control` — Context and Control as Separate Harness Lessons**  
    **MERGE → `model-plus-harness` · concept · 0 additional min.** Represent context and control as two labeled harness components.

47. **`action-and-persist` — Action and Persistence as a Separate Harness Lesson**  
    **MERGE → `model-plus-harness` · concept · 0 additional min.** Represent action and state persistence as harness capabilities rather than a standalone lesson.

48. **`observe-and-verify` — Observation and Verification as a Separate Harness Lesson**  
    **MERGE → `model-plus-harness` · concept · 0 additional min.** Make evidence and verification the final harness layer and human approval gate.

49. **`context-engineering` — Give the Right Context at the Right Time**  
    **MOVE · hands-on · 12 min.** Improve an agent task by reducing irrelevant context and supplying the smallest authoritative inputs.

50. **`prompt-engineering-for-agents` — Durable Instructions for Repeated Work**  
    **MOVE · hands-on · 12 min.** Write persistent project instructions that specify boundaries, conventions, and validation commands.

51. **`hooks-and-permissions` — Permission Gates and Automatic Guardrails**  
    **MOVE · hands-on · 12 min.** Configure or simulate allow, ask, and deny rules for file, command, network, and secret access.

52. **`tests-and-ci-for-agents` — Let Machines Check Repeatable Claims**  
    **MOVE · demo · 12 min.** Read a test result and CI summary and distinguish passing automation from human acceptance.

### Unit 5.3 — Optional advanced practice

53. **`memory-and-skills` — Project Memory and Reusable Skills**  
    **MOVE · hands-on · 15 min.** Store durable guidance separately from task-specific context and verify that the agent follows it.

54. **`rag-for-agents` — Retrieval Inside an Agent Workflow**  
    **MERGE → `rag-intro` · demo · 0 additional min.** Extend the grounding demo with one agent decision about when to search.

55. **`agents-and-workflows` — One Agent, a Workflow or Several Agents?**  
    **MOVE · concept · 12 min.** Prefer the simplest coordination pattern that can be observed, debugged, and evaluated.

56. **`mcp` — Connect an Agent to Tools Through MCP**  
    **MOVE · demo · 12 min.** Trace a tool’s description, invocation, permission boundary, and returned result through an MCP connection.

57. **`evals` — Evaluate Repeated Agent Behavior**  
    **MOVE · hands-on · 15 min.** Create several representative cases and a scoring rubric for a repeated agent task.

---

## Module 6 — Build Something Useful

### Unit 6.1 — Office outcome

58. **`project-office-automation` — Project: Turn a Spreadsheet into a Checked Report**  
    **KEEP · project · 90 min.** Use synthetic spreadsheet data to generate a report whose totals, missing values, and output format can be independently checked.

59. **`project-retrospective` — Project Retrospective and Evidence Pack**  
    **NEW · hands-on · 15 min.** Record the specification, before/after evidence, checks, limitations, and one improvement for the next project.

### Unit 6.2 — Advanced projects

60. **`project-mcp-tool` — Advanced Project: Build a Narrow MCP Tool**  
    **MOVE · project · 90 min.** Expose one low-risk read-only capability and test its input, output, failure behavior, and permission boundary.

61. **`capstone-your-idea` — Capstone: Solve One Real Problem Safely**  
    **KEEP · project · 120 min.** Scope, build, verify, document, and demonstrate an original project with explicit data and action boundaries.

---

# Completeness check for v0 IDs

The roadmap disposition registry above contains:

- **57 distinct v0 lesson IDs**
- **57 v0 IDs accounted for**
- **3 new IDs:** `agent-parts-and-loop`, `choose-your-learning-setup`, `data-safety-and-permissions`
- **1 additional new reflection lesson:** `project-retrospective`
- **No v0 ID renamed**
- **One standalone cut:** `fine-tuning-intro`
- **Seven merged standalone lessons:** `predictive-vs-generative`, `foundation-models`, `cli-for-agents`, `api-for-agents`, `context-and-control`, `action-and-persist`, `observe-and-verify`, plus `rag-for-agents` merged into the RAG demo

The zero-minute entries are **migration dispositions**, not publishable lessons. A future `curriculum.yaml` should omit those nodes and record their redirects or supersession metadata elsewhere.

---

# Minimum path

The minimum path should ship first in this exact order:

1. `chatbot-to-agent`
2. `agent-parts-and-loop`
3. `watch-an-agent-build`
4. `choose-your-learning-setup`
5. `data-safety-and-permissions`
6. `first-agent-session`
7. `lead-not-typist`
8. `writing-good-specs`
9. `explore-plan-build-verify`
10. `reviewing-agent-changes`
11. `testing-basics`
12. `errors-and-debugging`
13. `files-folders-paths`
14. `git-version-control`
15. `hallucination`
16. `context-window`
17. `project-personal-page`
18. `project-office-automation`

This is approximately **302 minutes**, or about **five hours**, including 150 minutes of projects. At 2–3 hours per week, it can be completed in roughly two to three weeks of concentrated study, or published as an 18-week Facebook learning series.

`how-to-learn-this-course` should be available during onboarding but does not need to count as a learning milestone.

---

# Answers to questions 1–11

## 1. Sequencing

**V0’s order is not right for these learners.**

### Strict foundations-first

A strictly linear path would teach files, terminal, programming, AI/ML, and model internals before asking learners to build. It is logically tidy but motivationally weak. For Mai and Hana, it risks confirming the fear that this is an abstract IT course; the learner constraints and those dropout risks are explicit in the brief. 

### V0

V0 improves on a conventional curriculum by opening with a concept and a demo, but it then reverts to 18 foundation lessons before the agentic-coding module and places the first agent session at lesson 30. 

### Recommended spiral

Use this spiral:

1. **See:** compare chatbot and agent.
2. **Protect:** choose a setup and set boundaries.
3. **Do:** build one isolated artifact.
4. **Check:** inspect output against acceptance criteria.
5. **Explain:** introduce files, code, context, models, and tools only when the learner has encountered them.
6. **Repeat:** apply the same supervision loop to an office task.
7. **Deepen:** offer internals and harness mechanisms as optional layers.

### Where LLM internals belong

- `hallucination` and `context-window`: early, because they change safe behavior.
- `next-token-prediction` and `tool-calling`: after the first build, because experience gives them meaning.
- `tokens`, `reasoning-models`, and `choosing-models`: optional model-literacy unit.
- Training taxonomy and fine-tuning: optional; never a gate before practical work.

---

## 2. The first win

The first real session should occur **in the first sitting, immediately after the safety/setup choice**.

### Build

Create a **single-file HTML “My Weekly Task Card”** containing:

- the learner’s name or a fictional name;
- three recurring tasks;
- one button that marks a task complete;
- a clearly visible title;
- no external packages;
- no deployment;
- no personal or company data.

### Why this build

- It produces an instantly visible artifact.
- It is understandable without programming knowledge.
- A single file makes the agent’s changes inspectable.
- It can run locally in a browser.
- It avoids account integrations, API keys, databases, and package installation.
- It can become the seed of `project-personal-page`.

### Definition of done

The learner verifies:

1. the file exists in the designated practice folder;
2. it opens locally;
3. the title and three tasks are visible;
4. the button changes state;
5. the agent explains which file it changed;
6. one requested revision appears correctly.

The current pilot already uses a small invitation page to contrast chatbot and agent workflows, so the task shape is established in the course. 

---

## 3. Scope and the minimum path

Ship the 18-lesson minimum path above before writing the full roadmap.

### Core

Core content is anything needed to:

- choose a safe environment;
- state a testable goal;
- let an agent make a bounded change;
- understand the affected files;
- inspect the result;
- recover from errors;
- protect data;
- finish one personally meaningful and one office-oriented artifact.

### Optional foundations

Make AI taxonomy, model selection, tokenization, code-reading detail, terminal breadth, APIs, RAG, and advanced workflow patterns optional.

### Advanced track

Move reusable instructions, skills/memory, MCP, multi-agent design, CI, and evals into an advanced “Reliable Agent Work” track.

### Merge or cut

- Merge predictive/generative AI and foundation models into the AI family tree.
- Merge CLI/API explanations into applied software-literacy lessons.
- Merge harness anatomy’s four fragments into one strong visual model.
- Merge RAG for agents into the introductory grounding demo.
- Cut standalone fine-tuning from the beginner path.
- Keep the definition of fine-tuning in the comparison lesson.

---

## 4. Engagement

Use **one recurring case-study family**, not unrelated examples in every lesson:

- **Mai:** spreadsheet-to-report progression.
- **Tuấn:** a safe, fictional work checklist on a constrained Windows computer.
- **Hana:** meeting notes or daily-report formatting with synthetic information.
- **Huy:** adds one optional extension or inspects the generated code.

A lesson need not include all four. Pick one main character and provide one short “try this instead” variant.

### Facebook cadence

The existing Monday lesson / Wednesday term or visual / Friday quiz cadence is sensible.  Extend it as follows:

- **Monday:** one idea and one prediction question.
- **Wednesday:** a diagram or before/after artifact.
- **Friday:** a challenge that produces a commentable result.
- **Weekend optional:** “show your evidence,” not merely “show your result.”

### Motivation mechanisms

Prefer:

- visible artifacts;
- “predict before reveal” questions;
- five-minute modifications;
- learner polls;
- screenshots with redacted data;
- peer review using a three-item checklist;
- a personal learning log.

Avoid platform-dependent streaks. Missing a week should not make a learner feel they have failed.

For Vietnamese audiences, localize familiar office and household contexts. For Japanese audiences, emphasize workplace permission, synthetic data, reporting discipline, and concise examples. Do not assert that either audience has one uniform learning style.

---

## 5. Effectiveness

Use a four-layer assessment model:

1. **Retrieval:** one question before the lesson and three concise questions after it.
2. **Application:** a five-to-ten-minute modification.
3. **Evidence:** screenshot, diff, test result, or checklist.
4. **Transfer:** reuse the idea in the next project.

Every hands-on lesson should end with:

- “I can show…” — the artifact;
- “I checked…” — the evidence;
- “I would not use this when…” — the boundary.

The current template already requires a self-checkable exercise for hands-on lessons and explanatory quiz answers. 

Use Facebook posts for spaced retrieval:

- week 0: introduce;
- week +1: one scenario question;
- week +3: identify an error or unsafe action;
- next project: require the same skill without naming it.

Do not use quiz scores as completion. A project checklist is stronger evidence of applied competence.

---

## 6. Hands-on constraints

Tool names and plans are volatile, so the curriculum should recommend a **capability profile**, backed by a separately maintained, dated tool matrix.

### Recommended path

1. **Browser or hosted workspace first**
   - No administrator rights required.
   - Can create a disposable practice project.
   - Shows the files changed.
   - Requests confirmation before risky actions.
   - Allows export or download.
   - Has a usable free allowance when the lesson is published.

2. **Personal Windows machine second**
   - Use a dedicated folder containing only practice files.
   - Prefer a maintained graphical installer or supported Windows route.
   - Start with read/write access only inside that folder.
   - Do not enable unrestricted commands or credentials.

3. **Terminal agent third**
   - Introduce only after files, paths, changes, checkpoints, and permissions.
   - Show every requested command and its effect.

### Tool categories

- **Browser-first fallback:** whichever maintained product at publication time can create or edit a small sandboxed artifact without local installation.
- **Editor-integrated route:** Cursor, GitHub Copilot, or an equivalent product if the learner already uses a supported editor.
- **Terminal route:** Claude Code, Codex, Gemini CLI, or an equivalent only after the learner can review commands and changes.

Because prices, free allowances, operating-system support, and product capabilities can change, v1 should **not permanently declare one vendor the winner inside evergreen prose**. The content guide already requires volatile commands, menus, prices, and plan names to be dated. 

### Locked-down company PC fallback

- Watch the demo on the company device.
- Perform the exercise later on a personal device or hosted sandbox.
- Use only synthetic data.
- Never attempt to bypass installation, proxy, policy, or security restrictions.
- If no executable agent is available, use a chatbot to generate the one-file artifact, download it, inspect it, and perform the same verification checklist. Clearly label this as a **manual-action simulation**, not a full agent session.

### Command safety

- Work in a disposable folder.
- Show the agent’s allowed scope.
- Default to “ask before command.”
- Refuse destructive, administrative, credential, or broad filesystem operations.
- Start each exercise from a known-good copy.
- Require a checkpoint before multi-file changes.
- Never paste company-confidential data.
- Stop when the tool’s explanation and observed change disagree.

The repository’s content guide already requires scope reminders, confidential-data warnings, and visible human checking whenever an agent operates. 

---

## 7. Trilingual strategy

Keep Vietnamese as the source language, but treat it as the **source of instructional intent**, not a sentence-by-sentence master translation.

The existing guide already calls for Vietnamese-first authoring, section parity, glossary consistency, and culturally appropriate localization. 

### Recommended workflow

1. Write a language-neutral lesson brief:
   - objective;
   - misconception;
   - worked example;
   - exercise;
   - acceptance evidence;
   - safety boundary.
2. Author Vietnamese.
3. Review the Vietnamese version for conceptual simplicity.
4. Localize English and Japanese independently against the brief.
5. Perform a parity review of meaning, diagrams, exercise outcome, and safety—not merely headings.
6. Have a native or professional Japanese reviewer check workplace phrasing before publication.

### Examples

- Preserve the same underlying skill.
- Localize names, currency, common workplace artifacts, and communication conventions.
- Use synthetic data in all languages.
- Avoid stereotypes such as assuming every Japanese company uses the same approval process.

### Glossary

For each term, store:

- preferred Vietnamese term;
- common English industry term;
- preferred Japanese term;
- Japanese reading where useful;
- short beginner definition;
- one “not the same as” distinction;
- term status: stable, emerging, or vendor-specific.

The current glossary already centralizes three-language terms and supports Japanese readings. 

### Risks

- Vietnamese wording copied too literally into Japanese.
- Different examples accidentally changing task difficulty.
- English technical terms overwhelming the Vietnamese explanation.
- Japanese katakana being presented without practical meaning.
- Terminology drifting between glossary and lessons.
- Triple production cost creating outdated translations.

---

## 8. The pilot lesson

### What works

- Friendly, direct tone.
- Strong “who performs the steps?” distinction.
- Concrete spreadsheet and web-page examples.
- The taxi analogy explicitly states where it breaks down.
- Human verification is repeated consistently.
- The diagrams appear at the point of explanation.
- All three language files preserve the same section structure, matching the repository model. 

### What should change before producing fifty more lessons

1. **Split the lesson.** Keep `chatbot-to-agent` focused on “who performs the steps?” Move model + tools + loop into `agent-parts-and-loop`.
2. **Reduce the first lesson to one or two diagrams.** Four visuals in one short beginner lesson compete for attention.
3. **Make the exercise behavioral.** Instead of only listing candidate tasks, ask learners to classify two examples and write one goal plus one verification criterion.
4. **Do not imply that all agents independently notice and repair failures.** Phrase this as a capability that depends on the tool, permissions, task, and feedback available.
5. **Use vendor names only as dated examples.** The pilot names Claude Code directly in the evergreen example. 
6. **Shorten repeated explanations.** The same human-check message appears in the analogy, example, misconceptions, takeaways, and quiz; retain repetition across posts, but not all of it in the core reading.
7. **Make `read-first` collapsible or place it at the end.** Asking absolute beginners to leave the lesson early weakens momentum.
8. **Change the template from “include whenever allowed” to “minimum useful sections.”** Keep objective, hook, core/try-it, evidence, takeaways, and quick check; add analogy, misconceptions, and sources only when useful.
9. **Add an estimated active time separate from reading time.**
10. **Pilot the lesson with at least one learner from each primary audience before scaling production.**

---

## 9. Staying current

Separate content into three layers:

### Evergreen core

- mental models;
- supervision workflow;
- verification;
- data boundaries;
- file/project concepts;
- prompting principles.

These should avoid product UI, prices, quotas, and plan names.

### Replaceable tool card

Maintain a small dated block containing:

- tested product/version or access date;
- operating-system support;
- free/paid requirement;
- exact exercise route;
- screenshots;
- known limitations;
- last verified date.

### Instructor maintenance note

Store links and a short re-test checklist outside learner prose.

### Review frequency

- **Monthly:** setup pages, tool matrix, pricing/access statements, screenshots, commands, and external links.
- **Quarterly:** tool-specific lessons and safety guidance.
- **Every six months:** minimum-path sequencing, glossary, and examples.
- **On trigger:** immediately review content after a major product rename, permission-model change, discontinued plan, broken link, or learner report.

The current guide already recognizes that tool-specific details can change monthly and requires an “as of” date for such content. 

---

## 10. Data model gaps

Add these curriculum fields:

```yaml
track: core | optional | advanced
minimum_path_order: 1
difficulty: starter | beginner | intermediate
prerequisites: [lesson-id]
outcomes:
  - observable learner action
artifact: short description
evidence: short description
active_minutes: 15
device_support: [phone-read, browser-do, windows-do]
setup_route: browser | local | either
risk_level: low | medium | high
data_policy: synthetic-only
tool_dependency: evergreen | dated-card | vendor-specific
last_verified: 2026-09-26
review_after: 2026-10-26
supersedes: [old-lesson-id]
```

Add these lesson-front-matter fields:

```yaml
content_reviewed: 2026-09-26
tool_steps_reviewed: 2026-09-26
facebook:
  sequence: 1
  variants: [lesson, visual, quiz, challenge]
```

Add these project fields:

```yaml
deliverables: [...]
rubric: [...]
starter_files: [...]
solution_notes: [...]
```

### Why these are gaps

The current curriculum schema stores title, type, minutes, and glossary terms but not prerequisite relationships, track, outcomes, artifacts, evidence, or update sensitivity.  The website plan assumes rendering and learner progress but does not yet define how alternate paths or prerequisites would be represented. 

Do not encode vendor availability directly in the core curriculum. Reference a dated tool-card ID instead.

---

## 11. Infographics

The four current templates—compare, equation, cycle, and flow—cover many conceptual explanations.  Add two templates:

- **boundary:** concentric or partitioned safe / ask / prohibited zones.
- **checklist:** artifact beside observable checks and evidence.

### Minimum-path diagram plan

| Lesson | Template | What it should show |
|---|---|---|
| `chatbot-to-agent` | compare | Chatbot answers versus agent acts; the emphasized row is “who performs the steps?” |
| `agent-parts-and-loop` | equation + cycle | Model + tools + loop = agent, followed by act → observe → decide. |
| `watch-an-agent-build` | flow | Goal → inspect folder → create → run → check → revise → report. |
| `choose-your-learning-setup` | flow | Installation rights, personal/company device, budget, then browser/local/watch-only route. |
| `data-safety-and-permissions` | **boundary** | Safe synthetic data, ask-first actions, and prohibited secrets/company data. |
| `first-agent-session` | **checklist** | Requested artifact on the left; six definition-of-done checks on the right. |
| `lead-not-typist` | compare | Human owns intent/approval; agent owns proposed execution. |
| `writing-good-specs` | equation | Goal + context + constraints + examples + definition of done. |
| `explore-plan-build-verify` | cycle | Explore → plan → build → verify, with a human approval gate. |
| `reviewing-agent-changes` | compare | Expected change versus observed diff versus unexplained change. |
| `testing-basics` | flow | Requirement → example → check → result → decision. |
| `errors-and-debugging` | cycle | Observe → isolate → hypothesize → test → learn. |
| `files-folders-paths` | flow | Practice folder → project folder → file; explicitly show the allowed boundary. |
| `git-version-control` | flow | Working copy → inspect diff → checkpoint → experiment → restore. |
| `hallucination` | compare | Fluent claim without evidence versus claim backed by inspection/test/source. |
| `context-window` | **boundary** | In context, available by tool, and unavailable unless supplied. |
| `project-personal-page` | **checklist** | Required page elements, behavior, accessibility check, and evidence. |
| `project-office-automation` | flow | Synthetic spreadsheet → validate rows → transform → report → reconcile totals. |

Not every lesson needs a new diagram. Reuse the same workflow graphic when the mental model is intentionally recurring; consistency reinforces the spiral and reduces trilingual production cost.

---

# Top risks and open questions

## Risks

1. **Tool churn:** a first-session route may stop being free or change its Windows support.
2. **False safety confidence:** a dedicated folder reduces risk but does not make arbitrary command execution safe.
3. **Locked-down workplace devices:** some learners may be unable to do any practical agent work at work.
4. **Trilingual production bottleneck:** four diagrams and eleven sections per lesson multiplied across three languages are unlikely to be sustainable for one part-time author.
5. **Scope creep:** advanced harness topics can easily displace beginner practice.
6. **“Agent” ambiguity:** tools marketed as agents have very different action, permission, and verification capabilities.
7. **Project difficulty gap:** the office-automation project may require more spreadsheet and Python knowledge than the minimum path supplies.
8. **Facebook fragmentation:** learners arriving through individual posts may miss prerequisites and safety warnings.
9. **Verification theater:** learners may tick a checklist without understanding whether the checks cover the real risk.
10. **Localization drift:** examples can remain structurally aligned while becoming unequal in difficulty or cultural clarity.

## Decisions needed from the course owner

1. Is the first hands-on experience allowed to use a hosted/browser service, or must all work run locally?
2. Can the minimum path assume access to a personal computer for two project sessions?
3. Is publishing/deployment part of `project-personal-page`, or is a local artifact sufficient?
4. Should Japanese learners be a co-primary audience from launch, or should Japanese follow after the Vietnamese pilot is validated?
5. Does the course promise “coding without prior coding,” or “learning enough code literacy to supervise coding agents”?
6. Is `project-office-automation` allowed to use Python, or must it have a spreadsheet-only route?
7. Who performs native-level Japanese review?
8. Which actions should be prohibited in every beginner exercise?
9. Should advanced-track lessons be produced only after minimum-path completion data exists?
10. Should “agentic engineering” be introduced as an optional broader label? My recommendation is yes: mention it once after the first project, while retaining “agentic coding” as the course’s beginner-facing term.

---

# Changed files

**None.** This was a read-only brainstorm. In accordance with the task contract, I did not edit files, create a commit, push a branch, or create a pull request.

---

# Tests performed

- ✅ `git rev-parse HEAD` — confirmed the checked-out repository was exactly `9c28f454f4e3789bcc344556daf902ca7e312d57`.
- ✅ `git show -s --format='%H %s' 9c28f454f4e3789bcc344556daf902ca7e312d57` — confirmed the requested target commit exists.
- ✅ `python -m pip install -r requirements-eval.txt` — installed the repository’s declared validation dependency.
- ✅ `python -m src.main validate` — `Content store OK`; 3 lesson files checked and 0 warnings.
- ✅ `python -m src.main stats` — confirmed 7 modules, 17 units, 57 lessons, 944 minutes, and one lesson in review in each language.
- ✅ `git diff --check` — no whitespace errors or working-tree patch.
- ✅ `git status --short` — no repository changes were produced.
- ⚠️ Official tool-product web verification could not be completed because the browsing service returned HTTP 401; consequently, the setup recommendation is deliberately capability-based rather than asserting current prices or free-plan limits.

---

# Remaining risks

The largest unresolved dependency is the **actual first-session environment**. Before implementation, the owner should test at least one browser route, one personal-Windows route, and the watch-only/manual fallback using fresh non-paid accounts and a restricted Windows user. Tool availability, plan limits, and exact permission behavior should be recorded with a verification date rather than embedded as timeless claims.

The second major uncertainty is whether the 90-minute office project can remain genuinely beginner-friendly without introducing a hidden Python, package-installation, or spreadsheet prerequisite.

---

# Recommended next action

Create a small decision record for a **minimum-path pilot** before rewriting the full curriculum:

1. Approve or amend the 18 lesson IDs.
2. Choose and test the three setup routes.
3. Split `chatbot-to-agent` into the focused concept lesson and `agent-parts-and-loop`.
4. Write `choose-your-learning-setup`, `data-safety-and-permissions`, and the revised `first-agent-session`.
5. Pilot those six opening lessons with Mai-like, Tuấn-like, and Hana-like learners.
6. Measure completion, time-on-task, setup failures, unsafe assumptions, and whether learners can independently state what they checked.
7. Only then update the remaining roadmap and produce additional translations.

# Tóm tắt

Lộ trình v1 nên cho người học dùng agent ngay trong buổi đầu, sau một bước chọn môi trường và thiết lập giới hạn an toàn.  
Lộ trình tối thiểu gồm 18 bài, đi từ trải nghiệm đầu tiên đến hai sản phẩm có thể kiểm tra được.  
Các kiến thức phần mềm và LLM được đưa vào đúng lúc cần dùng, thay vì trở thành 18 bài lý thuyết bắt buộc ở đầu khóa.  
Phần lớn nội dung harness, MCP, multi-agent và eval nên chuyển thành nhánh nâng cao sau khi kiểm chứng lộ trình tối thiểu.  
Bước tiếp theo là chốt môi trường thực hành, viết lại sáu bài mở đầu và thử với người học thật trước khi sản xuất thêm bằng ba ngôn ngữ.

 [View task →](https://chatgpt.com/s/cd_6ab7ce1bed888191af85b3c62935783c)
