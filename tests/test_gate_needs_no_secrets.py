"""A merge-blocking check must have a path to green without privileged secrets.

If a check in ``scripts/e2e_gate.py``'s ``REQUIRED_SPECS`` *requires* a repo
secret, anyone without that secret has **no path to green**: their pull request
cannot merge and nothing they do fixes it. The only ways out are to weaken the
gate or to normalise a red check, and both destroy what the gate is for.

Concretely it bites a fork (which never receives secrets), an outside
contributor, and everyone with an open PR the moment a credential rotates.

The rule is about REACHABILITY, not about mentioning a secret. A gated job may
read one, provided it detects the absence and still completes. The first draft
of this guard banned the reference itself and immediately flagged
``Cross-repo handoff (C4)``, which turned out to be correct code: it detects
``CLOUD_REPO_PAT``, prints "T2/T3/T4 will use inline stubs -- all four tiers
still run", and runs its pytest step unconditionally. The workflow's declared
behaviour outranks a test's expectation, so the test was the thing that was
wrong.

Hence :data:`DEGRADES_WITHOUT_SECRETS`: an explicit, justified exception list
rather than a blanket exemption. Adding an entry is a deliberate, reviewable
act that must state how the job stays green without the secret. Silence is not
an option, and neither is deleting the guard.

``GITHUB_TOKEN`` is exempt outright: GitHub mints it for every run, forks
included, so it can never be the thing that blocks someone.
"""
from __future__ import annotations

import glob
import os
import re
import sys

import pytest
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")

sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from e2e_gate import REQUIRED_SPECS  # noqa: E402

# Minted automatically for every run, forks included.
ALWAYS_AVAILABLE = {"GITHUB_TOKEN"}

# Gated jobs that reference a secret but are VERIFIED to complete without it.
# The value is the evidence, not a rubber stamp. Verify before adding: find the
# detection step, and confirm the work that produces the job's verdict still
# runs on the unavailable path.
DEGRADES_WITHOUT_SECRETS = {
    "Cross-repo handoff (C4)": (
        "Reads CLOUD_REPO_PAT only in its 'Detect cloud-repo access' step, "
        "which sets steps.access.outputs.available and emits a ::notice:: "
        "saying 'T2/T3/T4 will use inline stubs -- all four tiers still run'. "
        "Every private-repo checkout is gated on available=='true', and the "
        "'Run C4 cross-repo handoff' pytest step is unconditional, so a fork "
        "runs all four tiers against stubs and can still go green."
    ),
}

# Only a real GitHub expression counts. A bare `secrets\.` substring matches
# prose and filenames too: this guard's own step, which runs
# `tests/test_gate_needs_no_secrets.py`, was flagged by the looser pattern
# because the filename contains "secrets.py".
_SECRET_REF = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)")


def _workflow_files() -> list:
    files = []
    for ext in ("yml", "yaml"):
        files.extend(glob.glob(os.path.join(WORKFLOW_DIR, f"*.{ext}")))
    return sorted(files)


def _jobs_by_display_name() -> dict:
    """Map each job's reported check name to (workflow, job yaml text).

    The name GitHub reports is the job's ``name:`` when present, else the job
    id. Matrix placeholders are left intact, which is fine because the gate
    matches with globs: ``API Tests (*)`` matches ``API Tests (${{ matrix.os }})``.
    """
    out = {}
    for path in _workflow_files():
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        try:
            doc = yaml.safe_load(source)
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        for job_id, job in (doc.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            display = job.get("name") or job_id
            # Scope the scan to this job; a sibling job's secret is not its
            # problem.
            out[str(display)] = (os.path.basename(path), yaml.safe_dump(job))
    return out


def _gated_jobs() -> list:
    """(spec_label, check_name, workflow, job_yaml) for every gated job."""
    found = []
    for display, (workflow, job_yaml) in _jobs_by_display_name().items():
        for spec in REQUIRED_SPECS:
            if spec.matches(display):
                found.append((spec.label, display, workflow, job_yaml))
                break
    return found


def test_gated_jobs_are_discoverable() -> None:
    """If this finds nothing, everything below passes vacuously."""
    assert _gated_jobs(), (
        "No workflow job matched any REQUIRED_SPEC pattern. Either the gate is "
        "empty or job names drifted from the patterns in scripts/e2e_gate.py. "
        "Either way the checks below would prove nothing."
    )


@pytest.mark.parametrize(
    "entry",
    _gated_jobs(),
    ids=lambda e: f"{e[2]}::{e[1]}",
)
def test_gated_job_is_reachable_without_privileged_secrets(entry) -> None:
    label, display, workflow, job_yaml = entry
    referenced = set(_SECRET_REF.findall(job_yaml)) - ALWAYS_AVAILABLE
    if not referenced:
        return

    justification = DEGRADES_WITHOUT_SECRETS.get(display)
    assert justification, (
        f"{workflow} job {display!r} is merge-blocking as {label!r} and "
        f"references {sorted(referenced)}.\n\n"
        "A gated check that REQUIRES a privileged secret leaves forks, outside "
        "contributors, and everyone affected by a credential rotation with no "
        "path to green.\n\n"
        "Two legitimate resolutions:\n"
        "  1. Make the job degrade: detect the secret's absence and still "
        "produce a verdict, then add it to DEGRADES_WITHOUT_SECRETS here with "
        "the evidence.\n"
        "  2. Take it out of REQUIRED_SPECS in scripts/e2e_gate.py and run it "
        "unblocked, on a schedule, or in the conformance heartbeat.\n\n"
        "Weakening or deleting this guard is not one of them."
    )
    assert len(justification) > 80, (
        f"{display!r} has a DEGRADES_WITHOUT_SECRETS entry that is too short "
        "to be evidence. State which step detects the secret and which step "
        "still produces the verdict without it."
    )


def test_exception_list_has_no_stale_entries() -> None:
    """An entry for a job that no longer needs one hides the next real case."""
    gated = {display for _, display, _, _ in _gated_jobs()}
    jobs = _jobs_by_display_name()

    for display in DEGRADES_WITHOUT_SECRETS:
        assert display in gated, (
            f"{display!r} is listed in DEGRADES_WITHOUT_SECRETS but is no "
            "longer a gated check. Remove the entry so the list stays a real "
            "inventory."
        )
        _, job_yaml = jobs[display]
        referenced = set(_SECRET_REF.findall(job_yaml)) - ALWAYS_AVAILABLE
        assert referenced, (
            f"{display!r} no longer references any privileged secret, so its "
            "exception is obsolete. Remove it."
        )


def test_exception_list_stays_small() -> None:
    """A ratchet. Exceptions may shrink freely; growth must be deliberate."""
    assert len(DEGRADES_WITHOUT_SECRETS) <= 1, (
        f"DEGRADES_WITHOUT_SECRETS has grown to "
        f"{len(DEGRADES_WITHOUT_SECRETS)} entries. Each one is a gated check "
        "that only stays reachable because someone verified a fallback path. "
        "If this is genuinely correct, raise the bound in the same PR and say "
        "why, so the growth is visible rather than absorbed."
    )
