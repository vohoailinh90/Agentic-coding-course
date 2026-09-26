# Claude Code Web — Blind Eval v2

Use **two separate Claude Code Web tasks/sessions**. Do not combine classification and scoring in one task.

## Task 1 — blind classification

Copy this prompt into a fresh Claude Code Web task:

```text
Run the BLIND CLASSIFICATION PHASE for all cases in evals/routing-cases.yaml.

Hard constraints:
- Do not read, open, search, grep, or inspect evals/expected-routing.yaml.
- Do not inspect evals/results/.
- Do not inspect git history, prior commits, or diffs for old expected labels.
- Do not inspect requirements/examples/*.md; use the requirement text embedded
  in evals/routing-cases.yaml directly.
- Use only each requirement, .claude/skills/classify-requirement/SKILL.md,
  agent-routing/complexity-rubric.md, agent-routing/policy.yaml, and genuinely
  relevant code context if a case needs it.
- Run scripts/route.py to resolve the policy from your scores and signals, as
  the skill instructs. Never pass --record: this is classification, not execution.
- Do not implement any requirement and do not spawn the recommended execution agents.
- Classify each case independently.

For every case, record:
- classification dimensions
- raw_score
- signals
- score_tier
- overrides_applied
- final_tier
- strategy
- required_agents
- parallelizable
- human_gate

Write the frozen actual classifications to:
  evals/results/web-actual-routing-v2.yaml

Do not compare against any expected values. Stop after writing the actual-results file.
```

Before accepting the run as blind, verify the task transcript contains no access to `evals/expected-routing.yaml`, previous result files, or git history.

## Task 2 — oracle scoring

After Task 1 is fully complete, start a **new** Claude Code Web task and copy this prompt:

```text
Score the frozen blind-routing results in:
  evals/results/web-actual-routing-v2.yaml

against the evaluator oracle in:
  evals/expected-routing.yaml

Do not re-run or revise any classifications.

For each case compare:
- final tier
- strategy
- required agent set
- parallelizable
- human gate

Treat raw score, dimensions, and signals as diagnostic metrics rather than route-pass criteria.

Report:
- route accuracy
- tier accuracy
- strategy accuracy
- agent-set accuracy
- parallelizable accuracy
- human-gate accuracy
- raw-score exact match
- dimensions exact match
- signals exact match
- over-routing count
- under-routing count

Also list every mismatch with expected vs actual and a short diagnosis.
```

## Stability runs

For a stronger baseline, run Task 1 in five fresh tasks/sessions and save the outputs as:

```text
evals/results/web-actual-routing-v2-run1.yaml
...
evals/results/web-actual-routing-v2-run5.yaml
```

Then use one separate scoring task to compute per-case tier stability and mean tier stability across the five independent runs.

A single session repeating the same case five times is weaker evidence because earlier classifications can anchor later ones.
