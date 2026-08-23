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
import sys
import textwrap

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY_SCRIPT = os.path.join(REPO_ROOT, "scripts", "apply_required_status_checks.py")
STATUS_SCRIPT = os.path.join(REPO_ROOT, "scripts", "c6_required_checks_status.py")
HEALTH_WORKFLOW = os.path.join(REPO_ROOT, ".github", "workflows", "c6-health.yml")


def _load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # Register before executing: @dataclass resolves annotations through
    # sys.modules[cls.__module__], which is None for a module that is still
    # only half-imported, and e2e_gate.py defines frozen dataclasses at import.
    sys.modules[name] = mod
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


def test_drift_bot_gates_through_the_aggregator():
    """Regression pin for the rule FLYWHEEL 1f states.

    #5089 merged with drift-bot red, and clawmetry-cloud #2089 the day after,
    because the rule lived only in prose. drift-bot is a commit status with no
    re-run button: red is permanent once merged, so it has to block before.

    It gates from inside REQUIRED_SPECS rather than as a second
    branch-protection context: ADR-001 says protection names exactly one
    context, and scripts/e2e_gate.py is that context. The first attempt at this
    added a second name and drift-bot itself flagged the contradiction.
    """
    gate = _load(os.path.join(REPO_ROOT, "scripts", "e2e_gate.py"), "_e2e_gate")
    patterns = [s.pattern for s in gate.REQUIRED_SPECS]
    assert "drift-bot" in patterns, (
        "drift-bot must stay in REQUIRED_SPECS; a check not listed there "
        "cannot block a merge"
    )


def test_branch_protection_names_exactly_one_context_per_repo():
    """ADR-001. A second context is drift between the gate and its design."""
    for repo, checks in _grouped_required().items():
        assert len(checks) == 1, (
            "%s declares %d required contexts; ADR-001 allows one, with "
            "everything else aggregated behind it" % (repo, len(checks))
        )


@pytest.mark.parametrize("repo", ["clawmetry", "clawmetry-cloud", "clawmetry-landing"])
def test_every_declared_repo_has_at_least_one_required_check(repo):
    assert _grouped_required().get(repo), "%s declares no required check" % repo


# ── commit statuses are a second surface the gate must read ─────────────────

def _gate():
    return _load(os.path.join(REPO_ROOT, "scripts", "e2e_gate.py"), "_e2e_gate")


@pytest.mark.parametrize("state,expected_status,expected_conclusion", [
    ("success", "completed", "success"),
    ("failure", "completed", "failure"),
    # GitHub's transport-level failure. Blocks exactly like "failure": a broken
    # reporter must not be softer than a reporting failure.
    ("error", "completed", "failure"),
    # Not decided yet -- the gate must WAIT, never pass.
    ("pending", "in_progress", None),
    # Anything GitHub adds later defaults to "keep waiting", not "let it through".
    ("some_future_state", "in_progress", None),
])
def test_commit_status_states_map_to_check_run_shape(
    monkeypatch, state, expected_status, expected_conclusion
):
    gate = _gate()
    payload = {"statuses": [{"context": "drift-bot", "state": state}]}

    class _Resp:
        def read(self):
            import json as _j
            return _j.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(gate.urllib.request, "urlopen", lambda *a, **k: _Resp())
    shaped = gate.list_commit_statuses("o/r", "sha", "tok")
    assert shaped == [
        {"name": "drift-bot", "status": expected_status, "conclusion": expected_conclusion}
    ]


def test_a_pending_drift_bot_does_not_pass_the_gate():
    """The failure that matters: a status not yet posted must not read as green."""
    gate = _gate()
    spec = next(s for s in gate.REQUIRED_SPECS if s.pattern == "drift-bot")
    runs = [{"name": "drift-bot", "status": "in_progress", "conclusion": None}]
    (result,) = gate.evaluate([spec], runs)
    assert result.state == "pending"


def test_a_failed_drift_bot_fails_the_gate():
    gate = _gate()
    spec = next(s for s in gate.REQUIRED_SPECS if s.pattern == "drift-bot")
    runs = [{"name": "drift-bot", "status": "completed", "conclusion": "failure"}]
    (result,) = gate.evaluate([spec], runs)
    assert result.state == "failed"


def test_a_missing_drift_bot_does_not_pass_the_gate():
    """No status at all must block, not silently satisfy the spec."""
    gate = _gate()
    spec = next(s for s in gate.REQUIRED_SPECS if s.pattern == "drift-bot")
    (result,) = gate.evaluate([spec], [])
    assert result.state == "pending"
