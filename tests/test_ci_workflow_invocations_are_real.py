"""Guard: CI steps that silently do nothing.

Two real defects, both of which reported success for months:

1. `ci.yml` ran `ruff check ... --ignore E501,W503`. `W503` is a flake8 code
   ruff does not implement, so ruff exited with a usage error on every run and
   `|| true` swallowed it. The step was green and linted nothing.

2. `auto-deploy-cloud.yml` had no trigger that fires after a release, so the
   cloud pin silently stayed a version behind. The fix adds a `workflow_run`
   trigger, and a `workflow_run` naming a workflow that does not exist never
   fires and never warns, which would reintroduce the same silence.

Both checks derive their scope from the workflow files, so a NEW step or
trigger is covered without editing this test.
"""
import glob
import os
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS = sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")))


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_workflows_exist():
    assert WORKFLOWS, "no workflow files discovered"


# ---------------------------------------------------------- ruff invocations

_RUFF_RE = re.compile(r"ruff check\s+(?P<args>[^\n|&]+)")


def _ruff_invocations():
    for wf in WORKFLOWS:
        for m in _RUFF_RE.finditer(_read(wf)):
            yield os.path.basename(wf), m.group("args").strip()


@pytest.mark.skipif(shutil.which("ruff") is None and
                    subprocess.run([sys.executable, "-m", "ruff", "--version"],
                                   capture_output=True).returncode != 0,
                    reason="ruff not installed")
def test_every_ruff_invocation_is_accepted_by_ruff():
    """A rule code ruff does not know makes the whole step a no-op."""
    found = list(_ruff_invocations())
    assert found, "no ruff invocation found to validate"
    for wf, args in found:
        # Re-run the exact flags against a trivially clean file: we are
        # validating the FLAGS, not the codebase. A usage error (exit 2)
        # means the step can never lint anything.
        probe = os.path.join(ROOT, "setup.py")
        flags = [a for a in args.split() if a.startswith("-")or "=" in a]
        # keep flag values (e.g. "E,W" after --select)
        parts, keep = args.split(), []
        for i, tok in enumerate(parts):
            if tok.startswith("-"):
                keep.append(tok)
                if i + 1 < len(parts) and not parts[i + 1].startswith("-"):
                    keep.append(parts[i + 1])
        r = subprocess.run(
            [sys.executable, "-m", "ruff", "check", probe, *keep],
            capture_output=True, text=True, cwd=ROOT,
        )
        assert "invalid value" not in (r.stderr or ""), (
            f"{wf}: ruff rejects its own flags ({' '.join(keep)}): "
            f"{r.stderr.strip().splitlines()[0] if r.stderr.strip() else ''}. "
            "The step reports success while linting nothing."
        )


# ------------------------------------------------- workflow_run trigger names

# NB: a workflow name may itself contain "]" (this repo has
# "Auto-release on [RELEASE] merge"), so capture the whole line and pull the
# QUOTED items out rather than matching up to the first closing bracket.
_WF_RUN_RE = re.compile(
    r"workflow_run:\s*\n\s*workflows:\s*(?P<names>.+)$", re.MULTILINE
)
_QUOTED_RE = re.compile(r'"([^"]+)"|\'([^\']+)\'')
_NAME_RE = re.compile(r'^name:\s*(?P<name>.+?)\s*$', re.MULTILINE)


def _declared_workflow_names():
    names = set()
    for wf in WORKFLOWS:
        m = _NAME_RE.search(_read(wf))
        if m:
            names.add(m.group("name").strip().strip('"').strip("'"))
    return names


def test_workflow_run_triggers_name_a_real_workflow():
    """A workflow_run naming a non-existent workflow never fires, silently."""
    declared = _declared_workflow_names()
    checked = 0
    for wf in WORKFLOWS:
        for m in _WF_RUN_RE.finditer(_read(wf)):
            for a, b in _QUOTED_RE.findall(m.group("names")):
                ref = (a or b).strip()
                if not ref:
                    continue
                checked += 1
                assert ref in declared, (
                    f"{os.path.basename(wf)}: workflow_run references "
                    f"{ref!r}, which is not the `name:` of any workflow. "
                    f"It will never fire. Declared names: {sorted(declared)}"
                )
    assert checked > 0, "no workflow_run trigger found to validate"


def test_cloud_pin_can_follow_a_release():
    """The specific regression: the cloud pin must have a post-release trigger.

    A `[RELEASE]` merge fires the push trigger while PyPI still serves the old
    version, and the follow-up version-bump commit is `[skip ci]`, so without a
    release-completion trigger the cloud stays a version behind.
    """
    src = _read(os.path.join(ROOT, ".github", "workflows", "auto-deploy-cloud.yml"))
    assert "workflow_run:" in src, (
        "auto-deploy-cloud.yml has no workflow_run trigger, so nothing pins "
        "the cloud after a release completes"
    )


def test_pypi_wait_polls_the_index_pip_reads():
    """Waiting on the JSON API passes minutes before pip can install."""
    src = _read(os.path.join(ROOT, ".github", "workflows", "auto-deploy-cloud.yml"))
    assert "pypi.org/pypi/clawmetry/$V/json" not in src, (
        "the PyPI wait polls the JSON API, which goes live before the simple "
        "index pip resolves against; the pin PR's CI then fails with "
        "'No matching distribution found'"
    )
    assert "pip download" in src or "pip index versions" in src, (
        "the PyPI wait must prove installability through pip's own index"
    )
