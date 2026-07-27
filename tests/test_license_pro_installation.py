"""Tests for the ``pro_installed`` / ``pro_installed_version`` /
``pro_installation_info`` public helpers on ``clawmetry.license`` and their
paired ``/api/license/pro-installed`` + ``/api/license/pro-installation``
endpoints on ``routes.entitlement``.

These are the scalar / envelope views onto the ``clawmetry-pro`` install-state
axis -- an axis independent from the license *claim* (tier / exp / etc.). A
healthy Pro node needs both a signed Pro-tier license AND the wheel on-disk,
and splitting the two lets an operator diagnose "activated but wheel missing"
apart from "wheel installed but licence expired".

Both fronts must be never-crash: any underlying failure (broken
``importlib.metadata``, unreadable marker file, missing pubkey PEM) must
degrade to ``installed=False`` / empty marker rather than propagating an
exception up the paywall renderer.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Isolated license env: tmp marker path, controllable pro-version reader,
    Flask app with the entitlement blueprint mounted."""
    import clawmetry.license as _lic

    marker_path = str(tmp_path / "pro_installed.json")
    monkeypatch.setattr(_lic, "_PRO_MARKER_PATH", marker_path)

    # Default: paid wheel NOT installed. Individual tests flip this via the
    # ``state`` handle below to model "wheel present" without mutating the
    # real site-packages.
    state = {"version": None}
    monkeypatch.setattr(
        _lic, "_pro_installed_version", lambda: state["version"]
    )

    from routes.entitlement import bp_entitlement

    flask_app = Flask(__name__)
    flask_app.register_blueprint(bp_entitlement)
    flask_app.config["TESTING"] = True

    return SimpleNamespace(
        app=flask_app,
        lic=_lic,
        marker_path=marker_path,
        state=state,
    )


def _write_marker(env, payload):
    import json
    import os

    os.makedirs(os.path.dirname(env.marker_path), exist_ok=True)
    with open(env.marker_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


# -- module-level scalar: pro_installed_version --


def test_pro_installed_version_none_when_not_installed(env):
    assert env.lic.pro_installed_version() is None


def test_pro_installed_version_returns_string_when_installed(env):
    env.state["version"] = "0.3.4"
    assert env.lic.pro_installed_version() == "0.3.4"


def test_pro_installed_version_never_raises(env, monkeypatch):
    def boom():
        raise RuntimeError("simulated importlib.metadata failure")

    monkeypatch.setattr(env.lic, "_pro_installed_version", boom)
    # Must degrade to None rather than propagate the RuntimeError up into
    # a paywall renderer that just wanted a version string.
    assert env.lic.pro_installed_version() is None


# -- module-level scalar: pro_installed --


def test_pro_installed_false_when_not_installed(env):
    assert env.lic.pro_installed() is False


def test_pro_installed_true_when_installed(env):
    env.state["version"] = "0.3.4"
    assert env.lic.pro_installed() is True


def test_pro_installed_false_on_empty_version_string(env, monkeypatch):
    """A zero-length version string is not a healthy install -- treat it as
    "not installed" so a health tile bound to this gate doesn't render
    green for a broken metadata reader."""
    monkeypatch.setattr(env.lic, "_pro_installed_version", lambda: "")
    assert env.lic.pro_installed() is False


def test_pro_installed_never_raises(env, monkeypatch):
    def boom():
        raise RuntimeError("simulated importlib.metadata failure")

    monkeypatch.setattr(env.lic, "_pro_installed_version", boom)
    assert env.lic.pro_installed() is False


# -- module-level envelope: pro_installation_info --


_INFO_SHAPE = {"installed", "version", "marker"}


def test_pro_installation_info_no_wheel_no_marker(env):
    info = env.lic.pro_installation_info()
    assert set(info) == _INFO_SHAPE
    assert info["installed"] is False
    assert info["version"] is None
    assert info["marker"] == {}


def test_pro_installation_info_wheel_present_no_marker(env):
    """Wheel importable but marker never written -- normal on a pre-marker
    or manually-installed wheel. Both facts should surface side-by-side."""
    env.state["version"] = "0.3.4"
    info = env.lic.pro_installation_info()
    assert info["installed"] is True
    assert info["version"] == "0.3.4"
    assert info["marker"] == {}


def test_pro_installation_info_marker_present_no_wheel(env):
    """Marker present but wheel was pip-uninstalled -- exactly the
    disagreement that needs to be visible to an operator debugging a
    paywall glitch."""
    _write_marker(
        env,
        {
            "installed_at": 1_700_000_000,
            "version": "0.3.4",
            "source": "downloaded",
            "node_id": "node-abc",
        },
    )
    info = env.lic.pro_installation_info()
    assert info["installed"] is False
    assert info["version"] is None
    assert info["marker"] == {
        "installed_at": 1_700_000_000,
        "version": "0.3.4",
        "source": "downloaded",
        "node_id": "node-abc",
    }


def test_pro_installation_info_healthy_install(env):
    """Both wheel importable AND marker present -- the fully-healthy path."""
    env.state["version"] = "0.3.4"
    _write_marker(
        env,
        {
            "installed_at": 1_700_000_000,
            "version": "0.3.4",
            "source": "downloaded",
            "node_id": "node-abc",
        },
    )
    info = env.lic.pro_installation_info()
    assert info["installed"] is True
    assert info["version"] == "0.3.4"
    assert info["marker"]["source"] == "downloaded"


def test_pro_installation_info_never_raises_on_version_failure(env, monkeypatch):
    def boom():
        raise RuntimeError("simulated importlib.metadata failure")

    monkeypatch.setattr(env.lic, "_pro_installed_version", boom)
    info = env.lic.pro_installation_info()
    assert set(info) == _INFO_SHAPE
    assert info["installed"] is False
    assert info["version"] is None
    # Marker read is independent of the version read; empty here because
    # no marker was written in this test.
    assert info["marker"] == {}


def test_pro_installation_info_never_raises_on_marker_failure(env, monkeypatch):
    def boom():
        raise RuntimeError("simulated marker read failure")

    monkeypatch.setattr(env.lic, "_read_pro_marker", boom)
    env.state["version"] = "0.3.4"
    info = env.lic.pro_installation_info()
    # Version leg still succeeds; marker leg degrades to {}.
    assert info["installed"] is True
    assert info["version"] == "0.3.4"
    assert info["marker"] == {}


def test_pro_installation_info_marker_wrong_type(env, monkeypatch):
    """A corrupt marker file whose top-level JSON is a list, not an object,
    must not leak a wrong-shape marker up to the caller -- collapse to {}."""
    monkeypatch.setattr(env.lic, "_read_pro_marker", lambda: ["not", "a", "dict"])
    info = env.lic.pro_installation_info()
    assert info["marker"] == {}


# -- endpoint: /api/license/pro-installed --


_INSTALLED_SHAPE = {"installed", "version"}


def test_endpoint_pro_installed_no_wheel(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installed")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _INSTALLED_SHAPE
    assert data["installed"] is False
    assert data["version"] is None


def test_endpoint_pro_installed_wheel_present(env):
    env.state["version"] = "0.3.4"
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installed")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["installed"] is True
    assert data["version"] == "0.3.4"


def test_endpoint_pro_installed_never_5xx(env, monkeypatch):
    def boom():
        raise RuntimeError("simulated importlib.metadata failure")

    monkeypatch.setattr(env.lic, "_pro_installed_version", boom)
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installed")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _INSTALLED_SHAPE
    assert data["installed"] is False
    assert data["version"] is None


# -- endpoint: /api/license/pro-installation --


def test_endpoint_pro_installation_no_wheel_no_marker(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installation")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _INFO_SHAPE
    assert data["installed"] is False
    assert data["version"] is None
    assert data["marker"] == {}


def test_endpoint_pro_installation_full_healthy(env):
    env.state["version"] = "0.3.4"
    _write_marker(
        env,
        {
            "installed_at": 1_700_000_000,
            "version": "0.3.4",
            "source": "downloaded",
        },
    )
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installation")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["installed"] is True
    assert data["version"] == "0.3.4"
    assert data["marker"]["source"] == "downloaded"
    assert data["marker"]["installed_at"] == 1_700_000_000


def test_endpoint_pro_installation_wheel_uninstalled_marker_stays(env):
    """Marker + no wheel -- the operator-visible disagreement branch."""
    _write_marker(
        env,
        {
            "installed_at": 1_700_000_000,
            "version": "0.3.4",
            "source": "downloaded",
        },
    )
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installation")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["installed"] is False
    assert data["version"] is None
    # Marker survives on its own leg so the UI can render "was installed on
    # <date> from <source>, but the wheel is gone now" without needing a
    # second endpoint call.
    assert data["marker"]["installed_at"] == 1_700_000_000


def test_endpoint_pro_installation_never_5xx(env, monkeypatch):
    """Broken install (import / marker mismatch) must degrade to the empty
    envelope at HTTP 200 rather than 500 -- matches the never-crash posture
    of the sibling ``/api/license/*`` endpoints."""

    def boom_version():
        raise RuntimeError("simulated importlib.metadata failure")

    def boom_marker():
        raise RuntimeError("simulated marker read failure")

    monkeypatch.setattr(env.lic, "_pro_installed_version", boom_version)
    monkeypatch.setattr(env.lic, "_read_pro_marker", boom_marker)
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installation")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data) == _INFO_SHAPE
    assert data["installed"] is False
    assert data["version"] is None
    assert data["marker"] == {}
