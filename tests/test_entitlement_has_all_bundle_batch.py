"""Tests for the aggregate bundle-batch boolean-fold
``/api/entitlement/has-all-bundle-batch`` and
``/api/entitlement/has-all-bundle-batch-at`` endpoints (plus their
:func:`clawmetry.entitlements.has_all_bundle_batch` /
:func:`clawmetry.entitlements.has_all_bundle_batch_at` helpers).

Fills the bundle-axis batch boolean-fold slot for the aggregate 5-axis
``/api/entitlement/has-all`` singular endpoint (which folds ONE aggregate
bundle across features + runtimes + channels + retention + nodes to ONE
``has_all`` boolean) so a paywall matrix or upgrade-walkthrough surface
comparing several hypothetical *whole* configs ("Starter-shaped install
vs Pro-shaped install vs Enterprise-shaped install") reads the grant
answer off ONE round-trip instead of N calls to ``/has-all``. Symmetric
to ``/required-tier-bundle-batch`` on the reverse-lookup slot: same POST
body, same per-row axis echoes, only the fold slot diverges
(``has_all`` bool vs ``required_tier`` id).

Distinct from ``/has-all-at-batch`` (which fixes ONE bundle and sweeps N
perspective tiers): this fixes N bundles and reads the LIVE per-install
grant, and its ``_at`` sibling fixes N bundles at ONE perspective.

These tests pin:

* helper: per-bundle normalisation (feature/runtime CSV, runtime alias
  canonicalisation, capacity int coercion, blank / non-int axes collapse
  to ``None``, empty bundle surfaces as a stable row)
* helper: per-row parity with the singular :func:`has_all` scalar
* helper: never-crash contract on ``None`` / non-iterable / non-dict
  bundle inputs
* helper: perspective-shaping of the ``_at`` variant (deliberate
  divergence from the LIVE helper at OSS in grace: paid feature -> False)
* helper: perspective-validation ``None`` posture on the ``_at`` variant
* API happy path: shape, resolver envelope, ``count``
* API error paths: 400 on missing / non-list / empty ``bundles``
* API single-dict shorthand
* API per-row body byte-equals the bare singular endpoint
* API ``_at`` perspective envelope keys + 400 on missing ``tier=``,
  404 on unknown ``tier=``
* API never-5xxs on a delegate crash
* Grace vs enforce parity on the LIVE endpoint; grace-independence on
  the ``_at`` endpoint's ``has_all_at`` fold
* Cross-endpoint parity vs ``/required-tier-bundle-batch``: same axis
  echoes on the same bundle
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask

# -- Fixtures ------------------------------------------------------------------


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
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


@pytest.fixture
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# -- Row shape constants -------------------------------------------------------


_LIVE_ROW_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "has_all",
}

_AT_ROW_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "has_all_at",
}

_LIVE_ENVELOPE_KEYS = {
    "bundles",
    "count",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_AT_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "bundles",
    "count",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# -- helper: bundle normalisation ---------------------------------------------


def test_helper_batch_folds_across_all_five_axes(ent):
    rows = ent.has_all_bundle_batch(
        [{"features": ["fleet"], "runtimes": ["claude_code"],
          "channels": 5, "retention_days": 30, "nodes": 2}]
    )
    assert len(rows) == 1
    r = rows[0]
    assert set(r.keys()) == _LIVE_ROW_KEYS
    assert r["features"] == ["fleet"]
    assert r["runtimes"] == ["claude_code"]
    assert r["channels"] == 5
    assert r["retention_days"] == 30
    assert r["nodes"] == 2
    # Grace pass-through: LIVE fold reports True for every fully-known
    # bundle while ``ent.grace`` is on.
    assert r["has_all"] is True


def test_helper_batch_normalises_features_csv(ent):
    rows = ent.has_all_bundle_batch(
        [{"features": ["FLEET", "fleet", "", "otel_export"]}]
    )
    assert rows[0]["features"] == ["fleet", "otel_export"]


def test_helper_batch_canonicalises_runtime_aliases(ent):
    rows = ent.has_all_bundle_batch(
        [{"runtimes": ["claude-code", "codex", "claude_code"]}]
    )
    assert rows[0]["runtimes"] == ["claude_code", "codex"]


def test_helper_batch_capacity_coerces_ints(ent):
    rows = ent.has_all_bundle_batch(
        [{"channels": "5", "retention_days": "30", "nodes": "2"}]
    )
    assert rows[0]["channels"] == 5
    assert rows[0]["retention_days"] == 30
    assert rows[0]["nodes"] == 2


def test_helper_batch_capacity_non_int_collapses_to_none(ent):
    """A typo on ``retention_days`` must NOT silently grant on the
    aggregate -- it collapses to ``None`` (unset). Matches
    :func:`min_tier_for_all_batch` posture."""
    rows = ent.has_all_bundle_batch(
        [{"channels": "abc", "retention_days": "", "nodes": None}]
    )
    assert rows[0]["channels"] is None
    assert rows[0]["retention_days"] is None
    assert rows[0]["nodes"] is None
    # Empty bundle after coercion -> no axes supplied -> False.
    assert rows[0]["has_all"] is False


def test_helper_batch_empty_bundle_is_stable_row(ent):
    rows = ent.has_all_bundle_batch([{}])
    assert len(rows) == 1
    r = rows[0]
    assert set(r.keys()) == _LIVE_ROW_KEYS
    assert r["features"] == []
    assert r["runtimes"] == []
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None
    # Empty bundle: no axes supplied -> False (matches has_all).
    assert r["has_all"] is False


def test_helper_batch_non_dict_row_collapses_to_empty_row(ent):
    rows = ent.has_all_bundle_batch(
        [{"features": ["fleet"]}, "not a dict", 42]
    )
    assert len(rows) == 3
    assert rows[0]["features"] == ["fleet"]
    for r in rows[1:]:
        assert r["features"] == []
        assert r["has_all"] is False


def test_helper_batch_none_returns_empty(ent):
    assert ent.has_all_bundle_batch(None) == []


def test_helper_batch_non_iterable_returns_empty(ent):
    assert ent.has_all_bundle_batch(42) == []


def test_helper_batch_empty_list_returns_empty(ent):
    assert ent.has_all_bundle_batch([]) == []


# -- helper: per-row parity with the singular has_all -------------------------


def test_helper_batch_per_row_parity_with_has_all(ent):
    """Per-row ``has_all`` byte-equals :func:`has_all` for the same
    (canonicalised) bundle."""
    bundles = [
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5},
        {"retention_days": 30, "nodes": 2},
        {"features": ["sso"]},
        {},
    ]
    rows = ent.has_all_bundle_batch(bundles)
    for row in rows:
        expected = ent.has_all(
            features=row["features"] or None,
            runtimes=row["runtimes"] or None,
            channels=row["channels"],
            retention_days=row["retention_days"],
            nodes=row["nodes"],
        )
        assert row["has_all"] is bool(expected)


def test_helper_batch_paid_bundle_true_in_grace(ent):
    """Grace pass-through contract: paid bundle -> True in grace."""
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    bundle = {"features": [paid_f], "runtimes": [paid_r], "channels": 999}
    assert ent.has_all_bundle_batch([bundle])[0]["has_all"] is True


def test_helper_batch_paid_bundle_false_after_enforcement(enforced):
    """Post-enforcement: paid bundle -> False (matches has_all)."""
    paid_f = next(iter(enforced.PAID_FEATURES))
    paid_r = next(iter(enforced.PAID_RUNTIMES))
    bundle = {"features": [paid_f], "runtimes": [paid_r], "channels": 999}
    assert enforced.has_all_bundle_batch([bundle])[0]["has_all"] is False


# -- helper: _at perspective shaping ------------------------------------------


def test_helper_at_batch_oss_denies_paid_bundle_even_in_grace(ent):
    """Whole point of the ``_at`` slot: OSS statically does not grant
    paid features, so the _at variant reports ``has_all_at=False`` even
    while the LIVE helper reports ``has_all=True`` via grace pass-through
    on the same bundle."""
    paid_f = next(iter(ent.PAID_FEATURES))
    live = ent.has_all_bundle_batch([{"features": [paid_f]}])[0]
    at = ent.has_all_bundle_batch_at("oss", [{"features": [paid_f]}])[0]
    assert live["has_all"] is True
    assert at["has_all_at"] is False


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_helper_at_batch_free_bundle_true_at_every_tier(ent, perspective):
    free_f = next(iter(ent.FREE_FEATURES))
    free_r = next(iter(ent.FREE_RUNTIMES))
    rows = ent.has_all_bundle_batch_at(
        perspective,
        [{"features": [free_f], "runtimes": [free_r], "channels": 1}],
    )
    assert rows[0]["has_all_at"] is True


def test_helper_at_batch_paid_bundle_true_at_cloud_pro(ent):
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    rows = ent.has_all_bundle_batch_at(
        "cloud_pro",
        [{"features": [paid_f], "runtimes": [paid_r]}],
    )
    assert rows[0]["has_all_at"] is True


def test_helper_at_batch_row_shape(ent):
    rows = ent.has_all_bundle_batch_at(
        "cloud_pro", [{"features": ["fleet"], "runtimes": ["claude_code"]}]
    )
    assert len(rows) == 1
    assert set(rows[0].keys()) == _AT_ROW_KEYS


def test_helper_at_batch_grace_independent(ent, monkeypatch):
    """The ``_at`` variant is grace-independent by construction: the
    per-row fold reads static per-tier tables so grace vs enforce yields
    byte-identical rows for the same ``(perspective, bundle)`` pair."""
    bundles = [
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5, "retention_days": 30, "nodes": 2},
        {},
    ]
    perspectives = ("oss", "cloud_pro", "enterprise")
    grace_rows = {p: ent.has_all_bundle_batch_at(p, bundles) for p in perspectives}
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    for p in perspectives:
        assert ent.has_all_bundle_batch_at(p, bundles) == grace_rows[p]


def test_helper_at_batch_unknown_perspective_none(ent):
    assert ent.has_all_bundle_batch_at("bogus", [{"features": ["fleet"]}]) is None
    assert ent.has_all_bundle_batch_at("", [{"features": ["fleet"]}]) is None
    assert ent.has_all_bundle_batch_at(None, [{"features": ["fleet"]}]) is None


def test_helper_at_batch_valid_perspective_none_bundles_empty_list(ent):
    """Perspective valid but bundles ``None`` -> stable ``[]``, not
    ``None`` (which is reserved for perspective failure)."""
    assert ent.has_all_bundle_batch_at("cloud_pro", None) == []
    assert ent.has_all_bundle_batch_at("cloud_pro", []) == []


def test_helper_at_batch_non_iterable_bundles(ent):
    assert ent.has_all_bundle_batch_at("cloud_pro", 42) == []


# -- API: happy path ----------------------------------------------------------


def test_api_batch_happy(client, ent):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch",
        json={"bundles": [
            {"features": ["fleet"], "runtimes": ["claude_code"]},
            {"channels": 5, "retention_days": 30, "nodes": 2},
            {},
        ]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _LIVE_ENVELOPE_KEYS
    assert j["count"] == 3
    assert len(j["bundles"]) == 3
    for row in j["bundles"]:
        assert set(row.keys()) == _LIVE_ROW_KEYS
    assert j["bundles"][0]["features"] == ["fleet"]
    assert j["bundles"][0]["runtimes"] == ["claude_code"]
    assert j["bundles"][1]["channels"] == 5
    assert j["bundles"][1]["retention_days"] == 30
    # Empty bundle at index 2 -> has_all False.
    assert j["bundles"][2]["has_all"] is False


def test_api_batch_grace_paid_bundle_true(client, ent):
    """Grace posture: paid bundle at the LIVE endpoint reports has_all=True
    in grace (matches the singular /has-all endpoint's grace pass-through)."""
    paid_f = next(iter(ent.PAID_FEATURES))
    r = client.post(
        "/api/entitlement/has-all-bundle-batch",
        json={"bundles": [{"features": [paid_f]}]},
    )
    j = r.get_json()
    assert j["bundles"][0]["has_all"] is True
    assert j["grace"] is True


def test_api_batch_single_dict_shorthand(client, ent):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch",
        json={"bundles": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 1
    assert j["bundles"][0]["features"] == ["fleet"]


def test_api_batch_capacity_string_coerced(client, ent):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch",
        json={"bundles": [{"channels": "5", "retention_days": "abc"}]},
    )
    j = r.get_json()
    assert j["bundles"][0]["channels"] == 5
    # Non-int capacity collapses to null.
    assert j["bundles"][0]["retention_days"] is None


# -- API: error paths ---------------------------------------------------------


def test_api_batch_missing_bundles_400(client):
    r = client.post("/api/entitlement/has-all-bundle-batch", json={})
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_batch_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch", json={"bundles": []}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "empty bundles"


def test_api_batch_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch", json={"bundles": 42}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundles must be a list"


def test_api_batch_no_body_400(client):
    r = client.post("/api/entitlement/has-all-bundle-batch")
    # Empty body -> missing bundles -> 400
    assert r.status_code == 400


# -- API: per-row body byte-equals the singular /has-all ---------------------


def test_api_batch_row_matches_singular_has_all(client, ent):
    """Each per-bundle row's ``has_all`` byte-equals the singular
    ``/has-all`` endpoint's ``has_all`` for the same bundle."""
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"]}
    batch = client.post(
        "/api/entitlement/has-all-bundle-batch",
        json={"bundles": [bundle]},
    ).get_json()
    row = batch["bundles"][0]
    singular = client.get(
        "/api/entitlement/has-all"
        "?features=fleet&runtimes=claude_code"
    ).get_json()
    assert row["has_all"] is bool(singular["has_all"])
    assert row["features"] == singular["features"]
    assert row["runtimes"] == singular["runtimes"]


# -- API: cross-endpoint parity vs /required-tier-bundle-batch ---------------


def test_api_batch_axis_echo_matches_required_tier_bundle_batch(client, ent):
    """Per-row axis echoes byte-equal the sibling
    ``/required-tier-bundle-batch``: same normalisation, same alias
    canonicalisation, same capacity coercion. Only the fold slot
    diverges (``has_all`` vs ``required_tier``)."""
    bundles = [
        {"features": ["FLEET", "fleet"], "runtimes": ["claude-code"]},
        {"channels": "5", "retention_days": "30", "nodes": "2"},
        {"channels": "abc"},
    ]
    live = client.post(
        "/api/entitlement/has-all-bundle-batch", json={"bundles": bundles}
    ).get_json()
    rev = client.post(
        "/api/entitlement/required-tier-bundle-batch",
        json={"bundles": bundles},
    ).get_json()
    assert live["count"] == rev["count"]
    for a, b in zip(live["bundles"], rev["bundles"]):
        assert a["features"] == b["features"]
        assert a["runtimes"] == b["runtimes"]
        assert a["channels"] == b["channels"]
        assert a["retention_days"] == b["retention_days"]
        assert a["nodes"] == b["nodes"]


# -- API: _at perspective envelope + validation ------------------------------


def test_api_at_batch_happy(client, ent):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=cloud_pro",
        json={"bundles": [
            {"features": ["fleet"]},
            {"runtimes": ["claude_code"]},
        ]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _AT_ENVELOPE_KEYS
    assert j["perspective_tier"] == "cloud_pro"
    assert j["perspective_tier_label"]
    assert j["count"] == 2
    for row in j["bundles"]:
        assert set(row.keys()) == _AT_ROW_KEYS
    assert j["bundles"][0]["features"] == ["fleet"]
    assert j["bundles"][1]["runtimes"] == ["claude_code"]


def test_api_at_batch_oss_denies_paid_feature_even_in_grace(client, ent):
    """The whole point of the ``_at`` slot: at ``tier=oss`` a paid-feature
    bundle reports ``has_all_at=false`` even while grace is on and the
    LIVE ``/has-all-bundle-batch`` reports ``has_all=true`` for the same
    bundle."""
    paid_f = next(iter(ent.PAID_FEATURES))
    live = client.post(
        "/api/entitlement/has-all-bundle-batch",
        json={"bundles": [{"features": [paid_f]}]},
    ).get_json()
    at = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=oss",
        json={"bundles": [{"features": [paid_f]}]},
    ).get_json()
    assert live["bundles"][0]["has_all"] is True
    assert at["bundles"][0]["has_all_at"] is False
    # But both share the same grace envelope value (LIVE resolver unchanged).
    assert live["grace"] is True and at["grace"] is True


def test_api_at_batch_unknown_tier_404(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=bogus",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 404
    j = r.get_json()
    assert j["error"] == "unknown tier"
    assert j["which"] == "tier"
    assert j["tier"] == "bogus"


def test_api_at_batch_missing_tier_400(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch-at",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_api_at_batch_blank_tier_400(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=%20",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_api_at_batch_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=cloud_pro", json={}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_at_batch_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=cloud_pro",
        json={"bundles": []},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "empty bundles"


def test_api_at_batch_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=cloud_pro",
        json={"bundles": 42},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundles must be a list"


def test_api_at_batch_tier_case_and_whitespace_normalised(client, ent):
    r = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=%20CLOUD_PRO%20",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "cloud_pro"


# -- API: _at row body byte-equals the helper for known perspectives ---------


@pytest.mark.parametrize(
    "perspective",
    ["cloud_free", "trial", "cloud_starter", "cloud_pro", "pro", "enterprise"],
)
def test_api_at_batch_row_matches_helper(client, ent, perspective):
    bundles = [
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5, "retention_days": 30, "nodes": 2},
        {},
    ]
    resp = client.post(
        f"/api/entitlement/has-all-bundle-batch-at?tier={perspective}",
        json={"bundles": bundles},
    )
    j = resp.get_json()
    helper_rows = ent.has_all_bundle_batch_at(perspective, bundles)
    assert len(j["bundles"]) == len(helper_rows)
    for a, b in zip(j["bundles"], helper_rows):
        assert a["has_all_at"] is bool(b["has_all_at"])
        assert a["features"] == b["features"]
        assert a["runtimes"] == b["runtimes"]
        assert a["channels"] == b["channels"]
        assert a["retention_days"] == b["retention_days"]
        assert a["nodes"] == b["nodes"]


# -- API: never-5xxs on a delegate crash --------------------------------------


def test_api_batch_never_5xxs_on_delegate_crash(client, ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "has_all_bundle_batch", _boom)
    r = client.post(
        "/api/entitlement/has-all-bundle-batch",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []
    assert j["count"] == 0
    assert set(j.keys()) == _LIVE_ENVELOPE_KEYS


def test_api_at_batch_never_5xxs_on_delegate_crash(client, ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "has_all_bundle_batch_at", _boom)
    r = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=cloud_pro",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []
    assert j["count"] == 0
    assert j["perspective_tier"] == "cloud_pro"
    assert set(j.keys()) == _AT_ENVELOPE_KEYS


# -- API: grace vs enforce parity --------------------------------------------


def test_api_batch_grace_vs_enforce_row_diverges_on_paid_bundle(
    client, ent, monkeypatch
):
    """The LIVE endpoint follows grace: paid bundle -> True in grace,
    False in enforce."""
    paid_f = next(iter(ent.PAID_FEATURES))
    grace = client.post(
        "/api/entitlement/has-all-bundle-batch",
        json={"bundles": [{"features": [paid_f]}]},
    ).get_json()
    assert grace["bundles"][0]["has_all"] is True
    assert grace["grace"] is True

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    enforce_client = app.test_client()
    enforce = enforce_client.post(
        "/api/entitlement/has-all-bundle-batch",
        json={"bundles": [{"features": [paid_f]}]},
    ).get_json()
    assert enforce["bundles"][0]["has_all"] is False
    assert enforce["grace"] is False


def test_api_at_batch_row_grace_independent(client, ent, monkeypatch):
    """The ``_at`` endpoint's ``has_all_at`` fold is grace-independent
    by construction (backed by static per-tier tables). Grace vs enforce
    yields byte-identical row bodies for the same perspective+bundle."""
    bundles = [
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5, "retention_days": 30, "nodes": 2},
        {},
    ]
    grace = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=oss",
        json={"bundles": bundles},
    ).get_json()

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    enforce_client = app.test_client()
    enforce = enforce_client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=oss",
        json={"bundles": bundles},
    ).get_json()
    assert grace["bundles"] == enforce["bundles"]
