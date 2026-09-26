---
lesson: chatbot-to-agent
lang: en
status: review
summary: >-
  A chatbot answers questions; an AI agent takes a goal, then plans, uses tools, and checks
  and fixes its own work until the job is done. This lesson helps you tell apart three
  levels: chatbot, AI assistant and AI agent.
social:
  hook: "Google Maps gives you directions. A taxi driver gets you there. AI works the same way. 🚕"
  question: Which task in your daily work would you most like to hand to an AI agent?
---

# From Chatbot to AI Agent: AI That Does the Work, Not Just Answers

<!-- section: objective -->
## Lesson Objective

By the end of this lesson, you will be able to:

- Tell a **chatbot**, an **AI assistant** and an **AI agent** apart with one simple question: *who performs the steps?*
- Describe what an AI agent is made of: a brain (an LLM), hands (tools) and a do–check–fix loop.
- Explain why **agentic coding** — building software with AI agents — is the heart of this course.

<!-- section: hook -->
## Why It Matters

Think back to the last time you asked ChatGPT, Gemini or Claude for help with something concrete, such as *"How do I total this month's spending from three Excel files?"*

The answer was great: five steps, formulas included. But then **you** still had to open each file, copy the formulas, fix the errors and come back to ask again…

Now imagine a different kind of AI. You state the goal, and it **opens the files, writes the formulas, runs them, notices an error and fixes it**, then reports back: *"Done — September spending comes to $1,240. Here is what I did."*

That kind of AI has a name: an **AI agent**. And it is changing the way people build software.

<!-- section: read-first -->
## Watch and Read First

Optional — this lesson stands on its own. If you want to go further:

- [Building Effective AI Agents — Anthropic](https://www.anthropic.com/engineering/building-effective-agents): a very clear explanation of *workflows* versus *agents*.
- [What is agentic coding? — Google Cloud](https://cloud.google.com/discover/what-is-agentic-coding): a short introduction to agentic coding.

<!-- section: concept -->
## Core Idea

### Three levels of AI you will meet

| | Chatbot | AI assistant (copilot) | AI agent |
|---|---|---|---|
| You give it | A question | Work in progress | A **goal** |
| What it does | Answers in text | Suggests inside your tools | Plans, **acts on its own**, checks its work |
| Who performs the steps? | You | You (with suggestions) | **The AI** (you supervise) |
| Example | Q&A in ChatGPT | Code suggestions in an editor | Claude Code or Codex building a whole feature |

The single most useful question is: **who performs the steps?** With a chatbot, the AI thinks and you do. With an agent, the AI thinks *and* does — you assign the work and check it.

### What is an AI agent made of?

Remember this formula:

> **AI agent = brain (LLM) + hands (tools) + loop (do → check → fix)**

- **Brain — the LLM (large language model):** understands the request, reasons and decides the next step.
- **Hands — tools:** the real actions the agent is allowed to take: reading and writing files, running commands, searching the web, calling other services.
- **Loop:** an agent does not act once and stop. It **thinks → acts → observes the result**, and repeats until the goal is met or it needs to ask you.

### What is agentic coding?

When agents are used to build software — writing code, running it, fixing bugs, writing tests — we call it **agentic coding**. You no longer type every line; your role becomes **assigning the work, setting the criteria and checking the result**. That is exactly the skill this course teaches.

<!-- section: analogy -->
## Simple Analogy

You need to get from home to the airport.

- **A chatbot is like Google Maps:** it gives detailed directions — but **you** drive, deal with the traffic jams and find a parking space.
- **An AI agent is like a taxi driver:** you just say *"the airport, before 8 o'clock."* The driver picks the route, detours around traffic and gets you there.

But notice: even in a taxi, **you still have to give the right address and check that you arrived at the right terminal**. Working with an AI agent is the same — a clear request and a final check are your job.

The comparison has a weak spot, too: a taxi driver rarely drives to the wrong city, while an agent sometimes misunderstands a request with great confidence. That makes the final check even more important with an agent.

<!-- section: example -->
## Real Example

The task: *build a birthday invitation web page for An, who is turning five — dinosaur theme, with an "RSVP" button.*

**With a chatbot:**

1. You ask; the chatbot gives you a block of HTML.
2. You create a file, paste the code in and open it in a browser.
3. The button does not work, so you copy the error message and paste it back into the chat.
4. You repeat steps 2–3 until it works. You performed every step.

**With an AI agent (for example, Claude Code):**

1. You type the request above.
2. The agent creates the folder and files, writes the HTML and CSS, and opens the page to test it.
3. It notices the button is broken, reads the error, fixes it and runs it again.
4. It reports: *"Done. I created three files; here is how to open the page."* You look at it and ask for changes: *"Make it green and add the party date and time."*

Same goal — but with an agent, **you move from doing the work to directing and approving it**.

<!-- section: try-it -->
## Try It Yourself

No installation needed; it takes about five minutes:

1. List **three tasks** you repeat every week (for example: compiling a report, replying to template emails, renaming a batch of files).
2. For each one, ask yourself: *is an **answer** from a chatbot enough, or do I need an agent to **do** the steps?*
3. For the task best suited to an agent, write the goal in **one sentence**, plus how you would check that it was done correctly.

Keep this list — in the projects at the end of the course, you will turn one of these tasks into a real project.

<!-- section: misconceptions -->
## Common Misconceptions

- **"An agent is a humanoid robot."** — No. An agent is software; its "hands" are tools on a computer.
- **"Agents are smart, so they never make mistakes."** — Wrong. Agents can misunderstand a request or get things wrong, which is why you always check the result.
- **"You have to be a programmer to use agents."** — Not required. But understanding software basics helps you give clearer instructions and spot problems earlier — which is why this course starts with software foundations.
- **"Agents will replace people entirely."** — Agents take over many *steps*; people still decide *what* to build, *for whom*, and *what counts as done*.

<!-- section: takeaways -->
## Key Takeaways

- A chatbot **answers**; an AI agent **acts** to reach a goal.
- The deciding question: **who performs the steps?**
- Agent = LLM (brain) + tools (hands) + a do–check–fix loop.
- You still assign the work and **check the result** — the more capable the agent, the more that check matters.
- Agentic coding = building software with AI agents — the subject of this whole course.

<!-- section: quiz -->
## Quick Check

**Question 1.** What is the biggest difference between a chatbot and an AI agent?

- A) An agent uses a bigger AI model
- B) An agent can use tools to act on its own and check the results in a loop
- C) An agent never makes mistakes

**Question 2.** Which of these tasks needs an AI agent rather than a chatbot?

- A) Explaining what a "variable" is in programming
- B) Creating the files for a web page, running it and fixing errors until it works
- C) Translating a sentence into Japanese

**Question 3.** An agent says "done." What should you do next?

- A) Trust it completely and use it right away
- B) Check the result against the criteria you set
- C) Make the agent redo everything, just to be safe

<details>
<summary>Show answers</summary>

1. **B** — tools plus a loop are what turn an AI that *talks* into an AI that *works*.
2. **B** — it takes several real actions (creating files, running, fixing), not just an answer.
3. **B** — assigning the work and approving it is always your responsibility.

</details>

<!-- section: sources -->
## Recommended Sources

- Anthropic — [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents) (December 2024)
- Anthropic — [Claude Code overview](https://code.claude.com/docs/en/overview)
- Google Cloud — [What is agentic coding?](https://cloud.google.com/discover/what-is-agentic-coding)
- IBM — [What is Agentic AI?](https://www.ibm.com/think/topics/agentic-ai)
