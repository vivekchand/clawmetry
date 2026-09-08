"""Tests for the bundle-batch ``/api/entitlement/has-features-bundle-batch``
and ``/api/entitlement/has-runtimes-bundle-batch`` endpoints.

Boolean-fold bundle-axis batch sibling of the singular
``/api/entitlement/has-features`` / ``/api/entitlement/has-runtimes``
endpoints (which fold ONE bundle to ONE ``has_*`` boolean on the LIVE
install), in the same relationship
``/api/entitlement/min-tier-for-features-batch`` /
``/api/entitlement/min-tier-for-runtimes-batch`` have to the reverse-
lookup singular endpoints. Wraps the
:func:`clawmetry.entitlements.has_features_bundle_batch` /
:func:`clawmetry.entitlements.has_runtimes_bundle_batch` helpers.

Distinct from ``/has-features-at-batch`` (which fixes ONE bundle and
sweeps N perspective tiers): this fixes N bundles and reads the LIVE
per-install grant.

These tests pin:

* helper: per-bundle normalisation (whitespace, lowercase, dedup
  preserving first-seen order), unknown-id bucketing, runtime alias
  canonicalisation, empty / all-unknown bundles surface as a stable
  row with ``has_*=False``
* helper: unknown item collapses the row's fold ``False`` (typo-
  catches-at-callsite posture)
* helper: per-row parity with the singular scalar
  (``has_features_bundle_batch([b])[0]['has_features']`` byte-equals
  ``has_features(b)``) on the KNOWN slice
* helper: never-raise on ``None`` / non-iterable / non-dict bundles
* API happy path: 6-key envelope, 5-key row, ``count``, ``kind``
* API error paths: 400 on missing / non-list / empty ``bundles``
* API single-dict / bare-string shorthand ('bundles': ['fleet', 'sso'])
* API row byte-parity vs the singular scalar on the same known bundle
* API cross-endpoint axis-echo parity vs
  ``/min-tier-for-features-batch`` / ``/min-tier-for-runtimes-batch``
  on ``features`` / ``unknown`` / ``kind`` / ``count``
* API never-5xxs on a delegate crash (monkey-patched helper raises)
* grace vs enforce fold divergence (paid feature -> True in grace,
  False after enforcement — matches ``has_features`` grace posture)
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


def test_helper_features_bundle_batch_dedups_and_lowers(ent):
    rows = ent.has_features_bundle_batch(
        [["fleet", "", "FLEET", "sso"], ["otel_export"]]
    )
    assert len(rows) == 2
    assert rows[0]["features"] == ["fleet", "sso"]
    assert rows[0]["unknown"] == []
    assert rows[0]["count"] == 2
    assert rows[1]["features"] == ["otel_export"]


def test_helper_features_bundle_batch_buckets_unknown(ent):
    rows = ent.has_features_bundle_batch([["fleet", "bogus"]])
    assert rows[0]["features"] == ["fleet"]
    assert rows[0]["unknown"] == ["bogus"]
    # Unknown collapses the fold to False even in grace.
    assert rows[0]["has_features"] is False


def test_helper_features_bundle_batch_empty_bundle_stable_row(ent):
    rows = ent.has_features_bundle_batch([[]])
    assert len(rows) == 1
    r = rows[0]
    assert r["features"] == []
    assert r["unknown"] == []
    assert r["kind"] == "features"
    assert r["count"] == 0
    assert r["has_features"] is False


def test_helper_features_bundle_batch_all_unknown_stable_row(ent):
    rows = ent.has_features_bundle_batch([["bogus1", "bogus2"]])
    r = rows[0]
    assert r["features"] == []
    assert r["unknown"] == ["bogus1", "bogus2"]
    assert r["count"] == 0
    assert r["has_features"] is False


def test_helper_features_bundle_batch_none_returns_empty(ent):
    assert ent.has_features_bundle_batch(None) == []


def test_helper_features_bundle_batch_non_iterable_returns_empty(ent):
    assert ent.has_features_bundle_batch(42) == []


def test_helper_features_bundle_batch_none_bundle_stable_row(ent):
    rows = ent.has_features_bundle_batch([None, ["fleet"]])
    assert len(rows) == 2
    assert rows[0] == {
        "features": [],
        "unknown": [],
        "kind": "features",
        "count": 0,
        "has_features": False,
    }
    assert rows[1]["features"] == ["fleet"]


def test_helper_features_bundle_batch_non_string_tokens_coerce(ent):
    # Non-string tokens coerce via str(); numeric tokens land in unknown.
    rows = ent.has_features_bundle_batch([[42, "fleet"]])
    assert rows[0]["features"] == ["fleet"]
    assert "42" in rows[0]["unknown"]
    # Unknown collapses fold to False.
    assert rows[0]["has_features"] is False


def test_helper_runtimes_bundle_batch_canonicalises_aliases(ent):
    rows = ent.has_runtimes_bundle_batch(
        [["claude-code", "codex", "claude_code"]]
    )
    # Canonicalisation + dedup after canonicalisation.
    assert rows[0]["runtimes"] == ["claude_code", "codex"]
    assert rows[0]["unknown"] == []


def test_helper_runtimes_bundle_batch_buckets_unknown(ent):
    rows = ent.has_runtimes_bundle_batch([["claude_code", "bogus_rt"]])
    assert rows[0]["runtimes"] == ["claude_code"]
    assert rows[0]["unknown"] == ["bogus_rt"]
    assert rows[0]["has_runtimes"] is False


def test_helper_runtimes_bundle_batch_openclaw_free_grants(ent):
    rows = ent.has_runtimes_bundle_batch([["openclaw"]])
    # openclaw is the free runtime; every install grants it, so LIVE
    # fold is True across every rollout state.
    assert rows[0]["runtimes"] == ["openclaw"]
    assert rows[0]["has_runtimes"] is True


def test_helper_runtimes_bundle_batch_none_returns_empty(ent):
    assert ent.has_runtimes_bundle_batch(None) == []


# ── helper: per-row parity with the singular scalar ──────────────────────


def test_helper_features_bundle_batch_per_row_parity_with_scalar(ent):
    """Per-row ``has_features`` byte-equals the singular scalar for
    every KNOWN-only bundle (unknown items collapse the row to False
    without querying the scalar — that divergence is tested separately
    above)."""
    bundles = [
        ["fleet", "sso"],
        ["otel_export"],
        ["fleet"],
        ["sso"],
        [],
    ]
    rows = ent.has_features_bundle_batch(bundles)
    for row, bundle in zip(rows, bundles):
        # Reproduce the helper's normalisation for the singular
        # comparison (KNOWN slice only).
        seen: set[str] = set()
        known: list[str] = []
        for tok in bundle:
            s = tok.strip().lower()
            if s and s in ent.ALL_FEATURES and s not in seen:
                seen.add(s)
                known.append(s)
        singular = ent.has_features(known) if known else False
        assert row["has_features"] == singular


def test_helper_runtimes_bundle_batch_per_row_parity_with_scalar(ent):
    bundles = [
        ["openclaw"],
        ["claude-code", "codex"],
        ["claude_code"],
        [],
    ]
    rows = ent.has_runtimes_bundle_batch(bundles)
    for row, bundle in zip(rows, bundles):
        seen: set[str] = set()
        known: list[str] = []
        for tok in bundle:
            c = ent.canonical_runtime(tok.strip().lower())
            if c and c in ent.ALL_RUNTIMES and c not in seen:
                seen.add(c)
                known.append(c)
        singular = ent.has_runtimes(known) if known else False
        assert row["has_runtimes"] == singular


# ── helper: grace pass-through ───────────────────────────────────────────


def test_helper_features_bundle_batch_grace_paid_feature_true(ent):
    # In grace (default OSS-free rollout), a paid-only feature still
    # reads True from has_features via the resolver's grace pass-through
    # -- matches the singular has_features scalar posture.
    assert ent.get_entitlement().grace is True
    rows = ent.has_features_bundle_batch([["fleet"]])
    assert rows[0]["has_features"] is True


def test_helper_features_bundle_batch_never_raises_on_bad_bundle(ent):
    # A non-iterable per-bundle entry doesn't raise: normalisation
    # collapses it to the empty row shape.
    rows = ent.has_features_bundle_batch([42, ["fleet"]])
    assert len(rows) == 2
    assert rows[0]["has_features"] is False


# ── API: happy path ──────────────────────────────────────────────────────


_ROW_ENVELOPE = {
    "unknown",
    "kind",
    "count",
}


def _row_keys(axis: str) -> set[str]:
    return _ROW_ENVELOPE | {axis, f"has_{axis}"}


def test_api_features_bundle_batch_happy(client, ent):
    r = client.post(
        "/api/entitlement/has-features-bundle-batch",
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
        assert set(row.keys()) == _row_keys("features")
        assert row["kind"] == "features"
    assert j["bundles"][0]["features"] == ["fleet", "sso"]
    # Grace-on install: known paid features fold True.
    assert j["bundles"][0]["has_features"] is True
    assert j["bundles"][2]["features"] == []
    assert j["bundles"][2]["has_features"] is False


def test_api_runtimes_bundle_batch_happy(client, ent):
    r = client.post(
        "/api/entitlement/has-runtimes-bundle-batch",
        json={"bundles": [["claude-code", "codex"], ["openclaw"]]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 2
    for row in j["bundles"]:
        assert set(row.keys()) == _row_keys("runtimes")
        assert row["kind"] == "runtimes"
    # Canonicalisation applied.
    assert j["bundles"][0]["runtimes"] == ["claude_code", "codex"]
    assert j["bundles"][1]["runtimes"] == ["openclaw"]
    # openclaw is FREE_RUNTIMES so LIVE fold is True regardless of grace.
    assert j["bundles"][1]["has_runtimes"] is True


def test_api_features_bundle_batch_single_bundle_shorthand(client, ent):
    """A bare list of strings is treated as ONE bundle (matches the
    singular endpoint's bare-CSV posture and the reverse-lookup
    /min-tier-for-features-batch endpoint)."""
    r = client.post(
        "/api/entitlement/has-features-bundle-batch",
        json={"bundles": ["fleet", "sso"]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 1
    assert j["bundles"][0]["features"] == ["fleet", "sso"]


def test_api_runtimes_bundle_batch_single_bundle_shorthand(client, ent):
    r = client.post(
        "/api/entitlement/has-runtimes-bundle-batch",
        json={"bundles": ["claude_code", "codex"]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 1
    assert j["bundles"][0]["runtimes"] == ["claude_code", "codex"]


def test_api_features_bundle_batch_unknown_bucketed(client, ent):
    r = client.post(
        "/api/entitlement/has-features-bundle-batch",
        json={"bundles": [["fleet", "bogus"]]},
    )
    j = r.get_json()
    assert j["bundles"][0]["features"] == ["fleet"]
    assert j["bundles"][0]["unknown"] == ["bogus"]
    # Unknown collapses fold to False even in grace.
    assert j["bundles"][0]["has_features"] is False


# ── API: error paths ─────────────────────────────────────────────────────


def test_api_features_bundle_batch_missing_bundles_400(client):
    r = client.post("/api/entitlement/has-features-bundle-batch", json={})
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_features_bundle_batch_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/has-features-bundle-batch",
        json={"bundles": []},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "empty bundles"


def test_api_features_bundle_batch_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/has-features-bundle-batch",
        json={"bundles": 42},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundles must be a list"


def test_api_features_bundle_batch_no_body_400(client):
    r = client.post("/api/entitlement/has-features-bundle-batch")
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_runtimes_bundle_batch_missing_bundles_400(client):
    r = client.post("/api/entitlement/has-runtimes-bundle-batch", json={})
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_runtimes_bundle_batch_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/has-runtimes-bundle-batch",
        json={"bundles": []},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "empty bundles"


def test_api_runtimes_bundle_batch_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/has-runtimes-bundle-batch",
        json={"bundles": "not-a-list"},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundles must be a list"


# ── API: row byte-parity with the singular scalar ────────────────────────


def test_api_features_bundle_batch_row_parity_with_singular_scalar(
    client, ent
):
    """Per-row ``has_features`` byte-equals ``has_features`` on the
    KNOWN slice of the same bundle -- the paywall matrix column reads
    identical values whether it queries the singular scalar per row or
    the bundle-batch endpoint once."""
    for bundle in (
        ["fleet", "sso"],
        ["otel_export"],
        ["fleet"],
        ["sso"],
    ):
        r = client.post(
            "/api/entitlement/has-features-bundle-batch",
            json={"bundles": [bundle]},
        )
        row = r.get_json()["bundles"][0]
        # KNOWN slice = every item passed since bundle is all known.
        assert row["has_features"] == ent.has_features(bundle)


def test_api_runtimes_bundle_batch_row_parity_with_singular_scalar(
    client, ent
):
    for bundle in (
        ["openclaw"],
        ["claude_code"],
        ["claude_code", "codex"],
    ):
        r = client.post(
            "/api/entitlement/has-runtimes-bundle-batch",
            json={"bundles": [bundle]},
        )
        row = r.get_json()["bundles"][0]
        assert row["has_runtimes"] == ent.has_runtimes(bundle)


# ── API: cross-endpoint axis echo parity ────────────────────────────────


def test_api_features_bundle_batch_axis_echo_parity_vs_min_tier(
    client, ent
):
    """The axis / unknown / kind / count slice of each row byte-equals
    the same slice on ``/min-tier-for-features-batch`` on the same
    input bundle (only the fold slot diverges -- ``has_features`` bool
    here vs ``required_tier`` id on the reverse-lookup sibling)."""
    bundles = [["FLEET", "fleet", "sso"], ["bogus", "otel_export"], []]

    r_has = client.post(
        "/api/entitlement/has-features-bundle-batch",
        json={"bundles": bundles},
    ).get_json()
    r_mtr = client.post(
        "/api/entitlement/min-tier-for-features-batch",
        json={"bundles": bundles},
    ).get_json()

    for row_has, row_mtr in zip(r_has["bundles"], r_mtr["bundles"]):
        for k in ("features", "unknown", "kind", "count"):
            assert row_has[k] == row_mtr[k], k


def test_api_runtimes_bundle_batch_axis_echo_parity_vs_min_tier(
    client, ent
):
    bundles = [
        ["claude-code", "codex", "claude_code"],
        ["openclaw", "bogus_rt"],
        [],
    ]
    r_has = client.post(
        "/api/entitlement/has-runtimes-bundle-batch",
        json={"bundles": bundles},
    ).get_json()
    r_mtr = client.post(
        "/api/entitlement/min-tier-for-runtimes-batch",
        json={"bundles": bundles},
    ).get_json()
    for row_has, row_mtr in zip(r_has["bundles"], r_mtr["bundles"]):
        for k in ("runtimes", "unknown", "kind", "count"):
            assert row_has[k] == row_mtr[k], k


# ── API: never-5xxs on delegate crash ────────────────────────────────────


def test_api_features_bundle_batch_never_5xxs_on_delegate_crash(
    monkeypatch, client, ent
):
    def _boom(bundles):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "has_features_bundle_batch", _boom)
    r = client.post(
        "/api/entitlement/has-features-bundle-batch",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 200
    j = r.get_json()
    # Fallback envelope shape preserved.
    assert set(j.keys()) == {
        "bundles",
        "count",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    assert j["bundles"] == []
    assert j["count"] == 0


def test_api_runtimes_bundle_batch_never_5xxs_on_delegate_crash(
    monkeypatch, client, ent
):
    def _boom(bundles):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "has_runtimes_bundle_batch", _boom)
    r = client.post(
        "/api/entitlement/has-runtimes-bundle-batch",
        json={"bundles": [["openclaw"]]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []
    assert j["count"] == 0


# ── grace vs enforce fold divergence ─────────────────────────────────────


def test_helper_features_bundle_batch_grace_vs_enforce_diverges(
    monkeypatch, tmp_path
):
    """Paid feature reads True under grace (matches ``has_features``
    grace pass-through) and False after enforcement."""
    import clawmetry.entitlements as e

    monkeypatch.setenv("HOME", str(tmp_path))

    # GRACE mode (default).
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()
    grace_rows = e.has_features_bundle_batch([["fleet"]])
    assert e.get_entitlement().grace is True
    assert grace_rows[0]["has_features"] is True

    # ENFORCE mode.
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforce_rows = e.has_features_bundle_batch([["fleet"]])
    assert e.get_entitlement().grace is False
    assert enforce_rows[0]["has_features"] is False

    # Reset for other tests.
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()
