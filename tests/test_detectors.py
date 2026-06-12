"""Host tests for clawmetry/detectors.py (issue #2999).

Pure unit tests over synthetic event sequences — no server, no store. Each
detector gets a POSITIVE case (the failure it must catch) and a NEGATIVE case
(a legitimate pattern it must NOT flag), plus a healthy-trace guard that proves
zero false positives on a normal session. The stuck_loop + action_discrepancy
guards are written to be RED before the detector logic and GREEN after (the
revert-proof is run separately in CI / the PR description).

Events are built in the store's on-the-wire ``query_events`` shape: a list of
dicts ``{event_type, ts, data}`` ordered NEWEST-FIRST (the detectors reverse to
chronological internally).
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import detectors  # noqa: E402


# ── helpers: build events NEWEST-FIRST (store convention) ────────────────────
def _ts(i: int) -> str:
    # Monotonic increasing seconds so chronological order is unambiguous.
    return f"2026-06-11T10:{i // 60:02d}:{i % 60:02d}"


def _tool_call(name: str, args=None, i: int = 0) -> dict:
    return {"event_type": "tool_call", "ts": _ts(i),
            "data": {"tool": name, "args": args or {}}}


def _tool_result(is_error: bool = False, tool: str = "", text: str = "",
                 i: int = 0) -> dict:
    d = {"is_error": is_error}
    if tool:
        d["tool"] = tool
    if text:
        d["output"] = text
    return {"event_type": "tool_result", "ts": _ts(i), "data": d}


def _assistant_text(text: str, i: int = 0) -> dict:
    return {"event_type": "assistant", "ts": _ts(i),
            "data": {"role": "assistant",
                     "content": [{"type": "text", "text": text}]}}


def _user(text: str = "hi", i: int = 0) -> dict:
    return {"event_type": "user", "ts": _ts(i),
            "data": {"role": "user", "content": text}}


def _newest_first(chronological: list[dict]) -> list[dict]:
    """The store returns newest-first; our builders are chronological."""
    return list(reversed(chronological))


SID = "claude_code:abc123"


# ── normalize_events ─────────────────────────────────────────────────────────
def test_normalize_handles_malformed_events_without_raising():
    junk = [None, 42, {"event_type": "tool_call", "data": "not-json{"},
            {"event_type": "tool_result", "data": None}, "string"]
    steps = detectors.normalize_events(junk)
    assert isinstance(steps, list)


def test_normalize_family_tool_calls_array():
    # claude_code/codex family shape: event_type=tool_call w/ data.tool_calls[]
    ev = {"event_type": "tool_call", "ts": _ts(1),
          "data": {"tool_calls": [
              {"function": {"name": "Bash", "arguments": "{\"cmd\":\"ls\"}"}},
              {"name": "Read", "input": {"path": "/x"}},
          ]}}
    steps = detectors.normalize_events([ev])
    calls = [s for s in steps if s["kind"] == "tool_call"]
    assert {c["tool"] for c in calls} == {"Bash", "Read"}


# ── Detector 1: stuck_loop ───────────────────────────────────────────────────
def test_stuck_loop_identical_calls_positive():
    # 5 identical Bash calls with identical args -> loop.
    chrono = [_tool_call("Bash", {"cmd": "git status"}, i) for i in range(5)]
    inc = detectors.stuck_loop(_newest_first(chrono), SID)
    assert inc is not None
    assert inc["kind"] == "stuck_loop"
    assert inc["severity"] == "warning"
    assert inc["evidence"]["pattern"] == "identical"
    assert inc["first_bad_step"] is not None


def test_stuck_loop_ngram_cycle_positive():
    # A,B,A,B,A,B cycle of two distinct tools -> loop.
    chrono = []
    for i in range(3):
        chrono.append(_tool_call("Read", {"p": i}, i * 2))
        chrono.append(_tool_call("Grep", {"q": i}, i * 2 + 1))
    inc = detectors.stuck_loop(_newest_first(chrono), SID)
    assert inc is not None
    assert inc["evidence"]["pattern"] == "cycle"


def test_stuck_loop_negative_legitimate_different_calls():
    # Repeated-but-DIFFERENT tool calls (different args each) = real work.
    chrono = [_tool_call("Bash", {"cmd": f"cat file{i}.txt"}, i) for i in range(8)]
    inc = detectors.stuck_loop(_newest_first(chrono), SID)
    assert inc is None


def test_stuck_loop_negative_progress_between():
    # Same tool but a text reply / different tool breaks the run.
    chrono = [
        _tool_call("Bash", {"cmd": "ls"}, 0),
        _tool_call("Read", {"p": "a"}, 1),
        _tool_call("Bash", {"cmd": "ls"}, 2),
        _assistant_text("here is the result", 3),
        _tool_call("Bash", {"cmd": "ls"}, 4),
    ]
    inc = detectors.stuck_loop(_newest_first(chrono), SID)
    assert inc is None


# ── Detector 2: no_progress ──────────────────────────────────────────────────
def test_no_progress_positive():
    # 25 read-only tool calls, no writes, no completion.
    chrono = [_tool_call("Read", {"p": f"/f{i}"}, i) for i in range(25)]
    inc = detectors.no_progress(_newest_first(chrono), SID)
    assert inc is not None
    assert inc["kind"] == "no_progress"
    assert inc["evidence"]["writes"] == 0


def test_no_progress_negative_with_write():
    # 25 calls but one is an Edit -> real progress, not flagged.
    chrono = [_tool_call("Read", {"p": f"/f{i}"}, i) for i in range(24)]
    chrono.append(_tool_call("Edit", {"path": "/f", "new": "x"}, 24))
    inc = detectors.no_progress(_newest_first(chrono), SID)
    assert inc is None


def test_no_progress_negative_short_session():
    # Few tool calls (below threshold) = normal early work.
    chrono = [_tool_call("Read", {"p": f"/f{i}"}, i) for i in range(5)]
    inc = detectors.no_progress(_newest_first(chrono), SID)
    assert inc is None


def test_no_progress_resets_after_user_turn():
    # Many calls but a recent user prompt resets the progress window.
    chrono = [_tool_call("Read", {"p": f"/f{i}"}, i) for i in range(25)]
    chrono.append(_user("now do this", 25))
    chrono.append(_tool_call("Read", {"p": "/again"}, 26))
    inc = detectors.no_progress(_newest_first(chrono), SID)
    assert inc is None


# ── Detector 3: repeated_tool_failure ────────────────────────────────────────
def test_repeated_tool_failure_positive():
    chrono = []
    for i in range(4):
        chrono.append(_tool_call("Bash", {"cmd": f"git push attempt {i}"}, i * 2))
        chrono.append(_tool_result(is_error=True, tool="Bash",
                                   text="error: failed to push", i=i * 2 + 1))
    inc = detectors.repeated_tool_failure(_newest_first(chrono), SID)
    assert inc is not None
    assert inc["kind"] == "repeated_tool_failure"
    assert inc["evidence"]["failures"] == 4
    assert "Bash" in inc["title"]


def test_repeated_tool_failure_negative_single_failure():
    chrono = [
        _tool_call("Bash", {"cmd": "git push"}, 0),
        _tool_result(is_error=True, tool="Bash", text="rejected", i=1),
        _tool_call("Bash", {"cmd": "git pull"}, 2),
        _tool_result(is_error=False, tool="Bash", i=3),
    ]
    inc = detectors.repeated_tool_failure(_newest_first(chrono), SID)
    assert inc is None


def test_repeated_tool_failure_text_marker_inference():
    # No structured is_error, but result text screams failure.
    chrono = []
    for i in range(3):
        chrono.append(_tool_call("Bash", {"cmd": "deploy"}, i * 2))
        chrono.append(_tool_result(is_error=False, tool="Bash",
                                   text="bash: deploy: command not found",
                                   i=i * 2 + 1))
    inc = detectors.repeated_tool_failure(_newest_first(chrono), SID)
    assert inc is not None
    assert inc["evidence"]["failures"] == 3


# ── Detector 4: action_discrepancy ───────────────────────────────────────────
def test_action_discrepancy_positive():
    # Failure -> immediately a DIFFERENT tool call, no retry, no ack.
    chrono = [
        _tool_call("Bash", {"cmd": "make build"}, 0),
        _tool_result(is_error=True, tool="Bash", text="exit code 1", i=1),
        _tool_call("send_email", {"to": "boss@x.com"}, 2),  # plowed ahead
    ]
    inc = detectors.action_discrepancy(_newest_first(chrono), SID)
    assert inc is not None
    assert inc["kind"] == "action_discrepancy"
    assert inc["severity"] == "info"  # honest: lower precision -> lower severity
    assert "continued after a failed command" in inc["title"]


def test_action_discrepancy_negative_retry():
    # Failure -> retry of the SAME tool = proper acknowledgement.
    chrono = [
        _tool_call("Bash", {"cmd": "git push"}, 0),
        _tool_result(is_error=True, tool="Bash", text="rejected", i=1),
        _tool_call("Bash", {"cmd": "git pull --rebase"}, 2),  # same tool retry
    ]
    inc = detectors.action_discrepancy(_newest_first(chrono), SID)
    assert inc is None


def test_action_discrepancy_negative_acknowledge_then_continue():
    # Failure -> a reasoning text beat before continuing = acknowledged.
    chrono = [
        _tool_call("Bash", {"cmd": "make build"}, 0),
        _tool_result(is_error=True, tool="Bash", text="exit code 1", i=1),
        _assistant_text("The build failed, let me investigate the error.", 2),
        _tool_call("Read", {"p": "/log"}, 3),
    ]
    inc = detectors.action_discrepancy(_newest_first(chrono), SID)
    assert inc is None


def test_action_discrepancy_negative_no_failure():
    chrono = [
        _tool_call("Bash", {"cmd": "ls"}, 0),
        _tool_result(is_error=False, tool="Bash", text="file1\nfile2", i=1),
        _tool_call("Read", {"p": "/file1"}, 2),
    ]
    inc = detectors.action_discrepancy(_newest_first(chrono), SID)
    assert inc is None


# ── Healthy trace: ZERO false positives across ALL detectors ─────────────────
def test_healthy_session_no_incidents():
    # A normal, progressing session: prompt, varied tools, a write, replies,
    # successful results, a couple benign single failures handled by retries.
    chrono = [
        _user("please fix the bug", 0),
        _assistant_text("Let me look.", 1),
        _tool_call("Read", {"p": "/src/a.py"}, 2),
        _tool_result(is_error=False, tool="Read", text="contents", i=3),
        _tool_call("Grep", {"q": "def foo"}, 4),
        _tool_result(is_error=False, tool="Grep", text="match", i=5),
        _assistant_text("Found it, editing now.", 6),
        _tool_call("Edit", {"path": "/src/a.py", "new": "fixed"}, 7),
        _tool_result(is_error=False, tool="Edit", text="ok", i=8),
        _tool_call("Bash", {"cmd": "pytest"}, 9),
        _tool_result(is_error=True, tool="Bash", text="1 failed", i=10),
        _assistant_text("One test failed, let me retry after a fix.", 11),
        _tool_call("Bash", {"cmd": "pytest"}, 12),
        _tool_result(is_error=False, tool="Bash", text="passed", i=13),
        _assistant_text("All green.", 14),
    ]
    incidents = detectors.run_all(_newest_first(chrono), SID)
    assert incidents == [], f"healthy trace flagged: {incidents}"


# ── TRAIL-shaped fixture (representative; full dataset validation = follow-up) ─
def test_trail_shaped_tool_hallucination_fixture():
    """A hand-built event sequence in the shape of a TRAIL tool-related
    hallucination span: a tool errors (HTTP 500 / non-zero exit) and the agent
    proceeds as if it succeeded. Representative fixture only — validating
    against the full TRAIL (1987 spans) / MAST-Data (1600+ traces) sets is a
    tracked follow-up (we do NOT download datasets in CI)."""
    chrono = [
        _user("fetch the user record and email them", 0),
        _tool_call("http_get", {"url": "https://api/users/42"}, 1),
        _tool_result(is_error=True, tool="http_get",
                     text="HTTP 500 Internal Server Error", i=2),
        # Agent proceeds to email as if it had the record -> discrepancy.
        _tool_call("send_email", {"to": "user@x.com", "body": "Hi {{name}}"}, 3),
    ]
    inc = detectors.action_discrepancy(_newest_first(chrono), SID)
    assert inc is not None
    assert inc["kind"] == "action_discrepancy"


# ── run_all ordering ─────────────────────────────────────────────────────────
def test_run_all_orders_warning_before_info():
    # A loop (warning) plus a discrepancy (info) -> warning first.
    chrono = [_tool_call("Bash", {"cmd": "x"}, i) for i in range(4)]
    chrono.append(_tool_result(is_error=True, tool="Bash", text="exit code 1", i=4))
    chrono.append(_tool_call("Read", {"p": "/y"}, 5))
    incidents = detectors.run_all(_newest_first(chrono), SID)
    if len(incidents) >= 2:
        sevs = [i["severity"] for i in incidents]
        assert sevs == sorted(sevs, key=lambda s: detectors._SEVERITY_RANK[s])


# ── Daemon integration: seeded loop -> device_summary.alert ──────────────────
# Mirrors tests/test_stuck_detection.py's proven device-alert path: drive the
# daemon emitter (sync._emit_detector_incidents) against a fake-events store,
# write the incident into a REAL DuckDB store, and read it back exactly as
# _build_device_summary does (loop_signals -> repeat_count>=5 -> details.message).
import clawmetry.sync as sync  # noqa: E402


class _FakeStore:
    """Minimal store satisfying the emitter surface."""

    def __init__(self, sessions, events_by_sid, sink=None):
        self._sessions = sessions
        self._events = events_by_sid
        self._sink = sink  # a real store to forward ingest_loop_signal into
        self.ingested: list[dict] = []

    def query_sessions_table(self, *, agent_type=None, limit=200):
        return list(self._sessions)[:limit]

    def query_events(self, *, session_id=None, limit=500, **kw):
        evs = list(self._events.get(session_id, []))
        return list(reversed(evs))[:limit]  # newest-first like DuckDB

    def ingest_loop_signal(self, **kw):
        self.ingested.append(kw)
        if self._sink is not None:
            self._sink.ingest_loop_signal(**kw)


def _active_session(sid):
    from datetime import datetime
    now = datetime.now().isoformat()
    return {"session_id": sid, "status": "active", "ended_at": None,
            "started_at": now, "last_active_at": now}


@pytest.fixture
def real_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "det.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    store = ls.get_store()
    yield store
    try:
        store.close()
    except Exception:
        pass


def test_seeded_loop_surfaces_device_alert(real_store):
    """A seeded looping session, run through the daemon emitter, lands in the
    loop_signals table and surfaces via the EXACT _build_device_summary path
    (repeat_count>=5, details.message) with NO cloud/firmware change."""
    sid = "codex:loopint"
    # 6 identical Bash calls -> stuck_loop (warning) incident.
    chrono = [
        {"event_type": "tool_call", "ts": _ts(i * 10),
         "data": {"tool": "Bash", "args": {"cmd": "make"}}}
        for i in range(6)
    ]
    fake = _FakeStore([_active_session(sid)], {sid: list(reversed(chrono))},
                      sink=real_store)
    # query_events in _FakeStore re-reverses, so pass chronological here.
    fake._events[sid] = chrono

    state: dict = {}
    n = sync._emit_detector_incidents(fake, state)
    assert n >= 1, "emitter must produce at least one incident"

    # The incident must be folded into the heartbeat slice (device_summary.alert
    # source for the cloud path).
    items = sync._LATEST_STUCK.get("items") or []
    assert any("loop" in (it.get("message") or "").lower() for it in items)

    # And readable via the loop_signals -> device-alert path.
    sigs = real_store.query_recent_loop_signals(limit=5, since_minutes=30)
    hot = next((s for s in sigs if int(s.get("repeat_count") or 0) >= 5), None)
    assert hot is not None, "incident must clear the repeat_count>=5 device gate"
    det = hot.get("details")
    if isinstance(det, str):
        import json as _j
        det = _j.loads(det)
    assert isinstance(det, dict)
    assert det.get("source") == "daemon_detector"
    assert "looping" in (det.get("message") or "").lower()
    # Detection only: the incident text invites a human Stop/Pause, never auto-kill.
    assert "stop or pause" in (det.get("detail") or "").lower()


def test_emitter_dedupes_within_window(real_store):
    sid = "codex:dedupe"
    chrono = [
        {"event_type": "tool_call", "ts": _ts(i * 10),
         "data": {"tool": "Bash", "args": {"cmd": "make"}}}
        for i in range(6)
    ]
    fake = _FakeStore([_active_session(sid)], {sid: chrono}, sink=real_store)
    state: dict = {}
    first = sync._emit_detector_incidents(fake, state)
    second = sync._emit_detector_incidents(fake, state)  # same tick window
    assert first >= 1
    assert second == 0, "a re-run within the window must not re-emit"


def test_emitter_never_raises_on_bad_store():
    class _Boom:
        def query_sessions_table(self, **kw):
            raise RuntimeError("boom")
    # Must swallow and return 0, never propagate into the daemon loop.
    assert sync._emit_detector_incidents(_Boom(), {}) == 0
