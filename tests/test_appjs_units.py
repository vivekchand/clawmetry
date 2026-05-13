"""
Pytest wrapper that runs the Node-based unit tests in test_appjs_units.js.

These cover the pure helpers added/changed in app.js for issue #1127:
  - formatBrainTime() — must include the year when the event is from a
    different calendar year than "now" (bug #1127.2).
  - _isStuckDismissed / _markStuckDismissed / _pruneStuckDismissals — the
    localStorage-backed dismissal store for the stuck-session banner
    (bug #1127.5) must survive a page reload and prune entries > 24h old.

The actual assertions live in test_appjs_units.js so they exercise the
exact shipped source (regex-extracted, vm-evaluated). This wrapper just
shells out to `node` and surfaces the stdout/stderr if anything fails.

Skipped (not failed) when `node` is not on PATH so non-JS contributors
running `pytest -q` don't get spurious failures.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_appjs_units.js")


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_appjs_unit_suite() -> None:
    """Run the Node-based pure-function tests for app.js."""
    proc = subprocess.run(
        ["node", _JS_TEST],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "app.js unit tests failed:\n" + output
    # Belt-and-braces: ensure we actually ran cases.
    assert "PASS" in output, "no PASS line in output:\n" + output
