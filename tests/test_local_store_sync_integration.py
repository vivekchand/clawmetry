"""Integration test for the sync.py → local_store wire-up (epic #964 phase 1).

Verifies that ``_flush_session_batch`` translates raw OpenClaw transcript events
into the local store's normalised shape and queues them for write — without
breaking the cloud POST path (we mock _post and assert it still gets called)."""

from __future__ import annotations

import importlib
import os
import time
import uuid
from unittest.mock import patch

import pytest


@pytest.fixture
def sync_with_isolated_store(tmp_path, monkeypatch):
    """Reload sync + local_store with an isolated DB per test."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    # sync.py grabs local_store via a local import inside the helper, so a
    # plain reload of sync isn't strictly required — but reloading both keeps
    # tests independent.
    importlib.reload(sync)
    yield sync, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_for_flush(store, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError("flusher did not drain in time")


def test_flush_session_batch_writes_to_local_store(sync_with_isolated_store):
    sync, ls = sync_with_isolated_store
    batch = [
        {
            "id": "ev-1",
            "type": "tool_call",
            "timestamp": "2026-05-11T10:00:00Z",
            "tool": "Bash",
            "model": "claude-opus-4-7",
            "tokens": 142,
            "cost_usd": 0.003,
        },
        {
            "id": "ev-2",
            "type": "message",
            "timestamp": "2026-05-11T10:00:05Z",
            "role": "user",
            "text": "hello",
        },
    ]
    fname = "session-abc.jsonl"
    with patch.object(sync, "_post") as mock_post:
        sync._flush_session_batch(
            batch, fname, api_key="cm_x", enc_key=None, node_id="agent+test", subagent_id=None
        )
    # Cloud path still fires:
    mock_post.assert_called_once()
    cloud_args = mock_post.call_args[0]
    assert cloud_args[0] == "/ingest/events"
    assert cloud_args[1]["node_id"] == "agent+test"
    assert len(cloud_args[1]["events"]) == 2

    # Local store path also fires:
    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_events(session_id="session-abc")
    assert len(rows) == 2
    by_id = {r["id"]: r for r in rows}
    assert by_id["ev-1"]["event_type"] == "tool_call"
    assert by_id["ev-1"]["model"] == "claude-opus-4-7"
    assert by_id["ev-1"]["token_count"] == 142
    assert round(by_id["ev-1"]["cost_usd"], 6) == 0.003
    assert by_id["ev-2"]["event_type"] == "message"


def test_local_store_failure_does_not_block_cloud_post(sync_with_isolated_store):
    sync, ls = sync_with_isolated_store
    batch = [{"id": "ev-x", "type": "tool_call", "timestamp": "2026-05-11T10:00:00Z"}]
    # Force the local-ingest path to blow up — cloud POST must still happen.
    with patch.object(sync, "_local_ingest_session_batch", side_effect=RuntimeError("disk full")):
        with patch.object(sync, "_post") as mock_post:
            sync._flush_session_batch(
                batch, "s.jsonl", api_key="cm_x", enc_key=None, node_id="agent+test"
            )
    mock_post.assert_called_once()


def test_subagent_id_used_as_session_id(sync_with_isolated_store):
    """When subagent_id is provided, local store rows key on it (not the file UUID)
    so the dashboard's subagent views can correlate."""
    sync, ls = sync_with_isolated_store
    batch = [{"id": "sub-1", "type": "tool_call", "timestamp": "2026-05-11T10:00:00Z"}]
    with patch.object(sync, "_post"):
        sync._flush_session_batch(
            batch,
            "00b5b41b-file-uuid.jsonl",
            api_key="cm_x",
            enc_key=None,
            node_id="agent+test",
            subagent_id="317db68b-subagent-uuid",
        )
    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_events(session_id="317db68b-subagent-uuid")
    assert len(rows) == 1
    rows_under_file_uuid = store.query_events(session_id="00b5b41b-file-uuid")
    assert len(rows_under_file_uuid) == 0


def test_events_without_timestamp_skipped(sync_with_isolated_store):
    """Local store requires ts; events missing it are dropped (logged elsewhere).
    Cloud POST still ships the full batch — cloud has its own validation."""
    sync, ls = sync_with_isolated_store
    batch = [
        {"id": "no-ts", "type": "tool_call"},  # missing timestamp
        {"id": "ok",    "type": "tool_call", "timestamp": "2026-05-11T10:00:00Z"},
    ]
    with patch.object(sync, "_post"):
        sync._flush_session_batch(
            batch, "s.jsonl", api_key="cm_x", enc_key=None, node_id="agent+test"
        )
    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_events(session_id="s")
    assert [r["id"] for r in rows] == ["ok"]


def test_id_synthesised_when_missing(sync_with_isolated_store):
    """Some openclaw events lack an explicit id; the helper composes one from
    session+ts+type so INSERT OR IGNORE still does the right thing on re-delivery."""
    sync, ls = sync_with_isolated_store
    batch = [{"type": "tool_call", "timestamp": "2026-05-11T10:00:00Z"}]
    with patch.object(sync, "_post"):
        sync._flush_session_batch(
            batch, "s.jsonl", api_key="cm_x", enc_key=None, node_id="agent+test"
        )
        # Ingest the same batch a second time — should not duplicate.
        sync._flush_session_batch(
            batch, "s.jsonl", api_key="cm_x", enc_key=None, node_id="agent+test"
        )
    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_events(session_id="s")
    assert len(rows) == 1


# ── PR 2: write-through for sessions / memory / heartbeat ─────────────────


def test_local_ingest_sessions_batch_upserts_into_sessions_table(sync_with_isolated_store):
    sync, ls = sync_with_isolated_store
    rows = [
        {
            "session_id": "sess-1",
            "model": "claude-opus-4-7",
            "total_tokens": 12500,
            "total_cost": 0.42,
            "started_at": "2026-05-11T10:00:00Z",
            "updated_at": "2026-05-11T10:30:00Z",
            "status": "completed",
            "subject": "Refactoring routes/sessions.py",
            "channel": "telegram",
            "chat_type": "private",
        },
        {
            "session_id": "sess-2",
            "model": "claude-opus-4-7",
            "total_tokens": 800,
            "total_cost": 0.03,
            "status": "active",
        },
    ]
    sync._local_ingest_sessions_batch(rows, node_id="agent+test")
    store = ls.get_store()
    out = store._fetch(
        "SELECT session_id, total_tokens, cost_usd, title, status FROM sessions ORDER BY session_id",
        [],
    )
    assert len(out) == 2
    assert out[0] == ("sess-1", 12500, 0.42, "Refactoring routes/sessions.py", "completed")
    assert out[1][0] == "sess-2"
    assert out[1][4] == "active"


def test_local_ingest_sessions_batch_handles_empty_and_id_aliases(sync_with_isolated_store):
    """Empty list = no-op. Rows missing session_id but with `id` get stored."""
    sync, ls = sync_with_isolated_store
    sync._local_ingest_sessions_batch([], node_id="x")  # must not raise
    sync._local_ingest_sessions_batch(
        [{"id": "from-id-field", "model": "m", "total_cost": 0.01}],
        node_id="agent+test",
    )
    out = ls.get_store()._fetch("SELECT session_id FROM sessions", [])
    assert ("from-id-field",) in out


def test_local_ingest_memory_files_writes_only_changed(sync_with_isolated_store):
    sync, ls = sync_with_isolated_store
    all_files = [
        ("MEMORY.md", "# All my notes"),
        ("AGENTS.md", "# Agent roster"),
        ("memory/notes.md", "# Subnotes"),
    ]
    # Only AGENTS.md changed this cycle.
    sync._local_ingest_memory_files(all_files, ["AGENTS.md"])
    store = ls.get_store()
    rows = store._fetch(
        "SELECT path, blob FROM memory_blobs ORDER BY path", [],
    )
    assert len(rows) == 1
    assert rows[0][0] == "AGENTS.md"
    assert bytes(rows[0][1]) == b"# Agent roster"


def test_local_ingest_memory_files_dedups_on_resync(sync_with_isolated_store):
    """Same content re-ingested = sha256 dedup, no row update."""
    sync, ls = sync_with_isolated_store
    files = [("MEMORY.md", "stable content here")]
    sync._local_ingest_memory_files(files, ["MEMORY.md"])
    rows1 = ls.get_store()._fetch(
        "SELECT updated_at FROM memory_blobs WHERE path='MEMORY.md'", [],
    )
    sync._local_ingest_memory_files(files, ["MEMORY.md"])
    rows2 = ls.get_store()._fetch(
        "SELECT updated_at FROM memory_blobs WHERE path='MEMORY.md'", [],
    )
    assert rows1[0][0] == rows2[0][0]


def test_local_ingest_sessions_batch_failure_does_not_break_caller(sync_with_isolated_store):
    """If the local store throws (e.g. corrupt file), the caller should
    catch — verified by patching ingest_session to raise."""
    sync, ls = sync_with_isolated_store
    store = ls.get_store()
    with patch.object(store, "ingest_session", side_effect=RuntimeError("disk full")):
        # The helper itself doesn't catch; the CALLER (sync_session_metadata's
        # _flush) catches via try/except. Here we just verify the helper
        # propagates the exception so the caller's try/except sees it.
        with pytest.raises(RuntimeError, match="disk full"):
            sync._local_ingest_sessions_batch(
                [{"session_id": "x"}], node_id="agent+test"
            )
