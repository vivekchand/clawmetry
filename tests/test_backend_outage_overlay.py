"""Global "backend unreachable" overlay -- the affordance that was missing.

2026-08-17: a desktop user's backend died and every tab froze. Activity said
"Failed to load: TypeError: Load failed", Cost sat on "Loading..." forever,
Agents claimed "No agents yet". Each panel swallowed the failure privately,
so a machine-wide outage rendered as a dozen unrelated spinners and nothing
that named the actual problem or offered a way out. The user's report: there
is no refresh button when it gets into this state.

The fix adds one global detector at the single chokepoint every /api/ call
already passes through (the auth-header fetch wrapper in auth-bootstrap.js)
and one overlay that always carries an action -- a real backend restart over
the pywebview JS bridge inside the desktop shell, a reload in a browser tab.

Runs the Node suite in ``test_backend_outage_overlay.js``, which extracts the
shipped IIFEs from auth-bootstrap.js and exercises them against a DOM stub.
Skipped (not failed) when ``node`` is not on PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_backend_outage_overlay.js")


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_backend_outage_overlay_suite() -> None:
    """Run the Node-based behavioural tests for the outage detector."""
    proc = subprocess.run(
        ["node", _JS_TEST],
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "backend outage overlay tests failed:\n" + output
    assert "PASS" in output, "no PASS line in output:\n" + output
