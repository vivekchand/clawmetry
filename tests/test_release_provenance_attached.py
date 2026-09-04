"""Every release must ship its artifacts and their provenance.

Before this guard, a published release carried ten desktop installers and
nothing else: no signature, no provenance, no wheel. Anyone auditing a download
had to take our word for what produced it, and OpenSSF Scorecard's
Signed-Releases check scored the repo 0/10 for exactly that reason.

The upload is deliberately non-blocking (``|| echo``), because the wheel is
already on PyPI by the time it runs and a failed upload must not fail a
completed release. That tolerance is precisely how the desktop-artifacts
dispatch broke silently with an HTTP 403, so the *wiring* is asserted here
rather than trusted to stay in place.

Two things have to hold together, and neither is sufficient alone:

* the attestation must be **minted** -- which needs ``id-token: write`` on the
  job, or ``actions/attest-build-provenance`` fails rather than warning; and
* the attestation must be **attached**, under a ``.intoto.jsonl`` name, or it
  exists only inside a deleted runner.
"""
from __future__ import annotations

import os

import pytest
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")

# release-on-merge.yml is the workflow that actually runs for an auto-release;
# publish.yml covers a hand-pushed tag. Both must attach provenance, or which
# path cut the release would decide whether it is verifiable.
RELEASE_WORKFLOWS = ("release-on-merge.yml", "publish.yml")

ATTEST_ACTION = "actions/attest-build-provenance"


def _read(name: str) -> str:
    with open(os.path.join(WORKFLOW_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def _job_for(name: str) -> dict:
    doc = yaml.safe_load(_read(name))
    jobs = doc["jobs"]
    # Each of these workflows has exactly one job that builds and releases.
    assert len(jobs) == 1, f"{name} gained a second job; update this guard"
    return next(iter(jobs.values()))


@pytest.mark.parametrize("workflow", RELEASE_WORKFLOWS)
def test_workflow_mints_provenance(workflow: str) -> None:
    source = _read(workflow)
    assert ATTEST_ACTION in source, (
        f"{workflow} no longer runs {ATTEST_ACTION}.\n\n"
        "Without it the release has no provenance and a downloader cannot "
        "verify what built the artifact."
    )


@pytest.mark.parametrize("workflow", RELEASE_WORKFLOWS)
def test_provenance_step_is_addressable(workflow: str) -> None:
    """The attest step needs an `id:` or its bundle-path output is unreachable."""
    job = _job_for(workflow)
    steps = [s for s in job.get("steps", []) if ATTEST_ACTION in str(s.get("uses", ""))]
    assert steps, f"{workflow} has no {ATTEST_ACTION} step"
    for step in steps:
        assert step.get("id") == "attest", (
            f"{workflow}'s provenance step must keep `id: attest`; the upload "
            "reads steps.attest.outputs.bundle-path, which silently resolves to "
            "an empty string if the id changes -- and the upload is "
            "non-blocking, so the release would simply lose its provenance."
        )


@pytest.mark.parametrize("workflow", RELEASE_WORKFLOWS)
def test_job_can_mint_and_upload(workflow: str) -> None:
    perms = _job_for(workflow).get("permissions") or {}
    assert perms.get("id-token") == "write", (
        f"{workflow} needs `id-token: write`; attest-build-provenance FAILS "
        "without the OIDC token rather than degrading."
    )
    assert perms.get("attestations") == "write", (
        f"{workflow} needs `attestations: write` to record the attestation."
    )
    assert perms.get("contents") == "write", (
        f"{workflow} needs `contents: write` to upload release assets."
    )


@pytest.mark.parametrize("workflow", RELEASE_WORKFLOWS)
def test_artifacts_and_provenance_are_uploaded(workflow: str) -> None:
    source = _read(workflow)
    assert "gh release upload" in source, (
        f"{workflow} no longer uploads anything to the GitHub release."
    )
    assert ".intoto.jsonl" in source, (
        f"{workflow} must attach the attestation under a `.intoto.jsonl` name. "
        "That suffix is the convention consumers and scanners look for; an "
        "attestation attached under any other name is not discoverable."
    )
    assert "dist/*.whl" in source and "dist/*.tar.gz" in source, (
        f"{workflow} must attach the wheel and sdist, not just the provenance. "
        "Provenance for artifacts that are not on the release is unverifiable."
    )


@pytest.mark.parametrize("workflow", RELEASE_WORKFLOWS)
def test_uploads_never_fail_a_completed_release(workflow: str) -> None:
    """The wheel is already on PyPI by upload time; a 403 must not fail it."""
    source = _read(workflow)
    for line in source.splitlines():
        if "gh release upload" in line:
            block = source[source.index(line):source.index(line) + 400]
            assert "|| echo" in block, (
                f"{workflow} has a blocking `gh release upload`. The release is "
                "already published to PyPI at that point, so a failed upload "
                "must warn, not fail."
            )
