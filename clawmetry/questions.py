"""clawmetry/questions.py — human-in-the-loop ask/notify engine.

Lets any agent reach the operator when it needs a human: send a push
notification when a task finishes or fails, ask a question (yes/no
confirm, multiple-choice select, or free-text input) and block until the
answer comes back, and honor an operator kill switch that denies every
gated action until released.

Questions are stored in the ``agent_questions`` DuckDB table (writes go
through the sync daemon's ``/__local_query__`` proxy — the daemon owns
the writer lock — with a direct-open fallback for single-process boots).
Delivery fans out to any configured channels: ntfy topic push (phone),
Pushover, Slack incoming webhook, and a generic JSON webhook
(n8n-compatible). Configuration lives in
``~/.clawmetry/questions-channels.json``; the kill switch in
``~/.clawmetry/killswitch.json``; the delivery mode in
``~/.clawmetry/approval-mode.json``.

Consumers:
  * ``clawmetry/mcp_server.py`` — the ``send_notification`` / ``ask_user`` /
    ``wait_for_answer`` / ``cancel_question`` MCP tools
  * ``clawmetry/agent_hooks.py`` — the PreToolUse permission gate
  * ``routes/questions.py`` — the dashboard HTTP API + inbox UI
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("clawmetry-questions")

_CLAWMETRY_DIR = Path.home() / ".clawmetry"
CHANNELS_PATH = _CLAWMETRY_DIR / "questions-channels.json"
KILLSWITCH_PATH = _CLAWMETRY_DIR / "killswitch.json"
MODE_PATH = _CLAWMETRY_DIR / "approval-mode.json"
_DISCOVERY_PATH = _CLAWMETRY_DIR / "local_query.json"
# Existing channel configs we reuse so approvals need zero extra setup on
# a machine that already has alert channels configured:
#   * alerts webhook config (Slack / Discord URLs) — routes/alerts.py
#   * budget config SQLite (Telegram bot token + chat id) — bp_budget
#   * gateway cache + OpenClaw config — the connected chat channel
#     (WhatsApp / Signal / Telegram / iMessage / …) via message.send
ALERTS_CONFIG_PATH = Path.home() / ".openclaw" / "clawmetry-alerts.json"
FLEET_DB_PATH = _CLAWMETRY_DIR / "fleet.db"
GW_CACHE_PATH = Path.home() / ".clawmetry-gateway.json"
OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"

QUESTION_TYPES = ("confirm", "select", "input")
# Where approval is requested (Pushary-parity delivery modes):
#   push_only     — phone only; unanswered escalations follow the
#                   `unanswered` policy (default deny — fail closed)
#   push_first    — phone first, fall back to the agent's own terminal
#                   prompt when unanswered
#   terminal_only — never push for approvals; the agent's native prompt
#                   handles them (notifications still send)
#   notify_only   — awareness only: notify, never gate
DELIVERY_MODES = ("push_only", "push_first", "terminal_only", "notify_only")
# What happens when an escalated question goes unanswered:
#   deny — fail closed; wait — keep waiting (hold for the phone);
#   terminal — fall back to the agent's own permission prompt.
UNANSWERED_POLICIES = ("deny", "wait", "terminal")

DEFAULT_EXPIRY_SECONDS = 600      # questions expire after 10 minutes
DEFAULT_WAIT_SECONDS = 45         # blocking-wait ladder default
_POLL_INTERVAL_SEC = 1.5
MAX_QUESTION_CHARS = 500
MAX_CONTEXT_CHARS = 500
MAX_OPTIONS = 6

_DEFAULT_CHANNELS: dict[str, Any] = {
    "mode": "push_first",
    "wait_seconds": DEFAULT_WAIT_SECONDS,
    "unanswered": "terminal",
    "expiry_seconds": DEFAULT_EXPIRY_SECONDS,
    "ntfy_server": "https://ntfy.sh",
    "ntfy_topic": "",
    "pushover_token": "",
    "pushover_user": "",
    "slack_webhook_url": "",
    "discord_webhook_url": "",
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "webhook_url": "",
    # Deliver through the chat channel the operator already talks to
    # their agent on (WhatsApp / Signal / Telegram / iMessage / …) via
    # the OpenClaw gateway `message` tool. Off by default — it's the
    # only sender that goes through the agent runtime itself.
    "notify_gateway": False,
    "gateway_channel": "",
}


# ── Secret redaction ─────────────────────────────────────────────────────
# Applied to every string that leaves the machine (channel payloads and
# stored question bodies authored from tool args). Only the question
# metadata travels — never transcripts or code.

_SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd|pwd|auth|bearer|credential)s?\b(\s*[=:]\s*)(\S+)"),
    re.compile(r"\b(sk|pk|ghp|gho|ghu|ghs|glpat|xoxb|xoxp|cm)[-_][A-Za-z0-9_\-\.]{12,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),
    re.compile(r"(?i)(https?://[^\s/]*:)([^\s@]+)(@)"),
]


def redact_secrets(text: str) -> str:
    """Best-effort masking of credential-shaped substrings."""
    if not text:
        return text
    out = text
    out = _SECRET_PATTERNS[0].sub(lambda m: m.group(1) + m.group(2) + "[redacted]", out)
    out = _SECRET_PATTERNS[1].sub("[redacted]", out)
    out = _SECRET_PATTERNS[2].sub("[redacted]", out)
    out = _SECRET_PATTERNS[3].sub("[redacted]", out)
    out = _SECRET_PATTERNS[4].sub(lambda m: m.group(1) + "[redacted]" + m.group(3), out)
    return out


# ── Store access ─────────────────────────────────────────────────────────


def _read_discovery() -> Optional[dict[str, Any]]:
    try:
        data = json.loads(_DISCOVERY_PATH.read_text())
        port = int(data.get("port") or 0)
        token = data.get("token") or ""
        pid = int(data.get("pid") or 0)
        if not (port and token and pid):
            return None
        from clawmetry.process_control import is_alive as _pid_alive
        if not _pid_alive(pid):
            return None
        return {"port": port, "token": token}
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        return None


def _store_call(method: str, **kwargs) -> Any:
    """LocalStore call: daemon proxy first, direct open as fallback.

    Same contract as ``routes/hitl.py:_try_store_call`` but usable from
    package-side processes (MCP server, hook subprocess) where the Flask
    ``routes`` package may not be importable. Returns None on total
    failure — callers treat that as "store unavailable" and fail safe."""
    disc = _read_discovery()
    if disc:
        import urllib.request
        payload = json.dumps({"kwargs": kwargs}, default=str).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{disc['port']}/__local_query__/{method}",
            data=payload,
            headers={
                "Authorization": f"Bearer {disc['token']}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            if isinstance(body, dict) and "result" in body:
                return body["result"]
            return body
        except Exception as exc:
            log.debug("daemon proxy %s failed: %s", method, exc)
    try:
        from clawmetry import local_store
        store = local_store.get_store(
            read_only=method.startswith("query"))
        return getattr(store, method)(**kwargs)
    except Exception as exc:
        log.debug("direct store %s failed: %s", method, exc)
        return None


def _rows(result: Any) -> list[dict]:
    """Unwrap the daemon-proxy envelope variants to a plain list."""
    if isinstance(result, list):
        return [r for r in result if isinstance(r, dict)]
    if isinstance(result, dict):
        for key in ("result", "rows", "questions"):
            v = result.get(key)
            if isinstance(v, list):
                return [r for r in v if isinstance(r, dict)]
    return []


# ── Config: channels / delivery mode ─────────────────────────────────────


def load_channels_config() -> dict[str, Any]:
    cfg = dict(_DEFAULT_CHANNELS)
    try:
        stored = json.loads(CHANNELS_PATH.read_text())
        if isinstance(stored, dict):
            for k in cfg:
                if k in stored:
                    cfg[k] = stored[k]
    except (FileNotFoundError, OSError, ValueError):
        pass
    if cfg.get("mode") not in DELIVERY_MODES:
        cfg["mode"] = _DEFAULT_CHANNELS["mode"]
    if cfg.get("unanswered") not in UNANSWERED_POLICIES:
        cfg["unanswered"] = _DEFAULT_CHANNELS["unanswered"]
    return cfg


def save_channels_config(update: dict[str, Any]) -> dict[str, Any]:
    cfg = load_channels_config()
    for k in _DEFAULT_CHANNELS:
        if k in update:
            cfg[k] = update[k]
    if cfg.get("mode") not in DELIVERY_MODES:
        cfg["mode"] = _DEFAULT_CHANNELS["mode"]
    if cfg.get("unanswered") not in UNANSWERED_POLICIES:
        cfg["unanswered"] = _DEFAULT_CHANNELS["unanswered"]
    try:
        cfg["wait_seconds"] = max(5, min(int(cfg.get("wait_seconds") or DEFAULT_WAIT_SECONDS), 3600))
    except (TypeError, ValueError):
        cfg["wait_seconds"] = DEFAULT_WAIT_SECONDS
    try:
        cfg["expiry_seconds"] = max(30, min(int(cfg.get("expiry_seconds") or DEFAULT_EXPIRY_SECONDS), 86400))
    except (TypeError, ValueError):
        cfg["expiry_seconds"] = DEFAULT_EXPIRY_SECONDS
    _CLAWMETRY_DIR.mkdir(parents=True, exist_ok=True)
    CHANNELS_PATH.write_text(json.dumps(cfg, indent=2))
    return cfg


def effective_channels_config() -> tuple[dict[str, Any], dict[str, str]]:
    """Channels config with fallbacks from configs the user already has.

    Configure once, notify everywhere: when the questions config leaves a
    channel blank, we borrow the credential from where it already lives —
    Slack / Discord webhooks from the alerts config, the Telegram bot from
    the budget config. Returns ``(cfg, sources)`` where ``sources`` maps
    each borrowed channel to where its credential came from."""
    cfg = load_channels_config()
    sources: dict[str, str] = {}
    if not (cfg.get("slack_webhook_url") and cfg.get("discord_webhook_url")):
        try:
            alerts = json.loads(ALERTS_CONFIG_PATH.read_text())
            if isinstance(alerts, dict):
                if not cfg.get("slack_webhook_url") and alerts.get("slack_webhook_url"):
                    cfg["slack_webhook_url"] = alerts["slack_webhook_url"]
                    sources["slack"] = "alerts config"
                if not cfg.get("discord_webhook_url") and alerts.get("discord_webhook_url"):
                    cfg["discord_webhook_url"] = alerts["discord_webhook_url"]
                    sources["discord"] = "alerts config"
        except (FileNotFoundError, OSError, ValueError):
            pass
    if not (cfg.get("telegram_bot_token") and cfg.get("telegram_chat_id")):
        try:
            import sqlite3
            db = sqlite3.connect(str(FLEET_DB_PATH), timeout=5)
            try:
                rows = dict(db.execute(
                    "SELECT key, value FROM budget_config "
                    "WHERE key IN ('telegram_bot_token', 'telegram_chat_id')"
                ).fetchall())
            finally:
                db.close()
            token = (rows.get("telegram_bot_token") or "").strip()
            chat_id = (rows.get("telegram_chat_id") or "").strip()
            if token and chat_id and not cfg.get("telegram_bot_token"):
                cfg["telegram_bot_token"] = token
                cfg["telegram_chat_id"] = chat_id
                sources["telegram"] = "budget config"
        except Exception:
            pass
    return cfg, sources


def load_mode() -> dict[str, Any]:
    """Current delivery mode, honoring a temporary override window.

    ``clawmetry hooks mode push_only --for 30m`` writes
    ``{"mode": ..., "until": <epoch>}``; past ``until`` the configured
    channel-config mode applies again."""
    try:
        data = json.loads(MODE_PATH.read_text())
        mode = data.get("mode")
        until = data.get("until")
        if mode in DELIVERY_MODES:
            if not until or float(until) > time.time():
                return {"mode": mode, "until": until, "override": True}
    except (FileNotFoundError, OSError, ValueError, TypeError):
        pass
    return {"mode": load_channels_config()["mode"], "until": None, "override": False}


def set_mode(mode: str, duration_seconds: Optional[int] = None) -> dict[str, Any]:
    if mode not in DELIVERY_MODES:
        raise ValueError(f"mode must be one of {DELIVERY_MODES}")
    until = time.time() + duration_seconds if duration_seconds else None
    _CLAWMETRY_DIR.mkdir(parents=True, exist_ok=True)
    MODE_PATH.write_text(json.dumps({"mode": mode, "until": until}))
    return {"mode": mode, "until": until}


# ── Kill switch ──────────────────────────────────────────────────────────


def killswitch_state() -> dict[str, Any]:
    """Return ``{engaged, sessions, reason, engaged_at, engaged_by}``.

    ``engaged`` is the global switch; ``sessions`` is a map of
    session_id → info for session-scoped switches."""
    try:
        data = json.loads(KILLSWITCH_PATH.read_text())
        if isinstance(data, dict):
            data.setdefault("engaged", False)
            data.setdefault("sessions", {})
            return data
    except (FileNotFoundError, OSError, ValueError):
        pass
    return {"engaged": False, "sessions": {}}


def killswitch_active(session_id: Optional[str] = None) -> bool:
    state = killswitch_state()
    if state.get("engaged"):
        return True
    if session_id and session_id in (state.get("sessions") or {}):
        return True
    return False


def set_killswitch(
    engaged: bool,
    session_id: Optional[str] = None,
    reason: str = "",
    actor: str = "operator",
) -> dict[str, Any]:
    """Engage/release the kill switch, globally or for one session.

    While engaged every gated tool call is denied — even ones policy
    would auto-approve — until released."""
    state = killswitch_state()
    now = datetime.now(timezone.utc).isoformat()
    if session_id:
        sessions = state.setdefault("sessions", {})
        if engaged:
            sessions[session_id] = {"reason": reason, "engaged_at": now, "engaged_by": actor}
        else:
            sessions.pop(session_id, None)
    else:
        state["engaged"] = bool(engaged)
        if engaged:
            state["reason"] = reason
            state["engaged_at"] = now
            state["engaged_by"] = actor
        else:
            state.pop("reason", None)
            state.pop("engaged_at", None)
            state.pop("engaged_by", None)
    _CLAWMETRY_DIR.mkdir(parents=True, exist_ok=True)
    KILLSWITCH_PATH.write_text(json.dumps(state, indent=2))
    return state


# ── Channel fan-out ──────────────────────────────────────────────────────


def _http_post(url: str, data: bytes, headers: dict[str, str], timeout: int = 10) -> bool:
    import urllib.request
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception as exc:
        log.debug("channel POST %s failed: %s", url.split("?")[0], exc)
        return False


def _dashboard_url() -> str:
    port = os.environ.get("CLAWMETRY_PORT") or "8900"
    return f"http://localhost:{port}"


def _gateway_conn() -> Optional[dict[str, str]]:
    """Resolve OpenClaw gateway url+token without importing dashboard.py
    (this runs inside hook / MCP subprocesses where the Flask module is
    too heavy). Resolution mirrors dashboard._load_gw_config: env var →
    live openclaw.json → cached ~/.clawmetry-gateway.json."""
    token = (os.environ.get("OPENCLAW_GATEWAY_TOKEN") or "").strip()
    url = (os.environ.get("OPENCLAW_GATEWAY_URL") or "").strip()
    if not token:
        try:
            oc = json.loads(OPENCLAW_CONFIG_PATH.read_text())
            token = (((oc.get("gateway") or {}).get("auth") or {}).get("token") or "").strip()
            port = (oc.get("gateway") or {}).get("port")
            if not url and port:
                url = f"http://127.0.0.1:{int(port)}"
        except (FileNotFoundError, OSError, ValueError, TypeError):
            pass
    if not token or not url:
        try:
            cache = json.loads(GW_CACHE_PATH.read_text())
            token = token or (cache.get("token") or "").strip()
            url = url or (cache.get("url") or "").strip()
        except (FileNotFoundError, OSError, ValueError):
            pass
    if not url:
        url = "http://127.0.0.1:18789"
    if not token:
        return None
    return {"url": url.rstrip("/"), "token": token}


def _gateway_send(message: str, channel: str = "") -> bool:
    """Send a text through the operator's connected OpenClaw chat channel
    (WhatsApp / Signal / Telegram / iMessage / …) via the gateway
    ``message`` tool — the same path budget alerts already use."""
    conn = _gateway_conn()
    if not conn:
        return False
    args: dict[str, Any] = {"action": "send", "message": message}
    if channel:
        args["channel"] = channel
    payload = json.dumps({"tool": "message", "args": args}).encode("utf-8")
    import urllib.request
    req = urllib.request.Request(
        f"{conn['url']}/tools/invoke",
        data=payload,
        headers={
            "Authorization": f"Bearer {conn['token']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return bool(data.get("ok"))
    except Exception as exc:
        log.debug("gateway send failed: %s", exc)
        return False


def notify_channels(
    title: str,
    body: str,
    cfg: Optional[dict[str, Any]] = None,
    question: Optional[dict[str, Any]] = None,
) -> list[str]:
    """Fan a notification (optionally carrying a question) out to every
    configured channel. Returns the list of channels that accepted it.
    Only redacted question metadata travels — title, body, tool name —
    never transcripts or code."""
    if cfg is None:
        cfg, _ = effective_channels_config()
    title = redact_secrets((title or "")[:100])
    body = redact_secrets((body or "")[:500])
    sent: list[str] = []
    qid = (question or {}).get("id") or ""
    inbox_url = f"{_dashboard_url()}/?tab=approvals"
    # Plain-text answer lines for channels without interactive buttons
    # (Telegram / gateway chat). Clickable on the same network; always a
    # copy-pasteable fallback.
    answer_lines = ""
    if question and qid:
        base = f"{_dashboard_url()}/api/questions/{qid}/answer"
        if (question.get("qtype") or "confirm") == "confirm":
            answer_lines = f"\n✅ Approve: {base}?value=yes\n❌ Deny: {base}?value=no"
        else:
            answer_lines = f"\n💬 Answer: {inbox_url}"

    # ntfy — phone push with tap-to-answer action buttons on confirms.
    if cfg.get("ntfy_topic"):
        server = (cfg.get("ntfy_server") or "https://ntfy.sh").rstrip("/")
        headers = {"Title": title.encode("ascii", "replace").decode(),
                   "Priority": "high" if question else "default",
                   "Tags": "robot" if not question else "question"}
        if question and (question.get("qtype") or "confirm") == "confirm" and qid:
            base = f"{_dashboard_url()}/api/questions/{qid}/answer"
            headers["Actions"] = (
                f"http, Approve, {base}, method=POST, "
                f"headers.Content-Type=application/json, body={{\"value\":\"yes\"}}; "
                f"http, Deny, {base}, method=POST, "
                f"headers.Content-Type=application/json, body={{\"value\":\"no\"}}"
            )
        elif question:
            headers["Click"] = inbox_url
        if _http_post(f"{server}/{cfg['ntfy_topic']}", body.encode("utf-8"), headers):
            sent.append("ntfy")

    # Pushover — phone push.
    if cfg.get("pushover_token") and cfg.get("pushover_user"):
        import urllib.parse
        payload = urllib.parse.urlencode({
            "token": cfg["pushover_token"],
            "user": cfg["pushover_user"],
            "title": title,
            "message": body,
            "url": inbox_url if question else "",
            "url_title": "Open approvals inbox" if question else "",
            "priority": 1 if question else 0,
        }).encode("utf-8")
        if _http_post("https://api.pushover.net/1/messages.json", payload,
                      {"Content-Type": "application/x-www-form-urlencoded"}):
            sent.append("pushover")

    # Slack — incoming webhook with answer buttons linking to the inbox.
    if cfg.get("slack_webhook_url"):
        blocks: list[dict[str, Any]] = [
            {"type": "section",
             "text": {"type": "mrkdwn", "text": f"*{title}*\n{body}"}},
        ]
        if question:
            elements = []
            if (question.get("qtype") or "confirm") == "confirm" and qid:
                base = f"{_dashboard_url()}/api/questions/{qid}/answer"
                elements = [
                    {"type": "button", "style": "primary",
                     "text": {"type": "plain_text", "text": "Approve"},
                     "url": f"{base}?value=yes"},
                    {"type": "button", "style": "danger",
                     "text": {"type": "plain_text", "text": "Deny"},
                     "url": f"{base}?value=no"},
                ]
            else:
                elements = [{"type": "button",
                             "text": {"type": "plain_text", "text": "Answer in ClawMetry"},
                             "url": inbox_url}]
            blocks.append({"type": "actions", "elements": elements})
        payload = json.dumps({"text": f"{title} — {body}", "blocks": blocks}).encode("utf-8")
        if _http_post(cfg["slack_webhook_url"], payload,
                      {"Content-Type": "application/json"}):
            sent.append("slack")

    # Telegram — bot sendMessage; the answer links ride in the text since
    # inline URL buttons reject non-public hosts.
    if cfg.get("telegram_bot_token") and cfg.get("telegram_chat_id"):
        payload = json.dumps({
            "chat_id": cfg["telegram_chat_id"],
            "text": f"🤖 {title}\n{body}{answer_lines}",
            "disable_web_page_preview": True,
        }).encode("utf-8")
        if _http_post(
                f"https://api.telegram.org/bot{cfg['telegram_bot_token']}/sendMessage",
                payload, {"Content-Type": "application/json"}):
            sent.append("telegram")

    # Discord — incoming webhook.
    if cfg.get("discord_webhook_url"):
        payload = json.dumps({
            "content": f"**{title}**\n{body}{answer_lines}",
        }).encode("utf-8")
        if _http_post(cfg["discord_webhook_url"], payload,
                      {"Content-Type": "application/json"}):
            sent.append("discord")

    # Connected OpenClaw chat channel (WhatsApp / Signal / Telegram /
    # iMessage / …) — the channel the operator already talks to their
    # agent on, via the gateway message tool.
    if cfg.get("notify_gateway"):
        text = f"🤖 ClawMetry — {title}\n{body}{answer_lines}"
        if _gateway_send(text, channel=cfg.get("gateway_channel") or ""):
            sent.append("gateway_chat")

    # Generic webhook — n8n / custom automations get the full envelope.
    if cfg.get("webhook_url"):
        payload = json.dumps({
            "source": "clawmetry",
            "event": "question" if question else "notification",
            "title": title,
            "body": body,
            "question": {
                "id": qid,
                "type": (question or {}).get("qtype"),
                "options": (question or {}).get("options"),
                "session_id": (question or {}).get("session_id"),
                "agent_name": (question or {}).get("agent_name"),
                "expires_at": (question or {}).get("expires_at"),
                "answer_url": f"{_dashboard_url()}/api/questions/{qid}/answer" if qid else None,
            } if question else None,
            "ts": datetime.now(timezone.utc).isoformat(),
        }).encode("utf-8")
        if _http_post(cfg["webhook_url"], payload,
                      {"Content-Type": "application/json"}):
            sent.append("webhook")

    return sent


def send_notification(
    title: str,
    body: str,
    agent_name: str = "",
    context: Optional[dict[str, Any]] = None,
    cfg: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """One-way notification (task_complete / error / info) to all channels."""
    full_title = f"{agent_name}: {title}" if agent_name else title
    if context:
        extras = []
        if context.get("summary"):
            extras.append(str(context["summary"])[:200])
        if context.get("errorMessage"):
            extras.append(f"Error: {str(context['errorMessage'])[:200]}")
        files = context.get("filesChanged") or []
        if files:
            extras.append(f"{len(files)} file(s) changed")
        if context.get("nextSteps"):
            extras.append(f"Next: {str(context['nextSteps'])[:150]}")
        if extras:
            body = f"{body}\n" + "\n".join(extras)
    sent = notify_channels(full_title, body, cfg=cfg)
    return {"sent": bool(sent), "channels": sent}


# ── Question lifecycle ───────────────────────────────────────────────────


def create_question(
    question: str,
    qtype: str = "confirm",
    options: Optional[list[str]] = None,
    placeholder: str = "",
    context: str = "",
    agent_name: str = "",
    session_id: str = "",
    source: str = "api",
    expiry_seconds: Optional[int] = None,
    notify: bool = True,
) -> dict[str, Any]:
    """Create a pending question, fan it out, return the stored row."""
    question = redact_secrets((question or "").strip()[:MAX_QUESTION_CHARS])
    if not question:
        raise ValueError("question is required")
    if qtype not in QUESTION_TYPES:
        raise ValueError(f"type must be one of {QUESTION_TYPES}")
    opts: Optional[list[str]] = None
    if qtype == "select":
        opts = [redact_secrets(str(o))[:120] for o in (options or []) if str(o).strip()]
        if not 2 <= len(opts) <= MAX_OPTIONS:
            raise ValueError(f"select needs 2-{MAX_OPTIONS} options")
    cfg = load_channels_config()
    if expiry_seconds is None:
        expiry_seconds = int(cfg.get("expiry_seconds") or DEFAULT_EXPIRY_SECONDS)
    now = datetime.now(timezone.utc)
    row = {
        "id": str(uuid.uuid4()),
        "session_id": session_id or None,
        "agent_name": agent_name or None,
        "source": source,
        "qtype": qtype,
        "question": question,
        "options": opts,
        "placeholder": redact_secrets(placeholder or "")[:200] or None,
        "context": redact_secrets(context or "")[:MAX_CONTEXT_CHARS] or None,
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=expiry_seconds)).isoformat(),
    }
    _store_call("ingest_question", question=row)
    if notify:
        title = agent_name or "Agent question"
        body = question if not context else f"{question}\n{context}"
        row["notified_channels"] = notify_channels(title, body, cfg=cfg, question=row)
    return row


def get_question(question_id: str) -> Optional[dict[str, Any]]:
    rows = _rows(_store_call("query_questions", question_id=question_id, limit=1))
    return rows[0] if rows else None


def answer_question(
    question_id: str,
    value: str,
    answered_by: str = "operator",
) -> dict[str, Any]:
    """Record an answer (first answer wins). Returns ``{ok, status, ...}``."""
    q = get_question(question_id)
    if not q:
        return {"ok": False, "error": "not_found"}
    if q.get("status") != "pending":
        return {"ok": True, "already": True, "status": q.get("status"), "answer": q.get("answer")}
    qtype = q.get("qtype") or "confirm"
    value = str(value or "").strip()
    if qtype == "confirm":
        low = value.lower()
        if low in ("yes", "y", "approve", "approved", "true", "1", "ok"):
            value = "yes"
        elif low in ("no", "n", "deny", "denied", "false", "0"):
            value = "no"
        else:
            return {"ok": False, "error": "confirm answers must be yes or no"}
    elif qtype == "select":
        opts = q.get("options") or []
        if isinstance(opts, str):
            try:
                opts = json.loads(opts)
            except (ValueError, TypeError):
                opts = []
        if value not in [str(o) for o in opts]:
            return {"ok": False, "error": "answer must be one of the options",
                    "options": opts}
    else:  # input
        if not value:
            return {"ok": False, "error": "answer text required"}
        value = value[:1000]
    flipped = _store_call(
        "update_question_answer",
        question_id=question_id,
        answer=value,
        answered_by=answered_by,
        status="answered",
    )
    try:
        flipped = int(flipped)
    except (TypeError, ValueError):
        flipped = 0
    if not flipped:
        q = get_question(question_id) or {}
        return {"ok": True, "already": True, "status": q.get("status"), "answer": q.get("answer")}
    return {"ok": True, "status": "answered", "answer": value}


def cancel_question(question_id: str, actor: str = "agent") -> dict[str, Any]:
    """Cancel a pending question so it can no longer be answered."""
    flipped = _store_call(
        "update_question_answer",
        question_id=question_id,
        answer=None,
        answered_by=actor,
        status="cancelled",
    )
    try:
        ok = bool(int(flipped))
    except (TypeError, ValueError):
        ok = False
    return {"ok": ok, "status": "cancelled" if ok else "not_pending"}


def expire_pending() -> int:
    """Lazily flip past-deadline pending questions to expired."""
    n = _store_call("expire_questions")
    try:
        return int(n)
    except (TypeError, ValueError):
        return 0


def list_questions(
    status: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    expire_pending()
    return _rows(_store_call(
        "query_questions", status=status, session_id=session_id, limit=limit))


def wait_for_answer(
    question_id: str,
    timeout_s: float = 30.0,
    poll_interval: float = _POLL_INTERVAL_SEC,
) -> dict[str, Any]:
    """Block until the question resolves or ``timeout_s`` elapses.

    Returns the Pushary-compatible shape:
    ``{"answered": true, "value": ...}`` on an answer,
    ``{"answered": false, "timedOut": true}`` on timeout, and
    ``{"answered": false, "status": "cancelled"|"expired"}`` when the
    question was resolved without an answer."""
    deadline = time.monotonic() + max(0.0, timeout_s)
    while True:
        q = get_question(question_id)
        if not q:
            return {"answered": False, "error": "not_found", "correlationId": question_id}
        status = q.get("status")
        if status == "answered":
            return {"answered": True, "value": q.get("answer"),
                    "correlationId": question_id}
        if status in ("cancelled", "expired", "timeout"):
            return {"answered": False, "status": status, "correlationId": question_id}
        if time.monotonic() >= deadline:
            return {"answered": False, "timedOut": True, "correlationId": question_id}
        time.sleep(min(poll_interval, max(0.05, deadline - time.monotonic())))


def ask_blocking(
    question: str,
    qtype: str = "confirm",
    options: Optional[list[str]] = None,
    placeholder: str = "",
    context: str = "",
    agent_name: str = "",
    session_id: str = "",
    source: str = "api",
    timeout_s: Optional[float] = None,
) -> dict[str, Any]:
    """Create a question and block for the answer (the MCP ask_user path)."""
    cfg = load_channels_config()
    if timeout_s is None:
        timeout_s = float(cfg.get("wait_seconds") or DEFAULT_WAIT_SECONDS)
    row = create_question(
        question, qtype=qtype, options=options, placeholder=placeholder,
        context=context, agent_name=agent_name, session_id=session_id,
        source=source,
    )
    return wait_for_answer(row["id"], timeout_s=timeout_s)
