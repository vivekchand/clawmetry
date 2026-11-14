"""Short-lived, runtime-scoped policy evidence for an initial hook outage.

The daemon captures the policies it actually installed. A client may deny a
matched protected call only while that evidence is fresh and the current
entitlement still permits approvals. Missing, stale or invalid evidence has
no blocking authority. This is a local file, never a cloud export.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
from pathlib import Path
import re
import tempfile
import time

CACHE_DIR = Path.home() / ".clawmetry" / "gate_policies"
VERSION = 1
TTL_S = 60
REFRESH_S = 20
MAX_BYTES = 1024 * 1024
MAX_POLICIES = 100
log = logging.getLogger("clawmetry.gate_policy_cache")


def _path(runtime):
    if not isinstance(runtime, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", runtime):
        raise ValueError("invalid runtime identifier")
    return CACHE_DIR / (runtime + ".json")


def _entitled():
    try:
        from clawmetry.entitlements import get_entitlement
        entitlement = get_entitlement()
        return (getattr(entitlement, "source", "") != "resolver_error"
                and bool(entitlement.allows_feature("approval_queue")))
    except Exception:
        return False


def _read(path):
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return None
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _valid(snapshot, runtime, now):
    try:
        captured = snapshot["captured_at"]
        expires = snapshot["expires_at"]
        return (snapshot.get("version") == VERSION and snapshot.get("runtime") == runtime
                and isinstance(captured, (int, float)) and isinstance(expires, (int, float))
                and math.isfinite(captured) and math.isfinite(expires)
                and 0 <= now - captured < TTL_S and expires == captured + TTL_S
                and isinstance(snapshot.get("policies"), list)
                and len(snapshot["policies"]) <= MAX_POLICIES)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def _serialize(policy):
    result = {key: policy.get(key) for key in
              ("name", "tool", "runtime", "action", "min_risk", "timeout", "on_timeout", "action_binding")}
    for key in ("command_regex", "command_not_regex", "args_regex"):
        pattern = policy.get(key)
        result[key] = ({"pattern": pattern.pattern, "flags": pattern.flags}
                       if pattern is not None else None)
    return result


def _restore(raw):
    if not isinstance(raw, dict) or raw.get("action") not in ("require_approval", "approve", "monitor"):
        raise ValueError("invalid policy evidence")
    result = dict(raw)
    for key in ("command_regex", "command_not_regex", "args_regex"):
        value = raw.get(key)
        result[key] = re.compile(value["pattern"], value["flags"]) if value is not None else None
    return result


def capture(runtime, policies, *, now=None):
    """Refresh installed policy evidence at most every twenty seconds."""
    temporary = None
    try:
        path = _path(runtime)
        scoped = [p for p in policies if isinstance(p, dict)
                  and p.get("runtime", "") in (None, "", runtime)]
        if (len(scoped) > MAX_POLICIES or not any(
                p.get("action") == "require_approval" for p in scoped) or not _entitled()):
            path.unlink(missing_ok=True)
            return
        serialized = [_serialize(p) for p in scoped]
        fingerprint = hashlib.sha256(json.dumps(serialized, sort_keys=True,
                                                allow_nan=False).encode()).hexdigest()
        now = time.time() if now is None else now
        previous = _read(path)
        if (previous and _valid(previous, runtime, now)
                and previous.get("fingerprint") == fingerprint
                and now - previous["captured_at"] < REFRESH_S):
            return
        snapshot = dict(version=VERSION, runtime=runtime, policies=serialized,
                        fingerprint=fingerprint, captured_at=now, expires_at=now + TTL_S)
        raw = json.dumps(snapshot, sort_keys=True, allow_nan=False).encode()
        if len(raw) > MAX_BYTES:
            path.unlink(missing_ok=True)
            return
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(raw)
        os.replace(temporary, path)
        temporary = None
    except Exception as exc:
        log.warning("Local gate policy evidence could not be refreshed: %s", type(exc).__name__)
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def protects(runtime, payload, *, now=None):
    """True only for a fresh, scoped, still-entitled require-approval match."""
    try:
        snapshot = _read(_path(runtime))
        now = time.time() if now is None else now
        if not snapshot or not _valid(snapshot, runtime, now) or not _entitled():
            return False
        from clawmetry.approvals import match_policy
        from clawmetry.prompt_injection import coerce_context
        policies = [_restore(raw) for raw in snapshot["policies"]]
        if any(p.get("runtime", "") not in (None, "", runtime) for p in policies):
            return False
        policy = match_policy(policies, payload.get("tool_name") or "",
                              payload.get("tool_input") or {},
                              context=coerce_context(payload.get("untrusted_context")),
                              runtime=runtime, cwd=payload.get("cwd") or "")
        return bool(policy and policy.get("action") == "require_approval")
    except Exception:
        return False
