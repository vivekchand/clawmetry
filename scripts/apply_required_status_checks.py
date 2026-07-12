#!/usr/bin/env python3
"""Apply required status checks for E2E Robustness criterion C6.

This script is idempotent: running it multiple times is safe.
It adds checks listed in REQUIRED_CHECKS and removes any in DEPRECATED_CHECKS
from the main branch protection of each repo.

Usage
-----
  # Quickest path (no PAT needed -- uses your existing gh CLI session):
  bash scripts/close-c6.sh

  # Or directly with a token:
  GITHUB_TOKEN=ghp_xxx python3 scripts/apply_required_status_checks.py

Token types
-----------
GITHUB_TOKEN from Actions (prefix ghs_):
  Can read branch protection state but CANNOT write it. The script detects
  this automatically: it verifies current state (read-only, scoped to the
  current repo only) and exits 1 if not configured (red badge = forcing
  signal), exits 0 when already configured (self-heals to green on the
  next push after admin action). Push-triggered runs use this path.
  Note: requesting administration:write in the workflow permissions block is
  invalid for GITHUB_TOKEN and causes 0-job workflow failures -- do not add it.

Fine-grained PAT (prefix ghp_ or github_pat_), classic OAuth (gho_), or
any non-ghs_ token:
  Required to write branch protection rules. Needs Administration (read+write)
  or repo ownership on clawmetry, clawmetry-cloud, clawmetry-landing.
  Full apply + verify across all repos.

  Easiest way to get one: gh auth token (uses your gh CLI session, which
  already has admin rights if you own the repos -- run close-c6.sh instead
  of calling this script directly).

Primary repo behaviour (clawmetry):
  When GITHUB_REPOSITORY=vivekchand/clawmetry and using a PAT, the script
  applies ALL 6 required checks across all 3 repos in one run. This means
  you only need to trigger the apply-required-checks.yml workflow ONCE -- on
  the clawmetry repo -- to close C6 everywhere.

  When using GITHUB_TOKEN (read-only push path), only the current repo's
  checks are verified to avoid cross-repo 403s.

When run locally (GITHUB_REPOSITORY not set), the script applies all 6
checks and requires a token with cross-repo admin access.

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
# Job names verified against workflow files 2026-06-11:
#   clawmetry/.github/workflows/oss-golden-path.yml      -> "OSS golden path (wheel + OpenClaw + 9 tabs)"
#   clawmetry/.github/workflows/cross-repo-handoff.yml   -> "Cross-repo handoff (C4)"
#   clawmetry/.github/workflows/ci.yml (moat-keystone)   -> "MOAT Keystone (13-endpoint bar)"
#   clawmetry/.github/workflows/ci.yml (e2e-critical)    -> "E2E Browser Tests (critical subset)"
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
    # docs/MOAT_BAR.md Section 5, AC#1: keystone_e2e --no-drive blocks merge.
    # ci.yml `moat-keystone` job runs on every PR; job name must match exactly.
    ("clawmetry",         "MOAT Keystone (13-endpoint bar)"),
    # ci.yml `e2e-critical` job: 32-tab auth-overlay sweep (C5 gate).
    # Without this, a PR breaking tabs 10-32 fails CI but remains mergeable.
    ("clawmetry",         "E2E Browser Tests (critical subset)"),
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


def _get_branch_protection_contexts(repo: str, token: str) -> set[str] | None:
    """Read required status check contexts via the public branch endpoint.

    Uses GET /repos/{owner}/{repo}/branches/main which is accessible with
    GITHUB_TOKEN on public repos (unlike
    /branches/main/protection/required_status_checks which requires admin).

    Returns the set of configured context strings, or None if the branch
    endpoint is unreachable or returns no protection data.
    """
    path = f"/repos/{OWNER}/{repo}/branches/main"
    try:
        data = _api("GET", path, token=token)
    except RuntimeError as exc:
        print(f"  [{repo}] WARN: could not read branch info: {exc}")
        return None
    protection = data.get("protection") or {}
    rsc = protection.get("required_status_checks") or {}
    return set(rsc.get("contexts", []))


def verify_required_checks_readonly(
    checks: list[tuple[str, str]],
    deprecated: list[tuple[str, str]],
    token: str,
) -> bool:
    """Read-only variant of verify_required_checks using the branch endpoint.

    Called from the GITHUB_TOKEN (read-only) code path. Uses
    GET /repos/{owner}/{repo}/branches/main which returns protection info
    for public repos without requiring admin credentials.

    Returns True if all required checks are present and no deprecated checks
    remain. Returns False (but does not exit) if any discrepancy is found,
    so the calling code can decide how to exit.
    """
    repos = dict.fromkeys([r for r, _ in checks + deprecated])
    ok = True
    for repo in repos:
        actual = _get_branch_protection_contexts(repo, token)
        if actual is None:
            print(f"  [{repo}] UNKNOWN: branch endpoint did not return protection info")
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


def _current_repo() -> str:
    """Return the bare repo name from GITHUB_REPOSITORY, or empty string."""
    github_repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    return github_repository.split("/", 1)[-1] if github_repository else ""


def _checks_to_apply() -> list[tuple[str, str]]:
    """Return the REQUIRED_CHECKS to apply for the current context (PAT path).

    clawmetry is the primary E2E hub. When running from here with a PAT that
    has Administration (read+write) on all 3 repos, we apply all 6 required
    checks in a single run -- matching the dry-run preview in
    apply-required-checks.yml which already says 'apply to all 3 repos'.

    Other repos (clawmetry-cloud, clawmetry-landing) apply only their own
    checks; their companion apply-required-checks.yml workflows exist for
    single-repo PATs.
    """
    current_repo = _current_repo()
    if not current_repo:
        return REQUIRED_CHECKS

    # Primary hub: one run closes all 3 repos.
    if current_repo == "clawmetry":
        print(
            f"  Primary E2E hub: applying all {len(REQUIRED_CHECKS)} required check(s) "
            f"across all repos (one run = C6 closed everywhere)"
        )
        return REQUIRED_CHECKS

    filtered = [(repo, ctx) for repo, ctx in REQUIRED_CHECKS if repo == current_repo]
    if filtered:
        print(
            f"  Applying {len(filtered)} check(s) for {current_repo!r} only"
        )
        return filtered

    print(
        f"  Warning: GITHUB_REPOSITORY={current_repo!r} did not match any "
        "entry in REQUIRED_CHECKS; applying all checks."
    )
    return REQUIRED_CHECKS


def _deprecated_to_remove() -> list[tuple[str, str]]:
    """Return the DEPRECATED_CHECKS to remove for the current context (PAT path).

    clawmetry (primary hub) removes deprecated checks from all repos.
    Other repos only remove their own deprecated checks.
    """
    current_repo = _current_repo()
    if not current_repo or current_repo == "clawmetry":
        return DEPRECATED_CHECKS
    return [(repo, ctx) for repo, ctx in DEPRECATED_CHECKS if repo == current_repo]


def _readonly_scope() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (checks, deprecated) scoped to the current repo for read-only mode.

    GITHUB_TOKEN in Actions is scoped to the current repo. Attempting to GET
    branch protection for cross-repo paths returns 403 and produces noise in
    the read-only verification step. Scope to current repo only.
    """
    current_repo = _current_repo()
    if not current_repo:
        return REQUIRED_CHECKS, DEPRECATED_CHECKS
    local_checks = [(r, c) for r, c in REQUIRED_CHECKS if r == current_repo]
    local_deprecated = [(r, c) for r, c in DEPRECATED_CHECKS if r == current_repo]
    return local_checks or REQUIRED_CHECKS, local_deprecated


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        sys.exit(
            "Error: GITHUB_TOKEN is not set.\n"
            "Quickest path: bash scripts/close-c6.sh (uses gh CLI session)\n"
            "Or: GITHUB_TOKEN=ghp_xxx python3 scripts/apply_required_status_checks.py"
        )

    # Token type detection:
    #   ghs_ prefix  = GITHUB_TOKEN from Actions (scoped to current repo only).
    #                  Cannot write branch protection rules. Read-only path.
    #   Anything else = PAT or OAuth token (gho_, ghp_, github_pat_, etc.).
    #                  Full apply when token has admin/owner rights.
    is_pat = not token.startswith("ghs_")

    if not is_pat:
        # Fail clearly when confirm=APPLY was typed but only GITHUB_TOKEN is available.
        # Without this check the workflow exits 0 silently, which looks like success.
        confirm_input = os.environ.get("CONFIRM_INPUT", "").strip()
        if confirm_input.upper() == "APPLY":
            sys.exit(
                "ERROR: confirm=APPLY requires an admin token -- GITHUB_TOKEN cannot write branch protection.\n"
                "  Fix: re-run the workflow and paste a fine-grained PAT into the 'pat_token' field.\n"
                "  PAT permissions: Administration (read+write) on clawmetry, clawmetry-cloud, clawmetry-landing.\n"
                "  Alternative: bash scripts/close-c6.sh (uses your gh CLI session, ~30 sec).\n"
                "  Tracking: vivekchand/clawmetry#2146 (C6)"
            )
        # Read-only path: GITHUB_TOKEN cannot write branch protection.
        # Scope verification to the current repo only to avoid cross-repo 403s.
        local_checks, local_deprecated = _readonly_scope()
        print("=== E2E Robustness C6: read-only verify (GITHUB_TOKEN, no write access) ===")
        print()
        print("INFO: GITHUB_TOKEN cannot write branch protection rules.")
        print()
        print("INFO: Quickest path to close C6 (one run, no local setup):")
        print("  1. Create a fine-grained PAT: github.com > Settings > Developer settings")
        print("     > Fine-grained tokens > Generate. Repository access: clawmetry,")
        print("     clawmetry-cloud, clawmetry-landing. Permission: Administration (read+write).")
        print("  2. Actions > 'Apply required E2E status checks (C6 -- one-shot)' > Run workflow")
        print("     confirm=APPLY, pat_token=<paste token> > Run workflow")
        print("  Closes C6 for ALL 3 repos in one run. No local clone, no gh CLI.")
        print()
        print("INFO: Alternative -- one-liner from a terminal (uses existing gh CLI session):")
        print("  bash scripts/close-c6.sh")
        print()
        print("INFO: Manual alternative -- Settings > Branches > main >")
        print("  Required status checks > add:")
        for repo, ctx in REQUIRED_CHECKS:
            print(f"    [{repo}] {ctx!r}")
        print()
        print("=== Reading current required status checks (current repo only) ===")
        c6_ok = verify_required_checks_readonly(local_checks, local_deprecated, token)
        if c6_ok:
            print()
            print("=== C6: checks already correctly configured ===")
            print("=== (Set by manual Settings UI action or a prior admin run.) ===")
            return  # exit 0: C6 is done, self-heals to green after admin action
        print()
        print("Action needed (takes ~30 seconds) to make these checks required on main:")
        print("  bash scripts/close-c6.sh")
        print("  (Or: Actions > 'Apply required E2E status checks (C6 -- one-shot)' > Run workflow)")
        # Exit 1 so the apply-required-checks.yml workflow shows RED in the GitHub
        # Actions UI until C6 is configured. The module-level docstring specifies
        # this: "exit 1 if not configured (red badge = forcing signal)". Once the
        # admin runs scripts/close-c6.sh, the next push to main goes green and
        # stays green permanently. This workflow is NOT in REQUIRED_CHECKS, so
        # it cannot block PR merges; it only creates a visible badge on main.
        sys.exit(1)

    # PAT / OAuth path: full apply + verify across all repos.
    checks = _checks_to_apply()
    deprecated = _deprecated_to_remove()
    total = len(checks)

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
            "If this is a 403, your token may lack admin rights on this repo.\n"
            "Run 'gh auth status' to verify your gh CLI session has the repo scope,\n"
            "then re-run: bash scripts/close-c6.sh"
        )
        sys.exit(2)
    print("=== Verification passed: C6 branch protection is correctly configured ===")


if __name__ == "__main__":
    main()
