"""C5 drift guard: CANONICAL_TABS must cover every tab template.

Pure-Python, no Playwright, no running server. Fails immediately when:
  * A new .html is added to clawmetry/templates/tabs/ without also adding
    its stem to CANONICAL_TABS in tests/test_e2e_oss_all_tabs.py.

Closes the root cause of the 2026-05-17 user-reported bug permanently:
  "gateway token not passed for OSS so it never displays other screens."

Without this guard, CANONICAL_TABS silently drifted for weeks (13 tabs
missed; caught in PR #2937, 2026-06-09). The drift guard makes that
impossible: any template shipped without a CANONICAL_TABS entry fails CI
immediately, before the PR can merge.

Tracking: vivekchand/clawmetry#2146 (C5, fire 2026-06-10)
"""
from __future__ import annotations

import pathlib
import sys

import pytest

# Allow importing CANONICAL_TABS from the sibling test file without requiring
# tests/ to be a Python package (no __init__.py). pytest adds conftest dirs
# to sys.path but the sibling module path may vary by runner setup.
_TESTS_DIR = pathlib.Path(__file__).parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

from test_e2e_oss_all_tabs import CANONICAL_TABS  # noqa: E402

_TABS_DIR = _TESTS_DIR.parent / "clawmetry" / "templates" / "tabs"


def test_canonical_tabs_covers_all_templates() -> None:
    """Every .html in clawmetry/templates/tabs/ must be in CANONICAL_TABS.

    Adding a tab template without updating CANONICAL_TABS fails this test,
    preventing silent auth-overlay regressions on the uncovered tab.
    """
    if not _TABS_DIR.is_dir():
        pytest.skip(
            f"tabs directory not found at {_TABS_DIR} -- "
            "run from the repo root or ensure clawmetry/templates/tabs/ exists"
        )

    template_names = {p.stem for p in _TABS_DIR.glob("*.html")}
    covered = set(CANONICAL_TABS)
    missing = template_names - covered

    assert not missing, (
        "Tab templates present on disk but MISSING from CANONICAL_TABS in "
        "tests/test_e2e_oss_all_tabs.py.\n"
        "These tabs are invisible to the C5 post-auth overlay sweep:\n\n"
        + "\n".join(f"  {n}.html" for n in sorted(missing))
        + "\n\nAdd each name to CANONICAL_TABS so the overlay check covers them."
    )
