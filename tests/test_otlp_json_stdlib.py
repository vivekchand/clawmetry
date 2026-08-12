"""Test OTLP/JSON trace ingest without opentelemetry-proto (#4781).

Verifies that a default `pip install clawmetry` (no [otel] extra) can receive
OTLP/JSON traces on /v1/traces and persist them to DuckDB. The protobuf path
is explicitly excluded by monkeypatching _HAS_OTEL_PROTO = False.
"""

from __future__ import annotations

import importlib
import json
import time

import pytest
from flask import Flask


SAMPLE_TRACE = {
    "resourceSpans": [
        {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "my-langchain-app"}},
                    {"key": "host.name", "value": {"stringValue": "dev-box"}},
                ]
            },
            "scopeSpans": [
                {
                    "scope": {"name": "openai"},
                    "spans": [
                        {
                            "traceId": "abcdef1234567890abcdef1234567890",
                            "spanId": "1234567890abcdef",
                            "parentSpanId": "",
                            "name": "openai.chat",
                            "kind": 3,
                            "startTimeUnixNano": str(int(time.time() * 1e9)),
                            "endTimeUnixNano": str(int(time.time() * 1e9) + 500_000_000),
                            "attributes": [
                                {"key": "gen_ai.request.model", "value": {"stringValue": "gpt-4o"}},
                                {"key": "gen_ai.usage.input_tokens", "value": {"intValue": "120"}},
                                {"key": "gen_ai.usage.output_tokens", "value": {"intValue": "45"}},
                                {"key": "gen_ai.usage.cost_usd", "value": {"doubleValue": 0.0023}},
                                {"key": "gen_ai.operation.name", "value": {"stringValue": "chat"}},
                            ],
                            "status": {"code": 1, "message": ""},
                            "events": [],
                            "links": [],
                        }
                    ],
                }
            ],
        }
    ]
}


@pytest.fixture
def app_no_proto(tmp_path, monkeypatch):
    """Flask app with _HAS_OTEL_PROTO=False to simulate a default install."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)

    import dashboard as _d
    importlib.reload(_d)

    # Simulate no protobuf installed.
    monkeypatch.setattr(_d, "_HAS_OTEL_PROTO", False)

    from routes.meta import bp_otel
    from routes.otel_export import bp_otel_export

    mini = Flask(__name__)
    mini.register_blueprint(bp_otel)
    mini.register_blueprint(bp_otel_export)
    mini.config["TESTING"] = True
    yield mini


def test_json_trace_returns_200_without_proto(app_no_proto):
    """A JSON OTLP POST must succeed even without opentelemetry-proto."""
    with app_no_proto.test_client() as client:
        resp = client.post(
            "/v1/traces",
            data=json.dumps(SAMPLE_TRACE),
            content_type="application/json",
        )
    assert resp.status_code == 200, resp.get_data(as_text=True)


def test_binary_trace_returns_501_without_proto(app_no_proto):
    """A binary protobuf POST must still return 501 without the [otel] extra."""
    with app_no_proto.test_client() as client:
        resp = client.post(
            "/v1/traces",
            data=b"\x00\x01\x02",
            content_type="application/x-protobuf",
        )
    assert resp.status_code == 501


def test_json_attr_value_types():
    """_otlp_json_attr_value handles all OTLP/JSON tagged-union variants."""
    import dashboard as _d

    assert _d._otlp_json_attr_value({"stringValue": "hello"}) == "hello"
    assert _d._otlp_json_attr_value({"intValue": "42"}) == 42
    assert _d._otlp_json_attr_value({"doubleValue": 1.5}) == 1.5
    assert _d._otlp_json_attr_value({"boolValue": True}) is True
    arr = _d._otlp_json_attr_value({"arrayValue": {"values": [{"stringValue": "a"}, {"intValue": "1"}]}})
    assert arr == ["a", 1]


def test_json_span_row_shape():
    """_otlp_json_span_to_row produces the expected row keys."""
    import dashboard as _d

    span = SAMPLE_TRACE["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
    attrs = {a["key"]: _d._otlp_json_attr_value(a["value"]) for a in span.get("attributes", [])}
    resource_attrs = {a["key"]: _d._otlp_json_attr_value(a["value"])
                      for a in SAMPLE_TRACE["resourceSpans"][0]["resource"]["attributes"]}
    row = _d._otlp_json_span_to_row(span, attrs, resource_attrs)

    assert row["span_id"] == "1234567890abcdef"
    assert row["trace_id"] == "abcdef1234567890abcdef1234567890"
    assert row["parent_span_id"] is None  # empty string → None
    assert row["name"] == "openai.chat"
    assert row["agent_type"] == "my_langchain_app"  # service.name slugified
    assert row["model"] == "gpt-4o"
    assert row["tokens_input"] == 120
    assert row["tokens_output"] == 45
    assert row["cost_usd"] == pytest.approx(0.0023)
    assert row["duration_ns"] > 0
    assert row["kind"] == "CLIENT"
    assert row["status_code"] == "OK"
