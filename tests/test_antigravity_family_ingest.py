"""Antigravity family-runtime ingest: sync_family_runtimes lands Antigravity
conversations in DuckDB.

Mirrors tests/test_n8n_family_ingest.py for the antigravity runtime (added
2026-07-31). The fixture is a REAL Google Antigravity capture
(tests/fixtures/runtimes/antigravity/REAL/antigravity-cli/) from a live
``agy --print`` tool-using session: brain JSONL transcript (write_to_file +
run_command + view_file + one CHECKPOINT) plus the per-generation token
protobuf rows in conversations/<uuid>.db (WAL sidecars committed — rows
live there).

Asserts the full attribution contract: namespaced ``antigravity:<uuid>``
session ids, agent_type='openclaw' (family convention),
metadata.runtime='antigravity', events carrying data._runtime + tool_calls
in the Case-D shape the approvals watcher extracts, model attribution
surviving to event rows, and the CHECKPOINT step landing as a renderable
event.

Skips cleanly when clawmetry-pro (or a pro build without the antigravity
adapter) is missing — OSS-only CI has no paid adapters.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import time
from unittest.mock import patch

import pytest

pytest.importorskip("clawmetry_pro", reason="paid runtime adapters live in clawmetry-pro")
if importlib.util.find_spec("clawmetry_pro.adapters.antigravity") is None:
    pytest.skip("installed clawmetry-pro predates the antigravity adapter",
                allow_module_level=True)

_FIX_HOME = os.path.join(
    os.path.dirname(__file__), "fixtures", "runtimes", "antigravity", "REAL"
)
_SESSION = "edbc1e89-7892-4ccc-a7dd-c4100698ce7b"


@pytest.fixture
def sync_with_isolated_store(tmp_path, monkeypatch):
    """Reload sync + local_store with an isolated DB, pointed at the fixture.
    Other family adapters see an empty HOME so only antigravity ingests."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_ANTIGRAVITY_HOME", _FIX_HOME)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
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


def test_antigravity_conversation_ingests_with_full_attribution(sync_with_isolated_store):
    sync, ls = sync_with_isolated_store
    config = {"node_id": "test-node", "api_key": "test-key"}

    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}):
        n_events = sync.sync_family_runtimes(config, {}, {})
    assert n_events > 0
    store = ls.get_store()
    _wait_for_flush(store)

    rows = store._fetch(
        "SELECT agent_type, session_id, title, metadata FROM sessions "
        "WHERE session_id LIKE 'antigravity:%'",
        (),
    )
    assert [r[1] for r in rows] == [f"antigravity:{_SESSION}"]
    agent_type, sid, title, metadata = rows[0]
    assert agent_type == "openclaw"  # family convention
    md = json.loads(metadata) if metadata else {}
    assert md.get("runtime") == "antigravity"
    assert md.get("model") == "gemini-3.6-flash"
    assert md.get("flavor") == "antigravity-cli"
    assert "fib.py" in title

    assert sync._runtime_of_session(f"antigravity:{_SESSION}") == "antigravity"
    # a bare uuid is NOT a runtime prefix (runtime_filter_no_leak semantics)
    assert sync._runtime_of_session(_SESSION) == "openclaw"

    events = store._fetch(
        "SELECT event_type, model, data FROM events "
        "WHERE session_id LIKE 'antigravity:%' ORDER BY ts",
        (),
    )
    assert events, "expected antigravity events in the store"
    types = [e[0] for e in events]
    assert "message" in types
    assert "tool_call" in types
    assert "tool_result" in types

    saw_model = False
    named = []
    for event_type, model, data in events:
        d = json.loads(data) if data else {}
        assert d.get("_runtime") == "antigravity"
        if model == "gemini-3.6-flash":
            saw_model = True
        if event_type == "tool_call":
            named.extend(
                blk for blk in (d.get("tool_calls") or [])
                if isinstance(blk, dict) and blk.get("name")
            )
    assert saw_model, "model attribution must survive to event rows"

    # Approvals Case-D contract: tool_call rows carry named tool_calls blocks.
    assert named
    names = {blk["name"] for blk in named}
    assert {"write_to_file", "run_command", "view_file"} <= names


def test_antigravity_checkpoint_lands_as_event(sync_with_isolated_store):
    """Antigravity CHECKPOINT steps (its own auto-compaction summaries) must
    reach the store so compaction analytics see them."""
    sync, ls = sync_with_isolated_store
    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}):
        sync.sync_family_runtimes({"node_id": "n", "api_key": "k"}, {}, {})
    store = ls.get_store()
    _wait_for_flush(store)
    rows = store._fetch(
        "SELECT data FROM events WHERE session_id LIKE 'antigravity:%'", ()
    )
    step_types = {
        ((json.loads(r[0]) if r[0] else {}).get("extra") or {}).get("stepType")
        for r in rows
    }
    assert "CHECKPOINT" in step_types


def test_approvals_canonicalize_antigravity_tools():
    """A policy authored against OpenClaw's canonical categories must match
    Antigravity's native tool names (the n8n-era 'policies never fire for a
    new runtime' bug class)."""
    from clawmetry.approvals import _canonical_tool
    assert _canonical_tool("run_command") == "exec"
    assert _canonical_tool("view_file") == "read"
    assert _canonical_tool("view_file_outline") == "read"
    assert _canonical_tool("write_to_file") == "write"
    assert _canonical_tool("replace_file_content") == "write"
    assert _canonical_tool("search_web") == "web"
    assert _canonical_tool("read_url_content") == "web"
    assert _canonical_tool("grep_search") == "search"
    assert _canonical_tool("codebase_search") == "search"
