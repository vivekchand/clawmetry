"""Regression test for issue #1231 — privacy boundary on the
``sync_openclaw_claude_sessions_via_index`` walk of ``~/.claude/projects/``.

Background: ``~/.claude/projects/<encoded-cwd>/`` is shared by EVERY ``claude``
CLI invocation from that directory, not just the ones OpenClaw spawned. The
only thing preventing a refactor from sweeping unrelated personal Claude
chats into the cloud-sync pipeline is the implicit boundary "we only walk
ids that came from sessions.json". This test pins that boundary down with
an explicit allowlist check.

If someone removes the ``_assert_claude_session_allowed`` guard or starts
deriving the session id from a directory glob, this test must fail.
"""

from __future__ import annotations

import importlib
import json
import os
import time
from pathlib import Path

import pytest


def _write_jsonl(path: Path, lines: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for obj in lines:
            f.write(json.dumps(obj) + "\n")


def _wait_for_flush(store, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError("flusher did not drain in time")


@pytest.fixture
def sync_with_isolated_store(tmp_path, monkeypatch):
    """Isolated DuckDB + fake ``~/.openclaw`` + fake ``~/.claude``."""
    openclaw_root = tmp_path / "openclaw"
    claude_root = tmp_path / "claude_cfg"
    openclaw_root.mkdir()
    claude_root.mkdir()

    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(openclaw_root))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_root))
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"),
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.delenv(
        "CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST", raising=False,
    )

    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    yield sync, ls, openclaw_root, claude_root
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _build_workspace(
    openclaw_root: Path,
    claude_root: Path,
    *,
    workspace_dir: str,
    allowed_claude_id: str,
    unrelated_claude_id: str,
    openclaw_session_id: str,
) -> tuple[Path, Path, Path]:
    """Lay out a fake ~/.openclaw + ~/.claude/projects state with:
      * exactly ONE binding in sessions.json (the "allowed" id)
      * a personal/unrelated transcript dir under the SAME encoded-cwd slug
        that is NOT referenced anywhere in sessions.json.

    Returns (allowed_top_jsonl, unrelated_top_jsonl, unrelated_subagent_jsonl).
    """
    # sessions.json — only references the allowed id.
    sessions_dir = openclaw_root / "agents" / "main" / "sessions"
    sessions_dir.mkdir(parents=True)
    sessions_json = sessions_dir / "sessions.json"
    sessions_json.write_text(json.dumps({
        "agent:main:main": {
            "sessionId": openclaw_session_id,
            "claudeCliSessionId": allowed_claude_id,
            "systemPromptReport": {"workspaceDir": workspace_dir},
            "sessionStartedAt": 1715000000000,
            "lastInteractionAt": 1715000005000,
            "status": "active",
        },
    }))

    # Encode the slug the same way Claude Code / sync.py does.
    from clawmetry import sync as sync_mod
    slug = sync_mod._encode_cwd_for_claude_projects(workspace_dir)
    projects_root = claude_root / "projects" / slug

    # ALLOWED transcript: 1 user line so the happy path produces a real row.
    allowed_top = projects_root / f"{allowed_claude_id}.jsonl"
    _write_jsonl(allowed_top, [{
        "type": "user",
        "message": {"role": "user", "content": "from-openclaw"},
        "uuid": "allowed-evt-1",
        "timestamp": "2026-05-15T10:00:00.000Z",
        "sessionId": allowed_claude_id,
    }])

    # UNRELATED transcript — a personal "claude" chat the user ran from the
    # same workspace dir. NOT referenced by sessions.json.
    unrelated_top = projects_root / f"{unrelated_claude_id}.jsonl"
    _write_jsonl(unrelated_top, [{
        "type": "user",
        "message": {
            "role": "user",
            "content": "SECRET-PERSONAL-CHAT-MUST-NOT-INGEST",
        },
        "uuid": "unrelated-evt-1",
        "timestamp": "2026-05-15T10:05:00.000Z",
        "sessionId": unrelated_claude_id,
    }])
    unrelated_subagent = (
        projects_root / unrelated_claude_id / "subagents" / "sub.jsonl"
    )
    _write_jsonl(unrelated_subagent, [{
        "type": "user",
        "message": {
            "role": "user",
            "content": "SECRET-SUBAGENT-MUST-NOT-INGEST",
        },
        "uuid": "unrelated-sub-1",
        "timestamp": "2026-05-15T10:06:00.000Z",
        "sessionId": unrelated_claude_id,
    }])
    return allowed_top, unrelated_top, unrelated_subagent


def test_unrelated_claude_session_in_same_slug_is_never_ingested(
    sync_with_isolated_store,
):
    """The crawl must touch ONLY the claude_session_id listed in
    sessions.json, even when another transcript exists in the same
    encoded-cwd directory."""
    sync, ls, openclaw_root, claude_root = sync_with_isolated_store
    workspace_dir = str(openclaw_root / "workspace")

    allowed_id = "11111111-aaaa-bbbb-cccc-111111111111"
    unrelated_id = "99999999-dead-beef-cafe-999999999999"
    oc_id = "oc-session-uuid-abc"

    _build_workspace(
        openclaw_root, claude_root,
        workspace_dir=workspace_dir,
        allowed_claude_id=allowed_id,
        unrelated_claude_id=unrelated_id,
        openclaw_session_id=oc_id,
    )

    ingested, handled = sync.sync_openclaw_claude_sessions_via_index(
        {"node_id": "node-test"}, state={}, paths=None,
    )

    # Happy path: the bound session produced exactly its 1 line.
    assert ingested == 1, f"expected 1 allowed row, got {ingested}"
    assert handled == {allowed_id}, (
        f"handled set should contain ONLY the allowed id; got {handled}"
    )

    store = ls.get_store()
    _wait_for_flush(store)

    # The allowed row exists, tagged under the OpenClaw session UUID.
    allowed_rows = store.query_events(session_id=oc_id)
    assert any(
        "from-openclaw" in json.dumps(r.get("data") or {})
        for r in allowed_rows
    ), "expected the allowed row to land under the OpenClaw session id"

    # Privacy assertion: the unrelated transcript's content must appear in
    # ZERO rows. We scan every event in the store, not just one session id,
    # so a future bug that ingests under a different session_id still fails.
    all_rows = store.query_events(limit=10000)
    for r in all_rows:
        blob = json.dumps(r.get("data") or {})
        assert "SECRET-PERSONAL-CHAT-MUST-NOT-INGEST" not in blob, (
            f"privacy leak: unrelated top-level transcript ingested: {r}"
        )
        assert "SECRET-SUBAGENT-MUST-NOT-INGEST" not in blob, (
            f"privacy leak: unrelated subagent transcript ingested: {r}"
        )


def test_path_helpers_refuse_session_id_outside_allowlist(
    sync_with_isolated_store,
):
    """Direct unit test of the guard: calling either path helper with a
    session id that isn't in the allowlist must raise. This is the line of
    defence that pins the boundary against future refactors."""
    sync, _ls, openclaw_root, _claude_root = sync_with_isolated_store

    workspace = str(openclaw_root / "workspace")
    allowed = {"a-allowed-id"}

    # Happy path: allowed id constructs a path without raising.
    p1 = sync._claude_session_dir(workspace, "a-allowed-id", allowed)
    p2 = sync._claude_session_top_level_path(
        workspace, "a-allowed-id", allowed,
    )
    assert "a-allowed-id" in str(p1)
    assert "a-allowed-id" in str(p2)

    # Privacy gate: an id NOT in the allowlist must raise PermissionError.
    with pytest.raises(PermissionError):
        sync._claude_session_dir(workspace, "evil-personal-id", allowed)
    with pytest.raises(PermissionError):
        sync._claude_session_top_level_path(
            workspace, "evil-personal-id", allowed,
        )

    # Empty allowlist rejects every id.
    with pytest.raises(PermissionError):
        sync._claude_session_dir(workspace, "anything", set())
