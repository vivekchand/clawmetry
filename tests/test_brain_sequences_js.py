"""Runner for the Node-based Brain run-grouping unit tests.

``tests/brain_sequences.test.mjs`` extracts the sequence helpers from the
shipped ``clawmetry/static/js/app.js`` (plus the real ``_cmRuntimeOf``
resolver) and asserts that a Brain feed groups into one block per agent run,
labels each run with its actual runtime, and renders the swimlane.

The suite existed for months with NO runner -- nothing in the Makefile or any
workflow ever executed it, so it was a test that could not fail. This wrapper
wires it into the normal pytest run. It also carries the regression guard for
the hosted-Brain label bug (every Claude Code run rendered "OpenClaw . ?"
because the cloud feed carries ``source`` + ``runtime`` instead of a
namespaced ``sessionId``).

Skipped (not failed) when ``node`` is not on PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "brain_sequences.test.mjs")


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_brain_sequences_js_suite() -> None:
    proc = subprocess.run(
        ["node", _JS_TEST],
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "brain sequence JS tests failed:\n" + output
    assert "0 failed" in output, "no clean summary line in output:\n" + output
