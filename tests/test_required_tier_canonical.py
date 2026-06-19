"""Pin :func:`clawmetry._gate._required_tier` and
:func:`clawmetry._paywall._min_tier_for_feature` to the canonical
:func:`clawmetry.entitlements.min_tier_for_feature` resolver.

Before this consolidation both helpers carried their own hand-rolled
if-tree against ``FREE_FEATURES`` / ``STARTER_FEATURES`` / ``PRO_ONLY_FEATURES``
/ ``ENTERPRISE_FEATURES``. The runtime side already pointed at the
canonical :func:`min_tier_for_runtime` (see :func:`_required_tier_for_runtime`
in ``_gate.py``); the feature side did not. Adding a new tier bucket or
renaming a constant would silently drift the 402 ``required_tier`` between
the ``@gate`` decorator's body and the OSS-stub body for the same key.

These tests assert that for every key in the catalogue both helpers track
:func:`min_tier_for_feature` exactly, with the single documented translation
:data:`TIER_OSS` -> ``None`` (free keys don't have an upgrade target -- the
UI uses ``None`` to short-circuit the CTA render). They also verify the
never-raise contract still holds when the canonical resolver itself blows
up.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def ent_grace(monkeypatch, tmp_path):
    """Reload entitlements pointed at an empty HOME so the resolver collapses
    to OSS-free deterministically. Mirrors the fixture in
    ``tests/test_paywall_body.py``."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


def _expected_required_tier(ent_module, key: str):
    """The wire shape both helpers must produce: canonical resolver answer
    with :data:`TIER_OSS` collapsed to ``None``."""
    tier = ent_module.min_tier_for_feature(key)
    if tier is None or tier == ent_module.TIER_OSS:
        return None
    return tier


def test_gate_required_tier_matches_canonical_for_full_catalogue(ent_grace):
    """``_gate._required_tier`` must agree with the canonical resolver for
    every key in ``ALL_FEATURES`` -- the universe both the ``@gate``
    decorator and the OSS-stub body builder branch on."""
    from clawmetry._gate import _required_tier

    for key in ent_grace.ALL_FEATURES:
        assert _required_tier(key) == _expected_required_tier(ent_grace, key), key


def test_paywall_min_tier_matches_canonical_for_full_catalogue(ent_grace):
    """``_paywall._min_tier_for_feature`` must agree with the canonical
    resolver for every key in ``ALL_FEATURES`` -- the OSS-stub blueprints
    that adopt :func:`upgrade_required_body` rely on this."""
    from clawmetry._paywall import _min_tier_for_feature

    for key in ent_grace.ALL_FEATURES:
        assert (
            _min_tier_for_feature(ent_grace, key)
            == _expected_required_tier(ent_grace, key)
        ), key


def test_gate_and_paywall_helpers_agree_for_full_catalogue(ent_grace):
    """The two helpers must produce identical output for every catalogue
    key, so the 402 body emitted by ``@gate`` and by the OSS-stub builder
    carry the same ``required_tier`` for the same feature."""
    from clawmetry._gate import _required_tier
    from clawmetry._paywall import _min_tier_for_feature

    for key in ent_grace.ALL_FEATURES:
        assert _required_tier(key) == _min_tier_for_feature(ent_grace, key), key


def test_gate_required_tier_free_collapses_to_none(ent_grace):
    """Free features have no upgrade target -- ``required_tier`` is ``None``
    so the UI short-circuits the CTA render."""
    from clawmetry._gate import _required_tier

    for key in ent_grace.FREE_FEATURES:
        assert _required_tier(key) is None, key


def test_gate_required_tier_unknown_collapses_to_none(ent_grace):
    """An unknown / typo'd key resolves to ``None`` -- a clawmetry-pro
    plugin's private feature id we don't have in the OSS catalogue still
    produces a well-formed 402 body."""
    from clawmetry._gate import _required_tier

    assert _required_tier("totally_unknown_feature_xyz") is None
    assert _required_tier("") is None


def test_gate_required_tier_starter_feature_resolves_to_starter(ent_grace):
    """Starter-card features resolve to ``cloud_starter`` -- the cheapest
    purchasable tier that unlocks them. Mirrors
    :func:`min_tier_for_feature`."""
    from clawmetry._gate import _required_tier

    for key in ("multi_runtime", "fleet", "all_channels", "budget_limits"):
        assert _required_tier(key) == ent_grace.TIER_CLOUD_STARTER, key


def test_gate_required_tier_pro_feature_resolves_to_pro(ent_grace):
    """Pro-only features resolve to ``cloud_pro``."""
    from clawmetry._gate import _required_tier

    for key in ("self_evolve", "custom_runtime_ingest", "otel_export"):
        assert _required_tier(key) == ent_grace.TIER_CLOUD_PRO, key


def test_gate_required_tier_enterprise_feature_resolves_to_enterprise(ent_grace):
    """Enterprise-only features resolve to ``enterprise`` so the 402 body
    drives the right CTA (not the Pro one)."""
    from clawmetry._gate import _required_tier

    for key in ("audit_logs", "sso", "siem_export"):
        assert _required_tier(key) == ent_grace.TIER_ENTERPRISE, key


def test_gate_required_tier_swallows_resolver_errors(monkeypatch):
    """A flaky :func:`min_tier_for_feature` falls back to ``None`` -- the
    402 body must stay well-formed even when the catalogue lookup blows
    up. Same posture as ``upgrade_required_body``'s never-raise contract."""
    import clawmetry.entitlements as ent
    from clawmetry._gate import _required_tier

    def explode(_key):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "min_tier_for_feature", explode)
    assert _required_tier("self_evolve") is None


def test_paywall_min_tier_swallows_resolver_errors(monkeypatch):
    """Same never-raise contract for the OSS-stub helper -- the body
    builder's outer try/except still degrades cleanly to
    ``required_tier=None`` when the canonical resolver blows up."""
    import clawmetry.entitlements as ent
    from clawmetry._paywall import _min_tier_for_feature

    def explode(_key):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "min_tier_for_feature", explode)
    with pytest.raises(RuntimeError):
        # The helper itself propagates -- the outer try/except in
        # ``upgrade_required_body`` is what swallows it. Pin both layers
        # explicitly so the contract is unambiguous.
        _min_tier_for_feature(ent, "self_evolve")

    from clawmetry._paywall import upgrade_required_body

    body = upgrade_required_body("self_evolve")
    assert body["error"] == "upgrade_required"
    assert body["required_tier"] is None


def test_paywall_min_tier_handles_missing_resolver(ent_grace):
    """A stripped ``entitlements`` module without ``min_tier_for_feature``
    collapses cleanly to ``None`` -- the OSS-stub builder still emits a
    well-formed body."""
    from clawmetry._paywall import _min_tier_for_feature

    class _Stub:
        TIER_OSS = "oss"
        # deliberately no ``min_tier_for_feature`` attr

    assert _min_tier_for_feature(_Stub, "self_evolve") is None


def test_paywall_min_tier_handles_blank_key(ent_grace):
    """Blank / whitespace-only keys short-circuit to ``None`` without
    calling the canonical resolver."""
    from clawmetry._paywall import _min_tier_for_feature

    assert _min_tier_for_feature(ent_grace, "") is None
    assert _min_tier_for_feature(ent_grace, "   ") is None
    assert _min_tier_for_feature(ent_grace, None) is None  # type: ignore[arg-type]
