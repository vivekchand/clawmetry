"""What a finding costs, and therefore what to look at first.

Split out of :mod:`clawmetry.detectors` because "how do we price an incident"
is a product decision with its own rules, and burying it among the detectors
made those rules hard to find and easy to weaken.

The rule that matters: an estimate that was not measured may not escalate
anything. ``burn_rate`` prices a stretch we actually watched go wrong.
``window_fraction`` apportions a session's cost by the share of the window
after the first bad step, which assumes even spend, and on real sessions
attributed most of a $100 session to "Bash failed 4 times". So the second one
is context and never raises severity. With neither, the figure is 0.0 and the
basis says ``unknown``: a fabricated dollar figure would make the list worse
than sorting by severity, which is the thing it replaces.
"""
from __future__ import annotations

import os


# Higher is louder. ``critical`` exists because "an agent disabled a system
# protection" and "an agent continued after a failed grep" both landing on
# `warning` made the top of the list meaningless.
_SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}


# Spend at risk (USD) at which a warning is promoted to critical.
CRITICAL_SPEND_USD = float(os.environ.get("CLAWMETRY_GUARD_CRITICAL_USD", "5"))

# ── Severity that maps to money ──────────────────────────────────────────────
# An incident list sorted by severity puts a $0.02 info above a $170 warning.
# The number that decides what to look at first is what ignoring it costs, so
# every incident carries an ESTIMATE of the spend behind the flagged stretch.
#
# It is an estimate and the field says so. Two bases, in order of preference:
#
#   burn_rate      cost / session-minutes * minutes-flagged. Used when the
#                  caller knows how long the session has been bad. This is the
#                  honest one: it prices the stretch, not the session.
#   window_fraction cost * (steps after the first bad step / steps in window).
#                  Used with no clock. Assumes even spend across the window,
#                  which is wrong in detail and right in order of magnitude.
#
# With neither, spend_at_risk is 0.0 and ``basis`` is "unknown" — never a
# fabricated number, because a fabricated dollar figure is the one thing that
# would make this list worse than sorting by severity.

def _severity_promote(severity: str, spend_at_risk: float, basis: str) -> str:
    """Money can raise a warning to critical, under two restrictions.

    It never promotes an ``info``: a low-precision signal stays low-precision
    no matter how expensive the session is.

    And it only promotes on a MEASURED figure. ``window_fraction`` assumes
    spend is spread evenly across the window, which on real sessions attributes
    most of a $100 session to "Bash failed 4 times" and turned eleven of twelve
    real incidents critical. An estimate that rough is useful as context and
    has no business escalating anything, so only ``burn_rate`` (a real clock
    over a stretch we actually watched go wrong) can.
    """
    if (severity == "warning" and basis == "burn_rate"
            and spend_at_risk >= CRITICAL_SPEND_USD):
        return "critical"
    return severity


def annotate_spend(incidents: list, *, cost_usd: float = 0.0,
                   bad_for_seconds: float = 0.0,
                   session_seconds: float = 0.0,
                   window_steps: int = 0) -> list:
    """Attach ``spend_at_risk_usd`` / ``burn_rate_usd_per_min`` / ``basis`` to
    each incident, promote severity on cost, and return the list sorted by what
    it costs to ignore. Never raises; a bad number degrades to 0.0."""
    try:
        cost = max(0.0, float(cost_usd or 0))
    except (TypeError, ValueError):
        cost = 0.0
    try:
        bad_s = max(0.0, float(bad_for_seconds or 0))
    except (TypeError, ValueError):
        bad_s = 0.0
    try:
        sess_s = max(0.0, float(session_seconds or 0))
    except (TypeError, ValueError):
        sess_s = 0.0

    burn = (cost / (sess_s / 60.0)) if (cost > 0 and sess_s >= 60) else 0.0
    for inc in incidents or []:
        if not isinstance(inc, dict):
            continue
        risk, basis = 0.0, "unknown"
        if burn > 0 and bad_s > 0:
            risk = min(cost, burn * (bad_s / 60.0))
            basis = "burn_rate"
        elif cost > 0 and window_steps > 0:
            fbs = inc.get("first_bad_step")
            if isinstance(fbs, int) and 0 <= fbs < window_steps:
                risk = cost * ((window_steps - fbs) / float(window_steps))
                basis = "window_fraction"
        inc["spend_at_risk_usd"] = round(risk, 4)
        inc["spend_basis"] = basis
        inc["burn_rate_usd_per_min"] = round(burn, 4)
        inc["session_cost_usd"] = round(cost, 4)
        inc["severity"] = _severity_promote(
            str(inc.get("severity") or "warning"), risk, basis)
    return sort_incidents(incidents or [])


def incident_rank(incident: dict) -> tuple:
    """Sort key: money first, then severity, then how much of it there is.

    Ties are everywhere in practice (a free-tier local model session costs
    nothing), so severity remains the second key and the old warning-before-
    info ordering still holds when no cost is known.
    """
    if not isinstance(incident, dict):
        return (0.0, 0, 0, "")
    try:
        spend = float(incident.get("spend_at_risk_usd") or 0)
    except (TypeError, ValueError):
        spend = 0.0
    sev = _SEVERITY_RANK.get(str(incident.get("severity") or ""), 0)
    ev = incident.get("evidence") if isinstance(incident.get("evidence"), dict) else {}
    try:
        size = int(ev.get("repeats") or ev.get("tool_calls") or ev.get("failures")
                   or ev.get("distinct_files") or ev.get("accesses") or 0)
    except (TypeError, ValueError):
        size = 0
    return (spend, sev, size, str(incident.get("kind") or ""))


def sort_incidents(incidents: list) -> list:
    """Most expensive to ignore first."""
    try:
        return sorted([i for i in incidents if isinstance(i, dict)],
                      key=lambda i: incident_rank(i), reverse=True)
    except Exception:
        return list(incidents or [])
