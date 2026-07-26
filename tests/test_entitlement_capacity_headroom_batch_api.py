"""HTTP tests for ``/api/entitlement/capacity-headroom-batch``.

Pins:
  * envelope shape (``tiers`` / ``current_tier`` / ``current_tier_rank`` /
    ``grace`` / ``enforced``)
  * one row per purchasable tier, walked in ``(rank, id)`` order --
    byte-stable against ``/capacity-diff-batch``
  * each row is byte-identical to
    ``/api/entitlement/capacity-headroom-at`` for the same axis inputs
  * per-axis opt-in via query params (unsupplied axes stay ``None``
    on every row)
  * bad query values on any axis collapse that axis to ``None`` on
    every row -- a stray ``?channels=junk`` cannot silently blank
    the pricing ladder
  * ``current_tier`` / ``grace`` / ``enforced`` still track the live
    resolver even though ``tiers`` walks the static per-tier caps
  * never 5xxs: a resolver failure returns the empty-tiers grace envelope
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


# -- envelope ------------------------------------------------------------


def test_envelope_shape(client):
    resp = client.get("/api/entitlement/capacity-headroom-batch?channels=2")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == {
        "tiers",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }


def test_envelope_carries_resolver_state(client, enforced):
    resp = client.get("/api/entitlement/capacity-headroom-batch?channels=2")
    body = resp.get_json()
    ent = enforced.get_entitlement()
    assert body["current_tier"] == ent.tier
    assert body["current_tier_rank"] == enforced.tier_rank(ent.tier)
    assert body["enforced"] is True
    assert body["grace"] == bool(ent.grace)


# -- rows ----------------------------------------------------------------


def test_one_row_per_purchasable_tier(client, enforced):
    body = client.get(
        "/api/entitlement/capacity-headroom-batch?channels=2"
    ).get_json()
    assert len(body["tiers"]) == len(enforced._PURCHASABLE_TIERS)


def test_trial_tier_excluded(client, enforced):
    body = client.get(
        "/api/entitlement/capacity-headroom-batch?channels=2"
    ).get_json()
    tiers = {r["tier"] for r in body["tiers"]}
    assert enforced.TIER_TRIAL not in tiers


def test_row_envelope_shape(client):
    body = client.get(
        "/api/entitlement/capacity-headroom-batch?channels=2&retention_days=5&nodes=1"
    ).get_json()
    for r in body["tiers"]:
        assert set(r) == {
            "tier", "tier_label", "channels", "retention_days", "nodes",
        }


def test_row_ordering_matches_capacity_diff_batch(client, enforced):
    diff_body = client.get(
        "/api/entitlement/capacity-diff-batch"
    ).get_json()
    headroom_body = client.get(
        "/api/entitlement/capacity-headroom-batch?channels=2"
    ).get_json()
    diff_ids = [r["target"] for r in diff_body["tiers"]]
    headroom_ids = [r["tier"] for r in headroom_body["tiers"]]
    assert diff_ids == headroom_ids


def test_each_row_matches_scalar_at_endpoint(client, enforced):
    body = client.get(
        "/api/entitlement/capacity-headroom-batch?channels=2&retention_days=5&nodes=1"
    ).get_json()
    for r in body["tiers"]:
        scalar = client.get(
            f"/api/entitlement/capacity-headroom-at?tier={r['tier']}"
            "&channels=2&retention_days=5&nodes=1"
        )
        assert scalar.status_code == 200
        assert r == scalar.get_json()


# -- per-axis opt-in ------------------------------------------------------


def test_unsupplied_axis_stays_none_on_every_row(client):
    body = client.get(
        "/api/entitlement/capacity-headroom-batch?channels=2"
    ).get_json()
    for r in body["tiers"]:
        assert r["channels"] is not None
        assert r["retention_days"] is None
        assert r["nodes"] is None


def test_no_args_returns_ladder_with_all_none_rows(client, enforced):
    body = client.get(
        "/api/entitlement/capacity-headroom-batch"
    ).get_json()
    assert len(body["tiers"]) == len(enforced._PURCHASABLE_TIERS)
    for r in body["tiers"]:
        assert r["channels"] is None
        assert r["retention_days"] is None
        assert r["nodes"] is None


@pytest.mark.parametrize("axis", ["channels", "retention_days", "nodes"])
@pytest.mark.parametrize("bad", ["junk", "", "-1", "true", "false", "1.5"])
def test_bad_axis_collapses_to_none_on_every_row(client, axis, bad):
    body = client.get(
        f"/api/entitlement/capacity-headroom-batch?{axis}={bad}"
    ).get_json()
    for r in body["tiers"]:
        assert r[axis] is None


def test_mixed_bad_and_good_axes(client):
    body = client.get(
        "/api/entitlement/capacity-headroom-batch?channels=junk&retention_days=5"
    ).get_json()
    for r in body["tiers"]:
        assert r["channels"] is None
        assert r["retention_days"] is not None
        assert r["retention_days"]["used"] == 5


# -- concrete per-tier caps ----------------------------------------------


def _row_for(rows, tier):
    for r in rows:
        if r["tier"] == tier:
            return r
    raise AssertionError(f"tier {tier!r} missing from batch rows")


def test_oss_channels_row_uses_free_cap(client, enforced):
    body = client.get(
        "/api/entitlement/capacity-headroom-batch?channels=2"
    ).get_json()
    row = _row_for(body["tiers"], enforced.TIER_OSS)["channels"]
    assert row["cap"] == enforced._FREE_CHANNEL_LIMIT
    assert row["is_unlimited"] is False


def test_enterprise_retention_row_unlimited(client, enforced):
    body = client.get(
        "/api/entitlement/capacity-headroom-batch?retention_days=365"
    ).get_json()
    row = _row_for(body["tiers"], enforced.TIER_ENTERPRISE)["retention_days"]
    assert row["cap"] is None
    assert row["is_unlimited"] is True


# -- decoupled from resolver ---------------------------------------------


def test_tiers_grace_vs_enforce_byte_identical(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    def _rows(enforce: bool):
        if enforce:
            monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
        else:
            monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        import clawmetry.entitlements as e

        importlib.reload(e)
        e.invalidate()
        from routes.entitlement import bp_entitlement

        app = Flask(__name__)
        app.register_blueprint(bp_entitlement)
        c = app.test_client()
        try:
            return c.get(
                "/api/entitlement/capacity-headroom-batch"
                "?channels=2&retention_days=5&nodes=1"
            ).get_json()["tiers"]
        finally:
            e.invalidate()

    assert _rows(False) == _rows(True)


# -- never 5xxs -----------------------------------------------------------


def test_never_5xxs_on_helper_failure(monkeypatch, client, enforced):
    def _bang(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(enforced, "capacity_headroom_batch", _bang)
    monkeypatch.setattr(enforced, "get_entitlement", _bang)
    resp = client.get(
        "/api/entitlement/capacity-headroom-batch?channels=2"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }
