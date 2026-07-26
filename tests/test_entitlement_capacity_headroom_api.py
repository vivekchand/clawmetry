"""HTTP tests for ``/api/entitlement/capacity-headroom`` and
``/api/entitlement/capacity-headroom-at``.

Pins:
  * the envelope shape matches the underlying helper byte-for-byte
  * per-axis opt-in via query params (unsupplied axes stay ``None``)
  * bad query values on any axis collapse that axis to ``None`` -- a stray
    ``?channels=junk`` cannot silently blank a gauge
  * ``-at`` variant 404s for empty / unknown ``?tier=``
  * never 5xxs: a resolver failure returns the neutral envelope on the
    unscoped endpoint
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(enforced):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# -- unscoped endpoint ----------------------------------------------------


def test_headroom_envelope_shape(client):
    resp = client.get(
        "/api/entitlement/capacity-headroom?channels=2&retention_days=5&nodes=1"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == {
        "tier", "tier_label", "channels", "retention_days", "nodes",
    }


def test_headroom_row_shape(client):
    resp = client.get("/api/entitlement/capacity-headroom?channels=2")
    assert resp.status_code == 200
    row = resp.get_json()["channels"]
    assert set(row) == {
        "kind", "used", "cap", "remaining", "is_unlimited",
        "at_limit", "over_limit", "pct_used",
    }


def test_headroom_unsupplied_axes_stay_none(client):
    resp = client.get("/api/entitlement/capacity-headroom?channels=2")
    body = resp.get_json()
    assert body["channels"] is not None
    assert body["retention_days"] is None
    assert body["nodes"] is None


def test_headroom_no_args_returns_neutral_envelope(client):
    resp = client.get("/api/entitlement/capacity-headroom")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None


@pytest.mark.parametrize("axis", ["channels", "retention_days", "nodes"])
@pytest.mark.parametrize("bad", ["junk", "", "-1", "true", "false", "1.5"])
def test_headroom_bad_axis_collapses_to_none(client, axis, bad):
    resp = client.get(f"/api/entitlement/capacity-headroom?{axis}={bad}")
    assert resp.status_code == 200
    assert resp.get_json()[axis] is None


def test_headroom_mixed_bad_good(client):
    resp = client.get(
        "/api/entitlement/capacity-headroom?channels=junk&retention_days=5"
    )
    body = resp.get_json()
    assert body["channels"] is None
    assert body["retention_days"] is not None
    assert body["retention_days"]["used"] == 5


def test_headroom_never_5xxs_on_resolver_failure(monkeypatch, client, enforced):
    def _bang(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(enforced, "capacity_headroom", _bang)
    resp = client.get("/api/entitlement/capacity-headroom?channels=2")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == {
        "tier", "tier_label", "channels", "retention_days", "nodes",
    }


# -- -at endpoint --------------------------------------------------------


def test_headroom_at_ok(client, enforced):
    resp = client.get(
        f"/api/entitlement/capacity-headroom-at?tier={enforced.TIER_OSS}&channels=2"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == enforced.TIER_OSS
    assert body["channels"]["cap"] == enforced._FREE_CHANNEL_LIMIT


@pytest.mark.parametrize("bad_tier", ["", "does-not-exist", "nonesuch"])
def test_headroom_at_unknown_tier_404s(client, bad_tier):
    resp = client.get(
        f"/api/entitlement/capacity-headroom-at?tier={bad_tier}&channels=1"
    )
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "unknown tier"}


def test_headroom_at_missing_tier_arg_404s(client):
    resp = client.get("/api/entitlement/capacity-headroom-at?channels=1")
    assert resp.status_code == 404


def test_headroom_at_row_matches_helper(client, enforced):
    resp = client.get(
        f"/api/entitlement/capacity-headroom-at?tier={enforced.TIER_CLOUD_STARTER}&retention_days=45"
    )
    body = resp.get_json()
    expected = enforced.capacity_headroom_at(
        enforced.TIER_CLOUD_STARTER, retention_days=45
    )
    assert body == expected


def test_headroom_at_bad_axis_collapses_to_none(client, enforced):
    resp = client.get(
        f"/api/entitlement/capacity-headroom-at?tier={enforced.TIER_OSS}&channels=junk&retention_days=5"
    )
    body = resp.get_json()
    assert body["channels"] is None
    assert body["retention_days"] is not None
