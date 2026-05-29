#!/usr/bin/env python3
"""Apply required status checks for E2E Robustness criterion C6.

This script is idempotent: running it multiple times is safe.
It adds the named E2E job checks without removing any existing
required status checks on main.

Usage
-----
  GITHUB_TOKEN=ghp_xxx python3 scripts/apply_required_status_checks.py

Requirements
------------
A fine-grained PAT (or classic token) with:
  - Repository access: clawmetry, clawmetry-cloud, clawmetry-landing
  - Permissions: Administration (read + write) on each repo
    (required to modify branch protection rules)

If branch protection does not yet exist on main, the script creates a
minimal protection rule first (no push restrictions, no required reviews)
before adding the status checks. Existing protection rules are preserved.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

OWNER = "vivekchand"

# Each tuple: (repo, exact job name as it appears in the workflow's `name:` field)
REQUIRED_CHECKS: list[tuple[str, str]] = [
    ("clawmetry",         "OSS golden path (wheel + OpenClaw + 9 tabs)"),
    ("clawmetry-cloud",   "Cloud golden-path browser E2E"),
    ("clawmetry-cloud",   "cross-repo handoff golden path"),
    ("clawmetry-landing", "Landing golden path (hero + CTA + subscribe + cloud handoff)"),
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


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        sys.exit(
            "Error: GITHUB_TOKEN is not set.\n"
            "Usage: GITHUB_TOKEN=ghp_xxx python3 scripts/apply_required_status_checks.py"
        )

    print("=== E2E Robustness C6: applying required status checks ===")
    for repo, context in REQUIRED_CHECKS:
        try:
            add_required_check(repo, context, token)
        except RuntimeError as exc:
            print(f"  ERROR [{repo}]: {exc}")
            sys.exit(1)

    print()
    print("=== All 4 E2E checks are now required on main ===")
    print()
    print("Verify at:")
    for repo, _ in dict.fromkeys((r for r, _ in REQUIRED_CHECKS)):
        print(f"  https://github.com/{OWNER}/{repo}/settings/branches")


if __name__ == "__main__":
    main()
