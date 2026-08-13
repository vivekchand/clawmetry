"""The Tracing tab reads the spans table — issue #4782.

``routes/tracing.py`` reconstructed traces from the EVENTS table only. An app
that speaks OTLP produces spans and no events, so it showed up in the runtime
switcher, the Agent Inventory, and the cost tiles while having nothing to click
into in the one view built to show traces. Its module docstring claimed OTel
spans were "merged in when present"; they were never read.

These tests pin the union:
  * a span-only trace is listed and opens to a real waterfall
  * event-derived traces are unchanged (no regression, no reordering)
  * a session with BOTH resolves to exactly one entry, the richer event one
  * ``?runtime=`` scopes server-side and does not leak across runtimes
  * a span whose parent was never delivered is promoted to a root instead of
    vanishing from the tree
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


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
    import routes.tracing as tr
    importlib.reload(tr)

    a = Flask(__name__)
    a.register_blueprint(tr.bp_tracing)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── seeding ─────────────────────────────────────────────────────────────────


def _put_span(store, **kw):
    base = time.time() - 300
    start = kw.pop("start_ts", base)
    span = {
        "span_id": kw.pop("span_id"),
        "trace_id": kw.pop("trace_id"),
        "parent_span_id": kw.pop("parent_span_id", None),
        "agent_type": kw.pop("agent_type", "my_app"),
        "agent_id": "main",
        "session_id": kw.pop("session_id", None),
        "service_name": kw.pop("service_name", "my-app"),
        "name": kw.pop("name", "openai.chat"),
        "kind": "CLIENT",
        "status": kw.pop("status", "OK"),
        "status_code": kw.pop("status", "OK"),
        "start_ts": start,
        "end_ts": start + kw.pop("duration_s", 0.5),
        "duration_ms": kw.pop("duration_ms", 500.0),
        "model": kw.pop("model", "gpt-4o-mini"),
        "tool_name": kw.pop("tool_name", None),
        "cost_usd": kw.pop("cost_usd", 0.002),
        "tokens_input": kw.pop("tokens_input", 100),
        "tokens_output": kw.pop("tokens_output", 50),
        "attributes": kw.pop("attributes", {}),
    }
    span.update(kw)
    store.put_span(span=span)


def _seed_event(store, sid, ts):
    store.ingest({
        "id": f"{sid}-{int(ts * 1000)}",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "tool_call",
        "ts": _iso(ts),
        "data": {"tool_name": "Bash"},
        "cost_usd": 0.01,
        "token_count": 100,
        "model": "claude-opus-5",
    })


def _drain(ls):
    store = ls.get_store()
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        if store.health().get("ring_depth", 0) == 0:
            return
        time.sleep(0.02)


# ── the headline case ───────────────────────────────────────────────────────


def test_span_only_trace_is_listed(app):
    """A bring-your-own-agent app with zero events must appear in the list."""
    a, ls = app
    store = ls.get_store()
    _put_span(store, span_id="a1" * 8, trace_id="ab" * 16, name="agent.run")
    _drain(ls)

    body = a.test_client().get("/api/traces?limit=50").get_json()
    assert body["available"] is True
    traces = [t for t in body["traces"] if t["trace_id"] == "ab" * 16]
    assert len(traces) == 1, f"span-only trace missing from the list: {body}"
    t = traces[0]
    assert t["source"] == "spans"
    assert t["span_count"] == 1
    assert t["model"] == "gpt-4o-mini"
    assert t["total_tokens"] == 150
    assert t["total_cost_usd"] == pytest.approx(0.002)
    # Reads as a name, never a bare checksum.
    assert "my-app" in t["title"] and "agent.run" in t["title"]


def test_span_only_trace_opens_to_a_waterfall(app):
    """Listing it is half the job: the detail view has to render too."""
    a, ls = app
    store = ls.get_store()
    tid = "cd" * 16
    _put_span(store, span_id="b1" * 8, trace_id=tid, name="agent.run",
              model=None, cost_usd=None, tokens_input=None, tokens_output=None)
    _put_span(store, span_id="b2" * 8, trace_id=tid, parent_span_id="b1" * 8,
              name="openai.chat", start_ts=time.time() - 299)
    _put_span(store, span_id="b3" * 8, trace_id=tid, parent_span_id="b1" * 8,
              name="tool.search", tool_name="search", model=None)
    _drain(ls)

    body = a.test_client().get(f"/api/trace/{tid}").get_json()
    assert body["available"] is True
    assert body["source"] == "spans"
    assert body["root_span_ids"] == ["b1" * 8]
    by_id = {s["span_id"]: s for s in body["spans"]}
    assert len(by_id) == 3
    assert by_id["b2" * 8]["parent_span_id"] == "b1" * 8
    # Kind drives the waterfall colour, and must come from semantics rather
    # than OTel's INTERNAL/CLIENT (which says nothing about what ran).
    assert by_id["b2" * 8]["kind"] == "llm"
    assert by_id["b3" * 8]["kind"] == "tool"
    assert body["summary"]["span_count"] == 3
    assert body["summary"]["duration_ms"] > 0


def test_orphan_span_is_promoted_to_root(app):
    """A parent lost to sampling or a dropped batch must not swallow its
    child: an orphan becomes a root, never disappears from the tree."""
    a, ls = app
    store = ls.get_store()
    tid = "ef" * 16
    _put_span(store, span_id="c2" * 8, trace_id=tid,
              parent_span_id="ffffffffffffffff", name="openai.chat")
    _drain(ls)

    body = a.test_client().get(f"/api/trace/{tid}").get_json()
    assert body["root_span_ids"] == ["c2" * 8]
    assert body["spans"][0]["parent_span_id"] is None


# ── no regression for the event path ────────────────────────────────────────


def test_event_traces_still_listed_and_labelled(app):
    a, ls = app
    _seed_event(ls.get_store(), "sess-events-1", time.time() - 100)
    _drain(ls)

    body = a.test_client().get("/api/traces?limit=50").get_json()
    ev = [t for t in body["traces"] if t["trace_id"] == "sess-events-1"]
    assert len(ev) == 1
    assert ev[0]["source"] == "events"


def test_session_with_both_sources_appears_once(app):
    """The dedupe contract. Two rows for one run is the bug this guards."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-both-1"
    _seed_event(store, sid, time.time() - 100)
    _put_span(store, span_id="d1" * 8, trace_id="11" * 16, session_id=sid)
    _drain(ls)

    body = a.test_client().get("/api/traces?limit=50").get_json()
    rows = [t for t in body["traces"]
            if t["trace_id"] in (sid, "11" * 16)]
    assert len(rows) == 1, f"one run produced two trace rows: {rows}"
    assert rows[0]["source"] == "events", "event reconstruction is the richer one"


def test_event_trace_detail_unchanged(app):
    a, ls = app
    _seed_event(ls.get_store(), "sess-detail-1", time.time() - 100)
    _drain(ls)

    body = a.test_client().get("/api/trace/sess-detail-1").get_json()
    assert body["available"] is True
    assert body["source"] == "events"
    assert body["spans"]


def test_unknown_id_returns_no_trace(app):
    """An id that matches neither source must not fabricate a trace.

    Which of the two honest answers comes back depends on whether the read
    returned "nothing here" (``[]`` -> 404) or "could not read" (``None`` ->
    ``available: false``); both are pre-existing behaviour and both are fine.
    What matters is that no spans are invented.
    """
    a, _ls = app
    r = a.test_client().get("/api/trace/does-not-exist")
    assert r.status_code in (200, 404)
    body = r.get_json()
    assert not body.get("spans")
    if r.status_code == 200:
        assert body.get("available") is False


# ── runtime scoping (FLYWHEEL 1c) ───────────────────────────────────────────


def test_runtime_filter_scopes_span_traces(app):
    a, ls = app
    store = ls.get_store()
    _put_span(store, span_id="e1" * 8, trace_id="22" * 16,
              agent_type="app_a", service_name="app-a")
    _put_span(store, span_id="e2" * 8, trace_id="33" * 16,
              agent_type="app_b", service_name="app-b")
    _drain(ls)

    body = a.test_client().get("/api/traces?runtime=app_a").get_json()
    ids = {t["trace_id"] for t in body["traces"]}
    assert "22" * 16 in ids
    assert "33" * 16 not in ids, "another app's traces leaked under a runtime filter"


def test_otlp_runtime_does_not_leak_event_traces(app):
    """Selecting a foreign OTLP app must not show the node's OpenClaw
    sessions. The app has no session prefix, so a prefix filter is what keeps
    the two apart."""
    a, ls = app
    store = ls.get_store()
    _seed_event(store, "sess-openclaw-1", time.time() - 100)
    _put_span(store, span_id="f1" * 8, trace_id="44" * 16, agent_type="app_a")
    _drain(ls)

    body = a.test_client().get("/api/traces?runtime=app_a").get_json()
    ids = {t["trace_id"] for t in body["traces"]}
    assert ids == {"44" * 16}, f"unexpected traces under runtime=app_a: {ids}"


def test_native_runtime_filter_scopes_event_traces(app):
    a, ls = app
    store = ls.get_store()
    _seed_event(store, "claude_code:sess-1", time.time() - 100)
    _seed_event(store, "sess-openclaw-2", time.time() - 100)
    _drain(ls)

    c = a.test_client()
    cc = {t["trace_id"] for t in c.get("/api/traces?runtime=claude_code").get_json()["traces"]}
    assert cc == {"claude_code:sess-1"}
    oc = {t["trace_id"] for t in c.get("/api/traces?runtime=openclaw").get_json()["traces"]}
    assert oc == {"sess-openclaw-2"}


def test_snapshot_slice_carries_span_traces(app):
    """Cloud parity (FLYWHEEL 0a.1). The hosted dashboard has no DuckDB, so a
    trace only reaches a trial user through the encrypted snapshot. Without
    this, a BYO-agent app appears in the cloud runtime switcher with an empty
    trace list, which is the blank-card failure the gate exists to prevent.
    """
    a, ls = app
    store = ls.get_store()
    _seed_event(store, "sess-snap-1", time.time() - 100)
    tid = "66" * 16
    _put_span(store, span_id="aa" * 8, trace_id=tid, name="agent.run")
    _put_span(store, span_id="ab" * 8, trace_id=tid, parent_span_id="aa" * 8,
              name="openai.chat")
    _drain(ls)

    import clawmetry.sync as sync
    slice_ = sync._build_traces(limit_traces=5, span_cap=100)
    ids = {t["trace_id"] for t in slice_["list"]}
    assert tid in ids, f"span trace missing from the snapshot slice: {ids}"
    assert "sess-snap-1" in ids, "event traces must still ship"
    detail = slice_["detail"][tid]
    assert len(detail["spans"]) == 2
    assert detail["root_span_ids"] == ["aa" * 8]
    assert detail["summary"]["source"] == "spans"


def test_runtime_all_is_the_unfiltered_union(app):
    a, ls = app
    store = ls.get_store()
    _seed_event(store, "sess-all-1", time.time() - 100)
    _put_span(store, span_id="a9" * 8, trace_id="55" * 16, agent_type="app_a")
    _drain(ls)

    body = a.test_client().get("/api/traces?runtime=all").get_json()
    ids = {t["trace_id"] for t in body["traces"]}
    assert {"sess-all-1", "55" * 16} <= ids
