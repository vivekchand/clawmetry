"""Tests for issue #1404 — alerts evaluator reads DuckDB when OTLP is empty.

Background
----------
The OSS alerts evaluator path (``dashboard._get_budget_status``) historically
summed only the in-process ``metrics_store["cost"]`` ring buffer, which is
fed exclusively by the optional OTLP exporter. On the typical OSS install —
``pip install clawmetry`` with no ``[otel]`` extra — that buffer is empty
forever and ``daily_spent`` is permanently 0, so threshold rules like
"alert when daily spend > $5" silently NEVER fire on real spend.

This regression test asserts the DuckDB fallback added in PR #1404 actually
computes ``daily_spent`` from the ``events`` table — using the real
v3 ``model.completed`` envelope shape (the dominant shape on real OpenClaw
installs) — when no OTLP cost rows are present.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Fresh DuckDB ``LocalStore`` against a tmp file."""
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
    """Reload dashboard.py so ``_duckdb_cost_since`` resolves to the fresh
    local_store. Also drop the in-process cost buffer to simulate a
    no-OTLP install (the common OSS case)."""
    sys.modules.pop("dashboard", None)
    import dashboard as _d
    _d.FLEET_DB_PATH = str(tmp_path / "fleet.db")
    with _d._metrics_lock:
        _d.metrics_store["cost"].clear()
    _d._otel_last_received = 0  # belt-and-braces: no OTLP traffic ever seen
    try:
        _d._budget_init_db()
    except Exception:
        pass
    yield _d


# ── Helpers ───────────────────────────────────────────────────────────────────


def _model_completed_event(*, cost_usd_total: float, ts: str | None = None,
                            sid: str | None = None) -> dict:
    """Build a real-shape ``model.completed`` event (the dominant envelope on
    OpenClaw v3 installs). Carries both the ``cost_usd`` column the sync
    daemon populates AND a ``data.promptCache.lastCallUsage`` block — the
    same shape ``query_aggregates`` walks on the fast path."""
    return {
        "id":         f"evt-{uuid.uuid4().hex[:12]}",
        "node_id":    "test-node-1404",
        "agent_id":   "main",
        "session_id": sid or "session-1404",
        "event_type": "model.completed",
        "ts":         ts or datetime.now(timezone.utc).isoformat(),
        "cost_usd":   float(cost_usd_total),
        "data":       {
            "promptCache": {
                "lastCallUsage": {
                    "input":  1000,
                    "output": 200,
                    "cost":   {"total": float(cost_usd_total)},
                },
            },
        },
    }


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_otel_cost_is_fresh_false_when_buffer_empty(dashboard_module):
    """No OTLP entries ⇒ ``_otel_cost_is_fresh`` must return False so the
    DuckDB fallback path activates."""
    _d = dashboard_module
    today_start = (
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    )
    assert _d._otel_cost_is_fresh(today_start) is False


def test_otel_cost_is_fresh_true_when_recent_entry(dashboard_module):
    """A cost entry within the 5-min window ⇒ OTLP is considered fresh and
    the DuckDB fallback should NOT run (avoid double-counting)."""
    _d = dashboard_module
    today_start = (
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    )
    with _d._metrics_lock:
        _d.metrics_store["cost"].append({
            "timestamp": time.time(),  # now ⇒ inside fresh window
            "usd": 1.23,
            "model": "test-model",
        })
    assert _d._otel_cost_is_fresh(today_start) is True


def test_evaluator_sums_cost_from_duckdb_when_otlp_empty(
    fresh_store, dashboard_module,
):
    """The headline regression for issue #1404.

    Setup: three real-shape ``model.completed`` events totalling $4.00 of
    spend, no OTLP rows in ``metrics_store['cost']`` (i.e. simulate the
    ~99% of OSS installs without an OTLP exporter wired).

    Expected: ``_get_budget_status()`` returns ``daily_spent ≈ 4.00`` and
    flags ``cost_source == "duckdb"``, proving the evaluator can finally
    see real spend and a threshold rule like "alert when spend > $3" can
    fire.

    Before this fix, ``daily_spent`` was 0.0 and no rule could ever fire.
    """
    ls, store = fresh_store
    _d = dashboard_module

    # Three turns, all dated today (UTC). The sync daemon would write rows
    # like this for every real OpenClaw turn.
    today = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0,
                                                microsecond=0)
    events = [
        _model_completed_event(cost_usd_total=1.50,
                                ts=today.replace(hour=9).isoformat()),
        _model_completed_event(cost_usd_total=1.25,
                                ts=today.replace(hour=10).isoformat()),
        _model_completed_event(cost_usd_total=1.25,
                                ts=today.replace(hour=11).isoformat()),
    ]
    for ev in events:
        store.ingest(ev)
    # CLAWMETRY_LOCAL_FLUSH_BATCH=1 flushes per ingest; belt-and-braces:
    store._flush_now()

    # Sanity: store really has these rows. If query_aggregates returns
    # nothing we want a clear failure right here, not a misleading one in
    # the evaluator assertion below.
    today_iso = today.replace(hour=0).isoformat()
    rows = store.query_aggregates(since=today_iso)
    assert any(float(r.get("cost_usd") or 0) > 0 for r in rows), \
        f"DuckDB query_aggregates returned no cost rows; got {rows}"

    # OTLP buffer is empty (confirmed by the fixture). Now run the
    # evaluator path the alerts loop uses.
    status = _d._get_budget_status()

    expected_total = 1.50 + 1.25 + 1.25
    assert status["cost_source"] == "duckdb", (
        f"expected DuckDB fallback when OTLP buffer empty, got "
        f"cost_source={status.get('cost_source')!r}"
    )
    assert abs(status["daily_spent"] - expected_total) <= 0.01, (
        f"daily_spent={status['daily_spent']} should match ground truth "
        f"{expected_total} (±$0.01 for float rounding). status={status}"
    )
    # Weekly/monthly windows include today, so they must be >= daily.
    assert status["weekly_spent"] >= status["daily_spent"] - 0.001
    assert status["monthly_spent"] >= status["daily_spent"] - 0.001


def test_evaluator_prefers_otlp_when_fresh(fresh_store, dashboard_module):
    """When BOTH paths have data, the in-memory OTLP buffer wins (cheaper,
    already aggregated, no DB round-trip). Verifies we don't double-count
    spend on OTLP-fed installs after the fallback was added."""
    ls, store = fresh_store
    _d = dashboard_module

    # OTLP says $7.50.
    with _d._metrics_lock:
        _d.metrics_store["cost"].append({
            "timestamp": time.time(),
            "usd": 7.50,
            "model": "test-model",
        })
    # DuckDB has totally different number — if we double-counted we'd see
    # $7.50 + $99 = $106.50 in the assertion.
    store.ingest(_model_completed_event(cost_usd_total=99.00))
    store._flush_now()

    status = _d._get_budget_status()
    assert status["cost_source"] == "otlp", (
        f"OTLP should win when buffer is fresh; got {status['cost_source']!r}"
    )
    assert abs(status["daily_spent"] - 7.50) <= 0.01, status


def test_evaluator_empty_store_returns_zero(dashboard_module):
    """Brand-new install: no OTLP, no DuckDB events. Evaluator must return
    ``daily_spent = 0`` without crashing — graceful fallback per CLAUDE.md."""
    _d = dashboard_module
    status = _d._get_budget_status()
    assert status["daily_spent"] == 0.0
    # cost_source stays "otlp" since we never switched (no DuckDB rows).
    assert status["cost_source"] == "otlp"
