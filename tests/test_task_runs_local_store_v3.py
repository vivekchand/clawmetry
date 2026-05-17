"""Regression guard for /api/task-runs DuckDB fast path (Tier-1 #1565).

``routes/sessions.py:_try_local_store_task_runs`` reads the
pre-aggregated ``subagents`` DuckDB table (same source PR #1569 wired
into ``_try_local_store_subagents``) and maps it onto the legacy
``~/.openclaw/tasks/runs.sqlite`` response shape so the Subagents modal
(``app.js`` ``renderModalSubagents``) keeps working bit-for-bit when
the daemon serves it from DuckDB instead of opening the sqlite file.

Audit-hint check: the #1565 hint said "derive from query_events task
lifecycle types", but verified 2026-05-17 against
``sync.py::_parse_v3_event`` — no ``task.started`` / ``task.completed``
event types exist in v3 ingest. The canonical DuckDB source for task
lifecycle IS the ``subagents`` table (its schema comment in
``local_store.py`` explicitly says "Shared by OpenClaw subagents +
Claude Code Task tool."). Test seeds DuckDB via the daemon's canonical
``LocalStore.ingest_subagent`` helper (matching sync.py call site).

This file asserts:

1. Populated path → fast path returns ``_source='local_store'`` and the
   shape the modal needs (``task_id``, ``parent_task_id``,
   ``child_session_key``, ``status``, ``duration_ms``, ``label``,
   ``task``, ``terminal_outcome``).
2. Empty store → returns ``None`` so the legacy sqlite fallback fires.
3. Status normalisation — gateway snapshot vocabulary
   (``active`` / ``completed`` / ``failed``) maps onto the
   runs.sqlite UI vocabulary (``running`` / ``succeeded`` / ``failed``)
   so the colour pills + Failed stat chip render consistently.
4. Filter params (``status=``, ``requester_session_key=``) are honoured
   exactly like the legacy sqlite WHERE clause — guards against the
   silent-drop pattern flagged in
   ``feedback_usage_dedupe_pattern.md``.
"""

from __future__ import annotations

import importlib
import time

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
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    # Issue #1538 pattern — isolate the fixture from a contributor's locally
    # running clawmetry daemon. Without this, ``_ls_call`` proxies through
    # ``~/.clawmetry/local_query.json`` and the daemon queries its OWN
    # production DuckDB instead of our tmp_path fixture.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_task_runs_local_store_returns_local_store_source(app):
    """Two children for one parent → fast path returns both rows tagged
    with ``_source='local_store'`` and the UI-keyed shape preserved on
    each row (``task_id`` / ``child_session_key`` / ``duration_ms`` /
    ``label`` / ``terminal_outcome``)."""
    a, ls = app
    store = ls.get_store()
    parent_sid = "parent-session-xyz"
    now_ms = int(time.time() * 1000)

    store.ingest_subagent({
        "subagent_id":       "child-a",
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-17T10:00:00Z",
        "ended_at":          "2026-05-17T10:00:15Z",
        "task":              "refactor auth.py",
        "status":            "completed",
        "cost_usd":          0.0234,
        "token_count":       4200,
        "label":             "auth-refactor",
        "displayName":       "auth-refactor",
        "runId":             "run-aaaa",
        "started_at_ms":     now_ms - 15000,
        "ended_at_ms":       now_ms,
        "updated_at_ms":     now_ms,
        "completionStatus":  "ok",
        "completionResult":  "Refactor complete, 3 files touched.",
    })
    store.ingest_subagent({
        "subagent_id":       "child-b",
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-17T10:01:00Z",
        "task":              "summarise transcripts",
        "status":            "active",  # gateway vocabulary
        "cost_usd":          0.0089,
        "token_count":       1800,
        "label":             "summariser",
        "started_at_ms":     now_ms - 8000,
        "updated_at_ms":     now_ms,
    })

    r = a.test_client().get("/api/task-runs")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"_source must be local_store; got {body.get('_source')!r}"
    )
    tasks = body.get("tasks") or []
    ids = {t["task_id"] for t in tasks}
    assert ids == {"child-a", "child-b"}, f"expected both children, got {ids!r}"

    by_id = {t["task_id"]: t for t in tasks}
    a_row = by_id["child-a"]
    # Status normalisation: gateway ``completed`` → UI ``succeeded``.
    assert a_row["status"] == "succeeded", a_row["status"]
    assert a_row["label"] == "auth-refactor"
    assert a_row["task"] == "refactor auth.py"
    assert a_row["child_session_key"].startswith("agent:main:subagent:")
    assert a_row["terminal_summary"] == "Refactor complete, 3 files touched."
    assert a_row["terminal_outcome"] == "ok"
    assert a_row["run_id"] == "run-aaaa"
    # duration_ms must mirror the legacy ``ended - started`` formula
    # (only set when BOTH endpoints exist).
    assert a_row["duration_ms"] == 15000, a_row["duration_ms"]

    b_row = by_id["child-b"]
    # Gateway ``active`` → UI ``running`` so the colour pill stays green.
    assert b_row["status"] == "running", b_row["status"]
    # Still-running task → no ended_at → duration_ms == 0.
    assert b_row["duration_ms"] == 0

    counts = body.get("counts") or {}
    assert counts.get("running") == 1
    assert counts.get("succeeded") == 1

    stats = body.get("stats") or {}
    assert stats["total"] == 2
    assert stats["succeeded"] == 1
    assert stats["running"] == 1
    assert stats["failed"] == 0
    assert stats["error_rate_pct"] == 0


def test_task_runs_local_store_returns_none_when_empty(app):
    """No rows in the ``subagents`` table → fast path returns None so
    the legacy ``~/.openclaw/tasks/runs.sqlite`` fallback fires. The
    handler must NOT short-circuit to a populated zero-shell here:
    older OpenClaw installs whose daemon hasn't snapshotted yet need
    the sqlite path to find their task registry on disk."""
    _, ls = app
    assert ls.get_store().query_subagents(limit=10) == []

    import routes.sessions as sessions_mod
    fast = sessions_mod._try_local_store_task_runs(
        limit=500, status_filter="", parent_filter="", requester_filter="",
    )
    assert fast is None, (
        f"empty store must return None for legacy fallback; got {fast!r}"
    )


def test_task_runs_local_store_failed_transitions(app):
    """Failed status path: gateway ``failed`` → UI ``failed`` (no
    normalisation needed), error message survives the data-blob
    round-trip, and the stats block reports a non-zero
    ``error_rate_pct``."""
    a, ls = app
    store = ls.get_store()
    now_ms = int(time.time() * 1000)

    store.ingest_subagent({
        "subagent_id":      "bad-child",
        "agent_type":       "openclaw",
        "parent_session_id": "parent-x",
        "spawned_at":       "2026-05-17T10:00:00Z",
        "ended_at":         "2026-05-17T10:00:02Z",
        "task":             "broken",
        "status":           "failed",
        "error":            "tool unavailable",
        "started_at_ms":    now_ms - 2000,
        "ended_at_ms":      now_ms,
        "updated_at_ms":    now_ms,
    })
    store.ingest_subagent({
        "subagent_id":      "ok-child",
        "agent_type":       "openclaw",
        "parent_session_id": "parent-x",
        "spawned_at":       "2026-05-17T10:00:01Z",
        "task":             "fine",
        "status":           "succeeded",
        "started_at_ms":    now_ms - 1000,
        "ended_at_ms":      now_ms,
        "updated_at_ms":    now_ms,
    })

    r = a.test_client().get("/api/task-runs")
    body = r.get_json()
    by_id = {t["task_id"]: t for t in (body.get("tasks") or [])}
    assert by_id["bad-child"]["status"] == "failed"
    assert by_id["bad-child"]["error"] == "tool unavailable"
    assert body["stats"]["failed"] == 1
    # 1 failed out of 2 → 50% error rate.
    assert body["stats"]["error_rate_pct"] == 50.0


def test_task_runs_local_store_filters_honoured(app):
    """``status=`` and ``requester_session_key=`` filters must be
    applied to the DuckDB rows before they hit the response — same
    semantics as the legacy sqlite WHERE clause. Guards against the
    silent-drop pattern from ``feedback_usage_dedupe_pattern.md``
    where blind aggregate-replace lost non-matching rows."""
    a, ls = app
    store = ls.get_store()
    now_ms = int(time.time() * 1000)

    parent_a = "parent-aaa"
    parent_b = "parent-bbb"
    for sid, parent, status in [
        ("t1", parent_a, "running"),
        ("t2", parent_a, "succeeded"),
        ("t3", parent_b, "failed"),
    ]:
        store.ingest_subagent({
            "subagent_id":       sid,
            "agent_type":        "openclaw",
            "parent_session_id": parent,
            "spawned_at":        "2026-05-17T10:00:00Z",
            "task":              sid,
            "status":            status,
            "started_at_ms":     now_ms,
            "updated_at_ms":     now_ms,
        })

    # status filter: only the failed row should come back.
    r = a.test_client().get("/api/task-runs?status=failed")
    body = r.get_json()
    ids = [t["task_id"] for t in (body.get("tasks") or [])]
    assert ids == ["t3"], f"status=failed filter dropped or duplicated rows: {ids!r}"
    assert body["_source"] == "local_store"

    # requester_session_key filter: only t1 + t2 belong to parent_a.
    # _try_local_store_task_runs derives requester_session_key as
    # ``agent:main:<parent_session_id>`` when no override is stamped.
    r2 = a.test_client().get(
        "/api/task-runs?requester_session_key=agent:main:" + parent_a
    )
    body2 = r2.get_json()
    ids2 = sorted(t["task_id"] for t in (body2.get("tasks") or []))
    assert ids2 == ["t1", "t2"], (
        f"requester filter dropped or leaked rows: {ids2!r}"
    )
