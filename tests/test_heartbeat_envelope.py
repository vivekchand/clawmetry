"""Issue #1652 — heartbeat envelope plaintext activity counters."""
from __future__ import annotations

import importlib
import os
import sys
import time
import uuid
from datetime import datetime, timezone

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def sync_with_store(tmp_path, monkeypatch):
    """Reload ``clawmetry.sync`` + ``clawmetry.local_store`` against a
    fresh DuckDB. Yields (sync_module, local_store_module, config)."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    config = {
        "node_id":         "node-test",
        "api_key":         "cm_test",
        "encryption_key":  s.generate_encryption_key(),
    }

    yield s, ls, config

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _drain_ring(store, max_wait_secs: float = 4.0) -> None:
    """Block until the background flusher has drained the ring buffer."""
    deadline = time.time() + max_wait_secs
    while time.time() < deadline:
        try:
            if store.health()["ring_depth"] == 0:
                return
        except Exception:
            return
        time.sleep(0.05)


def _today_iso(seconds_into_day: int = 0) -> str:
    """A UTC ISO timestamp inside today, deliberately at midnight + N sec
    so even tests run a few ms before/after rollover still land in-day."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=12, minute=0, second=0, microsecond=0)
    return start.replace(second=(seconds_into_day % 60)).isoformat()


# ── 1. shape: helper returns the documented dict ────────────────────────────

def test_helper_returns_five_int_fields_on_empty_store(sync_with_store):
    s, _ls, _config = sync_with_store
    out = s._collect_activity_counters_today()
    assert isinstance(out, dict), "helper must return a dict (or None)"
    for field in (
        "tool_calls_today", "exec_calls_today", "browser_actions_today",
        "unique_tools_today", "messages_today",
    ):
        assert field in out, f"missing field: {field}"
        assert isinstance(out[field], int), f"{field} must be int"
        assert out[field] >= 0, f"{field} must be >= 0"
    # Empty store → every count is exactly zero.
    assert sum(out.values()) == 0


# ── 2. math: counters reflect seeded events ────────────────────────────────

def test_helper_counts_tool_calls_exec_browser_messages(sync_with_store):
    s, ls, _config = sync_with_store
    store = ls.get_store()

    # 3 tool calls: one Bash (exec), one browser_action (browser), one Read.
    seed = [
        ("tool.call", {"name": "Bash"}),
        ("tool.call", {"name": "browser_action"}),
        ("tool.call", {"name": "Read"}),
        # 2 messages: one assistant, one prompt.submitted.
        ("message", {"message": {"role": "assistant", "content": []}}),
        ("prompt.submitted", {"finalPromptText": "hi"}),
    ]
    for et, data in seed:
        store.ingest({
            "id":         str(uuid.uuid4()),
            "node_id":    "agent+test",
            "agent_id":   "main",
            "session_id": "sess-A",
            "event_type": et,
            "ts":         _today_iso(),
            "data":       data,
        })
    _drain_ring(store)

    out = s._collect_activity_counters_today()
    assert out is not None
    assert out["tool_calls_today"] == 3
    assert out["exec_calls_today"] == 1, "Bash should classify as exec"
    assert out["browser_actions_today"] == 1, "browser_action should classify"
    assert out["unique_tools_today"] == 3, "Bash, browser_action, Read distinct"
    assert out["messages_today"] == 2


# ── 3. wiring: send_heartbeat injects the counters into the POST payload ────

def test_send_heartbeat_payload_includes_counters(sync_with_store, monkeypatch):
    s, ls, config = sync_with_store
    store = ls.get_store()

    # Seed one exec tool call so counters are >0 and visibly distinct from
    # the empty-store baseline. Also tags messages_today with one row so
    # cloud has a non-zero "is this node talking today?" signal.
    store.ingest({
        "id":         str(uuid.uuid4()),
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": "sess-A",
        "event_type": "tool.call",
        "ts":         _today_iso(),
        "data":       {"name": "Bash"},
    })
    store.ingest({
        "id":         str(uuid.uuid4()),
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": "sess-A",
        "event_type": "message",
        "ts":         _today_iso(),
        "data":       {"message": {"role": "assistant", "content": []}},
    })
    _drain_ring(store)

    captured: list[dict] = []

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            captured.append(payload)
            return {"sync_allowed": True, "pending_queries": []}
        return {"ok": True}

    monkeypatch.setattr(s, "_post", fake_post)

    assert s.send_heartbeat(config) is True
    assert captured, "send_heartbeat must POST exactly one /ingest/heartbeat"
    pl = captured[0]
    for field in (
        "tool_calls_today", "exec_calls_today", "browser_actions_today",
        "unique_tools_today", "messages_today",
    ):
        assert field in pl, f"heartbeat payload missing {field}"
        assert isinstance(pl[field], int)
        assert pl[field] >= 0
    assert pl["tool_calls_today"] >= 1
    assert pl["exec_calls_today"] >= 1
    assert pl["messages_today"] >= 1
