"""Realistic fixture seeder for the MOAT fast-path perf suite.

Seeds an isolated DuckDB store with v3-shaped events at a scale
representative of a mid-volume install. The shapes match
``tests/test_duckdb_fastpath_v3_invariants.py`` (the canary that pins
real OpenClaw v3 event keys) so the perf numbers reflect actual SQL
predicate cost — not a synthetic shape that bypasses the v3 dedupe path.

Default scale (smaller than the spec's 1000 sessions / 50k events):
  100 sessions × 14 days × 5k events × 200 subagents × 60 channel msgs.

Rationale for the smaller-than-spec fixture: the 15-min wall-clock budget
on this PR doesn't let us seed 50k events (~30s alone on DuckDB single-row
inserts) and still run 14 endpoints × 5 iterations of fast-path + legacy
walkers. The 5k-event corpus is documented as the trade-off in the PR
body (per ``feedback_synthetic_tests_missed_real_event_shape.md`` we still
ship a realistic shape — just less of it). Refresh the baseline whenever
the scale is bumped.
"""
from __future__ import annotations

import datetime as _dt
import importlib
import time

# Tunables — kept tiny enough to flush in <2s, big enough to register on
# perf_counter for fast-path SQL (~ms scale) and legacy walkers (~10ms+).
SESSION_COUNT       = 100
EVENTS_PER_SESSION  = 50          # 100 × 50 = 5_000 events
SUBAGENT_COUNT      = 200
CHANNEL_MSG_COUNT   = 60          # per provider; we seed telegram + signal
DAYS_BACK           = 14

PROVIDER       = "anthropic"
MODELS         = ("claude-opus-4-7", "claude-sonnet-4-5", "claude-haiku-4-5")
NODE_ID        = "agent+moat-perf"
WORKSPACE_ID   = "ws-moat-perf"

_NOW = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)


def _ts(seconds_ago: float) -> str:
    return (_NOW - _dt.timedelta(seconds=seconds_ago)).isoformat().replace(
        "+00:00", "Z"
    )


def _ts_ms(seconds_ago: float) -> int:
    return int((_NOW - _dt.timedelta(seconds=seconds_ago)).timestamp() * 1000)


def _session_id(idx: int) -> str:
    return f"perf-sess-{idx:04d}-aaaa-bbbb-cccc-dddddddddddd"


def _assistant_data(model: str, in_tok: int, out_tok: int, cost: float,
                    *, tool_name: str | None = None) -> dict:
    content = [{"type": "text", "text": "ok"}]
    if tool_name:
        content.append({
            "type":  "tool_use",
            "name":  tool_name,
            "input": {"file_path": f"/tmp/{tool_name.lower()}.md"},
        })
    return {"message": {
        "role": "assistant", "model": model, "provider": PROVIDER,
        "usage": {
            "input_tokens": in_tok, "output_tokens": out_tok,
            "cache_read_input_tokens": in_tok // 3,
            "cache_creation_input_tokens": in_tok // 20,
            "total_tokens": in_tok + out_tok,
            "cost": {"total": cost},
        },
        "content": content,
    }}


def _model_completed_data(in_tok: int, out_tok: int, model: str) -> dict:
    return {
        "modelId": model, "provider": PROVIDER,
        "promptCache": {"lastCallUsage": {
            "input": in_tok, "output": out_tok, "total": in_tok + out_tok,
        }},
    }


def _build_session_events(sess_idx: int) -> list[dict]:
    """One session's worth of v3-shaped events (~EVENTS_PER_SESSION rows)."""
    sid = _session_id(sess_idx)
    model = MODELS[sess_idx % len(MODELS)]
    # Spread the session across the 14-day window — sessions near sess_idx=0
    # are newest, sess_idx=SESSION_COUNT-1 is at the back of the window.
    base_seconds_ago = int(
        (sess_idx / SESSION_COUNT) * DAYS_BACK * 86400
    ) + 60

    events: list[dict] = [{
        "id":           f"ev-sess-start-{sess_idx}",
        "node_id":      NODE_ID,
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": WORKSPACE_ID,
        "event_type":   "session_start",
        "ts":           _ts(base_seconds_ago),
        "data":         {"title": f"perf session {sess_idx}"},
    }]

    # Alternate assistant + model.completed sibling pairs + occasional
    # tool.call / model.changed / user prompt. Per-pair token budget keeps
    # /api/usage / /api/token-velocity aggregates non-trivial.
    pair_count = EVENTS_PER_SESSION // 4
    for pair in range(pair_count):
        secs = base_seconds_ago - pair * 5
        in_tok = 1000 + (pair * 50) % 4000
        out_tok = 100 + (pair * 7) % 400
        cost = (in_tok + out_tok) * 1e-6
        tool_name = ("Read", "Bash", "Edit", None)[pair % 4]

        events.append({
            "id": f"ev-asst-{sess_idx}-{pair}", "node_id": NODE_ID,
            "agent_type": "openclaw", "agent_id": "main",
            "session_id": sid, "workspace_id": WORKSPACE_ID,
            "event_type": "assistant", "ts": _ts(secs),
            "model": model, "provider": PROVIDER,
            "token_count": in_tok + out_tok, "cost_usd": cost,
            "data": _assistant_data(model, in_tok, out_tok, cost,
                                    tool_name=tool_name),
        })
        # Sibling at SAME ts_sec — dedupe path must keep one and drop one.
        events.append({
            "id": f"ev-mc-{sess_idx}-{pair}", "node_id": NODE_ID,
            "agent_type": "openclaw", "agent_id": "main",
            "session_id": sid, "workspace_id": WORKSPACE_ID,
            "event_type": "model.completed", "ts": _ts(secs),
            "model": model, "provider": PROVIDER,
            "token_count": in_tok + out_tok, "cost_usd": cost,
            "data": _model_completed_data(in_tok, out_tok, model),
        })

        # Inject a tool.call every few pairs (drives /api/component/gateway,
        # /api/flow-events, /api/automation-analysis).
        if pair % 3 == 0:
            events.append({
                "id": f"ev-tc-{sess_idx}-{pair}", "node_id": NODE_ID,
                "agent_type": "openclaw", "agent_id": "main",
                "session_id": sid, "workspace_id": WORKSPACE_ID,
                "event_type": "tool.call", "ts": _ts(secs - 1),
                "data": {"name": tool_name or "Read",
                         "input": {"file_path": f"/tmp/perf-{pair}.md"}},
            })

        # Inject a model.changed every 5 pairs — drives /api/sessions/<sid>/model-transitions.
        if pair % 5 == 4 and pair_count > pair + 1:
            next_model = MODELS[(sess_idx + pair) % len(MODELS)]
            events.append({
                "id": f"ev-mch-{sess_idx}-{pair}", "node_id": NODE_ID,
                "agent_type": "openclaw", "agent_id": "main",
                "session_id": sid, "workspace_id": WORKSPACE_ID,
                "event_type": "model.changed", "ts": _ts(secs - 2),
                "data": {"modelId": next_model, "provider": PROVIDER,
                         "from_model": model, "to_model": next_model},
            })

    return events


def _build_subagents() -> list[dict]:
    """200 subagent rows spread over a few parent sessions."""
    rows = []
    statuses = ("active", "completed", "failed", "idle")
    for i in range(SUBAGENT_COUNT):
        parent_idx = i % 25                    # 25 parents × 8 children
        rows.append({
            "subagent_id":       f"perf-sub-{i:04d}",
            "agent_type":        "openclaw",
            "parent_session_id": _session_id(parent_idx),
            "spawned_at":        _ts(i * 30),
            "task":              f"perf subtask {i}",
            "status":            statuses[i % len(statuses)],
            "cost_usd":          0.001 * (i + 1),
            "token_count":       100 + i * 5,
            "model":             MODELS[i % len(MODELS)],
            "label":             f"perf-{i}",
            "displayName":       f"perf-{i}",
            "runtime_ms":        5000 + i * 100,
            "updated_at_ms":     _ts_ms(i * 10),
        })
    return rows


def _build_channel_events(provider: str) -> list[dict]:
    """60 channel events per provider (telegram + signal)."""
    out = []
    for i in range(CHANNEL_MSG_COUNT):
        secs = i * 60                                # 1 per minute
        out.append({
            "id":         f"ev-chevt-{provider}-{i}",
            "node_id":    NODE_ID,
            "agent_type": "openclaw",
            "agent_id":   "main",
            "session_id": _session_id(i % SESSION_COUNT),
            "workspace_id": WORKSPACE_ID,
            "event_type": "channel.event",
            "ts":         _ts(secs),
            "data": {
                "channel":    provider,
                "provider":   provider,
                "direction":  "in" if i % 2 == 0 else "out",
                "sender":     f"user-{i}",
                "text":       f"hello from {provider} {i}",
                "message_id": f"{provider}-msg-{i}",
            },
        })
    return out


def _build_session_rows():
    """Upsert one row per session for query_sessions list."""
    rows = []
    for i in range(SESSION_COUNT):
        rows.append({
            "session_id":    _session_id(i),
            "agent_type":    "openclaw",
            "node_id":       NODE_ID,
            "agent_id":      "main",
            "workspace_id":  WORKSPACE_ID,
            "title":         f"perf session {i}",
            "started_at":    _ts(i * 86400 // 5 + 600),
            "last_active_at": _ts(i * 86400 // 5),
            "status":        "active" if i % 4 != 0 else "idle",
            "total_tokens":  10000 + i * 50,
            "cost_usd":      0.01 * (i + 1),
            "message_count": EVENTS_PER_SESSION,
        })
    return rows


def seed_store(tmp_path, monkeypatch):
    """Returns ``(store, ls_module)`` with a populated isolated DuckDB.

    Reload + isolation pattern mirrors
    ``tests/test_duckdb_fastpath_v3_invariants.py::store`` so the daemon
    discovery shim doesn't leak through to ``~/.clawmetry/local_query.json``.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1000")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    # Block daemon proxy so the fast-path helpers hit OUR isolated store,
    # not whatever ~/.clawmetry/local_query.json points at on the dev box.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    store = ls.get_store()

    # Events — the bulk of the fixture.
    all_events: list[dict] = []
    for s in range(SESSION_COUNT):
        all_events.extend(_build_session_events(s))
    for ev in all_events:
        store.ingest(ev)
    for ev in _build_channel_events("telegram"):
        store.ingest(ev)
    for ev in _build_channel_events("signal"):
        store.ingest(ev)

    # Sessions list + subagents (non-events tables — synchronous writes).
    for row in _build_session_rows():
        store.ingest_session(row)
    for sa in _build_subagents():
        store.ingest_subagent(sa)

    # Drain the ring → DuckDB. The public ``flush()`` is the only
    # synchronous + retry-safe path; ``_flush_now()`` can race the
    # background flusher and leave 100-200 events stuck in the ring
    # until the next 50ms tick. Call until it returns 0 (idempotent).
    for _ in range(10):
        if store.flush() == 0:
            break

    # Verify the corpus actually landed — guard against quiet partial
    # ingest (the bug the spec's `_synthetic_tests_missed_real_event_shape`
    # memory warns about).
    expected = len(all_events) + 2 * CHANNEL_MSG_COUNT
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        n = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
        if n >= expected:
            break
        time.sleep(0.05)
    else:                                            # pragma: no cover
        raise AssertionError(
            f"perf fixture failed to flush: only {n}/{expected} events"
        )

    return store, ls
