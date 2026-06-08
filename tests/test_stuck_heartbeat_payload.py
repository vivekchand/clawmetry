"""Stuck-agent signal → HEARTBEAT wiring (clawmetry-hardware#15).

The WiFi desk device fetches the CLOUD's device_summary (built from Postgres),
NOT the local dashboard or the legacy E2E snapshot — so the daemon's loop_signals
never reached it. The fix rides the cached stuck list on the plaintext, regularly-
sent, self-clearing HEARTBEAT.

These tests cover the OSS half of that wiring:

  * `_emit_stuck_signals` populates the module-level `_LATEST_STUCK` cache
    (items + fresh ts) when sessions are stuck, and clears it to `items=[]`
    (still fresh ts → self-clear) when a detector tick finds none.
  * `_heartbeat_stuck_payload()` returns the cached items when FRESH and `[]`
    when STALE (so a wedged/stopped detector can never pin a banner).
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import clawmetry.sync as sync  # noqa: E402


_BASE = 1_700_000_000


def _ts(offset_s: int) -> str:
    from datetime import datetime
    return datetime.fromtimestamp(_BASE + offset_s).isoformat()


def _tool_ev(offset_s: int, et: str = "tool_call") -> dict:
    return {"event_type": et, "ts": _ts(offset_s), "data": {"name": "Bash"}}


class _FakeStore:
    def __init__(self, sessions, events_by_sid):
        self._sessions = sessions
        self._events = events_by_sid
        self.ingested: list[dict] = []

    def query_sessions_table(self, *, agent_type=None, limit=200):
        return list(self._sessions)[:limit]

    def query_events(self, *, session_id=None, limit=500, **kw):
        evs = list(reversed(self._events.get(session_id, [])))
        return evs[:limit]

    def ingest_loop_signal(self, **kw):
        self.ingested.append(kw)


def _active_session(sid="claude_code:abc", **extra):
    from datetime import datetime
    row = {
        "session_id": sid,
        "status": "active",
        "ended_at": None,
        "started_at": datetime.now().isoformat(),
        "last_active_at": datetime.now().isoformat(),
    }
    row.update(extra)
    return row


@pytest.fixture(autouse=True)
def _conservative_thresholds(monkeypatch):
    monkeypatch.setattr(sync, "STUCK_TOOL_THRESHOLD", 25, raising=False)
    monkeypatch.setattr(sync, "STUCK_MIN_SECONDS", 180, raising=False)
    monkeypatch.setattr(sync, "STUCK_RECENT_MINUTES", 15, raising=False)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Each test starts from a clean cache so order can't leak state."""
    sync._LATEST_STUCK = {"ts": 0.0, "items": []}
    yield
    sync._LATEST_STUCK = {"ts": 0.0, "items": []}


# ── cache population ─────────────────────────────────────────────────────────

def test_emit_populates_latest_stuck_cache():
    sid = "claude_code:wedged"
    # 40 tool calls, one every 10s -> 390s span -> stuck on both bounds.
    evs = [_tool_ev(i * 10) for i in range(40)]
    store = _FakeStore([_active_session(sid)], {sid: evs})

    n = sync._emit_stuck_signals(store, {})
    assert n == 1

    cache = sync._LATEST_STUCK
    assert cache["ts"] > 0
    assert len(cache["items"]) == 1
    item = cache["items"][0]
    # Runtime resolution (waste_flags.runtime_from_session_id) is exercised by
    # the detector tests; here we only assert the cache carries SOME runtime and
    # the pre-built banner is correctly shaped — that's the heartbeat wiring.
    assert item["runtime"]
    assert item["tool_calls"] == 40
    assert "stuck:" in item["message"]
    assert "40 tool calls" in item["message"]
    assert len(item["message"]) <= sync._STUCK_HEARTBEAT_MAX_MSG


def test_emit_no_stuck_clears_cache_items_but_keeps_fresh_ts():
    """A detector tick that finds NONE must refresh ts with items=[] so the
    device self-clears (the payload helper then returns [] because items=[])."""
    # Pre-seed a stale "stuck" cache as if a prior tick had one.
    sync._LATEST_STUCK = {"ts": 123.0, "items": [{"runtime": "openclaw",
                          "tool_calls": 30, "since_seconds": 200,
                          "message": "openclaw stuck: 30 tool calls, no progress for 3m"}]}

    # Now feed a session with too few tool calls -> NOT stuck.
    sid = "openclaw:fine"
    evs = [_tool_ev(i * 10) for i in range(5)]
    store = _FakeStore([_active_session(sid)], {sid: evs})

    n = sync._emit_stuck_signals(store, {})
    assert n == 0
    # Cleared the items (self-clear) and refreshed ts to ~now.
    assert sync._LATEST_STUCK["items"] == []
    assert sync._LATEST_STUCK["ts"] > 123.0


# ── payload freshness gate ───────────────────────────────────────────────────

def test_payload_includes_stuck_when_fresh():
    import time
    sync._LATEST_STUCK = {
        "ts": time.time(),
        "items": [{"runtime": "codex", "tool_calls": 31, "since_seconds": 240,
                   "message": "codex stuck: 31 tool calls, no progress for 4m"}],
    }
    out = sync._heartbeat_stuck_payload()
    assert len(out) == 1
    assert out[0]["runtime"] == "codex"
    assert out[0]["tool_calls"] == 31
    assert out[0]["message"].startswith("codex stuck:")


def test_payload_omits_stuck_when_stale():
    import time
    # ts is well outside the freshness window -> helper returns [].
    sync._LATEST_STUCK = {
        "ts": time.time() - (sync._STUCK_HEARTBEAT_FRESH_SECONDS + 60),
        "items": [{"runtime": "codex", "tool_calls": 31, "since_seconds": 240,
                   "message": "codex stuck: 31 tool calls, no progress for 4m"}],
    }
    assert sync._heartbeat_stuck_payload() == []


def test_payload_empty_when_fresh_but_no_items():
    import time
    sync._LATEST_STUCK = {"ts": time.time(), "items": []}
    assert sync._heartbeat_stuck_payload() == []


def test_payload_caps_item_count_and_message_length():
    import time
    long_msg = "x" * 500
    items = [{"runtime": "openclaw", "tool_calls": 30, "since_seconds": 200,
              "message": long_msg} for _ in range(20)]
    sync._LATEST_STUCK = {"ts": time.time(), "items": items}
    out = sync._heartbeat_stuck_payload()
    assert len(out) == sync._STUCK_HEARTBEAT_MAX_ITEMS
    assert all(len(it["message"]) <= sync._STUCK_HEARTBEAT_MAX_MSG for it in out)


def test_payload_never_raises_on_garbage_cache():
    sync._LATEST_STUCK = {"ts": "not-a-float", "items": "nope"}
    assert sync._heartbeat_stuck_payload() == []


def test_emit_then_payload_end_to_end():
    """Integration: detector tick -> cache -> a FRESH payload carries it."""
    sid = "claude_code:wedged"
    evs = [_tool_ev(i * 10) for i in range(40)]
    store = _FakeStore([_active_session(sid)], {sid: evs})

    assert sync._emit_stuck_signals(store, {}) == 1
    out = sync._heartbeat_stuck_payload()
    assert len(out) == 1
    assert out[0]["runtime"]
    assert "stuck:" in out[0]["message"]
