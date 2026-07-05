"""Tests for ``clawmetry.entitlements.tier_diff_at(perspective, from, to)``
+ the ``GET /api/entitlement/tier-diff-at`` endpoint.

Fills the ``_at`` scalar slot of the ``tier_diff`` family alongside the
existing ``tier_diff`` (arbitrary-endpoint diff) and ``tier_diff_at_batch``
(what-if + batch fan-out over every purchasable target). Same relationship
to :func:`tier_diff` that :func:`tier_path_at` has to :func:`tier_path`:
the ``perspective`` argument is a URL-uniform slot so an ``_at`` scalar
tooltip can call ``X_at(perspective, from, to)`` uniformly across
:func:`capacity_diff_at` / :func:`tier_unlocks_at` / :func:`tier_locks_at`
/ ``tier_diff_at``, even though ``tier_diff`` is already arbitrary-
endpoint and the underlying diff is inherently perspective-independent.

Pins:

* full payload shape (from/to, direction tag, added/lost lists,
  capacity_changes dict) delegated byte-identically to :func:`tier_diff`
* perspective validated against :data:`_TIER_ORDER` but does NOT shape
  rows -- ``tier_diff_at(p, f, t) == tier_diff(f, t)`` for every ``p``
  in :data:`_TIER_ORDER` (parity invariant)
* whitespace / case normalisation on all three ids
* ``trial`` accepted as perspective (matches every other ``_at`` sibling)
  AND as ``from`` / ``to`` (matches :func:`tier_diff`)
* identity ``(from == to)`` collapses to ``direction="identity"`` with
  empty marginal lists
* swap-the-endpoints invariant is preserved through the ``_at`` prefix:
  ``tier_diff_at(p, X, Y)['added_features']`` byte-equals
  ``tier_diff_at(p, Y, X)['lost_features']`` for every valid ``p``
* unknown perspective / from / to returns ``None`` (and ``404`` on the
  endpoint with a ``which: "tier" | "from" | "to"`` marker)
* never raises: a builder failure short-circuits to ``None``
* grace vs enforce yields byte-identical rows (decoupled from resolver)
* API surface: 400 on missing args, 404 on unknown ids with the
  ``which`` marker, 200 on a happy path with the perspective echo on
  top of the ``/tier-diff`` shape
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


_EXPECTED_TIER_DIFF_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "added_features",
    "lost_features",
    "added_runtimes",
    "lost_runtimes",
    "capacity_changes",
}

_EXTRA_AT_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "perspective_tier_label",
}


# ── shape ────────────────────────────────────────────────────────────────────


def test_tier_diff_at_shape(ent):
    body = ent.tier_diff_at(ent.TIER_TRIAL, ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert body is not None
    assert set(body.keys()) == _EXPECTED_TIER_DIFF_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_CLOUD_PRO
    assert body["direction"] == "upgrade"


def test_tier_diff_at_returns_dict_for_identity(ent):
    body = ent.tier_diff_at(
        ent.TIER_TRIAL, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO
    )
    assert body is not None
    assert body["direction"] == "identity"
    assert body["added_features"] == []
    assert body["lost_features"] == []
    assert body["added_runtimes"] == []
    assert body["lost_runtimes"] == []


# ── parity vs tier_diff ──────────────────────────────────────────────────────


def test_tier_diff_at_parity_across_every_perspective(ent):
    """The core invariant: perspective is validated but does not shape
    rows. For every ``p`` in :data:`_TIER_ORDER`,
    ``tier_diff_at(p, f, t) == tier_diff(f, t)`` byte-for-byte.
    """
    for p in ent._TIER_ORDER:
        for f in ent._TIER_FEATURES:
            for t in ent._TIER_FEATURES:
                assert ent.tier_diff_at(p, f, t) == ent.tier_diff(f, t), (
                    p,
                    f,
                    t,
                )


def test_tier_diff_at_matches_scalar_diff_for_representative_pairs(ent):
    for f, t in [
        (ent.TIER_OSS, ent.TIER_CLOUD_PRO),
        (ent.TIER_CLOUD_PRO, ent.TIER_OSS),
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_CLOUD_PRO, ent.TIER_PRO),  # lateral (same rank 2)
        (ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO),  # identity
        (ent.TIER_TRIAL, ent.TIER_CLOUD_PRO),
    ]:
        assert ent.tier_diff_at(
            ent.TIER_CLOUD_STARTER, f, t
        ) == ent.tier_diff(f, t)


# ── swap-endpoints invariant preserved through _at ──────────────────────────


def test_tier_diff_at_swap_endpoints_invariant(ent):
    """The set-identity ``added_*`` mirrors swapped ``lost_*`` invariant
    that :func:`tier_diff` pins holds through the ``_at`` prefix.
    """
    for p in ent._TIER_ORDER:
        forward = ent.tier_diff_at(p, ent.TIER_OSS, ent.TIER_CLOUD_PRO)
        reverse = ent.tier_diff_at(p, ent.TIER_CLOUD_PRO, ent.TIER_OSS)
        assert forward["added_features"] == reverse["lost_features"]
        assert forward["lost_features"] == reverse["added_features"]
        assert forward["added_runtimes"] == reverse["lost_runtimes"]
        assert forward["lost_runtimes"] == reverse["added_runtimes"]


# ── direction tag ────────────────────────────────────────────────────────────


def test_tier_diff_at_direction_upgrade(ent):
    body = ent.tier_diff_at(ent.TIER_TRIAL, ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert body["direction"] == "upgrade"


def test_tier_diff_at_direction_downgrade(ent):
    body = ent.tier_diff_at(ent.TIER_TRIAL, ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    assert body["direction"] == "downgrade"


def test_tier_diff_at_direction_lateral(ent):
    body = ent.tier_diff_at(
        ent.TIER_TRIAL, ent.TIER_CLOUD_PRO, ent.TIER_PRO
    )
    assert body["direction"] == "lateral"


def test_tier_diff_at_direction_identity(ent):
    body = ent.tier_diff_at(
        ent.TIER_TRIAL, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO
    )
    assert body["direction"] == "identity"


# ── whitespace / case normalisation ─────────────────────────────────────────


def test_tier_diff_at_normalises_perspective(ent):
    body = ent.tier_diff_at("  Trial  ", ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert body is not None
    assert body == ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_PRO)


def test_tier_diff_at_normalises_from(ent):
    body = ent.tier_diff_at(ent.TIER_TRIAL, " OSS ", ent.TIER_CLOUD_PRO)
    assert body is not None
    assert body["from"] == ent.TIER_OSS


def test_tier_diff_at_normalises_to(ent):
    body = ent.tier_diff_at(ent.TIER_TRIAL, ent.TIER_OSS, " Cloud_Pro ")
    assert body is not None
    assert body["to"] == ent.TIER_CLOUD_PRO


# ── trial acceptance ────────────────────────────────────────────────────────


def test_tier_diff_at_accepts_trial_as_perspective(ent):
    body = ent.tier_diff_at(ent.TIER_TRIAL, ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert body is not None


def test_tier_diff_at_accepts_trial_as_from(ent):
    body = ent.tier_diff_at(
        ent.TIER_CLOUD_PRO, ent.TIER_TRIAL, ent.TIER_ENTERPRISE
    )
    assert body is not None
    assert body["from"] == ent.TIER_TRIAL


def test_tier_diff_at_accepts_trial_as_to(ent):
    body = ent.tier_diff_at(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_TRIAL
    )
    assert body is not None
    assert body["to"] == ent.TIER_TRIAL


# ── unknown / bad inputs ────────────────────────────────────────────────────


def test_tier_diff_at_unknown_perspective(ent):
    assert (
        ent.tier_diff_at("bogus", ent.TIER_OSS, ent.TIER_CLOUD_PRO) is None
    )


def test_tier_diff_at_empty_perspective(ent):
    assert ent.tier_diff_at("", ent.TIER_OSS, ent.TIER_CLOUD_PRO) is None


def test_tier_diff_at_none_perspective(ent):
    assert (
        ent.tier_diff_at(None, ent.TIER_OSS, ent.TIER_CLOUD_PRO) is None
    )


def test_tier_diff_at_non_string_perspective(ent):
    assert ent.tier_diff_at(123, ent.TIER_OSS, ent.TIER_CLOUD_PRO) is None


def test_tier_diff_at_unknown_from(ent):
    assert (
        ent.tier_diff_at(ent.TIER_TRIAL, "bogus", ent.TIER_CLOUD_PRO)
        is None
    )


def test_tier_diff_at_unknown_to(ent):
    assert (
        ent.tier_diff_at(ent.TIER_TRIAL, ent.TIER_OSS, "bogus") is None
    )


def test_tier_diff_at_empty_from(ent):
    assert (
        ent.tier_diff_at(ent.TIER_TRIAL, "", ent.TIER_CLOUD_PRO) is None
    )


def test_tier_diff_at_empty_to(ent):
    assert ent.tier_diff_at(ent.TIER_TRIAL, ent.TIER_OSS, "") is None


# ── grace vs enforce parity ─────────────────────────────────────────────────


def test_tier_diff_at_byte_identical_across_grace_and_enforce(
    ent, monkeypatch, tmp_path
):
    """The helper delegates to :func:`tier_diff`, which walks the static
    per-tier maps. Grace vs enforce yields byte-identical rows.
    """
    grace_rows = {}
    for p in ent._TIER_ORDER:
        grace_rows[p] = ent.tier_diff_at(
            p, ent.TIER_OSS, ent.TIER_CLOUD_PRO
        )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e2

    importlib.reload(e2)
    e2.invalidate()
    try:
        for p in e2._TIER_ORDER:
            assert e2.tier_diff_at(
                p, e2.TIER_OSS, e2.TIER_CLOUD_PRO
            ) == grace_rows[p]
    finally:
        e2.invalidate()


# ── never raises ────────────────────────────────────────────────────────────


def test_tier_diff_at_never_raises_on_weird_inputs(ent):
    for bad_p in [None, "", "bogus", 123, [], {}, object()]:
        for bad_f in [None, "", "bogus", 123, [], {}]:
            for bad_t in [None, "", "bogus", 123, [], {}]:
                try:
                    ent.tier_diff_at(bad_p, bad_f, bad_t)
                except Exception as exc:  # pragma: no cover
                    raise AssertionError(
                        f"tier_diff_at raised on ({bad_p!r},"
                        f" {bad_f!r}, {bad_t!r}): {exc}"
                    )


# ── API endpoint ────────────────────────────────────────────────────────────


def test_endpoint_missing_tier_returns_400(client):
    r = client.get("/api/entitlement/tier-diff-at?from=oss&to=cloud_pro")
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_endpoint_missing_from_returns_400(client):
    r = client.get(
        "/api/entitlement/tier-diff-at?tier=trial&to=cloud_pro"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing from"


def test_endpoint_missing_to_returns_400(client):
    r = client.get("/api/entitlement/tier-diff-at?tier=trial&from=oss")
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing to"


def test_endpoint_unknown_perspective_returns_404_with_which(client):
    r = client.get(
        "/api/entitlement/tier-diff-at?tier=bogus&from=oss&to=cloud_pro"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_endpoint_unknown_from_returns_404_with_which(client):
    r = client.get(
        "/api/entitlement/tier-diff-at?tier=trial&from=bogus&to=cloud_pro"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"
    assert body["from"] == "bogus"


def test_endpoint_unknown_to_returns_404_with_which(client):
    r = client.get(
        "/api/entitlement/tier-diff-at?tier=trial&from=oss&to=bogus"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "to"
    assert body["to"] == "bogus"


def test_endpoint_happy_path_returns_200_with_perspective_echo(client):
    r = client.get(
        "/api/entitlement/tier-diff-at?tier=trial&from=oss&to=cloud_pro"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "trial"
    assert body["perspective_tier_label"]
    assert isinstance(body["perspective_tier_rank"], int)
    assert body["from"] == "oss"
    assert body["to"] == "cloud_pro"
    assert body["direction"] == "upgrade"
    assert isinstance(body["added_features"], list)
    assert isinstance(body["capacity_changes"], dict)


def test_endpoint_shape_matches_expected_keys(client):
    r = client.get(
        "/api/entitlement/tier-diff-at?tier=trial&from=oss&to=cloud_pro"
    )
    body = r.get_json()
    assert (
        set(body.keys())
        == _EXPECTED_TIER_DIFF_KEYS | _EXTRA_AT_KEYS
    )


def test_endpoint_body_matches_tier_diff_endpoint_for_same_pair(client):
    r_at = client.get(
        "/api/entitlement/tier-diff-at?tier=trial&from=oss&to=cloud_pro"
    ).get_json()
    r_plain = client.get(
        "/api/entitlement/tier-diff?from=oss&to=cloud_pro"
    ).get_json()
    for key in _EXPECTED_TIER_DIFF_KEYS:
        assert r_at[key] == r_plain[key], key


def test_endpoint_trial_perspective_accepted(client):
    r = client.get(
        "/api/entitlement/tier-diff-at?tier=trial&from=oss&to=enterprise"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "trial"


def test_endpoint_case_and_whitespace_normalisation(client):
    r = client.get(
        "/api/entitlement/tier-diff-at?tier=%20Trial%20&from=OSS"
        "&to=%20cloud_pro%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "trial"
    assert body["from"] == "oss"
    assert body["to"] == "cloud_pro"


def test_endpoint_identity_returns_empty_deltas(client):
    r = client.get(
        "/api/entitlement/tier-diff-at?tier=trial&from=cloud_pro"
        "&to=cloud_pro"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["added_features"] == []
    assert body["lost_features"] == []


def test_endpoint_every_perspective_produces_200(client):
    for p in [
        "oss",
        "cloud_free",
        "trial",
        "cloud_starter",
        "cloud_pro",
        "pro",
        "enterprise",
    ]:
        r = client.get(
            f"/api/entitlement/tier-diff-at?tier={p}"
            "&from=oss&to=cloud_pro"
        )
        assert r.status_code == 200, (p, r.status_code, r.get_json())
        assert r.get_json()["perspective_tier"] == p
