"""Schema v14 -> v15: typed event columns + sessions.intent.

Builds a v14-SHAPED store by hand (events / sessions without the new
columns, schema_version stamped 14, a few pre-v15 rows), opens it through
``LocalStore`` and asserts the idempotent ALTERs landed, the version is
stamped 15, existing rows survive with NULL typed columns, and the bounded
lazy back-fill classifies them. Temp store only, never ~/.clawmetry.
"""
from __future__ import annotations

import importlib
import json
import time

import duckdb
import pytest


def _make_v14_store(path):
    """Minimal v14 tables: exactly the columns a 0.12.8xx store had."""
    conn = duckdb.connect(str(path))
    conn.execute("""
        CREATE TABLE events (
            id VARCHAR PRIMARY KEY,
            agent_type VARCHAR NOT NULL DEFAULT 'openclaw',
            node_id VARCHAR NOT NULL,
            agent_id VARCHAR NOT NULL DEFAULT 'main',
            session_id VARCHAR, workspace_id VARCHAR,
            event_type VARCHAR NOT NULL, ts VARCHAR NOT NULL,
            data BLOB, cost_usd DOUBLE, token_count INTEGER, model VARCHAR,
            created_at BIGINT NOT NULL,
            chain_prev_hash VARCHAR, chain_hash VARCHAR, runtime_kind VARCHAR
        )""")
    conn.execute("""
        CREATE TABLE sessions (
            agent_type VARCHAR NOT NULL DEFAULT 'openclaw',
            session_id VARCHAR NOT NULL, node_id VARCHAR,
            agent_id VARCHAR DEFAULT 'main', workspace_id VARCHAR,
            title VARCHAR, started_at VARCHAR, last_active_at VARCHAR,
            ended_at VARCHAR, status VARCHAR,
            total_tokens INTEGER DEFAULT 0, cost_usd DOUBLE DEFAULT 0,
            message_count INTEGER DEFAULT 0, metadata BLOB,
            updated_at BIGINT NOT NULL,
            outcome VARCHAR, outcome_confidence DOUBLE, outcome_classified_at BIGINT,
            eval_score DOUBLE, eval_reason VARCHAR, eval_judge_model VARCHAR,
            eval_scored_at BIGINT, eval_rubric VARCHAR,
            faithfulness_score DOUBLE, faithfulness_detail VARCHAR,
            faithfulness_scored_at BIGINT,
            cwd VARCHAR, git_branch VARCHAR,
            attention_state VARCHAR, attention_since BIGINT,
            attention_signal VARCHAR, attention_tool VARCHAR,
            PRIMARY KEY (agent_type, session_id)
        )""")
    conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at BIGINT)")
    conn.execute("INSERT INTO schema_version VALUES (14, ?)", [int(time.time() * 1000)])
    now = int(time.time() * 1000)
    sid = "claude_code:v14-legacy"
    conn.execute(
        "INSERT INTO sessions (agent_type, session_id, node_id, title, started_at, "
        "last_active_at, updated_at) VALUES ('claude_code', ?, 'n', 'legacy title', "
        "'2026-08-01T00:00:00Z', '2026-08-01T00:05:00Z', ?)", [sid, now])
    rows = [
        ("l1", "message", "2026-08-01T00:00:00Z",
         {"role": "user", "content": "Refactor the billing module so invoices round correctly"}),
        ("l2", "tool_call", "2026-08-01T00:00:01Z",
         {"role": "assistant", "content": "", "tool_name": "Edit",
          "tool_calls": [{"id": "c1", "input": {"file": "billing.py"}}]}),
        ("l3", "tool_result", "2026-08-01T00:00:02Z",
         {"role": "user", "content": "SyntaxError", "tool_name": "Edit",
          "extra": {"toolUseId": "c1", "isError": True}}),
        ("l4", "session.started", "2026-07-31T23:59:59Z", {"type": "session.started"}),
    ]
    for eid, et, ts, data in rows:
        conn.execute(
            "INSERT INTO events (id, node_id, session_id, event_type, ts, data, created_at) "
            "VALUES (?, 'n', ?, ?, ?, ?, ?)",
            [eid, sid, et, ts, json.dumps(data).encode("utf-8"), now])
    conn.close()
    return sid


@pytest.fixture
def v14_store(tmp_path, monkeypatch):
    path = tmp_path / "events.duckdb"
    sid = _make_v14_store(path)
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    store = ls.get_store()
    yield store, ls, sid
    try:
        store.stop(flush=True)
    except Exception:
        pass


def _cols(store, table):
    return {r[1] for r in store._conn.execute(f"PRAGMA table_info('{table}')").fetchall()}


def test_v15_adds_typed_event_columns_and_intent(v14_store):
    store, ls, _sid = v14_store
    assert ls.SCHEMA_VERSION == 15
    ev = _cols(store, "events")
    assert {"role", "block_kind", "tool_name", "is_error"} <= ev
    se = _cols(store, "sessions")
    assert {"intent", "intent_source"} <= se
    ver = store._conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert ver == 15


def test_v15_keeps_legacy_rows_with_null_typed_columns(v14_store):
    store, _ls, sid = v14_store
    rows = store._conn.execute(
        "SELECT id, role, block_kind FROM events WHERE session_id = ? ORDER BY id", [sid]
    ).fetchall()
    assert [r[0] for r in rows] == ["l1", "l2", "l3", "l4"]
    # No startup scan rewrote them: that is the lazy back-fill's job.
    assert all(r[1] is None and r[2] is None for r in rows)
    intent = store._conn.execute(
        "SELECT intent, intent_source FROM sessions WHERE session_id = ?", [sid]).fetchone()
    assert intent == (None, None)


def test_v15_lazy_backfill_types_legacy_rows_and_sets_intent(v14_store):
    store, _ls, sid = v14_store
    # Bounded: limit=2 classifies two rows and leaves the rest NULL.
    assert store.backfill_event_shapes(limit=2) == 2
    remaining = store._conn.execute(
        "SELECT COUNT(*) FROM events WHERE block_kind IS NULL").fetchone()[0]
    assert remaining == 2
    assert store.backfill_event_shapes(limit=500) == 2
    assert store.backfill_event_shapes(limit=500) == 0  # idles to zero work
    typed = dict(
        (r[0], (r[1], r[2], r[3], r[4])) for r in store._conn.execute(
            "SELECT id, role, block_kind, tool_name, is_error FROM events").fetchall())
    assert typed["l1"] == ("user", "text", None, False)
    assert typed["l2"] == ("assistant", "tool_use", "Edit", False)
    assert typed["l3"] == ("tool", "tool_result", "Edit", True)
    assert typed["l4"] == (None, "other", None, False)  # stamped, never revisited

    assert store.backfill_session_intents(limit=25) == 1
    intent, source = store._conn.execute(
        "SELECT intent, intent_source FROM sessions WHERE session_id = ?", [sid]).fetchone()
    assert intent == "Refactor the billing module so invoices round correctly"
    assert source == "events"
    assert store.backfill_session_intents(limit=25) == 0


def test_v15_migration_is_idempotent_on_reopen(v14_store, monkeypatch):
    store, ls, _sid = v14_store
    store.stop(flush=True)
    importlib.reload(ls)
    again = ls.get_store()
    try:
        assert {"role", "block_kind", "tool_name", "is_error"} <= _cols(again, "events")
        assert again._conn.execute(
            "SELECT COUNT(*) FROM schema_version WHERE version = 15").fetchone()[0] == 1
        # New writes land typed on the migrated store.
        again.ingest({"id": "n1", "node_id": "n", "session_id": "s-new",
                      "event_type": "message", "ts": "2026-09-01T00:00:00Z",
                      "data": {"role": "assistant", "content": "typed on write"}})
        again._flush_now()
        row = again._conn.execute(
            "SELECT role, block_kind FROM events WHERE id = 'n1'").fetchone()
        assert row == ("assistant", "text")
    finally:
        again.stop(flush=True)


def test_event_to_row_stamps_typed_columns_on_insert():
    """The insert path types every row: 14 legacy columns + 4 typed ones
    (+ 2 chain columns appended by the flush), matching _EVENT_INSERT_COLS."""
    import clawmetry.local_store as ls
    row = ls._event_to_row({"id": "r1", "node_id": "n", "event_type": "tool_result",
                            "ts": "2026-09-01T00:00:00Z",
                            "data": {"role": "user", "content": "boom", "tool_name": "Bash",
                                     "extra": {"toolUseId": "c1", "isError": True}}})
    assert len(row) == 18
    assert row[-4:] == ("tool", "tool_result", "Bash", True)
    assert ls.LocalStore._EVENT_INSERT_NCOLS == 20
    assert ls.LocalStore._EVENT_INSERT_COLS.split(", ")[14:18] == \
        ["role", "block_kind", "tool_name", "is_error"]
