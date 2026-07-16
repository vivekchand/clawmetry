"""Tests for the bare ``/api/entitlement/min-tier-for-features`` and
``/api/entitlement/min-tier-for-runtimes`` endpoints.

Fills the *bare* slot in the plural grant-axis ``min_tier_for_*`` family
alongside the singular ``/min-tier?feature=<id>`` route (which resolves
ONE feature at a time) and the ``_at`` sibling
``/min-tier-for-features-at`` (which layers a hypothetical-perspective
envelope on top). Wraps the existing
:func:`clawmetry.entitlements.min_tier_for_features` /
:func:`clawmetry.entitlements.min_tier_for_runtimes` helpers.

These tests pin:

* API happy path: shape, resolver envelope, ``kind``, ``count``, ``free``
* API error paths: 400 on missing / blank ``features=`` / ``runtimes=``
* all-unknown IS 200 with ``unknown`` populated and ``required_tier=null``
  (not confused with "asked for nothing")
* CSV dedup / normalisation via the shared ``_parse_csv_arg`` helper
* runtime canonicalisation (``claude-code`` -> ``claude_code``)
* body byte-parity with the ``_at`` sibling once the three perspective
  keys are stripped -- the bare and ``_at`` bodies must not drift
* cross-endpoint parity: ``required_tier`` byte-equals the helper's return
* resolver envelope carried
* never-5xxs on a delegate crash
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


_BARE_ENVELOPE_KEYS = {
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "free",
    "kind",
    "count",
    "unknown",
}


# ── API: happy path ────────────────────────────────────────────────────────


def test_api_features_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-features?features=fleet,sso"
    )
    assert r.status_code == 200
    j = r.get_json()
    expected = _BARE_ENVELOPE_KEYS | {"features"}
    assert set(j.keys()) == expected
    assert j["kind"] == "features"
    assert j["features"] == ["fleet", "sso"]
    assert j["unknown"] == []
    assert j["count"] == 2
    assert j["required_tier"] == ent.min_tier_for_features(["fleet", "sso"])
    assert j["required_tier_label"] == ent.tier_label(j["required_tier"])
    assert j["required_tier_rank"] == ent.tier_rank(j["required_tier"])


def test_api_runtimes_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude-code,codex"
    )
    assert r.status_code == 200
    j = r.get_json()
    expected = _BARE_ENVELOPE_KEYS | {"runtimes"}
    assert set(j.keys()) == expected
    assert j["kind"] == "runtimes"
    assert j["runtimes"] == ["claude_code", "codex"]  # canonicalised
    assert j["unknown"] == []
    assert j["required_tier"] == ent.min_tier_for_runtimes(
        ["claude_code", "codex"]
    )


def test_api_features_bare_body_has_no_perspective_keys(client):
    r = client.get(
        "/api/entitlement/min-tier-for-features?features=fleet"
    )
    j = r.get_json()
    assert "perspective_tier" not in j
    assert "perspective_tier_label" not in j
    assert "perspective_tier_rank" not in j


def test_api_runtimes_bare_body_has_no_perspective_keys(client):
    r = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude_code"
    )
    j = r.get_json()
    assert "perspective_tier" not in j
    assert "perspective_tier_label" not in j
    assert "perspective_tier_rank" not in j


# ── API: error paths ──────────────────────────────────────────────────────


def test_api_features_missing_features_returns_400(client):
    r = client.get("/api/entitlement/min-tier-for-features")
    assert r.status_code == 400
    assert r.get_json().get("error") == "missing features"


def test_api_runtimes_missing_runtimes_returns_400(client):
    r = client.get("/api/entitlement/min-tier-for-runtimes")
    assert r.status_code == 400
    assert r.get_json().get("error") == "missing runtimes"


def test_api_features_blank_features_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-features?features=%20%20"
    )
    assert r.status_code == 400


def test_api_runtimes_blank_runtimes_returns_400(client):
    r = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=%20%20"
    )
    assert r.status_code == 400


def test_api_features_empty_csv_returns_400(client):
    r = client.get("/api/entitlement/min-tier-for-features?features=")
    assert r.status_code == 400


def test_api_runtimes_empty_csv_returns_400(client):
    r = client.get("/api/entitlement/min-tier-for-runtimes?runtimes=")
    assert r.status_code == 400


# ── API: all-unknown IS 200 ────────────────────────────────────────────────


def test_api_features_all_unknown_is_200(client):
    r = client.get(
        "/api/entitlement/min-tier-for-features?features=bogus1,bogus2"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["features"] == []
    assert j["unknown"] == ["bogus1", "bogus2"]
    assert j["required_tier"] is None
    assert j["required_tier_label"] is None
    assert j["required_tier_rank"] == -1
    assert j["count"] == 0
    assert j["free"] is False


def test_api_runtimes_all_unknown_is_200(client):
    r = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=bogus1,bogus2"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["runtimes"] == []
    assert j["unknown"] == ["bogus1", "bogus2"]
    assert j["required_tier"] is None
    assert j["count"] == 0
    assert j["free"] is False


# ── API: CSV normalisation / dedup ─────────────────────────────────────────


def test_api_features_dedup_preserves_order(client):
    r = client.get(
        "/api/entitlement/min-tier-for-features?features=fleet,,sso,fleet"
    )
    assert r.status_code == 200
    assert r.get_json()["features"] == ["fleet", "sso"]


def test_api_runtimes_dedup_preserves_order(client):
    r = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude-code,,codex,claude_code"
    )
    assert r.status_code == 200
    assert r.get_json()["runtimes"] == ["claude_code", "codex"]


def test_api_features_mixed_known_unknown(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-features?features=fleet,bogus"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["features"] == ["fleet"]
    assert j["unknown"] == ["bogus"]
    assert j["required_tier"] == ent.min_tier_for_features(["fleet"])


def test_api_runtimes_mixed_known_unknown(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude_code,bogus"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["runtimes"] == ["claude_code"]
    assert j["unknown"] == ["bogus"]
    assert j["required_tier"] == ent.min_tier_for_runtimes(["claude_code"])


# ── API: cross-endpoint parity ────────────────────────────────────────────


def test_api_features_required_tier_byte_equals_helper(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-features?features=fleet,sso"
    )
    assert r.status_code == 200
    assert (
        r.get_json()["required_tier"]
        == ent.min_tier_for_features(["fleet", "sso"])
    )


def test_api_runtimes_required_tier_byte_equals_helper(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude_code,codex"
    )
    assert r.status_code == 200
    assert (
        r.get_json()["required_tier"]
        == ent.min_tier_for_runtimes(["claude_code", "codex"])
    )


# ── API: body byte-parity with _at sibling (perspective keys stripped) ───


_PERSPECTIVE_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
}


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_api_features_bare_matches_at_with_perspective_stripped(
    client, perspective
):
    """The bare body must byte-equal the ``_at`` body once the three
    perspective envelope keys are stripped. Pins that the bare and
    ``_at`` bodies cannot drift."""
    bare = client.get(
        "/api/entitlement/min-tier-for-features?features=fleet,sso"
    ).get_json()
    at = client.get(
        f"/api/entitlement/min-tier-for-features-at?tier={perspective}&features=fleet,sso"
    ).get_json()
    at_stripped = {k: v for k, v in at.items() if k not in _PERSPECTIVE_ENVELOPE_KEYS}
    assert bare == at_stripped, (
        f"bare vs _at?tier={perspective} bodies diverged "
        f"(perspective keys stripped): "
        f"bare_only={set(bare) - set(at_stripped)} "
        f"at_only={set(at_stripped) - set(bare)}"
    )


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_api_runtimes_bare_matches_at_with_perspective_stripped(
    client, perspective
):
    bare = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude_code,codex"
    ).get_json()
    at = client.get(
        f"/api/entitlement/min-tier-for-runtimes-at?tier={perspective}&runtimes=claude_code,codex"
    ).get_json()
    at_stripped = {k: v for k, v in at.items() if k not in _PERSPECTIVE_ENVELOPE_KEYS}
    assert bare == at_stripped


# ── API: resolver envelope carried ────────────────────────────────────────


def test_api_features_carries_resolver_envelope(client):
    r = client.get(
        "/api/entitlement/min-tier-for-features?features=fleet"
    )
    j = r.get_json()
    for k in ("current_tier", "current_tier_rank", "grace", "enforced"):
        assert k in j
    assert j["grace"] is True
    assert j["enforced"] is False


def test_api_runtimes_carries_resolver_envelope(client):
    r = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude_code"
    )
    j = r.get_json()
    for k in ("current_tier", "current_tier_rank", "grace", "enforced"):
        assert k in j
    assert j["grace"] is True
    assert j["enforced"] is False


# ── API: never-5xxs on a delegate crash ───────────────────────────────────


def test_api_features_never_5xxs_on_delegate_crash(client, ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_features", _boom)
    r = client.get(
        "/api/entitlement/min-tier-for-features?features=fleet"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["required_tier"] is None
    assert j["features"] == []
    assert j["unknown"] == ["fleet"]
    assert j["kind"] == "features"


def test_api_runtimes_never_5xxs_on_delegate_crash(client, ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_runtimes", _boom)
    r = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude_code"
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["required_tier"] is None
    assert j["runtimes"] == []
    assert j["unknown"] == ["claude_code"]
    assert j["kind"] == "runtimes"


# ── grace vs enforce parity ───────────────────────────────────────────────


def test_api_features_grace_vs_enforce_identical(client, ent, monkeypatch):
    grace = client.get(
        "/api/entitlement/min-tier-for-features?features=fleet,sso"
    ).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    enforce_client = app.test_client()
    enforce = enforce_client.get(
        "/api/entitlement/min-tier-for-features?features=fleet,sso"
    ).get_json()
    # required_tier / kind / features / count / free must byte-equal.
    for k in ("required_tier", "kind", "features", "count", "free", "unknown"):
        assert grace[k] == enforce[k], f"key {k} drifted grace vs enforce"


def test_api_runtimes_grace_vs_enforce_identical(client, ent, monkeypatch):
    grace = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude_code"
    ).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    enforce_client = app.test_client()
    enforce = enforce_client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes=claude_code"
    ).get_json()
    for k in ("required_tier", "kind", "runtimes", "count", "free", "unknown"):
        assert grace[k] == enforce[k], f"key {k} drifted grace vs enforce"
