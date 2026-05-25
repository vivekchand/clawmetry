"""CI guard for #1393: DuckDB fast-paths must return non-zero on v3.

For ~10 wheel releases four high-signal queries
(``query_context_window_peek``, ``query_model_fallbacks``,
``query_recent_read_tool_calls``, ``query_tool_call_invocations``)
silently returned zero rows on real OpenClaw v3 because their predicates
filtered ``event_type='message'`` while v3 emits ``assistant`` /
``subagent:assistant`` / ``model.completed`` / ``tool.call`` /
``tool-result``. Three of the empty surfaces (Context Anatomy, Plugins,
Model Fallbacks) are direct paid-conversion funnels — showing zeros for
months blunted them. The legacy JSONL walker masked the regression in
unit tests because it parsed every shape.

This file is the canary: seed a DuckDB with the SAME event shapes a real
OpenClaw v3 install produces, then assert every events-table fast-path
returns a non-empty meaningful result. If a future PR re-introduces a
``event_type='message'``-only predicate (or any other shape regression),
this test goes red BEFORE we ship a wheel.

Fixture (matches what real OpenClaw v3 writes):
  * 1× ``session_start``
  * 2× ``assistant`` with full Anthropic ``data.message.usage`` envelope
  * 2× ``model.completed`` siblings at SAME ``ts_sec`` as the assistants
    (this is the dedupe regression case from PR #1444)
  * 1× ``subagent:assistant`` — Task tool delegated turn
  * 1× ``tool.call`` — top-level Read invocation
  * 1× ``tool-result`` — tool output event
"""

from __future__ import annotations

import datetime as _dt
import importlib
import time

import pytest


NODE_ID    = "agent+v3-invariants"
SESSION_ID = "ssss1111-2222-3333-4444-555566667777"
WS_ID      = "ws-v3-invariants"
MODEL      = "claude-opus-4-7"
PROVIDER   = "anthropic"

_NOW = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)


def _ts(seconds_ago: int) -> str:
    return (_NOW - _dt.timedelta(seconds=seconds_ago)).isoformat().replace(
        "+00:00", "Z"
    )


def _base(ev_id: str, et: str, seconds_ago: int, *, data: dict,
          model: str | None = None, token_count: int | None = None,
          cost: float | None = None) -> dict:
    """Shared envelope for every fixture event."""
    ev: dict = {
        "id": ev_id, "node_id": NODE_ID, "agent_type": "openclaw",
        "agent_id": "main", "session_id": SESSION_ID, "workspace_id": WS_ID,
        "event_type": et, "ts": _ts(seconds_ago), "data": data,
    }
    if model is not None:
        ev["model"] = model
        ev["provider"] = PROVIDER
    if token_count is not None:
        ev["token_count"] = token_count
    if cost is not None:
        ev["cost_usd"] = cost
    return ev


def _assistant_data(*, model: str, input_t: int, output_t: int,
                    cache_r: int, cache_w: int, cost: float,
                    content_block: dict) -> dict:
    """Anthropic-SDK envelope, identical to what v3 emits for ``assistant``
    host events. ``cache_*_input_tokens`` are the native Anthropic keys (#1394)."""
    return {"message": {
        "role": "assistant", "model": model, "provider": PROVIDER,
        "usage": {
            "input_tokens": input_t, "output_tokens": output_t,
            "cache_read_input_tokens": cache_r,
            "cache_creation_input_tokens": cache_w,
            "total_tokens": input_t + output_t,
            "cost": {"total": cost},
        },
        "content": [{"type": "text", "text": "ok"}, content_block],
    }}


def _model_completed_data(*, input_t: int, output_t: int) -> dict:
    """Slim v3 ``model.completed`` envelope — token totals only, no cache
    split. Emitted by OpenClaw v3 ~100 ms after the ``assistant`` sibling."""
    return {
        "modelId": MODEL, "provider": PROVIDER,
        "promptCache": {"lastCallUsage": {
            "input": input_t, "output": output_t, "total": input_t + output_t,
        }},
    }


def _model_changed_data(*, model: str) -> dict:
    """v3 ``model.changed`` envelope — emitted when agent switches models."""
    return {"modelId": model, "provider": PROVIDER}


def _build_v3_events() -> list[dict]:
    """Mixed v3 transcript.

    Two ``assistant`` events get UNIQUE seconds so dedupe keeps both as
    billable turns; each ``model.completed`` sibling lands at the SAME
    ts_sec as its assistant partner so the dedupe layer can drop the
    slim sibling without losing the rich totals.
    """
    read_use = {
        "type":  "tool_use",
        "name":  "Read",
        "input": {"file_path": "/tmp/v3-fixture.md"},
    }
    bash_use = {
        "type":  "tool_use",
        "name":  "Bash",
        "input": {"cmd": "echo subagent"},
    }
    return [
        # session_start
        _base("ev-session-start", "session_start", 600,
              data={"title": "v3-invariants fixture"}),
        # 1× model.changed — agent selects Opus at session start
        _base("ev-model-changed", "model.changed", 550,
              data=_model_changed_data(model=MODEL), model=MODEL),
        # 2× assistant (different seconds so dedupe keeps both)
        _base("ev-assistant-1", "assistant", 500,
              data=_assistant_data(model=MODEL, input_t=10000, output_t=500,
                                   cache_r=8000, cache_w=200, cost=0.05,
                                   content_block=read_use),
              model=MODEL, token_count=10500, cost=0.05),
        _base("ev-assistant-2", "assistant", 400,
              data=_assistant_data(model=MODEL, input_t=11000, output_t=600,
                                   cache_r=8500, cache_w=250, cost=0.06,
                                   content_block=read_use),
              model=MODEL, token_count=11600, cost=0.06),
        # 2× model.completed siblings at SAME ts_sec as assistant pair
        _base("ev-modelcompleted-1", "model.completed", 500,
              data=_model_completed_data(input_t=10000, output_t=500),
              model=MODEL, token_count=10500, cost=0.05),
        _base("ev-modelcompleted-2", "model.completed", 400,
              data=_model_completed_data(input_t=11000, output_t=600),
              model=MODEL, token_count=11600, cost=0.06),
        # 1× subagent:assistant — Task tool spawned a haiku worker
        _base("ev-subagent-assistant", "subagent:assistant", 350,
              data=_assistant_data(model="claude-haiku-4-5", input_t=2000,
                                   output_t=150, cache_r=1000, cache_w=50,
                                   cost=0.002, content_block=bash_use),
              model="claude-haiku-4-5", token_count=2150, cost=0.002),
        # 1× tool.call — top-level Read invocation. We use the
        # ``tool.call`` event_type form specifically — the iterator
        # helpers in local_store.py lower-case match against
        # {tool.call, toolcall, tool_use}. The SQL predicate also
        # accepts ``tool_call`` (underscore), but the Python iterator
        # currently doesn't — a latent gap kept out of scope here.
        _base("ev-toolcall-read", "tool.call", 300,
              data={"name": "Read",
                    "input": {"file_path": "/tmp/v3-tool-call.md"}}),
        # 1× tool-result — event_type contains a dash like real v3 emits
        _base("ev-toolresult", "tool-result", 290,
              data={"tool": "Read",
                    "result": "# v3-tool-call.md\nhello\n"}),
    ]


EXPECTED_RAW_EVENT_COUNT  = 9
EXPECTED_INPUT_TOKENS_MIN = 21000   # 10000 + 11000 (subagent extras OK)
EXPECTED_OUTPUT_TOKENS_MIN = 1100   # 500 + 600


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh isolated DuckDB seeded with the v3 fixture."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)

    s = ls.get_store()
    for ev in _build_v3_events():
        s.ingest(ev)
    s._flush_now()

    deadline = time.monotonic() + 3.0
    n = 0
    while time.monotonic() < deadline:
        n = s._fetch("SELECT COUNT(*) FROM events", [])[0][0]
        if n >= EXPECTED_RAW_EVENT_COUNT:
            break
        time.sleep(0.02)
    else:
        raise AssertionError(
            f"v3 fixture failed to flush — only {n} rows in events table"
        )

    yield s

    try:
        s.stop(flush=True)
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


# ── The four queries that regressed in #1385/#1386 ───────────────────────


def test_query_context_window_peek_finds_v3_input_tokens(store):
    """Pre-#1385: filtered ``event_type='message'`` only → returned 0 on v3."""
    result = store.query_context_window_peek(scan_sessions=5)
    assert result["input_tokens"] > 0, (
        f"query_context_window_peek returned 0 on v3 fixture (#1385 regression). "
        f"result={result!r}"
    )
    assert result.get("session_id") == SESSION_ID


def test_query_model_fallbacks_walks_v3_assistant_events(store):
    """Fixture has a single model on the parent so ``top_transitions`` may be
    empty, but ``scanned`` must be > 0 — the canary that the v3 predicate
    actually engaged."""
    result = store.query_model_fallbacks(session_limit=10, top=5)
    assert result["scanned"] >= 1, (
        f"query_model_fallbacks scanned 0 sessions on v3 fixture — the "
        f"event_type IN (...) predicate likely regressed. result={result!r}"
    )


def test_query_recent_read_tool_calls_extracts_v3_paths(store):
    """Must yield rows from BOTH the top-level ``tool.call`` event AND the
    assistant content-block ``tool_use`` shapes the v3 fixture emits."""
    rows = store.query_recent_read_tool_calls(limit=100)
    assert len(rows) > 0, "query_recent_read_tool_calls returned 0 rows on v3"
    paths = {r.get("file_path") for r in rows}
    assert "/tmp/v3-tool-call.md" in paths, (
        f"top-level tool.call Read path missing: {paths}"
    )


def test_query_tool_call_invocations_counts_v3_tools(store):
    """Powers /api/plugins. Must yield Read (top-level + assistant content)
    AND Bash (subagent content) from the v3 fixture."""
    rows = store.query_tool_call_invocations(limit=100)
    assert len(rows) > 0, (
        "query_tool_call_invocations returned 0 rows on v3 (#1385 regression "
        "for the Plugins paid-conversion surface)."
    )
    names = {(r.get("name") or "").lower() for r in rows}
    assert "read" in names, f"Read missing from tool-invocation names: {names}"
    assert "bash" in names, f"Bash missing from tool-invocation names: {names}"


# ── Broader events-table fast-paths (same bug class) ─────────────────────


def test_query_aggregates_sums_v3_tokens_and_cost(store):
    """Powers /api/usage. Must report non-zero totals after dedupe drops the
    model.completed siblings without zeroing the assistant rows (PR #1444 /
    #1464)."""
    days = store.query_aggregates()
    assert days, "query_aggregates returned no day rows on v3 fixture"
    total_tokens = sum(int(d.get("token_count") or 0) for d in days)
    total_cost   = sum(float(d.get("cost_usd") or 0.0) for d in days)
    assert total_tokens > 0, f"query_aggregates aggregated 0 tokens (#1444). days={days!r}"
    assert total_cost > 0, f"query_aggregates aggregated 0 cost. days={days!r}"


def test_query_daily_usage_splits_breaks_down_v3_tokens(store):
    """Powers the Tokens-tab daily chart on v3. Legacy fast-path returned all
    0s here (#1394)."""
    days = store.query_daily_usage_splits()
    assert days, "query_daily_usage_splits returned no day rows on v3 fixture"
    input_total  = sum(int(d.get("input_tokens") or 0) for d in days)
    output_total = sum(int(d.get("output_tokens") or 0) for d in days)
    assert input_total >= EXPECTED_INPUT_TOKENS_MIN, (
        f"input_tokens too low: got {input_total}, expected >= "
        f"{EXPECTED_INPUT_TOKENS_MIN}. days={days!r}"
    )
    assert output_total >= EXPECTED_OUTPUT_TOKENS_MIN, (
        f"output_tokens too low: got {output_total}, expected >= "
        f"{EXPECTED_OUTPUT_TOKENS_MIN}. days={days!r}"
    )


def test_query_sessions_lists_v3_session_with_nonzero_totals(store):
    """Drives /api/sessions. Dedupe SQL from #1460 must not zero out totals."""
    rows = store.query_sessions(limit=10)
    sessions = [r for r in rows if r.get("session_id") == SESSION_ID]
    assert sessions, (
        f"v3 session {SESSION_ID!r} missing from query_sessions: "
        f"{[r.get('session_id') for r in rows]}"
    )
    sess = sessions[0]
    assert int(sess.get("token_count") or 0) > 0, (
        f"query_sessions token_count zeroed out on v3: {sess!r}"
    )
    assert float(sess.get("cost_usd") or 0) > 0, (
        f"query_sessions cost_usd zeroed out on v3: {sess!r}"
    )


def test_query_events_returns_full_v3_transcript(store):
    """Raw read — must return every event regardless of event_type shape."""
    rows = store.query_events(session_id=SESSION_ID, limit=100)
    assert len(rows) == EXPECTED_RAW_EVENT_COUNT, (
        f"query_events returned {len(rows)}, expected {EXPECTED_RAW_EVENT_COUNT}"
    )
    types = {r.get("event_type") for r in rows}
    for required in (
        "assistant", "model.completed", "subagent:assistant",
        "tool.call", "tool-result", "session_start",
    ):
        assert required in types, (
            f"v3 event_type {required!r} missing from query_events: {types}"
        )


def test_query_session_model_journey_returns_v3_model_completed_rows(store):
    """Pre-fix: only ``message`` was in the IN-clause so ``model.completed``
    events were invisible — the journey returned [] for every v3 session."""
    rows = store.query_session_model_journey(session_id=SESSION_ID)
    assert rows, (
        "query_session_model_journey returned [] for v3 session — "
        "model.completed event_type is missing from the IN-clause predicate"
    )
    total = sum(int(r.get("total_tokens") or 0) for r in rows if r.get("kind") == "message")
    assert total > 0, (
        f"query_session_model_journey summed 0 total_tokens on v3 fixture; "
        f"typed cost_usd/token_count columns not being read. rows={rows!r}"
    )


def test_query_session_model_journey_tracks_v3_model_change(store):
    """``model.changed`` events must produce ``kind='model_change'`` rows so
    segment boundaries are computed for v3 sessions that switch models."""
    rows = store.query_session_model_journey(session_id=SESSION_ID)
    change_rows = [r for r in rows if r.get("kind") == "model_change"]
    assert change_rows, (
        f"query_session_model_journey returned no model_change rows from "
        f"v3 model.changed event. all rows: {rows!r}"
    )
    assert any(r.get("model") == MODEL for r in change_rows), (
        f"model_change row missing expected model {MODEL!r}: {change_rows!r}"
    )
