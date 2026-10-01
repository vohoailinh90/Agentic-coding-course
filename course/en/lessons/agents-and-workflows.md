---
lesson: agents-and-workflows
lang: en
status: review
summary: >-
  A workflow is a set of steps fixed in advance by you (or by code); an agent is when the model decides the next
  step itself. Start with the simplest thing that gets the job done, and add complexity only when needed. A
  second agent (a subagent) helps when a side task would flood the main context, when you need a review in a
  fresh context, or when independent parts can run in parallel — but every added agent costs more and needs a
  clear brief.
social:
  hook: "A video online: \"10 agents working like a company\". Does Huy's club newsletter need 5 agents? 🤖🤖🤖"
  question: In your own work, is there a part that really needs a second "person" to check it with fresh eyes?
---

🌐 [Tiếng Việt](../../vi/lessons/agents-and-workflows.md) · **English** · [日本語](../../ja/lessons/agents-and-workflows.md)

# Agents and Workflows: When Do You Need More Than One Agent?

<!-- section: objective -->
## Lesson Objective

By the end of this lesson, you will be able to:

- Tell a **workflow** (steps fixed in advance) apart from an **agent** (the model decides the steps).
- Choose the simplest thing that gets the job done, using a four-step "ladder".
- Name three cases where a **subagent** (a helper agent) really helps, and what it costs.

<!-- section: hook -->
## Why It Matters

Huy watches a video: ten agents working like a company. He wants the same for his club's **monthly newsletter**: five agents, each with a role.

But the newsletter is one page, drawn from three calendar files, once a month. Are five agents the right tool — or is it hiring five chefs to cook a family dinner?

<!-- section: concept -->
## Core Idea

### Workflows and agents

Anthropic (December 2024) distinguishes two kinds of system:

- **A workflow:** the steps are fixed in advance, by code or by you; the model does each step but does not choose them. Example: Mai's monthly-report skill in [Project Memory and Reusable Skills](memory-and-skills.md).
- **An agent:** the model **decides** the next step and the tool itself, as in [the agent loop](the-agent-loop.md).

Workflows are predictable for well-defined tasks; agents are flexible when the steps cannot be predicted.

### Start simple

Anthropic's advice: find **the simplest solution** that works, and add complexity only when needed.

![The complexity ladder](../diagrams/complexity-ladder.svg)

Climb one step at a time, only when the step below is not enough:

1. **One request** to a chatbot — one question, one answer, no tools or loop.
2. **A fixed workflow** — the steps are known in advance (if it repeats, package it as a skill).
3. **One agent** — the steps depend on what it discovers along the way.
4. **Agent + subagent** — only for a specific reason, like the three below.

### Three times a subagent helps

A **subagent** is a helper the main agent starts to do one part of the work in **its own context**. The Claude Code documentation (as of September 2026) gives reasons to use one; the three most common:

- **A side task would flood the main context** — searching hundreds of files, reading long logs. The subagent returns only its final answer, so ask it for a short summary.
- **You need fresh eyes** — a review that sees only the result and the criteria, as in [Add Structure When the Task Needs It](workflow-frameworks.md).
- **Independent parts can run in parallel.**

### What every added agent costs

- **More cost:** each subagent sends its own requests, counted against the same usage limits.
- **It usually starts without your conversation:** in Claude Code (as of September 2026), an ordinary subagent gets only its brief plus what its setup loads (usually the project's instruction file). Some tools, and Claude Code's fork mode, pass the conversation along — check yours.
- **More places to go wrong:** each handoff can lose information, and you still check the final result.

<!-- section: analogy -->
## Simple Analogy

A big restaurant kitchen has a head chef, several cooks and someone who tastes before serving — right for hundreds of plates a night. Hiring five chefs for a family dinner only adds directing, bumping into each other, and cost. One thing worth keeping even in a small kitchen: **someone who did not cook the dish tastes it again**.

Where the comparison breaks down: a new cook can hear everything in the kitchen. An ordinary subagent does not hear your conversation with the main agent, so whatever it needs from it must be written in its brief.

<!-- section: example -->
## Real Example

Each month Huy has to read three event-calendar files (made-up data in `ai-practice`), write a one-page newsletter, check the dates, times and places, and save it as `newsletter_month_X.md`. Instead of his five-agent plan, he climbs the ladder:

- **One request?** Almost enough, but he repeats the same steps every month.
- **A fixed workflow?** Yes. He writes a `monthly-newsletter` skill: read the three files, write to the template, save the file.
- **A subagent?** The calendars are short and nothing needs to run in parallel, but the whole club will rely on the dates — so **fresh eyes**, yes. The skill's last step: *"Give a new subagent this task: compare every date, time and place in the newsletter with the three calendar files. Only report mismatches; change nothing."*

In the first month, the reviewer reports one mismatch: the picnic says *Saturday 17 October*, the calendar file says *Sunday 18 October*. Huy fixes it, then reads the whole newsletter himself before sending it. One workflow and one reviewer instead of five agents: cheaper, fewer handoffs, and fresh eyes where they mattered.

<!-- section: misconceptions -->
## Common Misconceptions

- **"More agents means more intelligence."** — Each one adds cost and another handoff. Add agents for a specific reason, not because it sounds modern.
- **"A subagent knows what I told the main agent."** — An ordinary Claude Code subagent does not see that conversation (other tools vary). Write its brief as clearly as a request for someone new.
- **"With a review agent, I don't need to read it."** — It helps catch mistakes; the final result is still your responsibility.

<!-- section: recap -->
## The Lesson in One Picture

![Recap: agents and workflows](../diagrams/agents-and-workflows-recap.svg)

<!-- section: takeaways -->
## Key Takeaways

- Workflow: steps fixed in advance. Agent: the model picks the steps.
- Start simple; only climb to a more complex step when the one below is not enough.
- Subagents help when a side task would flood the context, when you need fresh eyes, or when independent parts can run in parallel.
- Every added agent: more cost, usually no access to your conversation, more places to go wrong.
- More agents do not replace your check of the final result.

<!-- section: quiz -->
## Quick Check

**Question 1.** What is the core difference between a workflow and an agent?

- A) Workflows use cheap models, agents use expensive ones
- B) In a workflow the steps are fixed in advance; in an agent the model decides the next step
- C) Workflows don't use AI

**Question 2.** When is a subagent most worth using?

- A) Changing the color of a heading
- B) Writing a short email
- C) Finding one piece of information in hundreds of long log files, when you only need a summary

**Question 3.** Why does a subagent's brief need to be clear?

- A) Because an ordinary subagent (as in Claude Code) starts with a fresh context and does not see your conversation with the main agent
- B) Because a subagent always runs on a weaker model that needs simpler instructions
- C) Because the subagent cannot use any tools

<details>
<summary>Show answers</summary>

1. **B** — who picks the next step is the main difference; both use a model.
2. **C** — the side task would flood the main context; a subagent does it separately and returns the short summary you ask for.
3. **A** — what you told the main agent reaches it only through the brief (or the project files it reads).

</details>

<!-- section: sources -->
## Recommended Sources

- Anthropic — [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents) (English, December 2024): workflows follow predefined paths, agents direct their own process; find the simplest solution and add complexity only when needed.
- Anthropic — [Create custom subagents](https://code.claude.com/docs/en/sub-agents) (English, as of September 2026): a subagent works in its own context and returns only its final result; it does not see the conversation history; each one counts against the same usage limits.
