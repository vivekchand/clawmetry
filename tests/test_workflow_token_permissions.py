"""Every workflow declares a least-privilege top-level ``permissions:`` block.

A workflow with no top-level ``permissions:`` runs at the *repository's*
default workflow permissions. Where that default is still the permissive one,
every job in the file gets a ``GITHUB_TOKEN`` that can write contents, open
issues and push packages -- whether it needs to or not. Scorecard reports this
as a HIGH ``TokenPermissions`` finding, and it was HIGH on 15 of this repo's
workflows until the hardening pass closed them one batch at a time.

Closing a finding is not the same as keeping it closed. Nothing in CI asserted
the result: ``test_workflow_has_required_top_level_keys`` checks for ``on:``
and ``jobs:`` only, so the next workflow added without a ``permissions:``
block would have reopened the alert silently, and the only notice would have
been a Scorecard re-scan some days later.

Two things are asserted here, and the second matters as much as the first:

1. The block exists.
2. The block grants **no write scope at the top level**. A write scope belongs
   on the one job that uses it, because a top-level grant hands it to every
   job in the file -- including jobs that check out a pull request's own code.
   Six workflows here legitimately need write scopes (``publish``,
   ``release-on-merge``, ``desktop-artifacts``, ``auto-deploy-cloud``, ``ci``,
   ``moat-keystone-drive-nightly``); each one keeps a read-only top level and
   elevates inside the job that publishes, releases or files the issue.

What this guard deliberately does NOT do is require a particular read scope.
``contents: read`` is what nearly every file here wants, but a workflow that
needs nothing at all is better served by ``permissions: {}`` and should not be
pushed back up to a broader grant to satisfy a test.

Auto-discovers the workflow directory, so a newly added workflow is covered
without anyone maintaining a list.
"""
from __future__ import annotations

import glob
import os

import pytest
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")

# The scalar shorthands. ``read-all`` is a legitimate (if broad) read-only
# top level; ``write-all`` is the permissive default spelled out, and is the
# single worst value this guard exists to keep out.
_SCALAR_READ_ONLY = {"read-all"}


def _workflow_files() -> list[str]:
    files: list[str] = []
    for ext in ("yml", "yaml"):
        files.extend(glob.glob(os.path.join(WORKFLOW_DIR, f"*.{ext}")))
    return sorted(files)


def _load_or_skip(path: str) -> dict:
    """Parse a workflow, or skip.

    A malformed workflow is ``test_workflow_parses_as_yaml``'s finding, not
    this one. Skipping keeps one broken file from producing two failures that
    say different things about the same cause.
    """
    with open(path, encoding="utf-8") as fh:
        try:
            doc = yaml.safe_load(fh)
        except yaml.YAMLError:
            pytest.skip("file does not parse; see test_workflow_parses_as_yaml")
    if not isinstance(doc, dict):
        pytest.skip("file is not a workflow mapping")
    return doc


def test_workflow_files_are_discovered() -> None:
    """An empty input set must not read as a clean scan.

    Every parametrized check below disappears if the glob returns nothing --
    zero tests run, and the step goes green. That failure mode has shipped
    here before (an empty zizmor input set, an npm audit that scanned
    nothing), so the discovery itself is asserted.
    """
    found = _workflow_files()
    assert len(found) >= 20, (
        f"Expected to discover the workflow files under {WORKFLOW_DIR}, found "
        f"{len(found)}. If the directory moved, update WORKFLOW_DIR -- an "
        "empty glob silently turns every check in this file into a pass."
    )


@pytest.mark.parametrize("path", _workflow_files(), ids=os.path.basename)
def test_workflow_declares_top_level_permissions(path: str) -> None:
    doc = _load_or_skip(path)
    rel = os.path.relpath(path, REPO_ROOT)

    assert "permissions" in doc, (
        f"`{rel}` declares no top-level `permissions:` block, so every job in "
        "it runs at the repository's DEFAULT workflow permissions. Where that "
        "default is permissive, each job gets a GITHUB_TOKEN that can write "
        "contents, issues and packages regardless of what it does -- the HIGH "
        "Scorecard TokenPermissions finding. Add a least-privilege top level "
        "(`permissions: {contents: read}`, or `permissions: {}` if the jobs "
        "need no token scope at all) and elevate per job where a job really "
        "writes."
    )


@pytest.mark.parametrize("path", _workflow_files(), ids=os.path.basename)
def test_top_level_permissions_grant_no_write(path: str) -> None:
    doc = _load_or_skip(path)
    rel = os.path.relpath(path, REPO_ROOT)

    perms = doc.get("permissions")
    if perms is None:
        pytest.skip(
            "no top-level block; see test_workflow_declares_top_level_permissions"
        )

    if isinstance(perms, str):
        assert perms in _SCALAR_READ_ONLY, (
            f"`{rel}` declares `permissions: {perms}` at the top level. A "
            "scalar write grant hands every job in the file a writable "
            "GITHUB_TOKEN. Use a read-only top level and give the one job "
            "that writes its own `permissions:` block."
        )
        return

    assert isinstance(perms, dict), (
        f"`{rel}` declares `permissions: {perms!r}`, which is neither a "
        "scope mapping nor one of the scalar shorthands."
    )

    writable = sorted(
        scope for scope, level in perms.items() if str(level) == "write"
    )
    assert not writable, (
        f"`{rel}` grants {writable} at the TOP level, which applies to every "
        "job in the file -- including any job that checks out a pull "
        "request's own code. Move each write scope onto the job that needs "
        "it: keep the top level read-only and add a job-level `permissions:` "
        "block covering exactly what that job does. This is how `publish`, "
        "`release-on-merge`, `desktop-artifacts` and "
        "`moat-keystone-drive-nightly` are already arranged here."
    )
