"""Tests for ``clawmetry.entitlements.capacity_headroom_at_path`` +
``capacity_headroom_at_path_batch`` and their two HTTP endpoints
``GET /api/entitlement/capacity-headroom-at-path`` +
``GET /api/entitlement/capacity-headroom-at-path-batch``.

Path-shaped what-if sibling of :func:`capacity_headroom_path` /
:func:`capacity_headroom_path_batch`: renders the per-rung capacity-
headroom envelope path between two tiers from a hypothetical
``perspective_tier`` given caller-supplied per-axis usage in ONE
round-trip. Fills the ``_at_path`` / ``_at_path_batch`` slots on the
capacity-headroom axis so a pricing-comparison walkthrough surface can
call ``X_at_path(perspective, from, to)`` uniformly across every
``_at_path`` family member.

Pins:

* body byte-identical to :func:`capacity_headroom_path` /
  :func:`capacity_headroom_path_batch` for every perspective -- the
  perspective is validated but does NOT shape the rows (parity with
  every other ``_at_path`` helper the ``capacity_diff_at_path`` /
  ``feature_catalog_at_path`` / ``preview_at_path`` family ships).
* per-rung row shape carries the ``tier`` / ``tier_label`` /
  ``channels`` / ``retention_days`` / ``nodes`` envelope
  :func:`capacity_headroom_at` returns.
* per-axis "None means axis not supplied" posture: an unsupplied axis
  stays ``None`` on every rung; a supplied axis is echoed on every
  rung.
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


_ROW_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "channels",
    "retention_days",
    "nodes",
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


_USAGE = {"channels": 100, "retention_days": 30, "nodes": 5}


# ─────────────────────────────────────────────────────────────────────────────
# scalar helper: shape + happy path
# ─────────────────────────────────────────────────────────────────────────────


def test_scalar_returns_list(ent):
    path = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
    )
    assert isinstance(path, list)
    assert len(path) >= 1


def test_scalar_each_row_has_expected_shape(ent):
    path = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
    )
    for row in path:
        assert isinstance(row, dict)
        assert set(row.keys()) == _ROW_ENVELOPE_KEYS
        assert isinstance(row["tier"], str)


def test_scalar_identity_yields_empty(ent):
    for tid in _all_tiers(ent):
        assert (
            ent.capacity_headroom_at_path(
                ent.TIER_CLOUD_PRO, tid, tid, **_USAGE
            )
            == []
        )


def test_scalar_lateral_yields_single_row(ent):
    """Lateral (same rank, different id) yields a one-row path."""
    path = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        **_USAGE,
    )
    assert isinstance(path, list)
    assert len(path) == 1
    assert path[0]["tier"] == ent.TIER_PRO


def test_scalar_upgrade_walks_ascending_rungs(ent):
    """Every walked rung should be strictly above ``from_rank`` and up
    to ``to_rank`` inclusive (upgrade direction)."""
    path = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
    )
    from_rank = ent.tier_rank(ent.TIER_OSS)
    to_rank = ent.tier_rank(ent.TIER_ENTERPRISE)
    for row in path:
        r = ent.tier_rank(row["tier"])
        assert from_rank < r <= to_rank


def test_scalar_downgrade_walks_descending_rungs(ent):
    path = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE, ent.TIER_OSS, **_USAGE
    )
    from_rank = ent.tier_rank(ent.TIER_ENTERPRISE)
    to_rank = ent.tier_rank(ent.TIER_OSS)
    for row in path:
        r = ent.tier_rank(row["tier"])
        assert to_rank <= r < from_rank


# ─────────────────────────────────────────────────────────────────────────────
# scalar helper: byte-parity with capacity_headroom_path
# ─────────────────────────────────────────────────────────────────────────────


def test_scalar_body_parity_with_capacity_headroom_path(ent):
    """Body byte-identical to ``capacity_headroom_path(from, to)`` for
    every ``(perspective, from, to)`` triple in
    ``ALL_TIERS × ALL_TIERS × ALL_TIERS``. Perspective validates but
    does NOT shape rows."""
    tiers = _all_tiers(ent)
    for p in tiers:
        for f in tiers:
            for t in tiers:
                got = ent.capacity_headroom_at_path(p, f, t, **_USAGE)
                want = ent.capacity_headroom_path(f, t, **_USAGE)
                assert got == want, (
                    f"body drift for perspective={p} from={f} to={t}: "
                    f"{got!r} != {want!r}"
                )


def test_scalar_perspective_invariance(ent):
    """Shifting perspective across every id in ``_TIER_ORDER`` yields
    byte-identical rows for the same ``(from, to)`` pair."""
    baseline = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
    )
    for p in _all_tiers(ent):
        assert (
            ent.capacity_headroom_at_path(
                p, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
            )
            == baseline
        ), f"perspective {p} drifted from cloud_pro baseline"


# ─────────────────────────────────────────────────────────────────────────────
# scalar helper: per-axis usage semantics
# ─────────────────────────────────────────────────────────────────────────────


def test_scalar_unsupplied_axis_is_none_on_every_row(ent):
    """No usage kwargs supplied -> every rung's per-axis rows are
    ``None`` (matches capacity_headroom_path's posture)."""
    path = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    for row in path:
        assert row["channels"] is None
        assert row["retention_days"] is None
        assert row["nodes"] is None


def test_scalar_only_channels_supplied(ent):
    """Only channels supplied -> only channels row echoed on every
    rung; retention / nodes stay ``None``."""
    path = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=25
    )
    for row in path:
        assert row["channels"] is not None
        assert row["retention_days"] is None
        assert row["nodes"] is None


def test_scalar_all_axes_supplied(ent):
    path = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
    )
    for row in path:
        assert row["channels"] is not None
        assert row["retention_days"] is not None
        assert row["nodes"] is not None


def test_scalar_row_matches_capacity_headroom_at(ent):
    """Each rung's row byte-equals :func:`capacity_headroom_at(rung, ...)`
    -- the scalar/what-if no-drift contract."""
    path = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
    )
    for row in path:
        assert row == ent.capacity_headroom_at(row["tier"], **_USAGE)


# ─────────────────────────────────────────────────────────────────────────────
# scalar helper: input handling / error posture
# ─────────────────────────────────────────────────────────────────────────────


def test_scalar_trial_accepted_as_perspective(ent):
    """Trial IS accepted as perspective (lenient ``_at`` posture)."""
    got = ent.capacity_headroom_at_path(
        ent.TIER_TRIAL, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
    )
    want = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
    )
    assert got == want


def test_scalar_trial_accepted_as_endpoint(ent):
    """Trial IS accepted as ``to`` via the lateral / identity branches
    (matches :func:`capacity_headroom_path`)."""
    got = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_PRO,
        ent.TIER_TRIAL,
        **_USAGE,
    )
    # cloud_pro and trial share rank 2 -- lateral, single-row path.
    assert isinstance(got, list)
    assert len(got) == 1
    assert got[0]["tier"] == ent.TIER_TRIAL


def test_scalar_unknown_perspective_returns_none(ent):
    assert (
        ent.capacity_headroom_at_path(
            "bogus_tier", ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
        )
        is None
    )


def test_scalar_unknown_from_returns_none(ent):
    assert (
        ent.capacity_headroom_at_path(
            ent.TIER_CLOUD_PRO, "bogus_tier", ent.TIER_ENTERPRISE, **_USAGE
        )
        is None
    )


def test_scalar_unknown_to_returns_none(ent):
    assert (
        ent.capacity_headroom_at_path(
            ent.TIER_CLOUD_PRO, ent.TIER_OSS, "bogus_tier", **_USAGE
        )
        is None
    )


def test_scalar_none_perspective_returns_none(ent):
    assert (
        ent.capacity_headroom_at_path(
            None, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
        )
        is None
    )


def test_scalar_empty_perspective_returns_none(ent):
    assert (
        ent.capacity_headroom_at_path(
            "", ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
        )
        is None
    )


def test_scalar_case_and_whitespace_normalised(ent):
    got = ent.capacity_headroom_at_path(
        "  Cloud_Pro  ", "  OSS  ", "  ENTERPRISE  ", **_USAGE
    )
    want = ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
    )
    assert got == want


def test_scalar_never_raises_on_weird_types(ent):
    """A perspective coerce crash short-circuits to ``None`` rather
    than surfacing an exception."""
    for bad in (b"bytes", 12345, 3.14, object()):
        assert (
            ent.capacity_headroom_at_path(
                bad, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
            )
            is None
        )


def test_scalar_delegate_crash_short_circuits(ent, monkeypatch):
    """A delegate blowup logs a warning and returns ``None`` -- an
    upgrade-walkthrough surface keeps rendering."""

    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "capacity_headroom_path", _boom)
    assert (
        ent.capacity_headroom_at_path(
            ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
        )
        is None
    )


def test_scalar_grace_vs_enforce_identical(ent, enforced):
    """Helper is resolver-independent -- grace and enforce yield the
    same rows."""
    grace_rows = ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, **_USAGE
    )
    enforce_rows = enforced.capacity_headroom_at_path(
        enforced.TIER_CLOUD_PRO,
        enforced.TIER_OSS,
        enforced.TIER_ENTERPRISE,
        **_USAGE,
    )
    assert grace_rows == enforce_rows


# ─────────────────────────────────────────────────────────────────────────────
# batch helper: shape + happy path
# ─────────────────────────────────────────────────────────────────────────────


def test_batch_returns_dict_shape(ent):
    out = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
        **_USAGE,
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_batch_each_item_has_expected_shape(ent):
    out = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
        **_USAGE,
    )
    for item in out["tiers"]:
        assert set(item.keys()) == _ITEM_KEYS
        assert item["direction"] in {
            "upgrade",
            "downgrade",
            "lateral",
            "identity",
        }


def test_batch_body_parity_with_capacity_headroom_path_batch(ent):
    """For every perspective, batch body byte-equals
    :func:`capacity_headroom_path_batch(from, to_tiers)` for the same
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
            got = ent.capacity_headroom_at_path_batch(
                p, f, dests, **_USAGE
            )
            want = ent.capacity_headroom_path_batch(f, dests, **_USAGE)
            assert got == want, (
                f"batch body drift for perspective={p} from={f}"
            )


def test_batch_perspective_invariance(ent):
    dests = [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    baseline = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, dests, **_USAGE
    )
    for p in _all_tiers(ent):
        assert (
            ent.capacity_headroom_at_path_batch(
                p, ent.TIER_OSS, dests, **_USAGE
            )
            == baseline
        )


def test_batch_scalar_parity(ent):
    """Each ``tiers[].path`` byte-equals the scalar
    :func:`capacity_headroom_at_path(perspective, from, tid)` for the
    same id -- the scalar/batch no-drift contract."""
    p = ent.TIER_CLOUD_PRO
    f = ent.TIER_OSS
    dests = [ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    out = ent.capacity_headroom_at_path_batch(p, f, dests, **_USAGE)
    by_id = {row["to"]: row for row in out["tiers"]}
    for tid in dests:
        assert by_id[tid]["path"] == ent.capacity_headroom_at_path(
            p, f, tid, **_USAGE
        )


# ─────────────────────────────────────────────────────────────────────────────
# batch helper: per-axis usage semantics
# ─────────────────────────────────────────────────────────────────────────────


def test_batch_unsupplied_axis_is_none_on_every_row(ent):
    out = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
    )
    for item in out["tiers"]:
        for row in item["path"]:
            assert row["channels"] is None
            assert row["retention_days"] is None
            assert row["nodes"] is None


def test_batch_only_retention_supplied(ent):
    out = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
        retention_days=30,
    )
    for item in out["tiers"]:
        for row in item["path"]:
            assert row["retention_days"] is not None
            assert row["channels"] is None
            assert row["nodes"] is None


# ─────────────────────────────────────────────────────────────────────────────
# batch helper: input handling / error posture
# ─────────────────────────────────────────────────────────────────────────────


def test_batch_unknown_perspective_returns_none(ent):
    assert (
        ent.capacity_headroom_at_path_batch(
            "bogus_tier", ent.TIER_OSS, [ent.TIER_ENTERPRISE], **_USAGE
        )
        is None
    )


def test_batch_unknown_from_returns_none(ent):
    assert (
        ent.capacity_headroom_at_path_batch(
            ent.TIER_CLOUD_PRO,
            "bogus_tier",
            [ent.TIER_ENTERPRISE],
            **_USAGE,
        )
        is None
    )


def test_batch_none_perspective_returns_none(ent):
    assert (
        ent.capacity_headroom_at_path_batch(
            None, ent.TIER_OSS, [ent.TIER_ENTERPRISE], **_USAGE
        )
        is None
    )


def test_batch_unknown_destinations_bucketed(ent):
    out = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_ENTERPRISE, "bogus_id"],
        **_USAGE,
    )
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_ENTERPRISE]
    assert out["unknown"] == ["bogus_id"]


def test_batch_all_unknown_destinations_empty_tiers(ent):
    out = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ["bogus_a", "bogus_b"],
        **_USAGE,
    )
    assert out == {"tiers": [], "unknown": ["bogus_a", "bogus_b"]}


def test_batch_trial_accepted_as_destination(ent):
    out = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_PRO,
        [ent.TIER_TRIAL],
        **_USAGE,
    )
    assert out["unknown"] == []
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_TRIAL]


def test_batch_normalises_destinations(ent):
    got = ent.capacity_headroom_at_path_batch(
        "  cloud_pro  ",
        "  OSS  ",
        ["  Enterprise  ", "ENTERPRISE", "cloud_pro"],
        **_USAGE,
    )
    want = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO],
        **_USAGE,
    )
    assert got == want


def test_batch_grace_vs_enforce_identical(ent, enforced):
    dests = [ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    grace_out = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, dests, **_USAGE
    )
    enforce_out = enforced.capacity_headroom_at_path_batch(
        enforced.TIER_CLOUD_PRO, enforced.TIER_OSS, dests, **_USAGE
    )
    assert grace_out == enforce_out


def test_batch_never_raises_on_row_crash(ent, monkeypatch):
    """A per-destination ``capacity_headroom_path`` crash short-circuits
    that id into ``unknown[]`` rather than surfacing an exception."""
    real = ent.capacity_headroom_path

    def _boom(f, t, **kwargs):
        if t == ent.TIER_ENTERPRISE:
            raise RuntimeError("boom")
        return real(f, t, **kwargs)

    monkeypatch.setattr(ent, "capacity_headroom_path", _boom)
    out = ent.capacity_headroom_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_ENTERPRISE],
        **_USAGE,
    )
    assert ent.TIER_ENTERPRISE in out["unknown"]
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_CLOUD_STARTER]


def test_batch_delegate_crash_short_circuits(ent, monkeypatch):
    """A batch-delegate blowup logs a warning and returns ``None``."""

    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "capacity_headroom_path_batch", _boom)
    assert (
        ent.capacity_headroom_at_path_batch(
            ent.TIER_CLOUD_PRO,
            ent.TIER_OSS,
            [ent.TIER_ENTERPRISE],
            **_USAGE,
        )
        is None
    )


# ─────────────────────────────────────────────────────────────────────────────
# HTTP scalar: /capacity-headroom-at-path
# ─────────────────────────────────────────────────────────────────────────────


def test_http_scalar_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise"
        "&channels=100&retention_days=30&nodes=5"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list)
    assert body["path"] == ent.capacity_headroom_at_path(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        **_USAGE,
    )


def test_http_scalar_missing_tier_400(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?from=oss&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_http_scalar_missing_from_400(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=cloud_pro&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing from"


def test_http_scalar_missing_to_400(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=cloud_pro&from=oss"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing to"


def test_http_scalar_unknown_tier_which_key(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=bogus&from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_http_scalar_unknown_from_which_key(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=cloud_pro&from=bogus&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"


def test_http_scalar_unknown_to_which_key(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=cloud_pro&from=oss&to=bogus"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "to"


def test_http_scalar_trial_accepted_as_perspective(client, ent):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=trial&from=oss&to=enterprise&channels=25"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "trial"
    assert body["path"] == ent.capacity_headroom_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, channels=25
    )


def test_http_scalar_identity_path_empty(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=cloud_pro&from=enterprise&to=enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_http_scalar_downgrade_direction(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=cloud_pro&from=enterprise&to=oss"
    )
    assert r.status_code == 200
    assert r.get_json()["direction"] == "downgrade"


def test_http_scalar_case_and_whitespace_normalised(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=%20Cloud_Pro%20&from=%20OSS%20&to=%20ENTERPRISE%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"


def test_http_scalar_body_parity_with_capacity_headroom_path(client):
    """``path`` byte-parity with ``/capacity-headroom-path?from=&to=``
    (the current-perspective sibling)."""
    r_at = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise"
        "&channels=100&retention_days=30&nodes=5"
    )
    r_path = client.get(
        "/api/entitlement/capacity-headroom-path"
        "?from=oss&to=enterprise&channels=100&retention_days=30&nodes=5"
    )
    assert r_at.status_code == 200
    assert r_path.status_code == 200
    assert r_at.get_json()["path"] == r_path.get_json()["path"]


def test_http_scalar_perspective_invariance(client):
    baseline = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&channels=100"
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
            f"/api/entitlement/capacity-headroom-at-path"
            f"?tier={p}&from=oss&to=enterprise&channels=100"
        ).get_json()["path"]
        assert got == baseline, f"perspective {p} drifted from cloud_pro"


def test_http_scalar_bad_axis_ignored(client):
    """A blank / non-int / negative value on any axis short-circuits
    that axis to ``None`` on every row -- the whole walk still renders."""
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise"
        "&channels=abc&retention_days=&nodes=-1"
    )
    assert r.status_code == 200
    for row in r.get_json()["path"]:
        assert row["channels"] is None
        assert row["retention_days"] is None
        assert row["nodes"] is None


# ─────────────────────────────────────────────────────────────────────────────
# HTTP batch: /capacity-headroom-at-path-batch
# ─────────────────────────────────────────────────────────────────────────────


def test_http_batch_happy_path(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?tier=cloud_pro&from=oss"
        "&to=cloud_starter,cloud_pro,enterprise"
        "&channels=100&retention_days=30&nodes=5"
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
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?from=oss&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_http_batch_missing_from_400(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?tier=cloud_pro&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing from"


def test_http_batch_missing_to_400(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?tier=cloud_pro&from=oss"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "supply to=<csv>"


def test_http_batch_empty_to_400(client):
    """An empty ``to`` list normalises to zero targets and 400s."""
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?tier=cloud_pro&from=oss&to="
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "supply to=<csv>"


def test_http_batch_unknown_tier_which_key(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?tier=bogus&from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_http_batch_unknown_from_which_key(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?tier=cloud_pro&from=bogus&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"


def test_http_batch_partial_unknown_bucketed(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise,nope_tier"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["to"] for row in body["tiers"]] == ["enterprise"]
    assert body["unknown"] == ["nope_tier"]


def test_http_batch_multi_destination(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
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


def test_http_batch_body_parity_with_capacity_headroom_path_batch(client):
    """``tiers[]`` byte-parity with ``/capacity-headroom-path-batch``
    (the current-perspective sibling) for the same ``(from, to)``."""
    r_at = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?tier=cloud_pro&from=oss&to=cloud_pro,enterprise"
        "&channels=100&retention_days=30&nodes=5"
    )
    r_path = client.get(
        "/api/entitlement/capacity-headroom-path-batch"
        "?from=oss&to=cloud_pro,enterprise"
        "&channels=100&retention_days=30&nodes=5"
    )
    assert r_at.status_code == 200
    assert r_path.status_code == 200
    assert r_at.get_json()["tiers"] == r_path.get_json()["tiers"]


def test_http_batch_perspective_invariance(client):
    baseline = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
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
            f"/api/entitlement/capacity-headroom-at-path-batch"
            f"?tier={p}&from=oss&to=cloud_pro,enterprise"
        ).get_json()["tiers"]
        assert got == baseline, f"perspective {p} drifted from cloud_pro"


def test_http_batch_trial_accepted_as_both_perspective_and_destination(
    client,
):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?tier=trial&from=oss&to=trial,enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "trial"
    assert body["unknown"] == []
    assert {row["to"] for row in body["tiers"]} == {"trial", "enterprise"}


def test_http_batch_case_and_whitespace_normalised(client):
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
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


def test_http_batch_bad_axis_ignored(client):
    """A blank / non-int / negative value on any axis short-circuits
    that axis to ``None`` on every row of every destination."""
    r = client.get(
        "/api/entitlement/capacity-headroom-at-path-batch"
        "?tier=cloud_pro&from=oss&to=cloud_pro,enterprise"
        "&channels=abc&retention_days=&nodes=-1"
    )
    assert r.status_code == 200
    for item in r.get_json()["tiers"]:
        for row in item["path"]:
            assert row["channels"] is None
            assert row["retention_days"] is None
            assert row["nodes"] is None
