"""Opt-in pull of Cursor cloud-agent usage, with the operator's own key.

The PULL half of delegated usage (see ``clawmetry.delegated_usage``). A Grok
Bot hands work to Cursor cloud agents that belong to the operator; Cursor
meters them and will report the token split per agent. This asks for it.

This is the one place the product makes an authenticated outbound call to a
third party on the operator's behalf, so the rules are tighter than anywhere
else:

* **Opt-in only.** With no key configured, nothing here ever makes a request.
  There is no default endpoint to fall back to and no key to inherit.
* **The operator supplies the key.** It is stored locally, is never included
  in a synchronised snapshot, and is never logged -- not at debug, not in an
  error path. Only its last four characters are ever displayed.
* **Bounded to what we already saw.** We ask about agent ids that appeared in
  a transcript on THIS machine. There is a ``GET /v1/agents`` list endpoint and
  we deliberately do not call it: enumerating the operator's whole Cursor
  account would pull in agents that have nothing to do with any local session,
  and on a team key, other people's.
* **Never on a request path.** Called from the daemon, on a cadence. A user
  waiting for a page must never be waiting on Cursor.

Verified against Cursor's published API docs (2026-08-27):

* Base URL ``https://api.cursor.com``; ``Authorization: Bearer <key>``.
* ``GET /v1/agents/{id}/usage`` -> ``inputTokens``, ``outputTokens``,
  ``cacheWriteTokens``, ``cacheReadTokens``, ``totalTokens``.
* The agent object itself carries NO model and NO cost, which is why cost here
  is derived from the token split and usually labelled ``estimated``.
* Cursor's free tier cannot use this API at all; any paid plan can. That gate
  is Cursor's and offering this feature on our entry tier does not widen it.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.parse
from typing import Any

from clawmetry.delegated_usage import (
    CURSOR,
    SOURCE_API,
    DelegatedUsage,
    get_store,
    is_delegated_agent_id,
)

logger = logging.getLogger("clawmetry.cursor_connector")

_DEFAULT_API_BASE = "https://api.cursor.com"
_ALLOWED_API_SCHEME = "https"
_ALLOWED_API_HOST = "api.cursor.com"

API_BASE = os.environ.get("CLAWMETRY_CURSOR_API_BASE", _DEFAULT_API_BASE)
_KEY_ENV = "CLAWMETRY_CURSOR_API_KEY"
_TIMEOUT = 15

#: Cursor documents "standard rate limiting" without a number for this family,
#: and other families sit at 20-250/min. We pace well under the floor of that
#: range: this is a background refresh of a figure that changes slowly, and
#: being throttled would be a self-inflicted outage on someone else's service.
_MIN_INTERVAL_SECS = 0.35

#: Re-asking about a finished agent buys nothing. Cursor remains the system of
#: record; this is a cache with an honest refresh window.
_REFRESH_AFTER_SECS = 900


def key_path() -> str:
    raw = os.environ.get("CLAWMETRY_CURSOR_KEY_PATH", "~/.clawmetry/cursor.json")
    return os.path.realpath(os.path.expanduser(raw))


def load_key() -> str:
    """The operator's Cursor API key, or "" if they have not opted in."""
    env = (os.environ.get(_KEY_ENV) or "").strip()
    if env:
        return env
    try:
        with open(key_path(), encoding="utf-8") as fh:
            return str(json.load(fh).get("apiKey") or "").strip()
    except (OSError, ValueError):
        return ""


def save_key(api_key: str) -> str:
    """Persist the key 0600. Returns the masked form for display."""
    api_key = (api_key or "").strip()
    if not api_key:
        raise ValueError("empty api key")
    path = key_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Written 0600 BEFORE the secret lands in it, so there is no window in
    # which the file exists world-readable with a key inside.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        fh = os.fdopen(fd, "w", encoding="utf-8")
    except Exception:
        os.close(fd)
        raise
    with fh:
        json.dump({"apiKey": api_key, "savedAt": time.time()}, fh)
    return mask(api_key)


def save_key_from_file(path: str) -> str:
    """Read a key from ``path`` and store it. Returns ONLY the masked form.

    Exists so a caller never binds the raw secret. The CLI used to read the
    file itself and hand the string over, which put the credential in a local
    variable one ``print`` away from a terminal and a shell history -- exactly
    the shape static analysis flags, and it was right to. Reading, storing and
    masking all happen in here now, and the value that comes back out cannot
    be un-masked.
    """
    resolved = os.path.realpath(os.path.expanduser(path))
    with open(resolved, encoding="utf-8") as fh:
        return save_key(fh.read().strip())


def save_key_from_env() -> str:
    """Store the key named by ``CLAWMETRY_CURSOR_API_KEY``. Masked form out."""
    return save_key((os.environ.get(_KEY_ENV) or "").strip())


def save_key_from_body(payload: "dict[str, object]") -> str:
    """Extract and store the key from an HTTP request payload dict.

    Exists so the route handler never binds the raw secret under a local name.
    Reading, storing and masking all happen here; the value that comes back out
    cannot be un-masked. Mirrors save_key_from_file / save_key_from_env for the
    browser-form path.

    Raises ValueError when the payload carries no non-empty ``apiKey``.
    """
    return save_key(str(payload.get("apiKey") or "").strip())


def masked_key() -> str:
    """The stored key's masked form, or "" when not connected.

    The only key-derived string any caller outside this module may hold.
    """
    key = load_key()
    return mask(key) if key else ""


def is_connected() -> bool:
    return bool(load_key())


def forget_key() -> bool:
    try:
        os.remove(key_path())
        return True
    except OSError:
        return False


def mask(api_key: str) -> str:
    """The only representation of the key that may be displayed or returned."""
    k = (api_key or "").strip()
    return f"…{k[-4:]}" if len(k) >= 4 else "…"


def is_enabled() -> bool:
    return bool(load_key())


def _get(path: str, api_key: str) -> dict[str, Any] | None:
    """One GET. Returns None on any failure. NEVER logs the key or the header."""
    import urllib.error
    import urllib.request

    try:
        parsed = urllib.parse.urlparse(API_BASE)
        if parsed.scheme != _ALLOWED_API_SCHEME or parsed.netloc != _ALLOWED_API_HOST:
            logger.error(
                "cursor api: API_BASE must be %s://%s; blocking outbound call",
                _ALLOWED_API_SCHEME,
                _ALLOWED_API_HOST,
            )
            return None
    except Exception:
        return None

    req = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "clawmetry",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Status only. The response body of an auth failure can echo the
        # credential back, and this line goes to a log file.
        logger.warning("cursor api: %s returned HTTP %s", path, exc.code)
        return None
    except Exception as exc:  # noqa: BLE001 - network is best-effort
        logger.debug("cursor api: %s failed: %s", path, type(exc).__name__)
        return None


def _int(d: dict, *keys: str) -> int:
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return int(v)
    return 0


def fetch_agent_usage(agent_id: str, api_key: str = "") -> DelegatedUsage | None:
    """Ask Cursor what one cloud agent used. None if unavailable."""
    if not is_delegated_agent_id(agent_id):
        return None
    api_key = api_key or load_key()
    if not api_key:
        return None
    body = _get(f"/v1/agents/{urllib.parse.quote(agent_id, safe='')}/usage", api_key)
    if not isinstance(body, dict):
        return None
    # Cursor nests some responses under a data envelope; accept either.
    data = body.get("usage") if isinstance(body.get("usage"), dict) else body
    if not isinstance(data, dict):
        return None
    usage = DelegatedUsage(
        agent_id=agent_id,
        vendor=CURSOR,
        source=SOURCE_API,
        input_tokens=_int(data, "inputTokens", "input_tokens"),
        output_tokens=_int(data, "outputTokens", "output_tokens"),
        cache_read_tokens=_int(data, "cacheReadTokens", "cache_read_tokens"),
        cache_write_tokens=_int(data, "cacheWriteTokens", "cache_write_tokens"),
        updated_at=time.time(),
    )
    # An all-zero response is a real answer ("this agent used nothing yet"),
    # but recording it as usage would put a 0-token row where a reader expects
    # either work or silence. Treat it as nothing to report.
    if usage.total_tokens <= 0:
        return None
    return usage


def sync(limit: int = 200, force: bool = False) -> dict[str, Any]:
    """Refresh usage for the agent ids local transcripts have shown us.

    Returns a summary safe to log and to show: it contains counts and a masked
    key, never the key itself.
    """
    api_key = load_key()
    if not api_key:
        return {"enabled": False, "fetched": 0, "skipped": 0, "reason": "no_api_key"}

    store = get_store()
    targets = sorted(store.observed())[: max(int(limit), 0)]
    now = time.time()
    fetched = skipped = failed = 0
    for agent_id in targets:
        existing = store.get(agent_id)
        if (
            not force
            and existing is not None
            and (now - existing.updated_at) < _REFRESH_AFTER_SECS
        ):
            skipped += 1
            continue
        usage = fetch_agent_usage(agent_id, api_key)
        if usage is None:
            failed += 1
        elif store.record(usage):
            fetched += 1
        time.sleep(_MIN_INTERVAL_SECS)
    return {
        "enabled": True,
        "key": mask(api_key),
        "observed": len(store.observed()),
        "fetched": fetched,
        "skipped": skipped,
        "failed": failed,
    }
