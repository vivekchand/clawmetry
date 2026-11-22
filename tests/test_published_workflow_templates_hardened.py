"""Workflow templates this repo publishes follow the rules it enforces on itself.

`docs/github-action-template.yml` is not a workflow this repository runs. It
is a workflow this repository tells other people to run: the header says
"Drop this file into .github/workflows/clawmetry-evals.yml in your agent
repo", and `docs/EVALS_CI_INTEGRATION.md` points at it. So its blast radius
is the same one that put `integrations/github-action/` in scope for
`tests/test_action_refs_pinned.py` -- the steps execute in somebody else's
job, with their token, and in this case with their `ANTHROPIC_API_KEY` in the
step environment.

Two properties were missing, and both were invisible to every existing gate.

`tests/test_action_refs_pinned.py` discovers `.github/workflows/*` plus every
`action.yml`/`action.yaml` in the tree. A template under `docs/` is neither,
so it shipped `actions/checkout@v4`, `actions/setup-python@v5` and
`actions/upload-artifact@v4` -- three mutable tags -- while the ratchet
reported the repository fully pinned. The pins are the same vetted SHAs this
repo's own workflows already resolve, so this is not new trust: it is the
trust we already apply, applied to the copy we hand out.

The template also carried no `permissions:` block. In our own workflows that
is caught by Scorecard's Token-Permissions probe; in a published template it
is not caught by anything, and the consequence lands on the copier rather
than on us. A repository whose default workflow permissions are still
read/write would run this job with a token that can push to the default
branch, for a job that only needs to read a checkout.

This file is the floor for both. It is deliberately scoped to templates --
files outside `.github/` that are shaped like a workflow -- so a second
template added later is covered the day it lands rather than the day somebody
remembers this one exists.
"""

from __future__ import annotations

import os
import re

import pytest
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A full commit SHA, with the release it was, e.g.
#   actions/checkout@3d3c42e5... # v7.0.1
_PINNED = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")

# Local (`./`) and `docker://` refs are out of scope for the same reason the
# sibling ratchet excludes them: they are not fetched from a third-party
# repository under a mutable name.
_OUT_OF_SCOPE = ("./", "docker://")


def _template_files() -> list[str]:
    """Workflow-shaped YAML this repository publishes but does not run.

    Discovery follows what the file IS, not where it sits: anything outside
    `.github/` whose top level has both `on:` and `jobs:` is a workflow we are
    handing to somebody else, whatever directory it was filed under.
    """
    found = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in {".git", ".github", "node_modules", ".venv", "venv"}
        ]
        for name in filenames:
            if not name.endswith((".yml", ".yaml")):
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, encoding="utf-8") as fh:
                    doc = yaml.safe_load(fh)
            except (OSError, yaml.YAMLError):
                continue
            if not isinstance(doc, dict):
                continue
            # PyYAML resolves a bare `on:` key to the boolean True.
            has_on = "on" in doc or True in doc
            if has_on and isinstance(doc.get("jobs"), dict):
                found.append(path)
    return sorted(found)


def _uses_refs(path: str) -> list[tuple[str, int]]:
    refs = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            m = re.match(r"\s*-?\s*uses:\s*(\S+)", line)
            if m:
                refs.append((m.group(1), lineno))
    return refs


def test_a_published_template_is_discovered():
    """Guard the guard: a discovery bug would make everything below vacuous."""
    assert _template_files(), (
        "No published workflow template was discovered outside `.github/`. "
        "Either this repository stopped shipping one (then drop this file), "
        "or _template_files() no longer finds it and the checks below are "
        "passing on an empty set."
    )


@pytest.mark.parametrize("path", _template_files())
def test_template_action_refs_are_pinned(path: str):
    """A tag in a template is a mutable ref running in a stranger's job."""
    unpinned = [
        f"line {lineno}: {ref}"
        for ref, lineno in _uses_refs(path)
        if not ref.startswith(_OUT_OF_SCOPE) and not _PINNED.match(ref)
    ]
    rel = os.path.relpath(path, REPO_ROOT)
    assert not unpinned, (
        f"`{rel}` is a workflow this repository publishes for other people to "
        f"copy, and these `uses:` refs are not pinned to a full commit SHA:\n  "
        + "\n  ".join(unpinned)
        + "\nA tag can be repointed by whoever owns it, and the new code then "
        "runs in the copier's job with the copier's token and secrets. Pin to "
        "a 40-character commit SHA with the release in a trailing comment, "
        "e.g. `actions/checkout@3d3c42e5... # v7.0.1`."
    )


@pytest.mark.parametrize("path", _template_files())
def test_template_declares_least_privilege_permissions(path: str):
    """A template must not inherit the copier's default token scope."""
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    rel = os.path.relpath(path, REPO_ROOT)
    perms = doc.get("permissions")
    assert perms is not None, (
        f"`{rel}` declares no top-level `permissions:`. It is a template "
        "other people drop into their own repository, so with no block it "
        "runs at whatever their default workflow permissions are -- still "
        "read/write on many repositories. Declare the scopes the job "
        "actually needs."
    )
    assert perms != "write-all" and perms != {}, (
        f"`{rel}` declares `permissions: {perms!r}`, which is not "
        "least-privilege for a template."
    )
    if isinstance(perms, dict):
        granted = {k: v for k, v in perms.items() if v == "write"}
        assert not granted, (
            f"`{rel}` grants write scopes {sorted(granted)} in a template. "
            "A published template should ship the smallest scope that works "
            "and let a copier widen it deliberately; if this template really "
            "does need to write, say why here and in the file."
        )
