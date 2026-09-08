"""Tests for the ``has_batch_at`` per-item boolean-gate helper and its
paired ``/api/entitlement/has-batch-at`` endpoint -- hypothetical-
perspective sibling of :func:`clawmetry.entitlements.has_batch` and
per-item plural sibling of the singular ``_at`` scalars
:func:`~clawmetry.entitlements.has_feature_at` /
:func:`~clawmetry.entitlements.has_runtime_at` /
:func:`~clawmetry.entitlements.has_channel_count_at` /
:func:`~clawmetry.entitlements.has_retention_window_at` /
:func:`~clawmetry.entitlements.has_node_count_at`.

Where the LIVE :func:`has_batch` answers "does the CURRENT install
grant every item in this bundle?" (grace pass-through: every known row
is ``has=True`` while ``ent.grace`` is ``True``), ``has_batch_at``
answers the perspective-shaped what-if: "would tier ``perspective_tier``
statically grant each row?". Fills the missing ``_at`` slot on the
mixed-axis batch surface alongside :func:`min_tier_batch_at` (the
perspective sibling on the reverse-lookup axis).

This file pins:

1. Perspective validation: empty / blank / non-string / unknown ->
   ``None`` from the helper and ``400`` / ``404`` from the endpoint,
   matching the ``_at`` posture the rest of the family uses.
2. Envelope shape parity (fixed key set: 13 keys) across every input
   branch so a frontend can bind fields off the URL without a branch
   on the underlying resolver state.
3. Per-row shape parity across every axis (fixed 7-key row set).
4. Per-row parity with the singular ``_at`` scalars: each row's
   ``has`` byte-equals :func:`has_feature_at` / :func:`has_runtime_at`
   / :func:`has_channel_count_at` / :func:`has_retention_window_at` /
   :func:`has_node_count_at` on the same (perspective, item) pair.
5. ``required_tier`` perspective-independence: byte-equals
   :func:`min_tier_for_feature` / :func:`min_tier_for_runtime` /
   :func:`min_tier_for_channel_count` /
   :func:`min_tier_for_retention_window` /
   :func:`min_tier_for_node_count` regardless of perspective.
6. Grace-independence: the perspective-shaped rows are byte-identical
   under grace vs enforce (they read static tables, not the resolver's
   grace bit). ``has_batch_at("oss", features=["fleet"])`` reports
   ``has=False`` even in grace -- the whole point of the ``_at`` slot.
7. Strict-typo-fail-closed posture: unknown feature/runtime ids and
   non-int capacity values flip ``unknown=True`` / ``has=False``.
8. Runtime alias canonicalisation (``claude-code`` -> ``claude_code``)
   and dedup after canonicalisation (matches :func:`has_batch`).
9. ``retention_days=None`` means *unset*, NOT *unlimited*.
10. Never-5xx: any resolver / hypothetical / row-shape blowup collapses
    to the perspective-carrying grace-shape envelope.
11. ``has_all`` rollup: True iff every emitted row is ``has=True`` AND
    ``unknown=False`` (matches ``/has-batch``'s ``has_all`` contract).
12. Endpoint 400 when no axis is supplied, 400 on missing ``tier=``,
    404 on unknown ``tier=``.
13. Cross-consistency with the singular ``/has-*-at`` endpoints on
    ``has_*_at`` per row, and with ``/min-tier-batch-at`` on the
    ``required_tier`` slot for every row on every axis.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free grace mode. Matches the
    fixture shape in ``test_entitlement_has_batch.py`` so per-row
    assertions here reproduce the same install state the LIVE sibling
    is pinned against."""
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
    ``ent.grace`` off. Included to pin the perspective-shaped grace-
    independence invariant -- ``has_batch_at`` returns byte-identical
    rows under grace vs enforce for the same (perspective, bundle)."""
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


# ── Envelope + row-shape constants ──────────────────────────────────────────


_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "has_all",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_ROW_KEYS = {
    "key",
    "kind",
    "has",
    "unknown",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
}


def _get_json(client, url: str, expected_status: int = 200) -> dict:
    resp = client.get(url)
    assert resp.status_code == expected_status, (
        url,
        resp.status_code,
        resp.data,
    )
    return resp.get_json()


def _pick_paid_feature(ent) -> str:
    for f in sorted(ent.PAID_FEATURES):
        return f
    raise RuntimeError("no PAID_FEATURES ids available in the catalogue")


def _pick_paid_runtime(ent) -> str:
    for r in sorted(ent.PAID_RUNTIMES):
        return r
    raise RuntimeError("no PAID_RUNTIMES ids available in the catalogue")


# ── Helper: perspective validation ──────────────────────────────────────────


def test_helper_empty_perspective_returns_none(ent):
    for bad in ["", " ", "\t"]:
        assert ent.has_batch_at(bad, features=["fleet"]) is None, bad


def test_helper_none_perspective_returns_none(ent):
    assert ent.has_batch_at(None, features=["fleet"]) is None


def test_helper_non_string_perspective_returns_none(ent):
    for bad in [123, object(), [], {}]:
        assert ent.has_batch_at(bad, features=["fleet"]) is None, bad


def test_helper_unknown_perspective_returns_none(ent):
    for bad in ["mars", "starter_plus", "pro_max", "unknown_tier"]:
        assert ent.has_batch_at(bad, features=["fleet"]) is None, bad


def test_helper_perspective_is_case_insensitive(ent):
    got_upper = ent.has_batch_at("CLOUD_STARTER", features=["fleet"])
    got_lower = ent.has_batch_at("cloud_starter", features=["fleet"])
    assert got_upper == got_lower


def test_helper_perspective_is_whitespace_stripped(ent):
    got = ent.has_batch_at("  cloud_pro  ", features=["fleet"])
    lo = ent.has_batch_at("cloud_pro", features=["fleet"])
    assert got == lo


def test_helper_trial_is_accepted_as_perspective(ent):
    got = ent.has_batch_at(ent.TIER_TRIAL, features=["fleet"])
    assert got is not None


def test_helper_every_tier_in_order_is_accepted(ent):
    for tier in ent._TIER_ORDER:
        got = ent.has_batch_at(tier, features=["fleet"])
        assert got is not None, tier


# ── Helper: empty-call shape ────────────────────────────────────────────────


def test_helper_empty_call_shape(ent):
    """No axes supplied -- returns the all-empty envelope (no rows,
    three axis slots None). Matches has_batch()'s empty-call shape."""
    got = ent.has_batch_at("cloud_pro")
    assert got == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def test_helper_all_axes_shape(ent):
    got = ent.has_batch_at(
        "cloud_pro",
        features=["fleet", "sso"],
        runtimes=["claude_code"],
        channels=5,
        retention_days=30,
        nodes=3,
    )
    assert set(got.keys()) == {
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
    }
    for row in got["features"]:
        assert set(row.keys()) == _ROW_KEYS
    for row in got["runtimes"]:
        assert set(row.keys()) == _ROW_KEYS
    for slot in ("channels", "retention_days", "nodes"):
        assert set(got[slot].keys()) == _ROW_KEYS


# ── Helper: per-row parity with the singular ``_at`` scalars ────────────────


def test_helper_features_row_has_parity_with_singular_at_scalar(ent):
    """Every feature id in :data:`ALL_FEATURES` -- per-row ``has``
    byte-equals :func:`has_feature_at` on the same (perspective, feature)
    pair across every perspective in :data:`_TIER_ORDER`."""
    for tier in ent._TIER_ORDER:
        for fid in sorted(ent.ALL_FEATURES):
            row = ent.has_batch_at(tier, features=[fid])["features"][0]
            assert row["has"] is ent.has_feature_at(tier, fid), (tier, fid)
            assert row["unknown"] is False, (tier, fid)


def test_helper_runtimes_row_has_parity_with_singular_at_scalar(ent):
    for tier in ent._TIER_ORDER:
        for rt in sorted(ent.ALL_RUNTIMES):
            row = ent.has_batch_at(tier, runtimes=[rt])["runtimes"][0]
            assert row["has"] is ent.has_runtime_at(tier, rt), (tier, rt)
            assert row["unknown"] is False, (tier, rt)


def test_helper_channels_row_has_parity_with_singular_at_scalar(ent):
    counts = [0, 1, 3, 5, 100]
    for tier in ent._TIER_ORDER:
        for n in counts:
            row = ent.has_batch_at(tier, channels=n)["channels"]
            assert row["has"] is ent.has_channel_count_at(tier, n), (tier, n)


def test_helper_retention_days_row_has_parity_with_singular_at_scalar(ent):
    days_values = [0, 1, 7, 30, 90, 365]
    for tier in ent._TIER_ORDER:
        for d in days_values:
            row = ent.has_batch_at(tier, retention_days=d)["retention_days"]
            assert row["has"] is ent.has_retention_window_at(tier, d), (
                tier,
                d,
            )


def test_helper_nodes_row_has_parity_with_singular_at_scalar(ent):
    counts = [0, 1, 5, 100]
    for tier in ent._TIER_ORDER:
        for n in counts:
            row = ent.has_batch_at(tier, nodes=n)["nodes"]
            assert row["has"] is ent.has_node_count_at(tier, n), (tier, n)


def test_helper_required_tier_is_perspective_independent(ent):
    """``required_tier`` on every row is perspective-independent (matches
    the singular ``_at`` scalars' shape). For every axis: the row's
    ``required_tier`` byte-equals :func:`min_tier_for_*` regardless of
    perspective."""
    for tier in ent._TIER_ORDER:
        got = ent.has_batch_at(
            tier,
            features=[_pick_paid_feature(ent)],
            runtimes=[_pick_paid_runtime(ent)],
            channels=5,
            retention_days=30,
            nodes=5,
        )
        assert got["features"][0]["required_tier"] == ent.min_tier_for_feature(
            _pick_paid_feature(ent)
        )
        assert got["runtimes"][0]["required_tier"] == ent.min_tier_for_runtime(
            _pick_paid_runtime(ent)
        )
        assert (
            got["channels"]["required_tier"]
            == ent.min_tier_for_channel_count(5)
        )
        assert (
            got["retention_days"]["required_tier"]
            == ent.min_tier_for_retention_window(30)
        )
        assert (
            got["nodes"]["required_tier"] == ent.min_tier_for_node_count(5)
        )


# ── Helper: grace-independence ──────────────────────────────────────────────


def test_helper_grace_independence_oss_denies_paid_feature(ent):
    """The whole point of the ``_at`` slot: even in grace,
    ``has_batch_at("oss", features=[paid])`` reports has=False."""
    live = ent.get_entitlement()
    assert live.grace is True
    paid = _pick_paid_feature(ent)
    row = ent.has_batch_at("oss", features=[paid])["features"][0]
    assert row["has"] is False
    assert row["unknown"] is False


def test_helper_grace_independence_oss_denies_channels_above_free(ent):
    row = ent.has_batch_at("oss", channels=5)["channels"]
    assert row["has"] is False


def test_helper_grace_independence_oss_denies_nodes_above_free(ent):
    row = ent.has_batch_at("oss", nodes=5)["nodes"]
    assert row["has"] is False


def test_helper_grace_independence_cloud_pro_admits_paid_feature(ent):
    paid = _pick_paid_feature(ent)
    row = ent.has_batch_at("cloud_pro", features=[paid])["features"][0]
    assert row["has"] is True


def test_helper_grace_independence_cloud_pro_admits_unlimited_channels(ent):
    row = ent.has_batch_at("cloud_pro", channels=1000)["channels"]
    assert row["has"] is True


def test_helper_grace_independence_cloud_pro_admits_unlimited_nodes(ent):
    row = ent.has_batch_at("cloud_pro", nodes=1_000_000)["nodes"]
    assert row["has"] is True


def test_helper_grace_vs_enforced_returns_byte_identical_rows(ent, enforced):
    """Perspective-shaped rows are grace-independent by design: same
    (perspective, bundle) yields byte-identical rows under grace vs
    enforce."""
    for tier in ent._TIER_ORDER:
        got_grace = ent.has_batch_at(
            tier,
            features=[_pick_paid_feature(ent)],
            runtimes=[_pick_paid_runtime(ent)],
            channels=5,
            retention_days=30,
            nodes=3,
        )
        got_enforced = enforced.has_batch_at(
            tier,
            features=[_pick_paid_feature(ent)],
            runtimes=[_pick_paid_runtime(ent)],
            channels=5,
            retention_days=30,
            nodes=3,
        )
        assert got_grace == got_enforced, tier


# ── Helper: unknown / non-int / dedup / free ─────────────────────────


def test_helper_unknown_feature_id_is_unknown_row(ent):
    got = ent.has_batch_at("cloud_pro", features=["bogus_feature"])
    row = got["features"][0]
    assert row["unknown"] is True
    assert row["has"] is False
    assert row["required_tier"] is None
    assert row["required_tier_rank"] == -1


def test_helper_unknown_runtime_id_is_unknown_row(ent):
    got = ent.has_batch_at("cloud_pro", runtimes=["bogus_runtime"])
    row = got["runtimes"][0]
    assert row["unknown"] is True
    assert row["has"] is False


def test_helper_non_int_channels_is_unknown_row(ent):
    got = ent.has_batch_at("cloud_pro", channels="five")
    row = got["channels"]
    assert row["unknown"] is True
    assert row["has"] is False


def test_helper_non_int_retention_days_is_unknown_row(ent):
    got = ent.has_batch_at("cloud_pro", retention_days="thirty")
    row = got["retention_days"]
    assert row["unknown"] is True
    assert row["has"] is False


def test_helper_non_int_nodes_is_unknown_row(ent):
    got = ent.has_batch_at("cloud_pro", nodes="three")
    row = got["nodes"]
    assert row["unknown"] is True
    assert row["has"] is False


def test_helper_runtime_alias_canonicalises(ent):
    """``claude-code`` (with a hyphen) canonicalises to
    ``claude_code``; the row surfaces with the canonical key."""
    got = ent.has_batch_at("cloud_pro", runtimes=["claude-code"])
    assert len(got["runtimes"]) == 1
    assert got["runtimes"][0]["key"] == "claude_code"
    assert got["runtimes"][0]["unknown"] is False


def test_helper_runtime_alias_dedup_after_canonicalisation(ent):
    got = ent.has_batch_at(
        "cloud_pro", runtimes=["claude-code", "claude_code"]
    )
    assert len(got["runtimes"]) == 1


def test_helper_feature_ids_normalise_and_dedup(ent):
    got = ent.has_batch_at(
        "cloud_pro", features=["fleet", " Fleet ", "fleet"]
    )
    assert len(got["features"]) == 1


def test_helper_free_feature_is_granted_on_every_perspective(ent):
    """A FREE feature is granted on every perspective (including OSS)."""
    free_iter = iter(sorted(ent.FREE_FEATURES))
    try:
        f = next(free_iter)
    except StopIteration:
        pytest.skip("FREE_FEATURES is empty")
    for tier in ent._TIER_ORDER:
        row = ent.has_batch_at(tier, features=[f])["features"][0]
        assert row["has"] is True, (tier, f)


def test_helper_free_runtime_is_granted_on_every_perspective(ent):
    for tier in ent._TIER_ORDER:
        row = ent.has_batch_at(tier, runtimes=["openclaw"])["runtimes"][0]
        assert row["has"] is True, tier


def test_helper_zero_and_negative_capacity_are_free_floor(ent):
    for tier in ent._TIER_ORDER:
        for n in [0, -1, -100]:
            for axis in ("channels", "retention_days", "nodes"):
                got = ent.has_batch_at(tier, **{axis: n})
                assert got[axis]["has"] is True, (tier, axis, n)


# ── Helper: never-raises ────────────────────────────────────────────────────


def test_helper_never_raises_on_hypo_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("hypo build blew up")

    monkeypatch.setattr(ent, "_hypothetical_entitlement", _boom)
    assert ent.has_batch_at("oss", features=["fleet"]) is None


def test_helper_never_raises_on_normalise_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("csv normalise blew up")

    monkeypatch.setattr(ent, "_normalise_csv", _boom)
    got = ent.has_batch_at("oss", features=["fleet"])
    assert got == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


# ── Endpoint: error paths ───────────────────────────────────────────────────


def test_endpoint_missing_tier_400(client):
    resp = client.get("/api/entitlement/has-batch-at?features=fleet")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing tier"}


def test_endpoint_blank_tier_400(client):
    resp = client.get("/api/entitlement/has-batch-at?tier=&features=fleet")
    assert resp.status_code == 400
    resp = client.get("/api/entitlement/has-batch-at?tier=%20&features=fleet")
    assert resp.status_code == 400


def test_endpoint_unknown_tier_404_body_shape(client):
    resp = client.get(
        "/api/entitlement/has-batch-at?tier=bogus&features=fleet"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body == {"error": "unknown tier", "which": "tier", "tier": "bogus"}


def test_endpoint_no_axis_400(client):
    resp = client.get("/api/entitlement/has-batch-at?tier=cloud_pro")
    assert resp.status_code == 400
    body = resp.get_json()
    assert "supply at least one of" in body["error"]


def test_endpoint_blank_axes_400(client):
    resp = client.get(
        "/api/entitlement/has-batch-at?tier=cloud_pro&features=&runtimes="
    )
    assert resp.status_code == 400


# ── Endpoint: envelope shape ────────────────────────────────────────────────


def test_endpoint_envelope_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_pro"
        "&features=fleet&runtimes=claude_code&channels=5&retention_days=30"
        "&nodes=3",
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    for row in body["features"]:
        assert set(row.keys()) == _ROW_KEYS
    for row in body["runtimes"]:
        assert set(row.keys()) == _ROW_KEYS
    for slot in ("channels", "retention_days", "nodes"):
        assert set(body[slot].keys()) == _ROW_KEYS


def test_endpoint_row_types(client):
    body = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_pro&features=fleet"
        "&runtimes=claude_code&channels=5&retention_days=30&nodes=3",
    )
    for row in body["features"] + body["runtimes"]:
        assert isinstance(row["has"], bool)
        assert isinstance(row["unknown"], bool)
        assert isinstance(row["required_tier_rank"], int)
    for slot in ("channels", "retention_days", "nodes"):
        row = body[slot]
        assert isinstance(row["has"], bool)
        assert isinstance(row["unknown"], bool)


def test_endpoint_perspective_tier_normalised_uppercase(client):
    body_upper = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=%20CLOUD_PRO%20&features=fleet",
    )
    body_lower = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_pro&features=fleet",
    )
    assert body_upper["perspective_tier"] == "cloud_pro"
    assert body_upper["features"] == body_lower["features"]


def test_endpoint_perspective_metadata_carried(client, ent):
    for tier in ent._TIER_ORDER:
        body = _get_json(
            client,
            f"/api/entitlement/has-batch-at?tier={tier}&features=fleet",
        )
        assert body["perspective_tier"] == tier
        assert body["perspective_tier_label"] == ent.tier_label(tier)
        assert body["perspective_tier_rank"] == ent.tier_rank(tier)


# ── Endpoint: grace-independence + has_all rollup ───────────────────────────


def test_endpoint_oss_grace_denies_paid_feature(client, ent):
    """Even in grace, /has-batch-at?tier=oss reports has_all=False for a
    paid feature."""
    paid = _pick_paid_feature(ent)
    body = _get_json(
        client,
        f"/api/entitlement/has-batch-at?tier=oss&features={paid}",
    )
    assert body["grace"] is True
    assert body["features"][0]["has"] is False
    assert body["has_all"] is False


def test_endpoint_cloud_pro_admits_paid_feature(client, ent):
    paid = _pick_paid_feature(ent)
    body = _get_json(
        client,
        f"/api/entitlement/has-batch-at?tier=cloud_pro&features={paid}",
    )
    assert body["features"][0]["has"] is True
    assert body["has_all"] is True


def test_endpoint_has_all_flips_on_single_unknown_row(client, ent):
    """A single unknown row in the bundle flips has_all to False, even
    when every OTHER row is granted."""
    body = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_pro&features=fleet,bogus_id",
    )
    assert body["has_all"] is False


def test_endpoint_has_all_vacuously_true_with_empty_features_bundle(client):
    """When only capacity axes are supplied and they all pass, has_all is
    True (empty feature/runtime lists are trivially satisfied)."""
    body = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_pro&channels=5",
    )
    assert body["has_all"] is True


def test_endpoint_enforced_mode_returns_byte_stable_envelope(
    enforced_client, enforced
):
    """Perspective-shaped rows are grace-independent by design: enforced
    mode returns byte-identical rows for the same (perspective, bundle)."""
    paid = _pick_paid_feature(enforced)
    body = _get_json(
        enforced_client,
        f"/api/entitlement/has-batch-at?tier=oss&features={paid}",
    )
    assert body["grace"] is False
    assert body["enforced"] is True
    assert body["features"][0]["has"] is False


# ── Endpoint: never-5xx ─────────────────────────────────────────────────────


def test_endpoint_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/has-batch-at?tier=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["perspective_tier"] == "oss"
    assert body["has_all"] is False
    assert body["features"] == []


def test_endpoint_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "has_batch_at", _boom)
    resp = client.get(
        "/api/entitlement/has-batch-at?tier=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS


# ── Endpoint: cross-consistency with singular /has-*-at endpoints ───────────


def test_endpoint_features_row_parity_with_singular_at_endpoint(
    client, ent
):
    """Every feature row's ``has_*_at`` byte-equals the singular
    ``/api/entitlement/has-feature-at?tier=<p>&feature=<f>`` endpoint
    body."""
    fid = _pick_paid_feature(ent)
    body = _get_json(
        client,
        f"/api/entitlement/has-batch-at?tier=cloud_pro&features={fid}",
    )
    singular = _get_json(
        client,
        f"/api/entitlement/has-feature-at?tier=cloud_pro&feature={fid}",
    )
    assert body["features"][0]["has"] == singular["has_feature_at"]


def test_endpoint_runtimes_row_parity_with_singular_at_endpoint(
    client, ent
):
    rt = _pick_paid_runtime(ent)
    body = _get_json(
        client,
        f"/api/entitlement/has-batch-at?tier=cloud_pro&runtimes={rt}",
    )
    singular = _get_json(
        client,
        f"/api/entitlement/has-runtime-at?tier=cloud_pro&runtime={rt}",
    )
    assert body["runtimes"][0]["has"] == singular["has_runtime_at"]


def test_endpoint_channels_row_parity_with_singular_at_endpoint(client):
    body = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=oss&channels=5",
    )
    singular = _get_json(
        client,
        "/api/entitlement/has-channel-count-at?tier=oss&count=5",
    )
    assert (
        body["channels"]["has"]
        == singular["has_channel_count_at"]
    )
    assert (
        body["channels"]["required_tier"] == singular["required_tier"]
    )


def test_endpoint_retention_row_parity_with_singular_at_endpoint(client):
    body = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_starter&retention_days=90",
    )
    singular = _get_json(
        client,
        "/api/entitlement/has-retention-window-at?tier=cloud_starter&days=90",
    )
    assert (
        body["retention_days"]["has"]
        == singular["has_retention_window_at"]
    )


def test_endpoint_nodes_row_parity_with_singular_at_endpoint(client):
    body = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=oss&nodes=5",
    )
    singular = _get_json(
        client,
        "/api/entitlement/has-node-count-at?tier=oss&count=5",
    )
    assert (
        body["nodes"]["has"] == singular["has_node_count_at"]
    )
    assert body["nodes"]["required_tier"] == singular["required_tier"]


# ── Endpoint: cross-consistency with /min-tier-batch-at ─────────────────────


def test_endpoint_required_tier_parity_with_min_tier_batch_at(client, ent):
    """``required_tier`` on every row byte-equals the sibling
    ``/api/entitlement/min-tier-batch-at?tier=<p>&...`` row for the
    same (feature / runtime / capacity value) -- a UI wiring both
    cannot see inconsistent tier state."""
    fid = _pick_paid_feature(ent)
    rt = _pick_paid_runtime(ent)
    body_has = _get_json(
        client,
        f"/api/entitlement/has-batch-at?tier=oss&features={fid}"
        f"&runtimes={rt}&channels=5&retention_days=30&nodes=5",
    )
    body_min = _get_json(
        client,
        f"/api/entitlement/min-tier-batch-at?tier=oss&features={fid}"
        f"&runtimes={rt}&channels=5&retention_days=30&nodes=5",
    )
    assert (
        body_has["features"][0]["required_tier"]
        == body_min["features"][0]["min_tier"]
    )
    assert (
        body_has["runtimes"][0]["required_tier"]
        == body_min["runtimes"][0]["min_tier"]
    )
    assert (
        body_has["channels"]["required_tier"]
        == body_min["channels"]["min_tier"]
    )
    assert (
        body_has["retention_days"]["required_tier"]
        == body_min["retention_days"]["min_tier"]
    )
    assert (
        body_has["nodes"]["required_tier"] == body_min["nodes"]["min_tier"]
    )


# ── Endpoint: envelope stability across many input branches ─────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-batch-at?tier=oss&features=fleet",
        "/api/entitlement/has-batch-at?tier=cloud_pro&features=fleet",
        "/api/entitlement/has-batch-at?tier=enterprise&features=fleet",
        "/api/entitlement/has-batch-at?tier=trial&features=fleet",
        "/api/entitlement/has-batch-at?tier=oss&runtimes=claude_code",
        "/api/entitlement/has-batch-at?tier=oss&channels=5",
        "/api/entitlement/has-batch-at?tier=oss&retention_days=30",
        "/api/entitlement/has-batch-at?tier=oss&nodes=5",
        "/api/entitlement/has-batch-at?tier=oss&features=bogus_id",
        "/api/entitlement/has-batch-at?tier=oss&features=fleet&channels=five",
        "/api/entitlement/has-batch-at?tier=oss&features=fleet,sso"
        "&runtimes=claude_code,codex&channels=5&retention_days=30&nodes=3",
    ],
)
def test_endpoint_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert isinstance(body["features"], list)
    assert isinstance(body["runtimes"], list)


def test_endpoint_features_supply_order_preserved(client):
    body = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_pro&features=sso,fleet",
    )
    keys = [r["key"] for r in body["features"]]
    assert keys == ["sso", "fleet"]


def test_endpoint_runtime_alias_canonicalises(client):
    body = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_pro&runtimes=claude-code",
    )
    assert body["runtimes"][0]["key"] == "claude_code"


def test_endpoint_retention_none_is_unset(client):
    """``retention_days`` omitted / blank means unset -- NOT unlimited.
    The row slot collapses to None (matches has_batch)."""
    body = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_pro&features=fleet",
    )
    assert body["retention_days"] is None


# ── Endpoint: parity with LIVE has_batch on shape ───────────────────────────


def test_endpoint_shape_superset_of_live_has_batch(client):
    """The perspective sibling's envelope is a superset of the LIVE
    /has-batch envelope: adds ``perspective_tier`` / label / rank on
    top; everything else has the same shape."""
    body_at = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_pro&features=fleet",
    )
    body_live = _get_json(
        client,
        "/api/entitlement/has-batch?features=fleet",
    )
    live_keys = set(body_live.keys())
    at_keys = set(body_at.keys())
    added = at_keys - live_keys
    assert added == {
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
    }
    assert live_keys - at_keys == set()


def test_endpoint_row_shape_matches_live_has_batch(client):
    body_at = _get_json(
        client,
        "/api/entitlement/has-batch-at?tier=cloud_pro&features=fleet",
    )
    body_live = _get_json(
        client,
        "/api/entitlement/has-batch?features=fleet",
    )
    at_row_keys = set(body_at["features"][0].keys())
    live_row_keys = set(body_live["features"][0].keys())
    assert at_row_keys == live_row_keys
