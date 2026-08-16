"""Telegram inbound decisions — approve or deny from the phone message.

Telegram is the only channel that can carry a real decision back to a
self-hosted node with no public endpoint: the bot API's ``getUpdates`` is
an OUTBOUND long poll, so the daemon reaches out and collects button
presses. Slack/WhatsApp interactive callbacks need an inbound HTTPS route,
which is why those channels ship a decision link instead (see
approval_notify's channel table).

Runs as a daemon thread (started from sync.py's main loop). Each tick:

  1. long-poll ``getUpdates`` (offset-committed, ``callback_query`` only),
  2. for each press, verify it came from the configured chat,
  3. resolve the approval in DuckDB — first press wins, exactly the same
     ``update_approval_decision`` transition the dashboard button uses,
  4. answer the callback and swap the buttons for the verdict.

ONE POLLER PER BOT TOKEN: Telegram allows a single ``getUpdates`` consumer
per bot. If the user's own tooling already polls that bot, Telegram
answers 409 Conflict — we stop cleanly and record the reason so the
Notifications tab can say "use a separate bot for approvals" instead of
silently fighting over updates.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.parse
import urllib.request

logger = logging.getLogger("clawmetry.approval_inbound")

_STATE_PATH = os.path.expanduser("~/.clawmetry/approval_inbound.json")
_LONG_POLL_S = 25
_HTTP_TIMEOUT_S = _LONG_POLL_S + 10
_IDLE_SLEEP_S = 30.0        # nothing configured — re-check config this often
_CONFLICT_BACKOFF_S = 900.0  # someone else owns this bot token

_CALLBACK_PREFIX = "cma:"


# ── poller state (offset + last error, surfaced in /api/approvals/routing) ──

def _load_state() -> dict:
    try:
        with open(_STATE_PATH, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(**fields) -> None:
    try:
        state = _load_state()
        state.update(fields)
        os.makedirs(os.path.dirname(_STATE_PATH), exist_ok=True)
        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.replace(tmp, _STATE_PATH)
    except Exception:
        pass


def poller_status() -> dict:
    """What the UI shows under the Telegram channel."""
    state = _load_state()
    return {
        "running": bool(state.get("running")),
        "last_poll_at": state.get("last_poll_at"),
        "last_error": state.get("last_error"),
        "decisions": int(state.get("decisions") or 0),
    }


# ── telegram plumbing ──────────────────────────────────────────────────────

def _api(token: str, method: str, params: "dict | None" = None,
         timeout: float = 10.0):
    url = "https://api.telegram.org/bot%s/%s" % (token, method)
    data = urllib.parse.urlencode(
        {k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
         for k, v in (params or {}).items()}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("User-Agent", "clawmetry-approvals")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def _decide(approval_id: str, decision: str, resolver: str) -> bool:
    """Write the verdict through the daemon's own store handle.

    This module only ever runs inside the sync daemon, which owns the
    DuckDB writer lock — so this is a direct call, not a proxy round-trip.
    """
    try:
        from clawmetry import local_store
        store = local_store.get_store()
        updated = store.update_approval_decision(
            approval_id, decision, resolver,
            reason="decided from Telegram")
        return bool(updated)
    except Exception as exc:
        logger.warning("telegram decision write failed: %s", exc)
        return False


def _handle_callback(cb: dict, token: str, chat_id: str) -> None:
    data = str(cb.get("data") or "")
    cb_id = cb.get("id")
    msg = cb.get("message") or {}
    from_chat = str((msg.get("chat") or {}).get("id") or "")
    user = (cb.get("from") or {}).get("username") \
        or (cb.get("from") or {}).get("first_name") or "telegram"

    def _answer(text: str, alert: bool = False) -> None:
        try:
            _api(token, "answerCallbackQuery",
                 {"callback_query_id": cb_id, "text": text[:180],
                  "show_alert": alert})
        except Exception:
            pass

    if not data.startswith(_CALLBACK_PREFIX):
        return
    # Only the chat we were configured to talk to may decide. A bot added
    # to another group must never be able to approve this node's tool calls.
    if chat_id and from_chat and from_chat != str(chat_id):
        _answer("Not authorised for this chat.", alert=True)
        logger.warning("telegram approval press from unexpected chat %s",
                       from_chat)
        return
    parts = data.split(":")
    if len(parts) < 3:
        _answer("Already handled.")
        return
    approval_id, verdict = parts[1], parts[2]
    if verdict not in ("approve", "deny"):
        _answer("Unknown action.")
        return
    ok = _decide(approval_id, verdict, "telegram:%s" % user)
    if ok:
        _save_state(decisions=int(_load_state().get("decisions") or 0) + 1)
        mark = "✅ Approved by %s" % user if verdict == "approve" \
            else "⛔ Denied by %s" % user
        _answer("Approved — the agent is continuing." if verdict == "approve"
                else "Denied.")
    else:
        mark = "⏱ Already decided"
        _answer("This one was already decided.")
    try:
        _api(token, "editMessageReplyMarkup", {
            "chat_id": from_chat or chat_id,
            "message_id": msg.get("message_id"),
            "reply_markup": {"inline_keyboard": [[
                {"text": mark, "callback_data": "cma:done"}]]}})
    except Exception:
        pass


# ── the loop ───────────────────────────────────────────────────────────────

def _telegram_creds():
    """(token, chat_id) when Telegram is configured AND some runtime routes
    approvals to it — otherwise (None, None) so we never poll for nothing."""
    try:
        from clawmetry import approval_notify as an
        cfg = an.load_channel_config()
        token = str(cfg.get("telegram_bot_token") or "").strip()
        chat = str(cfg.get("telegram_chat_id") or "").strip()
        if not (token and chat):
            return None, None
        routes = an.load_routes()
        if not routes.get("enabled"):
            return None, None
        rows = [routes.get("default") or {}] + list(
            (routes.get("runtimes") or {}).values())
        for row in rows:
            chans = row.get("channels") or []
            if not chans or "telegram" in chans:
                return token, chat
        return None, None
    except Exception:
        return None, None


def poll_once(token: str, chat_id: str) -> str:
    """One long-poll cycle. Returns 'ok', 'conflict', or 'error'."""
    offset = _load_state().get("offset")
    params = {"timeout": _LONG_POLL_S,
              "allowed_updates": ["callback_query"]}
    if offset:
        params["offset"] = int(offset)
    try:
        resp = _api(token, "getUpdates", params, timeout=_HTTP_TIMEOUT_S)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if code == 409:
            _save_state(last_error="another process is polling this bot "
                                   "(409 Conflict) — use a separate bot "
                                   "token for approvals", running=False)
            return "conflict"
        _save_state(last_error=str(exc)[:200])
        return "error"
    if not resp.get("ok"):
        _save_state(last_error=str(resp.get("description"))[:200])
        return "error"
    updates = resp.get("result") or []
    highest = offset
    for upd in updates:
        try:
            highest = int(upd.get("update_id", 0)) + 1
            cb = upd.get("callback_query")
            if cb:
                _handle_callback(cb, token, chat_id)
        except Exception as exc:
            logger.warning("telegram update handling failed: %s", exc)
    _save_state(offset=highest, last_error=None,
                last_poll_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                running=True)
    return "ok"


def inbound_loop(stop_event: "threading.Event | None" = None) -> None:
    """Daemon thread body. Never raises; never exits on its own."""
    logger.info("approval inbound poller started")
    while not (stop_event and stop_event.is_set()):
        token, chat = _telegram_creds()
        if not token:
            _save_state(running=False)
            _sleep(_IDLE_SLEEP_S, stop_event)
            continue
        result = poll_once(token, chat)
        if result == "conflict":
            _sleep(_CONFLICT_BACKOFF_S, stop_event)
        elif result == "error":
            _sleep(10.0, stop_event)


def _sleep(seconds: float, stop_event) -> None:
    if stop_event is not None:
        stop_event.wait(seconds)
    else:
        time.sleep(seconds)


def start(stop_event=None) -> "threading.Thread | None":
    """Start the poller once per process. Returns the thread (or None when
    it is already running)."""
    global _THREAD
    if _THREAD is not None and _THREAD.is_alive():
        return None
    _THREAD = threading.Thread(target=inbound_loop, args=(stop_event,),
                               daemon=True, name="approval-inbound")
    _THREAD.start()
    return _THREAD


_THREAD = None
