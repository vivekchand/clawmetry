"""Tests for ``clawmetry.entitlements.tier_path_at`` +
``tier_path_at_batch`` and their two HTTP endpoints
``GET /api/entitlement/tier-path-at`` +
``GET /api/entitlement/tier-path-at-batch``.

Path-shaped what-if sibling of :func:`tier_path` /
:func:`tier_path_batch`: renders the per-rung full marginal
``tier_diff`` path between two tiers from a hypothetical
``perspective_tier`` in ONE round-trip. Fills the ``_at`` / ``_at_batch``
slots for the ``tier_path`` (all-slices per-rung) family so a pricing-
comparison walkthrough surface can call ``X_at(perspective, from, to)``
uniformly across every ``_at_path`` family member (``tier_path_at`` +
``capacity_diff_at_path`` + ``tier_unlocks_at_path`` +
``tier_locks_at_path`` + ...).

Pins:

* body byte-identical to :func:`tier_path` / :func:`tier_path_batch`
  for every perspective -- the perspective is validated but does NOT
  shape the rows (parity with every other ``_at_path`` helper the
  ``capacity_diff_at_path`` / ``tier_catalog_at_path`` /
  ``feature_catalog_at_path`` / ``preview_at_path`` families ship).
* per-rung row shape carries the full :func:`tier_diff` envelope
  (``from`` / ``to`` / ``direction`` / ``added_features`` /
  ``lost_features`` / ``added_runtimes`` / ``lost_runtimes`` /
  ``capacity_changes``).
* ``trial`` accepted as perspective and as endpoint / destination
  (matching every other ``_at`` sibling's lenient posture).
* case + whitespace normalisation on perspective, from, to.
* helper is decoupled from the resolver -- grace vs enforce yields
  byte-identical rows.
* unknown / empty / garbage ids return ``None`` and never raise; a
  per-destination failure short-circuits that id into ``unknown[]``
  and the rest of the batch keeps building.
* API scalar: 400 on missing args, 404 with ``which: "tier" | "from" |
  "to"`` on unknown ids, 200 with the standard resolver-context tail
  every ``_at*`` endpoint carries.
* API batch: 400 on missing tier / from / empty to, 404 with
  ``which: "tier" | "from"`` on unknown perspective / source, 200 with
  bucketed ``unknown[]`` on partially-bad destination lists, never
  5xxs on a synthesis failure.
"""
from __future__ import annotations

import importlib

import pytest


_ROW_TIER_DIFF_KEYS = {
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
_ITEM_KEYS = {"to", "to_label", "to_rank", "direction", "path"}
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
_BATCH_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "from",
    "from_label",
    "from_rank",
    "tiers",
    "unknown",
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


# ─────────────────────────────────────────────────────────────────────────────
# scalar helper: shape + happy path
# ─────────────────────────────────────────────────────────────────────────────


def test_scalar_returns_list(ent):
    path = ent.tier_path_at(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    assert isinstance(path, list)
    assert len(path) >= 1


def test_scalar_each_row_has_tier_diff_shape(ent):
    path = ent.tier_path_at(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    for row in path:
        assert isinstance(row, dict)
        # Row shape is the full tier_diff envelope; carriers may add extras
        # so we assert containment rather than exact equality.
        assert _ROW_TIER_DIFF_KEYS.issubset(set(row.keys()))
        assert row["direction"] in {
            "upgrade",
            "downgrade",
            "lateral",
            "identity",
        }


def test_scalar_identity_yields_empty(ent):
    for tid in _all_tiers(ent):
        assert ent.tier_path_at(ent.TIER_CLOUD_PRO, tid, tid) == []


def test_scalar_lateral_yields_single_row(ent):
    """Lateral (same rank, different id) yields a one-row path."""
    path = ent.tier_path_at(
        ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_PRO
    )
    assert isinstance(path, list)
    assert len(path) == 1
    assert path[0]["to"] == ent.TIER_PRO
    assert path[0]["direction"] == "lateral"


def test_scalar_upgrade_walks_ascending_rungs(ent):
    """Every walked rung's ``to`` should be strictly above ``from_rank``
    and up to ``to_rank`` inclusive (upgrade direction). Same invariant
    :func:`tier_path` upholds."""
    path = ent.tier_path_at(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    from_rank = ent.tier_rank(ent.TIER_OSS)
    to_rank = ent.tier_rank(ent.TIER_ENTERPRISE)
    for row in path:
        r = ent.tier_rank(row["to"])
        assert from_rank < r <= to_rank


def test_scalar_downgrade_walks_descending_rungs(ent):
    path = ent.tier_path_at(
        ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE, ent.TIER_OSS
    )
    from_rank = ent.tier_rank(ent.TIER_ENTERPRISE)
    to_rank = ent.tier_rank(ent.TIER_OSS)
    for row in path:
        r = ent.tier_rank(row["to"])
        assert to_rank <= r < from_rank


def test_scalar_from_chains_across_rungs(ent):
    """Per-step ``from`` chains across the path: for consecutive rows
    ``row[i]['to'] == row[i+1]['from']``. Same invariant :func:`tier_path`
    upholds so a consumer can fold the marginal rows into a cumulative
    diff."""
    path = ent.tier_path_at(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    for i in range(len(path) - 1):
        assert path[i]["to"] == path[i + 1]["from"]


# ─────────────────────────────────────────────────────────────────────────────
# scalar helper: byte-parity with tier_path
# ─────────────────────────────────────────────────────────────────────────────


def test_scalar_body_parity_with_tier_path(ent):
    """Body byte-identical to ``tier_path(from, to)`` for every
    ``(perspective, from, to)`` triple in ``ALL_TIERS × ALL_TIERS ×
    ALL_TIERS``. Perspective validates but does NOT shape rows."""
    tiers = _all_tiers(ent)
    for p in tiers:
        for f in tiers:
            for t in tiers:
                got = ent.tier_path_at(p, f, t)
                want = ent.tier_path(f, t)
                assert got == want, (
                    f"body drift for perspective={p} from={f} to={t}: "
                    f"{got!r} != {want!r}"
                )


def test_scalar_perspective_invariance(ent):
    """Shifting perspective across every id in ``_TIER_ORDER`` yields
    byte-identical rows for the same ``(from, to)`` pair."""
    baseline = ent.tier_path_at(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    for p in _all_tiers(ent):
        assert ent.tier_path_at(
            p, ent.TIER_OSS, ent.TIER_ENTERPRISE
        ) == baseline, f"perspective {p} drifted from cloud_pro baseline"


# ─────────────────────────────────────────────────────────────────────────────
# scalar helper: input handling / error posture
# ─────────────────────────────────────────────────────────────────────────────


def test_scalar_trial_accepted_as_perspective(ent):
    """Trial IS accepted as perspective (lenient ``_at`` posture)
    -- matches every other ``_at`` helper."""
    got = ent.tier_path_at(
        ent.TIER_TRIAL, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    want = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert got == want


def test_scalar_trial_accepted_as_endpoint(ent):
    """Trial IS accepted as ``to`` via the lateral / identity branches
    (matches :func:`tier_path`). cloud_pro and trial share rank 2 --
    lateral, single-row path."""
    got = ent.tier_path_at(
        ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO, ent.TIER_TRIAL
    )
    assert isinstance(got, list)
    assert len(got) == 1
    assert got[0]["to"] == ent.TIER_TRIAL


def test_scalar_unknown_perspective_returns_none(ent):
    assert ent.tier_path_at(
        "bogus_tier", ent.TIER_OSS, ent.TIER_ENTERPRISE
    ) is None


def test_scalar_unknown_from_returns_none(ent):
    assert ent.tier_path_at(
        ent.TIER_CLOUD_PRO, "bogus_tier", ent.TIER_ENTERPRISE
    ) is None


def test_scalar_unknown_to_returns_none(ent):
    assert ent.tier_path_at(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, "bogus_tier"
    ) is None


def test_scalar_none_perspective_returns_none(ent):
    assert ent.tier_path_at(
        None, ent.TIER_OSS, ent.TIER_ENTERPRISE
    ) is None


def test_scalar_empty_perspective_returns_none(ent):
    assert ent.tier_path_at(
        "", ent.TIER_OSS, ent.TIER_ENTERPRISE
    ) is None


def test_scalar_case_and_whitespace_normalised(ent):
    got = ent.tier_path_at(
        "  Cloud_Pro  ", "  OSS  ", "  ENTERPRISE  "
    )
    want = ent.tier_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert got == want


def test_scalar_never_raises_on_weird_types(ent):
    """A perspective coerce crash short-circuits to ``None`` rather
    than surfacing an exception."""
    for bad in (b"bytes", 12345, 3.14, object()):
        assert ent.tier_path_at(
            bad, ent.TIER_OSS, ent.TIER_ENTERPRISE
        ) is None


def test_scalar_delegate_crash_returns_none(ent, monkeypatch):
    """A ``tier_path`` blow-up short-circuits to ``None`` rather than
    surfacing an exception."""

    def _boom(f, t):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_path", _boom)
    assert (
        ent.tier_path_at(
            ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
        )
        is None
    )


def test_scalar_grace_vs_enforce_identical(ent, enforced):
    """Helper is resolver-independent -- grace and enforce yield the
    same rows."""
    grace_rows = ent.tier_path_at(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    enforce_rows = enforced.tier_path_at(
        enforced.TIER_CLOUD_PRO,
        enforced.TIER_OSS,
        enforced.TIER_ENTERPRISE,
    )
    assert grace_rows == enforce_rows


# ─────────────────────────────────────────────────────────────────────────────
# batch helper: shape + happy path
# ─────────────────────────────────────────────────────────────────────────────


def test_batch_returns_dict_shape(ent):
    out = ent.tier_path_at_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_batch_each_item_has_expected_shape(ent):
    out = ent.tier_path_at_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
    )
    for item in out["tiers"]:
        assert set(item.keys()) == _ITEM_KEYS
        assert item["direction"] in {
            "upgrade",
            "downgrade",
            "lateral",
            "identity",
        }


def test_batch_body_parity_with_tier_path_batch(ent):
    """For every perspective, batch body byte-equals
    :func:`tier_path_batch(from, to_tiers)` for the same
    ``(from, to_tiers)``."""
    tiers = _all_tiers(ent)
    dests = [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_TRIAL,
    ]
    for p in tiers:
        for f in tiers:
            got = ent.tier_path_at_batch(p, f, dests)
            want = ent.tier_path_batch(f, dests)
            assert got == want, (
                f"batch body drift for perspective={p} from={f}"
            )


def test_batch_perspective_invariance(ent):
    dests = [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    baseline = ent.tier_path_at_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, dests
    )
    for p in _all_tiers(ent):
        assert ent.tier_path_at_batch(
            p, ent.TIER_OSS, dests
        ) == baseline


def test_batch_scalar_parity(ent):
    """Each ``tiers[].path`` byte-equals the scalar
    :func:`tier_path_at(perspective, from, tid)` for the same id -- the
    scalar/batch no-drift contract."""
    p = ent.TIER_CLOUD_PRO
    f = ent.TIER_OSS
    dests = [ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    out = ent.tier_path_at_batch(p, f, dests)
    by_id = {row["to"]: row for row in out["tiers"]}
    for tid in dests:
        assert by_id[tid]["path"] == ent.tier_path_at(p, f, tid)


# ─────────────────────────────────────────────────────────────────────────────
# batch helper: input handling / error posture
# ─────────────────────────────────────────────────────────────────────────────


def test_batch_unknown_perspective_returns_none(ent):
    assert ent.tier_path_at_batch(
        "bogus_tier", ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    ) is None


def test_batch_unknown_from_returns_none(ent):
    assert ent.tier_path_at_batch(
        ent.TIER_CLOUD_PRO, "bogus_tier", [ent.TIER_ENTERPRISE]
    ) is None


def test_batch_none_perspective_returns_none(ent):
    assert ent.tier_path_at_batch(
        None, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    ) is None


def test_batch_unknown_destinations_bucketed(ent):
    out = ent.tier_path_at_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_ENTERPRISE, "bogus_id"],
    )
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert out["unknown"] == ["bogus_id"]


def test_batch_all_unknown_destinations_empty_tiers(ent):
    out = ent.tier_path_at_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ["bogus_a", "bogus_b"]
    )
    assert out == {"tiers": [], "unknown": ["bogus_a", "bogus_b"]}


def test_batch_trial_accepted_as_destination(ent):
    out = ent.tier_path_at_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO, [ent.TIER_TRIAL]
    )
    assert out["unknown"] == []
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_TRIAL]


def test_batch_normalises_destinations(ent):
    got = ent.tier_path_at_batch(
        "  cloud_pro  ",
        "  OSS  ",
        ["  Enterprise  ", "ENTERPRISE", "cloud_pro"],
    )
    want = ent.tier_path_at_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO],
    )
    assert got == want


def test_batch_grace_vs_enforce_identical(ent, enforced):
    dests = [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    grace_out = ent.tier_path_at_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, dests
    )
    enforce_out = enforced.tier_path_at_batch(
        enforced.TIER_CLOUD_PRO, enforced.TIER_OSS, dests
    )
    assert grace_out == enforce_out


def test_batch_never_raises_on_row_crash(ent, monkeypatch):
    """A per-destination ``tier_path`` crash short-circuits that id
    into ``unknown[]`` rather than surfacing an exception."""
    real = ent.tier_path

    def _boom(f, t):
        if t == ent.TIER_ENTERPRISE:
            raise RuntimeError("boom")
        return real(f, t)

    monkeypatch.setattr(ent, "tier_path", _boom)
    out = ent.tier_path_at_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
    )
    assert ent.TIER_ENTERPRISE in out["unknown"]
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_CLOUD_STARTER]


# ─────────────────────────────────────────────────────────────────────────────
# HTTP scalar: /tier-path-at
# ─────────────────────────────────────────────────────────────────────────────


def test_http_scalar_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list)
    assert body["path"] == ent.tier_path_at(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )


def test_http_scalar_missing_tier_400(client):
    r = client.get(
        "/api/entitlement/tier-path-at?from=oss&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_http_scalar_missing_from_400(client):
    r = client.get(
        "/api/entitlement/tier-path-at?tier=cloud_pro&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing from"


def test_http_scalar_missing_to_400(client):
    r = client.get(
        "/api/entitlement/tier-path-at?tier=cloud_pro&from=oss"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing to"


def test_http_scalar_unknown_tier_which_key(client):
    r = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=bogus&from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_http_scalar_unknown_from_which_key(client):
    r = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=cloud_pro&from=bogus&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"


def test_http_scalar_unknown_to_which_key(client):
    r = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=cloud_pro&from=oss&to=bogus"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "to"


def test_http_scalar_trial_accepted_as_perspective(client, ent):
    r = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=trial&from=oss&to=enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "trial"
    assert body["path"] == ent.tier_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE
    )


def test_http_scalar_identity_path_empty(client):
    r = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=cloud_pro&from=enterprise&to=enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_http_scalar_downgrade_direction(client):
    r = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=cloud_pro&from=enterprise&to=oss"
    )
    assert r.status_code == 200
    assert r.get_json()["direction"] == "downgrade"


def test_http_scalar_lateral_direction(client):
    r = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=cloud_pro&from=cloud_pro&to=pro"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1


def test_http_scalar_case_and_whitespace_normalised(client, ent):
    r = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=%20Cloud_Pro%20&from=%20OSS%20&to=%20ENTERPRISE%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"


def test_http_scalar_body_parity_with_tier_path(client, ent):
    """``path`` byte-parity with ``/tier-path?from=&to=`` (the current-
    perspective sibling)."""
    r_at = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=cloud_pro&from=oss&to=enterprise"
    )
    r_path = client.get(
        "/api/entitlement/tier-path?from=oss&to=enterprise"
    )
    assert r_at.status_code == 200
    assert r_path.status_code == 200
    assert r_at.get_json()["path"] == r_path.get_json()["path"]


def test_http_scalar_perspective_invariance(client, ent):
    baseline = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=cloud_pro&from=oss&to=enterprise"
    ).get_json()["path"]
    for p in (
        "oss",
        "cloud_free",
        "trial",
        "cloud_starter",
        "pro",
        "enterprise",
    ):
        got = client.get(
            f"/api/entitlement/tier-path-at"
            f"?tier={p}&from=oss&to=enterprise"
        ).get_json()["path"]
        assert got == baseline, f"perspective {p} drifted from cloud_pro"


def test_http_scalar_carries_resolver_tail(client):
    """Every ``_at*`` endpoint carries ``current_tier`` /
    ``current_tier_rank`` / ``grace`` / ``enforced`` alongside the
    perspective echo."""
    body = client.get(
        "/api/entitlement/tier-path-at"
        "?tier=cloud_pro&from=oss&to=enterprise"
    ).get_json()
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert "grace" in body
    assert "enforced" in body
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


# ─────────────────────────────────────────────────────────────────────────────
# HTTP batch: /tier-path-at-batch
# ─────────────────────────────────────────────────────────────────────────────


def test_http_batch_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=cloud_pro&from=oss&to=cloud_starter,cloud_pro,enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _BATCH_ENVELOPE_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert [row["to"] for row in body["tiers"]] == [
        "cloud_starter",
        "cloud_pro",
        "enterprise",
    ]
    assert body["unknown"] == []


def test_http_batch_missing_tier_400(client):
    r = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?from=oss&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_http_batch_missing_from_400(client):
    r = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=cloud_pro&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing from"


def test_http_batch_missing_to_400(client):
    r = client.get(
        "/api/entitlement/tier-path-at-batch?tier=cloud_pro&from=oss"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "supply to=<csv>"


def test_http_batch_empty_to_400(client):
    """An empty ``to`` list normalises to zero targets and 400s."""
    r = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=cloud_pro&from=oss&to="
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "supply to=<csv>"


def test_http_batch_unknown_tier_which_key(client):
    r = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=bogus&from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_http_batch_unknown_from_which_key(client):
    r = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=cloud_pro&from=bogus&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"


def test_http_batch_partial_unknown_bucketed(client):
    r = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=cloud_pro&from=oss&to=enterprise,nope_tier"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["to"] for row in body["tiers"]] == ["enterprise"]
    assert body["unknown"] == ["nope_tier"]


def test_http_batch_multi_destination(client, ent):
    r = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=cloud_pro&from=oss"
        "&to=cloud_starter,cloud_pro,enterprise,pro"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["to"] for row in body["tiers"]] == [
        "cloud_starter",
        "cloud_pro",
        "enterprise",
        "pro",
    ]
    assert body["unknown"] == []


def test_http_batch_body_parity_with_tier_path_batch(client):
    """``tiers[]`` byte-parity with ``/tier-path-batch`` (the current-
    perspective sibling) for the same ``(from, to)``."""
    r_at = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=cloud_pro&from=oss&to=cloud_pro,enterprise"
    )
    r_path = client.get(
        "/api/entitlement/tier-path-batch"
        "?from=oss&to=cloud_pro,enterprise"
    )
    assert r_at.status_code == 200
    assert r_path.status_code == 200
    assert r_at.get_json()["tiers"] == r_path.get_json()["tiers"]


def test_http_batch_perspective_invariance(client):
    """``tiers[]`` byte-identical across shifting perspective."""
    baseline = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=cloud_pro&from=oss&to=cloud_pro,enterprise"
    ).get_json()["tiers"]
    for p in (
        "oss",
        "cloud_free",
        "trial",
        "cloud_starter",
        "pro",
        "enterprise",
    ):
        got = client.get(
            f"/api/entitlement/tier-path-at-batch"
            f"?tier={p}&from=oss&to=cloud_pro,enterprise"
        ).get_json()["tiers"]
        assert got == baseline, f"perspective {p} drifted from cloud_pro"


def test_http_batch_trial_accepted_as_both_perspective_and_destination(
    client, ent
):
    r = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=trial&from=oss&to=trial,enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "trial"
    assert body["unknown"] == []
    assert set(row["to"] for row in body["tiers"]) == {
        "trial",
        "enterprise",
    }


def test_http_batch_case_and_whitespace_normalised(client):
    r = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=%20Cloud_Pro%20&from=%20OSS%20"
        "&to=%20Enterprise%20,ENTERPRISE,cloud_pro"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    # duplicates dropped, whitespace stripped, first-seen order preserved.
    assert [row["to"] for row in body["tiers"]] == [
        "enterprise",
        "cloud_pro",
    ]
    assert body["unknown"] == []


def test_http_batch_carries_resolver_tail(client):
    body = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=cloud_pro&from=oss&to=enterprise"
    ).get_json()
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert "grace" in body
    assert "enforced" in body


def test_http_batch_scalar_parity(client):
    """Each ``tiers[].path`` byte-equals the scalar endpoint's ``path``
    for the same ``(perspective, from, to)`` -- HTTP-side scalar/batch
    no-drift contract."""
    r_batch = client.get(
        "/api/entitlement/tier-path-at-batch"
        "?tier=cloud_pro&from=oss&to=cloud_starter,enterprise"
    ).get_json()
    by_id = {row["to"]: row for row in r_batch["tiers"]}
    for tid in ("cloud_starter", "enterprise"):
        r_scalar = client.get(
            f"/api/entitlement/tier-path-at"
            f"?tier=cloud_pro&from=oss&to={tid}"
        ).get_json()
        assert by_id[tid]["path"] == r_scalar["path"]
