# Vòng 2 — câu trả lời của Codex (nguyên văn)

> Bản sao nguyên văn, không sửa, của [bình luận 5850735921](https://github.com/vohoailinh90/Agentic-coding-course/issues/1#issuecomment-5850735921)
> trong issue #1 (Codex, 2026-09-26 23:05 UTC), trả lời yêu cầu ACC-0001 vòng 2 trên commit
> `44c7fb8b44064be2f0b648937861e1eed00a1e88`. Phần kiểm chứng và kết luận của Claude nằm ở
> [round-2.md](round-2.md); đọc file đó trước.

---

# Round 2 verdict on roadmap v1

## Summary

I reviewed the repository at the exact requested target SHA **`44c7fb8b44064be2f0b648937861e1eed00a1e88`**.

**Verdict:** roadmap v1 is ready to serve as the production baseline, but I recommend **two curriculum edits and three pilot-content corrections before writing the remaining minimum-path lessons**:

1. Teach `files-folders-paths` before learners review diffs.
2. Add `data-formats` to the minimum path before the office-automation project.
3. Correct the pilots’ overly absolute description of what an LLM emits and who selects tools.
4. Soften an infographic claim that makes every agent appear able to plan and verify its own work.
5. Localize the English and Japanese birthday-page example rather than carrying the Vietnamese name over unchanged.

These changes would leave **52 active lessons** and produce a **19-lesson, 347-minute minimum path**. The minimum path would still contain only core lessons, list each lesson once, and follow course order, as required by `docs/data-model.md`.

I **agree** with keeping `project-personal-page` immediately after `errors-and-debugging`. Details follow below.

---

# 1. Verdict on roadmap v1

Findings are ordered by severity. There are no critical findings.

## Finding 1 — High: file literacy arrives after several tasks that require it

- **Repository path:** `course/data/curriculum.yaml`
- **Evidence:** The minimum path asks beginners to complete `first-agent-session`, `reviewing-agent-changes`, `testing-basics`, `errors-and-debugging`, and `project-personal-page` before taking `files-folders-paths`. Reviewing a diff and diagnosing an error require learners to recognize which file was changed and where it lives.
- **Why it matters:** This is the principal remaining sequencing problem. It makes “software literacy just in time” arrive one task too late: learners encounter files in the first build, but do not formally learn files and paths until after their first full project.
- **Concrete proposed change:** Move the existing lesson **`files-folders-paths`** from `software-literacy / files-and-projects` into `direct-and-check / inspect-results`, immediately before **`reviewing-agent-changes`**. Move its existing minimum-path occurrence to that same position. Do not rename or duplicate the ID.
- **Validity:** `files-folders-paths` remains a core lesson, appears once in the curriculum and once in `minimum_path`, and remains in course order.

## Finding 2 — Medium: the office project lacks the data-format bridge proposed in its own learning progression

- **Repository path:** `course/data/curriculum.yaml`
- **Evidence:** `project-office-automation` asks learners to turn spreadsheet data into a checked report, potentially through Python under `docs/decisions/007-roadmap-v1.md`, but `data-formats` is not on the minimum path. The path therefore goes from files/Git and AI mental models directly to a 90-minute data project.
- **Why it matters:** Beginners do not need a full programming prerequisite, but they should be able to recognize rows, columns, CSV, and structured output before supervising a spreadsheet-to-report transformation. Otherwise, checking the input and output risks becoming superficial.
- **Concrete proposed change:** Add the existing core lesson **`data-formats`** to `minimum_path`, in its existing curriculum position after `project-personal-page` and before `git-version-control`. If Finding 1 is applied, `files-folders-paths` will already have moved earlier.
- **Validity:** `data-formats` is already in a core unit. Adding it once in course order produces a valid 19-lesson minimum path totaling **347 minutes**.

## Finding 3 — Medium: all three versions state the LLM/tool boundary too absolutely

- **Repository paths:** `course/vi/lessons/agent-parts-and-loop.md`, `course/en/lessons/agent-parts-and-loop.md`, `course/ja/lessons/agent-parts-and-loop.md`
- **Evidence:** The Vietnamese version says an LLM “chỉ viết ra chữ”; English says it “only writes text”; Japanese says it “文字を書くことしかできません.” The same section says the LLM chooses the tool.
- **What is wrong:** This is a useful beginner simplification, but it is stated as a universal fact. Modern models can produce structured outputs and tool-call requests, and some harnesses—not exclusively the model—constrain, route, approve, or select available actions. The important distinction is that **model output is not itself the external action**.
- **Concrete proposed change:** In all three language files, replace the absolute claim with the equivalent of:

  > An LLM produces an output such as text or a structured tool request; the surrounding agent software decides what requests are allowed and executes the approved tool.

  Also change “the LLM chooses the tool” to “the model may request a tool from those the harness makes available.”
- **Curriculum effect:** None; lesson IDs, type, time, track, and minimum path remain unchanged.

## Finding 4 — Medium: one diagram promises planning and self-checking without the lesson’s caveat

- **Repository path:** `course/data/diagrams/ai-three-levels.yaml`
- **Evidence:** The AI-agent column says “Plans, acts, checks its own work” and its Vietnamese and Japanese equivalents. Unlike the prose in `chatbot-to-agent`, the image does not say that these abilities depend on the available tools, permissions, feedback, and checks.
- **Why it matters:** Under ADR 008, the visuals are reused as memory aids and Facebook assets. A learner may encounter this image without the surrounding caveat and infer that self-checking is inherent in every product called an agent.
- **Concrete proposed change:** Change that cell in all three languages to a conditional description such as **“Can plan and act; checks when tools allow”**, with equivalent concise Vietnamese and Japanese text. Keep the diagram ID and template unchanged.
- **Curriculum effect:** None.

## Finding 5 — Low: the English and Japanese birthday examples have not localized the Vietnamese name

- **Repository paths:** `course/en/lessons/chatbot-to-agent.md`, `course/ja/lessons/chatbot-to-agent.md`
- **Evidence:** Both localized lessons retain the Vietnamese example name “An”; the English lesson says “for An,” while Japanese transliterates it as “アンちゃん.” `docs/content-guide.md` says each language should localize names, places, money, workplace habits, and idioms rather than translate mechanically.
- **Cultural assessment:** Nothing about the example is offensive or implausible. This is a small localization inconsistency, not a major cultural misfit. Money and the quiz’s translation-language option were localized correctly.
- **Concrete proposed change:** Keep **An** in Vietnamese; use a neutral English-local example such as **Alex** in `course/en/lessons/chatbot-to-agent.md`, and a natural Japanese example such as **あおいちゃん** in `course/ja/lessons/chatbot-to-agent.md`. The task, age, dinosaur theme, and verification requirements should remain identical.
- **Curriculum effect:** None.

---

# 2. The minimum-path order question

## Decision: agree with the owner

I **agree with keeping `project-personal-page` immediately after `errors-and-debugging`** on the minimum path, as decided in `docs/decisions/007-roadmap-v1.md`.

### Reasons

1. **It preserves the motivational promise of roadmap v1.**  
   The learner reaches a meaningful personal artifact after learning how to specify, review, test, and debug, rather than waiting through the software- and AI-foundation modules.

2. **It provides immediate transfer.**  
   `first-agent-session` is a tightly bounded one-file task card. `project-personal-page` is the first chance to apply the same supervision loop to a learner-chosen artifact.

3. **It gives the later Git lesson a concrete reason to exist.**  
   The learner has now made and manually protected something worth preserving. `git-version-control` can be introduced as a better replacement for copying folders rather than as abstract infrastructure.

4. **It follows the course order.**  
   The round-1 path placed the project later than its curriculum position. The implemented order resolves that inconsistency and satisfies the `minimum_path` invariant in `docs/data-model.md`.

5. **Moving `files-folders-paths` earlier solves the actual prerequisite issue without delaying the project.**  
   Learners need file orientation before reviewing changes, but they do not need the full software-literacy module before building a personal page.

I would therefore **not move `project-personal-page`**. I would move `files-folders-paths` forward instead.

---

# 3. Proposed `curriculum.yaml` edits

Apply these edits together:

## Edit A — Move `files-folders-paths`

Move:

- **ID:** `files-folders-paths`
- **From:** `software-literacy / files-and-projects`
- **To:** `direct-and-check / inspect-results`
- **Position:** immediately before `reviewing-agent-changes`
- **Keep:** type `hands-on`, time `10`, existing title and glossary term

This is a move, not a rename or a copy.

## Edit B — Add `data-formats` to `minimum_path`

Do not move or otherwise change `data-formats`. Add its existing ID to the minimum path at its course-order position.

## Resulting minimum path

1. `chatbot-to-agent`
2. `agent-parts-and-loop`
3. `watch-an-agent-build`
4. `choose-your-learning-setup`
5. `data-safety-and-permissions`
6. `first-agent-session`
7. `lead-not-typist`
8. `writing-good-specs`
9. `explore-plan-build-verify`
10. `files-folders-paths`
11. `reviewing-agent-changes`
12. `testing-basics`
13. `errors-and-debugging`
14. `project-personal-page`
15. `data-formats`
16. `git-version-control`
17. `hallucination`
18. `context-window`
19. `project-office-automation`

### Invariant check

This proposed list:

- contains **19 distinct lessons**;
- contains only lessons in core units;
- contains every ID once;
- follows the proposed course order;
- keeps `project-personal-page` directly after `errors-and-debugging`;
- totals **347 minutes**.

I do **not** recommend retyping, renaming, retiring, or re-timing any lesson before writing begins.

---

# 4. Pilot lesson review by language

## Vietnamese

### `chatbot-to-agent`

- **Repository path:** `course/vi/lessons/chatbot-to-agent.md`
- It follows the friendly `bạn` voice required by `docs/content-guide.md`.
- Its Vietnamese office examples—Excel files, đồng, and a familiar personal task—fit the intended audience.
- Its main distinction, “ai là người thực hiện các bước?”, remains consistent throughout the objective, explanation, exercise, recap, takeaways, and quiz.
- The tool-specific names are explicitly dated September 2026, satisfying the volatility rule.
- It correctly qualifies the agent’s ability to run and repair the page rather than promising autonomous success.
- I found **no Vietnamese mistranslation or cultural misfit**.
- The only related factual issue is in the following lesson and shared across languages, as described in Finding 3.

### `agent-parts-and-loop`

- **Repository path:** `course/vi/lessons/agent-parts-and-loop.md`
- The lesson cleanly contains the material split out of `chatbot-to-agent`.
- The cooking analogy states where it breaks down, satisfying `docs/content-guide.md`.
- The photo-renaming example demonstrates observation, an escalation to the human, verification, and a stopping condition.
- **Correction required:** replace “mô hình ngôn ngữ chỉ sinh ra chữ” and “LLM chọn công cụ” with the more accurate model-output/tool-request wording in Finding 3.
- I found **no other wrong fact or cultural misfit**.

## English

### `chatbot-to-agent`

- **Repository path:** `course/en/lessons/chatbot-to-agent.md`
- The prose is plain, direct, and broadly within the B1–B2 intent.
- Currency and the quiz’s language option are appropriately localized.
- The safety and verification meaning matches the Vietnamese source.
- **Localization correction:** replace the inherited name “An” with a natural English-local example name, while preserving the same task and difficulty.
- I found **no substantive mistranslation**.

### `agent-parts-and-loop`

- **Repository path:** `course/en/lessons/agent-parts-and-loop.md`
- The objective, analogy, example, quiz, and diagrams preserve the Vietnamese lesson’s meaning.
- “When a decision is yours” is clear and natural English.
- **Factual correction required:** change “The LLM … only writes text” and “The LLM chooses a tool” as described in Finding 3.
- I found **no English cultural misfit**.

## Japanese

### `chatbot-to-agent`

- **Repository path:** `course/ja/lessons/chatbot-to-agent.md`
- It consistently uses polite です・ます style and Japanese punctuation.
- Yen and the quiz’s translation option are localized correctly.
- `検収` is formal, but it is appropriate for the intended workplace-oriented Japanese audience and is explained by the surrounding context.
- **Localization correction:** replace `アンちゃん`, which reads as a transliteration of the Vietnamese source name, with a natural Japanese example such as `あおいちゃん`.
- I found **no substantive mistranslation or harmful cultural assumption**.

### `agent-parts-and-loop`

- **Repository path:** `course/ja/lessons/agent-parts-and-loop.md`
- The cooking analogy reads naturally in Japanese.
- The photo example does not depend on a specifically Vietnamese practice and transfers cleanly.
- The distinction between agent permissions and human authority is preserved.
- **Factual correction required:** revise `言語モデルが生み出すのは文字だけ` and `ツールを選ぶのはLLM` as described in Finding 3.
- I found **no other mistranslation or cultural misfit**.

## ADR 008 compliance

Both pilots comply with `docs/decisions/008-a-recap-infographic-in-every-lesson.md` in Vietnamese, English, and Japanese:

- each contains a `recap` section immediately before `takeaways`;
- each recap contains exactly one lesson-specific infographic;
- the recap image is not reused elsewhere in that lesson;
- the three language versions use the same diagrams in aligned sections;
- both recap specs use the `summary` template;
- validation reports no diagram or lesson-structure warning.

The two explanatory diagrams plus one recap diagram per pilot are reasonable after the original lesson was split. I do not recommend removing them.

---

# 5. Evidence

The implementation reflects the accepted round-1 direction:

- `course/data/curriculum.yaml` has six modules, seventeen units, fifty-two active lessons, unit tracks, an ordered minimum path, and nine retired IDs.
- `docs/decisions/007-roadmap-v1.md` records the four owner decisions and explicitly explains the placement of `project-personal-page`.
- `docs/decisions/008-a-recap-infographic-in-every-lesson.md` requires an independent recap visual in every review-ready lesson.
- `brainstorm/round-1.md` records the validation of all original IDs, the corrected 337-minute total, and how the owner’s decisions were applied.
- `course/data/sections.yaml` places `recap` before `takeaways` and requires it for every lesson type.
- `docs/data-model.md` requires a minimum path containing core lessons only, once each, in course order.
- `docs/content-guide.md` establishes one idea per lesson, localize-don’t-translate, dated volatile details, agent safety, human verification, and recap requirements.

---

# 6. Changed files

**None.**

This was a read-only brainstorm under `write_policy: none`. I did not edit files, create a commit, create a branch, push anything, or open a pull request.

---

# 7. Tests performed

- ✅ `git rev-parse HEAD` — confirmed the checkout is exactly `44c7fb8b44064be2f0b648937861e1eed00a1e88`.
- ✅ `git show -s --format='%H %s' 44c7fb8b44064be2f0b648937861e1eed00a1e88` — confirmed the requested commit exists.
- ✅ `python -m pip install -r requirements-eval.txt -q` — installed the declared evaluation dependencies.
- ✅ `python -m src.main validate` — `Content store OK`; 6 lesson files checked and 0 warnings.
- ✅ `python -m src.main stats` — confirmed 6 modules, 17 units, 52 lessons, 893 total minutes, and an 18-lesson/337-minute current minimum path.
- ✅ `python -m pytest -q` — completed successfully.
- ✅ `git diff --check` — no whitespace errors.
- ✅ `git status --short` — no repository changes were produced.
- ✅ Manual parity review of `course/vi/lessons/chatbot-to-agent.md`, `course/en/lessons/chatbot-to-agent.md`, and `course/ja/lessons/chatbot-to-agent.md`.
- ✅ Manual parity review of `course/vi/lessons/agent-parts-and-loop.md`, `course/en/lessons/agent-parts-and-loop.md`, and `course/ja/lessons/agent-parts-and-loop.md`.
- ✅ Manual review of the six associated specs under `course/data/diagrams/` against ADR 008 and `docs/content-guide.md`.

---

# 8. Remaining risks and open questions

1. **The first-session environment remains the largest delivery risk.**  
   `choose-your-learning-setup` and `first-agent-session` still need to prove that the browser, personal-PC, and watch-only routes lead to comparable learning outcomes.

2. **The office project may hide operational prerequisites.**  
   Adding `data-formats` helps, but the project lesson must still provide starter data, a known-good result, a Python route that does not require the learner to author Python, and the promised spreadsheet-only alternative.

3. **A dedicated folder is a boundary, not a sandbox.**  
   The practical lessons must explain that an agent or subprocess may still access data outside that folder unless the tool genuinely enforces isolation.

4. **Japanese publication should continue to follow the owner’s staged decision.**  
   The present Japanese pilots are strong enough for review, but the remaining Japanese lessons should wait for feedback on the Vietnamese minimum-path pilot, as recorded in `docs/decisions/007-roadmap-v1.md`.

5. **ADR 008 has a real production cost.**  
   Fifty-two recap infographics across a trilingual course are manageable only if the author reuses a disciplined visual vocabulary and reviews all three generated SVGs before each lesson advances.

### Questions for the owner

- Should `files-folders-paths` be moved into `inspect-results`, or should a smaller new file-orientation lesson be created? I recommend moving the existing ID to avoid duplication.
- Should `data-formats` become minimum-path lesson 15? I recommend yes.
- Who will perform the required native-level review of the Japanese pilots before they move from `review` to `done`?
- Which exact synthetic spreadsheet and expected totals will become the stable fixture for `project-office-automation`?

---

# 9. Recommended next action

Before writing `watch-an-agent-build`:

1. Apply the two `curriculum.yaml` changes:
   - move `files-folders-paths` before `reviewing-agent-changes`;
   - add `data-formats` to the minimum path.
2. Rebuild generated course pages and confirm that the resulting 19-lesson minimum path has 347 minutes.
3. Correct the LLM/tool-boundary wording in all three versions of `agent-parts-and-loop`.
4. Correct the conditional self-check wording in `course/data/diagrams/ai-three-levels.yaml`.
5. Localize the example names in the English and Japanese `chatbot-to-agent` files.
6. Have a native Japanese reviewer read both pilot lessons.
7. Freeze the opening six lessons’ shared scenario, safety boundary, and evidence format before producing further lessons.

# Tóm tắt
Lộ trình v1 đã đủ vững để làm nền sản xuất, nhưng nên sửa hai điểm thứ tự trước khi viết tiếp.  
Nên chuyển `files-folders-paths` lên trước `reviewing-agent-changes` và thêm `data-formats` vào lộ trình tối thiểu.  
Tôi đồng ý giữ `project-personal-page` ngay sau `errors-and-debugging` vì đây là chi���n thắng sớm có ý nghĩa.  
Ba bản ngôn ngữ của hai bài thử nhìn chung đồng nhất; cần sửa cách nói tuyệt đối về LLM và bản địa hóa tên ví dụ.  
Sau các sửa đổi, lộ trình tối thiểu sẽ có 19 bài, 347 phút và vẫn hợp lệ theo `docs/data-model.md`.

 [View task →](https://chatgpt.com/s/cd_6ab84eb891b48191a494b7f580e77ef1)
