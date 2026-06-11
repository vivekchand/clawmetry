"""Guards for the cost cluster:
- #1571 per-runtime leak: Cost-tab "Top Sessions" must scope to the runtime.
- #1570 tail: query_sessions_table must not double-count sibling rows.
"""
import datetime as _dt
import importlib
import time

import pytest

usage = importlib.import_module("routes.usage")


# ── #1571 Top Sessions by Cost honours the runtime switcher ────────────────

def test_top_sessions_runtime_filter(monkeypatch):
    def fake_ls_call(method, **kw):
        if method == "query_sessions":
            return [
                {"session_id": "claude_code:aaa", "cost_usd": 5.0},
                {"session_id": "plain-openclaw-bbb", "cost_usd": 9.0},
                {"session_id": "qwen_code:ccc", "cost_usd": 3.0},
            ]
        if method == "query_events":
            return [{"model": "m"}]
        return []
    monkeypatch.setattr(usage, "_ls_call", fake_ls_call)

    only_cc = usage._ls_top_sessions_by_cost(limit=20, runtime="claude_code")
    assert [r["session_id"] for r in only_cc] == ["claude_code:aaa"]

    only_oc = usage._ls_top_sessions_by_cost(limit=20, runtime="openclaw")
    assert [r["session_id"] for r in only_oc] == ["plain-openclaw-bbb"]

    node_wide = usage._ls_top_sessions_by_cost(limit=20)
    assert len(node_wide) == 3


# ── #1570 tail: query_sessions_table dedupes sibling rows ──────────────────

def _ts(secs):
    now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)
    return (now - _dt.timedelta(seconds=secs)).isoformat().replace("+00:00", "Z")


def _ev(eid, et, cost, tok, secs, sid):
    return {"id": eid, "node_id": "n", "agent_type": "openclaw", "agent_id": "main",
            "session_id": sid, "event_type": et, "ts": _ts(secs),
            "token_count": tok, "cost_usd": cost, "data": {}}


def test_sessions_table_dedupes_siblings(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.get_store()
    sid = "sess-st-0001"
    try:
        s.upsert_session({"session_id": sid, "agent_type": "openclaw",
                          "total_tokens": 0, "cost_usd": 0.0})
        s.ingest(_ev("a1", "assistant", 1.0, 100, 10, sid))
        s.ingest(_ev("m1", "model.completed", 1.0, 100, 10, sid))
        s.ingest(_ev("a2", "assistant", 2.0, 200, 5, sid))
        s.ingest(_ev("m2", "model.completed", 2.0, 200, 5, sid))
        s._flush_now()
        deadline = time.monotonic() + 3.0
        n = 0
        while time.monotonic() < deadline:
            row = s._fetch("SELECT COUNT(*) FROM events", [])
            n = row[0][0] if row and row[0] else 0
            if n >= 4:
                break
            time.sleep(0.02)
        if n < 4:
            pytest.skip("no local DuckDB writer (daemon holds the lock); CI covers this")
        rows = s.query_sessions_table(limit=50)
        mine = [r for r in rows if r["session_id"] == sid]
        assert mine, rows
        assert abs(mine[0]["cost_usd"] - 3.0) < 1e-6, mine          # not 6.0
        assert mine[0]["total_tokens"] == 300, mine                 # not 600
    finally:
        try:
            s.stop(flush=True)
        except Exception:
            pass
        try:
            ls._reset_singleton_for_tests()
        except Exception:
            pass
