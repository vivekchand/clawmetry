"""Tests for the ``POST /api/paywall/event`` telemetry endpoint
(``routes/entitlement.py::api_paywall_event``).

The route accepts a fire-and-forget client-side paywall ping
(``paywall_view`` / ``paywall_cta_click``) and is documented to:

* Always return **204** so callers never read the response.
* Never raise — a malformed payload, missing body, wrong content-type,
  or non-string fields must all fall through to 204.
* Truncate the ``event`` / ``harness`` / ``source`` fields to 64 chars
  and ``feature`` to 128 chars before logging, so an oversized field
  cannot blow up the log line or smuggle log content past the cap.
* Reject non-POST methods with 405 (Flask routing default).

None of these invariants are pinned today. This file is **tests-only**
— no production change — so the contract is locked in before any future
refactor of the endpoint (e.g. wiring the events into an analytics
sink) can silently regress it.
"""
from __future__ import annotations

import json
import logging

import pytest
from flask import Flask


@pytest.fixture
def client():
    """Minimal Flask app with ``bp_entitlement`` registered. The endpoint is
    pure logging + no I/O so no HOME / license / entitlements fixture is needed.
    """
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    app.config["TESTING"] = True
    return app.test_client()


# ── happy path ───────────────────────────────────────────────────────────────


def test_valid_event_returns_204(client):
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps(
            {
                "event": "paywall_view",
                "feature": "self_evolve",
                "harness": "claude_code",
                "source": "runtime_switcher",
            }
        ),
        content_type="application/json",
    )
    assert resp.status_code == 204
    # 204 contract: no body.
    assert resp.data == b""


def test_cta_click_event_returns_204(client):
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps({"event": "paywall_cta_click", "feature": "fleet"}),
        content_type="application/json",
    )
    assert resp.status_code == 204


# ── never-raise contract ─────────────────────────────────────────────────────


def test_empty_body_returns_204(client):
    """No body at all must still return 204 — the route uses
    ``request.get_json(silent=True)`` precisely so a beacon ping with no payload
    doesn't 500."""
    resp = client.post("/api/paywall/event")
    assert resp.status_code == 204


def test_empty_json_object_returns_204(client):
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 204


def test_malformed_json_body_returns_204(client):
    """A garbage body must not 400/500 — ``silent=True`` swallows the parse
    error and the route logs an empty event."""
    resp = client.post(
        "/api/paywall/event",
        data="{not valid json",
        content_type="application/json",
    )
    assert resp.status_code == 204


def test_missing_content_type_returns_204(client):
    """Beacons (``navigator.sendBeacon``) often omit the JSON content-type;
    silent=True still returns None and the handler must not raise."""
    resp = client.post("/api/paywall/event", data=json.dumps({"event": "paywall_view"}))
    assert resp.status_code == 204


def test_non_string_fields_do_not_raise(client):
    """The route does ``str(body.get(...))`` so ints / lists / dicts in the
    payload must coerce without raising."""
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps(
            {
                "event": 42,
                "feature": ["self_evolve"],
                "harness": {"name": "claude_code"},
                "source": None,
            }
        ),
        content_type="application/json",
    )
    assert resp.status_code == 204


def test_array_body_does_not_raise(client):
    """``get_json(silent=True)`` returns the parsed JSON which may be a list;
    the route guards with ``or {}`` so list bodies must still 204."""
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps(["not", "an", "object"]),
        content_type="application/json",
    )
    assert resp.status_code == 204


# ── truncation invariants ────────────────────────────────────────────────────


def _capture_log(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO, logger="clawmetry.routes.entitlement")
    return caplog


def test_event_field_truncated_to_64_chars(client, caplog):
    _capture_log(caplog)
    long_event = "a" * 200
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps({"event": long_event}),
        content_type="application/json",
    )
    assert resp.status_code == 204
    line = " ".join(r.getMessage() for r in caplog.records)
    assert "a" * 64 in line
    # The 65th `a` must not appear — caps the budget for log size.
    assert "a" * 65 not in line


def test_feature_field_truncated_to_128_chars(client, caplog):
    _capture_log(caplog)
    long_feature = "f" * 300
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps({"event": "paywall_view", "feature": long_feature}),
        content_type="application/json",
    )
    assert resp.status_code == 204
    line = " ".join(r.getMessage() for r in caplog.records)
    assert "f" * 128 in line
    assert "f" * 129 not in line


def test_harness_field_truncated_to_64_chars(client, caplog):
    _capture_log(caplog)
    long_harness = "h" * 200
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps({"event": "paywall_view", "harness": long_harness}),
        content_type="application/json",
    )
    assert resp.status_code == 204
    line = " ".join(r.getMessage() for r in caplog.records)
    assert "h" * 64 in line
    assert "h" * 65 not in line


def test_source_field_truncated_to_64_chars(client, caplog):
    _capture_log(caplog)
    long_source = "s" * 200
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps({"event": "paywall_view", "source": long_source}),
        content_type="application/json",
    )
    assert resp.status_code == 204
    line = " ".join(r.getMessage() for r in caplog.records)
    assert "s" * 64 in line
    assert "s" * 65 not in line


# ── method enforcement ───────────────────────────────────────────────────────


def test_get_method_not_allowed(client):
    """The route is registered POST-only; a GET must 405 so callers don't
    accidentally surface the telemetry endpoint as a readable resource."""
    resp = client.get("/api/paywall/event")
    assert resp.status_code == 405


def test_put_method_not_allowed(client):
    resp = client.put("/api/paywall/event", data=b"{}")
    assert resp.status_code == 405


# ── grace-mode invariant ─────────────────────────────────────────────────────


def test_endpoint_does_not_consult_entitlement(client):
    """The paywall telemetry endpoint must not gate on the resolved
    entitlement — it is a fire-and-forget client beacon that fires *exactly*
    when the user is locked out, so a paid/Pro/Enterprise install gating it
    would silently drop the event. Verify by monkey-patching
    ``clawmetry.entitlements.get_entitlement`` to raise and confirming the
    route still 204s."""
    import clawmetry.entitlements as e

    original = e.get_entitlement
    e.get_entitlement = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("nope"))
    try:
        resp = client.post(
            "/api/paywall/event",
            data=json.dumps({"event": "paywall_view"}),
            content_type="application/json",
        )
        assert resp.status_code == 204
    finally:
        e.get_entitlement = original


# ── logger pipeline ──────────────────────────────────────────────────────────


def test_event_is_logged_at_info_level(client, caplog):
    _capture_log(caplog)
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps(
            {"event": "paywall_view", "feature": "self_evolve", "harness": "claude_code"}
        ),
        content_type="application/json",
    )
    assert resp.status_code == 204
    info_records = [
        r for r in caplog.records
        if r.levelno == logging.INFO and r.name == "clawmetry.routes.entitlement"
    ]
    assert info_records, "expected an INFO log line on the entitlement route logger"
    joined = " ".join(r.getMessage() for r in info_records)
    assert "paywall_view" in joined
    assert "self_evolve" in joined
    assert "claude_code" in joined
