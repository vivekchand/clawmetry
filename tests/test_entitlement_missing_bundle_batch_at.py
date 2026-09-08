"""Tests for the perspective-shaped bundle-batch
``/api/entitlement/missing-features-bundle-batch-at`` and
``/api/entitlement/missing-runtimes-bundle-batch-at`` endpoints.

Hypothetical-perspective row-detail sibling of the LIVE
``/api/entitlement/missing-features-bundle-batch`` /
``/api/entitlement/missing-runtimes-bundle-batch`` endpoints (which fold
N bundles' per-item denial lists against the resolved entitlement),
scoped by a caller-supplied ``tier=<perspective>`` query arg. Wraps the
:func:`clawmetry.entitlements.missing_features_bundle_batch_at` /
:func:`clawmetry.entitlements.missing_runtimes_bundle_batch_at` helpers.

Fills the ``_at`` slot on the per-axis row-detail bundle-batch family
alongside the aggregate ``/api/entitlement/missing-all-bundle-batch-at``
and the boolean-fold ``/api/entitlement/has-{features,runtimes}-bundle-
batch-at`` so a caller can render the per-axis "which items would
<perspective> still deny?" column of a pricing matrix off ONE call per
axis per perspective instead of N calls to ``/missing-features-at`` /
``/missing-runtimes-at``.

These tests pin:

* helper: perspective validation (empty / non-string / unknown ->
  ``None``; known tier -> ``list[dict]``)
* helper: per-bundle normalisation (whitespace, lowercase, dedup
  preserving first-seen), unknown-id bucketing (surfaces via
  ``unknown[]`` rather than silently rendering "denied"), runtime
  alias canonicalisation, empty / all-unknown / ``None`` bundles
  surface as stable rows with ``missing_*_at=[]``
* helper: per-row parity with the singular scalar
  ``missing_features_at`` / ``missing_runtimes_at`` on the KNOWN slice
* helper: ``bundles`` handling (``None`` / non-iterable -> ``[]``;
  ``None`` bundle -> empty row)
* helper: **grace-independence** -- the perspective-shaped fold is
  byte-identical under grace vs enforce (delegates to
  :func:`missing_features_at` / :func:`missing_runtimes_at`, both
  backed by the static per-tier grant tables)
* helper: perspective divergence -- at ``oss`` a paid-feature bundle
  reports ``missing_features_at=["fleet"]`` even in grace, whereas
  the LIVE :func:`missing_features_bundle_batch` reports
  ``missing=[]`` on the same bundle via grace pass-through
* helper: **complement invariant** with
  :func:`has_features_bundle_batch_at` /
  :func:`has_runtimes_bundle_batch_at` -- for every fully-known bundle,
  ``bool(row["missing_<axis>_at"]) == (not has_row["has_<axis>_at"])``
* API: 400 on missing / blank ``tier``; 404 on unknown ``tier``
  (with ``which=tier`` in the body)
* API: 400 on missing / non-list / empty ``bundles``
* API: happy-path envelope layers ``perspective_tier`` /
  ``perspective_tier_label`` / ``perspective_tier_rank`` on top of the
  bare batch envelope; each row carries the perspective-shaped
  ``missing_features_at`` / ``missing_runtimes_at`` fold slot
* API: single-list ``{"bundles": ["fleet", "sso"]}`` shorthand
* API: runtime alias canonicalisation happens through the endpoint
* API: never-5xxs on a delegate crash (monkey-patched helper raises)
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# -- Fixtures ----------------------------------------------------------------


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
    """Enforcement-on fixture. Perspective-shaped ``_at`` answers are
    intentionally byte-identical in grace and enforce; this fixture
    pins that invariant against the singular ``_at`` delegates."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


@pytest.fixture
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# -- Helper: perspective validation ------------------------------------------


@pytest.mark.parametrize("bad", [None, "", "   ", "bogus", "Pro+", 42, object()])
def test_helper_features_none_on_bad_perspective(ent, bad):
    assert ent.missing_features_bundle_batch_at(bad, [["fleet"]]) is None


@pytest.mark.parametrize("bad", [None, "", "   ", "bogus", 42, object()])
def test_helper_runtimes_none_on_bad_perspective(ent, bad):
    assert ent.missing_runtimes_bundle_batch_at(bad, [["openclaw"]]) is None


def test_helper_features_accepts_all_known_tiers(ent):
    for tid in ent._TIER_ORDER:
        rows = ent.missing_features_bundle_batch_at(tid, [["fleet"]])
        assert isinstance(rows, list)


# -- Helper: bundle normalisation --------------------------------------------


def test_helper_features_dedups_and_lowers(ent):
    rows = ent.missing_features_bundle_batch_at(
        "enterprise", [["fleet", "", "FLEET", "sso"], ["otel_export"]]
    )
    assert len(rows) == 2
    assert rows[0]["features"] == ["fleet", "sso"]
    assert rows[0]["unknown"] == []
    assert rows[0]["count"] == 2
    assert rows[1]["features"] == ["otel_export"]


def test_helper_features_buckets_unknown(ent):
    """Unknown tokens are echoed via ``unknown[]`` and drop from the
    ``missing_features_at`` walk -- a typo surfaces at the callsite
    rather than silently rendering as ``denied``."""
    rows = ent.missing_features_bundle_batch_at(
        "enterprise", [["fleet", "bogus"]]
    )
    assert rows[0]["features"] == ["fleet"]
    assert rows[0]["unknown"] == ["bogus"]
    # Fleet IS granted at enterprise -- KNOWN slice is fully granted -> [].
    assert rows[0]["missing_features_at"] == []


def test_helper_features_empty_bundle_stable_row(ent):
    rows = ent.missing_features_bundle_batch_at("pro", [[]])
    assert len(rows) == 1
    assert rows[0] == {
        "features": [],
        "unknown": [],
        "kind": "features",
        "count": 0,
        "missing_features_at": [],
    }


def test_helper_features_all_unknown_stable_row(ent):
    rows = ent.missing_features_bundle_batch_at("pro", [["bogus1", "bogus2"]])
    r = rows[0]
    assert r["features"] == []
    assert r["unknown"] == ["bogus1", "bogus2"]
    assert r["count"] == 0
    # All-unknown -> nothing known to check -> [] (matches
    # missing_features_at empty-[] posture).
    assert r["missing_features_at"] == []


def test_helper_features_none_bundle_stable_row(ent):
    rows = ent.missing_features_bundle_batch_at("pro", [None, ["fleet"]])
    assert len(rows) == 2
    assert rows[0] == {
        "features": [],
        "unknown": [],
        "kind": "features",
        "count": 0,
        "missing_features_at": [],
    }
    assert rows[1]["features"] == ["fleet"]


def test_helper_features_non_string_tokens_coerce(ent):
    rows = ent.missing_features_bundle_batch_at("enterprise", [[42, "fleet"]])
    assert rows[0]["features"] == ["fleet"]
    assert "42" in rows[0]["unknown"]
    # Fleet IS granted at enterprise; KNOWN slice fully granted -> [].
    assert rows[0]["missing_features_at"] == []


def test_helper_features_none_bundles_returns_empty(ent):
    assert ent.missing_features_bundle_batch_at("pro", None) == []


def test_helper_features_non_iterable_bundles_returns_empty(ent):
    assert ent.missing_features_bundle_batch_at("pro", 42) == []


def test_helper_runtimes_canonicalises_aliases(ent):
    rows = ent.missing_runtimes_bundle_batch_at(
        "pro", [["claude-code", "codex", "claude_code"]]
    )
    # Canonicalisation + dedup after canonicalisation.
    assert rows[0]["runtimes"] == ["claude_code", "codex"]
    assert rows[0]["unknown"] == []


def test_helper_runtimes_buckets_unknown(ent):
    rows = ent.missing_runtimes_bundle_batch_at(
        "pro", [["claude_code", "bogus_rt"]]
    )
    assert rows[0]["runtimes"] == ["claude_code"]
    assert rows[0]["unknown"] == ["bogus_rt"]
    # Pro grants claude_code -> KNOWN slice fully granted -> [].
    assert rows[0]["missing_runtimes_at"] == []


def test_helper_runtimes_none_bundles_returns_empty(ent):
    assert ent.missing_runtimes_bundle_batch_at("pro", None) == []


def test_helper_runtimes_free_runtime_empty_at_every_perspective(ent):
    """Free runtimes are granted at every tier -- the row's
    ``missing_runtimes_at`` list is empty regardless of perspective."""
    for perspective in ent._TIER_ORDER:
        rows = ent.missing_runtimes_bundle_batch_at(
            perspective, [["openclaw"]]
        )
        assert rows[0]["missing_runtimes_at"] == [], perspective


# -- Helper: per-row parity with the singular scalar --------------------------


def test_helper_features_per_row_parity_with_scalar(ent):
    """Per-row ``missing_features_at`` byte-equals
    :func:`missing_features_at` on the KNOWN slice for every
    (perspective, bundle) pair."""
    bundles = [
        ["fleet", "sso"],
        ["otel_export"],
        ["fleet"],
        ["sso"],
        [],
    ]
    for perspective in ("oss", "cloud_starter", "pro", "enterprise"):
        rows = ent.missing_features_bundle_batch_at(perspective, bundles)
        assert rows is not None
        for row, bundle in zip(rows, bundles):
            seen: set[str] = set()
            known: list[str] = []
            for tok in bundle:
                s = tok.strip().lower()
                if s and s in ent.ALL_FEATURES and s not in seen:
                    seen.add(s)
                    known.append(s)
            singular = (
                list(ent.missing_features_at(perspective, known))
                if known
                else []
            )
            assert row["missing_features_at"] == singular, (
                perspective,
                bundle,
                singular,
            )


def test_helper_runtimes_per_row_parity_with_scalar(ent):
    bundles = [
        ["openclaw"],
        ["claude-code", "codex"],
        ["claude_code"],
        [],
    ]
    for perspective in ("oss", "cloud_starter", "pro", "enterprise"):
        rows = ent.missing_runtimes_bundle_batch_at(perspective, bundles)
        assert rows is not None
        for row, bundle in zip(rows, bundles):
            seen: set[str] = set()
            known: list[str] = []
            for tok in bundle:
                c = ent.canonical_runtime(tok.strip().lower())
                if c and c in ent.ALL_RUNTIMES and c not in seen:
                    seen.add(c)
                    known.append(c)
            singular = (
                list(ent.missing_runtimes_at(perspective, known))
                if known
                else []
            )
            assert row["missing_runtimes_at"] == singular, (
                perspective,
                bundle,
                singular,
            )


# -- Helper: perspective divergence from LIVE --------------------------------


def test_helper_features_oss_diverges_from_live_grace(ent):
    """At ``oss`` a paid-feature bundle reports the item as missing in
    grace, whereas the LIVE :func:`missing_features_bundle_batch`
    reports ``missing=[]`` on the same bundle via grace pass-through.
    That divergence is the whole point of the ``_at`` slot."""
    live = ent.missing_features_bundle_batch([["fleet"]])
    at_oss = ent.missing_features_bundle_batch_at("oss", [["fleet"]])
    assert live[0]["missing"] == []  # grace pass-through
    assert at_oss[0]["missing_features_at"] == ["fleet"]  # static per-tier


def test_helper_runtimes_oss_diverges_from_live_grace(ent):
    live = ent.missing_runtimes_bundle_batch([["claude_code"]])
    at_oss = ent.missing_runtimes_bundle_batch_at("oss", [["claude_code"]])
    assert live[0]["missing"] == []
    assert at_oss[0]["missing_runtimes_at"] == ["claude_code"]


# -- Helper: grace vs enforce invariance -------------------------------------


def test_helper_features_grace_enforce_identical(ent, enforced):
    """Perspective-shaped fold is byte-identical under grace vs enforce."""
    bundles = [["fleet", "sso"], ["otel_export"], ["bogus"], []]
    for perspective in ("oss", "cloud_starter", "pro", "enterprise"):
        rows_grace = ent.missing_features_bundle_batch_at(perspective, bundles)
        rows_enf = enforced.missing_features_bundle_batch_at(
            perspective, bundles
        )
        assert rows_grace == rows_enf, perspective


def test_helper_runtimes_grace_enforce_identical(ent, enforced):
    bundles = [["openclaw"], ["claude_code"], ["bogus_rt"], []]
    for perspective in ("oss", "cloud_starter", "pro", "enterprise"):
        rows_grace = ent.missing_runtimes_bundle_batch_at(perspective, bundles)
        rows_enf = enforced.missing_runtimes_bundle_batch_at(
            perspective, bundles
        )
        assert rows_grace == rows_enf, perspective


# -- Helper: complement invariant with has_...bundle_batch_at ----------------


def test_helper_features_complement_invariant_with_has(ent):
    """For every fully-known bundle,
    ``bool(missing_features_at) == (not has_features_at)`` -- pins the
    row-detail seat as the exact perspective-shaped negation of the
    boolean-fold seat."""
    bundles = [
        ["fleet", "sso"],
        ["otel_export"],
        ["fleet"],
        ["sso"],
    ]
    for perspective in ("oss", "cloud_starter", "pro", "enterprise"):
        has_rows = ent.has_features_bundle_batch_at(perspective, bundles)
        miss_rows = ent.missing_features_bundle_batch_at(perspective, bundles)
        for h, m in zip(has_rows, miss_rows):
            # Fully-known bundle -> unknown[] is empty on both sides.
            assert h["unknown"] == [] and m["unknown"] == []
            assert bool(m["missing_features_at"]) == (
                not h["has_features_at"]
            ), (perspective, h, m)


def test_helper_runtimes_complement_invariant_with_has(ent):
    bundles = [
        ["openclaw"],
        ["claude_code"],
        ["claude_code", "codex"],
    ]
    for perspective in ("oss", "cloud_starter", "pro", "enterprise"):
        has_rows = ent.has_runtimes_bundle_batch_at(perspective, bundles)
        miss_rows = ent.missing_runtimes_bundle_batch_at(perspective, bundles)
        for h, m in zip(has_rows, miss_rows):
            assert h["unknown"] == [] and m["unknown"] == []
            assert bool(m["missing_runtimes_at"]) == (
                not h["has_runtimes_at"]
            ), (perspective, h, m)


# -- API: error paths --------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/entitlement/missing-features-bundle-batch-at",
        "/api/entitlement/missing-runtimes-bundle-batch-at",
    ],
)
def test_api_missing_tier_400(client, path):
    r = client.post(path, json={"bundles": [["fleet"]]})
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing tier"}


@pytest.mark.parametrize(
    "path",
    [
        "/api/entitlement/missing-features-bundle-batch-at",
        "/api/entitlement/missing-runtimes-bundle-batch-at",
    ],
)
def test_api_blank_tier_400(client, path):
    r = client.post(f"{path}?tier=   ", json={"bundles": [["fleet"]]})
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing tier"}


@pytest.mark.parametrize(
    "path",
    [
        "/api/entitlement/missing-features-bundle-batch-at",
        "/api/entitlement/missing-runtimes-bundle-batch-at",
    ],
)
def test_api_unknown_tier_404(client, path):
    r = client.post(f"{path}?tier=bogus", json={"bundles": [["fleet"]]})
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


@pytest.mark.parametrize(
    "path",
    [
        "/api/entitlement/missing-features-bundle-batch-at",
        "/api/entitlement/missing-runtimes-bundle-batch-at",
    ],
)
def test_api_missing_bundles_400(client, path):
    r = client.post(f"{path}?tier=pro", json={})
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing bundles"}


@pytest.mark.parametrize(
    "path",
    [
        "/api/entitlement/missing-features-bundle-batch-at",
        "/api/entitlement/missing-runtimes-bundle-batch-at",
    ],
)
def test_api_empty_bundles_400(client, path):
    r = client.post(f"{path}?tier=pro", json={"bundles": []})
    assert r.status_code == 400
    assert r.get_json() == {"error": "empty bundles"}


@pytest.mark.parametrize(
    "path",
    [
        "/api/entitlement/missing-features-bundle-batch-at",
        "/api/entitlement/missing-runtimes-bundle-batch-at",
    ],
)
def test_api_scalar_bundles_400(client, path):
    r = client.post(f"{path}?tier=pro", json={"bundles": 42})
    assert r.status_code == 400
    assert r.get_json() == {"error": "bundles must be a list"}


# -- API: happy path envelope shape ------------------------------------------


def test_api_features_envelope_shape(client):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch-at?tier=enterprise",
        json={"bundles": [["fleet", "sso"], ["bogus"], []]},
    )
    assert r.status_code == 200
    body = r.get_json()
    expected_keys = {
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
        "bundles",
        "count",
    }
    assert set(body) == expected_keys
    assert body["perspective_tier"] == "enterprise"
    assert body["perspective_tier_label"] == "Enterprise"
    assert body["perspective_tier_rank"] == 3
    assert body["count"] == 3
    row_keys = {
        "features",
        "unknown",
        "kind",
        "count",
        "missing_features_at",
    }
    for row in body["bundles"]:
        assert set(row) == row_keys
        assert row["kind"] == "features"


def test_api_runtimes_envelope_shape(client):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch-at?tier=pro",
        json={"bundles": [["claude-code"], ["openclaw"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "pro"
    row_keys = {
        "runtimes",
        "unknown",
        "kind",
        "count",
        "missing_runtimes_at",
    }
    for row in body["bundles"]:
        assert set(row) == row_keys
        assert row["kind"] == "runtimes"


# -- API: fold answers -------------------------------------------------------


def test_api_features_enterprise_grants_all(client):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch-at?tier=enterprise",
        json={"bundles": [["fleet", "sso"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["bundles"][0]["missing_features_at"] == []


def test_api_features_oss_denies_paid(client):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch-at?tier=oss",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 200
    assert r.get_json()["bundles"][0]["missing_features_at"] == ["fleet"]


def test_api_runtimes_alias_canonicalises_through_endpoint(client):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch-at?tier=pro",
        json={"bundles": [["claude-code"]]},
    )
    assert r.status_code == 200
    row = r.get_json()["bundles"][0]
    # Alias canonicalises into the row's runtimes list.
    assert row["runtimes"] == ["claude_code"]
    # Pro grants claude_code -> nothing missing at this perspective.
    assert row["missing_runtimes_at"] == []


def test_api_runtimes_oss_free_runtime_empty(client):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch-at?tier=oss",
        json={"bundles": [["openclaw"]]},
    )
    assert r.status_code == 200
    row = r.get_json()["bundles"][0]
    assert row["runtimes"] == ["openclaw"]
    assert row["missing_runtimes_at"] == []


def test_api_runtimes_oss_denies_paid_runtime(client):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch-at?tier=oss",
        json={"bundles": [["claude_code"]]},
    )
    assert r.status_code == 200
    assert r.get_json()["bundles"][0]["missing_runtimes_at"] == [
        "claude_code"
    ]


# -- API: shorthand ----------------------------------------------------------


def test_api_features_bare_list_shorthand_treated_as_one_bundle(client):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch-at?tier=oss",
        json={"bundles": ["fleet", "sso"]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 1
    assert body["bundles"][0]["features"] == ["fleet", "sso"]
    # OSS grants neither.
    assert set(body["bundles"][0]["missing_features_at"]) == {"fleet", "sso"}


# -- API: per-row parity with helper -----------------------------------------


def test_api_features_row_parity_with_helper(client, ent):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch-at?tier=oss",
        json={"bundles": [["fleet", "sso"], ["bogus"], []]},
    )
    assert r.status_code == 200
    api_rows = r.get_json()["bundles"]
    helper_rows = ent.missing_features_bundle_batch_at(
        "oss", [["fleet", "sso"], ["bogus"], []]
    )
    for api_row, helper_row in zip(api_rows, helper_rows):
        assert api_row["features"] == helper_row["features"]
        assert api_row["unknown"] == helper_row["unknown"]
        assert api_row["kind"] == helper_row["kind"]
        assert api_row["count"] == helper_row["count"]
        assert (
            api_row["missing_features_at"] == helper_row["missing_features_at"]
        )


# -- API: never-5xx on delegate crash ----------------------------------------


def test_api_features_never_5xx_on_helper_crash(client, monkeypatch, ent):
    def boom(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "missing_features_bundle_batch_at", boom)
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch-at?tier=pro",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["bundles"] == []
    assert body["count"] == 0
    assert body["perspective_tier"] == "pro"


def test_api_runtimes_never_5xx_on_helper_crash(client, monkeypatch, ent):
    def boom(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "missing_runtimes_bundle_batch_at", boom)
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch-at?tier=pro",
        json={"bundles": [["claude_code"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["bundles"] == []
    assert body["count"] == 0
    assert body["perspective_tier"] == "pro"
