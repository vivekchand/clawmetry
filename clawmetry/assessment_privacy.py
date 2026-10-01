"""Mandatory, local-only masking for explicitly consented assessments.

This boundary covers declared ASCII identifier formats, not names, addresses,
or contextual identity. It has no provider client, persistence, or activation
side effects. All built-in detectors run regardless of ingest redaction flags.
Restored text is only for an authorized local display, never a new request.

Transports passed to ConsentGate must be trusted, synchronous, honor their
timeout, and perform no deferred sends. This module cannot cancel arbitrary
Python callbacks or retract an already-started network request.
"""
from __future__ import annotations

import html
import json
import math
import re
import secrets
import threading
import time
import weakref
from dataclasses import dataclass

from clawmetry import endpoints, redaction

SUPPORTED_CATEGORIES = frozenset({"email", "phone", "card", "iban", "national_id"})
POLICY_VERSION = "identifiers-v1"
SECRET_REMOVED = "[WITHHELD:secret]"
_TOKEN_PREFIX = "[CMPII:"
_TOKEN = re.compile(r"\[CMPII:[a-f0-9]{32}:[a-f0-9]{32}\]")
_LABEL = re.compile(r"[A-Za-z0-9_.:/-]{1,200}\Z")
_GENERIC_KEY = re.compile(r"\b(?:apikey_|cm_s_|cmk_)[A-Za-z0-9_-]{8,}\b")
_AUTH = re.compile(r"(?i)\b(?:Bearer|Basic|Digest|Token|JWT)\s+([^\s,;]+)")
_SECRET_PREFIX = re.compile(
    r"(?i)\b(?:api[_-]?key|secret|password|passwd|passphrase|access[_-]?token|"
    r"auth[_-]?token|refresh[_-]?token|authorization|client[_-]?secret)"
    r"[\"']?\s*[:=]\s*"
)
_ASSIGNMENT = re.compile(_SECRET_PREFIX.pattern + r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s"'][^\r\n]*)''')
_CREDENTIAL_URL = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]{1,20}://([^/\s?#]*@)")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*")
_SECRET_HEADER = re.compile(r"(?i)\b(?:Cookie|Set-Cookie|X-API-Key)\s*:\s*([^\r\n]+)")
_PRIVATE_BEGIN = re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")
_EXTRA_SECRET_FIELDS = frozenset({"token", "cookie", "set_cookie", "session_token",
                                   "connection_string", "database_url", "secret_access_key"})


class PrivacyError(ValueError):
    """A controlled code, with no payload or detector exception in its text."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _number(value, minimum, maximum, code):
    if type(value) not in (int, float) or not minimum <= value <= maximum or not math.isfinite(value):
        raise PrivacyError(code)


def _label(value):
    if type(value) is not str or not _LABEL.fullmatch(value):
        raise PrivacyError("invalid_scope_or_policy")
    return value


@dataclass(frozen=True)
class PrivacyPolicy:
    # Required: callers must name the coverage they need. No universal-PII
    # default approves arbitrary evidence under an ambiguous promise.
    required_categories: tuple
    language: str = "en"
    version: str = POLICY_VERSION
    max_bytes: int = 65536
    max_text_bytes: int = 4096
    max_nodes: int = 4096
    max_depth: int = 16
    max_identifiers: int = 256
    scan_timeout_seconds: float = 0.5
    map_ttl_seconds: float = 300.0

    def __post_init__(self):
        if type(self.required_categories) not in (tuple, list, set, frozenset):
            raise PrivacyError("unsupported_coverage")
        if any(type(category) is not str for category in self.required_categories):
            raise PrivacyError("unsupported_coverage")
        categories = frozenset(self.required_categories)
        if not categories or not categories <= SUPPORTED_CATEGORIES:
            raise PrivacyError("unsupported_coverage")
        if type(self.language) is not str or type(self.version) is not str or self.language != "en" or self.version != POLICY_VERSION:
            raise PrivacyError("unsupported_coverage")
        object.__setattr__(self, "required_categories", tuple(sorted(categories)))
        for field, ceiling in (("max_bytes", 1048576), ("max_text_bytes", 4096), ("max_nodes", 10000),
                               ("max_depth", 32), ("max_identifiers", 1024)):
            value = getattr(self, field)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise PrivacyError("invalid_limits")
        _number(self.scan_timeout_seconds, 0.001, 2.0, "invalid_limits")
        _number(self.map_ttl_seconds, 0.01, 900.0, "invalid_limits")


def _sensitive_key(key):
    leaf = re.split(r"[.\[\]]", key.rstrip("]"))[-1]
    leaf = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", leaf)
    normalized = re.sub(r"[\s-]+", "_", leaf).lower()
    pieces = normalized.split("_")
    return any(redaction._SENSITIVE_KEY.fullmatch(candidate) or candidate in _EXTRA_SECRET_FIELDS
               for candidate in ("_".join(pieces[start:]) for start in range(len(pieces))))


def _pii_patterns():
    # Reuse strict candidates and checksum validators, not public helpers
    # that honor opt-outs or silently return the original text on failure.
    return ((redaction._EMAIL, None),
            (redaction._IBAN_CANDIDATE, redaction.iban_valid),
            (redaction._CARD_CANDIDATE, redaction.card_valid),
            (redaction._PHONE_CANDIDATE, redaction.phone_valid),
            (redaction._SSN, None), (redaction._NINO, None),
            (redaction._AADHAAR, redaction.aadhaar_valid),
            (redaction._BSN, redaction.bsn_valid))


def _expire_session(reference):
    session = reference()
    if session is not None:
        session.close()


class MaskingSession:
    """One payload and a bounded memory-only restoration map.

    Use as a context manager or close explicitly. A daemon timer also clears
    the map at its TTL even if the session is left idle. Python strings cannot
    promise secure memory zeroization; clearing drops this component's refs.
    """
    __slots__ = (
        "__weakref__",
        "_closed",
        "_expires",
        "_lock",
        "_masked",
        "_namespace",
        "_policy",
        "_scope",
        "_timer",
        "_tokens",
        "_values",
    )

    def __init__(self, scope, policy):
        self._scope = _label(scope)
        if type(policy) is not PrivacyPolicy:
            raise PrivacyError("invalid_policy")
        self._policy = policy
        self._namespace = secrets.token_hex(16)
        self._values = {}
        self._tokens = {}
        self._masked = None
        self._expires = time.monotonic() + policy.map_ttl_seconds
        self._closed = False
        self._lock = threading.RLock()
        self._timer = threading.Timer(policy.map_ttl_seconds, _expire_session, (weakref.ref(self),))
        self._timer.daemon = True
        self._timer.start()

    @property
    def policy(self):
        return self._policy

    def __repr__(self):
        return "<MaskingSession local-only>"

    def __reduce_ex__(self, protocol):
        raise PrivacyError("serialization_forbidden")

    def __reduce__(self):
        raise PrivacyError("serialization_forbidden")

    def __getstate__(self):
        raise PrivacyError("serialization_forbidden")

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()

    def __del__(self):
        if hasattr(self, "_lock"):
            self.close()

    def close(self):
        with self._lock:
            self._closed = True
            self._values.clear()
            self._tokens.clear()
            self._masked = None
            self._timer.cancel()

    def _live(self):
        if self._closed or time.monotonic() >= self._expires:
            self.close()
            raise PrivacyError("session_expired")

    def mask(self, payload):
        """Validate and mask the complete JSON-like payload once, atomically."""
        with self._lock:
            self._live()
            if self._masked is not None:
                raise PrivacyError("session_already_masked")
            deadline = time.monotonic() + self._policy.scan_timeout_seconds
            counts = [0, 0]
            secret_values = set()
            try:
                def check():
                    self._live()
                    if time.monotonic() >= deadline:
                        raise PrivacyError("scan_timeout")

                def numeric_text(value):
                    # Identifiers encoded as JSON numbers are still scanned.
                    if type(value) is float and value.is_integer():
                        return str(int(value))
                    return str(value)

                def snapshot(value, depth=0, ancestors=None):
                    check()
                    counts[0] += 1
                    if counts[0] > self._policy.max_nodes or depth > self._policy.max_depth:
                        raise PrivacyError("structure_limit")
                    kind = type(value)
                    if kind is str:
                        if len(value) > self._policy.max_text_bytes:
                            raise PrivacyError("text_span_limit")
                        if not value.isascii():
                            raise PrivacyError("unsupported_text")
                        if _TOKEN_PREFIX in value:
                            raise PrivacyError("reserved_placeholder")
                        if any(len(part) > 320 for part in value.split()):
                            raise PrivacyError("text_span_limit")
                        counts[1] += len(value)
                    elif kind in (int, float):
                        # Avoid huge-int conversion and unbounded numeric
                        # representations before JSON serialization.
                        if (kind is int and value.bit_length() > 128) or (kind is float and (not math.isfinite(value) or abs(value) > 1e38)):
                            raise PrivacyError("invalid_number")
                        counts[1] += len(numeric_text(value))
                    elif value is None or kind is bool:
                        counts[1] += 5
                    elif kind in (dict, list):
                        ancestors = set() if ancestors is None else ancestors
                        if id(value) in ancestors:
                            raise PrivacyError("cyclic_payload")
                        ancestors.add(id(value))
                        try:
                            if kind is list:
                                return [snapshot(item, depth + 1, ancestors) for item in value]
                            out = {}
                            for key, item in value.items():
                                if type(key) is not str:
                                    raise PrivacyError("invalid_key")
                                out[snapshot(key, depth + 1, ancestors)] = snapshot(item, depth + 1, ancestors)
                            return out
                        finally:
                            ancestors.remove(id(value))
                    else:
                        raise PrivacyError("invalid_payload_type")
                    if counts[1] > self._policy.max_bytes:
                        raise PrivacyError("payload_too_large")
                    return value

                def pii_spans(text):
                    chosen = []
                    for pattern, validator in _pii_patterns():
                        check()
                        # Input lexemes are bounded to 320 characters. A
                        # 512-character lookahead contains every supported
                        # candidate whole. Each start belongs to exactly one
                        # primary window, so a truncated match in lookahead
                        # cannot preempt its complete match in the next one.
                        # The clock is checked even when a regex finds none.
                        for base in range(0, len(text), 512):
                            check()
                            left = max(0, base - 1)  # real one-character lookbehind
                            window = text[left:base + 1024]
                            for match in pattern.finditer(window):
                                check()
                                start, end = left + match.start(), left + match.end()
                                if not base <= start < base + 512:
                                    continue
                                candidate = match.group(1) if match.lastindex else match.group(0)
                                if validator is not None and not validator(candidate):
                                    if ((pattern is redaction._CARD_CANDIDATE and redaction.card_candidate_ambiguous(candidate))
                                            or (pattern is redaction._PHONE_CANDIDATE and redaction.phone_candidate_ambiguous(candidate))):
                                        raise PrivacyError("ambiguous_identifier")
                                    continue
                                if not any(start < b and end > a for a, b in chosen):
                                    chosen.append((start, end))
                                    if len(chosen) > self._policy.max_nodes:
                                        raise PrivacyError("identifier_limit")
                    return sorted(chosen)

                def remember_secret(value):
                    if value:
                        secret_values.add(value)
                        # An identifier inside a secret must not become a
                        # restorable token when repeated in another field.
                        for start, end in pii_spans(value):
                            secret_values.add(value[start:end])
                        if len(secret_values) > self._policy.max_identifiers:
                            raise PrivacyError("identifier_limit")

                def collect(value, sensitive=False):
                    check()
                    if type(value) is dict:
                        for key, item in value.items():
                            collect(key, sensitive)
                            collect(item, sensitive or _sensitive_key(key))
                    elif type(value) is list:
                        for item in value:
                            collect(item, sensitive)
                    elif type(value) in (str, int, float):
                        text = value if type(value) is str else numeric_text(value)
                        if sensitive:
                            remember_secret(text)
                        stripped = redaction._PRIVATE_KEY.sub(SECRET_REMOVED, text)
                        if _PRIVATE_BEGIN.search(stripped):
                            raise PrivacyError("incomplete_secret")
                        for prefix in _SECRET_PREFIX.finditer(text):
                            # A truncated quoted credential cannot fall back
                            # to prefix-only redaction and leak the remainder.
                            if text[prefix.end():prefix.end() + 1] in ("\"", "'"):
                                assignment = _ASSIGNMENT.match(text, prefix.start())
                                if assignment is None:
                                    raise PrivacyError("incomplete_secret")
                        for pattern, group in ((redaction._PRIVATE_KEY, 0), (_AUTH, 1),
                                               (_ASSIGNMENT, 1), (redaction._KEYVAL, 3),
                                               (_GENERIC_KEY, 0), (_CREDENTIAL_URL, 1),
                                               (_JWT, 0), (_SECRET_HEADER, 1)):
                            check()
                            for match in pattern.finditer(text):
                                remember_secret(match.group(group).strip("\"'"))
                        for pattern in redaction._TOKEN_PATTERNS:
                            check()
                            for match in pattern.finditer(text):
                                remember_secret(match.group(0))

                original = snapshot(payload)
                if len(json.dumps(original, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()) > self._policy.max_bytes:
                    raise PrivacyError("payload_too_large")
                collect(original)
                check()

                def mask_text(text):
                    check()
                    # Never compile raw secret values into a regex: Python's
                    # regex cache would retain them beyond the session TTL.
                    secret_spans = []
                    for secret_value in secret_values:
                        check()
                        offset = 0
                        while True:
                            start = text.find(secret_value, offset)
                            if start < 0:
                                break
                            offset = start + len(secret_value)
                            secret_spans.append((start, offset))
                            if len(secret_spans) > self._policy.max_nodes:
                                raise PrivacyError("identifier_limit")
                    if secret_spans:
                        # Do not leave a half-identifier after a short secret
                        # overlaps one, or make its remainder restorable.
                        for start, end in pii_spans(text):
                            if any(start < b and end > a for a, b in secret_spans):
                                secret_spans.append((start, end))
                        merged = []
                        for start, end in sorted(secret_spans):
                            if merged and start <= merged[-1][1]:
                                merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
                            else:
                                merged.append((start, end))
                        chunks, offset = [], 0
                        for start, end in merged:
                            chunks.extend((text[offset:start], SECRET_REMOVED))
                            offset = end
                        chunks.append(text[offset:])
                        text = "".join(chunks)
                    chunks, offset = [], 0
                    for start, end in pii_spans(text):
                        value = text[start:end]
                        token = self._tokens.get(value)
                        if token is None:
                            if len(self._values) >= self._policy.max_identifiers:
                                raise PrivacyError("identifier_limit")
                            token = "[CMPII:" + self._namespace + ":" + secrets.token_hex(16) + "]"
                            if token in self._values:
                                raise PrivacyError("token_collision")
                            self._tokens[value] = token
                            self._values[token] = value
                        chunks.extend((text[offset:start], token))
                        offset = end
                    chunks.append(text[offset:])
                    return "".join(chunks)

                def transform(value):
                    check()
                    if type(value) is str:
                        return mask_text(value)
                    if type(value) in (int, float):
                        text = numeric_text(value)
                        masked = mask_text(text)
                        return value if masked == text else masked
                    if type(value) is list:
                        return [transform(item) for item in value]
                    if type(value) is dict:
                        out = {}
                        for key, item in value.items():
                            masked_key = mask_text(key)
                            if masked_key in out:
                                raise PrivacyError("masked_key_collision")
                            out[masked_key] = SECRET_REMOVED if _sensitive_key(key) else transform(item)
                        return out
                    return value

                masked = transform(original)
                encoded = json.dumps(masked, sort_keys=True, ensure_ascii=True, allow_nan=False,
                                     separators=(",", ":")).encode("utf-8")
                check()
                if len(encoded) > self._policy.max_bytes:
                    raise PrivacyError("payload_too_large")
                self._masked = encoded
                return encoded
            except PrivacyError:
                self.close()
                raise
            except Exception:  # noqa: BLE001 - never expose detector errors or raw fallback
                self.close()
                raise PrivacyError("masking_failed") from None
            finally:
                secret_values.clear()

    def _dispatch_bytes(self, scope):
        with self._lock:
            self._live()
            if scope != self._scope:
                raise PrivacyError("scope_mismatch")
            if self._masked is None:
                raise PrivacyError("payload_not_masked")
            return self._masked, self._expires

    def restore(self, text, *, scope, field):
        """Single-pass, escaped text for the authorized local explanation only."""
        if type(text) is not str or len(text) > self._policy.max_bytes:
            raise PrivacyError("invalid_result_text")
        if type(scope) is not str or scope != self._scope:
            raise PrivacyError("scope_mismatch")
        if type(field) is not str or field != "explanation":
            raise PrivacyError("restoration_field_forbidden")
        with self._lock:
            if self._closed or time.monotonic() >= self._expires:
                self.close()
                return html.escape(text, quote=True)
            return html.escape(_TOKEN.sub(lambda match: self._values.get(match.group(0), match.group(0)), text), quote=True)


class ConsentGate:
    """Explicit consent generation, serialized with every bounded send/retry."""
    __slots__ = ("_generation", "_lock", "_policy", "_processor", "_scope", "_started")

    def __init__(self, scope):
        self._scope = _label(scope)
        self._lock = threading.RLock()
        self._generation = 0
        self._policy = None
        self._processor = None
        self._started = 0

    def __repr__(self):
        return "<ConsentGate>"

    def grant(self, policy, processor_policy):
        if type(policy) is not PrivacyPolicy:
            raise PrivacyError("invalid_policy")
        _label(processor_policy)
        with self._lock:
            self._generation += 1
            self._policy, self._processor = policy, processor_policy
            return self._generation

    def revoke(self):
        # Acknowledgement waits for any already-started bounded callback.
        # Nothing queued with an earlier generation can start afterward.
        with self._lock:
            self._generation += 1
            self._policy = self._processor = None
            return self._generation

    @property
    def dispatch_count(self):
        with self._lock:
            return self._started

    def dispatch(self, session, generation, processor_policy, transport, *, timeout_seconds=5.0):
        _number(timeout_seconds, 0.001, 30.0, "invalid_timeout")
        _label(processor_policy)
        if type(session) is not MaskingSession or type(generation) is not int or not callable(transport):
            raise PrivacyError("invalid_dispatch")
        deadline = time.monotonic() + timeout_seconds
        if not self._lock.acquire(timeout=timeout_seconds):
            raise PrivacyError("dispatch_timeout")
        try:
            if (self._policy is None or generation != self._generation
                    or session.policy != self._policy or processor_policy != self._processor):
                raise PrivacyError("consent_required")
            try:
                if endpoints.egress_suppressed():
                    raise PrivacyError("egress_suppressed")
            except PrivacyError:
                raise
            except Exception:  # noqa: BLE001 - unknown egress state must stop dispatch
                raise PrivacyError("egress_unavailable") from None
            encoded, expires = session._dispatch_bytes(self._scope)
            remaining = min(deadline, expires) - time.monotonic()
            if remaining <= 0:
                raise PrivacyError("dispatch_timeout")
            self._started += 1
            try:
                result = transport(encoded, timeout=remaining)
            except Exception:  # noqa: BLE001 - transport exceptions can contain request data
                raise PrivacyError("transport_failed") from None
            if time.monotonic() >= deadline:
                raise PrivacyError("transport_timeout")
            return result
        finally:
            self._lock.release()
