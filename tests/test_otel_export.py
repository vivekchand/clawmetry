"""Tests for routes/otel_export.py — Pro+ OTLP/JSON export.

Validates the envelope shape, event→LogRecord mapping, and attribute
encoding. The entitlement-gate contract (grace passthrough + enforce 402)
is pinned end-to-end in ``tests/test_otel_export_route_gate.py`` now that
the route uses the shared ``@gate("otel_export")`` decorator instead of a
hand-rolled ``_entitlement_allows()`` helper.
"""
from __future__ import annotations

import routes.otel_export as O


def test_envelope_shape_and_scope():
    env = O._build_otlp_envelope([])
    assert "resourceLogs" in env and isinstance(env["resourceLogs"], list)
    rl = env["resourceLogs"][0]
    res_attrs = {a["key"]: a["value"]["stringValue"] for a in rl["resource"]["attributes"]}
    assert res_attrs["service.name"] == "clawmetry"
    scope = rl["scopeLogs"][0]["scope"]
    assert scope["name"] == "clawmetry.events"


def test_event_to_log_record_basic():
    rec = O._event_to_log_record({
        "ts": 1717000000.5, "event_type": "model.completed",
        "session_id": "abc", "role": "assistant", "model": "claude-opus-4-7",
    })
    assert rec["severityText"] == "INFO"
    assert rec["body"]["stringValue"] == "model.completed"
    attrs = {a["key"]: a["value"] for a in rec["attributes"]}
    assert attrs["session_id"]["stringValue"] == "abc"
    assert attrs["event_type"]["stringValue"] == "model.completed"
    assert attrs["model"]["stringValue"] == "claude-opus-4-7"
    # nanosecond conversion
    assert rec["timeUnixNano"] == str(1717000000_500_000_000)


def test_attribute_type_encoding():
    rec = O._event_to_log_record({"ts": 0, "event_type": "x", "model": 42})
    attrs = {a["key"]: a["value"] for a in rec["attributes"]}
    assert "intValue" in attrs["model"]


def test_missing_fields_dont_raise():
    # Defensive: a sparse event row must never crash mapping.
    rec = O._event_to_log_record({})
    assert rec["body"]["stringValue"] == "event"
    assert rec["timeUnixNano"] == "0"


