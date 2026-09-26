#!/usr/bin/env python3
"""Resolve a routing decision deterministically from scores and signals.

The classifier's job is probabilistic: read a requirement, score six
dimensions 0-2, and name the actions the change performs. Everything after
that — the raw score, the score tier, dropping read-only signals, matching
overrides, choosing the profile, firing conditional agents, and adding up the
budget — is a pure function of `agent-routing/policy.yaml`. A model applying
those rules by hand can misread them; this script cannot. See *Deterministic
work is not agent work* in CLAUDE.md.

    python3 scripts/route.py --dimensions 1,1,1,1,2,2 --signals changes-schema,runs-backfill
    python3 scripts/route.py --dimensions ambiguity=2 scope=2 ... --signal moves-money
    python3 scripts/route.py --from classification.yaml          # dimensions+signals from a file
    python3 scripts/route.py --from classification.yaml --check  # diff the file's route against policy
    python3 scripts/route.py ... --record --requirement REQ-007  # also write the agent-budget ledger

The output carries only what the policy decides. `parallelizable` is a
judgement the policy leaves to the session, so it is not emitted here.

Exit codes: 0 resolved (or `--check` agrees), 1 `--check` found a mismatch,
2 the input or the policy could not be used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only where PyYAML is absent
    print(
        "PyYAML is required. Install it with: python -m pip install -r requirements-eval.txt",
        file=sys.stderr,
    )
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "agent-routing" / "policy.yaml"

DIMENSION_CONDITION = re.compile(r"^when_(?P<dimension>[a-z_]+)_dimension_at_least$")
RESERVE_CONDITION = re.compile(r"^(?P<dimension>[a-z_]+)_dimension_at_least_(?P<threshold>\d+)$")
# A reserve whose grant_condition is not a dimension threshold must name one of
# these runtime findings. Anything else is rejected rather than quietly treated
# as runtime: a misspelt threshold would otherwise stop granting at
# classification time and become grantable by hand, with routing still green.
RUNTIME_GRANT_CONDITIONS = {"reviewer_formally_escalated_for_verification_design"}

# The deterministic fields of a classification: what `--check` recomputes and
# what the eval runner compares against the model's own emission.
ROUTE_FIELDS = (
    "raw_score",
    "score_tier",
    "overrides_applied",
    "final_tier",
    "strategy",
    "required_agents",
    "max_agent_invocations",
    "human_gate",
)


class RoutingError(ValueError):
    """The input or the policy cannot produce a route."""


# ---------------------------------------------------------------------------
# Policy access
# ---------------------------------------------------------------------------


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        policy = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RoutingError(f"cannot read policy {path}: {exc}") from exc
    if not isinstance(policy, dict):
        raise RoutingError(f"policy {path} is not a mapping")
    for key in ("scoring", "score_tiers", "profiles", "budget", "overrides", "signal_taxonomy"):
        if key not in policy:
            raise RoutingError(f"policy is missing `{key}`")
    return policy


def tier_order(policy: dict[str, Any]) -> list[str]:
    """Tier names from lowest to highest, by their score band."""
    bands = sorted(policy["score_tiers"], key=lambda band: band["min_score"])
    return [band["tier"] for band in bands]


def tier_rank(policy: dict[str, Any], tier: str) -> int:
    order = tier_order(policy)
    if tier not in order:
        raise RoutingError(f"unknown tier {tier!r}; policy defines {order}")
    return order.index(tier)


def highest_tier(policy: dict[str, Any], tiers: list[str]) -> str:
    return max(tiers, key=lambda tier: tier_rank(policy, tier))


def signal_vocabulary(policy: dict[str, Any]) -> set[str]:
    """Every signal name the policy can act on, plus the exempt reads it drops."""
    vocabulary: set[str] = set(policy["signal_taxonomy"].get("read_only_exempt", []))
    for override in policy["overrides"]:
        vocabulary.update(override.get("match_any_signal", []))
        vocabulary.update(override.get("match_all_signals", []))
    for profile in policy["profiles"].values():
        for entry in profile.get("conditional_agents", []):
            vocabulary.update(entry.get("when_any_signal", []))
    return vocabulary


def reserves(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Every `*_reserve` block under budget, keyed by name."""
    return {
        name: block
        for name, block in policy["budget"].items()
        if name.endswith("_reserve") and isinstance(block, dict) and "grantable_agents" in block
    }


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def validate_dimensions(policy: dict[str, Any], dimensions: Any) -> dict[str, int]:
    names = list(policy["scoring"]["dimensions"])
    allowed = set(policy["scoring"]["allowed_values"])
    if not isinstance(dimensions, dict):
        raise RoutingError("dimensions must be a mapping of dimension name to score")
    missing = [name for name in names if name not in dimensions]
    extra = sorted(set(dimensions) - set(names))
    if missing or extra:
        problem = []
        if missing:
            problem.append(f"missing {missing}")
        if extra:
            problem.append(f"unknown {extra}")
        raise RoutingError(f"dimensions {', '.join(problem)}; expected exactly {names}")
    scored: dict[str, int] = {}
    for name in names:
        value = dimensions[name]
        # bool is an int subclass; True scoring as 1 would be a silent lie.
        if isinstance(value, bool) or not isinstance(value, int) or value not in allowed:
            raise RoutingError(f"{name} must be one of {sorted(allowed)}, got {value!r}")
        scored[name] = value
    return scored


def validate_signals(signals: Any) -> list[str]:
    if signals is None:
        return []
    if isinstance(signals, str):
        signals = [signals]
    if not isinstance(signals, (list, tuple)):
        raise RoutingError("signals must be a list of strings")
    cleaned: list[str] = []
    for signal in signals:
        if not isinstance(signal, str) or not signal.strip():
            raise RoutingError(f"signal {signal!r} is not a non-empty string")
        name = signal.strip()
        if name not in cleaned:
            cleaned.append(name)
    return cleaned


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def score_tier_for(policy: dict[str, Any], raw_score: int) -> str:
    for band in policy["score_tiers"]:
        if band["min_score"] <= raw_score <= band["max_score"]:
            return band["tier"]
    raise RoutingError(f"raw score {raw_score} falls in no score band")


def matching_overrides(policy: dict[str, Any], signals: list[str]) -> list[dict[str, Any]]:
    present = set(signals)
    matched = []
    for override in policy["overrides"]:
        any_of = set(override.get("match_any_signal", []))
        all_of = set(override.get("match_all_signals", []))
        if not any_of and not all_of:
            raise RoutingError(f"override {override.get('id')!r} has no signal condition")
        if any_of and not (any_of & present):
            continue
        if all_of and not (all_of <= present):
            continue
        matched.append(override)
    return matched


def conditional_reason(entry: dict[str, Any], dimensions: dict[str, int], signals: list[str]) -> str | None:
    """Why a conditional_agents entry fires, or None when it does not.

    Each entry is one arm. An entry carrying both a threshold and a signal list
    would read ambiguously as AND, so it is rejected rather than guessed at.
    """
    reasons: list[str] = []
    for key, value in entry.items():
        match = DIMENSION_CONDITION.match(key)
        if match:
            dimension = match.group("dimension")
            if dimension not in dimensions:
                raise RoutingError(f"conditional agent {entry.get('agent')!r} tests unknown dimension {dimension!r}")
            if not isinstance(value, int) or isinstance(value, bool):
                raise RoutingError(f"{key} must be an integer threshold")
            if dimensions[dimension] >= value:
                reasons.append(f"{dimension} {dimensions[dimension]} >= {value}")
            else:
                return None
        elif key == "when_any_signal":
            hit = [signal for signal in value if signal in signals]
            if hit:
                reasons.append(f"signal {hit[0]}")
            else:
                return None
    if not reasons:
        raise RoutingError(f"conditional agent {entry.get('agent')!r} has no machine-checkable condition")
    if len(reasons) > 1:
        raise RoutingError(
            f"conditional agent {entry.get('agent')!r} combines several conditions in one entry; "
            "split them into independent arms"
        )
    return reasons[0]


def reserve_grants(
    policy: dict[str, Any],
    tier: str,
    dimensions: dict[str, int],
    fired: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Reserves granted now, and reserves that only a later runtime finding can grant.

    A reserve is classification-time when its grant condition is a dimension
    threshold the scores already answer AND a fired conditional agent is one it
    may pay for. `escalation_reserve` names `test-engineer`, which no profile
    fires conditionally, and a condition only a reviewer can raise — so it is
    reported as available, never added to the ceiling here.
    """
    granted: list[dict[str, Any]] = []
    runtime: list[dict[str, Any]] = []
    fired_agents = [item["agent"] for item in fired]
    for name, block in reserves(policy).items():
        amount = block.get(tier)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            continue
        grantable = list(block.get("grantable_agents", []))
        condition = str(block.get("grant_condition", ""))
        match = RESERVE_CONDITION.match(condition)
        summary = {"reserve": name, "amount": amount, "grantable_agents": grantable, "grant_condition": condition}
        if match is None:
            if condition not in RUNTIME_GRANT_CONDITIONS:
                raise RoutingError(
                    f"{name}.grant_condition {condition!r} is neither a dimension threshold "
                    f"(<dimension>_dimension_at_least_<n>) nor a known runtime condition {sorted(RUNTIME_GRANT_CONDITIONS)}"
                )
            runtime.append(summary)
            continue
        dimension, threshold = match.group("dimension"), int(match.group("threshold"))
        if dimension not in dimensions:
            raise RoutingError(f"{name} tests unknown dimension {dimension!r}")
        payable = [agent for agent in grantable if agent in fired_agents]
        if dimensions[dimension] >= threshold and payable:
            granted.append({**summary, "agent": payable[0]})
    return granted, runtime


def resolve(policy: dict[str, Any], dimensions: Any, signals: Any) -> dict[str, Any]:
    """The routing decision policy.yaml makes for these scores and signals."""
    scored = validate_dimensions(policy, dimensions)
    emitted = validate_signals(signals)

    exempt = set(policy["signal_taxonomy"].get("read_only_exempt", []))
    dropped = [signal for signal in emitted if signal in exempt]
    effective = [signal for signal in emitted if signal not in exempt]
    vocabulary = signal_vocabulary(policy)
    unknown = [signal for signal in effective if signal not in vocabulary]

    raw_score = sum(scored.values())
    score_tier = score_tier_for(policy, raw_score)

    overrides = matching_overrides(policy, effective)
    candidates = [score_tier] + [override["minimum_tier"] for override in overrides]
    final_tier = highest_tier(policy, candidates)

    profile = policy["profiles"].get(final_tier)
    if profile is None:
        raise RoutingError(f"policy has no profile for {final_tier}")

    fired: list[dict[str, Any]] = []
    for entry in profile.get("conditional_agents", []):
        reason = conditional_reason(entry, scored, effective)
        if reason is None:
            continue
        if any(item["agent"] == entry["agent"] for item in fired):
            continue  # a second arm of an agent that already fired adds nothing
        fired.append({"agent": entry["agent"], "because": reason})

    required: list[str] = []
    for agent in [item["agent"] for item in fired] + list(profile.get("required_agents", [])):
        if agent not in required:
            required.append(agent)
    for override in overrides:
        for agent in override.get("require_agents", []):
            if agent not in required:
                required.append(agent)

    ceilings = policy["budget"]["max_agent_invocations"]
    if final_tier not in ceilings:
        raise RoutingError(f"budget.max_agent_invocations has no entry for {final_tier}")
    base = int(ceilings[final_tier])
    granted, runtime = reserve_grants(policy, final_tier, scored, fired)
    ceiling = base + sum(item["amount"] for item in granted)
    if len(required) > ceiling:
        raise RoutingError(
            f"{final_tier} requires {required} but its ceiling is {ceiling}; the policy is inconsistent"
        )

    gated = [override for override in overrides if override.get("human_gate") is True]
    human_gate = {
        "required": bool(gated),
        "reason": "; ".join(
            str(override.get("human_gate_reason") or override.get("id")) for override in gated
        )
        or None,
    }

    return {
        "dimensions": scored,
        "raw_score": raw_score,
        "score_tier": score_tier,
        "signals": effective,
        "dropped_read_only_signals": dropped,
        "unknown_signals": unknown,
        "overrides_applied": [override["id"] for override in overrides],
        "final_tier": final_tier,
        "strategy": profile["strategy"],
        "required_agents": required,
        "conditional_agents_fired": fired,
        "max_agent_invocations": ceiling,
        "budget": {
            "base": base,
            "reserves_granted": granted,
            "runtime_reserves": runtime,
        },
        "human_gate": human_gate,
    }


# ---------------------------------------------------------------------------
# Checking an emitted classification
# ---------------------------------------------------------------------------


def classification_inputs(document: dict[str, Any]) -> tuple[Any, Any]:
    """The probabilistic half of a classification document: scores and signals."""
    dimensions = document.get("classification", document.get("dimensions"))
    if dimensions is None:
        raise RoutingError("document has no `classification` (or `dimensions`) mapping")
    return dimensions, document.get("signals", [])


def _emitted(document: dict[str, Any], field: str) -> Any:
    aliases = {"final_tier": ("final_tier", "tier"), "raw_score": ("raw_score", "score")}
    for key in aliases.get(field, (field,)):
        if key in document:
            return document[key]
    return None


def check(policy: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    """Recompute the deterministic fields of an emitted classification and diff them.

    Returns {"resolved": ..., "mismatches": {field: {"emitted", "resolved"}},
    "warnings": [...]}. An empty `mismatches` means the model applied the policy
    exactly as this script does; anything else is a policy-application error,
    distinct from a scoring error.
    """
    dimensions, signals = classification_inputs(document)
    resolved = resolve(policy, dimensions, signals)
    mismatches: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []

    for field in ROUTE_FIELDS:
        emitted = _emitted(document, field)
        expected = resolved[field]
        if field in ("overrides_applied", "required_agents"):
            same = set(emitted or []) == set(expected)
        elif field == "human_gate":
            emitted_required = emitted.get("required") if isinstance(emitted, dict) else emitted
            same = bool(emitted_required) == expected["required"]
        else:
            same = emitted == expected
        if not same:
            mismatches[field] = {"emitted": emitted, "resolved": expected}

    if resolved["dropped_read_only_signals"]:
        warnings.append(
            "emitted read-only signals that the taxonomy drops before matching: "
            + ", ".join(resolved["dropped_read_only_signals"])
        )
    if resolved["unknown_signals"]:
        warnings.append(
            "emitted signals outside the policy vocabulary (they match nothing): "
            + ", ".join(resolved["unknown_signals"])
        )
    return {"resolved": resolved, "mismatches": mismatches, "warnings": warnings}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_dimension_args(policy: dict[str, Any], raw: list[str]) -> dict[str, Any]:
    """`1,1,1,1,2,2` in policy order, or `name=value` pairs, or a mix of pairs."""
    names = list(policy["scoring"]["dimensions"])
    tokens: list[str] = []
    for item in raw:
        tokens.extend(part for part in item.split(",") if part.strip())
    if tokens and all("=" not in token for token in tokens):
        if len(tokens) != len(names):
            raise RoutingError(f"--dimensions needs {len(names)} values in order {names}, got {len(tokens)}")
        return {name: _int_token(name, token) for name, token in zip(names, tokens)}
    parsed: dict[str, Any] = {}
    for token in tokens:
        if "=" not in token:
            raise RoutingError(f"mixing positional and name=value dimensions: {token!r}")
        name, value = token.split("=", 1)
        parsed[name.strip()] = _int_token(name.strip(), value)
    return parsed


def _int_token(name: str, token: str) -> Any:
    token = token.strip()
    try:
        return int(token)
    except ValueError:
        return token  # validate_dimensions reports it with the dimension name


def parse_signal_args(items: list[str]) -> list[str]:
    signals: list[str] = []
    for item in items:
        signals.extend(part.strip() for part in item.split(",") if part.strip())
    return signals


def load_document(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RoutingError(f"cannot read {path}: {exc}") from exc
    try:
        document = yaml.safe_load(text)  # JSON is YAML
    except yaml.YAMLError as exc:
        raise RoutingError(f"{path} is not valid YAML/JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise RoutingError(f"{path} must hold a mapping")
    return document


def render(result: dict[str, Any], as_json: bool) -> str:
    if as_json:
        return json.dumps(result, indent=2, ensure_ascii=False)
    return yaml.safe_dump(result, sort_keys=False, allow_unicode=True).rstrip()


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--policy", type=Path, default=POLICY_PATH, help="routing policy (default: agent-routing/policy.yaml)")
    parser.add_argument("--from", dest="source", type=Path,
                        help="classification YAML/JSON to read dimensions and signals from")
    parser.add_argument("--dimensions", "-d", action="append", default=[], metavar="SCORES",
                        help="six scores in policy order (1,1,0,1,2,2) or name=value pairs")
    parser.add_argument("--signals", "--signal", "-s", action="append", default=[],
                        metavar="SIGNAL[,SIGNAL]", help="verb-first signals the change performs; repeatable")
    parser.add_argument("--check", action="store_true", help="with --from: diff the file's route against the policy")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of YAML")
    parser.add_argument("--record", action="store_true",
                        help="also write the agent-budget ledger the PreToolUse hook enforces")
    parser.add_argument("--requirement", default="", help="label stored in the ledger with --record")
    parser.add_argument("--fresh", action="store_true",
                        help="with --record: start the ledger from zero instead of carrying over this requirement's charges")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        policy = load_policy(args.policy)
        if args.check and args.source is None:
            raise RoutingError("--check needs --from FILE")
        if args.source is not None:
            document = load_document(args.source)
            dimensions, signals = classification_inputs(document)
            if args.dimensions:
                dimensions = parse_dimension_args(policy, args.dimensions)
            if args.signals:
                signals = parse_signal_args(args.signals)
        else:
            if not args.dimensions:
                raise RoutingError("give --dimensions (or --from FILE)")
            document = {}
            dimensions = parse_dimension_args(policy, args.dimensions)
            signals = parse_signal_args(args.signals)

        if args.check:
            outcome = check(policy, document)
            for warning in outcome["warnings"]:
                print(f"warning: {warning}", file=sys.stderr)
            if outcome["mismatches"]:
                print(render({"mismatches": outcome["mismatches"], "resolved": outcome["resolved"]}, args.json))
                return 1
            print(render(outcome["resolved"], args.json))
            return 0

        result = resolve(policy, dimensions, signals)
        print(render(result, args.json))
        if args.record:
            path = load_ledger_module().record(result, args.requirement, fresh=args.fresh)
            print(f"recorded agent budget -> {path}", file=sys.stderr)
        return 0
    except RoutingError as exc:
        print(f"route: {exc}", file=sys.stderr)
        return 2


def load_ledger_module():
    """The ledger lives with the hooks; import it by path so this stays a plain script."""
    import importlib.util

    path = ROOT / "scripts" / "hooks" / "agent_budget.py"
    spec = importlib.util.spec_from_file_location("agent_budget", path)
    if spec is None or spec.loader is None:
        raise RoutingError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
