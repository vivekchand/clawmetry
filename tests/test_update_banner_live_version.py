"""The update banner must reflect the LIVE installed version, never the
version recorded at the last PyPI check.

Regression: after upgrading 0.12.306 → 0.12.309, the banner still showed
"Update available: v0.12.308 is out. You are on v0.12.306." for ~60s (until
the delayed on-startup recheck ran), because `_get_latest_update_check`
returned the recorded `current_version` from the DB. Fix overlays the live
version and recomputes availability against it.
"""
from __future__ import annotations

import contextlib
import importlib


def _uc():
    import routes.update_check as uc
    return importlib.reload(uc)


def test_version_gt_numeric_tuple():
    uc = _uc()
    assert uc._version_gt("0.12.309", "0.12.308") is True
    assert uc._version_gt("0.12.309", "0.12.309") is False
    assert uc._version_gt("0.12.308", "0.12.309") is False
    # numeric, not lexicographic: 310 > 9
    assert uc._version_gt("0.12.310", "0.12.9") is True
    assert uc._version_gt("", "0.1") is False


class _FakeRow(dict):
    pass


def _patch_db(monkeypatch, uc, row):
    class _FakeDB:
        def execute(self, *a, **k):
            class _C:
                def fetchone(_self):
                    return row
            return _C()
        def close(self):
            pass
    monkeypatch.setattr(uc, "_get_fleet_db", lambda: _FakeDB())
    monkeypatch.setattr(uc, "_get_fleet_db_lock", lambda: contextlib.nullcontext())


def test_latest_check_overlays_live_version(monkeypatch):
    """DB recorded current=.306/latest=.308, but we're actually on .309 now."""
    uc = _uc()
    monkeypatch.setattr(uc, "_live_current_version", lambda: "0.12.309")
    _patch_db(monkeypatch, uc, _FakeRow(
        current_version="0.12.306", latest_version="0.12.308",
        update_available=1, changelog_url="", check_at=123,
    ))
    res = uc._get_latest_update_check()
    assert res["current"] == "0.12.309"          # live, not the stale .306
    assert res["update_available"] is False        # .308 is NOT > .309
    # → banner stays hidden
    assert uc._should_show_update_banner({"enabled": True}, res) is False


def test_latest_check_still_flags_real_update(monkeypatch):
    """A genuinely newer latest still shows the banner, with live current."""
    uc = _uc()
    monkeypatch.setattr(uc, "_live_current_version", lambda: "0.12.309")
    _patch_db(monkeypatch, uc, _FakeRow(
        current_version="0.12.309", latest_version="0.12.312",
        update_available=1, changelog_url="", check_at=123,
    ))
    res = uc._get_latest_update_check()
    assert res["current"] == "0.12.309"
    assert res["latest"] == "0.12.312"
    assert res["update_available"] is True
    assert uc._should_show_update_banner({"enabled": True}, res) is True
