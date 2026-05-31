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

import importlib
import time

import pytest
from flask import Flask

try:
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2 as _ts_pb2
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


def _build_pb(specs, *, n_resource_spans=1):
    """Build a serialized OTLP request. ``specs`` is a list of span dicts;
    set n_resource_spans>1 to split them across multiple resource_spans."""
    req = _ts_pb2.ExportTraceServiceRequest()
    groups = [[] for _ in range(n_resource_spans)]
    for i, spec in enumerate(specs):
        groups[i % n_resource_spans].append(spec)
    for grp in groups:
        rs = req.resource_spans.add()
        ra = rs.resource.attributes.add()
        ra.key = "service.name"
        ra.value.string_value = "openclaw"
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
    return req.SerializeToString()


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
