"""Regression tests for issue #1603 — Pro feature flash.

Pre-fix, the full Pro-feature DOM (NemoClaw governance shell, alerts
rule-editor modal) shipped in the dashboard HTML for every user. A
client-side overlay then mounted on a later tick to cover it. Free users
could:
  1. See the Pro UI rendered for ~1-3 frames (perception of paywall as
     artificial).
  2. Inspect/screenshot the Pro UI source.
  3. Land a frame-perfect click on the Pro feature before the overlay
     mounted — bypassing the gate entirely.

The fix is a server-side Jinja gate in ``routes/meta.py:index()`` that
branches on ``dashboard._is_pro_user()`` BEFORE the page is rendered.
Pro users get the full feature shell; Free / OSS users get the
``partials/paywall_modal.html`` partial in its place.

The tests below pin three scenarios:
  - Free / OSS user: NemoClaw shell is NOT in the response, alerts
    editor modal is NOT in the response, paywall partial IS.
  - Pro user: NemoClaw shell IS in the response, alerts editor modal
    IS in the response, paywall partial is NOT.
  - Exception in tier check: fail-closed to Free (no Pro DOM leaks).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import dashboard  # noqa: E402  (import registers shared module state)
from routes.meta import bp_auth  # noqa: E402


# Stable DOM markers that uniquely identify each surface. Picked over CSS
# class names because the latter change every redesign — these IDs come
# straight from the templates and are referenced by JS handlers, so they
# are load-bearing and unlikely to drift silently.
NEMOCLAW_SHELL_MARKER = 'id="page-nemoclaw"'
ALERTS_EDITOR_MARKER = 'id="alerts-editor-modal"'
PAYWALL_MARKER = 'id="page-nemoclaw"'  # paywall partial reuses the id
PAYWALL_FEATURE_MARKER = "NemoClaw governance"
PAYWALL_CTA_MARKER = "Start 7-day free trial"


@pytest.fixture
def client(monkeypatch):
    """Mount only ``bp_auth`` so the test stays hermetic.

    The auth blueprint owns the ``/`` index handler. We point the Flask
    app at the real templates directory so ``{% include 'tabs/...' %}``
    resolves the same files prod renders.
    """
    a = Flask(
        __name__,
        template_folder=os.path.join(ROOT, "clawmetry", "templates"),
    )
    a.register_blueprint(bp_auth)
    # Loopback peer so the @before_request auth hook (if any leaks in
    # through dashboard import) does not block the test client.
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", "", raising=False)
    return a.test_client()


def _get_index(client):
    r = client.get("/", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
    assert r.status_code == 200, r.get_data(as_text=True)[:500]
    return r.get_data(as_text=True)


# ─── Scenario 1: Free / OSS user ─────────────────────────────────────────


def test_free_user_index_omits_nemoclaw_pro_shell(client, monkeypatch):
    """Free user GET / must NOT include the NemoClaw governance shell.

    The pre-fix bug was that the shell rendered first then was covered
    by a JS overlay. With the server-side gate, the shell DOM should
    never enter the response in the first place.
    """
    monkeypatch.setattr(dashboard, "_is_pro_user", lambda: False)
    html = _get_index(client)
    # The shell's distinctive sandbox / policy / drift markers should be
    # gone. We can't just check ``id="page-nemoclaw"`` because the
    # paywall partial reuses that id (so JS switchTab still finds a
    # page to activate). Pick markers that ONLY appear in the shell.
    assert "nc-sandbox-status" not in html, (
        "NemoClaw sandbox status table leaked into Free-tier HTML "
        "(issue #1603 regression)."
    )
    assert "nc-policy-table" not in html, (
        "NemoClaw policy table leaked into Free-tier HTML."
    )
    assert "nc-approvals-list" not in html, (
        "NemoClaw approvals list leaked into Free-tier HTML."
    )


def test_free_user_index_omits_alerts_editor_modal(client, monkeypatch):
    """Free user GET / must NOT include the alerts rule editor modal.

    The canned-example teaser shell is intentional (memory:
    project_free_plan_upsell — let users invest in config before the
    paywall fires) so that part stays. But the editor's 6 alert-type
    buttons + channel picker + re-alert cadence inputs are Pro-only
    DOM that lets a Free user build a rule they can never save.
    """
    monkeypatch.setattr(dashboard, "_is_pro_user", lambda: False)
    html = _get_index(client)
    assert ALERTS_EDITOR_MARKER not in html, (
        "Alerts editor modal leaked into Free-tier HTML "
        "(issue #1603 regression)."
    )
    # The canned-example teaser shell must STILL be present — that is
    # the intentional upsell path.
    assert 'id="page-alerts"' in html
    assert "alerts-rules-list" in html


def test_free_user_index_includes_paywall_partial(client, monkeypatch):
    """Free user GET / must include the server-side paywall partial.

    Replaces the pre-fix client-side overlay that mounted on a later
    tick. Same render pass = no flash.
    """
    monkeypatch.setattr(dashboard, "_is_pro_user", lambda: False)
    html = _get_index(client)
    assert PAYWALL_FEATURE_MARKER in html, (
        "Paywall partial missing its NemoClaw feature headline."
    )
    assert PAYWALL_CTA_MARKER in html, (
        "Paywall partial missing the trial CTA."
    )


# ─── Scenario 2: Pro user ────────────────────────────────────────────────


def test_pro_user_index_includes_nemoclaw_full_shell(client, monkeypatch):
    """Pro user GET / must include the full NemoClaw governance shell.

    Critical: if the server-side gate is wrong we ship paywalls to
    paying customers, which is worse than the original flash bug.
    """
    monkeypatch.setattr(dashboard, "_is_pro_user", lambda: True)
    html = _get_index(client)
    assert "nc-sandbox-status" in html
    assert "nc-policy-table" in html
    assert "nc-approvals-list" in html


def test_pro_user_index_includes_alerts_editor_modal(client, monkeypatch):
    """Pro user GET / must include the alerts rule editor modal."""
    monkeypatch.setattr(dashboard, "_is_pro_user", lambda: True)
    html = _get_index(client)
    assert ALERTS_EDITOR_MARKER in html


def test_pro_user_index_omits_paywall_partial(client, monkeypatch):
    """Pro user GET / must NOT include the paywall partial."""
    monkeypatch.setattr(dashboard, "_is_pro_user", lambda: True)
    html = _get_index(client)
    assert PAYWALL_FEATURE_MARKER not in html, (
        "Paywall partial leaked into Pro-tier HTML — paying users "
        "would see the upsell where their feature should be."
    )


# ─── Scenario 3: fail-closed on errors ───────────────────────────────────


def test_index_fails_closed_when_tier_check_raises(client, monkeypatch):
    """If ``_is_pro_user`` raises, treat the user as Free.

    Matches the helper's own conservative default (a flaky cache must
    never leak Pro DOM onto a free node). The pre-fix bug had the
    inverse default — undefined-tier → showed Pro UI briefly — which is
    exactly how Free users could screenshot the Pro source.
    """
    def boom():
        raise RuntimeError("tier check failed")
    monkeypatch.setattr(dashboard, "_is_pro_user", boom)
    html = _get_index(client)
    # No Pro shell, paywall present.
    assert "nc-sandbox-status" not in html
    assert ALERTS_EDITOR_MARKER not in html
    assert PAYWALL_FEATURE_MARKER in html
