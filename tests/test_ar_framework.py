"""Data-layer tests for the Agent Resources (AR) framework — issue #1713.

Covers the two new DuckDB tables (agent_resources_rules, agent_resources_history)
and the five CRUD methods added to LocalStore, plus _DAEMON_METHODS membership
for the daemon proxy allowlist.
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
    """Fresh DuckDB-backed LocalStore for each test. Yields (module, store)."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ar_test.duckdb")
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


def _rule(rule_id: str = "r-001", **kwargs) -> dict:
    return {
        "id": rule_id,
        "name": "Stop burnout",
        "trigger_type": "forward_progress",
        "threshold": 0.0,
        "window_seconds": 300,
        "action_type": "alert_only",
        "cooldown_seconds": 300,
        "created_at": int(time.time()),
        **kwargs,
    }


def _entry(entry_id: str = "h-001", rule_id: str = "r-001", **kwargs) -> dict:
    return {
        "id": entry_id,
        "rule_id": rule_id,
        "session_id": "sess-abc",
        "triggered_at": int(time.time()),
        "action_type": "alert_only",
        **kwargs,
    }


# ── Tables exist after LocalStore init ────────────────────────────────────


def test_ar_tables_exist(fresh_store):
    ls, store = fresh_store
    rows = store._fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name IN ('agent_resources_rules', 'agent_resources_history') "
        "ORDER BY table_name",
        [],
    )
    names = {r[0] for r in rows}
    assert "agent_resources_rules" in names
    assert "agent_resources_history" in names


# ── Rules round-trip ──────────────────────────────────────────────────────


def test_persist_and_list_ar_rule(fresh_store):
    ls, store = fresh_store
    store.persist_ar_rule(_rule("r-001", name="Stop burnout", enabled=True))
    rows = store.list_ar_rules()
    assert len(rows) == 1
    r = rows[0]
    assert r["id"] == "r-001"
    assert r["name"] == "Stop burnout"
    assert r["trigger_type"] == "forward_progress"
    assert r["action_type"] == "alert_only"
    assert r["enabled"] is True


def test_delete_ar_rule(fresh_store):
    ls, store = fresh_store
    store.persist_ar_rule(_rule("r-del"))
    assert store.delete_ar_rule("r-del") == 1
    assert store.delete_ar_rule("r-del") == 0
    assert store.list_ar_rules() == []


def test_list_ar_rules_enabled_only_filter(fresh_store):
    ls, store = fresh_store
    store.persist_ar_rule(_rule("r-on", enabled=True))
    store.persist_ar_rule(_rule("r-off", enabled=False))
    all_rows = store.list_ar_rules()
    assert len(all_rows) == 2
    enabled_rows = store.list_ar_rules(enabled_only=True)
    assert len(enabled_rows) == 1
    assert enabled_rows[0]["id"] == "r-on"


# ── History round-trip ────────────────────────────────────────────────────


def test_log_and_query_ar_history(fresh_store):
    ls, store = fresh_store
    store.persist_ar_rule(_rule("r-001"))
    store.log_ar_history(_entry("h-001", rule_id="r-001", session_id="sess-abc"))
    rows = store.query_ar_history()
    assert len(rows) == 1
    h = rows[0]
    assert h["id"] == "h-001"
    assert h["rule_id"] == "r-001"
    assert h["session_id"] == "sess-abc"
    assert h["action_type"] == "alert_only"


def test_query_ar_history_detail_json_decoded(fresh_store):
    ls, store = fresh_store
    store.persist_ar_rule(_rule())
    store.log_ar_history(_entry(detail_json={"tokens": 50000, "metric": 0.0}))
    rows = store.query_ar_history()
    assert isinstance(rows[0]["detail_json"], dict)
    assert rows[0]["detail_json"]["tokens"] == 50000


def test_query_ar_history_session_filter(fresh_store):
    ls, store = fresh_store
    store.persist_ar_rule(_rule())
    store.log_ar_history(_entry("h-a", session_id="sess-A"))
    store.log_ar_history(_entry("h-b", session_id="sess-B"))
    rows = store.query_ar_history(session_id="sess-A")
    assert len(rows) == 1
    assert rows[0]["id"] == "h-a"


# ── DAEMON_METHODS allowlist ───────────────────────────────────────────────


def test_ar_methods_in_daemon_methods():
    sys.modules.pop("routes.local_query", None)
    import routes.local_query as lq
    importlib.reload(lq)
    expected = {
        "persist_ar_rule",
        "delete_ar_rule",
        "log_ar_history",
        "list_ar_rules",
        "query_ar_history",
    }
    assert expected.issubset(lq._DAEMON_METHODS)
