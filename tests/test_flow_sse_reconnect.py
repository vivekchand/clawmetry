"""Class-bug sibling tests for the Flow SSE reconnect chain (sibling of #1596).

Before this fix ``_flowSse.onerror`` in app.js scheduled a single
``_startFlowSse()`` 5s later and went silent if that also failed. Same
bug shape as #1596; the fix mirrors PR #1610's pattern.

This test runs the Node-based unit test in ``test_flow_sse_reconnect.js``
which extracts the helpers from the shipped app.js source and exercises
the backoff ladder, chain survival, banner threshold, no-storm guard,
visibility-pause, ``_stopFlowSse`` teardown, and a source-level
``location.reload`` scan (defence per
``feedback_no_reload_in_bootstrap_e2e``).

Skipped (not failed) when ``node`` is not on PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_flow_sse_reconnect.js")


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_flow_sse_reconnect_suite() -> None:
    """Run the Node-based pure-function tests for the Flow SSE reconnect chain."""
    proc = subprocess.run(
        ["node", _JS_TEST],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "Flow SSE reconnect tests failed:\n" + output
    assert "PASS" in output, "no PASS line in output:\n" + output
