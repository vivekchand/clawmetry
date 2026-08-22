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

Note the separate, still-open issue this module does NOT fix: DuckDB buckets
a day as ``substr(ts, 1, 10)`` over a source-supplied timestamp string, so
the bucket boundary follows whatever timezone each runtime wrote. Aligning
the buckets to these windows is tracked separately.
"""
from datetime import datetime, timedelta


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
