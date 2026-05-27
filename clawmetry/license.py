"""
clawmetry/license.py — self-hosted Pro/Enterprise license client.

A ClawMetry Pro/Enterprise license is a signed token issued by
``license.clawmetry.com``. It unlocks the closed-source ``clawmetry-pro``
package (the paid runtimes + advanced features) on self-hosted installs, for N
nodes, for one year.

Trust model
-----------
The license server holds the Ed25519 PRIVATE key and signs licenses. This OSS
package embeds only the matching PUBLIC key, so a license verifies fully
OFFLINE — no phone-home needed to keep a paid feature working once activated.
``clawmetry activate`` does one online call to register this node against the
key's node count and fetch the clawmetry-pro wheel; after that the node runs
offline until the license expires.

Token format
------------
``CLAW1.<b64url(payload_json)>.<b64url(ed25519_sig)>`` where the signature
covers the exact payload-json bytes. Payload::

    {"sub": "<account>", "tier": "pro"|"enterprise", "nodes": N,
     "iat": <epoch>, "exp": <epoch>, "features": [...]}

Nothing here ever raises to the caller — a bad/expired/forged token resolves to
"no license" (OSS free), logged at warning level.
"""

from __future__ import annotations

import base64
import json
import logging
import os

logger = logging.getLogger("clawmetry.license")

# Ed25519 PUBLIC verification key. The matching PRIVATE key lives only on the
# license server (clawmetry-cloud, never shipped). Rotating the server key
# means bumping this constant + an OSS release.
_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEA1xcY0kmz1Ns+SVWTzJ/8BtLWDIS+OGquGxtk3FIaDzA=
-----END PUBLIC KEY-----
"""

_TOKEN_PREFIX = "CLAW1"
LICENSE_PATH = os.path.expanduser("~/.clawmetry/license.key")
_CONFIG_PATH = os.path.expanduser("~/.clawmetry/config.json")


def _b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _load_public_key():
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    return load_pem_public_key(_PUBLIC_KEY_PEM)


def _encode_token(payload: dict, private_key) -> str:
    """Mint a license token. Needs the Ed25519 PRIVATE key — used by the
    license server and tests, never with a key shipped in this package."""
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = private_key.sign(raw)
    return f"{_TOKEN_PREFIX}.{_b64u_encode(raw)}.{_b64u_encode(sig)}"


def verify_token(token: str) -> dict | None:
    """Verify a license token against the embedded public key. Returns the
    payload dict if the signature is valid, else None. Never raises."""
    try:
        from cryptography.exceptions import InvalidSignature

        parts = (token or "").strip().split(".")
        if len(parts) != 3 or parts[0] != _TOKEN_PREFIX:
            return None
        raw = _b64u_decode(parts[1])
        sig = _b64u_decode(parts[2])
        try:
            _load_public_key().verify(sig, raw)
        except InvalidSignature:
            logger.warning("license: signature verification failed")
            return None
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            return None
        return payload
    except Exception as exc:
        logger.warning("license: token parse failed: %s", exc)
        return None


def parse_license(token: str):
    """Verify ``token`` and build an Entitlement, or None if invalid."""
    payload = verify_token(token)
    if payload is None:
        return None
    try:
        from clawmetry import entitlements as _ent

        tier_in = str(payload.get("tier", "")).strip().lower()
        tier = _ent.TIER_ENTERPRISE if tier_in == "enterprise" else _ent.TIER_PRO
        return _ent._build(
            tier,
            "license",
            node_limit=int(payload.get("nodes", 1) or 1),
            expiry=payload.get("exp"),
        )
    except Exception as exc:
        logger.warning("license: entitlement build failed: %s", exc)
        return None


def load_license(path: str = LICENSE_PATH):
    """Load + verify the on-disk license, returning an Entitlement or None.
    This is the hook :mod:`clawmetry.entitlements` calls."""
    try:
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            token = fh.read().strip()
        return parse_license(token)
    except Exception as exc:
        logger.warning("license: load failed: %s", exc)
        return None


def _node_id() -> str | None:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh).get("node_id")
    except Exception:
        return None


def _download_and_install_pro(payload: dict) -> str:
    """Register this node with the license server and install ``clawmetry-pro``.

    Gated on ``CLAWMETRY_LICENSE_SERVER`` — when unset (e.g. before the license
    server exists) this is a graceful no-op so offline activation still saves a
    verified license. Returns a human status string. Never raises."""
    server = os.environ.get("CLAWMETRY_LICENSE_SERVER", "").strip()
    if not server:
        return "clawmetry-pro install deferred (no license server configured)"
    try:
        # Phase 3: POST {key, node_id} to <server>/activate, receive a scoped
        # wheel/index URL bounded by the key's node count, pip-install it into
        # the daemon venv; extensions.load_plugins() then discovers it.
        logger.info("license: would activate node %s against %s", _node_id(), server)
        return f"node registration + clawmetry-pro install via {server} (pending Phase 3)"
    except Exception as exc:
        logger.warning("license: pro install failed: %s", exc)
        return f"clawmetry-pro install failed: {exc}"


def activate(key: str, node_id: str | None = None) -> tuple[bool, str]:
    """Verify ``key`` offline, persist it, and (best-effort) register the node
    + install clawmetry-pro. Returns (ok, message). Never raises."""
    payload = verify_token(key)
    if payload is None:
        return False, "Invalid or unrecognized license key."
    import time as _t

    exp = payload.get("exp")
    if isinstance(exp, (int, float)) and _t.time() > exp:
        return False, "This license key has expired."
    try:
        os.makedirs(os.path.dirname(LICENSE_PATH), exist_ok=True)
        with open(LICENSE_PATH, "w", encoding="utf-8") as fh:
            fh.write(key.strip() + "\n")
    except Exception as exc:
        return False, f"Could not write license file: {exc}"
    # Refresh the entitlement cache so the new license takes effect immediately.
    try:
        from clawmetry import entitlements as _ent

        _ent.invalidate()
    except Exception:
        pass
    install_status = _download_and_install_pro(payload)
    tier = str(payload.get("tier", "pro")).lower()
    nodes = payload.get("nodes", 1)
    return True, f"Activated {tier} license for {nodes} node(s). {install_status}"


def current_license_info() -> dict | None:
    """Human-readable summary of the installed license, or None if there is no
    valid one. Never raises."""
    import time as _t

    try:
        if not os.path.isfile(LICENSE_PATH):
            return None
        with open(LICENSE_PATH, "r", encoding="utf-8") as fh:
            payload = verify_token(fh.read().strip())
        if payload is None:
            return {"valid": False, "status": "invalid"}
        exp = payload.get("exp")
        days_left = None
        expired = False
        if isinstance(exp, (int, float)):
            days_left = int((exp - _t.time()) // 86400)
            expired = _t.time() > exp
        return {
            "valid": not expired,
            "status": "expired" if expired else "active",
            "tier": payload.get("tier", "pro"),
            "nodes": payload.get("nodes", 1),
            "sub": payload.get("sub", ""),
            "exp": exp,
            "days_left": days_left,
        }
    except Exception as exc:
        logger.warning("license: info read failed: %s", exc)
        return None
