"""Regressions for two "healthy install looks broken" bugs.

**Ghost sessions.** A ``session_id`` is minted for every distinct id the
events table has seen — including ids scraped off gateway log lines, which
land as ``{event_type: "log", data: {kind: "gateway_log"}}`` and carry zero
renderable turns. Those showed up in the Sessions tab as bare-UUID rows
(sorted to the TOP, because a log line is newer than the last real turn) and
opened a detail card reading "Messages 0" with no model, no duration and no
turns. On a live install 22 of the 50 listed rows were ghosts.

**Local-only heartbeat.** ``send_heartbeat`` returns early when cloud sync is
off, which also skipped the DuckDB write-through it owns — so the
``heartbeats`` table froze at whatever row predated the switch to local-only
and ``/api/heartbeat-status`` reported an ever-growing gap. The dashboard
painted a permanent red "Agent heartbeat SILENT for Nh" banner on a node
whose daemon had been running the whole time.
"""

from __future__ import annotations

import importlib
import uuid

import pytest


# ── ghost sessions ────────────────────────────────────────────────────────

def _session_row(sid, message_count, *, updated="2026-08-16T08:17:21+00:00"):
    return {
        "session_id": sid,
        "agent_id": "main",
        "started_at": updated,
        "updated_at": updated,
        "event_count": max(message_count, 1),
        "message_count": message_count,
        "cost_usd": 0,
        "token_count": 0,
    }


def test_log_only_sessions_are_dropped_from_the_list(monkeypatch):
    """A session whose only event is a gateway log line has no renderable
    turn, so it must not appear in /api/transcripts."""
    import routes.sessions as rs

    rows = [
        _session_row("1e19a4ce-4025-4375-8422-9f4951a6ec54", 0),  # ghost
        _session_row("claude_code:real-one", 142),
        _session_row("b527b4e6-2491-4afc-9d5b-f334258796a9", 0),  # ghost
    ]
    monkeypatch.setattr(rs, "_ls_call", lambda *a, **k: rows)
    monkeypatch.setattr(rs, "_first_user_title", lambda _p: "")

    out = rs._try_local_store_transcripts()
    ids = [t["id"] for t in out["transcripts"]]
    assert ids == ["claude_code:real-one"]


def test_list_still_fills_to_the_display_limit(monkeypatch):
    """Ghosts are dropped AFTER the fetch, so a head full of them must not
    shorten the list — that's what the over-fetch is for."""
    import routes.sessions as rs

    ghosts = [_session_row(f"ghost-{i}", 0) for i in range(120)]
    real = [_session_row(f"claude_code:real-{i}", 5) for i in range(80)]
    monkeypatch.setattr(rs, "_ls_call", lambda *a, **k: ghosts + real)
    monkeypatch.setattr(rs, "_first_user_title", lambda _p: "")

    out = rs._try_local_store_transcripts()
    assert len(out["transcripts"]) == rs._TRANSCRIPT_LIST_LIMIT
    assert all(t["messages"] > 0 for t in out["transcripts"])


def test_scan_limit_is_requested_not_the_display_limit(monkeypatch):
    import routes.sessions as rs

    seen = {}

    def _fake(method, **kwargs):
        seen[method] = kwargs
        return [_session_row("claude_code:real", 3)]

    monkeypatch.setattr(rs, "_ls_call", _fake)
    monkeypatch.setattr(rs, "_first_user_title", lambda _p: "")
    rs._try_local_store_transcripts()
    assert seen["query_sessions"]["limit"] == rs._TRANSCRIPT_LIST_SCAN_LIMIT
    assert rs._TRANSCRIPT_LIST_SCAN_LIMIT > rs._TRANSCRIPT_LIST_LIMIT


def test_detail_defers_when_rows_exist_but_none_are_renderable():
    """The bug: rows existed (one ``log`` row), so the ``if not rows`` guard
    didn't fire, and the zero-filled shell was served as a 200 — which also
    blocked the JSONL fallback. It must return None instead."""
    import routes.sessions as rs

    log_row = {
        "event_type": "log",
        "ts": "2026-08-16T08:17:21+00:00",
        "session_id": "1e19a4ce-4025-4375-8422-9f4951a6ec54",
        "data": {"kind": "gateway_log", "level": "WARN",
                 "message": "model fallback decision"},
    }
    assert rs._try_local_store_transcript("ghost", _events=[log_row]) is None


def test_detail_still_serves_a_real_transcript():
    """Guard against the fix over-reaching: one renderable turn is enough."""
    import routes.sessions as rs

    rows = [
        {"event_type": "log", "ts": "2026-08-16T08:17:20+00:00",
         "data": {"kind": "gateway_log", "message": "noise"}},
        {"event_type": "user", "ts": "2026-08-16T08:17:21+00:00",
         "data": {"role": "user", "content": "hello"}},
    ]
    out = rs._try_local_store_transcript("real", _events=rows)
    assert out is not None
    assert out["messageCount"] == 1
    assert out["messages"][0]["content"] == "hello"


def test_ghost_session_404s_end_to_end(monkeypatch, tmp_path):
    """The route must 404 rather than serve an empty card, so the UI can show
    its "no messages" empty state instead of "Session undefined"."""
    import dashboard as _d
    import routes.sessions as rs

    import routes.local_query as lq

    log_row = {
        "event_type": "log", "ts": "2026-08-16T08:17:21+00:00",
        "data": {"kind": "gateway_log", "message": "model fallback decision"},
    }
    # Feed the real DuckDB detail path the exact shape the live install had:
    # one non-renderable log row. Nothing is stubbed downstream, so this
    # exercises the fix rather than asserting on a stub.
    monkeypatch.setattr(rs, "is_local_store_read_enabled", lambda: True)
    monkeypatch.setattr(
        lq, "local_store_via_daemon",
        lambda method, **kw: [log_row] if method == "query_events" else None)
    # Point the JSONL fallback at an empty dir so "not found" is the only
    # possible outcome for an id with no file.
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(tmp_path), raising=False)

    client = _d.app.test_client()
    resp = client.get("/api/transcript/ghost")
    assert resp.status_code == 404


# ── local-only heartbeat ──────────────────────────────────────────────────

@pytest.fixture
def local_store_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.02")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Without this, a dev box with a running daemon hands back a _ProxyStore
    # pointed at the REAL ~/.clawmetry DB — the assertions below would then
    # pass on production rows and prove nothing.
    ls.mark_writer_owner()
    yield ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_local_only_mode_still_records_a_heartbeat_row(local_store_env):
    """Cloud off must not mean "no liveness history" — that's exactly the
    case the local write-through was written for."""
    ls = local_store_env
    from clawmetry import sync

    node = "agent+test-" + uuid.uuid4().hex[:6]
    assert not ls.get_store().query_heartbeats(limit=1), "fixture DB not empty"

    sync.record_local_heartbeat({"node_id": node})

    rows = ls.get_store().query_heartbeats(limit=5)
    assert len(rows) == 1, "local-only heartbeat wrote no row"
    assert rows[0]["node_id"] == node
    assert rows[0].get("version")


def test_record_local_heartbeat_never_raises(monkeypatch):
    """Best-effort contract: a broken store must not take down the sync loop."""
    from clawmetry import sync
    import clawmetry.local_store as ls

    monkeypatch.setattr(
        ls, "get_store", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("locked")))
    sync.record_local_heartbeat({"node_id": "agent+test"})  # must not raise


def test_no_egress_branch_records_heartbeat():
    """Pin the wiring: the no-cloud-egress branch of the sync loop calls the
    recorder. Without this the fix is a function nobody invokes.

    Anchored on the branch's CODE, not its comment prose, so a reworded
    comment can't silently un-pin it (the comment has already been rewritten
    once, when #4329 widened local-only to "no egress").
    """
    import inspect
    from clawmetry import sync

    src = inspect.getsource(sync)
    start = src.find("if not _hb_egress(config):")
    assert start > 0, "no-egress branch moved — re-point this test"
    end = src.find("elif send_heartbeat(config):", start)
    assert end > start, "branch shape changed — re-point this test"
    assert "record_local_heartbeat(config)" in src[start:end]
