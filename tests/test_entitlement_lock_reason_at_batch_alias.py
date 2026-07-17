"""Tests pinning the ``/api/entitlement/lock-reason-at-batch`` bare singular URL.

``/api/entitlement/lock-reasons-at-batch`` (plural URL) has been the
per-item plural sibling of ``/lock-reason-at`` since it landed; it delegates
to :func:`clawmetry.entitlements.lock_reasons_at_batch` and returns a
five-axis body of rows against a hypothetical ``perspective_tier``. Its LIVE
sibling was ``/api/entitlement/lock-reason-batch`` (bare singular URL), and
that URL was aliased to ``/api/entitlement/lock-reasons-batch`` (plural URL)
so the LIVE surface exposes both naming conventions.

This alias registers ``/api/entitlement/lock-reason-at-batch`` as a second
route on the same view function so the ``_at`` URL exposes the same
bare / plural pairing already registered on the LIVE URL. Together the four
routes read as one 2x2 ({singular, plural} x {live, _at}) so callers can
address either half under either naming convention:

    /lock-reason-batch      <-> /lock-reasons-batch       (live)
    /lock-reason-at-batch   <-> /lock-reasons-at-batch    (_at)

Both URLs in the ``_at`` pair dispatch to the same code path and MUST return
byte-identical JSON -- the tests below pin that contract so the alias cannot
silently drift.
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
    bare = client.get(
        "/api/entitlement/lock-reason-at-batch?tier=cloud_pro&features=fleet"
    )
    canon = client.get(
        "/api/entitlement/lock-reasons-at-batch?tier=cloud_pro&features=fleet"
    )
    assert bare.status_code == 200
    assert canon.status_code == 200


def test_alias_endpoint_name_is_distinct():
    """The alias must register under its own Flask endpoint name so
    ``url_for`` reverse lookups stay unambiguous. Mirrors the naming used on
    the LIVE side: ``api_entitlement_lock_reason_batch`` (function name,
    singular) vs ``api_entitlement_lock_reasons_batch`` (plural alias)."""
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    rules = {r.rule: r.endpoint for r in app.url_map.iter_rules()}
    assert (
        rules["/api/entitlement/lock-reasons-at-batch"]
        == "entitlement.api_entitlement_lock_reasons_at_batch"
    )
    assert (
        rules["/api/entitlement/lock-reason-at-batch"]
        == "entitlement.api_entitlement_lock_reason_at_batch"
    )


# ── byte-parity across the whole surface ─────────────────────────────────


def _bodies_match(client, qs: str) -> tuple[dict, dict]:
    bare = client.get(f"/api/entitlement/lock-reason-at-batch{qs}")
    canon = client.get(f"/api/entitlement/lock-reasons-at-batch{qs}")
    assert bare.status_code == canon.status_code
    return bare.get_json(), canon.get_json()


def test_parity_features_only(client):
    b, c = _bodies_match(client, "?tier=cloud_pro&features=fleet,sso")
    assert b == c


def test_parity_runtimes_only(client):
    b, c = _bodies_match(
        client, "?tier=cloud_pro&runtimes=claude_code,openclaw"
    )
    assert b == c


def test_parity_all_five_axes_grace(client):
    b, c = _bodies_match(
        client,
        "?tier=cloud_pro&features=fleet,sso&runtimes=claude_code"
        "&channels=5&retention_days=30&nodes=3",
    )
    assert b == c


def test_parity_all_five_axes_enforce(client, ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    b, c = _bodies_match(
        client,
        "?tier=cloud_pro&features=fleet,sso&runtimes=claude_code"
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
        client, "?tier=cloud_pro&features=fleet,not_a_real_feature"
    )
    assert b == c
    rows = {r["key"]: r for r in b["features"]}
    assert rows["not_a_real_feature"]["locked"] is False
    assert rows["not_a_real_feature"]["required_tier"] is None


def test_parity_blank_capacity_treated_as_unsupplied(client):
    """Blank capacities on both URLs must 400 with the same body."""
    b = client.get(
        "/api/entitlement/lock-reason-at-batch"
        "?tier=cloud_pro&channels=&retention_days=&nodes="
    )
    c = client.get(
        "/api/entitlement/lock-reasons-at-batch"
        "?tier=cloud_pro&channels=&retention_days=&nodes="
    )
    assert b.status_code == 400
    assert c.status_code == 400
    assert b.get_json() == c.get_json()


def test_parity_missing_tier_400(client):
    b = client.get(
        "/api/entitlement/lock-reason-at-batch?features=fleet"
    )
    c = client.get(
        "/api/entitlement/lock-reasons-at-batch?features=fleet"
    )
    assert b.status_code == 400
    assert c.status_code == 400
    assert b.get_json() == c.get_json()


def test_parity_unknown_tier_404(client):
    b = client.get(
        "/api/entitlement/lock-reason-at-batch"
        "?tier=not_a_tier&features=fleet"
    )
    c = client.get(
        "/api/entitlement/lock-reasons-at-batch"
        "?tier=not_a_tier&features=fleet"
    )
    assert b.status_code == 404
    assert c.status_code == 404
    assert b.get_json() == c.get_json()


def test_parity_no_input_400(client):
    b = client.get("/api/entitlement/lock-reason-at-batch?tier=cloud_pro")
    c = client.get("/api/entitlement/lock-reasons-at-batch?tier=cloud_pro")
    assert b.status_code == 400
    assert c.status_code == 400
    assert b.get_json() == c.get_json()


def test_parity_non_int_capacity_silently_skipped(client):
    b, c = _bodies_match(
        client, "?tier=cloud_pro&features=fleet&channels=abc"
    )
    assert b == c
    assert b["channels"] is None


def test_parity_capacity_alone_is_enough_input(client):
    b, c = _bodies_match(client, "?tier=cloud_pro&channels=5")
    assert b == c
    b, c = _bodies_match(client, "?tier=cloud_pro&retention_days=30")
    assert b == c
    b, c = _bodies_match(client, "?tier=cloud_pro&nodes=3")
    assert b == c


def test_parity_carries_perspective_and_current_tier_metadata(client, ent):
    b, c = _bodies_match(client, "?tier=cloud_pro&features=fleet")
    assert b == c
    for key in (
        "perspective_tier",
        "perspective_tier_rank",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    ):
        assert key in b
    assert b["perspective_tier"] == "cloud_pro"


def test_parity_resolver_failure_returns_grace_shape(client, monkeypatch):
    """A synthetic resolver crash must yield the SAME grace-shape body on
    both URLs (never a 5xx). The perspective tier is echoed back so the
    caller can render "you asked for X" even on the fallback."""
    import clawmetry.entitlements as _ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(_ent, "lock_reasons_at_batch", boom)
    b, c = _bodies_match(client, "?tier=cloud_pro&features=fleet")
    assert b == c
    assert b["features"] == []
    assert b["perspective_tier"] == "cloud_pro"
    assert b["grace"] is True
    assert b["enforced"] is False


def test_parity_body_shape_matches_live_batch_with_perspective_added(
    client, ent
):
    """The ``_at`` body must match the LIVE ``/lock-reason-batch`` body plus
    the ``perspective_*`` keys -- same relationship the LIVE / ``_at`` pair
    already establishes on the singular / plural halves. Pins that adding
    the singular ``_at`` alias did not accidentally drift the shape."""
    at = client.get(
        "/api/entitlement/lock-reason-at-batch"
        "?tier=cloud_pro&features=fleet"
    ).get_json()
    live = client.get(
        "/api/entitlement/lock-reason-batch?features=fleet"
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
    assert live == stripped
