"""Tests for #3650 — NemoClaw advisor-session tool-execution retry/exhaustion lifecycle.

NemoClaw's advisor session runner drives terminal tool calls through a
retry/repair loop, emitting tool_execution_start / tool_execution_end (with
isError) per attempt and modeling terminal outcomes ('exhausted' vs 'success').
Before this fix NemoClawAdapter.list_events() never decoded the blob for those
event types, so a tool that failed twice then succeeded looked identical to a
single clean call.
"""
from __future__ import annotations

import importlib
import time
import uuid

import pytest


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.local_store as _ls
    importlib.reload(_ls)
    s = _ls.LocalStore()
    s.start()
    monkeypatch.setattr(_ls, "get_store", lambda *a, **kw: s)
    yield s
    s.stop(flush=True)


def _seed(store, session_id, event_type, data=None):
    store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "nemo+test-node",
        "agent_id": "advisor",
        "agent_type": "nemoclaw",
        "session_id": session_id,
        "event_type": event_type,
        "ts": time.time(),
        "data": data or {},
    })


def _wait_flush(s, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def test_tool_execution_start_surfaces_attempt_number(isolated_store):
    """tool_execution_start events must surface attemptNumber as attempt_number."""
    _seed(isolated_store, "sess-1", "tool_execution_start", {"attemptNumber": 1})
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-1")
    assert len(events) == 1
    assert events[0].extra.get("attempt_number") == 1


def test_tool_execution_end_retry_surfaces_all_fields(isolated_store):
    """tool_execution_end with isError=True and retryResponse='retry' must expose both fields."""
    _seed(isolated_store, "sess-2", "tool_execution_end", {
        "attemptNumber": 1,
        "isError": True,
        "retryResponse": "retry",
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-2")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("attempt_number") == 1
    assert ex.get("is_error") is True
    assert ex.get("retry_response") == "retry"


def test_tool_execution_end_success_preserves_is_error_false(isolated_store):
    """is_error=False must not be dropped; False distinguishes success from missing."""
    _seed(isolated_store, "sess-3", "tool_execution_end", {
        "attemptNumber": 2,
        "isError": False,
        "retryResponse": "success",
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-3")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("is_error") is False
    assert ex.get("retry_response") == "success"
    assert ex.get("attempt_number") == 2


def test_tool_execution_exhaustion(isolated_store):
    """retryResponse='exhausted' must be visible so the dashboard can flag exhausted tool calls."""
    _seed(isolated_store, "sess-4", "tool_execution_end", {
        "attemptNumber": 3,
        "isError": True,
        "retryResponse": "exhausted",
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-4")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("retry_response") == "exhausted"
    assert ex.get("is_error") is True
    assert ex.get("attempt_number") == 3


def test_plain_events_gain_no_spurious_retry_keys(isolated_store):
    """Regular session events without retry fields must not gain attempt_number etc."""
    _seed(isolated_store, "sess-5", "session.started", {"sessionId": "sess-5"})
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-5")
    assert len(events) == 1
    ex = events[0].extra
    assert "attempt_number" not in ex
    assert "is_error" not in ex
    assert "retry_response" not in ex


# ---------------------------------------------------------------------------
# Advisor output-state classification (#3840)
# emitAnalysisError / emitCommitProse / emitRepairProse each produce a
# distinct event type so the dashboard can distinguish the three advisor run
# outcomes.
# ---------------------------------------------------------------------------

def test_analysis_error_surfaces_output_type(isolated_store):
    """analysis_error events must expose output_type='analysis_error'."""
    _seed(isolated_store, "sess-6", "analysis_error", {"outputType": "analysis_error"})
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-6")
    assert len(events) == 1
    assert events[0].extra.get("output_type") == "analysis_error"


def test_commit_prose_surfaces_output_type(isolated_store):
    """commit_prose events must expose output_type='commit_prose'."""
    _seed(isolated_store, "sess-7", "commit_prose", {"outputType": "commit_prose"})
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-7")
    assert len(events) == 1
    assert events[0].extra.get("output_type") == "commit_prose"


def test_repair_prose_surfaces_output_type(isolated_store):
    """repair_prose events must expose output_type='repair_prose'."""
    _seed(isolated_store, "sess-8", "repair_prose", {"outputType": "repair_prose"})
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-8")
    assert len(events) == 1
    assert events[0].extra.get("output_type") == "repair_prose"


def test_output_type_derived_from_event_type_when_field_absent(isolated_store):
    """When outputType field is absent, output_type is derived from the event type."""
    _seed(isolated_store, "sess-9", "analysis_error", {})
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-9")
    assert len(events) == 1
    assert events[0].extra.get("output_type") == "analysis_error"


def test_screaming_snake_alias_surfaces_output_type(isolated_store):
    """ANALYSIS_ERROR (SCREAMING_SNAKE) alias must also surface output_type."""
    _seed(isolated_store, "sess-10", "ANALYSIS_ERROR", {"outputType": "analysis_error"})
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-10")
    assert len(events) == 1
    assert events[0].extra.get("output_type") == "analysis_error"


def test_output_state_events_gain_no_spurious_retry_keys(isolated_store):
    """Advisor output-state events must not gain attempt_number etc."""
    _seed(isolated_store, "sess-11", "commit_prose", {"outputType": "commit_prose"})
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-11")
    assert len(events) == 1
    ex = events[0].extra
    assert "attempt_number" not in ex
    assert "is_error" not in ex
    assert "retry_response" not in ex
    assert ex.get("output_type") == "commit_prose"
