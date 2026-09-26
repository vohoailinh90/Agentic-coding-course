#!/usr/bin/env python3
"""Set `CI_RUNNER` across several repositories from one Actions quota reading.

    CI_RUNNER_TOKEN=... python3 scripts/sync_ci_runner.py \
        --owner vohoailinh90 --repo a --repo b --repo c

`.github/workflows/runner-mode.yml` does this for one repository, from inside
Actions, and needs its own isolated runner to hold the token away from
pull-request code. That design does not scale to a personal account with
several private repositories: GitHub has no user-level self-hosted runner, so
every repository would need a probe runner of its own -- one more persistent
runner process per repository, each holding a PAT.

This is the same decision taken once, outside Actions, on a host that already
has the token. One cron entry covers every repository and no probe runner
exists to be shared with untrusted code. The decision itself is not
reimplemented: `pick_runner.decide` is imported unchanged, so the hysteresis,
the SKU conversion and the refusal to guess behave exactly as they do in the
workflow and are covered by the same tests.

The token is read from the environment only, never from a flag: an argument is
visible to every process on the box through `ps`.

**Run this under a different OS user than the runners.** Keeping the PAT out of
argv keeps it out of `ps`; it does not keep it out of `/proc/<pid>/environ`,
which any process sharing this process's UID can read while it runs. A
self-hosted runner executes workflow code and is not destroyed afterwards, so a
process an earlier job left behind under the runner's account is exactly such a
process. Cron this as a separate unprivileged user that owns nothing the runner
account can reach, and the environment it holds the PAT in is no longer one the
runner's leftovers can open. Putting the cron under the runner's own account
undoes that, whatever this script does with its arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import types
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://api.github.com"
TIMEOUT = 30


def _load_picker() -> types.ModuleType:
    """Import pick_runner.py from beside this file, without requiring a package."""
    path = pathlib.Path(__file__).resolve().parent / "pick_runner.py"
    module = types.ModuleType("pick_runner")
    module.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)
    return module


pick = _load_picker()


def billing_candidates(owner: str, now: datetime | None = None) -> list[str]:
    """The four endpoints the probe tries, in the same order and with the same window.

    Kept identical to runner-mode.yml deliberately. The enhanced platform does
    not mirror the legacy paths -- its organization report lives under
    /organizations/, not /orgs/ -- and both enhanced reports need an explicit
    year and month, because the allowance is monthly and a year-wide report
    would overstate usage and pin every repository to the VPS for good.
    """
    now = now or datetime.now(timezone.utc)
    window = f"year={now.year}&month={now.month}"
    return [
        f"{API}/users/{owner}/settings/billing/actions",
        f"{API}/orgs/{owner}/settings/billing/actions",
        f"{API}/users/{owner}/settings/billing/usage?{window}",
        f"{API}/organizations/{owner}/settings/billing/usage?{window}",
    ]


def request(url: str, token: str, method: str = "GET", body: dict | None = None):
    """Return (status, headers, parsed-json-or-None). Never raises on an HTTP error."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            raw = response.read()
            parsed = json.loads(raw) if raw else None
            return response.status, dict(response.headers), parsed
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"  {method} {url} -> {exc}", file=sys.stderr)
        return 0, {}, None


def fetch_billing(owner: str, token: str) -> object | None:
    """The first candidate that answers 200, or None when none does.

    A paginated report is refused rather than read: one page of a report is not
    the report, and a first page carrying no Actions items would read as zero
    usage and move every repository onto an allowance that may already be spent.
    """
    for url in billing_candidates(owner):
        status, headers, payload = request(url, token)
        print(f"  GET {url.split(API)[-1]} -> {status}")
        if status != 200:
            continue
        if 'rel="next"' in headers.get("Link", ""):
            print("  billing report is paginated; refusing to decide from one page", file=sys.stderr)
            return None
        return payload
    return None


def current_runner(owner: str, repo: str, token: str) -> str | None:
    """The repository's CI_RUNNER, "" when genuinely unset, None when unreadable.

    The three states have to stay apart. A 404 means the variable does not
    exist, which is information; a timeout, a 5xx or a malformed 200 means we
    learned nothing. Returning "" for both let a transient read failure be read
    as "unset", and an unset value is what `decide` treats as having no standing
    choice -- so a blip could hand a repository a label chosen from a state that
    was never observed. Not knowing is not the same as knowing it is empty.
    """
    status, _, payload = request(f"{API}/repos/{owner}/{repo}/actions/variables/CI_RUNNER", token)
    if status == 200 and isinstance(payload, dict):
        value = payload.get("value")
        # A 200 whose body has no `value`, or a null one, is a malformed
        # response, not an observation. `str(payload.get("value", ""))` turned
        # the first into "" -- indistinguishable from a genuine absence -- and
        # the second into the literal string "None", which is worse: a label
        # nothing answers to, reported as though it had been read.
        return value if isinstance(value, str) else None
    if status == 404:
        return ""
    return None


def write_runner(owner: str, repo: str, token: str, value: str) -> bool:
    base = f"{API}/repos/{owner}/{repo}/actions/variables"
    body = {"name": "CI_RUNNER", "value": value}
    status, _, _ = request(f"{base}/CI_RUNNER", token, method="PATCH", body=body)
    if status == 404:  # the variable does not exist yet
        status, _, _ = request(base, token, method="POST", body=body)
    if status not in (201, 204):
        print(f"  could not set CI_RUNNER on {repo} (HTTP {status})", file=sys.stderr)
        return False
    return True


def delete_runner(owner: str, repo: str, token: str) -> bool:
    """Remove CI_RUNNER so each repository's own workflow fallback applies again.

    404 counts as success. The decision that asks for this is "leave the
    standing choice alone", and a variable that is already absent is that state
    -- failing the run because the work was done elsewhere would turn a correct
    outcome into a reported failure.
    """
    status, _, _ = request(f"{API}/repos/{owner}/{repo}/actions/variables/CI_RUNNER",
                           token, method="DELETE")
    if status not in (204, 404):
        print(f"  could not remove CI_RUNNER on {repo} (HTTP {status})", file=sys.stderr)
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", action="append", default=[], metavar="NAME",
                        help="repeatable; the repositories to keep in step")
    parser.add_argument("--mode", default="auto", choices=["auto", "github", "self-hosted"])
    parser.add_argument("--github-label", default="ubuntu-latest")
    parser.add_argument("--self-hosted-label", default="self-hosted")
    parser.add_argument("--low-water", type=int, default=50)
    parser.add_argument("--high-water", type=int, default=200)
    parser.add_argument("--included-minutes", type=int, default=None,
                        help="your plan's monthly allowance; required on the enhanced billing platform, "
                             "which reports consumption but not the allowance")
    parser.add_argument("--dry-run", action="store_true", help="decide and report, write nothing")
    args = parser.parse_args(argv)

    if not args.repo:
        print("no --repo given; nothing to do", file=sys.stderr)
        return 1

    token = os.environ.get("CI_RUNNER_TOKEN", "")
    if not token:
        print("CI_RUNNER_TOKEN is not set; refusing to run", file=sys.stderr)
        return 1

    print(f"reading Actions billing for {args.owner}")
    payload = fetch_billing(args.owner, token) if args.mode == "auto" else None
    quota = pick.read_quota(payload, args.included_minutes) if args.mode == "auto" else pick.Quota(None, "pinned")
    print(f"quota: remaining={quota.remaining} source={quota.source}\n")

    failures = 0
    for repo in args.repo:
        current = current_runner(args.owner, repo, token)
        if current is None:
            # Deciding from a state we failed to observe is how a transient blip
            # becomes a permanent wrong answer. Skip and let the next run try.
            print(f"{repo}: could not read CI_RUNNER; skipped")
            failures += 1
            continue
        decision = pick.decide(
            mode=args.mode,
            current=current,
            github_label=args.github_label,
            self_hosted_label=args.self_hosted_label,
            quota=quota,
            low_water=args.low_water,
            high_water=args.high_water,
        )
        target = "(removed)" if decision.delete else decision.runner
        state = f"{repo}: {current or '(unset)'} -> {target}  [{decision.reason}]"
        # `undetermined` gates the write on its own. With CI_RUNNER unset a
        # quota that could not be read still reports `changed`, so writing on
        # `changed` alone would commit a label the picker never decided on.
        if decision.undetermined:
            print(f"{repo}: left alone  [{decision.reason}]")
        elif not decision.changed:
            print(f"{repo}: unchanged ({current})")
        elif args.dry_run:
            print(f"{state}  (dry run)")
        elif decision.delete and delete_runner(args.owner, repo, token):
            print(state)
        elif not decision.delete and write_runner(args.owner, repo, token, decision.runner):
            print(state)
        else:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
