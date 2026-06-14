"""Auto-update must target the newest AGED-IN release, not the absolute latest.

Burned 2026-06-13: a dense release run left every published version younger
than the 48h stability window, so the old rail (gate the install on the
absolute latest's age) found no installable target and left daemons stuck on
an ancient build indefinitely. The fix selects the newest version above the
current build that has aged past the window, so the fleet keeps moving forward.
"""
from datetime import datetime, timezone, timedelta

from routes.update_check import _newest_aged_in_version


def _iso(hours_ago):
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat().replace("+00:00", "Z")


def _releases(spec):
    """spec: {version: hours_ago}. None hours_ago => no upload time."""
    out = {}
    for ver, ago in spec.items():
        out[ver] = [] if ago is None else [{"upload_time_iso_8601": _iso(ago)}]
    return out


def test_picks_newest_aged_in_not_absolute_latest():
    # current 0.12.504. 509 (72h) and 510 (50h) have aged in; 517/518 are fresh.
    rel = _releases({
        "0.12.504": 200, "0.12.509": 72, "0.12.510": 50,
        "0.12.517": 20, "0.12.518": 3,
    })
    # Absolute latest is 0.12.518 (3h) but it is too fresh; install 0.12.510.
    assert _newest_aged_in_version(rel, "0.12.504", 48) == "0.12.510"


def test_none_when_everything_too_fresh():
    # The real 2026-06-13 shape: every version above current is < 48h old.
    rel = _releases({
        "0.12.504": 200, "0.12.509": 44, "0.12.514": 21, "0.12.518": 3,
    })
    assert _newest_aged_in_version(rel, "0.12.504", 48) is None


def test_ignores_versions_at_or_below_current():
    rel = _releases({"0.12.504": 200, "0.12.503": 300, "0.12.510": 60})
    assert _newest_aged_in_version(rel, "0.12.504", 48) == "0.12.510"


def test_skips_versions_without_upload_time():
    rel = _releases({"0.12.504": 200, "0.12.510": None, "0.12.509": 60})
    # 510 has no timestamp so it cannot be confirmed aged-in; fall back to 509.
    assert _newest_aged_in_version(rel, "0.12.504", 48) == "0.12.509"


def test_lower_window_makes_more_installable():
    rel = _releases({"0.12.504": 200, "0.12.514": 21, "0.12.518": 3})
    assert _newest_aged_in_version(rel, "0.12.504", 48) is None
    # A 12h window lets the 21h-old 0.12.514 in (3h-old 518 still too fresh).
    assert _newest_aged_in_version(rel, "0.12.504", 12) == "0.12.514"
