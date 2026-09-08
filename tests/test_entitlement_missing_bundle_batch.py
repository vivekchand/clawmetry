"""Tests for the bundle-batch ``/api/entitlement/missing-features-bundle-batch``
and ``/api/entitlement/missing-runtimes-bundle-batch`` endpoints (plus
their :func:`clawmetry.entitlements.missing_features_bundle_batch` /
:func:`clawmetry.entitlements.missing_runtimes_bundle_batch` helpers).

Row-detail complement of the sibling boolean-fold
``/has-features-bundle-batch`` / ``/has-runtimes-bundle-batch`` on the
LIVE per-install slot: where the boolean-fold answers "does the CURRENT
install grant this whole bundle?" for N caller-supplied bundles, this
answers "which subset of THIS bundle isn't granted?" for the same N
bundles in ONE round-trip. Reverse-lookup sibling of
``/min-tier-for-features-batch`` / ``/min-tier-for-runtimes-batch`` on
the axis-echo slots (``features`` / ``runtimes`` / ``unknown`` /
``kind`` / ``count``) so a UI can render "cheapest tier that grants it?
/ denied right now?" side by side per bundle off two calls.

These tests pin:

* helper: per-bundle normalisation (whitespace, lowercase, dedup
  preserving first-seen order), unknown-id bucketing, runtime alias
  canonicalisation, empty / all-unknown bundles surface as a stable row
* helper: grace pass-through (paid feature in grace -> ``missing=[]``)
* helper: post-enforce paid feature surfaces in ``missing``
* helper: :data:`FREE_RUNTIMES` (``openclaw``) reports ``missing=[]``
  on the LIVE install regardless of rollout state
* helper: per-row parity with the singular
  :func:`missing_features` / :func:`missing_runtimes` on the known slice
* helper: never-crash on ``None`` / non-iterable / non-list bundle input
* API happy path: 6-key envelope, 5-key row, ``count``, ``kind``
* API single-bundle shorthand (bare-CSV posture)
* API error paths: 400 on missing / non-list / empty ``bundles``
* API cross-endpoint axis-echo parity with
  ``/min-tier-for-features-batch`` / ``/min-tier-for-runtimes-batch``
* API row-shape byte-parity with the singular
  ``/missing-features`` / ``/missing-runtimes`` ``missing`` slot on
  the same known bundle
* API never-5xxs on a monkey-patched delegate crash
* grace vs enforce fold divergence on a paid bundle
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask

# ── Fixtures ─────────────────────────────────────────────────────────────


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
    """Enforcement-on fixture: ``CLAWMETRY_ENFORCE=1`` flips
    ``ent.grace`` off so the grace pass-through collapses and paid
    axes report their post-enforce denial in ``missing``."""
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


@pytest.fixture
def enforced_client(enforced):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── Row / envelope shape constants ───────────────────────────────────────


_FEATURES_ROW_KEYS = {"features", "unknown", "kind", "count", "missing"}
_RUNTIMES_ROW_KEYS = {"runtimes", "unknown", "kind", "count", "missing"}
_ENVELOPE_KEYS = {
    "bundles",
    "count",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# ── helper: bundle normalisation ─────────────────────────────────────────


def test_helper_features_dedups_and_lowers(ent):
    rows = ent.missing_features_bundle_batch(
        [["fleet", "", "SSO", "fleet"], ["otel_export"]]
    )
    assert len(rows) == 2
    assert rows[0]["features"] == ["fleet", "sso"]
    assert rows[0]["unknown"] == []
    assert rows[0]["count"] == 2
    assert rows[0]["kind"] == "features"
    assert rows[1]["features"] == ["otel_export"]


def test_helper_features_buckets_unknown(ent):
    rows = ent.missing_features_bundle_batch([["fleet", "bogus", "Bogus"]])
    r = rows[0]
    assert r["features"] == ["fleet"]
    assert r["unknown"] == ["bogus"]
    assert r["count"] == 1


def test_helper_features_strips_whitespace(ent):
    rows = ent.missing_features_bundle_batch([["  fleet  ", "\tsso\n"]])
    assert rows[0]["features"] == ["fleet", "sso"]


def test_helper_features_empty_bundle_stable_row(ent):
    rows = ent.missing_features_bundle_batch([[]])
    r = rows[0]
    assert r["features"] == []
    assert r["unknown"] == []
    assert r["count"] == 0
    assert r["missing"] == []
    assert r["kind"] == "features"


def test_helper_features_all_unknown_stable_row(ent):
    rows = ent.missing_features_bundle_batch([["bogus1", "bogus2"]])
    r = rows[0]
    assert r["features"] == []
    assert r["unknown"] == ["bogus1", "bogus2"]
    assert r["missing"] == []


def test_helper_features_none_returns_empty(ent):
    assert ent.missing_features_bundle_batch(None) == []


def test_helper_features_non_iterable_returns_empty(ent):
    assert ent.missing_features_bundle_batch(42) == []


def test_helper_features_none_bundle_row_stable(ent):
    rows = ent.missing_features_bundle_batch([None, ["fleet"]])
    assert rows[0] == {
        "features": [],
        "unknown": [],
        "kind": "features",
        "count": 0,
        "missing": [],
    }
    assert rows[1]["features"] == ["fleet"]


def test_helper_features_non_iterable_row_stable(ent):
    rows = ent.missing_features_bundle_batch([42, ["fleet"]])
    assert rows[0]["features"] == []
    assert rows[0]["missing"] == []
    assert rows[1]["features"] == ["fleet"]


def test_helper_runtimes_canonicalises_aliases(ent):
    rows = ent.missing_runtimes_bundle_batch(
        [["claude-code", "codex", "claude_code"]]
    )
    r = rows[0]
    assert r["runtimes"] == ["claude_code", "codex"]
    assert r["unknown"] == []
    assert r["kind"] == "runtimes"


def test_helper_runtimes_buckets_unknown(ent):
    rows = ent.missing_runtimes_bundle_batch([["claude_code", "bogus_rt"]])
    assert rows[0]["runtimes"] == ["claude_code"]
    assert rows[0]["unknown"] == ["bogus_rt"]


def test_helper_runtimes_free_runtime_missing_empty_in_grace(ent):
    """openclaw is FREE_RUNTIMES; missing is empty regardless of rollout."""
    rows = ent.missing_runtimes_bundle_batch([["openclaw"]])
    assert rows[0]["runtimes"] == ["openclaw"]
    assert rows[0]["missing"] == []


def test_helper_runtimes_free_runtime_missing_empty_after_enforce(enforced):
    rows = enforced.missing_runtimes_bundle_batch([["openclaw"]])
    assert rows[0]["missing"] == []


# ── helper: grace pass-through vs post-enforce fold ──────────────────────


def test_helper_features_grace_pass_through(ent):
    """Paid feature (fleet) is granted in grace; missing=[]."""
    rows = ent.missing_features_bundle_batch([["fleet", "sso"]])
    assert rows[0]["features"] == ["fleet", "sso"]
    assert rows[0]["missing"] == []


def test_helper_features_enforce_reports_paid_missing(enforced):
    rows = enforced.missing_features_bundle_batch([["fleet", "sso"]])
    assert rows[0]["features"] == ["fleet", "sso"]
    assert set(rows[0]["missing"]) == {"fleet", "sso"}


def test_helper_runtimes_grace_pass_through(ent):
    """Paid runtime (claude_code) is granted in grace; missing=[]."""
    rows = ent.missing_runtimes_bundle_batch([["claude_code", "codex"]])
    assert rows[0]["runtimes"] == ["claude_code", "codex"]
    assert rows[0]["missing"] == []


def test_helper_runtimes_enforce_reports_paid_missing(enforced):
    rows = enforced.missing_runtimes_bundle_batch([["claude_code", "codex"]])
    assert set(rows[0]["missing"]) == {"claude_code", "codex"}


def test_helper_features_multiple_bundles_grace(ent):
    rows = ent.missing_features_bundle_batch(
        [["fleet"], ["sso", "otel_export"], []]
    )
    assert len(rows) == 3
    assert rows[0]["missing"] == []
    assert rows[1]["missing"] == []
    assert rows[2]["missing"] == []


def test_helper_features_multiple_bundles_enforce(enforced):
    rows = enforced.missing_features_bundle_batch(
        [["fleet"], ["sso", "otel_export"], []]
    )
    assert set(rows[0]["missing"]) == {"fleet"}
    assert set(rows[1]["missing"]) == {"sso", "otel_export"}
    assert rows[2]["missing"] == []


# ── helper: per-row parity with the singular scalar ──────────────────────


@pytest.mark.parametrize(
    "bundle",
    [
        ["fleet", "sso"],
        ["otel_export"],
        ["fleet"],
        ["sso"],
        [],
    ],
)
def test_helper_features_per_row_parity_with_singular_grace(ent, bundle):
    """Per-bundle ``missing`` byte-equals the singular helper on the
    known slice."""
    row = ent.missing_features_bundle_batch([bundle])[0]
    known = [f for f in row["features"]]
    singular = list(ent.missing_features(known)) if known else []
    assert row["missing"] == singular


@pytest.mark.parametrize(
    "bundle",
    [
        ["fleet", "sso"],
        ["otel_export"],
        ["fleet"],
    ],
)
def test_helper_features_per_row_parity_with_singular_enforce(
    enforced, bundle
):
    row = enforced.missing_features_bundle_batch([bundle])[0]
    known = [f for f in row["features"]]
    singular = list(enforced.missing_features(known)) if known else []
    assert row["missing"] == singular


@pytest.mark.parametrize(
    "bundle",
    [
        ["claude-code", "codex"],
        ["openclaw"],
        ["claude_code"],
        [],
    ],
)
def test_helper_runtimes_per_row_parity_with_singular_grace(ent, bundle):
    row = ent.missing_runtimes_bundle_batch([bundle])[0]
    known = [rt for rt in row["runtimes"]]
    singular = list(ent.missing_runtimes(known)) if known else []
    assert row["missing"] == singular


@pytest.mark.parametrize(
    "bundle",
    [
        ["claude-code", "codex"],
        ["openclaw"],
        ["claude_code"],
    ],
)
def test_helper_runtimes_per_row_parity_with_singular_enforce(
    enforced, bundle
):
    row = enforced.missing_runtimes_bundle_batch([bundle])[0]
    known = [rt for rt in row["runtimes"]]
    singular = list(enforced.missing_runtimes(known)) if known else []
    assert row["missing"] == singular


# ── helper: never-raise contract ─────────────────────────────────────────


def test_helper_features_never_raises_on_bad_bundle(ent):
    # Non-string tokens are coerced via str(); mixed garbage should not crash.
    rows = ent.missing_features_bundle_batch(
        [[None, 42, object()], ["fleet"]]
    )
    assert len(rows) == 2


def test_helper_runtimes_never_raises_on_bad_bundle(ent):
    rows = ent.missing_runtimes_bundle_batch(
        [[None, 42, object()], ["claude_code"]]
    )
    assert len(rows) == 2


# ── API: happy path ──────────────────────────────────────────────────────


def test_api_features_happy(client, ent):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch",
        json={"bundles": [["fleet", "sso"], ["otel_export"], []]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _ENVELOPE_KEYS
    assert j["count"] == 3
    assert len(j["bundles"]) == 3
    for row in j["bundles"]:
        assert set(row.keys()) == _FEATURES_ROW_KEYS
        assert row["kind"] == "features"
    assert j["bundles"][0]["features"] == ["fleet", "sso"]
    # grace pass-through
    assert j["bundles"][0]["missing"] == []
    assert j["bundles"][2]["features"] == []
    assert j["bundles"][2]["missing"] == []


def test_api_runtimes_happy(client, ent):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch",
        json={"bundles": [["claude-code", "codex"], ["openclaw"]]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _ENVELOPE_KEYS
    assert j["count"] == 2
    for row in j["bundles"]:
        assert set(row.keys()) == _RUNTIMES_ROW_KEYS
        assert row["kind"] == "runtimes"
    assert j["bundles"][0]["runtimes"] == ["claude_code", "codex"]
    assert j["bundles"][1]["runtimes"] == ["openclaw"]
    # FREE_RUNTIMES: missing is empty regardless
    assert j["bundles"][1]["missing"] == []


def test_api_features_single_bundle_shorthand(client, ent):
    """Bare list of strings is treated as ONE bundle (matches the
    singular endpoint's bare-CSV posture)."""
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch",
        json={"bundles": ["fleet", "sso"]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 1
    assert j["bundles"][0]["features"] == ["fleet", "sso"]


def test_api_features_unknown_bucketed(client, ent):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch",
        json={"bundles": [["fleet", "bogus"]]},
    )
    assert r.status_code == 200
    row = r.get_json()["bundles"][0]
    assert row["features"] == ["fleet"]
    assert row["unknown"] == ["bogus"]
    # unknown does NOT leak into missing; grace pass-through keeps it empty
    assert row["missing"] == []


def test_api_runtimes_alias_canonicalised(client, ent):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch",
        json={"bundles": [["claude-code", "claude_code"]]},
    )
    row = r.get_json()["bundles"][0]
    assert row["runtimes"] == ["claude_code"]
    assert row["unknown"] == []


# ── API: error paths ─────────────────────────────────────────────────────


def test_api_features_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch", json={}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_features_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch",
        json={"bundles": []},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "empty bundles"


def test_api_features_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch",
        json={"bundles": 42},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundles must be a list"


def test_api_features_no_body_400(client):
    r = client.post("/api/entitlement/missing-features-bundle-batch")
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_runtimes_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch", json={}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_runtimes_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch",
        json={"bundles": []},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "empty bundles"


def test_api_runtimes_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch",
        json={"bundles": {"not": "a list"}},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundles must be a list"


# ── API: cross-endpoint axis-echo parity ─────────────────────────────────


def test_api_features_axis_echo_parity_with_min_tier_batch(client):
    """features / unknown / kind / count byte-equal
    /min-tier-for-features-batch on the same body."""
    body = {
        "bundles": [
            ["FLEET", "fleet", "sso"],
            ["bogus", "otel_export"],
            [],
        ]
    }
    missing_bat = client.post(
        "/api/entitlement/missing-features-bundle-batch", json=body
    ).get_json()
    tier_bat = client.post(
        "/api/entitlement/min-tier-for-features-batch", json=body
    ).get_json()
    axes = ("features", "unknown", "kind", "count")
    for m, t in zip(missing_bat["bundles"], tier_bat["bundles"]):
        for k in axes:
            assert m[k] == t[k]


def test_api_runtimes_axis_echo_parity_with_min_tier_batch(client):
    body = {
        "bundles": [
            ["claude-code", "codex"],
            ["openclaw"],
            ["bogus_rt"],
        ]
    }
    missing_bat = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch", json=body
    ).get_json()
    tier_bat = client.post(
        "/api/entitlement/min-tier-for-runtimes-batch", json=body
    ).get_json()
    axes = ("runtimes", "unknown", "kind", "count")
    for m, t in zip(missing_bat["bundles"], tier_bat["bundles"]):
        for k in axes:
            assert m[k] == t[k]


# ── API: row-shape parity with the singular missing endpoints ────────────


def test_api_features_row_missing_matches_singular_endpoint(client):
    """Per-bundle ``missing`` byte-equals the singular endpoint's
    ``missing`` slot for the same known bundle."""
    bundle = ["fleet", "sso"]
    batch = client.post(
        "/api/entitlement/missing-features-bundle-batch",
        json={"bundles": [bundle]},
    ).get_json()
    singular = client.get(
        "/api/entitlement/missing-features?features=" + ",".join(bundle)
    ).get_json()
    assert batch["bundles"][0]["missing"] == singular["missing"]


def test_api_runtimes_row_missing_matches_singular_endpoint(client):
    bundle = ["claude_code", "codex"]
    batch = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch",
        json={"bundles": [bundle]},
    ).get_json()
    singular = client.get(
        "/api/entitlement/missing-runtimes?runtimes=" + ",".join(bundle)
    ).get_json()
    assert batch["bundles"][0]["missing"] == singular["missing"]


# ── API: never-5xxs on delegate crash ────────────────────────────────────


def test_api_features_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "missing_features_bundle_batch", _boom)
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []
    assert j["count"] == 0


def test_api_runtimes_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "missing_runtimes_bundle_batch", _boom)
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch",
        json={"bundles": [["claude_code"]]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []


# ── grace vs enforce fold divergence ─────────────────────────────────────


def test_api_features_grace_fold_pass_through(client):
    """Under grace the LIVE resolver pass-through keeps paid features
    granted, so ``missing`` is empty."""
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch",
        json={"bundles": [["fleet"]]},
    )
    j = r.get_json()
    assert j["bundles"][0]["features"] == ["fleet"]
    assert j["bundles"][0]["missing"] == []


def test_api_features_enforce_fold_denies_paid(enforced_client):
    """Under enforce the LIVE resolver denies paid features, so
    ``missing`` surfaces the whole bundle."""
    r = enforced_client.post(
        "/api/entitlement/missing-features-bundle-batch",
        json={"bundles": [["fleet"]]},
    )
    j = r.get_json()
    assert j["bundles"][0]["features"] == ["fleet"]
    assert j["bundles"][0]["missing"] == ["fleet"]


def test_api_runtimes_grace_fold_pass_through(client):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch",
        json={"bundles": [["claude_code"]]},
    )
    j = r.get_json()
    assert j["bundles"][0]["runtimes"] == ["claude_code"]
    assert j["bundles"][0]["missing"] == []


def test_api_runtimes_enforce_fold_denies_paid(enforced_client):
    r = enforced_client.post(
        "/api/entitlement/missing-runtimes-bundle-batch",
        json={"bundles": [["claude_code"]]},
    )
    j = r.get_json()
    assert j["bundles"][0]["runtimes"] == ["claude_code"]
    assert j["bundles"][0]["missing"] == ["claude_code"]


# ── envelope resolver-slot stability ─────────────────────────────────────


def test_api_features_envelope_grace_flags(client):
    r = client.post(
        "/api/entitlement/missing-features-bundle-batch",
        json={"bundles": [["fleet"]]},
    )
    j = r.get_json()
    assert j["grace"] is True
    assert j["enforced"] is False


def test_api_runtimes_envelope_grace_flags(client):
    r = client.post(
        "/api/entitlement/missing-runtimes-bundle-batch",
        json={"bundles": [["claude_code"]]},
    )
    j = r.get_json()
    assert j["grace"] is True
    assert j["enforced"] is False
