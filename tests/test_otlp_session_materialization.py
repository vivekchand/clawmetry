"""WO-55: sessions materialized from OTLP spans (bring-your-own-agent).

A fleet that only ever sends OTLP traces (AWS Bedrock AgentCore, an
OpenLLMetry app, ...) fills the ``spans`` table and the Tracing tab but used
to create no ``sessions`` row — so the Sessions tab and the runtime switcher
stayed empty for exactly the app the person just wired up. The /v1/traces
receiver now recomputes the touched sessions from their spans and upserts
sessions rows (``LocalStore.materialize_otlp_sessions``) once per export
batch.

Pinned here, through the REAL ingest path (``POST /v1/traces`` →
``_process_otlp_traces`` → DuckDB):

  * a GenAI-semconv span batch with ``session.id`` produces a sessions row
    with the right agent_type, token/cost rollup, message_count, title, and
    ``metadata.source='otlp_spans'`` + ``deployment_environment``;
  * an OTLP retry (same batch re-POSTed) does NOT double any total —
    delivery is at-least-once by spec;
  * OpenClaw-labelled spans never mint a session row (ghost-session guard:
    OpenClaw sessions come from transcripts);
  * a pre-existing session row owned by a richer ingest path is left alone.

Gated on ``opentelemetry-proto`` (the receiver 501s without it).
"""

from __future__ import annotations

import importlib
import json as _json
import time

import pytest
from flask import Flask

try:
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2 as _ts_pb2
    from opentelemetry.proto.common.v1 import common_pb2 as _common_pb2
    from opentelemetry.proto.trace.v1 import trace_pb2 as _trace_pb2
    _HAS_OTEL_PROTO = True
except Exception:  # pragma: no cover
    _HAS_OTEL_PROTO = False

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
    import routes.meta as meta
    importlib.reload(meta)

    a = Flask(__name__)
    a.register_blueprint(meta.bp_otel)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _kv(key, s=None, i=None):
    v = _common_pb2.AnyValue()
    if s is not None:
        v.string_value = s
    elif i is not None:
        v.int_value = i
    return _common_pb2.KeyValue(key=key, value=v)


def _agentcore_batch(session_id, *, service="payments-agent-prod",
                     environment="prod", trace_seed=1):
    """An ADOT/Strands-shaped export: invoke_agent root + two chat spans +
    one execute_tool span, GenAI semconv attrs, session id on every span."""
    now = int(time.time() * 1e9)
    trace_id = bytes([trace_seed]) * 16

    def _span(span_id, parent, name, off_ms, dur_ms, attrs):
        s = _trace_pb2.Span(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            start_time_unix_nano=now + int(off_ms * 1e6),
            end_time_unix_nano=now + int((off_ms + dur_ms) * 1e6),
        )
        if parent:
            s.parent_span_id = parent
        s.attributes.extend(attrs)
        return s

    chat_attrs = [
        _kv("gen_ai.operation.name", s="chat"),
        _kv("gen_ai.system", s="aws.bedrock"),
        _kv("gen_ai.request.model", s="anthropic.claude-sonnet-5-20250929-v1:0"),
        _kv("gen_ai.conversation.id", s=session_id),
    ]
    spans = [
        _span(b"\x0a" * 8, b"", "invoke_agent payments-agent", 0, 5000, [
            _kv("gen_ai.operation.name", s="invoke_agent"),
            _kv("session.id", s=session_id),
        ]),
        _span(b"\x0b" * 8, b"\x0a" * 8, "chat claude", 100, 2000, chat_attrs + [
            _kv("gen_ai.usage.input_tokens", i=1000),
            _kv("gen_ai.usage.output_tokens", i=200),
        ]),
        _span(b"\x0c" * 8, b"\x0a" * 8, "execute_tool lookup_invoice", 2200, 700, [
            _kv("gen_ai.operation.name", s="execute_tool"),
            _kv("gen_ai.tool.name", s="lookup_invoice"),
            _kv("session.id", s=session_id),
        ]),
        _span(b"\x0d" * 8, b"\x0a" * 8, "chat claude", 3000, 1500, chat_attrs + [
            _kv("gen_ai.usage.input_tokens", i=2000),
            _kv("gen_ai.usage.output_tokens", i=500),
        ]),
    ]
    resource = _trace_pb2.ResourceSpans(
        scope_spans=[_trace_pb2.ScopeSpans(spans=spans)])
    resource.resource.attributes.extend([
        _kv("service.name", s=service),
        _kv("deployment.environment", s=environment),
        _kv("host.name", s="agentcore-runtime-1"),
    ])
    return _ts_pb2.ExportTraceServiceRequest(resource_spans=[resource])


def _post(app_obj, req):
    client = app_obj.test_client()
    resp = client.post("/v1/traces", data=req.SerializeToString(),
                       content_type="application/x-protobuf")
    assert resp.status_code == 200, resp.data
    return resp


def _session_row(ls, session_id):
    store = ls.get_store()
    rows = store._fetch(
        "SELECT agent_type, title, total_tokens, cost_usd, message_count,"
        " status, started_at, last_active_at, metadata"
        " FROM sessions WHERE session_id = ?", [session_id])
    if not rows:
        return None
    (agent_type, title, total_tokens, cost_usd, message_count,
     status, started_at, last_active_at, metadata) = rows[0]
    if isinstance(metadata, (bytes, bytearray, memoryview)):
        metadata = bytes(metadata).decode("utf-8", "replace")
    if isinstance(metadata, str) and metadata:
        try:
            metadata = _json.loads(metadata)
        except ValueError:
            pass
    return {
        "agent_type": agent_type, "title": title,
        "total_tokens": int(total_tokens or 0),
        "cost_usd": float(cost_usd or 0.0),
        "message_count": int(message_count or 0), "status": status,
        "started_at": started_at, "last_active_at": last_active_at,
        "metadata": metadata if isinstance(metadata, dict) else {},
    }


def test_span_only_app_gets_session_row(app):
    a, ls = app
    sid = "agentcore-sess-mat-1"
    _post(a, _agentcore_batch(sid))

    row = _session_row(ls, sid)
    assert row is not None, "no sessions row materialized from spans"
    assert row["agent_type"] == "payments_agent_prod"
    assert row["total_tokens"] == 3700  # 1000+200 + 2000+500
    assert row["cost_usd"] > 0, "cost should be derived from tokens x model"
    assert row["message_count"] == 2  # the two chat spans
    assert row["title"] == "invoke_agent payments-agent"
    assert row["started_at"] and row["last_active_at"]
    assert row["metadata"].get("source") == "otlp_spans"
    assert row["metadata"].get("deployment_environment") == "prod"
    assert row["metadata"].get("service_name") == "payments-agent-prod"


def test_otlp_retry_does_not_double_totals(app):
    a, ls = app
    sid = "agentcore-sess-mat-retry"
    req = _agentcore_batch(sid)
    _post(a, req)
    first = _session_row(ls, sid)
    assert first is not None and first["total_tokens"] == 3700

    # At-least-once delivery: the exporter re-sends the same batch.
    _post(a, req)
    second = _session_row(ls, sid)
    assert second["total_tokens"] == 3700, "retry doubled the token rollup"
    assert abs(second["cost_usd"] - first["cost_usd"]) < 1e-9


def test_openclaw_spans_never_mint_a_session(app):
    a, ls = app
    sid = "openclaw-sess-from-spans"
    # service.name 'openclaw' maps to agent_type 'openclaw' — those sessions
    # come from transcripts via the daemon, not from spans.
    _post(a, _agentcore_batch(sid, service="openclaw", environment=""))
    assert _session_row(ls, sid) is None


def test_rollup_buckets_materialized_session_under_its_app(app):
    """The prefix-only runtime CASE used to dump prefix-less OTLP sessions into
    the 'openclaw' bucket, so a bring-your-own-agent app's tokens and cost
    showed under OpenClaw the moment its sessions materialized."""
    a, ls = app
    sid = "agentcore-sess-bucket"
    _post(a, _agentcore_batch(sid, service="billing-agent-tst", environment="tst"))
    br = (ls.get_store().query_model_rollup() or {}).get("by_runtime") or {}
    assert "billing_agent_tst" in br, f"buckets: {sorted(br)}"
    assert br["billing_agent_tst"]["sessions"] == 1
    assert br["billing_agent_tst"]["tokens"] == 3700
    oc = br.get("openclaw") or {}
    assert int(oc.get("tokens") or 0) == 0, (
        "OTLP session tokens leaked into the openclaw bucket")
    assert float(oc.get("cost_usd") or 0.0) == 0.0


def test_runtime_summary_entry_keeps_otlp_markers(app):
    """With a sessions row present, the summary already holds a key for the
    app, and the spans merge used to SKIP it — losing otlp=True and
    display_name, so the frontend scoped the app by a session-id prefix it
    does not have. The merge must enrich, and never double the numbers."""
    a, ls = app
    sid = "agentcore-sess-summary"
    _post(a, _agentcore_batch(sid, service="billing-agent-tst", environment="tst"))
    from clawmetry import sync as _sync
    summ = _sync._build_runtime_summary() or {}
    entry = summ.get("billing_agent_tst")
    assert entry, f"no summary entry for the app; keys={sorted(summ)}"
    assert entry.get("otlp") is True
    assert "(OTel)" in (entry.get("display_name") or "")
    assert entry["sessions"] == 1
    assert entry["tokens"] == 3700, "sessions pass + spans merge double-counted"


def test_richer_ingest_owned_session_is_not_clobbered(app):
    a, ls = app
    sid = "agentcore-sess-owned"
    store = ls.get_store()
    store.ingest_session({
        "session_id": sid,
        "agent_type": "payments_agent_prod",
        "title": "real transcript title",
        "total_tokens": 999,
        "metadata": {"origin": "daemon"},
    })
    _post(a, _agentcore_batch(sid))
    row = _session_row(ls, sid)
    assert row["title"] == "real transcript title"
    assert row["total_tokens"] == 999, (
        "span materialization overwrote a session owned by a richer ingest")
