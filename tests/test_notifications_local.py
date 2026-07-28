"""Notifications (the channel manager Alerts + Approvals use) must work
self-hosted (founder 2026-07-28, after the same fix for Alerts): local
entitlement unlocks the tab, channels persist in the local alert-channels
config, and Slack / Telegram / PagerDuty deliver from this machine."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def test_notifications_tab_resolves_local_entitlement_first():
    src = _read("clawmetry/templates/tabs/notifications.html")
    assert "fetch('/api/entitlement')" in src
    assert "state.localMode = true" in src
    assert "'/api/alert-channels'" in src, "local mode must use the local channel config"
    assert "LOCAL_KEYS" in src, "the local channel adapter must exist"


def test_local_channel_config_accepts_telegram_keys():
    src = _read("routes/alerts.py")
    assert '"telegram_bot_token"' in src and '"telegram_chat_id"' in src, \
        "telegram must be configurable locally"
    assert '"pagerduty"' in src and '"telegram"' in src, \
        "the local test endpoint must cover telegram and pagerduty targets"


def test_alerts_tab_reads_local_channels_in_local_mode():
    src = _read("clawmetry/static/js/alerts.js")
    assert "alertsState.localMode" in src
    assert "'/api/alert-channels'" in src, \
        "alerts channel chips must come from the local config in local mode"
