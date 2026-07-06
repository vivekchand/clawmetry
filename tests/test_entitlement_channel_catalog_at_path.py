"""Tests for ``clawmetry.entitlements.channel_catalog_at_path`` +
its HTTP endpoint ``GET /api/entitlement/channel-catalog-at-path``.

Path-shaped what-if sibling of :func:`channel_catalog_path`: renders
the FULL per-rung channel-catalog path between two tiers from a
hypothetical ``perspective_tier`` in ONE round-trip. Fills the
``_at_path`` slot for the channel-catalog family (alongside
:func:`channel_catalog_at` and :func:`channel_catalog_at_batch` which
fill the scalar-what-if and batch-what-if slots) so a pricing-
comparison walkthrough surface can call
``X_at_path(perspective, from, to)`` uniformly across every
``_at_path`` family member on all four axes (feature / runtime /
channel / tier).

Pins:

* body byte-identical to :func:`channel_catalog_path` for every
  perspective -- the perspective is validated but does NOT shape the
  rows (parity with every other ``_at_path`` helper the
  ``feature_catalog_at_path`` / ``runtime_catalog_at_path`` /
  ``tier_catalog_at_path`` family ships).
* per-rung row shape carries the same 4 keys as
  :func:`channel_catalog_path` (``tier``, ``tier_label``,
  ``tier_rank``, ``channels``); each inner ``channels`` list byte-
  equals :func:`channel_catalog()` -- the "channels are always free
  at every tier" invariant is inherited from the delegate and pinned
  here so the ``_at`` / ``_at_path`` / ``_at_batch`` /
  ``_at_path_batch`` channel-catalog surfaces cannot drift.
* ``trial`` accepted as perspective and as endpoint (matching every
  other ``_at`` sibling's lenient posture, unlike
  :func:`channel_catalog_path` which excludes trial from the walked
  intermediate rungs but accepts it as an endpoint via the lateral /
  identity branches).
* case + whitespace normalisation on perspective, from, to.
* helper is decoupled from the resolver -- grace vs enforce yields
  byte-identical rows.
* unknown / empty / garbage ids return ``None`` and never raise;
  a delegate crash short-circuits to ``None`` and logs a warning.
* API: 400 on missing args, 404 with ``which: "tier" | "from" |
  "to"`` on unknown ids, 200 with the standard resolver-context tail
  every ``_at*`` endpoint carries.
"""
from __future__ import annotations

import importlib

import pytest


_ROW_KEYS = {"tier", "tier_label", "tier_rank", "channels"}
_SCALAR_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "path",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


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
def enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(ent):
    from flask import Flask

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


def _all_tiers(mod):
    return [
        mod.TIER_OSS,
        mod.TIER_CLOUD_FREE,
        mod.TIER_TRIAL,
        mod.TIER_CLOUD_STARTER,
        mod.TIER_CLOUD_PRO,
        mod.TIER_PRO,
        mod.TIER_ENTERPRISE,
    ]


# ── helper: shape + happy path ───────────────────────────────────────────


def test_helper_returns_list(ent):
    path = ent.channel_catalog_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    assert isinstance(path, list)
    assert len(path) >= 1


def test_helper_each_row_has_expected_shape(ent):
    path = ent.channel_catalog_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == _ROW_KEYS
        assert isinstance(row["tier"], str)
        assert isinstance(row["tier_label"], str)
        assert isinstance(row["tier_rank"], int)
        assert isinstance(row["channels"], list)


def test_helper_identity_yields_empty(ent):
    for tid in _all_tiers(ent):
        assert ent.channel_catalog_at_path(ent.TIER_CLOUD_PRO, tid, tid) == []


def test_helper_lateral_yields_single_row(ent):
    """Lateral (same rank, different id) yields a one-row path."""
    path = ent.channel_catalog_at_path(
        ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_PRO
    )
    assert isinstance(path, list)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_PRO


def test_helper_upgrade_direction_walks_rungs(ent):
    path = ent.channel_catalog_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    ranks = [r["tier_rank"] for r in path]
    assert ranks == sorted(ranks)


def test_helper_downgrade_direction_walks_rungs(ent):
    path = ent.channel_catalog_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE, ent.TIER_OSS
    )
    ranks = [r["tier_rank"] for r in path]
    assert ranks == sorted(ranks, reverse=True)


# ── helper: byte-parity with channel_catalog_path ────────────────────────


def test_helper_body_parity_with_channel_catalog_path(ent):
    """Body byte-identical to ``channel_catalog_path(from, to)`` for every
    ``(perspective, from, to)`` triple in ``ALL_TIERS × ALL_TIERS ×
    ALL_TIERS`` -- the perspective is validated but does NOT shape rows.
    """
    tiers = _all_tiers(ent)
    for p in tiers:
        for f in tiers:
            for t in tiers:
                got = ent.channel_catalog_at_path(p, f, t)
                want = ent.channel_catalog_path(f, t)
                assert got == want, (p, f, t)


def test_helper_perspective_invariance(ent):
    """Two different perspectives yield byte-identical rows."""
    tiers = _all_tiers(ent)
    for f in tiers:
        for t in tiers:
            a = ent.channel_catalog_at_path(ent.TIER_OSS, f, t)
            b = ent.channel_catalog_at_path(ent.TIER_ENTERPRISE, f, t)
            assert a == b, (f, t)


def test_helper_per_rung_channels_matches_channel_catalog(ent):
    """Each per-rung ``channels`` list byte-equals ``channel_catalog()``
    (the "channels always free at every tier" invariant, inherited
    from :func:`channel_catalog_path`)."""
    baseline = ent.channel_catalog()
    path = ent.channel_catalog_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    assert path
    for row in path:
        assert row["channels"] == baseline


def test_helper_channel_list_invariant_across_all_walks(ent):
    """Every rung across every walk carries the same channels list."""
    baseline = ent.channel_catalog()
    tiers = _all_tiers(ent)
    for p in tiers:
        for f in tiers:
            for t in tiers:
                path = ent.channel_catalog_at_path(p, f, t)
                if not path:
                    continue
                for row in path:
                    assert row["channels"] == baseline


# ── helper: trial + endpoint acceptance ──────────────────────────────────


def test_helper_trial_accepted_as_perspective(ent):
    """Perspective acceptance is lenient: trial IS accepted."""
    got = ent.channel_catalog_at_path(
        ent.TIER_TRIAL, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    assert isinstance(got, list)
    assert got == ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)


def test_helper_trial_accepted_as_endpoint(ent):
    """Trial IS accepted as from or to via the lateral / identity branch."""
    got = ent.channel_catalog_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_TRIAL, ent.TIER_TRIAL
    )
    assert got == []
    lateral = ent.channel_catalog_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_TRIAL, ent.TIER_CLOUD_FREE
    )
    assert isinstance(lateral, list)


# ── helper: unknown / normalisation / robustness ─────────────────────────


def test_helper_unknown_perspective_returns_none(ent):
    assert ent.channel_catalog_at_path("bogus", ent.TIER_OSS, ent.TIER_ENTERPRISE) is None


def test_helper_unknown_from_returns_none(ent):
    assert ent.channel_catalog_at_path(ent.TIER_CLOUD_PRO, "bogus", ent.TIER_ENTERPRISE) is None


def test_helper_unknown_to_returns_none(ent):
    assert ent.channel_catalog_at_path(ent.TIER_CLOUD_PRO, ent.TIER_OSS, "bogus") is None


def test_helper_none_perspective_returns_none(ent):
    assert ent.channel_catalog_at_path(None, ent.TIER_OSS, ent.TIER_ENTERPRISE) is None


def test_helper_empty_perspective_returns_none(ent):
    assert ent.channel_catalog_at_path("", ent.TIER_OSS, ent.TIER_ENTERPRISE) is None
    assert ent.channel_catalog_at_path("   ", ent.TIER_OSS, ent.TIER_ENTERPRISE) is None


def test_helper_case_and_whitespace_normalised(ent):
    """Case + whitespace on perspective, from, to are all normalised."""
    got = ent.channel_catalog_at_path(
        "  Cloud_Pro  ", "  OSS  ", "  ENTERPRISE  "
    )
    want = ent.channel_catalog_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    assert got == want


def test_helper_never_raises_on_weird_types(ent):
    """Garbage inputs return None, never raise."""
    for bad_p in (123, 4.5, [], {}, object()):
        assert ent.channel_catalog_at_path(bad_p, ent.TIER_OSS, ent.TIER_ENTERPRISE) is None


def test_helper_grace_vs_enforce_identical(ent, enforced):
    """Grace vs enforce yields byte-identical rows."""
    tiers = _all_tiers(ent)
    for p in tiers:
        for f in tiers:
            for t in tiers:
                a = ent.channel_catalog_at_path(p, f, t)
                b = enforced.channel_catalog_at_path(p, f, t)
                assert a == b, (p, f, t)


def test_helper_delegate_crash_returns_none(ent, monkeypatch):
    """A crash inside :func:`channel_catalog_path` short-circuits to
    ``None`` instead of propagating."""
    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "channel_catalog_path", _boom)
    got = ent.channel_catalog_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    assert got is None


# ── HTTP scalar ──────────────────────────────────────────────────────────


def test_http_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list)
    assert body["path"]
    for row in body["path"]:
        assert set(row.keys()) == _ROW_KEYS


def test_http_missing_tier_400(client):
    r = client.get("/api/entitlement/channel-catalog-at-path?from=oss&to=enterprise")
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_http_missing_from_400(client):
    r = client.get("/api/entitlement/channel-catalog-at-path?tier=cloud_pro&to=enterprise")
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing from"


def test_http_missing_to_400(client):
    r = client.get("/api/entitlement/channel-catalog-at-path?tier=cloud_pro&from=oss")
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing to"


def test_http_unknown_tier_which_key(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path?tier=bogus&from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_http_unknown_from_which_key(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path?tier=cloud_pro&from=bogus&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "from"
    assert body["from"] == "bogus"


def test_http_unknown_to_which_key(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path?tier=cloud_pro&from=oss&to=bogus"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "to"
    assert body["to"] == "bogus"


def test_http_trial_accepted_as_perspective(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path"
        f"?tier={ent.TIER_TRIAL}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_TRIAL


def test_http_identity_path_empty(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path?tier=cloud_pro&from=oss&to=oss"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_http_downgrade_direction(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path"
        "?tier=cloud_pro&from=enterprise&to=oss"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    ranks = [row["tier_rank"] for row in body["path"]]
    assert ranks == sorted(ranks, reverse=True)


def test_http_lateral_direction(client):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path"
        "?tier=cloud_starter&from=cloud_pro&to=pro"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1


def test_http_case_and_whitespace_normalised(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path"
        "?tier=%20Cloud_Pro%20&from=%20OSS%20&to=%20ENTERPRISE%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE


def test_http_body_parity_with_channel_catalog_path(client, ent):
    """Wire body's ``path`` byte-equals ``/channel-catalog-path?from&to``
    for the same ``(from, to)`` pair."""
    r_at = client.get(
        "/api/entitlement/channel-catalog-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    r_bare = client.get(
        "/api/entitlement/channel-catalog-path"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r_at.status_code == 200
    assert r_bare.status_code == 200
    assert r_at.get_json()["path"] == r_bare.get_json()["path"]


def test_http_perspective_invariance(client, ent):
    """Wire body's ``path`` is byte-identical across two perspectives."""
    r_a = client.get(
        "/api/entitlement/channel-catalog-at-path"
        f"?tier={ent.TIER_OSS}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    r_b = client.get(
        "/api/entitlement/channel-catalog-at-path"
        f"?tier={ent.TIER_ENTERPRISE}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r_a.status_code == 200
    assert r_b.status_code == 200
    assert r_a.get_json()["path"] == r_b.get_json()["path"]


def test_http_channel_list_invariant_across_rungs(client, ent):
    """Every rung's ``channels`` list is byte-equal to
    ``/channel-catalog`` (the "channels are always free" invariant
    inherited from the delegate)."""
    r = client.get(
        "/api/entitlement/channel-catalog-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    r_bare = client.get("/api/entitlement/channel-catalog")
    assert r.status_code == 200
    assert r_bare.status_code == 200
    baseline = r_bare.get_json()["channels"]
    for row in r.get_json()["path"]:
        assert row["channels"] == baseline


def test_http_carries_resolver_context_tail(client, ent):
    r = client.get(
        "/api/entitlement/channel-catalog-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


def test_http_never_5xx_on_delegate_crash(client, ent, monkeypatch):
    """A crash inside the helper short-circuits to 404, not 5xx."""
    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "channel_catalog_at_path", _boom)
    r = client.get(
        "/api/entitlement/channel-catalog-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 404


def test_http_grace_vs_enforce_identical(client, ent, enforced):
    """Wire body's ``path`` is byte-identical across grace / enforce."""
    r_a = client.get(
        "/api/entitlement/channel-catalog-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r_a.status_code == 200

    from flask import Flask
    from routes.entitlement import bp_entitlement

    app_e = Flask(__name__)
    app_e.register_blueprint(bp_entitlement)
    client_e = app_e.test_client()
    r_b = client_e.get(
        "/api/entitlement/channel-catalog-at-path"
        f"?tier={enforced.TIER_CLOUD_PRO}&from={enforced.TIER_OSS}"
        f"&to={enforced.TIER_ENTERPRISE}"
    )
    assert r_b.status_code == 200
    assert r_a.get_json()["path"] == r_b.get_json()["path"]
