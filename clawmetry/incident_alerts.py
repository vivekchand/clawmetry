"""clawmetry/incident_alerts.py: deliver a detector incident to a human.

Before this module a Guard detector could see an agent stuck, rate limited,
crashed or waiting on you, write a ``loop_signals`` row, and stop. A policy
whose action was ``alert`` recorded "no action for this policy type". Nothing
reached a person unless they happened to be looking at the Guard tab.

This closes that gap with the SAME delivery surfaces the budget monitor and the
built-in monitors already use, so what the Alerts tab shows as "where does
this go" is what actually fires:

* **banner** (always): one ``alert_history`` row per channel in the fleet
  SQLite DB, which the dashboard's red banner + bell poll. Free.
* **telegram**: the direct Bot API, creds from the Notifications tab file or
  the legacy budget config, exactly like ``dashboard._telegram_creds``. Free,
  matching the budget path (budget alerts have always gone banner+telegram
  with no entitlement check).
* **slack / discord / webhook**: URLs from the same alerts config file, gated
  on the ``alert_webhooks`` entitlement, the gate the daemon's local alert
  path already applies to webhooks.

Operators mute or pin channels per monitor in ``~/.clawmetry/builtin_monitors.json``
(the ``agent_attention`` monitor), the same prefs the Alerts tab writes.

Dedup: one delivery per (session, kind) per ``cooldown_sec`` (30 min default),
latched in DuckDB (``incident_alerts``) so a daemon restart does not re-fire
every channel. The latch row also records ``delivered_via``.

Works from either process. Inside the dashboard it calls the dashboard's own
senders; inside the daemon (where ``dashboard`` is not imported) it uses
equivalent minimal senders that read the same config files and produce the
same payload shapes.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
import time
import urllib.request
from typing import Any, Optional

log = logging.getLogger("clawmetry.incident_alerts")

#: The built-in monitor id these incidents fire under (routes/alerts.py
#: BUILTIN_MONITORS + the prefs file key).
ALERT_TYPE = "agent_attention"

DEFAULT_COOLDOWN_SEC = int(os.environ.get("CLAWMETRY_INCIDENT_ALERT_COOLDOWN_SEC", "1800"))

#: Severities that reach a human on their own. ``info`` is a hint, not a page.
DELIVER_SEVERITIES = frozenset({"warning", "critical"})

#: Channels free on every plan (mirrors the budget monitor's hardcoded pair).
FREE_CHANNELS = frozenset({"banner", "telegram"})
#: Channels that need the ``alert_webhooks`` entitlement.
GATED_CHANNELS = frozenset({"slack", "discord", "webhook"})

_ALERTS_CONFIG_FILE = os.path.expanduser("~/.openclaw/clawmetry-alerts.json")
_BUILTIN_PREFS_FILE = os.path.expanduser("~/.clawmetry/builtin_monitors.json")
_HTTP_TIMEOUT = 10

# Plain words per kind for the message a person reads on their phone.
KIND_HEADLINE = {
    "stuck_loop": "is repeating itself",
    "no_progress": "is busy but not finishing",
    "repeated_tool_failure": "keeps failing the same step",
    "action_discrepancy": "carried on after a failure",
    "file_blast_radius": "changed a lot of files at once",
    "credential_access": "opened a password or key file",
    "network_egress": "contacted somewhere new",
    "privilege_change": "asked for admin rights",
    "rate_limited": "is being rate limited",
    "blocked_on_user": "is waiting for you",
    "crashed": "crashed and restarted",
}


# ── Config readers (same files the dashboard reads) ─────────────────────────

def _dashboard():
    """The dashboard module when it is ALREADY loaded in this process.

    Never imports it: from the daemon that would pull a 17k-line Flask app
    into a process that only needs four senders."""
    return sys.modules.get("dashboard")


def _load_alerts_config() -> dict:
    d = _dashboard()
    if d is not None and hasattr(d, "_load_alerts_webhook_config"):
        try:
            cfg = d._load_alerts_webhook_config()
            if isinstance(cfg, dict):
                return cfg
        except Exception:
            pass
    try:
        with open(_ALERTS_CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _fleet_db_path() -> str:
    # The env override wins everywhere (sync._local_alerts_fleet_db_path does
    # the same): the dashboard's FLEET_DB_PATH is frozen at import, so asking
    # it first would ignore an override set after it loaded.
    env = (os.environ.get("CLAWMETRY_FLEET_DB") or "").strip()
    if env:
        return os.path.expanduser(env)
    d = _dashboard()
    if d is not None and hasattr(d, "_fleet_db_path"):
        try:
            p = d._fleet_db_path()
            if p:
                return str(p)
        except Exception:
            pass
    preferred = os.path.expanduser("~/.clawmetry")
    try:
        os.makedirs(preferred, exist_ok=True)
    except OSError:
        pass
    if os.path.isdir(preferred):
        return os.path.join(preferred, "fleet.db")
    return os.path.expanduser("~/.clawmetry-fleet.db")


def _budget_config() -> dict:
    """Legacy budget config (fleet SQLite ``budget_config`` key/value)."""
    d = _dashboard()
    if d is not None and hasattr(d, "_get_budget_config"):
        try:
            cfg = d._get_budget_config()
            if isinstance(cfg, dict):
                return cfg
        except Exception:
            pass
    try:
        path = _fleet_db_path()
        if not os.path.exists(path):
            return {}
        db = sqlite3.connect(path, timeout=5)
        try:
            rows = db.execute("SELECT key, value FROM budget_config").fetchall()
        finally:
            db.close()
        return {str(k): v for k, v in rows}
    except Exception:
        return {}


def telegram_creds() -> tuple[str, str]:
    """(bot_token, chat_id) from either store, like ``dashboard._telegram_creds``."""
    for loader in (_load_alerts_config, _budget_config):
        try:
            cfg = loader()
            tok = str(cfg.get("telegram_bot_token", "") or "").strip()
            cid = str(cfg.get("telegram_chat_id", "") or "").strip()
            if tok and cid:
                return tok, cid
        except Exception:
            continue
    return "", ""


def _load_prefs() -> dict:
    try:
        with open(_BUILTIN_PREFS_FILE) as f:
            data = json.load(f)
        prefs = data.get(ALERT_TYPE) if isinstance(data, dict) else None
        return prefs if isinstance(prefs, dict) else {}
    except Exception:
        return {}


def _webhooks_entitled() -> bool:
    try:
        from clawmetry import entitlements as _ent
        return bool(_ent.get_entitlement().allows_feature("alert_webhooks"))
    except Exception:
        return False


def resolve_delivery() -> dict:
    """``{"enabled", "channels", "mode", "gated_off"}`` for the monitor.

    Same answer the Alerts tab shows: every channel this process can deliver
    to right now (in-app always; Telegram when creds exist; Slack/Discord/
    webhook when a URL exists AND the node is entitled), intersected with the
    operator's pinned list when one is set. ``gated_off`` names configured
    sinks that were dropped for lack of entitlement, so the caller can say so
    instead of silently not sending."""
    prefs = _load_prefs()
    cfg = _load_alerts_config()
    available = ["banner"]
    tok, cid = telegram_creds()
    if tok and cid:
        available.append("telegram")
    gated_off: list[str] = []
    entitled = None
    for ch, key in (("slack", "slack_webhook_url"),
                    ("discord", "discord_webhook_url"),
                    ("webhook", "webhook_url")):
        if not str(cfg.get(key, "") or "").strip():
            continue
        if entitled is None:
            entitled = _webhooks_entitled()
        if entitled:
            available.append(ch)
        else:
            gated_off.append(ch)
    pinned = prefs.get("channels")
    if isinstance(pinned, list):
        chans = [c for c in available if c in pinned or c == "banner"]
        mode = "custom"
    else:
        chans, mode = list(available), "auto"
    return {"enabled": bool(prefs.get("enabled", True)),
            "channels": chans, "mode": mode, "gated_off": gated_off}


# ── Senders ─────────────────────────────────────────────────────────────────

def _post_json(url: str, payload: dict) -> bool:
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "User-Agent": "clawmetry"})
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            status = getattr(resp, "status", None) or 200
            return 200 <= int(status) < 300
    except Exception as e:
        log.warning("incident alert POST failed (%s): %s", url[:40], e)
        return False


def send_telegram(message: str) -> bool:
    d = _dashboard()
    if d is not None and hasattr(d, "_send_telegram_alert"):
        try:
            d._send_telegram_alert(message)
            tok, cid = telegram_creds()
            return bool(tok and cid)
        except Exception:
            return False
    tok, cid = telegram_creds()
    if not (tok and cid):
        return False
    return _post_json(
        f"https://api.telegram.org/bot{tok}/sendMessage",
        {"chat_id": cid, "text": f"[ClawMetry Alert] {message}"})


def send_slack(message: str, severity: str, title: str) -> bool:
    d = _dashboard()
    if d is not None and hasattr(d, "_send_slack_alert"):
        try:
            d._send_slack_alert(message, severity=severity, title=title)
            return True
        except Exception:
            return False
    url = str(_load_alerts_config().get("slack_webhook_url", "") or "").strip()
    if not url:
        return False
    color = {"critical": "#dc2626", "warning": "#f59e0b"}.get(severity, "#3b82f6")
    return _post_json(url, {"attachments": [{
        "color": color, "title": title, "text": message, "footer": "ClawMetry",
        "ts": int(time.time()),
        "fields": [{"title": "Severity", "value": severity.upper(), "short": True}],
    }]})


def send_discord(message: str, severity: str, title: str) -> bool:
    d = _dashboard()
    if d is not None and hasattr(d, "_send_discord_alert"):
        try:
            d._send_discord_alert(message, severity=severity, title=title)
            return True
        except Exception:
            return False
    url = str(_load_alerts_config().get("discord_webhook_url", "") or "").strip()
    if not url:
        return False
    color = {"critical": 14423100, "warning": 16023040}.get(severity, 3901635)
    return _post_json(url, {"embeds": [{
        "title": title, "description": message, "color": color,
        "fields": [{"name": "Severity", "value": severity.upper(), "inline": True}],
        "footer": {"text": "ClawMetry"},
    }]})


def send_webhook(payload: dict) -> bool:
    url = str(_load_alerts_config().get("webhook_url", "") or "").strip()
    if not url:
        return False
    d = _dashboard()
    if d is not None and hasattr(d, "_send_webhook_alert"):
        try:
            d._send_webhook_alert(url, payload, payload_type="generic")
            return True
        except Exception:
            return False
    return _post_json(url, payload)


def persist_banner(rule_id: str, message: str, channels: list[str],
                   alert_type: str = ALERT_TYPE) -> bool:
    """One ``alert_history`` row per channel in the fleet SQLite DB: the
    exact table ``dashboard._fire_alert`` writes and the banner + bell read.
    Never raises; True on success."""
    try:
        db = sqlite3.connect(_fleet_db_path(), timeout=10)
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    fired_at REAL NOT NULL,
                    acknowledged INTEGER DEFAULT 0,
                    ack_at REAL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_alert_history_fired "
                       "ON alert_history(fired_at DESC)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_alert_history_rule "
                       "ON alert_history(rule_id, fired_at DESC)")
            now = time.time()
            for ch in channels or ["banner"]:
                db.execute(
                    "INSERT INTO alert_history (rule_id, type, message, channel, fired_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (rule_id, alert_type, str(message)[:500], ch, now))
            db.commit()
        finally:
            db.close()
        return True
    except Exception as e:
        log.warning("incident alert banner persist failed: %s", e)
        return False


# ── Message ─────────────────────────────────────────────────────────────────

def compose_message(incident: dict) -> str:
    """Plain-words message for a person. No internal ids up front, no jargon,
    the money when we know it, and what to do."""
    kind = str(incident.get("kind") or "")
    runtime = str(incident.get("runtime") or "agent").replace("_", " ")
    head = KIND_HEADLINE.get(kind)
    sev = str(incident.get("severity") or "warning")
    parts = []
    if head:
        parts.append(f"Your {runtime} agent {head}.")
    else:
        parts.append(str(incident.get("title") or f"Your {runtime} agent needs attention."))
    detail = str(incident.get("detail") or "").strip()
    if detail:
        parts.append(detail)
    try:
        risk = float(incident.get("spend_at_risk_usd") or 0)
    except (TypeError, ValueError):
        risk = 0.0
    basis = str(incident.get("spend_basis") or "unknown")
    if risk > 0 and basis != "unknown":
        parts.append(f"About ${risk:.2f} at risk so far.")
    sid = str(incident.get("session_id") or "")
    if sid:
        parts.append(f"Session {sid[:24]}.")
    msg = " ".join(parts)
    if sev == "critical":
        msg = "CRITICAL: " + msg
    return msg[:1500]


# ── Main entry point ────────────────────────────────────────────────────────

def deliver_incident(store: Any, incident: dict, *,
                     source: str = "detector",
                     force: bool = False,
                     cooldown_sec: Optional[int] = None,
                     policy_id: str = "") -> dict:
    """Fan one incident out to the humans configured for it.

    Returns ``{"delivered": bool, "delivered_via": [...], "reason": str,
    "gated_off": [...]}``. ``reason`` is plain text suitable for a
    ``policy_actions.result_detail`` cell ("alerted via banner, telegram" /
    "already alerted 4 min ago" / "muted by operator").

    * ``force`` (a policy said ``alert``) skips the severity floor but never
      the cooldown latch or the operator's mute.
    * The latch lives in DuckDB (``store.incident_alert_last_sent`` /
      ``record_incident_alert``); a store without those methods degrades to
      an in-process memo so an older daemon still delivers once.
    Never raises.
    """
    out = {"delivered": False, "delivered_via": [], "reason": "", "gated_off": []}
    try:
        if not isinstance(incident, dict):
            out["reason"] = "no incident"
            return out
        sid = str(incident.get("session_id") or "")
        kind = str(incident.get("kind") or "")
        sev = str(incident.get("severity") or "warning").lower()
        if not sid or not kind:
            out["reason"] = "incident has no session or kind"
            return out
        if not force and sev not in DELIVER_SEVERITIES:
            out["reason"] = f"severity {sev} is below the alert floor (warning)"
            return out

        cd = DEFAULT_COOLDOWN_SEC if cooldown_sec is None else max(0, int(cooldown_sec))
        last_ms = _last_sent(store, sid, kind)
        now_ms = int(time.time() * 1000)
        if cd > 0 and last_ms and (now_ms - last_ms) < cd * 1000:
            ago = max(1, int((now_ms - last_ms) / 60000))
            out["reason"] = f"already alerted {ago} min ago (cooldown {cd // 60} min)"
            return out

        delivery = resolve_delivery()
        out["gated_off"] = list(delivery.get("gated_off") or [])
        if not delivery.get("enabled", True):
            out["reason"] = "muted by operator (Alerts tab, Agent needs attention)"
            return out
        channels = list(delivery.get("channels") or ["banner"])

        message = compose_message(incident)
        title = f"ClawMetry Alert [{ALERT_TYPE}]"
        rule_id = f"{ALERT_TYPE}:{kind}" + (f":{policy_id}" if policy_id else "")

        via: list[str] = []
        # Literal alert_type on purpose: tests/test_builtin_monitors.py scrapes
        # call sites so the Alerts tab's monitor list cannot drift from code.
        if persist_banner(rule_id, message, channels, alert_type="agent_attention"):
            via.append("banner")
        if "telegram" in channels and send_telegram(message):
            via.append("telegram")
        if "slack" in channels and send_slack(message, sev, title):
            via.append("slack")
        if "discord" in channels and send_discord(message, sev, title):
            via.append("discord")
        if "webhook" in channels:
            payload = {
                "type": ALERT_TYPE, "kind": kind, "title": title,
                "message": message, "severity": sev,
                "session_id": sid, "runtime": incident.get("runtime"),
                "spend_at_risk_usd": incident.get("spend_at_risk_usd"),
                "spend_basis": incident.get("spend_basis"),
                "evidence": incident.get("evidence"),
                "source": source, "policy_id": policy_id or None,
                "timestamp": time.time(),
            }
            if send_webhook(payload):
                via.append("webhook")

        if not via:
            out["reason"] = "no channel accepted the alert (banner write failed)"
            return out
        _record(store, sid, kind, via, sev)
        out["delivered"] = True
        out["delivered_via"] = via
        reason = "alerted via " + ", ".join(via)
        if out["gated_off"]:
            reason += " (" + ", ".join(out["gated_off"]) + " configured but not on this plan)"
        out["reason"] = reason
        log.info("incident alert: %s %s -> %s", sid[:24], kind, ", ".join(via))
        return out
    except Exception as e:  # noqa: BLE001
        out["reason"] = f"alert failed: {type(e).__name__}"
        log.warning("incident alert failed: %s", e)
        return out


_MEMO: dict = {}


def _last_sent(store: Any, sid: str, kind: str) -> int:
    fn = getattr(store, "incident_alert_last_sent", None)
    if callable(fn):
        # Keyword args on purpose: the dashboard's _ProxyStore forwards
        # kwargs only and silently drops positionals.
        try:
            return int(fn(session_id=sid, kind=kind) or 0)
        except Exception:
            pass
    return int(_MEMO.get((sid, kind)) or 0)


def _record(store: Any, sid: str, kind: str, via: list, sev: str) -> None:
    _MEMO[(sid, kind)] = int(time.time() * 1000)
    fn = getattr(store, "record_incident_alert", None)
    if callable(fn):
        try:
            fn(session_id=sid, kind=kind, delivered_via=via, severity=sev)
        except Exception:
            pass
