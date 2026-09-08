"""Regression checks for the issue-#1127 UX dead-end fixes.

Each test pins one of the 5 fixes so future refactors don't silently re-
introduce the bad copy / code path.

Why a static scan instead of a browser test: every fix is a frontend string
inside Python templates or a JS file. Spinning up Playwright for one-line
copy checks is overkill — a focused grep is sufficient and runs in <100 ms.
"""

from __future__ import annotations

import os

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
def test_bug3_no_manual_gateway_token_form() -> None:
    """There is no manual gateway-token form left to get wrong.

    Historical note: this originally pinned copy inside the auto-popping
    "ClawMetry Setup" modal (dashboard.py). That modal was retired
    (2026-08-06: it kept reappearing regardless of onboarding state, and
    the product now detects 20+ runtimes instead of assuming OpenClaw), and
    the opt-in Gateway tab that inherited its copy was removed too — the
    gateway token is auto-detected server-side from ~/.openclaw/openclaw.json
    (`_detect_gateway_token`), so asking the user to paste one was a dead end
    dressed up as configuration. Pin that neither surface comes back.
    """
    tab = os.path.join(ROOT, "clawmetry", "templates", "tabs", "gateway.html")
    assert not os.path.exists(tab), (
        "The manual gateway-token tab is gone; the token is auto-detected."
    )
    nav = _read("dashboard.py")
    assert 'data-tab="gateway"' not in nav, "Gateway nav item must stay removed."


# ── Bug 4 ────────────────────────────────────────────────────────────────────
def test_bug4_no_leftover_gw_setup_overlay_z_stacking_code() -> None:
    """Historical note: bug 4 was the auto-popping gateway-setup overlay
    z-stacking on top of the cloud sign-in modal. That overlay was retired
    entirely (2026-08-06) in favor of the onboarding-gate modal, so there
    is no longer a second modal to stack with — pin that the dead
    z-stacking guard (`_isCloudModalOpen`, only ever called from the
    removed modal's auto-show path) was cleaned up rather than left as
    dead code calling a now-nonexistent overlay."""
    js = _read("clawmetry/static/js/gw-setup.js")
    assert "gw-setup-overlay" not in js
    assert "_isCloudModalOpen" not in js


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
