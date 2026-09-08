"""A published release must pin the cloud to *itself*.

`auto-deploy-cloud.yml` decides what to pin by reading PyPI's `info.version`
— deliberately, because `dashboard.py`'s `__version__` is permanently one or
more releases stale (release-on-merge publishes the bump without committing it
back). That is correct, and it is also why the workflow's OTHER trigger is a
trap.

`auto-deploy-cloud.yml` triggers on push-to-main for `CHANGELOG.md` /
`clawmetry/**` / `dashboard.py` / `setup.py`. On a `[RELEASE]` merge that push
fires **before** `release-on-merge.yml` publishes: auto-deploy starts, reads
PyPI's latest — still the PREVIOUS release — and pins that. Its "wait for
version on PyPI" step then passes instantly, because the version it is waiting
for is the old one that is already there. Nothing re-triggers it afterwards.

The release that was just cut is therefore **never pinned and never deployed**,
and the failure is silent and total: PR merged, wheel on PyPI, CHANGELOG
updated, release job green — and the hosted dashboard serves the previous
bundle indefinitely. Every artifact a person would check says "shipped".

Measured 2026-09-08 on 0.12.829: the [RELEASE] merge fired auto-deploy at
23:27:51, which read `Latest published OSS version: 0.12.828` and pinned it;
0.12.829 published moments later and had to be dispatched by hand.

The fix is an explicit dispatch from `release-on-merge.yml` AFTER the upload —
the only ordering in which "PyPI's latest" is the release that job produced.
This is the same rule that already forces the `desktop-artifacts` and
`release-canary` dispatches to exist: GITHUB_TOKEN activity does not cascade
into new workflow runs, so the push trigger cannot be relied upon.

Like those, the dispatch is non-blocking (`|| echo`) — the wheel is already
published and a failed dispatch must not fail a completed release. That
tolerance is precisely how the desktop-artifacts dispatch broke silently with
an HTTP 403, so its existence is asserted here rather than trusted.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RELEASE_WF = REPO / ".github" / "workflows" / "release-on-merge.yml"
DEPLOY_WF = REPO / ".github" / "workflows" / "auto-deploy-cloud.yml"

RELEASE_SRC = RELEASE_WF.read_text(encoding="utf-8")
DEPLOY_SRC = DEPLOY_WF.read_text(encoding="utf-8")


def test_release_dispatches_the_cloud_deploy():
    assert "gh workflow run auto-deploy-cloud.yml" in RELEASE_SRC, (
        "release-on-merge.yml must explicitly dispatch auto-deploy-cloud.yml "
        "after publishing. Without it, the only trigger is the push that "
        "happens BEFORE the upload, so the cloud pins the previous release and "
        "the one just published never deploys."
    )


def test_the_dispatch_happens_after_the_upload():
    """Ordering is the whole fix — a dispatch before the upload changes nothing."""
    upload = max(
        (m.start() for m in re.finditer(r"pypa/gh-action-pypi-publish|twine upload", RELEASE_SRC)),
        default=-1,
    )
    assert upload != -1, "could not locate the PyPI upload step"
    dispatch = RELEASE_SRC.index("gh workflow run auto-deploy-cloud.yml")
    assert dispatch > upload, (
        "the auto-deploy dispatch must come AFTER the PyPI upload; dispatched "
        "before it, auto-deploy reads the previous release from PyPI and pins "
        "that — which is the exact bug this guards"
    )


def test_the_dispatch_cannot_fail_the_release():
    tail = RELEASE_SRC[RELEASE_SRC.index("gh workflow run auto-deploy-cloud.yml"):][:400]
    assert "|| echo" in tail, (
        "the dispatch must be non-blocking: the wheel is already on PyPI by "
        "then, so a dispatch failure must not fail a completed release"
    )


def test_the_dispatch_targets_a_branch_not_the_new_tag():
    """auto-deploy-cloud.yml has no tag trigger; --ref must be a branch."""
    tail = RELEASE_SRC[RELEASE_SRC.index("gh workflow run auto-deploy-cloud.yml"):][:400]
    assert "--ref main" in tail, (
        "dispatch auto-deploy-cloud.yml against main; it is not a "
        "tag-triggered workflow like desktop-artifacts"
    )


def test_release_job_still_has_actions_write():
    """`gh workflow run` 403s without it, and the `|| echo` hides that."""
    assert "actions: write" in RELEASE_SRC, (
        "the release job needs actions: write to dispatch workflows; without "
        "it every dispatch silently 403s (verified on v0.12.658)"
    )


def test_deploy_still_reads_the_published_version():
    """The pin source must stay PyPI, not the stale checkout __version__."""
    assert "pypi.org/pypi/clawmetry/json" in DEPLOY_SRC, (
        "auto-deploy must pin the PUBLISHED version; dashboard.py's "
        "__version__ is permanently stale because release-on-merge does not "
        "commit the bump back"
    )
    # Only CODE matters here — both remaining `__version__` mentions are
    # comments explaining why the file no longer reads it.
    code = "\n".join(
        ln for ln in DEPLOY_SRC.splitlines() if not ln.lstrip().startswith("#")
    )
    assert "__version__" not in code, (
        "reading __version__ from the checkout was the root cause of the "
        "2026-07-31 stale-pin rollbacks"
    )


def test_deploy_still_waits_for_pip_not_just_the_json_api():
    """The JSON API goes live minutes before the index pip resolves against."""
    assert "pip download" in DEPLOY_SRC, (
        "the wait must poll what pip reads; pypi.org/pypi/<v>/json goes live "
        "before the simple index, so a JSON-only wait passes while the pin is "
        "still uninstallable"
    )
