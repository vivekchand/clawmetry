"""Tests for :func:`clawmetry.entitlements.has_all_breakdown` and the
``/api/entitlement/has-all-breakdown`` endpoint.

The breakdown helper is the boolean-fold twin of
:func:`min_tier_for_all_breakdown`. Where the reverse-lookup breakdown
identifies which axis is *binding* the aggregate required-tier floor,
this helper identifies which axis (or axes) is *blocking* the LIVE
aggregate grant. A paywall diagnostics tile can then render "denied
here BECAUSE of channels (Starter caps at 5, you asked for 8)" off
one round-trip alongside "the cheapest tier that would grant it is
Pro BECAUSE of channels" from the reverse-lookup companion.

This file pins:

* Parity with :func:`has_all` on the aggregate fold across the five
  capacity axes -- so a future tier shuffle or singular-scalar
  posture change breaks loudly here.
* The per-axis row shape (``kind``, ``supplied``, ``has``, ``blocking``,
  plus ``items`` / ``unknown`` for grants and ``value`` for capacities).
* ``blocking_axes`` identification -- single-axis denials, multi-axis
  denials, empty on ``has_all=True``, empty on the "nothing supplied"
  edge.
* Grace vs enforce -- grace turns every fully-known bundle into
  ``has_all=True`` / empty ``blocking_axes`` (matches :func:`has_all`);
  unknown / empty / non-int input still collapses the fold in grace
  (matches the singular scalars' strict-``False`` typo posture).
* The never-raise contract on unknown ids, non-int capacity input,
  and the "nothing supplied" edge.
* HTTP envelope shape (``current_tier`` / ``grace`` / ``enforced``
  mirror the sibling ``/has-*`` endpoints; the breakdown fields sit
  alongside).
* Pairing invariants with the reverse-lookup breakdown
  (:func:`min_tier_for_all_breakdown`) on the same inputs -- axes
  echoes match and the two envelopes render coherently in the same
  paywall tooltip.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


AXIS_KEYS = ("features", "runtimes", "channels", "retention_days", "nodes")


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


# ── envelope shape + null / empty edges ────────────────────────────────────


def test_no_constraints_returns_empty_envelope(ent):
    """Mirrors :func:`has_all`: "nothing asked" collapses the aggregate
    to ``False`` (empty-``False`` typo posture) but no axis is
    *blocking* since none was asked about."""
    out = ent.has_all_breakdown()
    assert out["has_all"] is False
    for k in AXIS_KEYS:
        assert out["axes"][k] is None
    assert out["blocking_axes"] == []


def test_all_axes_none_returns_empty_envelope(ent):
    out = ent.has_all_breakdown(
        features=None,
        runtimes=None,
        channels=None,
        retention_days=None,
        nodes=None,
    )
    assert out["has_all"] is False
    for k in AXIS_KEYS:
        assert out["axes"][k] is None
    assert out["blocking_axes"] == []


def test_envelope_top_level_keys(ent):
    out = ent.has_all_breakdown(features=["fleet"])
    assert set(out.keys()) == {"has_all", "axes", "blocking_axes"}
    assert set(out["axes"].keys()) == set(AXIS_KEYS)


# ── parity with has_all across the five axes ───────────────────────────────


def test_parity_features_only(ent):
    for feats in (["fleet"], ["sso"], ["fleet", "sso"]):
        out = ent.has_all_breakdown(features=feats)
        assert out["has_all"] == ent.has_all(features=feats), feats


def test_parity_runtimes_only(ent):
    for rts in (["openclaw"], ["claude_code"], ["openclaw", "claude_code"]):
        out = ent.has_all_breakdown(runtimes=rts)
        assert out["has_all"] == ent.has_all(runtimes=rts), rts


def test_parity_capacity_only(ent):
    for kw in ({"channels": 5}, {"retention_days": 30}, {"nodes": 2}):
        out = ent.has_all_breakdown(**kw)
        assert out["has_all"] == ent.has_all(**kw), kw


def test_parity_mixed_bundle(ent):
    bundle = dict(
        features=["fleet"],
        runtimes=["claude_code"],
        channels=8,
        retention_days=30,
        nodes=2,
    )
    out = ent.has_all_breakdown(**bundle)
    assert out["has_all"] == ent.has_all(**bundle)


def test_parity_empty_grant_axis_collapses_to_false(ent):
    """``features=[]`` collapses :func:`has_all` to False (its empty-
    ``False`` typo posture); the breakdown must fold the same way and
    surface the features axis as blocking."""
    out = ent.has_all_breakdown(features=[])
    assert out["has_all"] is False
    assert out["has_all"] == ent.has_all(features=[])
    row = out["axes"]["features"]
    assert row is not None
    assert row["has"] is False
    assert row["blocking"] is True
    assert "features" in out["blocking_axes"]


def test_parity_unknown_grant_token_collapses_to_false(ent):
    """An unknown token in features collapses :func:`has_all` to False
    even under grace (matches :func:`has_features` strict typo posture);
    the breakdown must fold the same way and surface the axis as
    blocking with the typo in ``unknown``."""
    out = ent.has_all_breakdown(features=["fleet", "bogus-feature"])
    assert out["has_all"] is False
    assert out["has_all"] == ent.has_all(features=["fleet", "bogus-feature"])
    row = out["axes"]["features"]
    assert row["has"] is False
    assert row["blocking"] is True
    assert "bogus-feature" in row["unknown"]
    assert "fleet" in row["items"]


def test_parity_non_int_capacity_collapses_to_false(ent):
    """Non-int capacity value collapses :func:`has_all` to False; the
    breakdown must fold the same way and surface the axis as blocking
    with the raw value in ``value``."""
    out = ent.has_all_breakdown(channels="five")
    assert out["has_all"] is False
    assert out["has_all"] == ent.has_all(channels="five")
    row = out["axes"]["channels"]
    assert row["has"] is False
    assert row["blocking"] is True
    assert row["value"] == "five"


# ── blocking-axis identification ───────────────────────────────────────────


def test_blocking_axes_empty_when_has_all_true(ent):
    """Grace grants every fully-known bundle; blocking_axes must be
    empty and every axis row's ``blocking`` must be False."""
    out = ent.has_all_breakdown(
        features=["fleet"],
        runtimes=["openclaw"],
        channels=1,
        retention_days=7,
        nodes=1,
    )
    assert out["has_all"] is True
    assert out["blocking_axes"] == []
    for k in AXIS_KEYS:
        row = out["axes"][k]
        if row is not None:
            assert row["blocking"] is False


def test_blocking_axes_single_axis_denial(ent):
    """When only one axis' :func:`has_*` is False, only that axis is
    blocking. Uses ``channels=-1`` to force a per-axis False without
    depending on tier caps (grace-independent typo path via a
    non-positive channel count)."""
    # Force the fold to False by giving features=[] alone -- only the
    # features axis can be blocking.
    out = ent.has_all_breakdown(
        features=[],
        runtimes=["openclaw"],
    )
    assert out["has_all"] is False
    assert out["blocking_axes"] == ["features"]
    assert out["axes"]["features"]["blocking"] is True
    assert out["axes"]["runtimes"]["blocking"] is False


def test_blocking_axes_multi_axis_denial_ordered(ent):
    """When several axes deny, ``blocking_axes`` lists them in envelope
    order (features / runtimes / channels / retention_days / nodes)."""
    out = ent.has_all_breakdown(
        features=[], runtimes=[], channels="five"
    )
    assert out["has_all"] is False
    # features + runtimes + channels all block; envelope order preserved.
    assert out["blocking_axes"] == ["features", "runtimes", "channels"]


def test_blocking_axes_null_when_nothing_supplied(ent):
    """Empty envelope: has_all=False (empty-``False`` typo posture)
    but no axis was asked about, so ``blocking_axes`` stays empty."""
    out = ent.has_all_breakdown()
    assert out["has_all"] is False
    assert out["blocking_axes"] == []


# ── per-axis row shape ─────────────────────────────────────────────────────


def test_grant_axis_row_shape(ent):
    out = ent.has_all_breakdown(features=["fleet"])
    row = out["axes"]["features"]
    assert row["kind"] == "features"
    assert row["supplied"] is True
    assert row["items"] == ["fleet"]
    assert row["unknown"] == []
    assert isinstance(row["has"], bool)
    assert isinstance(row["blocking"], bool)


def test_runtime_axis_row_shape(ent):
    out = ent.has_all_breakdown(runtimes=["openclaw"])
    row = out["axes"]["runtimes"]
    assert row["kind"] == "runtimes"
    assert row["supplied"] is True
    assert row["items"] == ["openclaw"]
    assert row["unknown"] == []
    assert isinstance(row["has"], bool)


def test_capacity_axis_row_shape(ent):
    out = ent.has_all_breakdown(channels=5)
    row = out["axes"]["channels"]
    assert row["kind"] == "channels"
    assert row["supplied"] is True
    assert row["value"] == 5
    assert isinstance(row["has"], bool)


def test_capacity_row_preserves_bad_input(ent):
    """A non-int capacity value keeps ``supplied=True`` and echoes the
    raw input in ``value`` so a tooltip can flag the typo. ``has`` is
    False and the axis is blocking."""
    out = ent.has_all_breakdown(channels="five")
    row = out["axes"]["channels"]
    assert row["supplied"] is True
    assert row["value"] == "five"
    assert row["has"] is False
    assert row["blocking"] is True


def test_runtime_axis_canonicalises_aliases(ent):
    """``claude-code`` -> ``claude_code`` matches the singular
    :func:`has_runtimes` posture (aliases collapse)."""
    out = ent.has_all_breakdown(runtimes=["claude-code"])
    row = out["axes"]["runtimes"]
    assert "claude_code" in row["items"]


def test_grant_axis_splits_known_from_unknown(ent):
    out = ent.has_all_breakdown(features=["fleet", "bogus1", "bogus2"])
    row = out["axes"]["features"]
    assert row["items"] == ["fleet"]
    assert set(row["unknown"]) == {"bogus1", "bogus2"}


def test_unsupplied_axes_are_none(ent):
    """Axes the caller did not supply short-circuit to ``None`` at the
    envelope level (mirrors :func:`min_tier_for_all_breakdown`)."""
    out = ent.has_all_breakdown(features=["fleet"])
    assert out["axes"]["runtimes"] is None
    assert out["axes"]["channels"] is None
    assert out["axes"]["retention_days"] is None
    assert out["axes"]["nodes"] is None


# ── grace / enforce posture ────────────────────────────────────────────────


def test_grace_grants_fully_known_bundle(ent):
    """Grace posture: every fully-known bundle folds to ``has_all=True``
    with empty ``blocking_axes`` (matches :func:`has_all` grace)."""
    out = ent.has_all_breakdown(
        features=["fleet", "sso"],
        runtimes=["openclaw", "claude_code"],
        channels=100,
        retention_days=90,
        nodes=100,
    )
    assert out["has_all"] is True
    assert out["blocking_axes"] == []


def test_grace_still_denies_unknown_token(ent):
    """Grace does NOT rescue an unknown grant token (:func:`has_features`
    strict typo posture is preserved even in grace); the breakdown
    surfaces the axis as blocking with the typo in ``unknown``."""
    out = ent.has_all_breakdown(features=["Fleeet"])
    assert out["has_all"] is False
    row = out["axes"]["features"]
    assert row["has"] is False
    assert row["blocking"] is True
    assert "fleeet" in row["unknown"] or "Fleeet" in row["unknown"]


def test_grace_still_denies_non_int_capacity(ent):
    out = ent.has_all_breakdown(channels="five")
    assert out["has_all"] is False
    assert "channels" in out["blocking_axes"]


# ── pair-invariants with min_tier_for_all_breakdown ────────────────────────


def test_axes_echo_matches_reverse_lookup_breakdown(ent):
    """The two breakdowns must agree on axis-level ``supplied`` / echo
    slots so a paywall tooltip pairing them renders coherently."""
    bundle = dict(
        features=["fleet"],
        runtimes=["claude_code"],
        channels=8,
        retention_days=30,
        nodes=2,
    )
    fwd = ent.has_all_breakdown(**bundle)
    rev = ent.min_tier_for_all_breakdown(**bundle)
    for key in AXIS_KEYS:
        f_row = fwd["axes"][key]
        r_row = rev["axes"][key]
        assert (f_row is None) == (r_row is None), key
        if f_row is None:
            continue
        assert f_row["kind"] == r_row["kind"]
        assert f_row["supplied"] == r_row["supplied"]
        if "items" in f_row and "items" in r_row:
            assert f_row["items"] == r_row["items"], key
        if "value" in f_row and "value" in r_row:
            assert f_row["value"] == r_row["value"], key


# ── never-raise contract ───────────────────────────────────────────────────


def test_never_raises_on_garbage(ent):
    """Every bad-input shape must fall through to the empty envelope
    rather than 500-ing / raising."""
    for bad in (
        {"features": object()},
        {"runtimes": 42},
        {"channels": {"nope": "dict"}},
        {"retention_days": ["not", "int"]},
        {"nodes": None},
    ):
        out = ent.has_all_breakdown(**bad)
        assert isinstance(out, dict)
        assert "has_all" in out
        assert "axes" in out
        assert "blocking_axes" in out


def test_never_raises_when_delegate_boom(ent, monkeypatch):
    """A delegate raising mid-fold must short-circuit to the empty
    envelope, not propagate."""
    def _boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "has_features", _boom)
    out = ent.has_all_breakdown(features=["fleet"])
    assert out["has_all"] is False
    assert out["blocking_axes"] == []
    assert out["axes"]["features"] is None


# ── HTTP endpoint ──────────────────────────────────────────────────────────


def test_endpoint_400_on_no_args(client):
    resp = client.get("/api/entitlement/has-all-breakdown")
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body


def test_endpoint_features_only_returns_shape(ent, client):
    resp = client.get("/api/entitlement/has-all-breakdown?features=fleet")
    assert resp.status_code == 200
    body = resp.get_json()
    for k in (
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
        "axes",
        "blocking_axes",
    ):
        assert k in body, f"missing key {k}"
    assert body["features"] == ["fleet"]
    assert body["has_all"] == ent.has_all(features=["fleet"])


def test_endpoint_mixed_bundle_matches_helper(ent, client):
    resp = client.get(
        "/api/entitlement/has-all-breakdown"
        "?features=fleet&runtimes=claude_code&channels=8"
        "&retention_days=30&nodes=2"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    expected = ent.has_all_breakdown(
        features=["fleet"],
        runtimes=["claude_code"],
        channels=8,
        retention_days=30,
        nodes=2,
    )
    assert body["has_all"] == expected["has_all"]
    assert body["blocking_axes"] == expected["blocking_axes"]
    assert body["axes"] == expected["axes"]


def test_endpoint_bad_capacity_value_still_200(ent, client):
    """Non-int capacity doesn't 400 -- the axis still surfaces with
    ``has=false`` and the raw input in ``value`` (matches ``/has-*``
    never-crash posture)."""
    resp = client.get(
        "/api/entitlement/has-all-breakdown?features=fleet&channels=five"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_all"] is False
    assert body["axes"]["channels"] is not None
    assert body["axes"]["channels"]["value"] == "five"
    assert "channels" in body["blocking_axes"]


def test_endpoint_unknown_feature_flags_blocking(client):
    resp = client.get("/api/entitlement/has-all-breakdown?features=bogus")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["has_all"] is False
    assert "features" in body["blocking_axes"]
    row = body["axes"]["features"]
    assert row is not None
    assert "bogus" in row["unknown"]


def test_endpoint_grace_flag_true_on_default_install(client):
    """The default OSS install ships in grace -- the ``grace`` flag
    MUST be True and ``enforced`` MUST be False in the response."""
    resp = client.get("/api/entitlement/has-all-breakdown?features=fleet")
    body = resp.get_json()
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_current_tier_defaults_to_oss(client):
    resp = client.get("/api/entitlement/has-all-breakdown?features=fleet")
    body = resp.get_json()
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


def test_endpoint_capacity_only_returns_shape(ent, client):
    resp = client.get("/api/entitlement/has-all-breakdown?nodes=1")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["nodes"] == 1
    assert body["has_all"] == ent.has_all(nodes=1)
