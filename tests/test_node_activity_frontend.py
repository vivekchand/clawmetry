"""Node activity preserves unknown attribution and scopes request lifetimes.

AC-OBS-NODE-SEARCH-003.3: live frames preserve search and distinguish freshness.
AC-OBS-NODE-006.3: obsolete requests cannot paint or restart stopped pollers.
AC-OBS-NODE-007.1: selection uses chronological events and preceding measurements.
AC-OBS-NODE-007.2: reduced motion disables travel and hidden pages stop replay.
AC-OBS-NODE-007.3: unknown values and identities remain unknown.
AC-OBS-NODE-PART-004.1: rendered rows show their own observation age and limited history.
AC-OBS-NODE-CLARITY-001.1: positive source counts remain distinct from exact totals.
AC-OBS-NODE-CLARITY-001.2: empty, stale, disabled and unavailable counts stay distinct.
AC-OBS-NODE-CLARITY-004.1: selected observations explain evidence without actor guesses.
AC-OBS-NODE-CLARITY-004.2: original source and before/after details remain accessible.
AC-OBS-NODE-CLARITY-005.1: missing-source reasons are visible beside empty inventories.
AC-OBS-NODE-CLARITY-006.2: old snapshots render without invented counts or rates.
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
