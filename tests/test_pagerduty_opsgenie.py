"""Tests for the PagerDuty + OpsGenie alert sinks (Pro feature).

Pins the payload shape for each vendor's API + the dispatcher
fan-out + the new config keys.
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def d(tmp_path, monkeypatch):
    """Import dashboard once with a sandbox alerts-config path so tests
    don't touch the real ~/.clawmetry/alerts.json."""
    monkeypatch.setenv("HOME", str(tmp_path))
    import dashboard as _d
    monkeypatch.setattr(_d, "_ALERTS_CONFIG_FILE", str(tmp_path / "alerts.json"))
    return _d


# ── PagerDuty payload ─────────────────────────────────────────────────────────


def test_pagerduty_payload_shape(d):
    body = d._build_pagerduty_payload(
        {
            "type": "cost_spike",
            "severity": "critical",
            "agent": "main",
            "message": "Cost crossed $50 in 5 min",
            "cost_usd": 53.12,
            "threshold": 50,
        },
        routing_key="abcdef0123456789",
    )
    assert body["routing_key"] == "abcdef0123456789"
    assert body["event_action"] == "trigger"
    assert body["dedup_key"] == "clawmetry:main:cost_spike"
    pay = body["payload"]
    assert pay["severity"] == "critical"
    assert pay["source"] == "clawmetry"
    assert pay["summary"].startswith("Cost crossed")
    assert pay["component"] == "main"
    assert pay["custom_details"]["cost_usd"] == 53.12


def test_pagerduty_severity_falls_back_to_warning(d):
    body = d._build_pagerduty_payload({"severity": "nonsense"}, routing_key="k")
    assert body["payload"]["severity"] == "warning"


def test_pagerduty_summary_truncates_at_1024(d):
    body = d._build_pagerduty_payload({"message": "x" * 5000}, routing_key="k")
    assert len(body["payload"]["summary"]) == 1024


# ── OpsGenie payload ─────────────────────────────────────────────────────────


def test_opsgenie_payload_shape(d):
    body = d._build_opsgenie_payload({
        "type": "agent_error_rate",
        "severity": "error",
        "agent": "scout",
        "message": "Error rate >20% on scout",
    })
    assert body["message"] == "Error rate >20% on scout"
    assert body["alias"] == "clawmetry:scout:agent_error_rate"
    assert body["priority"] == "P2"
    assert body["source"] == "clawmetry"
    assert "clawmetry" in body["tags"]


def test_opsgenie_severity_mapping(d):
    for sev, pri in [("info", "P5"), ("warning", "P3"), ("error", "P2"), ("critical", "P1")]:
        body = d._build_opsgenie_payload({"severity": sev, "message": "x"})
        assert body["priority"] == pri, sev


def test_opsgenie_message_caps_at_130(d):
    body = d._build_opsgenie_payload({"message": "y" * 1000})
    assert len(body["message"]) == 130


# ── dispatcher routing ───────────────────────────────────────────────────────


def _last_call(mock):
    return mock.call_args_list[-1]


def test_dispatch_fanout_calls_every_configured_sink(d):
    d._save_alerts_webhook_config({
        "webhook_url": "https://wh.example/incoming",
        "slack_webhook_url": "https://hooks.slack.com/services/AAA",
        "discord_webhook_url": "https://discord.com/api/webhooks/BBB",
        "pagerduty_routing_key": "pdkey-001",
        "opsgenie_api_key": "ogkey-001",
    })
    sent_via: list[str] = []

    def _capture(url, payload, payload_type="generic"):
        sent_via.append(payload_type)

    with patch.object(d, "_send_webhook_alert", side_effect=_capture):
        out = d._dispatch_alert_to_all_sinks({
            "type": "cost_spike", "severity": "warning", "agent": "main",
            "message": "hi", "cost_usd": 1, "threshold": 0,
        })
    assert set(out) == {"generic", "slack", "discord", "pagerduty", "opsgenie"}
    assert set(sent_via) == {"generic", "slack", "discord", "pagerduty", "opsgenie"}


def test_dispatch_skips_unconfigured_sinks(d):
    d._save_alerts_webhook_config({"slack_webhook_url": "https://hooks.slack.com/x"})
    with patch.object(d, "_send_webhook_alert") as mock:
        out = d._dispatch_alert_to_all_sinks({"type": "t", "severity": "warning"})
    assert out == ["slack"]
    assert mock.call_count == 1


def test_dispatch_includes_pd_key_in_payload_not_in_other_bodies(d):
    """The routing_key + opsgenie api_key are stashed on the payload
    dict so the formatter can read them. They must NEVER be forwarded
    to generic/slack/discord webhooks (those see the original dict
    without the underscore-prefixed leaks)."""
    d._save_alerts_webhook_config({
        "webhook_url": "https://wh.example/in",
        "pagerduty_routing_key": "pdkey-leak-test",
        "opsgenie_api_key": "ogkey-leak-test",
    })
    captured: list[dict] = []

    def _capture(url, payload, payload_type="generic"):
        captured.append((payload_type, dict(payload)))

    with patch.object(d, "_send_webhook_alert", side_effect=_capture):
        d._dispatch_alert_to_all_sinks({"type": "t", "severity": "warning"})
    # Generic must not see the secret keys.
    for kind, body in captured:
        if kind == "generic":
            assert "_pd_routing_key" not in body
            assert "_og_api_key" not in body
        if kind == "pagerduty":
            assert body.get("_pd_routing_key") == "pdkey-leak-test"
        if kind == "opsgenie":
            assert body.get("_og_api_key") == "ogkey-leak-test"


# ── config plumbing ──────────────────────────────────────────────────────────


def test_save_persists_new_keys(d):
    cfg = d._save_alerts_webhook_config({
        "pagerduty_routing_key": "abc",
        "opsgenie_api_key": "def",
        "opsgenie_api_url": "https://api.eu.opsgenie.com/v2/alerts",
    })
    assert cfg["pagerduty_routing_key"] == "abc"
    assert cfg["opsgenie_api_key"] == "def"
    assert cfg["opsgenie_api_url"].endswith("eu.opsgenie.com/v2/alerts")
    # Re-load from disk to confirm round-trip.
    cfg2 = d._load_alerts_webhook_config()
    assert cfg2["pagerduty_routing_key"] == "abc"
    assert cfg2["opsgenie_api_key"] == "def"


def test_save_rejects_unknown_keys(d):
    cfg = d._save_alerts_webhook_config({"definitely_not_a_real_key": "evil"})
    assert "definitely_not_a_real_key" not in cfg
