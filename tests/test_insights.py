"""Tests for the Weekly Insights Digest (feat/insights-v1).

Coverage:
  1. SQL templates pass the Dives safety validator (defence in depth).
  2. WeeklyDigestGenerator runs end-to-end against an empty DuckDB and
     returns a well-formed digest (no LLM call when ANTHROPIC_API_KEY unset).
  3. raw_select_safe rejects non-SELECT, runs SELECT, returns dict rows.
  4. Config round-trip via save_config / load_config.
  5. Routes return 404 when the feature flag is off, 200 when on.
  6. _seconds_until_next_run computes drift-free Monday 9am.
"""
from __future__ import annotations

import datetime
import importlib
import json
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Empty DuckDB at a tmp path, with the local_store reloaded so the
    singleton picks up the new path."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "test.duckdb")
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
def fresh_insights(tmp_path, monkeypatch, fresh_store):
    """Reload clawmetry.insights with the config path pinned to tmp."""
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
    sys.modules.pop("clawmetry.insights", None)
    import clawmetry.insights as ins
    importlib.reload(ins)
    yield ins


# ── 1. SQL safety ──────────────────────────────────────────────────────────


def test_all_templates_pass_safety_validator():
    """Every shipped template must pass dives_sql_safety. Module-import
    runs this same check; we re-assert here so a bad template lands as a
    test failure (not a startup crash)."""
    from clawmetry import insights
    from clawmetry.dives_sql_safety import validate_sql
    assert insights._INSIGHT_TEMPLATES, "no templates registered"
    for key, _title, sql, _hint in insights._INSIGHT_TEMPLATES:
        sanitized = (
            sql.replace("$since", "'2026-01-01T00:00:00Z'")
               .replace("$prev_since", "'2025-12-25T00:00:00Z'")
               .replace("$prior_window_start", "'2025-12-01T00:00:00Z'")
               .replace("$now_ts", "'2026-01-08T00:00:00Z'")
               .replace("$since_str", "'2026-01-01T00:00:00Z'")
        )
        ok, reason = validate_sql(sanitized)
        assert ok, f"template {key!r} failed safety: {reason}"


# ── 2. End-to-end on empty store (no LLM key) ──────────────────────────────


def test_generate_on_empty_store_no_api_key(fresh_insights, monkeypatch):
    """Empty DuckDB + no key → digest is well-formed, narratives say
    'no data', cost_usd is 0, no exception. This is the worst-case path
    that must not crash."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    gen = fresh_insights.WeeklyDigestGenerator()
    digest = gen.generate()
    out = digest.to_dict()
    assert "generated_at" in out
    assert out["cost_usd"] == 0.0
    assert len(out["insights"]) == len(fresh_insights._INSIGHT_TEMPLATES)
    for ins in out["insights"]:
        assert "title" in ins and "narrative" in ins and "rows" in ins
    text = digest.to_text()
    assert "ClawMetry Weekly Insights" in text


# ── 3. raw_select_safe ─────────────────────────────────────────────────────


def test_raw_select_safe_rejects_non_select(fresh_store):
    _ls, store = fresh_store
    with pytest.raises(ValueError):
        store.raw_select_safe(sql="DELETE FROM events")
    with pytest.raises(ValueError):
        store.raw_select_safe(sql="ATTACH 'foo.db' AS bar")


def test_raw_select_safe_returns_dict_rows(fresh_store):
    _ls, store = fresh_store
    rows = store.raw_select_safe(
        sql="SELECT 1 AS one, 'hi' AS msg, NULL AS none_col"
    )
    assert rows == [{"one": 1, "msg": "hi", "none_col": None}]


def test_raw_select_safe_with_bind(fresh_store):
    _ls, store = fresh_store
    rows = store.raw_select_safe(
        sql="SELECT $x::INTEGER AS x", params={"x": 42},
    )
    assert rows == [{"x": 42}]


# ── 4. Config round-trip ───────────────────────────────────────────────────


def test_save_and_load_config_round_trip(fresh_insights):
    fresh_insights.save_config({"channel": "slack", "opt_out": True})
    cfg = fresh_insights.load_config()
    assert cfg["channel"] == "slack"
    assert cfg["opt_out"] is True
    # Unknown keys dropped
    fresh_insights.save_config({"sneaky": "should-not-stick"})
    cfg2 = fresh_insights.load_config()
    assert "sneaky" not in cfg2


# ── 5. Routes feature gate ─────────────────────────────────────────────────


def test_view_endpoints_open_for_free_tier_with_upsell(
    fresh_insights, monkeypatch
):
    """Tier split (#1420 P0a): view endpoints (preview + /insights HTML)
    are universal — paired Free callers see the dashboard digest plus an
    ``_upgrade_cta`` field pointing them at Cloud-Pro for dispatch. The
    legacy ``CLAWMETRY_INSIGHTS=1`` env-var stays as an explicit-on
    override, but is no longer required to read the digest."""
    monkeypatch.delenv("CLAWMETRY_INSIGHTS", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import dashboard as _d
    monkeypatch.setattr(_d, "_read_cloud_token", lambda: "cm_fakepaired")
    sys.modules.pop("routes.insights", None)
    from flask import Flask
    from routes.insights import bp_insights
    app = Flask(__name__)
    app.register_blueprint(bp_insights)
    client = app.test_client()
    r = client.get("/api/insights/preview")
    assert r.status_code == 200, r.data
    body = r.get_json()
    assert "insights" in body
    # Paired-Free carries the dispatch upsell so the UI can route to Pro.
    assert body.get("_upgrade_cta", "").startswith("Want this delivered")
    assert body.get("_tier") == "free"
    assert body.get("_upgrade_url") == "/cloud/billing"
    r2 = client.get("/insights")
    assert r2.status_code == 200, r2.data


def test_oss_only_tier_gets_pair_cta_not_pro_upsell(fresh_insights, monkeypatch):
    """OSS-only nodes (no ``cm_`` token) need the pair-to-Cloud CTA, not
    the Slack/dispatch upsell. Closes the first-touch friction wall from
    #1420 P0b: ask the OSS user to pair (free + zero-config AI summaries)
    before pitching paid dispatch."""
    monkeypatch.delenv("CLAWMETRY_INSIGHTS", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import dashboard as _d
    monkeypatch.setattr(_d, "_read_cloud_token", lambda: None)
    sys.modules.pop("routes.insights", None)
    from flask import Flask
    from routes.insights import bp_insights
    app = Flask(__name__)
    app.register_blueprint(bp_insights)
    client = app.test_client()
    r = client.get("/api/insights/preview")
    assert r.status_code == 200, r.data
    body = r.get_json()
    assert body.get("_tier") == "oss"
    assert body.get("_upgrade_url") == "/cloud/connect"
    assert "Connect this node" in body.get("_upgrade_cta", "")
    assert "No Anthropic key required" in body.get("_upgrade_cta", "")


def test_send_now_pro_paywall_for_free_tier(fresh_insights, monkeypatch):
    """Dispatch is Cloud-Pro only. Free / OSS callers get a 402 with the
    upsell envelope so the UI can route them to billing instead of a
    silent failure (project_free_plan_upsell.md, project_alerts_pro_feature.md).
    """
    monkeypatch.delenv("CLAWMETRY_INSIGHTS", raising=False)
    sys.modules.pop("routes.insights", None)
    from flask import Flask
    from routes.insights import bp_insights
    app = Flask(__name__)
    app.register_blueprint(bp_insights)
    client = app.test_client()
    r = client.post("/api/insights/send-now")
    assert r.status_code == 402, r.data
    body = r.get_json()
    assert body["error"] == "pro_required"
    assert "Upgrade to Cloud-Pro" in body["_upgrade_cta"]
    # POST /api/insights/config also paywalled (writes touch dispatch).
    r2 = client.post(
        "/api/insights/config",
        data=json.dumps({"channel": "slack"}),
        content_type="application/json",
    )
    assert r2.status_code == 402, r2.data


def test_config_get_returns_200_with_upsell_for_free_tier(
    fresh_insights, monkeypatch
):
    """/api/insights/config GET is the dashboard's nav-tab-reveal probe.
    Returning 404 there caused the browser to console.error on every page
    load, tripping cloud-contract gates (#1431). Under the tier split
    (#1420 P0a) GET is now universal — Free / OSS get the full config
    plus an upsell envelope so the nav tab reveals itself and the page
    can render the conversion CTA. POST stays Pro-gated (402)."""
    monkeypatch.delenv("CLAWMETRY_INSIGHTS", raising=False)
    import dashboard as _d
    monkeypatch.setattr(_d, "_read_cloud_token", lambda: "cm_fakepaired")
    sys.modules.pop("routes.insights", None)
    from flask import Flask
    from routes.insights import bp_insights
    app = Flask(__name__)
    app.register_blueprint(bp_insights)
    client = app.test_client()
    r = client.get("/api/insights/config")
    assert r.status_code == 200, r.data
    body = r.get_json()
    assert body.get("enabled") is True, body
    assert body.get("_tier") == "free"
    assert "Upgrade to Cloud-Pro" in body["_upgrade_cta"]
    # POST is Pro-only: writes touch dispatch settings.
    r2 = client.post(
        "/api/insights/config",
        data=json.dumps({"channel": "slack"}),
        content_type="application/json",
    )
    assert r2.status_code == 402, r2.data


def test_routes_serve_when_flag_on(fresh_insights, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_INSIGHTS", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Re-import routes/insights so the gate flag reads fresh.
    sys.modules.pop("routes.insights", None)
    from flask import Flask
    from routes.insights import bp_insights
    app = Flask(__name__)
    app.register_blueprint(bp_insights)
    client = app.test_client()
    r = client.get("/api/insights/preview")
    assert r.status_code == 200
    body = r.get_json()
    assert "insights" in body and len(body["insights"]) >= 8
    r2 = client.get("/insights")
    assert r2.status_code == 200
    assert b"Weekly Insights" in r2.data


def test_config_endpoint_redacts_api_key(fresh_insights, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_INSIGHTS", "1")
    sys.modules.pop("routes.insights", None)
    from flask import Flask
    from routes.insights import bp_insights
    app = Flask(__name__)
    app.register_blueprint(bp_insights)
    client = app.test_client()
    client.post(
        "/api/insights/config",
        data=json.dumps({"anthropic_api_key": "sk-secret"}),
        content_type="application/json",
    )
    r = client.get("/api/insights/config")
    assert r.get_json()["anthropic_api_key"] == "***"


# ── 6. Cloud-relayed synthesis (P0b — no Anthropic-key friction wall) ────


def test_resolver_picks_direct_when_local_key_set(fresh_insights, monkeypatch):
    """Local Anthropic key wins over cloud relay so Pro users keep cost
    attribution on their own invoice (#1420 P0b)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-local")
    mode, secret = fresh_insights._resolve_synthesis_credential({})
    assert mode == "direct"
    assert secret == "sk-local"


def test_resolver_picks_relay_when_paired_but_no_local_key(
    fresh_insights, monkeypatch
):
    """Cloud-paired node with no local key → relay path. This is the
    zero-friction first-touch behaviour mandated by #1420 P0b."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import dashboard as _d
    monkeypatch.setattr(_d, "_read_cloud_token", lambda: "cm_testtoken")
    mode, secret = fresh_insights._resolve_synthesis_credential({})
    assert mode == "relay"
    assert secret == "cm_testtoken"


def test_resolver_picks_none_for_oss_only_node(fresh_insights, monkeypatch):
    """OSS-only (no key, no pairing) → ``none`` — caller renders the stub
    narrative without throwing. Worst-case path must not crash."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import dashboard as _d
    monkeypatch.setattr(_d, "_read_cloud_token", lambda: None)
    mode, secret = fresh_insights._resolve_synthesis_credential({})
    assert mode == "none"
    assert secret is None


def test_synthesize_via_relay_hits_cloud_endpoint(fresh_insights, monkeypatch):
    """Relay path POSTs to ``{INGEST_URL}/api/insights/synthesize`` with
    the user's ``cm_`` bearer and parses ``{text, tokens}`` from the
    response. Validates the wire shape so the cloud-side handler can be
    built against a fixed contract."""
    import io
    import urllib.request

    captured: dict = {}

    class _FakeResp:
        def read(self):
            return json.dumps({"text": "synthesised via cloud.", "tokens": 42}).encode()
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    def _fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.headers)
        captured["body"] = json.loads(req.data.decode())
        return _FakeResp()

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    text, tokens = fresh_insights._synthesize_via_relay(
        "cm_testtoken", "Top cost drivers", "hint", [{"x": 1}],
    )
    assert text == "synthesised via cloud."
    assert tokens == 42
    assert captured["url"].endswith("/api/insights/synthesize")
    # Bearer goes in Authorization (capitalisation comes from urllib).
    assert captured["headers"].get("Authorization") == "Bearer cm_testtoken"
    # Body carries the prompt + raw row preview so the cloud handler has
    # both shapes available (cheap re-synth without re-running the prompt
    # builder cloud-side if it prefers).
    assert "prompt" in captured["body"]
    assert captured["body"]["rows"] == [{"x": 1}]


def test_relay_synthesis_failure_falls_back_to_stub(fresh_insights, monkeypatch):
    """Cloud endpoint not yet deployed / network error → caller gets the
    same stub fallback as the no-key path. Forward-compat with cloud
    rollout so we don't block this PR on a cloud-side merge."""
    import urllib.error
    import urllib.request

    def _fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 404, "not found", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    text, tokens = fresh_insights._synthesize_narrative(
        "cm_token", "title", "hint", [{"x": 1}], mode="relay",
    )
    assert "unavailable" in text
    assert tokens == 0


# ── 7. Scheduler math ──────────────────────────────────────────────────────


def test_seconds_until_next_run_rolls_to_next_week():
    from clawmetry.insights import _seconds_until_next_run
    # Sunday 10am → Monday 9am is 23h
    sunday = datetime.datetime(2026, 5, 17, 10, 0, 0)  # Sunday
    secs = _seconds_until_next_run(sunday, weekday=0, hour=9)
    assert 22 * 3600 < secs < 24 * 3600
    # Monday 9:01am → next Monday 9am is 7d - 1min
    monday_after = datetime.datetime(2026, 5, 18, 9, 1, 0)
    secs2 = _seconds_until_next_run(monday_after, weekday=0, hour=9)
    assert 6 * 86400 < secs2 < 7 * 86400
