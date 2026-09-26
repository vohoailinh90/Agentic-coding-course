#!/usr/bin/env bash
# Register a self-hosted Actions runner on this VPS for one or more repositories.
#
#   CI_RUNNER_TOKEN=<pat> ./scripts/setup-vps-runner.sh --owner vohoailinh90 \
#       --repo DocumentAIEditor --repo Shipping_Inspection
#
# Run it ON the VPS -- never as root: GitHub's runner refuses to configure as
# root, and a runner executes workflow code, so the runner account should own as
# little as possible.
#
# Run this as a control account and pass --runner-user for the account the
# service should run as. Those must differ, and the reason is narrow: the PAT is
# in THIS process's environment for the length of the run, and
# /proc/<pid>/environ is readable by any process sharing its UID -- including
# anything an earlier job left behind under the runner account, since a
# self-hosted runner is not destroyed between jobs. Keeping the token off argv
# (below) stops `ps` from showing it; it does not stop a same-UID reader. If the
# invoker IS the runner account, a workflow process left behind by an earlier
# job can read the PAT out of /proc/<pid>/environ while this runs.
#
# Leaving --runner-user at its default makes the invoker the runner account, so
# do that only on a box with no runners yet, and rotate the PAT afterwards.
#
# A personal GitHub account has no organization-level runner, so a runner is
# registered per repository. They share one downloaded package and one parent
# directory; each gets its own working directory and its own service.
#
# The PAT needs `repo` scope (classic) or Administration: read and write
# (fine-grained) to mint a registration token. Registration tokens themselves
# expire in an hour, which is why this mints one per repository at run time
# rather than asking you to paste one.
set -euo pipefail

OWNER=""
REPOS=()
LABELS="vps"
RUNNER_ROOT="${RUNNER_ROOT:-$HOME/actions-runners}"
# Runners are named <repo>-runner, lowercased, to match the ones this account
# already has (documentai-runner, customer-tcd-sync-runner). Set
# RUNNER_NAME_PREFIX to disambiguate if a second host ever registers runners for
# the same repositories -- a name has to be unique per repository, not per box.
VERSION="${RUNNER_VERSION:-2.328.0}"
# Who the runner SERVICE runs as. Defaults to the invoker, which is the simple
# case; pass --runner-user to install it as somebody else, so the account
# holding the PAT during setup is not the account that later executes
# workflow code. See docs/ci-runner-mode.md.
RUNNER_USER="$(id -un)"

usage() { sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --owner)  OWNER="$2"; shift 2 ;;
    --repo)   REPOS+=("$2"); shift 2 ;;
    --labels) LABELS="$2"; shift 2 ;;
    --root)   RUNNER_ROOT="$2"; shift 2 ;;
    --runner-user) RUNNER_USER="$2"; shift 2 ;;
    -h|--help) usage 0 ;;
    *) echo "unknown argument: $1" >&2; usage 1 ;;
  esac
done

[ -n "${OWNER}" ] || { echo "--owner is required" >&2; exit 1; }
[ "${#REPOS[@]}" -gt 0 ] || { echo "at least one --repo is required" >&2; exit 1; }
[ -n "${CI_RUNNER_TOKEN:-}" ] || { echo "CI_RUNNER_TOKEN is not set" >&2; exit 1; }
[ "$(id -u)" -ne 0 ] || { echo "refusing to run as root; use an unprivileged user" >&2; exit 1; }

# Resolved here, before anything with a side effect. This check used to sit
# just above `svc.sh install` -- after a registration token had been minted and
# config.sh had already registered the runner with GitHub and written
# ${dir}/.runner. A misspelt --runner-user therefore exited having left a
# registered runner with no service behind it, and the corrected rerun matched
# that same .runner file, printed "already configured", and skipped the
# repository, so the service was never installed at all. Nothing below this
# line can be undone by running the script again.
if [ "${RUNNER_USER}" != "$(id -un)" ]; then
  id -u "${RUNNER_USER}" >/dev/null 2>&1 || { echo "no such user: ${RUNNER_USER}" >&2; exit 1; }
fi

for tool in curl tar; do
  command -v "${tool}" >/dev/null || { echo "missing required tool: ${tool}" >&2; exit 1; }
done

case "$(uname -m)" in
  x86_64)  ARCH="x64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

TARBALL="actions-runner-linux-${ARCH}-${VERSION}.tar.gz"
CACHE="${RUNNER_ROOT}/${TARBALL}"
mkdir -p "${RUNNER_ROOT}"

# The service runs as ${RUNNER_USER} out of ${RUNNER_ROOT}, so that account has
# to be able to traverse every directory above it. The default root sits under
# this account's $HOME, which is routinely 0700 or 0750; chowning the runner's
# own directory does not help when an ancestor blocks the path, and `svc.sh
# install` succeeds either way -- leaving a service that can never start.
#
# Reported rather than repaired on purpose: widening the permissions on
# somebody's home directory is not a side effect a setup script should have
# silently. `test -x` on the deepest path fails if any ancestor denies
# traversal, so one check covers the whole chain.
if [ "${RUNNER_USER}" != "$(id -un)" ]; then
  if ! sudo -u "${RUNNER_USER}" test -x "${RUNNER_ROOT}" 2>/dev/null; then
    echo "${RUNNER_USER} cannot traverse ${RUNNER_ROOT} (checked via sudo)." >&2
    echo "Pass --root with a path that account can reach, e.g. --root /opt/actions-runners." >&2
    exit 1
  fi
fi

if [ ! -f "${CACHE}" ]; then
  echo "==> downloading ${TARBALL}"
  curl -fsSL -o "${CACHE}" \
    "https://github.com/actions/runner/releases/download/v${VERSION}/${TARBALL}"
fi

for repo in "${REPOS[@]}"; do
  dir="${RUNNER_ROOT}/${repo}"
  echo
  echo "==> ${OWNER}/${repo}"

  if [ -f "${dir}/.runner" ]; then
    echo "    already configured at ${dir}; leaving it alone"
    continue
  fi

  # A runner registered from somewhere else -- an earlier migration, another
  # box -- leaves nothing in ${dir}, so the check above cannot see it. Ask
  # GitHub instead. Registering a second runner for a repository that already
  # has one is not an error to GitHub: both simply sit in the pool, and the
  # duplicate quietly consumes memory on this box forever. This account already
  # has documentai-runner and customer-tcd-sync-runner, so it is a live case,
  # not a hypothetical.
  existing="$(printf 'header = "Authorization: Bearer %s"\n' "${CI_RUNNER_TOKEN}" \
    | curl -fsSL -K - \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/${OWNER}/${repo}/actions/runners" \
    | python3 -c 'import json,sys; print(",".join(r["name"] for r in json.load(sys.stdin).get("runners", [])))')"
  if [ -n "${existing}" ] && [ -z "${ALLOW_DUPLICATE_RUNNER:-}" ]; then
    echo "    already has runner(s): ${existing}"
    echo "    skipping. Set ALLOW_DUPLICATE_RUNNER=1 to register another anyway."
    continue
  fi

  # Minted per repository and short-lived, so it is never stored anywhere.
  #
  # The PAT goes in through `curl -K -`, read from stdin, NOT as a `-H` argument.
  # An argument is visible to every process on the box: /proc/<pid>/cmdline is
  # world-readable by default, so a literal `-H "Authorization: Bearer ..."`
  # hands a long-lived credential to anyone who runs ps at the right moment.
  # sync_ci_runner.py refuses a token on argv for exactly this reason; the same
  # rule has to hold here, on the machine that runs untrusted workflow code.
  echo "    minting a registration token"
  reg_token="$(printf 'header = "Authorization: Bearer %s"\n' "${CI_RUNNER_TOKEN}" \
    | curl -fsSL -X POST -K - \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/${OWNER}/${repo}/actions/runners/registration-token" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')"

  mkdir -p "${dir}"
  tar xzf "${CACHE}" -C "${dir}"

  echo "    configuring (labels: ${LABELS})"
  # --unattended so it never blocks on a prompt; --replace so re-running after a
  # failed attempt does not leave a duplicate registration behind.
  #
  # `--token` on the command line is config.sh's own interface and there is no
  # stdin form, so this one value is briefly visible in ps -- unlike the PAT
  # above, which is not. The exposure is bounded: a registration token is
  # single-purpose and expires in an hour, where the PAT can write variables in
  # every repository it reaches. Worth stating rather than leaving a reader to
  # assume the whole script keeps secrets off argv.
  ( cd "${dir}" && ./config.sh \
      --url "https://github.com/${OWNER}/${repo}" \
      --token "${reg_token}" \
      --name "${RUNNER_NAME_PREFIX:-}$(printf '%s' "${repo}" | tr '[:upper:]' '[:lower:]')-runner" \
      --labels "${LABELS}" \
      --unattended --replace )

  echo "    installing the service as ${RUNNER_USER}"
  if [ "${RUNNER_USER}" != "$(id -un)" ]; then
    # config.sh just wrote this tree as the invoking user; the service account
    # has to own it to run from it. The account's existence and its ability to
    # traverse ${RUNNER_ROOT} were both settled before the first side effect.
    sudo chown -R "${RUNNER_USER}" "${dir}"
  fi
  ( cd "${dir}" && sudo ./svc.sh install "${RUNNER_USER}" && sudo ./svc.sh start )
  echo "    done"
done

cat <<'NEXT'

==> Runners registered.

Every self-hosted runner also carries the automatic labels `self-hosted`,
`linux` and its architecture, on top of the custom labels above. That is why
`runs-on: self-hosted` reaches these runners without further configuration.

Next, keep CI_RUNNER in step with your remaining hosted quota. From this VPS,
one cron entry covers every repository:

  crontab -e
  17 */6 * * * CI_RUNNER_TOKEN=<pat> /usr/bin/python3 /path/to/sync_ci_runner.py \
      --owner OWNER --repo A --repo B --included-minutes 2000 >> ~/ci-runner-sync.log 2>&1

Check it once by hand first:

  CI_RUNNER_TOKEN=<pat> python3 scripts/sync_ci_runner.py --owner OWNER --repo A --dry-run
NEXT
