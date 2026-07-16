"""Tests for the licensed self-hosted (no-cloud) branch of
``clawmetry.sync.evaluate_alerts`` — ``_evaluate_alerts_local``.

Covers the fix for "self-hosted Pro alerting never fires": a node with a
signed license (tier pro/enterprise → feature ``custom_alerts``) but NO
``cm_`` cloud token must still evaluate its DuckDB alert rules and deliver
matches locally:

  * banner row in the fleet SQLite ``alert_history`` table (the table
    GET /api/alerts/active + /api/alerts/history read and the dashboard's
    ``#alert-banner`` polls),
  * optional generic-webhook POST (feature ``alert_webhooks``), mocked at
    the HTTP layer here and never allowed to raise into the daemon loop,
  * unlicensed enforced OSS nodes still get nothing,
  * the cm_ cloud-dispatch path never enters the local branch.

Fixture pattern mirrors tests/test_evaluate_alerts_integration.py (real
DuckDB LocalStore against a tmp file + module reloads).
"""
from __future__ import annotations

import importlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures (same shape as test_evaluate_alerts_integration.py) ─────────────


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
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as s
    importlib.reload(s)
    return s


@pytest.fixture
def fleet_db_path(tmp_path, monkeypatch):
    """Point the daemon's local banner delivery at a tmp fleet.db."""
    p = tmp_path / "fleet.db"
    monkeypatch.setenv("CLAWMETRY_FLEET_DB", str(p))
    return p


# ── Helpers ───────────────────────────────────────────────────────────────────


def _now_iso(offset_sec: int = 0) -> str:
    return (
        datetime.now(timezone.utc) + timedelta(seconds=offset_sec)
    ).isoformat()


def _seed_rule_and_events(store, *, threshold=3, n_events=5, channels=None):
    """One count_over_threshold rule + matching events (integration-test
    twin, plus optional ``channels`` inside condition_json)."""
    cond = {
        "type":         "count_over_threshold",
        "event_type":   "tool_call",
        "threshold":    threshold,
        "window_sec":   60,
        "cooldown_sec": 0,
    }
    if channels is not None:
        cond["channels"] = channels
    store.ingest_alert_rule({
        "id":         "rule-local-1",
        "owner_hash": None,
        "name":       "Local test count rule",
        "condition_json": cond,
        "enabled":    True,
    })
    for i in range(n_events):
        store.ingest({
            "id":         f"evt-{i}",
            "node_id":    "test-node",
            "event_type": "tool_call",
            "ts":         _now_iso(-30 + i),
            "data":       {"i": i},
        })
    return "rule-local-1"


def _use_store(monkeypatch, store):
    """Make the daemon's `from clawmetry import local_store` see our store."""
    import clawmetry.local_store as live_ls
    monkeypatch.setattr(live_ls, "get_store", lambda **kw: store)


def _pin_entitlement(monkeypatch, *, features=(), grace=False, tier="pro"):
    """Pin clawmetry.entitlements.get_entitlement to a fixed Entitlement so
    the test is hermetic w.r.t. the dev machine's license/enforce env."""
    import clawmetry.entitlements as ent
    e = ent.Entitlement(
        tier=tier, source="test", grace=grace,
        features=frozenset(features), runtimes=frozenset(),
    )
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    return e


def _no_cloud_post(monkeypatch, sync_module):
    """The local branch must NEVER hit the cloud dispatch endpoint."""
    def _boom(*a, **k):
        raise AssertionError("cloud _post must not be called on the "
                             "local-only path")
    monkeypatch.setattr(sync_module, "_post", _boom)


def _banner_rows(fleet_db_path):
    db = sqlite3.connect(str(fleet_db_path))
    db.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in db.execute(
            "SELECT * FROM alert_history ORDER BY id"
        ).fetchall()]
    finally:
        db.close()


# ── Local-branch tests ────────────────────────────────────────────────────────


def test_licensed_no_cm_evaluates_and_persists_banner(
    fresh_store, sync_module, fleet_db_path, monkeypatch
):
    """Signed-license node (custom_alerts, enforce on) + empty api_key →
    rules evaluate and the match lands in alert_history (channel=banner),
    which /api/alerts/active + the dashboard banner render."""
    ls, store = fresh_store
    rid = _seed_rule_and_events(store, threshold=3, n_events=5)
    _use_store(monkeypatch, store)
    _pin_entitlement(monkeypatch, features={"custom_alerts"}, grace=False)
    _no_cloud_post(monkeypatch, sync_module)

    state: dict = {}
    n = sync_module.evaluate_alerts({"api_key": "", "node_id": ""}, state)

    assert n == 1
    rows = _banner_rows(fleet_db_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["rule_id"] == rid
    assert row["channel"] == "banner"
    assert row["type"] == "count_over_threshold"
    assert row["message"], "banner message must be non-empty"
    assert row["acknowledged"] == 0
    # Same cooldown/memo state keys as the cm_ path.
    assert state.get("alerts_last_eval_ts")
    memo = state.get("alerts_eval_memo", {}).get(rid, {})
    assert memo.get("last_fired_ts", 0) > 0


def test_unlicensed_no_cm_returns_zero_without_evaluating(
    fresh_store, sync_module, fleet_db_path, monkeypatch
):
    """Enforced OSS-free node: no evaluation at all (alerting is paid).
    The store must not even be opened."""
    ls, store = fresh_store
    _seed_rule_and_events(store)
    _pin_entitlement(monkeypatch, features=(), grace=False, tier="oss_free")
    _no_cloud_post(monkeypatch, sync_module)

    import clawmetry.local_store as live_ls

    def _no_store(**kw):
        raise AssertionError("local store must not be opened for an "
                             "unlicensed node")
    monkeypatch.setattr(live_ls, "get_store", _no_store)

    state: dict = {}
    n = sync_module.evaluate_alerts({"api_key": "", "node_id": ""}, state)
    assert n == 0
    assert not fleet_db_path.exists()
    assert "alerts_last_eval_ts" not in state


def test_grace_mode_behaves_entitled(
    fresh_store, sync_module, fleet_db_path, monkeypatch
):
    """CLAWMETRY_ENFORCE unset → grace=True → allows_feature() is True even
    with an empty feature set — the local path must evaluate (no special-
    casing of grace, just the resolver)."""
    ls, store = fresh_store
    _seed_rule_and_events(store, threshold=3, n_events=5)
    _use_store(monkeypatch, store)
    _pin_entitlement(monkeypatch, features=(), grace=True, tier="oss_free")
    _no_cloud_post(monkeypatch, sync_module)

    n = sync_module.evaluate_alerts({"api_key": "", "node_id": ""}, {})
    assert n == 1
    assert len(_banner_rows(fleet_db_path)) == 1


def test_cm_path_never_enters_local_branch(
    fresh_store, sync_module, fleet_db_path, monkeypatch
):
    """A cm_-configured node keeps the cloud dispatch path — the local
    branch must not run and nothing may land in the fleet DB."""
    ls, store = fresh_store
    rid = _seed_rule_and_events(store)
    real_query = store.query_alert_rules
    monkeypatch.setattr(store, "query_alert_rules",
                        lambda **kw: real_query(limit=kw.get("limit", 200)))
    _use_store(monkeypatch, store)

    def _local_boom(*a, **k):
        raise AssertionError("_evaluate_alerts_local must not run on the "
                             "cm_ path")
    monkeypatch.setattr(sync_module, "_evaluate_alerts_local", _local_boom)

    posted = []

    def _fake_post(path, payload, api_key, timeout=10):
        posted.append({"path": path, "payload": payload})
        return {"ok": True, "dispatched": ["slack-1"]}
    monkeypatch.setattr(sync_module, "_post", _fake_post)

    n = sync_module.evaluate_alerts(
        {"api_key": "cm_test", "node_id": "node-1"}, {}
    )
    assert n == 1
    assert posted and posted[0]["path"] == "/api/cloud/alerts/dispatch"
    assert posted[0]["payload"]["rule_id"] == rid
    assert not fleet_db_path.exists(), "cm_ path must not write the fleet DB"


# ── Webhook delivery ──────────────────────────────────────────────────────────


class _FakeHTTPResp:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _write_webhook_config(tmp_path, monkeypatch, sync_module, url):
    cfg = tmp_path / "clawmetry-alerts.json"
    cfg.write_text(json.dumps({"webhook_url": url}))
    monkeypatch.setattr(
        sync_module, "_LOCAL_ALERTS_WEBHOOK_CONFIG", str(cfg)
    )


def test_local_webhook_posts_match_json(
    fresh_store, sync_module, fleet_db_path, tmp_path, monkeypatch
):
    """Rule channels include "webhook" + URL configured + alert_webhooks
    entitled → the match JSON is POSTed (HTTP layer mocked)."""
    ls, store = fresh_store
    rid = _seed_rule_and_events(store, channels=["banner", "webhook"])
    _use_store(monkeypatch, store)
    _pin_entitlement(
        monkeypatch, features={"custom_alerts", "alert_webhooks"},
        grace=False,
    )
    _no_cloud_post(monkeypatch, sync_module)
    _write_webhook_config(
        tmp_path, monkeypatch, sync_module, "http://127.0.0.1:9/hook"
    )

    calls = []

    def _fake_urlopen(req, timeout=None):
        calls.append({
            "url":     req.full_url,
            "body":    json.loads(req.data.decode("utf-8")),
            "timeout": timeout,
        })
        return _FakeHTTPResp()
    monkeypatch.setattr(sync_module.urllib.request, "urlopen", _fake_urlopen)

    n = sync_module.evaluate_alerts(
        {"api_key": "", "node_id": "node-local"}, {}
    )
    assert n == 1
    assert len(calls) == 1
    assert calls[0]["url"] == "http://127.0.0.1:9/hook"
    body = calls[0]["body"]
    assert body["rule_id"] == rid
    assert body["rule_name"] == "Local test count rule"
    assert body["node_id"] == "node-local"
    assert body["source"] == "clawmetry-local"
    assert isinstance(body["metadata"], dict)
    # Banner still written alongside the webhook.
    assert len(_banner_rows(fleet_db_path)) == 1


def test_local_webhook_failure_never_raises(
    fresh_store, sync_module, fleet_db_path, tmp_path, monkeypatch
):
    """A webhook endpoint blowing up must not raise into the daemon loop —
    the banner delivery still counts the match."""
    ls, store = fresh_store
    _seed_rule_and_events(store, channels=["webhook"])
    _use_store(monkeypatch, store)
    _pin_entitlement(
        monkeypatch, features={"custom_alerts", "alert_webhooks"},
        grace=False,
    )
    _no_cloud_post(monkeypatch, sync_module)
    _write_webhook_config(
        tmp_path, monkeypatch, sync_module, "http://127.0.0.1:9/hook"
    )

    def _boom(req, timeout=None):
        raise RuntimeError("simulated webhook outage")
    monkeypatch.setattr(sync_module.urllib.request, "urlopen", _boom)

    n = sync_module.evaluate_alerts({"api_key": "", "node_id": ""}, {})
    assert n == 1  # banner persisted; webhook failure swallowed
    assert len(_banner_rows(fleet_db_path)) == 1


def test_local_webhook_skipped_without_entitlement(
    fresh_store, sync_module, fleet_db_path, tmp_path, monkeypatch
):
    """custom_alerts without alert_webhooks (enforce on): banner fires,
    webhook must not be attempted even though URL + channel ask for it."""
    ls, store = fresh_store
    _seed_rule_and_events(store, channels=["webhook"])
    _use_store(monkeypatch, store)
    _pin_entitlement(monkeypatch, features={"custom_alerts"}, grace=False)
    _no_cloud_post(monkeypatch, sync_module)
    _write_webhook_config(
        tmp_path, monkeypatch, sync_module, "http://127.0.0.1:9/hook"
    )

    def _boom(req, timeout=None):
        raise AssertionError("webhook must not fire without alert_webhooks")
    monkeypatch.setattr(sync_module.urllib.request, "urlopen", _boom)

    n = sync_module.evaluate_alerts({"api_key": "", "node_id": ""}, {})
    assert n == 1
    assert len(_banner_rows(fleet_db_path)) == 1
