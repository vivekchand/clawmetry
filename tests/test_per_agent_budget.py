"""Tests for issue #951 — per-agent budget limits + tiered 80%/100% alerts.

Five surfaces:
  1. ``agent_budgets`` table — round-trip PUT/GET via the local-store API
     methods (``set_agent_budget`` / ``get_agent_budget`` /
     ``query_agent_budgets`` / ``delete_agent_budget``).
  2. ``/api/agents/<id>/budget`` PUT then GET — full HTTP round-trip via the
     Flask test client.
  3. 80% trigger — fires ``budget.warning``, does NOT auto-pause.
  4. 100% trigger — fires ``budget.critical`` AND auto-pauses when
     ``auto_pause_enabled`` is True.
  5. Dedup — same threshold crossed twice within the same period only
     fires once.
  6. Fallback — agent with no override row uses the global budget.
"""
from __future__ import annotations

import importlib
import os
import sys
import time
import types

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload `clawmetry.local_store` against a fresh DuckDB file."""
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
def dashboard_module(fresh_store, monkeypatch, tmp_path):
    """Import dashboard.py with a clean module slate so ``_get_agent_budget``
    et al. resolve to the freshly-loaded local_store. Also resets the
    in-memory cost store and tier-state dedup map between tests."""
    # Reload routes.alerts so its `import dashboard as _d` indirection
    # refers to the same dashboard import the test sees.
    sys.modules.pop("dashboard", None)
    sys.modules.pop("routes.alerts", None)
    import dashboard as _d
    import routes.alerts as ra
    importlib.reload(ra)

    # Point fleet-DB at a temp file so the test doesn't touch the user's
    # real ~/.clawmetry/fleet.db (and so each test gets fresh tables).
    _d.FLEET_DB_PATH = str(tmp_path / "fleet.db")

    # Wipe in-memory cost store + dedup map so each test starts clean.
    with _d._metrics_lock:
        _d.metrics_store["cost"].clear()
    _d._budget_agent_tier_state.clear()
    _d._budget_alert_cooldowns.clear()
    _d._budget_paused = False
    _d._budget_paused_at = 0
    _d._budget_paused_reason = ""

    # Ensure fleet-DB tables (budget_config, alert_rules, alert_history)
    # exist for this run — they're lazily initialized on dashboard boot.
    try:
        _d._budget_init_db()
    except Exception:
        pass

    # Stub out pause/telegram side effects so tests don't hit subprocess /
    # network. We still want _fire_alert to write to alert_history, so we
    # keep its internals; just stub the destinations.
    monkeypatch.setattr(_d, "_pause_gateway", lambda: None)
    monkeypatch.setattr(_d, "_send_telegram_alert", lambda msg: None)

    yield _d


def _add_cost(_d, agent_id, usd, when=None):
    """Append a cost-store entry tagged with ``agent_id``."""
    entry = {
        "timestamp": when if when is not None else time.time(),
        "usd": float(usd),
        "agent": agent_id,
        "model": "test-model",
    }
    with _d._metrics_lock:
        _d.metrics_store["cost"].append(entry)


def _count_alerts_for(_d, rule_id_substring):
    """Count rows in alert_history whose rule_id contains the substring."""
    try:
        with _d._fleet_db_lock:
            db = _d._fleet_db()
            rows = db.execute(
                "SELECT rule_id FROM alert_history WHERE rule_id LIKE ?",
                (f"%{rule_id_substring}%",),
            ).fetchall()
            db.close()
        return len(rows)
    except Exception:
        return 0


# ── 1. Schema round-trip ───────────────────────────────────────────────────


def test_set_get_agent_budget_round_trip(fresh_store):
    ls, store = fresh_store
    store.set_agent_budget("agent-a", daily_limit_usd=5.0, monthly_limit_usd=100.0)
    row = store.get_agent_budget("agent-a")
    assert row is not None
    assert row["agent_id"] == "agent-a"
    assert row["daily_limit_usd"] == 5.0
    assert row["monthly_limit_usd"] == 100.0
    assert row["updated_at"] > 0

    # Upsert overwrites
    store.set_agent_budget("agent-a", daily_limit_usd=7.5, monthly_limit_usd=None)
    row = store.get_agent_budget("agent-a")
    assert row["daily_limit_usd"] == 7.5
    assert row["monthly_limit_usd"] is None


def test_query_agent_budgets_lists_all_rows(fresh_store):
    ls, store = fresh_store
    store.set_agent_budget("agent-a", daily_limit_usd=1.0)
    store.set_agent_budget("agent-b", monthly_limit_usd=50.0)
    rows = store.query_agent_budgets()
    ids = {r["agent_id"] for r in rows}
    assert ids == {"agent-a", "agent-b"}


def test_delete_agent_budget_removes_row(fresh_store):
    ls, store = fresh_store
    store.set_agent_budget("agent-x", daily_limit_usd=2.0)
    assert store.get_agent_budget("agent-x") is not None
    n = store.delete_agent_budget("agent-x")
    assert n == 1
    assert store.get_agent_budget("agent-x") is None
    # Idempotent second delete
    assert store.delete_agent_budget("agent-x") == 0


def test_get_agent_budget_returns_none_when_missing(fresh_store):
    ls, store = fresh_store
    assert store.get_agent_budget("never-existed") is None


# ── 2. HTTP API round-trip ─────────────────────────────────────────────────


def _make_client(dashboard_module):
    from flask import Flask
    import routes.alerts as ra
    app = Flask(__name__)
    app.register_blueprint(ra.bp_budget)
    return app.test_client()


def test_put_then_get_agent_budget_via_api(dashboard_module):
    client = _make_client(dashboard_module)
    resp = client.put(
        "/api/agents/agent-1/budget",
        json={"daily_limit_usd": 3.0, "monthly_limit_usd": 75.0},
    )
    assert resp.status_code == 200, resp.data
    body = resp.get_json()
    assert body["ok"] is True

    g = client.get("/api/agents/agent-1/budget")
    assert g.status_code == 200
    payload = g.get_json()
    assert payload["agent_id"] == "agent-1"
    assert payload["daily_limit"] == 3.0
    assert payload["monthly_limit"] == 75.0
    assert payload["daily_limit_source"] == "agent"
    assert payload["monthly_limit_source"] == "agent"


def test_delete_agent_budget_via_api(dashboard_module):
    client = _make_client(dashboard_module)
    client.put(
        "/api/agents/agent-2/budget",
        json={"daily_limit_usd": 1.0},
    )
    d = client.delete("/api/agents/agent-2/budget")
    assert d.status_code == 200
    assert d.get_json()["deleted"] == 1
    # Second delete is a no-op
    d2 = client.delete("/api/agents/agent-2/budget")
    assert d2.get_json()["deleted"] == 0


def test_put_rejects_non_numeric(dashboard_module):
    client = _make_client(dashboard_module)
    resp = client.put(
        "/api/agents/agent-3/budget",
        json={"daily_limit_usd": "not a number"},
    )
    assert resp.status_code == 400


def test_api_budget_root_includes_agent_overrides(dashboard_module):
    client = _make_client(dashboard_module)
    client.put(
        "/api/agents/agent-root/budget",
        json={"daily_limit_usd": 2.5},
    )
    r = client.get("/api/budget")
    assert r.status_code == 200
    body = r.get_json()
    assert "config" in body and "agents" in body
    assert "agent-root" in body["agents"]
    assert body["agents"]["agent-root"]["daily_limit_usd"] == 2.5


# ── 3. Tiered alerts ───────────────────────────────────────────────────────


def test_warning_at_80_percent_no_pause(dashboard_module):
    _d = dashboard_module
    _d._set_agent_budget("a-warn", daily_limit_usd=10.0)
    _add_cost(_d, "a-warn", 8.0)  # 80%
    _d._budget_check()
    assert _count_alerts_for(_d, "a-warn") >= 1
    assert _count_alerts_for(_d, "warning") >= 1
    assert _d._budget_paused is False


def test_critical_at_100_percent_pauses_when_enabled(dashboard_module):
    _d = dashboard_module
    _d._set_budget_config({"auto_pause_enabled": True})
    _d._set_agent_budget("a-crit", daily_limit_usd=10.0)
    _add_cost(_d, "a-crit", 10.0)  # 100%
    _d._budget_check()
    assert _count_alerts_for(_d, "a-crit") >= 1
    assert _count_alerts_for(_d, "critical") >= 1
    assert _d._budget_paused is True


def test_critical_without_autopause_fires_alert_only(dashboard_module):
    _d = dashboard_module
    _d._set_budget_config({"auto_pause_enabled": False})
    _d._set_agent_budget("a-crit-nopause", daily_limit_usd=10.0)
    _add_cost(_d, "a-crit-nopause", 12.0)  # 120%
    _d._budget_check()
    assert _count_alerts_for(_d, "a-crit-nopause") >= 1
    assert _d._budget_paused is False


# ── 4. Dedup ───────────────────────────────────────────────────────────────


def test_dedup_same_tier_same_period_fires_once(dashboard_module):
    _d = dashboard_module
    _d._set_agent_budget("a-dedup", daily_limit_usd=10.0)
    _add_cost(_d, "a-dedup", 8.0)
    _d._budget_check()
    n1 = _count_alerts_for(_d, "a-dedup")
    # More spend, but still in the warning tier → should NOT re-fire.
    _add_cost(_d, "a-dedup", 0.5)
    _d._budget_check()
    n2 = _count_alerts_for(_d, "a-dedup")
    assert n2 == n1, "warning tier deduped within same day"


def test_warning_then_critical_both_fire_once_each(dashboard_module):
    _d = dashboard_module
    _d._set_budget_config({"auto_pause_enabled": False})
    _d._set_agent_budget("a-escalate", daily_limit_usd=10.0)
    _add_cost(_d, "a-escalate", 8.0)  # 80% → warning
    _d._budget_check()
    warns1 = _count_alerts_for(_d, "a-escalate_daily_warning")
    crits1 = _count_alerts_for(_d, "a-escalate_daily_critical")
    assert warns1 >= 1
    assert crits1 == 0
    _add_cost(_d, "a-escalate", 5.0)  # → 130% → critical
    _d._budget_check()
    warns2 = _count_alerts_for(_d, "a-escalate_daily_warning")
    crits2 = _count_alerts_for(_d, "a-escalate_daily_critical")
    assert warns2 == warns1, "warning should not re-fire after critical"
    assert crits2 >= 1


# ── 5. Fallback to global ──────────────────────────────────────────────────


def test_no_override_falls_back_to_global(dashboard_module):
    _d = dashboard_module
    # No per-agent override row exists for 'a-fallback'.
    status = _d._get_agent_budget_status("a-fallback")
    assert status["daily_limit_source"] in ("none", "global")
    assert status["has_override"] is False


def test_override_takes_precedence_over_global(dashboard_module):
    _d = dashboard_module
    _d._set_budget_config({"daily_limit": 99.0, "monthly_limit": 999.0})
    _d._set_agent_budget("a-precedence", daily_limit_usd=4.0)
    status = _d._get_agent_budget_status("a-precedence")
    assert status["daily_limit"] == 4.0
    assert status["daily_limit_source"] == "agent"
    # Monthly side falls back to global because override is None.
    assert status["monthly_limit"] == 999.0
    assert status["monthly_limit_source"] == "global"


# ── 6. Pro-tier gate on Telegram dispatch (issue #1168) ──────────────────────
#
# Per-agent LIMITS are OSS table-stakes (cost control). Per-agent Telegram
# DISPATCH is Cloud-Pro only. These tests assert that an OSS user (no
# ``cm_`` token, no Pro plan) crossing 80% / 100% on a per-agent budget
# does NOT trigger ``_send_telegram_alert`` even though the banner +
# alert-history row still fire.


@pytest.fixture
def telegram_spy(dashboard_module, monkeypatch):
    """Replace ``_send_telegram_alert`` with a counting spy."""
    _d = dashboard_module
    calls = []
    monkeypatch.setattr(_d, "_send_telegram_alert",
                        lambda msg: calls.append(msg))
    return _d, calls


def test_oss_user_does_not_trigger_telegram_on_per_agent_warning(telegram_spy,
                                                                  monkeypatch):
    """Regression for #1168: OSS user with per-agent budget at 80%
    must NOT fire Telegram dispatch (banner + history row are fine)."""
    _d, calls = telegram_spy
    # OSS = not Pro (no cm_ token, no cached plan).
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)

    _d._set_agent_budget("oss-warn", daily_limit_usd=10.0)
    _add_cost(_d, "oss-warn", 8.0)  # 80%
    _d._budget_check()

    # Banner / history row still fires — limits are free, visualisation is free.
    assert _count_alerts_for(_d, "oss-warn") >= 1
    # Telegram dispatch is gated.
    assert calls == [], (
        "OSS user should not trigger Telegram on per-agent threshold "
        f"(got {len(calls)} dispatch(es))"
    )


def test_oss_user_does_not_trigger_telegram_on_per_agent_critical(telegram_spy,
                                                                   monkeypatch):
    """Same gate at the 100% / critical tier — banner + auto-pause still
    work (those are free), but Telegram fan-out is Pro-only."""
    _d, calls = telegram_spy
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)
    _d._set_budget_config({"auto_pause_enabled": True})
    _d._set_agent_budget("oss-crit", daily_limit_usd=10.0)
    _add_cost(_d, "oss-crit", 12.0)  # 120%
    _d._budget_check()

    assert _count_alerts_for(_d, "oss-crit") >= 1
    # Auto-pause is a free cost-control feature, must still trigger.
    assert _d._budget_paused is True
    # Telegram dispatch is gated.
    assert calls == []


def test_pro_user_still_triggers_telegram_on_per_agent_warning(telegram_spy,
                                                                monkeypatch):
    """Cloud-Pro user gets the same alert PLUS Telegram dispatch."""
    _d, calls = telegram_spy
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    _d._set_agent_budget("pro-warn", daily_limit_usd=10.0)
    _add_cost(_d, "pro-warn", 8.0)
    _d._budget_check()

    assert _count_alerts_for(_d, "pro-warn") >= 1
    assert len(calls) >= 1, (
        "Cloud-Pro user should receive Telegram dispatch on per-agent threshold"
    )


def test_api_budget_root_surfaces_pro_dispatch_flag(dashboard_module,
                                                     monkeypatch):
    """``/api/budget`` advertises ``pro_dispatch_enabled`` so the UI can
    render the inline upsell instead of pretending alerts will fire."""
    _d = dashboard_module
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)
    client = _make_client(_d)
    r = client.get("/api/budget")
    assert r.status_code == 200
    body = r.get_json()
    assert "pro_dispatch_enabled" in body
    assert body["pro_dispatch_enabled"] is False

    # Flip to Pro and confirm the flag propagates.
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)
    r2 = client.get("/api/budget")
    assert r2.get_json()["pro_dispatch_enabled"] is True
