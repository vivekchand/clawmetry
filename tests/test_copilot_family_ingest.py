"""GitHub Copilot family-runtime ingest: sync_family_runtimes lands Copilot
CLI sessions in DuckDB.

Mirrors tests/test_antigravity_family_ingest.py for the copilot runtime
(added 2026-08-02). The fixture is a REAL GitHub Copilot CLI capture
(tests/fixtures/runtimes/copilot/REAL/) from a live ``copilot -p``
tool-using session: session-state/<uuid>/events.jsonl (bash tool
round-trip on gpt-5-mini via auto-mode routing) plus the
session-store.db assistant_usage_events per-call usage ledger.

Asserts the full attribution contract: namespaced ``copilot:<uuid>``
session ids, agent_type='openclaw' (family convention),
metadata.runtime='copilot', events carrying data._runtime + tool_calls
in the Case-D shape the approvals watcher extracts, model attribution
surviving to event rows, and vendor-billed AI-credit cost on the
session row.

Skips cleanly when clawmetry-pro (or a pro build without the copilot
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
if importlib.util.find_spec("clawmetry_pro.adapters.copilot") is None:
    pytest.skip("installed clawmetry-pro predates the copilot adapter",
                allow_module_level=True)

_FIX_HOME = os.path.join(
    os.path.dirname(__file__), "fixtures", "runtimes", "copilot", "REAL"
)
_SESSION = "42ddf424-ddf9-46ed-8045-25ecb41cc42f"


@pytest.fixture
def sync_with_isolated_store(tmp_path, monkeypatch):
    """Reload sync + local_store with an isolated DB, pointed at the fixture.
    Other family adapters see an empty HOME so only copilot ingests."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_COPILOT_HOME", _FIX_HOME)
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


def test_copilot_session_ingests_with_full_attribution(sync_with_isolated_store):
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
        "WHERE session_id LIKE 'copilot:%'",
        (),
    )
    assert [r[1] for r in rows] == [f"copilot:{_SESSION}"]
    agent_type, sid, title, metadata = rows[0]
    assert agent_type == "openclaw"  # family convention
    md = json.loads(metadata) if metadata else {}
    assert md.get("runtime") == "copilot"
    assert md.get("model") == "gpt-5-mini"
    assert "copilot_fixture_note.txt" in title

    assert sync._runtime_of_session(f"copilot:{_SESSION}") == "copilot"
    # a bare uuid is NOT a runtime prefix (runtime_filter_no_leak semantics)
    assert sync._runtime_of_session(_SESSION) == "openclaw"

    events = store._fetch(
        "SELECT event_type, model, data FROM events "
        "WHERE session_id LIKE 'copilot:%' ORDER BY ts",
        (),
    )
    assert events, "expected copilot events in the store"
    types = [e[0] for e in events]
    assert "message" in types
    assert "tool_call" in types
    assert "tool_result" in types

    saw_model = False
    named = []
    for event_type, model, data in events:
        d = json.loads(data) if data else {}
        assert d.get("_runtime") == "copilot"
        if model == "gpt-5-mini":
            saw_model = True
        if event_type == "tool_call":
            named.extend(
                blk for blk in (d.get("tool_calls") or [])
                if isinstance(blk, dict) and blk.get("name")
            )
    assert saw_model, "model attribution must survive to event rows"

    # Approvals Case-D contract: tool_call rows carry named tool_calls blocks.
    assert named
    assert {blk["name"] for blk in named} == {"bash"}


def test_copilot_cost_is_vendor_billed(sync_with_isolated_store):
    """The session row must carry the AI-credit derived cost (nano-AIU x
    $0.04/credit), not a token-table estimate."""
    sync, ls = sync_with_isolated_store
    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}):
        sync.sync_family_runtimes({"node_id": "n", "api_key": "k"}, {}, {})
    store = ls.get_store()
    _wait_for_flush(store)
    rows = store._fetch(
        "SELECT cost_usd, metadata FROM sessions WHERE session_id LIKE 'copilot:%'", ()
    )
    assert rows
    cost, metadata = rows[0]
    # 193555000 nano-AIU -> 0.193555 credits -> $0.0077422
    assert cost == pytest.approx(0.0077422, abs=1e-6)
    md = json.loads(metadata) if metadata else {}
    assert md.get("aiuCredits") == pytest.approx(0.1936, abs=1e-4)


def test_approvals_canonicalize_copilot_tools():
    """A policy authored against OpenClaw's canonical categories must match
    Copilot's native tool names (the n8n-era 'policies never fire for a
    new runtime' bug class)."""
    from clawmetry.approvals import _canonical_tool
    assert _canonical_tool("bash") == "exec"
    assert _canonical_tool("powershell") == "exec"
    assert _canonical_tool("view") == "read"
    assert _canonical_tool("read_agent") == "read"
    assert _canonical_tool("edit") == "write"
    assert _canonical_tool("create") == "write"
    assert _canonical_tool("grep") == "search"
    assert _canonical_tool("rg") == "search"
    assert _canonical_tool("glob") == "search"
    assert _canonical_tool("web_fetch") == "web"
    assert _canonical_tool("web_search") == "web"
