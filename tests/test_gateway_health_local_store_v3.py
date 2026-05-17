"""Regression guard for /api/gateway-health DuckDB fast path (Tier-1 #1565).

``routes/health.py:_try_local_store_gateway_health`` reads the most-recent
``gateway.metric`` event the sync daemon has already captured to DuckDB
(see ``clawmetry/sync.py::capture_gateway_metric`` — runs every 30s when
the daemon is up) instead of re-running the psutil/ps live probe on every
poll.

Why this matters:

* External monitors poll ``/api/gateway-health`` at sub-minute cadence;
  the live ``ps``/``psutil`` shell-out is the dominant per-request cost.
* On multi-node fleets, the dashboard process may not see the gateway
  PID at all (different container/namespace) and ``compute_gateway_health``
  returns a misleading ``not_running`` even when DuckDB has fresh samples
  written by the sibling daemon on the host where the gateway lives.

This file seeds DuckDB ``gateway.metric`` events via ``LocalStore.ingest``
(the same write path the sync daemon uses) and asserts:

1. Populated path — recent ``gateway.metric`` event → fast path returns
   ``_source='local_store'`` and surfaces pid/rss/cpu/uptime from the
   sample plus the standard ``memory_threshold_mb`` field.
2. Status re-classification — rss_mb beyond the warning/critical
   thresholds is mapped through ``_classify_gateway_status`` (DuckDB
   only stores raw vitals, NOT the classification).
3. Freshness gate — a sample older than the 10-minute freshness window
   is treated as "DuckDB has nothing recent" and the helper returns
   ``None`` so the caller defers to the live psutil/ps probe (a
   30-minute-old sample tagged ``healthy`` would actively mislead an
   operator triaging an outage).
4. Empty events table → helper returns ``None`` (NOT a populated zero
   shell) so the route falls back to the live probe which can still
   correctly report ``not_running`` from the missing PID file.
5. Env gate honoured — with ``CLAWMETRY_LOCAL_STORE_READ=0`` the route
   handler MUST NOT take the fast path even if a fresh DuckDB sample
   exists.
"""

from __future__ import annotations

import importlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


def _now_iso():
    return datetime.now(tz=timezone.utc).isoformat()


def _iso_minutes_ago(minutes: int) -> str:
    return (
        datetime.now(tz=timezone.utc) - timedelta(minutes=minutes)
    ).isoformat()


def _ingest_gateway_metric(
    store,
    *,
    pid: int = 4321,
    rss_mb: float = 320.0,
    cpu_pct: float = 1.4,
    uptime_seconds: int = 7200,
    ts: str | None = None,
):
    """Helper: ingest one ``gateway.metric`` event in the shape
    ``clawmetry/sync.py::capture_gateway_metric`` writes."""
    store.ingest({
        "id":         f"gm-{uuid.uuid4().hex[:12]}",
        "node_id":    "node-test",
        "agent_type": "openclaw",
        "agent_id":   "openclaw-gateway",
        "event_type": "gateway.metric",
        "ts":         ts or _now_iso(),
        "data": {
            "rss_mb":         rss_mb,
            "cpu_pct":        cpu_pct,
            "pid":            pid,
            "uptime_seconds": uptime_seconds,
        },
    })


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.health as health_mod
    importlib.reload(health_mod)

    # Isolate from a contributor's running daemon: without this, ``_ls_call``
    # proxies through ``~/.clawmetry/local_query.json`` and the daemon
    # queries its OWN production DuckDB instead of our tmp_path fixture.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    import dashboard  # noqa: F401

    a = Flask(__name__)
    a.register_blueprint(health_mod.bp_health)
    yield a, ls, health_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_gateway_health_local_store_tags_source_and_returns_vitals(app):
    """Recent ``gateway.metric`` event → fast path returns
    ``_source='local_store'`` with pid/rss/cpu/uptime drawn from the
    DuckDB sample plus the standard ``memory_threshold_mb`` field."""
    a, ls, _h = app
    store = ls.get_store()
    _ingest_gateway_metric(
        store,
        pid=9876,
        rss_mb=384.5,
        cpu_pct=2.1,
        uptime_seconds=12345,
    )
    store.flush()
    assert len(store.query_events(event_type="gateway.metric", limit=5)) == 1

    r = a.test_client().get("/api/gateway-health")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"_source must be local_store; got {body.get('_source')!r}"
    )
    assert body.get("pid") == 9876
    assert body.get("rss_mb") == pytest.approx(384.5)
    assert body.get("cpu_pct") == pytest.approx(2.1)
    assert body.get("uptime_seconds") == 12345
    # 384.5 MB < 75% of 900 → healthy ladder rung.
    assert body.get("status") == "healthy"
    # The threshold MUST be echoed back so dashboard UI can render the
    # gauge against the canonical OpenClaw OOM cliff.
    assert body.get("memory_threshold_mb") == 900
    # Sample timestamp must be surfaced so operators can tell how stale
    # the reading is.
    assert body.get("sample_ts"), "sample_ts must be present on the fast path"


def test_gateway_health_local_store_reclassifies_status_from_rss(app):
    """DuckDB only stores raw vitals; the fast path MUST re-derive the
    warning/critical status badge so the UI shows the same threshold
    ladder the legacy path uses (not just the raw bytes)."""
    a, ls, _h = app
    store = ls.get_store()
    # 950 MB sits above the 900 MB hard cap → critical rung.
    _ingest_gateway_metric(store, rss_mb=950.0, pid=1111)
    store.flush()

    r = a.test_client().get("/api/gateway-health")
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["status"] == "critical", (
        f"rss_mb=950 must classify as critical (>900 MB cap); got {body['status']!r}"
    )


def test_gateway_health_local_store_freshness_gate_defers_old_samples(app):
    """A sample older than the 10-minute freshness window MUST be ignored
    and the helper returns ``None`` so the route defers to the live
    psutil/ps probe. Otherwise a daemon that died 30 min ago would keep
    reporting ``healthy`` to operators triaging an outage."""
    a, ls, health_mod = app
    store = ls.get_store()
    # 25 min ago — comfortably past the 10-min freshness gate.
    _ingest_gateway_metric(store, ts=_iso_minutes_ago(25))
    store.flush()
    # Sanity: the row is in DuckDB; only the freshness gate should hide it.
    assert len(store.query_events(event_type="gateway.metric", limit=5)) == 1

    fast = health_mod._try_local_store_gateway_health()
    assert fast is None, (
        "stale gateway.metric sample must NOT serve the fast path; "
        "operator needs the live probe to flag the outage"
    )


def test_gateway_health_local_store_empty_returns_none(app):
    """Empty events table → helper returns ``None`` so the route falls
    back to ``compute_gateway_health()``. Unlike rate-limits (where an
    empty zero-shell is meaningful), gateway-health's empty answer
    requires the live psutil probe — DuckDB silence doesn't prove the
    gateway is down, it just proves the daemon hasn't written yet."""
    a, ls, health_mod = app
    assert ls.get_store().query_events(event_type="gateway.metric", limit=5) == []
    fast = health_mod._try_local_store_gateway_health()
    assert fast is None, (
        "no gateway.metric rows → helper must defer; legacy probe is the "
        "only source of ground truth here"
    )


def test_gateway_health_env_gate_off_bypasses_fast_path(tmp_path, monkeypatch):
    """With ``CLAWMETRY_LOCAL_STORE_READ=0`` the route MUST NOT call the
    fast path even when a fresh DuckDB sample exists. Guards against
    accidental default-ON regressions
    (feedback_local_store_default_off_killed_moat.md, inverse: opt-OUT
    must work too)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.health as health_mod
    importlib.reload(health_mod)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    store = ls.get_store()
    _ingest_gateway_metric(store, pid=2222, rss_mb=300.0)
    store.flush()

    import dashboard  # noqa: F401
    a = Flask(__name__)
    a.register_blueprint(health_mod.bp_health)

    # Force the legacy path to report a deterministic "not_running" so
    # the assertion below doesn't accidentally hit a real local gateway
    # on a contributor's box.
    import routes.health as _rh
    monkeypatch.setattr(
        _rh, "compute_gateway_health",
        lambda *a, **kw: {
            "pid": None, "uptime_seconds": None, "rss_mb": None,
            "cpu_pct": None, "status": "not_running",
            "memory_threshold_mb": 900,
        },
    )

    r = a.test_client().get("/api/gateway-health")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") is None, (
        "env-gate OFF must NOT take the local_store fast path; got "
        f"_source={body.get('_source')!r}"
    )
    # The legacy stub above returned not_running → confirm we received it.
    assert body.get("status") == "not_running"
    assert body.get("pid") is None
