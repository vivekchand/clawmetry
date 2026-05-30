"""Lock-in test for issue #2290 — free trial copy must consistently say
7 days, never 14.

The cloud trial dropped from 14 → 7 days as part of the canonical pricing
matrix in #2288. This test prevents an accidental regression — e.g. a
copy-paste from old marketing material — that reintroduces "14-day" trial
copy in any user-facing surface.

We scan raw source strings (no Flask boot required) because trial copy
is embedded across dashboard.py, the templates/ directory, and the PRD.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# User-facing files that mention the trial. Tests/, CHANGELOG, internal
# docs are excluded — they may legitimately reference history.
USER_FACING_FILES = [
    "PRD.md",
    "dashboard.py",
    "clawmetry/sync.py",
    "clawmetry/templates/partials/paywall_modal.html",
    "clawmetry/templates/tabs/alerts.html",
    "clawmetry/templates/tabs/approvals.html",
    "clawmetry/templates/tabs/notifications.html",
]

# "14 day" / "14-day" near "trial" — the exact regression we're guarding.
# Allow "14-day chart" / "14 days of events" (token-usage window, unrelated).
_TRIAL_RX = re.compile(r"14[\s-]?day", re.IGNORECASE)
_TRIAL_CONTEXT_RX = re.compile(r"14[\s-]?day[^.\n]{0,80}trial", re.IGNORECASE)
_TRIAL_CONTEXT_RX_REV = re.compile(r"trial[^.\n]{0,80}14[\s-]?day", re.IGNORECASE)


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_no_14_day_trial_copy_in_user_facing_files():
    """No user-facing surface should pair "14 day" with "trial"."""
    offenders: list[str] = []
    for rel in USER_FACING_FILES:
        text = _read(rel)
        for rx in (_TRIAL_CONTEXT_RX, _TRIAL_CONTEXT_RX_REV):
            for match in rx.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                snippet = text[max(0, match.start() - 20): match.end() + 20]
                offenders.append(f"{rel}:{line_no} -> {snippet!r}")
    assert not offenders, (
        "Found '14-day' near 'trial' — trial must say 7 days (issue #2290):\n  "
        + "\n  ".join(offenders)
    )


def test_prd_canonical_matrix_says_7_days():
    """The PRD pricing matrix is the canonical source of truth."""
    prd = _read("PRD.md")
    # Match a line in the pricing matrix table that mentions Trial + 7 days.
    assert re.search(r"\|\s*\*\*Trial\*\*.*7\s*days", prd), (
        "PRD pricing matrix must list Trial as 7 days"
    )


def test_paywall_cta_says_7_day_trial():
    """The paywall modal CTA is the highest-traffic trial copy surface."""
    paywall = _read("clawmetry/templates/partials/paywall_modal.html")
    assert "7-day free trial" in paywall, (
        "paywall modal CTA must say '7-day free trial'"
    )


def test_dashboard_inline_trial_copy_says_7_day():
    """dashboard.py has two inline `7-day free trial` strings used by the
    Pro-gate error path. Pin both to the canonical phrase."""
    text = _read("dashboard.py")
    assert text.count("7-day free trial") >= 2, (
        "dashboard.py must mention '7-day free trial' in at least 2 places "
        "(Pro-gate error messages + cloud upgrade link)"
    )
