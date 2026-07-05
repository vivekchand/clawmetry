"""Guards for rollup runtime attribution (founder report 2026-07-02).

The bug: the v3 event mapper stamped agent_type='openclaw' on family-runtime
events, and _rollup_deltas trusted agent_type. Result: EVERY claude_code token
rolled up under openclaw (rollup_runtime_daily held ONLY openclaw rows: 9.45M
tokens / $2,048 over 31d on the founder node, with today's "openclaw" row
exactly equal to Claude Code's real day), so on the Cost tab OpenClaw showed
the node-wide week/month while Claude Code showed today=$103 but week/month=$0.

The fix, three layers, all guarded here:
  1. _rollup_deltas attributes by the SESSION-ID PREFIX (the canonical runtime
     key, mirrors _runtime_of_session) and only falls back to agent_type.
  2. The rollup backfill feeds session_id through, so a force rebuild repairs
     mis-attributed history from the stored events.
  3. schema v11 wipes the rollups once so the startup backfill rebuilds them;
     _parse_v3_event (sync.py) threads the real agent_type for new events.
"""

from __future__ import annotations

import importlib
import os
import re
from datetime import datetime, timedelta

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SYNC = os.path.join(_HERE, "..", "clawmetry", "sync.py")
_LS = os.path.join(_HERE, "..", "clawmetry", "local_store.py")


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "3600")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "100000")
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "attribution.duckdb")
    )
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    store = ls.LocalStore()
    try:
        yield ls, store
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass


def _ts(offset_days: int = 0) -> str:
    return (datetime.now() - timedelta(days=offset_days)).strftime(
        "%Y-%m-%dT12:00:00"
    )


def _ev(eid, session_id, agent_type, cost, tokens):
    return {
        "id": eid, "node_id": "n1", "agent_type": agent_type,
        "session_id": session_id, "event_type": "assistant",
        "ts": _ts(0), "data": {}, "cost_usd": cost,
        "token_count": tokens, "model": "claude-opus-4-8",
    }


def test_rollup_deltas_prefix_wins_over_wrong_agent_type(fresh_store):
    """THE regression: a claude_code:* event stamped agent_type='openclaw'
    must roll up under claude_code."""
    ls, _ = fresh_store
    pairs = []
    for e in (
        _ev("e1", "claude_code:abc", "openclaw", 1.5, 100),
        _ev("e2", "bare-openclaw-session", "openclaw", 0.5, 10),
        _ev("e3", "nemo-session", "nemoclaw", 0.25, 5),
        _ev("e4", "no-type-session", None, 0.1, 1),
    ):
        pairs.append((e, ls._extract_event_usage(e)))
    _, runtime_d = ls._rollup_deltas(pairs)
    by_rt = {rt: vals for (day, rt), vals in runtime_d.items()}
    assert by_rt["claude_code"] == [100, 1.5], (
        "claude_code:* events must attribute to claude_code even when the "
        "stored agent_type says openclaw (the v3-mapper stamp bug)"
    )
    assert by_rt["openclaw"] == [11, 0.6], (
        "prefix-less events keep agent_type / default to openclaw"
    )
    assert by_rt["nemoclaw"] == [5, 0.25], "nemoclaw stamped rows must survive"


def test_live_ingest_attributes_by_prefix(fresh_store):
    """End-to-end through ingest_events -> incremental rollup upsert."""
    _, store = fresh_store
    store.ingest(_ev("e10", "claude_code:xyz", "openclaw", 2.0, 200))
    store.ingest(_ev("e11", "claude_code:xyz", "openclaw", 3.0, 300))
    store.flush()
    rows = store.query_rollup_runtime_daily()
    by_rt = {}
    for r in rows:
        acc = by_rt.setdefault(r["runtime"], [0, 0.0])
        acc[0] += int(r["tokens"] or 0)
        acc[1] += float(r["cost_usd"] or 0.0)
    assert by_rt.get("claude_code", [0, 0])[0] == 500
    assert round(by_rt.get("claude_code", [0, 0])[1], 2) == 5.0
    assert by_rt.get("openclaw", [0, 0])[0] == 0, (
        "no claude_code spend may leak into the openclaw bucket"
    )


def test_force_backfill_repairs_polluted_history(fresh_store):
    """The v11 repair path: events stored with the WRONG agent_type (and a
    polluted rollup) re-attribute correctly on backfill_rollups(force=True),
    because the backfill now reads session_id."""
    _, store = fresh_store
    store.ingest(_ev("e20", "claude_code:old", "openclaw", 4.0, 400))
    store.flush()
    # Simulate the historical pollution: hand-write a wrong rollup row.
    with store._write_lock:
        store._conn.execute("DELETE FROM rollup_runtime_daily")
        store._conn.execute(
            "INSERT INTO rollup_runtime_daily "
            "(day, runtime, tokens, cost_usd, sessions, active_sessions) "
            "VALUES (CAST(? AS DATE), 'openclaw', 400, 4.0, 0, 0)",
            [_ts(0)[:10]],
        )
    out = store.backfill_rollups(force=True)
    assert not out.get("skipped"), out
    rows = store.query_rollup_runtime_daily()
    by_rt = {}
    for r in rows:
        acc = by_rt.setdefault(r["runtime"], [0, 0.0])
        acc[0] += int(r["tokens"] or 0)
        acc[1] += float(r["cost_usd"] or 0.0)
    assert by_rt.get("claude_code", [0, 0])[0] == 400, (
        "force backfill must re-attribute mis-stamped history via session_id"
    )
    assert by_rt.get("openclaw", [0, 0])[0] == 0


def test_schema_v11_wipe_migration_present():
    src = open(_LS, encoding="utf-8").read()
    assert "SCHEMA_VERSION = 11" in src
    m = re.search(r"if not migration_failed and current < 11:.*?DELETE FROM rollup_runtime_daily",
                  src, re.S)
    assert m, "the v11 rollup-wipe migration must exist (repairs shipped stores)"


def test_v3_mapper_threads_agent_type():
    src = open(_SYNC, encoding="utf-8").read()
    assert re.search(
        r"def _parse_v3_event\(\s*obj: dict,\s*session_id: str,\s*node_id: str,\s*agent_type: str = \"openclaw\",",
        src,
    ), "_parse_v3_event must accept the batch agent_type"
    assert "_parse_v3_event(obj, session_id, node_id, agent_type)" in src, (
        "_local_ingest_session_batch must pass its agent_type through"
    )
    m = re.search(r"def _parse_v3_event.*?return \{.*?\"agent_type\": (\S+),", src, re.S)
    assert m and m.group(1) == "agent_type", (
        "the mapper's returned row must use the agent_type param, not a "
        "hardcoded 'openclaw'"
    )
