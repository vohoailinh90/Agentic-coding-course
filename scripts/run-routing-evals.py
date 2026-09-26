#!/usr/bin/env python3
"""Run blind Claude Code routing evaluations.

Phase 1 classifies every selected requirement without loading the evaluator oracle.
Phase 2 loads evals/expected-routing.yaml and scores the frozen classifications.
Claude subprocess output is decoded explicitly as UTF-8 for Windows locales.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print(
        "PyYAML is required. Install it with: python -m pip install -r requirements-eval.txt",
        file=sys.stderr,
    )
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "routing-cases.yaml"
EXPECTED_PATH = ROOT / "evals" / "expected-routing.yaml"
RESULTS_DIR = ROOT / "evals" / "results"
ROUTE_PATH = ROOT / "scripts" / "route.py"
POLICY_PATH = ROOT / "agent-routing" / "policy.yaml"


def load_resolver():
    """scripts/route.py, the deterministic half of the classifier."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("route", ROUTE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {ROUTE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

AGENT_NAMES = [
    "requirement-analyst",
    "architect",
    "architecture-critic",
    "implementer",
    "code-reviewer",
    "code-reviewer-t3",
    "code-reviewer-verify",
    "test-engineer",
]

DIMENSION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ambiguity": {"type": "integer", "minimum": 0, "maximum": 2},
        "scope": {"type": "integer", "minimum": 0, "maximum": 2},
        "architecture": {"type": "integer", "minimum": 0, "maximum": 2},
        "dependencies": {"type": "integer", "minimum": 0, "maximum": 2},
        "risk": {"type": "integer", "minimum": 0, "maximum": 2},
        "verification": {"type": "integer", "minimum": 0, "maximum": 2},
    },
    "required": [
        "ambiguity",
        "scope",
        "architecture",
        "dependencies",
        "risk",
        "verification",
    ],
}

CLASSIFICATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "requirement_summary": {"type": "string"},
        "classification": DIMENSION_SCHEMA,
        "raw_score": {"type": "integer", "minimum": 0, "maximum": 12},
        "signals": {"type": "array", "items": {"type": "string"}},
        "score_tier": {"type": "string", "enum": ["T0", "T1", "T2", "T3"]},
        "overrides_applied": {"type": "array", "items": {"type": "string"}},
        "final_tier": {"type": "string", "enum": ["T0", "T1", "T2", "T3"]},
        "strategy": {
            "type": "string",
            "enum": [
                "main_session",
                "main_with_reviewer",
                "main_with_architect_and_reviewer",
                "main_with_critic_and_reviewer",
            ],
        },
        "required_agents": {
            "type": "array",
            "items": {"type": "string", "enum": AGENT_NAMES},
            "uniqueItems": True,
        },
        # 5 = T3 base ceiling (3) + analyst_reserve (1) + escalation_reserve (1),
        # the worst case where a requirement is both ambiguity-2 and later
        # found to need designed verification. See agent-routing/policy.yaml.
        "max_agent_invocations": {"type": "integer", "minimum": 0, "maximum": 5},
        "parallelizable": {"type": "boolean"},
        "human_gate": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "required": {"type": "boolean"},
                "reason": {"type": ["string", "null"]},
            },
            "required": ["required", "reason"],
        },
        "rationale": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "requirement_summary",
        "classification",
        "raw_score",
        "signals",
        "score_tier",
        "overrides_applied",
        "final_tier",
        "strategy",
        "required_agents",
        "max_agent_invocations",
        "parallelizable",
        "human_gate",
        "rationale",
    ],
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping in {path}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run blind routing eval cases through Claude Code, then score them against the oracle."
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Independent runs per case (default: 1). Use 5+ to measure stability.",
    )
    parser.add_argument(
        "--case",
        action="append",
        dest="cases",
        help="Only run this case id; repeat for multiple cases.",
    )
    parser.add_argument(
        "--model",
        help="Optional Claude Code model alias/full model name, e.g. sonnet or opus.",
    )
    parser.add_argument(
        "--claude-bin",
        default="claude",
        help="Claude Code executable (default: claude).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for each Claude invocation (default: 300).",
    )
    parser.add_argument(
        "--max-budget-usd",
        type=float,
        help="Optional Claude Code max budget per invocation.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Print the report without writing evals/results/*.json.",
    )
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be >= 1")
    if args.timeout < 1:
        parser.error("--timeout must be >= 1")
    return args


def build_prompt(case_id: str, requirement: str) -> str:
    return f"""Invoke the project skill /classify-requirement for the requirement below.
Follow agent-routing/complexity-rubric.md and agent-routing/policy.yaml exactly.
This is the BLIND CLASSIFICATION PHASE of an evaluation.
Do not use evals/expected-routing.yaml, previous eval results, git history, or prior expected labels.
Do not implement, modify files, or spawn the recommended implementation agents.
You may run scripts/route.py (read-only; never with --record) to resolve the policy from your scores and signals.
Return only the classification requested by the structured output schema.

Case: {case_id}
Requirement:
{requirement}
"""


def normalize(native: dict[str, Any]) -> dict[str, Any]:
    human_gate = native.get("human_gate") or {}
    return {
        "dimensions": native.get("classification"),
        "score": native.get("raw_score"),
        "signals": native.get("signals", []),
        "score_tier": native.get("score_tier"),
        "overrides_applied": native.get("overrides_applied", []),
        "tier": native.get("final_tier"),
        "strategy": native.get("strategy"),
        "required_agents": native.get("required_agents", []),
        "max_agent_invocations": native.get("max_agent_invocations"),
        "parallelizable": native.get("parallelizable"),
        "human_gate": human_gate.get("required") if isinstance(human_gate, dict) else None,
        "human_gate_reason": human_gate.get("reason") if isinstance(human_gate, dict) else None,
    }


def create_blind_workspace(destination: Path) -> Path:
    """Copy the project without evaluator-only data for classification."""

    workspace = destination / "project"

    def ignore(path: str, names: list[str]) -> set[str]:
        relative = Path(path).resolve().relative_to(ROOT)
        ignored: set[str] = set()
        if relative == Path("."):
            ignored.update({".git", "artifacts"})
        if relative == Path("evals"):
            ignored.update({"expected-routing.yaml", "results"})
        if relative == Path("requirements"):
            ignored.add("examples")
        return ignored.intersection(names)

    shutil.copytree(ROOT, workspace, ignore=ignore)
    return workspace


def run_claude(
    claude_bin: str,
    case_id: str,
    requirement: str,
    model: str | None,
    timeout: int,
    max_budget_usd: float | None,
    workspace: Path,
) -> dict[str, Any]:
    command = [
        claude_bin,
        "-p",
        build_prompt(case_id, requirement),
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(CLASSIFICATION_SCHEMA, separators=(",", ":")),
        "--no-session-persistence",
    ]
    if model:
        command.extend(["--model", model])
    if max_budget_usd is not None:
        command.extend(["--max-budget-usd", str(max_budget_usd)])

    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=workspace,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    duration_seconds = time.monotonic() - started

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    if completed.returncode != 0:
        raise RuntimeError(
            f"Claude exited {completed.returncode}. stderr={stderr.strip()!r} stdout={stdout.strip()!r}"
        )

    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Claude returned non-JSON output: {stdout!r}") from exc

    structured = envelope.get("structured_output")
    if not isinstance(structured, dict):
        result = envelope.get("result")
        if isinstance(result, str):
            try:
                structured = json.loads(result)
            except json.JSONDecodeError:
                structured = None

    if not isinstance(structured, dict):
        raise RuntimeError(
            "Claude response did not contain structured_output. "
            f"Available fields: {sorted(envelope.keys())}"
        )

    return {
        "native_classification": structured,
        "classification": normalize(structured),
        "total_cost_usd": envelope.get("total_cost_usd"),
        "duration_seconds": round(duration_seconds, 3),
        "session_id": envelope.get("session_id"),
        "usage": envelope.get("usage"),
    }


def budget_respected(actual: dict[str, Any]) -> bool:
    """A roster larger than its own declared ceiling is internally inconsistent.

    This check needs no oracle: it catches a classifier that names a budget and
    then routes past it, which is the failure mode the ceiling exists to stop.
    """

    budget = actual.get("max_agent_invocations")
    if not isinstance(budget, int):
        return False
    return len(actual.get("required_agents", [])) <= budget


ROUTE_DECISION_FIELDS = ("tier", "strategy", "required_agents", "max_agent_invocations", "human_gate")


def resolved_route(resolver, policy: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any] | None:
    """The route policy.yaml assigns to the classifier's OWN scores and signals.

    None when the emission cannot be resolved at all (a dimension outside 0-2,
    a missing field): that is a schema failure, and the structured-output
    schema should already have rejected it.
    """
    try:
        result = resolver.resolve(policy, actual.get("dimensions"), actual.get("signals", []))
    except resolver.RoutingError:
        return None
    return {
        "tier": result["final_tier"],
        "strategy": result["strategy"],
        "required_agents": result["required_agents"],
        "max_agent_invocations": result["max_agent_invocations"],
        "human_gate": result["human_gate"]["required"],
        "overrides_applied": result["overrides_applied"],
        "dropped_read_only_signals": result["dropped_read_only_signals"],
        "unknown_signals": result["unknown_signals"],
    }


def _same_decision(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for field in ROUTE_DECISION_FIELDS:
        a, b = left.get(field), right.get(field)
        if field == "required_agents":
            a, b = set(a or []), set(b or [])
        if a != b:
            return False
    return True


def resolver_checks(actual: dict[str, Any], expected: dict[str, Any], resolved: dict[str, Any] | None) -> dict[str, bool]:
    """Separate a policy-application error from a scoring error.

    `resolver_agrees`: the model routed its own scores the way policy.yaml does.
    `resolved_route_pass`: the route policy.yaml assigns to the model's scores
    matches the oracle — the scoring was right even if the model then applied
    the policy wrongly. The parallelizable judgement stays with the model.
    """
    if resolved is None:
        return {"resolver_agrees": False, "resolved_route_pass": False}
    return {
        "resolver_agrees": _same_decision(actual, resolved),
        "resolved_route_pass": (
            _same_decision(resolved, expected)
            and actual.get("parallelizable") == expected.get("parallelizable")
        ),
    }


def compare(actual: dict[str, Any], expected: dict[str, Any]) -> dict[str, bool]:
    checks = {
        "tier": actual.get("tier") == expected.get("tier"),
        "strategy": actual.get("strategy") == expected.get("strategy"),
        "agents": set(actual.get("required_agents", [])) == set(expected.get("required_agents", [])),
        "budget": actual.get("max_agent_invocations") == expected.get("max_agent_invocations"),
        "budget_not_exceeded": budget_respected(actual),
        "parallelizable": actual.get("parallelizable") == expected.get("parallelizable"),
        "human_gate": actual.get("human_gate") == expected.get("human_gate"),
        "score": actual.get("score") == expected.get("raw_score"),
        "dimensions": actual.get("dimensions") == expected.get("semantic_hints", {}),
        "signals": set(actual.get("signals", [])) == set(expected.get("signals", [])),
    }
    checks["route_pass"] = all(
        checks[name]
        for name in [
            "tier",
            "strategy",
            "agents",
            "budget",
            "budget_not_exceeded",
            "parallelizable",
            "human_gate",
        ]
    )
    return checks


def pct(numerator: int, denominator: int) -> float:
    return round((numerator / denominator * 100.0), 1) if denominator else 0.0


def main() -> int:
    args = parse_args()

    if shutil.which(args.claude_bin) is None:
        print(
            f"Claude Code executable not found: {args.claude_bin!r}. Install Claude Code and authenticate first.",
            file=sys.stderr,
        )
        return 2

    cases_doc = load_yaml(CASES_PATH)
    all_cases = cases_doc.get("cases", [])

    if args.cases:
        selected = set(args.cases)
        unknown = sorted(selected - {item["id"] for item in all_cases})
        if unknown:
            print(f"Unknown case id(s): {', '.join(unknown)}", file=sys.stderr)
            return 2
        all_cases = [item for item in all_cases if item["id"] in selected]

    print("Claude Agent Routing Eval v2 — BLIND")
    print("=" * 72)
    print(
        f"Cases: {len(all_cases)} | Runs/case: {args.runs} | Model: {args.model or 'Claude Code default'}"
    )
    print("Phase 1: classify without loading evaluator oracle")
    print()

    records: list[dict[str, Any]] = []
    execution_errors = 0

    # Phase 1: classify in a disposable copy where the oracle and previous
    # results do not exist. Prompt instructions alone do not guarantee blindness.
    with tempfile.TemporaryDirectory(prefix="routing-eval-blind-") as temp_dir:
        blind_workspace = create_blind_workspace(Path(temp_dir))
        for case in all_cases:
            case_id = case["id"]
            for run_number in range(1, args.runs + 1):
                try:
                    execution = run_claude(
                        args.claude_bin,
                        case_id,
                        case["requirement"],
                        args.model,
                        args.timeout,
                        args.max_budget_usd,
                        blind_workspace,
                    )
                    actual = execution["classification"]
                    cost = execution.get("total_cost_usd")
                    cost_text = f"${cost:.4f}" if isinstance(cost, (int, float)) else "n/a"
                    print(
                        f"{case_id} run={run_number:<2} CLASSIFIED tier={actual.get('tier')} "
                        f"cost={cost_text} time={execution['duration_seconds']:.1f}s"
                    )
                    records.append(
                        {
                            "id": case_id,
                            "run": run_number,
                            "requirement": case["requirement"],
                            "actual": actual,
                            **execution,
                        }
                    )
                except (RuntimeError, subprocess.TimeoutExpired) as exc:
                    execution_errors += 1
                    print(f"{case_id} run={run_number:<2} ERROR {exc}", file=sys.stderr)
                    records.append(
                        {
                            "id": case_id,
                            "run": run_number,
                            "requirement": case["requirement"],
                            "error": str(exc),
                        }
                    )

    # Phase 2: classifications are now frozen. Only now load the oracle.
    expected_doc = load_yaml(EXPECTED_PATH)
    expected_by_id = {item["id"]: item for item in expected_doc.get("expected", [])}
    resolver = load_resolver()
    policy = resolver.load_policy(POLICY_PATH)

    print()
    print("Phase 2: score frozen classifications against evaluator oracle")
    print("-" * 72)

    route_failures = 0
    for record in records:
        if "actual" not in record:
            continue
        expected = expected_by_id.get(record["id"])
        if expected is None:
            print(f"{record['id']}: missing oracle entry", file=sys.stderr)
            return 2
        checks = compare(record["actual"], expected)
        resolved = resolved_route(resolver, policy, record["actual"])
        checks.update(resolver_checks(record["actual"], expected, resolved))
        record["expected"] = expected
        record["resolved"] = resolved
        record["checks"] = checks
        status = "PASS" if checks["route_pass"] else "FAIL"
        if not checks["route_pass"]:
            route_failures += 1
        note = "" if checks["resolver_agrees"] else " (policy misapplied: resolver disagrees)"
        print(
            f"{record['id']} run={record['run']:<2} {status:<4} "
            f"expected={expected['tier']} actual={record['actual'].get('tier')}"
            f"{note}"
        )

    successful = [record for record in records if "checks" in record]
    total = len(successful)
    metric_names = [
        "route_pass",
        "tier",
        "strategy",
        "agents",
        "budget",
        "budget_not_exceeded",
        "parallelizable",
        "human_gate",
        "score",
        "dimensions",
        "signals",
        "resolver_agrees",
        "resolved_route_pass",
    ]
    metrics = {
        name: pct(sum(1 for record in successful if record["checks"][name]), total)
        for name in metric_names
    }

    tier_stability: dict[str, float] = {}
    grouped_tiers: dict[str, list[str]] = defaultdict(list)
    for record in successful:
        grouped_tiers[record["id"]].append(record["actual"].get("tier"))
    for case_id, tiers in grouped_tiers.items():
        tier_stability[case_id] = pct(Counter(tiers).most_common(1)[0][1], len(tiers))

    # Over-routing is measured on the ROSTER, not on the declared ceiling.
    # Comparing ceilings measures nothing: the ceiling is a function of the
    # tier, so any correctly tiered run reports a zero delta whether its roster
    # holds one agent or six. Roster size is what the classifier actually
    # chooses, so that is what can be over-routed. Neither figure is a token
    # measurement — this runner classifies and never executes the routed
    # profile, so it reports roles requested, not context or tokens spent.
    expected_rosters = [len(record["expected"]["required_agents"]) for record in successful]
    actual_rosters = [len(record["actual"].get("required_agents", [])) for record in successful]
    over_routing = [
        len(record["actual"].get("required_agents", []))
        - len(record["expected"]["required_agents"])
        for record in successful
    ]

    costs = [
        float(record["total_cost_usd"])
        for record in successful
        if isinstance(record.get("total_cost_usd"), (int, float))
    ]
    durations = [float(record["duration_seconds"]) for record in successful]

    print()
    print("Summary")
    print("-" * 72)
    print(f"Route accuracy:          {metrics['route_pass']:6.1f}%")
    print(f"  resolved from scores:  {metrics['resolved_route_pass']:6.1f}%  (policy applied by scripts/route.py)")
    print(f"  policy self-applied OK:{metrics['resolver_agrees']:6.1f}%  (model's route == resolver's route)")
    print(f"Tier accuracy:           {metrics['tier']:6.1f}%")
    print(f"Strategy accuracy:       {metrics['strategy']:6.1f}%")
    print(f"Agent-set accuracy:      {metrics['agents']:6.1f}%")
    print(f"Parallelizable accuracy: {metrics['parallelizable']:6.1f}%")
    print(f"Human-gate accuracy:     {metrics['human_gate']:6.1f}%")
    print(f"Agent-budget accuracy:   {metrics['budget']:6.1f}%")
    print(f"Budget self-consistency: {metrics['budget_not_exceeded']:6.1f}%")
    print(f"Raw-score exact match:   {metrics['score']:6.1f}%")
    print(f"Dimensions exact match:  {metrics['dimensions']:6.1f}%")
    print(f"Signals exact match:     {metrics['signals']:6.1f}%")
    if args.runs > 1 and tier_stability:
        print(f"Mean tier stability:     {statistics.mean(tier_stability.values()):6.1f}%")
    if actual_rosters:
        print(
            f"Mean roster size:        {statistics.mean(actual_rosters):6.2f} "
            f"(oracle {statistics.mean(expected_rosters):.2f})"
        )
    if over_routing:
        print(
            f"Over-routing (roles):    {sum(over_routing):+d} roles across "
            f"{len(over_routing)} runs; {sum(1 for d in over_routing if d > 0)} over, "
            f"{sum(1 for d in over_routing if d < 0)} under"
        )
        print("  (roles requested, not tokens: the runner does not execute the profile)")
    if costs:
        print(f"Total estimated cost:    ${sum(costs):.4f}")
        print(f"Average cost/run:        ${statistics.mean(costs):.4f}")
    if durations:
        print(f"Average duration/run:    {statistics.mean(durations):.1f}s")

    report = {
        "eval_version": 2,
        "blind": True,
        "oracle_loaded_after_classification": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runner": "scripts/run-routing-evals.py",
        "cases": len(all_cases),
        "runs_per_case": args.runs,
        "model": args.model,
        "metrics": metrics,
        "tier_stability": tier_stability,
        "execution_errors": execution_errors,
        "route_failures": route_failures,
        "mean_roster_size_actual": (
            round(statistics.mean(actual_rosters), 3) if actual_rosters else None
        ),
        "mean_roster_size_expected": (
            round(statistics.mean(expected_rosters), 3) if expected_rosters else None
        ),
        "over_routing_role_delta": sum(over_routing) if over_routing else 0,
        "over_routing_is_token_measurement": False,
        "total_estimated_cost_usd": round(sum(costs), 6) if costs else None,
        "average_cost_usd": round(statistics.mean(costs), 6) if costs else None,
        "average_duration_seconds": round(statistics.mean(durations), 3) if durations else None,
        "records": records,
    }

    if not args.no_save:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = RESULTS_DIR / f"routing-eval-v2-{stamp}.json"
        output_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"\nSaved: {output_path.relative_to(ROOT)}")

    return 1 if (execution_errors or route_failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
