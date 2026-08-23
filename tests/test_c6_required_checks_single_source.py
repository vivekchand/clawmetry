"""The required-checks list must have exactly one source of truth.

Which status checks block a merge was, until this file existed, written down in
three places: ``REQUIRED_CHECKS`` in ``scripts/apply_required_status_checks.py``
(which applies them), ``EXPECTED`` in ``scripts/c6_required_checks_status.py``
(which reports them), and ``ALL_CHECKS`` inline in
``.github/workflows/c6-health.yml`` (which alerts on them). Each carried a
"keep in sync" comment, and a comment is not a mechanism.

This repo has already paid for that arrangement elsewhere: three cost surfaces
each defined "this week" for themselves, and #5080 had to go and reconcile
them. A merge gate that disagrees with its own health report is the same bug
with worse consequences, because the thing it silently gets wrong is what is
allowed to reach main.

``c6_required_checks_status.py`` now imports the real list, so that copy is
gone by construction. The workflow is inline YAML and cannot import Python, so
it stays a copy and this file is what stops it drifting.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import textwrap

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY_SCRIPT = os.path.join(REPO_ROOT, "scripts", "apply_required_status_checks.py")
STATUS_SCRIPT = os.path.join(REPO_ROOT, "scripts", "c6_required_checks_status.py")
HEALTH_WORKFLOW = os.path.join(REPO_ROOT, ".github", "workflows", "c6-health.yml")


def _load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _grouped_required() -> dict:
    mod = _load(APPLY_SCRIPT, "_apply_required")
    grouped: dict = {}
    for repo, check in mod.REQUIRED_CHECKS:
        grouped.setdefault(repo, []).append(check)
    return grouped


def _workflow_all_checks() -> dict:
    """Pull the ALL_CHECKS literal out of the workflow's inline Python block."""
    with open(HEALTH_WORKFLOW, encoding="utf-8") as fh:
        text = fh.read()
    match = re.search(r"ALL_CHECKS = (\{.*?\n\s*\})\n", text, re.S)
    assert match, "ALL_CHECKS literal not found in c6-health.yml"
    return ast.literal_eval(textwrap.dedent(match.group(1)))


def test_health_workflow_matches_the_required_checks_source():
    required = _grouped_required()
    workflow = _workflow_all_checks()
    assert {k: sorted(v) for k, v in workflow.items()} == {
        k: sorted(v) for k, v in required.items()
    }, (
        "c6-health.yml ALL_CHECKS has drifted from REQUIRED_CHECKS in "
        "scripts/apply_required_status_checks.py. Update the workflow to match; "
        "do not edit this test to agree with the drift."
    )


def test_status_reporter_derives_rather_than_duplicates():
    """EXPECTED must be computed from REQUIRED_CHECKS, not retyped beside it."""
    status = _load(STATUS_SCRIPT, "_c6_status")
    assert {k: sorted(v) for k, v in status.EXPECTED.items()} == {
        k: sorted(v) for k, v in _grouped_required().items()
    }


def test_drift_bot_is_required_on_the_repos_that_run_it():
    """Regression pin for the rule FLYWHEEL 1f states.

    #5089 merged with drift-bot red, and clawmetry-cloud #2089 the day after,
    because the rule lived only in prose. drift-bot is a commit status with no
    re-run button: red is permanent once merged, so it has to block before.
    """
    required = _grouped_required()
    for repo in ("clawmetry", "clawmetry-cloud"):
        assert "drift-bot" in required.get(repo, []), (
            "drift-bot must stay a required check on %s" % repo
        )


@pytest.mark.parametrize("repo", ["clawmetry", "clawmetry-cloud", "clawmetry-landing"])
def test_every_declared_repo_has_at_least_one_required_check(repo):
    assert _grouped_required().get(repo), "%s declares no required check" % repo
