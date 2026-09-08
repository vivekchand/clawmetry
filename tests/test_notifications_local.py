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


def test_channel_loader_reads_the_variable_it_declared():
    """Regression: the loader assigned the fetch to `resp` but the next line
    read a stale `data` name. The ReferenceError was swallowed by the
    surrounding catch, state.rows stayed [], and a freshly connected channel
    kept rendering as "Connect" with the status stuck on "No channels
    configured yet" (live-hit 2026-07-29 with a saved Telegram config)."""
    src = _read("clawmetry/templates/tabs/notifications.html")
    assert "state.rows = (resp && resp.channels) || [];" in src
    assert "state.rows = (data && data.channels) || [];" not in src


def test_telegram_keys_survive_the_effective_save_load_round_trip(tmp_path, monkeypatch):
    """Regression: the /api/alert-channels ROUTE allowlisted telegram keys but
    dashboard._save_alerts_webhook_config (the LATER, winning definition of a
    duplicated trio) silently dropped them - a "saved" Telegram channel never
    persisted, its card stayed on "Connect", and the Alerts tab kept saying
    "no channels" (live-hit 2026-07-29). This exercises the EFFECTIVE
    functions on the imported module, so a revert of either duplicate fails."""
    import dashboard as _d
    monkeypatch.setattr(_d, "_ALERTS_CONFIG_FILE",
                        str(tmp_path / "alerts_webhook.json"))
    saved = _d._save_alerts_webhook_config({
        "telegram_bot_token": "12345:abcde",
        "telegram_chat_id": "-100999",
    })
    assert saved.get("telegram_bot_token") == "12345:abcde"
    assert saved.get("telegram_chat_id") == "-100999"
    loaded = _d._load_alerts_webhook_config()
    assert loaded.get("telegram_bot_token") == "12345:abcde"
    assert loaded.get("telegram_chat_id") == "-100999"
