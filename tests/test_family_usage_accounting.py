"""Growing sessions must not add successive lifetime estimates together."""
from types import SimpleNamespace

import pytest

@pytest.fixture(scope="session", autouse=True)
def server():
    """These tests use isolated DuckDB/Flask clients, never a live daemon."""
    return None


@pytest.fixture
def store(tmp_path, monkeypatch):
    # Other suites reload local_store. Resolve the same current module that
    # sync imports instead of retaining a collection-time module instance.
    from clawmetry import local_store as ls
    monkeypatch.setattr(ls, "DB_PATH", tmp_path / "usage.duckdb")
    ls.invalidate_aggregate_cache()
    result = ls.LocalStore()
    yield result
    result.stop(flush=True)
    ls.invalidate_aggregate_cache()


def event(eid, *, cost=0, tokens=0, day="2026-09-29", runtime="codex"):
    return {"id": runtime + ":" + eid, "node_id": "test-node",
            "session_id": runtime + ":session", "agent_id": "main",
            "event_type": "message", "ts": day + "T12:00:00Z",
            "model": "gpt-5", "cost_usd": cost, "token_count": tokens,
            "data": {"_runtime": runtime, "role": "assistant"}}


def totals(store):
    rows = store.query_aggregates(runtime="codex")
    return sum(r["cost_usd"] for r in rows), sum(r["token_count"] for r in rows)


def reconcile(store, rows):
    store.ingest_many(rows)
    store.reconcile_family_event_usage("codex:session", rows)


def test_growing_lifetime_allocation_replaces_previous_amount(store):
    reconcile(store, [event("first", cost=10, tokens=100)])
    # Prime both caches before the second pass.
    assert totals(store) == (10, 100)
    reconcile(store, [event("first"), event("second", cost=12, tokens=120)])
    assert totals(store) == (12, 120)
    assert store.verify_integrity()["status"] == "valid"
    rows = [r for r in store.query_rollup_runtime_daily() if r["runtime"] == "codex"]
    assert sum(r["cost_usd"] for r in rows) == pytest.approx(12)
    assert sum(r["tokens"] for r in rows) == 120


def test_upgrade_repairs_inflated_history_and_keeps_original_days(store):
    # Old versions inserted lifetime costs into successive transcript rows.
    store.ingest_many([event("old1", cost=10),
                       event("old2", cost=12, day="2026-09-30")])
    store.flush()
    assert totals(store) == (22, 0)
    expected = [event("old1"), event("old2", day="2026-09-30"),
                event("usage1", cost=10, tokens=100),
                event("usage2", cost=2, tokens=20, day="2026-09-30")]
    reconcile(store, expected)
    assert totals(store) == (12, 120)
    by_day = {r["day"]: r for r in store.query_aggregates(runtime="codex")}
    assert by_day["2026-09-29"]["cost_usd"] == 10
    assert by_day["2026-09-30"]["cost_usd"] == 2
    before = store._fetch("SELECT id, chain_hash FROM events ORDER BY id", [])
    reconcile(store, expected)
    assert totals(store) == (12, 120)
    assert store._fetch("SELECT id, chain_hash FROM events ORDER BY id", []) == before
    assert store.verify_integrity()["status"] == "valid"


def test_reconciliation_preserves_other_sessions(store):
    store.ingest_many([event("other", cost=7, tokens=70, runtime="openclaw")])
    reconcile(store, [event("first", cost=10, tokens=100)])
    other = store.query_aggregates(runtime="openclaw")
    assert sum(r["cost_usd"] for r in other) == 7
    with pytest.raises(ValueError):
        store.reconcile_family_event_usage("codex:session", [event("bad", runtime="openclaw")])


def test_billing_coverage_does_not_apply_claude_plan_to_codex(monkeypatch):
    import dashboard
    from clawmetry import sync
    claude = {"mode": "subscription", "label": "Claude Max 20x"}
    monkeypatch.setattr(sync, "_build_billing_payload", lambda _: {
        "account_plan": claude, "runtimes": {
            "claude_code": claude,
            "codex": {"mode": "unknown", "label": "Unknown"}}})
    cov = dashboard._get_billing_coverage([], 1, 2, 3,
        fallback_all_covered_when_no_models=True, runtime="codex")
    assert cov["all_covered"] is False
    assert cov["any_subscription"] is False
    assert cov["account_plan"] is None
    assert cov["subscription_labels"] == []
    assert set(cov["runtimes"]) == {"codex"}


def test_selected_subscription_uses_its_own_label(monkeypatch):
    import dashboard
    from clawmetry import sync
    claude = {"mode": "subscription", "label": "Claude Max 20x"}
    codex = {"mode": "subscription", "label": "ChatGPT Pro"}
    monkeypatch.setattr(sync, "_build_billing_payload", lambda _: {
        "account_plan": claude, "runtimes": {"claude_code": claude, "codex": codex}})
    cov = dashboard._get_billing_coverage([], 1, 2, 3,
        fallback_all_covered_when_no_models=True, runtime="codex")
    assert cov["all_covered"] is True
    assert cov["account_plan"] == codex
    assert cov["subscription_labels"] == ["ChatGPT Pro"]


def test_sync_growing_session_counts_only_latest_lifetime_total(store, monkeypatch):
    from clawmetry import sync, entitlements, local_store as ls
    from clawmetry.adapters.base import Session, Event

    current = {"cost": 10, "tokens": 100, "count": 1}

    class Adapter:
        name = "codex"
        def detect(self):
            return SimpleNamespace(detected=True)
        def list_sessions(self, limit):
            return [Session(agent="codex", id="session", model="gpt-5",
                started_at=1790683200, ended_at=1790683200 + current["count"],
                cost_usd=current["cost"], total_tokens=current["tokens"])]
        def list_events(self, session_id, limit):
            return [Event(agent="codex", session_id=session_id, id=str(i),
                type="message", role="assistant", ts=1790683200 + i,
                content="fixture") for i in range(current["count"])]

    monkeypatch.setattr(ls, "get_store", lambda *a, **kw: store)
    monkeypatch.setattr(sync, "_family_adapter_classes", lambda: [Adapter])
    monkeypatch.setattr(sync, "_sync_allowed", lambda: True)
    monkeypatch.setattr(sync, "_ingest_keepalive_heartbeat", lambda *a: None)
    monkeypatch.setattr(sync, "_openclaw_spawned_claude_ids", lambda: set())
    monkeypatch.setattr(entitlements, "get_entitlement", lambda: SimpleNamespace(allows_runtime=lambda r: True))
    state = {}
    sync.sync_family_runtimes({"node_id": "test-node"}, state, {})
    store.flush()
    assert totals(store)[0] == 10
    current.update(cost=12, tokens=120, count=2)
    sync.sync_family_runtimes({"node_id": "test-node"}, state, {})
    store.flush()
    assert totals(store) == (12, 120)


@pytest.mark.parametrize("poisoned_mark", [False, True])
def test_loaded_pro_revision_repairs_idle_sessions_after_restart(store, monkeypatch, poisoned_mark):
    import importlib.metadata
    import sys
    from clawmetry import sync, entitlements, local_store as ls
    from clawmetry.adapters.base import Session, Event

    installed = {"version": "0.7.32"}
    loaded = SimpleNamespace(__version__="0.7.32")
    reads = []

    class Adapter:
        name = "codex"
        def detect(self):
            return SimpleNamespace(detected=True)
        def list_sessions(self, limit):
            fixed = loaded.__version__ == "0.7.33"
            return [Session(agent="codex", id="session", model="gpt-5",
                started_at=1790683200, ended_at=1790683201,
                cost_usd=10 if fixed else 90000, total_tokens=1000 if fixed else 0)]
        def list_events(self, session_id, limit):
            reads.append(loaded.__version__)
            return [Event(agent="codex", session_id=session_id, id="first",
                type="message", role="assistant", ts=1790683200, content="fixture")]

    monkeypatch.setitem(sys.modules, "clawmetry_pro", loaded)
    monkeypatch.setattr(importlib.metadata, "version", lambda _: installed["version"])
    monkeypatch.setattr(ls, "get_store", lambda *a, **kw: store)
    monkeypatch.setattr(sync, "_family_adapter_classes", lambda: [Adapter])
    monkeypatch.setattr(sync, "_sync_allowed", lambda: True)
    monkeypatch.setattr(sync, "_ingest_keepalive_heartbeat", lambda *a: None)
    monkeypatch.setattr(sync, "_openclaw_spawned_claude_ids", lambda: set())
    monkeypatch.setattr(entitlements, "get_entitlement", lambda: SimpleNamespace(allows_runtime=lambda r: True))
    state = {}
    config = {"node_id": "test-node"}
    sync.sync_family_runtimes(config, state, {})
    assert totals(store) == (90000, 0)
    immutable = store._fetch("SELECT id, chain_hash FROM events ORDER BY id", [])

    # Replacing the distribution does not replace the process's cached parser.
    installed["version"] = "0.7.33"
    assert sync.sync_family_runtimes(config, state, {}) == 0
    assert reads == ["0.7.32"]
    mark = state["family_event_high_water"]["codex:session"]
    assert mark.partition("@@")[2].startswith("0.7.32/")
    if poisoned_mark:
        # A previous release could already have stamped the new disk version
        # using old code. The new salt must repair that mark too.
        state["family_event_high_water"]["codex:session"] = (
            mark.partition("@@")[0] + "@@0.7.33/ctx1/q2/usage1/t2")

    # A restarted process loads the new package and parser for the same input.
    loaded = SimpleNamespace(__version__="0.7.33")
    monkeypatch.setitem(sys.modules, "clawmetry_pro", loaded)
    assert sync.sync_family_runtimes(config, state, {}) > 0
    assert totals(store) == (10, 1000)
    assert reads == ["0.7.32", "0.7.33"]
    assert sync.sync_family_runtimes(config, state, {}) == 0
    assert totals(store) == (10, 1000)
    assert store._fetch("SELECT id, chain_hash FROM events ORDER BY id", []) == immutable
    assert store.verify_integrity()["status"] == "valid"


@pytest.mark.parametrize("loaded", [None, SimpleNamespace()])
def test_unavailable_loaded_pro_version_does_not_claim_disk_version(monkeypatch, loaded):
    import importlib.metadata
    import sys
    from clawmetry import sync
    monkeypatch.setitem(sys.modules, "clawmetry_pro", loaded)
    monkeypatch.setattr(importlib.metadata, "version", lambda _: "9.9.9")
    assert sync._family_ingest_rev() == "usage2/t2"


def usage(eid, *, cost=1, tokens=100, model='gpt-5', cached=0):
    row = event(eid, cost=cost, tokens=tokens)
    row.update(event_type='usage', model=model)
    row['data']['extra'] = {'usageBasis': 'per_call', 'model': model,
        'costUsd': cost, 'inputTokens': tokens - cached,
        'cacheReadInputTokens': cached, 'outputTokens': 0}
    return row


def test_native_usage_keeps_distinct_responses_splits_and_unknown_prices(store):
    from clawmetry.family_usage import allocate_usage
    rows = [event('message'), usage('a', cached=80), usage('b', cost=None, model='')]
    allocate_usage(rows, SimpleNamespace(cost_usd=99, model='gpt-5'))
    reconcile(store, rows)
    assert totals(store) == (1, 200)
    splits = store.query_daily_usage_splits(runtime='codex')
    assert sum(r['input_tokens'] for r in splits) == 120
    assert sum(r['cache_read_tokens'] for r in splits) == 80
    assert store._fetch("SELECT cost_usd, model FROM events WHERE id='codex:b'", []) == [(None, None)]


def test_native_records_retire_legacy_source_and_aggregate_cache(store):
    reconcile(store, [usage('legacy')])
    assert totals(store) == (1, 100)
    reconcile(store, [usage('native1'), usage('native2')])
    assert totals(store) == (2, 200)
    assert sum(r['input_tokens'] for r in store.query_daily_usage_splits(runtime='codex')) == 200
    rollups = store.query_rollup_model_daily()
    assert sum(r['tokens_in'] for r in rollups) == 200
    # Appending immutable usage records must invalidate a primed sum cache.
    reconcile(store, [usage('native1'), usage('native2'), usage('native3')])
    assert totals(store) == (3, 300)


def test_retired_usage_restores_token_splits_when_source_reappears(store):
    original = usage('original', cached=80)
    reconcile(store, [original])
    expected = store.query_rollup_model_daily()
    reconcile(store, [usage('replacement', cached=30)])
    reconcile(store, [original])
    assert totals(store) == (1, 100)
    assert store.query_rollup_model_daily() == expected
    daily = store.query_daily_usage_splits(runtime='codex')
    assert sum(r['input_tokens'] for r in daily) == 20
    assert sum(r['cache_read_tokens'] for r in daily) == 80
    reconcile(store, [usage('replacement', cached=30)])
    assert sum(r['cache_read'] for r in store.query_rollup_model_daily()) == 30


def test_reconciliation_rolls_back_metrics_and_rollups_together(store, monkeypatch):
    reconcile(store, [event('first', cost=10, tokens=100)])
    before = store.query_rollup_runtime_daily()
    def fail(*args):
        raise RuntimeError('rollup unavailable')
    monkeypatch.setattr(store, '_apply_rollup_deltas_locked', fail)
    with pytest.raises(RuntimeError, match='rollup unavailable'):
        store.reconcile_family_event_usage('codex:session', [event('first', cost=12, tokens=120)])
    assert totals(store) == (10, 100)
    assert store.query_rollup_runtime_daily() == before


def test_cached_native_usage_survives_usage_handler(store, monkeypatch):
    from routes import usage as route
    from datetime import datetime
    now = datetime.now().astimezone()
    rows = [usage('cached', cached=80)]
    rows[0]['ts'] = now.isoformat()
    reconcile(store, rows)
    monkeypatch.setattr(route, '_ls_call', lambda name, *a, **kw: getattr(store, name)(*a, **kw))
    result = route._try_local_store_usage(runtime='codex')
    assert result is not None
    day = next(r for r in result['days'] if r['date'] == now.strftime('%Y-%m-%d'))
    assert day['tokens'] == 100


def test_hosted_periods_use_calendar_and_runtime_billing(monkeypatch):
    import dashboard
    from clawmetry.usage_snapshot import runtime_periods
    monkeypatch.setattr(dashboard, '_get_billing_coverage', lambda *a, **kw: {'runtime': kw['runtime']})
    result = runtime_periods([
        {'day': '2026-09-28', 'runtime': 'codex', 'tokens': 100, 'cost_usd': 1},
        {'day': '2026-10-01', 'runtime': 'codex', 'tokens': 20, 'cost_usd': .2},
        {'day': '2026-10-01', 'runtime': 'claude_code', 'tokens': 900, 'cost_usd': 9},
    ], '2026-10-01', '2026-09-28', '2026-10-01')
    assert result['codex']['today'] == result['codex']['month'] == 20
    assert result['codex']['week'] == 120
    assert result['codex']['weekCost'] == 1.2
    assert result['codex']['billingCoverage'] == {'runtime': 'codex'}


def test_saved_anomaly_uses_current_totals_and_keeps_history(monkeypatch):
    from clawmetry import cost_anomaly as ca
    from datetime import date, timedelta
    today = date.today()
    rows = [{'day': today.isoformat(), 'cost_usd': 21},
            {'day': (today - timedelta(days=6)).isoformat(), 'cost_usd': 28}]
    reads = []
    monkeypatch.setattr(ca, '_cache', (None, 0, None))
    monkeypatch.setattr(ca, '_read_days', lambda *a: reads.append(a) or rows)
    history = [{'rule_id': 'anomaly_daily', 'message': 'today $89063.11'},
               {'rule_id': 'anomaly_daily', 'message': 'older'},
               {'rule_id': 'agent_down', 'message': 'agent down'}]
    active = ca.refresh_active(history)
    assert len(active) == 2
    assert 'today $21.00' in active[0]['message']
    assert '$4.00/day' in active[0]['message']
    assert 'all runtimes' in active[0]['message']
    assert 'not a bill' in active[0]['message']
    assert history[0]['message'] == 'today $89063.11'
    assert ca.current()['daily'] == 21
    assert len(reads) == 1
    assert reads[0] == ((today - timedelta(days=7)).isoformat(), today.isoformat())
    # A repaired/rolled-over day stops showing the historical alert.
    monkeypatch.setattr(ca, '_cache', (None, 0, None))
    rows[0]['cost_usd'] = 0
    assert ca.refresh_active(history) == [history[2]]


def test_active_alert_endpoint_revalidates_saved_spending(tmp_path, monkeypatch):
    import dashboard
    import sqlite3
    import time
    from clawmetry import cost_anomaly as ca
    path = tmp_path / 'alerts.sqlite'
    def connection():
        db = sqlite3.connect(path)
        db.row_factory = sqlite3.Row
        return db
    with connection() as db:
        db.execute('CREATE TABLE alert_history (rule_id TEXT, message TEXT, acknowledged INT, fired_at REAL)')
        db.execute('INSERT INTO alert_history VALUES (?,?,0,?)',
                   ('anomaly_daily', 'today $89063.11', time.time()))
    monkeypatch.setattr(dashboard, '_fleet_db', connection)
    monkeypatch.setattr(ca, 'current', lambda: {'message': 'current verified amount'})
    assert dashboard._get_active_alerts()[0]['message'] == 'current verified amount'
    assert dashboard._get_alert_history()[0]['message'] == 'today $89063.11'
    monkeypatch.setattr(ca, 'current', lambda: None)
    assert dashboard._get_active_alerts() == []


def test_anomaly_cache_invalidates_at_local_midnight_and_read_failure(monkeypatch):
    from clawmetry import cost_anomaly as ca
    from datetime import date, timedelta
    import time
    monkeypatch.setattr(ca, '_cache', (date.today() - timedelta(days=1),
        time.monotonic() + 999, {'message': 'yesterday'}))
    def unavailable(*args):
        raise RuntimeError('daemon unavailable')
    monkeypatch.setattr(ca, '_read_days', unavailable)
    assert ca.current() is None


def test_anomaly_refresh_preserves_budget_monitor_threshold_rules(monkeypatch):
    import dashboard as d
    from clawmetry import cost_anomaly as ca
    class StopMonitor(BaseException):
        pass
    ticks = []
    def sleep(_):
        if ticks:
            raise StopMonitor()
        ticks.append(1)
    alerts = []
    monkeypatch.setattr(d, 'time', SimpleNamespace(time=lambda: 2000000000, sleep=sleep))
    monkeypatch.setattr(d, '_otel_last_received', 0)
    monkeypatch.setattr(d, '_last_heartbeat_ts', 0)
    monkeypatch.setattr(d, '_security_posture_hash', '')
    monkeypatch.setattr(d, '_budget_alert_cooldowns', {})
    monkeypatch.setattr(d, 'metrics_store', {'webhooks': [], 'cost': []})
    monkeypatch.setattr(d, '_get_budget_status', lambda: {'daily_spent': 200})
    monkeypatch.setattr(d, '_get_budget_config', lambda: {
        'auto_pause_threshold_usd': 100, 'auto_pause_action': 'alert'})
    monkeypatch.setattr(d, '_compute_velocity_status', lambda: {'active': False})
    monkeypatch.setattr(d, '_detect_error_spikes', lambda: None)
    monkeypatch.setattr(d, '_detect_security_metadata', lambda: {})
    monkeypatch.setattr(d, '_get_alert_rules', lambda: [])
    monkeypatch.setattr(d, '_fire_alert', lambda **kw: alerts.append(kw))
    monkeypatch.setattr(d, '_dispatch_configured_webhooks', lambda *a: None)
    monkeypatch.setattr(ca, 'current', lambda: None)
    with pytest.raises(StopMonitor):
        d._budget_monitor_loop()
    assert any(a['rule_id'] == 'auto_pause_daily_alert_only' and '$200.00' in a['message']
               for a in alerts)
