"""Phase-3b: sync_family_runtimes ingests PicoClaw + NanoClaw sessions into DuckDB.

Verifies the daemon maps the reader adapters' unified Session/Event objects onto
the same DuckDB rows OpenClaw uses, so the runtimes appear in the sessions list +
transcripts. Tagged agent_type='openclaw' + data._runtime, namespaced session ids,
ISO timestamps. Cloud push (_post) is mocked; the assertions are about the local
store (the source of truth the sessions list + snapshot read from).
"""
from __future__ import annotations

import importlib
import json
import os
import time
from unittest.mock import patch

import pytest

_FIX = os.path.join(os.path.dirname(__file__), "fixtures", "runtimes")
_PICO_HOME = os.path.join(_FIX, "picoclaw")          # <home>/workspace/sessions/*.jsonl
_NANO_DIR = os.path.join(_FIX, "nanoclaw", "REAL")   # <group>/<session>/{inbound,outbound}.db


@pytest.fixture
def sync_with_isolated_store(tmp_path, monkeypatch):
    """Reload sync + local_store with an isolated DB, pointed at the fixtures."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    # Point the family adapters at the committed real-capture fixtures.
    monkeypatch.setenv("PICOCLAW_HOME", _PICO_HOME)
    monkeypatch.setenv("CLAWMETRY_NANOCLAW_DIR", _NANO_DIR)
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    # Force the in-process writer on the isolated tmp DB. Without this, when a
    # real ClawMetry daemon happens to be running on the dev box, get_store()
    # returns a proxy to that daemon's PROD store and the test would read/write
    # the wrong database. In CI no daemon runs, so this is a harmless no-op.
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    yield sync, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_for_flush(store, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError("flusher did not drain in time")


def test_family_runtimes_ingest_sessions_and_events(sync_with_isolated_store):
    sync, ls = sync_with_isolated_store
    # api_key truthy so the cloud-push path runs (_post is mocked below).
    config = {"node_id": "test-node", "api_key": "test-key"}

    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}) as mock_post:
        n_events = sync.sync_family_runtimes(config, {}, {})

    assert n_events > 0, "expected family-runtime events to be ingested"
    store = ls.get_store()
    _wait_for_flush(store)

    # Sessions landed under namespaced ids, tagged agent_type='openclaw'.
    rows = store._fetch(
        "SELECT agent_type, session_id, title, message_count, metadata "
        "FROM sessions WHERE session_id LIKE 'picoclaw:%' OR session_id LIKE 'nanoclaw:%'",
        [],
    )
    sids = {r[1] for r in rows}
    assert any(s.startswith("picoclaw:") for s in sids), f"no picoclaw session: {sids}"
    assert any(s.startswith("nanoclaw:") for s in sids), f"no nanoclaw session: {sids}"
    for agent_type, sid, _title, mcount, meta in rows:
        assert agent_type == "openclaw", f"{sid} should be tagged openclaw, got {agent_type}"
        # runtime discriminator is preserved in metadata
        md = json.loads(meta) if isinstance(meta, (str, bytes)) else (meta or {})
        assert md.get("runtime") in ("picoclaw", "nanoclaw")

    # Events landed with renderable types + the _runtime discriminator.
    evrows = store._fetch(
        "SELECT session_id, event_type, data FROM events "
        "WHERE session_id LIKE 'picoclaw:%' OR session_id LIKE 'nanoclaw:%'",
        [],
    )
    assert evrows, "expected family-runtime events in the events table"
    types = {r[1] for r in evrows}
    assert "message" in types
    for _sid, etype, data in evrows:
        d = json.loads(data) if isinstance(data, (str, bytes)) else (data or {})
        assert d.get("_runtime") in ("picoclaw", "nanoclaw")
    # PicoClaw real capture has an exec tool call -> tool_call event present.
    assert "tool_call" in types

    # Cloud push was attempted with the namespaced session rows.
    assert mock_post.called
    _path, payload, _key = mock_post.call_args[0]
    assert _path == "/ingest/sessions"
    assert any(
        s["session_id"].startswith(("picoclaw:", "nanoclaw:"))
        for s in payload["sessions"]
    )


def test_family_runtimes_transcript_renders(sync_with_isolated_store):
    """Ingested events render as a transcript (the renderable event-type path)."""
    sync, ls = sync_with_isolated_store
    config = {"node_id": "test-node", "api_key": None}
    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}):
        sync.sync_family_runtimes(config, {}, {})
    store = ls.get_store()
    _wait_for_flush(store)

    # Find a picoclaw session and pull its events back in ts order (what the
    # transcript builder does). query_events applies no agent_type filter.
    sess = store._fetch(
        "SELECT session_id FROM sessions WHERE session_id LIKE 'picoclaw:%' LIMIT 1", []
    )
    assert sess, "no picoclaw session to render"
    sid = sess[0][0]
    evs = store.query_events(session_id=sid, limit=1000)
    assert evs, "transcript events should be returned by query_events (no agent_type filter)"
    roles = {(json.loads(e["data"]) if isinstance(e.get("data"), (str, bytes)) else e.get("data", {})).get("role")
             for e in evs}
    assert "user" in roles and "assistant" in roles


def test_family_runtimes_gated_by_sync_allowed(sync_with_isolated_store):
    sync, _ls = sync_with_isolated_store
    with patch.object(sync, "_sync_allowed", return_value=False):
        assert sync.sync_family_runtimes({"node_id": "n"}, {}, {}) == 0


def test_family_runtimes_noop_when_absent(tmp_path, monkeypatch):
    """No PicoClaw/NanoClaw on the host -> zero events, never raises."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("PICOCLAW_HOME", str(tmp_path / "nope-pico"))
    monkeypatch.setenv("CLAWMETRY_NANOCLAW_DIR", str(tmp_path / "nope-nano"))
    monkeypatch.setenv("HOME", str(tmp_path))  # keep nano discovery from finding a real checkout
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    try:
        with patch.object(sync, "_sync_allowed", return_value=True), \
             patch.object(sync, "_post", return_value={}) as mock_post:
            assert sync.sync_family_runtimes({"node_id": "n", "api_key": "k"}, {}, {}) == 0
        assert not mock_post.called
    finally:
        try:
            ls.get_store().stop(flush=True)
        except Exception:
            pass
