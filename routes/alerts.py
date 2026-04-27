"""
routes/alerts.py — Budget + Alerts endpoints.

Extracted from dashboard.py as Phase 5.6 of the incremental modularisation.
Owns the 6 routes registered on ``bp_budget`` plus the 10 routes registered on
``bp_alerts``:

  bp_budget:
    GET/POST /api/budget/config         — get or update budget configuration
    GET      /api/budget/status         — current budget status with spending totals
    POST     /api/budget/auto-pause     — set absolute daily auto-pause threshold
    POST     /api/budget/pause          — manually pause the gateway
    POST     /api/budget/resume         — resume the gateway after a budget pause
    POST     /api/budget/test-telegram  — send a test Telegram notification

  bp_alerts:
    GET/POST /api/alerts/rules                     — list or create alert rules
    PUT/DEL  /api/alerts/rules/<rule_id>           — update or delete a rule
    GET      /api/alerts/history                   — alert history
    POST     /api/alerts/history/<int>/ack         — acknowledge an alert
    GET      /api/alerts/active                    — active (unacknowledged) alerts
    GET/POST /api/alerts/webhook                   — get/update outgoing webhook config
    POST     /api/alerts/webhook/test              — test payload to configured webhooks
    GET      /api/alerts/velocity                  — real-time token velocity status
    GET/POST /api/alert-channels                   — alert channel configuration (GH#204)
    POST     /api/alert-channels/test              — test alert to configured channels

Module-level helpers (``_get_budget_config``, ``_set_budget_config``,
``_get_budget_status``, ``_pause_gateway``, ``_resume_gateway``,
``_budget_paused``, ``_budget_paused_at``, ``_budget_paused_reason``,
``_fleet_db``, ``_fleet_db_lock``, ``_get_alert_rules``, ``_get_alert_history``,
``_get_active_alerts``, ``_load_alerts_webhook_config``,
``_save_alerts_webhook_config``, ``_send_webhook_alert``, ``_send_slack_alert``,
``_send_discord_alert``, ``_compute_velocity_status``) stay in ``dashboard.py``
and are reached via late ``import dashboard as _d``. Pure mechanical move —
zero behaviour change.
"""

import json
import time

from flask import Blueprint, jsonify, request

bp_budget = Blueprint('budget', __name__)
bp_alerts = Blueprint('alerts', __name__)


# ── Budget API Routes ───────────────────────────────────────────────────


@bp_budget.route("/api/budget/config", methods=["GET", "POST"])
def api_budget_config():
    """Get or update budget configuration."""
    import dashboard as _d
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        allowed = [
            "daily_limit",
            "weekly_limit",
            "monthly_limit",
            "auto_pause_enabled",
            "auto_pause_threshold_pct",
            "auto_pause_threshold_usd",
            "auto_pause_action",
            "warning_threshold_pct",
            "telegram_bot_token",
            "telegram_chat_id",
        ]
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return jsonify({"error": "No valid fields provided"}), 400
        _d._set_budget_config(updates)
        return jsonify({"ok": True})
    return jsonify(_d._get_budget_config())


@bp_budget.route("/api/budget/status")
def api_budget_status():
    """Get current budget status with spending totals."""
    import dashboard as _d
    return jsonify(_d._get_budget_status())


@bp_budget.route("/api/budget/auto-pause", methods=["POST"])
def api_budget_auto_pause():
    """Set absolute daily auto-pause/alert threshold."""
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    threshold = data.get("threshold_usd")
    action = str(data.get("action", "pause")).strip().lower()
    if action not in ("pause", "alert"):
        return jsonify({"ok": False, "error": "action must be 'pause' or 'alert'"}), 400
    try:
        threshold_val = float(threshold)
    except Exception:
        return jsonify({"ok": False, "error": "threshold_usd must be a number"}), 400
    if threshold_val < 0:
        return jsonify({"ok": False, "error": "threshold_usd must be >= 0"}), 400
    _d._set_budget_config(
        {"auto_pause_threshold_usd": threshold_val, "auto_pause_action": action}
    )
    return jsonify({"ok": True, "threshold_usd": threshold_val, "action": action})


@bp_budget.route("/api/budget/pause", methods=["POST"])
def api_budget_pause():
    """Manually pause the gateway."""
    import dashboard as _d
    _d._budget_paused = True
    _d._budget_paused_at = time.time()
    _d._budget_paused_reason = "Manually paused from dashboard"
    _d._pause_gateway()
    return jsonify({"ok": True, "paused": True})


@bp_budget.route("/api/budget/resume", methods=["POST"])
def api_budget_resume():
    """Resume the gateway after budget pause."""
    import dashboard as _d
    _d._resume_gateway()
    return jsonify({"ok": True, "paused": False})


@bp_budget.route("/api/budget/test-telegram", methods=["POST"])
def api_budget_test_telegram():
    """Send a test Telegram notification using saved config."""
    import dashboard as _d
    cfg = _d._get_budget_config()
    token = str(cfg.get("telegram_bot_token", "")).strip()
    chat_id = str(cfg.get("telegram_chat_id", "")).strip()
    if not token or not chat_id:
        return jsonify(
            {"ok": False, "error": "Set Telegram bot token and chat ID first"}
        ), 400
    try:
        import urllib.request

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps(
            {
                "chat_id": chat_id,
                "text": "\u2705 *ClawMetry Budget Alerts* - Test notification successful!",
                "parse_mode": "Markdown",
            }
        ).encode()
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── Alerts API Routes ───────────────────────────────────────────────────


@bp_alerts.route("/api/alerts/rules", methods=["GET", "POST"])
def api_alert_rules():
    """List or create alert rules."""
    import dashboard as _d
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        rtype = data.get("type", "")
        threshold = data.get("threshold", 0)
        channels = data.get("channels", ["banner"])
        cooldown = data.get("cooldown_min", 30)
        enabled = data.get("enabled", True)
        if rtype not in ("threshold", "spike", "token_spike", "anomaly", "agent_down"):
            return jsonify({"error": "Invalid alert type"}), 400
        if not isinstance(threshold, (int, float)) or threshold <= 0:
            return jsonify({"error": "Threshold must be a positive number"}), 400
        import uuid

        rule_id = str(uuid.uuid4())[:8]
        now = time.time()
        with _d._fleet_db_lock:
            db = _d._fleet_db()
            db.execute(
                "INSERT INTO alert_rules (id, type, threshold, channels, cooldown_min, enabled, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    rule_id,
                    rtype,
                    threshold,
                    json.dumps(channels),
                    cooldown,
                    1 if enabled else 0,
                    now,
                    now,
                ),
            )
            db.commit()
            db.close()
        return jsonify({"ok": True, "id": rule_id})
    return jsonify({"rules": _d._get_alert_rules()})


@bp_alerts.route("/api/alerts/rules/<rule_id>", methods=["PUT", "DELETE"])
def api_alert_rule(rule_id):
    """Update or delete an alert rule."""
    import dashboard as _d
    if request.method == "DELETE":
        with _d._fleet_db_lock:
            db = _d._fleet_db()
            db.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
            db.commit()
            db.close()
        return jsonify({"ok": True})
    # PUT
    data = request.get_json(silent=True) or {}
    sets = []
    vals = []
    for field in ["threshold", "cooldown_min", "enabled"]:
        if field in data:
            sets.append(f"{field} = ?")
            vals.append(
                data[field] if field != "enabled" else (1 if data[field] else 0)
            )
    if "channels" in data:
        sets.append("channels = ?")
        vals.append(json.dumps(data["channels"]))
    if not sets:
        return jsonify({"error": "No fields to update"}), 400
    sets.append("updated_at = ?")
    vals.append(time.time())
    vals.append(rule_id)
    with _d._fleet_db_lock:
        db = _d._fleet_db()
        db.execute(f"UPDATE alert_rules SET {', '.join(sets)} WHERE id = ?", vals)
        db.commit()
        db.close()
    return jsonify({"ok": True})


@bp_alerts.route("/api/alerts/history")
def api_alert_history():
    """Get alert history."""
    import dashboard as _d
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"alerts": _d._get_alert_history(limit)})


@bp_alerts.route("/api/alerts/history/<int:alert_id>/ack", methods=["POST"])
def api_alert_ack(alert_id):
    """Acknowledge an alert."""
    import dashboard as _d
    with _d._fleet_db_lock:
        db = _d._fleet_db()
        db.execute(
            "UPDATE alert_history SET acknowledged = 1, ack_at = ? WHERE id = ?",
            (time.time(), alert_id),
        )
        db.commit()
        db.close()
    return jsonify({"ok": True})


@bp_alerts.route("/api/alerts/active")
def api_alerts_active():
    """Get active (unacknowledged) alerts."""
    import dashboard as _d
    return jsonify({"alerts": _d._get_active_alerts()})


@bp_alerts.route("/api/alerts/webhook", methods=["GET", "POST"])
def api_alerts_webhook():
    """Get or update outgoing webhook configuration."""
    import dashboard as _d
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        allowed = {
            "webhook_url",
            "slack_webhook_url",
            "discord_webhook_url",
            "cost_spike_alerts",
            "agent_error_rate_alerts",
            "security_posture_changes",
        }
        updates = {k: data[k] for k in data if k in allowed}
        cfg = _d._save_alerts_webhook_config(updates)
        return jsonify({"ok": True, "config": cfg})
    return jsonify(_d._load_alerts_webhook_config())


@bp_alerts.route("/api/alerts/webhook/test", methods=["POST"])
def api_alerts_webhook_test():
    """Send a test payload to configured outgoing webhooks."""
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    target = str(data.get("target", "all")).strip().lower()
    cfg = _d._load_alerts_webhook_config()
    payload = {
        "type": "test_alert",
        "agent": "main",
        "cost_usd": 0,
        "threshold": 0,
        "timestamp": time.time(),
        "message": "ClawMetry webhook test alert",
    }
    sent = []
    if target in ("all", "generic"):
        url = str(cfg.get("webhook_url", "")).strip()
        if url:
            _d._send_webhook_alert(url, payload, payload_type="generic")
            sent.append("generic")
    if target in ("all", "slack"):
        url = str(cfg.get("slack_webhook_url", "")).strip()
        if url:
            _d._send_webhook_alert(url, payload, payload_type="slack")
            sent.append("slack")
    if target in ("all", "discord"):
        url = str(cfg.get("discord_webhook_url", "")).strip()
        if url:
            _d._send_webhook_alert(url, payload, payload_type="discord")
            sent.append("discord")
    if not sent:
        return jsonify(
            {"ok": False, "error": "No configured webhook URL for selected target"}
        ), 400
    return jsonify({"ok": True, "sent": sent})


@bp_alerts.route("/api/alerts/velocity")
def api_alerts_velocity():
    """Real-time token velocity status — detects runaway agent loops.

    Returns whether any velocity threshold is currently exceeded:
      - tokensIn2Min: tokens consumed in last 2-min sliding window
      - costPerMin: estimated USD/min burn rate
      - maxConsecutiveTools: longest consecutive tool-call chain
      - active: True if any threshold is breached
      - reasons: human-readable list of triggered thresholds
    """
    import dashboard as _d
    return jsonify(_d._compute_velocity_status())


@bp_alerts.route("/api/alert-channels", methods=["GET", "POST"])
def api_alert_channels():
    """GET/POST alert channel configuration (webhook, Slack, Discord, severity filter).

    This is the canonical endpoint for GH#204 alerting integrations.
    GET  -> returns current config (webhook_url, slack_webhook_url, discord_webhook_url, min_severity, toggles)
    POST -> saves config; accepts any subset of fields
    """
    import dashboard as _d
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        allowed = {
            "webhook_url",
            "slack_webhook_url",
            "discord_webhook_url",
            "cost_spike_alerts",
            "agent_error_rate_alerts",
            "security_posture_changes",
            "min_severity",
        }
        updates = {k: data[k] for k in data if k in allowed}
        cfg = _d._save_alerts_webhook_config(updates)
        return jsonify({"ok": True, "config": cfg})
    return jsonify(_d._load_alerts_webhook_config())


@bp_alerts.route("/api/alert-channels/test", methods=["POST"])
def api_alert_channels_test():
    """Send a test alert to one or all configured channels.

    Body: { "target": "all" | "slack" | "discord" | "generic", "severity": "warning" | "critical" }
    """
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    target = str(data.get("target", "all")).strip().lower()
    severity = str(data.get("severity", "warning")).strip().lower()
    cfg = _d._load_alerts_webhook_config()
    sent = []
    title = "ClawMetry Test Alert"
    message = "This is a test alert from ClawMetry webhook integrations."

    if target in ("all", "generic"):
        url = str(cfg.get("webhook_url", "")).strip()
        if url:
            _d._send_webhook_alert(
                url,
                {"type": "test", "title": title, "message": message, "severity": severity},
                payload_type="generic",
            )
            sent.append("generic")
    if target in ("all", "slack"):
        url = str(cfg.get("slack_webhook_url", "")).strip()
        if url:
            _d._send_slack_alert(message, severity=severity, title=title)
            sent.append("slack")
    if target in ("all", "discord"):
        url = str(cfg.get("discord_webhook_url", "")).strip()
        if url:
            _d._send_discord_alert(message, severity=severity, title=title)
            sent.append("discord")

    if not sent:
        return jsonify({"ok": False, "error": "No configured webhook URL for selected target"}), 400
    return jsonify({"ok": True, "sent": sent})
