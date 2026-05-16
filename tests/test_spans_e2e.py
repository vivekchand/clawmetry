"""E2E test for /api/spans — MOAT issue #1364.

Confirms the read-side surface for OTel spans we already persist:

  inject 3 spans via LocalStore.ingest_span()  →
  GET /api/spans                                →
  assert all 3 returned, ordered by start_time DESC.

The ingest path under test is the same one routes/meta.py /v1/traces uses
in production: dashboard._process_otlp_traces → LocalStore.put_span (which
is an alias for ingest_span). Calling ingest_span directly here keeps the
test independent of opentelemetry-proto being installed.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Fresh DuckDB store + Flask app with the sessions blueprint mounted.

    Uses single-process mode (the dashboard owns the writer lock since no
    sync daemon is running) so _ls_call's daemon-proxy path falls through
    to the direct-open fallback — exactly what we want to exercise here.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as ses
    importlib.reload(ses)

    a = Flask(__name__)
    a.register_blueprint(ses.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _span(span_id, start_ts, *, session_id="sess-spans-e2e", name="llm.call"):
    """Minimal valid span dict (matches ingest_span's required keys)."""
    return {
        "span_id":      span_id,
        "trace_id":     "trace-e2e",
        "name":         name,
        "kind":         "CLIENT",
        "start_ts":     float(start_ts),
        "end_ts":       float(start_ts) + 0.5,
        "status":       "OK",
        "service_name": "openclaw",
        "agent_id":     "main",
        "agent_type":   "openclaw",
        "session_id":   session_id,
        "model":        "claude-opus-4-7",
        "tokens_input":  10,
        "tokens_output": 5,
        "attributes":   {"gen_ai.system": "anthropic"},
    }


def test_api_spans_returns_ingested_spans_ordered_desc(app):
    """Synthetic event → DuckDB → /api/spans round-trip.

    Asserts:
      * All 3 ingested spans surface in the response.
      * Order is start_time DESC (newest first) — what the UI table shows.
      * Each row carries the contract fields the UI renders
        (name, duration_ms, session_id, kind, start_time).
    """
    a, ls = app
    store = ls.get_store()
    # Use distinct, increasing start_ts so the DESC sort is unambiguous.
    base = time.time() - 60
    store.put_span(_span("span-e2e-1", base + 1.0, name="llm.call"))
    store.put_span(_span("span-e2e-2", base + 2.0, name="tool.call"))
    store.put_span(_span("span-e2e-3", base + 3.0, name="agent.step"))

    c = a.test_client()
    r = c.get("/api/spans?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["count"] == 3
    spans = body["spans"]
    # Newest first.
    assert [s["span_id"] for s in spans] == ["span-e2e-3", "span-e2e-2", "span-e2e-1"]
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
    a, ls = app
    store = ls.get_store()
    base = time.time() - 60
    store.put_span(_span("span-a", base + 1.0, session_id="sess-A"))
    store.put_span(_span("span-b", base + 2.0, session_id="sess-B"))
    store.put_span(_span("span-c", base + 3.0, session_id="sess-A"))

    c = a.test_client()
    r = c.get("/api/spans?session_id=sess-A")
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 2
    assert {s["span_id"] for s in body["spans"]} == {"span-a", "span-c"}


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
    a, ls = app
    store = ls.get_store()
    base = time.time() - 60
    for i in range(5):
        store.put_span(_span(f"span-l-{i}", base + i))

    c = a.test_client()
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


def _seed_old_and_recent_spans(store):
    """One ancient span (8 days old) + one fresh span (5 min ago)."""
    now = time.time()
    store.put_span(_span("span-old", now - 8 * 86400, name="ancient"))
    store.put_span(_span("span-new", now - 300, name="fresh"))


def test_api_spans_oss_capped_to_24h(app, monkeypatch):
    """Non-Pro users see only spans newer than now-24h; flag set."""
    a, ls = app
    _seed_old_and_recent_spans(ls.get_store())
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)

    r = a.test_client().get("/api/spans?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body["capped_at_24h"] is True
    sids = {s["span_id"] for s in body["spans"]}
    # The 8-day-old span must be excluded; only the fresh one shows.
    assert sids == {"span-new"}


def test_api_spans_pro_bypasses_cap(app, monkeypatch):
    """Pro users get the full history, unflagged."""
    a, ls = app
    _seed_old_and_recent_spans(ls.get_store())
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    r = a.test_client().get("/api/spans?limit=10")
    body = r.get_json()
    assert body["capped_at_24h"] is False
    sids = {s["span_id"] for s in body["spans"]}
    assert sids == {"span-old", "span-new"}
