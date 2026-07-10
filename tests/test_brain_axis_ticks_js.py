"""Runner for the Node-based Brain density-chart time-axis unit tests.

``tests/test_brain_axis_ticks.js`` extracts ``_brainAxisTicks`` from the
shipped app.js (vm + regex, same pattern as test_brain_time_range) and
asserts:

  1. Tick fractions span exactly 0..1 and strictly increase, so labels line
     up with the bucketed bars.
  2. Labels carry the date whenever the window is longer than ~20h OR
     crosses local midnight ("03:00" must not read as today), and stay
     time-only otherwise.
  3. Date-bearing labels get fewer, wider-spaced ticks so they never
     collide; degenerate input (zero/negative span, zero width, NaN)
     yields no ticks instead of throwing mid-render.

Skipped (not failed) when ``node`` is not on PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_brain_axis_ticks.js")


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_brain_axis_ticks_js_suite() -> None:
    proc = subprocess.run(
        ["node", _JS_TEST],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "brain axis-ticks JS tests failed:\n" + output
    assert "PASS" in output, "no PASS line in output:\n" + output
