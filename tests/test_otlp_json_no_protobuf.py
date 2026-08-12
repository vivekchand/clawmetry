"""OTLP/JSON ingest with NO protobuf installed — issue #4781.

``opentelemetry-proto`` sits behind the ``otel`` extra, so a default
``pip install clawmetry`` used to answer 501 to every OTLP request: the
receiver we advertise in the README was off for most users on first run.

These tests pin the dependency-free path. Every one of them runs with
``dashboard._HAS_OTEL_PROTO`` forced to False, so the JSON decoder is
exercised even on a CI runner that HAS protobuf installed — otherwise the
minimal-install behaviour would only ever be tested by not testing it.

Coverage:
  * real OpenLLMetry-shaped OTLP/JSON POST -> DuckDB -> ``GET /api/spans``
  * the wire-format traps: hex-string ids, int64-as-string, enum-as-name,
    gzip, arrayValue attributes, snake_case field aliases
  * honest status codes: 501 only for payloads that truly need protobuf,
    400 for a malformed body, never 501 for JSON traces or logs
  * the protobuf path still works unchanged when the extra IS installed
"""

from __future__ import annotations

import gzip
import importlib
import json
import time

import pytest
from flask import Flask

try:
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2 as _ts_pb2
    from opentelemetry.proto.trace.v1 import trace_pb2 as _trace_pb2
    _REALLY_HAS_PROTO = True
except Exception:  # pragma: no cover - minimal installs
    _REALLY_HAS_PROTO = False


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Fresh DuckDB store + Flask app with the OTLP receiver and /api/spans.

    Mirrors tests/test_spans_e2e.py's hermetic single-process setup: no daemon
    proxy, direct-open store, so the POST and the read hit the same DuckDB.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda *a, **k: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    import routes.sessions as ses
    importlib.reload(ses)
    import routes.meta as meta
    importlib.reload(meta)

    a = Flask(__name__)
    a.register_blueprint(ses.bp_sessions)
    a.register_blueprint(meta.bp_otel)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def no_proto(monkeypatch):
    """Simulate a default install: opentelemetry-proto absent."""
    import dashboard as _d
    monkeypatch.setattr(_d, "_HAS_OTEL_PROTO", False)
    return _d


# ── payload builders ────────────────────────────────────────────────────────


def _openllmetry_json(
    *,
    span_id="00000000000000a1",
    trace_id="0123456789abcdef0123456789abcdef",
    parent_span_id="",
    service_name="my-langchain-app",
    start_ts=None,
    duration_s=0.5,
    snake_case=False,
    extra_attrs=None,
):
    """An OTLP/JSON trace shaped the way traceloop-sdk / OpenLLMetry emits one.

    Deliberately uses the spec's awkward encodings: ids are hex strings,
    nanosecond timestamps are STRINGS (JSON cannot hold int64), ``intValue`` is
    a string, and the enums arrive as their proto names.
    """
    start_ts = time.time() - 60 if start_ts is None else start_ts
    start_ns = str(int(start_ts * 1e9))
    end_ns = str(int((start_ts + duration_s) * 1e9))
    attrs = [
        {"key": "gen_ai.operation.name", "value": {"stringValue": "chat"}},
        {"key": "gen_ai.request.model", "value": {"stringValue": "gpt-4o-mini"}},
        {"key": "gen_ai.provider.name", "value": {"stringValue": "openai"}},
        {"key": "gen_ai.usage.input_tokens", "value": {"intValue": "1200"}},
        {"key": "gen_ai.usage.output_tokens", "value": {"intValue": "340"}},
        {"key": "gen_ai.conversation.id", "value": {"stringValue": "conv-json-1"}},
        {"key": "stream", "value": {"boolValue": True}},
        {"key": "temperature", "value": {"doubleValue": 0.7}},
    ]
    attrs.extend(extra_attrs or [])
    span = {
        "traceId": trace_id,
        "spanId": span_id,
        "parentSpanId": parent_span_id,
        "name": "openai.chat",
        "kind": "SPAN_KIND_CLIENT",
        "startTimeUnixNano": start_ns,
        "endTimeUnixNano": end_ns,
        "attributes": attrs,
        "status": {"code": "STATUS_CODE_OK"},
    }
    body = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}},
                    ]
                },
                "scopeSpans": [{"spans": [span]}],
            }
        ]
    }
    if snake_case:
        # protobuf's JSON parser accepts the original field names too, and some
        # hand-rolled exporters emit them. Same payload, snake_case keys.
        span["trace_id"] = span.pop("traceId")
        span["span_id"] = span.pop("spanId")
        span["parent_span_id"] = span.pop("parentSpanId")
        span["start_time_unix_nano"] = span.pop("startTimeUnixNano")
        span["end_time_unix_nano"] = span.pop("endTimeUnixNano")
        rs = body["resourceSpans"][0]
        rs["scope_spans"] = rs.pop("scopeSpans")
        body["resource_spans"] = body.pop("resourceSpans")
    return json.dumps(body).encode("utf-8")


def _post_json(client, ls, payload, path="/v1/traces", **kw):
    r = client.post(path, data=payload, content_type="application/json", **kw)
    store = ls.get_store()
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        if store.health().get("ring_depth", 0) == 0:
            break
        time.sleep(0.02)
    return r


# ── the headline case ───────────────────────────────────────────────────────


def test_json_trace_ingests_without_protobuf(app, no_proto):
    """The whole point: a default install receives an OTLP/JSON trace."""
    a, ls = app
    c = a.test_client()

    r = _post_json(c, ls, _openllmetry_json())
    assert r.status_code == 200, (
        f"OTLP/JSON POST rejected on a no-protobuf install: "
        f"{r.status_code} {r.get_data(as_text=True)[:300]}"
    )

    body = c.get("/api/spans?limit=10").get_json()
    assert body["count"] == 1, f"span did not persist: {body}"
    span = body["spans"][0]
    assert span["span_id"] == "00000000000000a1"
    assert span["name"] == "openai.chat"
    assert span["kind"] == "CLIENT"
    assert span["duration_ms"] == pytest.approx(500.0, abs=1.0)
    assert span["session_id"] == "conv-json-1"


def test_json_trace_projects_typed_columns(app, no_proto):
    """Model, tokens, and derived cost must land in the typed columns, or the
    app shows up in the switcher with nothing in its cost tiles."""
    a, ls = app
    c = a.test_client()
    _post_json(c, ls, _openllmetry_json())

    rows = ls.get_store().query_spans(limit=10)
    assert len(rows) == 1
    row = rows[0]
    assert row["model"] == "gpt-4o-mini"
    assert row["tokens_input"] == 1200
    assert row["tokens_output"] == 340
    assert row["token_count"] == 1540
    # Cost is not an OTel-standard span attribute; _otel_to_row derives it from
    # tokens x model pricing. A token-bearing span must never read as $0.
    assert row["cost_usd"] and row["cost_usd"] > 0


def test_service_name_becomes_its_own_agent_type(app, no_proto):
    """#2822's rule must hold on the JSON path too: a foreign app is its own
    runtime, never mis-bucketed under openclaw."""
    a, ls = app
    c = a.test_client()
    _post_json(c, ls, _openllmetry_json(service_name="my-langchain-app"))

    row = ls.get_store().query_spans(limit=1)[0]
    assert row["agent_type"] == "my_langchain_app"
    assert row["service_name"] == "my-langchain-app"


# ── wire-format traps ───────────────────────────────────────────────────────


def test_snake_case_field_names_accepted(app, no_proto):
    a, ls = app
    c = a.test_client()
    r = _post_json(c, ls, _openllmetry_json(snake_case=True, span_id="00000000000000b2"))
    assert r.status_code == 200
    assert ls.get_store().query_spans(limit=5)[0]["span_id"] == "00000000000000b2"


def test_gzipped_json_accepted(app, no_proto):
    a, ls = app
    c = a.test_client()
    r = c.post(
        "/v1/traces",
        data=gzip.compress(_openllmetry_json(span_id="00000000000000c3")),
        content_type="application/json",
        headers={"Content-Encoding": "gzip"},
    )
    assert r.status_code == 200, r.get_data(as_text=True)[:300]


def test_array_and_kvlist_attributes_do_not_crash(app, no_proto):
    """Non-scalar AnyValues have no scalar field. They must survive as text,
    not blow up the batch (never crash on bad input)."""
    a, ls = app
    c = a.test_client()
    r = _post_json(c, ls, _openllmetry_json(extra_attrs=[
        {"key": "tags", "value": {"arrayValue": {"values": [
            {"stringValue": "a"}, {"stringValue": "b"}]}}},
        {"key": "meta", "value": {"kvlistValue": {"values": [
            {"key": "k", "value": {"stringValue": "v"}}]}}},
    ]))
    assert r.status_code == 200
    attrs = ls.get_store().query_spans(limit=1)[0]["attributes"]
    assert "tags" in attrs and "meta" in attrs


def test_span_events_and_links_survive(app, no_proto):
    a, ls = app
    c = a.test_client()
    payload = json.loads(_openllmetry_json(span_id="00000000000000d4"))
    span = payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
    span["events"] = [{
        "timeUnixNano": span["startTimeUnixNano"],
        "name": "first_token",
        "attributes": [{"key": "index", "value": {"intValue": "0"}}],
    }]
    span["links"] = [{
        "traceId": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "spanId": "bbbbbbbbbbbbbbbb",
        "attributes": [],
    }]
    r = _post_json(c, ls, json.dumps(payload).encode("utf-8"))
    assert r.status_code == 200
    row = ls.get_store().query_spans(limit=1)[0]
    assert row["events"][0]["name"] == "first_token"
    assert row["links"][0]["span_id"] == "bbbbbbbbbbbbbbbb"


def test_error_status_maps(app, no_proto):
    a, ls = app
    c = a.test_client()
    payload = json.loads(_openllmetry_json(span_id="00000000000000e5"))
    payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["status"] = {
        "code": "STATUS_CODE_ERROR", "message": "rate limited",
    }
    r = _post_json(c, ls, json.dumps(payload).encode("utf-8"))
    assert r.status_code == 200
    row = ls.get_store().query_spans(limit=1)[0]
    assert row["status_code"] == "ERROR"
    assert row["status_message"] == "rate limited"


def test_root_span_has_empty_parent(app, no_proto):
    """parent_span_id must stay falsy for roots or the trace tree cannot find
    its root and the waterfall renders empty."""
    a, ls = app
    c = a.test_client()
    _post_json(c, ls, _openllmetry_json(span_id="00000000000000f6"))
    assert not ls.get_store().query_spans(limit=1)[0]["parent_span_id"]


# ── honest status codes ─────────────────────────────────────────────────────


def test_protobuf_body_without_the_extra_still_501s(app, no_proto):
    """501 must still mean "install the extra", and only for payloads that
    genuinely need it."""
    a, _ls = app
    c = a.test_client()
    r = c.post("/v1/traces", data=b"\x0a\x00binary", content_type="application/x-protobuf")
    assert r.status_code == 501
    assert "opentelemetry-proto" in r.get_json()["error"]


def test_malformed_json_is_400_not_501(app, no_proto):
    a, _ls = app
    c = a.test_client()
    r = c.post("/v1/traces", data=b"{not json", content_type="application/json")
    assert r.status_code == 400


def test_json_logs_accepted_without_protobuf(app, no_proto):
    """/v1/logs carries the Claude Code / Codex event stream (#2596); it must
    not 501 on a default install either."""
    a, ls = app
    c = a.test_client()
    body = {"resourceLogs": [{
        "resource": {"attributes": [
            {"key": "service.name", "value": {"stringValue": "claude-code"}}]},
        "scopeLogs": [{"logRecords": [{
            "timeUnixNano": str(int(time.time() * 1e9)),
            "eventName": "claude_code.api_request",
            "attributes": [
                {"key": "model", "value": {"stringValue": "claude-opus-5"}},
                {"key": "cost_usd", "value": {"doubleValue": 0.0123}},
                {"key": "input_tokens", "value": {"intValue": "900"}},
                {"key": "output_tokens", "value": {"intValue": "120"}},
                {"key": "duration_ms", "value": {"doubleValue": 812.5}},
            ],
        }]}],
    }]}
    r = _post_json(c, ls, json.dumps(body).encode("utf-8"), path="/v1/logs")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]


def test_json_metrics_501s_with_an_honest_hint(app, no_proto):
    """Metrics still need protobuf (its mapper reaches into sum/gauge/histogram
    point types). Say so rather than pretending, and never 400 it."""
    a, _ls = app
    c = a.test_client()
    r = c.post("/v1/metrics", data=b'{"resourceMetrics":[]}',
               content_type="application/json")
    assert r.status_code == 501
    assert "opentelemetry-proto" in r.get_json()["error"]


# ── the protobuf path must be untouched ─────────────────────────────────────


@pytest.mark.skipif(not _REALLY_HAS_PROTO, reason="needs clawmetry[otel]")
def test_protobuf_path_unchanged(app):
    """The #4781 refactor routes both formats through _otlp_request. Prove the
    binary path still ingests when the extra IS installed."""
    a, ls = app
    c = a.test_client()
    req = _ts_pb2.ExportTraceServiceRequest()
    rs = req.resource_spans.add()
    ra = rs.resource.attributes.add()
    ra.key = "service.name"
    ra.value.string_value = "openclaw"
    sp = rs.scope_spans.add().spans.add()
    sp.trace_id = bytes.fromhex("0123456789abcdef0123456789abcdef")
    sp.span_id = bytes.fromhex("00000000000000aa")
    sp.name = "llm.call"
    sp.kind = _trace_pb2.Span.SPAN_KIND_CLIENT
    start_ns = int((time.time() - 30) * 1e9)
    sp.start_time_unix_nano = start_ns
    sp.end_time_unix_nano = start_ns + int(0.25 * 1e9)

    r = c.post("/v1/traces", data=req.SerializeToString(),
               content_type="application/x-protobuf")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    store = ls.get_store()
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline and store.health().get("ring_depth", 0):
        time.sleep(0.02)
    assert store.query_spans(limit=5)[0]["span_id"] == "00000000000000aa"


# ── the base64 id corruption ────────────────────────────────────────────────


def test_json_ids_stay_hex_even_with_protobuf_installed(app):
    """OTLP/JSON ids are HEX, and must survive as hex whether or not the
    ``otel`` extra is installed. NOTE: no ``no_proto`` fixture here on purpose.

    protobuf's ``json_format`` maps ``bytes`` fields from BASE64, but the
    OTLP/JSON spec overrides that for ``traceId`` / ``spanId`` /
    ``parentSpanId``. Routing JSON through ``json_format.Parse`` therefore
    base64-decoded every id and stored the garbage: measured on a live
    dashboard, span id ``3333333333333333`` persisted as
    ``df7df7df7df7df7df7df7df7``. Ids that do not round-trip cannot be
    correlated with the emitting app or any other backend, and a lookup by the
    real trace id finds nothing.
    """
    a, ls = app
    c = a.test_client()
    _post_json(c, ls, _openllmetry_json(
        span_id="3333333333333333",
        trace_id="33333333333333333333333333333333",
    ))

    row = ls.get_store().query_spans(limit=1)[0]
    assert row["span_id"] == "3333333333333333", (
        "OTLP/JSON span id was not stored verbatim; it was probably parsed as "
        "base64 (the pre-#4781 json_format path did exactly that)"
    )
    assert row["trace_id"] == "33333333333333333333333333333333"


def test_json_parent_child_ids_stay_hex(app):
    """Parent links must survive too, or the trace tree joins on garbage."""
    a, ls = app
    c = a.test_client()
    payload = json.loads(_openllmetry_json(span_id="00000000000000c1"))
    child = dict(payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0])
    child["spanId"] = "00000000000000c2"
    child["parentSpanId"] = "00000000000000c1"
    payload["resourceSpans"][0]["scopeSpans"][0]["spans"].append(child)

    _post_json(c, ls, json.dumps(payload).encode("utf-8"))
    rows = {r["span_id"]: r for r in ls.get_store().query_spans(limit=10)}
    assert set(rows) == {"00000000000000c1", "00000000000000c2"}
    assert rows["00000000000000c2"]["parent_span_id"] == "00000000000000c1"


# ── decoder unit tests ──────────────────────────────────────────────────────


def test_decoder_normalises_numeric_enums_and_ints():
    """Enums may arrive as ints instead of names, and some exporters send real
    JSON numbers for nanos. Both must decode identically."""
    from clawmetry.otlp_json import decode
    body = {"resourceSpans": [{"scopeSpans": [{"spans": [{
        "traceId": "0123456789abcdef0123456789abcdef",
        "spanId": "00000000000000a1",
        "name": "x",
        "kind": 3,
        "startTimeUnixNano": 1700000000000000000,
        "endTimeUnixNano": 1700000000500000000,
        "status": {"code": 2},
    }]}]}]}
    req = decode(json.dumps(body), "traces")
    span = req.resource_spans[0].scope_spans[0].spans[0]
    assert span.kind == 3
    assert span.start_time_unix_nano == 1700000000000000000
    assert span.HasField("status") and span.status.code == 2


def test_decoder_rejects_unknown_kind():
    from clawmetry.otlp_json import decode
    with pytest.raises(ValueError):
        decode("{}", "profiles")


def test_decoder_metrics_raises_the_typed_error():
    from clawmetry.otlp_json import OtlpProtobufUnavailable, decode
    with pytest.raises(OtlpProtobufUnavailable):
        decode("{}", "metrics")


def test_decoder_tolerates_missing_resource():
    """A payload with no resource block must still yield its spans."""
    from clawmetry.otlp_json import decode
    body = {"resourceSpans": [{"scopeSpans": [{"spans": [
        {"traceId": "ab" * 16, "spanId": "cd" * 8, "name": "n"}]}]}]}
    req = decode(json.dumps(body), "traces")
    assert req.resource_spans[0].resource is None
    assert req.resource_spans[0].scope_spans[0].spans[0].name == "n"
