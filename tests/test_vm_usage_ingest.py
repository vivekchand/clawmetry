"""sync_vm_usage_log: hosted-VM per-call LLM usage → DuckDB cost events.

The only cost source for token-blind runtimes (picoclaw — live-hit
2026-07-20: BYOK picoclaw showed $0 forever). Allowlist prevents double
counting on self-reporting runtimes."""
from __future__ import annotations

import importlib
import json
import os
import time

import pytest


@pytest.fixture
def iso_sync(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "e.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
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


def _write_log(path, n=3, session="telegram-chat42"):
    with open(path, "a") as fh:
        for i in range(n):
            fh.write(json.dumps({
                "ts": time.time(), "model": "claude-haiku-4-5",
                "input_tokens": 1000, "output_tokens": 200,
                "cache_read_tokens": 100, "cache_write_tokens": 50,
                "session": session}) + "\n")


def _wait_flush(store, timeout=3.0):
    import time as _t
    end = _t.monotonic() + timeout
    while _t.monotonic() < end:
        if store.health()["ring_depth"] == 0:
            return
        _t.sleep(0.02)
    raise AssertionError("flush did not drain")


def test_ingests_priced_events_for_allowlisted_runtime(iso_sync, tmp_path, monkeypatch):
    sync, ls = iso_sync
    log = tmp_path / "llm-usage.jsonl"
    _write_log(log, n=3)
    monkeypatch.setenv("CLAWMETRY_VM_USAGE_LOG", str(log))
    monkeypatch.setenv("CLAWMETRY_VM_USAGE_RUNTIME", "picoclaw")
    state = {}
    from unittest.mock import patch
    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}):
        n = sync.sync_vm_usage_log({"node_id": "n1", "api_key": "k"}, state, {})
    assert n == 3
    store = ls.get_store()
    _wait_flush(store)
    rows = store._fetch(
        "SELECT session_id, event_type, model, cost_usd, token_count "
        "FROM events WHERE session_id LIKE 'picoclaw:vmusage:%'", [])
    assert len(rows) == 3
    for sid, etype, model, cost, tokens in rows:
        assert etype == "llm_usage" and model == "claude-haiku-4-5"
        assert sid == "picoclaw:vmusage:telegram-chat42"
        assert cost is not None and cost > 0, "ingest-time cost derivation"
        assert tokens == 1200
    # hand-check one line's cost against the pricing helper
    from clawmetry.providers_pricing import estimate_event_cost_usd
    expect = estimate_event_cost_usd(
        "claude-haiku-4-5", input_tokens=1000, output_tokens=200,
        cache_read_tokens=100, cache_write_tokens=50)
    assert abs(rows[0][3] - expect) < 1e-9
    # replay with fresh state: PK-deduped, no inflation
    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}):
        sync.sync_vm_usage_log({"node_id": "n1", "api_key": "k"}, {}, {})
    _wait_flush(store)
    rows2 = store._fetch(
        "SELECT COUNT(*) FROM events WHERE session_id LIKE 'picoclaw:vmusage:%'", [])
    assert rows2[0][0] == 3


def test_offset_advances_and_rotation_resets(iso_sync, tmp_path, monkeypatch):
    sync, ls = iso_sync
    log = tmp_path / "llm-usage.jsonl"
    _write_log(log, n=2)
    monkeypatch.setenv("CLAWMETRY_VM_USAGE_LOG", str(log))
    monkeypatch.setenv("CLAWMETRY_VM_USAGE_RUNTIME", "picoclaw")
    state = {}
    from unittest.mock import patch
    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}):
        assert sync.sync_vm_usage_log({"node_id": "n"}, state, {}) == 2
        # nothing new: offset holds, zero ingested
        assert sync.sync_vm_usage_log({"node_id": "n"}, state, {}) == 0
        # rotation: replace the file (new inode) -> offset resets, new lines land
        os.replace(log, str(log) + ".1")
        _write_log(log, n=1, session="web-web")
        assert sync.sync_vm_usage_log({"node_id": "n"}, state, {}) == 1


def test_allowlist_blocks_self_reporting_runtimes(iso_sync, tmp_path, monkeypatch):
    sync, ls = iso_sync
    log = tmp_path / "llm-usage.jsonl"
    _write_log(log, n=2)
    monkeypatch.setenv("CLAWMETRY_VM_USAGE_LOG", str(log))
    monkeypatch.setenv("CLAWMETRY_VM_USAGE_RUNTIME", "nanoclaw")
    from unittest.mock import patch
    with patch.object(sync, "_sync_allowed", return_value=True):
        assert sync.sync_vm_usage_log({"node_id": "n"}, {}, {}) == 0
    # override allowlist opts a verified runtime in
    monkeypatch.setenv("CLAWMETRY_VM_USAGE_ALLOW", "nanoclaw")
    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}):
        assert sync.sync_vm_usage_log({"node_id": "n", "api_key": "k"}, {}, {}) == 2
