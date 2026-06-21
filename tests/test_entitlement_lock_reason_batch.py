"""Tests for ``lock_reasons_batch`` helper and the
``/api/entitlement/lock-reason-batch`` endpoint.

Plural per-item sibling of ``lock_reason`` / ``/lock-reason``. Where
``min_tier_for_all`` / ``/required-tier-batch`` collapse the answer to the
single most-constraining tier, this surface preserves the per-item detail so
a Settings or paywall matrix UI ("show me each runtime + feature row with
its own lock + required tier") renders off ONE round-trip instead of N
calls. These tests pin that the shape, the grace-mode posture, the
unknown-id fallback, and the never-raise contract all match the singular
endpoint's behaviour, item-for-item.
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


# ── lock_reasons_batch -- grace mode (default) ─────────────────────────────


def test_helper_grace_mode_returns_no_reasons(ent):
    """In grace mode (default) every row must report reason=None,
    locked=False, allowed=True -- the helper must not invent locks
    pre-enforcement."""
    out = ent.lock_reasons_batch(
        features=["fleet", "sso"],
        runtimes=["claude_code"],
        channels=5,
        retention_days=30,
        nodes=3,
    )
    for row in out["features"] + out["runtimes"]:
        assert row["reason"] is None
        assert row["locked"] is False
        assert row["allowed"] is True
    for axis in ("channels", "retention_days", "nodes"):
        assert out[axis] is not None
        assert out[axis]["reason"] is None
        assert out[axis]["locked"] is False
        assert out[axis]["allowed"] is True


def test_helper_no_inputs_returns_empty_shape(ent):
    out = ent.lock_reasons_batch()
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


def test_helper_none_axis_means_unsupplied_not_unlimited(ent):
    """``retention_days=None`` here means "axis not supplied", NOT the
    unlimited sentinel that would mis-route to Enterprise."""
    out = ent.lock_reasons_batch(retention_days=None)
    assert out["retention_days"] is None


# ── helper -- enforce mode + OSS ──────────────────────────────────────────


def test_helper_enforce_oss_locks_paid_features(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    out = ent.lock_reasons_batch(features=["fleet", "otel_export", "sso"])
    rows = {r["key"]: r for r in out["features"]}
    assert rows["fleet"]["locked"] is True
    assert rows["fleet"]["required_tier"] == ent.TIER_CLOUD_STARTER
    assert rows["otel_export"]["locked"] is True
    assert rows["otel_export"]["required_tier"] == ent.TIER_CLOUD_PRO
    assert rows["sso"]["locked"] is True
    assert rows["sso"]["required_tier"] == ent.TIER_ENTERPRISE


def test_helper_enforce_oss_free_features_never_locked(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    out = ent.lock_reasons_batch(
        features=["sessions", "transcripts", "nemo_governance"],
    )
    for row in out["features"]:
        assert row["reason"] is None
        assert row["locked"] is False


def test_helper_enforce_oss_locks_paid_runtimes(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    out = ent.lock_reasons_batch(runtimes=["claude_code", "openclaw"])
    rows = {r["key"]: r for r in out["runtimes"]}
    assert rows["claude_code"]["locked"] is True
    assert "Paid runtime" in rows["claude_code"]["reason"]
    assert rows["claude_code"]["required_tier"] == ent.TIER_CLOUD_STARTER
    assert rows["openclaw"]["locked"] is False
    assert rows["openclaw"]["reason"] is None


def test_helper_enforce_oss_locks_capacity(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    out = ent.lock_reasons_batch(channels=5, retention_days=30, nodes=3)
    assert out["channels"]["locked"] is True
    assert out["channels"]["required_tier"] == (
        ent.min_tier_for_channel_count(5)
    )
    assert out["retention_days"]["locked"] is True
    assert out["retention_days"]["required_tier"] == (
        ent.min_tier_for_retention_window(30)
    )
    assert out["nodes"]["locked"] is True
    assert out["nodes"]["required_tier"] == ent.min_tier_for_node_count(3)


# ── helper -- unknown / malformed inputs ──────────────────────────────────


def test_helper_unknown_ids_get_grace_shape(ent, monkeypatch):
    """A typo must not 500 and must not invent a tier -- the row reports
    reason=None / required_tier=None."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    out = ent.lock_reasons_batch(
        features=["not_a_real_feature"],
        runtimes=["not_a_real_runtime"],
    )
    assert out["features"][0]["reason"] is None
    assert out["features"][0]["required_tier"] is None
    assert out["features"][0]["locked"] is False
    assert out["runtimes"][0]["reason"] is None
    assert out["runtimes"][0]["required_tier"] is None
    assert out["runtimes"][0]["locked"] is False


def test_helper_csv_string_accepted(ent):
    """The helper accepts a comma-separated string in addition to an
    iterable -- mirrors how the HTTP wrapper would forward a raw param."""
    out = ent.lock_reasons_batch(features="fleet, sso , fleet")
    assert [r["key"] for r in out["features"]] == ["fleet", "sso"]


def test_helper_duplicates_collapsed(ent):
    out = ent.lock_reasons_batch(features=["fleet", "FLEET", "fleet"])
    assert [r["key"] for r in out["features"]] == ["fleet"]


def test_helper_never_raises_on_resolver_failure(ent, monkeypatch):
    """Resolver crash must short-circuit to the OSS-free grace shape, not
    raise."""

    def boom(*_, **__):
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    out = ent.lock_reasons_batch(features=["fleet"])
    assert out["features"][0]["reason"] is None
    assert out["features"][0]["locked"] is False


# ── /api/entitlement/lock-reason-batch ────────────────────────────────────


def test_endpoint_no_input_400s(client):
    rv = client.get("/api/entitlement/lock-reason-batch")
    assert rv.status_code == 400
    assert "supply at least one" in rv.get_json()["error"]


def test_endpoint_blank_capacities_treated_as_unsupplied(client):
    """A blank capacity value must be treated as "not supplied" (NOT
    mis-routed to Enterprise via retention-None=unlimited). With ALL inputs
    blank the endpoint must 400, matching ``/required-tier-batch``."""
    rv = client.get(
        "/api/entitlement/lock-reason-batch"
        "?channels=&retention_days=&nodes="
    )
    assert rv.status_code == 400


def test_endpoint_features_only(client, ent):
    d = client.get(
        "/api/entitlement/lock-reason-batch?features=fleet,sso"
    ).get_json()
    keys = [r["key"] for r in d["features"]]
    assert keys == ["fleet", "sso"]
    # grace -- every reason None
    for row in d["features"]:
        assert row["reason"] is None
        assert row["locked"] is False
    assert d["grace"] is True
    assert d["enforced"] is False
    assert d["current_tier"] == ent.TIER_OSS
    assert d["current_tier_rank"] == ent.tier_rank(ent.TIER_OSS)


def test_endpoint_runtimes_only(client):
    d = client.get(
        "/api/entitlement/lock-reason-batch?runtimes=claude_code,openclaw"
    ).get_json()
    keys = [r["key"] for r in d["runtimes"]]
    assert keys == ["claude_code", "openclaw"]


def test_endpoint_all_five_axes_one_call(client, ent, monkeypatch):
    """The whole point: one round-trip yields per-item rows for every axis
    a paywall matrix needs to render."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    d = client.get(
        "/api/entitlement/lock-reason-batch"
        "?features=fleet,sso"
        "&runtimes=claude_code"
        "&channels=5"
        "&retention_days=30"
        "&nodes=3"
    ).get_json()
    feat_rows = {r["key"]: r for r in d["features"]}
    assert feat_rows["fleet"]["locked"] is True
    assert feat_rows["sso"]["required_tier"] == ent.TIER_ENTERPRISE
    rt_rows = {r["key"]: r for r in d["runtimes"]}
    assert rt_rows["claude_code"]["locked"] is True
    assert d["channels"]["locked"] is True
    assert d["retention_days"]["locked"] is True
    assert d["nodes"]["locked"] is True
    assert d["grace"] is False
    assert d["enforced"] is True


def test_endpoint_non_int_capacity_silently_skipped(client):
    """A non-int capacity is the never-crash path: that axis goes None, the
    remaining axes still resolve -- same posture as the singular endpoint."""
    d = client.get(
        "/api/entitlement/lock-reason-batch?features=fleet&channels=abc"
    ).get_json()
    assert d["channels"] is None
    assert len(d["features"]) == 1


def test_endpoint_unknown_ids_dont_500(client, ent, monkeypatch):
    """A typo in features must not error and must report a grace-shape row
    rather than mis-routing to a tier."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    rv = client.get(
        "/api/entitlement/lock-reason-batch"
        "?features=fleet,not_a_real_feature"
    )
    assert rv.status_code == 200
    rows = {r["key"]: r for r in rv.get_json()["features"]}
    assert rows["fleet"]["locked"] is True
    assert rows["not_a_real_feature"]["locked"] is False
    assert rows["not_a_real_feature"]["required_tier"] is None


def test_endpoint_capacity_alone_is_enough_input(client):
    """Supplying only a capacity axis (no features/runtimes) must NOT 400
    -- the "at least one axis" rule covers all five."""
    assert client.get(
        "/api/entitlement/lock-reason-batch?channels=5"
    ).status_code == 200
    assert client.get(
        "/api/entitlement/lock-reason-batch?retention_days=30"
    ).status_code == 200
    assert client.get(
        "/api/entitlement/lock-reason-batch?nodes=3"
    ).status_code == 200


def test_endpoint_resolver_failure_returns_grace_shape(client, monkeypatch):
    """A resolver crash must fall back to the grace shape -- never a 500."""
    import clawmetry.entitlements as _ent

    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(_ent, "lock_reasons_batch", boom)
    rv = client.get("/api/entitlement/lock-reason-batch?features=fleet")
    assert rv.status_code == 200
    d = rv.get_json()
    assert d["features"] == []
    assert d["current_tier"] == "oss"
    assert d["grace"] is True
    assert d["enforced"] is False


def test_endpoint_carries_current_tier_metadata(client, ent):
    """Every response must carry current_tier / current_tier_rank / grace /
    enforced so a single round-trip can render the upgrade-CTA badge
    alongside the per-row locks without a second /api/entitlement call."""
    d = client.get(
        "/api/entitlement/lock-reason-batch?features=fleet"
    ).get_json()
    assert "current_tier" in d
    assert "current_tier_rank" in d
    assert "grace" in d
    assert "enforced" in d
