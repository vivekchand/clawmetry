"""Tests for the bare ``/api/entitlement/{next,previous}-tier-diff``
endpoints -- the stand-alone sibling of ``/next-tier-unlocks`` /
``/next-tier-locks`` / ``/next-tier-spec`` for the marginal
``upgrade_diff`` / ``downgrade_diff`` row.

``Entitlement.next_tier_diff`` / ``previous_tier_diff`` (the instance
methods) and the module-level ``next_tier_diff()`` / ``previous_tier_diff()``
convenience wrappers already ship. ``/api/entitlement`` already surfaces
these bodies inline under ``next_tier_diff`` / ``prev_tier_diff``. What
was missing were the dedicated ``GET /api/entitlement/next-tier-diff`` and
``GET /api/entitlement/previous-tier-diff`` endpoints -- the sibling
docstrings on ``/next-tier-spec`` and ``/next-tier-unlocks`` reference them
as if they existed.

These tests pin:

* endpoint envelope shape (6 stable keys) matches the sibling
  ``/next-tier-unlocks`` / ``/next-tier-locks`` / ``/next-tier-spec``
  envelopes so the four bare directional routes stay interchangeable
  from a UI layout point of view
* endpoint ``row`` byte-parity with the resolved
  ``Entitlement.next_tier_diff`` / ``previous_tier_diff`` bound method
  so the endpoint cannot drift from the helper
* endpoint ``row`` byte-parity with the module-level
  ``next_tier_diff()`` / ``previous_tier_diff()`` helper for the same
  reason
* endpoint ``row`` byte-parity with the existing inline slot on
  ``/api/entitlement`` (``next_tier_diff`` / ``prev_tier_diff``) so the
  two surfaces agree on the same body
* ceiling (Enterprise for ``next``) and floor (OSS / cloud_free for
  ``previous``) collapse ``row`` to ``null``; envelope metadata stays
  populated so the CTA surface keeps rendering
* trial-source resolution matches the sibling directional endpoints
  (next -> enterprise, previous -> cloud_starter)
* grace vs enforce yields byte-identical bodies (catalogue-derived)
* never-5xx: a synthesised resolver failure returns 200 with the
  grace-shape envelope
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


_ENVELOPE_KEYS = {
    "current_tier",
    "current_tier_label",
    "current_tier_rank",
    "row",
    "grace",
    "enforced",
}

_UPGRADE_ROW_KEYS = {"target", "added_features", "added_runtimes"}
_DOWNGRADE_ROW_KEYS = {"target", "lost_features", "lost_runtimes"}


# ── /api/entitlement/next-tier-diff ──────────────────────────────────────────


def test_next_tier_diff_endpoint_oss_default(client, ent):
    rv = client.get("/api/entitlement/next-tier-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["row"] is not None
    assert set(body["row"].keys()) == _UPGRADE_ROW_KEYS
    # OSS -> next purchasable rung is cloud_starter (rank 1).
    assert body["row"]["target"] == ent.TIER_CLOUD_STARTER
    assert body["grace"] is True
    assert body["enforced"] is False


def test_next_tier_diff_endpoint_row_matches_bound_method(client, ent):
    rv = client.get("/api/entitlement/next-tier-diff")
    body = rv.get_json()
    assert body["row"] == ent.get_entitlement().next_tier_diff()


def test_next_tier_diff_endpoint_row_matches_module_helper(client, ent):
    rv = client.get("/api/entitlement/next-tier-diff")
    body = rv.get_json()
    assert body["row"] == ent.next_tier_diff()


def test_next_tier_diff_endpoint_row_matches_entitlement_inline_slot(
    client, ent
):
    # /api/entitlement already surfaces next_tier_diff inline under the
    # `next_tier_diff` key. The stand-alone endpoint's `row` slot must
    # agree byte-for-byte so both surfaces stay in sync.
    ent_body = client.get("/api/entitlement").get_json()
    dedicated = client.get("/api/entitlement/next-tier-diff").get_json()
    assert dedicated["row"] == ent_body.get("next_tier_diff")


def test_next_tier_diff_endpoint_row_at_ceiling(client, ent, monkeypatch):
    # Pin an enterprise-tier entitlement and confirm the endpoint reports
    # `row=null` with the envelope metadata still populated so a CTA can
    # render "you're at the top" copy.
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    rv = client.get("/api/entitlement/next-tier-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["current_tier"] == ent.TIER_ENTERPRISE
    assert body["current_tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert body["current_tier_rank"] == ent.tier_rank(ent.TIER_ENTERPRISE)
    assert body["row"] is None


def test_next_tier_diff_endpoint_trial_resolves_to_enterprise(
    client, ent, monkeypatch
):
    # Trial sits at rank 2, so the next strictly-higher purchasable rung
    # is enterprise -- matches the sibling next-tier-unlocks/locks/spec
    # behaviour.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    body = client.get("/api/entitlement/next-tier-diff").get_json()
    assert body["row"] is not None
    assert body["row"]["target"] == ent.TIER_ENTERPRISE


def test_next_tier_diff_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/next-tier-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == "oss"
    assert body["current_tier_label"] == "OSS"
    assert body["current_tier_rank"] == 0
    assert body["row"] is None
    assert body["grace"] is True
    assert body["enforced"] is False


# ── /api/entitlement/previous-tier-diff ──────────────────────────────────────


def test_previous_tier_diff_endpoint_oss_default_floor(client, ent):
    # OSS sits at rank 0 -- no rung below -- so the row collapses to
    # null while the envelope metadata stays populated.
    rv = client.get("/api/entitlement/previous-tier-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["current_tier"] == ent.TIER_OSS
    assert body["row"] is None
    assert body["grace"] is True


def test_previous_tier_diff_endpoint_row_matches_bound_method(
    client, ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    rv = client.get("/api/entitlement/previous-tier-diff")
    body = rv.get_json()
    assert body["row"] == e.previous_tier_diff()
    assert set(body["row"].keys()) == _DOWNGRADE_ROW_KEYS
    assert body["row"]["target"] == ent.TIER_CLOUD_STARTER


def test_previous_tier_diff_endpoint_row_matches_module_helper(
    client, ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    rv = client.get("/api/entitlement/previous-tier-diff")
    body = rv.get_json()
    assert body["row"] == ent.previous_tier_diff()


def test_previous_tier_diff_endpoint_row_matches_entitlement_inline_slot(
    client, ent, monkeypatch
):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    ent_body = client.get("/api/entitlement").get_json()
    dedicated = client.get("/api/entitlement/previous-tier-diff").get_json()
    assert dedicated["row"] == ent_body.get("prev_tier_diff")


def test_previous_tier_diff_endpoint_cloud_free_floor(
    client, ent, monkeypatch
):
    # cloud_free is a same-rank sibling of OSS at rank 0, so it also has
    # no rung strictly below -- the row collapses to null just like OSS.
    e = ent._build(ent.TIER_CLOUD_FREE, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    body = client.get("/api/entitlement/previous-tier-diff").get_json()
    assert body["current_tier"] == ent.TIER_CLOUD_FREE
    assert body["row"] is None


def test_previous_tier_diff_endpoint_trial_resolves_to_starter(
    client, ent, monkeypatch
):
    # Trial steps down to rank 1 (starter) -- matches the sibling
    # previous-tier-unlocks/locks/spec behaviour.
    e = ent._build(ent.TIER_TRIAL, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    body = client.get("/api/entitlement/previous-tier-diff").get_json()
    assert body["row"] is not None
    assert body["row"]["target"] == ent.TIER_CLOUD_STARTER


def test_previous_tier_diff_endpoint_never_raises(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/previous-tier-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["row"] is None
    assert body["current_tier"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False


# ── grace vs enforce parity ─────────────────────────────────────────────────


def test_next_tier_diff_endpoint_grace_matches_enforce(
    client, ent, monkeypatch
):
    # The helper is catalogue-derived (off upgrade_diff on the static
    # per-tier grants), not gated -- so flipping enforce on must not
    # change the row body.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    grace_body = client.get("/api/entitlement/next-tier-diff").get_json()

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    # Rebuild the entitlement under enforce and re-pin the resolver so we
    # compare identical resolved contexts (only enforce flag differs).
    e2 = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e2)
    # And rebuild the client so the fresh module is picked up.
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    enforce_body = (
        app.test_client().get("/api/entitlement/next-tier-diff").get_json()
    )
    assert enforce_body["row"] == grace_body["row"]


# ── sibling family parity ───────────────────────────────────────────────────


def test_next_tier_diff_envelope_shape_matches_sibling_family(client, ent):
    # The four bare directional endpoints (diff/unlocks/locks/spec) share
    # a common envelope shape so a UI can lay them out on a single card
    # without conditional key handling. Pin that they carry the same
    # metadata keys around the payload slot.
    diff = client.get("/api/entitlement/next-tier-diff").get_json()
    unlocks = client.get("/api/entitlement/next-tier-unlocks").get_json()
    common = {
        "current_tier",
        "current_tier_label",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    assert common.issubset(diff.keys())
    assert common.issubset(unlocks.keys())
    # Payload slot differs by name (row vs unlocks) but the surrounding
    # metadata must byte-equal so a shared header component can render
    # both bodies.
    for key in common:
        assert diff[key] == unlocks[key]
