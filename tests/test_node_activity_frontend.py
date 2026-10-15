"""Node activity preserves unknown attribution and scopes request lifetimes.

AC-OBS-NODE-006.3: obsolete requests cannot paint or restart stopped pollers.
AC-OBS-NODE-007.1: selection uses chronological events and preceding measurements.
AC-OBS-NODE-007.2: reduced motion disables travel and hidden pages stop replay.
AC-OBS-NODE-007.3: unknown values and identities remain unknown.
AC-OBS-NODE-PART-004.1: rendered rows show their own observation age and limited history.
"""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_node_activity_frontend_lifecycle():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the frontend lifecycle check")
    result = subprocess.run([node, str(Path(__file__).with_name("test_node_activity_js.js"))],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
