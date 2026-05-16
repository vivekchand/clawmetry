"""Tests for Phase 3 of the heartbeat-piggyback relay (epic #1032).

Three surfaces:
  1. DuckDB schema — ``alert_rules`` table is reachable via ``ingest_alert_rule``
     + ``query_alert_rules`` + ``delete_alert_rule``. Round-trip + filter +
     enabled_only behaviour.
  2. Route fast path — ``/api/alerts/rules`` GET serves from DuckDB tagged
     ``_source: "local_store"`` when ``CLAWMETRY_LOCAL_STORE_READ=1``. With
     the flag off the legacy fleet-DB helper is used (no ``_source`` tag).
  3. ``_build_alert_rules_cache_pushes`` — heartbeat cache push for
     ``alerts:{owner_hash}:rules`` is emitted iff rules exist and an
     encryption key is configured.
"""
from __future__ import annotations

import importlib
import os
import sys
import time

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload `clawmetry.local_store` against a fresh DuckDB file. Yields
    (module, store); closes on teardown."""
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


# ── 1. Schema round-trip ───────────────────────────────────────────────────


def test_ingest_and_query_alert_rule_round_trip(fresh_store):
    ls, store = fresh_store
    rule = {
        "id": "rule-001",
        "owner_hash": "abc123",
        "name": "Daily spend > $10",
        "condition_json": {
            "alert_type": "daily_spend",
            "threshold_value": 10.0,
            "channel_ids": ["chan-1"],
        },
        "enabled": True,
        "created_at": "2026-05-12T10:00:00Z",
        "updated_at": "2026-05-12T10:00:00Z",
    }
    store.ingest_alert_rule(rule)
    rows = store.query_alert_rules(limit=10)
    assert len(rows) == 1
    r = rows[0]
    assert r["id"] == "rule-001"
    assert r["owner_hash"] == "abc123"
    assert r["name"] == "Daily spend > $10"
    assert r["enabled"] is True
    # condition_json BLOB is decoded back to a dict by the read path.
    assert isinstance(r["condition_json"], dict)
    assert r["condition_json"]["alert_type"] == "daily_spend"
    assert r["condition_json"]["threshold_value"] == 10.0


def test_query_filters_by_owner_and_enabled(fresh_store):
    ls, store = fresh_store
    store.ingest_alert_rule({
        "id": "r-a-on", "owner_hash": "owner-A",
        "condition_json": {"alert_type": "x"}, "enabled": True,
    })
    store.ingest_alert_rule({
        "id": "r-a-off", "owner_hash": "owner-A",
        "condition_json": {"alert_type": "y"}, "enabled": False,
    })
    store.ingest_alert_rule({
        "id": "r-b-on", "owner_hash": "owner-B",
        "condition_json": {"alert_type": "z"}, "enabled": True,
    })
    a_all = store.query_alert_rules(owner_hash="owner-A")
    assert {r["id"] for r in a_all} == {"r-a-on", "r-a-off"}
    a_on = store.query_alert_rules(owner_hash="owner-A", enabled_only=True)
    assert {r["id"] for r in a_on} == {"r-a-on"}
    b_all = store.query_alert_rules(owner_hash="owner-B")
    assert {r["id"] for r in b_all} == {"r-b-on"}


def test_ingest_alert_rule_upsert_updates_existing(fresh_store):
    ls, store = fresh_store
    store.ingest_alert_rule({
        "id": "r1", "owner_hash": "owner-A",
        "name": "v1",
        "condition_json": {"threshold_value": 1},
        "enabled": True,
    })
    store.ingest_alert_rule({
        "id": "r1", "owner_hash": "owner-A",
        "name": "v2",
        "condition_json": {"threshold_value": 2},
        "enabled": False,
        "updated_at": "2026-05-12T11:00:00Z",
    })
    rows = store.query_alert_rules()
    assert len(rows) == 1
    r = rows[0]
    assert r["name"] == "v2"
    assert r["enabled"] is False
    assert r["condition_json"]["threshold_value"] == 2
    assert r["updated_at"] == "2026-05-12T11:00:00Z"


def test_delete_alert_rule_removes_row(fresh_store):
    ls, store = fresh_store
    store.ingest_alert_rule({
        "id": "r-del", "owner_hash": "owner-A",
        "condition_json": {"alert_type": "x"}, "enabled": True,
    })
    assert len(store.query_alert_rules()) == 1
    n = store.delete_alert_rule("r-del")
    assert n == 1
    assert store.query_alert_rules() == []
    # Deleting again — no row, returns 0.
    assert store.delete_alert_rule("r-del") == 0


# ── 2. Route fast path ──────────────────────────────────────────────────────


def test_api_alerts_rules_fast_path_serves_local_store(fresh_store, monkeypatch):
    """With CLAWMETRY_LOCAL_STORE_READ=1 and a non-empty alert_rules table,
    GET /api/alerts/rules returns the DuckDB rows tagged _source=local_store."""
    ls, store = fresh_store
    store.ingest_alert_rule({
        "id": "r-fast",
        "owner_hash": "owner-X",
        "name": "fast-path rule",
        "condition_json": {"alert_type": "token_velocity", "threshold_value": 9999},
        "enabled": True,
    })

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    # Reload the routes module so the late-bound _try_local_store_alert_rules
    # picks up the freshly-reloaded local_store.
    sys.modules.pop("routes.alerts", None)
    import routes.alerts as ra
    importlib.reload(ra)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(ra.bp_alerts)
    client = app.test_client()

    resp = client.get("/api/alerts/rules")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("_source") == "local_store"
    assert isinstance(body.get("rules"), list)
    assert len(body["rules"]) == 1
    rule = body["rules"][0]
    assert rule["id"] == "r-fast"
    assert rule["condition_json"]["alert_type"] == "token_velocity"


def test_api_alerts_rules_flag_off_uses_legacy(fresh_store, monkeypatch):
    """With CLAWMETRY_LOCAL_STORE_READ unset, the route falls back to the
    legacy dashboard helper — even if DuckDB has data."""
    ls, store = fresh_store
    store.ingest_alert_rule({
        "id": "r-legacy",
        "owner_hash": "owner-X",
        "condition_json": {"alert_type": "x"},
        "enabled": True,
    })

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    sys.modules.pop("routes.alerts", None)
    import routes.alerts as ra
    importlib.reload(ra)

    # Stub `dashboard._get_alert_rules` so the legacy path returns a known
    # sentinel that we can distinguish from the local-store response.
    import types
    fake_dashboard = types.ModuleType("dashboard")
    fake_dashboard._get_alert_rules = lambda: [{"id": "legacy-rule", "src": "fleet_db"}]
    monkeypatch.setitem(sys.modules, "dashboard", fake_dashboard)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(ra.bp_alerts)
    client = app.test_client()

    resp = client.get("/api/alerts/rules")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "_source" not in body, "flag-off path must not tag _source"
    assert body["rules"] == [{"id": "legacy-rule", "src": "fleet_db"}]


# ── 2b. Issue #1419 PR #1410 comms envelope ────────────────────────────────


def test_alerts_rules_comms_banner_for_stale_rule_cohort(monkeypatch):
    """The /api/alerts/rules response carries _comms with show_alerts_comms_banner
    when the user has 1+ rules, 0 fires, and the oldest rule is >24h old.

    Mirrors the PR #1410 conversion cohort: rules configured pre-fix that
    never triggered because daily_spent was stuck at 0 on no-OTLP installs.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path
    sys.modules.pop("routes.alerts", None)
    import routes.alerts as ra
    importlib.reload(ra)

    import types
    fake_d = types.ModuleType("dashboard")
    # 25h-old rule, never fired
    fake_d._get_alert_rules = lambda: [
        {"id": "stale-rule", "type": "threshold", "threshold": 5.0,
         "created_at": time.time() - 90000}
    ]
    fake_d._get_alert_history = lambda limit=50: []
    fake_d._get_budget_status = lambda: {"cost_source": "duckdb"}
    fake_d._is_pro_user = lambda: False
    monkeypatch.setitem(sys.modules, "dashboard", fake_d)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(ra.bp_alerts)
    body = app.test_client().get("/api/alerts/rules").get_json()
    assert body["_comms"]["show_alerts_comms_banner"] is True, body["_comms"]
    assert body["_comms"]["show_cloud_pro_cta"] is True, body["_comms"]
    assert body["_comms"]["cost_source"] == "duckdb"


def test_alerts_rules_comms_no_banner_when_rule_recently_fired(monkeypatch):
    """If any rule has fired, suppress the banner — there's nothing to convert."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")
    sys.modules.pop("routes.alerts", None)
    import routes.alerts as ra
    importlib.reload(ra)

    import types, time as _t
    fake_d = types.ModuleType("dashboard")
    fake_d._get_alert_rules = lambda: [
        {"id": "fired-rule", "type": "threshold", "threshold": 5.0,
         "created_at": _t.time() - 90000}
    ]
    fake_d._get_alert_history = lambda limit=50: [
        {"rule_id": "fired-rule", "fired_at": _t.time() - 300}
    ]
    fake_d._get_budget_status = lambda: {"cost_source": "duckdb"}
    fake_d._is_pro_user = lambda: False
    monkeypatch.setitem(sys.modules, "dashboard", fake_d)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(ra.bp_alerts)
    body = app.test_client().get("/api/alerts/rules").get_json()
    assert body["_comms"]["show_alerts_comms_banner"] is False
    assert body["_comms"]["show_cloud_pro_cta"] is False
    # last_fired_at should be stamped onto the rule
    assert body["rules"][0]["last_fired_at"] is not None


# ── 3. Heartbeat cache push ─────────────────────────────────────────────────


@pytest.fixture
def sync_with_rules(tmp_path, monkeypatch):
    """Reload `clawmetry.sync` against a fresh DuckDB seeded with alert
    rules. Yields (sync_module, local_store_module, config)."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    api_key = "cm_test_alerts_token_xyz"
    owner_hash = s._owner_hash_for_token(api_key)

    store = ls.get_store()
    for i in range(3):
        store.ingest_alert_rule({
            "id": f"rule-{i}",
            "owner_hash": owner_hash,
            "name": f"rule {i}",
            "condition_json": {"alert_type": "daily_spend", "threshold_value": i + 1},
            "enabled": True,
        })

    config = {
        "node_id":         "node-test",
        "api_key":         api_key,
        "encryption_key":  s.generate_encryption_key(),
    }

    yield s, ls, config

    try:
        ls.get_store().stop(flush=False)
    except Exception:
        pass


def test_build_alert_rules_cache_pushes_returns_one_entry(sync_with_rules):
    s, ls, config = sync_with_rules
    pushes = s._build_alert_rules_cache_pushes(config)
    assert isinstance(pushes, list)
    assert len(pushes) == 1
    entry = pushes[0]
    owner_hash = s._owner_hash_for_token(config["api_key"])
    assert entry["key"] == f"alerts:{owner_hash}:rules"
    assert entry["ttl_s"] == s.ALERT_RULES_CACHE_TTL_SEC == 3600
    blob = entry["blob"]
    assert isinstance(blob, str) and len(blob) > 0
    # Plaintext must not leak (rule name + alert_type are sensitive).
    assert "daily_spend" not in blob
    assert "rule-0" not in blob


def test_build_alert_rules_cache_pushes_empty_when_no_rules(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    # Boot the store so the DB file exists (no rules ingested).
    ls.get_store()
    config = {
        "node_id":         "node-empty",
        "api_key":         "cm_empty",
        "encryption_key":  s.generate_encryption_key(),
    }
    assert s._build_alert_rules_cache_pushes(config) == []
    try:
        ls.get_store().stop(flush=False)
    except Exception:
        pass


def test_build_alert_rules_cache_pushes_no_encryption_key(sync_with_rules):
    s, ls, config = sync_with_rules
    cfg = dict(config)
    cfg["encryption_key"] = None
    assert s._build_alert_rules_cache_pushes(cfg) == []


def test_pushed_blob_decrypts_to_alert_rules_shape(sync_with_rules):
    s, ls, config = sync_with_rules
    pushes = s._build_alert_rules_cache_pushes(config)
    assert len(pushes) == 1
    decoded = s.decrypt_payload(pushes[0]["blob"], config["encryption_key"])
    assert isinstance(decoded, dict)
    assert decoded["_shape"] == "alert_rules"
    assert decoded["_source"] == "local_store"
    assert decoded["count"] == 3
    assert len(decoded["rules"]) == 3
    # Each rule preserves the condition_json dict shape from DuckDB.
    sample = decoded["rules"][0]
    assert "id" in sample
    assert "condition_json" in sample
    assert isinstance(sample["condition_json"], dict)


# ── 4. Write-through dispatcher (cloud → DuckDB) ───────────────────────────


def test_apply_pending_write_alert_rule_upsert(sync_with_rules):
    """Cloud-authored alert_rule_upsert lands in local DuckDB."""
    s, ls, config = sync_with_rules
    body = {
        "id": "cloud-rule-1",
        "owner_hash": s._owner_hash_for_token(config["api_key"]),
        "name": "Cloud-authored",
        "alert_type": "session_cost",
        "threshold_value": 5.0,
        "enabled": True,
        "created_at": "2026-05-12T12:00:00Z",
        "updated_at": "2026-05-12T12:00:00Z",
    }
    s._apply_pending_write("alert_rule_upsert", {
        "type": "alert_rule_upsert",
        "id":   "cloud-rule-1",
        "body": body,
    })

    rows = ls.get_store().query_alert_rules()
    cloud_row = next((r for r in rows if r["id"] == "cloud-rule-1"), None)
    assert cloud_row is not None
    assert cloud_row["name"] == "Cloud-authored"
    # condition_json is the full cloud body — including fields OSS doesn't
    # break out into columns (alert_type, threshold_value).
    assert cloud_row["condition_json"]["alert_type"] == "session_cost"
    assert cloud_row["condition_json"]["threshold_value"] == 5.0


def test_apply_pending_write_alert_rule_delete(sync_with_rules):
    """Cloud-authored alert_rule_delete removes the row from local DuckDB."""
    s, ls, config = sync_with_rules
    # `sync_with_rules` already seeded rule-0/1/2 — pick one and delete it.
    s._apply_pending_write("alert_rule_delete", {
        "type": "alert_rule_delete",
        "id":   "rule-0",
    })
    remaining_ids = {r["id"] for r in ls.get_store().query_alert_rules()}
    assert "rule-0" not in remaining_ids
    assert {"rule-1", "rule-2"} <= remaining_ids


def test_dispatch_pending_queries_routes_writes(sync_with_rules, monkeypatch):
    """_dispatch_pending_queries handles both shapes (reads) and types
    (writes) in the same pending list. Read shapes still POST to
    /ingest/cache; writes apply locally with no /ingest/cache POST."""
    s, ls, config = sync_with_rules
    cache_posts = []

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/cache":
            cache_posts.append(payload)
            return {"ok": True}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(s, "_post", fake_post)

    pending = [
        {
            "type": "alert_rule_upsert",
            "id": "via-dispatch",
            "body": {
                "id": "via-dispatch",
                "name": "Via dispatch",
                "alert_type": "daily_spend",
                "threshold_value": 1.0,
                "enabled": True,
            },
        },
        {
            "type": "alert_rule_delete",
            "id": "rule-1",
        },
        # A junk item with an unknown type — must be silently skipped.
        {"type": "unknown_write", "id": "x"},
    ]
    s._dispatch_pending_queries(config, pending)

    rule_ids = {r["id"] for r in ls.get_store().query_alert_rules()}
    assert "via-dispatch" in rule_ids
    assert "rule-1" not in rule_ids
    # Writes intentionally don't POST to /ingest/cache — heartbeat's
    # cache_push handles the cloud-visible state on the next cycle.
    assert cache_posts == []


def test_send_heartbeat_attaches_alert_rules_push(sync_with_rules, monkeypatch):
    """End-to-end: send_heartbeat with seeded rules must include an alert
    rules entry in the heartbeat payload's cache_pushes list."""
    s, ls, config = sync_with_rules
    captured = {}

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            captured["payload"] = payload
            return {"sync_allowed": True, "pending_queries": []}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(s, "_post", fake_post)
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    assert s.send_heartbeat(config) is True
    payload = captured["payload"]
    pushes = payload.get("cache_pushes", [])
    alert_keys = [p for p in pushes if p["key"].startswith("alerts:")]
    assert len(alert_keys) == 1
    entry = alert_keys[0]
    assert entry["ttl_s"] == 3600
    assert isinstance(entry["blob"], str) and len(entry["blob"]) > 0
