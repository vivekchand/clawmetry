"""Tests for ``clawmetry.entitlements.min_tier_at`` and the
``GET /api/entitlement/min-tier-at`` endpoint.

Perspective-scoped scalar sibling of the five singular ``min_tier_for_*``
helpers -- the cheapest purchasable tier that admits a single-axis
constraint, scoped by a caller-supplied ``perspective_tier``. Same
relationship to :func:`min_tier_for_feature` / :func:`min_tier_for_runtime`
/ :func:`min_tier_for_channel_count` / :func:`min_tier_for_retention_window`
/ :func:`min_tier_for_node_count` that :func:`min_tier_batch_at` has to
:func:`min_tier_batch` and :func:`min_tier_for_all_at` has to
:func:`min_tier_for_all` -- perspective is validated but does NOT shape
the answer so a walkthrough surface can call ``X_at(perspective, axis)``
uniformly across every ``_at`` scalar / batch / bundle sibling.

These tests pin:

* perspective validation: empty / blank / None / non-string / unknown
  short-circuits to ``None`` at the helper layer; 400 / 404 at the HTTP
  layer
* trial accepted as perspective (matches every other ``_at`` sibling)
* perspective case-insensitive + whitespace-stripped
* axis validation: zero axes / more than one axis short-circuits to
  ``None`` at the helper layer; 400 at the HTTP layer
* per-axis parity with the singular ``min_tier_for_*`` helper for every
  perspective in :data:`_TIER_ORDER` -- the ``_at`` prefix cannot silently
  drift into shaping the answer
* per-axis coverage: every feature id in :data:`ALL_FEATURES`, every
  runtime id in :data:`ALL_RUNTIMES`, and every capacity axis
* runtime canonicalisation (``claude-code`` -> ``claude_code``) via the
  singular helper
* ``retention_days=None`` in the helper means unset (matches the route
  parsing), NOT the unlimited-history sentinel
* grace vs enforce yields byte-identical answers (pinned via a
  ``CLAWMETRY_ENFORCE=1`` reload roundtrip)
* helper never raises on a delegate crash (``monkeypatch`` the delegate
  to raise)
* API happy paths: all five axes, case-insensitive tier, trial
  perspective, envelope shape
* API error paths: 400 on missing / blank ``tier=``, 400 on no axis /
  more than one axis / non-int capacity, 404 on unknown ``tier=``, 404
  on unknown feature / runtime id
* Cross-endpoint parity: ``/min-tier-at?tier=<p>&<axis>=<v>`` on the
  scalar body (drop the perspective + resolver envelope keys) byte-equals
  ``/min-tier?<axis>=<v>`` for every ``p`` in :data:`_TIER_ORDER`
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


# ────────────────────────── perspective validation ──────────────────────────


def test_helper_empty_perspective_returns_none(ent):
    assert ent.min_tier_at("", feature="fleet") is None


def test_helper_blank_perspective_returns_none(ent):
    assert ent.min_tier_at("   ", feature="fleet") is None


def test_helper_none_perspective_returns_none(ent):
    assert ent.min_tier_at(None, feature="fleet") is None  # type: ignore[arg-type]


def test_helper_unknown_perspective_returns_none(ent):
    assert ent.min_tier_at("bogus", feature="fleet") is None


def test_helper_non_string_perspective_returns_none(ent):
    assert ent.min_tier_at(42, feature="fleet") is None  # type: ignore[arg-type]
    assert ent.min_tier_at([], feature="fleet") is None  # type: ignore[arg-type]


def test_helper_perspective_is_case_insensitive(ent):
    for p in ent._TIER_ORDER:
        assert (
            ent.min_tier_at(p.upper(), feature="fleet")
            == ent.min_tier_at(p, feature="fleet")
        )


def test_helper_perspective_is_whitespace_stripped(ent):
    for p in ent._TIER_ORDER:
        assert (
            ent.min_tier_at(f"  {p}  ", feature="fleet")
            == ent.min_tier_at(p, feature="fleet")
        )


def test_helper_trial_is_accepted_as_perspective(ent):
    got = ent.min_tier_at(ent.TIER_TRIAL, feature="fleet")
    assert got == ent.min_tier_for_feature("fleet")


# ─────────────────────────────── axis validation ───────────────────────────────


def test_helper_zero_axes_returns_none(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p) is None


def test_helper_two_axes_returns_none(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, feature="fleet", channels=5) is None
        assert ent.min_tier_at(p, runtime="claude_code", nodes=3) is None
        assert (
            ent.min_tier_at(
                p, retention_days=30, nodes=3
            )
            is None
        )


def test_helper_three_axes_returns_none(ent):
    for p in ent._TIER_ORDER:
        assert (
            ent.min_tier_at(
                p, feature="fleet", runtime="claude_code", channels=5
            )
            is None
        )


def test_helper_all_five_axes_returns_none(ent):
    for p in ent._TIER_ORDER:
        assert (
            ent.min_tier_at(
                p,
                feature="fleet",
                runtime="claude_code",
                channels=5,
                retention_days=30,
                nodes=3,
            )
            is None
        )


def test_helper_blank_feature_string_treated_as_unsupplied(ent):
    # A blank feature="" behaves as if that axis wasn't passed; combined
    # with an actually-supplied axis it degrades to a single-axis call.
    for p in ent._TIER_ORDER:
        assert (
            ent.min_tier_at(p, feature="", channels=5)
            == ent.min_tier_for_channel_count(5)
        )


def test_helper_blank_runtime_string_treated_as_unsupplied(ent):
    for p in ent._TIER_ORDER:
        assert (
            ent.min_tier_at(p, runtime="   ", nodes=3)
            == ent.min_tier_for_node_count(3)
        )


# ─────────────────────────── per-axis parity contract ───────────────────────────


def test_helper_feature_parity_across_perspectives(ent):
    for p in ent._TIER_ORDER:
        for fid in ent.ALL_FEATURES:
            assert (
                ent.min_tier_at(p, feature=fid)
                == ent.min_tier_for_feature(fid)
            )


def test_helper_runtime_parity_across_perspectives(ent):
    for p in ent._TIER_ORDER:
        for rt in ent.ALL_RUNTIMES:
            assert (
                ent.min_tier_at(p, runtime=rt)
                == ent.min_tier_for_runtime(rt)
            )


def test_helper_channels_parity_across_perspectives(ent):
    for p in ent._TIER_ORDER:
        for n in (0, 1, 3, 5, 10, 100):
            assert (
                ent.min_tier_at(p, channels=n)
                == ent.min_tier_for_channel_count(n)
            )


def test_helper_retention_parity_across_perspectives(ent):
    for p in ent._TIER_ORDER:
        for d in (0, 1, 7, 30, 90, 365):
            assert (
                ent.min_tier_at(p, retention_days=d)
                == ent.min_tier_for_retention_window(d)
            )


def test_helper_nodes_parity_across_perspectives(ent):
    for p in ent._TIER_ORDER:
        for n in (0, 1, 3, 5, 10, 100):
            assert (
                ent.min_tier_at(p, nodes=n)
                == ent.min_tier_for_node_count(n)
            )


def test_helper_runtime_alias_not_canonicalised(ent):
    # Matches min_tier_for_runtime's contract: aliases with hyphens are
    # not canonicalised at the helper layer -- they land as unknown ids.
    # The /min-tier route has the same posture (no canonical_runtime
    # call), so scalar and _at siblings stay in step.
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, runtime="claude-code") is None
        assert ent.min_tier_for_runtime("claude-code") is None


def test_helper_unknown_feature_returns_none(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, feature="bogus-feature") is None


def test_helper_unknown_runtime_returns_none(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, runtime="bogus-runtime") is None


def test_helper_retention_none_kwarg_means_unset(ent):
    # retention_days=None with no other axis supplied -> 0 axes -> None.
    # The unlimited-history sentinel must be requested through the
    # singular helper directly (matches the /min-tier route parsing).
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, retention_days=None) is None


def test_helper_channels_none_kwarg_means_unset(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, channels=None) is None


def test_helper_nodes_none_kwarg_means_unset(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, nodes=None) is None


def test_helper_channels_negative_collapses_to_oss(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, channels=-1) == ent.TIER_OSS
        assert ent.min_tier_at(p, channels=0) == ent.TIER_OSS


def test_helper_nodes_negative_collapses_to_oss(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, nodes=-1) == ent.TIER_OSS
        assert ent.min_tier_at(p, nodes=0) == ent.TIER_OSS


def test_helper_retention_negative_collapses_to_oss(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, retention_days=-1) == ent.TIER_OSS
        assert ent.min_tier_at(p, retention_days=0) == ent.TIER_OSS


def test_helper_channels_non_int_returns_none(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, channels="not-an-int") is None  # type: ignore[arg-type]


def test_helper_nodes_non_int_returns_none(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, nodes="not-an-int") is None  # type: ignore[arg-type]


def test_helper_retention_non_int_returns_none(ent):
    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, retention_days="not-an-int") is None  # type: ignore[arg-type]


# ────────────────────────────── grace vs enforce ──────────────────────────────


def test_helper_grace_vs_enforce_yields_byte_identical_answers(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e_grace

    importlib.reload(e_grace)
    e_grace.invalidate()
    grace_answers = {
        p: [
            e_grace.min_tier_at(p, feature="fleet"),
            e_grace.min_tier_at(p, runtime="claude_code"),
            e_grace.min_tier_at(p, channels=5),
            e_grace.min_tier_at(p, retention_days=30),
            e_grace.min_tier_at(p, nodes=3),
        ]
        for p in e_grace._TIER_ORDER
    }
    e_grace.invalidate()

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e_enf

    importlib.reload(e_enf)
    e_enf.invalidate()
    enf_answers = {
        p: [
            e_enf.min_tier_at(p, feature="fleet"),
            e_enf.min_tier_at(p, runtime="claude_code"),
            e_enf.min_tier_at(p, channels=5),
            e_enf.min_tier_at(p, retention_days=30),
            e_enf.min_tier_at(p, nodes=3),
        ]
        for p in e_enf._TIER_ORDER
    }
    e_enf.invalidate()

    assert grace_answers == enf_answers

    # Restore grace mode for downstream tests.
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e_grace)
    e_grace.invalidate()


# ──────────────────────────── never-raise contract ────────────────────────────


def test_helper_never_raises_on_delegate_crash(monkeypatch, ent):
    def _boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "min_tier_for_feature", _boom)
    monkeypatch.setattr(ent, "min_tier_for_runtime", _boom)
    monkeypatch.setattr(ent, "min_tier_for_channel_count", _boom)
    monkeypatch.setattr(ent, "min_tier_for_retention_window", _boom)
    monkeypatch.setattr(ent, "min_tier_for_node_count", _boom)

    for p in ent._TIER_ORDER:
        assert ent.min_tier_at(p, feature="fleet") is None
        assert ent.min_tier_at(p, runtime="claude_code") is None
        assert ent.min_tier_at(p, channels=5) is None
        assert ent.min_tier_at(p, retention_days=30) is None
        assert ent.min_tier_at(p, nodes=3) is None


# ─────────────────────────────── API happy paths ───────────────────────────────


def test_api_feature_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&feature=fleet"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["key"] == "feature"
    assert body["value"] == "fleet"
    assert body["min_tier"] == ent.min_tier_for_feature("fleet")
    assert body["perspective_tier"] == "cloud_pro"
    assert body["perspective_tier_label"] == ent.tier_label("cloud_pro")
    assert body["perspective_tier_rank"] == ent.tier_rank("cloud_pro")
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert "grace" in body
    assert "enforced" in body


def test_api_runtime_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_starter&runtime=claude_code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["key"] == "runtime"
    assert body["value"] == "claude_code"
    assert body["min_tier"] == ent.min_tier_for_runtime("claude_code")


def test_api_runtime_alias_unknown(client, ent):
    # /min-tier-at follows /min-tier: hyphen-alias runtime ids are not
    # canonicalised at the route layer, so they surface as unknown
    # (matches min_tier_for_runtime, whose PAID_RUNTIMES set only holds
    # canonical underscore-form ids).
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&runtime=claude-code"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body.get("error") == "unknown"
    assert body["min_tier"] is None


def test_api_channels_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&channels=5"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["key"] == "channels"
    assert body["value"] == "5"
    assert body["min_tier"] == ent.min_tier_for_channel_count(5)


def test_api_retention_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&retention_days=30"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["key"] == "retention_days"
    assert body["value"] == "30"
    assert body["min_tier"] == ent.min_tier_for_retention_window(30)


def test_api_nodes_happy_path(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&nodes=3"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["key"] == "nodes"
    assert body["value"] == "3"
    assert body["min_tier"] == ent.min_tier_for_node_count(3)


def test_api_case_insensitive_tier(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=CLOUD_PRO&feature=fleet"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"


def test_api_trial_perspective(client, ent):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=trial&feature=fleet"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "trial"
    assert body["min_tier"] == ent.min_tier_for_feature("fleet")


# ─────────────────────────────── API error paths ───────────────────────────────


def test_api_missing_tier(client):
    r = client.get("/api/entitlement/min-tier-at?feature=fleet")
    assert r.status_code == 400
    assert "tier" in (r.get_json() or {}).get("error", "")


def test_api_blank_tier(client):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=%20%20&feature=fleet"
    )
    assert r.status_code == 400


def test_api_unknown_tier(client):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=bogus&feature=fleet"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body.get("which") == "tier"
    assert body.get("tier") == "bogus"


def test_api_no_axis(client):
    r = client.get("/api/entitlement/min-tier-at?tier=cloud_pro")
    assert r.status_code == 400


def test_api_two_axes(client):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&feature=fleet&channels=5"
    )
    assert r.status_code == 400


def test_api_channels_non_int(client):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&channels=abc"
    )
    assert r.status_code == 400
    assert "integer" in (r.get_json() or {}).get("error", "")


def test_api_retention_non_int(client):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&retention_days=abc"
    )
    assert r.status_code == 400


def test_api_nodes_non_int(client):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&nodes=abc"
    )
    assert r.status_code == 400


def test_api_unknown_feature_returns_404(client):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&feature=bogus-feature"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body.get("error") == "unknown"
    assert body["min_tier"] is None
    # Perspective envelope populated even on the unknown-id 404 -- a
    # pricing UI reading current_tier / grace from the same response
    # doesn't need a separate call to render the "not available" copy.
    assert body["perspective_tier"] == "cloud_pro"


def test_api_unknown_runtime_returns_404(client):
    r = client.get(
        "/api/entitlement/min-tier-at?tier=cloud_pro&runtime=bogus-runtime"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body.get("error") == "unknown"
    assert body["min_tier"] is None
    assert body["perspective_tier"] == "cloud_pro"


# ────────────────────────── cross-endpoint parity ──────────────────────────


_PARITY_KEYS = (
    "key",
    "value",
    "free",
    "min_tier",
    "tier_label",
    "tier_rank",
)


def _min_tier_body(client, args: str) -> dict:
    r = client.get(f"/api/entitlement/min-tier?{args}")
    assert r.status_code == 200, r.get_data(as_text=True)
    return {k: r.get_json()[k] for k in _PARITY_KEYS}


def _min_tier_at_body(client, tier: str, args: str) -> dict:
    r = client.get(f"/api/entitlement/min-tier-at?tier={tier}&{args}")
    assert r.status_code == 200, r.get_data(as_text=True)
    return {k: r.get_json()[k] for k in _PARITY_KEYS}


def test_api_scalar_parity_feature_across_perspectives(client, ent):
    expected = _min_tier_body(client, "feature=fleet")
    for p in ent._TIER_ORDER:
        assert _min_tier_at_body(client, p, "feature=fleet") == expected


def test_api_scalar_parity_runtime_across_perspectives(client, ent):
    expected = _min_tier_body(client, "runtime=claude_code")
    for p in ent._TIER_ORDER:
        assert (
            _min_tier_at_body(client, p, "runtime=claude_code") == expected
        )


def test_api_scalar_parity_channels_across_perspectives(client, ent):
    expected = _min_tier_body(client, "channels=5")
    for p in ent._TIER_ORDER:
        assert _min_tier_at_body(client, p, "channels=5") == expected


def test_api_scalar_parity_retention_across_perspectives(client, ent):
    expected = _min_tier_body(client, "retention_days=30")
    for p in ent._TIER_ORDER:
        assert (
            _min_tier_at_body(client, p, "retention_days=30") == expected
        )


def test_api_scalar_parity_nodes_across_perspectives(client, ent):
    expected = _min_tier_body(client, "nodes=3")
    for p in ent._TIER_ORDER:
        assert _min_tier_at_body(client, p, "nodes=3") == expected


def test_api_scalar_parity_every_feature_across_perspectives(client, ent):
    for fid in ent.ALL_FEATURES:
        expected = _min_tier_body(client, f"feature={fid}")
        for p in ent._TIER_ORDER:
            assert _min_tier_at_body(client, p, f"feature={fid}") == expected


def test_api_scalar_parity_every_runtime_across_perspectives(client, ent):
    for rt in ent.ALL_RUNTIMES:
        expected = _min_tier_body(client, f"runtime={rt}")
        for p in ent._TIER_ORDER:
            assert _min_tier_at_body(client, p, f"runtime={rt}") == expected
