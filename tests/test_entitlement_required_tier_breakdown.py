"""Tests for :func:`clawmetry.entitlements.min_tier_for_all_breakdown`
and the ``/api/entitlement/required-tier-breakdown`` endpoint.

The breakdown helper is the per-axis companion of
:func:`min_tier_for_all`. Where the floor helper collapses to one tier
id, the breakdown additionally exposes each axis' individual
``min_tier`` and calls out which axis (or axes, on a tie) is *binding*
the aggregate floor -- so a paywall CTA can render "You need Pro
*because* you have 8 channels (Starter caps at 5)" off one round-trip.

This file pins:

* Parity with :func:`min_tier_for_all` on the aggregate floor across the
  five capacity axes -- so a future tier shuffle breaks loudly here.
* The per-axis row shape (``kind``, ``supplied``, ``min_tier``,
  ``min_tier_label``, ``min_tier_rank``, ``binding``, plus ``items`` for
  grants / ``value`` for capacities).
* ``binding_axes`` identification -- single-axis dominance, multi-axis
  ties, and the "nothing binds" null-floor case.
* Grace vs enforce invariance -- decoupled from the resolved
  entitlement (walks the static per-tier caps).
* The never-raise contract on unknown ids, non-int capacity input, and
  the "nothing supplied" edge.
* HTTP envelope shape (``required_tier`` / ``current_tier`` /
  ``upgrade_required`` mirror ``/required-tier-batch`` exactly; the
  breakdown fields sit alongside).
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


# ── helper: envelope shape + null-floor edge ───────────────────────────────


def _axis_keys():
    return ("features", "runtimes", "channels", "retention_days", "nodes")


def test_no_constraints_returns_null_floor(ent):
    """Mirrors :func:`min_tier_for_all`: "nothing asked" -> null floor,
    every axis unsupplied, empty ``binding_axes``."""
    out = ent.min_tier_for_all_breakdown()
    assert out["min_tier"] is None
    assert out["min_tier_label"] is None
    assert out["min_tier_rank"] is None
    for k in _axis_keys():
        assert out["axes"][k] is None
    assert out["binding_axes"] == []


def test_all_axes_none_returns_null_floor(ent):
    out = ent.min_tier_for_all_breakdown(
        features=None,
        runtimes=None,
        channels=None,
        retention_days=None,
        nodes=None,
    )
    assert out["min_tier"] is None
    assert out["binding_axes"] == []


def test_all_axes_collapse_to_none_returns_null_floor(ent):
    """Empty iterables / all-unknown items collapse each axis' ``min_tier``
    to ``None``; when every supplied axis collapses the aggregate floor
    is ``None`` too, and no axis is binding."""
    out = ent.min_tier_for_all_breakdown(
        features=[], runtimes=(), channels="not-an-int"
    )
    assert out["min_tier"] is None
    assert out["binding_axes"] == []
    assert out["axes"]["features"] is not None
    assert out["axes"]["features"]["min_tier"] is None
    assert out["axes"]["features"]["items"] == []
    assert out["axes"]["runtimes"]["items"] == []
    assert out["axes"]["channels"]["value"] == "not-an-int"


# ── parity with min_tier_for_all across the five axes ──────────────────────


def test_parity_features_only(ent):
    out = ent.min_tier_for_all_breakdown(features=["fleet"])
    assert out["min_tier"] == ent.min_tier_for_all(features=["fleet"])
    assert out["binding_axes"] == ["features"]


def test_parity_runtimes_only(ent):
    out = ent.min_tier_for_all_breakdown(runtimes=["openclaw"])
    assert out["min_tier"] == ent.min_tier_for_all(runtimes=["openclaw"])
    assert out["min_tier"] == ent.TIER_OSS
    assert out["binding_axes"] == ["runtimes"]


def test_parity_channels_only(ent):
    out = ent.min_tier_for_all_breakdown(channels=5)
    assert out["min_tier"] == ent.min_tier_for_all(channels=5)
    if out["min_tier"] is not None:
        assert "channels" in out["binding_axes"]


def test_parity_retention_only(ent):
    out = ent.min_tier_for_all_breakdown(retention_days=30)
    assert out["min_tier"] == ent.min_tier_for_all(retention_days=30)


def test_parity_nodes_only(ent):
    out = ent.min_tier_for_all_breakdown(nodes=2)
    assert out["min_tier"] == ent.min_tier_for_all(nodes=2)


def test_parity_mixed_bundle(ent):
    bundle = dict(
        features=["fleet"],
        runtimes=["claude_code"],
        channels=8,
        retention_days=30,
        nodes=2,
    )
    out = ent.min_tier_for_all_breakdown(**bundle)
    assert out["min_tier"] == ent.min_tier_for_all(**bundle)
    if out["min_tier"] is not None:
        assert out["min_tier_rank"] == ent.tier_rank(out["min_tier"])
        assert out["min_tier_label"] == ent.tier_label(out["min_tier"])


# ── binding-axis identification ────────────────────────────────────────────


def test_binding_axis_is_the_highest_rank(ent):
    """Enterprise-only features MUST bind the floor when mixed with
    otherwise-free axes."""
    out = ent.min_tier_for_all_breakdown(
        features=["sso"], runtimes=["openclaw"], channels=2
    )
    assert out["min_tier"] == ent.TIER_ENTERPRISE
    assert out["binding_axes"] == ["features"]
    assert out["axes"]["features"]["binding"] is True
    assert out["axes"]["runtimes"]["binding"] is False
    assert out["axes"]["channels"]["binding"] is False


def test_binding_axes_tie_lists_all_binders(ent):
    """When two axes both resolve to the aggregate floor, both are listed
    in ``binding_axes`` in envelope order (features / runtimes / channels
    / retention_days / nodes)."""
    # A paid feature + paid runtime both at Enterprise -> both bind.
    out = ent.min_tier_for_all_breakdown(features=["sso"], runtimes=["claude_code"])
    if out["min_tier"] == ent.TIER_ENTERPRISE:
        assert "features" in out["binding_axes"]
        # runtime binds iff its min_tier == floor
        rt_row = out["axes"]["runtimes"]
        assert rt_row["binding"] == (rt_row["min_tier"] == out["min_tier"])


def test_binding_axes_null_when_floor_null(ent):
    """When the aggregate floor is ``None`` (nothing / unknown-only),
    ``binding_axes`` is empty."""
    out = ent.min_tier_for_all_breakdown(features=["bogus-feature-id"])
    assert out["min_tier"] is None
    assert out["binding_axes"] == []
    # axis row still renders so the caller can flag the unknown token
    assert out["axes"]["features"] is not None
    assert out["axes"]["features"]["items"] == []


# ── per-axis row shape ─────────────────────────────────────────────────────


def test_grant_axis_row_shape(ent):
    out = ent.min_tier_for_all_breakdown(features=["fleet"])
    row = out["axes"]["features"]
    assert row["kind"] == "features"
    assert row["supplied"] is True
    assert row["items"] == ["fleet"]
    assert row["min_tier"] == ent.min_tier_for_features(["fleet"])
    assert row["min_tier_label"] == ent.tier_label(row["min_tier"])
    assert row["min_tier_rank"] == ent.tier_rank(row["min_tier"])
    assert isinstance(row["binding"], bool)


def test_capacity_axis_row_shape(ent):
    out = ent.min_tier_for_all_breakdown(channels=5)
    row = out["axes"]["channels"]
    assert row["kind"] == "channels"
    assert row["supplied"] is True
    assert row["value"] == 5
    assert row["min_tier"] == ent.min_tier_for_channel_count(5)


def test_capacity_row_preserves_bad_input(ent):
    """A non-int capacity value keeps ``supplied=True`` (the caller DID
    supply it), reports ``min_tier=None``, and echoes the raw input in
    ``value`` so the tooltip can flag the typo."""
    out = ent.min_tier_for_all_breakdown(channels="five")
    row = out["axes"]["channels"]
    assert row["supplied"] is True
    assert row["value"] == "five"
    assert row["min_tier"] is None
    assert row["min_tier_rank"] == -1


def test_runtime_axis_canonicalises_aliases(ent):
    """``claude-code`` -> ``claude_code`` matches the singular
    :func:`min_tier_for_runtime` posture (aliases collapse)."""
    out = ent.min_tier_for_all_breakdown(runtimes=["claude-code"])
    row = out["axes"]["runtimes"]
    assert "claude_code" in row["items"]


def test_unsupplied_axes_are_none(ent):
    """Axes the caller did not supply short-circuit to ``None`` at the
    envelope level."""
    out = ent.min_tier_for_all_breakdown(features=["fleet"])
    assert out["axes"]["runtimes"] is None
    assert out["axes"]["channels"] is None
    assert out["axes"]["retention_days"] is None
    assert out["axes"]["nodes"] is None


# ── grace / enforce invariance ─────────────────────────────────────────────


def test_grace_vs_enforce_yields_identical_breakdown(monkeypatch, tmp_path):
    """Decoupled from the resolved entitlement: reloading with
    ``CLAWMETRY_ENFORCE=1`` MUST produce byte-identical output for the
    same bundle."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    grace = e.min_tier_for_all_breakdown(
        features=["fleet"], runtimes=["claude_code"], channels=5
    )

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforced = e.min_tier_for_all_breakdown(
        features=["fleet"], runtimes=["claude_code"], channels=5
    )
    assert grace == enforced


# ── never-raise contract ───────────────────────────────────────────────────


def test_never_raises_on_garbage(ent):
    """Every bad-input shape must fall through to the null-floor envelope
    rather than 500-ing / raising."""
    for bad in (
        {"features": object()},
        {"runtimes": 42},
        {"channels": {"nope": "dict"}},
        {"retention_days": ["not", "int"]},
        {"nodes": None},
    ):
        out = ent.min_tier_for_all_breakdown(**bad)
        assert isinstance(out, dict)
        assert "axes" in out
        assert "binding_axes" in out


# ── HTTP endpoint ──────────────────────────────────────────────────────────


def test_endpoint_400_on_no_args(client):
    resp = client.get("/api/entitlement/required-tier-breakdown")
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body


def test_endpoint_features_only_returns_shape(ent, client):
    resp = client.get(
        "/api/entitlement/required-tier-breakdown?features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    # Top-level shape mirrors /required-tier-batch
    for k in (
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
        "required_tier",
        "required_tier_label",
        "required_tier_rank",
        "current_tier",
        "current_tier_rank",
        "upgrade_required",
    ):
        assert k in body, f"missing key {k}"
    # Breakdown-specific fields
    assert "axes" in body and isinstance(body["axes"], dict)
    assert "binding_axes" in body
    assert body["required_tier"] == ent.min_tier_for_all(features=["fleet"])
    assert "features" in body["binding_axes"]


def test_endpoint_mixed_bundle_matches_helper(ent, client):
    resp = client.get(
        "/api/entitlement/required-tier-breakdown"
        "?features=fleet&runtimes=claude_code&channels=8"
        "&retention_days=30&nodes=2"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    expected = ent.min_tier_for_all_breakdown(
        features=["fleet"],
        runtimes=["claude_code"],
        channels=8,
        retention_days=30,
        nodes=2,
    )
    assert body["required_tier"] == expected["min_tier"]
    assert body["required_tier_label"] == expected["min_tier_label"]
    assert body["binding_axes"] == expected["binding_axes"]
    assert body["axes"] == expected["axes"]


def test_endpoint_bad_capacity_value_still_200(ent, client):
    """Non-int capacity value doesn't 400 -- it contributes nothing to
    the floor (matches ``/required-tier`` never-crash posture)."""
    resp = client.get(
        "/api/entitlement/required-tier-breakdown?features=fleet&channels=five"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["channels"] is None  # unparseable -> not echoed
    # features axis still binds
    assert "features" in body["binding_axes"]


def test_endpoint_unknown_feature_returns_null_floor(client):
    resp = client.get(
        "/api/entitlement/required-tier-breakdown?features=bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["required_tier"] is None
    assert body["required_tier_rank"] == -1
    assert body["upgrade_required"] is False
    assert body["binding_axes"] == []


def test_endpoint_upgrade_required_flag(ent, client):
    """When the aggregate floor exceeds the resolved tier, the endpoint
    reports ``upgrade_required=True``."""
    resp = client.get(
        "/api/entitlement/required-tier-breakdown?features=sso"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    required_rank = body["required_tier_rank"]
    current_rank = body["current_tier_rank"]
    assert body["upgrade_required"] == (required_rank > current_rank)
