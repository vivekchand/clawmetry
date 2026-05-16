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
    # Steer the daemon-proxy discovery away from the real install so the
    # ``_ls_call`` helper falls through to the in-process LocalStore (which
    # is what these tests are actually exercising). Without this, a running
    # ``com.clawmetry.sync`` daemon serves the request from
    # ``~/.clawmetry/clawmetry.duckdb`` instead of our tmp_path store.
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_DISCOVERY_PATH", str(tmp_path / "no-such-discovery.json"))
    lq._invalidate_daemon_cache()

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
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_DISCOVERY_PATH", str(tmp_path / "no-such-discovery.json"))
    lq._invalidate_daemon_cache()

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


# ── /api/usage 24h retention cap (issue #1448 surface 2) ─────────────────
#
# OSS / Cloud-Free callers get clamped to the last 24h of the 14-day chart;
# Cloud-Pro callers (gated by ``dashboard._is_pro_user``) keep the full
# window. Response always carries ``capped_at_24h`` so the UI can render
# the upgrade CTA.


def test_api_usage_caps_14d_to_24h_for_free(fast_path_app, monkeypatch):
    app, ls, _u = fast_path_app
    # Seed events across 7 days; the cap should zero out everything except
    # today + yesterday for non-Pro callers.
    _seed_events(ls.get_store(), n=14, base_tokens=100)

    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)

    body = app.test_client().get("/api/usage").get_json()
    assert body["capped_at_24h"] is True
    # Chart still has 14 slots so the UI shape is unchanged.
    assert isinstance(body["days"], list) and len(body["days"]) == 14
    # Buckets older than today/yesterday must be zeroed.
    older = body["days"][:-2]
    for d in older:
        assert d["tokens"] == 0, f"older bucket {d['date']} leaked tokens"
        assert d["cost"] == 0


def test_api_usage_no_cap_for_pro(fast_path_app, monkeypatch):
    app, ls, _u = fast_path_app
    _seed_events(ls.get_store(), n=14, base_tokens=100)

    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    body = app.test_client().get("/api/usage").get_json()
    assert body["capped_at_24h"] is False
    # Pro callers see the full 14-day window with seeded tokens spread
    # across the whole period (events seeded at day_offset = i % 7).
    assert isinstance(body["days"], list) and len(body["days"]) == 14
    # At least one bucket older than yesterday must carry tokens.
    older = body["days"][:-2]
    assert any(d["tokens"] > 0 for d in older), (
        "pro caller should see historical tokens beyond 24h window"
    )


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


def test_cost_comparison_does_not_double_count_v3_sibling_pairs(fast_path_app):
    """Regression: on real v3 installs every billable turn emits both an
    ``assistant`` row AND a slim ``model.completed`` sibling ~100 ms later.
    The cost-comparison fast path used to sum ``token_count`` across every
    event row, doubling actual tokens + cost on real data and making the
    "savings vs alternative" $ amounts look 2× as good as truth. We now
    skip the slimmer sibling when the assistant exists for the same
    (session_id, ts ±1 s) bucket.
    """
    app, ls, _u = fast_path_app
    store = ls.get_store()
    # One LLM turn within the 30-day window: 100 in + 50 out = 150 tokens.
    # Both writers race-emit so two rows land at the same ts.
    ts_iso = _iso(time.time() - 86400)
    _ingest_v3_assistant(
        store, sid="sess-dup", ts=ts_iso, ev_id="ev-assistant",
        input_tokens=100, output_tokens=50, cache_read=0, cache_write=0,
    )
    _ingest_v3_model_completed(
        store, sid="sess-dup", ts=ts_iso, ev_id="ev-modelcompleted",
        input_tokens=100, output_tokens=50,
    )
    _wait_flush(store)

    body = app.test_client().get("/api/usage/cost-comparison").get_json()
    assert body["_source"] == "local_store"
    # The pair represents ONE LLM turn = 150 tokens. Anything > 150 means
    # the sibling-dedup regressed and we're double-counting again.
    assert body["actual"]["tokens"] == 150, (
        f"cost-comparison double-counted sibling pair: "
        f"got {body['actual']['tokens']}, expected 150 (one deduped turn)"
    )


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


# ── v3 real-shape regression (issue #1394) ────────────────────────────────


def _ingest_v3_assistant(store, *, sid, ts, ev_id,
                          input_tokens, output_tokens,
                          cache_read, cache_write):
    """Insert one ``assistant``-typed event whose ``data.message.usage``
    carries the Anthropic-SDK envelope real OpenClaw v3 + Claude Code
    installs emit. Matches the fixture pulled from
    ``~/.clawmetry/clawmetry.duckdb`` on 2026-05-16 (issue #1394).
    """
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "assistant",
        "ts":         ts,
        "data": {
            "type":    "assistant",
            "version": 3,
            "message": {
                "role":  "assistant",
                "model": "claude-opus-4-7",
                "type":  "message",
                "usage": {
                    "input_tokens":               input_tokens,
                    "output_tokens":              output_tokens,
                    "cache_read_input_tokens":    cache_read,
                    "cache_creation_input_tokens": cache_write,
                },
            },
        },
        "cost_usd":    0.0,
        "token_count": input_tokens + output_tokens,
        "model":       "claude-opus-4-7",
    })


def _ingest_v3_model_completed(store, *, sid, ts, ev_id,
                                input_tokens, output_tokens):
    """Insert one ``model.completed`` sibling event (slim envelope, no
    cache split). The pair (assistant + model.completed) emits ~100 ms
    apart for every LLM turn on a real install — the fast-path must
    dedup them so input/output aren't double-counted.
    """
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "model.completed",
        "ts":         ts,
        "data": {
            "type":     "model.completed",
            "modelId":  "claude-opus-4-7",
            "provider": "claude-cli",
            "promptCache": {
                "lastCallUsage": {
                    "input":  input_tokens,
                    "output": output_tokens,
                    "total":  input_tokens + output_tokens,
                },
            },
        },
        "cost_usd":    0.0,
        "token_count": input_tokens + output_tokens,
        "model":       "claude-opus-4-7",
    })


def test_usage_v3_real_shape_returns_real_splits(fast_path_app):
    """v3 real-shape regression (#1394): /api/usage was returning
    ``inputTokens=0 outputTokens=0 cacheReadTokens=0 cacheWriteTokens=0``
    on real OpenClaw v3 + Claude Code installs because the fast-path
    derived the chart from ``query_aggregates`` only (which sums
    ``token_count``) and stamped 0 into every split. Real installs
    emit the splits on ``assistant``-typed events, not the legacy
    synthetic ``message`` shape.

    Three turns @ ``input=6, output=7, cacheRead=28k, cacheWrite=70``
    each — the same shape the accuracy harness drove on a live box
    when filing this bug.
    """
    app, ls, _u = fast_path_app
    store = ls.get_store()

    today = datetime.now().strftime("%Y-%m-%d")
    base = f"{today}T10:00"

    # Three turns, each emitting BOTH an assistant + model.completed
    # event ~150 ms apart (matches the gateway-vs-Claude-Code emit race).
    for i, (sec_a, sec_mc) in enumerate([("00", "00"), ("04", "04"), ("08", "08")]):
        _ingest_v3_assistant(
            store,
            sid="sess-v3-real",
            ts=f"{base}:{sec_a}.100Z",
            ev_id=f"v3-asst-{i}",
            input_tokens=6, output_tokens=7,
            cache_read=28_500 + i, cache_write=70 + i,
        )
        _ingest_v3_model_completed(
            store,
            sid="sess-v3-real",
            ts=f"{base}:{sec_mc}.250Z",  # ~150ms later
            ev_id=f"v3-mc-{i}",
            input_tokens=6, output_tokens=7,
        )
    _wait_flush(store)

    body = app.test_client().get("/api/usage").get_json()
    assert body["_source"] == "local_store"

    today_bucket = next(d for d in body["days"] if d["date"] == today)

    # Splits must reflect the assistant envelope (sums of 3 turns).
    # input/output are 6+6+6=18 / 7+7+7=21 — DOUBLED if dedup fails.
    assert today_bucket["inputTokens"] == 18, (
        f"input drift: got {today_bucket['inputTokens']} (likely sibling "
        f"event double-count if 36)"
    )
    assert today_bucket["outputTokens"] == 21, (
        f"output drift: got {today_bucket['outputTokens']}"
    )
    # Cache splits come ONLY from the assistant envelope (the slim
    # model.completed sibling has no cache_read/cache_write keys),
    # so they should NOT double — but they also can't drop to 0.
    assert today_bucket["cacheReadTokens"] == 28_500 + 28_501 + 28_502, (
        f"cache_read drift: got {today_bucket['cacheReadTokens']}"
    )
    assert today_bucket["cacheWriteTokens"] == 70 + 71 + 72, (
        f"cache_write drift: got {today_bucket['cacheWriteTokens']}"
    )

    # Top-line ``today`` scalar should be input+output (39), not the
    # raw column sum that would inflate to 78 (= 39 × 2 sibling events).
    assert body["today"] == 39, (
        f"today scalar drift: got {body['today']} (likely 78 if dedup failed)"
    )


def test_usage_v3_today_week_month_match_when_only_today(fast_path_app):
    """Issue #1394 — when ALL ingested data falls in ``today``, the
    today/week/month scalars must agree (no silent zero in the wider
    windows). The accuracy harness asserts this directly: same
    ``input/output/cache_read/cache_write/total`` across all four windows
    when no older data exists.
    """
    app, ls, _u = fast_path_app
    store = ls.get_store()

    today = datetime.now().strftime("%Y-%m-%d")

    _ingest_v3_assistant(
        store, sid="sess-window-test",
        ts=f"{today}T11:30:00.100Z", ev_id="v3-w-asst",
        input_tokens=6, output_tokens=7, cache_read=28_500, cache_write=70,
    )
    _ingest_v3_model_completed(
        store, sid="sess-window-test",
        ts=f"{today}T11:30:00.250Z", ev_id="v3-w-mc",
        input_tokens=6, output_tokens=7,
    )
    _wait_flush(store)

    body = app.test_client().get("/api/usage").get_json()
    today_bucket = next(d for d in body["days"] if d["date"] == today)

    # The day bucket is the canonical source — assert today/week/month
    # all derive from it (week/month start ≤ today, so they sum to
    # the same value when only today has data).
    assert today_bucket["inputTokens"] == 6
    assert today_bucket["outputTokens"] == 7
    assert today_bucket["cacheReadTokens"] == 28_500
    assert today_bucket["cacheWriteTokens"] == 70

    # Top-line scalars derive from the same day_bucket sum (today only).
    assert body["today"] == 13  # 6 + 7 (deduped)
    # week/month aren't returned as splits in the response — the harness
    # sums days[] for each window. We mirror that here so the assertion
    # protects the same surface.
    today_iso = today
    week_start = today_iso  # only one day of data → week start ≤ today
    month_start = today_iso[:8] + "01"

    def _sum_field(field, since):
        return sum(d.get(field, 0) for d in body["days"] if d["date"] >= since)

    for since in (today_iso, week_start, month_start, "0000-00-00"):
        assert _sum_field("inputTokens", since) == 6, f"input drift at since={since}"
        assert _sum_field("outputTokens", since) == 7, f"output drift at since={since}"
        assert _sum_field("cacheReadTokens", since) == 28_500, f"cache_read drift at since={since}"
        assert _sum_field("cacheWriteTokens", since) == 70, f"cache_write drift at since={since}"
        assert _sum_field("tokens", since) == 13, f"total drift at since={since}"


def test_usage_v3_subagent_assistant_event(fast_path_app):
    """Subagent (Task tool) emits ``subagent:assistant`` events with the
    same Anthropic envelope as the parent ``assistant`` event. They
    represent real LLM spend the user pays for, so the splits MUST
    count them. (Different from the model-fallback route, which
    deliberately excludes them — see #1385.)
    """
    app, ls, _u = fast_path_app
    store = ls.get_store()

    today = datetime.now().strftime("%Y-%m-%d")

    # Parent assistant turn.
    _ingest_v3_assistant(
        store, sid="sess-with-subagent",
        ts=f"{today}T12:00:00.100Z", ev_id="v3-parent",
        input_tokens=6, output_tokens=7, cache_read=28_500, cache_write=70,
    )

    # Sub-agent assistant turn (same shape — overrides event_type).
    store.ingest({
        "id":         "v3-sub",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": "sess-with-subagent",
        "event_type": "subagent:assistant",
        "ts":         f"{today}T12:00:30.100Z",
        "data": {
            "type":    "subagent:assistant",
            "version": 3,
            "message": {
                "role":  "assistant",
                "model": "claude-haiku-4-7",
                "type":  "message",
                "usage": {
                    "input_tokens":               4,
                    "output_tokens":              5,
                    "cache_read_input_tokens":    1_000,
                    "cache_creation_input_tokens": 10,
                },
            },
        },
        "cost_usd":    0.0,
        "token_count": 9,
        "model":       "claude-haiku-4-7",
    })
    _wait_flush(store)

    body = app.test_client().get("/api/usage").get_json()
    today_bucket = next(d for d in body["days"] if d["date"] == today)

    # Both turns counted: 6+4=10, 7+5=12, 28500+1000=29500, 70+10=80.
    assert today_bucket["inputTokens"] == 10
    assert today_bucket["outputTokens"] == 12
    assert today_bucket["cacheReadTokens"] == 29_500
    assert today_bucket["cacheWriteTokens"] == 80


# ── Unit: query_daily_usage_splits + helpers ───────────────────────────────


def test_extract_usage_splits_v3_assistant_shape():
    """v3 ``assistant`` event carries the Anthropic-SDK envelope. All four
    splits should round-trip from ``data.message.usage``."""
    from clawmetry.local_store import _extract_usage_splits

    data = {
        "message": {
            "role": "assistant",
            "usage": {
                "input_tokens":               6,
                "output_tokens":              7,
                "cache_read_input_tokens":    28_668,
                "cache_creation_input_tokens": 71,
            },
        },
    }
    assert _extract_usage_splits(data) == {
        "input_tokens": 6, "output_tokens": 7,
        "cache_read_tokens": 28_668, "cache_write_tokens": 71,
    }


def test_extract_usage_splits_v3_model_completed_shape():
    """v3 ``model.completed`` carries only ``promptCache.lastCallUsage``
    with input/output/total — no cache split. Cache buckets must
    fall through to 0 (caller pairs this row with the richer
    ``assistant`` sibling for the splits)."""
    from clawmetry.local_store import _extract_usage_splits

    data = {
        "type":      "model.completed",
        "modelId":   "claude-opus-4-7",
        "promptCache": {
            "lastCallUsage": {"input": 6, "output": 7, "total": 13},
        },
    }
    assert _extract_usage_splits(data) == {
        "input_tokens": 6, "output_tokens": 7,
        "cache_read_tokens": 0, "cache_write_tokens": 0,
    }


def test_extract_usage_splits_openclaw_native_shape():
    """OpenClaw native v3 ``message`` event uses camelCase
    ``usage.cacheRead`` / ``cacheWrite`` (no ``_input_tokens`` suffix)."""
    from clawmetry.local_store import _extract_usage_splits

    data = {
        "message": {
            "role": "assistant",
            "usage": {
                "input":      6,
                "output":     7,
                "cacheRead":  28_312,
                "cacheWrite": 72,
            },
        },
    }
    assert _extract_usage_splits(data) == {
        "input_tokens": 6, "output_tokens": 7,
        "cache_read_tokens": 28_312, "cache_write_tokens": 72,
    }


def test_extract_usage_splits_returns_zero_dict_on_empty():
    """No usage anywhere → all-zero dict (caller treats as "skip row")."""
    from clawmetry.local_store import _extract_usage_splits

    assert _extract_usage_splits({}) == {
        "input_tokens": 0, "output_tokens": 0,
        "cache_read_tokens": 0, "cache_write_tokens": 0,
    }
    assert _extract_usage_splits(None) == {  # type: ignore[arg-type]
        "input_tokens": 0, "output_tokens": 0,
        "cache_read_tokens": 0, "cache_write_tokens": 0,
    }


def test_query_daily_usage_splits_dedups_sibling_events(fast_path_app):
    """assistant + model.completed emitted ~150 ms apart for the SAME
    LLM turn must collapse to one billable count. Without dedup,
    input/output would double; cache splits would stay correct
    (only assistant carries them) but the TOTAL row count would
    lie."""
    _app, ls, _u = fast_path_app
    store = ls.get_store()

    today = datetime.now().strftime("%Y-%m-%d")
    _ingest_v3_assistant(
        store, sid="sess-dedup",
        ts=f"{today}T10:00:00.100Z", ev_id="dedup-asst",
        input_tokens=6, output_tokens=7, cache_read=28_500, cache_write=70,
    )
    _ingest_v3_model_completed(
        store, sid="sess-dedup",
        ts=f"{today}T10:00:00.250Z", ev_id="dedup-mc",
        input_tokens=6, output_tokens=7,
    )
    _wait_flush(store)

    rows = store.query_daily_usage_splits()
    assert len(rows) == 1
    assert rows[0]["day"] == today
    assert rows[0]["input_tokens"] == 6
    assert rows[0]["output_tokens"] == 7
    assert rows[0]["cache_read_tokens"] == 28_500
    assert rows[0]["cache_write_tokens"] == 70
    assert rows[0]["event_count"] == 1


def test_query_daily_usage_splits_keeps_distinct_turns(fast_path_app):
    """Two turns ≥ 4 s apart in the same session are NOT siblings — the
    dedup window (±1 s) must not collapse them."""
    _app, ls, _u = fast_path_app
    store = ls.get_store()

    today = datetime.now().strftime("%Y-%m-%d")
    _ingest_v3_assistant(
        store, sid="sess-distinct",
        ts=f"{today}T10:00:00.100Z", ev_id="t1",
        input_tokens=6, output_tokens=7, cache_read=28_500, cache_write=70,
    )
    _ingest_v3_assistant(
        store, sid="sess-distinct",
        ts=f"{today}T10:00:04.500Z", ev_id="t2",  # 4.4 s later
        input_tokens=6, output_tokens=7, cache_read=28_600, cache_write=71,
    )
    _wait_flush(store)

    rows = store.query_daily_usage_splits()
    assert rows[0]["input_tokens"] == 12  # 6 + 6
    assert rows[0]["output_tokens"] == 14  # 7 + 7
    assert rows[0]["cache_read_tokens"] == 57_100  # 28_500 + 28_600
    assert rows[0]["event_count"] == 2


def test_query_daily_usage_splits_skips_zero_usage_rows(fast_path_app):
    """Events without recoverable usage (queue-operation, session.started,
    etc.) must not bloat ``event_count``. Only counts rows we actually
    bucketed."""
    _app, ls, _u = fast_path_app
    store = ls.get_store()

    today = datetime.now().strftime("%Y-%m-%d")
    # One real assistant event.
    _ingest_v3_assistant(
        store, sid="sess-skip",
        ts=f"{today}T10:00:00.100Z", ev_id="real",
        input_tokens=6, output_tokens=7, cache_read=28_500, cache_write=70,
    )
    # One assistant event with empty usage — should be skipped.
    store.ingest({
        "id":         "empty",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": "sess-skip",
        "event_type": "assistant",
        "ts":         f"{today}T10:00:30.000Z",
        "data":       {"message": {"role": "assistant"}},
        "model":      "claude-opus-4-7",
    })
    _wait_flush(store)

    rows = store.query_daily_usage_splits()
    assert rows[0]["event_count"] == 1


# ── issue #1451: sibling-dedupe across remaining surfaces ─────────────────


def _ingest_v3_pair(store, *, sid, ts_iso, plugin="bash", tokens=150):
    """Seed one v3 assistant + model.completed sibling pair. Both rows
    carry ``token_count=tokens`` — a blind sum returns 2×, a deduped sum
    returns ``tokens``. Used by all #1451 regression tests."""
    base = {
        "node_id": "agent+test", "agent_id": "main", "session_id": sid,
        "cost_usd": 0.0, "token_count": tokens, "model": "claude-opus-4-7",
    }
    store.ingest({**base, "id": f"asst-{sid}", "event_type": "assistant",
                  "ts": ts_iso,
                  "data": {"plugin": plugin, "message": {"role": "assistant"}}})
    store.ingest({**base, "id": f"mc-{sid}", "event_type": "model.completed",
                  "ts": ts_iso, "data": {"plugin": plugin}})


def test_by_plugin_does_not_double_count_v3_sibling_pairs(fast_path_app):
    """Regression: /api/usage/by-plugin summed ``token_count`` per plugin
    without skipping the slim ``model.completed`` sibling — every turn was
    counted twice. Shared dedupe helper (issue #1451) must collapse to 1×."""
    app, ls, _u = fast_path_app
    _ingest_v3_pair(ls.get_store(), sid="sess-plug-dup",
                     ts_iso=_iso(time.time() - 3600))
    _wait_flush(ls.get_store())

    body = app.test_client().get("/api/usage/by-plugin").get_json()
    assert body["_source"] == "local_store"
    bash_row = next((r for r in body["plugins"] if r["plugin"] == "bash"), None)
    assert bash_row is not None, "expected bash plugin row"
    assert bash_row["total_tokens"] == 150, (
        f"by-plugin double-counted sibling pair: got "
        f"{bash_row['total_tokens']}, expected 150"
    )


def test_by_plugin_trend_does_not_double_count_v3_sibling_pairs(fast_path_app):
    """Same regression as the by-plugin scalar route but for the daily
    bucket aggregator at /api/usage/by-plugin/trend."""
    app, ls, _u = fast_path_app
    today = datetime.now().strftime("%Y-%m-%d")
    _ingest_v3_pair(ls.get_store(), sid="sess-trend-dup",
                     ts_iso=f"{today}T10:00:00.100Z")
    _wait_flush(ls.get_store())

    body = app.test_client().get("/api/usage/by-plugin/trend?days=14").get_json()
    assert body["_source"] == "local_store"
    today_entry = next((e for e in (body["plugins"].get("bash") or [])
                         if e["day"] == today), None)
    assert today_entry is not None, "expected today entry in bash trend"
    assert today_entry["tokens"] == 150, (
        f"by-plugin/trend double-counted sibling pair: got "
        f"{today_entry['tokens']}, expected 150"
    )


def test_sessions_clusters_does_not_double_count_v3_sibling_pairs(fast_path_app):
    """Regression: the session aggregator at routes/usage.py:1372 read
    ``token_count`` from ``query_sessions`` (which returns ``SUM`` over
    events) and never deduped — every session's tokens were 2× on v3.
    Shared dedupe helper must collapse to 1×."""
    app, ls, _u = fast_path_app
    _ingest_v3_pair(ls.get_store(), sid="sess-clust-dup",
                     ts_iso=_iso(time.time() - 3600))
    _wait_flush(ls.get_store())

    body = app.test_client().get("/api/sessions/clusters?days=30").get_json()
    total = sum(c.get("total_tokens", 0) for c in body.get("clusters", []))
    assert total == 150, (
        f"sessions/clusters double-counted sibling pair: got {total}, "
        f"expected 150"
    )
