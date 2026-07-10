"""Runner for the Node-based Brain date-time-range unit tests.

``tests/test_brain_time_range.js`` extracts the range-picker helpers from
the shipped app.js (vm + regex, same pattern as test_brain_sse_reconnect)
and asserts:

  1. Preset / custom ranges produce a correct frozen UTC window (reversed
     bounds are swapped, never an inverted window).
  2. History mode freezes the live machinery: no EventSource open, no
     reconnect scheduling, and the SSE reconnect flush + poll fallback are
     gated — the pre-guard code would clobber a historical view with live
     events.
  3. Back-to-live clears the range and reloads the live feed.

Skipped (not failed) when ``node`` is not on PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_brain_time_range.js")


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_brain_time_range_js_suite() -> None:
    proc = subprocess.run(
        ["node", _JS_TEST],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "brain time-range JS tests failed:\n" + output
    assert "PASS" in output, "no PASS line in output:\n" + output
