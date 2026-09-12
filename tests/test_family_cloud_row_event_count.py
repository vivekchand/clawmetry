"""The hosted session page said "Messages 0" for every non-OpenClaw runtime.

Founder report 2026-09-11: a Codex session page on app.clawmetry.com showed
``Messages 0`` beside a transcript the local store counts as 371 messages.

The cloud's ``sessions`` table has **no message_count column**. The one count
it stores is ``event_count`` (``clawmetry-cloud/routes/api.py``), and the
hosted page renders "Messages" straight from it
(``routes/team_sessions.py``: ``int(r.get('event_count') or 0)``). The
OpenClaw cloud row has always carried that key; the family row (claude_code,
codex, cursor, …) carried ``message_count`` instead, which the cloud drops on
the floor, so the column stayed 0 for every one of those sessions.

Pins the key on the family cloud row. The cloud upsert keeps
``GREATEST(existing, new)``, so a read capped by ``_family_event_read_cap()``
can never walk a session's count backwards.
"""

from __future__ import annotations

import importlib
import time
from unittest.mock import patch

import pytest

from clawmetry.adapters.base import (
    AgentAdapter,
    Capability,
    DetectResult,
    Event,
    Session,
)

_UUID = "cccccccc-1111-2222-3333-444444444444"


def _ev(role, content, i=0):
    return Event(agent="claude_code", session_id=_UUID, id=f"e{i}",
                 type="message", ts=float(i), role=role, content=content)


def _fake_adapter(sessions, events_by_sid):
    class _Fake(AgentAdapter):
        name = "claude_code"
        display_name = "Claude Code"

        def detect(self):
            return DetectResult(name=self.name, display_name=self.display_name,
                                detected=True, session_count=len(sessions))

        def list_sessions(self, limit=100):
            return sessions

        def list_events(self, session_id, limit=500):
            return events_by_sid.get(session_id, [])

        def capabilities(self):
            return {Capability.SESSIONS, Capability.EVENTS}

    return _Fake


@pytest.fixture
def isolated_sync(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path / ".openclaw"))
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    yield sync, ls, tmp_path
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _session_rows(calls):
    """Every dict in the captured ``_post`` payloads that looks like a session
    row. The endpoint's arg order is not the contract under test; carrying the
    count is."""
    found = []

    def walk(obj):
        if isinstance(obj, dict):
            if "session_id" in obj and "runtime" in obj:
                found.append(obj)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                walk(v)

    walk(calls)
    return found


def test_family_cloud_row_carries_event_count(isolated_sync):
    sync, ls, _tmp = isolated_sync
    sessions = [Session(agent="claude_code", id=_UUID, started_at=1000.0,
                        ended_at=1010.0, message_count=2)]
    events = {_UUID: [_ev("user", "add a dark mode toggle", 0),
                      _ev("assistant", "on it", 1),
                      _ev("user", "and a light one", 2),
                      _ev("assistant", "done", 3)]}
    calls = []

    def _capture(*args, **kwargs):
        calls.append({"args": list(args), "kwargs": dict(kwargs)})
        return {}

    with patch.object(sync, "_family_adapter_classes",
                      lambda: [_fake_adapter(sessions, events)]), \
         patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", side_effect=_capture):
        sync.sync_family_runtimes(
            {"node_id": "n", "api_key": "k"}, {}, {})

    rows = [r for r in _session_rows(calls)
            if str(r.get("session_id", "")).endswith(_UUID)]
    assert rows, "no family session row reached the cloud push"
    row = rows[0]
    # The column the hosted page actually reads.
    assert row.get("event_count") == 4
    # message_count stays too: it is the honest per-row turn count the local
    # store keeps, and older cloud servers ignore unknown keys either way.
    assert row.get("message_count") == 2
