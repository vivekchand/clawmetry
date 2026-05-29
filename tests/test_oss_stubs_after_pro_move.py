"""Tests for the OSS 402-stub behavior after Pro impls moved to clawmetry-pro.

These pin the shape OSS-only installs see when clawmetry-pro is NOT
loaded. The corresponding full-impl tests now live in clawmetry-pro
(``tests/test_sinks_payloads.py`` and the moved
``tests/test_runtime_ingest.py``).

What this file covers:

* ``routes/runtime_ingest.py`` (OSS stub):
  - GET /api/v1/runtimes is still free (returns the catalogue)
  - POST /api/v1/runs returns 402 upgrade_required
  - POST /api/v1/runs/<id>/events returns 402
  - POST /api/v1/runs/<id>/end returns 402
  - GET  /api/v1/runs/<id> returns 402

* ``clawmetry/otel_push.py`` (OSS delegating shim):
  - forward_event() is a no-op when pro is unavailable
  - stats() returns {"running": False, "reason": ...}
  - reset_for_tests() is a no-op when pro is unavailable

* ``dashboard._build_pagerduty_payload`` / ``_build_opsgenie_payload``:
  - Return {} when ``clawmetry_pro.sinks`` is not importable

* ``dashboard._send_webhook_alert("...", ..., "pagerduty")``:
  - No-op when ``clawmetry_pro.sinks`` is not importable
"""
from __future__ import annotations

import importlib
import sys

import pytest
from flask import Flask


# ── runtime_ingest stub ───────────────────────────────────────────────────────


@pytest.fixture
def app_with_stub(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as _ent
    importlib.reload(_ent)
    _ent.invalidate()
    from routes import runtime_ingest as _ri
    importlib.reload(_ri)
    app = Flask(__name__)
    app.register_blueprint(_ri.bp_runtime_ingest)
    return app


def test_runtimes_list_stays_free(app_with_stub):
    with app_with_stub.test_client() as c:
        r = c.get("/api/v1/runtimes")
        assert r.status_code == 200
        body = r.get_json()
        assert isinstance(body["runtimes"], list)


def test_start_run_returns_402(app_with_stub):
    with app_with_stub.test_client() as c:
        r = c.post("/api/v1/runs", json={})
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "custom_runtime_ingest"
        assert "clawmetry-pro" in body["hint"]


def test_append_events_returns_402(app_with_stub):
    with app_with_stub.test_client() as c:
        r = c.post("/api/v1/runs/r1/events", json={"events": [{"event_type": "x"}]})
        assert r.status_code == 402


def test_end_run_returns_402(app_with_stub):
    with app_with_stub.test_client() as c:
        r = c.post("/api/v1/runs/r1/end", json={})
        assert r.status_code == 402


def test_get_run_returns_402(app_with_stub):
    with app_with_stub.test_client() as c:
        r = c.get("/api/v1/runs/r1")
        assert r.status_code == 402


# ── otel_push delegating shim ────────────────────────────────────────────────


def _hide_pro(monkeypatch):
    """Force ``from clawmetry_pro import otel_push`` to raise ImportError."""
    monkeypatch.setitem(sys.modules, "clawmetry_pro", None)
    monkeypatch.setitem(sys.modules, "clawmetry_pro.otel_push", None)
    monkeypatch.setitem(sys.modules, "clawmetry_pro.sinks", None)


def test_otel_push_forward_event_noop_when_pro_absent(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.otel_push as _otelp
    importlib.reload(_otelp)
    # Must not raise.
    _otelp.forward_event({"id": "e1", "event_type": "x"})


def test_otel_push_stats_reports_not_running(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.otel_push as _otelp
    importlib.reload(_otelp)
    s = _otelp.stats()
    assert s["running"] is False
    assert "reason" in s


def test_otel_push_reset_is_safe(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.otel_push as _otelp
    importlib.reload(_otelp)
    _otelp.reset_for_tests()  # no-op, no raise


# ── PD/OG dashboard helpers delegate ──────────────────────────────────────────


def test_build_pagerduty_payload_returns_empty_when_pro_absent(monkeypatch):
    _hide_pro(monkeypatch)
    import dashboard as _d
    body = _d._build_pagerduty_payload({"severity": "warning"}, routing_key="k")
    assert body == {}


def test_build_opsgenie_payload_returns_empty_when_pro_absent(monkeypatch):
    _hide_pro(monkeypatch)
    import dashboard as _d
    body = _d._build_opsgenie_payload({"severity": "warning"})
    assert body == {}


def test_send_webhook_alert_pagerduty_no_op_when_pro_absent(monkeypatch):
    _hide_pro(monkeypatch)
    import dashboard as _d
    # Must not raise; alert is dropped (logged at INFO level).
    _d._send_webhook_alert("", {"_pd_routing_key": "k", "severity": "warning"}, payload_type="pagerduty")


def test_send_webhook_alert_opsgenie_no_op_when_pro_absent(monkeypatch):
    _hide_pro(monkeypatch)
    import dashboard as _d
    _d._send_webhook_alert("", {"_og_api_key": "k", "severity": "warning"}, payload_type="opsgenie")
