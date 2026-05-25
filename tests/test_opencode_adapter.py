"""Tests for OpencodeAdapter (clawmetry/adapters/opencode.py).

Validates against a real captured opencode 1.15.x SQLite store (the fixture
``tests/fixtures/runtimes/opencode/opencode.db`` was produced by running
opencode headless against a local Ollama provider — three real sessions:
a hello-world, a print() explanation, and a one-word "pong" reply).

  - detect() reports detected + the right session_count, never raises
  - list_sessions() returns all three sessions, newest first, with the model
    id and provider parsed out of the session.model JSON object
  - tokens come from the session's tokens_* columns; cost is the real 0.0
    recorded for local Ollama models (so COST capability is honest)
  - list_events() yields ordered event types: user message, assistant
    thinking (reasoning part), assistant message (text part), and
    tool_call + tool_result for the tool parts
  - the adapter never raises on a missing or garbage database file
"""
from __future__ import annotations

import os
import sqlite3

import pytest

from clawmetry.adapters.base import Capability
from clawmetry.adapters.opencode import OpencodeAdapter

_FIXTURE_DB = os.path.join(
    os.path.dirname(__file__),
    "fixtures",
    "runtimes",
    "opencode",
    "opencode.db",
)

# Real captured session ids (newest -> oldest by time_updated).
_SID_PONG = "ses_19f202ce8ffewinb8V7QzrOtYs"      # qwen3:8b, pong reply
_SID_PRINT = "ses_19f20e199ffeaQgEKieQOxEXiK"     # llama3.2, print() + glob tool
_SID_HELLO = "ses_19f21ab0effeyPYrBvBz79SSog"     # llama3.2, hello-world + write tool


@pytest.fixture
def adapter() -> OpencodeAdapter:
    return OpencodeAdapter(db_path=_FIXTURE_DB)


# -- detect ------------------------------------------------------------------


def test_detect_detected_and_counts(adapter):
    result = adapter.detect()
    assert result.detected is True
    assert result.running is False
    assert result.name == "opencode"
    assert result.display_name == "opencode"
    assert result.session_count == 3
    assert result.meta["dbPath"] == _FIXTURE_DB


def test_detect_false_when_db_absent(tmp_path):
    """detect() must not raise and reports detected=False with no DB/dir."""
    a = OpencodeAdapter(db_path=str(tmp_path / "no-such" / "opencode.db"))
    result = a.detect()
    assert result.detected is False
    assert result.session_count == 0


# -- list_sessions -----------------------------------------------------------


def test_list_sessions_count_and_order(adapter):
    sessions = adapter.list_sessions()
    assert len(sessions) == 3
    # Newest first by time_updated: pong (latest) then print then hello.
    assert sessions[0].id == _SID_PONG
    assert sessions[1].id == _SID_PRINT
    assert sessions[2].id == _SID_HELLO


def test_list_sessions_model_and_provider_parsed(adapter):
    by_id = {s.id: s for s in adapter.list_sessions()}
    assert by_id[_SID_PONG].model == "qwen3:8b"
    assert by_id[_SID_PONG].source == "ollama"
    assert by_id[_SID_HELLO].model == "llama3.2:latest"
    assert by_id[_SID_HELLO].source == "ollama"


def test_list_sessions_title_and_timestamps(adapter):
    by_id = {s.id: s for s in adapter.list_sessions()}
    hello = by_id[_SID_HELLO]
    assert hello.title == "One line Python Hello World example"
    assert hello.display_name == hello.title
    # epoch-ms in the DB must be converted to float seconds (~1.78e9).
    assert 1.7e9 < hello.started_at < 2.0e9
    assert hello.ended_at is not None
    assert hello.ended_at >= hello.started_at


def test_list_sessions_tokens_and_cost(adapter):
    by_id = {s.id: s for s in adapter.list_sessions()}
    hello = by_id[_SID_HELLO]
    # Real captured token counts for the hello-world turn.
    assert hello.input_tokens == 6684
    assert hello.output_tokens == 29
    assert hello.total_tokens == 6684 + 29
    # Local Ollama model -> opencode records cost 0.0 (real, not None).
    assert hello.cost_usd == 0.0
    assert hello.message_count == 2


# -- list_events -------------------------------------------------------------


def test_list_events_ordered_roles(adapter):
    events = adapter.list_events(_SID_PONG)
    types = [(e.type, e.role) for e in events]
    # user prompt -> assistant reasoning -> assistant text reply.
    assert types == [
        ("message", "user"),
        ("thinking", "assistant"),
        ("message", "assistant"),
    ]
    # Chronological, non-decreasing timestamps.
    ts = [e.ts for e in events]
    assert ts == sorted(ts)
    assert events[-1].content == "pong"


def test_list_events_tool_call_and_result(adapter):
    events = adapter.list_events(_SID_PRINT)
    calls = [e for e in events if e.type == "tool_call"]
    results = [e for e in events if e.type == "tool_result"]
    assert any(e.tool_name == "glob" for e in calls)
    assert results, "expected a tool_result for the completed glob call"
    glob_result = next(e for e in results if e.tool_name == "glob")
    assert glob_result.content == "No files found"
    assert glob_result.extra.get("isError") is False
    assert glob_result.role == "tool"


def test_list_events_tool_error_surfaced(adapter):
    events = adapter.list_events(_SID_HELLO)
    results = [e for e in events if e.type == "tool_result"]
    assert results
    err = results[0]
    assert err.extra.get("isError") is True
    assert "rejected permission" in err.content


# -- capabilities ------------------------------------------------------------


def test_capabilities(adapter):
    caps = adapter.capabilities()
    assert Capability.SESSIONS in caps
    assert Capability.EVENTS in caps
    # COST is honest here: opencode stores token + cost columns on disk.
    assert Capability.COST in caps


# -- never raises ------------------------------------------------------------


def test_never_raises_on_missing_db(tmp_path):
    # Point at a DB whose parent dir also does not exist, so neither the file
    # nor the data dir is present (a present data dir alone counts as
    # "installed but no sessions yet" and is reported detected on purpose).
    a = OpencodeAdapter(db_path=str(tmp_path / "no-such-dir" / "missing.db"))
    assert a.detect().detected is False
    assert a.list_sessions() == []
    assert a.list_events("anything") == []


def test_never_raises_on_garbage_db(tmp_path):
    bad = tmp_path / "garbage.db"
    bad.write_bytes(b"this is not a sqlite database at all\x00\x01\x02")
    a = OpencodeAdapter(db_path=str(bad))
    # detect() may report the file exists, but reading must degrade to empty.
    a.detect()
    assert a.list_sessions() == []
    assert a.list_events("anything") == []


def test_never_raises_on_db_missing_tables(tmp_path):
    """An opencode DB with an unexpected/empty schema yields empty, not error."""
    p = tmp_path / "empty.db"
    conn = sqlite3.connect(str(p))
    conn.execute("CREATE TABLE unrelated (x int)")
    conn.commit()
    conn.close()
    a = OpencodeAdapter(db_path=str(p))
    # detect() must not raise; no session table -> count 0.
    res = a.detect()
    assert res.session_count == 0
    assert a.list_sessions() == []
    assert a.list_events("anything") == []
