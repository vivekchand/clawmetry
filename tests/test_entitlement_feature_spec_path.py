"""Tests for ``clawmetry.entitlements.feature_spec_path(from, to, feature)``
+ the ``GET /api/entitlement/feature-spec-path`` endpoint.

Single-feature sibling of :func:`tier_spec_path` (full slim spec per
rung) and perspective-walked sibling of :func:`feature_spec_at`. Lets a
paywall "how does THIS one feature unlock as I climb the ladder" UI
render every rung's ``allowed`` / ``locked`` / ``entitled`` status off
ONE round-trip without fetching the full :func:`feature_catalog_at` at
every rung.

Pins:

* rung walk byte-stable against :func:`tier_path`,
  :func:`tier_spec_path`, :func:`capacity_diff_path`,
  :func:`tier_unlocks_path`, :func:`tier_locks_path` and
  :func:`preview_path` (same ``_PURCHASABLE_TIERS`` filter + same sort
  + same destination-sibling exclusion)
* per-rung row carries the singular :func:`feature_spec_at` body PLUS
  the three rung-identification keys (``rung``, ``rung_label``,
  ``rung_rank``); dropping the three ``rung*`` keys yields exact
  byte-equality with :func:`feature_spec_at(rung, feature)`
* static feature-property keys (``id``, ``label``, ``tier``, ``tiers``,
  ``free``, ``alias``) stay constant across all rows
* paid-feature unlock boundary visible: ``allowed`` flips from
  ``False`` to ``True`` at the rung where the feature's min tier is
  reached
* free feature surfaces ``allowed=True`` at every rung
* enterprise-only feature stays ``allowed=False`` until the enterprise
  rung
* identity returns ``[]``
* lateral (same rank, different id) returns a single-row path
* trial accepted as an endpoint (lateral branch for ``to=trial``;
  ``from=trial`` walks intermediate rungs above)
* unknown / empty / garbage tier or feature ids return ``None`` and
  never raise
* grace vs enforce yields identical rows (helper walks the static
  per-tier maps via :func:`feature_spec_at`)
* API surface: 400 on missing args, 404 on unknown ids, 200 envelope
  on happy path (incl. direction tag and ``feature`` echo)
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
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "feature",
    "path",
}

_RUNG_KEYS = {"rung", "rung_label", "rung_rank"}


# ── helper-level: shape + invariants ─────────────────────────────────────────


def test_returns_list(ent):
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts")
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_carries_rung_keys(ent):
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts")
    for row in path:
        assert set(row).issuperset(_RUNG_KEYS)
        assert row["rung_label"] == ent.tier_label(row["rung"])
        assert row["rung_rank"] == ent.tier_rank(row["rung"])


def test_per_rung_byte_equality_with_singular_feature_spec_at(ent):
    """Dropping the three ``rung*`` keys from a path row yields exact
    byte-equality with :func:`feature_spec_at(rung, feature)`."""
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts")
    for row in path:
        body = {k: v for k, v in row.items() if k not in _RUNG_KEYS}
        direct = ent.feature_spec_at(row["rung"], "custom_alerts")
        assert body == direct


def test_static_feature_property_keys_constant_across_rungs(ent):
    """``id``, ``label``, ``tier``, ``tiers``, ``free``, ``alias`` are
    feature-properties -- they must NOT vary rung by rung. Only the
    perspective-dependent fields (``allowed``, ``locked``, ``entitled``)
    can move."""
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts")
    static = {"id", "label", "tier", "tiers", "free", "alias"}
    first = {k: path[0][k] for k in static}
    for row in path[1:]:
        assert {k: row[k] for k in static} == first


def test_first_row_is_first_step_above_from(ent):
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts")
    assert path[0]["rung"] == ent.TIER_CLOUD_STARTER


def test_last_row_is_destination(ent):
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts")
    assert path[-1]["rung"] == ent.TIER_ENTERPRISE


def test_rung_walk_byte_stable_against_tier_spec_path(ent):
    """Rung ids must match :func:`tier_spec_path`'s rung ``id`` field
    byte-for-byte -- same ``_PURCHASABLE_TIERS`` filter + same sort +
    same destination-sibling exclusion."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_OSS, ent.TIER_CLOUD_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_PRO, ent.TIER_CLOUD_FREE),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        feat_rungs = [
            r["rung"] for r in ent.feature_spec_path(f, t, "custom_alerts")
        ]
        spec_rungs = [r["id"] for r in ent.tier_spec_path(f, t)]
        assert feat_rungs == spec_rungs


def test_rung_walk_byte_stable_against_tier_path(ent):
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        feat_rungs = [
            r["rung"] for r in ent.feature_spec_path(f, t, "custom_alerts")
        ]
        diff_rungs = [r["to"] for r in ent.tier_path(f, t)]
        assert feat_rungs == diff_rungs


def test_rung_walk_invariant_across_features(ent):
    """The walked rung sequence is feature-agnostic -- swapping the
    feature must not move the rungs."""
    a = [
        r["rung"]
        for r in ent.feature_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts"
        )
    ]
    b = [
        r["rung"]
        for r in ent.feature_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "sessions"
        )
    ]
    c = [
        r["rung"]
        for r in ent.feature_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "siem_export"
        )
    ]
    assert a == b == c


def test_paid_feature_unlock_boundary_visible(ent):
    """``custom_alerts`` is a Pro-only feature -- ``allowed`` must
    flip from ``False`` to ``True`` exactly at the cloud_pro rung."""
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts")
    by_rung = {row["rung"]: row for row in path}
    # cloud_starter rank 1: not yet unlocked
    assert by_rung[ent.TIER_CLOUD_STARTER]["allowed"] is False
    assert by_rung[ent.TIER_CLOUD_STARTER]["locked"] is True
    # cloud_pro / pro / enterprise: unlocked
    for rung in (ent.TIER_CLOUD_PRO, ent.TIER_PRO, ent.TIER_ENTERPRISE):
        assert by_rung[rung]["allowed"] is True
        assert by_rung[rung]["locked"] is False
        assert by_rung[rung]["entitled"] is True


def test_free_feature_allowed_at_every_rung(ent):
    """``sessions`` is a free feature -- ``allowed`` must be ``True``
    at every walked rung."""
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "sessions")
    for row in path:
        assert row["allowed"] is True
        assert row["locked"] is False
        assert row["entitled"] is True
        assert row["free"] is True


def test_enterprise_only_feature_locked_until_enterprise(ent):
    """``siem_export`` is enterprise-only -- ``allowed`` must stay
    ``False`` at every rung below enterprise and ``True`` at
    enterprise."""
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "siem_export")
    by_rung = {row["rung"]: row for row in path}
    for rung in (ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_PRO):
        assert by_rung[rung]["allowed"] is False
    assert by_rung[ent.TIER_ENTERPRISE]["allowed"] is True


def test_ascending_walk_is_non_decreasing_in_rank(ent):
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts")
    walk_ranks = [row["rung_rank"] for row in path]
    assert walk_ranks == sorted(walk_ranks)


def test_descending_walk_is_non_increasing_in_rank(ent):
    path = ent.feature_spec_path(ent.TIER_ENTERPRISE, ent.TIER_OSS, "custom_alerts")
    walk_ranks = [row["rung_rank"] for row in path]
    assert walk_ranks == sorted(walk_ranks, reverse=True)


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2 -- the path must end
    exactly at ``pro`` and exclude the same-rank sibling."""
    rungs = [
        r["rung"]
        for r in ent.feature_spec_path(ent.TIER_OSS, ent.TIER_PRO, "custom_alerts")
    ]
    assert rungs[-1] == ent.TIER_PRO
    assert ent.TIER_CLOUD_PRO not in rungs


def test_identity_returns_empty(ent):
    for tid in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        assert ent.feature_spec_path(tid, tid, "custom_alerts") == []


def test_lateral_single_row(ent):
    """``cloud_pro`` and ``pro`` share rank 2 -- lateral branch yields
    a one-row path."""
    path = ent.feature_spec_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO, "custom_alerts")
    assert len(path) == 1
    assert path[0]["rung"] == ent.TIER_PRO


def test_trial_endpoint_via_lateral(ent):
    path = ent.feature_spec_path(ent.TIER_CLOUD_PRO, ent.TIER_TRIAL, "custom_alerts")
    assert len(path) == 1
    assert path[0]["rung"] == ent.TIER_TRIAL


def test_trial_excluded_from_walked_intermediate_rungs(ent):
    path = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts")
    for row in path:
        assert row["rung"] != ent.TIER_TRIAL


def test_unknown_tier_returns_none(ent):
    assert (
        ent.feature_spec_path("not_a_tier", ent.TIER_ENTERPRISE, "custom_alerts")
        is None
    )
    assert (
        ent.feature_spec_path(ent.TIER_OSS, "still_not", "custom_alerts") is None
    )


def test_unknown_feature_returns_none(ent):
    assert (
        ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "not_a_feature")
        is None
    )
    assert ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.feature_spec_path("", "", "") is None
    assert ent.feature_spec_path(None, None, None) is None  # type: ignore[arg-type]
    assert ent.feature_spec_path("  ", "  ", "  ") is None
    assert ent.feature_spec_path(123, 456, 789) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.feature_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts")
    b = ent.feature_spec_path("  OSS ", " ENTERPRISE  ", "  CUSTOM_ALERTS ")
    assert a == b


def test_grace_and_enforce_yield_identical_rows(ent, monkeypatch):
    grace_rows = ent.feature_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_rows = ent.feature_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts"
    )
    assert grace_rows == enforced_rows


def test_resolver_failure_returns_none(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "feature_spec_at",
        lambda _t, _f: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    result = ent.feature_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts"
    )
    assert result is None


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_400_on_missing_from(client):
    r = client.get("/api/entitlement/feature-spec-path?to=cloud_pro&feature=sessions")
    assert r.status_code == 400


def test_api_400_on_missing_to(client):
    r = client.get("/api/entitlement/feature-spec-path?from=oss&feature=sessions")
    assert r.status_code == 400


def test_api_400_on_missing_feature(client):
    r = client.get("/api/entitlement/feature-spec-path?from=oss&to=enterprise")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "missing feature"


def test_api_404_on_unknown_tier(client):
    r = client.get(
        "/api/entitlement/feature-spec-path?from=oss&to=not_a_tier&feature=sessions"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier or feature"


def test_api_404_on_unknown_feature(client):
    r = client.get(
        "/api/entitlement/feature-spec-path?from=oss&to=enterprise&feature=bogus"
    )
    assert r.status_code == 404


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/feature-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["feature"] == "custom_alerts"
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["rung"] == ent.TIER_ENTERPRISE


def test_api_happy_path_descending(client, ent):
    r = client.get(
        f"/api/entitlement/feature-spec-path?from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS}&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["rung"] == ent.TIER_OSS


def test_api_identity_empty_path(client, ent):
    r = client.get(
        f"/api/entitlement/feature-spec-path?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO}&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        f"/api/entitlement/feature-spec-path?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_PRO}&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["rung"] == ent.TIER_PRO


def test_api_rungs_match_tier_spec_path_route(client, ent):
    """API-level byte-equality: rung ids from ``/feature-spec-path``
    match rung ids from ``/tier-spec-path``."""
    a = client.get(
        f"/api/entitlement/feature-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&feature=custom_alerts"
    ).get_json()
    b = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    assert [r["rung"] for r in a["path"]] == [r["id"] for r in b["path"]]
