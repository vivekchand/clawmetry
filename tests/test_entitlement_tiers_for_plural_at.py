"""Tests for ``clawmetry.entitlements.tiers_for_features_at`` /
``tiers_for_runtimes_at`` and the two matching HTTP endpoints.

Hypothetical-perspective siblings of :func:`tiers_for_features` /
:func:`tiers_for_runtimes`. Fills the ``_at`` slot on the plural
``tiers_for_*`` ladder axes alongside :func:`min_tier_for_features_at`
so a pricing-matrix walkthrough (``?tier=<p>``) can hit
``/tiers-for-features-at`` uniformly across the whole ``_at`` family
instead of falling back to per-item ``/tiers-for-at`` calls +
intersecting on the client.

These tests pin:

* perspective validation: empty / blank / ``None`` / non-string /
  unknown short-circuits to ``None`` on the helper and 400 / 404 on the
  endpoint
* trial accepted as perspective (matches the rest of the ``_at`` family)
* case-insensitive + whitespace-stripped perspective
* byte-parity vs the non-``_at`` sibling for every perspective in
  :data:`_TIER_ORDER` -- the ``_at`` prefix cannot silently drift into
  shaping the answer
* semantics inherited from the non-``_at`` sibling: empty iterable ->
  empty ladder shape (NOT ``None`` -- distinguishes "asked for nothing"
  from perspective-validation failure), unknown-only bundle -> empty
  ladder shape with ``unknown`` populated, mixed bundle -> intersection
  ladder + matching ``min_tier``
* runtime canonicalisation on the runtime helper
  (``claude-code`` -> ``claude_code``)
* grace vs enforce yields byte-identical results
* helpers never raise on a delegate crash (monkeypatched)
* API happy path: shape, envelope keys, perspective envelope, resolver
  envelope, ``kind``, ``count`` fields
* API error paths: 400 on missing / blank ``tier=`` or ``features=`` /
  ``runtimes=``, 404 on unknown ``tier=``
* all-unknown IS 200 with ``unknown`` populated and empty ``tiers`` list
  (not confused with "asked for nothing")
* CSV dedup / normalisation via the shared ``_parse_csv_arg`` helper
* cross-endpoint parity: the eight body keys
  (``items``/``unknown``/``kind``/``count``/``min_tier``/
  ``min_tier_label``/``min_tier_rank``/``tiers``) byte-equal
  ``/tiers-for-features?features=X`` for every perspective
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


# ── helpers: perspective validation ────────────────────────────────────────


@pytest.mark.parametrize("bad", ["", "   ", "bogus", "cloud_pro_typo"])
def test_helper_empty_or_unknown_perspective_returns_none(ent, bad):
    assert ent.tiers_for_features_at(bad, ["fleet"]) is None
    assert ent.tiers_for_runtimes_at(bad, ["claude_code"]) is None


def test_helper_none_perspective_returns_none(ent):
    assert ent.tiers_for_features_at(None, ["fleet"]) is None
    assert ent.tiers_for_runtimes_at(None, ["claude_code"]) is None


def test_helper_non_string_perspective_returns_none(ent):
    for bad in (object(), 123, ["cloud_pro"]):
        assert ent.tiers_for_features_at(bad, ["fleet"]) is None
        assert ent.tiers_for_runtimes_at(bad, ["claude_code"]) is None


def test_helper_perspective_is_case_insensitive(ent):
    assert (
        ent.tiers_for_features_at("CLOUD_PRO", ["fleet"])
        == ent.tiers_for_features(["fleet"])
    )
    assert (
        ent.tiers_for_runtimes_at("CLOUD_STARTER", ["claude_code"])
        == ent.tiers_for_runtimes(["claude_code"])
    )


def test_helper_perspective_is_whitespace_stripped(ent):
    assert (
        ent.tiers_for_features_at("  cloud_pro  ", ["fleet"])
        == ent.tiers_for_features(["fleet"])
    )
    assert (
        ent.tiers_for_runtimes_at("  cloud_starter  ", ["claude_code"])
        == ent.tiers_for_runtimes(["claude_code"])
    )


def test_helper_trial_is_accepted_as_perspective(ent):
    """Trial is in :data:`_TIER_ORDER` (non-purchasable but a valid
    hypothetical perspective across every ``_at`` sibling)."""
    assert (
        ent.tiers_for_features_at(ent.TIER_TRIAL, ["fleet"])
        == ent.tiers_for_features(["fleet"])
    )
    assert (
        ent.tiers_for_runtimes_at(ent.TIER_TRIAL, ["claude_code"])
        == ent.tiers_for_runtimes(["claude_code"])
    )


# ── helpers: byte-parity vs non-_at sibling for every perspective ──────────


def _every_perspective(ent):
    return list(ent._TIER_ORDER)


def test_helper_features_parity_across_all_perspectives(ent):
    bundles = [
        [],
        ["fleet"],
        ["fleet", "sso"],
        ["bogus"],
        ["fleet", "bogus"],
    ]
    for p in _every_perspective(ent):
        for bundle in bundles:
            assert ent.tiers_for_features_at(p, bundle) == ent.tiers_for_features(
                bundle
            ), f"perspective={p} bundle={bundle}"


def test_helper_runtimes_parity_across_all_perspectives(ent):
    bundles = [
        [],
        ["claude_code"],
        ["claude-code", "codex"],
        ["bogus"],
        ["claude_code", "bogus"],
    ]
    for p in _every_perspective(ent):
        for bundle in bundles:
            assert ent.tiers_for_runtimes_at(p, bundle) == ent.tiers_for_runtimes(
                bundle
            ), f"perspective={p} bundle={bundle}"


# ── helpers: inherited semantics ───────────────────────────────────────────


def test_helper_features_empty_iterable_returns_empty_shape(ent):
    body = ent.tiers_for_features_at(ent.TIER_CLOUD_PRO, [])
    assert body is not None
    assert body["items"] == []
    assert body["unknown"] == []
    assert body["kind"] == "features"
    assert body["count"] == 0
    assert body["min_tier"] is None
    assert body["tiers"] == []


def test_helper_runtimes_empty_iterable_returns_empty_shape(ent):
    body = ent.tiers_for_runtimes_at(ent.TIER_CLOUD_PRO, [])
    assert body is not None
    assert body["items"] == []
    assert body["kind"] == "runtimes"
    assert body["min_tier"] is None
    assert body["tiers"] == []


def test_helper_features_none_iterable_returns_none(ent):
    assert ent.tiers_for_features_at(ent.TIER_CLOUD_PRO, None) is None
    assert ent.tiers_for_runtimes_at(ent.TIER_CLOUD_PRO, None) is None


def test_helper_features_all_unknown_populates_unknown(ent):
    body = ent.tiers_for_features_at(
        ent.TIER_CLOUD_PRO, ["bogus1", "bogus2"]
    )
    assert body is not None
    assert body["items"] == []
    assert set(body["unknown"]) == {"bogus1", "bogus2"}
    assert body["tiers"] == []
    assert body["min_tier"] is None


def test_helper_runtimes_all_unknown_populates_unknown(ent):
    body = ent.tiers_for_runtimes_at(
        ent.TIER_CLOUD_PRO, ["bogus1", "bogus2"]
    )
    assert body is not None
    assert body["items"] == []
    assert body["tiers"] == []
    assert body["min_tier"] is None


def test_helper_features_non_iterable_returns_none(ent):
    assert ent.tiers_for_features_at(ent.TIER_CLOUD_PRO, 42) is None
    assert ent.tiers_for_runtimes_at(ent.TIER_CLOUD_PRO, 42) is None


def test_helper_runtimes_at_matches_non_at_on_canonical_id(ent):
    """The runtime helper delegates to :func:`tiers_for_runtimes`
    unchanged; canonical ids resolve to the paid-runtime tier ladder."""
    got = ent.tiers_for_runtimes_at(ent.TIER_CLOUD_PRO, ["claude_code"])
    assert got == ent.tiers_for_runtimes(["claude_code"])
    assert got is not None
    # claude_code is a paid runtime -- not every tier grants it
    assert got["min_tier"] is not None
    assert got["min_tier"] != ent.TIER_OSS


def test_helper_runtimes_at_canonicalises_alias(ent):
    """``claude-code`` -> ``claude_code`` before intersection, matching
    the non-``_at`` sibling's behaviour."""
    got = ent.tiers_for_runtimes_at(ent.TIER_CLOUD_PRO, ["claude-code"])
    assert got is not None
    assert got["items"] == ["claude_code"]


# ── helpers: grace vs enforce parity ───────────────────────────────────────


def test_helper_features_grace_vs_enforce_identical(ent, monkeypatch):
    grace = ent.tiers_for_features_at(ent.TIER_CLOUD_PRO, ["fleet", "sso"])
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    enforce = ent.tiers_for_features_at(ent.TIER_CLOUD_PRO, ["fleet", "sso"])
    assert grace == enforce


def test_helper_runtimes_grace_vs_enforce_identical(ent, monkeypatch):
    grace = ent.tiers_for_runtimes_at(ent.TIER_CLOUD_PRO, ["claude_code"])
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    enforce = ent.tiers_for_runtimes_at(ent.TIER_CLOUD_PRO, ["claude_code"])
    assert grace == enforce


# ── helpers: never-raises contract ─────────────────────────────────────────


def test_helper_features_never_raises_on_delegate_crash(ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "tiers_for_features", _boom)
    assert (
        ent.tiers_for_features_at(ent.TIER_CLOUD_PRO, ["fleet"]) is None
    )


def test_helper_runtimes_never_raises_on_delegate_crash(ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "tiers_for_runtimes", _boom)
    assert (
        ent.tiers_for_runtimes_at(ent.TIER_CLOUD_PRO, ["claude_code"])
        is None
    )


# ── API: happy path ───────────────────────────────────────────────────────


_BODY_KEYS = {
    "items",
    "unknown",
    "kind",
    "count",
    "min_tier",
    "min_tier_label",
    "min_tier_rank",
    "tiers",
}

_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


def test_api_features_at_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=cloud_pro&features=fleet,sso"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _BODY_KEYS | _ENVELOPE_KEYS
    assert j["kind"] == "features"
    assert j["items"] == ["fleet", "sso"]
    assert j["unknown"] == []
    assert j["count"] == 2
    assert j["perspective_tier"] == "cloud_pro"
    assert j["perspective_tier_label"] == ent.tier_label("cloud_pro")
    assert j["perspective_tier_rank"] == ent.tier_rank("cloud_pro")
    assert j["min_tier"] == ent.min_tier_for_features(["fleet", "sso"])


def test_api_runtimes_at_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=cloud_starter&runtimes=claude-code,codex"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _BODY_KEYS | _ENVELOPE_KEYS
    assert j["kind"] == "runtimes"
    assert j["items"] == ["claude_code", "codex"]  # canonicalised
    assert j["unknown"] == []
    assert j["perspective_tier"] == "cloud_starter"
    assert j["min_tier"] == ent.min_tier_for_runtimes(
        ["claude_code", "codex"]
    )


def test_api_features_at_case_insensitive_tier(client):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=CLOUD_PRO&features=fleet"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "cloud_pro"


def test_api_runtimes_at_case_insensitive_tier(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=CLOUD_STARTER&runtimes=claude_code"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "cloud_starter"


def test_api_features_at_trial_perspective_accepted(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=trial&features=fleet"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "trial"


def test_api_runtimes_at_trial_perspective_accepted(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=trial&runtimes=claude_code"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "trial"


# ── API: error paths ──────────────────────────────────────────────────────


def test_api_features_at_missing_tier_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?features=fleet"
    )
    assert r.status_code == 400


def test_api_runtimes_at_missing_tier_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?runtimes=claude_code"
    )
    assert r.status_code == 400


def test_api_features_at_blank_tier_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=%20%20&features=fleet"
    )
    assert r.status_code == 400


def test_api_runtimes_at_blank_tier_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=%20%20&runtimes=claude_code"
    )
    assert r.status_code == 400


def test_api_features_at_missing_features_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=cloud_pro"
    )
    assert r.status_code == 400


def test_api_runtimes_at_missing_runtimes_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=cloud_pro"
    )
    assert r.status_code == 400


def test_api_features_at_blank_features_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=cloud_pro&features=%20%20"
    )
    assert r.status_code == 400


def test_api_runtimes_at_blank_runtimes_returns_400(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=cloud_pro&runtimes=%20%20"
    )
    assert r.status_code == 400


def test_api_features_at_unknown_tier_returns_404(client):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=bogus&features=fleet"
    )
    assert r.status_code == 404
    j = r.get_json()
    assert j.get("which") == "tier"


def test_api_runtimes_at_unknown_tier_returns_404(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=bogus&runtimes=claude_code"
    )
    assert r.status_code == 404
    j = r.get_json()
    assert j.get("which") == "tier"


# ── API: all-unknown IS 200 ────────────────────────────────────────────────


def test_api_features_at_all_unknown_is_200(client):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=cloud_pro&features=bogus1,bogus2"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["items"] == []
    assert set(j["unknown"]) == {"bogus1", "bogus2"}
    assert j["min_tier"] is None
    assert j["count"] == 0
    assert j["tiers"] == []


def test_api_runtimes_at_all_unknown_is_200(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=cloud_pro&runtimes=bogus1,bogus2"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["items"] == []
    assert j["min_tier"] is None
    assert j["count"] == 0
    assert j["tiers"] == []


# ── API: CSV normalisation / dedup ─────────────────────────────────────────


def test_api_features_at_dedup_preserves_order(client):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=cloud_pro&features=fleet,,sso,fleet"
    )
    assert r.status_code == 200
    assert r.get_json()["items"] == ["fleet", "sso"]


def test_api_runtimes_at_dedup_preserves_order(client):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=cloud_pro&runtimes=claude-code,,codex,claude_code"
    )
    assert r.status_code == 200
    assert r.get_json()["items"] == ["claude_code", "codex"]


def test_api_features_at_mixed_known_unknown(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=cloud_pro&features=fleet,bogus"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["items"] == ["fleet"]
    assert j["unknown"] == ["bogus"]
    assert j["min_tier"] == ent.min_tier_for_features(["fleet"])


# ── API: cross-endpoint byte-parity with non-_at sibling ───────────────────


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_api_features_at_body_byte_equals_non_at_endpoint(
    client, perspective
):
    """The eight body keys (``items`` / ``unknown`` / ``kind`` /
    ``count`` / ``min_tier`` / ``min_tier_label`` / ``min_tier_rank`` /
    ``tiers``) byte-equal ``/tiers-for-features?features=<same>`` for
    every perspective -- the ``_at`` prefix cannot silently drift into
    shaping the ladder."""
    at = client.get(
        f"/api/entitlement/tiers-for-features-at?tier={perspective}&features=fleet,sso"
    )
    non_at = client.get(
        "/api/entitlement/tiers-for-features?features=fleet,sso"
    )
    assert at.status_code == 200
    assert non_at.status_code == 200
    at_body = {k: at.get_json()[k] for k in _BODY_KEYS}
    non_at_body = {k: non_at.get_json()[k] for k in _BODY_KEYS}
    assert at_body == non_at_body, (
        f"perspective={perspective} shaped the ladder -- "
        f"_at prefix must not shape rows"
    )


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_api_runtimes_at_body_byte_equals_non_at_endpoint(
    client, perspective
):
    at = client.get(
        f"/api/entitlement/tiers-for-runtimes-at?tier={perspective}&runtimes=claude_code,codex"
    )
    non_at = client.get(
        "/api/entitlement/tiers-for-runtimes?runtimes=claude_code,codex"
    )
    assert at.status_code == 200
    assert non_at.status_code == 200
    at_body = {k: at.get_json()[k] for k in _BODY_KEYS}
    non_at_body = {k: non_at.get_json()[k] for k in _BODY_KEYS}
    assert at_body == non_at_body, (
        f"perspective={perspective} shaped the ladder -- "
        f"_at prefix must not shape rows"
    )


# ── API: resolver + perspective envelope carried ──────────────────────────


def test_api_features_at_carries_resolver_envelope(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=cloud_pro&features=fleet"
    )
    j = r.get_json()
    for k in ("current_tier", "current_tier_rank", "grace", "enforced"):
        assert k in j
    assert j["grace"] is True
    assert j["enforced"] is False


def test_api_runtimes_at_carries_resolver_envelope(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=cloud_pro&runtimes=claude_code"
    )
    j = r.get_json()
    for k in ("current_tier", "current_tier_rank", "grace", "enforced"):
        assert k in j
    assert j["grace"] is True
    assert j["enforced"] is False


def test_api_features_at_carries_perspective_envelope(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-features-at?tier=cloud_starter&features=fleet"
    )
    j = r.get_json()
    assert j["perspective_tier"] == "cloud_starter"
    assert j["perspective_tier_label"] == ent.tier_label("cloud_starter")
    assert j["perspective_tier_rank"] == ent.tier_rank("cloud_starter")


def test_api_runtimes_at_carries_perspective_envelope(client, ent):
    r = client.get(
        "/api/entitlement/tiers-for-runtimes-at?tier=cloud_starter&runtimes=claude_code"
    )
    j = r.get_json()
    assert j["perspective_tier"] == "cloud_starter"
    assert j["perspective_tier_label"] == ent.tier_label("cloud_starter")
    assert j["perspective_tier_rank"] == ent.tier_rank("cloud_starter")
