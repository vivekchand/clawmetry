"""Built-in monitor delivery must be honest and controllable.

Founder-reported 2026-08-17: every always-on monitor showed an
"In-app · telegram" pill on a node where Telegram was never configured.
The pill came from a hardcoded ``channels=["banner", "telegram"]`` in the
catalog; actual delivery read creds from a store the Notifications tab
never writes, so "telegram" was a fabricated destination.

The fix: one resolver (``_resolve_builtin_delivery``) answers "where does
this monitor deliver?" for both the API the tab renders and ``_fire_alert``
itself, and only ever offers channels this process can deliver to right
now. Operators can mute a monitor or pin its channels. These tests pin
that contract.
"""

import json

import pytest

import dashboard as _d
from routes.alerts import BUILTIN_MONITORS


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    """No channels configured anywhere, prefs in a temp file."""
    monkeypatch.setattr(_d, "_BUILTIN_MONITOR_PREFS_FILE",
                        str(tmp_path / "builtin_monitors.json"))
    monkeypatch.setattr(_d, "_load_alerts_webhook_config", lambda: {})
    monkeypatch.setattr(_d, "_get_budget_config", lambda: {})
    return tmp_path


def test_unconfigured_node_gets_banner_only(isolated):
    """The founder's bug: no Telegram configured -> no telegram channel."""
    r = _d._resolve_builtin_delivery("heartbeat_silent")
    assert r["enabled"] is True
    assert r["channels"] == ["banner"]
    assert r["mode"] == "auto"


def test_catalog_carries_no_hardcoded_channels():
    """The static catalog must not advertise destinations; only the live
    resolver may. A ``channels`` key here is exactly the old bug."""
    for m in BUILTIN_MONITORS:
        assert "channels" not in m, (
            f"BUILTIN_MONITORS[{m['alert_type']}] hardcodes channels; "
            f"delivery is resolved live via _resolve_builtin_delivery"
        )


def test_telegram_offered_once_configured(isolated, monkeypatch):
    monkeypatch.setattr(_d, "_load_alerts_webhook_config", lambda: {
        "telegram_bot_token": "123:abc", "telegram_chat_id": "42"})
    r = _d._resolve_builtin_delivery("anomaly")
    assert r["channels"] == ["banner", "telegram"]


def test_telegram_creds_read_from_legacy_budget_store(isolated, monkeypatch):
    """Both stores must count — the budget-config store predates the
    Notifications tab and existing installs still hold creds there."""
    monkeypatch.setattr(_d, "_get_budget_config", lambda: {
        "telegram_bot_token": "123:abc", "telegram_chat_id": "42"})
    assert _d._telegram_creds() == ("123:abc", "42")


def test_mute_silences_fire(isolated, monkeypatch):
    _d._save_builtin_monitor_pref("heartbeat_silent", enabled=False)
    assert _d._resolve_builtin_delivery("heartbeat_silent")["enabled"] is False

    delivered = []
    monkeypatch.setattr(_d, "_send_telegram_alert",
                        lambda msg: delivered.append(("telegram", msg)))
    monkeypatch.setattr(_d, "_dispatch_alert",
                        lambda *a, **k: delivered.append(("dispatch", k)))
    monkeypatch.setattr(_d, "_budget_alert_cooldowns", {})
    history_calls = []
    monkeypatch.setattr(_d, "_fleet_db", lambda: history_calls.append(1))
    _d._fire_alert("heartbeat_gap", "heartbeat_silent", "test message")
    assert delivered == [] and history_calls == [], (
        "a muted built-in monitor must not deliver anywhere or write history"
    )


def test_pinned_unconfigured_channel_is_dropped(isolated):
    """Pinning telegram while it is unconfigured must not advertise it —
    the pin waits until the channel is deliverable."""
    _d._save_builtin_monitor_pref("anomaly", channels=["telegram"])
    r = _d._resolve_builtin_delivery("anomaly")
    assert r["mode"] == "custom"
    assert r["channels"] == ["banner"]


def test_banner_cannot_be_removed(isolated):
    _d._save_builtin_monitor_pref("anomaly", channels=[])
    prefs = json.loads(open(_d._BUILTIN_MONITOR_PREFS_FILE).read())
    assert "banner" in prefs["anomaly"]["channels"]


def test_auto_clears_pin(isolated):
    _d._save_builtin_monitor_pref("anomaly", channels=["banner"])
    _d._save_builtin_monitor_pref("anomaly", channels="auto")
    assert _d._resolve_builtin_delivery("anomaly")["mode"] == "auto"


def test_user_rule_channels_untouched(isolated, monkeypatch):
    """builtin=False must bypass the resolver entirely: a user rule keeps
    the channels it was saved with even when the same alert_type is also a
    built-in monitor."""
    seen = {}
    monkeypatch.setattr(_d, "_budget_alert_cooldowns", {})
    monkeypatch.setattr(_d, "_fleet_db_lock", _d._fleet_db_lock)

    class _FakeDb:
        def execute(self, *a):
            seen.setdefault("channels", []).append(a[1][3])
        def commit(self):
            pass
        def close(self):
            pass

    monkeypatch.setattr(_d, "_fleet_db", lambda: _FakeDb())
    monkeypatch.setattr(_d, "_send_telegram_alert", lambda m: seen.setdefault("tg", True))
    monkeypatch.setattr(_d, "_dispatch_alert", lambda *a, **k: seen.setdefault("only", k.get("only")))
    _d._save_builtin_monitor_pref("threshold", enabled=False)  # builtin muted...
    _d._fire_alert("rule_x", "threshold", "msg", channels=["banner", "telegram"],
                   builtin=False)  # ...but the user rule still fires
    assert seen.get("channels") == ["banner", "telegram"]
    assert seen.get("tg") is True
    assert seen.get("only") is None
