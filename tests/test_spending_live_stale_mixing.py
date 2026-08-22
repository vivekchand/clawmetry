"""Guard: the snapshot's spending triple never mixes live and stale eras.

Regression reported 2026-08-22 by a paying customer: app.clawmetry.com showed
"$22.73 today, $7.25/week, $22.73/mo" and flipped to a different triple every
few seconds. Root cause was an `or` chain in ``sync_system_snapshot``:

    "today": float(_du.get("todayCost") or _state.get("today") or 0)

`or` treats a legitimate 0.0 as missing, so an idle window silently fell back
to the stale ``state.json`` value -- per key, independently, so a single
payload could carry a live `week` beside a stale `today`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry.sync import _resolve_spending


def test_real_zero_is_not_treated_as_missing():
    """A live $0.00 stays $0.00 -- it must NOT fall back to stale state."""
    live = {"todayCost": 0.0, "weekCost": 0.0, "monthCost": 0.0}
    stale = {"today": 22.73, "week": 7.25, "month": 22.73}
    out = _resolve_spending(live, stale)
    assert out["today"] == 0.0, "a real $0 today was overwritten by stale state"
    assert out["week"] == 0.0
    assert out["month"] == 0.0
    assert out["source"] == "live"


def test_partial_zero_does_not_mix_eras():
    """The exact customer shape: idle today, real spend this week.

    Pre-fix, `today` fell back to stale ($22.73) while `week` stayed live
    ($7.25) -- three numbers from two different eras in one payload.
    """
    live = {"todayCost": 0.0, "weekCost": 7.25, "monthCost": 24.11}
    stale = {"today": 22.73, "week": 999.0, "month": 22.73}
    out = _resolve_spending(live, stale)
    assert out == {"today": 0.0, "week": 7.25, "month": 24.11, "source": "live"}


def test_failed_read_falls_back_wholesale_and_is_labelled():
    """_build_daily_usage() returns {} on failure -> use stale, and SAY so."""
    out = _resolve_spending({}, {"today": 1.5, "week": 2.5, "month": 3.5})
    assert out == {"today": 1.5, "week": 2.5, "month": 3.5, "source": "state"}


def test_partial_live_payload_is_not_half_trusted():
    """A live dict missing a key is a degraded read, not a licence to mix."""
    out = _resolve_spending(
        {"todayCost": 5.0, "weekCost": None, "monthCost": 9.0},
        {"today": 1.0, "week": 2.0, "month": 3.0},
    )
    assert out["source"] == "state"
    assert out["today"] == 1.0


def test_both_sources_empty_is_zero_not_a_crash():
    out = _resolve_spending({}, {})
    assert out == {"today": 0.0, "week": 0.0, "month": 0.0, "source": "state"}


def test_never_crashes_on_none():
    out = _resolve_spending(None, None)
    assert out["today"] == 0.0 and out["source"] == "state"
