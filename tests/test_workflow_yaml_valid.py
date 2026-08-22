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


def _conftest_module_level_imports() -> set:
    """Third-party modules tests/conftest.py imports at module scope.

    pytest imports conftest before collecting anything, so a missing one of
    these is not a test failure -- it is exit code 4, "could not collect", with
    zero tests run. A job that installs an incomplete set therefore reports a
    hard failure that looks nothing like the thing it was meant to check.
    """
    conftest = os.path.join(REPO_ROOT, "tests", "conftest.py")
    if not os.path.isfile(conftest):
        return set()

    import ast

    with open(conftest, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())

    stdlib_ish = {
        "os", "sys", "re", "json", "time", "glob", "shutil", "socket",
        "signal", "typing", "pathlib", "tempfile", "subprocess", "threading",
        "datetime", "urllib", "collections", "contextlib", "functools",
        "itertools", "warnings", "logging", "uuid", "base64", "hashlib",
        "random", "string", "textwrap", "traceback", "pytest", "clawmetry",
        "dashboard", "sqlite3", "csv", "io", "math", "copy", "ast",
    }

    found = set()
    for node in tree.body:  # module scope only
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return {m for m in found if m not in stdlib_ish}


def _jobs_running_pytest() -> list:
    """(workflow, job_id, install_text) for every job that invokes pytest."""
    out = []
    for path in _workflow_files():
        with open(path, encoding="utf-8") as fh:
            try:
                doc = yaml.safe_load(fh)
            except yaml.YAMLError:
                continue
        if not isinstance(doc, dict):
            continue
        for job_id, job in (doc.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            steps = job.get("steps") or []
            runs = " ".join(
                str(s.get("run", "")) for s in steps if isinstance(s, dict)
            )
            if "pytest" in runs:
                out.append((os.path.basename(path), job_id, runs))
    return out


@pytest.mark.parametrize(
    "entry",
    _jobs_running_pytest(),
    ids=lambda e: f"{e[0]}::{e[1]}",
)
def test_pytest_jobs_install_what_conftest_needs(entry) -> None:
    """A job that runs pytest must install conftest's module-scope imports.

    Burned twice in one pull request: both new verification jobs installed a
    minimal dependency set, and because tests/conftest.py imports `requests` at
    module scope, pytest exited 4 before collecting a single test. The job went
    red for a reason unrelated to what it was checking.

    Auto-discovered from conftest rather than hard-coded, so adding an import
    there surfaces every job that now needs it, instead of waiting for CI to
    fail one job at a time.
    """
    workflow, job_id, runs = entry
    needed = _conftest_module_level_imports()
    if not needed:
        pytest.skip("conftest has no third-party module-scope imports")

    # Jobs that install from a requirements file or the package itself pull
    # dependencies transitively; only explicit `pip install a b c` lines are
    # checked, since those are the ones that can silently omit something.
    if "-r " in runs or "pip install ." in runs or "pip install -e" in runs:
        pytest.skip("installs from a requirements file or the package itself")

    missing = [m for m in sorted(needed) if m not in runs]
    assert not missing, (
        f"{workflow} job {job_id!r} runs pytest but never installs "
        f"{missing}, which tests/conftest.py imports at module scope. "
        "pytest will exit 4 (collection error) before running a single test, "
        "so the job fails for a reason unrelated to what it checks."
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
