"""Approval notification routing — page a human where they actually are.

The gap this closes (founder, 2026-08-15): an approval parks in the local
queue and *nothing* tells you. You find out by looking at the Approvals
tab. For a Claude Code session stalled on a permission prompt that is the
same wait as walking over to the terminal, so the pre-execution gate buys
nothing in practice.

This module is the fan-out half: when an approval parks, deliver it to the
channels configured for THAT RUNTIME, with a one-tap decision link.

  * Per-runtime routing (``~/.clawmetry/approval_routes.json``) — Claude
    Code prompts to Telegram, OpenClaw exec approvals to Slack, everything
    else to the default row. Mirrors the ``alert_rules.runtime`` scoping
    that shipped in 0.12.642; unknown runtime → the ``default`` row, never
    silently dropped.
  * Channel credentials are the EXISTING alert-channel config
    (``~/.openclaw/clawmetry-alerts.json``, the file /api/alert-channels
    already reads/writes) plus the new whatsapp/twilio/smtp keys. One
    place to configure a channel, two features that use it.

Honesty about what each channel can do LOCALLY (no cloud account):

  channel    notify   decide from the message
  --------   ------   -----------------------
  telegram     ✓      ✓ inline Approve/Deny buttons (approval_inbound.py
                        long-polls getUpdates — no inbound port needed)
  slack        ✓      link only (Slack's interactive callbacks need a
                      public HTTPS endpoint → that is the cloud relay's
                      job; the message carries a decision link instead)
  discord      ✓      link only
  webhook      ✓      whatever the receiving system does with it
  pagerduty    ✓      link only
  whatsapp     ✓      link only locally (Meta/Twilio button replies need a
                      public webhook; the 24h-window rule also applies)
  email        ✓      link only (SMTP configured locally, else cloud)
  phone        ✓      notify only locally — "press 1 to approve" needs a
                      public TwiML callback URL, so DTMF decisions stay a
                      cloud feature. The local call still tells you.

The decision link points at this node's own dashboard
(``/a/<id>?t=<sig>``, routes/approval_routing.py). That is reachable from
a phone on the same LAN/Tailscale; set ``CLAWMETRY_PUBLIC_BASE`` to
override the host we advertise.

CONTRACT: never raise, never block long. Every sender runs with a 4 s
timeout and swallows its own errors — this runs inside the pre-tool gate's
request path, where a slow vendor must never become an agent stall.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import socket
import threading
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger("clawmetry.approval_notify")

ROUTES_PATH = os.path.expanduser("~/.clawmetry/approval_routes.json")
_SECRET_PATH = os.path.expanduser("~/.clawmetry/approval_link_secret")
_MSG_STATE_PATH = os.path.expanduser("~/.clawmetry/approval_messages.json")
_ALERTS_CONFIG_FILE = os.path.expanduser("~/.openclaw/clawmetry-alerts.json")

_TIMEOUT_S = 4.0
_STATE_LOCK = threading.Lock()

#: Channels a routing row may name. Order is delivery order.
CHANNELS = ("telegram", "slack", "discord", "webhook", "pagerduty",
            "whatsapp", "email", "phone")

#: Channels that can carry a real decision back without a public endpoint.
TWO_WAY_LOCAL = ("telegram",)

#: Default mirror window — how long the phone gets to answer a runtime's own
#: permission prompt before the local terminal prompt takes over.
MIRROR_TIMEOUT_DEFAULT_S = 180


# ── routing config ─────────────────────────────────────────────────────────

def default_routes() -> dict:
    """Ship-safe defaults: routing on, no channels selected yet.

    An empty ``channels`` list means "every channel that has credentials"
    — so a user who configured Telegram in the Notifications tab starts
    getting approvals there without a second setup step. Explicit lists
    win the moment they set one.
    """
    return {
        "version": 1,
        "enabled": True,
        "default": {"channels": [], "mirror_permission_prompts": False,
                    "mirror_timeout_s": MIRROR_TIMEOUT_DEFAULT_S},
        "runtimes": {},
    }


def load_routes() -> dict:
    cfg = default_routes()
    try:
        if os.path.exists(ROUTES_PATH):
            with open(ROUTES_PATH, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cfg["enabled"] = bool(data.get("enabled", True))
                if isinstance(data.get("default"), dict):
                    cfg["default"] = _clean_row(data["default"])
                rts = data.get("runtimes")
                if isinstance(rts, dict):
                    cfg["runtimes"] = {
                        str(k): _clean_row(v)
                        for k, v in rts.items() if isinstance(v, dict)
                    }
    except Exception as exc:
        logger.warning("approval routes unreadable (%s) — using defaults", exc)
    return cfg


def save_routes(cfg: dict) -> bool:
    try:
        clean = default_routes()
        clean["enabled"] = bool(cfg.get("enabled", True))
        if isinstance(cfg.get("default"), dict):
            clean["default"] = _clean_row(cfg["default"])
        rts = cfg.get("runtimes")
        if isinstance(rts, dict):
            clean["runtimes"] = {str(k): _clean_row(v)
                                 for k, v in rts.items()
                                 if isinstance(v, dict)}
        os.makedirs(os.path.dirname(ROUTES_PATH), exist_ok=True)
        tmp = ROUTES_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(clean, f, indent=2)
        os.replace(tmp, ROUTES_PATH)
        return True
    except Exception as exc:
        logger.warning("approval routes not saved: %s", exc)
        return False


def _clean_row(row: dict) -> dict:
    chans = row.get("channels")
    if not isinstance(chans, list):
        chans = []
    try:
        window = int(row.get("mirror_timeout_s") or MIRROR_TIMEOUT_DEFAULT_S)
    except (TypeError, ValueError):
        window = MIRROR_TIMEOUT_DEFAULT_S
    return {
        "channels": [c for c in CHANNELS if c in chans],
        "mirror_permission_prompts": bool(
            row.get("mirror_permission_prompts", False)),
        # How long the phone gets before the runtime's own prompt takes
        # over. Clamped: under 30 s nobody can answer, over an hour the
        # hook process would outlive most sessions.
        "mirror_timeout_s": max(30, min(window, 3600)),
    }


def route_for(runtime: str) -> dict:
    """Resolve the routing row for one runtime (falls back to default)."""
    cfg = load_routes()
    row = cfg["runtimes"].get(str(runtime or "").strip())
    if not isinstance(row, dict):
        row = cfg["default"]
    return {"enabled": cfg["enabled"], **row}


def mirror_enabled(runtime: str = "claude_code") -> bool:
    """Should we intercept the runtime's OWN permission prompts?"""
    row = route_for(runtime)
    return bool(row.get("enabled") and row.get("mirror_permission_prompts"))


# ── channel credentials (shared with /api/alert-channels) ──────────────────

def load_channel_config() -> dict:
    cfg = {}
    try:
        if os.path.exists(_ALERTS_CONFIG_FILE):
            with open(_ALERTS_CONFIG_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cfg = data
    except Exception:
        cfg = {}
    return cfg


def _s(cfg: dict, key: str) -> str:
    return str(cfg.get(key) or "").strip()


def configured_channels(cfg: "dict | None" = None) -> list:
    """Which channels have enough credentials to deliver right now."""
    cfg = load_channel_config() if cfg is None else cfg
    out = []
    if _s(cfg, "telegram_bot_token") and _s(cfg, "telegram_chat_id"):
        out.append("telegram")
    if _s(cfg, "slack_webhook_url"):
        out.append("slack")
    if _s(cfg, "discord_webhook_url"):
        out.append("discord")
    if _s(cfg, "webhook_url"):
        out.append("webhook")
    if _s(cfg, "pagerduty_routing_key"):
        out.append("pagerduty")
    if _s(cfg, "whatsapp_to") and (
            _s(cfg, "whatsapp_token") and _s(cfg, "whatsapp_phone_id")
            or _s(cfg, "twilio_account_sid") and _s(cfg, "twilio_auth_token")):
        out.append("whatsapp")
    if _s(cfg, "email_address") and _s(cfg, "smtp_host"):
        out.append("email")
    if (_s(cfg, "phone_number") and _s(cfg, "twilio_account_sid")
            and _s(cfg, "twilio_auth_token") and _s(cfg, "twilio_from")):
        out.append("phone")
    return out


# ── decision links ─────────────────────────────────────────────────────────

def _link_secret() -> bytes:
    """Per-node HMAC secret for decision links (created 0600 on first use)."""
    try:
        if os.path.exists(_SECRET_PATH):
            with open(_SECRET_PATH, "rb") as f:
                sec = f.read().strip()
            if len(sec) >= 32:
                return sec
        sec = os.urandom(32).hex().encode()
        os.makedirs(os.path.dirname(_SECRET_PATH), exist_ok=True)
        fd = os.open(_SECRET_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(sec)
        return sec
    except Exception:
        # Deterministic per-host fallback so links still verify within a
        # process even when the home dir is read-only.
        return hashlib.sha256(
            (os.uname().nodename if hasattr(os, "uname") else "clawmetry")
            .encode()).hexdigest().encode()


def sign_link(approval_id: str) -> str:
    return hmac.new(_link_secret(), str(approval_id).encode(),
                    hashlib.sha256).hexdigest()[:32]


def verify_link(approval_id: str, token: str) -> bool:
    return hmac.compare_digest(sign_link(approval_id), str(token or ""))


def _lan_host() -> str:
    """Best-effort routable address for this machine (phones aren't on
    127.0.0.1). Never raises; falls back to localhost."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except Exception:
        return "127.0.0.1"


def _dashboard_port() -> int:
    try:
        with open(os.path.expanduser("~/.clawmetry/server.json"), "r") as f:
            return int(json.load(f).get("port") or 8900)
    except Exception:
        return 8900


def base_url() -> str:
    override = str(os.environ.get("CLAWMETRY_PUBLIC_BASE") or "").strip()
    if override:
        return override.rstrip("/")
    return "http://%s:%d" % (_lan_host(), _dashboard_port())


def decision_url(approval_id: str, decision: str = "") -> str:
    url = "%s/a/%s?t=%s" % (base_url(), urllib.parse.quote(str(approval_id)),
                            sign_link(approval_id))
    if decision:
        url += "&d=" + urllib.parse.quote(decision)
    return url


# ── HTTP helper ────────────────────────────────────────────────────────────

def _post(url: str, payload, *, headers: "dict | None" = None,
          form: bool = False, basic_auth: "tuple | None" = None):
    """POST JSON (or form-encoded) with a hard timeout. Returns the parsed
    JSON body on success, None on any failure."""
    try:
        if form:
            body = urllib.parse.urlencode(payload).encode()
            ctype = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(payload).encode()
            ctype = "application/json"
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", ctype)
        req.add_header("User-Agent", "clawmetry-approvals")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        if basic_auth:
            import base64
            tok = base64.b64encode(
                ("%s:%s" % basic_auth).encode()).decode()
            req.add_header("Authorization", "Basic " + tok)
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            raw = resp.read().decode("utf-8", "replace")
        try:
            return json.loads(raw)
        except Exception:
            return {"raw": raw}
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        logger.warning("approval notify POST %s failed: %s %s",
                       url.split("?")[0], exc.code, detail)
        return None
    except Exception as exc:
        logger.warning("approval notify POST %s failed: %s",
                       url.split("?")[0], exc)
        return None


# ── message state (so a decision can edit/close the original message) ──────

def _load_msg_state() -> dict:
    try:
        with open(_MSG_STATE_PATH, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def remember_message(approval_id: str, channel: str, meta: dict) -> None:
    with _STATE_LOCK:
        state = _load_msg_state()
        entry = state.get(approval_id) or {}
        entry[channel] = meta
        state[approval_id] = entry
        # Bound the file — approvals resolve fast and stale rows are junk.
        if len(state) > 200:
            for k in list(state)[:len(state) - 200]:
                state.pop(k, None)
        try:
            os.makedirs(os.path.dirname(_MSG_STATE_PATH), exist_ok=True)
            tmp = _MSG_STATE_PATH + ".tmp"
            with open(tmp, "w") as f:
                json.dump(state, f)
            os.replace(tmp, _MSG_STATE_PATH)
        except Exception:
            pass


def message_meta(approval_id: str, channel: str) -> dict:
    entry = _load_msg_state().get(str(approval_id)) or {}
    meta = entry.get(channel)
    return meta if isinstance(meta, dict) else {}


# ── the payload ────────────────────────────────────────────────────────────

RUNTIME_LABELS = {
    "claude_code": "Claude Code",
    "openclaw": "OpenClaw",
    "codex": "Codex",
    "cursor": "Cursor",
    "copilot": "Copilot",
    "gemini_cli": "Gemini CLI",
    "grok": "Grok",
    "antigravity": "Antigravity",
    "deepseek_harness": "DeepSeek Harness",
    "aider": "Aider",
    "goose": "Goose",
    "opencode": "OpenCode",
    "qwen_code": "Qwen Code",
    "hermes": "Hermes",
    "nanoclaw": "NanoClaw",
    "picoclaw": "PicoClaw",
    "n8n": "n8n",
}


def runtime_label(runtime: str) -> str:
    r = str(runtime or "").strip()
    return RUNTIME_LABELS.get(r, r.replace("_", " ").title() or "Agent")


def build_payload(approval: dict) -> dict:
    """Normalise an approval row / park record into the notification shape."""
    args = approval.get("args")
    args = args if isinstance(args, dict) else {}
    runtime = (approval.get("runtime") or args.get("runtime")
               or "openclaw")
    tool = (approval.get("tool_name") or args.get("tool_name")
            or (str(approval.get("action") or "").split(":")[0]) or "tool")
    command = str(approval.get("command") or args.get("command") or "").strip()
    if not command:
        action = str(approval.get("action") or "")
        command = action.split(":", 1)[1].strip() if ":" in action else action
    aid = str(approval.get("id") or "")
    return {
        "id": aid,
        "runtime": runtime,
        "runtime_label": runtime_label(runtime),
        "kind": approval.get("kind") or args.get("kind") or "policy",
        "tool_name": tool,
        "command": command[:400],
        "cwd": str(approval.get("cwd") or args.get("cwd") or "")[:200],
        "session_id": str(approval.get("requestor_session_id")
                          or approval.get("session_id") or "")[:120],
        "policy": str(approval.get("policy") or args.get("policy") or ""),
        "node": socket.gethostname(),
        "url": decision_url(aid) if aid else "",
        "approve_url": decision_url(aid, "approve") if aid else "",
        "deny_url": decision_url(aid, "deny") if aid else "",
    }


def _title(p: dict) -> str:
    if p["kind"] == "permission_prompt":
        return "%s needs permission" % p["runtime_label"]
    return "%s approval needed" % p["runtime_label"]


def _body_lines(p: dict) -> list:
    lines = ["*%s*" % _title(p), "`%s`" % (p["command"] or p["tool_name"])]
    if p["cwd"]:
        lines.append("in %s" % p["cwd"])
    if p["policy"]:
        lines.append("rule: %s" % p["policy"])
    lines.append("node: %s" % p["node"])
    return lines


def _plain(p: dict) -> str:
    return "\n".join(x.replace("*", "").replace("`", "")
                     for x in _body_lines(p))


# ── senders ────────────────────────────────────────────────────────────────

def _send_telegram(cfg: dict, p: dict) -> bool:
    token, chat = _s(cfg, "telegram_bot_token"), _s(cfg, "telegram_chat_id")
    if not (token and chat):
        return False
    text = ("*%s*\n```\n%s\n```\n%s"
            % (_title(p), (p["command"] or p["tool_name"])[:300],
               "\n".join(_body_lines(p)[2:])))
    payload = {
        "chat_id": chat,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": {"inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": "cma:%s:approve" % p["id"]},
            {"text": "⛔ Deny", "callback_data": "cma:%s:deny" % p["id"]},
        ], [
            {"text": "Open dashboard", "url": p["url"]},
        ]]},
    }
    resp = _post("https://api.telegram.org/bot%s/sendMessage" % token, payload)
    if not resp or not resp.get("ok"):
        return False
    try:
        remember_message(p["id"], "telegram", {
            "chat_id": resp["result"]["chat"]["id"],
            "message_id": resp["result"]["message_id"],
        })
    except Exception:
        pass
    return True


def _send_slack(cfg: dict, p: dict) -> bool:
    url = _s(cfg, "slack_webhook_url")
    if not url:
        return False
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn",
                                     "text": "*%s*" % _title(p)}},
        {"type": "section", "text": {"type": "mrkdwn",
                                     "text": "```%s```" % (p["command"]
                                                           or p["tool_name"])[:400]}},
        {"type": "context", "elements": [
            {"type": "mrkdwn",
             "text": " · ".join(x for x in [p["cwd"], p["policy"], p["node"]]
                                if x) or p["node"]}]},
    ]
    if p["url"]:
        blocks.append({"type": "actions", "elements": [
            {"type": "button", "style": "primary",
             "text": {"type": "plain_text", "text": "Approve"},
             "url": p["approve_url"]},
            {"type": "button", "style": "danger",
             "text": {"type": "plain_text", "text": "Deny"},
             "url": p["deny_url"]},
        ]})
    return _post(url, {"text": "%s: %s" % (_title(p), p["command"][:120]),
                       "blocks": blocks}) is not None


def _send_discord(cfg: dict, p: dict) -> bool:
    url = _s(cfg, "discord_webhook_url")
    if not url:
        return False
    return _post(url, {
        "content": "**%s**" % _title(p),
        "embeds": [{
            "title": (p["command"] or p["tool_name"])[:250],
            "description": "[Approve](%s) · [Deny](%s)" % (p["approve_url"],
                                                           p["deny_url"]),
            "color": 0xF59E0B,
            "fields": [f for f in [
                {"name": "Runtime", "value": p["runtime_label"],
                 "inline": True},
                {"name": "Node", "value": p["node"], "inline": True},
                ({"name": "Rule", "value": p["policy"], "inline": True}
                 if p["policy"] else None),
            ] if f],
        }],
    }) is not None


def _send_webhook(cfg: dict, p: dict) -> bool:
    url = _s(cfg, "webhook_url")
    if not url:
        return False
    return _post(url, {"type": "approval.pending", **p}) is not None


def _send_pagerduty(cfg: dict, p: dict) -> bool:
    key = _s(cfg, "pagerduty_routing_key")
    if not key:
        return False
    return _post("https://events.pagerduty.com/v2/enqueue", {
        "routing_key": key,
        "event_action": "trigger",
        "dedup_key": "clawmetry-approval-%s" % p["id"],
        "payload": {
            "summary": "%s: %s" % (_title(p), (p["command"]
                                               or p["tool_name"])[:200]),
            "severity": "warning",
            "source": p["node"],
            "component": p["runtime"],
            "custom_details": {k: p[k] for k in
                               ("command", "cwd", "policy", "session_id")},
        },
        "links": [{"href": p["url"], "text": "Approve or deny"}],
    }) is not None


def _send_whatsapp(cfg: dict, p: dict) -> bool:
    """Meta Cloud API when configured, else Twilio's WhatsApp channel.

    Buttons are sent when the recipient is inside Meta's 24-hour service
    window; outside it Meta rejects free-form sends, so we fall back to the
    configured template (``whatsapp_template``) if there is one. Either way
    the message carries the decision link, which is what actually resolves
    the approval locally.
    """
    to = _s(cfg, "whatsapp_to")
    if not to:
        return False
    text = "%s\n%s\n\nApprove: %s\nDeny: %s" % (
        _title(p), (p["command"] or p["tool_name"])[:250],
        p["approve_url"], p["deny_url"])
    token, phone_id = _s(cfg, "whatsapp_token"), _s(cfg, "whatsapp_phone_id")
    if token and phone_id:
        url = "https://graph.facebook.com/v21.0/%s/messages" % phone_id
        hdrs = {"Authorization": "Bearer " + token}
        resp = _post(url, {"messaging_product": "whatsapp", "to": to,
                           "type": "text", "text": {"body": text}},
                     headers=hdrs)
        if resp is not None:
            return True
        tpl = _s(cfg, "whatsapp_template")
        if tpl:
            return _post(url, {
                "messaging_product": "whatsapp", "to": to,
                "type": "template",
                "template": {"name": tpl,
                             "language": {"code": _s(cfg, "whatsapp_lang")
                                          or "en_US"},
                             "components": [{"type": "body", "parameters": [
                                 {"type": "text",
                                  "text": (p["command"]
                                           or p["tool_name"])[:200]},
                                 {"type": "text", "text": p["url"]}]}]},
            }, headers=hdrs) is not None
        return False
    sid, tok = _s(cfg, "twilio_account_sid"), _s(cfg, "twilio_auth_token")
    frm = _s(cfg, "twilio_whatsapp_from") or _s(cfg, "twilio_from")
    if not (sid and tok and frm):
        return False
    return _post(
        "https://api.twilio.com/2010-04-01/Accounts/%s/Messages.json" % sid,
        {"From": "whatsapp:%s" % frm.replace("whatsapp:", ""),
         "To": "whatsapp:%s" % to.replace("whatsapp:", ""), "Body": text},
        form=True, basic_auth=(sid, tok)) is not None


def _send_email(cfg: dict, p: dict) -> bool:
    """Local SMTP. Cloud-synced nodes get the richer cloud email too; this
    is the self-hosted path so a nocloud node is not silent."""
    host, addr = _s(cfg, "smtp_host"), _s(cfg, "email_address")
    if not (host and addr):
        return False
    try:
        import smtplib
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["Subject"] = "%s: %s" % (_title(p),
                                     (p["command"] or p["tool_name"])[:80])
        msg["From"] = _s(cfg, "smtp_from") or addr
        msg["To"] = addr
        msg.set_content("%s\n\nApprove: %s\nDeny: %s\n"
                        % (_plain(p), p["approve_url"], p["deny_url"]))
        port = int(cfg.get("smtp_port") or 587)
        if port == 465:
            srv = smtplib.SMTP_SSL(host, port, timeout=_TIMEOUT_S)
        else:
            srv = smtplib.SMTP(host, port, timeout=_TIMEOUT_S)
        with srv:
            if port != 465:
                try:
                    srv.starttls()
                except Exception:
                    pass
            user, pw = _s(cfg, "smtp_user"), _s(cfg, "smtp_password")
            if user and pw:
                srv.login(user, pw)
            srv.send_message(msg)
        return True
    except Exception as exc:
        logger.warning("approval email failed: %s", exc)
        return False


def _send_phone(cfg: dict, p: dict) -> bool:
    """Outbound Twilio voice call announcing the approval.

    Locally this NOTIFIES only: "press 1 to approve" needs Twilio to POST
    the DTMF digits back to a public URL, which a laptop behind NAT does
    not have. Cloud-synced nodes get the full press-1 flow from the cloud
    (routes/cloud.py:_trigger_approval_call). Announce + link is still the
    difference between noticing in 10 seconds and noticing in an hour.
    """
    sid, tok = _s(cfg, "twilio_account_sid"), _s(cfg, "twilio_auth_token")
    frm, to = _s(cfg, "twilio_from"), _s(cfg, "phone_number")
    if not (sid and tok and frm and to):
        return False
    say = ("ClawMetry. %s wants to run %s. Open ClawMetry to approve or deny."
           % (p["runtime_label"], (p["command"] or p["tool_name"])[:120]))
    twiml = "<Response><Say>%s</Say><Pause length=\"1\"/><Say>%s</Say></Response>" % (
        _xml_escape(say), _xml_escape("Repeating. " + say))
    return _post(
        "https://api.twilio.com/2010-04-01/Accounts/%s/Calls.json" % sid,
        {"From": frm, "To": to, "Twiml": twiml},
        form=True, basic_auth=(sid, tok)) is not None


def _xml_escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


_SENDERS = {
    "telegram": _send_telegram,
    "slack": _send_slack,
    "discord": _send_discord,
    "webhook": _send_webhook,
    "pagerduty": _send_pagerduty,
    "whatsapp": _send_whatsapp,
    "email": _send_email,
    "phone": _send_phone,
}


# ── fan-out ────────────────────────────────────────────────────────────────

def resolve_targets(runtime: str, cfg: "dict | None" = None) -> list:
    """Channels this runtime's approvals should go to, right now."""
    row = route_for(runtime)
    if not row.get("enabled"):
        return []
    have = configured_channels(cfg)
    want = row.get("channels") or []
    if not want:
        return have          # nothing chosen → everything configured
    return [c for c in want if c in have]


def notify_pending(approval: dict, *, blocking: bool = False) -> list:
    """Page the human. Returns the channels delivered to.

    ``blocking=False`` (default) hands the fan-out to a daemon thread so
    the pre-tool gate answers Claude Code immediately; the approval is
    already parked by then, so nothing is lost if a vendor is slow.
    """
    try:
        p = build_payload(approval)
    except Exception as exc:
        logger.warning("approval payload build failed: %s", exc)
        return []
    cfg = load_channel_config()
    targets = resolve_targets(p["runtime"], cfg)
    if not targets:
        return []
    if not blocking:
        t = threading.Thread(target=_fan_out, args=(targets, cfg, p),
                             daemon=True, name="approval-notify")
        t.start()
        return targets
    return _fan_out(targets, cfg, p)


def _fan_out(targets: list, cfg: dict, p: dict) -> list:
    sent = []
    for ch in targets:
        fn = _SENDERS.get(ch)
        if fn is None:
            continue
        try:
            if fn(cfg, p):
                sent.append(ch)
        except Exception as exc:
            logger.warning("approval notify via %s failed: %s", ch, exc)
    if sent:
        logger.info("approval %s paged %s", p["id"][:8], ",".join(sent))
    return sent


def notify_resolved(approval_id: str, decision: str,
                    resolver: str = "") -> None:
    """Close the loop on channels that can be edited (Telegram today).

    Best-effort and silent: the decision is already recorded, this is only
    so the phone message stops showing live buttons.
    """
    try:
        meta = message_meta(str(approval_id), "telegram")
        if not meta:
            return
        cfg = load_channel_config()
        token = _s(cfg, "telegram_bot_token")
        if not token:
            return
        mark = "✅ Approved" if decision in ("approve", "allow", "approved") \
            else "⛔ Denied"
        if resolver:
            mark += " · %s" % resolver
        _post("https://api.telegram.org/bot%s/editMessageReplyMarkup" % token,
              {"chat_id": meta.get("chat_id"),
               "message_id": meta.get("message_id"),
               "reply_markup": {"inline_keyboard": [[
                   {"text": mark, "callback_data": "cma:done"}]]}})
    except Exception:
        pass
