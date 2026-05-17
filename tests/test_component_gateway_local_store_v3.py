"""Synthetic safety net for /api/component/gateway DuckDB fast path.

Tier-1 surface #15 in the 2026-05-17 DuckDB coverage audit (issue #1565).
``_try_local_store_component_gateway`` sources the routing-event list +
the four ``today_*`` counters (messages / heartbeats / crons / errors)
from the daemon-ingested ``events`` table instead of re-parsing today's
``gateway.log``.

What this file pins:

  1. Empty store → helper returns None → caller falls through to the
     legacy log-tail parser. Critical for fresh installs.
  2. Real v3 event names (``prompt.submitted`` / ``model.completed``)
     hydrate the routing list AND bump ``today_messages``. Synthetic
     tests on 2026-05-15 missed this exact class of bug — see
     ``feedback_synthetic_tests_missed_real_event_shape.md``.
  3. Multi-channel rows propagate the channel hint into ``route.from``
     so the Flow-panel "gateway" column lights up per provider.
  4. Error rows bump ``today_errors`` AND tag ``route.status=error``.
  5. ``CLAWMETRY_LOCAL_STORE_READ=0`` skips the fast path entirely.
"""

from __future__ import annotations

import importlib
import json
import time
from datetime import datetime

import pytest
from flask import Flask


def _today_iso(suffix: str) -> str:
    return f"{datetime.now().strftime('%Y-%m-%d')}T{suffix}"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import routes.components as components_mod
    importlib.reload(components_mod)

    # Issue #1538 pattern: isolate fixture from a developer's locally-
    # running clawmetry daemon (otherwise ``_ls_call`` proxies through
    # ``~/.clawmetry/local_query.json`` and queries the daemon's production
    # DuckDB instead of our tmp_path fixture — seeded rows would be
    # invisible to the fast path).
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(components_mod.bp_components)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def gated_off_app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import routes.components as components_mod
    importlib.reload(components_mod)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(components_mod.bp_components)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _drain(store):
    store._flush_now()
    for _ in range(10):
        if not store._ring:
            break
        time.sleep(0.05)


def _row(event_id, sid, event_type, ts, data, **extra):
    base = {
        "id":           event_id,
        "node_id":      "node-test",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": None,
        "event_type":   event_type,
        "ts":           ts,
        "data":         json.dumps(data),
    }
    base.update(extra)
    return base


# ── empty-store: defer to legacy log parser ────────────────────────────────

def test_empty_store_defers_to_legacy_parser(app):
    """No DuckDB rows → helper returns None → legacy log-tail parser
    fires. The response carries NO ``_source`` tag (so the audit can
    confirm the gate fired but had no data to serve)."""
    a, _ls = app
    r = a.test_client().get("/api/component/gateway")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    # Legacy path returns {"routes": [], "stats": {...}, "total": 0} when
    # gateway.log isn't present — confirm the fast path didn't tag.
    assert body.get("_source") != "local_store", (
        f"empty store should defer, got: {body!r}"
    )


# ── happy path: v3 event names hydrate the panel ─────────────────────────

def test_v3_events_hydrate_routes_and_stats(app):
    """Real OpenClaw v3 event names (``prompt.submitted`` /
    ``model.completed``) must populate routes[] AND bump
    today_messages. Synthetic-test regression class from 2026-05-15."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-gw-v3"

    store.ingest(_row(
        "e1", sid, "prompt.submitted", _today_iso("10:00:01Z"),
        {"_v3_type": "message", "finalPromptText": "hi",
         "channel": "telegram"},
    ))
    store.ingest(_row(
        "e2", sid, "model.completed", _today_iso("10:00:02Z"),
        {"_v3_type": "message", "modelId": "claude-opus-4-7",
         "provider": "anthropic", "channel": "telegram"},
        model="claude-opus-4-7", cost_usd=0.001,
    ))
    _drain(store)

    body = a.test_client().get("/api/component/gateway").get_json()
    assert body.get("_source") == "local_store", (
        f"v3 events lost canary tag: {body!r}"
    )
    routes_out = body.get("routes") or []
    assert routes_out, f"expected populated routes list: {body!r}"
    # Both v3 events count as messages.
    assert body["stats"]["today_messages"] >= 2, body["stats"]
    assert body["stats"]["today_errors"] == 0, body["stats"]
    # Channel propagation into the ``from`` slot (gateway-flow lane).
    channels = {r.get("from") for r in routes_out}
    assert "telegram" in channels, f"channel hint lost: {routes_out!r}"
    # Model propagation into the ``to`` slot.
    models = {r.get("to") for r in routes_out}
    assert "claude-opus-4-7" in models, f"model hint lost: {routes_out!r}"


# ── multi-provider: every channel surfaces ───────────────────────────────

def test_multi_provider_channels_all_surface(app):
    """When multiple adapters (telegram / signal / webchat) flow through
    the gateway on the same day, every channel must appear in the
    routes list — the panel's "messages by source" column relies on
    it. Catches the silent-channel-drop class of bugs."""
    a, ls = app
    store = ls.get_store()

    for i, channel in enumerate(("telegram", "signal", "webchat")):
        store.ingest(_row(
            f"e-{channel}", f"sess-{channel}", "prompt.submitted",
            _today_iso(f"10:0{i}:00Z"),
            {"_v3_type": "message", "channel": channel,
             "finalPromptText": f"from {channel}"},
        ))
    _drain(store)

    body = a.test_client().get("/api/component/gateway").get_json()
    assert body.get("_source") == "local_store"
    channels = {r.get("from") for r in (body.get("routes") or [])}
    for expected in ("telegram", "signal", "webchat"):
        assert expected in channels, (
            f"channel {expected!r} dropped: {channels!r}"
        )
    assert body["stats"]["today_messages"] >= 3


# ── error classification ─────────────────────────────────────────────────

def test_error_rows_bump_today_errors_and_tag_route(app):
    """Rows whose data carries ``errorCode`` (gateway RPC failure
    shape) must increment ``today_errors`` AND tag the route's
    status=error. Without this the panel under-reports gateway
    failures and the per-row chip stays green."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-gw-err"

    store.ingest(_row(
        "e-ok", sid, "prompt.submitted", _today_iso("11:00:00Z"),
        {"_v3_type": "message", "channel": "telegram"},
    ))
    store.ingest(_row(
        "e-err", sid, "model.completed", _today_iso("11:00:01Z"),
        {"_v3_type": "message", "channel": "telegram",
         "errorCode": "rate_limited", "modelId": "claude-opus-4-7"},
    ))
    _drain(store)

    body = a.test_client().get("/api/component/gateway").get_json()
    assert body.get("_source") == "local_store"
    assert body["stats"]["today_errors"] >= 1, body["stats"]
    err_routes = [r for r in body.get("routes", []) if r.get("status") == "error"]
    assert err_routes, f"no route tagged status=error: {body!r}"


# ── cron + heartbeat classification ──────────────────────────────────────

def test_cron_and_heartbeat_rows_route_to_correct_buckets(app):
    """``cron.run.started`` rows belong in ``today_crons`` and surface as
    ``type='cron'`` routes. ``gateway.metric`` rows belong in
    ``today_heartbeats``. This guards against the cron/heartbeat lane
    being silently absorbed into ``today_messages``."""
    a, ls = app
    store = ls.get_store()

    store.ingest(_row(
        "e-cron", "sess-cron", "cron.run.started",
        _today_iso("12:00:00Z"),
        {"_v3_type": "cron", "cronId": "daily-sync"},
    ))
    store.ingest(_row(
        "e-hb", "sess-hb", "gateway.metric",
        _today_iso("12:00:01Z"),
        {"rss_mb": 124, "cpu_pct": 1.2},
    ))
    _drain(store)

    body = a.test_client().get("/api/component/gateway").get_json()
    assert body.get("_source") == "local_store"
    assert body["stats"]["today_crons"] >= 1, body["stats"]
    assert body["stats"]["today_heartbeats"] >= 1, body["stats"]
    types = {r.get("type") for r in body.get("routes", [])}
    assert "cron" in types, f"cron type missing: {types!r}"
    assert "heartbeat" in types, f"heartbeat type missing: {types!r}"


# ── gate honoured: env flag OFF ──────────────────────────────────────────

def test_local_store_disabled_skips_fast_path(gated_off_app):
    """``CLAWMETRY_LOCAL_STORE_READ=0`` → fast path never fires even
    when DuckDB has flow-shape rows. Response is the legacy parser's
    shape (no ``_source`` tag)."""
    a, ls = gated_off_app
    store = ls.get_store()
    store.ingest(_row(
        "e1", "sess-x", "prompt.submitted", _today_iso("13:00:00Z"),
        {"_v3_type": "message"},
    ))
    _drain(store)

    body = a.test_client().get("/api/component/gateway").get_json()
    assert body.get("_source") != "local_store", (
        f"gate honoured? body={body!r}"
    )
