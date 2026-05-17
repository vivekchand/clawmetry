"""Tests for issue #1596 — Brain SSE reconnect with exponential backoff.

Before this fix the EventSource ``onerror`` handler in app.js scheduled a
single ``loadBrainPage(true)`` poll 5s later and then went silent. On a
flaky network the user saw an indefinitely stale feed with no UI signal
beyond the small ``● POLLING`` pill.

This test runs the Node-based unit test in ``test_brain_sse_reconnect.js``
which extracts the helpers from the shipped app.js source and exercises:

  1. Reconnect after one failed poll fallback — i.e. the SSE retry chain
     keeps scheduling reconnects even when ``loadBrainPage`` errors out.
  2. After 30s+ of failed retries the "Connection lost" banner is
     surfaced via ``_showBrainConnectionLostBanner`` and the wording
     matches the no-em-dash / non-technical-user copy rules.

Skipped (not failed) when ``node`` is not on PATH so non-JS contributors
running ``pytest -q`` don't get spurious failures.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_brain_sse_reconnect.js")


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_brain_sse_reconnect_suite() -> None:
    """Run the Node-based pure-function tests for the SSE reconnect chain."""
    proc = subprocess.run(
        ["node", _JS_TEST],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "brain SSE reconnect tests failed:\n" + output
    # Belt-and-braces: ensure we actually ran cases.
    assert "PASS" in output, "no PASS line in output:\n" + output
