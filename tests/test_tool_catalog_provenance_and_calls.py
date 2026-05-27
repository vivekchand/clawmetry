"""Regression tests for the Tool Catalog provenance + drill-down fixes.

Two bugs this guards (both surfaced on a live Claude Code node,
``agent+Macbook-Pro-2-local``):

1. **Cross-runtime provenance.** ``builtin`` was decided *only* from the
   OpenClaw sandbox ``tool_policy`` allow set. A Claude Code / Codex node ships
   no such policy, so its core tools (Bash/Read/Edit/Write/Task*…) fell through
   to ``plugin`` and the whole provenance breakdown was wrong. The fix unions a
   ``RUNTIME_BUILTINS`` set into the builtin universe.

2. **Cloud drill-down always empty.** The cloud ``cm-cloud-tool-catalog``
   interceptor reads ``snapshot.toolCatalog.calls[name]`` for the per-call
   drill-down, but the daemon's ``_build_tool_catalog_slice`` only ever shipped
   ``{tools, groups}`` — so the expand showed "No individual calls captured"
   for every tool on cloud. The fix ships a bounded per-tool ``calls`` map.

Events are ingested in the real Claude Code tool_call/tool_result shape so a
synthetic-but-wrong fixture can't pass while real data flunks.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


def _iso(s: float) -> str:
    return datetime.fromtimestamp(s, tz=timezone.utc).isoformat()


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def catalog_app(tmp_path, monkeypatch):
    """Flask app + tmp DuckDB with the daemon proxy short-circuited so the
    route's ``_ls_call`` falls through to the in-process store."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Own the writer in-process so get_store() opens the tmp DuckDB directly
    # instead of proxying to a live daemon (CI has none; a dev box does).
    ls.mark_writer_owner()
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)
    import routes.tool_catalog as tc
    importlib.reload(tc)
    a = Flask(__name__)
    a.register_blueprint(tc.bp_tool_catalog)
    yield a, ls, tc
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _call(store, *, eid, sid, ts, name, tuid):
    """A Claude Code tool-invocation event."""
    store.ingest({
        "id": eid, "node_id": "agent+test", "agent_id": "main",
        "session_id": sid, "event_type": "tool_call", "ts": _iso(ts),
        "data": {"tool_name": name, "tool_calls": [{"id": tuid, "name": name}]},
        "cost_usd": None, "token_count": None, "model": None,
    })


def _result(store, *, eid, sid, ts, tuid, error=False):
    """The closing tool_result for ``tuid`` (Claude Code role='tool' shape)."""
    store.ingest({
        "id": eid, "node_id": "agent+test", "agent_id": "main",
        "session_id": sid, "event_type": "tool_result", "ts": _iso(ts),
        "data": {"role": "tool", "extra": {"toolUseId": tuid, "isError": error}},
        "cost_usd": None, "token_count": None, "model": None,
    })


def _seed_claude_code_tools(store):
    """One call+result for each of: two builtins, an MCP tool, a real plugin,
    plus a second Bash call that errored (so error_rate > 0)."""
    now = time.time()
    rows = [
        ("Bash", "t1", False),
        ("Read", "t2", False),
        ("TaskCreate", "t3", False),
        ("mcp__chrome-devtools__click", "t4", False),
        ("some_vendor_tool", "t5", False),
        ("Bash", "t6", True),   # second Bash call, errored
    ]
    for i, (name, tuid, err) in enumerate(rows):
        ts = now - 600 + i * 10
        _call(store, eid=f"c-{i}", sid=f"sess-{i % 2}", ts=ts, name=name, tuid=tuid)
        _result(store, eid=f"r-{i}", sid=f"sess-{i % 2}", ts=ts + 0.05,
                 tuid=tuid, error=err)
    _wait_flush(store)


def test_provenance_classifies_claude_code_builtins(catalog_app):
    """Bash/Read/TaskCreate are builtin even with no OpenClaw sandbox policy."""
    a, ls, _tc = catalog_app
    _seed_claude_code_tools(ls.get_store())
    body = a.test_client().get("/api/tool-catalog").get_json() or {}
    prov = {t["name"]: t["provenance"] for t in body["tools"]}
    assert prov.get("Bash") == "builtin", prov
    assert prov.get("Read") == "builtin", prov
    assert prov.get("TaskCreate") == "builtin", prov
    assert prov.get("mcp__chrome-devtools__click") == "mcp", prov
    # A genuinely unknown name is still plugin — the fix must not over-classify.
    assert prov.get("some_vendor_tool") == "plugin", prov
    g = body["groups"]
    assert g["builtin"] >= 3 and g["mcp"] >= 1 and g["plugin"] >= 1, g


def test_mcp_provider_extracted(catalog_app):
    """``mcp__<provider>__<tool>`` → provider segment for the MCP rollup."""
    a, ls, _tc = catalog_app
    _seed_claude_code_tools(ls.get_store())
    body = a.test_client().get("/api/tool-catalog").get_json() or {}
    row = next(t for t in body["tools"] if t["name"] == "mcp__chrome-devtools__click")
    assert row["provider"] == "chrome-devtools", row


def test_drilldown_returns_individual_calls(catalog_app):
    """The live /calls endpoint returns per-call rows (status + session)."""
    a, ls, _tc = catalog_app
    _seed_claude_code_tools(ls.get_store())
    body = a.test_client().get("/api/tool-catalog/Bash/calls").get_json() or {}
    assert body["provenance"] == "builtin", body
    calls = body["calls"]
    assert len(calls) == 2, body            # two Bash invocations
    assert {c["status"] for c in calls} == {"ok", "error"}, calls
    assert all(c.get("session_id") for c in calls), calls


def test_snapshot_slice_ships_calls_map(catalog_app):
    """The cloud drill-down reads toolCatalog.calls[name] — the daemon slice
    must ship it (was the always-empty-in-cloud bug)."""
    a, ls, _tc = catalog_app
    _seed_claude_code_tools(ls.get_store())
    from clawmetry.sync import _build_tool_catalog_slice
    slice_ = _build_tool_catalog_slice()
    assert "calls" in slice_, slice_.keys()
    calls = slice_["calls"]
    # Every shipped tool row has a (non-empty) recent-calls list keyed by name.
    shipped = {t["name"] for t in slice_["tools"]}
    assert shipped, slice_
    for name in shipped:
        assert name in calls, (name, list(calls))
    bash = calls["Bash"]
    assert len(bash) == 2, bash
    sample = bash[0]
    assert set(sample) == {"ts_ms", "duration_ms", "status", "session_id"}, sample
    # Provenance is fixed in the slice too (cloud renders this verbatim).
    prov = {t["name"]: t["provenance"] for t in slice_["tools"]}
    assert prov.get("Bash") == "builtin", prov
