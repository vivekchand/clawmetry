"""OpenClaw public-share state (issue #5746).

OpenClaw 2026.9.3 lets a session owner publish a **revocable, read-only
public link** to a session's existing *and future* conversation text
(openclaw#139489). That is an exposure signal Guard and the security
posture should be able to see, so ClawMetry records whether a session is
published — and nothing else about it.

Three facts about the upstream shape drive every decision in here.

**1. It is not on ``sessions.list``.** ``publicShare`` is listed in
OpenClaw's ``PRIVATE_SESSION_ENTRY_KEYS`` and every session entry is run
through ``stripPrivateSessionEntryFields()`` before it leaves the
gateway. Reading a session list — ours or the gateway's — will never
surface it. The read method that carries it is ``session.members.list``
(scope ``operator.read``, since 2026.7), addressed one session at a
time::

    session.members.list {sessionKey, agentId?}
      -> {sessionKey, publicShare?, owner?, members[], identities[],
          role, allowedVisibilities[]}

**2. The payload is a live credential.** The upstream schema is::

    publicShare = {token: /^v1\\.[A-Za-z0-9_-]+$/ (<=7000), createdAt: int}

``token`` *is* the public link — OpenClaw builds the shareable URL
directly from it. Storing it would put a working read capability for the
user's conversation into DuckDB and into the E2E-encrypted cloud
snapshot, which is a strictly worse exposure than the one we are trying
to report on. So this module lifts ``bool(publicShare)`` and
``createdAt`` and deliberately never returns, logs, or stores the token.
:func:`share_fields` is the only place that reads the upstream object,
and it is the enforcement point for that rule.

**3. Not knowing is not the same as "not shared".** Because the probe is
a per-session RPC it can fail, be out of scope, be capped out, or be
unavailable entirely (cloud containers have no gateway). #5746 is filed
as a high-severity exposure gap, so reporting a confident ``isShared:
false`` for a session we never actually asked about would be the worst
available answer — Guard would show a publicly-linked transcript as
private. Where the answer is unknown the field is **omitted**, and the
read helpers below leave the payload untouched.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Iterable, Mapping

logger = logging.getLogger("clawmetry.adapters.openclaw_share")

#: Gateway read method that carries ``publicShare`` (scope ``operator.read``).
SHARE_RPC_METHOD = "session.members.list"

#: Metadata keys written into ``sessions.metadata`` by the daemon. Kept
#: short and snake_case to match the other keys in that blob.
META_SHARED = "shared"
META_SHARE_CREATED_AT = "share_created_at"

#: Upper bound on probes per sync pass. A backfill can flush hundreds of
#: sessions at once and each probe is a serialised WebSocket round-trip;
#: without a cap the first sync after an install would spend minutes in
#: the gateway. Sessions past the cap are left unknown, not false.
_DEFAULT_MAX_PROBES = 60


def _max_probes() -> int:
    try:
        return max(0, int(os.environ.get("CLAWMETRY_OPENCLAW_SHARE_MAX", "")
                          or _DEFAULT_MAX_PROBES))
    except (TypeError, ValueError):
        return _DEFAULT_MAX_PROBES


def _created_at_seconds(value: Any) -> float | None:
    """``publicShare.createdAt`` as epoch seconds, or ``None``.

    Upstream types it as a bare ``Integer(minimum: 0)`` rather than one of
    OpenClaw's ``*Ms``-suffixed fields, so the unit is not self-evident
    from the schema. Rather than assume milliseconds, apply the same
    magnitude test the rest of this repo uses (``routes/agents.py``
    ``_ts_to_seconds``): anything past 1e12 is milliseconds. That is
    correct for both spellings instead of correct for one guess.
    """
    if isinstance(value, bool) or value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if num <= 0:
        return None
    return num / 1000.0 if num > 1e12 else num


def share_fields(share: Any) -> dict[str, Any]:
    """Project one upstream ``publicShare`` object into what we may keep.

    Returns ``{"shared": bool}`` plus ``share_created_at`` when the
    timestamp is usable. **The token is never included** — see the module
    docstring; this function is the single point where the upstream object
    is read, so the rule is enforced in one place rather than trusted to
    every caller.
    """
    if not isinstance(share, Mapping):
        return {META_SHARED: False}
    fields: dict[str, Any] = {META_SHARED: True}
    created = _created_at_seconds(share.get("createdAt"))
    if created is not None:
        fields[META_SHARE_CREATED_AT] = created
    return fields


def fetch_share_state(
    session_keys: Iterable[str],
    rpc: Callable[[str, dict], Any] | None = None,
    agent_id: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Probe the gateway for the share state of ``session_keys``.

    Daemon-side only: this makes one ``session.members.list`` call per
    session key, serialised through the gateway WebSocket. Returns a dict
    keyed by session key; **a key is absent when we could not get an
    answer**, which the callers below render as "unknown" rather than
    "not shared".

    ``rpc`` is injected in tests; by default the shared gateway helper is
    used. Never raises — a gateway that is down, unauthorised, or running
    a version without the method yields an empty result and the daemon
    carries on.
    """
    keys = [str(k) for k in session_keys if k]
    if not keys:
        return {}
    if rpc is None:
        try:
            from helpers.gateway import _gw_ws_rpc as rpc  # type: ignore
        except Exception as exc:
            logger.debug("share probe unavailable (no gateway helper): %s", exc)
            return {}

    limit = _max_probes()
    if limit <= 0:
        return {}
    if len(keys) > limit:
        logger.debug(
            "share probe capped at %d of %d sessions "
            "(raise CLAWMETRY_OPENCLAW_SHARE_MAX to widen)", limit, len(keys)
        )
        keys = keys[:limit]

    out: dict[str, dict[str, Any]] = {}
    answered = 0
    for key in keys:
        params: dict[str, Any] = {"sessionKey": key}
        if agent_id:
            params["agentId"] = agent_id
        try:
            payload = rpc(SHARE_RPC_METHOD, params)
        except Exception as exc:  # a wedged socket must not sink the pass
            logger.debug("share probe failed for %s: %s", key[:12], exc)
            continue
        if not isinstance(payload, Mapping):
            # None = RPC error/timeout/unknown method. Unknown, not false.
            continue
        answered += 1
        out[key] = share_fields(payload.get("publicShare"))
    if keys and not answered:
        _warn_all_probes_failed()
    return out


_warned_no_answer = False


def _warn_all_probes_failed() -> None:
    """Say once why the share column is empty.

    ``_gw_ws_rpc`` collapses every failure to ``None``, so we cannot tell a
    scope denial from a timeout here. The overwhelmingly common cause is the
    known v4 gateway scope gap: a raw bearer token connects fine but is
    granted no scopes, and ``session.members.list`` (``operator.read``) comes
    back FORBIDDEN — the same reason the Sessions and Crons tabs read empty
    against such a gateway. Without this line the feature looks like it
    simply found nothing, which is the one reading that is never true.
    """
    global _warned_no_answer
    if _warned_no_answer:
        return
    _warned_no_answer = True
    logger.warning(
        "openclaw share state unavailable: no session answered %s. "
        "Sessions will read as UNKNOWN (never as 'not shared'). Most often "
        "the gateway token carries no operator.read scope.",
        SHARE_RPC_METHOD,
    )


def share_extra(meta: Any) -> dict[str, Any]:
    """UI ``extra`` fields for one session, from its stored metadata.

    Returns an empty dict when the daemon has not recorded a share verdict
    for this session, so an unknown stays unknown all the way to the UI.
    """
    if not isinstance(meta, Mapping) or META_SHARED not in meta:
        return {}
    shared = bool(meta.get(META_SHARED))
    extra: dict[str, Any] = {"isShared": shared}
    if not shared:
        return extra
    created = _created_at_seconds(meta.get(META_SHARE_CREATED_AT))
    if created is not None:
        extra["shareCreatedAt"] = created
    # Describes the upstream feature, not something we measured: the
    # published view is read-only and omits tools, reasoning and files.
    extra["shareVisibility"] = "public-read-only"
    return extra


def apply_share_state(sessions: Iterable[Any], meta_by_id: Mapping[str, Any]) -> None:
    """Stamp share fields onto adapter :class:`Session` objects in place."""
    for session in sessions:
        extra = share_extra(meta_by_id.get(str(getattr(session, "id", ""))))
        if not extra:
            continue
        if not isinstance(getattr(session, "extra", None), dict):
            session.extra = {}
        session.extra.update(extra)


def apply_share_state_to_payloads(payloads: Iterable[Any]) -> None:
    """Stamp share fields onto local-store session payload dicts in place.

    Each payload is expected to carry its stored ``metadata`` under
    ``_metadata`` (set by the caller in ``routes/agents.py``); the key is
    popped so it never reaches the wire.
    """
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        extra = share_extra(payload.pop("_metadata", None))
        if not extra:
            continue
        existing = payload.get("extra")
        payload["extra"] = {**existing, **extra} if isinstance(existing, dict) else extra
