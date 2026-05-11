"""Tests for _fire_token_spike_alerts() — pins the contract added in PR #969 / issue #874.

PR #969 wires the existing token_spike anomaly detector to user-configured alert rules.
These tests cover the matching/threshold/cooldown semantics so future changes can't
silently regress the roadmap promise.
"""
from __future__ import annotations

import os
import pytest

# Match the convention from tests/test_track.py — keep import side effects quiet.
os.environ.setdefault("CLAWMETRY_NO_INTERCEPT", "1")
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("SKIP_INTEGRATION", "1")

import dashboard


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def capture_fired(monkeypatch):
    """Replace dashboard._fire_alert with a recorder; return the call log."""
    calls: list[dict] = []

    def _record(rule_id, alert_type, message, channels=None, severity="warning"):
        calls.append({
            "rule_id": rule_id,
            "alert_type": alert_type,
            "message": message,
            "channels": channels,
            "severity": severity,
        })

    monkeypatch.setattr(dashboard, "_fire_alert", _record)
    return calls


@pytest.fixture
def rules_factory(monkeypatch):
    """Returns a setter that controls what _get_alert_rules() yields per test."""
    state: dict = {"rules": []}

    def _set(rules):
        state["rules"] = list(rules)

    monkeypatch.setattr(dashboard, "_get_alert_rules", lambda: list(state["rules"]))
    return _set


def _spike(*, ratio=5.0, session_key="sess-A", value=12000, baseline=1000.0,
           severity="warning", metric="token_spike"):
    """Build an anomaly dict matching the _detect_and_store_anomalies output shape."""
    return {
        "metric": metric,
        "session_key": session_key,
        "value": value,
        "baseline": baseline,
        "ratio": ratio,
        "severity": severity,
    }


def _rule(*, rule_id="rule-1", threshold=2.0, enabled=True,
          channels='["banner"]', rtype="token_spike"):
    return {
        "id": rule_id,
        "type": rtype,
        "enabled": enabled,
        "threshold": threshold,
        "channels": channels,
    }


# ---------------------------------------------------------------------------
# Empty / no-op paths
# ---------------------------------------------------------------------------

def test_empty_input_fires_nothing(capture_fired, rules_factory):
    rules_factory([_rule()])
    dashboard._fire_token_spike_alerts([])
    assert capture_fired == []


def test_non_token_spike_anomalies_ignored(capture_fired, rules_factory):
    rules_factory([_rule()])
    dashboard._fire_token_spike_alerts([_spike(metric="error_spike")])
    assert capture_fired == []


def test_no_rules_fires_nothing(capture_fired, rules_factory):
    rules_factory([])
    dashboard._fire_token_spike_alerts([_spike(ratio=10.0)])
    assert capture_fired == []


def test_disabled_rule_does_not_fire(capture_fired, rules_factory):
    rules_factory([_rule(enabled=False)])
    dashboard._fire_token_spike_alerts([_spike(ratio=10.0)])
    assert capture_fired == []


def test_rule_of_other_type_does_not_fire(capture_fired, rules_factory):
    rules_factory([_rule(rtype="threshold")])
    dashboard._fire_token_spike_alerts([_spike(ratio=10.0)])
    assert capture_fired == []


# ---------------------------------------------------------------------------
# Threshold semantics
# ---------------------------------------------------------------------------

def test_ratio_below_threshold_does_not_fire(capture_fired, rules_factory):
    rules_factory([_rule(threshold=5.0)])
    dashboard._fire_token_spike_alerts([_spike(ratio=3.0)])
    assert capture_fired == []


def test_ratio_at_threshold_fires(capture_fired, rules_factory):
    # Contract is inclusive: `ratio < threshold` skips, so equality fires.
    rules_factory([_rule(threshold=5.0)])
    dashboard._fire_token_spike_alerts([_spike(ratio=5.0)])
    assert len(capture_fired) == 1


def test_ratio_above_threshold_fires_with_expected_payload(capture_fired, rules_factory):
    rules_factory([_rule(rule_id="r1", threshold=2.0, channels='["banner"]')])
    dashboard._fire_token_spike_alerts([
        _spike(ratio=4.5, session_key="sess-X", value=8000, baseline=1000.0)
    ])
    assert len(capture_fired) == 1
    call = capture_fired[0]
    assert call["alert_type"] == "token_spike"
    assert call["channels"] == ["banner"]
    assert "sess-X" in call["message"]
    assert "8,000 tokens" in call["message"]
    assert "4.5" in call["message"]


# ---------------------------------------------------------------------------
# Cooldown key + multi-rule fan-out
# ---------------------------------------------------------------------------

def test_cooldown_key_scoped_per_rule_and_session(capture_fired, rules_factory):
    rules_factory([_rule(rule_id="r1", threshold=2.0),
                   _rule(rule_id="r2", threshold=3.0)])
    dashboard._fire_token_spike_alerts([_spike(ratio=10.0, session_key="sess-A")])
    cooldown_keys = sorted(c["rule_id"] for c in capture_fired)
    assert cooldown_keys == ["token_spike_r1_sess-A", "token_spike_r2_sess-A"]


def test_multi_anomalies_each_get_unique_cooldown_keys(capture_fired, rules_factory):
    rules_factory([_rule(rule_id="r1", threshold=2.0)])
    dashboard._fire_token_spike_alerts([
        _spike(ratio=10.0, session_key="sess-A"),
        _spike(ratio=5.0, session_key="sess-B"),
    ])
    keys = sorted(c["rule_id"] for c in capture_fired)
    assert keys == ["token_spike_r1_sess-A", "token_spike_r1_sess-B"]


def test_mixed_thresholds_only_meeting_rules_fire(capture_fired, rules_factory):
    rules_factory([
        _rule(rule_id="low", threshold=2.0),
        _rule(rule_id="high", threshold=10.0),
    ])
    dashboard._fire_token_spike_alerts([_spike(ratio=4.0)])
    fired_rule_ids = [c["rule_id"] for c in capture_fired]
    assert fired_rule_ids == ["token_spike_low_sess-A"]


# ---------------------------------------------------------------------------
# Channels parsing
# ---------------------------------------------------------------------------

def test_channels_parsed_from_json(capture_fired, rules_factory):
    rules_factory([_rule(threshold=2.0,
                         channels='["banner","slack","webhook"]')])
    dashboard._fire_token_spike_alerts([_spike(ratio=5.0)])
    assert capture_fired[0]["channels"] == ["banner", "slack", "webhook"]


def test_invalid_channels_json_falls_back_to_banner(capture_fired, rules_factory):
    rules_factory([_rule(threshold=2.0, channels="not-json")])
    dashboard._fire_token_spike_alerts([_spike(ratio=5.0)])
    assert capture_fired[0]["channels"] == ["banner"]


def test_null_channels_falls_back_to_banner(capture_fired, rules_factory):
    rules_factory([_rule(threshold=2.0, channels=None)])
    dashboard._fire_token_spike_alerts([_spike(ratio=5.0)])
    assert capture_fired[0]["channels"] == ["banner"]


# ---------------------------------------------------------------------------
# Severity passthrough
# ---------------------------------------------------------------------------

def test_severity_propagates_from_anomaly(capture_fired, rules_factory):
    rules_factory([_rule(threshold=2.0)])
    dashboard._fire_token_spike_alerts([_spike(ratio=5.0, severity="critical")])
    assert capture_fired[0]["severity"] == "critical"
