"""In-process rolling store for ``POST /api/paywall/event`` client beacons.

The frontend fires a fire-and-forget ``paywall_view`` / ``paywall_cta_click``
ping every time a locked feature or runtime shows the upgrade card, and every
time a viewer clicks the CTA. Today ``routes/entitlement.py::api_paywall_event``
just logs the ping and returns 204 -- the data lands in the daemon log and
vanishes. An operator wanting to answer "which locked features are pulling
the most attention this session?" has to grep the log by hand.

This module gives that operator a small, bounded, thread-safe rolling store
so ``GET /api/paywall/events/summary`` can hand back a live tally and
``GET /api/paywall/events/recent`` can hand back the last N pings verbatim,
without persisting anything to disk. The store is intentionally in-process
only -- it survives across requests inside a single Flask worker but resets
on daemon restart, so no schema / migration / on-disk-format concerns.

Design invariants:

* **Bounded** -- the ring holds at most ``capacity()`` events (default 200,
  overridable via ``CLAWMETRY_PAYWALL_EVENT_CAPACITY`` in ``[1, 5000]``) so
  a stuck browser tab spraying the endpoint cannot balloon memory.
* **Thread-safe** -- every mutation and every read runs under a
  ``threading.Lock`` because Flask/waitress serves requests from a thread
  pool.
* **Never-raise** -- ``record_event`` swallows every failure. The
  ``/api/paywall/event`` route is a client beacon and must stay 204.
* **Truncation parity** -- ``event`` / ``harness`` / ``source`` /
  ``plan_chosen`` cap at 64 chars, ``feature`` caps at 128 chars, matching
  ``api_paywall_event``'s existing truncation so an oversized field cannot
  balloon a ring entry or a log line.
* **Monotonic totals** -- ``total`` counts every event ever recorded (across
  the ring's lifetime); ``dropped`` counts every event evicted by ring
  rotation. Callers can spot "the ring is churning" without seeing the
  actual eviction rate rise inside ``in_window``.

Nothing here consults ``clawmetry.entitlements`` -- a paid tier gating this
would silently drop the very events the operator most needs to see (locked
features being clicked at). Grace mode.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from collections import Counter, deque
from typing import Any


logger = logging.getLogger("clawmetry.paywall.events")


_EVENT_MAX = 64
_HARNESS_MAX = 64
_SOURCE_MAX = 64
_PLAN_MAX = 64
_FEATURE_MAX = 128

_DEFAULT_CAPACITY = 200
_MIN_CAPACITY = 1
_MAX_CAPACITY = 5000

_RECENT_DEFAULT = 50
_RECENT_MAX = 200


def _resolve_capacity() -> int:
    """Resolve the ring capacity from the environment, clamped and
    never-raise. A bad value logs a warning and falls through to the
    default so an operator typo cannot make the endpoint 500 for the
    lifetime of the process."""
    raw = os.environ.get("CLAWMETRY_PAYWALL_EVENT_CAPACITY", "").strip()
    if not raw:
        return _DEFAULT_CAPACITY
    try:
        value = int(raw)
    except (TypeError, ValueError):
        logger.warning(
            "paywall.events: bad CLAWMETRY_PAYWALL_EVENT_CAPACITY=%r, using default %d",
            raw, _DEFAULT_CAPACITY,
        )
        return _DEFAULT_CAPACITY
    if value < _MIN_CAPACITY:
        return _MIN_CAPACITY
    if value > _MAX_CAPACITY:
        return _MAX_CAPACITY
    return value


def _coerce_str(value: Any, limit: int) -> str:
    """Coerce a JSON body field to a bounded string.

    Matches ``api_paywall_event``'s ``str(body.get(k, ""))[:limit]`` so an
    oversized or non-string field cannot bloat the ring entry beyond the
    same budget the log line already respects. Never raises.
    """
    if value is None:
        return ""
    try:
        text = str(value)
    except Exception:
        return ""
    if len(text) > limit:
        return text[:limit]
    return text


class _PaywallEventStore:
    """Thread-safe bounded ring + running aggregates for paywall beacons.

    Not exposed directly -- callers use the module-level ``record_event``,
    ``summary``, ``recent``, ``reset``, ``capacity`` shims below so a future
    move to a different backing store keeps the module API stable.
    """

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._ring: deque = deque(maxlen=capacity)
        self._total = 0
        self._dropped = 0
        self._first_ts: float | None = None
        self._last_ts: float | None = None
        self._lock = threading.Lock()

    def capacity(self) -> int:
        return self._capacity

    def resize(self, new_capacity: int) -> None:
        """Rebuild the ring at ``new_capacity``, preserving the tail. Only
        used by tests / operator to shrink or grow the window without
        restarting the process. Increments ``dropped`` for any tail that
        falls out of the shrunken window so the summary still reflects
        reality."""
        clamped = max(_MIN_CAPACITY, min(_MAX_CAPACITY, int(new_capacity)))
        with self._lock:
            old = list(self._ring)
            if len(old) > clamped:
                self._dropped += len(old) - clamped
                old = old[-clamped:]
            self._ring = deque(old, maxlen=clamped)
            self._capacity = clamped

    def record(self, payload: Any) -> None:
        """Record one client beacon.

        ``payload`` is whatever the route parsed out of the request body --
        typically a dict, but the route uses ``get_json(silent=True) or {}``
        so anything non-dict-shaped short-circuits to a no-op recording,
        matching the endpoint's "empty body still returns 204" contract.

        Never raises.
        """
        try:
            if not isinstance(payload, dict):
                # Match the route: a list / string / None body degrades to
                # "no fields", but we still bump the counter so the operator
                # can see "beacons are firing but the client is malformed".
                payload = {}

            event = _coerce_str(payload.get("event"), _EVENT_MAX)
            feature = _coerce_str(payload.get("feature"), _FEATURE_MAX)
            harness = _coerce_str(payload.get("harness"), _HARNESS_MAX)
            source = _coerce_str(payload.get("source"), _SOURCE_MAX)
            plan_chosen = _coerce_str(payload.get("plan_chosen"), _PLAN_MAX)
            now = time.time()

            entry = {
                "event": event,
                "feature": feature,
                "harness": harness,
                "source": source,
                "plan_chosen": plan_chosen,
                "ts": now,
            }

            with self._lock:
                if len(self._ring) == self._capacity:
                    # deque.append will evict the leftmost element.
                    self._dropped += 1
                self._ring.append(entry)
                self._total += 1
                if self._first_ts is None:
                    self._first_ts = now
                self._last_ts = now
        except Exception as exc:
            # Genuinely defensive -- record must never leak into the 204 route.
            logger.debug("paywall.events: record swallowed error: %s", exc)

    def summary(self) -> dict:
        """Return a JSON-safe aggregate snapshot of the current ring.

        Aggregations (``by_event`` etc.) reflect ONLY the events currently
        in the ring -- deliberately -- so an operator sees "what's live" and
        not "what happened weeks ago and was evicted". Long-run totals live
        in ``total`` / ``dropped`` for context.

        Empty-key values (e.g. an event with no ``feature``) are excluded
        from the per-key dicts so a mostly-empty payload doesn't flood
        every dimension's tally with an ``""`` bucket.

        Never raises.
        """
        try:
            with self._lock:
                snap = list(self._ring)
                total = self._total
                dropped = self._dropped
                first_ts = self._first_ts
                last_ts = self._last_ts
                capacity = self._capacity

            by_event: Counter = Counter()
            by_feature: Counter = Counter()
            by_harness: Counter = Counter()
            by_source: Counter = Counter()
            by_plan: Counter = Counter()
            for e in snap:
                if e.get("event"):
                    by_event[e["event"]] += 1
                if e.get("feature"):
                    by_feature[e["feature"]] += 1
                if e.get("harness"):
                    by_harness[e["harness"]] += 1
                if e.get("source"):
                    by_source[e["source"]] += 1
                if e.get("plan_chosen"):
                    by_plan[e["plan_chosen"]] += 1

            return {
                "total": total,
                "in_window": len(snap),
                "dropped": dropped,
                "capacity": capacity,
                "first_ts": first_ts,
                "last_ts": last_ts,
                "by_event": dict(by_event),
                "by_feature": dict(by_feature),
                "by_harness": dict(by_harness),
                "by_source": dict(by_source),
                "by_plan_chosen": dict(by_plan),
            }
        except Exception as exc:
            logger.warning("paywall.events: summary swallowed error: %s", exc)
            return {
                "total": 0,
                "in_window": 0,
                "dropped": 0,
                "capacity": self._capacity,
                "first_ts": None,
                "last_ts": None,
                "by_event": {},
                "by_feature": {},
                "by_harness": {},
                "by_source": {},
                "by_plan_chosen": {},
            }

    def recent(self, limit: int) -> list[dict]:
        """Return up to ``limit`` most-recent events, newest first.

        ``limit`` is clamped into ``[0, _RECENT_MAX]`` so an operator can't
        blow the response size out with ``?limit=999999``. A negative or
        non-int limit falls back to ``_RECENT_DEFAULT``. Never raises.
        """
        try:
            try:
                n = int(limit)
            except (TypeError, ValueError):
                n = _RECENT_DEFAULT
            if n < 0:
                n = _RECENT_DEFAULT
            if n > _RECENT_MAX:
                n = _RECENT_MAX
            if n == 0:
                return []
            with self._lock:
                snap = list(self._ring)
            snap.reverse()
            return [dict(e) for e in snap[:n]]
        except Exception as exc:
            logger.warning("paywall.events: recent swallowed error: %s", exc)
            return []

    def reset(self) -> None:
        with self._lock:
            self._ring.clear()
            self._total = 0
            self._dropped = 0
            self._first_ts = None
            self._last_ts = None


_STORE = _PaywallEventStore(_resolve_capacity())


def record_event(payload: Any) -> None:
    """Public shim for ``routes/entitlement.py::api_paywall_event``."""
    _STORE.record(payload)


def summary() -> dict:
    """Public shim for ``GET /api/paywall/events/summary``."""
    return _STORE.summary()


def recent(limit: int | None = None) -> list[dict]:
    """Public shim for ``GET /api/paywall/events/recent``."""
    if limit is None:
        limit = _RECENT_DEFAULT
    return _STORE.recent(limit)


def reset() -> None:
    """Test / operator-only shim to clear the store without a restart."""
    _STORE.reset()


def capacity() -> int:
    """Effective ring capacity (env-driven at import; test-adjustable via
    :func:`_set_capacity`)."""
    return _STORE.capacity()


def _set_capacity(new_capacity: int) -> None:
    """Test-only knob for shrinking / growing the ring at runtime.

    Prefixed with underscore because production code should let the env
    var pick the size once at import."""
    _STORE.resize(new_capacity)


RECENT_DEFAULT_LIMIT = _RECENT_DEFAULT
RECENT_MAX_LIMIT = _RECENT_MAX
