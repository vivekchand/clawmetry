"""Every `uses:` reference must stay pinned to a full commit SHA.

Pinning the whole repository was a series of changes, one workflow family at a
time. Nothing kept it done. A tag is mutable -- the repository that owns
``@v4`` can repoint it at new code, and that code then runs inside our jobs
with our token. Several of these workflows hold ``contents: write``, publish to
PyPI, or deploy to Cloud Run, so the blast radius of a repointed tag is real.

The pinning work itself is therefore only half the control. Without a gate, one
convenient ``uses: actions/checkout@v4`` in a later PR reverts a slice of it,
and nothing goes red: the job runs perfectly well against a floating tag. That
is the same shape as the acceptance-criteria ratchet -- catching "untouched
code stopped satisfying a property" rather than "this diff is wrong".

``scripts/check_action_refs.py`` performs the same check, but it runs only in
``supply-chain.yml`` and its resolution half needs a token. This test carries
the offline half into the ordinary CI matrix, so the ratchet applies to every
pull request.

Local (``./``) and ``docker://`` references are out of scope by construction:
they are not fetched from a third-party repository, and the shared ``_USES``
pattern does not match them.
"""
from __future__ import annotations

import os
import re
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import check_action_refs  # noqa: E402

_SHA = re.compile(r"^[0-9a-f]{40}$")


def _refs() -> list:
    """[(action, ref, [files])] for every third-party reference in the repo."""
    return [
        (action, ref, files)
        for (action, ref), files in sorted(check_action_refs.collect_refs().items())
    ]


def test_repo_has_action_references_to_check():
    """Guard the guard: a discovery bug would make every check below vacuous."""
    assert _refs(), (
        "No `uses:` references found at all. The workflows certainly have some, "
        "so collect_refs() is not discovering files."
    )


def test_every_action_definition_is_scanned():
    """A composite action's `uses:` runs with the calling job's token.

    Scanning only ``.github/workflows`` left that shorter path unchecked, and
    then scanning only ``.github/actions`` left it half-checked: an action
    definition is one wherever it sits, so discovery follows what the file IS
    rather than which directory holds it. ``integrations/github-action/`` is the
    case that matters -- this repository PUBLISHES it, so its ``uses:`` lines
    run in other people's jobs with their token, and a directory-scoped walk
    skipped precisely the one action whose blast radius is outside this repo.
    """
    actions = check_action_refs.action_files()
    if not actions:
        pytest.skip("repository has no action definitions")
    scanned = set(check_action_refs.source_files())
    missing = sorted(
        os.path.relpath(a, REPO_ROOT) for a in actions if a not in scanned
    )
    assert not missing, (
        "These action definitions are not scanned for pinned `uses:` refs:\n  "
        + "\n  ".join(missing)
        + "\nTheir steps run with a caller's token, so an unpinned ref in one "
        "is the same exposure as an unpinned ref in a workflow."
    )


def test_action_discovery_is_not_scoped_to_one_directory():
    """Guard the widening itself, not just today's file list.

    ``action_files()`` walking the repository is what puts the published action
    in scope. A later refactor narrowing it back to ``.github/actions/`` would
    leave every test above passing -- they would simply have less to check.
    """
    found = {os.path.relpath(a, REPO_ROOT) for a in check_action_refs.action_files()}
    outside = {
        a for a in found if not a.startswith(os.path.join(".github", "actions"))
    }
    assert outside, (
        "No action definition was discovered outside `.github/actions/`. "
        "Either this repository stopped shipping one (then drop this test), or "
        "discovery was narrowed back to that directory and the published "
        "action at `integrations/github-action/` is unchecked again."
    )


def test_zizmor_audit_covers_the_same_files():
    """The reporting scan and this gate must not disagree about coverage.

    ``supply-chain.yml`` hands zizmor its own file list. It was scoped to
    ``.github/actions`` by the same assumption this module carried, so the two
    halves went blind to the published action together. Keep them in step: a
    directory-scoped `find` here means the reporting scan is narrower than the
    gate, and nothing else would say so.
    """
    workflow = os.path.join(REPO_ROOT, ".github", "workflows", "supply-chain.yml")
    if not os.path.isfile(workflow):
        pytest.skip("supply-chain.yml not present")
    with open(workflow, encoding="utf-8") as fh:
        text = fh.read()
    assert "find .github/actions" not in text, (
        "supply-chain.yml discovers action definitions under `.github/actions` "
        "only, so zizmor does not audit the published action at "
        "`integrations/github-action/`. Search the repository instead."
    )
    assert "-name 'action.yml'" in text, (
        "supply-chain.yml no longer searches for action definitions at all; "
        "zizmor would audit workflows only."
    )


@pytest.mark.parametrize(
    "action,ref,files",
    _refs(),
    ids=[f"{action}@{ref[:12]}" for action, ref, _ in _refs()],
)
def test_action_reference_is_sha_pinned(action, ref, files):
    assert _SHA.match(ref), (
        f"{action}@{ref} in {', '.join(files)} is not pinned to a commit SHA.\n"
        f"A tag is mutable and its owner can repoint it at code that then runs "
        f"with our token. Pin it:\n"
        f"    uses: {action}@<40-hex-sha> # {ref}\n"
        f"Resolve the SHA with:\n"
        f"    git ls-remote https://github.com/{'/'.join(action.split('/')[:2])} "
        f"refs/tags/{ref}"
    )
