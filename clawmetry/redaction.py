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

Personal-data tier (WO-61)
--------------------------
Secrets are not the only thing an agent reads off a fixture. A customer
email, a phone number, a card number or a national identifier in a tool
result would otherwise rest in DuckDB and ride the sealed snapshot. The
second tier below runs *after* the secret tier, inside the same scan cap,
on the operator's machine, and replaces each hit with a **typed**
placeholder (``[email]``, ``[phone]``, ``[card]``, ``[iban]``,
``[national_id]``) so a reader can still see what kind of thing was there.

Precision over recall, deliberately: every numeric category carries a
checksum (Luhn for cards, mod-97 for IBANs, Verhoeff for Aadhaar, the
11-proef for a Dutch BSN, the area rules for a US SSN) and a word boundary,
so a commit hash, a timestamp, a port or a version string never matches.
Names and street addresses in free text are out of scope for this tier and
the posture copy says so.

Per-category off switch: ``~/.clawmetry/config.json`` ->
``{"redaction": {"pii": {"email": false}}}``. ``CLAWMETRY_REDACT_PII=0``
turns the whole tier off. :func:`pii_status` reports what is active.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any, Callable


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


# ── personal-data tier ──────────────────────────────────────────────────────
#
# Order matters and is fixed in ``PII_CATEGORIES``: IBAN before card (an IBAN
# body can contain a Luhn-valid digit run), card before phone (a spaced card
# number looks like a long phone number), and the identifier set last.

PII_CATEGORIES: tuple[str, ...] = (
    "email", "iban", "card", "phone", "national_id",
)

_CONFIG_PATH = os.path.expanduser("~/.clawmetry/config.json")
_PII_ENV = "CLAWMETRY_REDACT_PII"
_CONFIG_TTL_S = 5.0
_pii_cfg_cache: dict[str, Any] = {"at": 0.0, "mtime": None, "value": {}}


def _pii_config() -> dict[str, bool]:
    """Per-category switches from config.json, cached on mtime + a short
    TTL because ``redact_text`` runs once per ingested event."""
    now = time.monotonic()
    cache = _pii_cfg_cache
    if now - cache["at"] < _CONFIG_TTL_S:
        return cache["value"]
    out: dict[str, bool] = {}
    try:
        st = os.stat(_CONFIG_PATH)
        if st.st_mtime == cache["mtime"] and cache["value"]:
            cache["at"] = now
            return cache["value"]
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        raw = ((cfg.get("redaction") or {}).get("pii")
               if isinstance(cfg, dict) else None)
        if isinstance(raw, dict):
            for k, v in raw.items():
                if isinstance(k, str):
                    out[k.strip().lower()] = bool(v)
        elif raw is False:
            out = {c: False for c in PII_CATEGORIES}
        cache["mtime"] = st.st_mtime
    except Exception:
        cache["mtime"] = None
    cache["value"] = out
    cache["at"] = now
    return out


def _pii_tier_disabled() -> bool:
    return os.environ.get(_PII_ENV, "1").strip().lower() in {"0", "false", "no", "off"}


def pii_status() -> dict[str, Any]:
    """What the personal-data tier is doing right now.

    ``enabled`` is the whole tier (the secret tier's ``CLAWMETRY_REDACT``
    and this tier's ``CLAWMETRY_REDACT_PII`` both have to be on);
    ``categories`` is every category with its switch; ``active`` is the
    ordered list of categories that will actually fire.
    """
    tier_on = not _disabled() and not _pii_tier_disabled()
    cfg = _pii_config() if tier_on else {}
    cats = {c: bool(tier_on and cfg.get(c, True)) for c in PII_CATEGORIES}
    return {
        "enabled": tier_on and any(cats.values()),
        "categories": cats,
        "active": [c for c in PII_CATEGORIES if cats[c]],
        "source": "env" if _pii_tier_disabled() or _disabled() else "config",
        "scan_cap_bytes": _MAX_SCAN,
    }


_PII_LABELS = {
    "email": "email", "phone": "phone", "card": "card",
    "iban": "IBAN", "national_id": "national id",
}


def pii_posture_check() -> dict[str, Any]:
    """One line for the security posture surface.

    ``pass`` when every category is on, ``warn`` when the operator turned
    some or all of it off. Never ``fail``: switching a category off is a
    choice the operator made, and the surface's job is to state it, not to
    grade it. No em dashes in this copy: it renders to users.
    """
    st = pii_status()
    active = [_PII_LABELS[c] for c in st["active"]]
    off = [_PII_LABELS[c] for c in PII_CATEGORIES if c not in st["active"]]
    scope = ("Names and street addresses in free text are not detected "
             "by this tier.")
    if not st["enabled"]:
        return {
            "id": "pii_redaction", "label": "Personal data redaction",
            "status": "warn",
            "detail": "Off. Emails, phone numbers, card numbers, IBANs and "
                      "national ids are stored as the agent saw them. " + scope,
            "remediation": "Unset CLAWMETRY_REDACT_PII (and CLAWMETRY_REDACT) "
                           "or remove redaction.pii from ~/.clawmetry/config.json.",
            "severity": "medium", "weight": 5,
        }
    if off:
        return {
            "id": "pii_redaction", "label": "Personal data redaction",
            "status": "warn",
            "detail": "Personal data redaction: " + ", ".join(active)
                      + ". Off for: " + ", ".join(off) + ". " + scope,
            "remediation": "Re-enable the category under redaction.pii in "
                           "~/.clawmetry/config.json.",
            "severity": "medium", "weight": 5,
        }
    return {
        "id": "pii_redaction", "label": "Personal data redaction",
        "status": "pass",
        "detail": "Personal data redaction: " + ", ".join(active)
                  + ". Applied before storage, on this machine. " + scope,
        "remediation": None, "severity": "medium", "weight": 5,
    }


# email: local@domain.tld, the same shape trace_capture already uses for
# publication. No checksum exists for an email; the TLD requirement keeps
# "user@host" log lines and "@decorator" tokens out.
_EMAIL = re.compile(r"(?<![\w.+-])[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}\b")

# IBAN: country code + 2 check digits + BBAN, optional 4-character spacing.
# The country must be one whose IBAN length is known; the mod-97 check then
# has to pass. An unknown country code is not an IBAN as far as this tier is
# concerned, which is the precise side to fail on.
_IBAN_CANDIDATE = re.compile(r"\b([A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,7}(?:[ ]?[A-Z0-9]{1,4})?)\b")
_IBAN_LENGTHS: dict[str, int] = {
    "AD": 24, "AE": 23, "AL": 28, "AT": 20, "AZ": 28, "BA": 20, "BE": 16,
    "BG": 22, "BH": 22, "BR": 29, "BY": 28, "CH": 21, "CR": 22, "CY": 28,
    "CZ": 24, "DE": 22, "DK": 18, "DO": 28, "EE": 20, "EG": 29, "ES": 24,
    "FI": 18, "FO": 18, "FR": 27, "GB": 22, "GE": 22, "GI": 23, "GL": 18,
    "GR": 27, "GT": 28, "HR": 21, "HU": 28, "IE": 22, "IL": 23, "IQ": 23,
    "IS": 26, "IT": 27, "JO": 30, "KW": 30, "KZ": 20, "LB": 28, "LC": 32,
    "LI": 21, "LT": 20, "LU": 20, "LV": 21, "LY": 25, "MC": 27, "MD": 24,
    "ME": 22, "MK": 19, "MR": 27, "MT": 31, "MU": 30, "NL": 18, "NO": 15,
    "PK": 24, "PL": 28, "PS": 29, "PT": 25, "QA": 29, "RO": 24, "RS": 22,
    "SA": 24, "SC": 31, "SD": 18, "SE": 24, "SI": 19, "SK": 24, "SM": 27,
    "ST": 25, "SV": 28, "TL": 23, "TN": 24, "TR": 26, "UA": 29, "VA": 22,
    "VG": 24, "XK": 20,
}


def iban_valid(candidate: str) -> bool:
    """ISO 13616 check: known country length, then mod-97 == 1."""
    s = candidate.replace(" ", "").upper()
    if len(s) < 15 or len(s) > 34:
        return False
    expected = _IBAN_LENGTHS.get(s[:2])
    if expected is None or len(s) != expected:
        return False
    rearranged = s[4:] + s[:4]
    try:
        num = int("".join(str(int(ch, 36)) for ch in rearranged))
    except ValueError:
        return False
    return num % 97 == 1


# Payment card: 13 to 19 digits, spaces or dashes between groups allowed,
# Luhn-valid, AND a brand prefix with the length that brand issues. The
# prefix is what keeps an epoch-milliseconds timestamp (13 digits, starts
# 17) out even on the one-in-ten chance it passes Luhn.
_CARD_CANDIDATE = re.compile(r"(?<![\w.\-])(\d(?:[ \-]?\d){12,18})(?![\w.\-])")
_CARD_BRANDS: tuple[tuple[re.Pattern[str], tuple[int, ...]], ...] = (
    (re.compile(r"^4"), (13, 16, 19)),                              # Visa
    (re.compile(r"^(?:5[1-5]|2(?:22[1-9]|2[3-9]\d|[3-6]\d\d|7[01]\d|720))"), (16,)),  # Mastercard
    (re.compile(r"^3[47]"), (15,)),                                 # Amex
    (re.compile(r"^(?:6011|65|64[4-9])"), (16, 19)),                # Discover
    (re.compile(r"^35(?:2[89]|[3-8]\d)"), (16, 17, 18, 19)),         # JCB
    (re.compile(r"^(?:30[0-5]|3[689])"), (14, 15, 16, 17, 18, 19)),  # Diners
    (re.compile(r"^62"), (16, 17, 18, 19)),                         # UnionPay
    (re.compile(r"^(?:50|5[6-9]|6)"), (12, 13, 14, 15, 16, 17, 18, 19)),  # Maestro
)


def luhn_valid(digits: str) -> bool:
    if not digits.isdigit() or len(digits) < 2:
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def card_valid(candidate: str) -> bool:
    digits = re.sub(r"[ \-]", "", candidate)
    if len(digits) < 13 or len(digits) > 19 or len(set(digits)) == 1:
        return False
    if not luhn_valid(digits):
        return False
    return any(pat.match(digits) and len(digits) in lengths
               for pat, lengths in _CARD_BRANDS)


# Phone, E.164 only: a leading "+", a country code that does not start with
# 0, then 8 to 15 digits in total, with optional single separators between
# groups. The lookbehind refuses a "+" glued to a preceding digit, so the
# "+05:30" of an ISO timestamp and "1.2.3+4567" build tags stay put.
_PHONE_CANDIDATE = re.compile(
    r"(?<![\w.+\-])\+([1-9]\d{0,2}(?:[ \-.]?\(?\d{1,4}\)?){1,5})(?![\w\-])"
)


def phone_valid(candidate: str) -> bool:
    digits = re.sub(r"\D", "", candidate)
    return 8 <= len(digits) <= 15


# National identifiers. Each has a structural rule and a check, and each
# is written in the form the document prints it, not a bare digit run.
# US SSN: AAA-GG-SSSS, area not 000/666/9xx, group not 00, serial not 0000.
_SSN = re.compile(r"(?<![\w\-])(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}(?![\w\-])")
# UK NINO: two letters (restricted alphabet, forbidden pairs), six digits,
# suffix A-D, optional spaces in the printed grouping.
_NINO = re.compile(
    r"(?<![A-Za-z0-9])(?!BG|GB|NK|KN|TN|NT|ZZ)"
    r"[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z] ?\d{2} ?\d{2} ?\d{2} ?[A-D](?![A-Za-z0-9])"
)
# India Aadhaar: 12 digits, first digit 2-9, optional 4-4-4 grouping,
# Verhoeff check digit.
_AADHAAR = re.compile(r"(?<![\w.\-])([2-9]\d{3}[ \-]?\d{4}[ \-]?\d{4})(?![\w.\-])")
# Netherlands BSN: nine digits, 11-proef with weights 9..2 and -1.
_BSN = re.compile(r"(?<![\w.\-:/+])(\d{9})(?![\w.\-:/])")

_VERHOEFF_D = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9), (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6), (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8), (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2), (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4), (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)
_VERHOEFF_P = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9), (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2), (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0), (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5), (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)


def verhoeff_valid(digits: str) -> bool:
    if not digits.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][int(ch)]]
    return c == 0


def aadhaar_valid(candidate: str) -> bool:
    digits = re.sub(r"[ \-]", "", candidate)
    return len(digits) == 12 and digits[0] in "23456789" and verhoeff_valid(digits)


def bsn_valid(digits: str) -> bool:
    """Dutch 11-proef: sum(d_i * w_i) with weights 9..2 for the first eight
    digits and -1 for the last must be divisible by 11."""
    if len(digits) != 9 or not digits.isdigit():
        return False
    total = sum(int(digits[i]) * (9 - i) for i in range(8)) - int(digits[8])
    return total % 11 == 0 and total != 0


def _sub_checked(pat: re.Pattern[str], check: Callable[[str], bool],
                 placeholder: str, text: str) -> str:
    def _repl(m: re.Match) -> str:
        cand = m.group(1) if m.lastindex else m.group(0)
        return placeholder if check(cand) else m.group(0)
    return pat.sub(_repl, text)


def redact_pii(text: str, categories: "dict[str, bool] | None" = None) -> str:
    """Apply the personal-data tier only (the secret tier is separate).

    ``categories`` overrides the config switches (tests, and callers that
    already resolved them). Never raises: any error returns the input.
    """
    if not text:
        return text
    cats = categories if categories is not None else pii_status()["categories"]
    try:
        return _pii_core(text, cats)
    except Exception:
        return text


def _pii_core(text: str, cats: "dict[str, bool]") -> str:
    """The personal-data substitutions with no error handling, for callers
    that must know when scrubbing failed (see :func:`scrub_payload`)."""
    out = text
    if cats.get("email"):
        out = _EMAIL.sub("[email]", out)
    if cats.get("iban"):
        out = _sub_checked(_IBAN_CANDIDATE, iban_valid, "[iban]", out)
    if cats.get("card"):
        out = _sub_checked(_CARD_CANDIDATE, card_valid, "[card]", out)
    if cats.get("phone"):
        out = _sub_checked(_PHONE_CANDIDATE, phone_valid, "[phone]", out)
    if cats.get("national_id"):
        out = _SSN.sub("[national_id]", out)
        out = _NINO.sub("[national_id]", out)
        out = _sub_checked(_AADHAAR, aadhaar_valid, "[national_id]", out)
        out = _sub_checked(_BSN, bsn_valid, "[national_id]", out)
    return out


def redact_text(text: str, pii: bool = True) -> str:
    """Redact secret-shaped substrings in free text. Idempotent-ish: a value
    already replaced by a fingerprint won't re-match. ``pii=False`` skips the
    personal-data tier (received telemetry under the ``full`` content profile,
    clawmetry/otlp_content.py); the secret tier always runs."""
    if _disabled() or not text or len(text) > _MAX_SCAN:
        return text
    try:
        return _scrub_text(text) if pii else _scrub_text(text, pii=False)
    except Exception:
        return text  # never lose data on a redaction bug


def _scrub_text(text: str, pii: bool = True) -> str:
    """Secret tier, then personal-data tier. No size cap and no error
    handling: :func:`redact_text` returns the input when this fails (the event
    path's "never lose data" rule) and :func:`scrub_payload` withholds it."""
    out = _PRIVATE_KEY.sub("[REDACTED:private-key]", text)
    # Bearer before keyval so "Authorization: Bearer <tok>" redacts the
    # token, not the scheme word.
    out = _BEARER.sub(lambda m: "Bearer " + _fingerprint(m.group(1)), out)
    out = _KEYVAL.sub(lambda m: m.group(1) + m.group(2) + _fingerprint(m.group(3)), out)
    for pat in _TOKEN_PATTERNS:
        out = pat.sub(lambda m: _fingerprint(m.group(0)), out)
    # Personal-data tier, after secrets so a token that happens to look
    # like an identifier is fingerprinted rather than typed.
    if pii and not _pii_tier_disabled():
        out = _pii_core(out, pii_status()["categories"])
    return out


# Nested OpenTelemetry identifiers (a span event's link, a trace-derived tool
# event's provenance). A span id is 16 hex characters and can be all digits,
# which a Luhn-valid run would otherwise mask as ``[card]`` and so erase the
# join back to the trace. Passed through only under these exact names AND only
# when the value is a bare 16- or 32-character hex id.
_OTEL_ID_KEYS = frozenset({"trace_id", "span_id", "parent_span_id"})
_OTEL_HEX_ID = re.compile(r"(?:[0-9a-fA-F]{16}|[0-9a-fA-F]{32})")


def _is_otel_id(key: str, value: str) -> bool:
    return key in _OTEL_ID_KEYS and bool(_OTEL_HEX_ID.fullmatch(value))


def _redact_value(value: Any, key: str = "", pii: bool = True) -> Any:
    if isinstance(value, str):
        if _is_otel_id(key, value):
            return value
        if key and key.lower() not in _COUNT_KEYS and _SENSITIVE_KEY.match(key) and len(value) >= 6:
            return _fingerprint(value)
        return redact_text(value) if pii else redact_text(value, pii=False)
    if isinstance(value, dict):
        return {k: _redact_value(v, k if isinstance(k, str) else "", pii) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_value(v, "", pii) for v in value]
    return value


def _content_profile_allows_pii(kind: str, obj: Any) -> bool:
    """Whether the personal-data tier applies, per the OTLP content profile
    (clawmetry/otlp_content.py). True unless received telemetry is under
    ``full``; the secret tier is never affected."""
    try:
        from clawmetry import otlp_content as _oc
        if kind == "span":
            return _oc.personal_data_applies_to_span(obj)
        return _oc.personal_data_applies_to_event(obj)
    except Exception:
        return True


def redact_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted copy of an ingest event. Structural identifier fields
    are passed through untouched; every other text-bearing field (notably the
    nested ``data`` payload with tool args / prompts / content) is scrubbed."""
    if _disabled() or not isinstance(event, dict):
        return event
    try:
        pii = _content_profile_allows_pii("event", event)
        return {
            k: (v if k in _STRUCTURAL_KEYS else _redact_value(v, k if isinstance(k, str) else "", pii))
            for k, v in event.items()
        }
    except Exception:
        return event


# ── Spans (OTLP traces) and other received payloads ─────────────────────────
#
# Span rows used to bypass everything above: the event chokepoint is
# ``LocalStore.ingest``, and spans are written by ``ingest_spans_batch``, so a
# prompt, a tool argument or an exception message received over /v1/traces
# rested in DuckDB exactly as sent (REQ-OBS-OTG-001). The same two tiers apply
# here, with one deliberate difference. The event path returns the ORIGINAL
# text when scrubbing fails or the value is too large to scan ("never lose
# data"). A span value that could not be scanned is WITHHELD instead, and the
# row says so, because storing it unscanned while the posture reads "applied"
# is a false claim of scrubbing.

# Typed span columns that are identifiers, times, numbers or model/tool names.
_SPAN_STRUCTURAL_KEYS = frozenset({
    "span_id", "trace_id", "parent_span_id", "agent_type", "agent_id",
    "node_id", "session_id", "service_name", "kind", "status_code",
    "start_ts", "end_ts", "duration_ms", "duration_ns", "model", "tool_name",
    "cost_usd", "token_count", "tokens_input", "tokens_output", "ts",
    "created_at",
})

WITHHELD_TOO_LARGE = "[WITHHELD:too-large-to-scan]"
WITHHELD_ERROR = "[WITHHELD:redaction-error]"
REDACTION_MARKER_KEY = "clawmetry.redaction"


def _leaf_key(key: Any) -> str:
    """``http.request.header.authorization`` -> ``authorization``. OTel
    attribute names are dotted; the sensitive-name rule is written for the
    last segment."""
    if not isinstance(key, str):
        return ""
    return key.rsplit(".", 1)[-1]


def _scrub_strict(value: Any, key: str, withheld: list, pii: bool = True) -> Any:
    if isinstance(value, (bytes, bytearray, memoryview)):
        try:
            value = bytes(value).decode("utf-8")
        except Exception:
            withheld.append("error")
            return WITHHELD_ERROR
    if isinstance(value, str):
        if len(value) > _MAX_SCAN:
            withheld.append("too_large")
            return WITHHELD_TOO_LARGE
        if _is_otel_id(key, value):
            return value
        leaf = _leaf_key(key)
        try:
            if (leaf and leaf.lower() not in _COUNT_KEYS
                    and _SENSITIVE_KEY.match(leaf) and len(value) >= 6):
                return _fingerprint(value)
            return _scrub_text(value) if pii else _scrub_text(value, pii=False)
        except Exception:
            withheld.append("error")
            return WITHHELD_ERROR
    if isinstance(value, dict):
        return {k: _scrub_strict(v, k if isinstance(k, str) else "", withheld, pii)
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        # An attribute array inherits its name: semconv sends
        # ``http.request.header.authorization`` as a list of strings.
        return [_scrub_strict(v, key, withheld, pii) for v in value]
    return value


def scrub_payload(value: Any, key: str = "", pii: bool = True) -> "tuple[Any, list[str]]":
    """Scrub one received payload (a span's attributes, a ledger row's
    attributes, ...). Returns ``(scrubbed, withheld_reasons)``: an empty list
    means every string in it was scanned. With ``CLAWMETRY_REDACT=0`` the
    value comes back untouched, matching the event path. ``pii=False`` skips
    only the personal-data tier. Never raises."""
    if _disabled():
        return value, []
    withheld: list = []
    try:
        return _scrub_strict(value, key, withheld, pii), sorted(set(withheld))
    except Exception:
        return WITHHELD_ERROR, ["error"]


def mark_withheld(attributes: Any, reasons: "list[str]") -> Any:
    """Stamp ``clawmetry.redaction: withheld:<reasons>`` on an attributes
    value, whatever its shape. No reasons: returned unchanged."""
    if not reasons:
        return attributes
    note = "withheld:" + ",".join(reasons)
    if isinstance(attributes, dict):
        out = dict(attributes)
        out[REDACTION_MARKER_KEY] = note
        return out
    if attributes in (None, "", b""):
        return {REDACTION_MARKER_KEY: note}
    return {"_value": attributes, REDACTION_MARKER_KEY: note}


def redact_span(span: dict[str, Any]) -> dict[str, Any]:
    """A redacted copy of one span row dict (the ``LocalStore.ingest_span``
    shape). Identifier, time and number columns pass through; ``name``,
    ``status``, ``status_message``, ``input``, ``output``, ``attributes``,
    ``events`` and ``links`` are scrubbed. A value that could not be scanned
    is withheld and the span's attributes carry the marker. Never raises."""
    if _disabled() or not isinstance(span, dict):
        return span
    reasons: set = set()
    # A received span stored under the ``full`` content profile skips the
    # personal-data tier; secrets are scrubbed either way.
    pii = _content_profile_allows_pii("span", span)
    try:
        out: dict[str, Any] = {}
        for k, v in span.items():
            if k in _SPAN_STRUCTURAL_KEYS:
                out[k] = v
                continue
            scrubbed, why = scrub_payload(v, "", pii)
            out[k] = scrubbed
            reasons.update(why)
    except Exception:
        out = {k: (v if k in _SPAN_STRUCTURAL_KEYS else WITHHELD_ERROR)
               for k, v in span.items()}
        reasons.add("error")
    if reasons:
        out["attributes"] = mark_withheld(
            out.get("attributes") if out.get("attributes") != WITHHELD_ERROR else None,
            sorted(reasons))
    return out
