"""Pytest wrapper for the Node-based Active Tasks behavioural tests.

The assertions live in ``test_active_tasks_units.js`` so they exercise the
exact shipped ``app.js`` source (regex-extracted, vm-evaluated) rather than a
copy that can drift. This wrapper shells out to ``node`` and surfaces the
output on failure.

Companion to ``test_active_tasks_honesty.py``: that one pins the SHAPE of the
fix, this one pins its BEHAVIOUR, so a refactor that keeps the function names
while reintroducing the lie still fails.

Skipped (not failed) when ``node`` is not on PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_active_tasks_units.js")


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_active_tasks_unit_suite() -> None:
    proc = subprocess.run(
        ["node", _JS_TEST],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        pytest.fail(
            "Active Tasks JS unit tests failed:\n"
            + proc.stdout
            + "\n"
            + proc.stderr
        )
