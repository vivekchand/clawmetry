"""Deep edge-case coverage for the OTLP traces → /api/spans feature.

Companion to ``tests/test_spans_e2e.py`` (the happy-path real-OTLP e2e). This
file pins the edge cases a user-facing tracing surface must survive WITHOUT
crashing or silently corrupting data, driven through the REAL ingest path
(``POST /v1/traces`` → ``_process_otlp_traces`` → DuckDB → ``GET /api/spans``):

  * empty trace request (no spans) — accepted, no rows, no error;
  * span missing session.id — still ingested, never 500s;
  * minimal span (only required OTLP fields) — ingested;
  * duplicate span_id re-POST — idempotent (no double row);
  * multiple resource_spans in one request — all ingested;
  * token-only span (no cost attr) — cost derived from tokens × model pricing
    (#2049 read-path), not left null;
  * retention boundary — a span just inside 24h shows, just outside is capped;
  * malformed payload bytes — 400, never a 500/stacktrace leak.

Deterministic (we control every OTLP payload) and real (HTTP both ways).
Gated on ``opentelemetry-proto`` (the receiver 501s without it).
"""

from __future__ import annotations

import gzip as _gzip
import importlib
import json as _json
import time

import pytest
from flask import Flask
from google.protobuf import json_format as _json_format

try:
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2 as _ts_pb2
    from opentelemetry.proto.trace.v1 import trace_pb2 as _trace_pb2
    _HAS_OTEL_PROTO = True
except Exception:  # pragma: no cover
    _HAS_OTEL_PROTO = False

try:
    from opentelemetry.proto.collector.metrics.v1 import (
        metrics_service_pb2 as _ms_pb2,
    )
except Exception:  # pragma: no cover
    _ms_pb2 = None

pytestmark = pytest.mark.skipif(
    not _HAS_OTEL_PROTO,
    reason="opentelemetry-proto not installed (pip install clawmetry[otel])",
)


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Hermetic: force the in-process direct store past any host daemon proxy
    # (CI has no daemon; this makes the suite pass on a dev box too).
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


def _hx(n: int) -> str:
    return f"{n:016x}"


def _build_req(specs, *, n_resource_spans=1, service_name="openclaw"):
    """Build the OTLP request PROTO object (not yet serialized) so callers can
    pick the wire encoding (binary / JSON / gzip). ``specs`` is a list of span
    dicts; set n_resource_spans>1 to split them across multiple resource_spans."""
    req = _ts_pb2.ExportTraceServiceRequest()
    groups = [[] for _ in range(n_resource_spans)]
    for i, spec in enumerate(specs):
        groups[i % n_resource_spans].append(spec)
    for grp in groups:
        rs = req.resource_spans.add()
        ra = rs.resource.attributes.add()
        ra.key = "service.name"
        ra.value.string_value = service_name
        ss = rs.scope_spans.add()
        for spec in grp:
            sp = ss.spans.add()
            sp.trace_id = bytes.fromhex("0123456789abcdef0123456789abcdef")
            sp.span_id = bytes.fromhex(spec["span_id_hex"])
            sp.name = spec.get("name", "llm.call")
            sp.kind = _trace_pb2.Span.SPAN_KIND_CLIENT
            start_ns = int(spec["start_ts"] * 1e9)
            sp.start_time_unix_nano = start_ns
            sp.end_time_unix_nano = start_ns + int(spec.get("duration_s", 0.5) * 1e9)
            sp.status.code = _trace_pb2.Status.STATUS_CODE_OK
            for k, v in (spec.get("str_attrs") or {}).items():
                a = sp.attributes.add()
                a.key = k
                a.value.string_value = v
            for k, iv in (spec.get("int_attrs") or {}).items():
                a = sp.attributes.add()
                a.key = k
                a.value.int_value = iv
    return req


def _build_pb(specs, *, n_resource_spans=1, service_name="openclaw"):
    """Serialized (binary protobuf) OTLP request — the common case."""
    return _build_req(
        specs, n_resource_spans=n_resource_spans, service_name=service_name
    ).SerializeToString()


def _post(client, pb_bytes):
    return client.post("/v1/traces", data=pb_bytes,
                       content_type="application/x-protobuf")


def _drain(ls, t=3.0):
    store = ls.get_store()
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health().get("ring_depth", 0) == 0:
            return
        time.sleep(0.02)


def _spans(client, qs=""):
    r = client.get("/api/spans" + qs)
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    return r.get_json()


# ── empty / minimal ─────────────────────────────────────────────────────────


def test_empty_trace_request_accepted_no_rows(app):
    a, ls = app
    c = a.test_client()
    r = _post(c, _build_pb([]))
    assert r.status_code == 200, "empty OTLP request must be accepted, not error"
    _drain(ls)
    assert _spans(c)["count"] == 0


def test_minimal_span_only_required_fields(app):
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    _post(c, _build_pb([{"span_id_hex": _hx(1), "start_ts": base}]))
    _drain(ls)
    body = _spans(c, "?limit=10")
    assert body["count"] == 1
    assert body["spans"][0]["span_id"] == _hx(1)


def test_span_missing_session_id_still_ingests(app):
    """A span with no session.id must never 500 the receiver; it ingests with
    an empty/None session_id and is still listable."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    r = _post(c, _build_pb([{"span_id_hex": _hx(2), "start_ts": base,
                             "str_attrs": {"gen_ai.request.model": "x"}}]))
    assert r.status_code == 200
    _drain(ls)
    assert _spans(c, "?limit=10")["count"] == 1


# ── idempotency / multi-resource ────────────────────────────────────────────


def test_duplicate_span_id_is_idempotent(app):
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    spec = [{"span_id_hex": _hx(3), "start_ts": base,
             "str_attrs": {"session.id": "s-dup"}}]
    _post(c, _build_pb(spec)); _drain(ls)
    _post(c, _build_pb(spec)); _drain(ls)  # same span_id again
    _post(c, _build_pb(spec)); _drain(ls)
    body = _spans(c, "?session_id=s-dup&limit=10")
    assert body["count"] == 1, (
        f"duplicate span_id re-POST must not create duplicate rows; "
        f"got {body['count']}"
    )


def test_multiple_resource_spans_all_ingested(app):
    a, ls = app
    c = a.test_client()
    base = time.time() - 60
    specs = [{"span_id_hex": _hx(0x10 + i), "start_ts": base + i,
              "str_attrs": {"session.id": "s-multi"}} for i in range(4)]
    _post(c, _build_pb(specs, n_resource_spans=3))  # split across 3 resources
    _drain(ls)
    assert _spans(c, "?session_id=s-multi&limit=20")["count"] == 4


# ── cost derivation (#2049) ─────────────────────────────────────────────────


def test_token_only_span_derives_cost(app):
    """OTLP GenAI spans carry tokens but usually NO cost attribute. The read
    path must derive cost from tokens × model pricing, not leave it null."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    _post(c, _build_pb([{
        "span_id_hex": _hx(0x30), "start_ts": base,
        "str_attrs": {"session.id": "s-cost",
                      "gen_ai.request.model": "claude-3-5-haiku-20241022",
                      "gen_ai.provider.name": "anthropic"},
        "int_attrs": {"gen_ai.usage.input_tokens": 1000,
                      "gen_ai.usage.output_tokens": 500},
    }]))
    _drain(ls)
    store = ls.get_store()
    rows = store._fetch(
        "SELECT cost_usd, tokens_input, tokens_output FROM spans "
        "WHERE session_id='s-cost'", [])
    assert rows, "token-only span was not ingested"
    cost, ti, to = rows[0]
    assert ti == 1000 and to == 500
    assert cost is not None and cost > 0, (
        f"cost must be DERIVED from tokens×pricing for a token-only span; "
        f"got {cost!r}"
    )


# ── retention boundary (#1374) ──────────────────────────────────────────────


def test_retention_boundary_24h(app, monkeypatch):
    """Non-Pro: a span ~just inside 24h is shown; ~just outside is capped."""
    a, ls = app
    c = a.test_client()
    now = time.time()
    _post(c, _build_pb([
        {"span_id_hex": _hx(0x41), "start_ts": now - (24 * 3600 - 600),  # inside
         "str_attrs": {"session.id": "s-ret"}},
        {"span_id_hex": _hx(0x42), "start_ts": now - (24 * 3600 + 600),  # outside
         "str_attrs": {"session.id": "s-ret"}},
    ]))
    _drain(ls)
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)
    body = _spans(c, "?session_id=s-ret&limit=10")
    assert body["capped_at_24h"] is True
    ids = {s["span_id"] for s in body["spans"]}
    assert _hx(0x41) in ids, "span just inside 24h must be visible"
    assert _hx(0x42) not in ids, "span just outside 24h must be capped out"


# ── malformed input ─────────────────────────────────────────────────────────


def test_malformed_protobuf_is_400_not_500(app):
    """Garbage bytes to /v1/traces must be a clean 4xx, never a 500 with a
    stacktrace (the receiver is internet-facing on opted-in installs)."""
    a, _ls = app
    c = a.test_client()
    r = c.post("/v1/traces", data=b"\x00\x01not-a-valid-protobuf\xff\xfe",
               content_type="application/x-protobuf")
    assert r.status_code in (400, 422), (
        f"malformed OTLP must be a 4xx, got {r.status_code}: "
        f"{r.get_data(as_text=True)[:200]}"
    )
    assert r.status_code != 500


# ════════════════════════════════════════════════════════════════════════════
# OpenLLMetry ("bring your own agent") ingest — OTLP/JSON + gzip, indexed
# prompts, service.name runtime identity, gen_ai.* live tiles + metrics.
# OpenLLMetry / traceloop-sdk is the neutral standard most third-party apps use;
# these pin that ClawMetry is a first-class OTLP backend for them.
# ════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def clear_metrics():
    """The in-memory metrics tiles are module-global; clear them so a test can
    assert exactly what its own POST produced."""
    import dashboard as _d
    with _d._metrics_lock:
        for k in _d.metrics_store:
            _d.metrics_store[k].clear()
    yield _d


# ── OTLP/JSON + gzip wire encodings ─────────────────────────────────────────


def test_gzip_protobuf_accepted(app):
    """OTLP exporters can gzip the body (Content-Encoding: gzip). The receiver
    must gunzip before parsing, not 400 on the compressed bytes."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    raw = _build_pb([{"span_id_hex": _hx(0x51), "start_ts": base,
                      "str_attrs": {"session.id": "s-gz"}}])
    r = c.post("/v1/traces", data=_gzip.compress(raw),
               content_type="application/x-protobuf",
               headers={"Content-Encoding": "gzip"})
    assert r.status_code == 200, r.get_data(as_text=True)[:200]
    _drain(ls)
    assert _spans(c, "?session_id=s-gz&limit=10")["count"] == 1


def test_otlp_json_accepted_and_parsed_identically(app):
    """OTLP/JSON (Content-Type: application/json) must parse into the same proto
    and persist the span identically to the binary path."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    req = _build_req([{"span_id_hex": _hx(0x52), "start_ts": base,
                       "str_attrs": {"session.id": "s-json",
                                     "gen_ai.request.model": "claude-3-5-haiku-20241022"},
                       "int_attrs": {"gen_ai.usage.input_tokens": 10,
                                     "gen_ai.usage.output_tokens": 5}}])
    body = _json_format.MessageToJson(req)
    r = c.post("/v1/traces", data=body, content_type="application/json")
    assert r.status_code == 200, r.get_data(as_text=True)[:200]
    _drain(ls)
    sp = _spans(c, "?session_id=s-json&limit=10")
    assert sp["count"] == 1
    assert sp["spans"][0]["span_id"] == _hx(0x52)
    assert sp["spans"][0].get("model") == "claude-3-5-haiku-20241022"


def test_gzip_json_accepted(app):
    """The two can combine: gzip-wrapped OTLP/JSON."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    req = _build_req([{"span_id_hex": _hx(0x53), "start_ts": base,
                       "str_attrs": {"session.id": "s-gzjson"}}])
    body = _json_format.MessageToJson(req).encode("utf-8")
    r = c.post("/v1/traces", data=_gzip.compress(body),
               content_type="application/json",
               headers={"Content-Encoding": "gzip"})
    assert r.status_code == 200, r.get_data(as_text=True)[:200]
    _drain(ls)
    assert _spans(c, "?session_id=s-gzjson&limit=10")["count"] == 1


def test_malformed_json_is_400_not_500(app):
    """Garbage JSON to /v1/traces must be a clean 4xx, never a 500."""
    a, _ls = app
    c = a.test_client()
    r = c.post("/v1/traces", data=b'{"not":"a valid OTLP doc"',
               content_type="application/json")
    assert r.status_code in (400, 422), r.get_data(as_text=True)[:200]
    assert r.status_code != 500


# ── indexed prompt / completion attributes (OpenLLMetry shape) ──────────────


def test_indexed_prompts_assemble_into_input_output(app):
    """OpenLLMetry emits gen_ai.prompt.<i>.role/content and
    gen_ai.completion.<i>.role/content rather than the flat semconv keys. They
    must be assembled, in order, into the span input/output columns."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    _post(c, _build_pb([{
        "span_id_hex": _hx(0x60), "start_ts": base, "name": "openai.chat",
        "str_attrs": {
            "session.id": "s-idx",
            "gen_ai.prompt.0.role": "system",
            "gen_ai.prompt.0.content": "You are helpful.",
            "gen_ai.prompt.1.role": "user",
            "gen_ai.prompt.1.content": "Hello there",
            "gen_ai.completion.0.role": "assistant",
            "gen_ai.completion.0.content": "Hi! How can I help?",
        },
    }]))
    _drain(ls)
    store = ls.get_store()
    rows = store._fetch(
        "SELECT input, output FROM spans WHERE session_id='s-idx'", [])
    assert rows, "indexed-prompt span was not ingested"
    raw_in, raw_out = rows[0]
    inp = raw_in.decode() if isinstance(raw_in, (bytes, bytearray)) else raw_in
    out = raw_out.decode() if isinstance(raw_out, (bytes, bytearray)) else raw_out
    msgs_in = _json.loads(inp)
    msgs_out = _json.loads(out)
    assert [m.get("role") for m in msgs_in] == ["system", "user"], msgs_in
    assert msgs_in[1]["content"] == "Hello there"
    assert msgs_out[0]["role"] == "assistant"
    assert msgs_out[0]["content"] == "Hi! How can I help?"


def test_flat_keys_win_over_indexed(app):
    """When the flat gen_ai.prompt key is present it must be used as-is (the
    indexed assembly only kicks in as a fallback)."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    _post(c, _build_pb([{
        "span_id_hex": _hx(0x61), "start_ts": base,
        "str_attrs": {
            "session.id": "s-flat",
            "gen_ai.prompt": "FLAT-PROMPT-WINS",
            "gen_ai.prompt.0.content": "indexed-should-be-ignored",
        },
    }]))
    _drain(ls)
    store = ls.get_store()
    rows = store._fetch("SELECT input FROM spans WHERE session_id='s-flat'", [])
    raw = rows[0][0]
    inp = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
    assert "FLAT-PROMPT-WINS" in inp


# ── service.name → agent_type runtime identity ──────────────────────────────


def test_service_name_becomes_agent_type_slug(app):
    """A foreign OpenLLMetry app's service.name becomes its agent_type slug so
    it shows up as its OWN runtime, not mis-bucketed under openclaw."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    _post(c, _build_pb([{"span_id_hex": _hx(0x70), "start_ts": base,
                         "str_attrs": {"session.id": "s-svc"}}],
                       service_name="my-langchain-app"))
    _drain(ls)
    store = ls.get_store()
    rows = store._fetch(
        "SELECT agent_type FROM spans WHERE session_id='s-svc'", [])
    assert rows and rows[0][0] == "my_langchain_app", rows


def test_service_name_absent_falls_back_to_custom(app):
    """No service.name on the resource → agent_type 'custom' (NOT openclaw)."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    # Build a request with NO service.name resource attribute.
    req = _ts_pb2.ExportTraceServiceRequest()
    rs = req.resource_spans.add()
    ss = rs.scope_spans.add()
    sp = ss.spans.add()
    sp.trace_id = bytes.fromhex("0123456789abcdef0123456789abcdef")
    sp.span_id = bytes.fromhex(_hx(0x71))
    sp.name = "openai.chat"
    sp.start_time_unix_nano = int((base) * 1e9)
    sp.end_time_unix_nano = int((base + 0.1) * 1e9)
    aa = sp.attributes.add()
    aa.key = "session.id"
    aa.value.string_value = "s-nosvc"
    _post(c, req.SerializeToString())
    _drain(ls)
    store = ls.get_store()
    rows = store._fetch(
        "SELECT agent_type FROM spans WHERE session_id='s-nosvc'", [])
    assert rows and rows[0][0] == "custom", rows


def test_openclaw_service_name_preserved(app):
    """The default fixture service.name 'openclaw' must keep agent_type
    'openclaw' so existing OpenClaw OTLP flows are unchanged."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    _post(c, _build_pb([{"span_id_hex": _hx(0x72), "start_ts": base,
                         "str_attrs": {"session.id": "s-oc"}}]))
    _drain(ls)
    store = ls.get_store()
    rows = store._fetch(
        "SELECT agent_type FROM spans WHERE session_id='s-oc'", [])
    assert rows and rows[0][0] == "openclaw", rows


def test_explicit_agent_type_wins_over_service_name(app):
    """An explicit agent.type span attr (clawmetry-pro adapters set it) wins
    over the service.name derivation."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 30
    _post(c, _build_pb([{"span_id_hex": _hx(0x73), "start_ts": base,
                         "str_attrs": {"session.id": "s-at",
                                       "agent.type": "claude_code"}}],
                       service_name="my-app"))
    _drain(ls)
    store = ls.get_store()
    rows = store._fetch(
        "SELECT agent_type FROM spans WHERE session_id='s-at'", [])
    assert rows and rows[0][0] == "claude_code", rows


# ── gen_ai.* live tiles ─────────────────────────────────────────────────────


def test_genai_usage_lights_live_tiles(app, clear_metrics):
    """gen_ai.usage.* span attrs + a GenAI operation must light the in-memory
    tokens + runs tiles (not just persist to the spans table)."""
    a, ls = app
    _d = clear_metrics
    c = a.test_client()
    base = time.time() - 5
    _post(c, _build_pb([{
        "span_id_hex": _hx(0x80), "start_ts": base, "name": "anthropic.chat",
        "str_attrs": {"session.id": "s-tile",
                      "gen_ai.operation.name": "chat",
                      "gen_ai.request.model": "claude-3-5-haiku-20241022"},
        "int_attrs": {"gen_ai.usage.input_tokens": 120,
                      "gen_ai.usage.output_tokens": 34},
    }]))
    with _d._metrics_lock:
        toks = list(_d.metrics_store["tokens"])
        runs = list(_d.metrics_store["runs"])
    assert any(t.get("input") == 120 and t.get("output") == 34 for t in toks), toks
    assert len(runs) >= 1, "a GenAI chat span must count as a run"


def test_genai_cost_usd_lights_cost_tile(app, clear_metrics):
    """gen_ai.usage.cost_usd on a span must light the live cost tile."""
    a, ls = app
    _d = clear_metrics
    c = a.test_client()
    base = time.time() - 5
    # cost_usd is a float; the proto builder above only does str/int attrs, so
    # add the double attr directly.
    req = _build_req([{"span_id_hex": _hx(0x81), "start_ts": base,
                       "name": "openai.chat",
                       "str_attrs": {"session.id": "s-costtile"}}])
    sp = req.resource_spans[0].scope_spans[0].spans[0]
    da = sp.attributes.add()
    da.key = "gen_ai.usage.cost_usd"
    da.value.double_value = 0.0123
    _post(c, req.SerializeToString())
    with _d._metrics_lock:
        costs = list(_d.metrics_store["cost"])
    assert any(abs(x.get("usd", 0) - 0.0123) < 1e-9 for x in costs), costs


# ── gen_ai.client.token.usage metric ────────────────────────────────────────


@pytest.mark.skipif(_ms_pb2 is None, reason="metrics proto unavailable")
def test_genai_token_usage_metric_ingested(app, clear_metrics):
    """OTel GenAI metric semconv: gen_ai.client.token.usage split by
    gen_ai.token.type (input|output) must route into the tokens tile."""
    a, ls = app
    _d = clear_metrics
    c = a.test_client()

    req = _ms_pb2.ExportMetricsServiceRequest()
    rm = req.resource_metrics.add()
    ra = rm.resource.attributes.add()
    ra.key = "service.name"
    ra.value.string_value = "my-app"
    sm = rm.scope_metrics.add()

    def _add_token_metric(ttype, val):
        m = sm.metrics.add()
        m.name = "gen_ai.client.token.usage"
        dp = m.sum.data_points.add()
        dp.as_int = val
        at = dp.attributes.add()
        at.key = "gen_ai.token.type"
        at.value.string_value = ttype
        mt = dp.attributes.add()
        mt.key = "gen_ai.request.model"
        mt.value.string_value = "gpt-4o-mini"

    _add_token_metric("input", 200)
    _add_token_metric("output", 50)

    r = c.post("/v1/metrics", data=req.SerializeToString(),
               content_type="application/x-protobuf")
    assert r.status_code == 200, r.get_data(as_text=True)[:200]
    with _d._metrics_lock:
        toks = list(_d.metrics_store["tokens"])
    assert any(t.get("input") == 200 for t in toks), toks
    assert any(t.get("output") == 50 for t in toks), toks


# ── end-to-end: a real traceloop-sdk openai.chat shape ──────────────────────


def test_openllmetry_openai_chat_shape_end_to_end(app):
    """A realistic OTLP/JSON trace matching what traceloop-sdk emits for an
    openai.chat span: resource service.name, gen_ai.system, llm.usage.* aliases,
    indexed prompts, gen_ai.conversation.id. Assert end to end that the span is
    persisted with model, tokens, DERIVED cost, the conversation id as
    session_id, and the service.name-derived agent_type."""
    a, ls = app
    c = a.test_client()
    base = time.time() - 20
    req = _ts_pb2.ExportTraceServiceRequest()
    rs = req.resource_spans.add()
    for k, v in (("service.name", "rag-chatbot"),
                 ("telemetry.sdk.name", "opentelemetry")):
        ra = rs.resource.attributes.add()
        ra.key = k
        ra.value.string_value = v
    ss = rs.scope_spans.add()
    ss.scope.name = "opentelemetry.instrumentation.openai"
    sp = ss.spans.add()
    sp.trace_id = bytes.fromhex("aaaabbbbccccddddeeeeffff00001111")
    sp.span_id = bytes.fromhex(_hx(0x90))
    sp.name = "openai.chat"
    sp.kind = _trace_pb2.Span.SPAN_KIND_CLIENT
    sp.start_time_unix_nano = int(base * 1e9)
    sp.end_time_unix_nano = int((base + 1.2) * 1e9)
    sp.status.code = _trace_pb2.Status.STATUS_CODE_OK

    def _sattr(k, v):
        a_ = sp.attributes.add()
        a_.key = k
        a_.value.string_value = v

    def _iattr(k, v):
        a_ = sp.attributes.add()
        a_.key = k
        a_.value.int_value = v

    _sattr("gen_ai.system", "openai")
    _sattr("gen_ai.request.model", "gpt-4o")
    _sattr("gen_ai.response.model", "gpt-4o-2024-08-06")
    _sattr("gen_ai.operation.name", "chat")
    _sattr("gen_ai.conversation.id", "conv-xyz-789")
    _sattr("gen_ai.prompt.0.role", "user")
    _sattr("gen_ai.prompt.0.content", "Summarize the quarterly report.")
    _sattr("gen_ai.completion.0.role", "assistant")
    _sattr("gen_ai.completion.0.content", "Revenue grew 12% QoQ.")
    # traceloop also ships the llm.usage.* aliases the mapper understands.
    _iattr("llm.usage.prompt_tokens", 850)
    _iattr("llm.usage.completion_tokens", 120)

    body = _json_format.MessageToJson(req)
    r = c.post("/v1/traces", data=body, content_type="application/json")
    assert r.status_code == 200, r.get_data(as_text=True)[:200]
    _drain(ls)

    store = ls.get_store()
    rows = store._fetch(
        "SELECT model, tokens_input, tokens_output, cost_usd, agent_type, "
        "session_id, input, output FROM spans WHERE span_id=?", [_hx(0x90)])
    assert rows, "openllmetry openai.chat span was not persisted"
    model, ti, to, cost, atype, sid, raw_in, raw_out = rows[0]
    assert model == "gpt-4o"
    assert ti == 850 and to == 120
    assert cost is not None and cost > 0, (
        f"cost must be DERIVED from tokens × gpt-4o pricing; got {cost!r}")
    assert sid == "conv-xyz-789", "gen_ai.conversation.id must map to session_id"
    assert atype == "rag_chatbot", f"service.name slug agent_type; got {atype!r}"
    inp = raw_in.decode() if isinstance(raw_in, (bytes, bytearray)) else raw_in
    out = raw_out.decode() if isinstance(raw_out, (bytes, bytearray)) else raw_out
    assert "Summarize the quarterly report." in inp
    assert "Revenue grew 12% QoQ." in out

    # session-attach: the span is queryable scoped to its conversation id.
    sp_body = _spans(c, "?session_id=conv-xyz-789&limit=10")
    assert sp_body["count"] == 1
    assert sp_body["spans"][0]["span_id"] == _hx(0x90)


class _RecordingProxy:
    """Stand-in for the dashboard-process _ProxyStore: records every method
    call (args + kwargs) and no-ops, mirroring how the real proxy forwards to
    the daemon. Crucially it lets us assert the OTLP receiver passes the span
    by KEYWORD (the real proxy drops positional args)."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def _f(*a, **k):
            self.calls.append((name, a, k))
            return None
        return _f


@pytest.mark.skipif(_ts_pb2 is None, reason="opentelemetry-proto not installed")
def test_otlp_span_write_forwards_through_daemon_proxy(monkeypatch):
    """Regression (caught live 2026-06-08): when the daemon owns the DuckDB
    writer, the dashboard's get_store() returns a _ProxyStore that ONLY
    forwards **kwargs (positional args are dropped). The OTLP /v1/traces
    receiver therefore MUST call put_span(span=...) by keyword, and put_span
    MUST be in routes.local_query._DAEMON_METHODS, or every OTLP span silently
    no-ops and a bring-your-own-agent (OpenLLMetry) app never persists or shows
    up in the runtime switcher / Agent Inventory. The other tests in this file
    force single-process (`_daemon_registered` -> False), which is exactly why
    they missed this; here we force the proxy path."""
    import importlib
    import clawmetry.local_store as ls
    importlib.reload(ls)
    rec = _RecordingProxy()
    monkeypatch.setattr(ls, "get_store", lambda *a, **k: rec)

    import dashboard as _d
    pb = _build_pb(
        [{
            "span_id_hex": "1111111111111111",
            "name": "openai.chat",
            "start_ts": time.time(),
            "str_attrs": {"gen_ai.system": "openai", "gen_ai.request.model": "gpt-4o"},
            "int_attrs": {
                "gen_ai.usage.input_tokens": 1200,
                "gen_ai.usage.output_tokens": 350,
            },
        }],
        service_name="my-langchain-app",
    )
    _d._process_otlp_traces(pb)

    put_calls = [c for c in rec.calls if c[0] == "put_span"]
    assert put_calls, "put_span was never called by the OTLP receiver"
    _name, args, kwargs = put_calls[0]
    # The real proxy drops positional args; the span MUST ride as a keyword.
    assert not args, f"positional put_span args are dropped by the proxy: {args!r}"
    assert "span" in kwargs, "put_span must be called as put_span(span=...)"
    row = kwargs["span"]
    # service.name -> per-app agent_type (the bring-your-own-agent identity).
    assert row.get("agent_type") == "my_langchain_app", row.get("agent_type")

    # And the daemon must accept the write, or the proxy 400s -> silent drop.
    import routes.local_query as lq
    assert "put_span" in lq._DAEMON_METHODS
