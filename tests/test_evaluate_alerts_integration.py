"""Integration tests for ``clawmetry.sync.evaluate_alerts`` (PRD #779 PR-D pt2).

Wires up a real DuckDB ``LocalStore`` (against a tmp file) + a stubbed cloud
``_post`` so we can assert:

  * The function reads rules + events from DuckDB (NOT cloud).
  * Each evaluator match results in a POST to ``/api/cloud/alerts/dispatch``
    with the right body shape.
  * Cloud-unreachable raises into ``_post`` are caught and don't crash the
    daemon tick.
  * ``state['alerts_last_eval_ts']`` and ``state['alerts_eval_memo']`` are
    populated for cooldown persistence across daemon restarts.
"""
from __future__ import annotations

import importlib
import os
import sys
from datetime import datetime, timedelta, timezone

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Fresh DuckDB LocalStore against a tmp file. Yields (module, store)."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)

    store = ls.get_store()
    yield ls, store

    try:
        store.stop(flush=False)
    except Exception:
        pass


@pytest.fixture
def sync_module():
    """Reload sync.py after the local_store reload so any `from clawmetry
    import local_store` cached at import time gets the fresh module."""
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as s
    importlib.reload(s)
    return s


# ── Helpers ───────────────────────────────────────────────────────────────────


def _now_iso(offset_sec: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_sec)).isoformat()


def _seed_rule_and_events(store, *, threshold=3, n_events=5):
    """Seed one count_over_threshold rule and ``n_events`` matching events
    bunched into the past 30 seconds (well inside the default window).
    Returns the rule id."""
    store.ingest_alert_rule({
        "id":        "rule-int-1",
        "owner_hash": None,    # accept any caller for the test
        "name":      "Test count rule",
        "condition_json": {
            "type":         "count_over_threshold",
            "event_type":   "tool_call",
            "threshold":    threshold,
            "window_sec":   60,
            "cooldown_sec": 0,
        },
        "enabled": True,
    })
    for i in range(n_events):
        store.ingest({
            "id":          f"evt-{i}",
            "node_id":     "test-node",
            "event_type":  "tool_call",
            "ts":          _now_iso(-30 + i),
            "data":        {"i": i},
        })
    # CLAWMETRY_LOCAL_FLUSH_BATCH=1 means each ingest triggers a flush
    # synchronously — no extra step needed before query_events.
    return "rule-int-1"


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_evaluate_alerts_skips_when_no_cloud_account(sync_module, monkeypatch):
    """OSS-only nodes (no cm_ key) should silently return 0."""
    posted = []
    monkeypatch.setattr(sync_module, "_post",
                        lambda *a, **k: posted.append((a, k)) or {"ok": True})
    n = sync_module.evaluate_alerts({"api_key": "", "node_id": "n1"}, {})
    assert n == 0
    assert posted == []
    n = sync_module.evaluate_alerts(
        {"api_key": "not-cm-prefix", "node_id": "n1"}, {}
    )
    assert n == 0
    assert posted == []


def test_evaluate_alerts_skips_when_no_rules(fresh_store, sync_module, monkeypatch):
    """With cloud configured but zero local rules, dispatch must NOT fire."""
    posted = []
    monkeypatch.setattr(sync_module, "_post",
                        lambda *a, **k: posted.append((a, k)) or {"ok": True})
    cfg = {"api_key": "cm_test", "node_id": "node-1"}
    state = {}
    n = sync_module.evaluate_alerts(cfg, state)
    assert n == 0
    assert posted == []
    # State still gets the last_eval_ts? Spec: only set after we attempted
    # evaluation. With zero rules we short-circuit before that, so don't
    # assert presence here — just absence of bogus dispatches.


def test_evaluate_alerts_dispatches_match(fresh_store, sync_module, monkeypatch):
    ls, store = fresh_store
    rid = _seed_rule_and_events(store, threshold=3, n_events=5)

    posted = []

    def _fake_post(path, payload, api_key, timeout=10):
        posted.append({
            "path":    path,
            "payload": payload,
            "api_key": api_key,
            "timeout": timeout,
        })
        return {"ok": True, "dispatched": ["slack-1"]}

    monkeypatch.setattr(sync_module, "_post", _fake_post)
    # owner_hash mismatch is the common failure mode — make
    # query_alert_rules indifferent to owner by stubbing it to bypass
    # the hash filter.
    real_query = store.query_alert_rules
    monkeypatch.setattr(store, "query_alert_rules",
                        lambda **kw: real_query(limit=kw.get("limit", 200)))
    # And make sure sync's local_store.get_store returns OUR store (the
    # reloaded sync module imported a different singleton).
    monkeypatch.setattr(sync_module, "_post", _fake_post)
    # Replace get_store on the module the daemon imports.
    import clawmetry.local_store as live_ls
    monkeypatch.setattr(live_ls, "get_store", lambda **kw: store)

    cfg = {"api_key": "cm_test", "node_id": "node-1"}
    state: dict = {}
    n = sync_module.evaluate_alerts(cfg, state)

    assert n == 1, f"expected 1 dispatch, got {n} (posted={posted})"
    assert len(posted) == 1
    p = posted[0]
    assert p["path"] == "/api/cloud/alerts/dispatch"
    assert p["api_key"] == "cm_test"
    body = p["payload"]
    assert body["rule_id"] == rid
    assert body["rule_name"] == "Test count rule"
    assert body["node_id"] == "node-1"
    assert body["event_id"], "expected event_id on dispatch body"
    assert "evaluated_at" in body
    assert isinstance(body["metadata"], dict)
    assert body["metadata"]["threshold"] == 3
    assert body["metadata"]["count"] >= 3
    # Cooldown bookkeeping persisted into state.
    assert state.get("alerts_last_eval_ts")
    assert state.get("alerts_eval_memo", {}).get(rid, {}).get("last_fired_ts", 0) > 0


def test_evaluate_alerts_swallows_post_exception(fresh_store, sync_module, monkeypatch):
    """Cloud unreachable → _post raises → evaluate_alerts logs and returns 0
    (does NOT propagate the exception into the daemon loop)."""
    ls, store = fresh_store
    _seed_rule_and_events(store, threshold=3, n_events=5)

    def _boom(*a, **k):
        raise RuntimeError("simulated cloud outage")

    monkeypatch.setattr(sync_module, "_post", _boom)
    real_query = store.query_alert_rules
    monkeypatch.setattr(store, "query_alert_rules",
                        lambda **kw: real_query(limit=kw.get("limit", 200)))
    import clawmetry.local_store as live_ls
    monkeypatch.setattr(live_ls, "get_store", lambda **kw: store)

    cfg = {"api_key": "cm_test", "node_id": "node-1"}
    state: dict = {}
    # Should not raise.
    n = sync_module.evaluate_alerts(cfg, state)
    assert n == 0
    # State still progresses so we don't get stuck retrying inside the same
    # eval window forever.
    assert state.get("alerts_last_eval_ts")


def test_evaluate_alerts_deduped_response_still_counts_as_dispatched(
    fresh_store, sync_module, monkeypatch
):
    """Cloud may return ``{"ok": true, "deduped": true}`` when a recent
    notification already fired. The OSS daemon should still count it as
    dispatched (since the local rule fired) — the cloud just chose not to
    fan out a second time."""
    ls, store = fresh_store
    _seed_rule_and_events(store, threshold=3, n_events=5)

    def _fake_post(path, payload, api_key, timeout=10):
        return {"ok": True, "deduped": True}

    monkeypatch.setattr(sync_module, "_post", _fake_post)
    real_query = store.query_alert_rules
    monkeypatch.setattr(store, "query_alert_rules",
                        lambda **kw: real_query(limit=kw.get("limit", 200)))
    import clawmetry.local_store as live_ls
    monkeypatch.setattr(live_ls, "get_store", lambda **kw: store)

    n = sync_module.evaluate_alerts(
        {"api_key": "cm_test", "node_id": "node-1"}, {}
    )
    assert n == 1


# ── Smoke: docstring + name sanity for verification step ──────────────────────


def test_docstring_mentions_duckdb(sync_module):
    """Spec: ``sync.evaluate_alerts.__doc__`` must mention DuckDB after the
    rewrite (so future agents can cheaply detect the legacy implementation
    has been replaced)."""
    assert sync_module.evaluate_alerts.__doc__
    assert "DuckDB" in sync_module.evaluate_alerts.__doc__
