"""Tests for issue #555 — Phase 1: hard budget cap config + pause flag + banner.

Two surfaces covered:

  1. ``_is_over_cap("daily")`` — set cap=10, spend=10.5, expect tripped=True
     with the spent/cap echoed back so the banner can render the dollar
     figure. Also asserts the "no cap configured" path (cap=0) never
     trips, which is the default-safe behaviour all new installs land on.

  2. ``POST /api/budget/pause-gateway`` — flips the daemon-level
     ``_budget_paused`` flag to True, persists a reason, and
     ``/api/budget/status`` then surfaces ``paused=true`` so the
     dashboard banner JS (``checkActiveAlerts``) shows the cap-reached
     message and resume CTA.

Stays under 70 lines of test logic so the diff fits the issue's 300 LOC
budget. Per-session cap accounting + actual gateway-RPC pause land in
Phase 2 and have their own coverage.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def dashboard_module(tmp_path, monkeypatch):
    """Fresh dashboard import against a temp fleet.db. Wipes in-memory
    cost store + paused flag between tests so the cap helper sees a
    deterministic starting point."""
    sys.modules.pop("dashboard", None)
    sys.modules.pop("routes.alerts", None)
    import dashboard as _d
    import routes.alerts as ra
    importlib.reload(ra)

    _d.FLEET_DB_PATH = str(tmp_path / "fleet.db")
    with _d._metrics_lock:
        _d.metrics_store["cost"].clear()
    _d._budget_paused = False
    _d._budget_paused_at = 0
    _d._budget_paused_reason = ""
    try:
        _d._budget_init_db()
    except Exception:
        pass

    # Don't actually shell out to the openclaw CLI / send SIGTERM during
    # the test. We only care about the in-process state transitions.
    monkeypatch.setattr(_d, "_pause_gateway", lambda: None)
    yield _d


def _set_daily_spend(_d, usd):
    """Force a known daily_spent value by injecting a fresh OTLP cost
    row. The "fresh OTLP" branch in _get_budget_status uses
    metrics_store directly when a row is within the 5-min window, which
    sidesteps DuckDB entirely for the unit test."""
    import time as _t
    with _d._metrics_lock:
        _d.metrics_store["cost"].append({
            "timestamp": _t.time(),
            "usd": float(usd),
            "agent": "main",
            "model": "test-model",
        })


# ── 1. _is_over_cap ────────────────────────────────────────────────────


def test_is_over_cap_triggers_at_threshold(dashboard_module):
    """cap=10, spend=10.5 → tripped True with cap/spent echoed back."""
    _d = dashboard_module
    _d._set_budget_config({"daily_cap_usd": 10.0})
    _set_daily_spend(_d, 10.5)

    tripped, info = _d._is_over_cap("daily")
    assert tripped is True, f"expected tripped, got info={info}"
    assert info["cap"] == 10.0
    assert info["spent"] >= 10.5
    assert info["scope"] == "daily"


def test_is_over_cap_returns_false_when_no_cap_configured(dashboard_module):
    """cap=0 (default) never trips even on real spend — safety default."""
    _d = dashboard_module
    _set_daily_spend(_d, 999.0)
    tripped, info = _d._is_over_cap("daily")
    assert tripped is False
    assert info["cap"] == 0.0


def test_is_over_cap_returns_false_just_under_threshold(dashboard_module):
    """cap=10, spend=9.99 → not tripped."""
    _d = dashboard_module
    _d._set_budget_config({"daily_cap_usd": 10.0})
    _set_daily_spend(_d, 9.99)
    tripped, _ = _d._is_over_cap("daily")
    assert tripped is False


def test_is_over_cap_unknown_scope_safely_false(dashboard_module):
    """Garbage scope returns False rather than crashing the caller."""
    _d = dashboard_module
    tripped, info = _d._is_over_cap("yearly")
    assert tripped is False
    assert "error" in info


# ── 2. POST /api/budget/pause-gateway ──────────────────────────────────


def _make_client(_d):
    from flask import Flask
    import routes.alerts as ra
    app = Flask(__name__)
    app.register_blueprint(ra.bp_budget)
    return app.test_client()


def test_pause_gateway_sets_flag_and_status_reflects_paused(dashboard_module):
    """POST pause-gateway → _budget_paused True → /status reports paused."""
    _d = dashboard_module
    client = _make_client(_d)

    # Sanity check: starts un-paused.
    pre = client.get("/api/budget/status").get_json()
    assert pre["paused"] is False

    resp = client.post(
        "/api/budget/pause-gateway",
        json={"reason": "Daily cap reached: $10.50 / $10.00"},
    )
    assert resp.status_code == 200, resp.data
    body = resp.get_json()
    assert body["ok"] is True
    assert body["paused"] is True

    # Flag is persisted in the daemon-level globals…
    assert _d._budget_paused is True
    assert _d._budget_paused_reason.startswith("Daily cap reached")
    # …and visible through /api/budget/status, which is what the banner JS
    # polls.
    post = client.get("/api/budget/status").get_json()
    assert post["paused"] is True
    assert post["paused_reason"].startswith("Daily cap reached")


def test_resume_gateway_clears_flag(dashboard_module):
    """POST resume-gateway → _budget_paused False again."""
    _d = dashboard_module
    client = _make_client(_d)
    _d._budget_paused = True
    _d._budget_paused_at = 1.0
    _d._budget_paused_reason = "Daily cap reached"

    resp = client.post("/api/budget/resume-gateway")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["paused"] is False
    assert _d._budget_paused is False


# ── 3. Config persistence for new cap keys ─────────────────────────────


def test_new_cap_keys_round_trip_through_config_api(dashboard_module):
    """POST /api/budget/config accepts the three new cap keys and they
    round-trip back through the GET path with their numeric values
    intact (issue body requirement #1)."""
    _d = dashboard_module
    client = _make_client(_d)
    resp = client.post(
        "/api/budget/config",
        json={
            "daily_cap_usd": 25.5,
            "monthly_cap_usd": 500.0,
            "session_cap_usd": 2.5,
        },
    )
    assert resp.status_code == 200, resp.data

    g = client.get("/api/budget/config").get_json()
    assert g["daily_cap_usd"] == 25.5
    assert g["monthly_cap_usd"] == 500.0
    assert g["session_cap_usd"] == 2.5
