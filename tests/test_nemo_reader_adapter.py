"""Tests for ``NeMoReaderAdapter`` (Phase 4.5 read-side facade).

The push-side ``NeMoAdapter`` keeps ingesting events into DuckDB; the
new facade makes those events queryable through the standard
:class:`AgentAdapter` shape so:

* /api/agents lists "nemo" alongside openclaw + paid runtimes
* The header runtime switcher can filter to NeMo
* The homepage tooltip "OpenClaw + NeMo" stops being a lie

These pin the facade contract: detect/list_sessions/list_events query
DuckDB by ``agent_type='nemo'`` and return the shapes the dashboard
expects.
"""
from __future__ import annotations

import importlib
import time
import uuid

import pytest


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Fresh LocalStore at a tmp path so tests don't read the dev DuckDB.

    The adapter calls ``local_store.get_store(read_only=True)`` to fetch
    the singleton; we patch it to return our test instance so the read
    path sees the events we ingest in tests."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("HOME", str(tmp_path))  # daemon-detection shield
    import clawmetry.local_store as _ls
    importlib.reload(_ls)
    s = _ls.LocalStore()
    s.start()
    monkeypatch.setattr(_ls, "get_store", lambda *a, **kw: s)
    yield s
    s.stop(flush=True)


def _seed_nemo_event(store, *, session_id="nemo-sess-1", event_type="model.completed"):
    event_id = str(uuid.uuid4())
    store.ingest({
        "id": event_id,
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "nemo",
        "session_id": session_id,
        "event_type": event_type,
        "ts": time.time(),
        "model": "nv/llama3-70b",
        "data": {"role": "assistant", "content": "hi"},
        "token_count": 42,
        "cost_usd": 0.001,
    })


def _wait_flush(store, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


# ── detect ────────────────────────────────────────────────────────────────────


def test_nemo_reader_detect_false_when_no_events(isolated_store):
    """Empty store -> detected=False so we don't clutter /api/agents."""
    from clawmetry.adapters.nemo import NeMoReaderAdapter
    res = NeMoReaderAdapter().detect()
    assert res.detected is False
    assert res.name == "nemo"
    assert res.display_name == "NeMo"


def test_nemo_reader_detect_true_after_ingest(isolated_store):
    _seed_nemo_event(isolated_store)
    _wait_flush(isolated_store)
    from clawmetry.adapters.nemo import NeMoReaderAdapter
    res = NeMoReaderAdapter().detect()
    assert res.detected is True
    assert res.meta["event_count"] == 1


# ── list_sessions ────────────────────────────────────────────────────────────


def test_nemo_reader_list_sessions_groups_by_session_id(isolated_store):
    _seed_nemo_event(isolated_store, session_id="sess-a")
    _seed_nemo_event(isolated_store, session_id="sess-a", event_type="model.completed")
    _seed_nemo_event(isolated_store, session_id="sess-b")
    _wait_flush(isolated_store)
    from clawmetry.adapters.nemo import NeMoReaderAdapter
    sessions = NeMoReaderAdapter().list_sessions()
    ids = {s.id for s in sessions}
    assert ids == {"sess-a", "sess-b"}
    sess_a = next(s for s in sessions if s.id == "sess-a")
    assert sess_a.message_count == 2
    assert sess_a.total_tokens == 84  # 42 + 42


# ── list_events ──────────────────────────────────────────────────────────────


def test_nemo_reader_list_events_for_session(isolated_store):
    _seed_nemo_event(isolated_store, session_id="sess-c", event_type="prompt.submitted")
    _seed_nemo_event(isolated_store, session_id="sess-c", event_type="model.completed")
    _wait_flush(isolated_store)
    from clawmetry.adapters.nemo import NeMoReaderAdapter
    events = NeMoReaderAdapter().list_events("sess-c")
    types = [e.type for e in events]
    assert set(types) == {"prompt.submitted", "model.completed"}
    assert all(e.agent == "nemo" for e in events)


# ── capabilities ─────────────────────────────────────────────────────────────


def test_nemo_reader_capabilities():
    from clawmetry.adapters.nemo import NeMoReaderAdapter
    from clawmetry.adapters.base import Capability
    caps = NeMoReaderAdapter().capabilities()
    assert Capability.SESSIONS in caps
    assert Capability.EVENTS in caps
    assert Capability.BRAIN in caps
    assert Capability.COST in caps


# ── isolation: doesn't pick up non-nemo runtimes ────────────────────────────


def test_nemo_reader_ignores_non_nemo_events(isolated_store):
    """A claude_code event seeded into the same store must NOT make NeMo
    detect True. agent_type is the discriminator."""
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "claude_code",
        "session_id": "cc-sess",
        "event_type": "model.completed",
        "ts": time.time(),
    })
    _wait_flush(isolated_store)
    from clawmetry.adapters.nemo import NeMoReaderAdapter
    assert NeMoReaderAdapter().detect().detected is False
