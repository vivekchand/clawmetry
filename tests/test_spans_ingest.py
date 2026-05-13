"""Tests for OTel span ingest + DuckDB write-through (issue #1007).

Phase 1 of the tracing epic (#1006). Covers:

  * Schema: ``spans`` table exists, schema_version bumped exactly once.
  * Direct ingest: ``local_store.put_span`` / ``ingest_span`` round-trip
    through DuckDB and back via ``query_spans``.
  * Idempotency: re-ingesting the same ``span_id`` does not create a
    duplicate row (OTLP exporter retry-on-5xx safety).
  * OTLP write-through: a protobuf POST to ``/v1/traces`` lands the span
    in the spans table via ``_process_otlp_traces`` → ``_otel_to_row`` →
    ``local_store.put_span``.
  * Parent-child hierarchy: ``parent_span_id`` is preserved on round-trip
    so the trace-tree UI (issue #1008) can reconstruct the hierarchy.

The OTLP test is gated on ``opentelemetry-proto`` being installed — same
gate the receiver itself uses. CI installs it via the ``[otel]`` extra.
"""

from __future__ import annotations

import importlib
import json
import uuid

import pytest


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh isolated DuckDB store per test."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls._reset_singleton_for_tests()
    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass
    ls._reset_singleton_for_tests()


def _span(**overrides):
    """Build a minimal valid span dict (matches ingest_span() required keys)."""
    base = {
        "span_id":        uuid.uuid4().hex,
        "trace_id":       uuid.uuid4().hex,
        "parent_span_id": None,
        "name":           "llm.call",
        "kind":           "CLIENT",
        "start_ts":       1_715_000_000.0,
        "end_ts":         1_715_000_001.25,
        "status":         "OK",
        "service_name":   "openclaw",
        "agent_id":       "main",
        "agent_type":     "openclaw",
        "session_id":     "sess-1",
        "model":          "claude-opus-4-7",
        "token_count":    42,
        "tokens_input":   30,
        "tokens_output":  12,
        "cost_usd":       0.001,
        "attributes":     {"gen_ai.system": "anthropic"},
        "events":         [],
        "links":          [],
    }
    base.update(overrides)
    return base


# ── schema / migration ──────────────────────────────────────────────────────


def test_schema_version_bumped_to_6(store):
    """SCHEMA_VERSION must be exactly 6 — issue #1007 bumps 5 → 6
    (on top of v5 = bootstrap_archive + cron_runs from #1158 / #1160).

    Guards against a concurrent migration silently re-bumping us past 6
    without updating callers / cloud relay that pin schema-aware reads."""
    import clawmetry.local_store as ls
    assert ls.SCHEMA_VERSION == 6
    # And exactly one row stamped — re-running _migrate is idempotent.
    rows = store._fetch(
        "SELECT version FROM schema_version ORDER BY version", []
    )
    versions = [r[0] for r in rows]
    assert 6 in versions
    # Re-invoke migrate; the version 6 row must NOT double-up.
    store._migrate()
    rows2 = store._fetch(
        "SELECT version, COUNT(*) FROM schema_version GROUP BY version", []
    )
    counts = {v: c for v, c in rows2}
    assert counts.get(6, 0) == 1, f"schema_version row for v6 duplicated: {counts}"


def test_spans_table_exists(store):
    """The spans table + indexes are created by the v6 DDL."""
    tables = {r[0] for r in store._fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'",
        [],
    )}
    assert "spans" in tables
    cols = {r[1] for r in store._fetch("PRAGMA table_info('spans')", [])}
    # Required spec'd columns from the issue body.
    for required in (
        "trace_id", "span_id", "parent_span_id", "name", "kind",
        "start_ts", "end_ts", "duration_ms", "status",
        "attributes", "events", "links",
        "service_name", "agent_id", "session_id", "ts",
    ):
        assert required in cols, f"spans table missing column: {required}"


# ── direct ingest + query round-trip ────────────────────────────────────────


def test_put_span_round_trip(store):
    """put_span → query_spans round-trip preserves all fields."""
    s = _span(span_id="span-aaaa", trace_id="trace-xxxx")
    store.put_span(s)
    rows = store.query_spans(trace_id="trace-xxxx")
    assert len(rows) == 1
    row = rows[0]
    assert row["span_id"] == "span-aaaa"
    assert row["trace_id"] == "trace-xxxx"
    assert row["name"] == "llm.call"
    assert row["kind"] == "CLIENT"
    assert row["status"] == "OK"
    assert row["session_id"] == "sess-1"
    assert row["model"] == "claude-opus-4-7"
    assert row["token_count"] == 42
    assert row["tokens_input"] == 30
    assert row["tokens_output"] == 12
    assert row["cost_usd"] == pytest.approx(0.001)
    # Time + duration auto-derived from start/end.
    assert row["start_ts"] == pytest.approx(1_715_000_000.0)
    assert row["end_ts"] == pytest.approx(1_715_000_001.25)
    assert row["duration_ms"] == pytest.approx(1250.0, abs=0.1)
    # Attributes round-trip as dict.
    assert row["attributes"] == {"gen_ai.system": "anthropic"}


def test_ingest_span_validates_required_keys(store):
    """Missing PK / time-key fields raise ValueError, not silently drop."""
    with pytest.raises(ValueError, match="span_id"):
        store.put_span(_span(span_id=""))
    with pytest.raises(ValueError, match="trace_id"):
        store.put_span(_span(trace_id=""))
    with pytest.raises(ValueError, match="name"):
        store.put_span(_span(name=""))
    with pytest.raises(ValueError, match="start_ts"):
        s = _span()
        s["start_ts"] = None
        store.put_span(s)


def test_idempotent_reingest(store):
    """Re-ingesting the same span_id does not duplicate (OTLP retry safety)."""
    s = _span(span_id="span-dup", trace_id="trace-dup")
    store.put_span(s)
    store.put_span(s)
    store.put_span(s)
    rows = store.query_spans(trace_id="trace-dup")
    assert len(rows) == 1, "OTLP retry duplicated the span row"
    # Re-ingest with mutated fields → row is replaced (not appended).
    s2 = dict(s)
    s2["status"] = "ERROR"
    s2["token_count"] = 999
    store.put_span(s2)
    rows = store.query_spans(trace_id="trace-dup")
    assert len(rows) == 1
    assert rows[0]["status"] == "ERROR"
    assert rows[0]["token_count"] == 999


def test_parent_child_hierarchy_round_trip(store):
    """parent_span_id preserved → trace-tree UI can reconstruct hierarchy."""
    root = _span(span_id="root", trace_id="trace-h", parent_span_id=None,
                 name="session", start_ts=1.0, end_ts=10.0)
    child = _span(span_id="child-1", trace_id="trace-h",
                  parent_span_id="root", name="llm.call",
                  start_ts=2.0, end_ts=4.0)
    grandchild = _span(span_id="grand-1", trace_id="trace-h",
                       parent_span_id="child-1", name="tool.call",
                       start_ts=3.0, end_ts=3.5)
    for sp in (root, child, grandchild):
        store.put_span(sp)
    rows = store.query_spans(trace_id="trace-h", limit=10)
    by_id = {r["span_id"]: r for r in rows}
    assert by_id["root"]["parent_span_id"] in (None, "")
    assert by_id["child-1"]["parent_span_id"] == "root"
    assert by_id["grand-1"]["parent_span_id"] == "child-1"
    # query_spans with parent_span_id filter walks one level of the tree.
    children = store.query_spans(parent_span_id="root")
    assert len(children) == 1
    assert children[0]["span_id"] == "child-1"


def test_blob_columns_round_trip_json(store):
    """input/output/attributes/events/links coerced to BLOB on write, decoded
    back to Python dict/list on read."""
    sp = _span(
        span_id="span-blobs",
        trace_id="trace-blobs",
        input={"prompt": "Hello"},
        output={"text": "Hi there"},
        attributes={"gen_ai.system": "openai", "custom.flag": True},
        events=[{"name": "tok", "time_unix_nano": 1, "attributes": {}}],
        links=[{"trace_id": "other", "span_id": "x", "attributes": {}}],
    )
    store.put_span(sp)
    row = store.query_spans(span_id="span-blobs")[0]
    assert row["input"] == {"prompt": "Hello"}
    assert row["output"] == {"text": "Hi there"}
    assert row["attributes"]["custom.flag"] is True
    assert isinstance(row["events"], list) and row["events"][0]["name"] == "tok"
    assert isinstance(row["links"], list) and row["links"][0]["span_id"] == "x"


# ── OTLP /v1/traces write-through ───────────────────────────────────────────

try:
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2  # noqa: F401
    from opentelemetry.proto.trace.v1 import trace_pb2
    from opentelemetry.proto.common.v1 import common_pb2
    from opentelemetry.proto.resource.v1 import resource_pb2
    _HAS_OTEL_PROTO = True
except ImportError:
    _HAS_OTEL_PROTO = False


def _build_export_request(spans_spec):
    """Build an OTLP ExportTraceServiceRequest from a list of dicts.

    Each spec: {trace_id, span_id, parent_span_id, name, start_ns, end_ns,
                attributes: {k: v}}.
    """
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2 as ts_pb2
    req = ts_pb2.ExportTraceServiceRequest()
    rs = req.resource_spans.add()
    # Resource attr: service.name
    res_attr = rs.resource.attributes.add()
    res_attr.key = "service.name"
    res_attr.value.string_value = "test-service"
    scope_spans = rs.scope_spans.add()
    for spec in spans_spec:
        sp = scope_spans.spans.add()
        sp.trace_id = bytes.fromhex(spec["trace_id"])
        sp.span_id = bytes.fromhex(spec["span_id"])
        if spec.get("parent_span_id"):
            sp.parent_span_id = bytes.fromhex(spec["parent_span_id"])
        sp.name = spec["name"]
        sp.kind = spec.get("kind", trace_pb2.Span.SPAN_KIND_CLIENT)
        sp.start_time_unix_nano = spec["start_ns"]
        sp.end_time_unix_nano = spec["end_ns"]
        sp.status.code = spec.get("status_code", trace_pb2.Status.STATUS_CODE_OK)
        for k, v in (spec.get("attributes") or {}).items():
            a = sp.attributes.add()
            a.key = k
            if isinstance(v, bool):
                a.value.bool_value = v
            elif isinstance(v, int):
                a.value.int_value = v
            elif isinstance(v, float):
                a.value.double_value = v
            else:
                a.value.string_value = str(v)
    return req.SerializeToString()


@pytest.mark.skipif(not _HAS_OTEL_PROTO,
                    reason="opentelemetry-proto not installed (pip install clawmetry[otel])")
def test_otlp_traces_write_through_persists_span(store, monkeypatch):
    """A protobuf POST to /v1/traces lands the span in DuckDB.

    Bypasses the Flask routing layer and calls the dashboard function
    directly — the route handler is a thin pass-through (see
    ``routes/meta.py::otlp_traces``)."""
    import dashboard as _d
    # Force the dashboard's local-store-import path to resolve to the same
    # process-wide singleton our fixture set up.
    import clawmetry.local_store as ls
    monkeypatch.setattr(_d, "_HAS_OTEL_PROTO", True, raising=False)
    monkeypatch.setattr(_d, "trace_service_pb2", trace_service_pb2, raising=False)

    trace_id_hex = "0123456789abcdef0123456789abcdef"
    span_id_hex = "fedcba9876543210"
    pb = _build_export_request([{
        "trace_id": trace_id_hex,
        "span_id":  span_id_hex,
        "parent_span_id": None,
        "name":     "anthropic.messages.create",
        "start_ns": 1_715_000_000_000_000_000,
        "end_ns":   1_715_000_001_500_000_000,
        "attributes": {
            "gen_ai.request.model": "claude-opus-4-7",
            "gen_ai.usage.input_tokens": 100,
            "gen_ai.usage.output_tokens": 50,
            "gen_ai.usage.cost_usd": 0.0042,
            "session.id": "sess-otlp-1",
        },
    }])

    _d._process_otlp_traces(pb)

    rows = ls.get_store().query_spans(trace_id=trace_id_hex)
    assert len(rows) == 1, f"OTLP write-through did not persist span (rows={rows})"
    row = rows[0]
    assert row["span_id"] == span_id_hex
    assert row["trace_id"] == trace_id_hex
    assert row["name"] == "anthropic.messages.create"
    # OTel attribute → typed column projection.
    assert row["model"] == "claude-opus-4-7"
    assert row["tokens_input"] == 100
    assert row["tokens_output"] == 50
    assert row["token_count"] == 150  # auto-summed when total missing
    assert row["cost_usd"] == pytest.approx(0.0042)
    assert row["session_id"] == "sess-otlp-1"
    # Service name + kind from resource / span.
    assert row["service_name"] == "test-service"
    assert row["kind"] == "CLIENT"
    assert row["status"] == "OK"
    # Time-unit conversion: nano → unix-seconds.
    assert row["start_ts"] == pytest.approx(1_715_000_000.0)
    assert row["end_ts"] == pytest.approx(1_715_000_001.5)
    assert row["duration_ms"] == pytest.approx(1500.0, abs=1.0)


@pytest.mark.skipif(not _HAS_OTEL_PROTO,
                    reason="opentelemetry-proto not installed (pip install clawmetry[otel])")
def test_otlp_retry_does_not_duplicate(store, monkeypatch):
    """OTel exporters retry on 5xx — same span_id must NOT duplicate in DuckDB."""
    import dashboard as _d
    import clawmetry.local_store as ls
    monkeypatch.setattr(_d, "_HAS_OTEL_PROTO", True, raising=False)
    monkeypatch.setattr(_d, "trace_service_pb2", trace_service_pb2, raising=False)

    trace_id_hex = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    span_id_hex = "bbbbbbbbbbbbbbbb"
    pb = _build_export_request([{
        "trace_id": trace_id_hex,
        "span_id":  span_id_hex,
        "name":     "llm.call",
        "start_ns": 1_715_000_000_000_000_000,
        "end_ns":   1_715_000_000_500_000_000,
        "attributes": {"gen_ai.request.model": "claude-opus-4-7"},
    }])
    for _ in range(3):
        _d._process_otlp_traces(pb)
    rows = ls.get_store().query_spans(trace_id=trace_id_hex)
    assert len(rows) == 1
