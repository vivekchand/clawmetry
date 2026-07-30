"""n8n family-runtime ingest: sync_family_runtimes lands n8n executions in DuckDB.

Mirrors tests/test_family_runtime_ingest.py for the n8n runtime (added
2026-07-30, clawmetry-pro#108). The fixture is a REAL n8n 2.32.6 capture
(tests/fixtures/runtimes/n8n/REAL/database.sqlite, pruned to the
execution tables the adapter reads): three executions run via the real n8n
CLI — a success, an intentional failure, and an AI Agent run that failed at
model auth (which still records the ai_languageModel run with the
configured model id).

Asserts the full attribution contract: namespaced ``n8n:n8n-<id>`` session
ids, agent_type='openclaw' (family convention), metadata.runtime='n8n',
events carrying data._runtime + tool_calls in the Case-D shape the
approvals watcher extracts, and the model surviving to the event rows.

Skips cleanly when clawmetry-pro (or a pro build without the n8n adapter)
is installed — OSS-only CI has no paid adapters.
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
if importlib.util.find_spec("clawmetry_pro.adapters.n8n") is None:
    pytest.skip("installed clawmetry-pro predates the n8n adapter",
                allow_module_level=True)

_FIX_DB = os.path.join(
    os.path.dirname(__file__), "fixtures", "runtimes", "n8n", "REAL", "database.sqlite"
)


@pytest.fixture
def sync_with_isolated_store(tmp_path, monkeypatch):
    """Reload sync + local_store with an isolated DB, pointed at the fixture.
    Other family adapters are pointed at empty dirs so only n8n ingests."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_N8N_DB", _FIX_DB)
    # Keep the sweep scoped: home-relative adapters see an empty HOME.
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


def test_n8n_executions_ingest_with_full_attribution(sync_with_isolated_store):
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
        "WHERE session_id LIKE 'n8n:%' ORDER BY session_id",
        (),
    )
    assert [r[1] for r in rows] == ["n8n:n8n-1", "n8n:n8n-2", "n8n:n8n-3"]
    for agent_type, _sid, _title, metadata in rows:
        assert agent_type == "openclaw"  # family convention
        assert (json.loads(metadata) if metadata else {}).get("runtime") == "n8n"
    titles = {r[1]: r[2] for r in rows}
    assert "CM Plain Pipeline" in titles["n8n:n8n-1"]
    assert "CM Research Agent" in titles["n8n:n8n-3"]

    assert sync._runtime_of_session("n8n:n8n-3") == "n8n"
    # dash form is NOT a runtime prefix (test_runtime_filter_no_leak semantics)
    assert sync._runtime_of_session("n8n-3") == "openclaw"

    events = store._fetch(
        "SELECT session_id, event_type, model, data FROM events "
        "WHERE session_id LIKE 'n8n:%' ORDER BY ts",
        (),
    )
    assert events, "expected n8n events in the store"
    tool_calls = []
    saw_model = False
    for _sid, event_type, model, data in events:
        d = json.loads(data) if data else {}
        assert d.get("_runtime") == "n8n"
        if event_type == "tool_call":
            tool_calls.append(d)
        if model == "claude-haiku-4-5-20251001":
            saw_model = True
    assert saw_model, "model attribution must survive to event rows"

    # The approvals watcher's Case-D extraction contract: event_type='tool_call'
    # rows carry an OpenAI-style data.tool_calls array with name + arguments.
    assert tool_calls
    named = [
        blk for d in tool_calls for blk in (d.get("tool_calls") or [])
        if isinstance(blk, dict) and blk.get("name")
    ]
    assert named, "tool_call events must carry named tool_calls blocks"
    assert any("arguments" in blk for blk in named)


def test_n8n_error_execution_flagged(sync_with_isolated_store):
    sync, ls = sync_with_isolated_store
    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}):
        sync.sync_family_runtimes({"node_id": "n", "api_key": "k"}, {}, {})
    store = ls.get_store()
    _wait_for_flush(store)
    rows = store._fetch(
        "SELECT data FROM events WHERE session_id = 'n8n:n8n-2' ORDER BY ts", ()
    )
    flags = [
        bool(((json.loads(r[0]) if r[0] else {}).get("extra") or {}).get("isError"))
        for r in rows
    ]
    assert any(flags), "the intentionally failing node run must be error-flagged"
