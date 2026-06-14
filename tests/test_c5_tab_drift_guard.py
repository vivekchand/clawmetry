"""C5 tab-drift guard: every template in clawmetry/templates/tabs/ must be in CANONICAL_TABS.

Pure-Python, no Playwright, no running server. Runs as part of the standard
pytest suite. When a new tab template is added without updating CANONICAL_TABS,
this test fails immediately with an actionable list naming the missing entries.

Prevents the silent drift that caused the 2026-05-17 user report:
  'gateway token not passed for OSS so it never displays other screens'
where 13 tab templates were uncovered for weeks before being noticed.

Acceptance test:
    pytest tests/test_c5_tab_drift_guard.py -v
    # Expected: 1 passed

To verify the guard works:
    touch clawmetry/templates/tabs/fake.html && pytest tests/test_c5_tab_drift_guard.py -v
    # Expected: FAILED with 'fake' in the error message
    rm clawmetry/templates/tabs/fake.html
"""
from __future__ import annotations

import pathlib


def test_all_tab_templates_in_canonical_tabs() -> None:
    """Every .html stem in clawmetry/templates/tabs/ must appear in CANONICAL_TABS."""
    # Import here to pick up the live file rather than a cached module.
    import importlib.util
    import sys

    module_path = (
        pathlib.Path(__file__).parent.parent
        / "tests"
        / "test_e2e_oss_all_tabs.py"
    )
    if not module_path.exists():
        # Try the sibling path directly.
        module_path = pathlib.Path(__file__).parent / "test_e2e_oss_all_tabs.py"

    spec = importlib.util.spec_from_file_location("_oss_all_tabs", module_path)
    assert spec is not None, f"Could not load spec from {module_path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("_oss_all_tabs", mod)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    canonical: set[str] = set(mod.CANONICAL_TABS)

    tabs_dir = (
        pathlib.Path(__file__).parent.parent / "clawmetry" / "templates" / "tabs"
    )
    assert tabs_dir.is_dir(), f"Expected tabs directory at {tabs_dir}"

    template_stems = {p.stem for p in tabs_dir.glob("*.html")}
    uncovered = template_stems - canonical

    assert not uncovered, (
        f"Tab template(s) not in CANONICAL_TABS -- add them to "
        f"tests/test_e2e_oss_all_tabs.py CANONICAL_TABS so the auth-overlay sweep "
        f"covers them:\n"
        + "\n".join(f"  {name}" for name in sorted(uncovered))
    )
