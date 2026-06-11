"""
clawmetry/narrator.py -- LLM-narrated alert enrichment (issue #1412, Feature C).

Reuses the Anthropic-direct / relay credential path from clawmetry/insights.py
so no new auth surface is needed. Call narrate() just before dispatching an
alert; it returns a 1-3 sentence human-readable explanation or None when the
LLM is unavailable, timed out, or coalesced — in which case the raw message
is used unchanged.

Public API:
    narrate(event_type, context_dict, *, timeout_secs=5.0) -> str | None
    is_enabled() -> bool
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from typing import Any

log = logging.getLogger("clawmetry.narrator")

# Haiku is fast and cheap; override with CLAWMETRY_NARRATOR_MODEL.
_MODEL = os.environ.get("CLAWMETRY_NARRATOR_MODEL", "claude-haiku-4-5-20251001")
_MAX_TOKENS = 200
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
# Context payload capped at 1 500 chars to keep token use predictable.
_CONTEXT_CHAR_LIMIT = 1500

# Per-(event_type, session/rule id) coalesce window. If the same alert fires
# 5 times in 60s, only the first gets narrated; the rest fall back to raw.
_COALESCE_WINDOW_SECS = 60.0
_coalesce_lock = threading.Lock()
_coalesce_last: dict[str, float] = {}

# Per-event-type system prompts.  {context} is replaced with JSON of the
# context dict passed by the caller.
_PROMPTS: dict[str, str] = {
    "threshold": (
        "You are a concise AI agent observability assistant. A cost-threshold alert just fired.\n"
        "Based on the data below, write 1-3 sentences explaining what happened and suggest "
        "1-2 actionable next steps. Use concrete numbers. No preamble.\n\nData:\n{context}"
    ),
    "loop": (
        "You are a concise AI agent observability assistant. An agent stuck-loop was detected.\n"
        "Based on the data below, write 1-3 sentences explaining what the agent was doing and "
        "suggest 1-2 actionable next steps. Be specific. No preamble.\n\nData:\n{context}"
    ),
    "anomaly": (
        "You are a concise AI agent observability assistant. A usage anomaly was detected.\n"
        "Based on the data below, write 1-3 sentences explaining the spike and suggest "
        "1-2 actionable next steps. Use concrete numbers. No preamble.\n\nData:\n{context}"
    ),
    "approval_timeout": (
        "You are a concise AI agent observability assistant. An approval request timed out.\n"
        "Based on the data below, write 1-3 sentences explaining what was waiting for approval "
        "and what the operator should do now. No preamble.\n\nData:\n{context}"
    ),
}
_DEFAULT_PROMPT = (
    "You are a concise AI agent observability assistant. An alert fired.\n"
    "Based on the data below, write 1-3 sentences explaining what happened and suggest "
    "1-2 actionable next steps. No preamble.\n\nData:\n{context}"
)


def is_enabled() -> bool:
    v = os.environ.get("CLAWMETRY_NARRATOR_ENABLED", "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def _coalesce_key(event_type: str, context: dict) -> str:
    """Stable key for the coalesce window — event type + session/rule id."""
    identity = (
        context.get("session_id")
        or context.get("rule_id")
        or context.get("alert_type")
        or ""
    )
    return f"{event_type}:{identity}"


def _check_coalesce(event_type: str, context: dict) -> bool:
    """Return True if narration should proceed, False if within coalesce window."""
    key = _coalesce_key(event_type, context)
    now = time.monotonic()
    with _coalesce_lock:
        last = _coalesce_last.get(key, 0.0)
        if now - last < _COALESCE_WINDOW_SECS:
            return False
        _coalesce_last[key] = now
    return True


def _resolve_api_key() -> str | None:
    """Reuse insights.py credential resolution so we inherit the same key."""
    try:
        from clawmetry.insights import _resolve_synthesis_credential, load_config
        mode, secret = _resolve_synthesis_credential(load_config())
        if mode == "direct" and secret:
            return secret
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY", "").strip() or None


def narrate(
    event_type: str,
    context: dict[str, Any],
    *,
    timeout_secs: float = 5.0,
) -> str | None:
    """Return an LLM-narrated alert string, or None on any failure/skip.

    Guaranteed never to raise — callers should use the returned value when
    truthy and fall back to the original raw message otherwise.
    """
    if not is_enabled():
        return None
    try:
        if not _check_coalesce(event_type, context):
            log.debug("narrator: coalesced %s", event_type)
            return None
        api_key = _resolve_api_key()
        if not api_key:
            return None
        prompt_tmpl = _PROMPTS.get(event_type, _DEFAULT_PROMPT)
        context_str = json.dumps(context, default=str, indent=2)[:_CONTEXT_CHAR_LIMIT]
        prompt = prompt_tmpl.format(context=context_str)
        body = {
            "model": _MODEL,
            "max_tokens": _MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        req = urllib.request.Request(
            _ANTHROPIC_URL,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "anthropic-version": _ANTHROPIC_VERSION,
                "x-api-key": api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_secs) as resp:
            data = json.loads(resp.read().decode())
        blocks = data.get("content") or []
        text = "".join(
            b.get("text", "") for b in blocks if isinstance(b, dict)
        ).strip()
        if text:
            log.debug("narrator: narrated %s (%d chars)", event_type, len(text))
        return text or None
    except Exception as exc:
        log.debug("narrator: failed for %s: %s", event_type, exc)
        return None
