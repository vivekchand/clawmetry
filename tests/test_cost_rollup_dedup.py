"""Regression guard for cost double-count in query_model_rollup (cloud #1570).

OpenClaw v3 emits BOTH an `assistant` row AND a sibling `model.completed` row
per billable turn, same second, same cost+tokens. The rollup's ev CTE, 24h
slice, and per-(runtime,model) query summed raw `events`, doubling every turn on
the cloud Models tab, the 24h spend columns, and the per-model rollup. They now
read from the shared envelope-dedup CTE.

Two turns ($1.00/100 tok and $2.00/200 tok), each as an assistant+model.completed
pair, must total $3.00 / 300 tok / 2 turns, never $6.00 / 600 / 4.
"""
import datetime as _dt
import importlib
import time

import pytest

NODE_ID = "node-dedup-test"
SESSION_ID = "sess-dedup-0001"
MODEL = "claude-opus-4-8"


def _ts(seconds_ago):
    now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)
    return (now - _dt.timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")


def _ev(ev_id, et, cost, tokens, secs):
    return {
        "id": ev_id, "node_id": NODE_ID, "agent_type": "openclaw",
        "agent_id": "main", "session_id": SESSION_ID,
        "event_type": et, "ts": _ts(secs),
        "model": MODEL, "provider": "anthropic",
        "token_count": tokens, "cost_usd": cost, "data": {},
    }


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.get_store()
    # Two turns, each an assistant + sibling model.completed (same second).
    s.ingest(_ev("a1", "assistant", 1.00, 100, 10))
    s.ingest(_ev("m1", "model.completed", 1.00, 100, 10))
    s.ingest(_ev("a2", "assistant", 2.00, 200, 5))
    s.ingest(_ev("m2", "model.completed", 2.00, 200, 5))
    s._flush_now()
    deadline = time.monotonic() + 3.0
    flushed = 0
    while time.monotonic() < deadline:
        row = s._fetch("SELECT COUNT(*) FROM events", [])
        flushed = row[0][0] if row and row[0] else 0
        if flushed >= 4:
            break
        time.sleep(0.02)
    if flushed < 4:
        pytest.skip("no local DuckDB writer (a daemon holds the lock); this runs "
                    "in CI where get_store() opens a real writer")
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


def test_model_rollup_dedupes_sibling(store):
    rb = store.query_model_rollup()
    oc = (rb.get("by_runtime") or {}).get("openclaw") or {}
    assert abs(oc.get("cost_usd", 0) - 3.0) < 1e-6, oc           # not 6.0
    assert oc.get("tokens") == 300, oc                            # not 600
    assert abs(oc.get("cost_24h_usd", 0) - 3.0) < 1e-6, oc        # 24h, not 6.0
    assert oc.get("tokens_24h") == 300, oc

    brm = [r for r in (rb.get("by_runtime_model") or []) if r.get("model") == MODEL]
    assert brm, rb.get("by_runtime_model")
    assert brm[0]["turns"] == 2, brm                              # not 4
    assert abs(brm[0]["cost_usd"] - 3.0) < 1e-6, brm
    assert brm[0]["tokens"] == 300, brm
