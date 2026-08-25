"""Guard for the launchd ``cwd="/"`` bug that kept the dashboard down.

Found 2026-08-24 on a founder machine: ``com.clawmetry.dashboard`` had been
exiting 1 on every boot with

    [clawmetry] ERROR: Could not initialise fleet database at
    '/.clawmetry-fleet.db' -- unable to open database file

launchd starts agents with ``cwd="/"``. ``dashboard.py``'s workspace
auto-detect ends in ``WORKSPACE = os.getcwd()``, so on any machine with no
detectable OpenClaw workspace WORKSPACE became ``"/"``. ``_fleet_db_path``
then returned ``os.path.join("/", ".clawmetry-fleet.db")`` -- unwritable on
macOS -- and the process died before it ever served a request.

Two independent guards, because either one alone would have prevented the
outage: "/" is not a workspace, and a workspace we cannot write to must never
win over the ~/.clawmetry path the function documents as authoritative.
"""

from __future__ import annotations

import os

import pytest

dashboard = pytest.importorskip("dashboard")


@pytest.fixture(autouse=True)
def _restore_globals(monkeypatch):
    monkeypatch.setattr(dashboard, "FLEET_DB_PATH", None, raising=False)
    yield


def test_unwritable_workspace_does_not_win(monkeypatch):
    """The launchd failure mode, exactly: WORKSPACE="/"."""
    monkeypatch.setattr(dashboard, "WORKSPACE", "/", raising=False)
    path = dashboard._fleet_db_path()
    assert path != "/.clawmetry-fleet.db"
    # It must fall through to a location we can actually create.
    parent = os.path.dirname(path)
    assert os.access(parent, os.W_OK), f"fell through to unwritable {path!r}"


def test_writable_workspace_is_still_honoured(tmp_path, monkeypatch):
    """Dev mode must keep working -- the fix is narrow, not a behaviour change."""
    monkeypatch.setattr(dashboard, "WORKSPACE", str(tmp_path), raising=False)
    assert dashboard._fleet_db_path() == str(tmp_path / ".clawmetry-fleet.db")


def test_explicit_fleet_db_path_still_overrides(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard, "WORKSPACE", "/", raising=False)
    monkeypatch.setattr(
        dashboard, "FLEET_DB_PATH", str(tmp_path / "custom.db"), raising=False
    )
    assert dashboard._fleet_db_path() == str(tmp_path / "custom.db")


def test_root_is_never_accepted_as_a_workspace_fallback():
    """The generated launchd plist must pin a real cwd/HOME.

    Belt and braces with the code guard above: the plist template is what
    stops the process from ever seeing cwd="/" in the first place.
    """
    import inspect

    from clawmetry import cli

    src = inspect.getsource(cli)
    assert "<key>WorkingDirectory</key>" in src, (
        "dashboard plist must pin WorkingDirectory or launchd gives it cwd=/"
    )
