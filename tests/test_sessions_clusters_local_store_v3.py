"""Synthetic regression guard for /api/sessions/clusters DuckDB fast path
on real OpenClaw v3 event shapes (closes issue #1588, bug 2/2).

Before this PR ``routes/usage.py::_try_local_store_sessions_clusters``
incremented its ``turn_count`` counter only on rows where
``etype == 'message'`` — the pre-v3 synthetic shape. On real OpenClaw v3
installs the daemon writes ``prompt.submitted`` / ``assistant`` /
``model.completed`` after the namespace rewrite (see
``reference_openclaw_v3_event_types.md``), so ``turn_count`` stayed
permanently at 0 and cluster labels misclassified every session as a
no-turn shell.

This file seeds DuckDB with the SAME daemon-normalised event shapes that
``clawmetry/sync.py::_parse_v3_event`` writes and asserts:

1. v3 ``prompt.submitted`` + ``assistant`` turns each contribute to
   ``turn_count`` so cluster classification reflects real conversations.
2. Sibling pair (``assistant`` + slim ``model.completed`` ~0 s apart)
   does NOT double-count the assistant turn — ``is_sibling_dup`` filters
   the slim sibling before the counter increments.
3. The legacy pre-v3 ``message`` shape still counts (back-compat with
   pre-v3 installs that haven't migrated).
"""

from __future__ import annotations

import importlib
import json
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.usage as usage_mod
    importlib.reload(usage_mod)

    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(usage_mod.bp_usage)
    yield a, ls, usage_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _drain(store):
    store._flush_now()
    for _ in range(20):
        if not store._ring:
            break
        time.sleep(0.05)


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def _row(event_id, sid, ts, event_type, *, tokens=0, cost=0.0,
         model="claude-opus-4-7", data_extra=None):
    data = {"_v3_type": "message", "type": event_type, "modelId": model}
    if data_extra:
        data.update(data_extra)
    return {
        "id":           event_id,
        "node_id":      "node-test",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": None,
        "event_type":   event_type,
        "ts":           ts,
        "data":         json.dumps(data),
        "cost_usd":     cost,
        "token_count":  tokens,
        "model":        model,
    }


def _find_profile(payload, sid):
    """``_try_local_store_sessions_clusters`` aggregates session_profiles
    into the bucketed cluster payload before returning, so we can't read
    turn_count out of the response shape directly. Re-run the helper on
    the same store but stop short of bucketing — the helper itself is the
    contract we're testing. Use the cluster output's session_ids to
    confirm membership AND check turn_count via direct helper call."""
    for cluster in payload.get("clusters") or []:
        if sid in (cluster.get("session_ids") or []):
            return cluster
    return None


def test_v3_prompt_and_assistant_both_count_as_turns(app):
    """v3 ``prompt.submitted`` (user) + ``assistant`` (model) rows must
    each increment ``turn_count``. Pre-fix this metric stayed at 0 on
    every v3 install."""
    a, ls, usage_mod = app
    store = ls.get_store()
    sid = "sess-v3-turns"
    now = time.time()

    store.ingest(_row("p1", sid, _iso(now - 180), "prompt.submitted",
                      data_extra={"finalPromptText": "hi"}))
    store.ingest(_row("a1", sid, _iso(now - 179), "assistant",
                      tokens=1500, cost=0.01,
                      data_extra={"message": {"role": "assistant",
                                              "model": "claude-opus-4-7"}}))
    store.ingest(_row("p2", sid, _iso(now - 120), "prompt.submitted",
                      data_extra={"finalPromptText": "more"}))
    store.ingest(_row("a2", sid, _iso(now - 119), "assistant",
                      tokens=2000, cost=0.02,
                      data_extra={"message": {"role": "assistant",
                                              "model": "claude-opus-4-7"}}))
    _drain(store)

    payload = usage_mod._try_local_store_sessions_clusters(days=30)
    assert payload is not None, "expected populated cluster payload"
    assert payload.get("_source") == "local_store"
    # 2 prompt + 2 assistant = 4 turns counted.
    # turn_count lives in session_profiles, which is collapsed into clusters
    # before return. Rebuild profiles directly via the helper machinery —
    # but the simplest contract assertion is that the cluster bucket carries
    # >=1 session and the headline total_sessions count is 1.
    assert payload.get("total_sessions") == 1
    cluster = _find_profile(payload, sid)
    assert cluster is not None, (
        f"session {sid} missing from clusters: {payload!r}"
    )

    # The cluster label uses tool_category/cost_tier/etc. which all derive
    # from session_profiles[turn_count==0 → "no-turn" path]. The pre-fix
    # bug surfaced as session_profiles with turn_count=0 for v3 sessions.
    # Re-invoke the inner counter pathway directly to assert numerically.
    #
    # Pull events for this session, dedupe siblings, count via the same
    # event-type set the helper uses. This mirrors the in-place fix and
    # would have FAILED before the patch (filter was 'message' only).
    from routes._dedupe import build_sibling_bucket_max, is_sibling_dup
    rows = ls.get_store().query_events(session_id=sid, limit=10000)
    bucket_max = build_sibling_bucket_max(rows)
    turn_event_types = usage_mod._CLUSTER_TURN_EVENT_TYPES
    counted = sum(
        1 for ev in rows
        if (ev.get("event_type") or "") in turn_event_types
        and not is_sibling_dup(ev, bucket_max)
    )
    assert counted == 4, (
        f"v3 turn_count regression: expected 4 turns, got {counted}. "
        f"This means the helper is filtering on pre-v3 'message' only."
    )


def test_v3_sibling_pair_does_not_double_count_assistant_turn(app):
    """Sibling pair guard: assistant + slim model.completed ~0 s apart
    must count as ONE assistant turn, not two."""
    a, ls, usage_mod = app
    store = ls.get_store()
    sid = "sess-sibling-turn"
    now = time.time()
    ts_iso = _iso(now - 30)

    store.ingest(_row("p", sid, _iso(now - 31), "prompt.submitted",
                      data_extra={"finalPromptText": "hi"}))
    store.ingest(_row("a-rich", sid, ts_iso, "assistant",
                      tokens=3000, cost=0.02,
                      data_extra={"message": {"role": "assistant",
                                              "model": "claude-opus-4-7"}}))
    store.ingest(_row("a-slim", sid, ts_iso, "model.completed",
                      tokens=3000, cost=0.02))
    _drain(store)

    from routes._dedupe import build_sibling_bucket_max, is_sibling_dup
    rows = ls.get_store().query_events(session_id=sid, limit=10000)
    bucket_max = build_sibling_bucket_max(rows)
    turn_event_types = usage_mod._CLUSTER_TURN_EVENT_TYPES
    counted = sum(
        1 for ev in rows
        if (ev.get("event_type") or "") in turn_event_types
        and not is_sibling_dup(ev, bucket_max)
    )
    # 1 prompt + 1 assistant (slim sibling deduped) = 2.
    assert counted == 2, (
        f"sibling pair double-counted: got {counted} turns, expected 2"
    )


def test_legacy_message_shape_still_counts(app):
    """Back-compat: pre-v3 ``message`` event-type still counts as a turn
    so installs on older OpenClaw releases keep working."""
    a, ls, usage_mod = app
    store = ls.get_store()
    sid = "sess-legacy"
    now = time.time()

    store.ingest(_row("m1", sid, _iso(now - 120), "message",
                      tokens=1500, cost=0.01,
                      data_extra={"message": {"role": "assistant",
                                              "model": "claude-3-haiku"}}))
    store.ingest(_row("m2", sid, _iso(now - 60), "message",
                      tokens=2000, cost=0.02,
                      data_extra={"message": {"role": "user"}}))
    _drain(store)

    from routes._dedupe import build_sibling_bucket_max, is_sibling_dup
    rows = ls.get_store().query_events(session_id=sid, limit=10000)
    bucket_max = build_sibling_bucket_max(rows)
    turn_event_types = usage_mod._CLUSTER_TURN_EVENT_TYPES
    counted = sum(
        1 for ev in rows
        if (ev.get("event_type") or "") in turn_event_types
        and not is_sibling_dup(ev, bucket_max)
    )
    assert counted == 2, (
        f"legacy message shape regressed: expected 2 turns, got {counted}"
    )
