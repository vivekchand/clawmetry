"""Detector incidents reach a human.

Covers ``clawmetry/incident_alerts.py`` and its two callers in ``sync.py``:
the detector emit path (warning/critical incidents fan out) and the Guard
policy ``alert`` action (which used to record "no action for this policy
type" and deliver nothing). Everything network-shaped is stubbed; the banner
path writes to a temp fleet SQLite DB; the cooldown latch is exercised on a
fake store AND on a real temp DuckDB store.
"""
from __future__ import annotations

import importlib
import os
import sqlite3
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import incident_alerts as ia  # noqa: E402
from clawmetry import sync as _sync  # noqa: E402


class LatchStore:
    """Only the latch surface: what deliver_incident needs from a store."""

    def __init__(self):
        self.sent = {}
        self.recorded = []

    # Keyword-only on purpose: production calls these with kwargs because the
    # dashboard's _ProxyStore drops positionals, and a fake that accepted
    # positionals would let a regression to positional calls pass here.
    def incident_alert_last_sent(self, *, session_id, kind):
        return self.sent.get((session_id, kind), 0)

    def record_incident_alert(self, *, session_id, kind, delivered_via=None, severity=""):
        self.sent[(session_id, kind)] = int(time.time() * 1000)
        self.recorded.append((session_id, kind, list(delivered_via or []), severity))


def _incident(kind="rate_limited", sev="warning", sid="codex:abc"):
    return {"kind": kind, "session_id": sid, "runtime": "codex",
            "severity": sev, "title": "codex is being rate limited",
            "detail": "The provider refused 3 requests.",
            "evidence": {"refusals": 3},
            "spend_at_risk_usd": 1.25, "spend_basis": "burn_rate"}


@pytest.fixture
def sinks(monkeypatch, tmp_path):
    """Temp fleet DB for the banner, recorded senders, no entitlement gate."""
    monkeypatch.setenv("CLAWMETRY_FLEET_DB", str(tmp_path / "fleet.db"))
    monkeypatch.setattr(ia, "_fleet_db_path", lambda: str(tmp_path / "fleet.db"))
    monkeypatch.setattr(ia, "_BUILTIN_PREFS_FILE", str(tmp_path / "prefs.json"))
    monkeypatch.setattr(ia, "_ALERTS_CONFIG_FILE", str(tmp_path / "alerts.json"))
    monkeypatch.setattr(ia, "_load_alerts_config", lambda: {})
    monkeypatch.setattr(ia, "_budget_config", lambda: {})
    monkeypatch.setattr(ia, "_MEMO", {})
    calls = {"telegram": [], "slack": [], "discord": [], "webhook": []}
    monkeypatch.setattr(ia, "send_telegram", lambda m: calls["telegram"].append(m) or True)
    monkeypatch.setattr(ia, "send_slack", lambda m, s, t: calls["slack"].append(m) or True)
    monkeypatch.setattr(ia, "send_discord", lambda m, s, t: calls["discord"].append(m) or True)
    monkeypatch.setattr(ia, "send_webhook", lambda p: calls["webhook"].append(p) or True)
    calls["fleet_db"] = str(tmp_path / "fleet.db")
    return calls


def _banner_rows(path):
    if not os.path.exists(path):
        return []
    db = sqlite3.connect(path)
    try:
        has = db.execute("SELECT name FROM sqlite_master WHERE name='alert_history'").fetchone()
        if not has:
            return []
        return db.execute("SELECT rule_id, type, channel, message FROM alert_history").fetchall()
    finally:
        db.close()


# ── free channels: banner always, telegram when configured ─────────────────

def test_warning_incident_lands_in_banner_history(sinks):
    store = LatchStore()
    res = ia.deliver_incident(store, _incident())
    assert res["delivered"] is True
    assert res["delivered_via"] == ["banner"]
    rows = _banner_rows(sinks["fleet_db"])
    assert len(rows) == 1
    rule_id, atype, channel, message = rows[0]
    assert atype == "agent_attention" and channel == "banner"
    assert rule_id == "agent_attention:rate_limited"
    assert "rate limited" in message and "$1.25" in message
    assert "—" not in message and "--" not in message
    assert store.recorded == [("codex:abc", "rate_limited", ["banner"], "warning")]


def test_telegram_is_free_when_creds_exist(sinks, monkeypatch):
    monkeypatch.setattr(ia, "telegram_creds", lambda: ("tok", "123"))
    # Not entitled to webhooks: irrelevant for telegram, must not block it.
    monkeypatch.setattr(ia, "_webhooks_entitled", lambda: False)
    res = ia.deliver_incident(LatchStore(), _incident())
    assert res["delivered_via"] == ["banner", "telegram"]
    assert len(sinks["telegram"]) == 1
    channels = {r[2] for r in _banner_rows(sinks["fleet_db"])}
    assert channels == {"banner", "telegram"}


# ── gated channels ─────────────────────────────────────────────────────────

def test_webhooks_stay_behind_the_alert_webhooks_gate(sinks, monkeypatch):
    monkeypatch.setattr(ia, "_load_alerts_config", lambda: {
        "slack_webhook_url": "https://hooks.example/s",
        "webhook_url": "https://hooks.example/w"})
    monkeypatch.setattr(ia, "_webhooks_entitled", lambda: False)
    res = ia.deliver_incident(LatchStore(), _incident())
    assert res["delivered_via"] == ["banner"]
    assert sorted(res["gated_off"]) == ["slack", "webhook"]
    assert "not on this plan" in res["reason"]
    assert sinks["slack"] == [] and sinks["webhook"] == []


def test_webhooks_deliver_when_entitled(sinks, monkeypatch):
    monkeypatch.setattr(ia, "_load_alerts_config", lambda: {
        "slack_webhook_url": "https://hooks.example/s",
        "discord_webhook_url": "https://hooks.example/d",
        "webhook_url": "https://hooks.example/w"})
    monkeypatch.setattr(ia, "_webhooks_entitled", lambda: True)
    res = ia.deliver_incident(LatchStore(), _incident(sev="critical"))
    assert res["delivered_via"] == ["banner", "slack", "discord", "webhook"]
    payload = sinks["webhook"][0]
    assert payload["type"] == "agent_attention" and payload["kind"] == "rate_limited"
    assert payload["session_id"] == "codex:abc" and payload["severity"] == "critical"
    assert sinks["slack"][0].startswith("CRITICAL:")


# ── floor, mute, cooldown ──────────────────────────────────────────────────

def test_info_incidents_do_not_page_anyone(sinks):
    res = ia.deliver_incident(LatchStore(), _incident(sev="info"))
    assert res["delivered"] is False and "below the alert floor" in res["reason"]
    assert _banner_rows(sinks["fleet_db"]) == []


def test_policy_alert_forces_past_the_floor_but_not_the_latch(sinks):
    store = LatchStore()
    res = ia.deliver_incident(store, _incident(sev="info"), force=True, policy_id="p1")
    assert res["delivered"] is True
    assert _banner_rows(sinks["fleet_db"])[0][0] == "agent_attention:rate_limited:p1"
    again = ia.deliver_incident(store, _incident(sev="info"), force=True, policy_id="p1")
    assert again["delivered"] is False and "already alerted" in again["reason"]


def test_operator_mute_is_honoured(sinks, monkeypatch, tmp_path):
    import json
    (tmp_path / "prefs.json").write_text(json.dumps({"agent_attention": {"enabled": False}}))
    res = ia.deliver_incident(LatchStore(), _incident())
    assert res["delivered"] is False and "muted" in res["reason"]
    assert _banner_rows(sinks["fleet_db"]) == []


def test_cooldown_dedupes_per_session_and_kind(sinks):
    store = LatchStore()
    assert ia.deliver_incident(store, _incident())["delivered"] is True
    second = ia.deliver_incident(store, _incident())
    assert second["delivered"] is False and "already alerted" in second["reason"]
    # A different kind on the same session is a different fact.
    assert ia.deliver_incident(store, _incident(kind="crashed"))["delivered"] is True
    # A different session with the same kind too.
    assert ia.deliver_incident(store, _incident(sid="codex:other"))["delivered"] is True
    assert len(_banner_rows(sinks["fleet_db"])) == 3


def test_cooldown_expiry_refires(sinks):
    store = LatchStore()
    ia.deliver_incident(store, _incident())
    store.sent[("codex:abc", "rate_limited")] -= 31 * 60 * 1000
    assert ia.deliver_incident(store, _incident())["delivered"] is True


def test_latch_survives_a_restart_on_a_real_store(sinks, tmp_path, monkeypatch):
    """The latch is in DuckDB, so a fresh process (new memo, same store) must
    still see the earlier delivery."""
    pytest.importorskip("duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "t.duckdb"))
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    from pathlib import Path
    monkeypatch.setattr(ls, "DB_PATH", Path(str(tmp_path / "t.duckdb")))
    monkeypatch.setattr(ls, "_writer_owner", True)
    # A real store, not get_store(): in CI's shared pytest process an earlier
    # test can leave a daemon discovery file behind and get_store() then
    # returns a _ProxyStore that drops positional args and knows no daemon.
    store = ls.LocalStore(read_only=False)
    try:
        assert ia.deliver_incident(store, _incident())["delivered"] is True
        assert store.incident_alert_last_sent("codex:abc", "rate_limited") > 0
        monkeypatch.setattr(ia, "_MEMO", {})  # "restart": in-process memo gone
        res = ia.deliver_incident(store, _incident())
        assert res["delivered"] is False and "already alerted" in res["reason"]
        rows = store.query_incident_alerts()
        assert rows[0]["kind"] == "rate_limited" and rows[0]["delivered_via"] == ["banner"]
    finally:
        store.stop(flush=False)


# ── sync.py: policy action "alert" ─────────────────────────────────────────

class PolicyStore(LatchStore):
    def __init__(self, policies):
        super().__init__()
        self._policies = policies
        self.decisions = []
        self.fired = set()

    def query_session_policies(self, enabled_only=False):
        return list(self._policies)

    def query_policy_ladder_state(self):
        return {}

    def policy_already_fired(self, session_id, policy_id, step=0):
        return (session_id, policy_id, step) in self.fired

    def record_policy_action(self, session_id, policy_id, **kw):
        self.fired.add((session_id, policy_id, kw.get("step_index", 0)))
        self.decisions.append({"session_id": session_id, "policy_id": policy_id, **kw})


def _policy(action, pid="p1"):
    return {"policy_id": pid, "enabled": True, "scope_runtime": "",
            "scope_agent_id": "", "trigger_kind": "", "min_severity": "info",
            "min_repeat": 0, "min_duration_s": 0, "min_spend_usd": 0,
            "action": action}


_FACTS = {"codex:abc": {"cost_usd": 2.0, "bad_for_seconds": 300,
                        "runtime": "codex", "cwd": "/tmp/x", "agent_id": "main"}}


def test_policy_alert_action_delivers_and_records_where(sinks, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_POLICY_ENFORCE", raising=False)
    monkeypatch.setattr(_sync, "_guard_actuate",
                        lambda *a, **k: pytest.fail("alert must never signal a process"))
    store = PolicyStore([_policy("alert")])
    n = _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    assert n == 1
    d = store.decisions[0]
    assert d["action"] == "alert" and d["enforced"] is False
    assert d["result_detail"] == "alerted via banner"
    assert "no action for this policy type" not in d["result_detail"]
    rows = _banner_rows(sinks["fleet_db"])
    assert rows and rows[0][0] == "agent_attention:rate_limited:p1"


def test_policy_monitor_detail_says_monitor_mode(sinks, monkeypatch):
    monkeypatch.setattr(_sync, "_guard_actuate", lambda *a, **k: {"ok": True})
    store = PolicyStore([_policy("monitor")])
    _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    assert store.decisions[0]["result_detail"] == "recorded (monitor mode: watched, no action taken)"
    assert _banner_rows(sinks["fleet_db"]) == []


def test_policy_alert_within_cooldown_says_so(sinks, monkeypatch):
    monkeypatch.setattr(_sync, "_guard_actuate", lambda *a, **k: {"ok": True})
    store = PolicyStore([_policy("alert", "p1"), _policy("alert", "p2")])
    store.sent[("codex:abc", "rate_limited")] = int(time.time() * 1000)
    _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    details = {d["policy_id"]: d["result_detail"] for d in store.decisions}
    # policy_engine picks at most one decision per session; whichever won,
    # the latch held and the row says so instead of claiming an alert.
    assert details and all("already alerted" in v for v in details.values())


# ── sync.py: detector emit path ────────────────────────────────────────────

def test_emit_path_delivers_warning_incidents_and_records_delivered_via(monkeypatch):
    """Drive ``_emit_detector_incidents`` with a fake store and a stubbed
    detector: a warning incident is handed to deliver_incident, and the
    loop_signals row carries ``delivered_via``."""
    from clawmetry import detectors as _det
    # Local wall-clock ISO, the form the store writes and _seconds_since reads.
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    inc = _incident()

    class EmitStore(LatchStore):
        def __init__(self):
            super().__init__()
            self.signals = []

        def query_sessions_table(self, limit=300):
            return [{"session_id": "codex:abc", "agent_type": "codex",
                     "started_at": now_iso, "last_active_at": now_iso,
                     "status": "active", "cost_usd": 2.0, "metadata": {}}]

        def query_events(self, **kw):
            return [{"event_type": "tool_call", "ts": now_iso, "data": {"tool": "x"}}]

        def query_approvals(self, **kw):
            return []

        def ingest_loop_signal(self, **kw):
            self.signals.append(kw)

        def __getattr__(self, name):  # baseline / observation / prune: no-ops
            return lambda *a, **k: None

    monkeypatch.setattr(_det, "run_all", lambda *a, **k: [dict(inc)])
    delivered = []

    def fake_deliver(store, incident, **kw):
        delivered.append((incident["kind"], kw.get("source")))
        return {"delivered": True, "delivered_via": ["banner", "telegram"], "reason": "alerted"}

    monkeypatch.setattr(ia, "deliver_incident", fake_deliver)
    monkeypatch.setattr(_sync, "_apply_guard_policies", lambda *a, **k: 0)
    store = EmitStore()
    n = _sync._emit_detector_incidents(store, {})
    assert n == 1
    assert delivered == [("rate_limited", "detector")]
    assert store.signals[0]["details"]["delivered_via"] == ["banner", "telegram"]
    assert store.signals[0]["signature"] == "daemon_detect_rate_limited"


def test_builtin_monitor_is_listed_so_the_alerts_tab_can_explain_it():
    from routes.alerts import BUILTIN_MONITORS
    m = next(x for x in BUILTIN_MONITORS if x["alert_type"] == ia.ALERT_TYPE)
    assert m["label"] == "Agent needs attention"
