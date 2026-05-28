"""Defense-in-depth secret redaction for the daemon ingest path.

Events are stored **plaintext in local DuckDB** before the cloud-sync E2E
boundary (see ``local_store`` header). If an agent echoes an API key, bearer
token, or password into a tool argument or a transcript, that secret would
otherwise land verbatim in ``~/.clawmetry`` and in every local read surface.

This module scrubs obvious secrets *before* persistence, at the single event
chokepoint (``LocalStore.ingest``). Each match is replaced with a **stable
fingerprint** (``[REDACTED:<sha8>]``) so de-dup / cardinality / "same secret
leaked twice" still work without exposing the value.

Design goals:
- High precision, low false-positive — only well-known secret shapes and
  explicitly sensitive field names.
- Never lose data on a bug: any exception falls back to the original value.
- Opt-out via ``CLAWMETRY_REDACT=0`` for users who want raw capture.

Issue #2197.
"""
from __future__ import annotations

import hashlib
import os
import re
from typing import Any


def _disabled() -> bool:
    # Read at call time (not import) so tests can toggle the env var.
    return os.environ.get("CLAWMETRY_REDACT", "1").strip().lower() in {"0", "false", "no", "off"}


def _fingerprint(value: str) -> str:
    """Stable 8-char fingerprint so the same secret always redacts to the same
    token (preserves equality/cardinality) but is irreversible."""
    digest = hashlib.sha256(value.encode("utf-8", "ignore")).hexdigest()[:8]
    return f"[REDACTED:{digest}]"


# ── value patterns (the secret itself appears in free text) ─────────────────
# `key = value` / `"key": "value"` style, capturing the value in group 3.
_KEYVAL = re.compile(
    r"(?i)\b(api[_-]?key|secret|password|passwd|passphrase|access[_-]?token|"
    r"auth[_-]?token|refresh[_-]?token|authorization|client[_-]?secret)"
    r"(\s*[:=]\s*|\"\s*:\s*\"|'\s*:\s*')"
    # Don't capture an auth *scheme* word as the value (e.g.
    # "Authorization: Bearer <token>") — _BEARER handles those, and the real
    # secret is the token after the scheme.
    r"(?!(?:Bearer|Basic|Digest|Token|JWT)\b)"
    r"([A-Za-z0-9\-._~+/]{6,}=*)"
)
_BEARER = re.compile(r"(?i)\bBearer\s+([A-Za-z0-9\-._~+/]{8,}=*)")
_PRIVATE_KEY = re.compile(
    r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----.*?-----END (?:[A-Z ]+ )?PRIVATE KEY-----",
    re.DOTALL,
)
# Provider key formats — match the raw token wherever it appears.
_TOKEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{16,}\b"),        # Anthropic
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{16,}\b"),     # OpenAI-style
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                  # AWS access key id
    re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),            # Google API key
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),        # GitHub tokens
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),      # Slack
    re.compile(r"\bglpat-[A-Za-z0-9\-_]{20,}\b"),         # GitLab PAT
    re.compile(r"\b(?:cm|claw|evk)_[A-Za-z0-9]{16,}\b"),  # our own / connector keys
)

# Field NAMES that should have their entire string value fingerprinted,
# regardless of format (structured secrets like {"api_key": "abc123"}).
_SENSITIVE_KEY = re.compile(
    r"(?i)^(?:[a-z0-9]*[_-])?(?:api[_-]?key|apikey|secret|password|passwd|"
    r"passphrase|authorization|auth[_-]?token|access[_-]?token|"
    r"refresh[_-]?token|private[_-]?key|client[_-]?secret|"
    r"credentials?|bearer[_-]?token)(?:[_-][a-z0-9]+)?$"
)
# ...but never these (token/usage *counts*, not secrets).
_COUNT_KEYS = frozenset({
    "token_count", "max_tokens", "total_tokens", "prompt_tokens",
    "completion_tokens", "input_tokens", "output_tokens", "num_tokens",
})

# Event keys that are structural identifiers — never contain secrets and are
# used for indexing/dedup, so leave them untouched.
_STRUCTURAL_KEYS = frozenset({
    "id", "node_id", "agent_id", "agent_type", "session_id", "workspace_id",
    "event_type", "ts", "created_at", "model", "cost_usd", "token_count",
})

_MAX_SCAN = 1_000_000  # don't run regexes over absurdly large blobs


def redact_text(text: str) -> str:
    """Redact secret-shaped substrings in free text. Idempotent-ish: a value
    already replaced by a fingerprint won't re-match."""
    if _disabled() or not text or len(text) > _MAX_SCAN:
        return text
    try:
        out = _PRIVATE_KEY.sub("[REDACTED:private-key]", text)
        # Bearer before keyval so "Authorization: Bearer <tok>" redacts the
        # token, not the scheme word.
        out = _BEARER.sub(lambda m: "Bearer " + _fingerprint(m.group(1)), out)
        out = _KEYVAL.sub(lambda m: m.group(1) + m.group(2) + _fingerprint(m.group(3)), out)
        for pat in _TOKEN_PATTERNS:
            out = pat.sub(lambda m: _fingerprint(m.group(0)), out)
        return out
    except Exception:
        return text  # never lose data on a redaction bug


def _redact_value(value: Any, key: str = "") -> Any:
    if isinstance(value, str):
        if key and key.lower() not in _COUNT_KEYS and _SENSITIVE_KEY.match(key) and len(value) >= 6:
            return _fingerprint(value)
        return redact_text(value)
    if isinstance(value, dict):
        return {k: _redact_value(v, k if isinstance(k, str) else "") for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_value(v) for v in value]
    return value


def redact_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted copy of an ingest event. Structural identifier fields
    are passed through untouched; every other text-bearing field (notably the
    nested ``data`` payload with tool args / prompts / content) is scrubbed."""
    if _disabled() or not isinstance(event, dict):
        return event
    try:
        return {
            k: (v if k in _STRUCTURAL_KEYS else _redact_value(v, k if isinstance(k, str) else ""))
            for k, v in event.items()
        }
    except Exception:
        return event
