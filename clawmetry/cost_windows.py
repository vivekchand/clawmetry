"""One definition of "today", "this week" and "this month" for every cost surface.

Before this module ClawMetry computed the same three windows four different
ways, and a customer comparing the hosted dashboard, localhost and the desk
device on 2026-08-22 got three different answers that were all "correct":

    surface                          today        week              month
    sync.py _build_daily_usage       local day    calendar (Mon)    calendar (1st)
    dashboard _get_cost_summary      UTC+1 day    rolling 7d        rolling 30d
    dashboard _get_budget_status     local day    calendar (Mon)    calendar (1st)
    routes/infra cost-optimization   UTC day      rolling 7d        rolling 30d

On a Saturday a rolling 7 days spans 8 calendar days while a calendar week
spans 6, so the same spend legitimately renders as two different weekly
totals. That is not a rounding difference the user can be expected to
absorb; it reads as the product being broken.

The convention here is CALENDAR windows in the node's LOCAL timezone:

  * today  - the local calendar day
  * week   - the local calendar week, starting Monday
  * month  - the local calendar month, from the 1st

Rationale: cost is a billing-shaped number, and "this month" means the month
you will be billed for, not a rolling 30 days. Local, because the daemon runs
on the user's machine and "today" is the user's today. The old
``CET = timezone(timedelta(hours=1))`` was a fixed offset with no DST, so it
was wrong for Europe half the year and wrong for everyone else all year.

The day BUCKETS those windows filter are aligned to the same clock, by
``local_day()`` below and its SQL twin. They were not, once: a day was
``substr(ts, 1, 10)`` over whatever timestamp string the runtime wrote, so a
runtime writing UTC put a user in California's 5pm spend on tomorrow. The
window said "today, local" and the buckets said "today, wherever that runtime
thinks it is" — the same disagreement this module was written to end, one
layer down.
"""
from datetime import date as _date, datetime, timedelta


def now_local():
    """Timezone-aware 'now' in the node's local timezone, DST included."""
    return datetime.now().astimezone()


def window_start_days(now=None):
    """(today, week, month) window starts as ``YYYY-MM-DD`` strings.

    Suitable for comparing against DuckDB's day-bucketed rollup rows, which
    are ``YYYY-MM-DD`` strings. Inclusive lower bounds: a row belongs to the
    window when ``row_day >= start``.
    """
    n = now or now_local()
    return (
        n.strftime("%Y-%m-%d"),
        (n - timedelta(days=n.weekday())).strftime("%Y-%m-%d"),
        n.strftime("%Y-%m-01"),
    )


def window_start_epochs(now=None):
    """(today, week, month) window starts as POSIX timestamps.

    Suitable for filtering entries that carry an epoch timestamp, such as the
    in-process OTLP cost ring.
    """
    n = now or now_local()
    midnight = n.replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        midnight.timestamp(),
        (midnight - timedelta(days=n.weekday())).timestamp(),
        midnight.replace(day=1).timestamp(),
    )


def days_elapsed_in_month(now=None):
    """Whole days of the current calendar month so far, at least 1.

    Used to project a monthly cost from month-to-date spend without dividing
    by a rolling-30 constant that does not match the window being summed.
    """
    n = now or now_local()
    return max(1, n.day)


# ── day buckets ──────────────────────────────────────────────────────────
#
# A window is only as honest as the buckets it filters. ``window_start_days``
# returns node-local calendar days, so a row's day key has to be a node-local
# calendar day too, or the comparison silently mixes two clocks.
#
# The rule, matching DuckDB's TIMESTAMPTZ semantics exactly so the Python and
# SQL paths cannot disagree:
#
#   carries an offset ("...Z", "...+02:00")  -> convert to node-local, take the date
#   naive ("2026-08-24 23:30:00")            -> already local, take the date
#   unparseable                              -> fall back to the leading 10
#                                               characters if they are a date,
#                                               else no bucket
#
# The fallback matters: a bucket key we cannot derive must not become today,
# or unparsed rows would pile onto whatever day the code happened to run.


def _normalize_ts(text):
    """Make a timestamp string parseable by ``datetime.fromisoformat``.

    Handles the two shapes ``fromisoformat`` rejects on the Python versions we
    support: a trailing ``Z``, and sub-second precision finer than microseconds
    (some runtimes write nanoseconds). Both are common enough that treating
    them as unparseable would push real rows onto the string-prefix fallback,
    which is the behaviour this is replacing.
    """
    s = text.strip()
    if s.endswith("Z") or s.endswith("z"):
        s = s[:-1] + "+00:00"
    # Trim fractional seconds to 6 digits: 2026-08-24T23:30:00.123456789+00:00
    dot = s.find(".")
    if dot != -1:
        end = dot + 1
        while end < len(s) and s[end].isdigit():
            end += 1
        if end - (dot + 1) > 6:
            s = s[: dot + 7] + s[end:]
    return s


def local_day(ts):
    """Node-local calendar day (``YYYY-MM-DD``) for a source timestamp, or
    ``None`` when no day can be derived.

    The Python half of the day bucket. ``day_expr_sql`` is the SQL half; they
    must agree, and ``tests/test_day_bucket_local.py`` asserts they do on the
    same inputs.
    """
    s = str(ts or "").strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(_normalize_ts(s))
    except (TypeError, ValueError):
        prefix = s[:10]
        try:
            _date.fromisoformat(prefix)
        except ValueError:
            return None
        return prefix
    if dt.tzinfo is None:
        # Naive: the runtime wrote its own wall clock, which is this node's.
        return dt.strftime("%Y-%m-%d")
    return dt.astimezone().strftime("%Y-%m-%d")


def day_expr_sql(col: str = "ts") -> str:
    """SQL for the same bucket, for DuckDB.

    ``TRY_CAST`` so one malformed row cannot fail the whole aggregate, and a
    ``COALESCE`` onto the old string prefix so a row DuckDB will not parse
    still lands in the bucket it used to. Cast through ``DATE`` to ``VARCHAR``
    rather than returning a TIMESTAMPTZ: handing one back to Python requires a
    timezone library that is not a dependency here.

    The one place this and :func:`local_day` deliberately differ is a
    timestamp with NO derivable day. Here it keeps its old junk bucket; there
    it returns ``None`` and the row is skipped, because the rollup tables key
    on a real ``DATE`` column and cannot store a junk value. That split
    predates this change and is unchanged by it.
    """
    return (
        f"COALESCE(CAST(CAST(TRY_CAST({col} AS TIMESTAMPTZ) AS DATE) AS VARCHAR),"
        f" substr({col}, 1, 10))"
    )
