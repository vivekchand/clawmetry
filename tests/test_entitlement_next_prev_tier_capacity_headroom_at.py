"""Tests for ``next_tier_capacity_headroom_at`` /
``previous_tier_capacity_headroom_at`` (scalar what-ifs) and their
companion ``/api/entitlement/{next,previous}-tier-capacity-headroom-at``
endpoints.

Headroom-shaped mirror of the ``next_tier_capacity_diff_at`` /
``previous_tier_capacity_diff_at`` scalar what-ifs the diff family
already publishes: where the diff ``_at`` scalars answer "on the rung
above / below <hypothetical A>, what are the cap deltas", these
headroom ``_at`` scalars answer "on the rung above / below
<hypothetical A>, given my per-axis usage, what would my gauges look
like" -- the tooltip surface a pricing-comparison cell needs to render
the upgrade- / downgrade-side headroom for any hypothetical source rung
off **one** round-trip, without first hitting ``/api/entitlement`` and
without monkey-patching the entitlement context.

Fills the ``_at`` slot on the neighbour-tier capacity-headroom axis
alongside the live ``next_tier_capacity_headroom`` /
``previous_tier_capacity_headroom`` (which anchor to the resolved
entitlement) so the surface is complete on both the current-perspective
and hypothetical-perspective sides -- lining up rung-for-rung with the
diff / unlocks / locks ``_at`` scalars that already exist.

Pins covered here:

* ``next_tier_capacity_headroom_at(tier, ...)`` byte-equals
  ``capacity_headroom_at(_next_purchasable_tier_after(tier), ...)`` for
  every valid source / usage triple -- the convenience cannot drift
  from the explicit composition
* same identity for ``previous_tier_capacity_headroom_at`` against
  ``_previous_purchasable_tier_before``
* at the ceiling (``enterprise``) / floor (``oss`` / ``cloud_free``)
  both scalar helpers return ``None``
* trial-as-source resolves the same way the diff ``_at`` family does:
  next -> enterprise, previous -> cloud_starter
* unknown / empty / ``None`` / non-string source returns ``None``
* case + whitespace normalisation (``"  OSS  "`` -> ``"oss"``)
* per-axis "None means axis not supplied" posture matches the singular
  ``capacity_headroom_at`` -- an unsupplied axis stays ``None`` on the
  envelope, a supplied axis produces a full row
* grace vs enforce yields the same body (the ``_at`` family walks the
  static catalogue, not the gated resolver)
* the helpers never raise: a builder failure short-circuits to ``None``
* the endpoints never 5xx: builder failure short-circuits to
  ``headroom=null`` on the same 200 envelope; missing ``tier=`` yields
  400; unknown ``tier`` yields 404 with ``which=tier``
* at the ceiling / floor the endpoint stays 200 with
  ``target=null`` / ``headroom=null`` so callers do not have to branch
  on status
* endpoint ``headroom`` byte-equals
  ``/api/entitlement/capacity-headroom-at`` for the resolved neighbour
  target -- the endpoint cannot drift from the singular endpoint it
  composes
* endpoint envelope shape mirrors
  ``/api/entitlement/next-tier-capacity-diff-at`` byte-for-key on the
  source / target metadata (``tier`` / ``tier_label`` / ``tier_rank`` /
  ``target`` / ``target_label`` / ``target_rank``), with ``row`` replaced
  by ``headroom`` and ``direction`` echoing ``"upgrade"`` / ``"downgrade"``
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_HEADROOM_ROW_KEYS = {
    "kind",
    "used",
    "cap",
    "remaining",
    "is_unlimited",
    "at_limit",
    "over_limit",
    "pct_used",
}

_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "direction",
    "headroom",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- the capacity-headroom
    ``_at`` family walks the static catalogue and is independent of the
    resolver, so the fixture only needs to keep the live resolver from
    surprising the test."""
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


_NEXT_SOURCES = (
    "TIER_OSS",
    "TIER_CLOUD_FREE",
    "TIER_CLOUD_STARTER",
    "TIER_CLOUD_PRO",
    "TIER_PRO",
    "TIER_TRIAL",
)

_PREV_SOURCES = (
    "TIER_CLOUD_STARTER",
    "TIER_CLOUD_PRO",
    "TIER_PRO",
    "TIER_ENTERPRISE",
    "TIER_TRIAL",
)


# ── next_tier_capacity_headroom_at ────────────────────────────────────────────


def test_next_headroom_at_matches_explicit_composition(ent):
    for name in _NEXT_SOURCES:
        src = getattr(ent, name)
        nxt = ent._next_purchasable_tier_after(src)
        assert nxt is not None, src
        assert ent.next_tier_capacity_headroom_at(
            src, channels=10, retention_days=5, nodes=2
        ) == ent.capacity_headroom_at(
            nxt, channels=10, retention_days=5, nodes=2
        ), src


def test_next_headroom_at_returns_none_at_ceiling(ent):
    assert (
        ent.next_tier_capacity_headroom_at(
            ent.TIER_ENTERPRISE, channels=10, retention_days=5, nodes=2
        )
        is None
    )


def test_next_headroom_at_envelope_shape(ent):
    body = ent.next_tier_capacity_headroom_at(
        ent.TIER_OSS, channels=10, retention_days=5, nodes=2
    )
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    for axis in ("channels", "retention_days", "nodes"):
        assert body[axis] is not None
        assert set(body[axis].keys()) == _HEADROOM_ROW_KEYS


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_next_headroom_at_returns_none_on_bad_input(ent, bad):
    assert (
        ent.next_tier_capacity_headroom_at(
            bad, channels=10, retention_days=5, nodes=2
        )
        is None
    )


def test_next_headroom_at_trims_and_lowercases(ent):
    assert ent.next_tier_capacity_headroom_at(
        "  OSS  ", channels=10, retention_days=5, nodes=2
    ) == ent.capacity_headroom_at(
        ent.TIER_CLOUD_STARTER, channels=10, retention_days=5, nodes=2
    )


def test_next_headroom_at_trial_source_resolves_to_enterprise(ent):
    body = ent.next_tier_capacity_headroom_at(
        ent.TIER_TRIAL, channels=10, retention_days=5, nodes=2
    )
    assert body is not None
    assert body["tier"] == ent.TIER_ENTERPRISE


def test_next_headroom_at_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.next_tier_capacity_headroom_at(
        ent.TIER_CLOUD_STARTER, channels=10, retention_days=5, nodes=2
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_capacity_headroom_at(
        ent.TIER_CLOUD_STARTER, channels=10, retention_days=5, nodes=2
    )
    assert enforce == grace


def test_next_headroom_at_never_raises(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "capacity_headroom_at",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert (
        ent.next_tier_capacity_headroom_at(
            ent.TIER_OSS, channels=10, retention_days=5, nodes=2
        )
        is None
    )


def test_next_headroom_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.next_tier_capacity_headroom_at(
        ent.TIER_OSS, channels=10, retention_days=5, nodes=2
    )
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


def test_next_headroom_at_axis_none_when_unsupplied(ent):
    body = ent.next_tier_capacity_headroom_at(ent.TIER_OSS)
    assert body is not None
    for axis in ("channels", "retention_days", "nodes"):
        assert body[axis] is None


def test_next_headroom_at_axis_supplied_row_populated(ent):
    body = ent.next_tier_capacity_headroom_at(ent.TIER_OSS, channels=25)
    assert body is not None
    assert body["channels"] is not None
    assert body["channels"]["kind"] == "channels"
    assert body["channels"]["used"] == 25
    assert body["retention_days"] is None
    assert body["nodes"] is None


# ── previous_tier_capacity_headroom_at ────────────────────────────────────────


def test_prev_headroom_at_matches_explicit_composition(ent):
    for name in _PREV_SOURCES:
        src = getattr(ent, name)
        prv = ent._previous_purchasable_tier_before(src)
        assert prv is not None, src
        assert ent.previous_tier_capacity_headroom_at(
            src, channels=10, retention_days=5, nodes=2
        ) == ent.capacity_headroom_at(
            prv, channels=10, retention_days=5, nodes=2
        ), src


def test_prev_headroom_at_returns_none_at_floor(ent):
    assert (
        ent.previous_tier_capacity_headroom_at(
            ent.TIER_OSS, channels=10, retention_days=5, nodes=2
        )
        is None
    )
    assert (
        ent.previous_tier_capacity_headroom_at(
            ent.TIER_CLOUD_FREE, channels=10, retention_days=5, nodes=2
        )
        is None
    )


def test_prev_headroom_at_envelope_shape(ent):
    body = ent.previous_tier_capacity_headroom_at(
        ent.TIER_ENTERPRISE, channels=10, retention_days=5, nodes=2
    )
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    for axis in ("channels", "retention_days", "nodes"):
        assert body[axis] is not None
        assert set(body[axis].keys()) == _HEADROOM_ROW_KEYS


@pytest.mark.parametrize("bad", ["", "  ", None, 0, 1.5, "BOGUS", "bogus"])
def test_prev_headroom_at_returns_none_on_bad_input(ent, bad):
    assert (
        ent.previous_tier_capacity_headroom_at(
            bad, channels=10, retention_days=5, nodes=2
        )
        is None
    )


def test_prev_headroom_at_trims_and_lowercases(ent):
    assert ent.previous_tier_capacity_headroom_at(
        "  CLOUD_STARTER  ", channels=10, retention_days=5, nodes=2
    ) == ent.capacity_headroom_at(
        ent.TIER_OSS, channels=10, retention_days=5, nodes=2
    )


def test_prev_headroom_at_trial_source_resolves_to_cloud_starter(ent):
    body = ent.previous_tier_capacity_headroom_at(
        ent.TIER_TRIAL, channels=10, retention_days=5, nodes=2
    )
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


def test_prev_headroom_at_grace_and_enforce_match(ent, monkeypatch):
    grace = ent.previous_tier_capacity_headroom_at(
        ent.TIER_CLOUD_PRO, channels=10, retention_days=5, nodes=2
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.previous_tier_capacity_headroom_at(
        ent.TIER_CLOUD_PRO, channels=10, retention_days=5, nodes=2
    )
    assert enforce == grace


def test_prev_headroom_at_never_raises(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "capacity_headroom_at",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert (
        ent.previous_tier_capacity_headroom_at(
            ent.TIER_ENTERPRISE, channels=10, retention_days=5, nodes=2
        )
        is None
    )


def test_prev_headroom_at_independent_of_resolver(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("resolver must not be reached")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    body = ent.previous_tier_capacity_headroom_at(
        ent.TIER_ENTERPRISE, channels=10, retention_days=5, nodes=2
    )
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_PRO


def test_prev_headroom_at_axis_none_when_unsupplied(ent):
    body = ent.previous_tier_capacity_headroom_at(ent.TIER_ENTERPRISE)
    assert body is not None
    for axis in ("channels", "retention_days", "nodes"):
        assert body[axis] is None


# ── /api/entitlement/next-tier-capacity-headroom-at ───────────────────────────


def _json(client, url):
    resp = client.get(url)
    return resp.status_code, resp.get_json()


def test_endpoint_next_missing_tier_returns_400(client):
    status, body = _json(client, "/api/entitlement/next-tier-capacity-headroom-at")
    assert status == 400
    assert body == {"error": "missing tier"}


def test_endpoint_next_unknown_tier_returns_404(client):
    status, body = _json(
        client,
        "/api/entitlement/next-tier-capacity-headroom-at?tier=bogus",
    )
    assert status == 404
    assert body == {"error": "unknown tier", "which": "tier", "tier": "bogus"}


def test_endpoint_next_envelope_shape(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/next-tier-capacity-headroom-at"
        "?tier=oss&channels=10&retention_days=5&nodes=2",
    )
    assert status == 200
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["target_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["target_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert body["direction"] == "upgrade"
    assert body["headroom"] is not None
    for axis in ("channels", "retention_days", "nodes"):
        assert set(body["headroom"][axis].keys()) == _HEADROOM_ROW_KEYS


def test_endpoint_next_ceiling_stays_200_with_null_target(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/next-tier-capacity-headroom-at?tier=enterprise&channels=10",
    )
    assert status == 200
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["direction"] == "upgrade"
    assert body["headroom"] is None


def test_endpoint_next_matches_singular_capacity_headroom_at(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/next-tier-capacity-headroom-at"
        "?tier=cloud_starter&channels=100&retention_days=30&nodes=5",
    )
    assert status == 200
    # The endpoint must byte-equal /api/entitlement/capacity-headroom-at
    # for the resolved neighbour target so the two surfaces cannot drift.
    _, singular = _json(
        client,
        "/api/entitlement/capacity-headroom-at"
        "?tier=cloud_pro&channels=100&retention_days=30&nodes=5",
    )
    assert body["headroom"] == singular


def test_endpoint_next_trial_source_resolves_to_enterprise(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/next-tier-capacity-headroom-at?tier=trial&channels=10",
    )
    assert status == 200
    assert body["tier"] == ent.TIER_TRIAL
    assert body["target"] == ent.TIER_ENTERPRISE
    assert body["headroom"] is not None
    assert body["headroom"]["tier"] == ent.TIER_ENTERPRISE


def test_endpoint_next_bad_axis_short_circuits_to_none(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/next-tier-capacity-headroom-at"
        "?tier=oss&channels=abc&retention_days=&nodes=-1",
    )
    assert status == 200
    assert body["headroom"] is not None
    for axis in ("channels", "retention_days", "nodes"):
        assert body["headroom"][axis] is None


def test_endpoint_next_never_5xxs_on_builder_crash(client, ent, monkeypatch):
    from clawmetry import entitlements as _ent

    monkeypatch.setattr(
        _ent,
        "next_tier_capacity_headroom_at",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    status, body = _json(
        client,
        "/api/entitlement/next-tier-capacity-headroom-at?tier=oss&channels=10",
    )
    assert status == 200
    assert body["headroom"] is None
    assert body["direction"] == "upgrade"


def test_endpoint_next_case_and_whitespace_normalised(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/next-tier-capacity-headroom-at?tier=%20OSS%20&channels=10",
    )
    assert status == 200
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent.TIER_CLOUD_STARTER


# ── /api/entitlement/previous-tier-capacity-headroom-at ───────────────────────


def test_endpoint_prev_missing_tier_returns_400(client):
    status, body = _json(
        client, "/api/entitlement/previous-tier-capacity-headroom-at"
    )
    assert status == 400
    assert body == {"error": "missing tier"}


def test_endpoint_prev_unknown_tier_returns_404(client):
    status, body = _json(
        client,
        "/api/entitlement/previous-tier-capacity-headroom-at?tier=bogus",
    )
    assert status == 404
    assert body == {"error": "unknown tier", "which": "tier", "tier": "bogus"}


def test_endpoint_prev_envelope_shape(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/previous-tier-capacity-headroom-at"
        "?tier=enterprise&channels=10&retention_days=5&nodes=2",
    )
    assert status == 200
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["direction"] == "downgrade"
    assert body["headroom"] is not None
    for axis in ("channels", "retention_days", "nodes"):
        assert set(body["headroom"][axis].keys()) == _HEADROOM_ROW_KEYS


def test_endpoint_prev_floor_stays_200_with_null_target(client, ent):
    for floor in ("oss", "cloud_free"):
        status, body = _json(
            client,
            f"/api/entitlement/previous-tier-capacity-headroom-at?tier={floor}&channels=10",
        )
        assert status == 200, floor
        assert body["target"] is None, floor
        assert body["target_label"] is None, floor
        assert body["target_rank"] is None, floor
        assert body["direction"] == "downgrade", floor
        assert body["headroom"] is None, floor


def test_endpoint_prev_matches_singular_capacity_headroom_at(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/previous-tier-capacity-headroom-at"
        "?tier=cloud_pro&channels=100&retention_days=30&nodes=5",
    )
    assert status == 200
    _, singular = _json(
        client,
        "/api/entitlement/capacity-headroom-at"
        "?tier=cloud_starter&channels=100&retention_days=30&nodes=5",
    )
    assert body["headroom"] == singular


def test_endpoint_prev_trial_source_resolves_to_cloud_starter(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/previous-tier-capacity-headroom-at?tier=trial&channels=10",
    )
    assert status == 200
    assert body["tier"] == ent.TIER_TRIAL
    assert body["target"] == ent.TIER_CLOUD_STARTER


def test_endpoint_prev_bad_axis_short_circuits_to_none(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/previous-tier-capacity-headroom-at"
        "?tier=enterprise&channels=abc&retention_days=&nodes=-1",
    )
    assert status == 200
    assert body["headroom"] is not None
    for axis in ("channels", "retention_days", "nodes"):
        assert body["headroom"][axis] is None


def test_endpoint_prev_never_5xxs_on_builder_crash(client, ent, monkeypatch):
    from clawmetry import entitlements as _ent

    monkeypatch.setattr(
        _ent,
        "previous_tier_capacity_headroom_at",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    status, body = _json(
        client,
        "/api/entitlement/previous-tier-capacity-headroom-at"
        "?tier=enterprise&channels=10",
    )
    assert status == 200
    assert body["headroom"] is None
    assert body["direction"] == "downgrade"


def test_endpoint_prev_case_and_whitespace_normalised(client, ent):
    status, body = _json(
        client,
        "/api/entitlement/previous-tier-capacity-headroom-at"
        "?tier=%20ENTERPRISE%20&channels=10",
    )
    assert status == 200
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["target"] == ent.TIER_CLOUD_PRO


# ── cross-family parity ───────────────────────────────────────────────────────


def test_next_headroom_at_target_matches_diff_at_target(ent):
    """The neighbour headroom_at scalar and neighbour diff_at scalar
    must resolve to the same source-anchored "next above" target so a
    pricing-comparison cell can bind both surfaces off one column
    identifier."""
    for name in _NEXT_SOURCES:
        src = getattr(ent, name)
        diff = ent.next_tier_capacity_diff_at(src)
        headroom = ent.next_tier_capacity_headroom_at(src, channels=10)
        assert diff is not None and headroom is not None, src
        assert headroom["tier"] == diff["target"], src


def test_prev_headroom_at_target_matches_diff_at_target(ent):
    for name in _PREV_SOURCES:
        src = getattr(ent, name)
        diff = ent.previous_tier_capacity_diff_at(src)
        headroom = ent.previous_tier_capacity_headroom_at(src, channels=10)
        assert diff is not None and headroom is not None, src
        assert headroom["tier"] == diff["target"], src


def test_endpoint_next_envelope_source_metadata_matches_diff_at_endpoint(
    client, ent
):
    """The source-side metadata (``tier`` / ``tier_label`` / ``tier_rank``
    / ``target`` / ``target_label`` / ``target_rank``) must byte-equal
    what ``/api/entitlement/next-tier-capacity-diff-at`` publishes for
    the same source, so a UI can fold both surfaces into one pricing-
    comparison cell without re-keying."""
    _, headroom_env = _json(
        client,
        "/api/entitlement/next-tier-capacity-headroom-at?tier=cloud_starter",
    )
    _, diff_env = _json(
        client,
        "/api/entitlement/next-tier-capacity-diff-at?tier=cloud_starter",
    )
    for key in (
        "tier",
        "tier_label",
        "tier_rank",
        "target",
        "target_label",
        "target_rank",
    ):
        assert headroom_env[key] == diff_env[key], key


def test_endpoint_prev_envelope_source_metadata_matches_diff_at_endpoint(
    client, ent
):
    _, headroom_env = _json(
        client,
        "/api/entitlement/previous-tier-capacity-headroom-at?tier=cloud_pro",
    )
    _, diff_env = _json(
        client,
        "/api/entitlement/previous-tier-capacity-diff-at?tier=cloud_pro",
    )
    for key in (
        "tier",
        "tier_label",
        "tier_rank",
        "target",
        "target_label",
        "target_rank",
    ):
        assert headroom_env[key] == diff_env[key], key
