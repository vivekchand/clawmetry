"""Tests for the ``pro_installed_at()`` / ``pro_install_age_days()``
scalar helpers on ``clawmetry.license`` and their paired
``/api/license/pro-installed-at`` + ``/api/license/pro-install-age-days``
HTTP endpoints.

These scalars view onto the ``installed_at`` field of the
``clawmetry-pro`` provisioning marker (``~/.clawmetry/pro_installed.json``),
mirroring the ``license_issued_at`` / ``license_age_days`` pattern that
already exists for the signed-license ``iat`` claim. Same never-raise
posture, same clock-skew clamp, same "share a snapshot across the two
endpoints so a UI cannot catch them disagreeing" invariant.

The env is hermetic: the marker path is monkeypatched into ``tmp_path``
and ``_pro_installed_version`` is stubbed so tests never touch the real
site-packages.
"""
from __future__ import annotations

import json
import os
import time
from types import SimpleNamespace

import pytest
from flask import Flask


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Isolated license env mirroring
    ``tests/test_license_pro_installation.py``: tmp marker path,
    controllable pro-version reader, Flask app with the entitlement
    blueprint mounted."""
    import clawmetry.license as _lic

    marker_path = str(tmp_path / "pro_installed.json")
    monkeypatch.setattr(_lic, "_PRO_MARKER_PATH", marker_path)

    state = {"version": None}
    monkeypatch.setattr(_lic, "_pro_installed_version", lambda: state["version"])

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
    os.makedirs(os.path.dirname(env.marker_path), exist_ok=True)
    with open(env.marker_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


# ── clawmetry.license.pro_installed_at() ─────────────────────────────────────


def test_pro_installed_at_none_when_no_marker(env):
    """No marker file on disk -> None (nothing to surface)."""
    assert env.lic.pro_installed_at() is None


def test_pro_installed_at_returns_epoch_when_marker_present(env):
    now = int(time.time())
    _write_marker(env, {"installed_at": now - 3600, "version": "0.3.4"})
    got = env.lic.pro_installed_at()
    assert isinstance(got, int)
    assert got == now - 3600


def test_pro_installed_at_accepts_float_installed_at(env):
    """Some markers wrote ``installed_at`` as a float; must coerce to int
    rather than collapse to None."""
    now = time.time()
    _write_marker(env, {"installed_at": now - 60.0, "version": "0.3.4"})
    got = env.lic.pro_installed_at()
    assert isinstance(got, int)
    assert got == int(now - 60.0)


def test_pro_installed_at_independent_of_live_import(env):
    """Marker on disk but ``clawmetry-pro`` not importable -> still returns
    the epoch. That disagreement (marker present, wheel missing) is
    exactly what a paywall-debugging tile wants to surface."""
    _write_marker(env, {"installed_at": 1_700_000_000, "version": "0.3.4"})
    # state["version"] stays None -> pro_installed() is False.
    assert env.lic.pro_installed() is False
    assert env.lic.pro_installed_at() == 1_700_000_000


def test_pro_installed_at_missing_installed_at_key(env):
    """Marker exists but ``installed_at`` key absent -> None."""
    _write_marker(env, {"version": "0.3.4", "source": "test"})
    assert env.lic.pro_installed_at() is None


def test_pro_installed_at_non_numeric_installed_at(env):
    """``installed_at`` is a string -> None (never raises)."""
    _write_marker(env, {"installed_at": "yesterday", "version": "0.3.4"})
    assert env.lic.pro_installed_at() is None


def test_pro_installed_at_bool_installed_at_rejected(env):
    """``bool`` is an ``int`` subclass -- explicitly refuse it so a marker
    that somehow contains ``{"installed_at": true}`` collapses to None
    rather than surfacing as epoch 1."""
    _write_marker(env, {"installed_at": True, "version": "0.3.4"})
    assert env.lic.pro_installed_at() is None


def test_pro_installed_at_zero_and_negative_rejected(env):
    """Non-positive epochs are meaningless -> None."""
    _write_marker(env, {"installed_at": 0, "version": "0.3.4"})
    assert env.lic.pro_installed_at() is None
    _write_marker(env, {"installed_at": -1, "version": "0.3.4"})
    assert env.lic.pro_installed_at() is None


def test_pro_installed_at_corrupt_marker_json(env):
    """Marker file is not JSON -> None (via _read_pro_marker's fallback)."""
    os.makedirs(os.path.dirname(env.marker_path), exist_ok=True)
    with open(env.marker_path, "w", encoding="utf-8") as fh:
        fh.write("{not valid json")
    assert env.lic.pro_installed_at() is None


def test_pro_installed_at_marker_is_list_not_dict(env):
    """_read_pro_marker returns {} for non-dict JSON -> scalar returns None."""
    os.makedirs(os.path.dirname(env.marker_path), exist_ok=True)
    with open(env.marker_path, "w", encoding="utf-8") as fh:
        json.dump(["not", "a", "dict"], fh)
    assert env.lic.pro_installed_at() is None


def test_pro_installed_at_never_raises(env, monkeypatch):
    """Even if ``_read_pro_marker`` blows up, the scalar must not
    propagate -- degrade to None."""
    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(env.lic, "_read_pro_marker", _boom)
    assert env.lic.pro_installed_at() is None


# ── clawmetry.license.pro_install_age_days() ─────────────────────────────────


def test_pro_install_age_days_none_when_no_marker(env):
    assert env.lic.pro_install_age_days() is None


def test_pro_install_age_days_zero_on_day_of_install(env):
    """Just-provisioned wheel -> 0 days old."""
    _write_marker(env, {"installed_at": int(time.time()), "version": "0.3.4"})
    assert env.lic.pro_install_age_days() == 0


def test_pro_install_age_days_positive_after_days(env):
    """Wheel provisioned N days ago -> ~N days old (floor-divided from
    seconds)."""
    _write_marker(
        env,
        {"installed_at": int(time.time()) - 30 * 86400, "version": "0.3.4"},
    )
    age = env.lic.pro_install_age_days()
    assert isinstance(age, int)
    # Allow +/- 1 for clock jitter across the day boundary.
    assert 29 <= age <= 31


def test_pro_install_age_days_clock_skew_installed_at_in_future_clamps_to_zero(env):
    """A clock-skewed ``installed_at`` in the future must not render as a
    negative age -- clamped to 0 so callers can safely render
    ``f"{age} days old"``."""
    _write_marker(
        env,
        {"installed_at": int(time.time()) + 7 * 86400, "version": "0.3.4"},
    )
    assert env.lic.pro_install_age_days() == 0


def test_pro_install_age_days_missing_installed_at(env):
    _write_marker(env, {"version": "0.3.4"})
    assert env.lic.pro_install_age_days() is None


def test_pro_install_age_days_non_numeric_installed_at(env):
    _write_marker(env, {"installed_at": "tomorrow", "version": "0.3.4"})
    assert env.lic.pro_install_age_days() is None


def test_pro_install_age_days_independent_of_live_import(env):
    """Marker present but wheel not importable -> still returns age. Age
    tracks the marker, not live importability -- ``installed`` is the
    separate signal for that."""
    _write_marker(
        env,
        {"installed_at": int(time.time()) - 5 * 86400, "version": "0.3.4"},
    )
    assert env.lic.pro_installed() is False
    age = env.lic.pro_install_age_days()
    assert isinstance(age, int)
    assert 4 <= age <= 6


def test_pro_install_age_days_never_raises(env, monkeypatch):
    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(env.lic, "pro_installed_at", _boom)
    assert env.lic.pro_install_age_days() is None


# ── GET /api/license/pro-installed-at ────────────────────────────────────────


def test_endpoint_pro_installed_at_no_marker(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installed-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "installed_at": None,
        "age_days": None,
        "marker_present": False,
        "installed": False,
    }


def test_endpoint_pro_installed_at_healthy(env):
    """Marker on disk + wheel importable -> full quartet populated."""
    now = int(time.time())
    _write_marker(env, {"installed_at": now - 3 * 86400, "version": "0.3.4"})
    env.state["version"] = "0.3.4"
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installed-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["installed_at"], int)
    assert isinstance(data["age_days"], int)
    assert 2 <= data["age_days"] <= 4
    assert data["marker_present"] is True
    assert data["installed"] is True


def test_endpoint_pro_installed_at_marker_present_but_wheel_missing(env):
    """The paywall-debug case: marker on disk but pip-uninstall wiped
    the wheel. Both facts must surface -- marker_present=true,
    installed=false -- so the UI can render the disagreement."""
    _write_marker(env, {"installed_at": 1_700_000_000, "version": "0.3.4"})
    # state["version"] stays None -> pro_installed() is False.
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installed-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["installed_at"] == 1_700_000_000
    assert data["marker_present"] is True
    assert data["installed"] is False


def test_endpoint_pro_installed_at_wheel_present_but_no_marker(env):
    """The opposite disagreement: pre-marker install (or marker deleted)
    yet the wheel is importable. installed=true but marker_present=false
    and the age scalars collapse to None because there's nothing to
    date."""
    env.state["version"] = "0.3.4"
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installed-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["installed_at"] is None
    assert data["age_days"] is None
    assert data["marker_present"] is False
    assert data["installed"] is True


def test_endpoint_pro_installed_at_corrupt_marker(env):
    os.makedirs(os.path.dirname(env.marker_path), exist_ok=True)
    with open(env.marker_path, "w", encoding="utf-8") as fh:
        fh.write("{not json")
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installed-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "installed_at": None,
        "age_days": None,
        "marker_present": False,
        "installed": False,
    }


def test_endpoint_pro_installed_at_never_5xxs(env, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the no-marker shape."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_pro_install_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-installed-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "installed_at": None,
        "age_days": None,
        "marker_present": False,
        "installed": False,
    }


# ── GET /api/license/pro-install-age-days ────────────────────────────────────


def test_endpoint_pro_install_age_days_no_marker(env):
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-install-age-days")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "age_days": None,
        "installed_at": None,
        "marker_present": False,
        "installed": False,
    }


def test_endpoint_pro_install_age_days_active(env):
    now = int(time.time())
    _write_marker(env, {"installed_at": now - 14 * 86400, "version": "0.3.4"})
    env.state["version"] = "0.3.4"
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-install-age-days")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["age_days"], int)
    assert 13 <= data["age_days"] <= 15
    assert isinstance(data["installed_at"], int)
    assert data["marker_present"] is True
    assert data["installed"] is True


def test_endpoint_pro_install_age_days_clock_skew_clamps_to_zero(env):
    _write_marker(
        env,
        {"installed_at": int(time.time()) + 30 * 86400, "version": "0.3.4"},
    )
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-install-age-days")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] == 0
    assert data["marker_present"] is True


def test_endpoint_pro_install_age_days_missing_installed_at(env):
    _write_marker(env, {"version": "0.3.4"})
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-install-age-days")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["installed_at"] is None
    # marker_present hangs off installed_at, so it collapses to False
    # here -- consistent with the scalar's "nothing to date" branch.
    assert data["marker_present"] is False


def test_endpoint_pro_install_age_days_never_5xxs(env, monkeypatch):
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_pro_install_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-install-age-days")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "age_days": None,
        "installed_at": None,
        "marker_present": False,
        "installed": False,
    }


# ── consistency: both endpoints see the same snapshot ────────────────────────


def test_both_endpoints_agree_on_snapshot(env):
    """Both endpoints share :func:`_pro_install_snapshot` -- they must
    surface identical ``installed_at`` / ``age_days`` / ``marker_present``
    / ``installed`` values for the same install."""
    _write_marker(
        env,
        {"installed_at": int(time.time()) - 42 * 86400, "version": "0.3.4"},
    )
    env.state["version"] = "0.3.4"
    with env.app.test_client() as c:
        a = c.get("/api/license/pro-installed-at").get_json()
        b = c.get("/api/license/pro-install-age-days").get_json()
    for key in ("installed_at", "age_days", "marker_present", "installed"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"


def test_both_endpoints_agree_on_disagreement_shape(env):
    """The marker-present-but-wheel-missing case: both endpoints must
    surface installed=False in lockstep so a UI binding both cannot
    catch them disagreeing."""
    _write_marker(env, {"installed_at": 1_700_000_000, "version": "0.3.4"})
    with env.app.test_client() as c:
        a = c.get("/api/license/pro-installed-at").get_json()
        b = c.get("/api/license/pro-install-age-days").get_json()
    for key in ("installed_at", "age_days", "marker_present", "installed"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"
    assert a["marker_present"] is True
    assert a["installed"] is False
