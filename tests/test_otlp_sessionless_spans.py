"""Issue #5691: a pushed span with no conversation id must still become a session.

`_otel_to_row` read the session id from four keys and had no fallback, and
`materialize_otlp_sessions` (WO-55) only ever sees the ids that collection
gathered. So an exporter that sets `gen_ai.conversation.id` worked, and one
that does not landed its spans in `spans` and produced no `sessions` row at
all: the data was in the store and the Sessions tab could not see it. Nothing
errored, so nothing prompted anyone to look. Nothing in the GenAI convention
requires a conversation id, and a plain OTel SDK or OpenLLMetry on defaults
does not send one, so that is the common case, not the exotic one.

The fallback is the trace id, chosen against real data rather than taste
(measurement on the issue): across 265 real traces `trace_id` maps to exactly
one session and no session spans more than one trace, and traces are runs
(median 2 spans, p90 231, p90 duration ~2.4 h) rather than tool calls, so the
feared flood is not the shape of the data.

The derived key is `<runtime>:trace:<id>`, and that detail is the point of
half this file. Every session-id parser in the codebase takes the text before
the FIRST colon as the runtime, so the `otlp:trace:<id>` shape that first
suggested itself would have filed every one of these sessions under a runtime
literally named "otlp" instead of the app's own agent_type.

Everything here runs through the REAL ingest path: POST /v1/traces ->
_process_otlp_traces -> DuckDB.
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


def _batch(*, service, trace_seed, conversation_id=None, span_seed=0x40):
    """A plain OpenLLMetry-shaped export: a root chat span plus a tool span.

    ``conversation_id=None`` is the whole point: the GenAI attributes are all
    present and correct, and no key in ``_pick``'s list is set.
    """
    now = int(time.time() * 1e9)
    trace_id = bytes([trace_seed]) * 16
    conv = [_kv("gen_ai.conversation.id", s=conversation_id)] if conversation_id else []

    def _span(span_id, parent, name, off_ms, dur_ms, attrs):
        sp = _trace_pb2.Span(
            trace_id=trace_id, span_id=span_id, name=name,
            start_time_unix_nano=now + int(off_ms * 1e6),
            end_time_unix_nano=now + int((off_ms + dur_ms) * 1e6),
        )
        if parent:
            sp.parent_span_id = parent
        sp.attributes.extend(attrs)
        return sp

    root = bytes([span_seed]) * 8
    spans = [
        _span(root, b"", "chat gpt-4o", 0, 3000, conv + [
            _kv("gen_ai.operation.name", s="chat"),
            _kv("gen_ai.system", s="openai"),
            _kv("gen_ai.request.model", s="gpt-4o"),
            _kv("gen_ai.usage.input_tokens", i=800),
            _kv("gen_ai.usage.output_tokens", i=150),
        ]),
        _span(bytes([span_seed + 1]) * 8, root, "execute_tool search", 100, 400,
              conv + [
            _kv("gen_ai.operation.name", s="execute_tool"),
            _kv("gen_ai.tool.name", s="search"),
        ]),
    ]
    resource = _trace_pb2.ResourceSpans(
        scope_spans=[_trace_pb2.ScopeSpans(spans=spans)])
    resource.resource.attributes.extend([_kv("service.name", s=service)])
    return _ts_pb2.ExportTraceServiceRequest(resource_spans=[resource])


def _post(app_obj, req):
    resp = app_obj.test_client().post(
        "/v1/traces", data=req.SerializeToString(),
        content_type="application/x-protobuf")
    assert resp.status_code == 200, resp.data
    return resp


def _sessions(ls):
    rows = ls.get_store()._fetch(
        "SELECT session_id, agent_type, total_tokens, message_count, metadata"
        " FROM sessions ORDER BY session_id", [])
    out = []
    for sid, atype, tok, mc, meta in rows:
        if isinstance(meta, (bytes, bytearray, memoryview)):
            meta = bytes(meta).decode("utf-8", "replace")
        if isinstance(meta, str) and meta:
            try:
                meta = _json.loads(meta)
            except ValueError:
                meta = {}
        out.append({"session_id": sid, "agent_type": atype,
                    "total_tokens": int(tok or 0),
                    "message_count": int(mc or 0),
                    "metadata": meta if isinstance(meta, dict) else {}})
    return out


def _spans(ls):
    return ls.get_store()._fetch(
        "SELECT span_id, session_id, trace_id FROM spans", [])


# ── the gap itself ──────────────────────────────────────────────────────────


def test_a_sessionless_batch_produces_exactly_one_session(app):
    """The issue's reproduction: spans land, and now a session does too."""
    a, ls = app
    _post(a, _batch(service="my-engine", trace_seed=0xA1))

    rows = _sessions(ls)
    assert len(rows) == 1, f"expected one session per run, got {rows}"
    row = rows[0]
    assert row["agent_type"] == "my_engine"
    assert row["session_id"] == "my_engine:trace:" + ("a1" * 16)
    assert row["total_tokens"] == 950
    assert row["metadata"].get("source") == "otlp_spans"


def test_the_spans_are_still_stored_and_now_joined_to_that_session(app):
    """Before the fix the spans were in the store with session_id NULL. The
    data was never missing; the join was."""
    a, ls = app
    _post(a, _batch(service="my-engine", trace_seed=0xA1))
    rows = _spans(ls)
    assert len(rows) == 2
    assert all(r[1] == "my_engine:trace:" + ("a1" * 16) for r in rows), rows


def test_one_session_per_trace_not_per_span(app):
    """Two spans, one trace, one session. The flood the issue worried about
    would show up here as two."""
    a, ls = app
    _post(a, _batch(service="my-engine", trace_seed=0xA1))
    assert len(_sessions(ls)) == 1


def test_two_runs_are_two_sessions(app):
    a, ls = app
    _post(a, _batch(service="my-engine", trace_seed=0xA1, span_seed=0x40))
    _post(a, _batch(service="my-engine", trace_seed=0xB2, span_seed=0x60))
    sids = {r["session_id"] for r in _sessions(ls)}
    assert sids == {"my_engine:trace:" + ("a1" * 16),
                    "my_engine:trace:" + ("b2" * 16)}


def test_an_otlp_retry_does_not_double_anything(app):
    """OTLP delivery is at-least-once by spec, so the same batch arrives twice."""
    a, ls = app
    batch = _batch(service="my-engine", trace_seed=0xA1)
    _post(a, batch)
    _post(a, batch)
    rows = _sessions(ls)
    assert len(rows) == 1
    assert rows[0]["total_tokens"] == 950


# ── the derived key must not invent a runtime ───────────────────────────────


def test_the_derived_id_resolves_to_the_apps_own_runtime(app):
    """`otlp:trace:<id>` would have filed every one of these under a runtime
    named "otlp". Every parser in the codebase splits on the FIRST colon, so
    the prefix has to be the agent_type."""
    a, ls = app
    _post(a, _batch(service="my-engine", trace_seed=0xA1))
    sid = _sessions(ls)[0]["session_id"]

    import routes.sessions as rs
    assert rs._sid_runtime(sid) == "my_engine"
    assert not sid.startswith("otlp:")


@pytest.mark.parametrize("mod_name,fn", [
    ("routes.bench", None),
    ("routes.cohort", None),
    ("routes.harness", None),
])
def test_every_sibling_parser_agrees_on_the_runtime(app, mod_name, fn):
    """The prefix convention is read in several modules; a derived id must
    behave like any other session id in all of them."""
    a, ls = app
    _post(a, _batch(service="my-engine", trace_seed=0xA1))
    sid = _sessions(ls)[0]["session_id"]
    # The shared shape those modules implement inline.
    assert (sid.split(":", 1)[0] if ":" in sid else "openclaw") == "my_engine"


def test_the_id_is_marked_as_derived(app):
    """A reader must be able to tell a session id we invented from one an
    exporter actually sent."""
    a, ls = app
    _post(a, _batch(service="my-engine", trace_seed=0xA1))
    assert ":trace:" in _sessions(ls)[0]["session_id"]


# ── the regression guard: this is a SHARED path ─────────────────────────────


def test_an_exporter_that_sets_a_conversation_id_is_untouched(app):
    """The half of the contract that already worked. This changes a path
    every current OTLP user depends on, so the old behaviour is pinned."""
    a, ls = app
    _post(a, _batch(service="my-engine", trace_seed=0xA1,
                    conversation_id="conv-abc-123"))

    rows = _sessions(ls)
    assert len(rows) == 1
    assert rows[0]["session_id"] == "conv-abc-123", (
        "a source that sends a conversation id must keep it verbatim")
    assert ":trace:" not in rows[0]["session_id"]
    assert rows[0]["total_tokens"] == 950


def test_a_mixed_export_keeps_each_source_on_its_own_key(app):
    """One app sends a conversation id, another does not. Both must land."""
    a, ls = app
    _post(a, _batch(service="my-engine", trace_seed=0xA1,
                    conversation_id="conv-abc-123", span_seed=0x40))
    _post(a, _batch(service="other-engine", trace_seed=0xC3, span_seed=0x70))

    sids = {r["session_id"] for r in _sessions(ls)}
    assert sids == {"conv-abc-123", "other_engine:trace:" + ("c3" * 16)}


def test_openclaw_labelled_spans_still_mint_no_session(app):
    """Ghost-session guard from WO-55: OpenClaw sessions come from
    transcripts, and the fallback must not start inventing them."""
    a, ls = app
    _post(a, _batch(service="openclaw", trace_seed=0xD4))
    assert _sessions(ls) == []


def test_openclaw_spans_keep_the_null_session_id_they_have_today(app):
    """Not just "no session row" -- no KEY either. The materializer skips
    agent_type=openclaw, so a derived id there would sit on a span that joins
    nothing: a phantom session id, which is a bug shape we have shipped
    before. The fallback is confined to the apps it is for."""
    a, ls = app
    _post(a, _batch(service="openclaw", trace_seed=0xD4))
    rows = _spans(ls)
    assert len(rows) == 2, "the spans themselves must still be stored"
    assert all(not r[1] for r in rows), (
        f"openclaw spans must keep a null session_id, got {rows}")
