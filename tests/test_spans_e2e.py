"""E2E test for /api/spans — MOAT issue #1364.

Confirms the read-side surface for OTel spans we already persist, driven by
the REAL ingest path end to end (no synthetic ``put_span`` shortcut):

  build OTLP ExportTraceServiceRequest  →
  POST protobuf to /v1/traces (the real production receiver)  →
  GET /api/spans                                               →
  assert the spans surface, ordered by start_time DESC.

This is a true e2e: the same path production traffic takes —
``POST /v1/traces`` → ``dashboard._process_otlp_traces`` → ``_otel_to_row``
→ ``LocalStore.put_span`` → ``GET /api/spans`` → read. Earlier this file
called ``store.put_span()`` directly, which skipped the OTLP receiver + the
attribute-projection layer — an ingest regression there would not have been
caught. Now both ingest and read run over HTTP for real.

Gated on ``opentelemetry-proto`` (``pip install clawmetry[otel]``); the OTLP
receiver returns 501 without it, so a real POST is only meaningful when it's
installed. Skips loudly otherwise rather than silently degrading.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask

try:
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2 as _ts_pb2
    from opentelemetry.proto.trace.v1 import trace_pb2 as _trace_pb2
    _HAS_OTEL_PROTO = True
except Exception:  # pragma: no cover - exercised only on minimal installs
    _HAS_OTEL_PROTO = False

pytestmark = pytest.mark.skipif(
    not _HAS_OTEL_PROTO,
    reason="opentelemetry-proto not installed (pip install clawmetry[otel]); "
           "the /v1/traces receiver returns 501, so a real OTLP POST is moot",
)


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Fresh DuckDB store + Flask app with the OTLP receiver AND the read
    surface mounted, so one test client can POST a real trace and read it back.

    Single-process mode (the dashboard owns the writer lock, no sync daemon)
    so ``_ls_call``'s daemon-proxy path falls through to the direct-open
    fallback — exactly what we want to exercise here.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Force a hermetic direct store: if a real ClawMetry daemon happens to be
    # running on the test host, get_store() would otherwise return a proxy to
    # the daemon's DuckDB (the writer-lock guard) and our tmp_path store would
    # never see the spans. CI has no daemon; this makes local runs match CI.
    monkeypatch.setattr(ls, "_daemon_registered", lambda *a, **k: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import routes.local_query as lq
    importlib.reload(lq)
    # Read path: force the local-query dispatch to the direct-open store too.
    # _read_discovery() returning None makes _proxy_dispatch raise, so reads
    # fall through to the in-process DuckDB (same hermetic store the OTLP
    # ingest writes to). Mirrors test_e2e_real_openclaw_pipeline.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    import routes.sessions as ses
    importlib.reload(ses)
    import routes.meta as meta
    importlib.reload(meta)

    a = Flask(__name__)
    a.register_blueprint(ses.bp_sessions)
    a.register_blueprint(meta.bp_otel)  # /v1/traces — the real receiver
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── Real OTLP ingest helpers ────────────────────────────────────────────────
#
# Span IDs are 8-byte / trace IDs 16-byte per OTLP, so we use hex ids (not
# arbitrary strings). ``/api/spans`` returns the hex span_id, which the
# ordering/filter assertions key off.


def _hex_span(n: int) -> str:
    return f"{n:016x}"


def _build_traces_pb(specs):
    """Build a serialized OTLP ExportTraceServiceRequest from span specs.

    Each spec: {span_id_hex, start_ts (unix sec), name, session_id,
                duration_s (default 0.5)}. Attributes use the GenAI semconv
    keys ``_otel_to_row`` projects (session.id, gen_ai.request.model,
    gen_ai.usage.*) so the typed columns the UI reads get populated.
    """
    req = _ts_pb2.ExportTraceServiceRequest()
    rs = req.resource_spans.add()
    res_attr = rs.resource.attributes.add()
    res_attr.key = "service.name"
    res_attr.value.string_value = "openclaw"
    scope_spans = rs.scope_spans.add()
    for spec in specs:
        sp = scope_spans.spans.add()
        sp.trace_id = bytes.fromhex("0123456789abcdef0123456789abcdef")
        sp.span_id = bytes.fromhex(spec["span_id_hex"])
        sp.name = spec["name"]
        sp.kind = _trace_pb2.Span.SPAN_KIND_CLIENT
        start_ns = int(spec["start_ts"] * 1e9)
        sp.start_time_unix_nano = start_ns
        sp.end_time_unix_nano = start_ns + int(spec.get("duration_s", 0.5) * 1e9)
        sp.status.code = _trace_pb2.Status.STATUS_CODE_OK
        for k, v in (
            ("session.id", spec.get("session_id", "sess-spans-e2e")),
            ("gen_ai.request.model", "claude-3-5-haiku-20241022"),
            ("agent.type", "openclaw"),
            ("agent.id", "main"),
        ):
            a = sp.attributes.add()
            a.key = k
            a.value.string_value = v
        for k, iv in (
            ("gen_ai.usage.input_tokens", 10),
            ("gen_ai.usage.output_tokens", 5),
        ):
            a = sp.attributes.add()
            a.key = k
            a.value.int_value = iv
    return req.SerializeToString()


def _post_traces(client, ls, specs):
    """POST a real OTLP protobuf to /v1/traces, assert 2xx, then wait for the
    async flusher to drain the ring so the spans are queryable from DuckDB
    (put_span enqueues; the read path reads flushed rows)."""
    r = client.post(
        "/v1/traces",
        data=_build_traces_pb(specs),
        content_type="application/x-protobuf",
    )
    assert r.status_code == 200, (
        f"/v1/traces rejected the OTLP payload: {r.status_code} "
        f"{r.get_data(as_text=True)[:300]}"
    )
    store = ls.get_store()
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        if store.health().get("ring_depth", 0) == 0:
            return
        time.sleep(0.02)


def test_api_spans_returns_ingested_spans_ordered_desc(app):
    """Real OTLP POST → DuckDB → /api/spans round-trip.

    Asserts:
      * All 3 ingested spans surface in the response.
      * Order is start_time DESC (newest first) — what the UI table shows.
      * Each row carries the contract fields the UI renders
        (name, duration_ms, session_id, kind, start_time).
    """
    a, _ls = app
    c = a.test_client()
    base = time.time() - 60
    _post_traces(c, _ls, [
        {"span_id_hex": _hex_span(1), "start_ts": base + 1.0, "name": "llm.call"},
        {"span_id_hex": _hex_span(2), "start_ts": base + 2.0, "name": "tool.call"},
        {"span_id_hex": _hex_span(3), "start_ts": base + 3.0, "name": "agent.step"},
    ])

    r = c.get("/api/spans?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["count"] == 3
    spans = body["spans"]
    # Newest first.
    assert [s["span_id"] for s in spans] == [_hex_span(3), _hex_span(2), _hex_span(1)]
    # Contract fields the UI renders.
    for s in spans:
        assert s["name"]
        assert s["session_id"] == "sess-spans-e2e"
        assert s["kind"] == "CLIENT"
        assert s["start_time"] is not None
        assert s["duration_ms"] is not None
        assert s["duration_ms"] == pytest.approx(500.0, abs=1.0)


def test_api_spans_session_filter(app):
    """`session_id` query param scopes the result set."""
    a, _ls = app
    c = a.test_client()
    base = time.time() - 60
    _post_traces(c, _ls, [
        {"span_id_hex": _hex_span(0xA), "start_ts": base + 1.0, "name": "a", "session_id": "sess-A"},
        {"span_id_hex": _hex_span(0xB), "start_ts": base + 2.0, "name": "b", "session_id": "sess-B"},
        {"span_id_hex": _hex_span(0xC), "start_ts": base + 3.0, "name": "c", "session_id": "sess-A"},
    ])

    r = c.get("/api/spans?session_id=sess-A")
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 2
    assert {s["span_id"] for s in body["spans"]} == {_hex_span(0xA), _hex_span(0xC)}


def test_api_spans_empty_store(app):
    """Empty store → empty list, never an error."""
    a, _ls = app
    c = a.test_client()
    r = c.get("/api/spans")
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 0
    assert body["spans"] == []


def test_api_spans_limit_clamped(app):
    """`limit` is clamped 1-500 to prevent runaway scans."""
    a, _ls = app
    c = a.test_client()
    base = time.time() - 60
    _post_traces(c, _ls, [
        {"span_id_hex": _hex_span(0x10 + i), "start_ts": base + i, "name": f"s{i}"}
        for i in range(5)
    ])

    # Out-of-range values should fall back to safe defaults rather than 400.
    r = c.get("/api/spans?limit=99999")
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 5
    r = c.get("/api/spans?limit=garbage")
    assert r.status_code == 200
    assert r.get_json()["count"] == 5


# ── Retention cap (issue #1374) ─────────────────────────────────────────────
#
# OSS / Cloud-Free callers are clamped to the last 24 h of ``start_ts``;
# Cloud-Pro users (gated by ``dashboard._is_pro_user``) bypass the cap. The
# response always carries a ``capped_at_24h`` boolean so the Brain-tab UI
# can render the upgrade CTA when the cap kicks in.


def _post_old_and_recent_spans(client, ls):
    """One ancient span (8 days old) + one fresh span (5 min ago), via OTLP."""
    now = time.time()
    _post_traces(client, ls, [
        {"span_id_hex": _hex_span(0x0100), "start_ts": now - 8 * 86400, "name": "ancient"},
        {"span_id_hex": _hex_span(0x0200), "start_ts": now - 300, "name": "fresh"},
    ])


def test_api_spans_oss_capped_to_24h(app, monkeypatch):
    """Non-Pro users see only spans newer than now-24h; flag set."""
    a, _ls = app
    c = a.test_client()
    _post_old_and_recent_spans(c, _ls)
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)

    r = c.get("/api/spans?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body["capped_at_24h"] is True
    sids = {s["span_id"] for s in body["spans"]}
    # The 8-day-old span must be excluded; only the fresh one shows.
    assert sids == {_hex_span(0x0200)}


def test_api_spans_pro_bypasses_cap(app, monkeypatch):
    """Pro users get the full history, unflagged."""
    a, _ls = app
    c = a.test_client()
    _post_old_and_recent_spans(c, _ls)
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    r = c.get("/api/spans?limit=10")
    body = r.get_json()
    assert body["capped_at_24h"] is False
    sids = {s["span_id"] for s in body["spans"]}
    assert sids == {_hex_span(0x0100), _hex_span(0x0200)}
