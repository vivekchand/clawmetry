"""Regression checks for the issue-#1127 UX dead-end fixes.

Each test pins one of the 5 fixes so future refactors don't silently re-
introduce the bad copy / code path.

Why a static scan instead of a browser test: every fix is a frontend string
inside Python templates or a JS file. Spinning up Playwright for one-line
copy checks is overkill — a focused grep is sufficient and runs in <100 ms.
"""

from __future__ import annotations

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel_path: str) -> str:
    with open(os.path.join(ROOT, rel_path), encoding="utf-8") as fh:
        return fh.read()


# ── Bug 1 ────────────────────────────────────────────────────────────────────
def test_bug1_alerts_page_falls_back_to_local_history() -> None:
    """When cloud history is empty, the Alerts page now reads local fires so
    the badge (which already counts local) and the page agree."""
    js = _read("clawmetry/static/js/alerts.js")
    assert "/api/alerts/history?limit=20" in js, (
        "alerts.js must fall back to local /api/alerts/history when cloud "
        "history returns empty — otherwise the nav badge can show N fires "
        "while the page says 'No alerts have fired yet'."
    )


# ── Bug 2 ────────────────────────────────────────────────────────────────────
def test_bug2_notifications_count_only_enabled_rows() -> None:
    """Disabled channel rows render as 'Connect' cards, so the header
    'N channels configured' must only count enabled rows."""
    html = _read("clawmetry/templates/tabs/notifications.html")
    # Look for the filter we added that excludes disabled rows.
    assert "state.rows.filter" in html and "r.enabled" in html, (
        "notifications.html must count only enabled channels in the status "
        "line; otherwise the header disagrees with the card grid."
    )


# ── Bug 3 ────────────────────────────────────────────────────────────────────
def test_bug3_gw_setup_modal_has_non_docker_path() -> None:
    """The gateway-setup modal must show a local-install path before Docker."""
    py = _read("dashboard.py")
    assert "Local install (pip / brew / install.sh)" in py, (
        "Gateway-setup modal must include a local-install instruction so "
        "non-Docker users have a working command."
    )
    # Docker block must still be present for Docker users.
    assert "Docker install" in py


# ── Bug 4 ────────────────────────────────────────────────────────────────────
def test_bug4_gw_setup_skips_when_cloud_modal_open() -> None:
    """The gateway-setup overlay must defer when a cloud modal is open, and
    openCloudModal must hide the gateway overlay when it shows."""
    js = _read("clawmetry/static/js/gw-setup.js")
    assert "_isCloudModalOpen" in js, "gw-setup.js missing cloud-modal guard"
    assert "cloud-modal-overlay" in js
    # And the cloud modal open path explicitly hides the gw overlay. Match
    # within the openCloudModal function body (its closing `}` ends the
    # block).
    m = re.search(r"function openCloudModal\([^)]*\)\s*\{([\s\S]*?)^\}", js, re.MULTILINE)
    assert m, "could not locate openCloudModal() body in gw-setup.js"
    body = m.group(1)
    assert "gw-setup-overlay" in body and "display = 'none'" in body, (
        "openCloudModal must suppress gw-setup-overlay (set display='none')"
    )


# ── Bug 5 ────────────────────────────────────────────────────────────────────
def test_bug5_no_pip_install_nemoclaw_in_user_copy() -> None:
    """`pip install nemoclaw` only exists as a 0.0.0a1 placeholder on PyPI —
    instructing users to run it is misleading. Make sure no user-facing
    string still suggests that command."""
    checked = [
        "clawmetry/static/js/app.js",
        "dashboard.py",
        "clawmetry/templates/tabs/nemoclaw.html",
    ]
    bad: list[str] = []
    for rel in checked:
        try:
            lines = _read(rel).splitlines()
        except FileNotFoundError:
            continue
        for i, line in enumerate(lines, 1):
            if "pip install nemoclaw" not in line:
                continue
            stripped = line.lstrip()
            # Allow it to live in a code comment that documents the fix.
            is_comment = (
                stripped.startswith("//")
                or stripped.startswith("#")
                or stripped.startswith("/*")
                or stripped.startswith("*")
            )
            if not is_comment:
                bad.append(f"{rel}:{i}: {line.strip()}")
    assert not bad, (
        "User-facing copy still suggests `pip install nemoclaw`, but the "
        "package is not publicly available:\n  " + "\n  ".join(bad)
    )


def test_bug5_nemoclaw_empty_state_says_coming_soon() -> None:
    """Empty state must be an honest 'Coming soon' rather than a broken
    install command."""
    js = _read("clawmetry/static/js/app.js")
    assert "Coming soon" in js and "NemoClaw governance is not yet available" in js, (
        "NemoClaw empty state must mention 'Coming soon' instead of "
        "suggesting `pip install nemoclaw`."
    )
