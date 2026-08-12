"""clawmetry/otlp_json.py: stdlib OTLP/JSON decoder (issue #4781).

Why this exists
---------------
``opentelemetry-proto`` + ``protobuf`` live behind the ``otel`` extra, so a
default ``pip install clawmetry`` answered **501** to every OTLP request. The
receiver we advertise in the README was off for most users on first run.

Moving those deps into ``install_requires`` would fix it in one line, but adds
~5 MB and a famously version-sensitive dependency to every install, against the
minimal-dependency rule (flask + waitress + cryptography + duckdb).

OTLP has a JSON encoding, and JSON is the one format the standard library can
always read. This module parses it and returns objects that **duck-type the
protobuf message API** -- ``req.resource_spans[i].scope_spans[j].spans[k]`` with
``.attributes``, ``.start_time_unix_nano``, ``.HasField("status")``, and friends.
That way ``dashboard._process_otlp_traces`` / ``_process_otlp_logs`` and
``_otel_to_row`` run **unchanged** over either wire format: one mapper, one set
of semantics, no second code path to drift.

Encoding details the OTLP/JSON spec mandates (and that trip people up):
  * ``traceId`` / ``spanId`` / ``parentSpanId`` are lowercase hex STRINGS, not
    bytes. ``dashboard._hex`` passes strings through untouched.
  * 64-bit ints (``startTimeUnixNano``, ``intValue``) are STRINGS, because JSON
    numbers cannot hold int64 without precision loss.
  * enums (``kind``, ``status.code``) may arrive as an int OR as their proto
    name (``"SPAN_KIND_CLIENT"``, ``"STATUS_CODE_ERROR"``).
  * protobuf's canonical JSON is lowerCamelCase, but its parser also accepts the
    original snake_case field names, so we accept both.

Not covered: metrics. ``_process_otlp_metrics`` reaches into sum/gauge/
histogram/summary point types and is a bigger surface; it keeps the protobuf
requirement until its own issue lands. :func:`decode` raises
:class:`OtlpProtobufUnavailable` for it so the caller answers an honest 501.
"""
from __future__ import annotations

import gzip
import io
import json
import logging
from typing import Any

logger = logging.getLogger("clawmetry.otlp_json")

__all__ = ["decode", "OtlpProtobufUnavailable"]


class OtlpProtobufUnavailable(Exception):
    """Raised when a payload can only be read with ``opentelemetry-proto``.

    The HTTP layer turns this into 501 with the install hint. It means "this
    encoding needs the extra", never "the payload was bad" (that is a 400).
    """


# Decompression cap. Same knob the protobuf receiver uses
# (``dashboard._OTLP_MAX_DECOMPRESSED``): a small compressed body must not be
# allowed to inflate into an OOM, and both wire formats must agree on the cap.
try:
    import os as _os
    _MAX_DECOMPRESSED = int(
        _os.environ.get("CLAWMETRY_OTLP_MAX_DECOMPRESSED_MB", "64")) * 1024 * 1024
except (TypeError, ValueError):
    _MAX_DECOMPRESSED = 64 * 1024 * 1024

# Enum names -> proto ints. The mappers index _OTEL_SPAN_KIND_NAMES /
# _OTEL_STATUS_CODE_NAMES by int, so normalise here.
_SPAN_KINDS = {
    "SPAN_KIND_UNSPECIFIED": 0,
    "SPAN_KIND_INTERNAL": 1,
    "SPAN_KIND_SERVER": 2,
    "SPAN_KIND_CLIENT": 3,
    "SPAN_KIND_PRODUCER": 4,
    "SPAN_KIND_CONSUMER": 5,
}
_STATUS_CODES = {
    "STATUS_CODE_UNSET": 0,
    "STATUS_CODE_OK": 1,
    "STATUS_CODE_ERROR": 2,
}


def _get(d: dict, *names, default=None):
    """First present key among ``names`` (camelCase and snake_case aliases)."""
    for n in names:
        if n in d and d[n] is not None:
            return d[n]
    return default


def _as_int(v, default: int = 0) -> int:
    """int64-safe coercion. OTLP/JSON ships these as strings."""
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _as_enum(v, names: dict, default: int = 0) -> int:
    if v is None:
        return default
    if isinstance(v, str):
        return names.get(v.strip().upper(), default)
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _as_hex(v) -> str:
    """Ids are already lowercase hex strings in OTLP/JSON. ``_hex`` in
    dashboard.py returns non-bytes unchanged, so pass the string through and
    keep '' for absent ids (root spans rely on parent_span_id being falsy)."""
    if not v:
        return ""
    if isinstance(v, (bytes, bytearray)):
        return v.hex()
    return str(v).strip().lower()


class _AnyValue:
    """Duck-type of the proto ``AnyValue``, for ``_otel_attr_value``.

    That helper probes ``HasField("string_value")`` and friends, then falls back
    to ``str(val)``. Arrays and kvlists have no scalar field, so they report no
    field and stringify as compact JSON -- structurally the same outcome the
    protobuf path produces for them.
    """

    __slots__ = ("string_value", "int_value", "double_value", "bool_value", "_present", "_raw")

    def __init__(self, raw: Any):
        self.string_value = ""
        self.int_value = 0
        self.double_value = 0.0
        self.bool_value = False
        self._present: str | None = None
        self._raw = raw
        if not isinstance(raw, dict):
            # A bare scalar is not spec-shaped, but tolerate it rather than
            # dropping the attribute (never crash on bad input).
            if isinstance(raw, bool):
                self.bool_value, self._present = raw, "bool_value"
            elif isinstance(raw, int):
                self.int_value, self._present = raw, "int_value"
            elif isinstance(raw, float):
                self.double_value, self._present = raw, "double_value"
            elif raw is not None:
                self.string_value, self._present = str(raw), "string_value"
            return
        if "stringValue" in raw or "string_value" in raw:
            self.string_value = str(_get(raw, "stringValue", "string_value", default="") or "")
            self._present = "string_value"
        elif "intValue" in raw or "int_value" in raw:
            self.int_value = _as_int(_get(raw, "intValue", "int_value"))
            self._present = "int_value"
        elif "doubleValue" in raw or "double_value" in raw:
            try:
                self.double_value = float(_get(raw, "doubleValue", "double_value", default=0.0))
            except (TypeError, ValueError):
                self.double_value = 0.0
            self._present = "double_value"
        elif "boolValue" in raw or "bool_value" in raw:
            self.bool_value = bool(_get(raw, "boolValue", "bool_value", default=False))
            self._present = "bool_value"
        elif "bytesValue" in raw or "bytes_value" in raw:
            self.string_value = str(_get(raw, "bytesValue", "bytes_value", default="") or "")
            self._present = "string_value"

    def HasField(self, name: str) -> bool:  # noqa: N802 - mirrors the proto API
        return self._present == name

    def __str__(self) -> str:
        if self._present == "string_value":
            return self.string_value
        try:
            return json.dumps(_plain_value(self._raw), separators=(",", ":"))
        except Exception:
            return str(self._raw)


def _plain_value(raw: Any) -> Any:
    """Recursively reduce an AnyValue dict to plain Python, for arrays/kvlists."""
    if not isinstance(raw, dict):
        return raw
    if "stringValue" in raw or "string_value" in raw:
        return _get(raw, "stringValue", "string_value", default="")
    if "intValue" in raw or "int_value" in raw:
        return _as_int(_get(raw, "intValue", "int_value"))
    if "doubleValue" in raw or "double_value" in raw:
        return _get(raw, "doubleValue", "double_value", default=0.0)
    if "boolValue" in raw or "bool_value" in raw:
        return bool(_get(raw, "boolValue", "bool_value", default=False))
    arr = _get(raw, "arrayValue", "array_value")
    if isinstance(arr, dict):
        return [_plain_value(v) for v in (arr.get("values") or [])]
    kv = _get(raw, "kvlistValue", "kvlist_value")
    if isinstance(kv, dict):
        return {
            str(item.get("key", "")): _plain_value(item.get("value"))
            for item in (kv.get("values") or [])
            if isinstance(item, dict)
        }
    return raw


class _KeyValue:
    __slots__ = ("key", "value")

    def __init__(self, raw: dict):
        self.key = str(raw.get("key", "") or "")
        self.value = _AnyValue(raw.get("value"))


def _attrs(raw_list) -> list:
    out = []
    for item in raw_list or []:
        if isinstance(item, dict) and item.get("key"):
            out.append(_KeyValue(item))
    return out


class _Status:
    __slots__ = ("code", "message")

    def __init__(self, raw: dict):
        self.code = _as_enum(raw.get("code"), _STATUS_CODES)
        self.message = str(raw.get("message", "") or "")


class _SpanEvent:
    __slots__ = ("time_unix_nano", "name", "attributes")

    def __init__(self, raw: dict):
        self.time_unix_nano = _as_int(_get(raw, "timeUnixNano", "time_unix_nano"))
        self.name = str(raw.get("name", "") or "")
        self.attributes = _attrs(raw.get("attributes"))


class _SpanLink:
    __slots__ = ("trace_id", "span_id", "attributes")

    def __init__(self, raw: dict):
        self.trace_id = _as_hex(_get(raw, "traceId", "trace_id"))
        self.span_id = _as_hex(_get(raw, "spanId", "span_id"))
        self.attributes = _attrs(raw.get("attributes"))


class _Span:
    __slots__ = (
        "trace_id", "span_id", "parent_span_id", "name", "kind",
        "start_time_unix_nano", "end_time_unix_nano",
        "attributes", "events", "links", "status", "_has_status",
    )

    def __init__(self, raw: dict):
        self.trace_id = _as_hex(_get(raw, "traceId", "trace_id"))
        self.span_id = _as_hex(_get(raw, "spanId", "span_id"))
        self.parent_span_id = _as_hex(_get(raw, "parentSpanId", "parent_span_id"))
        self.name = str(raw.get("name", "") or "")
        self.kind = _as_enum(raw.get("kind"), _SPAN_KINDS)
        self.start_time_unix_nano = _as_int(
            _get(raw, "startTimeUnixNano", "start_time_unix_nano"))
        self.end_time_unix_nano = _as_int(
            _get(raw, "endTimeUnixNano", "end_time_unix_nano"))
        self.attributes = _attrs(raw.get("attributes"))
        self.events = [_SpanEvent(e) for e in (raw.get("events") or []) if isinstance(e, dict)]
        self.links = [_SpanLink(ln) for ln in (raw.get("links") or []) if isinstance(ln, dict)]
        raw_status = raw.get("status")
        self._has_status = isinstance(raw_status, dict)
        self.status = _Status(raw_status if self._has_status else {})

    def HasField(self, name: str) -> bool:  # noqa: N802 - mirrors the proto API
        if name == "status":
            return self._has_status
        return False


class _LogRecord:
    __slots__ = ("time_unix_nano", "event_name", "severity_text", "body", "attributes")

    def __init__(self, raw: dict):
        self.time_unix_nano = _as_int(_get(raw, "timeUnixNano", "time_unix_nano"))
        self.event_name = str(_get(raw, "eventName", "event_name", default="") or "")
        self.severity_text = str(_get(raw, "severityText", "severity_text", default="") or "")
        body = raw.get("body")
        self.body = _plain_value(body) if isinstance(body, dict) else body
        self.attributes = _attrs(raw.get("attributes"))


class _Resource:
    __slots__ = ("attributes",)

    def __init__(self, raw: dict):
        self.attributes = _attrs(raw.get("attributes"))


class _ScopeSpans:
    __slots__ = ("spans",)

    def __init__(self, raw: dict):
        self.spans = [_Span(s) for s in (raw.get("spans") or []) if isinstance(s, dict)]


class _ScopeLogs:
    __slots__ = ("log_records",)

    def __init__(self, raw: dict):
        records = _get(raw, "logRecords", "log_records", default=[]) or []
        self.log_records = [_LogRecord(r) for r in records if isinstance(r, dict)]


class _ResourceSpans:
    __slots__ = ("resource", "scope_spans")

    def __init__(self, raw: dict):
        res = raw.get("resource")
        self.resource = _Resource(res) if isinstance(res, dict) else None
        scopes = _get(raw, "scopeSpans", "scope_spans", default=[]) or []
        self.scope_spans = [_ScopeSpans(s) for s in scopes if isinstance(s, dict)]


class _ResourceLogs:
    __slots__ = ("resource", "scope_logs")

    def __init__(self, raw: dict):
        res = raw.get("resource")
        self.resource = _Resource(res) if isinstance(res, dict) else None
        scopes = _get(raw, "scopeLogs", "scope_logs", default=[]) or []
        self.scope_logs = [_ScopeLogs(s) for s in scopes if isinstance(s, dict)]


class _TraceRequest:
    __slots__ = ("resource_spans",)

    def __init__(self, raw: dict):
        items = _get(raw, "resourceSpans", "resource_spans", default=[]) or []
        self.resource_spans = [_ResourceSpans(r) for r in items if isinstance(r, dict)]


class _LogsRequest:
    __slots__ = ("resource_logs",)

    def __init__(self, raw: dict):
        items = _get(raw, "resourceLogs", "resource_logs", default=[]) or []
        self.resource_logs = [_ResourceLogs(r) for r in items if isinstance(r, dict)]


def _gunzip(data: bytes) -> bytes:
    """Bounded gunzip. A 1 KB body must not inflate into an OOM."""
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
        out = gz.read(_MAX_DECOMPRESSED + 1)
    if len(out) > _MAX_DECOMPRESSED:
        raise ValueError("OTLP/JSON payload exceeds decompression cap")
    return out


def decode(payload, kind: str, content_encoding: str | None = None):
    """Decode an OTLP/JSON body into a protobuf-shaped request object.

    Args:
      payload: raw request body (bytes or str), optionally gzipped.
      kind: ``"traces"`` or ``"logs"``. ``"metrics"`` raises
        :class:`OtlpProtobufUnavailable` -- its mapper still needs protobuf.
      content_encoding: the request's ``Content-Encoding`` header.

    Raises:
      OtlpProtobufUnavailable: for ``kind="metrics"``.
      ValueError: on a malformed body (the caller turns this into a 400).
    """
    if kind == "metrics":
        raise OtlpProtobufUnavailable(
            "OTLP/JSON metrics need opentelemetry-proto; traces and logs do not"
        )
    if kind not in ("traces", "logs"):
        raise ValueError(f"unknown OTLP kind: {kind}")

    if "gzip" in (content_encoding or "").lower():
        payload = _gunzip(payload if isinstance(payload, (bytes, bytearray)) else
                          str(payload).encode("utf-8"))
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8")
    raw = json.loads(payload or "{}")
    if not isinstance(raw, dict):
        raise ValueError("OTLP/JSON body must be an object")

    return _TraceRequest(raw) if kind == "traces" else _LogsRequest(raw)
