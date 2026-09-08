"""Tests for the ``has_retention_window_at`` what-if boolean-gate scalar and
its paired ``/api/entitlement/has-retention-window-at`` endpoint -- the
retention-capacity twin of the sibling ``_at`` scalars
:func:`clawmetry.entitlements.has_feature_at` /
:func:`~clawmetry.entitlements.has_runtime_at` (grant axes) and
:func:`~clawmetry.entitlements.has_channel_count_at` /
:func:`~clawmetry.entitlements.has_node_count_at` (capacity axes).

Where the live :func:`~clawmetry.entitlements.has_retention_window` scalar
answers "does the CURRENT resolved entitlement admit this history window?",
``has_retention_window_at`` is the *what-if* answer: "would tier
``perspective_tier`` admit this window?" Backed directly by the static
:data:`~clawmetry.entitlements._TIER_RETENTION_DAYS` table so the answer is
grace-independent by construction -- the whole point of a what-if scalar is
that even in grace it renders the would-be-locked state so a pricing matrix
tile can show "you would be locked here" alongside the live grant.

This file pins:

1. Scalar-helper behaviour across every ``(perspective_tier, days)`` cell of
   interest (free-floor, mid-tier, unlimited-tier, unknown perspective,
   ``None``-unlimited request, zero / negative / non-int / string-int
   inputs).
2. Endpoint envelope shape parity (fixed 14-key set) across every input
   branch so a frontend can bind fields off the URL without a branch on the
   underlying resolver state.
3. The grace-independence invariant: unlike the live sibling, this scalar
   returns ``False`` even in grace on a perspective whose static cap
   doesn't fit ``days`` -- so pricing-matrix UI renders correctly today
   without waiting for enforcement.
4. Never-4xx on missing / blank / unknown perspective / unparseable days.
5. Never-5xx via monkeypatched blowup on both
   :func:`~clawmetry.entitlements.min_tier_for_retention_window` and
   :func:`~clawmetry.entitlements.get_entitlement`.
6. Scalar-vs-endpoint parity: envelope ``has_retention_window_at`` matches
   the module-level scalar byte-for-byte on the same input.
7. Cross-consistency with the sibling
   ``/api/entitlement/required-tier?retention_days=<N>`` -- same
   ``required_tier`` / ``current_tier`` for the same parsed ``days`` so a
   UI wiring both URLs into the same paywall tile can't see inconsistent
   tier state.
8. The unlimited-request branch: ``?days=unlimited`` (case-insensitive) is
   a first-class input separate from missing/blank -- ``days=null``,
   ``unlimited=true``, and ``has_retention_window_at`` reflects the static
   per-tier cap (Enterprise -> True; every other perspective -> False).
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
    Enforcement off by default -- matches the project rollout posture and
    reuses the same fixture shape ``tests/test_entitlement_has_retention_window.py``
    uses so the assertions here reproduce the same install state the sibling
    scalar tests are pinned against. What-if answers here are
    grace-independent by construction, but the LIVE resolver context fields
    (``current_tier``, ``grace``, ``enforced``) still come off the fixture."""
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
    to False. Only affects the ``grace`` / ``enforced`` envelope fields and
    the LIVE ``has_retention_window`` sibling; the what-if scalar answers
    remain identical."""
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


# ── Envelope shape ──────────────────────────────────────────────────────────

_ENVELOPE_KEYS = {
    "tier",
    "days",
    "days_raw",
    "unlimited",
    "has_retention_window_at",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# ── has_retention_window_at scalar: perspective validity ────────────────────


def test_scalar_unknown_perspective_is_false(ent):
    """Unknown perspective (typo, non-tier string) -> False. Matches the
    strict fail-closed posture of :func:`has_feature_at` /
    :func:`has_channel_count_at` / :func:`has_node_count_at` on an unknown
    perspective."""
    for p in ("mars", "Pro+", "starter+", "premium", "gold", "cloud"):
        assert ent.has_retention_window_at(p, 30) is False, p


def test_scalar_empty_perspective_is_false(ent):
    """Empty / blank / whitespace perspective -> False."""
    for p in ("", "  ", "\n", "\t"):
        assert ent.has_retention_window_at(p, 30) is False, repr(p)


def test_scalar_none_perspective_is_false(ent):
    """``None`` perspective -> False (no crash)."""
    assert ent.has_retention_window_at(None, 30) is False


def test_scalar_non_string_perspective_is_false(ent):
    """Non-string perspective (int, list, dict) -> False."""
    for p in (7, ["oss"], {"tier": "pro"}, 3.14, (1, 2)):
        assert ent.has_retention_window_at(p, 30) is False, p


def test_scalar_perspective_is_case_insensitive(ent):
    """Perspective is stripped / lowercased before validation (matches
    :func:`has_feature_at` / :func:`has_channel_count_at`)."""
    assert ent.has_retention_window_at("PRO", 90) is True
    assert ent.has_retention_window_at("  Cloud_Starter  ", 30) is True
    assert ent.has_retention_window_at("Enterprise", 365) is True


# ── has_retention_window_at scalar: days axis semantics ─────────────────────


def test_scalar_zero_days_is_true_on_every_tier(ent):
    """Zero days is trivially satisfied on every valid perspective -- the
    free floor covers it (matches the sibling ``_at`` scalars and
    :meth:`Entitlement.allows_retention_window`'s grace-on-zero contract)."""
    for tier in ("oss", "cloud_free", "trial", "cloud_starter", "cloud_pro",
                 "pro", "enterprise"):
        assert ent.has_retention_window_at(tier, 0) is True, tier


def test_scalar_negative_days_is_true_on_every_tier(ent):
    """Negative days is trivially satisfied on every valid perspective."""
    for tier in ("oss", "cloud_starter", "cloud_pro", "enterprise"):
        for n in (-1, -100, -999):
            assert ent.has_retention_window_at(tier, n) is True, (tier, n)


def test_scalar_oss_free_floor_at_seven(ent):
    """OSS caps at 7 days. Windows within the cap grant; above the cap deny
    -- even in grace, because the what-if scalar is grace-independent."""
    for n in (1, 7):
        assert ent.has_retention_window_at("oss", n) is True, n
    for n in (8, 30, 90, 365, 10_000):
        assert ent.has_retention_window_at("oss", n) is False, n


def test_scalar_cloud_free_matches_oss(ent):
    """Cloud Free shares the OSS-free floor (both cap at 7 days)."""
    for n in (1, 7):
        assert ent.has_retention_window_at("cloud_free", n) is True, n
    for n in (8, 30, 90):
        assert ent.has_retention_window_at("cloud_free", n) is False, n


def test_scalar_cloud_starter_caps_at_thirty(ent):
    """Cloud Starter caps at 30 days."""
    for n in (1, 7, 30):
        assert ent.has_retention_window_at("cloud_starter", n) is True, n
    for n in (31, 90, 365):
        assert ent.has_retention_window_at("cloud_starter", n) is False, n


def test_scalar_trial_caps_at_thirty(ent):
    """Trial promotional grant caps at 30 days (same as Cloud Starter)."""
    for n in (1, 7, 30):
        assert ent.has_retention_window_at("trial", n) is True, n
    for n in (31, 90):
        assert ent.has_retention_window_at("trial", n) is False, n


def test_scalar_cloud_pro_caps_at_ninety(ent):
    """Cloud Pro caps at 90 days."""
    for n in (1, 7, 30, 90):
        assert ent.has_retention_window_at("cloud_pro", n) is True, n
    for n in (91, 180, 365):
        assert ent.has_retention_window_at("cloud_pro", n) is False, n


def test_scalar_pro_caps_at_ninety(ent):
    """Self-hosted Pro caps at 90 days (matches Cloud Pro)."""
    for n in (1, 7, 30, 90):
        assert ent.has_retention_window_at("pro", n) is True, n
    for n in (91, 365):
        assert ent.has_retention_window_at("pro", n) is False, n


def test_scalar_enterprise_admits_every_finite_window(ent):
    """Enterprise cap is ``None`` (unlimited) -- every finite positive
    window is admitted."""
    for n in (1, 7, 30, 90, 365, 1_000, 10_000, 100_000):
        assert ent.has_retention_window_at("enterprise", n) is True, n


def test_scalar_none_days_only_on_enterprise(ent):
    """``days=None`` (unlimited request) grants only on Enterprise (the sole
    tier whose cap is ``None``). Mirrors
    :func:`min_tier_for_retention_window(None)` -> Enterprise and
    :meth:`Entitlement.allows_retention_window(None)`'s post-enforce
    contract."""
    assert ent.has_retention_window_at("enterprise", None) is True
    for tier in ("oss", "cloud_free", "trial", "cloud_starter", "cloud_pro",
                 "pro"):
        assert ent.has_retention_window_at(tier, None) is False, tier


def test_scalar_non_int_days_is_false(ent):
    """Non-int non-None days input collapses to False on every perspective
    -- fail-closed matches :func:`has_retention_window` /
    :func:`has_channel_count_at` on unknown/junk input. Python floats are
    NOT rejected because ``int(3.14)`` succeeds (truncates); the sibling
    scalars have the same posture -- only string-floats like ``"7.5"``
    fail ``int()`` and collapse to False."""
    for arg in ("seven", "7.5", "bogus", "", "  ", [], {}, (1,)):
        assert ent.has_retention_window_at("cloud_pro", arg) is False, arg


def test_scalar_string_int_is_accepted(ent):
    """String-int (``"30"``) is accepted -- ``int("30")`` succeeds. Lets a
    query-string caller (which always sees strings) hit the scalar without
    manual pre-parsing."""
    assert ent.has_retention_window_at("cloud_starter", "30") is True
    assert ent.has_retention_window_at("cloud_starter", "31") is False
    assert ent.has_retention_window_at("cloud_pro", "90") is True


def test_scalar_bool_is_truthy_because_int_subclass(ent):
    """Python bools ARE ints (``True == 1``, ``False == 0``): ``True`` -> 1
    admitted on every finite tier, ``False`` -> 0 trivially satisfied.
    Documented here to catch a future refactor that adds a bool-rejection
    branch (matches :func:`has_retention_window`'s bool posture)."""
    assert ent.has_retention_window_at("oss", True) is True
    assert ent.has_retention_window_at("oss", False) is True


# ── has_retention_window_at scalar: grace-independence ──────────────────────


def test_scalar_grace_independent_denies_below_cap(ent):
    """Grace-independence invariant: even while ``ent.grace`` is True, the
    what-if scalar returns False on a perspective whose static cap doesn't
    fit ``days``. This is what makes a pricing matrix UI render correctly
    TODAY without waiting for enforcement -- unlike the live sibling
    :func:`has_retention_window` which returns True in grace via
    :meth:`Entitlement.allows_retention_window`'s grace-passthrough."""
    assert ent.get_entitlement().grace is True  # fixture pin
    assert ent.has_retention_window(30) is True  # LIVE grants in grace
    assert ent.has_retention_window_at("oss", 30) is False  # WHAT-IF denies


def test_scalar_grace_independent_unlimited_denies_below_enterprise(ent):
    """The grace-independence invariant extends to the unlimited-request
    branch: only Enterprise grants ``None`` even in grace."""
    assert ent.get_entitlement().grace is True
    assert ent.has_retention_window(None) is True  # LIVE grants in grace
    for tier in ("oss", "cloud_starter", "cloud_pro", "pro"):
        assert ent.has_retention_window_at(tier, None) is False, tier
    assert ent.has_retention_window_at("enterprise", None) is True


def test_scalar_grace_and_enforce_agree(ent, enforced):
    """The what-if scalar answer is identical in grace and enforce for the
    same ``(perspective_tier, days)`` cell -- static-table backed by
    construction. Pinning both rollout modes here guards against a future
    refactor that reintroduces a grace-mode branch to this scalar."""
    cases = [
        ("oss", 7, True), ("oss", 8, False), ("oss", 30, False),
        ("cloud_starter", 30, True), ("cloud_starter", 31, False),
        ("cloud_pro", 90, True), ("cloud_pro", 91, False),
        ("enterprise", 10_000, True), ("enterprise", None, True),
        ("cloud_pro", None, False), ("oss", None, False),
    ]
    for tier, days, expected in cases:
        assert ent.has_retention_window_at(tier, days) is expected, (tier, days)
        assert enforced.has_retention_window_at(tier, days) is expected, (
            tier, days
        )


# ── has_retention_window_at scalar: never-raises ────────────────────────────


def test_scalar_never_raises_on_bogus_inputs(ent):
    """Any input combination -- valid / invalid / mixed -- returns a bool
    without raising."""
    for p in (None, "", "mars", 7, [], "oss", "cloud_starter"):
        for d in (None, 0, -1, 30, "seven", "30", [], {}):
            v = ent.has_retention_window_at(p, d)
            assert isinstance(v, bool), (p, d, v)


# ── /api/entitlement/has-retention-window-at envelope ───────────────────────


def test_endpoint_oss_below_cap_grants(client):
    """OSS admits a 7-day window (within the free floor)."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-at?tier=oss&days=7"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == "oss"
    assert body["days"] == 7
    assert body["days_raw"] == "7"
    assert body["unlimited"] is False
    assert body["has_retention_window_at"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "oss"
    assert body["required_tier_label"] == "OSS"
    assert body["required_tier_rank"] == 0
    assert body["perspective_tier_rank"] == 0
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


def test_endpoint_oss_above_cap_denies_in_grace(client):
    """OSS denies a 30-day window even in grace -- the what-if scalar is
    grace-independent by construction, unlike the live sibling."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-at?tier=oss&days=30"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == "oss"
    assert body["days"] == 30
    assert body["has_retention_window_at"] is False
    assert body["allowed"] is False
    assert body["required_tier"] == "cloud_starter"
    assert body["required_tier_label"] == "Starter"
    assert body["required_tier_rank"] == 1
    assert body["perspective_tier_rank"] == 0
    assert body["grace"] is True


def test_endpoint_starter_at_boundary(client):
    """Cloud Starter grants exactly at the 30-day boundary."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at?tier=cloud_starter&days=30"
    )
    assert body["has_retention_window_at"] is True
    assert body["required_tier"] == "cloud_starter"


def test_endpoint_starter_denies_thirty_one(client):
    """Cloud Starter denies 31 days (just over the cap)."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at?tier=cloud_starter&days=31"
    )
    assert body["has_retention_window_at"] is False
    assert body["required_tier"] == "cloud_pro"


def test_endpoint_pro_at_boundary(client):
    """Cloud Pro grants exactly at the 90-day boundary."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-at?tier=cloud_pro&days=90"
    )
    assert body["has_retention_window_at"] is True
    assert body["required_tier"] == "cloud_pro"
    assert body["required_tier_rank"] == 2


def test_endpoint_enterprise_grants_large_finite(client):
    """Enterprise grants a large finite window (cap is None)."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-at?tier=enterprise&days=10000"
    )
    assert body["has_retention_window_at"] is True
    assert body["required_tier"] == "enterprise"


def test_endpoint_zero_days_grants_on_every_tier(client):
    """Zero days trivially satisfied on every perspective."""
    for tier in ("oss", "cloud_starter", "cloud_pro", "enterprise"):
        body = _get_json(
            client,
            f"/api/entitlement/has-retention-window-at?tier={tier}&days=0"
        )
        assert body["has_retention_window_at"] is True, tier
        assert body["required_tier"] == "oss", tier


def test_endpoint_negative_days_grants_on_every_tier(client):
    """Negative days trivially satisfied on every perspective."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at?tier=cloud_starter&days=-5"
    )
    assert body["has_retention_window_at"] is True
    assert body["required_tier"] == "oss"


def test_endpoint_missing_tier(client):
    """Missing ``?tier=`` -- never 4xx. ``perspective_tier_rank=-1``,
    ``has_retention_window_at=false``."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-at?days=30"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ""
    assert body["perspective_tier_rank"] == -1
    assert body["has_retention_window_at"] is False
    assert body["allowed"] is False
    # The required_tier is still computed off days alone (perspective-independent).
    assert body["required_tier"] == "cloud_starter"


def test_endpoint_blank_tier(client):
    """Blank / whitespace tier -- same shape as missing."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-at?tier=&days=30"
    )
    assert body["tier"] == ""
    assert body["perspective_tier_rank"] == -1
    assert body["has_retention_window_at"] is False


def test_endpoint_unknown_tier(client):
    """Unknown perspective (``?tier=mars``) -- never 4xx."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-at?tier=mars&days=30"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == "mars"
    assert body["perspective_tier_rank"] == -1
    assert body["has_retention_window_at"] is False


def test_endpoint_tier_case_insensitive(client):
    """Perspective is canonicalised via strip-lower before validation."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-at?tier=PRO&days=90"
    )
    assert body["tier"] == "pro"
    assert body["has_retention_window_at"] is True


def test_endpoint_missing_days(client):
    """Missing ``?days=`` -- ``has_retention_window_at=false``,
    ``days=null``, ``required_tier=null``. Never 4xx."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-at?tier=cloud_pro"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == ""
    assert body["unlimited"] is False
    assert body["has_retention_window_at"] is False
    assert body["required_tier"] is None
    assert body["required_tier_rank"] == -1
    assert body["tier"] == "cloud_pro"
    assert body["perspective_tier_rank"] == 2


def test_endpoint_blank_days(client):
    """Explicit blank ``?days=`` -- same shape as missing."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at?tier=cloud_pro&days="
    )
    assert body["days"] is None
    assert body["days_raw"] == ""
    assert body["has_retention_window_at"] is False


def test_endpoint_whitespace_days(client):
    """Whitespace-only days -- strips to empty."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at?tier=cloud_pro&days=%20%20"
    )
    assert body["days"] is None
    assert body["days_raw"] == ""
    assert body["has_retention_window_at"] is False


def test_endpoint_unparseable_days(client):
    """Non-int days (``?days=bogus``) -- never 4xx."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at?tier=cloud_pro&days=bogus"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == "bogus"
    assert body["has_retention_window_at"] is False
    assert body["required_tier"] is None


def test_endpoint_float_string_unparseable(client):
    """``?days=30.5`` fails ``int()`` -- unparseable shape."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at?tier=cloud_pro&days=30.5"
    )
    assert body["days"] is None
    assert body["days_raw"] == "30.5"
    assert body["has_retention_window_at"] is False


def test_endpoint_stripped_days_raw(client):
    """Surrounding whitespace in the raw days param is stripped before echo."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at"
        "?tier=cloud_starter&days=%20%2030%20%20"
    )
    assert body["days"] == 30
    assert body["days_raw"] == "30"
    assert body["has_retention_window_at"] is True


# ── Unlimited-request branch ────────────────────────────────────────────────


def test_endpoint_unlimited_only_enterprise_grants(client):
    """``?days=unlimited`` grants only when perspective is Enterprise --
    grace-independent by construction."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at?tier=enterprise&days=unlimited"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == "unlimited"
    assert body["unlimited"] is True
    assert body["has_retention_window_at"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "enterprise"
    assert body["required_tier_label"] == "Enterprise"
    assert body["required_tier_rank"] == 3
    assert body["perspective_tier_rank"] == 3


def test_endpoint_unlimited_case_insensitive(client):
    """``?days=UNLIMITED`` -- case-insensitive alias."""
    body = _get_json(
        client,
        "/api/entitlement/has-retention-window-at?tier=enterprise&days=UNLIMITED"
    )
    assert body["unlimited"] is True
    assert body["days_raw"] == "UNLIMITED"
    assert body["has_retention_window_at"] is True


def test_endpoint_unlimited_denies_below_enterprise(client):
    """``?days=unlimited`` on any non-Enterprise perspective -- even in
    grace -- returns False. The what-if scalar is grace-independent."""
    for tier in ("oss", "cloud_free", "trial", "cloud_starter", "cloud_pro", "pro"):
        body = _get_json(
            client,
            f"/api/entitlement/has-retention-window-at?tier={tier}&days=unlimited"
        )
        assert body["unlimited"] is True, tier
        assert body["has_retention_window_at"] is False, tier
        assert body["allowed"] is False, tier
        assert body["required_tier"] == "enterprise", tier


def test_endpoint_unlimited_missing_tier(client):
    """``?days=unlimited`` without ``?tier=`` -- perspective is unknown so
    the boolean is False; ``required_tier`` still resolves to enterprise."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window-at?days=unlimited"
    )
    assert body["unlimited"] is True
    assert body["tier"] == ""
    assert body["perspective_tier_rank"] == -1
    assert body["has_retention_window_at"] is False
    assert body["required_tier"] == "enterprise"


# ── Enforce-mode: what-if answer unchanged ──────────────────────────────────


def test_endpoint_enforce_same_what_if(enforced_client):
    """Under enforcement the what-if answers are identical to the grace
    variant on the same input -- static-table backed. The ``grace`` /
    ``enforced`` envelope fields still reflect the live rollout state."""
    body = _get_json(
        enforced_client,
        "/api/entitlement/has-retention-window-at?tier=cloud_starter&days=30"
    )
    assert body["has_retention_window_at"] is True
    assert body["required_tier"] == "cloud_starter"
    assert body["grace"] is False
    assert body["enforced"] is True

    body_oss = _get_json(
        enforced_client,
        "/api/entitlement/has-retention-window-at?tier=oss&days=30"
    )
    assert body_oss["has_retention_window_at"] is False
    assert body_oss["required_tier"] == "cloud_starter"


# ── Never-5xx (monkeypatched blowup) ────────────────────────────────────────


def test_endpoint_never_5xx_on_min_tier_blowup(monkeypatch, client):
    """A blowup in :func:`min_tier_for_retention_window` still returns 200
    with the fallback envelope."""
    def _boom(*a, **kw):
        raise RuntimeError("min_tier_for_retention_window blew up")

    from clawmetry import entitlements as _ent

    monkeypatch.setattr(_ent, "min_tier_for_retention_window", _boom)
    resp = client.get(
        "/api/entitlement/has-retention-window-at?tier=cloud_pro&days=30"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == "cloud_pro"
    assert body["days"] is None
    assert body["days_raw"] == "30"
    assert body["unlimited"] is False
    assert body["has_retention_window_at"] is False
    assert body["allowed"] is False


def test_endpoint_never_5xx_on_entitlement_blowup(monkeypatch, client):
    """A blowup in :func:`get_entitlement` still 200s with the fallback."""
    def _boom(*a, **kw):
        raise RuntimeError("get_entitlement blew up")

    from clawmetry import entitlements as _ent

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/has-retention-window-at?tier=cloud_pro&days=30"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == "cloud_pro"
    assert body["has_retention_window_at"] is False


def test_endpoint_never_5xx_on_unlimited_branch_blowup(monkeypatch, client):
    """A blowup on the unlimited-request branch also 200s with the
    fallback -- ``unlimited=true`` and ``days_raw='unlimited'`` are
    preserved so the caller can still tell which branch tripped."""
    def _boom(*a, **kw):
        raise RuntimeError("get_entitlement blew up")

    from clawmetry import entitlements as _ent

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get(
        "/api/entitlement/has-retention-window-at?tier=enterprise&days=unlimited"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == "enterprise"
    assert body["days_raw"] == "unlimited"
    assert body["unlimited"] is True
    assert body["has_retention_window_at"] is False


def test_fallback_shape_direct():
    """Direct call of the fallback helper: fixed 14-key envelope, all
    fields fail-closed / defaulted."""
    from routes.entitlement import _has_retention_window_at_fallback

    body = _has_retention_window_at_fallback("cloud_pro", "42", False)
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == "cloud_pro"
    assert body["days"] is None
    assert body["days_raw"] == "42"
    assert body["unlimited"] is False
    assert body["has_retention_window_at"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["required_tier_label"] is None
    assert body["required_tier_rank"] == -1
    assert body["perspective_tier_rank"] == -1
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["grace"] is True
    assert body["enforced"] is False


def test_fallback_shape_preserves_unlimited():
    """Fallback preserves ``unlimited=true`` when the tripped branch was
    the unlimited-request one."""
    from routes.entitlement import _has_retention_window_at_fallback

    body = _has_retention_window_at_fallback("enterprise", "unlimited", True)
    assert body["tier"] == "enterprise"
    assert body["unlimited"] is True
    assert body["days_raw"] == "unlimited"
    assert body["days"] is None
    assert body["has_retention_window_at"] is False


# ── Cross-consistency with sibling endpoints ────────────────────────────────


@pytest.mark.parametrize("n", [1, 7, 8, 30, 31, 90, 91, 365])
def test_endpoint_required_tier_matches_has_retention_window(client, n):
    """Same ``days`` -> same ``required_tier`` on the live and what-if
    endpoints. A UI wiring both URLs into the same paywall tile can't see
    inconsistent tier state on the perspective-independent required-tier
    axis. (``current_tier`` also matches: both share the live resolver
    context.)"""
    at_body = _get_json(
        client,
        f"/api/entitlement/has-retention-window-at?tier=cloud_pro&days={n}"
    )
    live_body = _get_json(
        client, f"/api/entitlement/has-retention-window?days={n}"
    )
    assert at_body["required_tier"] == live_body["required_tier"], n
    assert at_body["required_tier_label"] == live_body["required_tier_label"], n
    assert at_body["required_tier_rank"] == live_body["required_tier_rank"], n
    assert at_body["current_tier"] == live_body["current_tier"], n
    assert at_body["current_tier_rank"] == live_body["current_tier_rank"], n


@pytest.mark.parametrize("n", [7, 30, 90, 365])
def test_endpoint_required_tier_matches_required_tier_endpoint(client, n):
    """``required_tier`` byte-parity with
    ``/api/entitlement/required-tier?retention_days=<N>``."""
    at_body = _get_json(
        client,
        f"/api/entitlement/has-retention-window-at?tier=cloud_starter&days={n}"
    )
    req_body = _get_json(
        client, f"/api/entitlement/required-tier?retention_days={n}"
    )
    assert at_body["required_tier"] == req_body["required_tier"], n
    assert at_body["required_tier_label"] == req_body["required_tier_label"], n
    assert at_body["required_tier_rank"] == req_body["required_tier_rank"], n


# ── Scalar-vs-endpoint parity ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "tier,days",
    [
        ("oss", 1), ("oss", 7), ("oss", 30), ("oss", 0), ("oss", -5),
        ("cloud_starter", 7), ("cloud_starter", 30), ("cloud_starter", 31),
        ("cloud_pro", 90), ("cloud_pro", 91), ("cloud_pro", 365),
        ("enterprise", 1), ("enterprise", 10_000),
        ("trial", 30), ("trial", 31),
        ("pro", 90), ("pro", 91),
    ],
)
def test_endpoint_matches_scalar_int(client, ent, tier, days):
    """Envelope ``has_retention_window_at`` matches the module-level scalar
    byte-for-byte -- no drift possible between the two."""
    body = _get_json(
        client,
        f"/api/entitlement/has-retention-window-at?tier={tier}&days={days}"
    )
    scalar = ent.has_retention_window_at(tier, days)
    assert body["has_retention_window_at"] is scalar, (tier, days)
    assert body["allowed"] is scalar, (tier, days)


@pytest.mark.parametrize(
    "tier",
    ["oss", "cloud_free", "trial", "cloud_starter", "cloud_pro", "pro",
     "enterprise"],
)
def test_endpoint_matches_scalar_unlimited(client, ent, tier):
    """``?days=unlimited`` -> scalar ``has_retention_window_at(tier, None)``
    on every perspective."""
    body = _get_json(
        client,
        f"/api/entitlement/has-retention-window-at?tier={tier}&days=unlimited"
    )
    scalar = ent.has_retention_window_at(tier, None)
    assert body["has_retention_window_at"] is scalar, tier
    assert body["allowed"] is scalar, tier


@pytest.mark.parametrize("raw", ["bogus", "  ", "", "30.5"])
def test_endpoint_matches_scalar_bad_input(client, ent, raw):
    """On unparseable days input, both endpoint and scalar report False."""
    import urllib.parse
    url = (
        "/api/entitlement/has-retention-window-at?tier=cloud_pro"
        f"&days={urllib.parse.quote(raw)}"
    )
    body = _get_json(client, url)
    assert body["has_retention_window_at"] is False
    assert ent.has_retention_window_at("cloud_pro", raw) is False


# ── Envelope invariant across every branch ──────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-retention-window-at",
        "/api/entitlement/has-retention-window-at?tier=",
        "/api/entitlement/has-retention-window-at?tier=oss",
        "/api/entitlement/has-retention-window-at?tier=oss&days=",
        "/api/entitlement/has-retention-window-at?tier=oss&days=0",
        "/api/entitlement/has-retention-window-at?tier=oss&days=7",
        "/api/entitlement/has-retention-window-at?tier=oss&days=30",
        "/api/entitlement/has-retention-window-at?tier=cloud_starter&days=30",
        "/api/entitlement/has-retention-window-at?tier=cloud_pro&days=90",
        "/api/entitlement/has-retention-window-at?tier=enterprise&days=10000",
        "/api/entitlement/has-retention-window-at?tier=enterprise&days=unlimited",
        "/api/entitlement/has-retention-window-at?tier=oss&days=unlimited",
        "/api/entitlement/has-retention-window-at?tier=mars&days=30",
        "/api/entitlement/has-retention-window-at?tier=oss&days=bogus",
        "/api/entitlement/has-retention-window-at?tier=oss&days=-1",
        "/api/entitlement/has-retention-window-at?tier=oss&days=30.5",
        "/api/entitlement/has-retention-window-at?tier=PRO&days=90",
        "/api/entitlement/has-retention-window-at?tier=%20%20&days=30",
        "/api/entitlement/has-retention-window-at?days=30",
    ],
)
def test_envelope_shape_invariant(client, url):
    """Fixed 14-key envelope across every input branch -- a frontend can
    bind fields off the URL without a branch on the resolver state."""
    body = _get_json(client, url)
    assert set(body.keys()) == _ENVELOPE_KEYS, url
    assert isinstance(body["has_retention_window_at"], bool), url
    assert isinstance(body["allowed"], bool), url
    assert isinstance(body["unlimited"], bool), url
    assert isinstance(body["grace"], bool), url
    assert isinstance(body["enforced"], bool), url
    assert isinstance(body["current_tier"], str), url
    assert isinstance(body["tier"], str), url
    assert isinstance(body["current_tier_rank"], int), url
    assert isinstance(body["required_tier_rank"], int), url
    assert isinstance(body["perspective_tier_rank"], int), url
    assert body["days"] is None or isinstance(body["days"], int), url
    assert isinstance(body["days_raw"], str), url
    # allowed must always mirror has_retention_window_at.
    assert body["allowed"] is body["has_retention_window_at"], url
