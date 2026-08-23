#!/usr/bin/env python3
"""The single required status check on ``main``, and what it aggregates.

Branch protection names exactly one context: ``E2E Gate (required)``. That is
deliberate -- one name in the Settings UI instead of a dozen -- but it means
this file *is* the merge gate. A check that is not listed here cannot block a
merge, no matter how good the test behind it is.

That distinction had teeth. Before this script existed the gate aggregated four
E2E checks and nothing else, so ``CI`` -- which carries the Python 3.9
annotation guard, the 3-OS API matrix, the MOAT verifier, the entitlement
suite, and the ``pip install`` matrix -- could be **fully red** while the pull
request merged green. 0.12.753 shipped a ``-> str | None`` at ``clawmetry/cli.py``
module scope that killed every subcommand at import on Python 3.9, including
``clawmetry uninstall``; the guard written afterwards landed in a workflow that
gated nothing.

Two matching modes:

* an exact name (``"Syntax & Lint"``) for a single job;
* an fnmatch pattern plus ``min_count`` for a matrix job, where the pattern
  expands to one check per leg (``"pip install (*)"`` -> four legs). ``min_count``
  is what stops a *shrinking* matrix from quietly passing: drop macOS from the
  matrix and the pattern still matches, but the count no longer does.

Pure evaluation lives in :func:`evaluate` so ``tests/test_e2e_gate.py`` can
drive it over synthetic check-run payloads with no network.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

POLL_INTERVAL = 30
DEFAULT_MAX_WAIT = 1800

# GitHub treats skipped/neutral as non-blocking; match that.
PASSING = {"success", "skipped", "neutral"}

# 'cancelled' means concurrency replaced this run with a newer one. Wait for
# the replacement rather than fast-failing on the stale cancellation.
WAIT_FOR_REPLACEMENT = {"cancelled"}

DEFINITIVE = {"success", "failure", "timed_out", "action_required", "startup_failure"}


@dataclass(frozen=True)
class Spec:
    """One required check, or one matrix of them.

    ``min_count`` is the number of distinct check names the pattern must match
    before the spec can pass. For a single job that is 1. For a matrix it is the
    number of legs, so removing a leg fails the gate instead of silently
    reducing coverage.
    """

    label: str
    pattern: str
    min_count: int = 1

    def matches(self, name: str) -> bool:
        return fnmatch.fnmatchcase(name, self.pattern)


# ---------------------------------------------------------------------------
# THE GATE. Adding a line here makes a check merge-blocking.
#
# Only list checks whose workflow runs on EVERY pull request. A path-filtered
# or tag-triggered workflow never reports on most PRs, so requiring it here
# would hang the gate until timeout and block every merge. Those surfaces are
# covered continuously by the conformance heartbeat instead.
# ---------------------------------------------------------------------------
REQUIRED_SPECS = [
    # -- The original four E2E checks. -------------------------------------
    Spec("OSS golden path", "OSS golden path (wheel + OpenClaw + 9 tabs)"),
    Spec("Cross-repo handoff", "Cross-repo handoff (C4)"),
    Spec("MOAT Keystone", "MOAT Keystone (13-endpoint bar)"),
    Spec("E2E Browser Tests", "E2E Browser Tests (critical subset)"),

    # -- Added by L0: guards that existed but did not gate. ----------------
    # Carries check_py39_annotations.py, the stdout-rebind ban, the runtime
    # count check, and the JS syntax check.
    Spec("Syntax & Lint", "Syntax & Lint"),
    # ubuntu / macos / windows.
    Spec("API Tests (3 OS)", "API Tests (*)", min_count=3),
    Spec("MOAT Verifier", "MOAT Verifier (72 tests)"),
    Spec("Entitlement API tests", "Entitlement API tests"),
    # 3 OS on 3.11 plus the ubuntu 3.9 leg that 0.12.753 needed.
    Spec("pip install matrix", "pip install (*)", min_count=4),
    Spec("Wheel install & assets", "Wheel install & asset presence"),
    # Property tests over the store, plus the mutation ratchet that keeps the
    # rest of these guards from decaying into tautologies.
    Spec("Store invariants", "Store invariants (property-based)"),

    # Blueprint/Requirement sync with 8090 Software Factory. FLYWHEEL 1f has
    # called a red drift-bot non-negotiable for months while nothing enforced
    # it: #5089 merged with it red, and clawmetry-cloud #2089 the day after.
    #
    # It belongs HERE rather than as a second branch-protection context. ADR-001
    # says protection names exactly one context and this file aggregates behind
    # it; adding a second name would have been a quieter kind of drift, where
    # the merge gate and its own architecture disagree.
    #
    # Unlike everything above, drift-bot is a COMMIT STATUS from the
    # 8090-software-factory GitHub App, not an Actions check run. It never
    # appears in /check-runs, which is why list_commit_statuses exists.
    Spec("Drift Bot", "drift-bot"),
]


@dataclass
class SpecResult:
    spec: Spec
    state: str  # "passed" | "failed" | "pending"
    detail: str = ""
    failing: list = field(default_factory=list)


def _priority(run):
    """Rank runs for the same check name; higher wins.

    A definitive conclusion beats an in-flight run, which beats a stale
    cancellation. This is what stops a cancel-in-progress race from
    fast-failing the gate on a run that has already been replaced.

    Both halves of the first condition are load-bearing: a completed run whose
    conclusion is 'cancelled' must NOT score as definitive, or a stale
    cancellation with a high id would outrank a real failure and a red check
    would silently present as merely pending.
    """
    status = run.get("status")
    conclusion = run.get("conclusion") or ""
    run_id = run.get("id", 0)
    if status == "completed" and conclusion in DEFINITIVE:
        return (2, run_id)
    if status in ("in_progress", "queued"):
        return (1, run_id)
    return (0, run_id)


def best_runs_by_name(runs):
    """Collapse many runs per check name down to the most informative one."""
    best = {}
    for run in runs:
        name = run.get("name", "")
        if not name:
            continue
        current = best.get(name)
        if current is None or _priority(run) > _priority(current):
            best[name] = run
    return best


def evaluate(specs, runs):
    """Resolve every spec against the check runs reported for a commit."""
    best = best_runs_by_name(runs)
    results = []

    for spec in specs:
        matched = {n: r for n, r in best.items() if spec.matches(n)}

        failing = [
            run
            for run in matched.values()
            if run.get("status") == "completed"
            and run.get("conclusion") not in PASSING
            and run.get("conclusion") not in WAIT_FOR_REPLACEMENT
        ]
        if failing:
            results.append(
                SpecResult(
                    spec,
                    "failed",
                    f"{len(failing)} of {len(matched)} matching check(s) failed",
                    failing,
                )
            )
            continue

        passed = [
            run
            for run in matched.values()
            if run.get("status") == "completed" and run.get("conclusion") in PASSING
        ]

        if len(matched) < spec.min_count:
            results.append(
                SpecResult(
                    spec,
                    "pending",
                    f"only {len(matched)} of {spec.min_count} expected leg(s) reported",
                )
            )
        elif len(passed) < spec.min_count:
            results.append(
                SpecResult(
                    spec,
                    "pending",
                    f"{len(passed)}/{spec.min_count} leg(s) complete",
                )
            )
        else:
            results.append(
                SpecResult(spec, "passed", f"{len(passed)} leg(s) passed")
            )

    return results


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "clawmetry-e2e-gate/2.0",
    }


def list_check_runs(repo, sha, token):
    """Fetch every check run for a commit, following pagination."""
    url = f"https://api.github.com/repos/{repo}/commits/{sha}/check-runs?per_page=100"
    runs = []
    while url:
        req = urllib.request.Request(url, headers=_headers(token))
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
                runs.extend(data.get("check_runs", []))
                url = None
                for part in resp.headers.get("Link", "").split(","):
                    part = part.strip()
                    if 'rel="next"' in part:
                        url = part.split(";")[0].strip().lstrip("<").rstrip(">")
        except urllib.error.HTTPError as exc:
            print(f"  warn: check-runs API {exc.code}: {exc.read()[:200]!r}")
            return runs
    return runs


# A commit status carries `state`, a check run carries `status` + `conclusion`.
# Normalising the former into the latter lets evaluate() stay one code path.
# "error" is GitHub's transport-level failure and blocks exactly like "failure";
# treating it as anything softer would let a broken reporter merge.
_STATUS_STATE_TO_CONCLUSION = {
    "success": "success",
    "failure": "failure",
    "error": "failure",
}


def list_commit_statuses(repo, sha, token):
    """Fetch commit statuses for a SHA, shaped like check runs.

    Commit statuses are a different API from check runs and do not appear in
    /check-runs at all. drift-bot is posted this way by the
    8090-software-factory app, so a gate that only reads check runs cannot see
    it -- which is precisely how it stayed unenforceable while FLYWHEEL called
    it non-negotiable.

    The combined endpoint already collapses to the most recent status per
    context, so no extra de-duplication is needed here.
    """
    url = f"https://api.github.com/repos/{repo}/commits/{sha}/status?per_page=100"
    req = urllib.request.Request(url, headers=_headers(token))
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"  warn: commit-status API {exc.code}: {exc.read()[:200]!r}")
        return []

    shaped = []
    for status in data.get("statuses", []):
        context = status.get("context") or ""
        if not context:
            continue
        state = status.get("state")
        conclusion = _STATUS_STATE_TO_CONCLUSION.get(state)
        if conclusion is None:
            # "pending", or anything GitHub adds later: not yet decided. Report
            # it as still running so the gate WAITS instead of passing on a
            # status that has not been posted yet.
            shaped.append({"name": context, "status": "in_progress", "conclusion": None})
        else:
            shaped.append({"name": context, "status": "completed", "conclusion": conclusion})
    return shaped


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=os.environ.get("REPO", ""))
    ap.add_argument("--sha", default=os.environ.get("COMMIT_SHA", ""))
    ap.add_argument(
        "--max-wait",
        type=int,
        default=int(os.environ.get("MAX_WAIT", DEFAULT_MAX_WAIT)),
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="print the required checks and exit (no network)",
    )
    args = ap.parse_args()

    if args.list:
        for spec in REQUIRED_SPECS:
            legs = f" x{spec.min_count}" if spec.min_count > 1 else ""
            print(f"{spec.label}{legs}: {spec.pattern}")
        return 0

    token = os.environ.get("GITHUB_TOKEN", "")
    # All three are required. Falling through without them would let the gate
    # report success without ever inspecting a check run -- the worst possible
    # failure mode for a merge gate.
    if not (token and args.repo and args.sha):
        print("FAIL: --repo, --sha and GITHUB_TOKEN are all required.")
        return 2

    sha = args.sha.strip()
    print(f"E2E Gate: {len(REQUIRED_SPECS)} required checks on {sha[:12]}")
    for spec in REQUIRED_SPECS:
        legs = f" (x{spec.min_count})" if spec.min_count > 1 else ""
        print(f"  - {spec.label}{legs}")
    print()

    start = time.monotonic()
    last = {}

    while True:
        elapsed = int(time.monotonic() - start)
        try:
            # Both surfaces, because the required set spans both: Actions
            # report as check runs, the Software Factory app as a commit
            # status. Reading only one is how drift-bot went unenforced.
            runs = list_check_runs(args.repo, sha, token)
            runs += list_commit_statuses(args.repo, sha, token)
        except Exception as exc:  # noqa: BLE001 - keep polling through blips
            print(f"  [{elapsed}s] warn: fetch failed: {exc}")
            time.sleep(POLL_INTERVAL)
            continue

        results = evaluate(REQUIRED_SPECS, runs)

        for res in results:
            line = f"{res.state}: {res.detail}"
            if last.get(res.spec.label) != line:
                print(f"  [{elapsed}s] {res.spec.label}: {line}")
                last[res.spec.label] = line

        failed = [r for r in results if r.state == "failed"]
        if failed:
            print("\nFAIL: required checks did not pass:")
            for res in failed:
                print(f"  - {res.spec.label}: {res.detail}")
                for run in res.failing:
                    print(
                        f"      {run.get('name')!r}: {run.get('conclusion')}"
                        f"  {run.get('html_url', '')}"
                    )
            return 1

        if all(r.state == "passed" for r in results):
            print(f"\nPASS: all {len(results)} required checks passed for {sha[:12]}.")
            return 0

        if elapsed >= args.max_wait:
            print(f"\nFAIL: timed out after {args.max_wait}s. Still pending:")
            for res in results:
                if res.state != "passed":
                    print(f"  - {res.spec.label}: {res.detail}")
            print(
                "\nA check stuck at 'not reported' usually means its workflow "
                "did not run for this commit -- confirm it triggers on "
                "pull_request without a paths filter."
            )
            return 1

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
