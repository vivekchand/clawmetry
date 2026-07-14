"""Tests pinning the ``/api/entitlement/lock-reasons-batch`` bare plural URL.

``/api/entitlement/lock-reason-batch`` (singular URL) has been the per-item
plural sibling of ``/lock-reason`` since it landed; it delegates to
:func:`clawmetry.entitlements.lock_reasons_batch` (plural helper) and returns
a five-axis body of rows. Its ``_at`` sibling was subsequently registered as
``/api/entitlement/lock-reasons-at-batch`` under the plural URL naming --
which left the bare URL out of step with the ``_at`` URL.

This alias registers ``/api/entitlement/lock-reasons-batch`` as a second
route on the same view function so the bare / ``_at`` URLs read symmetrically
(``/min-tier-for-features`` <-> ``/min-tier-for-features-at``,
``/lock-reasons-batch`` <-> ``/lock-reasons-at-batch``). Both URLs dispatch
to the same code path and MUST return byte-identical JSON -- the tests below
pin that contract so the alias cannot silently drift.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── URL-map registration ──────────────────────────────────────────────────


def test_alias_url_is_registered(client):
    """Both URLs must be reachable and dispatch 200 on a happy path."""
    bare = client.get("/api/entitlement/lock-reasons-batch?features=fleet")
    canon = client.get("/api/entitlement/lock-reason-batch?features=fleet")
    assert bare.status_code == 200
    assert canon.status_code == 200


def test_alias_endpoint_name_is_distinct():
    """The alias must register under its own Flask endpoint name so
    ``url_for`` reverse lookups stay unambiguous. Sibling ``_at`` URL is
    already ``api_entitlement_lock_reasons_at_batch``; the bare alias
    mirrors that naming."""
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    rules = {r.rule: r.endpoint for r in app.url_map.iter_rules()}
    assert (
        rules["/api/entitlement/lock-reasons-batch"]
        == "entitlement.api_entitlement_lock_reasons_batch"
    )
    assert (
        rules["/api/entitlement/lock-reason-batch"]
        == "entitlement.api_entitlement_lock_reason_batch"
    )


# ── byte-parity across the whole surface ─────────────────────────────────


def _bodies_match(client, qs: str) -> tuple[dict, dict]:
    bare = client.get(f"/api/entitlement/lock-reasons-batch{qs}")
    canon = client.get(f"/api/entitlement/lock-reason-batch{qs}")
    assert bare.status_code == canon.status_code
    return bare.get_json(), canon.get_json()


def test_parity_features_only(client):
    b, c = _bodies_match(client, "?features=fleet,sso")
    assert b == c


def test_parity_runtimes_only(client):
    b, c = _bodies_match(client, "?runtimes=claude_code,openclaw")
    assert b == c


def test_parity_all_five_axes_grace(client):
    b, c = _bodies_match(
        client,
        "?features=fleet,sso&runtimes=claude_code"
        "&channels=5&retention_days=30&nodes=3",
    )
    assert b == c


def test_parity_all_five_axes_enforce(client, ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    b, c = _bodies_match(
        client,
        "?features=fleet,sso&runtimes=claude_code"
        "&channels=5&retention_days=30&nodes=3",
    )
    assert b == c
    # Sanity: the shared body carries the enforce metadata.
    assert b["enforced"] is True
    assert b["grace"] is False


def test_parity_unknown_ids_dont_500(client, ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    b, c = _bodies_match(
        client, "?features=fleet,not_a_real_feature"
    )
    assert b == c
    rows = {r["key"]: r for r in b["features"]}
    assert rows["not_a_real_feature"]["locked"] is False
    assert rows["not_a_real_feature"]["required_tier"] is None


def test_parity_blank_capacity_treated_as_unsupplied(client):
    """Blank capacities on both URLs must 400 with the same body."""
    b = client.get(
        "/api/entitlement/lock-reasons-batch"
        "?channels=&retention_days=&nodes="
    )
    c = client.get(
        "/api/entitlement/lock-reason-batch"
        "?channels=&retention_days=&nodes="
    )
    assert b.status_code == 400
    assert c.status_code == 400
    assert b.get_json() == c.get_json()


def test_parity_no_input_400(client):
    b = client.get("/api/entitlement/lock-reasons-batch")
    c = client.get("/api/entitlement/lock-reason-batch")
    assert b.status_code == 400
    assert c.status_code == 400
    assert b.get_json() == c.get_json()


def test_parity_non_int_capacity_silently_skipped(client):
    b, c = _bodies_match(client, "?features=fleet&channels=abc")
    assert b == c
    assert b["channels"] is None


def test_parity_capacity_alone_is_enough_input(client):
    b, c = _bodies_match(client, "?channels=5")
    assert b == c
    b, c = _bodies_match(client, "?retention_days=30")
    assert b == c
    b, c = _bodies_match(client, "?nodes=3")
    assert b == c


def test_parity_carries_current_tier_metadata(client, ent):
    b, c = _bodies_match(client, "?features=fleet")
    assert b == c
    for key in ("current_tier", "current_tier_rank", "grace", "enforced"):
        assert key in b


def test_parity_resolver_failure_returns_grace_shape(client, monkeypatch):
    """A synthetic resolver crash must yield the SAME grace-shape body on
    both URLs (never a 5xx)."""
    import clawmetry.entitlements as _ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(_ent, "lock_reasons_batch", boom)
    b, c = _bodies_match(client, "?features=fleet")
    assert b == c
    assert b["features"] == []
    assert b["grace"] is True
    assert b["enforced"] is False


def test_parity_body_shape_matches_lock_reasons_at_batch_without_perspective(
    client, ent
):
    """The bare body must match ``/lock-reasons-at-batch`` with the three
    perspective_* keys stripped -- same relationship the sibling bare / _at
    pairs already establish. Pins that adding the alias did not accidentally
    drift the shape."""
    at = client.get(
        "/api/entitlement/lock-reasons-at-batch?tier=cloud_pro&features=fleet"
    ).get_json()
    bare = client.get(
        "/api/entitlement/lock-reasons-batch?features=fleet"
    ).get_json()
    stripped = {
        k: v
        for k, v in at.items()
        if k
        not in {
            "perspective_tier",
            "perspective_tier_rank",
            "perspective_tier_label",
        }
    }
    assert bare == stripped
