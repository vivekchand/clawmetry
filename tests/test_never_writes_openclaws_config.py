"""Repo guard: ClawMetry never writes its own key into OpenClaw's config.

``~/.openclaw/openclaw.json`` belongs to OpenClaw. ``clawmetry`` is not a key
in its schema, so writing one leaves OpenClaw's own config failing validation;
its next CLI run fires ``doctor --fix``, which restores the last-known-good
config and restarts the gateway — killing whatever session the user had going.

That shipped twice (field report 2026-09-09: broke one user's install on
2026-09-02 and again on 2026-09-07) from two independent code paths, which is
exactly the shape a grep guard is for. The unit tests next door assert the two
known paths behave; this one asserts a *third* one cannot quietly appear.

Removing the key is always allowed — sign-out, uninstall and the migration all
have to strip it — so the guard looks for assignment, not mention.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Where product code lives. Tests are excluded on purpose: they legitimately
#: construct a corrupted openclaw.json to prove we heal it.
SOURCE_ROOTS = ("clawmetry", "routes", "desktop", "helpers")
SOURCE_FILES = ("dashboard.py", "dashboard_claudecode.py")

#: Assignment into the OpenClaw config's ``clawmetry`` section, in the shapes
#: the two shipped bugs actually took:
#:     data["clawmetry"] = {}          /  data["clawmetry"]["cloudToken"] = tok
#:     cm["cloudToken"] = cm_key       /  data['clawmetry'] = cm
#: A trailing ``==`` is not an assignment, hence the negative lookahead.
_ASSIGNMENT = re.compile(
    r"""\[\s*['"](?:clawmetry|cloudToken)['"]\s*\]        # ["clawmetry"] / ["cloudToken"]
        (?:\s*\[[^\]]*\])?                                 # optional further subscript
        \s*=(?!=)                                          # assignment, not ==
    """,
    re.VERBOSE,
)

#: Deleting/stripping the legacy key is the point of these, not a violation.
#: ``watchdog.py`` embeds a shell one-liner that does ``del d["clawmetry"]``.
ALLOWLIST = {
    "clawmetry/watchdog.py",
}


def _source_files():
    for name in SOURCE_FILES:
        p = REPO_ROOT / name
        if p.is_file():
            yield p
    for root in SOURCE_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.py")):
            yield p


@pytest.mark.parametrize(
    "path", list(_source_files()), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_no_source_file_assigns_into_openclaws_clawmetry_key(path):
    rel = str(path.relative_to(REPO_ROOT))
    if rel in ALLOWLIST:
        pytest.skip(f"{rel} strips the legacy key; removal is allowed")

    offenders = [
        (i, line.strip())
        for i, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        )
        if _ASSIGNMENT.search(line)
    ]
    assert not offenders, (
        f"{rel} assigns into a `clawmetry` / `cloudToken` config key:\n"
        + "\n".join(f"  L{i}: {t}" for i, t in offenders)
        + "\n\nThe cm_ bearer belongs in ~/.clawmetry/config.json (see "
        "clawmetry.config.write_cloud_token). Writing a `clawmetry` key into "
        "~/.openclaw/openclaw.json makes OpenClaw's config fail its own schema, "
        "and OpenClaw repairs that by restoring the last-known-good config and "
        "restarting the gateway — which kills the user's live session."
    )


def test_the_guard_would_catch_the_bug_it_was_written_for():
    """Prove the pattern is not vacuous: it must match the exact lines that
    shipped, and must NOT match the removal/comparison forms."""
    caught = [
        'data["clawmetry"] = {}',
        'data["clawmetry"]["cloudToken"] = token',
        '        cm["cloudToken"] = cm_key',
        "data['clawmetry'] = cm",
    ]
    for line in caught:
        assert _ASSIGNMENT.search(line), f"guard missed a real offender: {line}"

    ignored = [
        'del data["clawmetry"]',
        'tok = (data.get("clawmetry", {}) or {}).get("cloudToken", "")',
        'if data["clawmetry"] == expected:',
        '"clawmetry" not in data',
    ]
    for line in ignored:
        assert not _ASSIGNMENT.search(line), f"guard false-positives on: {line}"
