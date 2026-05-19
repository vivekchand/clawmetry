"""Forward-progress signal (issue #1707).

Tests the per-session ``tokens / state_deltas`` ratio that distinguishes
productive token burn from spinning. The existing token-velocity alert
fires on any busy agent; this signal only fires when the agent burns N
tokens with ZERO new tools / new files / new error types in the window.
"""

from __future__ import annotations

import importlib
import time
import uuid

import pytest


# ── fixture ───────────────────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh isolated DuckDB store per test."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


def _wait_flush(s, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError("flusher did not drain ring")


def _ingest_assistant_with_tokens(s, *, sid: str, ts: str, input_tokens: int,
                                  output_tokens: int = 0):
    """One billable assistant turn — populates ``data.message.usage``
    so ``_extract_usage_splits`` yields a positive total."""
    s.ingest({
        "id":         f"asst-{uuid.uuid4()}",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "assistant",
        "ts":         ts,
        "data":       {
            "message": {
                "role":  "assistant",
                "usage": {
                    "input_tokens":  input_tokens,
                    "output_tokens": output_tokens,
                },
            },
        },
        "token_count": input_tokens + output_tokens,
    })


def _ingest_tool_call(s, *, sid: str, ts: str, name: str, file_path: str = ""):
    """One top-level v3 tool.call event. Optional file_path drives the
    second class of state delta (new file touched)."""
    inp = {"file_path": file_path} if file_path else {}
    s.ingest({
        "id":         f"tool-{uuid.uuid4()}",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "tool.call",
        "ts":         ts,
        "data":       {"name": name, "input": inp},
    })


# ── unit cases the issue spells out ────────────────────────────────────────


def test_spinning_session_yields_high_ratio(store):
    """100k tokens with state_deltas=1 (one tool, no new files) -> ratio=100000.

    This is the genuine spinning signal: lots of burn, almost no new
    state. Badge should land in the red bucket.
    """
    sid = "spin-1"
    # 10 assistant turns x 10k input = 100k tokens, 1 distinct tool ever.
    for i in range(10):
        _ingest_assistant_with_tokens(
            store, sid=sid,
            ts=f"2026-05-15T10:{i:02d}:00+00:00",
            input_tokens=10_000,
        )
    _ingest_tool_call(
        store, sid=sid, ts="2026-05-15T10:00:30+00:00", name="grep",
    )
    _wait_flush(store)

    rows = store.query_forward_progress(since="2026-05-15T00:00:00Z")
    by_sid = {r["session_id"]: r for r in rows}
    r = by_sid[sid]
    assert r["tokens"] == 100_000
    assert r["state_deltas"] == 1
    assert r["ratio"] == 100_000.0


def test_productive_session_yields_low_ratio(store):
    """100k tokens with state_deltas=20 -> ratio=5000.

    Twenty distinct file paths touched in the window means real progress.
    Badge should land at the green/yellow boundary.
    """
    sid = "prod-1"
    for i in range(10):
        _ingest_assistant_with_tokens(
            store, sid=sid,
            ts=f"2026-05-15T11:{i:02d}:00+00:00",
            input_tokens=10_000,
        )
    # 20 distinct file paths, all on the same tool name. Each new path
    # counts as one state delta.
    for i in range(20):
        _ingest_tool_call(
            store, sid=sid,
            ts=f"2026-05-15T11:{i:02d}:30+00:00",
            name="Read",
            file_path=f"/tmp/file_{i}.py",
        )
    _wait_flush(store)

    rows = store.query_forward_progress(since="2026-05-15T00:00:00Z")
    by_sid = {r["session_id"]: r for r in rows}
    r = by_sid[sid]
    assert r["tokens"] == 100_000
    # 1 tool name (Read) + 20 file paths = 21 deltas. Ratio still well
    # under the 50k threshold.
    assert r["state_deltas"] == 21
    assert r["ratio"] == pytest.approx(100_000.0 / 21)
    assert r["ratio"] < 5_000


def test_empty_session_returns_no_row(store):
    """Sessions with zero billable tokens in the window are dropped
    entirely — never a divide-by-zero, never a ratio=inf row."""
    sid = "empty-1"
    # Only tool calls, no assistant turns with usage. Tokens=0 so the
    # session should not appear in the result at all.
    _ingest_tool_call(
        store, sid=sid, ts="2026-05-15T12:00:00+00:00", name="Bash",
    )
    _wait_flush(store)

    rows = store.query_forward_progress(since="2026-05-15T00:00:00Z")
    assert sid not in {r["session_id"] for r in rows}


def test_error_event_counts_as_state_delta(store):
    """A new error type surfaced in the window counts as a state delta —
    keeps the signal honest for agents that legitimately learn from
    failed tool calls."""
    sid = "err-1"
    _ingest_assistant_with_tokens(
        store, sid=sid, ts="2026-05-15T13:00:00+00:00",
        input_tokens=10_000,
    )
    # Error event surfaces a new error class.
    store.ingest({
        "id":         f"e-{uuid.uuid4()}",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "error.timeout",
        "ts":         "2026-05-15T13:00:30+00:00",
        "data":       {"message": "tool call timed out"},
    })
    _wait_flush(store)

    rows = store.query_forward_progress(since="2026-05-15T00:00:00Z")
    by_sid = {r["session_id"]: r for r in rows}
    r = by_sid[sid]
    assert r["state_deltas"] >= 1
    assert r["tokens"] == 10_000


def test_since_until_window_filter(store):
    """Events outside [since, until] must not contribute. Keeps the
    10-minute rolling window honest for the unproductive_burn alert."""
    sid = "win-1"
    _ingest_assistant_with_tokens(
        store, sid=sid, ts="2026-05-15T08:00:00+00:00",
        input_tokens=10_000,
    )
    _ingest_assistant_with_tokens(
        store, sid=sid, ts="2026-05-15T14:00:00+00:00",
        input_tokens=20_000,
    )
    _wait_flush(store)

    rows = store.query_forward_progress(
        since="2026-05-15T13:00:00Z",
        until="2026-05-15T15:00:00Z",
    )
    by_sid = {r["session_id"]: r for r in rows}
    assert by_sid[sid]["tokens"] == 20_000


def test_session_id_filter(store):
    """Passing ``session_id`` returns exactly that session's row."""
    _ingest_assistant_with_tokens(
        store, sid="A", ts="2026-05-15T15:00:00+00:00", input_tokens=10_000,
    )
    _ingest_assistant_with_tokens(
        store, sid="B", ts="2026-05-15T15:01:00+00:00", input_tokens=20_000,
    )
    _wait_flush(store)

    rows = store.query_forward_progress(
        since="2026-05-15T00:00:00Z", session_id="B",
    )
    assert len(rows) == 1
    assert rows[0]["session_id"] == "B"
    assert rows[0]["tokens"] == 20_000
