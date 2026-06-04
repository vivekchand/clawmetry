#!/usr/bin/env python3
"""Apply required status checks for E2E Robustness criterion C6.

This script is idempotent: running it multiple times is safe.
It adds checks listed in REQUIRED_CHECKS and removes any in DEPRECATED_CHECKS
from the main branch protection of each repo.

Usage
-----
  GITHUB_TOKEN=ghp_xxx python3 scripts/apply_required_status_checks.py

Token types
-----------
GITHUB_TOKEN from Actions (prefix ghs_):
  Can read branch protection state but CANNOT write it. The script detects
  this automatically: it verifies current state (read-only) and exits 0 with
  actionable instructions. Push-triggered runs are always informational.
  Note: requesting administration:write in the workflow permissions block is
  invalid for GITHUB_TOKEN and causes 0-job workflow failures -- do not add it.

Fine-grained PAT (prefix ghp_ or github_pat_, set as E2E_ADMIN_PAT secret):
  Required to write branch protection rules. Needs Administration (read+write)
  on clawmetry, clawmetry-cloud, clawmetry-landing. Full apply + verify.

When run inside GitHub Actions, GITHUB_REPOSITORY is set automatically
(e.g. "vivekchand/clawmetry"). The script restricts the checks it applies
to only the matching repo so that a single-repo token is sufficient.

When run locally (GITHUB_REPOSITORY not set), the script applies all 4
checks and requires a token with cross-repo Administration access.

Tracking: vivekchand/clawmetry#2146 (C6)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

OWNER = "vivekchand"

# Each tuple: (repo, exact job name as it appears in the workflow's `name:` field)
#
# Job names verified against workflow files 2026-06-01:
#   clawmetry/.github/workflows/oss-golden-path.yml      -> "OSS golden path (wheel + OpenClaw + 9 tabs)"
#   clawmetry/.github/workflows/cross-repo-handoff.yml   -> "Cross-repo handoff (C4)"
#   clawmetry-cloud/.github/workflows/e2e.yml            -> "Cloud golden-path browser E2E"
#   clawmetry-landing/.github/workflows/landing-golden-path.yml -> "Landing golden path (C3)"
#
# visual-diff (pr-screenshots.yml) is intentionally excluded: that workflow has
# a paths: filter so the job only runs on PRs that touch UI files. Adding it as
# a required check would permanently stall non-UI PRs on "Expected -- Waiting
# for status to be reported."
REQUIRED_CHECKS: list[tuple[str, str]] = [
    ("clawmetry",         "OSS golden path (wheel + OpenClaw + 9 tabs)"),
    ("clawmetry",         "Cross-repo handoff (C4)"),
    ("clawmetry-cloud",   "Cloud golden-path browser E2E"),
    ("clawmetry-landing", "Landing golden path (C3)"),
]

# Checks previously added as required that must be actively removed.
DEPRECATED_CHECKS: list[tuple[str, str]] = [
    # Added in error before 2026-06-02: pr-screenshots.yml has a paths: filter
    # so visual-diff only fires on UI-touching PRs. As a required check it
    # permanently stalls non-UI PRs waiting for a status that never arrives.
    ("clawmetry", "visual-diff"),
]


def _api(
    method: str,
    path: str,
    body: object = None,
    *,
    token: str,
) -> dict:
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "clawmetry-e2e-c6/1.0",
    }
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:  # noqa: S310
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        msg = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"GitHub {method} {path} => {exc.code}: {msg}"
        ) from exc


def _ensure_protection(repo: str, token: str) -> None:
    """Create a minimal branch protection rule on main if none exists."""
    path = f"/repos/{OWNER}/{repo}/branches/main/protection"
    try:
        _api("GET", path, token=token)
        return  # already protected
    except RuntimeError as exc:
        if "404" not in str(exc):
            raise
    # Create minimal protection (no restrictions, no reviews required)
    _api(
        "PUT",
        path,
        body={
            "required_status_checks": {"strict": False, "contexts": []},
            "enforce_admins": False,
            "required_pull_request_reviews": None,
            "restrictions": None,
        },
        token=token,
    )
    print(f"  [{repo}] created minimal branch protection on main")


def add_required_check(repo: str, context: str, token: str) -> None:
    """Idempotently add context as a required status check on repo/main."""
    _ensure_protection(repo, token)

    path = f"/repos/{OWNER}/{repo}/branches/main/protection/required_status_checks"
    try:
        current = _api("GET", path, token=token)
        existing: list[str] = current.get("contexts", [])
    except RuntimeError:
        existing = []

    if context in existing:
        print(f"  [{repo}] already required: {context!r}")
        return

    existing.append(context)
    _api("PATCH", path, body={"strict": False, "contexts": existing}, token=token)
    print(f"  [{repo}] added required check ({len(existing)} total): {context!r}")


def remove_required_check(repo: str, context: str, token: str) -> None:
    """Idempotently remove context from required status checks on repo/main."""
    path = f"/repos/{OWNER}/{repo}/branches/main/protection/required_status_checks"
    try:
        current = _api("GET", path, token=token)
        existing: list[str] = current.get("contexts", [])
    except RuntimeError:
        print(f"  [{repo}] no branch protection found, skipping removal of: {context!r}")
        return

    if context not in existing:
        print(f"  [{repo}] not present (clean), nothing to remove: {context!r}")
        return

    updated = [c for c in existing if c != context]
    _api("PATCH", path, body={"strict": False, "contexts": updated}, token=token)
    print(f"  [{repo}] removed deprecated check ({len(updated)} remaining): {context!r}")


def verify_required_checks(
    checks: list[tuple[str, str]],
    deprecated: list[tuple[str, str]],
    token: str,
) -> bool:
    """Read back branch protection state and assert it matches intent.

    Returns True if all required checks are present and no deprecated checks
    remain. Prints a FAIL line for each discrepancy so CI logs are actionable.
    """
    repos = dict.fromkeys([r for r, _ in checks + deprecated])
    ok = True
    for repo in repos:
        path = f"/repos/{OWNER}/{repo}/branches/main/protection/required_status_checks"
        try:
            current = _api("GET", path, token=token)
            actual: set[str] = set(current.get("contexts", []))
        except RuntimeError as exc:
            print(f"  [{repo}] FAIL: could not read required checks: {exc}")
            ok = False
            continue
        required = {ctx for r, ctx in checks if r == repo}
        blocked = {ctx for r, ctx in deprecated if r == repo}
        missing = required - actual
        stale = blocked & actual
        if missing:
            print(f"  [{repo}] FAIL: check not yet required: {sorted(missing)}")
            ok = False
        if stale:
            print(f"  [{repo}] FAIL: deprecated check still present: {sorted(stale)}")
            ok = False
        if not missing and not stale:
            print(f"  [{repo}] OK: {sorted(actual)}")
    return ok


def _checks_to_apply() -> list[tuple[str, str]]:
    """Return the subset of REQUIRED_CHECKS applicable to the current context."""
    github_repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not github_repository:
        return REQUIRED_CHECKS

    current_repo = github_repository.split("/", 1)[-1]
    filtered = [(repo, ctx) for repo, ctx in REQUIRED_CHECKS if repo == current_repo]
    if filtered:
        print(
            f"  Scope: GITHUB_REPOSITORY={github_repository!r} -- "
            f"applying {len(filtered)} check(s) for {current_repo!r} only"
        )
        return filtered

    print(
        f"  Warning: GITHUB_REPOSITORY={github_repository!r} did not match any "
        "entry in REQUIRED_CHECKS; applying all checks."
    )
    return REQUIRED_CHECKS


def _deprecated_to_remove() -> list[tuple[str, str]]:
    """Return the DEPRECATED_CHECKS subset applicable to the current repo context."""
    github_repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not github_repository:
        return DEPRECATED_CHECKS
    current_repo = github_repository.split("/", 1)[-1]
    return [(repo, ctx) for repo, ctx in DEPRECATED_CHECKS if repo == current_repo]


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        sys.exit(
            "Error: GITHUB_TOKEN is not set.\n"
            "Usage: GITHUB_TOKEN=ghp_xxx python3 scripts/apply_required_status_checks.py"
        )

    # Token type detection:
    #   ghs_ prefix  = GITHUB_TOKEN from Actions (scoped to current repo only).
    #                  Cannot write branch protection rules. Read-only path.
    #   ghp_ or github_pat_ = Personal Access Token. Can write branch protection
    #                  when it has Administration (read+write) on target repos.
    is_pat = not token.startswith("ghs_")

    checks = _checks_to_apply()
    deprecated = _deprecated_to_remove()
    total = len(checks)

    if not is_pat:
        # Read-only path: GITHUB_TOKEN cannot write branch protection.
        # Verify current state so push runs detect if checks were already
        # configured by a prior PAT run or via the GitHub Settings UI.
        print("=== E2E Robustness C6: read-only verify (GITHUB_TOKEN, no write access) ===")
        print()
        print("INFO: GITHUB_TOKEN cannot write branch protection rules.")
        print("INFO: To auto-apply on every push to main, set E2E_ADMIN_PAT as a")
        print("  repo secret (fine-grained PAT, Administration read+write on")
        print("  clawmetry, clawmetry-cloud, clawmetry-landing).")
        print("INFO: Manual alternative -- Settings > Branches > main >")
        print("  Required status checks > add:")
        for repo, ctx in REQUIRED_CHECKS:
            print(f"    [{repo}] {ctx!r}")
        print()
        print("=== Reading current required status checks ===")
        if verify_required_checks(checks, deprecated, token):
            print()
            print("=== C6: checks already correctly configured ===")
            print("=== (Set by manual Settings UI action or a prior PAT run.) ===")
        else:
            print()
            print("INFO: Required checks not yet configured. Next steps:")
            print("  A) Set E2E_ADMIN_PAT repo secret (see above) -- auto-applies on")
            print("     next push to main.")
            print("  B) Settings > Branches > main > Required status checks (manual).")
        # Always exit 0: push-triggered runs are informational, never blocking.
        return

    # PAT path: full apply + verify.
    print(f"=== E2E Robustness C6: applying {total} required status check(s) ===")
    for repo, context in checks:
        try:
            add_required_check(repo, context, token)
        except RuntimeError as exc:
            print(f"  ERROR [{repo}]: {exc}")
            sys.exit(1)

    if deprecated:
        print()
        print(f"=== Removing {len(deprecated)} deprecated check(s) ===")
        for repo, context in deprecated:
            try:
                remove_required_check(repo, context, token)
            except RuntimeError as exc:
                # Removal failure is non-fatal: log and continue.
                print(f"  WARNING [{repo}]: could not remove {context!r}: {exc}")

    print()
    print(f"=== {total} E2E check(s) are now required on main ===")

    if total < len(REQUIRED_CHECKS):
        print()
        print(
            "Note: to apply checks in other repos, run the equivalent workflow "
            "in clawmetry-cloud and clawmetry-landing."
        )

    print()
    print("Verify at:")
    for repo in dict.fromkeys(r for r, _ in checks):
        print(f"  https://github.com/{OWNER}/{repo}/settings/branches")

    print()
    print("=== Verification: reading back branch protection state ===")
    if not verify_required_checks(checks, deprecated, token):
        print()
        print(
            "ERROR: branch protection state does not match expected config (see above).\n"
            "If this is a 403, E2E_ADMIN_PAT may lack Administration (read+write) on "
            "this repo. Check the PAT permissions and re-run."
        )
        sys.exit(2)
    print("=== Verification passed: C6 branch protection is correctly configured ===")


if __name__ == "__main__":
    main()
