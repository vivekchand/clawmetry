"""Class-bug drain: parent_sid blindness across 6 per-session reads (refs #1597).

PR #1611 fixed ``_try_local_store_session_tools`` by adding the
``query_events_with_subagents`` helper that UNIONs the parent's events
with every child sub-agent session's events. The same class bug existed
on 8 sibling per-session read paths; this test pins down the rollup
behaviour for the 6 sites we fixed in the class-bug drain PR and the 2
sites that legitimately stay per-session-only.

The 6 fixed sites
=================
1. ``routes/sessions.py:_try_local_store_transcript_events`` —
   /api/transcript-events/<id> — transcript modal events.
2. ``routes/sessions.py:_try_local_store_session_export`` —
   /api/sessions/<id>/export — JSON export.
3. ``routes/sessions.py:_try_local_store_session_cost_breakdown`` —
   /api/sessions/<id>/cost-breakdown — per-turn cost+token breakdown.
4. ``routes/crons.py:_try_local_store_cron_run_log`` —
   /api/cron-run-log — cron run-log modal.
5. ``routes/sessions.py:_try_local_store_cost_split`` (wanted_sid mode) —
   /api/cost-split?session=<id> — per-session token + cost split.
6. ``routes/sessions.py:_try_local_store_session_model_journey`` —
   /api/session-model-journey/<id> — ordered model + message events.

The 2 per-session-only sites (no rollup)
========================================
* ``routes/brain.py:_fetch_session_chain`` — /api/llm-call-timeline/<event_id>:
  walks back from an anchor to the nearest preceding ``prompt.submitted``
  in the SAME LLM call; rolling parent+child would mix two unrelated
  call chains. Test enforces no-rollup so the timeline can't regress.
* ``clawmetry/local_store.py::query_context_window_peek`` — context-anatomy
  gauge for the LIVE prompt context of one conversation. A child has its
  own context window; rolling would surface the child's most-recent
  context as the parent's.

All 8 sites are exercised end-to-end so a future refactor that
re-introduces the parent_sid blindness on a "fixed" site OR adds rollup
to a "no-rollup" site flips this test red.
"""

from __future__ import annotations

import importlib
import json
import time

import pytest
from flask import Flask


# ─── Fixture ──────────────────────────────────────────────────────────────


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Spin up a Flask app with fresh routes/sessions, routes/crons,
    routes/brain blueprints rooted at a tmp_path DuckDB.

    Matches the isolation pattern from ``test_subagent_attribution_v3.py``:
    sets CLAWMETRY_LOCAL_STORE_PATH, reloads the store + routes, and
    monkey-patches ``_read_discovery`` so the test never proxies to a
    contributor's running daemon."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import routes.crons as crons_mod
    importlib.reload(crons_mod)
    import routes.brain as brain_mod
    importlib.reload(brain_mod)

    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    a.register_blueprint(crons_mod.bp_crons)
    a.register_blueprint(brain_mod.bp_brain)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _drain(store):
    store._flush_now()
    for _ in range(10):
        if not store._ring:
            break
        time.sleep(0.05)


def _row(event_id, sid, event_type, ts, data, **extra):
    base = {
        "id":           event_id,
        "node_id":      "node-test",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": None,
        "event_type":   event_type,
        "ts":           ts,
        "data":         json.dumps(data),
    }
    base.update(extra)
    return base


def _seed_assistant_turn(store, *, event_id, sid, ts, model, in_tok, out_tok,
                         cr_tok=0, cw_tok=0, cost_input=0.0, cost_output=0.0,
                         cost_cr=0.0, cost_cw=0.0):
    """Emit a v3-shape assistant turn carrying a full Anthropic-SDK envelope
    so the cost/breakdown helpers all parse usage cleanly."""
    cost_total = cost_input + cost_output + cost_cr + cost_cw
    store.ingest(_row(
        event_id, sid, "message", ts,
        {
            "_v3_type": "message", "type": "message",
            "message": {
                "role":  "assistant",
                "model": model,
                "content": [{"type": "text", "text": "ok"}],
                "usage": {
                    "input":      in_tok,
                    "output":     out_tok,
                    "cacheRead":  cr_tok,
                    "cacheWrite": cw_tok,
                    "totalTokens": in_tok + out_tok + cr_tok + cw_tok,
                    "cost": {
                        "input":      cost_input,
                        "output":     cost_output,
                        "cacheRead":  cost_cr,
                        "cacheWrite": cost_cw,
                        "total":      cost_total,
                    },
                },
            },
        },
        model=model, cost_usd=cost_total, token_count=in_tok + out_tok,
    ))


def _seed_model_change(store, *, event_id, sid, ts, model, provider="anthropic"):
    store.ingest(_row(
        event_id, sid, "model_change", ts,
        {"_v3_type": "model_change", "type": "model_change",
         "modelId": model, "provider": provider},
        model=model,
    ))


def _link_subagent(store, *, child_sid, parent_sid, spawned_at, task="work"):
    store.ingest_subagent({
        "subagent_id":       child_sid,
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        spawned_at,
        "task":              task,
        "status":            "active",
    })


# ────────────────────────────────────────────────────────────────────────────
# Site 1: /api/transcript-events/<id> — _try_local_store_transcript_events.
# A parent with 0 direct + 2 sub-agent message events must show 2 events
# in the transcript modal (and the child events must be tagged).
# ────────────────────────────────────────────────────────────────────────────
def test_site1_transcript_events_rolls_up_subagent_messages(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "s1-parent"
    child_sid = "s1-child"

    store.ingest(_row(
        "s1-p0", parent_sid, "session.started", "2026-05-17T10:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    _link_subagent(store, child_sid=child_sid, parent_sid=parent_sid,
                   spawned_at="2026-05-17T10:00:01Z", task="research")
    _seed_assistant_turn(store, event_id="s1-c1", sid=child_sid,
                         ts="2026-05-17T10:00:02Z", model="claude-opus-4-7",
                         in_tok=100, out_tok=50, cost_input=0.001,
                         cost_output=0.002)
    _seed_assistant_turn(store, event_id="s1-c2", sid=child_sid,
                         ts="2026-05-17T10:01:02Z", model="claude-haiku-4-7",
                         in_tok=200, out_tok=80, cost_input=0.0005,
                         cost_output=0.001)
    _drain(store)

    r = a.test_client().get(f"/api/transcript-events/{parent_sid}")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store"
    # 2 child message events should now appear in the parent's transcript.
    assert body["messageCount"] == 2, (
        f"parent transcript must include 2 sub-agent messages; "
        f"got messageCount={body['messageCount']!r}"
    )


# ────────────────────────────────────────────────────────────────────────────
# Site 2: /api/sessions/<id>/export — _try_local_store_session_export.
# A parent with 0 direct messages + 3 sub-agent assistant turns must export
# 3 messages and a non-zero cost_data.total_cost_usd.
# ────────────────────────────────────────────────────────────────────────────
def test_site2_session_export_rolls_up_subagent_cost(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "s2-parent"
    child_sid = "s2-child"

    store.ingest(_row(
        "s2-p0", parent_sid, "session.started", "2026-05-17T11:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    _link_subagent(store, child_sid=child_sid, parent_sid=parent_sid,
                   spawned_at="2026-05-17T11:00:01Z")
    for i in range(3):
        _seed_assistant_turn(store, event_id=f"s2-c{i}", sid=child_sid,
                             ts=f"2026-05-17T11:0{i+1}:00Z",
                             model="claude-opus-4-7",
                             in_tok=500, out_tok=200,
                             cost_input=0.005, cost_output=0.003)
    _drain(store)

    r = a.test_client().get(f"/api/sessions/{parent_sid}/export")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"export must hit local_store fast path; body keys={list(body.keys())!r}"
    )
    assert len(body["messages"]) == 3, (
        f"export must include 3 sub-agent messages; got {len(body['messages'])}"
    )
    # 3 turns * (0.005 + 0.003) = 0.024 USD.
    assert body["cost_data"]["total_cost_usd"] > 0.02, (
        f"export cost must include sub-agent spend; "
        f"got total_cost_usd={body['cost_data']['total_cost_usd']!r}"
    )


# ────────────────────────────────────────────────────────────────────────────
# Site 3: /api/sessions/<id>/cost-breakdown —
# _try_local_store_session_cost_breakdown. A parent with 0 direct turns +
# 4 sub-agent turns must report 4 turns and the correct token totals.
# ────────────────────────────────────────────────────────────────────────────
def test_site3_cost_breakdown_rolls_up_subagent_turns(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "s3-parent"
    child_sid = "s3-child"

    store.ingest(_row(
        "s3-p0", parent_sid, "session.started", "2026-05-17T12:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    _link_subagent(store, child_sid=child_sid, parent_sid=parent_sid,
                   spawned_at="2026-05-17T12:00:01Z")
    for i in range(4):
        _seed_assistant_turn(store, event_id=f"s3-c{i}", sid=child_sid,
                             ts=f"2026-05-17T12:0{i+1}:00Z",
                             model="claude-opus-4-7",
                             in_tok=1000, out_tok=400, cr_tok=200,
                             cost_input=0.01, cost_output=0.006,
                             cost_cr=0.001)
    _drain(store)

    r = a.test_client().get(f"/api/sessions/{parent_sid}/cost-breakdown")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("turn_count") == 4, (
        f"parent cost breakdown must include 4 sub-agent turns; "
        f"got turn_count={body.get('turn_count')!r}"
    )
    # 4 turns * 1000 input each = 4000.
    assert body["totals"]["input_tokens"] == 4000
    assert body["totals"]["output_tokens"] == 1600
    assert body["totals"]["cache_read_tokens"] == 800


# ────────────────────────────────────────────────────────────────────────────
# Site 4: /api/cron-run-log — _try_local_store_cron_run_log.
# A cron run that delegated to a sub-agent must show the sub-agent's
# messages, not return an empty events list.
# ────────────────────────────────────────────────────────────────────────────
def test_site4_cron_run_log_rolls_up_subagent_messages(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "s4-cron-run"
    child_sid = "s4-child"

    store.ingest(_row(
        "s4-p0", parent_sid, "session.started", "2026-05-17T13:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    _link_subagent(store, child_sid=child_sid, parent_sid=parent_sid,
                   spawned_at="2026-05-17T13:00:01Z", task="nightly cleanup")
    # 2 child messages.
    _seed_assistant_turn(store, event_id="s4-c1", sid=child_sid,
                         ts="2026-05-17T13:00:02Z", model="claude-opus-4-7",
                         in_tok=50, out_tok=20)
    _seed_assistant_turn(store, event_id="s4-c2", sid=child_sid,
                         ts="2026-05-17T13:00:05Z", model="claude-opus-4-7",
                         in_tok=60, out_tok=15)
    _drain(store)

    r = a.test_client().get(f"/api/cron-run-log?session_id={parent_sid}")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert len(body["events"]) == 2, (
        f"cron run-log must include 2 sub-agent messages; "
        f"got {len(body['events'])} events"
    )


# ────────────────────────────────────────────────────────────────────────────
# Site 5: /api/cost-split?session=<id> — _try_local_store_cost_split
# (wanted_sid branch). A parent with 0 direct + sub-agent cost must return
# at least one ``sessions`` row with non-zero total_cost_usd attributable to
# the child via ``_via_subagent_id``.
# ────────────────────────────────────────────────────────────────────────────
def test_site5_cost_split_rolls_up_subagent_sessions(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "s5-parent"
    child_sid = "s5-child"

    store.ingest(_row(
        "s5-p0", parent_sid, "session.started", "2026-05-17T14:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    _link_subagent(store, child_sid=child_sid, parent_sid=parent_sid,
                   spawned_at="2026-05-17T14:00:01Z")
    _seed_assistant_turn(store, event_id="s5-c1", sid=child_sid,
                         ts="2026-05-17T14:00:02Z", model="claude-opus-4-7",
                         in_tok=1000, out_tok=400,
                         cost_input=0.01, cost_output=0.006)
    _drain(store)

    r = a.test_client().get(f"/api/cost-split?session_id={parent_sid}")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store"
    sess = body["sessions"]
    # The single child row should be returned as the sole session entry,
    # tagged with _via_subagent_id pointing at the child.
    child_rows = [s for s in sess if s.get("_via_subagent_id") == child_sid]
    assert child_rows, (
        f"cost-split must surface a sub-agent row tagged with _via_subagent_id; "
        f"got sessions={sess!r}"
    )
    assert child_rows[0]["total_cost_usd"] > 0.0


# ────────────────────────────────────────────────────────────────────────────
# Site 6: /api/session-model-journey/<id> —
# _try_local_store_session_model_journey. A parent that ran model A then
# delegated to a child running model B must show BOTH models in the
# journey segments — not just A.
# ────────────────────────────────────────────────────────────────────────────
def test_site6_model_journey_rolls_up_subagent_models(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "s6-parent"
    child_sid = "s6-child"

    # Parent: one direct assistant turn on Opus.
    store.ingest(_row(
        "s6-p0", parent_sid, "session.started", "2026-05-17T15:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    _seed_model_change(store, event_id="s6-pmc", sid=parent_sid,
                       ts="2026-05-17T15:00:01Z", model="claude-opus-4-7")
    _seed_assistant_turn(store, event_id="s6-p1", sid=parent_sid,
                         ts="2026-05-17T15:00:02Z", model="claude-opus-4-7",
                         in_tok=100, out_tok=50,
                         cost_input=0.001, cost_output=0.002)
    # Sub-agent: Haiku worker.
    _link_subagent(store, child_sid=child_sid, parent_sid=parent_sid,
                   spawned_at="2026-05-17T15:00:03Z")
    _seed_model_change(store, event_id="s6-cmc", sid=child_sid,
                       ts="2026-05-17T15:00:04Z", model="claude-haiku-4-7")
    _seed_assistant_turn(store, event_id="s6-c1", sid=child_sid,
                         ts="2026-05-17T15:00:05Z", model="claude-haiku-4-7",
                         in_tok=200, out_tok=80,
                         cost_input=0.0005, cost_output=0.0008)
    _drain(store)

    r = a.test_client().get(f"/api/session-model-journey/{parent_sid}")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    models_used = {s.get("modelId") for s in body.get("segments", [])}
    assert "claude-opus-4-7" in models_used and "claude-haiku-4-7" in models_used, (
        f"model journey must include parent Opus AND child Haiku; "
        f"got models_used={models_used!r}"
    )


# ────────────────────────────────────────────────────────────────────────────
# Cross-cutting guard A: CHILD view never bleeds the parent's events.
# Hitting any per-session endpoint with a child's session_id must NOT pull
# the parent's events in via reverse rollup. Validates the one-directional
# walk (parent → children, never children → parent).
# ────────────────────────────────────────────────────────────────────────────
def test_child_view_never_bleeds_parent_events(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "guardA-parent"
    child_sid = "guardA-child"

    # Parent: 5 direct assistant turns (the value we'd see if rollup
    # accidentally walked children → parent).
    store.ingest(_row(
        "ga-p0", parent_sid, "session.started", "2026-05-17T16:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    for i in range(5):
        _seed_assistant_turn(store, event_id=f"ga-p{i+1}", sid=parent_sid,
                             ts=f"2026-05-17T16:0{i+1}:00Z",
                             model="claude-opus-4-7",
                             in_tok=999, out_tok=111)
    # Child: 1 direct turn, registered as parent's sub-agent.
    _link_subagent(store, child_sid=child_sid, parent_sid=parent_sid,
                   spawned_at="2026-05-17T16:10:00Z")
    store.ingest(_row(
        "ga-c0", child_sid, "session.started", "2026-05-17T16:10:00Z",
        {"_v3_type": "session", "type": "session.started", "id": child_sid},
    ))
    _seed_assistant_turn(store, event_id="ga-c1", sid=child_sid,
                         ts="2026-05-17T16:10:01Z", model="claude-haiku-4-7",
                         in_tok=10, out_tok=5)
    _drain(store)

    # Hitting the CHILD's session_id on /api/sessions/<id>/cost-breakdown
    # must report 1 turn, not 6.
    r = a.test_client().get(f"/api/sessions/{child_sid}/cost-breakdown")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("turn_count") == 1, (
        f"child cost breakdown must NOT pull in parent's 5 turns "
        f"(one-directional walk only); got turn_count={body.get('turn_count')!r}"
    )


# ────────────────────────────────────────────────────────────────────────────
# Cross-cutting guard B: orphan tool calls must NOT leak into an
# unrelated parent's rollup. An "orphan" is a session that has no row in
# the subagents table — typical of pre-#1611 ingest paths that wrote
# events but not subagent rollups.
# ────────────────────────────────────────────────────────────────────────────
def test_orphan_session_never_leaks_into_unrelated_parent(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "guardB-parent"
    orphan_sid = "guardB-orphan-no-link"

    # Parent: 1 direct turn.
    store.ingest(_row(
        "gb-p0", parent_sid, "session.started", "2026-05-17T17:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    _seed_assistant_turn(store, event_id="gb-p1", sid=parent_sid,
                         ts="2026-05-17T17:00:01Z", model="claude-opus-4-7",
                         in_tok=100, out_tok=50,
                         cost_input=0.001, cost_output=0.002)
    # Orphan: 10 turns, NO ingest_subagent linkage.
    store.ingest(_row(
        "gb-o0", orphan_sid, "session.started", "2026-05-17T17:01:00Z",
        {"_v3_type": "session", "type": "session.started", "id": orphan_sid},
    ))
    for i in range(10):
        _seed_assistant_turn(store, event_id=f"gb-o{i+1}", sid=orphan_sid,
                             ts=f"2026-05-17T17:01:{i:02d}Z",
                             model="claude-opus-4-7",
                             in_tok=9999, out_tok=9999)
    _drain(store)

    r = a.test_client().get(f"/api/sessions/{parent_sid}/cost-breakdown")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("turn_count") == 1, (
        f"parent rollup must NOT include orphan session's 10 turns; "
        f"got turn_count={body.get('turn_count')!r}"
    )
    # And the totals match the parent's single turn only.
    assert body["totals"]["input_tokens"] == 100, (
        f"orphan turns must not pollute parent totals; "
        f"got input_tokens={body['totals']['input_tokens']!r}"
    )


# ────────────────────────────────────────────────────────────────────────────
# Site 7 (no-rollup): brain.py::_fetch_session_chain must STAY per-session.
# /api/llm-call-timeline/<event_id>?session_id=<child> must succeed without
# the parent's events polluting the chain walk. Conversely, looking up an
# event_id that only exists in a child while passing the parent's
# session_id must NOT silently find it via reverse rollup.
# ────────────────────────────────────────────────────────────────────────────
def test_site7_llm_call_timeline_stays_per_session_no_rollup(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "s7-parent"
    child_sid = "s7-child"

    # Parent: prompt.submitted + model.completed pair on Opus.
    store.ingest(_row(
        "s7-pp", parent_sid, "prompt.submitted", "2026-05-17T18:00:00Z",
        {"_v3_type": "user", "type": "prompt.submitted",
         "finalPromptText": "parent prompt"},
    ))
    store.ingest(_row(
        "s7-pm", parent_sid, "model.completed", "2026-05-17T18:00:01Z",
        {"_v3_type": "message", "type": "model.completed",
         "modelId": "claude-opus-4-7", "provider": "anthropic"},
        model="claude-opus-4-7",
    ))
    # Child: prompt.submitted + model.completed pair on Haiku.
    _link_subagent(store, child_sid=child_sid, parent_sid=parent_sid,
                   spawned_at="2026-05-17T18:01:00Z")
    store.ingest(_row(
        "s7-cp", child_sid, "prompt.submitted", "2026-05-17T18:01:01Z",
        {"_v3_type": "user", "type": "prompt.submitted",
         "finalPromptText": "child prompt"},
    ))
    store.ingest(_row(
        "s7-cm", child_sid, "model.completed", "2026-05-17T18:01:02Z",
        {"_v3_type": "message", "type": "model.completed",
         "modelId": "claude-haiku-4-7", "provider": "anthropic"},
        model="claude-haiku-4-7",
    ))
    _drain(store)

    # Asking for the CHILD's call timeline with the CHILD's session_id
    # must succeed. (Validates the no-rollup design — when the UI passes
    # the row's own session_id, the lookup works without help.)
    r = a.test_client().get(
        f"/api/llm-call-timeline/s7-cm?session_id={child_sid}"
    )
    assert r.status_code == 200, r.get_data(as_text=True)

    # Asking for the CHILD's call timeline with the PARENT's session_id
    # must FAIL ("event not found in session"). If a future refactor
    # accidentally adds query_events_with_subagents to _fetch_session_chain,
    # this call would silently succeed by walking children — masking the
    # cross-session bug. The 404 keeps the per-session contract honest.
    r = a.test_client().get(
        f"/api/llm-call-timeline/s7-cm?session_id={parent_sid}"
    )
    assert r.status_code == 404, (
        f"parent-session lookup must NOT pull a child event in via rollup; "
        f"got status={r.status_code} body={r.get_data(as_text=True)!r}"
    )


# ────────────────────────────────────────────────────────────────────────────
# Site 8 (no-rollup): query_context_window_peek must NOT roll children into
# the latest active session's context window. The gauge represents the
# live prompt for one conversation; a child has its own context. Test
# directly against the LocalStore method since the route reads /api/
# context-anatomy through a thicker stack.
# ────────────────────────────────────────────────────────────────────────────
def test_site8_context_window_peek_stays_per_session_no_rollup(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "s8-parent"
    child_sid = "s8-child"

    # Parent: latest activity, input_tokens=12345 (the value the gauge
    # should report).
    store.ingest(_row(
        "s8-p0", parent_sid, "session.started", "2026-05-17T19:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    store.ingest(_row(
        "s8-p1", parent_sid, "message", "2026-05-17T19:00:01Z",
        {"_v3_type": "message", "type": "message",
         "message": {
            "role": "assistant", "model": "claude-opus-4-7",
            "usage": {"input": 12345, "output": 100},
        }},
        model="claude-opus-4-7",
    ))
    # Child: latest activity is LATER than parent's, with a DIFFERENT
    # input_tokens (99999). If rollup leaks in, the gauge would report
    # 99999 — the child's context, not the parent's.
    _link_subagent(store, child_sid=child_sid, parent_sid=parent_sid,
                   spawned_at="2026-05-17T19:00:10Z")
    store.ingest(_row(
        "s8-c1", child_sid, "message", "2026-05-17T19:00:11Z",
        {"_v3_type": "message", "type": "message",
         "message": {
            "role": "assistant", "model": "claude-haiku-4-7",
            "usage": {"input": 99999, "output": 100},
        }},
        model="claude-haiku-4-7",
    ))
    _drain(store)

    # The peek scans the most-recent N active sessions; the child wins
    # the "latest" ordering on its own merits. That's expected — the
    # gauge picks the latest conversation, period. What we're guarding
    # against is collapsing parent + child into a single per-session
    # walk that returns one merged blob: each session's input_tokens
    # must remain attributed to its OWN session_id.
    peek = store.query_context_window_peek(scan_sessions=10)
    assert peek["input_tokens"] in (12345, 99999), (
        f"peek must return one session's own input_tokens, not a sum; "
        f"got {peek['input_tokens']!r}"
    )
    # Whichever session wins, its OWN session_id must come back — not a
    # collapsed "parent" sid for a value that came from the child.
    if peek["input_tokens"] == 12345:
        assert peek["session_id"] == parent_sid
    else:
        assert peek["session_id"] == child_sid, (
            f"peek must attribute the 99999 reading to the child's sid; "
            f"got session_id={peek['session_id']!r}"
        )
