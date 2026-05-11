"""Tests for the multi-agent schema expansion (sessions, memory_blobs,
heartbeats) added in 0.12.165+. Also covers the v1 → v2 migration path
for stores upgraded from 0.12.164.
"""

from __future__ import annotations

import importlib

import duckdb
import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass


def test_ingest_session_inserts_row(store):
    store.ingest_session({
        "session_id": "sess-A",
        "agent_type": "claude_code",
        "node_id": "agent+test",
        "title": "Refactoring routes/sessions.py",
        "started_at": "2026-05-11T10:00:00Z",
        "last_active_at": "2026-05-11T10:30:00Z",
        "status": "active",
        "total_tokens": 12500,
        "cost_usd": 0.42,
        "message_count": 17,
        "metadata": {"workspace": "/Users/vivek/projects/clawmetry"},
    })
    rows = store._fetch(
        "SELECT agent_type, session_id, title, total_tokens, cost_usd FROM sessions",
        [],
    )
    assert len(rows) == 1
    assert rows[0][0] == "claude_code"
    assert rows[0][1] == "sess-A"
    assert rows[0][2] == "Refactoring routes/sessions.py"
    assert rows[0][3] == 12500
    assert abs(rows[0][4] - 0.42) < 1e-9


def test_ingest_session_upserts_on_conflict(store):
    """Same (agent_type, session_id) re-ingested updates the row, doesn't dup."""
    base = {"session_id": "sess-up", "agent_type": "openclaw",
            "started_at": "2026-05-11T10:00:00Z", "status": "active"}
    store.ingest_session({**base, "total_tokens": 100, "cost_usd": 0.01,
                          "title": "first"})
    store.ingest_session({**base, "total_tokens": 200, "cost_usd": 0.05,
                          "status": "ended", "title": None})
    rows = store._fetch(
        "SELECT total_tokens, cost_usd, status, title, started_at FROM sessions",
        [],
    )
    assert len(rows) == 1
    assert rows[0][0] == 200
    assert abs(rows[0][1] - 0.05) < 1e-9
    assert rows[0][2] == "ended"
    # COALESCE preserves first title when second sends None.
    assert rows[0][3] == "first"
    # COALESCE preserves first started_at on update.
    assert rows[0][4] == "2026-05-11T10:00:00Z"


def test_ingest_session_isolates_agent_types(store):
    """Two agents using the same session_id string don't collide."""
    store.ingest_session({"session_id": "shared", "agent_type": "openclaw",
                          "title": "openclaw-side"})
    store.ingest_session({"session_id": "shared", "agent_type": "claude_code",
                          "title": "cc-side"})
    rows = store._fetch("SELECT agent_type, title FROM sessions ORDER BY agent_type", [])
    assert len(rows) == 2
    assert rows[0] == ("claude_code", "cc-side")
    assert rows[1] == ("openclaw", "openclaw-side")


def test_ingest_memory_blob_dedups_on_sha256(store):
    blob = b"# Notes\n\nFirst draft of project notes."
    store.ingest_memory_blob({
        "agent_type": "openclaw",
        "agent_id": "main",
        "path": "~/.openclaw/memory/notes.md",
        "ts": "2026-05-11T10:00:00Z",
        "blob": blob,
    })
    rows1 = store._fetch("SELECT COUNT(*), MAX(updated_at) FROM memory_blobs", [])
    # Re-ingest identical content → no new write.
    store.ingest_memory_blob({
        "agent_type": "openclaw",
        "agent_id": "main",
        "path": "~/.openclaw/memory/notes.md",
        "ts": "2026-05-11T10:05:00Z",
        "blob": blob,
    })
    rows2 = store._fetch("SELECT COUNT(*), MAX(updated_at) FROM memory_blobs", [])
    assert rows1[0][0] == 1
    assert rows2[0][0] == 1
    # updated_at should NOT advance on the dedup'd write.
    assert rows1[0][1] == rows2[0][1]


def test_ingest_memory_blob_updates_on_change(store):
    store.ingest_memory_blob({
        "agent_type": "claude_code", "path": "CLAUDE.md",
        "blob": b"v1 content", "ts": "2026-05-11T10:00:00Z",
    })
    store.ingest_memory_blob({
        "agent_type": "claude_code", "path": "CLAUDE.md",
        "blob": b"v2 content updated", "ts": "2026-05-11T11:00:00Z",
    })
    rows = store._fetch(
        "SELECT blob, ts, size_bytes FROM memory_blobs WHERE path = 'CLAUDE.md'", [],
    )
    assert len(rows) == 1
    assert bytes(rows[0][0]) == b"v2 content updated"
    assert rows[0][1] == "2026-05-11T11:00:00Z"
    assert rows[0][2] == len(b"v2 content updated")


def test_ingest_heartbeat_appends(store):
    """Heartbeats are append-only by (agent_type, node_id, ts)."""
    store.ingest_heartbeat({
        "node_id": "agent+test", "ts": "2026-05-11T10:00:00Z",
        "version": "0.12.165", "e2e": True,
        "local_store_size_mb": 0.5,
        "local_store": {"events_total": 100},
    })
    store.ingest_heartbeat({
        "node_id": "agent+test", "ts": "2026-05-11T10:05:00Z",
        "version": "0.12.165", "e2e": True,
        "local_store_size_mb": 0.6,
        "local_store": {"events_total": 120},
    })
    # Same ts is silently ignored (PK conflict).
    store.ingest_heartbeat({
        "node_id": "agent+test", "ts": "2026-05-11T10:05:00Z",
        "version": "0.12.165", "e2e": True, "local_store_size_mb": 999,
    })
    rows = store._fetch(
        "SELECT ts, size_mb, events_total FROM heartbeats ORDER BY ts", [],
    )
    assert len(rows) == 2
    assert rows[0][1] == 0.5
    assert rows[0][2] == 100
    assert rows[1][1] == 0.6
    assert rows[1][2] == 120


def test_ingest_session_requires_session_id(store):
    with pytest.raises(ValueError, match="session_id"):
        store.ingest_session({"agent_type": "openclaw"})


def test_ingest_memory_blob_requires_agent_type_and_path(store):
    with pytest.raises(ValueError, match="agent_type"):
        store.ingest_memory_blob({"path": "x"})
    with pytest.raises(ValueError, match="path"):
        store.ingest_memory_blob({"agent_type": "claude_code"})


def test_v1_to_v2_migration_adds_agent_type_column(tmp_path, monkeypatch):
    """A store created at SCHEMA_VERSION=1 (events table without agent_type)
    must auto-upgrade to v2 on next open without losing data."""
    db_path = tmp_path / "events.duckdb"
    # Manually create a v1 events table (without agent_type).
    with duckdb.connect(str(db_path)) as v1_conn:
        v1_conn.execute("""
            CREATE TABLE events (
                id            VARCHAR PRIMARY KEY,
                node_id       VARCHAR NOT NULL,
                agent_id      VARCHAR NOT NULL DEFAULT 'main',
                session_id    VARCHAR,
                workspace_id  VARCHAR,
                event_type    VARCHAR NOT NULL,
                ts            VARCHAR NOT NULL,
                data          BLOB,
                cost_usd      DOUBLE,
                token_count   INTEGER,
                model         VARCHAR,
                created_at    BIGINT NOT NULL
            )
        """)
        v1_conn.execute("""
            CREATE TABLE daily_aggregates (
                agent_id      VARCHAR NOT NULL,
                workspace_id  VARCHAR,
                day           VARCHAR NOT NULL,
                cost_usd      DOUBLE DEFAULT 0,
                token_count   INTEGER DEFAULT 0,
                event_count   INTEGER DEFAULT 0,
                error_count   INTEGER DEFAULT 0,
                PRIMARY KEY (agent_id, workspace_id, day)
            )
        """)
        v1_conn.execute("""
            CREATE TABLE schema_version (
                version    INTEGER PRIMARY KEY,
                applied_at BIGINT NOT NULL
            )
        """)
        v1_conn.execute("INSERT INTO schema_version VALUES (1, 1700000000000)")
        v1_conn.execute(
            "INSERT INTO events VALUES (?, ?, 'main', NULL, NULL, 'tool_call', ?, NULL, 0.001, 5, 'claude-opus-4-7', ?)",
            ["legacy-1", "agent+legacy", "2026-05-10T12:00:00Z", 1700000001000],
        )

    # Open via the production code path → should migrate seamlessly.
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    store = ls.get_store()
    try:
        cols = {row[1] for row in store._conn.execute("PRAGMA table_info('events')").fetchall()}
        assert "agent_type" in cols, "v1→v2 migration didn't add agent_type column"
        # Legacy event is still readable + agent_type backfilled to 'openclaw'.
        rows = store._fetch(
            "SELECT id, agent_type, event_type FROM events WHERE id = 'legacy-1'", [],
        )
        assert rows[0][1] == "openclaw"
        assert rows[0][2] == "tool_call"
    finally:
        try:
            store.stop(flush=True)
        except Exception:
            pass
