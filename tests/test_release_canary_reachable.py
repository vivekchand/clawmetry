"""The release canary must actually be reachable from a release.

A canary that never fires is worse than no canary: it occupies the slot where
post-publication verification is supposed to be, and its silence is
indistinguishable from a clean release.

That is not hypothetical. ``release-canary.yml`` originally declared only::

    on:
      workflow_run:
        workflows: ["Auto-release on [RELEASE] merge"]
        types: [completed]

The names matched exactly and the file was on the default branch, and it still
produced **zero runs** when 0.12.757 published on 2026-08-22. Activity driven by
``GITHUB_TOKEN`` does not cascade into new workflow runs, which is the same rule
that already forced ``release-on-merge.yml`` to dispatch ``desktop-artifacts.yml``
explicitly after v0.12.658 shipped without its ``.dmg``.

So the reachable path is the explicit ``gh workflow run`` dispatch, and this
guard asserts it stays there. The ``workflow_run`` trigger is kept as
belt-and-braces, but nothing may depend on it alone.

The dispatch is deliberately non-blocking (``|| echo``) because the wheel is
already on PyPI by the time it runs, and a failed dispatch must not fail a
completed release. That tolerance is exactly how the desktop-artifacts dispatch
broke silently with an HTTP 403, so the existence of the dispatch is asserted
here rather than trusted.
"""
from __future__ import annotations

import os

import pytest
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")
RELEASE = os.path.join(WORKFLOW_DIR, "release-on-merge.yml")
CANARY = os.path.join(WORKFLOW_DIR, "release-canary.yml")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_release_workflow_exists() -> None:
    assert os.path.isfile(RELEASE), "release-on-merge.yml is missing"


def test_canary_workflow_exists() -> None:
    assert os.path.isfile(CANARY), "release-canary.yml is missing"


def test_release_explicitly_dispatches_the_canary() -> None:
    """The only path that actually fires. Do not rely on workflow_run alone."""
    source = _read(RELEASE)
    assert "gh workflow run release-canary.yml" in source, (
        "release-on-merge.yml no longer dispatches release-canary.yml.\n\n"
        "The canary's `on: workflow_run:` trigger DID NOT FIRE for 0.12.757 -- "
        "zero runs were created -- because GITHUB_TOKEN activity does not "
        "cascade into new workflow runs. Without this explicit dispatch, "
        "nothing verifies a published release and the silence looks exactly "
        "like a clean one."
    )


def test_dispatch_targets_the_default_branch() -> None:
    """The canary must run from main, not from the release tag.

    The workflow file lives on main; dispatching against a tag would resolve a
    version of the file from that tag's tree, which for older tags does not
    contain the canary at all.
    """
    source = _read(RELEASE)
    index = source.find("gh workflow run release-canary.yml")
    assert index != -1, "dispatch missing; see the previous test"
    window = source[index:index + 400]
    assert "--ref main" in window, (
        "The canary dispatch must use `--ref main`. The workflow file only "
        "exists on the default branch."
    )


def test_dispatch_passes_the_published_version() -> None:
    """Verifying 'whatever PyPI calls latest' can race a concurrent release."""
    source = _read(RELEASE)
    index = source.find("gh workflow run release-canary.yml")
    window = source[index:index + 400]
    assert "-f version=" in window, (
        "The dispatch must pass the version it just published. Falling back to "
        "'latest' lets a concurrent release move the target, so the canary "
        "would verify a different artifact than the one just shipped."
    )


def test_canary_accepts_a_version_input() -> None:
    """The dispatch passes `version`, so the canary must declare it."""
    with open(CANARY, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)

    triggers = doc.get("on") or doc.get(True) or {}
    dispatch = (triggers or {}).get("workflow_dispatch") or {}
    inputs = dispatch.get("inputs") or {}
    assert "version" in inputs, (
        "release-canary.yml must declare a `version` workflow_dispatch input, "
        "because release-on-merge.yml passes `-f version=`. A dispatch that "
        "passes an undeclared input fails."
    )


def test_canary_still_declares_the_workflow_run_fallback() -> None:
    """Kept as belt-and-braces. Removing it is fine; removing both is not."""
    with open(CANARY, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)

    triggers = doc.get("on") or doc.get(True) or {}
    has_fallback = "workflow_run" in (triggers or {})
    has_dispatch = "workflow_dispatch" in (triggers or {})
    assert has_fallback or has_dispatch, (
        "release-canary.yml has no trigger that a release can reach."
    )


@pytest.mark.parametrize(
    "subcommand", ["status", "sync", "connect", "uninstall"]
)
def test_canary_exercises_every_subcommand(subcommand: str) -> None:
    """`uninstall` in particular.

    When 0.12.753 died at import, it took `clawmetry uninstall` with it, so
    affected users had no supported way off the product. A release that cannot
    be uninstalled is strictly worse than one that merely does not work.
    """
    source = _read(CANARY)
    assert subcommand in source, (
        f"release-canary.yml no longer exercises `clawmetry {subcommand}`."
    )
