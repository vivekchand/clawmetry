"""Tests for the ``pro_install_age_days_at(epoch)`` scalar helper on
``clawmetry.license`` and its paired ``/api/license/pro-install-age-days-at``
HTTP endpoint.

The perspective-epoch flavour of :func:`clawmetry.license.pro_install_age_days`.
Both derive from the same marker ``installed_at`` so they cannot disagree at
the day boundary when the perspective epoch equals "now"; on any other epoch
this helper answers "how old was the pro install as of ``epoch``?" without the
caller having to snapshot the marker state at that time or compute
``(epoch - installed_at) // 86400`` themselves.

Mirrors ``tests/test_license_age_days_at_scalar.py`` line-for-line where the
two scalars share posture (bool-refused, non-numeric coerced to None, never-
raises, independent of expiry / live importability), and diverges on the one
axis they must differ on: this scalar is intentionally NOT clamped to
``max(0, ...)`` because a perspective epoch BEFORE ``installed_at`` is a real
signal the caller asked for (as opposed to clock skew, which is the only way
``installed_at`` can be in the future when reading against ``time.time()``
from :func:`pro_install_age_days`).

Hermetic: the marker path is monkeypatched into ``tmp_path`` and
``_pro_installed_version`` is stubbed so tests never touch the real
site-packages -- same env fixture as
``tests/test_license_pro_install_age_scalar.py``.
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
    ``tests/test_license_pro_install_age_scalar.py``: tmp marker path,
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


# ── clawmetry.license.pro_install_age_days_at() ──────────────────────────────


def test_pro_install_age_days_at_none_when_no_marker(env):
    """No marker file on disk -> None (nothing to compute against)."""
    assert env.lic.pro_install_age_days_at(int(time.time())) is None


def test_pro_install_age_days_at_now_matches_pro_install_age_days(env):
    """When ``epoch`` equals "now", the perspective-epoch scalar must
    agree with :func:`pro_install_age_days` at the day boundary (+/- 1
    for the fractional-second drift between the two calls: the base
    scalar reads ``time.time()`` with sub-second precision inside
    itself, while the caller here passes an ``int(time.time())`` that
    already truncated the fraction)."""
    _write_marker(
        env,
        {"installed_at": int(time.time()) - 7 * 86400, "version": "0.3.4"},
    )
    now = int(time.time())
    at_now = env.lic.pro_install_age_days_at(now)
    scalar_now = env.lic.pro_install_age_days()
    assert isinstance(at_now, int)
    assert isinstance(scalar_now, int)
    assert abs(at_now - scalar_now) <= 1


def test_pro_install_age_days_at_future_epoch(env):
    """A perspective epoch 10 days from now against a just-provisioned
    marker should render age ~10 days."""
    _write_marker(env, {"installed_at": int(time.time()), "version": "0.3.4"})
    epoch = int(time.time()) + 10 * 86400
    days = env.lic.pro_install_age_days_at(epoch)
    assert isinstance(days, int)
    # Floor-divided; allow +/- 1 for day-boundary jitter.
    assert 9 <= days <= 10


def test_pro_install_age_days_at_far_future_epoch(env):
    """Perspective epoch 100 days from now against a just-provisioned
    marker should render age ~100 days -- unlike the "now" flavour, no
    cap on how old the caller may ask about."""
    _write_marker(env, {"installed_at": int(time.time()), "version": "0.3.4"})
    epoch = int(time.time()) + 100 * 86400
    days = env.lic.pro_install_age_days_at(epoch)
    assert isinstance(days, int)
    assert 99 <= days <= 100


def test_pro_install_age_days_at_negative_when_epoch_before_installed_at(env):
    """An operator asking "how old was the pro install on <date>?"
    where <date> is BEFORE provisioning -- perspective epoch BEFORE
    ``installed_at`` -> negative int, NOT None and NOT clamped to 0.
    Distinct from :func:`pro_install_age_days`, which clamps because it
    can only reach the future-``installed_at`` branch via clock skew
    (nothing to hide here -- the caller explicitly asked a pre-
    provisioning question)."""
    _write_marker(env, {"installed_at": int(time.time()), "version": "0.3.4"})
    epoch = int(time.time()) - 15 * 86400
    days = env.lic.pro_install_age_days_at(epoch)
    assert isinstance(days, int)
    assert days < 0
    # epoch - installed_at = -15d.
    assert -16 <= days <= -14


def test_pro_install_age_days_at_zero_on_day_of_install(env):
    """Perspective epoch on the day of provisioning -> 0."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    assert env.lic.pro_install_age_days_at(installed) == 0
    # Sub-day AFTER installed_at still floor-divides to 0.
    assert env.lic.pro_install_age_days_at(installed + 3600) == 0
    # Sub-day BEFORE installed_at floor-divides to -1 (Python's floor
    # division on a negative dividend rounds AWAY from zero).
    assert env.lic.pro_install_age_days_at(installed - 3600) == -1


def test_pro_install_age_days_at_independent_of_live_import(env):
    """Marker present but wheel not importable -> still returns age.
    Age tracks the marker, not live importability -- ``installed`` is
    the separate signal for that."""
    _write_marker(
        env,
        {"installed_at": int(time.time()) - 5 * 86400, "version": "0.3.4"},
    )
    # state["version"] stays None -> pro_installed() is False.
    assert env.lic.pro_installed() is False
    days = env.lic.pro_install_age_days_at(int(time.time()))
    assert isinstance(days, int)
    assert 4 <= days <= 6


def test_pro_install_age_days_at_missing_installed_at(env):
    """Marker exists but ``installed_at`` key absent -> None regardless
    of epoch."""
    _write_marker(env, {"version": "0.3.4"})
    assert env.lic.pro_install_age_days_at(int(time.time())) is None
    assert env.lic.pro_install_age_days_at(0) is None
    assert env.lic.pro_install_age_days_at(2_000_000_000) is None


def test_pro_install_age_days_at_non_numeric_installed_at(env):
    """``installed_at`` is a string -> None."""
    _write_marker(env, {"installed_at": "yesterday", "version": "0.3.4"})
    assert env.lic.pro_install_age_days_at(int(time.time())) is None


def test_pro_install_age_days_at_zero_installed_at_rejected(env):
    """Non-positive ``installed_at`` is meaningless -> None (marker's
    scalar refuses it, so the perspective flavour must too)."""
    _write_marker(env, {"installed_at": 0, "version": "0.3.4"})
    assert env.lic.pro_install_age_days_at(int(time.time())) is None


def test_pro_install_age_days_at_bool_installed_at_rejected(env):
    """``bool`` marker value is refused by :func:`pro_installed_at`,
    so the perspective flavour collapses too."""
    _write_marker(env, {"installed_at": True, "version": "0.3.4"})
    assert env.lic.pro_install_age_days_at(int(time.time())) is None


def test_pro_install_age_days_at_corrupt_marker(env):
    """Marker file is not JSON -> None."""
    os.makedirs(os.path.dirname(env.marker_path), exist_ok=True)
    with open(env.marker_path, "w", encoding="utf-8") as fh:
        fh.write("{not valid json")
    assert env.lic.pro_install_age_days_at(int(time.time())) is None


def test_pro_install_age_days_at_non_numeric_epoch(env):
    """A caller passing a typo must get None, not a crash."""
    _write_marker(env, {"installed_at": int(time.time()), "version": "0.3.4"})
    assert env.lic.pro_install_age_days_at("garbage") is None  # type: ignore[arg-type]
    assert env.lic.pro_install_age_days_at(None) is None  # type: ignore[arg-type]
    assert env.lic.pro_install_age_days_at([1]) is None  # type: ignore[arg-type]


def test_pro_install_age_days_at_bool_epoch_rejected(env):
    """``bool`` is an ``int`` subclass -- explicitly refuse it so a
    caller that passes ``True`` doesn't silently get "days from
    installed_at to epoch 1" back."""
    _write_marker(env, {"installed_at": int(time.time()), "version": "0.3.4"})
    assert env.lic.pro_install_age_days_at(True) is None  # type: ignore[arg-type]
    assert env.lic.pro_install_age_days_at(False) is None  # type: ignore[arg-type]


def test_pro_install_age_days_at_float_epoch_coerced(env):
    """Float epoch must coerce through ``int()`` rather than crash --
    same posture as :func:`license_age_days_at`."""
    _write_marker(env, {"installed_at": int(time.time()), "version": "0.3.4"})
    now_f = float(time.time())
    days = env.lic.pro_install_age_days_at(now_f)
    assert isinstance(days, int)


def test_pro_install_age_days_at_never_raises(env, monkeypatch):
    """Any underlying failure -> None. Even a fully-broken
    :func:`pro_installed_at` must not propagate."""
    def _boom():
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(env.lic, "pro_installed_at", _boom)
    assert env.lic.pro_install_age_days_at(int(time.time())) is None


# ── GET /api/license/pro-install-age-days-at ─────────────────────────────────


def test_endpoint_pro_install_age_days_at_no_marker(env):
    with env.app.test_client() as c:
        resp = c.get(f"/api/license/pro-install-age-days-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert isinstance(data["requested_epoch"], int)
    assert data["installed_at"] is None
    assert data["marker_present"] is False
    assert data["installed"] is False


def test_endpoint_pro_install_age_days_at_active(env):
    now = int(time.time())
    _write_marker(env, {"installed_at": now, "version": "0.3.4"})
    env.state["version"] = "0.3.4"
    epoch = now + 45 * 86400
    with env.app.test_client() as c:
        resp = c.get(f"/api/license/pro-install-age-days-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["age_days"], int)
    assert 44 <= data["age_days"] <= 45
    assert data["requested_epoch"] == epoch
    assert isinstance(data["installed_at"], int)
    assert data["marker_present"] is True
    assert data["installed"] is True


def test_endpoint_pro_install_age_days_at_negative_for_pre_install_epoch(env):
    """Perspective epoch BEFORE ``installed_at`` -> negative age_days,
    installed_at still populated so a support tile can render the pair
    without a second call."""
    _write_marker(env, {"installed_at": int(time.time()), "version": "0.3.4"})
    env.state["version"] = "0.3.4"
    epoch = int(time.time()) - 30 * 86400
    with env.app.test_client() as c:
        resp = c.get(f"/api/license/pro-install-age-days-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["age_days"], int)
    assert data["age_days"] < 0
    assert isinstance(data["installed_at"], int)
    assert data["marker_present"] is True


def test_endpoint_pro_install_age_days_at_marker_present_wheel_missing(env):
    """The paywall-debug case: marker on disk, wheel pip-uninstalled.
    ``age_days`` still surfaces (age tracks the marker, not live
    import); ``installed`` is False so a caller that wants to hide the
    row on a broken install has the signal."""
    _write_marker(env, {"installed_at": 1_700_000_000, "version": "0.3.4"})
    # state["version"] stays None -> pro_installed() is False.
    epoch = 1_700_000_000 + 12 * 86400
    with env.app.test_client() as c:
        resp = c.get(f"/api/license/pro-install-age-days-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] == 12
    assert data["installed_at"] == 1_700_000_000
    assert data["marker_present"] is True
    assert data["installed"] is False


def test_endpoint_pro_install_age_days_at_missing_installed_at(env):
    """Marker exists but ``installed_at`` key absent -> age_days null,
    installed_at null, marker_present false (mirrors the "nothing to
    date" branch of :func:`pro_installed_at`)."""
    _write_marker(env, {"version": "0.3.4"})
    with env.app.test_client() as c:
        resp = c.get(f"/api/license/pro-install-age-days-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["installed_at"] is None
    assert data["marker_present"] is False


def test_endpoint_pro_install_age_days_at_missing_epoch_arg(env):
    """No ``epoch=`` -> age_days null, requested_epoch null, HTTP 200.
    The snapshot still populates installed_at / marker_present /
    installed from the on-disk marker."""
    _write_marker(
        env,
        {"installed_at": int(time.time()) - 3 * 86400, "version": "0.3.4"},
    )
    env.state["version"] = "0.3.4"
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-install-age-days-at")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["requested_epoch"] is None
    assert isinstance(data["installed_at"], int)
    assert data["marker_present"] is True
    assert data["installed"] is True


def test_endpoint_pro_install_age_days_at_non_integer_epoch(env):
    """Typo epoch -> age_days null, requested_epoch null, HTTP 200
    (never a 4xx). Mirrors the ``/api/license/age-days-at`` posture."""
    _write_marker(env, {"installed_at": int(time.time()), "version": "0.3.4"})
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-install-age-days-at?epoch=garbage")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["requested_epoch"] is None
    assert data["marker_present"] is True


def test_endpoint_pro_install_age_days_at_corrupt_marker(env):
    os.makedirs(os.path.dirname(env.marker_path), exist_ok=True)
    with open(env.marker_path, "w", encoding="utf-8") as fh:
        fh.write("{not json")
    with env.app.test_client() as c:
        resp = c.get(f"/api/license/pro-install-age-days-at?epoch={int(time.time())}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["installed_at"] is None
    assert data["marker_present"] is False
    assert data["installed"] is False


def test_endpoint_pro_install_age_days_at_never_5xxs(env, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    must still return HTTP 200 with the no-marker shape (snapshot
    fallback kicks in, requested_epoch is still echoed, age_days is
    null)."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_pro_install_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    epoch = int(time.time())
    with env.app.test_client() as c:
        resp = c.get(f"/api/license/pro-install-age-days-at?epoch={epoch}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["age_days"] is None
    assert data["requested_epoch"] == epoch
    assert data["installed_at"] is None
    assert data["marker_present"] is False
    assert data["installed"] is False


# ── cross-endpoint consistency ───────────────────────────────────────────────


def test_endpoint_agrees_with_pro_install_age_days_at_now(env):
    """When ``epoch`` equals "now", the perspective endpoint must agree
    with ``/api/license/pro-install-age-days`` at the day boundary
    (+/- 1 for the fractional-second drift between the two request
    handlers: the base endpoint reads ``time.time()`` with sub-second
    precision inside :func:`pro_install_age_days` at handle-time, while
    the perspective endpoint receives an ``int(time.time())`` from the
    caller that already truncated the fraction). Both derive from the
    same marker, so a UI binding both cannot catch them disagreeing by
    more than a day for the same install."""
    _write_marker(
        env,
        {"installed_at": int(time.time()) - 8 * 86400, "version": "0.3.4"},
    )
    env.state["version"] = "0.3.4"
    now = int(time.time())
    with env.app.test_client() as c:
        a = c.get(f"/api/license/pro-install-age-days-at?epoch={now}").get_json()
        b = c.get("/api/license/pro-install-age-days").get_json()
    assert isinstance(a["age_days"], int)
    assert isinstance(b["age_days"], int)
    assert abs(a["age_days"] - b["age_days"]) <= 1


def test_endpoint_agrees_with_pro_installed_at_on_shared_snapshot(env):
    """Both endpoints share :func:`_pro_install_snapshot` -- they must
    surface identical ``installed_at`` / ``marker_present`` /
    ``installed`` values for the same install regardless of the epoch
    queried."""
    _write_marker(
        env,
        {"installed_at": int(time.time()) - 42 * 86400, "version": "0.3.4"},
    )
    env.state["version"] = "0.3.4"
    epoch = int(time.time()) + 5 * 86400
    with env.app.test_client() as c:
        a = c.get(f"/api/license/pro-install-age-days-at?epoch={epoch}").get_json()
        b = c.get("/api/license/pro-installed-at").get_json()
    for key in ("installed_at", "marker_present", "installed"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"
    assert a["requested_epoch"] == epoch


def test_endpoint_agrees_with_pro_install_age_days_on_shared_snapshot(env):
    """The perspective endpoint and the "now" endpoint share
    :func:`_pro_install_snapshot`, so their common fields must match
    exactly regardless of which epoch the perspective one is asked
    about."""
    _write_marker(
        env,
        {"installed_at": int(time.time()) - 20 * 86400, "version": "0.3.4"},
    )
    env.state["version"] = "0.3.4"
    epoch = int(time.time()) + 90 * 86400
    with env.app.test_client() as c:
        a = c.get(f"/api/license/pro-install-age-days-at?epoch={epoch}").get_json()
        b = c.get("/api/license/pro-install-age-days").get_json()
    for key in ("installed_at", "marker_present", "installed"):
        assert a[key] == b[key], f"mismatch on {key}: {a[key]!r} vs {b[key]!r}"
