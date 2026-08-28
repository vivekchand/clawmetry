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


def test_composite_actions_are_scanned():
    """A composite action's `uses:` runs with the calling job's token.

    Scanning only ``.github/workflows`` left that shorter path unchecked.
    """
    scanned = {os.path.relpath(p, REPO_ROOT) for p in check_action_refs.source_files()}
    actions_dir = os.path.join(REPO_ROOT, ".github", "actions")
    if not os.path.isdir(actions_dir):
        pytest.skip("repository has no composite actions")
    assert any(p.startswith(os.path.join(".github", "actions")) for p in scanned), (
        "`.github/actions/` exists but no composite action file was scanned; "
        "its `uses:` lines would be unchecked."
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
