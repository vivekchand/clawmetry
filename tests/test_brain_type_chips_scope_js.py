"""Runner for the Node-based Brain type-chip runtime-scope unit tests.

``tests/test_brain_type_chips_scope.js`` extracts ``renderBrainTypeChips``
from the shipped app.js (vm + regex, same pattern as test_brain_time_range)
and asserts the chip counts follow the header runtime switcher the same way
the list and chart do — node-wide counts over a runtime-scoped stream read
as a bug ("AGENT (84)" above a 1-row cursor feed, live-hit 2026-07-25).

Skipped (not failed) when ``node`` is not on PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_brain_type_chips_scope.js")


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_brain_type_chips_scope_js_suite() -> None:
    proc = subprocess.run(
        ["node", _JS_TEST],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, (
        "JS suite failed:\n" + proc.stdout + "\n" + proc.stderr
    )
