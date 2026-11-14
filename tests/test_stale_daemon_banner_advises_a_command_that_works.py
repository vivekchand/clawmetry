"""The stalled-collector banner must not advise `launchctl kickstart -k`.

`kickstart -k` restarts the job definition launchd already holds in memory.
It never re-reads the plist, so it cannot repair the most common reason the
collector goes quiet on macOS: a LaunchAgent pinned to an interpreter that
can no longer import `clawmetry`. On the node this was found on (2026-10-14)
that advice produced 12 consecutive failed launches and never could have
produced anything else.

`clawmetry sync --restart` re-registers the job (bootout -> bootstrap, see
tests/test_launchd_repin_requires_bootout.py), which is the action that
actually re-pins it, and it works on every OS rather than macOS alone.
"""
from __future__ import annotations

import pathlib

import pytest

APP_JS = pathlib.Path(__file__).resolve().parents[1].joinpath(
    "clawmetry", "static", "js", "app.js")


def _banner_line() -> str:
    for line in APP_JS.read_text().splitlines():
        if "background helper may have stopped" in line:
            return line
    raise AssertionError("stalled-collector banner copy not found in app.js")


def test_banner_does_not_advise_kickstart():
    assert "kickstart" not in _banner_line()


def test_banner_advises_the_command_that_re_pins():
    assert "clawmetry sync --restart" in _banner_line()


def test_banner_points_at_the_diagnostic_command():
    """`clawmetry status` is what correctly reported the dead daemon."""
    assert "clawmetry status" in _banner_line()


def test_banner_is_not_macos_only():
    """The old copy said "On macOS:" and offered nothing to anyone else."""
    assert "On macOS" not in _banner_line()


def test_no_kickstart_advice_anywhere_in_the_served_ui():
    """Any other surface repeating it would recreate the same dead end."""
    offenders = [
        i + 1
        for i, line in enumerate(APP_JS.read_text().splitlines())
        if "kickstart" in line
    ]
    assert not offenders, f"app.js still advises kickstart at lines {offenders}"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
