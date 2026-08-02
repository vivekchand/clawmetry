"""Tests for the ``has_batch`` per-item boolean-gate helper and its paired
``/api/entitlement/has-batch`` endpoint -- per-item plural sibling of
:func:`clawmetry.entitlements.has_feature` / :func:`~clawmetry.entitlements.has_runtime`
/ :func:`~clawmetry.entitlements.has_channel_count`.

Where the singular ``has_*`` scalars answer "does the resolved entitlement
grant this ONE item?", ``has_batch`` answers the same question for every
item in a caller-supplied bundle across all five capacity axes at once so a
paywall MATRIX UI ("show every requested feature + runtime + capacity row
with its individual granted flag AND the cheapest tier that would unlock
it") renders off ONE round-trip instead of N calls to the singular
endpoints.

This file pins:

1. Envelope shape parity (fixed key set) on the ``/has-batch`` endpoint
   across every input branch so a frontend can bind fields off the URL
   without a branch on the underlying resolver state.
2. Per-row shape parity across every axis (fixed row-key set).
3. Per-row parity with the singular ``has_feature`` / ``has_runtime`` /
   ``has_channel_count`` scalars: the batch cannot silently drift from the
   singular scalar on the same input.
4. Strict-typo-fail-closed posture: unknown feature/runtime ids and non-int
   capacity values flip ``unknown=True`` / ``has=False`` -- NOT silently
   granted in grace (matches the singular scalars, differs from
   ``lock_reasons_batch`` which is diagnostic, not gate-shaped).
5. Grace-mode invariant: every KNOWN row reports ``has=True`` while grace
   is on, so wiring this into a matrix gate today changes no current
   behaviour.
6. Runtime alias canonicalisation (``claude-code`` -> ``claude_code``) and
   dedup after canonicalisation.
7. ``retention_days=None`` means *unset*, NOT *unlimited* (matches
   ``min_tier_batch`` / ``lock_reasons_batch``).
8. Never-5xx: any resolver blowup collapses to the fail-closed envelope.
9. Endpoint 400 when no axis is supplied (matches ``/min-tier-batch``).
10. ``has_all`` rollup: True iff every emitted row is ``has=True`` AND
    ``unknown=False`` (single unknown or single missing flips it False).
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ``~/.clawmetry/license.key`` or ``cloud_plan.json`` leaks in.
    Enforcement off by default -- matches the project rollout posture."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture -- ``CLAWMETRY_ENFORCE=1`` flips ``ent.grace``
    to False so the grace pass-through collapses and paid axes report their
    post-enforce answers."""
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
def enforced_cloud_pro(monkeypatch, tmp_path):
    """Enforcement on, cloud_pro plan wired via the disk cache the resolver
    reads. Grants every paid runtime + most features so the batch on OSS-
    denied items flips to has=True."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
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
    assert resp.status_code == expected_status, (url, resp.status_code, resp.data)
    return resp.get_json()


def _pick_paid_feature(ent) -> str:
    """Return one feature id that lives above the OSS tier so ``required_tier``
    is a real paid tier (Starter+). Picked at runtime from PAID_FEATURES so the
    test is not brittle against catalogue reshuffles."""
    for f in sorted(ent.PAID_FEATURES):
        return f
    raise RuntimeError("no PAID_FEATURES ids available in the catalogue")


def _pick_paid_runtime(ent) -> str:
    """Return one runtime id above OSS -- Starter+ at least."""
    for r in sorted(ent.PAID_RUNTIMES):
        return r
    raise RuntimeError("no PAID_RUNTIMES ids available in the catalogue")


# ── has_batch scalar: envelope shape ────────────────────────────────────────


def test_scalar_empty_call_shape(ent):
    """No axes supplied -- returns the all-empty envelope (no rows, three
    axis slots None). Matches ``min_tier_batch()``'s empty-call shape."""
    out = ent.has_batch()
    assert out == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def test_scalar_shape_top_level_keys(ent):
    """Envelope keys are byte-stable regardless of axis mix."""
    for kwargs in (
        {"features": ["fleet"]},
        {"runtimes": ["openclaw"]},
        {"channels": 3},
        {"retention_days": 7},
        {"nodes": 2},
        {"features": ["fleet"], "runtimes": ["openclaw"], "channels": 3},
    ):
        out = ent.has_batch(**kwargs)
        assert set(out.keys()) == {
            "features",
            "runtimes",
            "channels",
            "retention_days",
            "nodes",
        }, kwargs


def test_scalar_row_shape_across_axes(ent):
    """Every emitted row (feature, runtime, channels, retention_days, nodes)
    carries the same 7-key set."""
    out = ent.has_batch(
        features=["fleet"],
        runtimes=["openclaw"],
        channels=3,
        retention_days=7,
        nodes=2,
    )
    assert set(out["features"][0].keys()) == _ROW_KEYS
    assert set(out["runtimes"][0].keys()) == _ROW_KEYS
    assert set(out["channels"].keys()) == _ROW_KEYS
    assert set(out["retention_days"].keys()) == _ROW_KEYS
    assert set(out["nodes"].keys()) == _ROW_KEYS


# ── has_batch scalar: grace vs enforce ──────────────────────────────────────


def test_scalar_grace_every_known_row_is_true(ent):
    """Grace invariant: every KNOWN feature id, KNOWN runtime id, and every
    finite capacity value reports ``has=True`` in grace. Wiring this into a
    matrix gate today changes no behaviour."""
    feats = sorted(ent.ALL_FEATURES)[:3]
    rts = sorted(ent.ALL_RUNTIMES)[:3]
    out = ent.has_batch(
        features=feats,
        runtimes=rts,
        channels=21,
        retention_days=365,
        nodes=100,
    )
    for row in out["features"] + out["runtimes"]:
        assert row["has"] is True, row
        assert row["unknown"] is False, row
    assert out["channels"]["has"] is True
    assert out["retention_days"]["has"] is True
    assert out["nodes"]["has"] is True


def test_scalar_enforce_paid_feature_is_false_on_oss(enforced):
    """Post-enforcement on OSS: a paid feature reports ``has=False`` with
    ``required_tier`` naming the cheapest unlocking tier."""
    paid = _pick_paid_feature(enforced)
    out = enforced.has_batch(features=[paid])
    row = out["features"][0]
    assert row["key"] == paid
    assert row["kind"] == "feature"
    assert row["has"] is False, row
    assert row["unknown"] is False, row
    assert row["required_tier"] is not None
    assert row["required_tier"] != enforced.TIER_OSS
    assert row["required_tier_rank"] > 0


def test_scalar_enforce_paid_runtime_is_false_on_oss(enforced):
    """Post-enforcement on OSS: a paid runtime reports has=False."""
    paid = _pick_paid_runtime(enforced)
    out = enforced.has_batch(runtimes=[paid])
    row = out["runtimes"][0]
    assert row["key"] == paid
    assert row["has"] is False, row
    assert row["unknown"] is False, row
    assert row["required_tier"] is not None


def test_scalar_enforce_free_runtime_is_true_on_oss(enforced):
    """A FREE runtime (openclaw) stays granted post-enforcement -- the free
    floor covers it."""
    out = enforced.has_batch(runtimes=["openclaw"])
    row = out["runtimes"][0]
    assert row["has"] is True, row
    assert row["unknown"] is False, row
    assert row["required_tier"] == enforced.TIER_OSS


def test_scalar_enforce_cloud_pro_grants_paid_feature(enforced_cloud_pro):
    """Post-enforcement on cloud_pro: a Pro-covered feature flips to has=True."""
    # Pick a feature that Pro covers -- fleet is a canonical starter/pro feature
    # in the catalogue.
    out = enforced_cloud_pro.has_batch(features=["fleet"])
    row = out["features"][0]
    assert row["has"] is True, row
    assert row["unknown"] is False, row


# ── has_batch scalar: strict-typo-fail-closed posture ───────────────────────


def test_scalar_unknown_feature_is_fail_closed(ent):
    """Unknown feature id: ``unknown=True`` / ``has=False`` even in grace.
    This is DIFFERENT from ``lock_reasons_batch`` which reports ``allowed=True``
    for unknown ids (diagnostic axis, not gate-shaped)."""
    out = ent.has_batch(features=["totally_fake_feature_xyz"])
    row = out["features"][0]
    assert row["unknown"] is True, row
    assert row["has"] is False, row
    assert row["required_tier"] is None
    assert row["required_tier_rank"] == -1


def test_scalar_unknown_runtime_is_fail_closed(ent):
    """Unknown runtime id: fail-closed."""
    out = ent.has_batch(runtimes=["totally_fake_runtime_xyz"])
    row = out["runtimes"][0]
    assert row["unknown"] is True, row
    assert row["has"] is False, row


def test_scalar_empty_feature_id_is_fail_closed(ent):
    """Whitespace / empty feature id after normalisation drops from the row list
    (``_normalise_csv`` strips empty tokens). No row emitted for
    ``features=[' ', '', '  ']``."""
    out = ent.has_batch(features=["  ", "", "\t"])
    assert out["features"] == []


def test_scalar_capacity_non_int_is_fail_closed(ent):
    """Non-int capacity value: ``unknown=True`` / ``has=False`` (matches
    ``has_channel_count("bogus")`` -> False strict posture)."""
    out = ent.has_batch(channels="bogus")
    assert out["channels"] == {
        "key": "bogus",
        "kind": "channels",
        "has": False,
        "unknown": True,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
    }


def test_scalar_capacity_none_is_axis_absent(ent):
    """``channels=None`` at the kwarg means AXIS NOT SUPPLIED, not
    ``allows_channel_count(None)`` -- matches ``min_tier_batch`` and
    ``lock_reasons_batch``. The axis slot in the envelope is None."""
    out = ent.has_batch(channels=None)
    assert out["channels"] is None


def test_scalar_retention_days_none_is_axis_absent_not_unlimited(ent):
    """``retention_days=None`` at the kwarg does NOT hit the unlimited
    sentinel branch of :meth:`Entitlement.allows_retention_window`. Same
    "not supplied" posture as the sibling batches. Verifying explicitly
    because unlimited is a legitimate call on the singular helper."""
    out = ent.has_batch(retention_days=None)
    assert out["retention_days"] is None


def test_scalar_retention_days_int_is_supplied(ent):
    """A finite int on retention_days emits a row."""
    out = ent.has_batch(retention_days=30)
    assert out["retention_days"] is not None
    assert out["retention_days"]["kind"] == "retention_days"
    assert out["retention_days"]["key"] == "30"
    assert out["retention_days"]["has"] is True  # grace


# ── has_batch scalar: runtime alias + dedup ─────────────────────────────────


def test_scalar_runtime_alias_canonicalises(ent):
    """``claude-code`` (hyphen) canonicalises to ``claude_code`` (underscore)
    on the singular ``has_runtime`` scalar; the batch does the same."""
    out = ent.has_batch(runtimes=["claude-code"])
    assert len(out["runtimes"]) == 1
    row = out["runtimes"][0]
    assert row["key"] == "claude_code"
    assert row["unknown"] is False, row


def test_scalar_runtime_alias_dedups_after_canonicalisation(ent):
    """Both aliases of the same runtime (``claude-code`` and ``claude_code``)
    collapse to ONE row after canonicalisation."""
    out = ent.has_batch(runtimes=["claude-code", "claude_code"])
    assert len(out["runtimes"]) == 1
    assert out["runtimes"][0]["key"] == "claude_code"


def test_scalar_feature_dedup_preserves_first_seen_order(ent):
    """``_normalise_csv`` drops duplicates while preserving first-seen order."""
    out = ent.has_batch(features=["fleet", "sso", "fleet", "otel_export"])
    keys = [r["key"] for r in out["features"]]
    # Only unique ids, in first-seen order.
    assert len(keys) == len(set(keys))
    # ``fleet`` appears before ``sso`` because it was first seen first.
    assert keys.index("fleet") < keys.index("sso")


# ── has_batch scalar: per-row parity with singular scalars ──────────────────


def test_scalar_row_has_parity_features(ent):
    """For every id in ALL_FEATURES, the batch's per-row ``has`` byte-equals
    the singular :func:`has_feature` scalar. Pins that the batch cannot
    silently drift from the scalar."""
    for f in sorted(ent.ALL_FEATURES):
        row = ent.has_batch(features=[f])["features"][0]
        assert row["has"] is ent.has_feature(f), f
        assert row["unknown"] is False, f


def test_scalar_row_has_parity_runtimes(ent):
    """For every id in ALL_RUNTIMES, per-row ``has`` byte-equals
    :func:`has_runtime`."""
    for r in sorted(ent.ALL_RUNTIMES):
        row = ent.has_batch(runtimes=[r])["runtimes"][0]
        assert row["has"] is ent.has_runtime(r), r


def test_scalar_row_has_parity_channels(ent):
    """Per-row ``has`` on the channels axis byte-equals
    :func:`has_channel_count`."""
    for n in (0, 1, 3, 4, 21, 100):
        row = ent.has_batch(channels=n)["channels"]
        assert row["has"] is ent.has_channel_count(n), n


def test_scalar_row_required_tier_parity_features(ent):
    """Per-row ``required_tier`` on the features axis byte-equals
    :func:`min_tier_for_feature` on the same input."""
    for f in sorted(ent.ALL_FEATURES):
        row = ent.has_batch(features=[f])["features"][0]
        assert row["required_tier"] == ent.min_tier_for_feature(f), f


def test_scalar_row_required_tier_parity_runtimes(ent):
    """Per-row ``required_tier`` on the runtimes axis byte-equals
    :func:`min_tier_for_runtime`."""
    for r in sorted(ent.ALL_RUNTIMES):
        row = ent.has_batch(runtimes=[r])["runtimes"][0]
        assert row["required_tier"] == ent.min_tier_for_runtime(r), r


def test_scalar_row_required_tier_parity_channels(ent):
    """Per-row ``required_tier`` on the channels axis byte-equals
    :func:`min_tier_for_channel_count`."""
    for n in (0, 1, 3, 4, 21, 100):
        row = ent.has_batch(channels=n)["channels"]
        assert row["required_tier"] == ent.min_tier_for_channel_count(n), n


# ── has_batch scalar: never-raises ──────────────────────────────────────────


def test_scalar_never_raises_on_resolver_blowup(monkeypatch, ent):
    """A blowup in :func:`get_entitlement` collapses to the OSS-free
    fallback resolver so per-row rendering keeps going (matches the
    ``lock_reasons_batch`` posture)."""
    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    out = ent.has_batch(features=["fleet"])
    # Fallback OSS-free resolver: grace still True on the fallback shape, so
    # the row's has flag reflects the OSS-free grant (True in grace).
    assert isinstance(out["features"], list)
    assert len(out["features"]) == 1


def test_scalar_never_raises_on_normalise_blowup(monkeypatch, ent):
    """A blowup mid-normalisation collapses to the empty envelope."""
    def _boom(*a, **kw):
        raise RuntimeError("normalise blew up")

    monkeypatch.setattr(ent, "_normalise_csv", _boom)
    out = ent.has_batch(features=["fleet"])
    assert out == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


# ── /api/entitlement/has-batch endpoint ─────────────────────────────────────


def test_endpoint_no_args_400s(client):
    """Missing every axis -- 400 (matches ``/min-tier-batch``'s posture)."""
    resp = client.get("/api/entitlement/has-batch")
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body


def test_endpoint_features_only_shape(client):
    """Features-only call: envelope key set is byte-stable."""
    body = _get_json(client, "/api/entitlement/has-batch?features=fleet")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert len(body["features"]) == 1
    assert body["runtimes"] == []
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None
    assert set(body["features"][0].keys()) == _ROW_KEYS


def test_endpoint_runtimes_only_shape(client):
    """Runtimes-only call: envelope stable, only runtimes list populated."""
    body = _get_json(client, "/api/entitlement/has-batch?runtimes=openclaw")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["features"] == []
    assert len(body["runtimes"]) == 1
    assert body["channels"] is None
    assert set(body["runtimes"][0].keys()) == _ROW_KEYS


def test_endpoint_channels_only_shape(client):
    """Channels-only capacity call."""
    body = _get_json(client, "/api/entitlement/has-batch?channels=3")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["channels"] is not None
    assert body["channels"]["kind"] == "channels"
    assert set(body["channels"].keys()) == _ROW_KEYS


def test_endpoint_retention_days_only_shape(client):
    """Retention-days-only capacity call."""
    body = _get_json(client, "/api/entitlement/has-batch?retention_days=30")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["retention_days"] is not None
    assert body["retention_days"]["kind"] == "retention_days"
    assert body["retention_days"]["key"] == "30"


def test_endpoint_nodes_only_shape(client):
    """Nodes-only capacity call."""
    body = _get_json(client, "/api/entitlement/has-batch?nodes=2")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["nodes"] is not None
    assert body["nodes"]["kind"] == "nodes"


def test_endpoint_mixed_axes_shape(client):
    """All 5 axes at once: envelope stable, every axis populated."""
    body = _get_json(
        client,
        "/api/entitlement/has-batch?features=fleet,sso"
        "&runtimes=openclaw,claude_code&channels=3&retention_days=7&nodes=2",
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert len(body["features"]) == 2
    assert len(body["runtimes"]) == 2
    assert body["channels"] is not None
    assert body["retention_days"] is not None
    assert body["nodes"] is not None


def test_endpoint_blank_capacity_is_axis_absent(client):
    """A blank capacity arg (``?channels=``) counts as SUPPLIED (present) but
    UNPARSEABLE, and drops through to axis-absent shape -- matches
    ``/min-tier-batch``'s posture. Since blank-only means no other axis is
    populated either, the endpoint 400s (no axis successfully parsed)."""
    resp = client.get("/api/entitlement/has-batch?channels=")
    assert resp.status_code == 400


def test_endpoint_features_present_blank_capacity_ok(client):
    """A blank capacity arg alongside a real feature works: the blank axis
    drops out (None), the feature row is emitted."""
    body = _get_json(
        client, "/api/entitlement/has-batch?features=fleet&channels="
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert len(body["features"]) == 1
    assert body["channels"] is None


def test_endpoint_unparseable_capacity_is_axis_absent(client):
    """Non-int capacity (``?channels=bogus``) drops that axis to None. Since
    nothing else is supplied, the endpoint 400s."""
    resp = client.get("/api/entitlement/has-batch?channels=bogus")
    assert resp.status_code == 400


def test_endpoint_unknown_feature_row_is_fail_closed(client):
    """Unknown feature id emits a fail-closed row (unknown=True, has=False)."""
    body = _get_json(
        client, "/api/entitlement/has-batch?features=totally_fake_xyz"
    )
    row = body["features"][0]
    assert row["unknown"] is True, row
    assert row["has"] is False, row
    assert row["required_tier"] is None
    assert row["required_tier_rank"] == -1


def test_endpoint_alias_canonicalises(client):
    """``runtimes=claude-code`` canonicalises to ``claude_code``."""
    body = _get_json(
        client, "/api/entitlement/has-batch?runtimes=claude-code"
    )
    assert body["runtimes"][0]["key"] == "claude_code"


def test_endpoint_alias_dedups(client):
    """Both aliases collapse to one row after canonicalisation."""
    body = _get_json(
        client,
        "/api/entitlement/has-batch?runtimes=claude-code,claude_code",
    )
    assert len(body["runtimes"]) == 1


def test_endpoint_feature_dedup(client):
    """CSV-level feature dedup preserves first-seen order."""
    body = _get_json(
        client, "/api/entitlement/has-batch?features=fleet,sso,fleet"
    )
    keys = [r["key"] for r in body["features"]]
    assert len(keys) == 2
    assert keys[0] == "fleet"
    assert keys[1] == "sso"


def test_endpoint_current_tier_present(client):
    """Envelope carries the resolver-context columns so the frontend does
    not have to re-hit ``/api/entitlement`` for tier metadata."""
    body = _get_json(client, "/api/entitlement/has-batch?features=fleet")
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_enforced_flag_reflects_env(enforced_client):
    """``CLAWMETRY_ENFORCE=1`` flips ``enforced=True`` and ``grace=False``."""
    body = _get_json(
        enforced_client, "/api/entitlement/has-batch?features=fleet"
    )
    assert body["enforced"] is True
    assert body["grace"] is False


# ── /has-batch endpoint: has_all rollup ─────────────────────────────────────


def test_endpoint_has_all_true_when_every_known_row_is_granted(client):
    """Grace invariant on the rollup: every known-id bundle reports
    ``has_all=True`` while grace is on."""
    body = _get_json(
        client,
        "/api/entitlement/has-batch?features=fleet,sso&runtimes=openclaw"
        "&channels=3&retention_days=7&nodes=2",
    )
    assert body["has_all"] is True


def test_endpoint_has_all_false_on_any_unknown(client):
    """A single unknown id in the bundle flips ``has_all`` to False -- even
    while grace grants the known rows -- because ``unknown`` is a callsite-
    typo signal (never grant a mystery id)."""
    body = _get_json(
        client,
        "/api/entitlement/has-batch?features=fleet,totally_fake_xyz"
        "&runtimes=openclaw",
    )
    assert body["has_all"] is False


def test_endpoint_has_all_false_on_enforce_denied(enforced_client, enforced):
    """Post-enforcement: a paid runtime on OSS flips ``has_all`` to False."""
    paid = _pick_paid_runtime(enforced)
    body = _get_json(
        enforced_client,
        f"/api/entitlement/has-batch?runtimes=openclaw,{paid}",
    )
    assert body["has_all"] is False


def test_endpoint_has_all_true_all_free(enforced_client):
    """Post-enforcement: an all-free bundle stays granted."""
    body = _get_json(
        enforced_client, "/api/entitlement/has-batch?runtimes=openclaw"
    )
    assert body["has_all"] is True


def test_endpoint_has_all_folds_capacity_axes(client):
    """Rollup includes capacity axes: a non-int capacity value 400s
    upstream (unparseable), but a supplied+parseable capacity value with
    ``has=True`` contributes to ``has_all``."""
    body = _get_json(client, "/api/entitlement/has-batch?channels=3")
    assert body["has_all"] is True


def test_endpoint_scalar_endpoint_parity(client, ent):
    """Endpoint per-row ``has`` byte-equals module scalar ``has_batch``
    per-row ``has`` on the same input."""
    body = _get_json(
        client,
        "/api/entitlement/has-batch?features=fleet,sso&runtimes=openclaw",
    )
    scalar = ent.has_batch(
        features=["fleet", "sso"], runtimes=["openclaw"]
    )
    assert [r["has"] for r in body["features"]] == [
        r["has"] for r in scalar["features"]
    ]
    assert [r["has"] for r in body["runtimes"]] == [
        r["has"] for r in scalar["runtimes"]
    ]


def test_endpoint_singular_row_parity_feature(client, ent):
    """Endpoint per-row ``has`` byte-equals the singular ``has_feature``
    scalar on the same input -- pins that the batch endpoint cannot silently
    drift from the singular scalar."""
    body = _get_json(client, "/api/entitlement/has-batch?features=fleet")
    assert body["features"][0]["has"] is ent.has_feature("fleet")


def test_endpoint_singular_row_parity_runtime(client, ent):
    """Endpoint per-row ``has`` byte-equals singular ``has_runtime``."""
    body = _get_json(
        client, "/api/entitlement/has-batch?runtimes=claude_code"
    )
    assert body["runtimes"][0]["has"] is ent.has_runtime("claude_code")


def test_endpoint_singular_row_parity_channels(client, ent):
    """Endpoint per-row ``has`` byte-equals singular ``has_channel_count``."""
    body = _get_json(client, "/api/entitlement/has-batch?channels=21")
    assert body["channels"]["has"] is ent.has_channel_count(21)


# ── /has-batch endpoint: never-5xx ──────────────────────────────────────────


def test_endpoint_never_5xx_on_resolver_blowup(monkeypatch, client):
    """A blowup in :func:`has_batch` collapses to the fail-closed envelope
    (matches sibling ``/has-feature`` / ``/has-runtime`` fallbacks). Never
    5xxs."""
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("has_batch blew up")

    monkeypatch.setattr(_ent, "has_batch", _boom)
    body = _get_json(client, "/api/entitlement/has-batch?features=fleet")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["has_all"] is False
    assert body["current_tier"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_never_5xx_on_get_entitlement_blowup(monkeypatch, client):
    """A blowup in :func:`get_entitlement` (after ``has_batch`` returns) also
    collapses to the fail-closed envelope."""
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("get_entitlement blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    body = _get_json(client, "/api/entitlement/has-batch?features=fleet")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["has_all"] is False


# ── Endpoint cross-consistency with sibling batches ─────────────────────────


def test_endpoint_current_tier_matches_entitlement_endpoint(client):
    """``current_tier`` on this envelope byte-equals the top-level
    ``/api/entitlement`` endpoint's ``tier`` field."""
    body_has = _get_json(
        client, "/api/entitlement/has-batch?features=fleet"
    )
    body_ent = _get_json(client, "/api/entitlement")
    assert body_has["current_tier"] == body_ent["tier"]


def test_endpoint_required_tier_matches_min_tier_batch(client):
    """Per-row ``required_tier`` on ``/has-batch`` byte-equals the
    corresponding row's ``min_tier`` on ``/min-tier-batch`` for the same
    input (both wrap the same underlying ``min_tier_for_*`` helpers)."""
    body_has = _get_json(
        client,
        "/api/entitlement/has-batch?features=fleet,sso&runtimes=openclaw",
    )
    body_min = _get_json(
        client,
        "/api/entitlement/min-tier-batch?features=fleet,sso&runtimes=openclaw",
    )
    has_features = {r["key"]: r["required_tier"] for r in body_has["features"]}
    min_features = {r["key"]: r["min_tier"] for r in body_min["features"]}
    assert has_features == min_features
    has_runtimes = {r["key"]: r["required_tier"] for r in body_has["runtimes"]}
    min_runtimes = {r["key"]: r["min_tier"] for r in body_min["runtimes"]}
    assert has_runtimes == min_runtimes
