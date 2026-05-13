"""Tests for epic #964 — local-store fast paths on the Usage tab routes.

Covers the 8 routes engineer-6 migrated under
``CLAWMETRY_LOCAL_STORE_READ=1``:

  * /api/usage
  * /api/usage/anomalies
  * /api/anomalies
  * /api/usage/by-plugin
  * /api/usage/by-plugin/trend
  * /api/usage/cost-comparison
  * /api/model-attribution
  * /api/skill-attribution

Each route gets:
  1. a positive case — env flag set + populated store → response carries
     ``_source: "local_store"`` and the legacy contract shape.
  2. a negative case — env flag UNSET → fast path is skipped entirely
     (response lacks the ``_source`` tag).

Pattern lifted from ``test_brain_local_store.py`` and
``test_heartbeat_local_store.py``.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


# ── shared helpers ─────────────────────────────────────────────────────────

def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _wait_flush(store, t=2.0):
    """Block until the in-memory ring has drained to DuckDB."""
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _seed_events(store, *, n=12, models=None, plugins=None, skills=None,
                  base_cost=0.05, base_tokens=100, sessions=None):
    """Seed N events spread across the last few days. Returns the event list
    so tests can introspect what was written."""
    models = models or ["claude-opus-4", "gpt-4o-mini"]
    plugins = plugins or ["bash", "edit"]
    sessions = sessions or ["sess-a", "sess-b"]
    now = time.time()
    events = []
    for i in range(n):
        sid = sessions[i % len(sessions)]
        plugin = plugins[i % len(plugins)]
        model = models[i % len(models)]
        # Spread events across 0-7 days back so the daily chart has buckets.
        day_offset = i % 7
        ts = _iso(now - (day_offset * 86400) - i)
        data = {"plugin": plugin, "tool": plugin, "input": f"call-{i}"}
        if skills and i < len(skills):
            data["skill"] = skills[i]
        ev = {
            "id":          f"ev-usage-{i}",
            "node_id":     "agent+test",
            "agent_id":    "main",
            "session_id":  sid,
            "event_type":  "tool_call",
            "ts":          ts,
            "data":        data,
            "cost_usd":    base_cost * (i + 1),
            "token_count": base_tokens * (i + 1),
            "model":       model,
        }
        store.ingest(ev)
        events.append(ev)
    _wait_flush(store)
    return events


def _seed_anomaly_session(store):
    """Seed events whose summed per-session cost shows a blow-out spike vs
    the 7-day baseline. ``query_sessions`` aggregates the events table so we
    write events (not session rows) here."""
    now = time.time()
    # Six baseline sessions over the past 7 days at ~$0.10 each (one event
    # per session — keeps the cost simple).
    for i in range(6):
        ts_iso = _iso(now - ((i + 2) * 86400))
        store.ingest({
            "id":          f"ev-baseline-{i}",
            "node_id":     "agent+test",
            "agent_id":    "main",
            "session_id":  f"sess-baseline-{i}",
            "event_type":  "tool_call",
            "ts":          ts_iso,
            "data":        {"plugin": "bash"},
            "cost_usd":    0.10,
            "token_count": 1000,
            "model":       "claude-opus-4",
        })
    # One blow-out within the past 24h at $5 (50× baseline) — trips 2× easily.
    store.ingest({
        "id":          "ev-spike",
        "node_id":     "agent+test",
        "agent_id":    "main",
        "session_id":  "sess-spike",
        "event_type":  "tool_call",
        "ts":          _iso(now - 3600),
        "data":        {"plugin": "bash"},
        "cost_usd":    5.0,
        "token_count": 50000,
        "model":       "claude-opus-4",
    })
    _wait_flush(store)


def _build_app(tmp_path, monkeypatch, *, enable_fast_path: bool):
    """Build an isolated Flask app + populated tmp DuckDB."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    if enable_fast_path:
        monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    else:
        monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.usage as usage_mod
    importlib.reload(usage_mod)

    app = Flask(__name__)
    app.register_blueprint(usage_mod.bp_usage)
    return app, ls, usage_mod


@pytest.fixture
def fast_path_app(tmp_path, monkeypatch):
    app, ls, usage_mod = _build_app(tmp_path, monkeypatch, enable_fast_path=True)
    yield app, ls, usage_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def legacy_path_app(tmp_path, monkeypatch):
    """Env flag UNSET — the fast path must be skipped completely. We still
    populate the store so the legacy path being chosen is provable (the
    response lacks the ``_source: local_store`` tag despite data existing)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")  # for seeding writes

    import clawmetry.local_store as ls
    importlib.reload(ls)

    store = ls.get_store()
    _seed_events(store, n=8, skills=["review", "review", "test"])
    _seed_anomaly_session(store)

    # Now drop the flag so the route handlers must take the legacy path.
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path
    import routes.usage as usage_mod
    importlib.reload(usage_mod)

    app = Flask(__name__)
    app.register_blueprint(usage_mod.bp_usage)
    yield app, ls
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ── /api/usage ─────────────────────────────────────────────────────────────

def test_usage_fast_path_returns_local_store_data(fast_path_app):
    app, ls, _u = fast_path_app
    _seed_events(ls.get_store(), n=10)

    body = app.test_client().get("/api/usage").get_json()
    assert body["_source"] == "local_store"
    # Legacy contract keys.
    for k in ("days", "today", "week", "month", "todayCost", "weekCost",
              "monthCost", "modelBreakdown"):
        assert k in body, f"missing key {k}"
    # 14-day rolling chart.
    assert isinstance(body["days"], list) and len(body["days"]) == 14
    # Some token volume should land within the window.
    assert sum(d["tokens"] for d in body["days"]) > 0
    # Model breakdown lists at least the seeded models.
    seen_models = {m["model"] for m in body["modelBreakdown"]}
    assert "claude-opus-4" in seen_models or "gpt-4o-mini" in seen_models


def test_usage_legacy_when_env_unset(legacy_path_app):
    app, _ls = legacy_path_app
    body = app.test_client().get("/api/usage").get_json()
    assert body.get("_source") != "local_store"


# ── /api/usage/anomalies ───────────────────────────────────────────────────

def test_usage_anomalies_fast_path(fast_path_app):
    app, ls, _u = fast_path_app
    _seed_anomaly_session(ls.get_store())

    body = app.test_client().get("/api/usage/anomalies").get_json()
    assert body["_source"] == "local_store"
    for k in ("anomalies", "baseline_7d_avg_usd", "threshold_multiplier"):
        assert k in body
    assert body["threshold_multiplier"] == 2.0
    # Spike session at $5 vs ~$0.10 baseline → must be flagged.
    sids = {a["session_id"] for a in body["anomalies"]}
    assert "sess-spike" in sids


def test_usage_anomalies_legacy_when_env_unset(legacy_path_app):
    app, _ls = legacy_path_app
    body = app.test_client().get("/api/usage/anomalies").get_json()
    assert body.get("_source") != "local_store"


# ── /api/anomalies ─────────────────────────────────────────────────────────

def test_anomalies_fast_path(fast_path_app):
    app, ls, _u = fast_path_app
    _seed_anomaly_session(ls.get_store())

    body = app.test_client().get("/api/anomalies").get_json()
    assert body["_source"] == "local_store"
    for k in ("anomalies", "active_count", "has_active", "baselines",
              "threshold_cost_multiplier"):
        assert k in body
    # Spike must register as active.
    assert body["has_active"] is True
    assert body["active_count"] >= 1
    # Each anomaly row carries the legacy detector's fields.
    a = body["anomalies"][0]
    for k in ("id", "session_key", "metric", "value", "baseline", "ratio",
              "severity", "detected_at", "acknowledged"):
        assert k in a, f"missing anomaly key {k}"
    assert a["metric"] == "cost_spike"
    assert a["severity"] in {"medium", "high", "critical"}


def test_anomalies_legacy_when_env_unset(legacy_path_app):
    app, _ls = legacy_path_app
    body = app.test_client().get("/api/anomalies").get_json()
    assert body.get("_source") != "local_store"


# ── /api/usage/by-plugin ───────────────────────────────────────────────────

def test_usage_by_plugin_fast_path(fast_path_app):
    app, ls, _u = fast_path_app
    _seed_events(ls.get_store(), n=10, plugins=["bash", "edit", "read"])

    body = app.test_client().get("/api/usage/by-plugin").get_json()
    assert body["_source"] == "local_store"
    assert "plugins" in body and "warnings" in body
    plugin_names = {p["plugin"] for p in body["plugins"]}
    assert {"bash", "edit", "read"}.issubset(plugin_names)
    # Each row carries the legacy contract fields.
    for row in body["plugins"]:
        for k in ("plugin", "total_tokens", "cost_usd", "call_count",
                  "pct_of_total", "trend"):
            assert k in row
    # pct_of_total values sum to ~100.
    total_pct = sum(p["pct_of_total"] for p in body["plugins"])
    assert 99.0 <= total_pct <= 101.0


def test_usage_by_plugin_threshold_warning(fast_path_app):
    """One dominant plugin → threshold warning fires."""
    app, ls, _u = fast_path_app
    # All events under one plugin → 100% share.
    _seed_events(ls.get_store(), n=8, plugins=["bash"])

    body = app.test_client().get("/api/usage/by-plugin?threshold=50").get_json()
    assert body["_source"] == "local_store"
    assert body["warnings"], "expected at least one threshold warning"
    assert body["warnings"][0]["plugin"] == "bash"


def test_usage_by_plugin_legacy_when_env_unset(legacy_path_app):
    app, _ls = legacy_path_app
    body = app.test_client().get("/api/usage/by-plugin").get_json()
    assert body.get("_source") != "local_store"


# ── /api/usage/by-plugin/trend ─────────────────────────────────────────────

def test_usage_by_plugin_trend_fast_path(fast_path_app):
    app, ls, _u = fast_path_app
    _seed_events(ls.get_store(), n=14, plugins=["bash", "edit"])

    body = app.test_client().get("/api/usage/by-plugin/trend?days=14").get_json()
    assert body["_source"] == "local_store"
    assert "days" in body and "plugins" in body
    assert len(body["days"]) == 14
    # Plugins seeded should appear keyed in the trend dict.
    assert "bash" in body["plugins"]
    assert "edit" in body["plugins"]
    # Each plugin's series is one entry per day.
    for series in body["plugins"].values():
        assert len(series) == 14
        for entry in series:
            for k in ("day", "tokens", "cost_usd", "calls"):
                assert k in entry


def test_usage_by_plugin_trend_legacy_when_env_unset(legacy_path_app):
    app, _ls = legacy_path_app
    body = app.test_client().get("/api/usage/by-plugin/trend").get_json()
    assert body.get("_source") != "local_store"


# ── /api/usage/cost-comparison ─────────────────────────────────────────────

def test_cost_comparison_fast_path(fast_path_app):
    app, ls, _u = fast_path_app
    _seed_events(ls.get_store(), n=10)

    body = app.test_client().get("/api/usage/cost-comparison").get_json()
    assert body["_source"] == "local_store"
    for k in ("actual", "alternatives", "period"):
        assert k in body
    assert body["period"] == "30d"
    assert body["actual"]["tokens"] > 0
    assert body["actual"]["cost_usd"] > 0
    # Alternatives sorted ascending by estimated_cost.
    costs = [a["estimated_cost"] for a in body["alternatives"]]
    assert costs == sorted(costs)
    # Each alternative carries the legacy fields.
    for alt in body["alternatives"]:
        for k in ("model_id", "display_name", "provider", "estimated_cost",
                  "savings_usd", "savings_pct"):
            assert k in alt


def test_cost_comparison_legacy_when_env_unset(legacy_path_app):
    app, _ls = legacy_path_app
    body = app.test_client().get("/api/usage/cost-comparison").get_json()
    assert body.get("_source") != "local_store"


# ── /api/model-attribution ─────────────────────────────────────────────────

def test_model_attribution_fast_path(fast_path_app):
    app, ls, _u = fast_path_app
    _seed_events(ls.get_store(), n=10,
                  models=["claude-opus-4", "gpt-4o-mini", "claude-opus-4"])

    body = app.test_client().get("/api/model-attribution").get_json()
    assert body["_source"] == "local_store"
    for k in ("models", "primary_model", "total_turns", "model_count",
              "switches", "switch_count"):
        assert k in body
    seen = {m["model"] for m in body["models"]}
    assert "claude-opus-4" in seen
    assert "gpt-4o-mini" in seen
    # share_pct sums to ~100.
    total = sum(m["share_pct"] for m in body["models"])
    assert 99.0 <= total <= 101.0
    # Each model row has the legacy fields.
    for m in body["models"]:
        for k in ("model", "turns", "sessions", "provider", "share_pct"):
            assert k in m


def test_model_attribution_legacy_when_env_unset(legacy_path_app):
    app, _ls = legacy_path_app
    body = app.test_client().get("/api/model-attribution").get_json()
    assert body.get("_source") != "local_store"


# ── /api/skill-attribution ─────────────────────────────────────────────────

def test_skill_attribution_fast_path(fast_path_app):
    app, ls, _u = fast_path_app
    _seed_events(ls.get_store(), n=8,
                  skills=["review", "review", "test", "test"])

    body = app.test_client().get("/api/skill-attribution").get_json()
    assert body["_source"] == "local_store"
    for k in ("skills", "top5_week", "total_cost", "note", "clawhub"):
        assert k in body
    skill_names = {s["name"] for s in body["skills"]}
    assert {"review", "test"}.issubset(skill_names)
    # Each skill row matches the legacy contract.
    for s in body["skills"]:
        for k in ("name", "invocations", "total_cost_usd", "avg_cost_usd",
                  "last_used", "clawhub_url"):
            assert k in s
        assert s["clawhub_url"].startswith("https://clawhub.dev/skills/")
    assert body["clawhub"] == {"enabled": False, "url": None}


def test_skill_attribution_legacy_when_env_unset(legacy_path_app):
    app, _ls = legacy_path_app
    body = app.test_client().get("/api/skill-attribution").get_json()
    assert body.get("_source") != "local_store"
