"""Tests for the canonical replay-event schema (#4813).

Foundation tests only: module imports, kind enum coverage, validator
correctness, and DuckDB table creation. Adapter-specific mapping tests
live with their adapters (Claude Code #4815, OpenClaw #4816, Pro
adapters in clawmetry-pro).
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import duckdb
import pytest

from clawmetry import replay_schema
from clawmetry.replay_schema import (
    ALL_KINDS,
    KIND_AGENT_SPAWN,
    KIND_APPROVAL_DECIDED,
    KIND_APPROVAL_REQUESTED,
    KIND_LLM_CALL,
    KIND_MODE_CHANGED,
    KIND_TOOL_CALL,
    is_valid_kind,
    validate,
)


def _valid_llm_event() -> dict:
    return {
        "ts": time.time(),
        "kind": KIND_LLM_CALL,
        "span_id": "span-1",
        "parent_span_id": None,
        "session_id": "sess-1",
        "runtime": "claude_code",
        "payload": {"model": "claude-opus-4-7"},
    }


# ── kind enum ────────────────────────────────────────────────────────────


def test_all_kinds_are_unique():
    assert len(ALL_KINDS) == len(set(ALL_KINDS))


def test_kinds_use_dotted_prefixes():
    # Renderer dispatches on prefix; leading dot-token must be stable.
    prefixes = {k.split(".")[0] for k in ALL_KINDS if "." in k}
    assert prefixes >= {"llm", "tool", "agent", "workflow", "approval", "mode"}


def test_is_valid_kind():
    for k in ALL_KINDS:
        assert is_valid_kind(k), k
    assert not is_valid_kind("bogus.kind")
    assert not is_valid_kind("")


# ── validator ────────────────────────────────────────────────────────────


def test_validate_accepts_minimal_event():
    assert validate(_valid_llm_event()) == []


def test_validate_flags_missing_required_fields():
    errs = validate({})
    assert any("ts" in e for e in errs)
    assert any("kind" in e for e in errs)
    assert any("span_id" in e for e in errs)
    assert any("session_id" in e for e in errs)
    assert any("runtime" in e for e in errs)


def test_validate_flags_unknown_kind():
    ev = _valid_llm_event()
    ev["kind"] = "gremlin.event"
    assert any("unknown kind" in e for e in validate(ev))


def test_mode_required_only_on_mode_changed():
    # Missing mode on mode.changed → error.
    ev = _valid_llm_event()
    ev["kind"] = KIND_MODE_CHANGED
    assert any("mode.changed" in e for e in validate(ev))
    ev["mode"] = {"permission": "bypassPermissions"}
    assert validate(ev) == []
    # Mode on a non-mode.changed event → error (prevents adapter bloat).
    ev2 = _valid_llm_event()
    ev2["mode"] = {"permission": "default"}
    assert any("mode field only valid" in e for e in validate(ev2))


def test_approval_required_only_on_approval_events():
    ev = _valid_llm_event()
    ev["kind"] = KIND_APPROVAL_REQUESTED
    assert any("approval dict" in e for e in validate(ev))
    ev["approval"] = {"status": "requested"}
    assert validate(ev) == []
    ev2 = _valid_llm_event()
    ev2["kind"] = KIND_TOOL_CALL
    ev2["approval"] = {"status": "approved"}
    assert any("approval field only valid" in e for e in validate(ev2))


def test_agent_spawn_kind_present():
    # Regression guard: the whole delegation-tree UI depends on this kind.
    assert KIND_AGENT_SPAWN in ALL_KINDS
    assert KIND_APPROVAL_DECIDED in ALL_KINDS


# ── DuckDB table shape ───────────────────────────────────────────────────


def test_replay_events_table_creates_and_accepts_a_row():
    """The DDL in local_store.py must be valid DuckDB and accept a row
    matching the ReplayEvent shape (blobs for payload/mode/approval)."""
    from clawmetry import local_store  # heavy import; keep test-scoped

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        try:
            for stmt in local_store._DDL:
                conn.execute(stmt)
            conn.execute(
                """
                INSERT INTO replay_events
                  (span_id, parent_span_id, session_id, runtime, kind, ts,
                   payload, mode, approval, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    "span-1", None, "sess-1", "claude_code",
                    KIND_LLM_CALL, time.time(),
                    b"{}", None, None, int(time.time() * 1000),
                ],
            )
            row = conn.execute(
                "SELECT span_id, session_id, runtime, kind FROM replay_events"
            ).fetchone()
            assert row == ("span-1", "sess-1", "claude_code", KIND_LLM_CALL)
        finally:
            conn.close()


def test_replay_events_indexes_exist():
    """The four indexes we rely on for the endpoint's queries must exist."""
    from clawmetry import local_store

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        try:
            for stmt in local_store._DDL:
                conn.execute(stmt)
            names = {
                row[0]
                for row in conn.execute(
                    "SELECT index_name FROM duckdb_indexes() "
                    "WHERE table_name = 'replay_events'"
                ).fetchall()
            }
            assert "idx_replay_events_session_ts" in names
            assert "idx_replay_events_parent" in names
            assert "idx_replay_events_runtime_kind" in names
            assert "idx_replay_events_created_at" in names
        finally:
            conn.close()
