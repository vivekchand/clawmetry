#!/usr/bin/env python3
"""Every `uses:` reference in every workflow must actually resolve.

An unresolvable action is a SILENT failure. GitHub accepts the push, queues the
run, and then fails the job at "Set up job" before a single step executes, with
the reason buried in a log nobody opens. The workflow keeps appearing in the
Actions list, so it reads as "ran and failed" rather than "never ran at all".

That is not hypothetical. `.github/workflows/supply-chain.yml` referenced
``ossf/scorecard-action@v2``. That project publishes ``v2.4.4``, ``v2.4.3`` and
so on, but **no floating ``v2`` tag**, so the OpenSSF Scorecard job failed at
setup on every run since the day it was written. The supply-chain workflow was
permanently red on main, which is corrosive in its own right: a check that is
always red trains everyone, human and agent, to read red as normal.

Same class as the malformed-YAML bug that kept ``c6-schedule-heal.yml`` from
ever running, and it is caught the same way: by checking the thing rather than
assuming it.

Resolving a ref needs the network, so that half is opt-in via
``CLAWMETRY_LIVE_CHECKS=1`` and runs in the supply-chain workflow, which already
has a token. Local runs without the flag do the offline checks only.

The offline half also enforces that every reference is pinned to a full commit
SHA. A floating tag such as ``@v4`` is mutable: whoever controls the action's
repository can repoint it at new code, and that code then runs inside our jobs
with their credentials. Several of these workflows hold ``contents: write`` or
publish to PyPI, so the blast radius is real. Pinning every reference was done
over a series of changes; this check is what keeps it done, because a single
convenient ``@v4`` in a later PR would otherwise undo it silently.

Both halves cover composite actions under ``.github/actions/`` as well as the
workflows. A composite action's own ``uses:`` lines run with the same token as
the job that calls it, so leaving them unchecked left the shorter path in.

Usage::

    python3 scripts/check_action_refs.py              # offline shape + pin checks
    CLAWMETRY_LIVE_CHECKS=1 python3 scripts/check_action_refs.py   # resolve refs
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")
ACTION_DIR = os.path.join(REPO_ROOT, ".github", "actions")

# `uses: owner/repo@ref` or `uses: owner/repo/path@ref`. Local (`./`) and
# docker (`docker://`) references resolve differently and are skipped.
_USES = re.compile(r"^\s*-?\s*uses:\s*['\"]?([A-Za-z0-9._-]+/[A-Za-z0-9._/-]+)@([^\s'\"#]+)")

_SHA = re.compile(r"^[0-9a-f]{40}$")


def source_files() -> list:
    """Every file that can carry a `uses:` line: workflows and composite actions.

    Auto-discovered rather than listed, so a new workflow or a new composite
    action is covered the day it lands (the FLYWHEEL rule: allowlists drift).
    """
    files: list = []
    for ext in ("yml", "yaml"):
        files.extend(glob.glob(os.path.join(WORKFLOW_DIR, f"*.{ext}")))
        files.extend(
            glob.glob(os.path.join(ACTION_DIR, "**", f"action.{ext}"), recursive=True)
        )
    return sorted(files)


def collect_refs() -> dict:
    """Return {(owner_repo, ref): [files that use it]}, paths repo-relative."""
    refs: dict = {}
    for path in source_files():
        rel = os.path.relpath(path, REPO_ROOT)
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                match = _USES.match(line)
                if not match:
                    continue
                action, ref = match.group(1), match.group(2)
                refs.setdefault((action, ref), []).append(rel)
    return refs


def _api(url: str, token: str) -> int:
    """Return the HTTP status for a GET, or 0 when the request itself failed."""
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("User-Agent", "clawmetry-action-ref-check/1.0")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=20) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:  # noqa: BLE001 - network blip, not a verdict
        return 0


def resolve(action: str, ref: str, token: str) -> tuple:
    """(resolved, detail). A ref resolves if it is a tag, branch, or commit.

    The top-level repository is what carries the tags, so `owner/repo/sub@ref`
    is checked against `owner/repo`.
    """
    owner_repo = "/".join(action.split("/")[:2])
    base = f"https://api.github.com/repos/{owner_repo}"

    if _SHA.match(ref):
        status = _api(f"{base}/commits/{ref}", token)
        if status == 200:
            return True, "commit"
        if status == 0:
            return True, "unverified (network)"
        return False, f"commit not found (HTTP {status})"

    for kind, path in (("tag", "git/ref/tags"), ("branch", "git/ref/heads")):
        status = _api(f"{base}/{path}/{ref}", token)
        if status == 200:
            return True, kind
        if status == 0:
            return True, "unverified (network)"

    return False, "no matching tag or branch"


def main() -> int:
    refs = collect_refs()
    print(
        f"Found {len(refs)} distinct action reference(s) across "
        f"{len(source_files())} workflow/composite-action file(s)."
    )

    problems = []
    unpinned = []

    # Offline checks, so these run on every PR rather than only where a token
    # is available: a ref must be non-empty, not templated, and pinned to a
    # full commit SHA.
    for (action, ref), files in sorted(refs.items()):
        if not ref or "${{" in ref:
            problems.append(f"{action}@{ref} in {', '.join(files)}: unresolvable ref shape")
        elif not _SHA.match(ref):
            unpinned.append(f"{action}@{ref} used by {', '.join(files)}")

    if unpinned:
        print()
        print("ACTION REFERENCES NOT PINNED TO A COMMIT SHA")
        print("=" * 72)
        for entry in unpinned:
            print(f"  {entry}")
        print()
        print(
            "A tag is mutable; the repository that owns it can repoint it at new "
            "code, which then runs in our jobs with our token. Pin to the full "
            "40-character commit SHA and keep the version in a trailing comment:\n"
            "    uses: owner/action@<40-hex-sha> # vX.Y.Z\n"
            "Resolve the SHA with: git ls-remote https://github.com/owner/action "
            "refs/tags/vX.Y.Z"
        )

    live = os.environ.get("CLAWMETRY_LIVE_CHECKS") == "1"
    if not live:
        if problems:
            for problem in problems:
                print(f"  {problem}")
        if problems or unpinned:
            return 1
        print(
            f"OK (offline checks only): all {len(refs)} reference(s) are pinned "
            "to a commit SHA. Set CLAWMETRY_LIVE_CHECKS=1 to also resolve every "
            "reference against the GitHub API."
        )
        return 0

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print(
            "warn: no GITHUB_TOKEN; unauthenticated API allows only 60 requests "
            "per hour and may report false negatives."
        )

    for (action, ref), files in sorted(refs.items()):
        ok, detail = resolve(action, ref, token)
        if ok:
            print(f"  ok    {action}@{ref[:12]} ({detail})")
        else:
            print(f"  FAIL  {action}@{ref} ({detail}) used by {', '.join(files)}")
            problems.append(
                f"{action}@{ref} does not resolve ({detail}); used by "
                f"{', '.join(files)}"
            )

    if problems:
        print()
        print("UNRESOLVABLE ACTION REFERENCES")
        print("=" * 72)
        for problem in problems:
            print(f"  {problem}")
        print()
        print(
            "A job referencing one of these fails at 'Set up job' before any "
            "step runs, so the workflow looks like it ran and failed when it "
            "never started. Pin to a real tag, or better, to a commit SHA."
        )
        return 1

    if unpinned:
        return 1

    print(f"\nOK - all {len(refs)} action reference(s) resolve and are SHA-pinned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
