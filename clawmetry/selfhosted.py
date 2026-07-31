"""
clawmetry.selfhosted — ClawMetry Enterprise single-tenant server mode.

Activated with ``SELF_HOSTED=true`` (or ``CLAWMETRY_SELF_HOSTED=true``).
When on, the dashboard process additionally registers the self-hosted
ingest blueprint (routes/selfhosted_ingest.py) so one container serves
both the UI and the ingest API that the node daemons push to, and the
cloud-only surfaces (managed-cloud signup CTA, install telemetry,
anonymous analytics) are disabled.

Auth model (deliberately simple, env-configured — no multi-tenant IdP):

* ``CLAWMETRY_API_TOKENS``  — comma-separated node tokens. Daemons connect
  with one of these (``clawmetry connect --key cm_...``). Tokens must start
  with ``cm_`` (the CLI enforces that prefix).
* ``CLAWMETRY_ADMIN_USER`` / ``CLAWMETRY_ADMIN_PASSWORD`` — HTTP Basic
  credentials for admin/read endpoints (audit export, node list).

Outbound traffic policy: a self-hosted deployment makes NO calls to
clawmetry.com, with one optional, off-by-default exception — the
license/version ping (``CLAWMETRY_LICENSE_PING=1``). The ping payload is
exactly::

    {
      "kind":    "selfhosted_ping",
      "version": "<clawmetry package version>",
      "license": "<'sub' claim of the activated license, or ''>",
      "tier":    "<license tier, or ''>",
      "ts":      "<ISO-8601 UTC>"
    }

No hostnames, node ids, counts, or telemetry of any kind — just enough to
check the license against revocation and surface available updates. It
POSTs to https://app.clawmetry.com/api/license/ping once every 24h.
"""
from __future__ import annotations

import base64
import hmac
import logging
import os
import threading

log = logging.getLogger("clawmetry.selfhosted")

_TRUTHY = frozenset({"1", "true", "yes", "on"})

_LICENSE_PING_URL = "https://app.clawmetry.com/api/license/ping"
_LICENSE_PING_INTERVAL_S = 24 * 3600


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def is_self_hosted() -> bool:
    """True when this process runs as a ClawMetry Enterprise self-hosted server."""
    return _env_truthy("SELF_HOSTED") or _env_truthy("CLAWMETRY_SELF_HOSTED")


def e2e_enabled() -> bool:
    """Whether this self-hosted server asks nodes to E2E-encrypt blobs.

    Default OFF: data already stays inside the customer deployment, and
    plaintext ingest is what makes server-side fleet views and audit export
    meaningful. Set CLAWMETRY_SELF_HOSTED_E2E=1 to keep client-side blob
    encryption (the server then stores opaque ciphertext and audit export
    only contains envelope metadata).
    """
    return _env_truthy("CLAWMETRY_SELF_HOSTED_E2E")


def api_tokens() -> list[str]:
    """Node API tokens accepted by the ingest API (CLAWMETRY_API_TOKENS)."""
    raw = os.environ.get("CLAWMETRY_API_TOKENS", "")
    return [t.strip() for t in raw.split(",") if t.strip()]


def check_api_key(key) -> bool:
    """Constant-time membership check of ``key`` against CLAWMETRY_API_TOKENS."""
    if not key:
        return False
    key = str(key)
    ok = False
    for token in api_tokens():
        # No early exit — compare every configured token.
        if hmac.compare_digest(key, token):
            ok = True
    return ok


def admin_credentials() -> tuple[str, str]:
    return (
        os.environ.get("CLAWMETRY_ADMIN_USER", "").strip(),
        os.environ.get("CLAWMETRY_ADMIN_PASSWORD", ""),
    )


def check_admin_basic_auth(header_value) -> bool:
    """Validate an ``Authorization: Basic ...`` header against the env creds."""
    user, password = admin_credentials()
    if not user or not password:
        return False
    if not header_value or not str(header_value).startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(str(header_value)[6:]).decode("utf-8")
        got_user, _, got_pass = decoded.partition(":")
    except Exception:
        return False
    return hmac.compare_digest(got_user, user) and hmac.compare_digest(
        got_pass, password
    )


def check_admin_or_token(request) -> bool:
    """Auth gate for read/export endpoints: admin Basic auth OR a node token."""
    if check_admin_basic_auth(request.headers.get("Authorization")):
        return True
    return check_api_key(request.headers.get("X-Api-Key"))


# ── Optional license/version ping (off by default) ──────────────────────────

_ping_thread_started = False


def _license_ping_payload() -> dict:
    from datetime import datetime, timezone

    version = ""
    try:
        import importlib.metadata

        version = importlib.metadata.version("clawmetry")
    except Exception:
        pass
    sub = tier = ""
    try:
        from clawmetry.license import load_license

        lic = load_license() or {}
        sub = str(lic.get("sub") or "")
        tier = str(lic.get("tier") or "")
    except Exception:
        pass
    return {
        "kind": "selfhosted_ping",
        "version": version,
        "license": sub,
        "tier": tier,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def _license_ping_loop() -> None:
    import json
    import time
    import urllib.request

    while True:
        try:
            body = json.dumps(_license_ping_payload()).encode("utf-8")
            req = urllib.request.Request(
                _LICENSE_PING_URL,
                data=body,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read()
        except Exception as exc:
            log.debug("license ping failed: %s", exc)
        time.sleep(_LICENSE_PING_INTERVAL_S)


def maybe_start_license_ping() -> bool:
    """Start the daily license/version ping IF explicitly enabled.

    Off by default: a self-hosted deployment phones home to nothing. The
    exact payload is documented in the module docstring. Returns True when
    the ping thread was started.
    """
    global _ping_thread_started
    if _ping_thread_started:
        return True
    if not _env_truthy("CLAWMETRY_LICENSE_PING"):
        return False
    t = threading.Thread(
        target=_license_ping_loop, daemon=True, name="selfhosted-license-ping"
    )
    t.start()
    _ping_thread_started = True
    return True
