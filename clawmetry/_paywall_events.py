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


_FILTER_KEYS = ("event", "feature", "harness", "source", "plan_chosen")


def _normalise_filters(**kwargs: Any) -> dict[str, str]:
    """Collapse the filter kwargs to a ``{key: value}`` dict keeping only
    non-blank string values.

    A ``None``, empty string, or all-whitespace value means "not supplied"
    and is dropped so the caller doesn't have to enumerate every
    dimension. Non-string values are coerced via ``str(...)`` (matching
    the store's own :func:`_coerce_str` posture) so a caller passing an
    int is not silently unmatchable. Whitespace is stripped from the ends
    only -- the stored values are never whitespace-padded, and stripping
    the interior would break exact-match on legitimately spaced
    ``source`` labels like ``"runtime switcher"``.

    Never raises.
    """
    out: dict[str, str] = {}
    for key in _FILTER_KEYS:
        raw = kwargs.get(key)
        if raw is None:
            continue
        try:
            text = str(raw).strip()
        except Exception:
            continue
        if not text:
            continue
        out[key] = text
    return out


def _row_matches_filters(row: dict, filters: dict[str, str]) -> bool:
    """Return True iff every filter key/value matches the row's stored
    field exactly. Missing row fields short-circuit to ``False`` (a filter
    on a dimension the row does not carry is a mismatch, not a wildcard).
    Never raises.
    """
    try:
        for key, want in filters.items():
            if row.get(key, "") != want:
                return False
        return True
    except Exception:
        return False


def _coerce_ts_bound(raw: Any) -> float | None:
    """Coerce one of ``since`` / ``until`` to epoch-seconds ``float``, or
    return ``None`` for "not supplied".

    A ``None``, empty string, all-whitespace string, non-numeric string,
    ``NaN``, or negative timestamp collapses to ``None`` so a caller's
    stray query string cannot restrict the window unexpectedly. An ``int``
    or ``float`` passes through after the same NaN / negative filter.

    Never raises.
    """
    if raw is None:
        return None
    try:
        if isinstance(raw, bool):
            # ``bool`` is an ``int`` subclass in Python; treat it as "not
            # supplied" so a stray ``True`` / ``False`` doesn't get coerced
            # to ``1.0`` / ``0.0`` and start slicing.
            return None
        if isinstance(raw, (int, float)):
            value = float(raw)
        else:
            text = str(raw).strip()
            if not text:
                return None
            value = float(text)
    except (TypeError, ValueError):
        return None
    # NaN comparisons always return False; treat NaN and negative epoch as
    # "not supplied" so a bogus bound is ignored rather than dropping every
    # row on the floor.
    if value != value:  # pragma: no cover - explicit NaN guard
        return None
    if value < 0:
        return None
    return value


def _normalise_time_bounds(
    since: Any, until: Any,
) -> tuple[float | None, float | None]:
    """Return the coerced ``(since, until)`` pair (each ``float | None``).

    ``since`` is inclusive, ``until`` is exclusive -- the standard half-open
    ``[since, until)`` convention -- so back-to-back windows do NOT double-
    count events landing exactly on the boundary. If both bounds resolve
    and ``since >= until`` the window is empty by construction; the store
    passes the pair through unchanged and every row is filtered out, which
    is the intended "empty window" behaviour.

    Never raises.
    """
    return _coerce_ts_bound(since), _coerce_ts_bound(until)


def _row_matches_time_window(
    row: dict, since: float | None, until: float | None,
) -> bool:
    """Return True iff ``row['ts']`` falls in the half-open window
    ``[since, until)``. Either bound may be ``None`` meaning "unbounded on
    that side". A row without a numeric ``ts`` is treated as a mismatch
    when either bound is supplied (a bounded query cannot match a row of
    unknown age), and as a match when neither bound is supplied. Never
    raises.
    """
    if since is None and until is None:
        return True
    ts = row.get("ts")
    if not isinstance(ts, (int, float)) or isinstance(ts, bool):
        return False
    if since is not None and ts < since:
        return False
    if until is not None and ts >= until:
        return False
    return True


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

    def summary(
        self,
        *,
        event: str | None = None,
        feature: str | None = None,
        harness: str | None = None,
        source: str | None = None,
        plan_chosen: str | None = None,
        since: Any = None,
        until: Any = None,
    ) -> dict:
        """Return a JSON-safe aggregate snapshot of the current ring.

        Aggregations (``by_event`` etc.) reflect ONLY the events currently
        in the ring -- deliberately -- so an operator sees "what's live" and
        not "what happened weeks ago and was evicted". Long-run totals live
        in ``total`` / ``dropped`` for context.

        Empty-key values (e.g. an event with no ``feature``) are excluded
        from the per-key dicts so a mostly-empty payload doesn't flood
        every dimension's tally with an ``""`` bucket.

        Optional keyword filters (``event`` / ``feature`` / ``harness`` /
        ``source`` / ``plan_chosen``) narrow the aggregation to rows whose
        corresponding field matches the supplied value exactly. Same
        semantics as :meth:`recent` / :meth:`count_matching`: ``None`` or
        empty-string means "not supplied", case-sensitive exact match,
        ``AND`` combined. With no filters the returned shape is byte-
        identical to the pre-filter contract EXCEPT for the always-present
        ``filters``, ``matched``, and ``time_window`` fields (added below).

        Optional keyword bounds (``since`` / ``until``) further restrict
        the aggregation to rows whose ``ts`` falls in the half-open
        interval ``[since, until)`` (epoch seconds; either bound may be
        ``None`` = unbounded on that side). Bounds and categorical
        filters are ``AND`` combined. A bogus bound (non-numeric string,
        ``NaN``, negative epoch, ``bool``) collapses to "not supplied" so
        an operator typo cannot silently drop every row; see
        :func:`_coerce_ts_bound` for the exact contract.

        ``filters`` echoes the applied categorical filter set (empty dict
        when none supplied) so a caller can distinguish "I asked for
        feature=X and got 0 rows" from "I asked for nothing and got 0
        rows". ``time_window`` is a sibling ``{"since": <float|null>,
        "until": <float|null>}`` echo of the resolved time bounds -- it
        is always present so a dashboard tile can trust the top-level key
        set is stable regardless of whether time bounds were supplied.
        ``matched`` is the count of rows the ``by_*`` aggregation was
        computed over -- byte-equal to ``in_window`` on a fully-unfiltered
        call, otherwise the post-filter, post-window subset size. Process-
        lifetime counters (``total``, ``dropped``, ``first_ts``,
        ``last_ts``, ``capacity``) are NOT sliced by the filters or the
        window -- they describe the ring itself, not the subset the caller
        cares about, and slicing them would silently under-report churn to
        a filtered dashboard tile.

        Never raises.
        """
        try:
            filters = _normalise_filters(
                event=event, feature=feature, harness=harness,
                source=source, plan_chosen=plan_chosen,
            )
            since_ts, until_ts = _normalise_time_bounds(since, until)
            with self._lock:
                snap = list(self._ring)
                total = self._total
                dropped = self._dropped
                first_ts = self._first_ts
                last_ts = self._last_ts
                capacity = self._capacity

            bucket = snap
            if filters:
                bucket = [e for e in bucket if _row_matches_filters(e, filters)]
            if since_ts is not None or until_ts is not None:
                bucket = [
                    e for e in bucket
                    if _row_matches_time_window(e, since_ts, until_ts)
                ]

            by_event: Counter = Counter()
            by_feature: Counter = Counter()
            by_harness: Counter = Counter()
            by_source: Counter = Counter()
            by_plan: Counter = Counter()
            for e in bucket:
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
                "filters": dict(filters),
                "matched": len(bucket),
                "time_window": {"since": since_ts, "until": until_ts},
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
                "filters": {},
                "matched": 0,
                "time_window": {"since": None, "until": None},
            }

    def recent(
        self,
        limit: int,
        *,
        event: str | None = None,
        feature: str | None = None,
        harness: str | None = None,
        source: str | None = None,
        plan_chosen: str | None = None,
        since: Any = None,
        until: Any = None,
    ) -> list[dict]:
        """Return up to ``limit`` most-recent events, newest first.

        ``limit`` is clamped into ``[0, _RECENT_MAX]`` so an operator can't
        blow the response size out with ``?limit=999999``. A negative or
        non-int limit falls back to ``_RECENT_DEFAULT``. Never raises.

        Optional keyword filters (``event`` / ``feature`` / ``harness`` /
        ``source`` / ``plan_chosen``) restrict the returned rows to those
        whose corresponding field matches the supplied value exactly. A
        ``None`` or empty-string filter is treated as "not supplied" and
        does not restrict on that dimension -- there is deliberately no
        way to query for rows with an empty field via this API, because
        ``?feature=`` in the query string would then be ambiguous.

        Optional keyword bounds (``since`` / ``until``) restrict the
        returned rows to those whose ``ts`` falls in the half-open
        interval ``[since, until)`` (epoch seconds; either bound may be
        ``None`` = unbounded on that side). Bounds combine with categorical
        filters via ``AND``. See :func:`_coerce_ts_bound` for the exact
        "bad bound collapses to unbounded" contract.

        Filter matching is case-sensitive against the stored (post-
        :func:`_coerce_str`) value, matching the case-sensitive keys of
        :meth:`summary`'s ``by_*`` breakdowns. Filters are ``AND``-
        combined so ``event=paywall_cta_click`` + ``feature=fleet`` narrows
        the ring to CTA clicks on the ``fleet`` feature.

        Never raises: a filter failure short-circuits to ``[]`` instead of
        propagating.
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
            filters = _normalise_filters(
                event=event, feature=feature, harness=harness,
                source=source, plan_chosen=plan_chosen,
            )
            since_ts, until_ts = _normalise_time_bounds(since, until)
            with self._lock:
                snap = list(self._ring)
            snap.reverse()

            def _keep(row: dict) -> bool:
                if filters and not _row_matches_filters(row, filters):
                    return False
                if (since_ts is not None or until_ts is not None) and not \
                        _row_matches_time_window(row, since_ts, until_ts):
                    return False
                return True

            if filters or since_ts is not None or until_ts is not None:
                return [dict(e) for e in snap if _keep(e)][:n]
            return [dict(e) for e in snap[:n]]
        except Exception as exc:
            logger.warning("paywall.events: recent swallowed error: %s", exc)
            return []

    def count_matching(
        self,
        *,
        event: str | None = None,
        feature: str | None = None,
        harness: str | None = None,
        source: str | None = None,
        plan_chosen: str | None = None,
        since: Any = None,
        until: Any = None,
    ) -> int:
        """Return the count of ring rows matching the supplied filters,
        BEFORE any ``limit`` clamp is applied.

        Same filter + window semantics as :meth:`recent` (``None`` /
        empty string means "not supplied", case-sensitive exact match,
        ``AND`` combined; ``since`` / ``until`` restrict to the half-open
        ``[since, until)`` epoch-seconds interval). With no filters and no
        window, returns the full ring size -- byte-equal to
        :meth:`summary`'s ``in_window`` on a quiet store, and always the
        ceiling ``recent(limit, **filters)`` could return at ``limit >=
        RECENT_MAX_LIMIT``.

        Purpose: a paywall dashboard tile rendering "showing N of M matches"
        needs the pre-limit total. Splitting this off from :meth:`recent`
        keeps :meth:`recent`'s return type stable (``list[dict]``) and
        lets a caller ask "how many matched?" without paying the
        ``dict(e)`` copy cost on every ring entry.

        Never raises.
        """
        try:
            filters = _normalise_filters(
                event=event, feature=feature, harness=harness,
                source=source, plan_chosen=plan_chosen,
            )
            since_ts, until_ts = _normalise_time_bounds(since, until)
            with self._lock:
                snap = list(self._ring)
            has_window = since_ts is not None or until_ts is not None
            if not filters and not has_window:
                return len(snap)
            count = 0
            for e in snap:
                if filters and not _row_matches_filters(e, filters):
                    continue
                if has_window and not _row_matches_time_window(
                    e, since_ts, until_ts,
                ):
                    continue
                count += 1
            return count
        except Exception as exc:
            logger.warning("paywall.events: count_matching swallowed: %s", exc)
            return 0

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


def summary(
    *,
    event: str | None = None,
    feature: str | None = None,
    harness: str | None = None,
    source: str | None = None,
    plan_chosen: str | None = None,
    since: Any = None,
    until: Any = None,
) -> dict:
    """Public shim for ``GET /api/paywall/events/summary``.

    Filter kwargs are optional; a ``None`` or empty-string value means
    "not supplied" and does not restrict on that dimension. Time bounds
    (``since`` / ``until``) restrict to the half-open ``[since, until)``
    epoch-seconds interval and may be supplied as ``float`` / ``int`` /
    numeric-string; bad or blank values collapse to "not supplied". See
    :meth:`_PaywallEventStore.summary` for the exact response shape
    (always includes ``filters``, ``matched``, and ``time_window``).
    """
    return _STORE.summary(
        event=event, feature=feature, harness=harness,
        source=source, plan_chosen=plan_chosen,
        since=since, until=until,
    )


def recent(
    limit: int | None = None,
    *,
    event: str | None = None,
    feature: str | None = None,
    harness: str | None = None,
    source: str | None = None,
    plan_chosen: str | None = None,
    since: Any = None,
    until: Any = None,
) -> list[dict]:
    """Public shim for ``GET /api/paywall/events/recent``.

    ``limit`` defaults to :data:`RECENT_DEFAULT_LIMIT`. Filter kwargs are
    optional; a ``None`` or empty-string value means "not supplied" and
    does not restrict on that dimension. ``since`` / ``until`` restrict
    to the half-open ``[since, until)`` epoch-seconds interval. See
    :meth:`_PaywallEventStore.recent` for the exact filter contract.
    """
    if limit is None:
        limit = _RECENT_DEFAULT
    return _STORE.recent(
        limit,
        event=event, feature=feature, harness=harness,
        source=source, plan_chosen=plan_chosen,
        since=since, until=until,
    )


def count_matching(
    *,
    event: str | None = None,
    feature: str | None = None,
    harness: str | None = None,
    source: str | None = None,
    plan_chosen: str | None = None,
    since: Any = None,
    until: Any = None,
) -> int:
    """Public shim for :meth:`_PaywallEventStore.count_matching`.

    Returns the count of ring rows matching the supplied filters +
    time-window BEFORE any ``limit`` clamp. Used by
    ``/api/paywall/events/recent`` so it can render "showing N of M
    matches" alongside the filtered event list.
    """
    return _STORE.count_matching(
        event=event, feature=feature, harness=harness,
        source=source, plan_chosen=plan_chosen,
        since=since, until=until,
    )


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
