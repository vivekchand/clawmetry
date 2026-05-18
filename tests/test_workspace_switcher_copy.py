"""
Lock-in test for issue #1172 — workspace switcher UI copy must explicitly
scope the feature as single-machine ("local") and point users at Cloud-Pro
for fleet view. Prevents future regressions that re-introduce the old
"Switch OpenClaw workspace" label confusable with multi-node fleet.

We assert on raw source strings (no Flask boot required) because the
switcher markup is embedded directly in dashboard.py template strings
and the dropdown rendering happens in clawmetry/static/js/app.js.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_switcher_button_tooltip_disambiguates_from_fleet():
    html = _read("dashboard.py")
    # New label explicitly says "this machine"
    assert "Switch profile (this machine)" in html, (
        "workspace-switcher button title must say 'Switch profile (this machine)'"
    )
    # New tooltip points fence-sitters at Cloud-Pro fleet view
    assert "upgrade to Pro" in html, (
        "workspace-switcher tooltip must mention Pro upgrade for fleet view"
    )
    # Old confusable label is fully gone
    assert "Switch OpenClaw workspace" not in html, (
        "Old 'Switch OpenClaw workspace' copy must not reappear (issue #1172)"
    )


def test_switcher_dropdown_items_have_local_suffix():
    js = _read("clawmetry/static/js/app.js")
    # Renderer must append "(local)" to each workspace name so the
    # local-only scoping survives even after the dropdown is opened.
    assert "+ ' (local)'" in js, (
        "renderWorkspaceSwitcher() must append ' (local)' to dropdown items"
    )
