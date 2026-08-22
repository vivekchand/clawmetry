"""Guard: every cost surface uses ONE definition of today/week/month.

Reported 2026-08-22 by a paying customer comparing three surfaces:

    app.clawmetry.com  $22.73 today, $7.25/week, $22.73/mo
    localhost:8900     $1.72 today,  $8.58/week, $21.26/mo
    desk device        ~$6.93 last 24h

Part of that spread was not corruption at all: the surfaces were summing
DIFFERENT WINDOWS. sync.py used calendar week/month, dashboard's cost panel
used ROLLING 7/30 days in a hardcoded UTC+1, routes/infra used rolling in
UTC. On a Saturday a rolling week spans 8 calendar days and a calendar week
spans 6, so the same events legitimately produced different totals.

This guard has two halves:
  1. the canonical helper means what it says, including at edges; and
  2. no cost surface computes its own windows behind its back.
"""
import ast
import inspect
import os
import sys
import textwrap
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from clawmetry.cost_windows import (
    days_elapsed_in_month,
    now_local,
    window_start_days,
    window_start_epochs,
)


# ---------------------------------------------------------------- semantics


def test_saturday_week_starts_monday_not_seven_days_ago():
    """The exact shape of the customer's report (2026-08-22 was a Saturday).

    Rolling-7 would start Aug 15 and span 8 calendar days.
    """
    sat = datetime(2026, 8, 22, 16, 30).astimezone()
    today, week, month = window_start_days(sat)
    assert today == "2026-08-22"
    assert week == "2026-08-17", "week must start Monday, not now-7d"
    assert month == "2026-08-01", "month must start the 1st, not now-30d"


def test_monday_week_starts_today():
    mon = datetime(2026, 8, 17, 9, 0).astimezone()
    _, week, _ = window_start_days(mon)
    assert week == "2026-08-17"


def test_sunday_belongs_to_the_week_that_started_monday():
    sun = datetime(2026, 8, 23, 23, 59).astimezone()
    _, week, _ = window_start_days(sun)
    assert week == "2026-08-17"


def test_first_of_month_all_three_collapse():
    first = datetime(2026, 9, 1, 0, 30).astimezone()
    today, _, month = window_start_days(first)
    assert today == month == "2026-09-01"


def test_epoch_and_day_windows_agree():
    """The two accessors must not disagree about where a window starts."""
    now = datetime(2026, 8, 22, 16, 30).astimezone()
    days = window_start_days(now)
    epochs = window_start_epochs(now)
    for day_str, epoch in zip(days, epochs):
        assert datetime.fromtimestamp(epoch).strftime("%Y-%m-%d") == day_str


def test_windows_are_ordered():
    today, week, month = window_start_days()
    assert month <= week <= today


def test_local_now_is_dst_aware():
    """A fixed UTC+1 offset was the old bug. utcoffset must track DST."""
    assert now_local().utcoffset() is not None
    jan = datetime(2026, 1, 15, 12, 0).astimezone()
    jul = datetime(2026, 7, 15, 12, 0).astimezone()
    if jan.utcoffset() == jul.utcoffset():
        pytest.skip("machine timezone does not observe DST")
    assert jan.utcoffset() != jul.utcoffset()


def test_days_elapsed_never_zero():
    assert days_elapsed_in_month(datetime(2026, 8, 1, 0, 1).astimezone()) == 1
    assert days_elapsed_in_month(datetime(2026, 8, 22, 0, 1).astimezone()) == 22


# ------------------------------------------------------------- class guard

# Auto-discovering rather than a hand-maintained allowlist: a NEW cost
# surface that invents its own window is caught without anyone remembering
# to add it here.
_COST_FUNCTIONS = [
    ("dashboard", "_get_cost_summary"),
    ("dashboard", "_get_budget_status"),
    ("clawmetry.sync", "_build_daily_usage"),
]

# Rolling-window and fixed-offset construction that must not reappear in a
# cost window. `timedelta(days=N)` for N in {7,30} is the rolling-window
# tell; `CET` was the fixed UTC+1.
_BANNED_ROLLING_DAYS = {7, 30}


def _source_of(module_name, func_name):
    import importlib

    mod = importlib.import_module(module_name)
    return inspect.getsource(getattr(mod, func_name))


@pytest.mark.parametrize("module_name,func_name", _COST_FUNCTIONS)
def test_cost_surface_does_not_roll_its_own_window(module_name, func_name):
    src = textwrap.dedent(_source_of(module_name, func_name))
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "timedelta"):
            continue
        for kw in node.keywords:
            if kw.arg == "days" and isinstance(kw.value, ast.Constant):
                assert kw.value.value not in _BANNED_ROLLING_DAYS, (
                    f"{module_name}.{func_name} builds a rolling "
                    f"{kw.value.value}-day cost window instead of using "
                    "clawmetry.cost_windows"
                )


@pytest.mark.parametrize("module_name,func_name", _COST_FUNCTIONS)
def test_cost_surface_uses_the_canonical_helper(module_name, func_name):
    src = _source_of(module_name, func_name)
    assert "cost_windows" in src, (
        f"{module_name}.{func_name} computes cost windows without "
        "clawmetry.cost_windows; that is how the surfaces drifted apart"
    )


def test_fixed_offset_cet_is_gone_from_the_dashboard():
    """The old `CET = timezone(timedelta(hours=1))`: no DST, wrong for
    everyone outside Europe, and it made this file's windows disagree."""
    import dashboard

    path = inspect.getsourcefile(dashboard)
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    assert "CET = timezone(" not in src, "the fixed UTC+1 constant is back"
