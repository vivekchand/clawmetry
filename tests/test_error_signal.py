"""Benign tool-error filtering (#2196).

A number of tool results carry an ``isError`` flag for outcomes that are not
real failures (runtime read-guards, transient gateway timeouts). They were
inflating error counts across Tracing / Health / Self-Evolve and the snapshot.
``clawmetry.error_signal`` is the single classifier; new events are corrected at
ingest and ``backfill_benign_errors`` heals the history.
"""
from __future__ import annotations

import importlib
import json
import time

from clawmetry import error_signal as es


# ── pure classifier ────────────────────────────────────────────────────────

def test_benign_signatures_match_case_insensitively():
    assert es.is_benign_tool_error("File has not been read yet")
    assert es.is_benign_tool_error(
        "<tool_use_error>File has been modified since read, either by the user "
        "or by a linter. Read it again.</tool_use_error>"
    )
    assert es.is_benign_tool_error("Gateway TIMEOUT after 30000ms")  # mixed case


def test_real_errors_are_not_benign():
    for txt in (
        "Exit code 1\nTraceback (most recent call last): ...",
        "fatal: not a git repository",
        '{"status":"error","message":"permission denied"}',
        "",
        None,
        12345,  # non-string input must not raise
    ):
        assert not es.is_benign_tool_error(txt)


def test_extract_tool_result_text_across_shapes():
    # v3 flattened string fields
    assert "modified since read" in es.extract_tool_result_text(
        {"output": "File has been modified since read"}
    )
    # Claude Code content as a plain string
    assert es.extract_tool_result_text({"content": "hello"}) == "hello"
    # Claude Code content as a list of blocks
    assert "guard" in es.extract_tool_result_text(
        {"content": [{"type": "text", "text": "guard"}]}
    )
    # garbage in -> "" out, never raises
    assert es.extract_tool_result_text("not a dict") == ""
    assert es.extract_tool_result_text(None) == ""


def test_corrected_is_error_truth_table():
    assert es.corrected_is_error(True, "File has been modified since read") is False
    assert es.corrected_is_error(True, "Exit code 1: traceback") is True
    assert es.corrected_is_error(False, "anything") is False
    assert es.corrected_is_error(None, "File has not been read yet") is False


# ── backfill integration ────────────────────────────────────────────────────

def _wait_flush(store, t=3.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ev.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "2")
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)  # in-process writer
    return ls, ls.get_store()


def _data(store, eid):
    rows = store._fetch("SELECT data FROM events WHERE id = ?", [eid])
    if not rows:
        return None
    blob = rows[0][0]
    if isinstance(blob, (bytes, bytearray)):
        blob = bytes(blob).decode("utf-8", "replace")
    return json.loads(blob)


def test_backfill_clears_benign_keeps_real(tmp_path, monkeypatch):
    ls, store = _store(tmp_path, monkeypatch)
    try:
        # Benign read-guard flagged as error (Claude Code family shape).
        store.ingest({
            "id": "claude_code:benign-1",
            "node_id": "n", "agent_id": "main",
            "session_id": "claude_code:s1",
            "event_type": "tool_result",
            "ts": "2026-05-26T12:00:00Z",
            "data": {
                "role": "tool", "_runtime": "claude_code",
                "content": "<tool_use_error>File has been modified since read</tool_use_error>",
                "extra": {"isError": True},
            },
            "cost_usd": None, "token_count": 0, "model": None,
        })
        # A genuine failure that must stay an error.
        store.ingest({
            "id": "claude_code:real-1",
            "node_id": "n", "agent_id": "main",
            "session_id": "claude_code:s1",
            "event_type": "tool_result",
            "ts": "2026-05-26T12:01:00Z",
            "data": {
                "role": "tool", "_runtime": "claude_code",
                "content": "Exit code 1\nTraceback (most recent call last): ...",
                "extra": {"isError": True},
            },
            "cost_usd": None, "token_count": 0, "model": None,
        })
        _wait_flush(store)

        _, updated, scanned = store.backfill_benign_errors(after_id="", batch=100)
        assert scanned == 2
        assert updated == 1, f"only the benign row should be rewritten, got {updated}"

        benign = _data(store, "claude_code:benign-1")
        assert benign["extra"]["isError"] is False
        assert benign.get("benign_error") is True

        real = _data(store, "claude_code:real-1")
        assert real["extra"]["isError"] is True
        assert not real.get("benign_error")

        # Idempotent: a second pass rewrites nothing.
        _, updated2, _ = store.backfill_benign_errors(after_id="", batch=100)
        assert updated2 == 0
    finally:
        store.stop(flush=True)
