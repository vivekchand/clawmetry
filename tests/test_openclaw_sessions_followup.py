"""Tests for the sessions.json walk path (PR closes #1226).

These tests cover the three gaps Diya (OpenClaw's bot) flagged when
verifying PR #1224 on the user's live install:

  1. Sub-agent transcripts under ``<claude-id>/subagents/*.jsonl`` were
     never captured — the process-inspection path only watched the
     top-level ``<claude-id>.jsonl``.
  2. Tool-result dumps under ``<claude-id>/tool-results/*`` were never
     captured.
  3. Discovery itself was fragile — process inspection misses any
     session whose ``claude`` subprocess isn't currently running. The
     primary path now reads sessions.json directly.

The new ``sync_openclaw_claude_sessions_via_index`` function:
  * walks ``~/.openclaw/agents/main/sessions/sessions.json``
  * follows ``cliSessionIds.claude-cli`` → Claude Code session UUID
  * tails the top-level transcript + every subagents/*.jsonl
  * ingests one event per tool-results/* file
  * tags events under the OpenClaw session UUID (NOT the Claude UUID)
  * upserts one row into the ``sessions`` table per OpenClaw session

so Brain's join-style reads find the session row and render it under
the right session-list entry.
"""

from __future__ import annotations

import importlib
import json
import os
import time
from pathlib import Path

import pytest


@pytest.fixture
def sync_with_isolated_store(tmp_path, monkeypatch):
    """Reload sync + local_store with an isolated DuckDB per test.

    Mirrors the fixture in test_openclaw_claude_session_ingest.py so
    test isolation matches PR #1224's existing tests.
    """
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH",
        str(tmp_path / "events.duckdb"),
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.delenv("CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST", raising=False)
    # Point ``~/.claude/projects`` and ``~/.openclaw`` at temp dirs so this
    # test never touches the user's real installation.
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(fake_home / ".claude"))
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(fake_home / ".openclaw"))
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    yield sync, ls, fake_home
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


# ── Synthetic OpenClaw + Claude Code on-disk layout ─────────────────────────

OPENCLAW_SESSION_ID = "625c0ad9-71af-4a56-9a3b-cab396860a85"  # Diya's session
CLAUDE_SESSION_ID = "49f1d9fc-0848-4b6b-8fd7-64633bbc6b58"
WORKSPACE_DIR = "/Users/test/.openclaw/workspace"
ENCODED_CWD = "-Users-test--openclaw-workspace"  # the slug Claude Code uses

SUBAGENT_FILE_STEM = "agent-a156b1052348a79c9"

TOP_LEVEL_LINES = [
    {
        "type": "user",
        "message": {"role": "user", "content": "hello, how are you?"},
        "uuid": "evt-user-001",
        "timestamp": "2026-05-14T20:12:45.580Z",
        "cwd": WORKSPACE_DIR,
        "sessionId": CLAUDE_SESSION_ID,
    },
    {
        "type": "assistant",
        "message": {
            "model": "claude-opus-4-7",
            "id": "msg_abc",
            "role": "assistant",
            "content": [{"type": "text", "text": "Doing well, thanks!"}],
            "usage": {
                "input_tokens": 1,
                "output_tokens": 12,
                "totalTokens": 113,
                "cost": {"total": 0.000456},
            },
        },
        "uuid": "evt-asst-001",
        "timestamp": "2026-05-14T20:12:50.000Z",
        "sessionId": CLAUDE_SESSION_ID,
    },
]

SUBAGENT_LINES = [
    {
        "parentUuid": None,
        "isSidechain": True,
        "type": "user",
        "message": {"role": "user", "content": "Research TVK ideology"},
        "uuid": "sub-evt-001",
        "timestamp": "2026-05-13T04:26:13.458Z",
        "sessionId": CLAUDE_SESSION_ID,
        "agentId": "a156b1052348a79c9",
    },
    {
        "type": "assistant",
        "message": {
            "model": "claude-opus-4-7",
            "role": "assistant",
            "content": [{"type": "text", "text": "TVK was founded by..."}],
            "usage": {"input_tokens": 1500, "output_tokens": 250, "totalTokens": 1750},
        },
        "uuid": "sub-evt-002",
        "timestamp": "2026-05-13T04:26:30.000Z",
        "sessionId": CLAUDE_SESSION_ID,
    },
]

TOOL_RESULT_FILES = {
    "bcdef74xu.txt": "file:line:matched-content for grep result\n" * 50,
    "bg5hiof10.txt": "<html>fetched content</html>",
}


def _setup_layout(fake_home: Path) -> dict:
    """Materialise the synthetic on-disk layout under the temp home dir.
    Returns paths so individual tests can inspect them.
    """
    sessions_dir = fake_home / ".openclaw" / "agents" / "main" / "sessions"
    sessions_dir.mkdir(parents=True)

    # sessions.json — exactly the shape we observed on the user's box.
    sessions_idx = {
        "agent:main:telegram:direct:1532693273": {
            "sessionId": OPENCLAW_SESSION_ID,
            "claudeCliSessionId": CLAUDE_SESSION_ID,
            "cliSessionIds": {"claude-cli": CLAUDE_SESSION_ID},
            "sessionFile": str(
                sessions_dir / f"{OPENCLAW_SESSION_ID}.jsonl"
            ),
            "chatType": "direct",
            "sessionStartedAt": 1778320882571,
            "lastInteractionAt": 1778790212965,
            "status": "done",
            "modelProvider": "claude-cli",
            "origin": {
                "label": "Vivek Chand id:1532693273",
                "provider": "telegram",
                "surface": "telegram",
                "chatType": "direct",
            },
            "lastChannel": "telegram",
            "deliveryContext": {"channel": "telegram"},
            "systemPromptReport": {"workspaceDir": WORKSPACE_DIR},
        },
    }
    (sessions_dir / "sessions.json").write_text(
        json.dumps(sessions_idx),
    )

    # Top-level Claude Code transcript.
    proj_dir = fake_home / ".claude" / "projects" / ENCODED_CWD
    proj_dir.mkdir(parents=True)
    top_path = proj_dir / f"{CLAUDE_SESSION_ID}.jsonl"
    with open(top_path, "w") as f:
        for obj in TOP_LEVEL_LINES:
            f.write(json.dumps(obj) + "\n")

    # Subagents subdirectory.
    sess_dir = proj_dir / CLAUDE_SESSION_ID
    sub_dir = sess_dir / "subagents"
    sub_dir.mkdir(parents=True)
    sub_path = sub_dir / f"{SUBAGENT_FILE_STEM}.jsonl"
    with open(sub_path, "w") as f:
        for obj in SUBAGENT_LINES:
            f.write(json.dumps(obj) + "\n")

    # Tool-results subdirectory.
    tr_dir = sess_dir / "tool-results"
    tr_dir.mkdir(parents=True)
    for fname, body in TOOL_RESULT_FILES.items():
        (tr_dir / fname).write_text(body)

    return {
        "sessions_dir": str(sessions_dir),
        "top_path": top_path,
        "sub_dir": sub_dir,
        "sub_path": sub_path,
        "tr_dir": tr_dir,
    }


def test_index_walk_ingests_top_subagent_and_tool_results(
    sync_with_isolated_store,
):
    """End-to-end: sessions.json walk picks up all three classes (top-
    level transcript + sub-agent transcript + tool-results) and writes
    a sessions table row keyed by the OpenClaw UUID."""
    sync, ls, fake_home = sync_with_isolated_store
    layout = _setup_layout(fake_home)

    state: dict = {}
    ingested, handled = sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "node-test"},
        state,
        paths={"sessions_dir": layout["sessions_dir"]},
    )

    # 2 top-level lines + 2 subagent lines + 2 tool-results = 6 events.
    assert ingested == 6, f"expected 6 events, got {ingested}"
    # Handled set must contain the Claude UUID so the fallback path
    # skips this session.
    assert CLAUDE_SESSION_ID in handled

    store = ls.get_store()
    _wait_for_flush(store)

    # All six rows are filed under the OpenClaw session UUID, NOT the
    # Claude Code UUID. This is the key fix from #1226.
    rows = store.query_events(session_id=OPENCLAW_SESSION_ID, limit=100)
    assert len(rows) == 6, (
        f"expected 6 events under OpenClaw UUID, got {len(rows)}"
    )

    # No events under the bare Claude UUID (the buggy state from #1226).
    rows_bad = store.query_events(session_id=CLAUDE_SESSION_ID, limit=100)
    assert len(rows_bad) == 0, (
        "no events should be filed under the Claude UUID — that's the "
        "bug #1226 closed"
    )

    # Each row's ``data`` blob carries the Claude UUID for cross-ref.
    for r in rows:
        data = r["data"]
        if isinstance(data, str):
            data = json.loads(data)
        assert data.get("_claude_session_id") == CLAUDE_SESSION_ID, (
            "every row must embed the Claude session UUID for traceability"
        )
        assert data.get("_openclaw_session_id") == OPENCLAW_SESSION_ID

    # Sub-agent rows are typed with the ``subagent:`` prefix so Brain
    # can lane them separately.
    by_type: dict[str, int] = {}
    for r in rows:
        by_type[r["event_type"]] = by_type.get(r["event_type"], 0) + 1
    assert by_type.get("subagent:user") == 1, by_type
    assert by_type.get("subagent:assistant") == 1, by_type
    assert by_type.get("user") == 1, by_type
    assert by_type.get("assistant") == 1, by_type
    assert by_type.get("tool-result") == 2, by_type


def test_sessions_table_row_upserted_with_openclaw_uuid(
    sync_with_isolated_store,
):
    """A row in the typed ``sessions`` table is keyed by the OpenClaw
    session UUID and carries the title/started_at/status from the
    sessions.json metadata. This is what closes the Brain join issue
    in #1226."""
    sync, ls, fake_home = sync_with_isolated_store
    layout = _setup_layout(fake_home)

    sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "node-test"},
        {},
        paths={"sessions_dir": layout["sessions_dir"]},
    )

    store = ls.get_store()
    _wait_for_flush(store)

    sessions = store.query_sessions_table(agent_type="openclaw", limit=20)
    by_id = {s["session_id"]: s for s in sessions}
    assert OPENCLAW_SESSION_ID in by_id, (
        f"sessions table must contain a row for OpenClaw UUID "
        f"{OPENCLAW_SESSION_ID}; got {list(by_id.keys())}"
    )
    row = by_id[OPENCLAW_SESSION_ID]
    assert row["agent_type"] == "openclaw"
    assert row["agent_id"] == "main"
    # title pulled from origin.label
    assert "Vivek Chand" in (row.get("title") or ""), row
    # status mirrored from sessions.json
    assert row["status"] == "done"
    # message_count is computed-on-read against the events table — must
    # see all six events filed under this session_id.
    assert row["message_count"] == 6, row
    # metadata includes the cross-ref to the Claude UUID
    meta = row["metadata"] or {}
    assert meta.get("claude_session_id") == CLAUDE_SESSION_ID, meta
    assert meta.get("channel") == "telegram", meta


def test_idempotent_on_re_run(sync_with_isolated_store):
    """Calling the syncer twice with the same files → still 6 rows
    (event PRIMARY KEY dedup)."""
    sync, ls, fake_home = sync_with_isolated_store
    layout = _setup_layout(fake_home)

    for _ in range(2):
        sync.sync_openclaw_claude_sessions_via_index(
            {"node_id": "n"},
            {},  # discard state to prove dedup is on the row id
            paths={"sessions_dir": layout["sessions_dir"]},
        )

    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_events(session_id=OPENCLAW_SESSION_ID, limit=100)
    assert len(rows) == 6, f"expected 6 unique rows, got {len(rows)}"


def test_offset_tracking_picks_up_only_new_top_level_lines(
    sync_with_isolated_store,
):
    """Append a new line to the top-level transcript and re-run: only
    the new line is ingested (byte-offset state survives across calls)."""
    sync, ls, fake_home = sync_with_isolated_store
    layout = _setup_layout(fake_home)
    state: dict = {}

    first, _ = sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "n"}, state,
        paths={"sessions_dir": layout["sessions_dir"]},
    )
    assert first == 6

    # Append a fresh user turn to the top-level file.
    new_line = {
        "type": "user",
        "message": {"role": "user", "content": "follow-up"},
        "uuid": "evt-user-002",
        "timestamp": "2026-05-14T20:13:00.000Z",
        "sessionId": CLAUDE_SESSION_ID,
    }
    with open(layout["top_path"], "a") as f:
        f.write(json.dumps(new_line) + "\n")

    second, _ = sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "n"}, state,
        paths={"sessions_dir": layout["sessions_dir"]},
    )
    assert second == 1, f"expected 1 new row, got {second}"

    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_events(session_id=OPENCLAW_SESSION_ID, limit=100)
    assert len(rows) == 7


def test_skip_claude_ids_propagates_to_process_inspection(
    sync_with_isolated_store,
):
    """The index path returns the set of Claude UUIDs it handled; the
    process-inspection path must skip those so we don't double-write."""
    sync, ls, fake_home = sync_with_isolated_store
    layout = _setup_layout(fake_home)

    _, handled = sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "n"}, {},
        paths={"sessions_dir": layout["sessions_dir"]},
    )
    assert handled == {CLAUDE_SESSION_ID}

    # Now feed those same Claude UUIDs to the process-inspection path
    # via the skip set — it should short-circuit without touching the
    # filesystem.
    from unittest.mock import patch
    with patch.object(
        sync,
        "_discover_openclaw_claude_session_files",
        return_value=[(CLAUDE_SESSION_ID, str(layout["top_path"]))],
    ) as mock_disc:
        out = sync.sync_openclaw_claude_sessions(
            {"node_id": "n"}, {},
            paths={"sessions_dir": layout["sessions_dir"]},
            skip_claude_ids=handled,
        )
    assert out == 0
    mock_disc.assert_called_once()  # discovery still runs but is filtered


def test_walk_handles_missing_sessions_json(sync_with_isolated_store):
    """A fresh OpenClaw install with no sessions.json yet must not
    crash the daemon — return (0, set())."""
    sync, ls, fake_home = sync_with_isolated_store
    # Don't call _setup_layout — sessions.json doesn't exist.
    out, handled = sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "n"}, {}, paths={"sessions_dir": str(fake_home)},
    )
    assert out == 0
    assert handled == set()


def test_walk_handles_missing_claude_files(
    sync_with_isolated_store,
):
    """sessions.json carries a binding but Claude Code hasn't started
    writing yet (no top-level .jsonl, no subdir). Skip the binding
    silently — next cycle will pick it up."""
    sync, ls, fake_home = sync_with_isolated_store
    # Materialise sessions.json but skip the projects/ tree entirely.
    sessions_dir = fake_home / ".openclaw" / "agents" / "main" / "sessions"
    sessions_dir.mkdir(parents=True)
    (sessions_dir / "sessions.json").write_text(json.dumps({
        "agent:main:main": {
            "sessionId": OPENCLAW_SESSION_ID,
            "claudeCliSessionId": CLAUDE_SESSION_ID,
            "systemPromptReport": {"workspaceDir": WORKSPACE_DIR},
        },
    }))

    out, handled = sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "n"}, {},
        paths={"sessions_dir": str(sessions_dir)},
    )
    assert out == 0
    # Skipped, not handled — we don't want the fallback path skipping
    # this session either, since its claude process might be running.
    assert handled == set()


def test_tool_result_truncation_and_dedup(sync_with_isolated_store):
    """A multi-MB tool-result file is truncated to the cap, and a
    second pass on the same (mtime-stable) file does not re-emit."""
    sync, ls, fake_home = sync_with_isolated_store
    layout = _setup_layout(fake_home)
    # Replace one tool-result with a >cap blob.
    big_path = layout["tr_dir"] / "huge.txt"
    cap = sync._OC_CC_TOOL_RESULT_MAX_BYTES
    big_path.write_text("x" * (cap * 2))

    state: dict = {}
    first, _ = sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "n"}, state,
        paths={"sessions_dir": layout["sessions_dir"]},
    )
    # 2 top + 2 subagent + 3 tool-results (2 original + 1 huge) = 7.
    assert first == 7

    # Re-run with the same state — tool-results should NOT re-emit
    # because mtime hasn't changed.
    second, _ = sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "n"}, state,
        paths={"sessions_dir": layout["sessions_dir"]},
    )
    assert second == 0

    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_events(session_id=OPENCLAW_SESSION_ID, limit=100)
    big_rows = [
        r for r in rows
        if r["event_type"] == "tool-result"
        and "huge.txt" in (
            (r["data"] if isinstance(r["data"], dict)
             else json.loads(r["data"]))
        ).get("filename", "")
    ]
    assert len(big_rows) == 1
    data = big_rows[0]["data"]
    if isinstance(data, str):
        data = json.loads(data)
    assert data["truncated"] is True
    assert len(data["body"].encode("utf-8")) <= cap
    assert data["size_bytes"] == cap * 2


def test_escape_hatch_disables_index_path(
    sync_with_isolated_store, monkeypatch,
):
    """CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST=1 short-circuits the index
    path same as the process-inspection path."""
    sync, ls, fake_home = sync_with_isolated_store
    layout = _setup_layout(fake_home)
    monkeypatch.setenv("CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST", "1")
    out, handled = sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "n"}, {},
        paths={"sessions_dir": layout["sessions_dir"]},
    )
    assert out == 0
    assert handled == set()


def test_legacy_uuid_only_path_still_works(sync_with_isolated_store):
    """Back-compat: when ``_translate_claude_session_line`` is called WITHOUT
    ``openclaw_session_id`` (the process-inspection fallback path), the
    session_id falls back to the Claude Code UUID and ``kind`` defaults to
    ``"top"``. PR #1224's existing tests rely on this signature."""
    sync, ls, fake_home = sync_with_isolated_store
    obj = {
        "type": "user",
        "message": {"role": "user", "content": "hi"},
        "uuid": "evt-1",
        "timestamp": "2026-05-14T20:00:00Z",
    }
    row = sync._translate_claude_session_line(
        obj, session_id="claude-only-uuid", node_id="n", line_no=0,
    )
    assert row is not None
    assert row["session_id"] == "claude-only-uuid"
    assert row["event_type"] == "user"
    # data still carries the cross-ref so debugging works
    assert row["data"]["_claude_session_id"] == "claude-only-uuid"
