"""Tests for ``clawmetry.entitlements.tiers_for_feature_at`` /
``tiers_for_runtime_at`` / ``tiers_for_batch_at`` plus their HTTP
endpoints ``GET /api/entitlement/tiers-for-at`` and
``GET /api/entitlement/tiers-for-batch-at``.

Hypothetical-perspective siblings of :func:`tiers_for_feature` /
:func:`tiers_for_runtime` / :func:`tiers_for_batch`. Same relationship
to the base helpers that :func:`min_tier_for_all_at` /
:func:`affordable_tiers_at` have to their current-perspective siblings:
the ``perspective_tier`` argument is validated against ``_TIER_ORDER``
(``trial`` accepted) but does NOT shape rows -- the ladder is
intrinsically perspective-independent because it walks static per-tier
tables.

These tests pin:

* every ``p`` in ``_TIER_ORDER`` yields identical rows to the base
  helper (parity across perspectives)
* perspective validation: empty / blank / ``None`` / unknown / non-str
  -> ``None`` at the helper layer, ``400`` / ``404`` at the HTTP layer
* helpers never raise and stay decoupled from the live entitlement
  (grace vs enforce yields byte-identical rows)
* the endpoints round-trip both axes and carry the perspective +
  resolver envelope; 400 on missing/blank ``tier=``, 404 on unknown
  ``tier=``, 400 on missing/both feature+runtime, 404 on unknown
  feature/runtime, never 5xxs on happy paths
* cross-endpoint parity: rows returned by ``/tiers-for-at`` byte-equal
  ``/tiers-for`` (minus the perspective envelope) for every ``p``, and
  ``/tiers-for-batch-at`` byte-equals ``/tiers-for-batch`` similarly
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


_ROW_KEYS = {
    "item",
    "kind",
    "label",
    "free",
    "min_tier",
    "min_tier_label",
    "min_tier_rank",
    "tiers",
}


# ── shape parity with base helper ─────────────────────────────────────────


def test_feature_at_returns_full_shape(ent):
    body = ent.tiers_for_feature_at(ent.TIER_CLOUD_STARTER, "self_evolve")
    assert body is not None
    assert set(body.keys()) == _ROW_KEYS
    assert body["kind"] == "feature"
    assert body["item"] == "self_evolve"


def test_runtime_at_returns_full_shape(ent):
    body = ent.tiers_for_runtime_at(ent.TIER_CLOUD_STARTER, "claude_code")
    assert body is not None
    assert set(body.keys()) == _ROW_KEYS
    assert body["kind"] == "runtime"
    assert body["item"] == "claude_code"


def test_batch_at_returns_features_and_runtimes(ent):
    body = ent.tiers_for_batch_at(ent.TIER_CLOUD_STARTER)
    assert body is not None
    assert set(body.keys()) == {"features", "runtimes"}
    assert body["features"] and body["runtimes"]


# ── perspective-independence parity ──────────────────────────────────────


def test_feature_at_byte_parity_across_perspectives(ent):
    """`tiers_for_feature_at(p, f) == tiers_for_feature(f)` for every
    ``p`` in ``_TIER_ORDER`` and every ``f`` in ``ALL_FEATURES`` -- pins
    the ``_at`` prefix against silently shaping rows."""
    for fid in ent.ALL_FEATURES:
        base = ent.tiers_for_feature(fid)
        for p in ent._TIER_ORDER:
            assert ent.tiers_for_feature_at(p, fid) == base, (p, fid)


def test_runtime_at_byte_parity_across_perspectives(ent):
    """`tiers_for_runtime_at(p, r) == tiers_for_runtime(r)` for every
    ``p`` in ``_TIER_ORDER`` and every ``r`` in ``ALL_RUNTIMES``."""
    for rt in ent.ALL_RUNTIMES:
        base = ent.tiers_for_runtime(rt)
        for p in ent._TIER_ORDER:
            assert ent.tiers_for_runtime_at(p, rt) == base, (p, rt)


def test_batch_at_byte_parity_across_perspectives(ent):
    """`tiers_for_batch_at(p) == tiers_for_batch()` for every ``p`` in
    ``_TIER_ORDER``."""
    base = ent.tiers_for_batch()
    for p in ent._TIER_ORDER:
        assert ent.tiers_for_batch_at(p) == base, p


# ── perspective validation ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "bad",
    ["", "   ", "bogus_tier", "not_a_tier"],
)
def test_feature_at_bad_perspective_returns_none(ent, bad):
    assert ent.tiers_for_feature_at(bad, "fleet") is None


@pytest.mark.parametrize(
    "bad",
    ["", "   ", "bogus_tier", "not_a_tier"],
)
def test_runtime_at_bad_perspective_returns_none(ent, bad):
    assert ent.tiers_for_runtime_at(bad, "claude_code") is None


@pytest.mark.parametrize(
    "bad",
    ["", "   ", "bogus_tier", "not_a_tier"],
)
def test_batch_at_bad_perspective_returns_none(ent, bad):
    assert ent.tiers_for_batch_at(bad) is None


def test_none_perspective_returns_none(ent):
    assert ent.tiers_for_feature_at(None, "fleet") is None  # type: ignore[arg-type]
    assert ent.tiers_for_runtime_at(None, "claude_code") is None  # type: ignore[arg-type]
    assert ent.tiers_for_batch_at(None) is None  # type: ignore[arg-type]


def test_non_string_perspective_returns_none(ent):
    assert ent.tiers_for_feature_at(42, "fleet") is None  # type: ignore[arg-type]
    assert ent.tiers_for_runtime_at([], "claude_code") is None  # type: ignore[arg-type]
    assert ent.tiers_for_batch_at({}) is None  # type: ignore[arg-type]


def test_trial_perspective_accepted(ent):
    """``trial`` is in ``_TIER_ORDER`` and must be accepted -- matches
    every other ``_at`` sibling."""
    assert ent.tiers_for_feature_at(ent.TIER_TRIAL, "fleet") is not None
    assert ent.tiers_for_runtime_at(ent.TIER_TRIAL, "claude_code") is not None
    assert ent.tiers_for_batch_at(ent.TIER_TRIAL) is not None


def test_perspective_case_insensitive(ent):
    """Perspective is stripped + lowered so a ``?tier=CLOUD_PRO``
    round-trip resolves the same as ``cloud_pro``."""
    upper = ent.TIER_CLOUD_PRO.upper()
    assert ent.tiers_for_feature_at(upper, "fleet") == ent.tiers_for_feature("fleet")
    assert ent.tiers_for_runtime_at(upper, "claude_code") == ent.tiers_for_runtime("claude_code")
    assert ent.tiers_for_batch_at(upper) == ent.tiers_for_batch()


def test_perspective_whitespace_stripped(ent):
    padded = f"  {ent.TIER_CLOUD_PRO}  "
    assert ent.tiers_for_feature_at(padded, "fleet") == ent.tiers_for_feature("fleet")


# ── item validation ──────────────────────────────────────────────────────


def test_feature_at_unknown_feature_returns_none(ent):
    assert ent.tiers_for_feature_at(ent.TIER_CLOUD_PRO, "not_a_real_feature") is None


def test_runtime_at_unknown_runtime_returns_none(ent):
    assert ent.tiers_for_runtime_at(ent.TIER_CLOUD_PRO, "not_a_real_runtime") is None


def test_feature_at_empty_item_returns_none(ent):
    assert ent.tiers_for_feature_at(ent.TIER_CLOUD_PRO, "") is None
    assert ent.tiers_for_feature_at(ent.TIER_CLOUD_PRO, None) is None  # type: ignore[arg-type]


def test_runtime_at_empty_item_returns_none(ent):
    assert ent.tiers_for_runtime_at(ent.TIER_CLOUD_PRO, "") is None
    assert ent.tiers_for_runtime_at(ent.TIER_CLOUD_PRO, None) is None  # type: ignore[arg-type]


def test_runtime_at_alias_resolves(ent):
    """``claude-code`` is an alias for ``claude_code`` -- must
    canonicalise through the delegate."""
    body = ent.tiers_for_runtime_at(ent.TIER_CLOUD_PRO, "claude-code")
    assert body is not None
    assert body["item"] == "claude_code"


# ── grace vs enforce ─────────────────────────────────────────────────────


def test_grace_vs_enforce_byte_identical_feature(monkeypatch, ent):
    grace_row = ent.tiers_for_feature_at(ent.TIER_CLOUD_PRO, "fleet")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_row = ent.tiers_for_feature_at(ent.TIER_CLOUD_PRO, "fleet")
    assert grace_row == enforced_row


def test_grace_vs_enforce_byte_identical_batch(monkeypatch, ent):
    grace = ent.tiers_for_batch_at(ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tiers_for_batch_at(ent.TIER_CLOUD_PRO)
    assert grace == enforced


# ── never raises / no live-entitlement mutation ──────────────────────────


def test_feature_at_never_raises_on_delegate_boom(monkeypatch, ent):
    def boom(*_a, **_k):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tiers_for_feature", boom)
    assert ent.tiers_for_feature_at(ent.TIER_CLOUD_PRO, "fleet") is None


def test_runtime_at_never_raises_on_delegate_boom(monkeypatch, ent):
    def boom(*_a, **_k):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tiers_for_runtime", boom)
    assert ent.tiers_for_runtime_at(ent.TIER_CLOUD_PRO, "claude_code") is None


def test_batch_at_never_raises_on_delegate_boom(monkeypatch, ent):
    def boom(*_a, **_k):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tiers_for_batch", boom)
    body = ent.tiers_for_batch_at(ent.TIER_CLOUD_PRO)
    # graceful fallback: empty features / runtimes, still a dict
    assert body == {"features": [], "runtimes": []}


def test_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tiers_for_feature_at(ent.TIER_CLOUD_PRO, "self_evolve")
    ent.tiers_for_runtime_at(ent.TIER_CLOUD_PRO, "claude_code")
    ent.tiers_for_batch_at(ent.TIER_CLOUD_PRO)
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# ── API happy path: singular ─────────────────────────────────────────────


def test_api_feature_at_returns_ladder(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_STARTER}&feature=fleet"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "feature"
    assert body["item"] == "fleet"
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_CLOUD_STARTER in ids
    assert ent.TIER_ENTERPRISE in ids
    assert ent.TIER_OSS not in ids


def test_api_runtime_at_returns_ladder(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_PRO}&runtime=claude_code"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "runtime"
    assert body["item"] == "claude_code"
    ids = {row["id"] for row in body["tiers"]}
    assert ids == {
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }


def test_api_carries_perspective_envelope(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_PRO}&feature=fleet"
    )
    body = rv.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["perspective_tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["perspective_tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_api_carries_resolver_envelope(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_PRO}&feature=fleet"
    )
    body = rv.get_json()
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert "grace" in body
    assert "enforced" in body
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


def test_api_case_insensitive_tier(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_PRO.upper()}&feature=fleet"
    )
    assert rv.status_code == 200
    assert rv.get_json()["perspective_tier"] == ent.TIER_CLOUD_PRO


def test_api_runtime_alias_resolves(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_PRO}&runtime=claude-code"
    )
    assert rv.status_code == 200
    assert rv.get_json()["item"] == "claude_code"


def test_api_lowercases_feature(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_PRO}&feature=FLEET"
    )
    assert rv.status_code == 200
    assert rv.get_json()["item"] == "fleet"


def test_api_trial_perspective_accepted(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_TRIAL}&feature=fleet"
    )
    assert rv.status_code == 200
    assert rv.get_json()["perspective_tier"] == ent.TIER_TRIAL


# ── API error paths: singular ────────────────────────────────────────────


def test_api_missing_tier_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-at?feature=fleet")
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_api_blank_tier_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-at?tier=&feature=fleet")
    assert rv.status_code == 400


def test_api_unknown_tier_is_404(client):
    rv = client.get(
        "/api/entitlement/tiers-for-at?tier=bogus_tier&feature=fleet"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "bogus_tier"


def test_api_missing_axis_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert rv.status_code == 400


def test_api_both_axes_is_400(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_PRO}&feature=fleet&runtime=claude_code"
    )
    assert rv.status_code == 400


def test_api_unknown_feature_is_404(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_PRO}&feature=nonsense_xyz"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["feature"] == "nonsense_xyz"


def test_api_unknown_runtime_is_404(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-at?tier={ent.TIER_CLOUD_PRO}&runtime=nonsense_xyz"
    )
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["runtime"] == "nonsense_xyz"


# ── API happy path: batch ────────────────────────────────────────────────


def test_api_batch_at_shape(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-batch-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == {
        "features",
        "runtimes",
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    assert body["features"] and body["runtimes"]
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO


def test_api_batch_at_trial_accepted(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-batch-at?tier={ent.TIER_TRIAL}"
    )
    assert rv.status_code == 200
    assert rv.get_json()["perspective_tier"] == ent.TIER_TRIAL


def test_api_batch_at_case_insensitive(client, ent):
    rv = client.get(
        f"/api/entitlement/tiers-for-batch-at?tier={ent.TIER_CLOUD_PRO.upper()}"
    )
    assert rv.status_code == 200
    assert rv.get_json()["perspective_tier"] == ent.TIER_CLOUD_PRO


# ── API error paths: batch ───────────────────────────────────────────────


def test_api_batch_at_missing_tier_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-batch-at")
    assert rv.status_code == 400


def test_api_batch_at_blank_tier_is_400(client):
    rv = client.get("/api/entitlement/tiers-for-batch-at?tier=")
    assert rv.status_code == 400


def test_api_batch_at_unknown_tier_is_404(client):
    rv = client.get(
        "/api/entitlement/tiers-for-batch-at?tier=bogus_tier"
    )
    assert rv.status_code == 404


# ── cross-endpoint parity ────────────────────────────────────────────────


def test_api_singular_rows_byte_equal_tiers_for(client, ent):
    """For every ``p``, ``/tiers-for-at?tier=<p>&feature=<f>`` returns
    the same core row shape as ``/tiers-for?feature=<f>`` (minus the
    perspective + resolver envelope keys)."""
    envelope_keys = {
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }
    for fid in list(ent.ALL_FEATURES)[:8]:
        base = client.get(f"/api/entitlement/tiers-for?feature={fid}").get_json()
        for p in ent._TIER_ORDER:
            rv = client.get(
                f"/api/entitlement/tiers-for-at?tier={p}&feature={fid}"
            )
            assert rv.status_code == 200, (p, fid)
            body = rv.get_json()
            core = {k: v for k, v in body.items() if k not in envelope_keys}
            assert core == base, (p, fid)


def test_api_batch_rows_byte_equal_tiers_for_batch(client, ent):
    """For every ``p``, ``/tiers-for-batch-at?tier=<p>`` returns
    ``features`` / ``runtimes`` byte-equal to ``/tiers-for-batch``."""
    base = client.get("/api/entitlement/tiers-for-batch").get_json()
    for p in ent._TIER_ORDER:
        rv = client.get(
            f"/api/entitlement/tiers-for-batch-at?tier={p}"
        )
        assert rv.status_code == 200, p
        body = rv.get_json()
        assert body["features"] == base["features"], p
        assert body["runtimes"] == base["runtimes"], p
