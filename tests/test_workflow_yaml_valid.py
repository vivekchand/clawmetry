"""Every GitHub Actions workflow must actually parse.

A workflow whose YAML is malformed does not fail loudly: GitHub accepts the
push, then fails the run at *startup*, before any step executes. The run shows
up in the Actions list named after the FILE PATH rather than the workflow's
declared ``name:`` -- which is easy to skim past for months.

That is not hypothetical. ``.github/workflows/c6-schedule-heal.yml`` embedded a
``python3 -c "`` block whose Python body started at column 0, which terminates
the enclosing ``run: |`` literal block. Every scheduled run since had failed at
startup, which meant **the workflow that auto-heals required-status-check
configuration had never once run**. The C6 safety net was itself dead, and the
only symptom was a red X on a workflow named after its own path.

This guard auto-discovers every workflow file, so a newly added workflow is
covered without anyone maintaining a list (the FLYWHEEL rule: prefer
auto-discovery over allowlists, which silently drift).
"""
from __future__ import annotations

import glob
import os

import pytest
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")


def _workflow_files() -> list[str]:
    files: list[str] = []
    for ext in ("yml", "yaml"):
        files.extend(glob.glob(os.path.join(WORKFLOW_DIR, f"*.{ext}")))
    return sorted(files)


def _load_or_skip(path: str) -> dict:
    """Parse a workflow, or skip.

    The shape checks below would each re-raise the same parse error, turning
    one broken file into three near-identical failures. Skipping here keeps
    ``test_workflow_parses_as_yaml`` as the single, readable signal.
    """
    with open(path, encoding="utf-8") as fh:
        try:
            return yaml.safe_load(fh)
        except yaml.YAMLError:
            pytest.skip("file does not parse; see test_workflow_parses_as_yaml")


def test_workflow_directory_is_discoverable() -> None:
    """Fail loudly if the glob stops finding anything (a moved directory)."""
    assert _workflow_files(), (
        f"No workflow files found under {WORKFLOW_DIR}. If workflows moved, "
        "update WORKFLOW_DIR -- do not let this guard silently pass on zero files."
    )


@pytest.mark.parametrize("path", _workflow_files(), ids=os.path.basename)
def test_workflow_parses_as_yaml(path: str) -> None:
    """The file must parse. A startup failure is invisible until you look."""
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    try:
        doc = yaml.safe_load(source)
    except yaml.YAMLError as exc:  # pragma: no cover - message is the point
        pytest.fail(
            f"{os.path.basename(path)} is not valid YAML, so GitHub will fail "
            f"the run at startup before any step executes:\n\n{exc}\n\n"
            "Common cause: an embedded script inside a 'run: |' block whose "
            "lines start at column 0. Every line of a literal block must be "
            "indented past the block marker. Extract the script to scripts/ "
            "and call it instead of inlining it."
        )

    assert isinstance(doc, dict), (
        f"{os.path.basename(path)} did not parse to a mapping."
    )


@pytest.mark.parametrize("path", _workflow_files(), ids=os.path.basename)
def test_workflow_has_required_top_level_keys(path: str) -> None:
    """A parseable file can still be a non-workflow. Check the shape."""
    doc = _load_or_skip(path)

    # PyYAML resolves the bare token `on` to boolean True (YAML 1.1), so a
    # workflow's trigger key arrives as either "on" or True depending on
    # whether it was quoted. Accept both rather than demanding one style.
    has_trigger = "on" in doc or True in doc
    assert has_trigger, (
        f"{os.path.basename(path)} has no 'on:' trigger block."
    )
    assert "jobs" in doc and isinstance(doc["jobs"], dict) and doc["jobs"], (
        f"{os.path.basename(path)} declares no jobs."
    )


@pytest.mark.parametrize("path", _workflow_files(), ids=os.path.basename)
def test_every_job_declares_runs_on(path: str) -> None:
    """A job without runs-on is a startup failure too."""
    doc = _load_or_skip(path)

    for job_id, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            pytest.fail(f"{os.path.basename(path)}: job {job_id!r} is not a mapping.")
        # A `uses:` job calls a reusable workflow and supplies no runner.
        if "uses" in job:
            continue
        assert "runs-on" in job, (
            f"{os.path.basename(path)}: job {job_id!r} has no 'runs-on'."
        )
