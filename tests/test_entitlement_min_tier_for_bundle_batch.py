"""Tests for the bundle-batch ``/api/entitlement/min-tier-for-features-batch``
and ``/api/entitlement/min-tier-for-runtimes-batch`` endpoints (plus their
``_at_batch`` siblings).

Fills the bundle-axis batch slot alongside the singular
``/min-tier-for-features`` / ``/min-tier-for-runtimes`` endpoints (which
fold ONE bundle to ONE tier) so a pricing-matrix surface comparing
several hypothetical feature/runtime sets renders off ONE round-trip
instead of N calls to the singular endpoints. Wraps the
:func:`clawmetry.entitlements.min_tier_for_features_batch` /
:func:`clawmetry.entitlements.min_tier_for_runtimes_batch` helpers.

These tests pin:

* helper: bundle normalisation (whitespace, lowercase, dedup preserving
  first-seen order), unknown-id bucketing, runtime alias
  canonicalisation, empty / all-unknown bundles surface as a stable row
* helper: per-row parity with the singular helper
  (``min_tier_for_features_batch([b])[0]['min_tier']`` byte-equals
  ``min_tier_for_features(b)``)
* helper: perspective-independence of the ``_at_batch`` variant
* API happy path: shape, resolver envelope, ``count``
* API error paths: 400 on missing / non-list / empty ``bundles``
* API per-row body byte-equals the bare singular endpoint body minus the
  resolver envelope
* API perspective envelope on the ``_at_batch`` variant
* API 404 on unknown ``tier=``, 400 on missing ``tier=``
* API never-5xxs on a delegate crash
* grace vs enforce yields byte-identical per-row bodies
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


# ── helper: bundle normalisation ─────────────────────────────────────────


def test_helper_features_batch_dedups_and_lowers(ent):
    rows = ent.min_tier_for_features_batch(
        [["fleet", "", "SSO", "fleet"], ["otel_export"]]
    )
    assert len(rows) == 2
    assert rows[0]["features"] == ["fleet", "sso"]
    assert rows[0]["unknown"] == []
    assert rows[0]["count"] == 2
    assert rows[1]["features"] == ["otel_export"]


def test_helper_features_batch_buckets_unknown(ent):
    rows = ent.min_tier_for_features_batch([["fleet", "bogus"]])
    assert rows[0]["features"] == ["fleet"]
    assert rows[0]["unknown"] == ["bogus"]


def test_helper_features_batch_empty_bundle_is_stable_row(ent):
    rows = ent.min_tier_for_features_batch([[]])
    assert len(rows) == 1
    r = rows[0]
    assert r["features"] == []
    assert r["unknown"] == []
    assert r["count"] == 0
    assert r["min_tier"] is None
    assert r["min_tier_label"] is None
    assert r["min_tier_rank"] == -1
    assert r["free"] is False


def test_helper_features_batch_all_unknown_bundle_is_stable_row(ent):
    rows = ent.min_tier_for_features_batch([["bogus1", "bogus2"]])
    r = rows[0]
    assert r["features"] == []
    assert r["unknown"] == ["bogus1", "bogus2"]
    assert r["min_tier"] is None


def test_helper_features_batch_none_returns_empty(ent):
    assert ent.min_tier_for_features_batch(None) == []


def test_helper_features_batch_non_iterable_returns_empty(ent):
    assert ent.min_tier_for_features_batch(42) == []


def test_helper_runtimes_batch_canonicalises_aliases(ent):
    rows = ent.min_tier_for_runtimes_batch(
        [["claude-code", "codex", "claude_code"]]
    )
    assert rows[0]["runtimes"] == ["claude_code", "codex"]
    assert rows[0]["unknown"] == []


def test_helper_runtimes_batch_buckets_unknown(ent):
    rows = ent.min_tier_for_runtimes_batch([["claude_code", "bogus_rt"]])
    assert rows[0]["runtimes"] == ["claude_code"]
    assert rows[0]["unknown"] == ["bogus_rt"]


# ── helper: per-row parity with the singular helper ──────────────────────


def test_helper_features_batch_per_row_parity_with_singular(ent):
    """Per-row ``min_tier`` byte-equals the singular helper for every
    (feature-bundle) row."""
    bundles = [
        ["fleet", "sso"],
        ["otel_export"],
        ["fleet"],
        ["sso"],
        ["bogus"],
        [],
    ]
    rows = ent.min_tier_for_features_batch(bundles)
    for row, bundle in zip(rows, bundles):
        # Reproduce the helper's normalisation for the singular comparison.
        seen: set[str] = set()
        known: list[str] = []
        for tok in bundle:
            s = tok.strip().lower()
            if s and s in ent.ALL_FEATURES and s not in seen:
                seen.add(s)
                known.append(s)
        singular = ent.min_tier_for_features(known) if known else None
        assert row["min_tier"] == singular


def test_helper_runtimes_batch_per_row_parity_with_singular(ent):
    bundles = [
        ["claude-code", "codex"],
        ["openclaw"],
        ["claude_code"],
        ["bogus_rt"],
        [],
    ]
    rows = ent.min_tier_for_runtimes_batch(bundles)
    for row, bundle in zip(rows, bundles):
        seen: set[str] = set()
        known: list[str] = []
        for tok in bundle:
            c = ent.canonical_runtime(tok.strip().lower())
            if c and c in ent.ALL_RUNTIMES and c not in seen:
                seen.add(c)
                known.append(c)
        singular = ent.min_tier_for_runtimes(known) if known else None
        assert row["min_tier"] == singular


# ── helper: _at_batch perspective-independence ───────────────────────────


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_helper_features_at_batch_perspective_independent(ent, perspective):
    bundles = [["fleet", "sso"], ["otel_export"], []]
    assert (
        ent.min_tier_for_features_at_batch(perspective, bundles)
        == ent.min_tier_for_features_batch(bundles)
    )


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_helper_runtimes_at_batch_perspective_independent(ent, perspective):
    bundles = [["claude-code", "codex"], ["openclaw"]]
    assert (
        ent.min_tier_for_runtimes_at_batch(perspective, bundles)
        == ent.min_tier_for_runtimes_batch(bundles)
    )


def test_helper_features_at_batch_unknown_perspective_none(ent):
    assert ent.min_tier_for_features_at_batch("bogus", [["fleet"]]) is None
    assert ent.min_tier_for_features_at_batch("", [["fleet"]]) is None
    assert ent.min_tier_for_features_at_batch(None, [["fleet"]]) is None


def test_helper_runtimes_at_batch_unknown_perspective_none(ent):
    assert ent.min_tier_for_runtimes_at_batch("bogus", [["claude_code"]]) is None


# ── API: happy path ──────────────────────────────────────────────────────


_BARE_ROW_KEYS = {
    "unknown",
    "kind",
    "count",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "free",
}


def test_api_features_batch_happy(client, ent):
    r = client.post(
        "/api/entitlement/min-tier-for-features-batch",
        json={"bundles": [["fleet", "sso"], ["otel_export"], []]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == {
        "bundles",
        "count",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    assert j["count"] == 3
    assert len(j["bundles"]) == 3
    for row in j["bundles"]:
        assert set(row.keys()) == _BARE_ROW_KEYS | {"features"}
        assert row["kind"] == "features"
    assert j["bundles"][0]["features"] == ["fleet", "sso"]
    assert j["bundles"][0]["required_tier"] == ent.min_tier_for_features(
        ["fleet", "sso"]
    )
    assert j["bundles"][2]["features"] == []
    assert j["bundles"][2]["required_tier"] is None
    assert j["bundles"][2]["required_tier_rank"] == -1


def test_api_runtimes_batch_happy(client, ent):
    r = client.post(
        "/api/entitlement/min-tier-for-runtimes-batch",
        json={
            "bundles": [["claude-code", "codex"], ["openclaw"]]
        },
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 2
    assert j["bundles"][0]["runtimes"] == ["claude_code", "codex"]
    assert j["bundles"][0]["required_tier"] == ent.min_tier_for_runtimes(
        ["claude_code", "codex"]
    )
    assert j["bundles"][1]["runtimes"] == ["openclaw"]
    assert j["bundles"][1]["free"] is True


def test_api_features_batch_single_bundle_shorthand(client, ent):
    """A bare list of strings is treated as ONE bundle (matches the
    singular endpoint's bare-CSV posture)."""
    r = client.post(
        "/api/entitlement/min-tier-for-features-batch",
        json={"bundles": ["fleet", "sso"]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 1
    assert j["bundles"][0]["features"] == ["fleet", "sso"]


# ── API: error paths ─────────────────────────────────────────────────────


def test_api_features_batch_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/min-tier-for-features-batch", json={}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_features_batch_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/min-tier-for-features-batch",
        json={"bundles": []},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "empty bundles"


def test_api_features_batch_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/min-tier-for-features-batch",
        json={"bundles": 42},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundles must be a list"


def test_api_runtimes_batch_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/min-tier-for-runtimes-batch", json={}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


# ── API: per-row body byte-equals the bare singular endpoint body ────────


def test_api_features_batch_row_matches_bare_singular(client):
    """Each per-bundle row (minus the outer envelope) byte-equals the
    bare singular endpoint body for that same bundle."""
    bundle = ["fleet", "sso"]
    batch = client.post(
        "/api/entitlement/min-tier-for-features-batch",
        json={"bundles": [bundle]},
    ).get_json()
    row = batch["bundles"][0]
    singular = client.get(
        "/api/entitlement/min-tier-for-features?features="
        + ",".join(bundle)
    ).get_json()
    envelope_keys = {
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    singular_stripped = {
        k: v for k, v in singular.items() if k not in envelope_keys
    }
    assert row == singular_stripped


def test_api_runtimes_batch_row_matches_bare_singular(client):
    bundle = ["claude-code", "codex"]
    batch = client.post(
        "/api/entitlement/min-tier-for-runtimes-batch",
        json={"bundles": [bundle]},
    ).get_json()
    row = batch["bundles"][0]
    singular = client.get(
        "/api/entitlement/min-tier-for-runtimes?runtimes="
        + ",".join(bundle)
    ).get_json()
    envelope_keys = {
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    singular_stripped = {
        k: v for k, v in singular.items() if k not in envelope_keys
    }
    assert row == singular_stripped


# ── API: _at_batch perspective envelope ──────────────────────────────────


def test_api_features_at_batch_happy(client, ent):
    r = client.post(
        "/api/entitlement/min-tier-for-features-at-batch?tier=cloud_pro",
        json={"bundles": [["fleet"], ["sso"]]},
    )
    assert r.status_code == 200
    j = r.get_json()
    for k in (
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
    ):
        assert k in j
    assert j["perspective_tier"] == "cloud_pro"
    assert j["count"] == 2
    assert j["bundles"][0]["features"] == ["fleet"]
    assert j["bundles"][1]["features"] == ["sso"]


def test_api_features_at_batch_unknown_tier_404(client):
    r = client.post(
        "/api/entitlement/min-tier-for-features-at-batch?tier=bogus",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 404
    j = r.get_json()
    assert j["error"] == "unknown tier"
    assert j["tier"] == "bogus"


def test_api_features_at_batch_missing_tier_400(client):
    r = client.post(
        "/api/entitlement/min-tier-for-features-at-batch",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_api_runtimes_at_batch_happy(client, ent):
    r = client.post(
        "/api/entitlement/min-tier-for-runtimes-at-batch?tier=cloud_starter",
        json={"bundles": [["claude_code"], ["openclaw"]]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["perspective_tier"] == "cloud_starter"
    assert j["bundles"][1]["free"] is True


# ── API: _at_batch row body byte-equals the bare batch row body ──────────


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_api_features_at_batch_row_matches_bare_batch(client, perspective):
    bundles = [["fleet", "sso"], ["otel_export"], []]
    bare = client.post(
        "/api/entitlement/min-tier-for-features-batch",
        json={"bundles": bundles},
    ).get_json()
    at = client.post(
        f"/api/entitlement/min-tier-for-features-at-batch?tier={perspective}",
        json={"bundles": bundles},
    ).get_json()
    assert bare["bundles"] == at["bundles"]
    assert bare["count"] == at["count"]


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_api_runtimes_at_batch_row_matches_bare_batch(client, perspective):
    bundles = [["claude-code", "codex"], ["openclaw"]]
    bare = client.post(
        "/api/entitlement/min-tier-for-runtimes-batch",
        json={"bundles": bundles},
    ).get_json()
    at = client.post(
        f"/api/entitlement/min-tier-for-runtimes-at-batch?tier={perspective}",
        json={"bundles": bundles},
    ).get_json()
    assert bare["bundles"] == at["bundles"]


# ── API: never-5xxs on a delegate crash ──────────────────────────────────


def test_api_features_batch_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_features_batch", _boom)
    r = client.post(
        "/api/entitlement/min-tier-for-features-batch",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []
    assert j["count"] == 0


def test_api_runtimes_batch_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "min_tier_for_runtimes_batch", _boom)
    r = client.post(
        "/api/entitlement/min-tier-for-runtimes-batch",
        json={"bundles": [["claude_code"]]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []


# ── grace vs enforce parity ──────────────────────────────────────────────


def test_api_features_batch_grace_vs_enforce_identical(
    client, ent, monkeypatch
):
    grace = client.post(
        "/api/entitlement/min-tier-for-features-batch",
        json={"bundles": [["fleet", "sso"], ["otel_export"]]},
    ).get_json()
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    enforce_client = app.test_client()
    enforce = enforce_client.post(
        "/api/entitlement/min-tier-for-features-batch",
        json={"bundles": [["fleet", "sso"], ["otel_export"]]},
    ).get_json()
    assert grace["bundles"] == enforce["bundles"]
    assert grace["count"] == enforce["count"]
