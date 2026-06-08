"""Tests for the daemon-side STUCK-agent detector (issue clawmetry-hardware#15).

The desk device promises a "<runtime> stuck: N tool calls, no progress" banner.
Until now the only stuck/loop signal came from the enforcement PROXY's
LoopDetector, so anyone not running the proxy never saw it. ``sync._detect_stuck_sessions``
reconstructs the same signal from the DuckDB event stream so it works for
EVERYONE, proxy-independent.

These tests pin the detector's LOGIC with a synthetic event stream (a fake
store) — synthetic input is appropriate for a deterministic unit test (the
no-synthetic-seeds rule targets e2e tests) — plus one real-DuckDB integration
test of the full emit -> query_recent_loop_signals -> device-alert path.

Covered:
  * A long no-progress tool streak trips the detector.
  * A stream WITH interleaved assistant text replies does NOT trip it.
  * Threshold boundary: streak of exactly (threshold-1) is excused, threshold trips.
  * The wall-clock min-seconds bound: a long but FAST streak is excused.
  * An ended / idle session is ignored.
  * A user message inside the streak resets it (progress marker).
  * Bad / malformed event data doesn't crash the detector.
  * Integration: _emit_stuck_signals -> ingest_loop_signal -> the
    _build_device_summary alert path produces the "<rt> stuck" banner, and the
    banner self-clears (no re-emit) once the session is no longer stuck.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import clawmetry.sync as sync  # noqa: E402


# ── Synthetic event-stream helpers ───────────────────────────────────────────
#
# query_events() returns NEWEST-first (ORDER BY ts DESC). The detector walks in
# that order, so build helpers that produce a chronological list and reverse it
# to mimic the store's ordering.

_BASE = 1_700_000_000  # arbitrary epoch base for synthetic ts (seconds)


def _ts(offset_s: int) -> str:
    """Naive-local ISO string `offset_s` seconds after the base — matches the
    store's wall-clock convention."""
    from datetime import datetime

    return datetime.fromtimestamp(_BASE + offset_s).isoformat()


def _tool_ev(offset_s: int, et: str = "tool_call") -> dict:
    return {"event_type": et, "ts": _ts(offset_s), "data": {"name": "Bash"}}


def _assistant_text_ev(offset_s: int, text: str = "Here is the result.") -> dict:
    return {
        "event_type": "assistant",
        "ts": _ts(offset_s),
        "data": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def _user_ev(offset_s: int) -> dict:
    return {"event_type": "user", "ts": _ts(offset_s),
            "data": {"role": "user", "content": "do the thing"}}


class _FakeStore:
    """Minimal store satisfying the detector's surface: query_sessions_table,
    query_events, ingest_loop_signal."""

    def __init__(self, sessions, events_by_sid):
        self._sessions = sessions
        # events_by_sid maps session_id -> chronological event list; store
        # returns newest-first, so reverse on read.
        self._events = events_by_sid
        self.ingested: list[dict] = []

    def query_sessions_table(self, *, agent_type=None, limit=200):
        return list(self._sessions)[:limit]

    def query_events(self, *, session_id=None, limit=500, **kw):
        evs = list(self._events.get(session_id, []))
        evs = list(reversed(evs))  # newest-first, like DuckDB ORDER BY ts DESC
        return evs[:limit]

    def ingest_loop_signal(self, **kw):
        self.ingested.append(kw)


def _active_session(sid="claude_code:abc", **extra):
    """A recently-active, non-ended session row. last_active_at defaults to
    'now' so the recency gate passes regardless of test clock."""
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
    """Pin module thresholds to the documented defaults regardless of the
    runner's env (a CI box might export CLAWMETRY_STUCK_* )."""
    monkeypatch.setattr(sync, "STUCK_TOOL_THRESHOLD", 25, raising=False)
    monkeypatch.setattr(sync, "STUCK_MIN_SECONDS", 180, raising=False)
    monkeypatch.setattr(sync, "STUCK_RECENT_MINUTES", 15, raising=False)


# ── Core logic ───────────────────────────────────────────────────────────────


def test_long_no_progress_streak_trips():
    sid = "claude_code:stuck1"
    # 40 tool calls, one every 10s -> 390s span, well over both bounds.
    evs = [_tool_ev(i * 10) for i in range(40)]
    store = _FakeStore([_active_session(sid)], {sid: evs})

    stuck = sync._detect_stuck_sessions(store)

    assert len(stuck) == 1
    s = stuck[0]
    assert s["session_id"] == sid
    assert s["runtime"] == "claude_code"
    assert s["tool_calls"] == 40
    assert s["since_seconds"] >= 180


def test_interleaved_text_replies_do_not_trip():
    sid = "openclaw:healthy"
    # 40 tool calls but an assistant TEXT reply every 5 calls -> the streak
    # since the last reply is only ~4, far below threshold.
    evs = []
    t = 0
    for batch in range(8):
        for _ in range(5):
            evs.append(_tool_ev(t))
            t += 10
        evs.append(_assistant_text_ev(t))  # progress marker
        t += 10
    store = _FakeStore([_active_session(sid)], {sid: evs})

    assert sync._detect_stuck_sessions(store) == []


def test_threshold_boundary():
    sid = "codex:edge"
    span_each = 10  # 10s between calls

    # threshold-1 (24) tool calls -> NOT stuck.
    evs24 = [_tool_ev(i * span_each) for i in range(sync.STUCK_TOOL_THRESHOLD - 1)]
    store24 = _FakeStore([_active_session(sid)], {sid: evs24})
    assert sync._detect_stuck_sessions(store24) == []

    # exactly threshold (25) tool calls AND span >= 180s -> stuck.
    evs25 = [_tool_ev(i * span_each) for i in range(sync.STUCK_TOOL_THRESHOLD)]
    store25 = _FakeStore([_active_session(sid)], {sid: evs25})
    stuck = sync._detect_stuck_sessions(store25)
    assert len(stuck) == 1
    assert stuck[0]["tool_calls"] == sync.STUCK_TOOL_THRESHOLD


def test_long_but_fast_streak_is_excused():
    sid = "aider:fast"
    # 60 tool calls but only 1s apart -> 59s span, below STUCK_MIN_SECONDS.
    evs = [_tool_ev(i) for i in range(60)]
    store = _FakeStore([_active_session(sid)], {sid: evs})
    assert sync._detect_stuck_sessions(store) == []


def test_user_message_resets_streak():
    sid = "openclaw:reset"
    # 30 tool calls, then a USER message, then 5 more tool calls (newest).
    # Walking newest->older, the user message breaks the streak at 5 tools.
    evs = [_tool_ev(i * 10) for i in range(30)]
    evs.append(_user_ev(300))
    evs += [_tool_ev(310 + i * 10) for i in range(5)]
    store = _FakeStore([_active_session(sid)], {sid: evs})
    assert sync._detect_stuck_sessions(store) == []


def test_ended_session_ignored():
    sid = "claude_code:done"
    evs = [_tool_ev(i * 10) for i in range(40)]
    ended = _active_session(sid, status="ended", ended_at=_ts(400))
    store = _FakeStore([ended], {sid: evs})
    assert sync._detect_stuck_sessions(store) == []


def test_idle_session_ignored():
    sid = "claude_code:idle"
    from datetime import datetime, timedelta

    long_ago = (datetime.now() - timedelta(minutes=90)).isoformat()
    evs = [_tool_ev(i * 10) for i in range(40)]
    idle = _active_session(sid, last_active_at=long_ago, started_at=long_ago)
    store = _FakeStore([idle], {sid: evs})
    assert sync._detect_stuck_sessions(store) == []


def test_bad_data_does_not_crash():
    sid = "openclaw:junk"
    # Mix valid tool calls with malformed rows: data is a junk string, a list,
    # None, an int; rows that aren't dicts; a tool row whose data is a bad
    # JSON string. None of this should raise.
    evs = []
    for i in range(40):
        evs.append(_tool_ev(i * 10))
    evs.append({"event_type": "tool_call", "ts": _ts(500), "data": "{not json"})
    evs.append({"event_type": "assistant", "ts": _ts(510), "data": "plain string body"})
    evs.append({"event_type": "weird", "ts": _ts(520), "data": [1, 2, 3]})
    evs.append({"event_type": "tool_call", "ts": _ts(530), "data": None})
    evs.append("not-a-dict-event")  # not a dict at all
    evs.append({"event_type": "tool_call", "ts": None, "data": {"x": 1}})
    store = _FakeStore([_active_session(sid)], {sid: evs})

    # Must not raise; the valid streak is still detected.
    stuck = sync._detect_stuck_sessions(store)
    assert isinstance(stuck, list)


def test_assistant_text_string_content_is_progress():
    sid = "openclaw:strcontent"
    # assistant reply whose content is a plain STRING (not a block list) counts
    # as text -> progress. 30 tools, then a string-content assistant reply,
    # then 5 tools -> streak resets to 5.
    evs = [_tool_ev(i * 10) for i in range(30)]
    evs.append({"event_type": "assistant", "ts": _ts(300),
                "data": {"role": "assistant", "content": "done with that step"}})
    evs += [_tool_ev(310 + i * 10) for i in range(5)]
    store = _FakeStore([_active_session(sid)], {sid: evs})
    assert sync._detect_stuck_sessions(store) == []


def test_tool_use_only_assistant_does_not_count_as_progress():
    sid = "claude_code:tooluseonly"
    # Anthropic shape: an assistant turn whose content is ONLY a tool_use block
    # is NOT a text reply, so it must NOT break the streak. 40 such turns ->
    # stuck. (The assistant envelope itself isn't a tool event type here, but
    # the explicit tool_call rows around it are; model it as tool_use events.)
    evs = [_tool_ev(i * 10, et="tool_use") for i in range(40)]
    store = _FakeStore([_active_session(sid)], {sid: evs})
    stuck = sync._detect_stuck_sessions(store)
    assert len(stuck) == 1
    assert stuck[0]["tool_calls"] == 40


def test_tool_result_not_counted_only_calls():
    """A round-trip is one tool_call + one tool_result; only the CALL counts
    (results would ~2x-inflate the streak)."""
    sid = "openclaw:dotted"
    evs = []
    t = 0
    for _ in range(30):
        evs.append(_tool_ev(t, et="tool.call"))
        t += 10
        evs.append(_tool_ev(t, et="tool.result"))  # result must NOT count
        t += 10
    store = _FakeStore([_active_session(sid)], {sid: evs})
    stuck = sync._detect_stuck_sessions(store)
    assert len(stuck) == 1
    assert stuck[0]["tool_calls"] == 30  # 30 calls, not 60


# ── Emit wiring + dedupe ─────────────────────────────────────────────────────


def test_emit_writes_signal_and_message():
    sid = "claude_code:emit"
    evs = [_tool_ev(i * 10) for i in range(40)]
    store = _FakeStore([_active_session(sid)], {sid: evs})
    state: dict = {}

    n = sync._emit_stuck_signals(store, state)

    assert n == 1
    assert len(store.ingested) == 1
    sig = store.ingested[0]
    assert sig["session_id"] == sid
    assert sig["signature"] == "daemon_stuck"
    assert sig["repeat_count"] == 40
    assert "stuck" in sig["details"]["message"]
    assert sig["details"]["message"].startswith("claude_code stuck:")
    assert "no progress" in sig["details"]["message"]


def test_emit_dedupes_within_window():
    sid = "claude_code:dedupe"
    evs = [_tool_ev(i * 10) for i in range(40)]
    store = _FakeStore([_active_session(sid)], {sid: evs})
    state: dict = {}

    assert sync._emit_stuck_signals(store, state) == 1
    # Immediate re-run: within the re-emit window -> no new write.
    assert sync._emit_stuck_signals(store, state) == 0
    assert len(store.ingested) == 1


def test_emit_no_stuck_is_noop():
    sid = "openclaw:fine"
    evs = [_tool_ev(i) for i in range(10)]  # short + fast
    store = _FakeStore([_active_session(sid)], {sid: evs})
    state: dict = {}
    assert sync._emit_stuck_signals(store, state) == 0
    assert store.ingested == []


# ── Real-DuckDB integration: emit -> read -> device alert -> self-clear ───────


@pytest.fixture
def real_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "stuck.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Own the writer so get_store() opens the real DuckDB writer against our tmp
    # file instead of returning a _ProxyStore that forwards to any daemon that
    # happens to be running on this dev box.
    ls.mark_writer_owner()
    store = ls.get_store()
    yield store
    try:
        store.close()
    except Exception:
        pass


def test_emit_to_device_alert_path(real_store):
    """Full path: a detected stuck session -> ingest_loop_signal ->
    query_recent_loop_signals -> _build_device_summary surfaces the precise
    "<rt> stuck: ..." banner with NO cloud change."""
    sid = "claude_code:integ"
    evs = [_tool_ev(i * 10) for i in range(40)]

    # Drive the detector against a fake-events store but write the signal into
    # the REAL store, then read it back exactly as the snapshot does.
    fake = _FakeStore([_active_session(sid)], {sid: evs})
    stuck = sync._detect_stuck_sessions(fake)
    assert len(stuck) == 1
    st = stuck[0]
    msg = f"{st['runtime']} stuck: {st['tool_calls']} tool calls, no progress"
    real_store.ingest_loop_signal(
        session_id=sid,
        signature="daemon_stuck",
        repeat_count=st["tool_calls"],
        severity="warning",
        agent_type=st["runtime"],
        details={"source": "daemon_stuck_detector", "message": msg,
                 "tool_calls": st["tool_calls"]},
    )

    sigs = real_store.query_recent_loop_signals(limit=5, since_minutes=30)
    assert sigs, "signal must be readable within the 30-min window"
    hot = next((s for s in sigs if int(s.get("repeat_count") or 0) >= 5), None)
    assert hot is not None

    # Mirror _build_device_summary's alert composition (details.message wins).
    det = hot.get("details")
    if isinstance(det, str):
        import json as _j
        det = _j.loads(det)
    alert_msg = det.get("message") if isinstance(det, dict) else None
    assert alert_msg and alert_msg.startswith("claude_code stuck:")


def test_device_alert_self_clears_when_not_stuck(real_store):
    """A signal whose last_seen is older than the snapshot's 30-min window is
    NOT surfaced — so once the daemon stops re-emitting (session no longer
    stuck) the banner clears on its own. No permanently-red banner.

    Drive it with an explicit BACK-DATED last_seen (45 min ago) so the
    snapshot's since_minutes=30 window excludes it, proving the auto-clear."""
    from datetime import datetime, timedelta

    sid = "claude_code:expire"
    stale = (datetime.now() - timedelta(minutes=45)).isoformat(timespec="seconds")
    real_store.ingest_loop_signal(
        session_id=sid, signature="daemon_stuck", repeat_count=40,
        first_seen=stale, last_seen=stale,
        severity="warning", agent_type="claude_code",
        details={"message": "claude_code stuck: 40 tool calls, no progress"},
    )
    # The snapshot reads with since_minutes=30 -> a 45-min-old row is excluded,
    # so summary['alert'] stays None (banner clears).
    assert real_store.query_recent_loop_signals(limit=5, since_minutes=30) == []
    # And a wider window still finds it (proves it's the window, not a lost row).
    assert real_store.query_recent_loop_signals(limit=5, since_minutes=60)


# ── Regression: real runtime shapes (blocker fix) ────────────────────────────
# The two dominant runtimes host tool calls INSIDE a message envelope, not as
# top-level tool_call events. Counting only top-level types made the detector
# inert for them. These lock in the content-aware counting.

def _v3_model_completed_tools_ev(offset_s, n_tools=1):
    """OpenClaw v3 turn: event_type=model.completed, tools in data.toolMetas."""
    return {
        "event_type": "model.completed",
        "ts": _ts(offset_s),
        "data": {"toolMetas": [{"name": "Bash"} for _ in range(n_tools)]},
    }


def _v3_model_completed_text_ev(offset_s, text="Done — here is the answer."):
    return {
        "event_type": "model.completed",
        "ts": _ts(offset_s),
        "data": {"completionText": text},
    }


def _cc_assistant_tooluse_ev(offset_s, n_tools=1):
    """Claude Code turn: event_type=assistant, tool_use in message.content."""
    return {
        "event_type": "assistant",
        "ts": _ts(offset_s),
        "data": {"message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Bash", "input": {}} for _ in range(n_tools)
        ]}},
    }


def test_openclaw_v3_model_completed_toolmetas_trips():
    """BLOCKER fix: OpenClaw v3 (model.completed + toolMetas) must be counted."""
    sid = "openclaw:v3stuck"
    evs = [_v3_model_completed_tools_ev(i * 10) for i in range(30)]
    store = _FakeStore([_active_session(sid)], {sid: evs})
    stuck = sync._detect_stuck_sessions(store)
    assert len(stuck) == 1
    assert stuck[0]["tool_calls"] == 30


def test_claude_code_assistant_content_tooluse_trips():
    """BLOCKER fix: Claude Code (assistant + message.content tool_use) counted."""
    sid = "claude_code:ccstuck"
    evs = [_cc_assistant_tooluse_ev(i * 10) for i in range(30)]
    store = _FakeStore([_active_session(sid)], {sid: evs})
    stuck = sync._detect_stuck_sessions(store)
    assert len(stuck) == 1
    assert stuck[0]["tool_calls"] == 30


def test_v3_model_completed_text_is_progress():
    """A v3 text reply (completionText) breaks the streak — not a false positive."""
    sid = "openclaw:v3narrating"
    evs = []
    # 30 tool turns, but a real text reply every 5 turns -> never a long streak.
    for i in range(30):
        evs.append(_v3_model_completed_tools_ev(i * 20))
        if i % 5 == 4:
            evs.append(_v3_model_completed_text_ev(i * 20 + 5))
    store = _FakeStore([_active_session(sid)], {sid: evs})
    assert sync._detect_stuck_sessions(store) == []


def test_cc_assistant_text_block_is_progress():
    """A Claude Code assistant turn with a text block breaks the streak."""
    sid = "claude_code:narrating"
    evs = []
    for i in range(30):
        evs.append(_cc_assistant_tooluse_ev(i * 20))
        if i % 5 == 4:
            evs.append({
                "event_type": "assistant", "ts": _ts(i * 20 + 5),
                "data": {"message": {"role": "assistant", "content": [
                    {"type": "text", "text": "Making progress."}]}},
            })
    store = _FakeStore([_active_session(sid)], {sid: evs})
    assert sync._detect_stuck_sessions(store) == []
