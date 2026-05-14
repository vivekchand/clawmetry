"""Tests for sync_openclaw_claude_sessions — the process-discovered Claude
Code session JSONL ingest path (PR release/openclaw-claude-session-ingest).

This is the missing capture path the user observed: OpenClaw delegates to a
``claude`` CLI subprocess that writes its transcript to
``~/.claude/projects/<encoded-cwd>/<session-id>.jsonl``. The legacy
``sync_claude_cli_sessions`` only fires when ``sessions.json`` carries the
binding; this complementary path discovers the file by inspecting the
running subprocess directly so capture works even when the index is stale.

We mock process discovery (the production path uses psutil) so the test
runs deterministically in CI without needing a real ``claude`` process.
"""

from __future__ import annotations

import importlib
import json
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def sync_with_isolated_store(tmp_path, monkeypatch):
    """Reload sync + local_store with an isolated DuckDB per test."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH",
        str(tmp_path / "events.duckdb"),
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    # Make sure the escape hatch is OFF for the test (default-on behavior).
    monkeypatch.delenv("CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST", raising=False)
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
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


def _write_synthetic_session(jsonl_path: Path, session_id: str, lines: list[dict]):
    """Write JSONL lines to disk in Claude Code's exact shape."""
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for obj in lines:
            f.write(json.dumps(obj) + "\n")


# ── Synthetic Claude Code session shape ────────────────────────────────────
# Minimal but faithful to the real lines in
# ~/.claude/projects/-Users-vivek--openclaw-workspace/<id>.jsonl.
SAMPLE_LINES = [
    # 1. user-role inbound (the "hello, how are you?" line shape)
    {
        "parentUuid": None,
        "isSidechain": False,
        "promptId": "p-001",
        "type": "user",
        "message": {
            "role": "user",
            "content": "hello, how are you?",
        },
        "uuid": "evt-user-001",
        "timestamp": "2026-05-14T20:12:45.580Z",
        "cwd": "/Users/test/.openclaw/workspace",
        "sessionId": "11111111-2222-3333-4444-555555555555",
    },
    # 2. assistant-role response with usage block (cost/tokens flow)
    {
        "parentUuid": "evt-user-001",
        "isSidechain": False,
        "type": "assistant",
        "message": {
            "model": "claude-opus-4-7",
            "id": "msg_abc",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Doing well, thanks!"}],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 1,
                "cache_read_input_tokens": 100,
                "output_tokens": 12,
                "totalTokens": 113,
                "cost": {"total": 0.000456},
            },
        },
        "uuid": "evt-asst-001",
        "timestamp": "2026-05-14T20:12:50.000Z",
        "cwd": "/Users/test/.openclaw/workspace",
        "sessionId": "11111111-2222-3333-4444-555555555555",
    },
    # 3. system / queue-operation control event
    {
        "type": "queue-operation",
        "operation": "dequeue",
        "timestamp": "2026-05-14T20:12:51.000Z",
        "sessionId": "11111111-2222-3333-4444-555555555555",
    },
]


def _setup_fake_session_file(tmp_path: Path) -> tuple[str, Path]:
    """Create a synthetic Claude Code session jsonl under a temp project dir."""
    session_id = "11111111-2222-3333-4444-555555555555"
    encoded_cwd = "-Users-test--openclaw-workspace"
    jsonl_path = tmp_path / "claude-projects" / encoded_cwd / f"{session_id}.jsonl"
    _write_synthetic_session(jsonl_path, session_id, SAMPLE_LINES)
    return session_id, jsonl_path


def test_three_synthetic_lines_land_in_events(sync_with_isolated_store, tmp_path):
    """Synthetic 3-line session → 3 rows in the events table with the
    right shape."""
    sync, ls = sync_with_isolated_store
    session_id, jsonl_path = _setup_fake_session_file(tmp_path)

    # Mock process discovery to return our synthetic file.
    with patch.object(
        sync,
        "_discover_openclaw_claude_session_files",
        return_value=[(session_id, str(jsonl_path))],
    ):
        state = {}
        ingested = sync.sync_openclaw_claude_sessions(
            {"node_id": "node-test"}, state, paths=None,
        )

    assert ingested == 3, f"expected 3 events, got {ingested}"

    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_events(session_id=session_id)
    assert len(rows) == 3

    # Re-key by event_type for inspection.
    by_type: dict[str, dict] = {r["event_type"]: r for r in rows}
    assert "user" in by_type
    assert "assistant" in by_type
    assert "queue-operation" in by_type

    user_row = by_type["user"]
    assert user_row["session_id"] == session_id
    assert user_row["agent_id"] == "main"
    assert user_row["ts"] == "2026-05-14T20:12:45.580Z"
    # data carries the full original line so detail extraction works
    data = user_row["data"]
    if isinstance(data, str):
        data = json.loads(data)
    assert data["message"]["content"] == "hello, how are you?"

    asst_row = by_type["assistant"]
    assert asst_row["model"] == "claude-opus-4-7"
    assert asst_row["token_count"] == 113
    assert asst_row["cost_usd"] is not None
    assert round(float(asst_row["cost_usd"]), 6) == 0.000456


def test_idempotent_on_re_run(sync_with_isolated_store, tmp_path):
    """Calling the syncer twice with the same file → still 3 rows
    (INSERT OR IGNORE on event id)."""
    sync, ls = sync_with_isolated_store
    session_id, jsonl_path = _setup_fake_session_file(tmp_path)

    # Two calls: simulate the daemon's loop running twice. We DON'T pass
    # the same state dict the second time, to prove that even with state
    # loss we don't dupe (the row id is deterministic).
    for _ in range(2):
        with patch.object(
            sync,
            "_discover_openclaw_claude_session_files",
            return_value=[(session_id, str(jsonl_path))],
        ):
            sync.sync_openclaw_claude_sessions({"node_id": "n"}, {}, paths=None)

    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_events(session_id=session_id)
    assert len(rows) == 3, f"expected 3 unique rows, got {len(rows)}"


def test_offset_tracking_picks_up_only_new_lines(sync_with_isolated_store, tmp_path):
    """First call ingests 3 rows; appending a 4th line and re-running
    ingests ONLY the new line."""
    sync, ls = sync_with_isolated_store
    session_id, jsonl_path = _setup_fake_session_file(tmp_path)

    state: dict = {}
    with patch.object(
        sync,
        "_discover_openclaw_claude_session_files",
        return_value=[(session_id, str(jsonl_path))],
    ):
        first = sync.sync_openclaw_claude_sessions(
            {"node_id": "n"}, state, paths=None,
        )
    assert first == 3

    # Append a 4th line (a fresh user turn).
    new_line = {
        "type": "user",
        "message": {"role": "user", "content": "follow-up"},
        "uuid": "evt-user-002",
        "timestamp": "2026-05-14T20:13:00.000Z",
        "sessionId": session_id,
    }
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(new_line) + "\n")

    with patch.object(
        sync,
        "_discover_openclaw_claude_session_files",
        return_value=[(session_id, str(jsonl_path))],
    ):
        second = sync.sync_openclaw_claude_sessions(
            {"node_id": "n"}, state, paths=None,
        )
    assert second == 1, f"expected 1 new row, got {second}"

    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_events(session_id=session_id)
    assert len(rows) == 4


def test_escape_hatch_disables_ingest(sync_with_isolated_store, tmp_path, monkeypatch):
    """CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST=1 short-circuits the syncer."""
    sync, ls = sync_with_isolated_store
    session_id, jsonl_path = _setup_fake_session_file(tmp_path)
    monkeypatch.setenv("CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST", "1")

    with patch.object(
        sync,
        "_discover_openclaw_claude_session_files",
        return_value=[(session_id, str(jsonl_path))],
    ) as mock_disc:
        out = sync.sync_openclaw_claude_sessions({"node_id": "n"}, {}, paths=None)

    assert out == 0
    # Discovery should not even have run when the escape hatch is set.
    mock_disc.assert_not_called()


def test_encode_cwd_matches_claude_code_convention():
    """Sanity-check the slug encoder against known examples."""
    from clawmetry import sync as sync_mod
    enc = sync_mod._encode_cwd_for_claude_projects
    # macOS user with the OpenClaw default workspace.
    assert (
        enc("/Users/vivek/.openclaw/workspace")
        == "-Users-vivek--openclaw-workspace"
    )
    # Linux user.
    assert (
        enc("/home/alice/.openclaw/workspace")
        == "-home-alice--openclaw-workspace"
    )
    # Path with a single dot in it.
    assert enc("/srv/app.dir/work") == "-srv-app-dir-work"


def test_translate_handles_lines_without_timestamp(sync_with_isolated_store):
    """Lines lacking ``timestamp`` are silently dropped — the events
    table indexes on ts so storing NULL would corrupt the read path."""
    sync, ls = sync_with_isolated_store
    bad = {"type": "user", "message": {"role": "user", "content": "hi"}}
    out = sync._translate_claude_session_line(
        bad, session_id="s", node_id="n", line_no=0,
    )
    assert out is None


def test_e2e_against_real_user_file_if_present(sync_with_isolated_store):
    """If the live user file is on the test machine (vivek's box only), do
    an end-to-end ingest pass and assert the 22:12 'hello, how are you?'
    line landed.

    Skipped on every CI runner — purely a local smoke test.
    """
    real_path = Path(
        "/Users/vivek/.claude/projects/"
        "-Users-vivek--openclaw-workspace/"
        "49f1d9fc-0848-4b6b-8fd7-64633bbc6b58.jsonl"
    )
    if not real_path.is_file():
        pytest.skip("real user session file not on this host")
    sync, ls = sync_with_isolated_store
    session_id = real_path.stem
    with patch.object(
        sync,
        "_discover_openclaw_claude_session_files",
        return_value=[(session_id, str(real_path))],
    ):
        sync.sync_openclaw_claude_sessions({"node_id": "n"}, {}, paths=None)
    store = ls.get_store()
    _wait_for_flush(store, timeout=10)
    rows = store.query_events(session_id=session_id, limit=2000)
    assert len(rows) > 0
    # Surface the user's known 22:12 line.
    matched = [
        r for r in rows
        if isinstance(r.get("data"), (dict, str))
        and "hello, how are you?" in (
            json.dumps(r["data"]) if isinstance(r["data"], dict) else r["data"]
        )
    ]
    assert matched, "did not find the user's 22:12 'hello, how are you?' line"
