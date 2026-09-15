"""Price book, second increment: the store half of usage facts (#5936).

REQ-OBS-CEA-024 (Software Factory). Kept apart from
tests/test_price_book_usage.py because it opens a real DuckDB store, so it runs
in the CI job that installs the store's dependencies.

AC-OBS-CEA-024.17 test_usage_facts_are_read_not_priced
"""
from __future__ import annotations

import importlib
import os
import sys
import time

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from clawmetry import price_book_usage as pbu  # noqa: E402
from tests.test_price_book_usage import (  # noqa: E402,F401  (fixtures are used by name)
    NOW_LOCAL, SONNET, _month, _save_v1_then_v2, _scratch_home, engine,
)


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls.get_store()


def _ev(ev_id, et, ts, data, model=None, cost=None, sid="claude_code:s1"):
    ev = {"id": ev_id, "node_id": "n1", "agent_type": "openclaw", "agent_id": "main",
          "session_id": sid, "event_type": et, "ts": ts, "data": data}
    if model:
        ev["model"] = model
    if cost is not None:
        ev["cost_usd"] = cost
    return ev


def test_usage_facts_are_read_not_priced(store, engine):
    usage = {"input_tokens": 1_000_000, "output_tokens": 0, "cache_read_input_tokens": 0,
             "cache_creation_input_tokens": 0}
    events = [
        _ev("e1", "assistant", "2026-09-10T16:00:00.100Z",
            {"message": {"role": "assistant", "model": SONNET, "usage": usage}}, model=SONNET, cost=3.0),
        # The slim sibling of the same turn: counted once, not twice.
        _ev("e2", "model.completed", "2026-09-10T16:00:00.300Z",
            {"promptCache": {"lastCallUsage": {"input": 1_000_000, "output": 0}}}, model=SONNET, cost=3.0),
        _ev("e3", "message", "2026-09-10T16:05:00Z",
            {"provider": "azure-openai", "deployment": "prod-chat", "endpoint_host": "contoso.openai.azure.com",
             "usage": {"input_tokens": 200, "output_tokens": 50}}, model="gpt-4o", sid="s2"),
    ]
    for ev in events:
        store.ingest(ev)
    store._flush_now()
    deadline = time.monotonic() + 3
    while store._fetch("SELECT COUNT(*) FROM events", [])[0][0] < 3 and time.monotonic() < deadline:
        time.sleep(0.02)
    facts = store.query_usage_facts(since="2026-09-01T00:00:00")
    assert [f["request_id"] for f in facts] == ["e1", "e3"]
    assert facts[0]["model"] == SONNET and facts[0]["input_tokens"] == 1_000_000
    assert facts[1]["deployment"] == "prod-chat" and facts[1]["resource"] == "contoso.openai.azure.com"
    assert all("cost_usd" not in f for f in facts)
    assert store.query_usage_facts(since="2026-09-01T00:00:00", runtime="claude_code")[0]["request_id"] == "e1"

    _save_v1_then_v2()
    stored_before = store._fetch("SELECT id, cost_usd, data FROM events ORDER BY id", [])
    block = pbu.build_block(facts, now=NOW_LOCAL)
    assert _month(block)["contract_usd"] == pytest.approx(2.0)
    assert store._fetch("SELECT id, cost_usd, data FROM events ORDER BY id", []) == stored_before
    assert "query_usage_facts" in open(os.path.join(_REPO, "routes", "local_query.py")).read()
