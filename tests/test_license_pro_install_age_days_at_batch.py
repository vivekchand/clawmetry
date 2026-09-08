"""Tests for :func:`clawmetry.license.pro_install_age_days_at_batch` and
the paired ``GET /api/license/pro-install-age-days-at-batch`` endpoint.

Per-value batch sibling of :func:`clawmetry.license.pro_install_age_days_at`
/ ``/api/license/pro-install-age-days-at``. Fills the ``_at_batch`` slot on
the pro-install-age axis alongside the singular scalar and the "now"
flavour, so a scheduled-audit tile can plot the install-age across a
sequence of perspective dates in one call. Twin of
``license_age_days_at_batch`` for the ``installed_at`` axis.

Hermetic: marker path monkeypatched into ``tmp_path``,
``_pro_installed_version`` stubbed so tests never touch site-packages --
mirrors ``tests/test_license_pro_install_age_days_at_scalar.py``.
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
    """Isolated pro-install env with the entitlement blueprint mounted.

    Mirrors the fixture in
    ``tests/test_license_pro_install_age_days_at_scalar.py`` so the two
    suites can be read side-by-side.
    """
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


# -- clawmetry.license.pro_install_age_days_at_batch() -----------------------


def test_pro_install_age_days_at_batch_none_returns_empty(env):
    """``epochs is None`` -> ``[]``. Never-raise posture, matches
    :func:`license_state_at_batch` / :func:`is_expired_at_batch`."""
    assert env.lic.pro_install_age_days_at_batch(None) == []


def test_pro_install_age_days_at_batch_non_iterable_returns_empty(env):
    """Non-iterable ``epochs`` (a bare int -- probable typo for a caller
    that forgot to wrap it) -> ``[]`` rather than a crash."""
    assert env.lic.pro_install_age_days_at_batch(42) == []


def test_pro_install_age_days_at_batch_empty_returns_empty(env):
    """Empty iterable -> ``[]``."""
    assert env.lic.pro_install_age_days_at_batch([]) == []
    assert env.lic.pro_install_age_days_at_batch(()) == []


def test_pro_install_age_days_at_batch_no_marker(env):
    """No marker file on disk -> every row ``age_days=None`` (nothing to
    compute against). Time-independent, matches the scalar posture."""
    rows = env.lic.pro_install_age_days_at_batch(
        [0, int(time.time()), 2_000_000_000]
    )
    assert [r["age_days"] for r in rows] == [None, None, None]


def test_pro_install_age_days_at_batch_active_marker_positive_days(env):
    """Active marker, epochs after ``installed_at`` -> positive signed
    day counts, floor-divided from seconds (matches the scalar)."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    env.state["version"] = "0.3.4"
    epochs = [installed, installed + 10 * 86400, installed + 100 * 86400]
    rows = env.lic.pro_install_age_days_at_batch(epochs)
    assert [r["epoch"] for r in rows] == epochs
    assert rows[0]["age_days"] == 0
    assert rows[1]["age_days"] == 10
    assert rows[2]["age_days"] == 100


def test_pro_install_age_days_at_batch_negative_for_pre_install_epochs(env):
    """Epoch BEFORE ``installed_at`` -> negative int, NOT clamped to 0
    (unlike the "now" flavour, a caller explicitly asking a pre-install
    question wants the signed answer). Matches the scalar."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    rows = env.lic.pro_install_age_days_at_batch(
        [installed - 5 * 86400, installed - 1, installed, installed + 1]
    )
    ages = [r["age_days"] for r in rows]
    assert ages[0] == -5
    # ``installed - 1`` -> ``(-1) // 86400`` -> -1 (Python floor-div on
    # a negative dividend rounds AWAY from zero).
    assert ages[1] == -1
    assert ages[2] == 0
    assert ages[3] == 0


def test_pro_install_age_days_at_batch_per_row_parity_with_scalar(env):
    """Per-row parity with :func:`pro_install_age_days_at` -- the batch
    cannot silently drift from the scalar. Pin every row."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    epochs = [
        installed - 10 * 86400,
        installed - 1,
        installed,
        installed + 1,
        installed + 60 * 86400,
    ]
    rows = env.lic.pro_install_age_days_at_batch(epochs)
    for row, epoch in zip(rows, epochs):
        assert row["age_days"] == env.lic.pro_install_age_days_at(epoch), epoch


def test_pro_install_age_days_at_batch_missing_installed_at(env):
    """Marker exists but ``installed_at`` key absent -> every row
    ``age_days=None`` regardless of epoch (matches the scalar)."""
    _write_marker(env, {"version": "0.3.4"})
    rows = env.lic.pro_install_age_days_at_batch(
        [0, int(time.time()), 2_000_000_000]
    )
    assert [r["age_days"] for r in rows] == [None, None, None]


def test_pro_install_age_days_at_batch_corrupt_marker(env):
    """Corrupt marker JSON -> every row ``age_days=None`` (scalar
    collapses too; batch inherits)."""
    os.makedirs(os.path.dirname(env.marker_path), exist_ok=True)
    with open(env.marker_path, "w", encoding="utf-8") as fh:
        fh.write("{not valid json")
    rows = env.lic.pro_install_age_days_at_batch([int(time.time()), 0])
    assert [r["age_days"] for r in rows] == [None, None]


def test_pro_install_age_days_at_batch_string_int_tokens_parsed(env):
    """Int-parseable strings coerce cleanly (matches the singular's
    ``int()`` coercion in :func:`_license_epoch_batch_keys`)."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    rows = env.lic.pro_install_age_days_at_batch(
        [str(installed + 5 * 86400), str(installed - 3 * 86400)]
    )
    assert [r["age_days"] for r in rows] == [5, -3]


def test_pro_install_age_days_at_batch_dedupes_by_int_key_preserves_order(env):
    """Duplicates by parsed int key are dropped preserving first-seen
    order so the response is byte-stable across calls."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    rows = env.lic.pro_install_age_days_at_batch(
        [
            installed,
            installed + 100,
            installed,
            str(installed + 100),
            installed + 200,
        ]
    )
    assert [r["epoch"] for r in rows] == [
        installed,
        installed + 100,
        installed + 200,
    ]


def test_pro_install_age_days_at_batch_bad_tokens_collapse_to_none(env):
    """``bool`` / non-numeric / ``None`` collapse to ``age_days=None``
    (matches the scalar's rejection). Row still keeps its slot so each
    bad input gets its own bucket."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    rows = env.lic.pro_install_age_days_at_batch(
        [True, False, None, "garbage", ""]
    )
    assert len(rows) == 5
    assert all(r["age_days"] is None for r in rows)


def test_pro_install_age_days_at_batch_mixed_good_and_bad(env):
    """Bad tokens don't fail the whole batch. Good rows still resolve;
    bad rows still slot in with ``age_days=None``."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    rows = env.lic.pro_install_age_days_at_batch(
        [installed, "garbage", installed + 30 * 86400]
    )
    ages = [r["age_days"] for r in rows]
    assert ages[0] == 0
    assert ages[1] is None
    assert ages[2] == 30


def test_pro_install_age_days_at_batch_independent_of_live_import(env):
    """Marker present but wheel not importable -> ``age_days`` still
    surfaces (age tracks the marker, not live importability). Matches
    the scalar."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    # state["version"] stays None -> pro_installed() is False.
    assert env.lic.pro_installed() is False
    rows = env.lic.pro_install_age_days_at_batch(
        [installed, installed + 7 * 86400]
    )
    assert [r["age_days"] for r in rows] == [0, 7]


def test_pro_install_age_days_at_batch_never_raises(env, monkeypatch):
    """Any per-row underlying failure of :func:`pro_install_age_days_at`
    -> ``age_days=None`` for THAT row. The batch never propagates."""
    def _boom(_epoch):
        raise RuntimeError("simulated corrupt install")

    monkeypatch.setattr(env.lic, "pro_install_age_days_at", _boom)
    rows = env.lic.pro_install_age_days_at_batch([1_700_000_000, 1_800_000_000])
    assert [r["age_days"] for r in rows] == [None, None]
    assert len(rows) == 2


# -- GET /api/license/pro-install-age-days-at-batch --------------------------


def test_endpoint_pro_install_age_days_at_batch_missing_epochs(env):
    """``?epochs=`` absent -> 400 missing epochs (matches the other
    ``/api/license/*-at-batch`` endpoints -- missing input is a real
    error, unlike bad input)."""
    with env.app.test_client() as c:
        resp = c.get("/api/license/pro-install-age-days-at-batch")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing epochs"}


def test_endpoint_pro_install_age_days_at_batch_blank_epochs(env):
    """``?epochs=`` blank / only-commas -> 400 missing epochs."""
    with env.app.test_client() as c:
        resp1 = c.get("/api/license/pro-install-age-days-at-batch?epochs=")
        resp2 = c.get("/api/license/pro-install-age-days-at-batch?epochs=,,,")
    assert resp1.status_code == 400
    assert resp2.status_code == 400


def test_endpoint_pro_install_age_days_at_batch_no_marker(env):
    """No marker file -> every row ``age_days=None``, HTTP 200, snapshot
    fields set to the no-marker branch shape."""
    now = int(time.time())
    with env.app.test_client() as c:
        resp = c.get(
            f"/api/license/pro-install-age-days-at-batch?epochs={now},0"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "pro_install_age_days_at"
    assert data["count"] == 2
    assert [r["age_days"] for r in data["rows"]] == [None, None]
    assert data["installed_at"] is None
    assert data["marker_present"] is False
    assert data["installed"] is False


def test_endpoint_pro_install_age_days_at_batch_active_marker(env):
    """Active marker: signed day counts, snapshot reflects live install."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    env.state["version"] = "0.3.4"
    epochs = [installed + 5 * 86400, installed + 20 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with env.app.test_client() as c:
        resp = c.get(f"/api/license/pro-install-age-days-at-batch?epochs={csv}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["kind"] == "pro_install_age_days_at"
    assert data["count"] == 2
    assert [r["age_days"] for r in data["rows"]] == [5, 20]
    assert data["installed_at"] == installed
    assert data["marker_present"] is True
    assert data["installed"] is True


def test_endpoint_pro_install_age_days_at_batch_per_row_parity_with_scalar(env):
    """Per-row parity with the singular
    ``/api/license/pro-install-age-days-at?epoch=<n>`` endpoint -- the
    batch cannot silently drift from the scalar endpoint."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    env.state["version"] = "0.3.4"
    epochs = [
        installed - 10 * 86400,
        installed - 1,
        installed,
        installed + 1,
        installed + 60 * 86400,
    ]
    csv = ",".join(str(e) for e in epochs)
    with env.app.test_client() as c:
        batch = c.get(
            f"/api/license/pro-install-age-days-at-batch?epochs={csv}"
        ).get_json()
        for row, epoch in zip(batch["rows"], epochs):
            scalar = c.get(
                f"/api/license/pro-install-age-days-at?epoch={epoch}"
            ).get_json()
            assert row["age_days"] == scalar["age_days"], epoch


def test_endpoint_pro_install_age_days_at_batch_negative_pre_install(env):
    """Epoch BEFORE ``installed_at`` -> negative ``age_days`` (matches
    the scalar's signed-integer posture)."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    with env.app.test_client() as c:
        resp = c.get(
            f"/api/license/pro-install-age-days-at-batch?epochs={installed - 30 * 86400},{installed + 30 * 86400}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    ages = [r["age_days"] for r in data["rows"]]
    assert ages[0] == -30
    assert ages[1] == 30
    assert data["marker_present"] is True


def test_endpoint_pro_install_age_days_at_batch_bad_tokens_collapse_to_none(env):
    """Bad tokens don't fail the whole batch. They slot in with
    ``age_days=null`` while good rows still resolve."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    with env.app.test_client() as c:
        resp = c.get(
            f"/api/license/pro-install-age-days-at-batch?epochs=garbage,{installed + 3 * 86400}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert data["rows"][0]["age_days"] is None
    assert data["rows"][1]["age_days"] == 3


def test_endpoint_pro_install_age_days_at_batch_marker_present_wheel_missing(env):
    """The paywall-debug case: marker on disk, wheel pip-uninstalled.
    ``age_days`` still surfaces (age tracks the marker, not live
    import); ``installed`` is False so a caller that wants to hide the
    row on a broken install has the signal."""
    _write_marker(env, {"installed_at": 1_700_000_000, "version": "0.3.4"})
    # state["version"] stays None -> pro_installed() is False.
    epochs = [1_700_000_000, 1_700_000_000 + 12 * 86400]
    csv = ",".join(str(e) for e in epochs)
    with env.app.test_client() as c:
        resp = c.get(f"/api/license/pro-install-age-days-at-batch?epochs={csv}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert [r["age_days"] for r in data["rows"]] == [0, 12]
    assert data["installed_at"] == 1_700_000_000
    assert data["marker_present"] is True
    assert data["installed"] is False


def test_endpoint_pro_install_age_days_at_batch_dedupe_preserves_order(env):
    """Duplicates by parsed int key are dropped preserving first-seen
    order for byte-stable output."""
    installed = int(time.time())
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    with env.app.test_client() as c:
        resp = c.get(
            f"/api/license/pro-install-age-days-at-batch?epochs={installed},{installed + 100},{installed},{installed + 100}"
        )
    data = resp.get_json()
    assert data["count"] == 2
    assert [r["epoch"] for r in data["rows"]] == [installed, installed + 100]


def test_endpoint_pro_install_age_days_at_batch_corrupt_marker(env):
    """Corrupt marker -> HTTP 200, every row ``age_days=null``, snapshot
    fields reflect the no-marker branch."""
    os.makedirs(os.path.dirname(env.marker_path), exist_ok=True)
    with open(env.marker_path, "w", encoding="utf-8") as fh:
        fh.write("{not json")
    now = int(time.time())
    with env.app.test_client() as c:
        resp = c.get(
            f"/api/license/pro-install-age-days-at-batch?epochs={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 1
    assert data["rows"][0]["age_days"] is None
    assert data["installed_at"] is None
    assert data["marker_present"] is False
    assert data["installed"] is False


def test_endpoint_pro_install_age_days_at_batch_never_5xxs(env, monkeypatch):
    """Even if the shared snapshot blows up mid-request, the endpoint
    still returns HTTP 200 with the no-marker snapshot fallback + honest
    per-row derivation."""
    from routes import entitlement as _routes

    monkeypatch.setattr(
        _routes,
        "_pro_install_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("simulated blowup")),
    )
    now = int(time.time())
    with env.app.test_client() as c:
        resp = c.get(
            f"/api/license/pro-install-age-days-at-batch?epochs={now}"
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["installed_at"] is None
    assert data["marker_present"] is False
    assert data["installed"] is False


# -- cross-endpoint consistency ----------------------------------------------


def test_endpoint_agrees_with_scalar_endpoint_on_shared_snapshot(env):
    """The batch endpoint and the singular perspective endpoint share
    :func:`_pro_install_snapshot`, so their common fields must match
    exactly regardless of which epoch each is asked about."""
    installed = int(time.time()) - 20 * 86400
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    env.state["version"] = "0.3.4"
    epoch = int(time.time()) + 5 * 86400
    with env.app.test_client() as c:
        batch = c.get(
            f"/api/license/pro-install-age-days-at-batch?epochs={epoch}"
        ).get_json()
        scalar = c.get(
            f"/api/license/pro-install-age-days-at?epoch={epoch}"
        ).get_json()
    for key in ("installed_at", "marker_present", "installed"):
        assert batch[key] == scalar[key], f"mismatch on {key}"
    # And the per-row age_days for that epoch matches the scalar's.
    assert batch["rows"][0]["age_days"] == scalar["age_days"]


def test_endpoint_agrees_with_pro_installed_at_on_shared_snapshot(env):
    """The batch endpoint and ``/api/license/pro-installed-at`` share
    :func:`_pro_install_snapshot`, so their common fields must match
    exactly."""
    installed = int(time.time()) - 42 * 86400
    _write_marker(env, {"installed_at": installed, "version": "0.3.4"})
    env.state["version"] = "0.3.4"
    with env.app.test_client() as c:
        batch = c.get(
            f"/api/license/pro-install-age-days-at-batch?epochs={int(time.time())}"
        ).get_json()
        installed_at_ep = c.get("/api/license/pro-installed-at").get_json()
    for key in ("installed_at", "marker_present", "installed"):
        assert batch[key] == installed_at_ep[key], f"mismatch on {key}"
