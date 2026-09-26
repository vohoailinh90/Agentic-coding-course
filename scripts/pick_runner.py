#!/usr/bin/env python3
"""Choose which runner label this repository's workflows should use.

The choice is a pure function of (mode, remaining quota, thresholds, current
value), so per `deterministic_work` in agent-routing/policy.yaml it belongs in a
script rather than in a model's judgement or in an unreviewable YAML expression.

The network call is deliberately NOT here. The workflow curls the billing API
and pipes the JSON in, which leaves this file with no I/O to mock and no reason
to fail differently in a test than in CI.

    python3 scripts/pick_runner.py --mode auto --current "$CI_RUNNER" < billing.json

Two billing shapes are recognized, because GitHub has two generations of the
endpoint and which one answers depends on whether the account has moved to the
enhanced billing platform:

    legacy    {"total_minutes_used": N, "included_minutes": M, ...}
    enhanced  {"usageItems": [{"product": "actions", "quantity": N, ...}, ...]}

An unrecognized payload is reported as UNDETERMINED and leaves the current
choice alone. Guessing here would silently move every job in the repository onto
the wrong runner, which is the one outcome worse than not deciding.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from typing import NamedTuple

UNDETERMINED = "undetermined"

# GitHub assigns a self-hosted runner `self-hosted` plus exactly one OS label
# and one architecture label -- not the whole vocabulary. One label never
# identifies one machine, which is why comparing the probe's custom label with
# the shared one is necessary but not sufficient; but the converse matters too,
# and an earlier version of this guard got it wrong in the expensive direction
# for the operator: it treated every OS and arch label as a collision, so a
# Linux probe beside Windows jobs (`CI_SELF_HOSTED_LABEL=windows`) was rejected
# for a machine it cannot be dispatched to.
AUTO_SHARED_LABEL = "self-hosted"
AUTO_OS_LABELS = frozenset({"linux", "windows", "macos"})
# `x86` is in `RUNNER_ARCH`'s documented vocabulary, so it belongs here even
# though current runner packages do not ship an x86 build. A value missing from
# these sets is not the safe "unrecognized" case below -- it is never treated as
# shared at all, so `CI_SELF_HOSTED_LABEL=x86` would read as isolated.
AUTO_ARCH_LABELS = frozenset({"x86", "x64", "arm", "arm64"})

# The union is what applies when the probe's own platform is unknown. Not
# knowing which OS the probe runs is not evidence that it differs from the one
# in question, so the unknown case keeps the conservative behaviour and rejects
# the lot -- narrowing requires the positive evidence `runner.os`/`runner.arch`
# supply, never the absence of it.
AUTO_SELF_HOSTED_LABELS = frozenset({AUTO_SHARED_LABEL}) | AUTO_OS_LABELS | AUTO_ARCH_LABELS

# One native runner minute costs this many *included* minutes on a private
# repository: Linux 1x, Windows 2x, macOS 10x. The enhanced billing report
# separates usage by SKU and states native minutes, so summing quantities across
# SKUs counts a macOS minute as a tenth of what it actually consumes.
#
# Deliberately an exact-match whitelist rather than a substring test. Larger
# runners carry SKUs like `actions_linux_4_core` and are billed per minute
# without drawing on the allowance at all, so matching on "linux" would charge
# them 1x against a budget they never touch. Anything not listed here is not
# 1x -- it is unconvertible, and says so.
INCLUDED_MINUTE_RATES = {
    "actions_linux": 1,
    "actions_windows": 2,
    "actions_macos": 10,
}


class Decision(NamedTuple):
    runner: str
    reason: str
    changed: bool
    undetermined: bool
    # Remove CI_RUNNER rather than write `runner`. Setting a label is not the
    # only way to leave a repository in a correct state: when the right answer
    # is "whatever this repository's own workflows fall back to", only deleting
    # the variable expresses it, because that fallback is written in each
    # repository's YAML and this function never sees it.
    delete: bool = False


class Quota(NamedTuple):
    remaining: int | None
    source: str


def read_quota(payload: object, included_minutes: int | None) -> Quota:
    """Remaining included Actions minutes, or None when it cannot be read."""
    if not isinstance(payload, dict):
        return Quota(None, "billing payload is not a JSON object")

    if payload.get("incomplete"):
        # The fetch saw more pages than it collected. A first page holding no
        # Actions items is not a statement of zero usage, it is a partial view,
        # and reading it as zero would move jobs onto an allowance that may
        # already be spent.
        return Quota(None, "billing report was paginated and could not be read in full")

    # Legacy: the endpoint states the allowance, so nothing has to be configured.
    used = payload.get("total_minutes_used")
    included = payload.get("included_minutes")
    if _is_number(used) and _is_number(included):
        return Quota(max(0, int(included) - int(used)), f"legacy billing: {int(used)}/{int(included)} minutes used")

    items = payload.get("usageItems")
    if isinstance(items, list):
        return _read_enhanced(items, included_minutes)

    return Quota(None, "billing payload matched no known shape")


def _read_enhanced(items: list, included_minutes: int | None) -> Quota:
    """The enhanced billing platform's usage report, converted to included minutes.

    It reports consumption but not the plan allowance, so the allowance has to
    be supplied: without it there is no remainder to compute, and a default
    would be a guess about someone's billing plan.
    """
    if included_minutes is None:
        return Quota(None, "enhanced billing payload needs --included-minutes to yield a remainder")
    total = 0.0
    for item in items:
        if not isinstance(item, dict):
            continue
        if str(item.get("product", "")).lower() != "actions":
            continue
        if "minute" not in str(item.get("unitType", "")).lower():
            continue
        quantity = item.get("quantity")
        if not _is_number(quantity):
            continue
        sku = str(item.get("sku", "")).strip().lower()
        rate = INCLUDED_MINUTE_RATES.get(sku)
        if rate is None:
            # Counting an unrecognized SKU at 1x is wrong in both directions
            # and silently: a macOS minute costs ten included minutes, a
            # larger-runner minute costs none. Either way the remainder would
            # be confidently wrong, and overstating it keeps jobs on a hosted
            # runner whose quota is already gone -- the exact failure this
            # switch exists to prevent.
            return Quota(None, f"enhanced billing reports an Actions SKU this cannot convert: {sku!r}")
        total += float(quantity) * rate
    # An empty report is a valid zero, and treating it as unreadable builds a
    # ratchet. A review round had this return undetermined, reasoning that an
    # idle month and a report that did not carry what was asked for look alike.
    # But once CI_RUNNER is self-hosted no hosted minutes are spent, so every
    # later report is legitimately empty -- and "refuse to decide" would then
    # hold that choice forever, having removed the evidence that would undo it.
    # Declining to decide is only safe when it does not foreclose deciding
    # later. A report that genuinely could not be read fails earlier: a non-200
    # never reaches here, and an Actions SKU with no known rate returns above.
    return Quota(
        max(0, included_minutes - int(total)),
        f"enhanced billing: {int(total)}/{included_minutes} included minutes used",
    )


def _is_number(value: object) -> bool:
    # bool is an int subclass, and `True` as a minute count is a broken payload,
    # not a quota of one.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def decide(
    *,
    mode: str,
    current: str,
    github_label: str,
    self_hosted_label: str,
    quota: Quota,
    low_water: int,
    high_water: int,
) -> Decision:
    """Pick a runner label. `mode` pins the answer unless it is `auto`."""
    if mode == "github":
        return _settle(github_label, current, "mode=github (pinned)")
    if mode == "self-hosted":
        return _settle(self_hosted_label, current, "mode=self-hosted (pinned)")

    # `current` arrives raw so this can tell three states apart: absent,
    # present-and-usable, and present-but-broken. main() used to strip before
    # calling, which collapsed the third into the first.
    standing = current.strip()
    fallback = standing or github_label
    if quota.remaining is None:
        return _settle(fallback, current, f"quota {UNDETERMINED} ({quota.source}); left unchanged", undetermined=True)

    if quota.remaining <= low_water:
        return _settle(self_hosted_label, current, f"{quota.remaining} minutes left <= low water {low_water}")
    if quota.remaining >= high_water:
        return _settle(github_label, current, f"{quota.remaining} minutes left >= high water {high_water}")
    # Between the marks. Switching here would flip the variable on every probe
    # while the remainder hovers, so the standing choice wins.
    #
    # `current`, not `fallback`. When CI_RUNNER is unset there is no standing
    # choice to hold, and `current or github_label` invented one: it reported
    # "held" while returning `ubuntu-latest` and changed=True. On a repository
    # whose workflows carry `--fallback self-hosted`, the first probe landing in
    # the band would then write the hosted label and move every job back onto
    # billed minutes -- precisely what that flag exists to prevent, reintroduced
    # one layer down. An unset variable already resolves to whatever fallback
    # the repository's own workflows carry, and this function cannot see which,
    # so the only correct move is to leave it alone.
    if not standing:
        if current:
            # Present but unusable. A GitHub expression treats any non-empty
            # string as truthy, so `${{ vars.CI_RUNNER || '...' }}` resolves to
            # the whitespace itself and every job queues against a label no
            # runner answers to. Holding would leave CI stuck with nothing able
            # to unstick it from here, so this one is repaired -- by REMOVING
            # the variable, not by writing the hosted label.
            #
            # Writing `github_label` here was the deadband bug one layer down,
            # in the one branch the earlier fix did not reach: on a repository
            # converted with `--fallback self-hosted` it moves every job back
            # onto billed minutes, which is exactly what that flag exists to
            # prevent. Deleting unsticks CI just as well -- an absent variable
            # makes `${{ vars.CI_RUNNER || '<fallback>' }}` resolve to the
            # repository's own fallback -- and it is the only outcome that
            # restores the standing choice the band is supposed to hold, rather
            # than guessing at a fallback this function cannot see.
            return _settle("", current,
                           f"{quota.remaining} minutes left is between {low_water} and {high_water}; "
                           "CI_RUNNER is whitespace-only and no runner answers to it; "
                           "removed so the repository's own fallback applies", delete=True)
        return _settle(current, current,
                       f"{quota.remaining} minutes left is between {low_water} and {high_water}; "
                       "CI_RUNNER is unset, so the repository's own fallback stands")
    # `standing`, not `current`: a value carrying stray whitespace is repaired
    # to the label it meant rather than held in a form GitHub reads differently.
    return _settle(standing, current, f"{quota.remaining} minutes left is between {low_water} and {high_water}; held")


def _settle(runner: str, current: str, reason: str, *, undetermined: bool = False,
            delete: bool = False) -> Decision:
    return Decision(runner=runner, reason=reason, changed=runner != current,
                    undetermined=undetermined, delete=delete)


def emit(decision: Decision, stream=None) -> None:
    # Resolved per call, not bound at import: a default of `sys.stdout` captures
    # whatever the stream was when this module was first executed, which is the
    # wrong one under any caller that redirects it.
    stream = sys.stdout if stream is None else stream
    print(f"runner:  {decision.runner}", file=stream)
    print(f"reason:  {decision.reason}", file=stream)
    print(f"changed: {'yes' if decision.changed else 'no'}", file=stream)
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    # A newline in any value forges an extra output key. The labels come from
    # repository variables today, which only someone who can already edit the
    # workflow can set -- but guarding one free-form field and not its sibling
    # is an asymmetry that stops being harmless the moment a value's provenance
    # changes, so both are flattened at the one place that writes them.
    with pathlib.Path(output).open("a", encoding="utf-8") as handle:
        handle.write(f"runner={_one_line(decision.runner)}\n")
        handle.write(f"changed={str(decision.changed).lower()}\n")
        handle.write(f"undetermined={str(decision.undetermined).lower()}\n")
        handle.write(f"delete={str(decision.delete).lower()}\n")
        handle.write(f"reason={_one_line(decision.reason)}\n")


def _one_line(value: str) -> str:
    return " ".join(str(value).splitlines()).strip()


def normalize_label(value: str) -> str:
    """A runner label as GitHub compares it, and as `_one_line` will emit it.

    `casefold`, not `lower`: GitHub matches labels case-insensitively over more
    than ASCII, and `tr '[:upper:]' '[:lower:]'` -- the shell approximation this
    replaced -- leaves every non-ASCII letter alone. Whitespace is collapsed
    because `_one_line` turns an embedded newline into a space before writing
    the value, so two labels that differ only there become one once emitted.
    """
    return " ".join(str(value).split()).casefold()


def auto_labels(*, os_name: str = "", arch: str = "") -> frozenset[str]:
    """The labels GitHub assigns to the probe's runner on top of its custom one.

    `runner.os` and `runner.arch` are the probe's own platform, so a known value
    narrows the set to the one OS and the one architecture that machine actually
    answers to. An unknown or unrecognized value widens back to every candidate
    *for that field*: the guard may only narrow on evidence, and "I could not
    read the platform" is not evidence that a label is safe.

    The two fields narrow independently, which is the point of doing it per
    field rather than jointly. A readable OS still rules out the other two OS
    labels even when the architecture is unreadable, so an unreadable
    architecture does not resurrect `windows` for a runner known to be Linux.
    """
    platform = {AUTO_SHARED_LABEL}
    for value, vocabulary in ((os_name, AUTO_OS_LABELS), (arch, AUTO_ARCH_LABELS)):
        normalized = normalize_label(value)
        platform |= {normalized} if normalized in vocabulary else set(vocabulary)
    return frozenset(platform)


def probe_conflicts(*, probe: str, current: str, github_label: str, self_hosted_label: str,
                    os_name: str = "", arch: str = "") -> list[str]:
    """Why this probe label is not isolated from the runners other jobs use.

    The picker's own defaults apply, because a guard comparing against what is
    literally set passes while the picker substitutes something else and writes
    that instead -- the exact gap three review rounds each found one instance of.
    """
    wanted = normalize_label(probe)
    if not wanted:
        # Not "no conflicts found". A probe label that is blank once normalized
        # is a configuration the workflow still acts on -- `!= ''` passes for a
        # whitespace-only variable, and `runs-on` then names a label no runner
        # registers -- so reporting isolation here would certify a setup whose
        # probe never runs. Refusing is the only answer that is not a false
        # negative.
        return [f"CI_PROBE_LABEL={probe!r} is blank once normalized, so no runner can match it "
                "while the workflow still queues the probe job against it"]
    shared = auto_labels(os_name=os_name, arch=arch)
    reasons = []
    if wanted in shared:
        reasons.append(
            f"{probe!r} is a label GitHub assigns to every self-hosted runner, so ordinary jobs "
            "can be dispatched to the probe's machine whatever it registered as"
        )
    for name, value in (("CI_RUNNER", current),
                        ("CI_SELF_HOSTED_LABEL", self_hosted_label),
                        ("CI_GITHUB_LABEL", github_label)):
        if not str(value).strip():
            continue
        if normalize_label(value) in shared:
            reasons.append(
                f"{name}={value!r} is a label the probe's own runner carries, so jobs using it "
                "can land on the probe's machine"
            )
        elif normalize_label(value) == wanted:
            reasons.append(f"{name}={value!r} is the probe's own label")
    return reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", default="auto", choices=["auto", "github", "self-hosted"])
    parser.add_argument("--current", default="", help="current value of the CI_RUNNER variable")
    parser.add_argument("--github-label", default="ubuntu-latest")
    parser.add_argument("--self-hosted-label", default="self-hosted")
    parser.add_argument("--low-water", type=int, default=50, help="switch to self-hosted at or below this many minutes")
    parser.add_argument("--high-water", type=int, default=200, help="switch back to GitHub at or above this many")
    parser.add_argument("--included-minutes", type=int, default=None, help="plan allowance, for enhanced billing")
    parser.add_argument("--billing-json", type=pathlib.Path, default=None, help="default: stdin")
    parser.add_argument(
        "--check-probe-isolation",
        metavar="PROBE_LABEL",
        help="verify the probe's runner label cannot receive other workflows' jobs, then exit",
    )
    # The probe's own platform, from `runner.os` / `runner.arch`. Supplying them
    # narrows the automatic labels to the ones that machine really carries;
    # omitting them keeps every candidate, so the guard fails closed.
    parser.add_argument("--probe-os", default="", help="RUNNER_OS of the probe runner")
    parser.add_argument("--probe-arch", default="", help="RUNNER_ARCH of the probe runner")
    args = parser.parse_args(argv)

    if args.check_probe_isolation is not None:
        # Lives here, not in the workflow, so the guard and the picker share one
        # normalization and one set of defaults. Duplicated in shell they drift,
        # and the guard then compares a different state from the one the picker
        # creates -- which is what three review rounds each found separately.
        reasons = probe_conflicts(
            probe=args.check_probe_isolation,
            current=args.current,
            github_label=args.github_label,
            self_hosted_label=args.self_hosted_label,
            os_name=args.probe_os,
            arch=args.probe_arch,
        )
        for reason in reasons:
            print(f"probe runner is not isolated: {reason}", file=sys.stderr)
        if reasons:
            print("The probe job holds CI_RUNNER_TOKEN. See docs/ci-runner-mode.md.", file=sys.stderr)
            return 1
        print("probe runner label is disjoint from the labels other workflows use.")
        return 0

    if args.high_water <= args.low_water:
        parser.error(f"--high-water ({args.high_water}) must exceed --low-water ({args.low_water}) to give hysteresis")

    raw = args.billing_json.read_text(encoding="utf-8") if args.billing_json else sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else None
    except json.JSONDecodeError as exc:
        payload = None
        quota = Quota(None, f"billing payload is not JSON ({exc.msg})")
    else:
        quota = read_quota(payload, args.included_minutes) if payload is not None else Quota(None, "no billing payload")

    emit(
        decide(
            mode=args.mode,
            current=args.current,
            github_label=args.github_label,
            self_hosted_label=args.self_hosted_label,
            quota=quota,
            low_water=args.low_water,
            high_water=args.high_water,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
