"""Tests for clawmetry.outcome_classifier — Issue #1614.

Coverage:
  1. Pure-classifier scenarios: success / failed / escalated / ongoing
  2. Real v3 event shapes (per memory
     ``feedback_synthetic_tests_missed_real_event_shape``): we exercise the
     same field names ingest sees on a live OpenClaw daemon, not synthetic
     "type=message" stubs. ``tool.result``, ``model.completed``,
     ``session.ended``.
  3. Aggregator math: success_rate excludes ongoing + escalated.
  4. DuckDB integration: ingest a session, run the classifier, read back
     via query_outcomes, hit /api/outcomes through Flask test client.
  5. Re-classification: a session that looked "ongoing" becomes "failed"
     after a tool-error event lands.
"""

from __future__ import annotations

import importlib
import os
import sys
import time

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── 1. Pure classifier — 4 outcome scenarios ───────────────────────────────


def test_classify_success_terminal_session_ended():
    """A session with a session.ended event + no errors → success."""
    from clawmetry.outcome_classifier import classify_session, OUTCOME_SUCCESS

    events = [
        {"event_type": "session.started", "ts": "2026-05-17T10:00:00Z"},
        {"event_type": "prompt.submitted", "ts": "2026-05-17T10:00:05Z",
         "data": {"finalPromptText": "list files"}},
        {"event_type": "tool.result", "ts": "2026-05-17T10:00:10Z",
         "data": {"name": "bash", "output": "a.txt b.txt", "status": "ok"}},
        {"event_type": "model.completed", "ts": "2026-05-17T10:00:12Z",
         "data": {"modelId": "claude-opus-4", "text": "Here are the files."}},
        {"event_type": "session.ended", "ts": "2026-05-17T10:00:13Z"},
    ]
    outcome, conf = classify_session(events, {})
    assert outcome == OUTCOME_SUCCESS
    assert conf >= 0.8


def test_classify_failed_tool_error_at_tail():
    """tool.result with error=True at the tail → failed (high confidence)."""
    from clawmetry.outcome_classifier import classify_session, OUTCOME_FAILED

    events = [
        {"event_type": "session.started", "ts": "2026-05-17T10:00:00Z"},
        {"event_type": "model.completed", "ts": "2026-05-17T10:00:05Z",
         "data": {"modelId": "claude-opus-4", "text": "Let me try."}},
        {"event_type": "tool.result", "ts": "2026-05-17T10:00:10Z",
         "data": {"name": "bash", "error": True,
                  "error_message": "command not found"}},
        {"event_type": "session.ended", "ts": "2026-05-17T10:00:11Z"},
    ]
    outcome, conf = classify_session(events, {})
    assert outcome == OUTCOME_FAILED
    assert conf >= 0.85


def test_classify_failed_assistant_text_pattern():
    """Last assistant text contains a configured failure pattern → failed."""
    from clawmetry.outcome_classifier import classify_session, OUTCOME_FAILED

    events = [
        {"event_type": "session.started", "ts": "2026-05-17T10:00:00Z"},
        {"event_type": "model.completed", "ts": "2026-05-17T10:00:12Z",
         "data": {"modelId": "claude-opus-4",
                  "text": "I couldn't complete that request because the API returned 403."}},
        {"event_type": "session.ended", "ts": "2026-05-17T10:00:13Z"},
    ]
    outcome, conf = classify_session(events, {})
    assert outcome == OUTCOME_FAILED
    assert 0.5 < conf < 0.9  # heuristic confidence, not the hard 0.9 signal


def test_classify_escalated_when_approval_row_exists():
    """An approval row scoped to this session → escalated, regardless of
    whether the tool itself succeeded or failed."""
    from clawmetry.outcome_classifier import classify_session, OUTCOME_ESCALATED

    events = [
        {"event_type": "session.started", "ts": "2026-05-17T10:00:00Z"},
        {"event_type": "tool.result", "ts": "2026-05-17T10:00:10Z",
         "data": {"name": "bash", "status": "ok"}},
        {"event_type": "session.ended", "ts": "2026-05-17T10:00:11Z"},
    ]
    approvals = [{"id": "app-1", "status": "approved"}]
    outcome, conf = classify_session(events, {}, approvals=approvals)
    assert outcome == OUTCOME_ESCALATED
    assert conf >= 0.9


def test_classify_ongoing_when_recent_no_terminal():
    """No session.ended AND last event <5 min ago → ongoing."""
    from clawmetry.outcome_classifier import classify_session, OUTCOME_ONGOING

    now = time.time()
    from datetime import datetime, timezone
    recent_ts = datetime.fromtimestamp(now - 30, tz=timezone.utc).isoformat()
    events = [
        {"event_type": "session.started", "ts": recent_ts},
        {"event_type": "model.completed", "ts": recent_ts,
         "data": {"modelId": "claude-opus-4", "text": "Working on it..."}},
    ]
    outcome, conf = classify_session(events, {}, now=now)
    assert outcome == OUTCOME_ONGOING
    assert conf > 0.5


def test_classify_stale_no_terminal_defaults_to_success():
    """No terminal event + old activity → falls through to conservative
    success (default). We err this direction per the issue spec — false
    failures are worse than missed failures."""
    from clawmetry.outcome_classifier import classify_session, OUTCOME_SUCCESS

    events = [
        {"event_type": "model.completed", "ts": "2026-05-17T10:00:05Z",
         "data": {"modelId": "claude-opus-4", "text": "Done."}},
    ]
    # now is 1 day later — events are stale.
    outcome, _ = classify_session(events, {}, now=time.time())
    assert outcome == OUTCOME_SUCCESS


def test_classify_explicit_failed_status_on_session_row():
    """sessions.status='errored' → failed with confidence 1.0."""
    from clawmetry.outcome_classifier import classify_session, OUTCOME_FAILED

    outcome, conf = classify_session([], {"status": "errored"})
    assert outcome == OUTCOME_FAILED
    assert conf == 1.0


# ── 2. Aggregator math ─────────────────────────────────────────────────────


def test_aggregate_success_rate_excludes_ongoing_and_escalated():
    """success_rate is success / (success + failed), NOT success / total.
    Ongoing + escalated have their own buckets."""
    from clawmetry.outcome_classifier import aggregate_outcomes

    rows = (
        [{"outcome": "success"}] * 80
        + [{"outcome": "failed"}] * 20
        + [{"outcome": "escalated"}] * 10
        + [{"outcome": "ongoing"}] * 5
    )
    agg = aggregate_outcomes(rows)
    assert agg["total"] == 115
    assert agg["success"] == 80
    assert agg["failed"] == 20
    assert agg["escalated"] == 10
    assert agg["ongoing"] == 5
    # 80 / (80 + 20) = 0.80
    assert agg["success_rate"] == 0.8
    # 10 / 115 ≈ 0.087
    assert agg["needed_human_rate"] == round(10 / 115, 4)


def test_aggregate_empty_input():
    """No sessions → zeros everywhere, no div-by-zero."""
    from clawmetry.outcome_classifier import aggregate_outcomes

    agg = aggregate_outcomes([])
    assert agg["total"] == 0
    assert agg["success_rate"] == 0.0
    assert agg["needed_human_rate"] == 0.0


# ── 3. Real-event-shape sanity (memory: synthetic tests missed real data) ──


def test_v3_message_envelope_assistant_role():
    """Legacy ``message`` event with role=assistant carrying failure text
    must be recognised — not just the v3 ``model.completed`` shape."""
    from clawmetry.outcome_classifier import classify_session, OUTCOME_FAILED

    events = [
        {"event_type": "message", "ts": "2026-05-17T10:00:05Z",
         "data": {"message": {"role": "assistant",
                              "content": "I was unable to find that file."}}},
        {"event_type": "session.ended", "ts": "2026-05-17T10:00:06Z"},
    ]
    outcome, _ = classify_session(events, {})
    assert outcome == OUTCOME_FAILED


def test_v3_anthropic_block_list_content():
    """Anthropic content-block list shape: data.message.content is a list
    of {type, text} blocks. The text extractor must join them, not drop
    everything."""
    from clawmetry.outcome_classifier import classify_session, OUTCOME_FAILED

    events = [
        {"event_type": "message", "ts": "2026-05-17T10:00:05Z",
         "data": {"message": {"role": "assistant", "content": [
             {"type": "text", "text": "Trying the request now. "},
             {"type": "text", "text": "I couldn't complete that — auth failed."},
         ]}}},
        {"event_type": "session.ended", "ts": "2026-05-17T10:00:06Z"},
    ]
    outcome, _ = classify_session(events, {})
    assert outcome == OUTCOME_FAILED


# ── 4. DuckDB integration + API endpoint ───────────────────────────────────


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Spin up a fresh DuckDB store backed by tmp_path."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    store = ls.get_store()
    yield ls, store
    try:
        store.stop(flush=True)
    except Exception:
        pass


def _seed_finished_session(store, *, sid, ok=True, with_error=False):
    """Insert a session row + a handful of events that wind to session.ended."""
    store.ingest_session({
        "agent_type": "openclaw",
        "session_id": sid,
        "started_at": "2026-05-17T10:00:00Z",
        "last_active_at": "2026-05-17T10:00:13Z",
        "ended_at": "2026-05-17T10:00:13Z",
        "status": "completed" if ok else "errored",
        "total_tokens": 1000,
        "cost_usd": 0.02,
    })
    base = [
        {"id": f"{sid}-1", "agent_type": "openclaw", "node_id": "n",
         "agent_id": "main", "session_id": sid,
         "event_type": "session.started", "ts": "2026-05-17T10:00:00Z"},
        {"id": f"{sid}-2", "agent_type": "openclaw", "node_id": "n",
         "agent_id": "main", "session_id": sid,
         "event_type": "model.completed", "ts": "2026-05-17T10:00:12Z",
         "data": {"modelId": "claude-opus-4", "text": "All done."}},
    ]
    if with_error:
        base.append({
            "id": f"{sid}-err", "agent_type": "openclaw", "node_id": "n",
            "agent_id": "main", "session_id": sid,
            "event_type": "tool.result", "ts": "2026-05-17T10:00:11Z",
            "data": {"name": "bash", "error": True,
                     "error_message": "command not found"},
        })
    base.append({
        "id": f"{sid}-end", "agent_type": "openclaw", "node_id": "n",
        "agent_id": "main", "session_id": sid,
        "event_type": "session.ended", "ts": "2026-05-17T10:00:13Z",
    })
    for e in base:
        store.ingest(e)
    store.flush()


def test_query_outcomes_classifies_unlabeled_rows(isolated_store):
    """Fresh session with no outcome column populated → query_outcomes
    inline-classifies and persists the result so the next call is pure
    SELECT."""
    _ls, store = isolated_store
    _seed_finished_session(store, sid="sess-ok")
    _seed_finished_session(store, sid="sess-bad", ok=True, with_error=True)

    rows = store.query_outcomes(agent_type="openclaw")
    by_id = {r["session_id"]: r for r in rows}
    assert "sess-ok" in by_id
    assert "sess-bad" in by_id
    # ok session — explicit status=completed isn't a "failed/errored" hit,
    # so classifier falls to event-walk. With session.ended + no errors
    # the outcome is success.
    assert by_id["sess-ok"]["outcome"] == "success"
    # bad session has both: status="errored" on the row (hard signal) + a
    # tool.result error in events. Either route lands on "failed".
    assert by_id["sess-bad"]["outcome"] == "failed"


def test_api_outcomes_endpoint_returns_aggregate(isolated_store):
    """End-to-end: GET /api/outcomes returns the aggregator output."""
    _ls, store = isolated_store
    _seed_finished_session(store, sid="sess-1", ok=True)
    _seed_finished_session(store, sid="sess-2", ok=True)
    _seed_finished_session(store, sid="sess-3", ok=False, with_error=True)

    # Build a Flask app with bp_sessions registered. The route module
    # late-imports dashboard so we stub the missing bits to keep this
    # test hermetic.
    from flask import Flask
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    app = Flask(__name__)
    app.register_blueprint(sessions_mod.bp_sessions)
    body = app.test_client().get("/api/outcomes?window=30d").get_json()
    assert body["total"] == 3
    assert body["success"] == 2
    assert body["failed"] == 1
    # 2 / (2 + 1) ≈ 0.667
    assert 0.65 < body["success_rate"] < 0.68
    assert body["_source"] == "local_store"


# ── 5. Reclassification on new events ──────────────────────────────────────


def test_reclassify_after_new_error_event(isolated_store):
    """A session that classified as success → reclassified as failed when
    a tool.result error lands later (e.g. a delayed retry hook). Closes
    the spec's "re-classification: if session reopens, outcome updates"
    requirement."""
    _ls, store = isolated_store
    sid = "sess-reopen"
    _seed_finished_session(store, sid=sid, ok=True)
    rows = store.query_outcomes(agent_type="openclaw")
    by_id = {r["session_id"]: r for r in rows}
    assert by_id[sid]["outcome"] == "success"

    # New event lands: a tool error that retroactively fails the session.
    store.ingest({
        "id": f"{sid}-late-err", "agent_type": "openclaw", "node_id": "n",
        "agent_id": "main", "session_id": sid,
        "event_type": "tool.result", "ts": "2026-05-17T10:00:20Z",
        "data": {"name": "bash", "error": True,
                 "error_message": "post-hook fail"},
    })
    store.flush()
    outcome, conf = store.reclassify_session_outcome(sid)
    assert outcome == "failed"
    assert conf >= 0.85

    # Persisted: next query_outcomes returns the new label without re-
    # running the classifier (already populated → pure SELECT path).
    rows2 = store.query_outcomes(agent_type="openclaw")
    by_id2 = {r["session_id"]: r for r in rows2}
    assert by_id2[sid]["outcome"] == "failed"


# ── 7. Cognitive loop detection (issue #1706) ──────────────────────────────


def _assistant_msg(ts_iso, text, *, session_id="loop-sess", tool_uses=()):
    """Build a real ``message`` envelope event matching v3 ingest shape."""
    content = [{"type": "text", "text": text}]
    for name, file_path in tool_uses:
        content.append({
            "type": "tool_use",
            "name": name,
            "input": {"file_path": file_path} if file_path else {},
        })
    return {
        "event_type": "message",
        "ts": ts_iso,
        "session_id": session_id,
        "data": {"message": {"role": "assistant", "content": content}},
    }


def test_classify_cognitive_loop_when_assistant_repeats_self():
    """5 near-identical 'validate the results' messages 60s apart -> loop."""
    from clawmetry.outcome_classifier import (
        classify_session,
        OUTCOME_COGNITIVE_LOOP,
    )
    from datetime import datetime, timezone

    now = time.time()
    events = []
    for i in range(5):
        ts = datetime.fromtimestamp(now - (300 - 60 * i), tz=timezone.utc).isoformat()
        events.append(_assistant_msg(
            ts, "I should validate the results again to be sure."
        ))
    outcome, conf = classify_session(events, {}, now=now)
    assert outcome == OUTCOME_COGNITIVE_LOOP
    assert 0.5 < conf <= 1.0


def test_classify_distinct_messages_is_ongoing_not_loop():
    """5 different assistant messages in window -> ongoing, not a loop."""
    from clawmetry.outcome_classifier import classify_session, OUTCOME_ONGOING
    from datetime import datetime, timezone

    now = time.time()
    distinct = [
        "Let me read the file.",
        "Now I'll check the database schema.",
        "Running the test suite next.",
        "Inspecting the failed assertion.",
        "Drafting a patch for the bug.",
    ]
    events = []
    for i, txt in enumerate(distinct):
        ts = datetime.fromtimestamp(now - (300 - 60 * i), tz=timezone.utc).isoformat()
        events.append(_assistant_msg(ts, txt))
    outcome, _ = classify_session(events, {}, now=now)
    assert outcome == OUTCOME_ONGOING


def test_classify_repeated_text_with_new_tools_each_time_is_ongoing():
    """5 identical assistant texts, each invoking a NEW tool/file -> ongoing.

    Forward progress (new tool name OR new file path) shields the session
    from the cognitive-loop label even if the prose is verbatim repeated.
    """
    from clawmetry.outcome_classifier import classify_session, OUTCOME_ONGOING
    from datetime import datetime, timezone

    now = time.time()
    tools = ["bash", "read_file", "grep", "edit_file", "write_file"]
    events = []
    for i, tn in enumerate(tools):
        ts = datetime.fromtimestamp(now - (300 - 60 * i), tz=timezone.utc).isoformat()
        events.append(_assistant_msg(
            ts,
            "I should validate the results again to be sure.",
            tool_uses=[(tn, f"file_{i}.py")],
        ))
    outcome, _ = classify_session(events, {}, now=now)
    assert outcome == OUTCOME_ONGOING


# ── 8. Bug-class gate (memory: synthetic vs real event shape) ──────────────


def test_classifier_does_not_filter_on_legacy_event_shape_only():
    """Regression guard against the same bug captured in memory
    ``feedback_synthetic_tests_missed_real_event_shape`` — synthetic
    tests that pass only because they used ``event_type='message'``
    while real OpenClaw v3 emits ``event_type='model.completed'``.

    Both shapes MUST classify identically when they carry the same
    semantic content."""
    from clawmetry.outcome_classifier import classify_session

    legacy = [
        {"event_type": "message", "ts": "2026-05-17T10:00:05Z",
         "data": {"message": {"role": "assistant",
                              "content": "I couldn't complete that task."}}},
        {"event_type": "session.ended", "ts": "2026-05-17T10:00:06Z"},
    ]
    v3 = [
        {"event_type": "model.completed", "ts": "2026-05-17T10:00:05Z",
         "data": {"modelId": "claude-opus-4",
                  "text": "I couldn't complete that task."}},
        {"event_type": "session.ended", "ts": "2026-05-17T10:00:06Z"},
    ]
    assert classify_session(legacy, {})[0] == classify_session(v3, {})[0]
    assert classify_session(legacy, {})[0] == "failed"


# ── 4. Stuck tool-call detection (issue #1648) ─────────────────────────────


def _iso(epoch: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def test_find_stuck_tool_calls_unanswered_invocation():
    """Top-level toolCall event with no matching tool.result older than the
    threshold → returned by find_stuck_tool_calls."""
    from clawmetry.outcome_classifier import find_stuck_tool_calls

    now = time.time()
    events = [
        {"event_type": "tool.call", "ts": _iso(now - 600),
         "data": {"id": "call_abc", "name": "bash", "input": {"cmd": "sleep 9999"}}},
    ]
    stuck = find_stuck_tool_calls(events, now=now, threshold_seconds=120)
    assert len(stuck) == 1
    assert stuck[0][0] == "call_abc"
    assert stuck[0][1] >= 120


def test_find_stuck_tool_calls_skips_when_result_present():
    """An invocation that DOES have a matching tool.result is not stuck —
    irrespective of how long ago the invocation fired."""
    from clawmetry.outcome_classifier import find_stuck_tool_calls

    now = time.time()
    events = [
        {"event_type": "tool.call", "ts": _iso(now - 600),
         "data": {"id": "call_done", "name": "bash"}},
        {"event_type": "tool.result", "ts": _iso(now - 500),
         "data": {"tool_call_id": "call_done", "status": "ok"}},
    ]
    assert find_stuck_tool_calls(events, now=now, threshold_seconds=120) == []


def test_find_stuck_tool_calls_skips_recent_invocation():
    """Below-threshold age → not stuck yet."""
    from clawmetry.outcome_classifier import find_stuck_tool_calls

    now = time.time()
    events = [
        {"event_type": "tool.call", "ts": _iso(now - 30),
         "data": {"id": "call_recent", "name": "bash"}},
    ]
    assert find_stuck_tool_calls(events, now=now, threshold_seconds=120) == []


def test_find_stuck_tool_calls_message_envelope_shape():
    """Anthropic-shape tool_use block inside an assistant message event
    with a later tool_result block carrying tool_use_id — matched."""
    from clawmetry.outcome_classifier import find_stuck_tool_calls

    now = time.time()
    events = [
        {"event_type": "message", "ts": _iso(now - 600),
         "data": {"message": {"role": "assistant", "content": [
             {"type": "tool_use", "id": "tu_xyz", "name": "bash", "input": {}},
         ]}}},
        # Result block carried in a later (user-role) message turn.
        {"event_type": "message", "ts": _iso(now - 500),
         "data": {"message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "tu_xyz", "content": "ok"},
         ]}}},
    ]
    assert find_stuck_tool_calls(events, now=now, threshold_seconds=120) == []


def test_find_stuck_tool_calls_multiple_calls_only_unanswered():
    """Two invocations, one answered + one not — only the unanswered one
    is returned, with age measured from the earlier of duplicate emits."""
    from clawmetry.outcome_classifier import find_stuck_tool_calls

    now = time.time()
    events = [
        {"event_type": "tool.call", "ts": _iso(now - 800),
         "data": {"id": "call_a", "name": "bash"}},
        {"event_type": "tool.call", "ts": _iso(now - 600),
         "data": {"id": "call_b", "name": "bash"}},
        # Only call_a returned.
        {"event_type": "tool.result", "ts": _iso(now - 700),
         "data": {"tool_call_id": "call_a", "status": "ok"}},
    ]
    stuck = find_stuck_tool_calls(events, now=now, threshold_seconds=120)
    assert [c for c, _ in stuck] == ["call_b"]


def test_find_stuck_tool_calls_skips_calls_without_id():
    """An invocation without a parseable id cannot be matched to a result;
    we can't tell whether it ever completed, so we don't flag it as stuck.
    Conservative on purpose."""
    from clawmetry.outcome_classifier import find_stuck_tool_calls

    now = time.time()
    events = [
        {"event_type": "tool.call", "ts": _iso(now - 600),
         "data": {"id": "", "name": "bash"}},
    ]
    assert find_stuck_tool_calls(events, now=now, threshold_seconds=120) == []


def test_classify_session_returns_tool_call_stuck():
    """An ongoing-looking session with an unmatched tool invocation older
    than the threshold → tool_call_stuck (not ``ongoing``)."""
    from clawmetry.outcome_classifier import (
        classify_session, OUTCOME_TOOL_CALL_STUCK,
    )

    now = time.time()
    events = [
        {"event_type": "session.started", "ts": _iso(now - 700)},
        {"event_type": "tool.call", "ts": _iso(now - 600),
         "data": {"id": "call_stuck", "name": "bash"}},
        # No tool.result; session.ended also absent. Last event is recent
        # enough that the old classifier would have called this "ongoing".
        {"event_type": "model.completed", "ts": _iso(now - 30),
         "data": {"modelId": "claude-opus-4", "text": "still waiting..."}},
    ]
    outcome, conf = classify_session(events, {}, now=now)
    assert outcome == OUTCOME_TOOL_CALL_STUCK
    assert conf >= 0.7


def test_classify_session_completed_tool_is_not_stuck():
    """Same shape as the stuck-tool test, but with a result event — the
    session should NOT be flagged as tool_call_stuck."""
    from clawmetry.outcome_classifier import (
        classify_session, OUTCOME_TOOL_CALL_STUCK,
    )

    now = time.time()
    events = [
        {"event_type": "session.started", "ts": _iso(now - 700)},
        {"event_type": "tool.call", "ts": _iso(now - 600),
         "data": {"id": "call_done", "name": "bash"}},
        {"event_type": "tool.result", "ts": _iso(now - 590),
         "data": {"tool_call_id": "call_done", "status": "ok"}},
        {"event_type": "model.completed", "ts": _iso(now - 30),
         "data": {"modelId": "claude-opus-4", "text": "done"}},
    ]
    outcome, _ = classify_session(events, {}, now=now)
    assert outcome != OUTCOME_TOOL_CALL_STUCK


def test_classify_session_terminal_session_ended_wins_over_stuck():
    """Once the session emits ``session.ended``, the run is no longer
    in-flight; a tail tool_result-shaped failure should classify cleanly
    as success/failed via the existing rules, not as tool_call_stuck."""
    from clawmetry.outcome_classifier import (
        classify_session, OUTCOME_TOOL_CALL_STUCK,
    )

    now = time.time()
    events = [
        {"event_type": "tool.call", "ts": _iso(now - 600),
         "data": {"id": "call_orphan", "name": "bash"}},
        # Session ended without a matching tool.result. Operator decided
        # to terminate — we don't double-flag this as stuck.
        {"event_type": "session.ended", "ts": _iso(now - 60)},
    ]
    outcome, _ = classify_session(events, {}, now=now)
    assert outcome != OUTCOME_TOOL_CALL_STUCK


def test_aggregate_outcomes_counts_tool_call_stuck_against_success_rate():
    """tool_call_stuck IS counted in the success-rate denominator — a tool
    that never returned is a failure mode the user cares about (matches
    OpenClaw's ``blocked_tool_call`` triage class)."""
    from clawmetry.outcome_classifier import aggregate_outcomes

    rows = (
        [{"outcome": "success"}] * 80
        + [{"outcome": "failed"}] * 15
        + [{"outcome": "tool_call_stuck"}] * 5
    )
    agg = aggregate_outcomes(rows)
    assert agg["total"] == 100
    assert agg["tool_call_stuck"] == 5
    # 80 / (80 + 15 + 5) = 0.80
    assert agg["success_rate"] == 0.8
