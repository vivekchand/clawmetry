"""Self-hosted nodes must keep clawmetry-pro current.

Found while moving approval delivery into clawmetry-pro: the wheel install
for a SIGNED-LICENSE node happened exactly once, inside
``activate_license``. Cloud-key nodes track releases through the ~30-min
pro-entitlement watcher; self-hosted ones were frozen on whatever wheel was
current on their activation day.

That is invisible until a paid capability MOVES from the OSS package into
the paid one. Then OSS drops the code, the frozen wheel does not have it,
and the feature disappears on exactly those nodes — with no automatic
recovery and nothing telling the operator to re-activate.

``refresh_pro_from_license`` closes it. These tests pin the four properties
that make it safe to run on a schedule.
"""
from __future__ import annotations

import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def lic(tmp_path, monkeypatch):
    import clawmetry.license as L
    monkeypatch.setattr(L, "LICENSE_PATH", str(tmp_path / "license.key"))
    monkeypatch.setattr(L, "_offline_mode", lambda: False)
    return L


def _write_license(lic, text="signed-token"):
    with open(lic.LICENSE_PATH, "w") as f:
        f.write(text)


def test_no_license_is_not_this_path(lic, monkeypatch):
    """A cloud-key or unlicensed node must not be touched by the
    self-hosted refresh."""
    monkeypatch.setattr(lic, "load_license", lambda path=None: None)
    called = []
    monkeypatch.setattr(lic, "_download_and_install_pro",
                        lambda p: called.append(p) or "")
    assert lic.refresh_pro_from_license() == (False, "")
    assert not called


def test_offline_never_phones_home(lic, monkeypatch):
    """CLAWMETRY_OFFLINE is an air-gap promise; a scheduled refresh must
    not quietly break it."""
    _write_license(lic)
    monkeypatch.setattr(lic, "load_license", lambda path=None: object())
    monkeypatch.setattr(lic, "_offline_mode", lambda: True)
    called = []
    monkeypatch.setattr(lic, "_download_and_install_pro",
                        lambda p: called.append(p) or "")
    ok, msg = lic.refresh_pro_from_license()
    assert ok is False
    assert "offline" in msg
    assert not called


def test_skips_when_pro_is_not_installed_at_all(lic, monkeypatch):
    """First install belongs to activation. Racing it here could fight the
    install that is already running."""
    _write_license(lic)
    monkeypatch.setattr(lic, "load_license", lambda path=None: object())
    monkeypatch.setattr(lic, "_pro_installed_version", lambda: None)
    called = []
    monkeypatch.setattr(lic, "_download_and_install_pro",
                        lambda p: called.append(p) or "")
    assert lic.refresh_pro_from_license() == (False, "")
    assert not called


def test_reports_an_upgrade(lic, monkeypatch):
    _write_license(lic)
    monkeypatch.setattr(lic, "load_license", lambda path=None: object())
    monkeypatch.setattr(lic, "verify_token", lambda t: {"tier": "pro"})
    versions = iter(["0.7.4", "0.7.7"])
    monkeypatch.setattr(lic, "_pro_installed_version",
                        lambda: next(versions))
    monkeypatch.setattr(lic, "_download_and_install_pro",
                        lambda p: "installed clawmetry-pro 0.7.7")
    ok, msg = lic.refresh_pro_from_license()
    assert ok is True
    assert "0.7.7" in msg


def test_no_change_is_not_reported_as_an_upgrade(lic, monkeypatch):
    """The steady state — the served wheel already matches — must be quiet,
    or a 30-minute loop logs an upgrade forever."""
    _write_license(lic)
    monkeypatch.setattr(lic, "load_license", lambda path=None: object())
    monkeypatch.setattr(lic, "verify_token", lambda t: {"tier": "pro"})
    monkeypatch.setattr(lic, "_pro_installed_version", lambda: "0.7.7")
    monkeypatch.setattr(lic, "_download_and_install_pro",
                        lambda p: "clawmetry-pro 0.7.7 already installed")
    ok, _ = lic.refresh_pro_from_license()
    assert ok is False


def test_never_raises(lic, monkeypatch):
    """It runs inside a daemon watcher; an exception must not take the
    thread down."""
    _write_license(lic)
    monkeypatch.setattr(lic, "load_license", lambda path=None: object())
    monkeypatch.setattr(lic, "_pro_installed_version", lambda: "0.7.4")
    monkeypatch.setattr(lic, "_download_and_install_pro",
                        lambda p: (_ for _ in ()).throw(RuntimeError("net")))
    assert lic.refresh_pro_from_license() == (False, "")
