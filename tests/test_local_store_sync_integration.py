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


def test_sync_extracts_cost_and_tokens(sync_with_isolated_store):
    """Real OpenClaw transcript shape: cost / tokens / model live under
    ``message.usage.{cost.total, totalTokens}`` and ``message.model``.

    Regression for MOAT_E2E_REPORT_2026-05-13 root-cause #4: the old code
    only checked top-level ``cost_usd`` / ``tokens`` / ``model`` and dropped
    the nested values to NULL, breaking every Token chart and the
    ``/api/local/aggregates`` cost roll-up.
    """
    sync, ls = sync_with_isolated_store
    batch = [
        # 1. Real OpenClaw `message` event with nested usage (the case that
        #    was silently NULL before this fix).
        {
            "id": "ev-real",
            "type": "message",
            "timestamp": "2026-05-12T22:35:31.159296Z",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "usage": {
                    "input": 200, "output": 100,
                    "totalTokens": 1234,
                    "cost": {"input": 0.30, "output": 0.12, "total": 0.42},
                },
            },
        },
        # 2. Synthesised event with top-level fields (legacy / sub-agent path).
        #    Should still work — top-level wins.
        {
            "id": "ev-flat",
            "type": "tool_call",
            "timestamp": "2026-05-12T22:35:32.000Z",
            "tokens": 50,
            "cost_usd": 0.01,
            "model": "claude-haiku",
        },
        # 3. Event with neither — both columns stay NULL (no synthesised zeros).
        {
            "id": "ev-bare",
            "type": "thinking_level_change",
            "timestamp": "2026-05-12T22:35:33.000Z",
        },
    ]
    with patch.object(sync, "_post"):
        sync._flush_session_batch(
            batch, "session-cost.jsonl", api_key="cm_x",
            enc_key=None, node_id="agent+test", subagent_id=None,
        )
    store = ls.get_store()
    _wait_for_flush(store)
    rows = {r["id"]: r for r in store.query_events(session_id="session-cost")}
    # After #1135 the v3 ``thinking_level_change`` row is intentionally
    # dropped (plumbing event with no transcript-visible content), so the
    # batch produces 2 rows, not 3 (real + flat — bare is skipped).
    assert len(rows) == 2

    # Nested usage: extracted to columns. After #1135 the v3 ``message``
    # event is mapped to ``model.completed`` (the dot.separated event_type
    # the trajectory parser produces), so the read-side handlers work
    # uniformly across both schemas.
    real = rows["ev-real"]
    assert real["event_type"] == "model.completed"
    assert real["token_count"] == 1234
    assert round(real["cost_usd"], 6) == 0.42
    assert real["model"] == "claude-opus-4-7"
    # PR #1132's expander reads tokens from this exact path:
    assert real["data"]["promptCache"]["lastCallUsage"]["total"] == 1234

    # Top-level still works.
    flat = rows["ev-flat"]
    assert flat["token_count"] == 50
    assert round(flat["cost_usd"], 6) == 0.01
    assert flat["model"] == "claude-haiku"

    # ``ev-bare`` (thinking_level_change) is now intentionally dropped by
    # ``_parse_v3_event`` — it carries no user-visible content and was
    # only polluting analytics with NULL-cost / NULL-token rows.
    assert "ev-bare" not in rows


def test_extract_cost_tokens_model_unit():
    """Direct unit test for the extractor — covers the field-name edge cases
    (totalTokens vs total_tokens, cost dict vs scalar, missing message).
    """
    from clawmetry import sync as _sync

    # OpenClaw real shape
    c, t, m = _sync._extract_cost_tokens_model({
        "type": "message",
        "message": {
            "model": "claude-opus-4-7",
            "usage": {"totalTokens": 162, "cost": {"total": 0.00495}},
        },
    })
    assert c == 0.00495 and t == 162 and m == "claude-opus-4-7"

    # snake_case fallback
    c, t, m = _sync._extract_cost_tokens_model({
        "message": {"usage": {"total_tokens": 50, "cost": {"total_usd": 0.005}}}
    })
    assert c == 0.005 and t == 50

    # Top-level wins
    c, t, m = _sync._extract_cost_tokens_model({
        "cost_usd": 0.99, "tokens": 7, "model": "haiku",
        "message": {"usage": {"totalTokens": 1, "cost": {"total": 0.01}}},
    })
    assert c == 0.99 and t == 7 and m == "haiku"

    # Empty
    assert _sync._extract_cost_tokens_model({}) == (None, None, None)
    assert _sync._extract_cost_tokens_model({"type": "session"}) == (None, None, None)
