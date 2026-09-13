"""clawmetry/ingest_auth.py -- the gate in front of the ingest surfaces.

Why this exists
---------------
Until now an agent could only be observed by ClawMetry if the daemon ran
on the same machine as the agent. ``/v1/{logs,metrics,traces}`` trusted
loopback and otherwise wanted the OpenClaw gateway token, and the custom
runtime write API trusted loopback or one static secret shared by the
whole install. Neither is something you can hand to a CI job, a
container, a Lambda or a teammate, so the agents that run there were
simply invisible.

This module adds one more way in: a scoped, revocable ingest key
(``clawmetry key create --scope write:ingest``). It does not replace the
existing paths. Loopback still works with no key at all, and the gateway
token still works exactly as it did -- this is a door, not a relocation.

The posture, stated plainly
---------------------------
* **An ingest key can only push.** ``write:ingest`` grants no ``q/1``
  shape (``granted_shapes`` returns an empty set for it), so a leaked
  ingest key cannot read a prompt, a cost or a session back out.
* **No CORS, ever.** Ingest is server-to-server and POST-only. This
  module never emits an ``Access-Control-Allow-Origin`` header and
  ``apikeys.create`` refuses to put a browser origin on an ingest key,
  so a page cannot hold one usefully. That is deliberate: the whole
  protection ``routes/public_api.py`` buys is the browser refusing to
  let a page read a reply, and a write surface should not be the place
  it gets handed back.
* **One gate, not two.** ``dashboard.py::_check_auth`` steps aside for a
  request that presents a key, the same way it does for ``/api/q/``, so
  the check here is the only one. Two gates on one path is how a request
  ends up accepted by the wrong one.

Routing
-------
A pushed event carries no filesystem layout to infer a runtime from, so
the pusher says which runtime it is and (optionally) which environment,
in headers. Both are resolved once per request and stamped on every
event in it. ``x-clawmetry-env`` is the single grouping axis above
runtime -- deliberately one axis and not a dataset/collection/tag
taxonomy, because that taxonomy is what a log platform needs and an
agent platform does not.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

logger = logging.getLogger("clawmetry.ingest_auth")

# The header names and the body cap are declared ONCE, in
# ``clawmetry/ingest_contract.py``, and re-exported here. The doc, the
# setup prompts and the landing reference are generated from that same
# declaration, so the thing the server enforces and the thing we tell
# people to send cannot drift apart -- which matters most for the setup
# prompts, where a wrong header name is a silent failure an agent will
# write confidently.
from clawmetry.ingest_contract import (  # noqa: F401  (re-exported)
    HEADER_ENV,
    HEADER_KEY,
    HEADER_RUNTIME,
    MAX_BODY_BYTES,
)

#: A runtime name we have never heard of is allowed -- in-house engines
#: are a supported case -- but it still has to be a name, not a payload.
_RUNTIME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
_ENV_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")


def _err(code: str, message: str, status: int) -> tuple:
    """One error shape for every rejection.

    ``message`` is a sentence for a person. A bare error code with no
    sentence is the thing a user should never be shown -- they are
    usually looking at it inside an agent's terminal output, with no
    documentation open.
    """
    return {"error": code, "message": message}, status


def presented_key(headers) -> str:
    """The raw key string from the request, or ``""``."""
    return (headers.get(HEADER_KEY) or "").strip()


def authenticate(headers) -> tuple:
    """``(record, None)`` when a live ingest key is presented, else
    ``(None, (body, status))``.

    Callers that reach this function have already been let past
    ``_check_auth`` on the strength of the header being present, so a
    bad key must be rejected here or it is not rejected anywhere.
    """
    from clawmetry import apikeys

    presented = presented_key(headers)
    if not presented:
        return None, _err(
            "unauthorized",
            f"This endpoint needs an ingest key in the {HEADER_KEY} header. "
            "Create one with: clawmetry key create --name ci "
            "--scope write:ingest --origin none",
            401,
        )
    record = apikeys.verify(presented)
    if not record:
        logger.warning("ingest: rejected key %s", apikeys.redact(presented))
        return None, _err(
            "unauthorized",
            "That ingest key is not valid on this ClawMetry. It may have "
            "been revoked, or it may belong to a different install.",
            401,
        )
    if not apikeys.allows_ingest(record):
        return None, _err(
            "forbidden",
            f"Key {record.get('name') or record.get('id')} may read, but it "
            "cannot push. Create a separate key with "
            "--scope write:ingest --origin none.",
            403,
        )
    apikeys.touch(record.get("id") or "")
    return record, None


def resolve_runtime(headers) -> tuple:
    """``(runtime, None)`` or ``(None, (body, status))``.

    ``None`` for the runtime means "the pusher did not say", which is
    fine: the OTLP path already derives a runtime from the resource's
    ``service.name``. The header, when present, wins -- an explicit
    statement by the pusher beats a value inferred from a field that
    exists for a different purpose.
    """
    raw = (headers.get(HEADER_RUNTIME) or "").strip().lower()
    if not raw:
        return None, None
    if not _RUNTIME_RE.match(raw):
        return None, _err(
            "bad_runtime",
            f"{HEADER_RUNTIME} must be a short name like claude_code or "
            "my-engine: lower-case letters, digits, underscore and dash, "
            "40 characters at most.",
            400,
        )
    return raw, None


def resolve_env(headers) -> tuple:
    """``(env, None)`` or ``(None, (body, status))``. ``None`` is fine."""
    raw = (headers.get(HEADER_ENV) or "").strip().lower()
    if not raw:
        return None, None
    if not _ENV_RE.match(raw):
        return None, _err(
            "bad_env",
            f"{HEADER_ENV} must be a short label like production or "
            "team-a.staging: lower-case letters, digits, dot, underscore "
            "and dash, 64 characters at most.",
            400,
        )
    return raw, None


def check_size(body: Any) -> Optional[tuple]:
    """``None`` when the body fits, else ``(body, 413)``.

    Checked before decode: a 40 MB protobuf should be refused with a
    sentence, not parsed and then rejected by whatever runs out of
    patience first.
    """
    try:
        size = len(body or b"")
    except TypeError:
        return None
    if size > MAX_BODY_BYTES:
        mb = MAX_BODY_BYTES // (1024 * 1024)
        return _err(
            "payload_too_large",
            f"That request is {size // (1024 * 1024)} MB and the limit is "
            f"{mb} MB. Split the batch and send it in parts; compressing "
            "with Content-Encoding: gzip also helps.",
            413,
        )
    return None


def prologue(headers, body) -> tuple:
    """Everything the ingest surfaces check, in one call.

    Returns ``(context, None)`` or ``(None, (body, status))``. The
    context is ``{"key": record|None, "runtime": str|None,
    "env": str|None}``; ``key`` is ``None`` for a request that got in on
    loopback or the gateway token, which stays legal.
    """
    err = check_size(body)
    if err:
        return None, err

    record = None
    if presented_key(headers):
        record, err = authenticate(headers)
        if err:
            return None, err

    runtime, err = resolve_runtime(headers)
    if err:
        return None, err
    env, err = resolve_env(headers)
    if err:
        return None, err

    return {"key": record, "runtime": runtime, "env": env}, None
