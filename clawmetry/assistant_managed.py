"""Optional bridge to ClawMetry's account-metered managed assistant."""

from __future__ import annotations

import json
import os
import base64
import uuid
from urllib import error, request

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    _CRYPTO_AVAILABLE = True
except ImportError:
    # Minimal dashboard installs can still use their local harness. Never
    # substitute plaintext for an unavailable encrypted managed transport.
    _CRYPTO_AVAILABLE = False


class ManagedAssistantError(RuntimeError):
    """Safe base error for managed assistant failures."""


class ManagedAssistantNotConfigured(ManagedAssistantError):
    pass


class ManagedAssistantUnavailable(ManagedAssistantError):
    pass


class ManagedAssistantAuthError(ManagedAssistantError):
    pass


class ManagedAssistantCreditsError(ManagedAssistantError):
    pass


DEFAULT_BUILDER_URL = "https://build.clawmetry.com"
DEFAULT_MAX_TOKENS = 2400
MAX_MAX_TOKENS = 2400
ENVELOPE_VERSION = 1
ENVELOPE_ALGORITHM = "X25519-HKDF-SHA256-AESGCM"
ENVELOPE_INFO = b"clawmetry-managed-assistant-response-v1"
ENVELOPE_AAD = b"clawmetry-managed-assistant-response-v1"


def _api_key() -> str:
    value = os.environ.get("CLAWMETRY_BUILDER_API_KEY", "").strip()
    return value if value.startswith("cmak_") else ""


def configured() -> bool:
    """Return whether a server-side Builder account key is configured."""
    return bool(_api_key())


def _base_url() -> str:
    return os.environ.get("CLAWMETRY_BUILDER_BASE_URL", DEFAULT_BUILDER_URL).strip().rstrip("/")


def _max_tokens() -> int:
    try:
        value = int(os.environ.get("CLAWMETRY_BUILDER_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))
    except (TypeError, ValueError):
        value = DEFAULT_MAX_TOKENS
    return max(1, min(value, MAX_MAX_TOKENS))


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_b64(value: str) -> bytes:
    if not isinstance(value, str):
        raise ValueError("invalid envelope")
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _decrypt_envelope(private_key: X25519PrivateKey, envelope: dict) -> str:
    if not isinstance(envelope, dict):
        raise ValueError("invalid envelope")
    if envelope.get("v") != ENVELOPE_VERSION or envelope.get("alg") != ENVELOPE_ALGORITHM:
        raise ValueError("unsupported envelope")
    server_key = X25519PublicKey.from_public_bytes(_decode_b64(envelope["ephemeral_public_key"]))
    nonce = _decode_b64(envelope["nonce"])
    ciphertext = _decode_b64(envelope["ciphertext"])
    if len(nonce) != 12:
        raise ValueError("invalid envelope nonce")
    shared = private_key.exchange(server_key)
    key = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None, info=ENVELOPE_INFO,
    ).derive(shared)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, ENVELOPE_AAD)
    value = json.loads(plaintext.decode("utf-8"))
    text = value.get("text") if isinstance(value, dict) else None
    if not isinstance(text, str):
        raise ValueError("invalid envelope payload")
    return text


def _json_request(path: str, *, method: str = "GET", payload: dict | None = None,
                  idempotency: bool = False, control=None) -> dict:
    key = _api_key()
    if not key:
        raise ManagedAssistantNotConfigured("managed assistant is not configured")
    body = None
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {key}",
    }
    if payload is not None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if idempotency:
        headers["Idempotency-Key"] = uuid.uuid4().hex

    req = request.Request(_base_url() + path, data=body, headers=headers, method=method)
    try:
        if control is None:
            with request.urlopen(req, timeout=60) as response:
                raw = response.read()
        else:
            from clawmetry.assistant_stream import http_response
            with http_response(req.full_url, payload=body, headers=headers,
                               method=method, control=control, timeout=60) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
                if len(raw) > 2 * 1024 * 1024:
                    raise ManagedAssistantUnavailable("managed assistant returned invalid data")
    except error.HTTPError as exc:
        status = int(getattr(exc, "code", 0) or 0)
        exc.close()
        if status in (401, 403):
            raise ManagedAssistantAuthError("managed assistant authentication failed") from None
        if status == 402:
            raise ManagedAssistantCreditsError("managed assistant credits unavailable") from None
        raise ManagedAssistantUnavailable("managed assistant unavailable") from None
    except (error.URLError, TimeoutError, OSError):
        raise ManagedAssistantUnavailable("managed assistant unavailable") from None

    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ManagedAssistantUnavailable("managed assistant returned invalid data") from None
    if not isinstance(value, dict):
        raise ManagedAssistantUnavailable("managed assistant returned invalid data")
    return value


def status() -> dict:
    """Return account balance plus separate deployed/readiness indicators."""
    if not configured():
        return {
            "configured": False,
            "available": False,
            "endpoint_ready": False,
            "capability_advertised": False,
            "balance_cents": None,
        }
    capability_advertised = False
    endpoint_ready = False
    provider_available = False
    health = {}
    try:
        config = _json_request("/api/config")
        capability = config.get("managed_assistant")
        capability_advertised = (
            isinstance(capability, dict)
            and capability.get("complete") == "/api/assistant/complete"
            and capability.get("status") == "/api/assistant/status"
            and int(capability.get("max_tokens", 0)) >= MAX_MAX_TOKENS
        )
    except (ManagedAssistantError, TypeError, ValueError):
        capability_advertised = False
    try:
        health = _json_request("/api/assistant/status") if capability_advertised else {}
        endpoint_ready = health.get("endpoint_ready") is True
        provider_available = health.get("available") is True
    except ManagedAssistantError:
        # A missing or not-yet-deployed health route must not be inferred from
        # a successful billing response.
        pass
    value = {}
    try:
        if "balance" in health:
            value["balance_cents"] = health["balance"]
        else:
            # Keep the existing billing surface as a diagnostic fallback. It
            # never makes the managed completion available by itself.
            value = _json_request("/api/billing")
    except ManagedAssistantError:
        return {
            "configured": True,
            "available": False,
            "endpoint_ready": endpoint_ready,
            "capability_advertised": capability_advertised,
            "balance_cents": None,
        }
    try:
        balance = int(value["balance_cents"])
    except (KeyError, TypeError, ValueError):
        raise ManagedAssistantUnavailable("managed assistant returned invalid status") from None
    starter = 0
    try:
        starter = max(0, int(health.get("starter_allowance_cents", 0)))
    except (TypeError, ValueError):
        starter = 0
    if not starter:
        entries = value.get("entries")
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and entry.get("kind") == "signup_grant":
                    try:
                        starter += max(0, int(entry.get("cents", 0)))
                    except (TypeError, ValueError):
                        continue
    result = {
        "configured": True,
        "available": bool(endpoint_ready and provider_available and _CRYPTO_AVAILABLE),
        "endpoint_ready": endpoint_ready,
        "capability_advertised": capability_advertised,
        "balance_cents": balance,
    }
    if starter:
        result["starter_allowance_cents"] = starter
    return result


def complete(system: str, prompt: str, *, control=None) -> str:
    """Complete one prompt against the managed account and return only text."""
    if not _CRYPTO_AVAILABLE:
        raise ManagedAssistantUnavailable("managed assistant encryption is unavailable")
    if not isinstance(system, str) or not isinstance(prompt, str) or not prompt.strip():
        raise ManagedAssistantError("managed assistant request is invalid")
    private_key = X25519PrivateKey.generate()
    public_key = _b64(private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw,
    ))
    options = {"control": control} if control is not None else {}
    value = _json_request(
        "/api/assistant/complete",
        method="POST",
        payload={"system": system, "prompt": prompt, "max_tokens": _max_tokens(),
                 "response_public_key": public_key},
        idempotency=True,
        **options,
    )
    if control is not None:
        control.check()
    try:
        return _decrypt_envelope(private_key, value.get("envelope"))
    except Exception:
        raise ManagedAssistantUnavailable("managed assistant returned invalid completion") from None


def checkout(amount_cents: int = 500) -> str:
    """Create an existing Builder checkout; callers invoke this only on click."""
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents < 500:
        raise ManagedAssistantCreditsError("managed assistant top-up amount is invalid")
    value = _json_request(
        "/api/credits/checkout",
        method="POST",
        payload={"amount_cents": amount_cents, "currency": "usd"},
    )
    url = value.get("url")
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        raise ManagedAssistantUnavailable("managed assistant checkout unavailable")
    return url
