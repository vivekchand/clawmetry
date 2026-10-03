"""Tell a value the store cannot hold from a store that failed (REQ-OBS-OIA-001).

The local DuckDB store keeps token counts in ``INTEGER`` (int32) columns, while
OpenTelemetry carries int64. A token count beyond that range, or a string the
driver cannot encode (a lone surrogate from a JSON body), fails every time it
is written: a retry resends the same value. Such an item must be refused on
its own, so it neither poisons the rest of its batch nor makes the sender
retry forever.

Anything else (a closed connection, an I/O error, a lock) is not the data's
fault. It stays a failure, and the OTLP receiver answers 503 so the sender
keeps the batch and resends it.

``clawmetry.local_store`` imports both helpers under their historical private
names (``_is_data_error``, ``_int32_or_none``):

* ``ingest_spans_batch`` writes a span batch in one transaction. When that
  write fails with a data error it writes the spans again one at a time, so
  the valid spans land and only the bad one is counted as refused.
* ``put_otlp_batch`` counts a record that fails with a data error as
  ``records_rejected``, not ``records_failed``.
* the event row builder stores an out-of-range ``events.token_count`` as
  unknown, because an exception in the ring flush fails every event queued
  beside it.
* the ring flush that fails with a data error rewrites the text of its events
  with ``storable_text`` and writes them again, so an event carrying a lone
  surrogate lands (with U+FFFD in its place) instead of holding the ring.
"""

from __future__ import annotations

from typing import Any, Optional

__all__ = [
    "INT32_MIN", "INT32_MAX", "int32_or_none", "is_data_error", "storable_text",
]

INT32_MIN, INT32_MAX = -(2 ** 31), 2 ** 31 - 1


def int32_or_none(v: Any) -> Optional[int]:
    """A count for an INTEGER column, or ``None`` (unknown) when it is not a
    number or does not fit. Used where a value is written by the ring flush:
    an exception there fails the flush for every event queued beside it, on
    every retry."""
    if v is None:
        return None
    try:
        n = int(v)
    except (TypeError, ValueError, OverflowError):
        return None
    return n if INT32_MIN <= n <= INT32_MAX else None


def is_data_error(exc: BaseException) -> bool:
    """True when a write failed because of a VALUE in the row, not the store.

    A DuckDB ``DataError`` (conversion or out-of-range), a ``ValueError`` /
    ``OverflowError``, or the driver's own cast error for a Python value it
    cannot convert. Everything else, including DuckDB's ``IOException`` and
    ``ConnectionException``, is a store failure."""
    if isinstance(exc, (ValueError, OverflowError)):
        return True
    try:
        import duckdb
    except Exception:  # no driver: nothing below can be a driver data error
        return False
    if isinstance(exc, duckdb.DataError):
        return True
    return isinstance(exc, RuntimeError) and "Unable to cast Python instance" in str(exc)


def _storable_str(s: str) -> str:
    if s.isascii():
        return s
    try:
        s.encode("utf-8")
        return s
    except UnicodeEncodeError:
        # A split surrogate pair becomes its character; a lone one, U+FFFD.
        return s.encode("utf-16", "surrogatepass").decode("utf-16", "replace")


def storable_text(v: Any) -> Any:
    """``v`` with every string the driver cannot encode made storable: a lone
    surrogate (JSON allows ``"\\ud800"``, UTF-8 does not) becomes U+FFFD.
    Walks dicts (keys too), lists and tuples. Returns ``v`` itself when
    nothing changed, so a caller can tell with ``is``."""
    if isinstance(v, str):
        return _storable_str(v)
    if isinstance(v, dict):
        out = {storable_text(k): storable_text(x) for k, x in v.items()}
        if len(out) == len(v) and all(
            a is b and out[a] is x for (a, x), b in zip(v.items(), out)
        ):
            return v
        return out
    if isinstance(v, (list, tuple)):
        items = [storable_text(x) for x in v]
        if all(a is b for a, b in zip(v, items)):
            return v
        return items if isinstance(v, list) else tuple(items)
    return v
