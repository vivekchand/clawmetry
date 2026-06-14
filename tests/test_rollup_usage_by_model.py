"""Tests for query-spine P3 (#2989): /api/usage/by-model reads from
rollup_model_daily instead of scanning raw events at request time.

Covers:
1. Rollup path returns correct per-model aggregates from rollup_model_daily.
2. Response shape is identical to the legacy event-scan path.
3. Empty rollup → function returns None (caller falls through to event scan).
4. Runtime filter is forwarded to query_rollup_model_daily.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest


# ── helpers ────────────────────────────────────────────────────────────────

def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _wait_flush(store, t: float = 2.0) -> None:
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "3600")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "100000")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "test.duckdb"))
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    s = ls.LocalStore()
    yield s
    try:
        s.stop(flush=False)
    except Exception:
        pass


def _seed(store, *, events):
    for ev in events:
        store.ingest(ev)
    store.flush()
    _wait_flush(store)


# ── test cases ─────────────────────────────────────────────────────────────

def test_rollup_by_model_returns_correct_aggregates(store, monkeypatch):
    """Rollup path aggregates per-model cost/tokens/calls correctly."""
    now = time.time()
    events = [
        {
            "id": f"ev-{i}", "node_id": "n1", "agent_type": "openclaw",
            "session_id": "s1", "event_type": "message",
            "ts": _iso(now - i * 3600),
            "model": "claude-opus-4-7" if i % 2 == 0 else "gpt-4o-mini",
            "cost_usd": 0.01 * (i + 1),
            "token_count": 100 * (i + 1),
            "data": {},
        }
        for i in range(6)
    ]
    _seed(store, events=events)

    rollup_rows = store.query_rollup_model_daily()
    assert rollup_rows, "rollup_model_daily must be populated after flush"

    # Patch _ls_call to return the rollup rows directly (no daemon in tests).
    import routes.usage as usage_mod
    monkeypatch.setattr(usage_mod, "_ls_call",
                        lambda name, **kw: store.query_rollup_model_daily(**kw)
                        if name == "query_rollup_model_daily" else None)

    result = usage_mod._try_rollup_usage_by_model()
    assert result is not None
    assert result["_source"] == "rollup"
    models_out = {r["model"]: r for r in result["models"]}
    assert "claude-opus-4-7" in models_out
    assert "gpt-4o-mini" in models_out

    opus = models_out["claude-opus-4-7"]
    gpt = models_out["gpt-4o-mini"]

    # 3 opus events (i=0,2,4), costs 0.01, 0.03, 0.05 → 0.09
    assert abs(opus["cost_usd"] - 0.09) < 1e-5
    assert opus["call_count"] == 3
    assert opus["call_count"] == 3

    # 3 gpt events (i=1,3,5), costs 0.02, 0.04, 0.06 → 0.12
    assert abs(gpt["cost_usd"] - 0.12) < 1e-5
    assert gpt["call_count"] == 3


def test_rollup_by_model_shape_matches_legacy(store, monkeypatch):
    """The rollup response shape has all fields the legacy path returns."""
    now = time.time()
    _seed(store, events=[{
        "id": "ev-shape", "node_id": "n1", "agent_type": "openclaw",
        "session_id": "s1", "event_type": "message",
        "ts": _iso(now), "model": "claude-haiku-4-5",
        "cost_usd": 0.005, "token_count": 500, "data": {},
    }])

    import routes.usage as usage_mod
    monkeypatch.setattr(usage_mod, "_ls_call",
                        lambda name, **kw: store.query_rollup_model_daily(**kw)
                        if name == "query_rollup_model_daily" else None)

    result = usage_mod._try_rollup_usage_by_model()
    assert result is not None
    row = result["models"][0]
    for field in ("model", "provider", "total_tokens", "cost_usd",
                  "call_count", "cost_per_call", "pct_of_total_cost"):
        assert field in row, f"missing field: {field}"
    assert row["pct_of_total_cost"] == pytest.approx(100.0, abs=0.01)


def test_rollup_by_model_empty_rollup_returns_none(monkeypatch):
    """When rollup is empty (fresh install) the function returns None."""
    import routes.usage as usage_mod
    monkeypatch.setattr(usage_mod, "_ls_call",
                        lambda name, **kw: [] if name == "query_rollup_model_daily" else None)

    assert usage_mod._try_rollup_usage_by_model() is None


def test_rollup_by_model_runtime_filter(store, monkeypatch):
    """runtime= is forwarded to query_rollup_model_daily."""
    now = time.time()
    events = [
        {"id": "ev-oc", "node_id": "n1", "agent_type": "openclaw",
         "session_id": "s-oc", "event_type": "message",
         "ts": _iso(now), "model": "claude-opus-4-7",
         "cost_usd": 0.1, "token_count": 1000, "data": {}},
        {"id": "ev-cc", "node_id": "n1", "agent_type": "claude_code",
         "session_id": "s-cc", "event_type": "message",
         "ts": _iso(now - 1), "model": "claude-sonnet-4-6",
         "cost_usd": 0.05, "token_count": 500, "data": {}},
    ]
    _seed(store, events=events)

    captured = {}

    def _fake_ls_call(name, **kw):
        if name == "query_rollup_model_daily":
            captured.update(kw)
            return store.query_rollup_model_daily(**kw)
        return None

    import routes.usage as usage_mod
    monkeypatch.setattr(usage_mod, "_ls_call", _fake_ls_call)

    usage_mod._try_rollup_usage_by_model(runtime="openclaw")
    assert captured.get("runtime") == "openclaw"
