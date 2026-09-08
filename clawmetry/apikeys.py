"""clawmetry/apikeys.py -- scoped, revocable read keys for custom UIs.

Requirement: "Build your own UI: a keyed, scoped read API for custom
dashboards" (64c10afd-038d-4fde-9c55-ddca80aaff1e).

Why this exists
---------------
The dashboard reads your agents through the ``q/1`` query contract. That
contract is a good API: it is declared, versioned, arg-checked and drift
tested. Until now the only thing allowed to call it was the dashboard
itself, because the only gate in front of it was the browser's
same-origin rule. Anyone who wanted a different view of their own data
had to fork the dashboard.

An API key changes that. You create one, say what it may read and which
site may read it, paste it into whatever you are building, and the page
gets exactly that slice. This is the substrate under "build your own UI"
(docs/BUILD_YOUR_OWN_UI.md).

The security posture, stated plainly
------------------------------------
Adding CORS to a localhost service is how local tools get robbed. Any
page in any tab can already SEND a request to ``127.0.0.1:8900``; the
only reason that has been harmless is that the browser refuses to let
the page READ the reply. Handing out ``Access-Control-Allow-Origin``
removes that protection, so it is only ever echoed for an origin the key
holder named. Concretely:

* A key is required. Loopback is NOT trusted here, unlike the rest of
  the dashboard -- ``routes/public_api.py`` is the one surface where
  "the request came from this machine" earns nothing.
* A key carries an origin allowlist and it may not be empty. There is
  no wildcard. A key with no browser origin (a CLI, a cron, a backend)
  is created with ``--origin none`` and simply never gets a CORS header.
* Scopes are least-revealing-first and ``read:content`` is never
  granted implicitly -- it has to be asked for by name.
* Keys are read-only. Nothing in this module can pause, stop or kill an
  agent, and ``routes/public_api.py`` dispatches only ``q/1`` read
  shapes, so this adds nothing to ClawMetry's control plane.

Storage
-------
``~/.clawmetry/api_keys.json``, 0o600, one JSON document. Only the
SHA-256 of the secret is stored, so a stolen file cannot be replayed as
a key and we cannot show a user a key they lost. The wire form is
``cmk_<key_id>_<secret>``: the id is public and appears in listings and
audit lines, the secret never leaves the creating terminal.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Optional

from clawmetry.query_contract import SCOPE_CONTENT, SCOPE_DOC, SCOPES

# ── Shape of the thing ──────────────────────────────────────────────────

#: Wire prefix. Deliberately distinct from ``cm_`` (the cloud node key)
#: and ``sk-ant-`` (a model provider key) so a leaked string is
#: identifiable at a glance by a scanner or by a human reading a log.
KEY_PREFIX = "cmk"

_ID_BYTES = 4        # 8 hex chars: enough to name a key in a listing
_SECRET_BYTES = 32   # 256 bits

STORE_PATH = os.path.expanduser("~/.clawmetry/api_keys.json")
_FILE_MODE = 0o600
_DIR_MODE = 0o700

#: A machine is not a key management product. The cap exists so a runaway
#: script cannot grow the file without bound; it is not a paywall.
MAX_KEYS = 50

#: Sentinel origin meaning "this key is not used from a browser". Stored
#: as an empty origin list; kept as a word so the CLI can say it back.
ORIGIN_NONE = "none"


#: Why a create call was refused. Every message is a literal authored here,
#: and a caller that has to put one in an HTTP response looks it up by code
#: rather than reading it off the exception: text taken from an exception is
#: exception-derived to a static analyser no matter who wrote it, and a
#: const-indexed lookup is the thing that is provably not.
REFUSAL_REASONS: dict = {
    "unknown_scope": (
        "That is not a scope. Choose from: " + ", ".join(SCOPES)
    ),
    "no_scope": (
        "A key needs at least one scope. Choose from: " + ", ".join(SCOPES)
    ),
    "wildcard_origin": (
        "A wildcard origin is not allowed. Any page in any tab could then "
        "read this machine's telemetry. Name the site you are building, for "
        "example https://my-app.vercel.app."
    ),
    "bad_origin": (
        "That is not an origin. An origin is just a scheme, host and port, "
        "with no path or query: https://my-app.vercel.app, or "
        "http://localhost:3000."
    ),
    "no_name": (
        "Give the key a name so you can tell it apart later, for example: "
        "latency-workbench."
    ),
    "name_too_long": "Key names are limited to 64 characters.",
    "at_capacity": (
        f"This machine already has {MAX_KEYS} active keys, which is the "
        "limit. Revoke one you no longer use: clawmetry key revoke <id>"
    ),
}


def message_for(reason: str) -> str:
    """The refusal sentence for ``reason``.

    Looked up from the literal table above, never read off an exception, so
    a caller can put the result in an HTTP response without carrying
    exception-derived text into it.
    """
    return REFUSAL_REASONS.get(
        str(reason), "That key could not be created."
    )


class ApiKeyError(Exception):
    """Raised for a caller mistake (bad scope, bad origin, cap reached).

    Carries a sentence meant for a person, not an error code -- these
    surface directly in ``clawmetry key`` output, where naming the exact
    offending value is worth more than it costs. ``reason`` is the same
    refusal as a stable code, for the HTTP callers that must not echo
    exception text; see :data:`REFUSAL_REASONS`.
    """

    def __init__(self, message: str, reason: str = ""):
        super().__init__(message)
        self.reason = reason


# ── Store I/O ───────────────────────────────────────────────────────────

def _store_path() -> str:
    return os.environ.get("CLAWMETRY_API_KEYS_PATH") or STORE_PATH


def _read_store() -> dict:
    """The stored document, or an empty one. Never raises: a corrupt or
    unreadable file must not take the dashboard down, it must behave as
    "no keys are configured" so every request 401s honestly."""
    try:
        with open(_store_path()) as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {"version": 1, "keys": []}
        keys = data.get("keys")
        if not isinstance(keys, list):
            data["keys"] = []
        return data
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        return {"version": 1, "keys": []}


def _write_store(doc: dict) -> None:
    """Atomically replace the store, 0o600, creating ~/.clawmetry if needed."""
    path = _store_path()
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
        try:
            os.chmod(parent, _DIR_MODE)
        except OSError:
            pass  # NFS home, Windows: best effort, never block a create
    body = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    tmp = path + ".tmp"
    # os.open with the mode arg so umask cannot widen a fresh key file to
    # 0o644. Mirrors clawmetry/license.py::_secure_write.
    fd = os.open(tmp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, _FILE_MODE)
    try:
        os.write(fd, body.encode("utf-8"))
    finally:
        os.close(fd)
    try:
        os.chmod(tmp, _FILE_MODE)
    except OSError:
        pass
    os.replace(tmp, path)


# ── Validation ──────────────────────────────────────────────────────────

def normalise_scopes(scopes) -> list:
    """Return ``scopes`` as a sorted, de-duplicated, validated list.

    Raises :class:`ApiKeyError` naming the offender, because "invalid
    scope" with no name is the kind of message that sends someone to the
    source to find out what they typed wrong.
    """
    out = set()
    for raw in scopes or ():
        s = str(raw).strip()
        if not s:
            continue
        if s not in SCOPES:
            raise ApiKeyError(
                f"{s!r} is not a scope. Choose from: " + ", ".join(SCOPES),
                "unknown_scope",
            )
        out.add(s)
    if not out:
        raise ApiKeyError(
            "A key needs at least one scope. Choose from: " + ", ".join(SCOPES),
            "no_scope",
        )
    # Keep the declared order (least revealing first) rather than
    # alphabetical, so a listing reads the way the docs do.
    return [s for s in SCOPES if s in out]


def normalise_origins(origins) -> list:
    """Validate browser origins down to ``scheme://host[:port]``.

    An origin is what a browser will actually send in the ``Origin``
    header, so anything with a path, a query or a wildcard is rejected
    here rather than silently never matching at request time.
    """
    from urllib.parse import urlsplit

    out = []
    for raw in origins or ():
        o = str(raw).strip().rstrip("/")
        if not o or o.lower() == ORIGIN_NONE:
            continue
        if o == "*":
            raise ApiKeyError(
                "A wildcard origin is not allowed. Any page in any tab could "
                "then read this machine's telemetry. Name the site you are "
                "building, for example https://my-app.vercel.app.",
                "wildcard_origin",
            )
        parts = urlsplit(o)
        if parts.scheme not in ("http", "https"):
            raise ApiKeyError(
                f"{o!r} is not an origin. An origin looks like "
                "https://my-app.vercel.app or http://localhost:3000.",
                "bad_origin",
            )
        if not parts.netloc or parts.path or parts.query or parts.fragment:
            raise ApiKeyError(
                f"{o!r} has a path or query. An origin is just the scheme, "
                "host and port: " + f"{parts.scheme}://{parts.netloc}",
                "bad_origin",
            )
        out.append(f"{parts.scheme}://{parts.netloc}".lower())
    # De-duplicate, keep first-seen order so the user's list reads back
    # the way they typed it.
    seen, uniq = set(), []
    for o in out:
        if o not in seen:
            seen.add(o)
            uniq.append(o)
    return uniq


# ── Create / list / revoke ──────────────────────────────────────────────

def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def create(name: str, scopes, origins, *, note: str = "") -> tuple:
    """Mint a key. Returns ``(record, plaintext_key)``.

    The plaintext is returned once and never stored. Callers show it and
    forget it.
    """
    label = (name or "").strip()
    if not label:
        raise ApiKeyError(
            "Give the key a name so you can tell it apart later, for "
            "example: latency-workbench.",
            "no_name",
        )
    if len(label) > 64:
        raise ApiKeyError("Key names are limited to 64 characters.",
                          "name_too_long")
    scope_list = normalise_scopes(scopes)
    origin_list = normalise_origins(origins)

    doc = _read_store()
    live = [k for k in doc["keys"] if not k.get("revoked_at")]
    if len(live) >= MAX_KEYS:
        raise ApiKeyError(
            f"This machine already has {MAX_KEYS} active keys, which is the "
            "limit. Revoke one you no longer use: clawmetry key revoke <id>",
            "at_capacity",
        )

    key_id = secrets.token_hex(_ID_BYTES)
    secret = secrets.token_urlsafe(_SECRET_BYTES)
    record = {
        "id": key_id,
        "name": label,
        "note": (note or "").strip()[:200],
        "hash": _hash_secret(secret),
        "scopes": scope_list,
        "origins": origin_list,
        "created_at": int(time.time()),
        "last_used_at": None,
        "use_count": 0,
        "revoked_at": None,
    }
    doc["keys"].append(record)
    _write_store(doc)
    return record, f"{KEY_PREFIX}_{key_id}_{secret}"


def list_keys(*, include_revoked: bool = False) -> list:
    """Key records with the hash stripped. Newest first."""
    doc = _read_store()
    rows = [
        {k: v for k, v in rec.items() if k != "hash"}
        for rec in doc["keys"]
        if include_revoked or not rec.get("revoked_at")
    ]
    rows.sort(key=lambda r: r.get("created_at") or 0, reverse=True)
    return rows


def revoke(key_id: str) -> bool:
    """Mark a key revoked. Returns False when no such live key exists.

    The record is kept, not deleted: "this key was revoked on the 8th"
    is the answer someone needs when a key stops working, and an absent
    row cannot give it.
    """
    wanted = (key_id or "").strip().lower()
    if wanted.startswith(KEY_PREFIX + "_"):
        # Someone pasted the whole key back. Accept it; the id is the
        # second field and the secret is ignored.
        parts = wanted.split("_")
        wanted = parts[1] if len(parts) > 1 else ""
    if not wanted:
        return False
    doc = _read_store()
    hit = False
    for rec in doc["keys"]:
        if rec.get("id") == wanted and not rec.get("revoked_at"):
            rec["revoked_at"] = int(time.time())
            hit = True
    if hit:
        _write_store(doc)
    return hit


# ── Verification (the request path) ─────────────────────────────────────

def parse(presented: str) -> Optional[tuple]:
    """Split a presented key into ``(key_id, secret)``, or None."""
    s = (presented or "").strip()
    if not s.startswith(KEY_PREFIX + "_"):
        return None
    parts = s.split("_", 2)
    if len(parts) != 3 or not parts[1] or not parts[2]:
        return None
    return parts[1], parts[2]


def verify(presented: str) -> Optional[dict]:
    """The key's record if ``presented`` is a live key, else None.

    Compared with :func:`hmac.compare_digest` over the hex digest so the
    check does not leak the secret through its own timing. Never raises:
    an unreadable store means "no key matches", which is the safe answer.
    """
    parsed = parse(presented)
    if not parsed:
        return None
    key_id, secret = parsed
    presented_hash = _hash_secret(secret)
    for rec in _read_store()["keys"]:
        if rec.get("id") != key_id or rec.get("revoked_at"):
            continue
        stored = str(rec.get("hash") or "")
        if stored and hmac.compare_digest(stored, presented_hash):
            return rec
    return None


def touch(key_id: str) -> None:
    """Record that a key was just used. Best effort, never raises.

    Usage is written back so ``clawmetry key list`` can answer "is
    anything still using this?" before someone revokes it. The write is
    skipped when the timestamp would not change to the second, so a page
    polling once a second does not rewrite the file on every request.
    """
    try:
        doc = _read_store()
        now = int(time.time())
        changed = False
        for rec in doc["keys"]:
            if rec.get("id") == key_id:
                rec["use_count"] = int(rec.get("use_count") or 0) + 1
                if rec.get("last_used_at") != now:
                    rec["last_used_at"] = now
                changed = True
        if changed:
            _write_store(doc)
    except Exception:
        return


def origin_allowed(record: dict, origin: str) -> bool:
    """True when ``origin`` is on this key's allowlist. Case-insensitive,
    trailing slash tolerated (some clients send one). An empty allowlist
    matches nothing, by design: that key is for non-browser callers."""
    if not origin:
        return False
    o = origin.strip().rstrip("/").lower()
    return o in [str(x).lower() for x in (record.get("origins") or [])]


def any_key_allows_origin(origin: str) -> bool:
    """True when ANY live key names ``origin``.

    A CORS preflight arrives without the ``Authorization`` header, so at
    preflight time we cannot know which key the real request will carry.
    This answers the only question the preflight can answer: is this
    origin one the user has authorised at all? The real request is still
    checked against its own key's allowlist.
    """
    if not origin:
        return False
    o = origin.strip().rstrip("/").lower()
    for rec in _read_store()["keys"]:
        if rec.get("revoked_at"):
            continue
        if o in [str(x).lower() for x in (rec.get("origins") or [])]:
            return True
    return False


def granted_shapes(record: dict) -> set:
    """Every live q/1 shape this key may dispatch."""
    from clawmetry.query_contract import shapes_for_scopes

    return shapes_for_scopes(record.get("scopes") or [])


def scope_catalogue() -> list:
    """``[{scope, doc, methods, sensitive}]`` for the UI and the CLI help.

    Derived from the query contract, so a method added there shows up
    here with no second list to update.
    """
    from clawmetry.query_contract import live_methods_by_scope

    return [
        {
            "scope": s,
            "doc": SCOPE_DOC[s],
            "methods": live_methods_by_scope(s),
            "sensitive": s == SCOPE_CONTENT,
        }
        for s in SCOPES
    ]


def redact(presented: str) -> str:
    """``cmk_a1b2c3d4_...`` -- safe to log. Shows the id, never the secret."""
    parsed = parse(presented)
    if not parsed:
        return "(no key)"
    return f"{KEY_PREFIX}_{parsed[0]}_..."


def store_summary() -> dict[str, Any]:
    """Counts for the dashboard panel, cheap enough to call per page load."""
    doc = _read_store()
    keys = doc["keys"]
    return {
        "active": sum(1 for k in keys if not k.get("revoked_at")),
        "revoked": sum(1 for k in keys if k.get("revoked_at")),
        "max": MAX_KEYS,
        "path": _store_path(),
    }
