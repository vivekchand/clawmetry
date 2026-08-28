#!/usr/bin/env python3
"""Report whether the required status checks are actually configured on ``main``.

This is the read-only half of the C6 auto-heal loop. It used to live inline in
``.github/workflows/c6-schedule-heal.yml`` as a ``run: |`` block containing a
``python3 -c "`` string whose Python body started at column 0. That column-0
body terminated the enclosing YAML literal block, so the workflow was
**unparseable and failed at startup on every single run** -- meaning the
mechanism that watches branch protection had never executed. The alarm designed
to tell you the gate was open was itself broken, and its only symptom was a run
named after its own file path.

Extracting it here fixes that permanently: a script file cannot break the
workflow's YAML, and it can be unit-tested. ``tests/test_workflow_yaml_valid.py``
now auto-discovers and parses every workflow so the class cannot recur.

Reads required contexts from BOTH sources, because either can carry them:

* classic branch protection -- ``contexts`` (legacy, written by script/API) and
  ``checks`` (current, written by the Settings UI);
* the Rulesets API, which ``c6-apply-ruleset.yml`` uses when ``GITHUB_TOKEN``
  has ruleset-write rights but no admin PAT is available.

Only same-repo reads are authoritative. ``GITHUB_TOKEN`` gets 403 on private
sibling repos, so those are reported as "cannot verify" and deliberately do NOT
fail the gate -- treating a 403 as "missing" was a real false-negative that kept
C6 permanently red.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

OWNER = os.environ.get("OWNER", "vivekchand")

# DERIVED, not duplicated. This list used to be a hand-maintained copy of
# REQUIRED_CHECKS with a "keep in sync" comment on top, which is the same
# arrangement that let three cost surfaces disagree about what a week is. A
# comment is not a mechanism. Importing the real list means adding a required
# check in one place cannot leave this reporter quietly describing the old set.
#
# "E2E Gate (required)" aggregates the underlying OSS checks (scripts/e2e_gate.py),
# so one entry covers that whole family.
def _expected_from_source():
    import importlib.util

    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "apply_required_status_checks.py")
    spec = importlib.util.spec_from_file_location("_c6_required", src_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    grouped: dict = {}
    for repo, check in mod.REQUIRED_CHECKS:
        grouped.setdefault(repo, []).append(check)
    return grouped


EXPECTED = _expected_from_source()

AUTHORITATIVE = ["clawmetry"]
CROSS_REPO = ["clawmetry-cloud", "clawmetry-landing"]


def _gh_api(path: str, timeout: int = 20):
    """Call `gh api <path>` and return parsed JSON, or None on any failure."""
    try:
        proc = subprocess.run(
            ["gh", "api", path, "--header", "Accept: application/vnd.github+json"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def protection_contexts(repo: str) -> set:
    """Required contexts from classic branch protection on main."""
    data = _gh_api(f"/repos/{OWNER}/{repo}/branches/main")
    if not isinstance(data, dict):
        return set()
    rsc = ((data.get("protection") or {}).get("required_status_checks")) or {}
    contexts = set(rsc.get("contexts") or [])
    for item in rsc.get("checks") or []:
        if isinstance(item, dict) and item.get("context"):
            contexts.add(item["context"])
    return contexts


def ruleset_contexts(repo: str) -> set:
    """Required contexts from any ACTIVE ruleset on the repo."""
    rulesets = _gh_api(f"/repos/{OWNER}/{repo}/rulesets")
    if not isinstance(rulesets, list):
        return set()
    contexts = set()
    for ruleset in rulesets:
        if ruleset.get("enforcement") != "active":
            continue
        detail = _gh_api(f"/repos/{OWNER}/{repo}/rulesets/{ruleset.get('id')}")
        if not isinstance(detail, dict):
            continue
        for rule in detail.get("rules") or []:
            if rule.get("type") != "required_status_checks":
                continue
            params = rule.get("parameters") or {}
            for check in params.get("required_status_checks") or []:
                if check.get("context"):
                    contexts.add(check["context"])
    return contexts


def configured_contexts(repo: str) -> set:
    """Union of both configuration paths -- either one counts as enforced."""
    return protection_contexts(repo) | ruleset_contexts(repo)


def build_report() -> tuple[bool, list[str]]:
    """Return (all_authoritative_checks_present, markdown table rows)."""
    all_ok = True
    rows: list[str] = []

    for repo in AUTHORITATIVE:
        present = configured_contexts(repo)
        for check in EXPECTED.get(repo, []):
            if check in present:
                icon = ":white_check_mark:"
            else:
                icon = ":x:"
                all_ok = False
            rows.append(f"| {repo} | {check} | {icon} |")

    for repo in CROSS_REPO:
        for check in EXPECTED.get(repo, []):
            rows.append(
                f"| {repo} | {check} | :grey_question: cannot verify (cross-repo) |"
            )

    return all_ok, rows


def render_summary(all_ok: bool, rows: list[str]) -> str:
    out = ["## C6: Required E2E Status Checks", ""]
    if all_ok:
        out += [
            "> :white_check_mark: **clawmetry/main: all required checks "
            "configured.** C6 gate is GREEN.",
            ">",
            "> clawmetry-cloud and clawmetry-landing cannot be verified "
            "cross-repo (GITHUB_TOKEN scope limit).",
        ]
    else:
        out += [
            "> :x: **clawmetry/main: one or more required checks are not "
            "enforced.**",
            ">",
            "> E2E tests can pass while PRs merge with them red -- the checks "
            "are not required.",
        ]
    out += ["", "| Repo | Check | Status |", "|------|-------|--------|"]
    out += rows
    out += [""]
    if not all_ok:
        out += [
            "### Close C6",
            "",
            "**Settings UI (no PAT, ~60s):** "
            "[clawmetry Settings > Branches]"
            "(https://github.com/vivekchand/clawmetry/settings/branches) "
            "-> edit main -> Require status checks -> add `E2E Gate (required)`.",
            "",
            "**Or store a PAT** as the `E2E_ADMIN_PAT` secret and this "
            "workflow heals it automatically.",
            "",
            "Tracking: [#5266](https://github.com/vivekchand/clawmetry/issues/5266)",
        ]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--print-only",
        action="store_true",
        help="write the report to stdout instead of the GitHub step summary",
    )
    args = ap.parse_args()

    all_ok, rows = build_report()
    summary = render_summary(all_ok, rows)

    print(summary)

    if not args.print_only:
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as fh:
                fh.write(summary + "\n")
        output_path = os.environ.get("GITHUB_OUTPUT")
        if output_path:
            with open(output_path, "a", encoding="utf-8") as fh:
                fh.write(f"checks_ok={'true' if all_ok else 'false'}\n")

    # Always exit 0: this step reports state. The workflow decides whether a
    # missing check is fatal, so an API hiccup here never masks that decision.
    return 0


if __name__ == "__main__":
    sys.exit(main())
