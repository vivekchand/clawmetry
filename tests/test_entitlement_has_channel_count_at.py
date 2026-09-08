"""Tests for the ``has_channel_count_at`` hypothetical-perspective boolean-gate
scalar helper and its paired ``/api/entitlement/has-channel-count-at`` endpoint.

Channel-capacity twin of :func:`has_node_count_at` on the fleet capacity axis
and of :func:`has_feature_at` / :func:`has_runtime_at` on the grant axes:
where those answer "would tier ``perspective_tier`` grant this
feature/runtime/node-count?", ``has_channel_count_at`` answers the same
question on the chat-channel capacity axis: "would tier ``perspective_tier``
admit ``count`` concurrent adapters?" -- one boolean per pricing-matrix cell,
decoupled from the live resolver's grace pass-through so a "does OSS admit
5 channels? Starter? Pro? Enterprise?" matrix can bind ``allowed`` directly
off ONE URL per cell.

Backed directly by the static :data:`_TIER_CHANNEL_LIMIT` table (not by
:func:`_hypothetical_entitlement`, which forces ``channel_limit`` to the
free-floor value regardless of the requested tier and would defeat the whole
point of the scalar).

This file pins:

1. Scalar semantics: empty / None / non-string / unknown perspective;
   non-int / None / zero / negative / positive ``count``; free-floor
   (OSS cap = :data:`_FREE_CHANNEL_LIMIT`) vs unlimited (paid tier cap =
   ``None``) branches.
2. Perspective-shaped grace-independence: ``has_channel_count_at("oss", 100)``
   returns ``False`` in BOTH grace and enforce (unlike the live
   :func:`has_channel_count` sibling which returns ``True`` in grace) --
   the whole point of the ``_at`` slot is to render the would-be-locked
   state alongside the live grant.
3. Endpoint envelope shape (fixed 13-key set) across every input branch.
4. Never-4xx / never-5xx guarantees on the endpoint.
5. Cross-consistency with the sibling ``/api/entitlement/has-channel-count``
   endpoint on the ``current_tier`` / ``current_tier_rank`` slots (both
   endpoints share the live resolver context; only the ``allowed`` bit
   differs by design).
6. Cross-consistency with the sibling
   ``/api/entitlement/required-tier?channels=<N>`` endpoint on the
   ``required_tier`` / ``required_tier_label`` / ``required_tier_rank``
   slots -- the perspective-independent min-tier answer is byte-parity.
7. Scalar-vs-endpoint parity across a mixed grid of (perspective, count)
   pairs.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode -- matches the
    sibling ``test_entitlement_has_channel_count.py`` fixture so the
    perspective assertions here reproduce the same install state the
    live boolean gate is pinned against."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture: ``CLAWMETRY_ENFORCE=1`` flips ``ent.grace``
    off. Included to pin the perspective-shaped grace-independence
    invariant -- ``has_channel_count_at`` returns the same answer under
    grace vs enforce for the same (perspective, count) pair."""
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
    "count",
    "count_raw",
    "has_channel_count_at",
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


# ── has_channel_count_at scalar ────────────────────────────────────────────


def test_has_channel_count_at_free_floor_on_every_tier(ent):
    """``count <= 0`` is trivially satisfied by the free floor on every
    real tier (mirrors :func:`has_channel_count`'s free-floor branch)."""
    for tier in ent._TIER_ORDER:
        assert ent.has_channel_count_at(tier, 0) is True, tier
        assert ent.has_channel_count_at(tier, -1) is True, tier
        assert ent.has_channel_count_at(tier, -100) is True, tier


def test_has_channel_count_at_oss_cap_is_free_floor(ent):
    """OSS tier statically caps at :data:`_FREE_CHANNEL_LIMIT`. Any count
    above that free floor collapses to False regardless of grace state."""
    cap = ent._FREE_CHANNEL_LIMIT
    assert ent.has_channel_count_at("oss", cap) is True
    assert ent.has_channel_count_at("oss", cap + 1) is False
    assert ent.has_channel_count_at("oss", cap * 100) is False


def test_has_channel_count_at_cloud_free_cap_is_free_floor(ent):
    """Cloud Free shares the OSS free floor on the channels axis."""
    cap = ent._FREE_CHANNEL_LIMIT
    assert ent.has_channel_count_at("cloud_free", cap) is True
    assert ent.has_channel_count_at("cloud_free", cap + 1) is False


def test_has_channel_count_at_paid_tiers_are_unlimited(ent):
    """Every paid tier has ``_TIER_CHANNEL_LIMIT[tier] is None`` (unlimited).
    Verifies the static per-tier cap table matches the assumption."""
    for tier in ent._TIER_ORDER:
        cap = ent._TIER_CHANNEL_LIMIT.get(tier, ent._FREE_CHANNEL_LIMIT)
        if cap is None:
            # Unlimited tier admits any positive count.
            assert ent.has_channel_count_at(tier, 1) is True, tier
            assert ent.has_channel_count_at(tier, 100) is True, tier
            assert ent.has_channel_count_at(tier, 1_000_000) is True, tier
        else:
            # Finite cap: admits <= cap, denies > cap.
            assert ent.has_channel_count_at(tier, cap) is True, tier
            assert ent.has_channel_count_at(tier, cap + 1) is False, tier


def test_has_channel_count_at_oss_never_admits_above_free_floor(ent):
    """Explicit spot-check of the whole point of the ``_at`` slot: OSS
    never admits ``count > _FREE_CHANNEL_LIMIT`` even in grace, unlike
    the live sibling."""
    floor = ent._FREE_CHANNEL_LIMIT
    for count in (floor + 1, floor + 2, 10, 100, 1_000):
        assert ent.has_channel_count_at("oss", count) is False, count


def test_has_channel_count_at_unknown_perspective_is_false(ent):
    """Perspective not in :data:`_TIER_ORDER` -> fail-closed False."""
    for bad in ["", " ", "mars", "pro_plus", "unknown_tier", "starter"]:
        assert ent.has_channel_count_at(bad, 5) is False, bad


def test_has_channel_count_at_non_string_perspective_is_false(ent):
    for bad in [None, 123, object(), []]:
        assert ent.has_channel_count_at(bad, 5) is False


def test_has_channel_count_at_non_int_count_is_false(ent):
    """Non-int count -> fail-closed False (strict callsite-typo posture
    matching :func:`has_channel_count`)."""
    for bad in [None, "five", object(), [], "3.5"]:
        assert ent.has_channel_count_at("pro", bad) is False, bad


def test_has_channel_count_at_case_insensitive_normalises(ent):
    """Casing / whitespace on perspective normalises via ``strip().lower()``
    -- a callsite passing raw config values doesn't have to
    pre-canonicalise."""
    assert ent.has_channel_count_at("  PRO  ", 1) is True
    assert ent.has_channel_count_at("Pro", 100) is True
    floor = ent._FREE_CHANNEL_LIMIT
    assert ent.has_channel_count_at("  OSS  ", floor + 1) is False


def test_has_channel_count_at_grace_independence(ent, enforced):
    """The whole point of the ``_at`` slot: perspective-shaped answers
    are IDENTICAL under grace vs enforce for the same (perspective,
    count) pair. Diverges from the live :func:`has_channel_count` which
    returns ``True`` in grace for every count via
    :meth:`Entitlement.allows_channel_count`'s grace-passthrough but
    flips to the actual cap in enforce."""
    for tier in ent._TIER_ORDER:
        for count in (1, 2, 5, 100, 10_000):
            assert ent.has_channel_count_at(
                tier, count
            ) is enforced.has_channel_count_at(tier, count), (tier, count)


def test_has_channel_count_at_string_int_parses(ent):
    """``int("5")`` succeeds, so a string-int input goes through the
    positive-int branch (matches :func:`has_channel_count`)."""
    assert ent.has_channel_count_at("pro", "1") is True
    assert ent.has_channel_count_at("oss", "1") is True
    floor = ent._FREE_CHANNEL_LIMIT
    assert ent.has_channel_count_at("oss", str(floor + 1)) is False


def test_has_channel_count_at_never_raises_on_lookup_blowup(monkeypatch, ent):
    """A blowup during the static-table lookup collapses to ``False`` so a
    pricing matrix cell keeps rendering."""

    class _Boom(dict):
        def get(self, *_a, **_kw):
            raise RuntimeError("map blew up")

    monkeypatch.setattr(ent, "_TIER_CHANNEL_LIMIT", _Boom())
    for tier in ent._TIER_ORDER:
        assert ent.has_channel_count_at(tier, 5) is False


def test_has_channel_count_at_free_tier_scalar_matches_live_scalar_grace(ent):
    """Grace-time cross-check: the LIVE :func:`has_channel_count` reports
    True for every finite count in grace (grace-passthrough), whereas
    ``has_channel_count_at("oss", <over-floor>)`` reports False.
    Documents the intentional divergence."""
    over = ent._FREE_CHANNEL_LIMIT + 5
    assert ent.has_channel_count(over) is True  # live: grace-passthrough
    assert ent.has_channel_count_at("oss", over) is False  # what-if: static cap


# ── /api/entitlement/has-channel-count-at endpoint ────────────────────────


def test_endpoint_shape_default(client):
    """Missing all args -> 200 with 13-key envelope and fail-closed False."""
    body = _get_json(client, "/api/entitlement/has-channel-count-at")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ""
    assert body["count"] is None
    assert body["count_raw"] == ""
    assert body["has_channel_count_at"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["required_tier_rank"] == -1
    assert body["perspective_tier_rank"] == -1
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


def test_endpoint_paid_tier_admits_any_count(client):
    """A paid perspective (unlimited cap) admits any positive count in
    grace AND enforce."""
    body = _get_json(
        client, "/api/entitlement/has-channel-count-at?tier=pro&count=100"
    )
    assert body["tier"] == "pro"
    assert body["count"] == 100
    assert body["has_channel_count_at"] is True
    assert body["allowed"] is True
    assert body["perspective_tier_rank"] > 0
    assert body["current_tier"] == "oss"


def test_endpoint_oss_denies_above_free_floor(client, ent):
    """The whole point of the ``_at`` slot: OSS reports
    ``allowed=false`` for count above the free floor EVEN IN GRACE,
    unlike the live ``/has-channel-count`` sibling which returns ``true``
    in grace on the same count."""
    over = ent._FREE_CHANNEL_LIMIT + 5
    body = _get_json(
        client, f"/api/entitlement/has-channel-count-at?tier=oss&count={over}"
    )
    assert body["has_channel_count_at"] is False
    assert body["allowed"] is False
    assert body["perspective_tier_rank"] == 0
    # Live sibling parity on the SHARED live-resolver-context slots.
    live = _get_json(client, f"/api/entitlement/has-channel-count?count={over}")
    assert live["has_channel_count"] is True  # grace-passthrough on live
    assert body["current_tier"] == live["current_tier"]
    assert body["current_tier_rank"] == live["current_tier_rank"]


def test_endpoint_oss_admits_free_floor(client, ent):
    """OSS admits count == :data:`_FREE_CHANNEL_LIMIT` (the free floor)."""
    body = _get_json(
        client,
        f"/api/entitlement/has-channel-count-at?tier=oss&count={ent._FREE_CHANNEL_LIMIT}",
    )
    assert body["has_channel_count_at"] is True
    assert body["allowed"] is True


def test_endpoint_zero_and_negative_admitted_on_every_tier(client):
    """count <= 0 collapses to True on every valid perspective (free floor)."""
    for tier in ("oss", "pro", "cloud_starter", "cloud_pro", "enterprise"):
        for count in (0, -1):
            body = _get_json(
                client,
                f"/api/entitlement/has-channel-count-at?tier={tier}&count={count}",
            )
            assert body["has_channel_count_at"] is True, (tier, count)


def test_endpoint_unknown_tier_never_4xx(client):
    body = _get_json(
        client, "/api/entitlement/has-channel-count-at?tier=mars&count=5"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == "mars"
    assert body["has_channel_count_at"] is False
    assert body["perspective_tier_rank"] == -1


def test_endpoint_unparseable_count_never_4xx(client):
    body = _get_json(
        client, "/api/entitlement/has-channel-count-at?tier=pro&count=five"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == "pro"
    assert body["count"] is None
    assert body["count_raw"] == "five"
    assert body["has_channel_count_at"] is False
    assert body["required_tier"] is None
    # Perspective is valid so its rank IS resolved even when count fails.
    assert body["perspective_tier_rank"] > 0


def test_endpoint_missing_count_never_4xx(client):
    body = _get_json(client, "/api/entitlement/has-channel-count-at?tier=pro")
    assert body["count"] is None
    assert body["count_raw"] == ""
    assert body["has_channel_count_at"] is False
    assert body["perspective_tier_rank"] > 0


def test_endpoint_case_insensitive(client):
    body = _get_json(
        client, "/api/entitlement/has-channel-count-at?tier=%20PRO%20&count=1"
    )
    assert body["tier"] == "pro"
    assert body["has_channel_count_at"] is True


def test_endpoint_required_tier_parity_with_min_tier(client, ent):
    """``required_tier`` byte-equals the sibling
    ``/api/entitlement/required-tier?channels=<N>`` answer for the same
    count -- a UI wiring both URLs into the same channels paywall tile
    cannot see inconsistent tier state."""
    over = ent._FREE_CHANNEL_LIMIT + 5
    body = _get_json(
        client, f"/api/entitlement/has-channel-count-at?tier=oss&count={over}"
    )
    min_body = _get_json(
        client, f"/api/entitlement/required-tier?channels={over}"
    )
    assert body["required_tier"] == min_body["required_tier"]


def test_endpoint_current_tier_parity_with_live(client):
    """The what-if endpoint shares the live resolver-context slots
    (``current_tier`` / ``current_tier_rank``) with the sibling live
    ``/has-channel-count`` endpoint."""
    at_body = _get_json(
        client, "/api/entitlement/has-channel-count-at?tier=oss&count=1"
    )
    live_body = _get_json(client, "/api/entitlement/has-channel-count?count=1")
    for k in ("current_tier", "current_tier_rank"):
        assert at_body[k] == live_body[k], k


def test_endpoint_never_5xx_on_resolver_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get("/api/entitlement/has-channel-count-at?tier=pro&count=5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["has_channel_count_at"] is False
    assert body["current_tier"] == "oss"


def test_endpoint_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("scalar blew up")

    monkeypatch.setattr(_ent, "has_channel_count_at", _boom)
    resp = client.get("/api/entitlement/has-channel-count-at?tier=pro&count=5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["has_channel_count_at"] is False


# ── Scalar-vs-endpoint parity ─────────────────────────────────────────────


def test_endpoint_scalar_vs_endpoint_parity(client, ent):
    """Endpoint value equals the scalar for every (perspective, count)
    pair on a mixed grid."""
    for tier in ("oss", "cloud_free", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        if tier not in ent._TIER_ORDER:
            continue
        for count in (0, 1, 2, 5, 10, 100, 10_000):
            body = _get_json(
                client,
                f"/api/entitlement/has-channel-count-at?tier={tier}&count={count}",
            )
            assert body["has_channel_count_at"] is ent.has_channel_count_at(
                tier, count
            ), (tier, count)


# ── Envelope stability across many input branches ────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-channel-count-at",
        "/api/entitlement/has-channel-count-at?tier=",
        "/api/entitlement/has-channel-count-at?count=",
        "/api/entitlement/has-channel-count-at?tier=&count=",
        "/api/entitlement/has-channel-count-at?tier=pro",
        "/api/entitlement/has-channel-count-at?count=5",
        "/api/entitlement/has-channel-count-at?tier=pro&count=5",
        "/api/entitlement/has-channel-count-at?tier=oss&count=5",
        "/api/entitlement/has-channel-count-at?tier=oss&count=1",
        "/api/entitlement/has-channel-count-at?tier=pro&count=five",
        "/api/entitlement/has-channel-count-at?tier=mars&count=5",
        "/api/entitlement/has-channel-count-at?tier=pro&count=0",
        "/api/entitlement/has-channel-count-at?tier=pro&count=-1",
        "/api/entitlement/has-channel-count-at?tier=%20PRO%20&count=%201%20",
    ],
)
def test_endpoint_envelope_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert isinstance(body["tier"], str)
    assert isinstance(body["count_raw"], str)
    assert body["count"] is None or isinstance(body["count"], int)
    assert isinstance(body["has_channel_count_at"], bool)
    assert isinstance(body["allowed"], bool)
    assert body["has_channel_count_at"] == body["allowed"]
    assert isinstance(body["perspective_tier_rank"], int)
    assert isinstance(body["required_tier_rank"], int)
    assert isinstance(body["current_tier"], str)
    assert isinstance(body["current_tier_rank"], int)
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


# ── Enforced-mode grace-independence at endpoint level ────────────────────


def test_endpoint_grace_independence(client, enforced_client, ent):
    """Endpoint answers for the SAME (perspective, count) pair are
    identical under grace vs enforce -- perspective-shaped by design.
    Only the ``grace`` / ``enforced`` envelope slots differ."""
    over = ent._FREE_CHANNEL_LIMIT + 5
    for tier in ("oss", "cloud_starter", "pro", "cloud_pro", "enterprise"):
        for count in (1, 2, over, 100):
            grace_body = _get_json(
                client,
                f"/api/entitlement/has-channel-count-at?tier={tier}&count={count}",
            )
            enf_body = _get_json(
                enforced_client,
                f"/api/entitlement/has-channel-count-at?tier={tier}&count={count}",
            )
            assert grace_body["has_channel_count_at"] == enf_body[
                "has_channel_count_at"
            ], (tier, count)
            # Diverge ONLY on the resolver-shaped slots.
            assert grace_body["required_tier"] == enf_body["required_tier"]
            assert grace_body["required_tier_rank"] == enf_body["required_tier_rank"]
            assert (
                grace_body["perspective_tier_rank"]
                == enf_body["perspective_tier_rank"]
            )
            # Deliberately do NOT assert on grace / enforced bits: both
            # fixtures reload the shared ``clawmetry.entitlements``
            # module during setup, so by the time the second fixture
            # spins up the first fixture's flask app hits whichever
            # rollout state was reloaded last. The perspective-shaped
            # invariant above is the actual point of this test.
