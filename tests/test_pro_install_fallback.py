"""Guards the clawmetry-pro install fallback for read-only site-packages.

Burned 2026-06-05: a system-wide install at /opt/clawmetry owned by root, run
by a non-root --user systemd daemon, could not write the Pro wheel into the
interpreter site-packages ("[Errno 13] Permission denied") so the paid runtime
adapters (Claude Code/Codex/...) silently never loaded. The provisioner now
falls back to a HOME-owned dir and puts it on sys.path.

Invariants:
  1. When site-packages is NOT writable, the wheel extracts into
     _PRO_FALLBACK_DIR (not the read-only interpreter dir) and that dir is put
     on sys.path so the adapters import.
  2. _pip_install_wheel short-circuits to the fallback when site-packages is
     read-only (pip would fail there too).
  3. When site-packages IS writable, the normal path is used (no fallback).
"""
import os
import sys
import zipfile

import pytest

from clawmetry import license as lic


def _make_fake_wheel(path):
    """A minimal pure-Python wheel: a package + dist-info so importlib.metadata
    can see it."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("clawmetry_pro/__init__.py", "VERSION = '9.9.9'\n")
        zf.writestr("clawmetry_pro-9.9.9.dist-info/METADATA",
                    "Metadata-Version: 2.1\nName: clawmetry-pro\nVersion: 9.9.9\n")
        zf.writestr("clawmetry_pro-9.9.9.dist-info/RECORD", "")


def test_unzip_falls_back_when_site_packages_readonly(tmp_path, monkeypatch):
    fallback = tmp_path / "pro-packages"
    monkeypatch.setattr(lic, "_PRO_FALLBACK_DIR", str(fallback))
    # Pretend the interpreter site-packages is read-only.
    monkeypatch.setattr(lic, "_site_packages_target",
                        lambda: ("/read/only/site-packages", False))
    wheel = tmp_path / "clawmetry_pro-9.9.9.whl"
    _make_fake_wheel(str(wheel))

    ok, detail = lic._unzip_wheel_into_site(str(wheel))

    assert ok, detail
    # Extracted into the fallback, NOT the read-only site-packages.
    assert (fallback / "clawmetry_pro" / "__init__.py").exists()
    assert (fallback / "clawmetry_pro-9.9.9.dist-info").exists()
    assert str(fallback) in sys.path
    assert "fallback" in detail


def test_pip_install_short_circuits_to_fallback_when_readonly(tmp_path, monkeypatch):
    fallback = tmp_path / "pro-packages"
    monkeypatch.setattr(lic, "_PRO_FALLBACK_DIR", str(fallback))
    monkeypatch.setattr(lic, "_site_packages_target",
                        lambda: ("/read/only", False))

    # If pip were invoked it would explode; assert it is NOT called.
    def _boom(*a, **k):
        raise AssertionError("pip must not run when site-packages is read-only")
    monkeypatch.setattr(lic, "_pip_run", _boom)

    wheel = tmp_path / "w.whl"
    _make_fake_wheel(str(wheel))
    ok, detail = lic._pip_install_wheel(str(wheel))
    assert ok, detail
    assert (fallback / "clawmetry_pro" / "__init__.py").exists()


def test_writable_site_packages_uses_normal_path(tmp_path, monkeypatch):
    site = tmp_path / "site-packages"
    site.mkdir()
    monkeypatch.setattr(lic, "_site_packages_target", lambda: (str(site), True))
    wheel = tmp_path / "w.whl"
    _make_fake_wheel(str(wheel))
    ok, detail = lic._unzip_wheel_into_site(str(wheel))
    assert ok, detail
    # Extracted into the (writable) interpreter site-packages, not the fallback.
    assert (site / "clawmetry_pro" / "__init__.py").exists()
    assert "fallback" not in detail


def test_ensure_pro_on_path_idempotent(tmp_path, monkeypatch):
    d = tmp_path / "pro-packages"
    d.mkdir()
    monkeypatch.setattr(lic, "_PRO_FALLBACK_DIR", str(d))
    before = list(sys.path)
    lic.ensure_pro_on_path()
    lic.ensure_pro_on_path()
    assert sys.path.count(str(d)) == 1
    # cleanup
    while str(d) in sys.path:
        sys.path.remove(str(d))
    monkeypatch.setattr(sys, "path", before, raising=False)
