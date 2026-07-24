"""routes/questions.py — human-in-the-loop questions API (bp_questions).

The dashboard surface of the ask/notify engine in
``clawmetry/questions.py``: a unified inbox of agent questions (confirm /
select / input), answer + cancel endpoints usable from the Approvals tab,
Slack link buttons, and phone-push action buttons, plus the operator kill
switch, delivery-channel configuration, and the decision audit trail.

Routes:
  POST /api/questions/ask               — create a question (agents / hooks)
  GET  /api/questions                   — inbox (pending + recent)
  GET  /api/questions/<qid>             — one question; ?wait_ms= long-polls
  POST /api/questions/<qid>/answer      — answer (GET supported for link buttons)
  POST /api/questions/<qid>/cancel      — cancel a pending question
  GET  /api/questions/audit             — audit trail (+ ?format=csv export)
  GET/POST /api/questions/channels      — delivery channels + mode config
  POST /api/questions/channels/test     — send a test notification
  GET/POST /api/killswitch              — operator kill switch (global/session)
"""

from __future__ import annotations

import csv
import io
import json
import logging

from flask import Blueprint, Response, jsonify, request

log = logging.getLogger("clawmetry-questions-api")

bp_questions = Blueprint("questions", __name__)

_MAX_WAIT_MS = 55_000  # long-poll cap, mirrors the MCP blocking-wait cap


def _engine():
    from clawmetry import questions as _q
    return _q


# ── Ask / inbox / answer ─────────────────────────────────────────────────


@bp_questions.route("/api/questions/ask", methods=["POST"])
def questions_ask():
    """Create a question. Body mirrors the MCP ask_user tool:
    {question, type, options, placeholder, context, agent_name,
     session_id, wait (bool), timeout_ms}."""
    q = _engine()
    data = request.get_json(force=True, silent=True) or {}
    try:
        row = q.create_question(
            question=data.get("question") or "",
            qtype=(data.get("type") or data.get("qtype") or "confirm").strip().lower(),
            options=data.get("options"),
            placeholder=data.get("placeholder") or "",
            context=data.get("context") or "",
            agent_name=data.get("agent_name") or data.get("agentName") or "",
            session_id=data.get("session_id") or "",
            source=data.get("source") or "api",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if data.get("wait"):
        timeout_ms = min(int(data.get("timeout_ms") or 30_000), _MAX_WAIT_MS)
        result = q.wait_for_answer(row["id"], timeout_s=timeout_ms / 1000.0)
        result["question"] = row
        return jsonify(result)
    return jsonify({
        "correlationId": row["id"],
        "status": "pending",
        "expires_at": row.get("expires_at"),
        "notified_channels": row.get("notified_channels", []),
        "question": row,
    })


@bp_questions.route("/api/questions", methods=["GET"])
def questions_list():
    """Unified inbox: pending questions plus recent history."""
    q = _engine()
    status = (request.args.get("status") or "").strip() or None
    session_id = (request.args.get("session_id") or "").strip() or None
    try:
        limit = max(1, min(int(request.args.get("limit") or 100), 500))
    except ValueError:
        limit = 100
    rows = q.list_questions(status=status, session_id=session_id, limit=limit)
    pending = [r for r in rows if r.get("status") == "pending"]
    return jsonify({
        "questions": rows,
        "count": len(rows),
        "pending_count": len(pending),
        "killswitch": q.killswitch_state(),
        "mode": q.load_mode(),
    })


@bp_questions.route("/api/questions/audit", methods=["GET"])
def questions_audit():
    """Every decision, frozen: what was asked, who answered, when, and
    how long it took. ``?format=csv`` exports the trail."""
    q = _engine()
    try:
        limit = max(1, min(int(request.args.get("limit") or 200), 1000))
    except ValueError:
        limit = 200
    rows = q.list_questions(limit=limit)
    summary = {"total": len(rows)}
    for r in rows:
        summary[r.get("status") or "unknown"] = summary.get(r.get("status") or "unknown", 0) + 1
    if (request.args.get("format") or "").lower() == "csv":
        buf = io.StringIO()
        cols = ["id", "created_at", "agent_name", "session_id", "source",
                "qtype", "question", "status", "answer", "answered_by",
                "answered_at", "latency_ms"]
        w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in cols})
        return Response(
            buf.getvalue(), mimetype="text/csv",
            headers={"Content-Disposition":
                     "attachment; filename=clawmetry-questions-audit.csv"})
    return jsonify({"decisions": rows, "summary": summary})


@bp_questions.route("/api/questions/<qid>", methods=["GET"])
def questions_get(qid: str):
    """One question. ``?wait_ms=N`` long-polls (max 55 s) so agents can
    block on the answer — the wait_for_answer path over HTTP."""
    q = _engine()
    wait_ms = 0
    try:
        wait_ms = min(max(int(request.args.get("wait_ms") or 0), 0), _MAX_WAIT_MS)
    except ValueError:
        wait_ms = 0
    if wait_ms:
        result = q.wait_for_answer(qid, timeout_s=wait_ms / 1000.0)
        result["question"] = q.get_question(qid)
        return jsonify(result)
    row = q.get_question(qid)
    if not row:
        return jsonify({"error": "not_found"}), 404
    return jsonify(row)


@bp_questions.route("/api/questions/<qid>/answer", methods=["POST", "GET"])
def questions_answer(qid: str):
    """Record an answer. POST body {value, answered_by}; GET with
    ?value= supports Slack link buttons and phone-push tap actions, and
    returns a tiny HTML confirmation instead of JSON."""
    q = _engine()
    if request.method == "GET":
        value = request.args.get("value") or ""
        result = q.answer_question(qid, value, answered_by="link")
        ok = result.get("ok") and not result.get("error")
        msg = ("Answer recorded — the agent will continue." if ok and not result.get("already")
               else "This question was already resolved." if result.get("already")
               else f"Could not record answer: {result.get('error', 'unknown')}")
        return Response(
            f"<html><body style='font-family:sans-serif;padding:40px;text-align:center'>"
            f"<h2>ClawMetry</h2><p>{msg}</p></body></html>",
            mimetype="text/html",
            status=200 if ok or result.get("already") else 400)
    data = request.get_json(force=True, silent=True) or {}
    value = data.get("value")
    if value is None:
        value = data.get("answer") or data.get("decision") or ""
    result = q.answer_question(
        qid, str(value), answered_by=data.get("answered_by") or "operator")
    if not result.get("ok"):
        status = 404 if result.get("error") == "not_found" else 400
        return jsonify(result), status
    return jsonify(result)


@bp_questions.route("/api/questions/<qid>/cancel", methods=["POST"])
def questions_cancel(qid: str):
    q = _engine()
    data = request.get_json(force=True, silent=True) or {}
    return jsonify(q.cancel_question(qid, actor=data.get("actor") or "agent"))


# ── Kill switch ──────────────────────────────────────────────────────────


@bp_questions.route("/api/killswitch", methods=["GET"])
def killswitch_get():
    return jsonify(_engine().killswitch_state())


@bp_questions.route("/api/killswitch", methods=["POST"])
def killswitch_set():
    """Engage/release: {engaged: bool, session_id?, reason?, actor?}.
    While engaged, every gated tool call is denied until released."""
    q = _engine()
    data = request.get_json(force=True, silent=True) or {}
    if "engaged" not in data:
        return jsonify({"error": "engaged (bool) required"}), 400
    state = q.set_killswitch(
        engaged=bool(data.get("engaged")),
        session_id=(data.get("session_id") or "").strip() or None,
        reason=(data.get("reason") or "").strip(),
        actor=(data.get("actor") or "operator").strip(),
    )
    log.info("killswitch %s (session=%s) by %s",
             "ENGAGED" if data.get("engaged") else "released",
             data.get("session_id") or "global",
             data.get("actor") or "operator")
    return jsonify(state)


# ── Channels / delivery-mode config ──────────────────────────────────────


@bp_questions.route("/api/questions/channels", methods=["GET"])
def channels_get():
    q = _engine()
    cfg = q.load_channels_config()
    effective, sources = q.effective_channels_config()
    # Never echo credentials back in full — mask like the alerts config UI.
    masked = dict(cfg)
    for key in ("pushover_token", "pushover_user", "telegram_bot_token"):
        if masked.get(key):
            masked[key] = str(masked[key])[:4] + "…"
    masked["mode_effective"] = q.load_mode()
    # Which channels a question would actually reach right now, including
    # credentials borrowed from the alerts / budget configs ("configure
    # once"). `fallbacks` says where each borrowed credential came from.
    masked["channels_active"] = [
        name for name, key in (
            ("ntfy", "ntfy_topic"), ("pushover", "pushover_token"),
            ("slack", "slack_webhook_url"), ("telegram", "telegram_bot_token"),
            ("discord", "discord_webhook_url"), ("webhook", "webhook_url"),
            ("gateway_chat", "notify_gateway"))
        if effective.get(key)
    ]
    masked["fallbacks"] = sources
    return jsonify(masked)


@bp_questions.route("/api/questions/channels", methods=["POST"])
def channels_set():
    q = _engine()
    data = request.get_json(force=True, silent=True) or {}
    if data.get("mode") and data["mode"] not in q.DELIVERY_MODES:
        return jsonify({"error": f"mode must be one of {list(q.DELIVERY_MODES)}"}), 400
    if data.get("unanswered") and data["unanswered"] not in q.UNANSWERED_POLICIES:
        return jsonify({"error": f"unanswered must be one of {list(q.UNANSWERED_POLICIES)}"}), 400
    cfg = q.save_channels_config(data)
    return jsonify({"saved": True, "config": {k: v for k, v in cfg.items()
                                              if "token" not in k and "user" not in k}})


@bp_questions.route("/api/questions/channels/test", methods=["POST"])
def channels_test():
    q = _engine()
    sent = q.notify_channels(
        "ClawMetry test notification",
        "Channel test — your agent questions will arrive here.",
    )
    return jsonify({"sent": bool(sent), "channels": sent})
