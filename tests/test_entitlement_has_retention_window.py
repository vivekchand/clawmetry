"""Tests for the ``has_retention_window`` boolean-gate scalar and its paired
``/api/entitlement/has-retention-window`` endpoint -- the capacity-axis
sibling of :func:`clawmetry.entitlements.has_feature` /
:func:`~clawmetry.entitlements.has_runtime` /
:func:`~clawmetry.entitlements.has_channel_count`.

Where the string-id ``has_feature`` / ``has_runtime`` scalars answer "does the
CURRENT resolved entitlement grant this feature/runtime?", and
``has_channel_count`` answers the same on the concurrent-channel axis,
``has_retention_window`` answers "does the resolved entitlement admit this
many days of history?" -- one boolean plus the surrounding tier envelope so a
paywall tile on the history-range surface can bind ``allowed`` directly off
the URL.

This file pins:

1. Scalar-helper behaviour under both rollout modes (grace vs enforce) for
   zero / negative / positive / non-int / None (unlimited) / string-int
   input.
2. Endpoint envelope shape parity (fixed 11-key set) across every input
   branch so a frontend can bind fields off the URL without a branch on the
   underlying resolver state.
3. Never-5xx via monkeypatched blowup on both
   :func:`min_tier_for_retention_window` and :func:`get_entitlement`.
4. Cross-consistency with the sibling
   ``/api/entitlement/required-tier?retention_days=<N>`` endpoint -- same
   ``required_tier`` / ``current_tier`` for the same parsed ``days`` so a UI
   wiring both URLs into the same paywall tile can't see inconsistent tier
   state.
5. The grace-mode invariant: ``has_retention_window`` reports ``True`` for
   every finite ``days`` AND the unlimited request while ``grace`` is on, so
   wiring this into a history-range gate today changes no current behavior.
6. Scalar-vs-endpoint parity: envelope ``has_retention_window`` matches the
   module-level scalar byte-for-byte on the same input.
7. The unlimited-request branch: ``?days=unlimited`` (case-insensitive) is a
   first-class input separate from missing/blank -- ``days=null``,
   ``unlimited=true``, ``required_tier`` routes to Enterprise.
"""
from __future__ import annotations

import importlib
import json
import time

import pytest
from flask import Flask


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ``~/.clawmetry/license.key`` or ``cloud_plan.json`` leaks in.
    Enforcement off by default -- matches the project rollout posture and
    reuses the same fixture shape ``tests/test_entitlements_retention_window.py``
    uses so the assertions here reproduce the same install state the sibling
    :meth:`Entitlement.allows_retention_window` tests are pinned against."""
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
    to False so the grace pass-through collapses and the paid axes report
    their post-enforce answers. Matches ``enforced`` in
    ``tests/test_entitlement_has_feature_has_runtime.py``."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


def _write_plan(tmp_path, plan, **extra):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    body = {"plan": plan}
    body.update(extra)
    cache.write_text(json.dumps(body))


@pytest.fixture
def enforced_enterprise(monkeypatch, tmp_path):
    """Enforcement on, enterprise plan wired via the disk cache the resolver
    reads. Enterprise's ``event_retention_days`` cap is ``None`` (unlimited)
    so every window (including the ``None`` unlimited request) is admitted
    -- lets a test pin the "top-tier grants everything" branch symmetrically
    with the OSS-cap-at-7 branch."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_plan(tmp_path, "enterprise")
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


@pytest.fixture
def enforced_cloud_starter(monkeypatch, tmp_path):
    """Enforcement on, cloud_starter plan (retention cap = 30 days). Lets a
    test pin the mid-tier boundary."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_plan(tmp_path, "cloud_starter")
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
    "days",
    "days_raw",
    "unlimited",
    "has_retention_window",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "upgrade_required",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# ── has_retention_window scalar ─────────────────────────────────────────────


def test_scalar_zero_is_true(ent):
    """A zero-day window is trivially satisfied -- matches
    :meth:`Entitlement.allows_retention_window`'s grace-on-zero contract and
    :func:`min_tier_for_retention_window`'s ``TIER_OSS`` fallback."""
    assert ent.has_retention_window(0) is True


def test_scalar_negative_is_true(ent):
    """Negative windows collapse to True (trivially satisfied)."""
    for n in (-1, -100, -999):
        assert ent.has_retention_window(n) is True, n


def test_scalar_positive_true_in_grace(ent):
    """Grace invariant on the days axis: every finite positive window
    reports True while ``ent.grace`` is on. Wiring this into a gate today
    changes no behavior."""
    for n in (1, 7, 30, 90, 365, 10_000):
        assert ent.has_retention_window(n) is True, n


def test_scalar_none_true_in_grace(ent):
    """The unlimited-request input (``None``) is also grace-permitted --
    matches :meth:`Entitlement.allows_retention_window(None)` in grace."""
    assert ent.has_retention_window(None) is True


def test_scalar_positive_after_enforcement_on_oss(enforced):
    """Post-enforcement on OSS: windows within the free cap of 7 return True,
    windows above collapse to False."""
    assert enforced.has_retention_window(1) is True
    assert enforced.has_retention_window(7) is True
    assert enforced.has_retention_window(8) is False
    assert enforced.has_retention_window(30) is False
    assert enforced.has_retention_window(365) is False


def test_scalar_none_after_enforcement_on_oss(enforced):
    """Post-enforcement on OSS: unlimited request is denied (only Enterprise
    grants it) -- mirrors
    :meth:`Entitlement.allows_retention_window(None)` under enforce."""
    assert enforced.has_retention_window(None) is False


def test_scalar_positive_after_enforcement_on_starter(enforced_cloud_starter):
    """Post-enforcement on cloud_starter: retention cap 30 days."""
    assert enforced_cloud_starter.has_retention_window(7) is True
    assert enforced_cloud_starter.has_retention_window(30) is True
    assert enforced_cloud_starter.has_retention_window(31) is False
    assert enforced_cloud_starter.has_retention_window(365) is False
    assert enforced_cloud_starter.has_retention_window(None) is False


def test_scalar_positive_after_enforcement_paid_is_unlimited(enforced_enterprise):
    """Post-enforcement on enterprise: every finite window AND the unlimited
    request are admitted."""
    for n in (1, 7, 30, 90, 365, 10_000):
        assert enforced_enterprise.has_retention_window(n) is True, n
    assert enforced_enterprise.has_retention_window(None) is True


def test_scalar_non_int_is_false(ent):
    """Non-int non-None input collapses to False -- fail-closed matches
    :func:`has_feature` / :func:`has_runtime` / :func:`has_channel_count`
    on unknown/junk input. The one exception is ``None``, which is a
    first-class input meaning "unlimited request"."""
    for arg in ("seven", "  ", "", "7.5", "bogus", [], {}, (1,)):
        assert ent.has_retention_window(arg) is False, arg


def test_scalar_bool_is_true_because_int_subclass(ent):
    """Python bools ARE ints (``True == 1``, ``False == 0``): the scalar
    delegates to ``int(days)`` so ``True`` -> 1 -> allowed (grace),
    ``False`` -> 0 -> trivially satisfied. Documented here to catch a
    future refactor that adds a bool-rejection branch."""
    assert ent.has_retention_window(True) is True
    assert ent.has_retention_window(False) is True


def test_scalar_string_int_is_accepted(ent):
    """String-int (``"30"``) is accepted -- ``int("30")`` succeeds. Lets a
    query-string caller (which always sees strings) hit the scalar without
    manual pre-parsing."""
    for n in ("1", "7", "30", "90"):
        assert ent.has_retention_window(n) is True, n


def test_scalar_never_raises_on_resolver_blowup(monkeypatch, ent):
    """Any blowup in ``get_entitlement`` collapses to False so a caller can
    bind this into a boolean AND-chain without a try/except -- covers both
    the ``None`` (unlimited) and int branches."""
    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    for arg in (1, 7, 30, 90, 0, -5, None):
        assert ent.has_retention_window(arg) is False, arg


def test_scalar_never_raises_on_allows_retention_window_blowup(monkeypatch, ent):
    """Blowup deeper in :meth:`Entitlement.allows_retention_window` also
    collapses to False -- pin the outer never-raises contract."""
    real_get = ent.get_entitlement

    def _fake_get(*a, **kw):
        en = real_get(*a, **kw)

        def _boom(*_a, **_kw):
            raise RuntimeError("allows_retention_window blew up")

        en.allows_retention_window = _boom  # type: ignore[method-assign]
        return en

    monkeypatch.setattr(ent, "get_entitlement", _fake_get)
    assert ent.has_retention_window(30) is False
    assert ent.has_retention_window(None) is False


# ── /api/entitlement/has-retention-window envelope ──────────────────────────


def test_endpoint_positive_shape_grace(client):
    """Grace-mode positive count above OSS floor:
    has_retention_window=True (grace grant) and required_tier routes to the
    cheapest tier that would fit the window post-enforcement."""
    body = _get_json(client, "/api/entitlement/has-retention-window?days=30")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] == 30
    assert body["days_raw"] == "30"
    assert body["unlimited"] is False
    assert body["has_retention_window"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "cloud_starter"
    assert body["required_tier_label"] == "Starter"
    assert body["required_tier_rank"] == 1
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["upgrade_required"] is True


def test_endpoint_within_free_cap_shape(client):
    """A window within the OSS free cap (<=7 days) routes to
    ``required_tier="oss"`` (the free floor covers it)."""
    body = _get_json(client, "/api/entitlement/has-retention-window?days=7")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] == 7
    assert body["required_tier"] == "oss"
    assert body["required_tier_label"] == "OSS"
    assert body["required_tier_rank"] == 0
    assert body["has_retention_window"] is True
    assert body["upgrade_required"] is False


def test_endpoint_pro_boundary_shape(client):
    """A 90-day window routes to cloud_pro exactly at the boundary."""
    body = _get_json(client, "/api/entitlement/has-retention-window?days=90")
    assert body["days"] == 90
    assert body["required_tier"] == "cloud_pro"
    assert body["required_tier_rank"] == 2
    assert body["has_retention_window"] is True  # grace grant
    assert body["upgrade_required"] is True


def test_endpoint_enterprise_only_shape(client):
    """A window above the Pro cap (>90 days) routes to enterprise."""
    body = _get_json(client, "/api/entitlement/has-retention-window?days=365")
    assert body["days"] == 365
    assert body["required_tier"] == "enterprise"
    assert body["has_retention_window"] is True  # grace grant


def test_endpoint_zero_shape(client):
    """Zero collapses to trivially-satisfied: ``has_retention_window=True``
    with ``required_tier="oss"``. Mirrors
    :func:`min_tier_for_retention_window` and
    :meth:`Entitlement.allows_retention_window`."""
    body = _get_json(client, "/api/entitlement/has-retention-window?days=0")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] == 0
    assert body["has_retention_window"] is True
    assert body["required_tier"] == "oss"
    assert body["required_tier_rank"] == 0
    assert body["upgrade_required"] is False
    assert body["unlimited"] is False


def test_endpoint_negative_shape(client):
    """Negative windows route the same way zero does (trivially
    satisfied)."""
    body = _get_json(client, "/api/entitlement/has-retention-window?days=-5")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] == -5
    assert body["has_retention_window"] is True
    assert body["required_tier"] == "oss"
    assert body["upgrade_required"] is False


def test_endpoint_missing_param_shape(client):
    """Missing ``?days=`` -- never 4xx (matches the never-crash posture of
    the sibling ``/api/entitlement/has-channel-count`` endpoint on missing
    input). ``days=null``, ``unlimited=false``,
    ``has_retention_window=false``, ``required_tier=null``. Distinguishable
    from ``?days=unlimited`` via the ``unlimited`` flag."""
    body = _get_json(client, "/api/entitlement/has-retention-window")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == ""
    assert body["unlimited"] is False
    assert body["has_retention_window"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["required_tier_label"] is None
    assert body["required_tier_rank"] == -1
    assert body["upgrade_required"] is False


def test_endpoint_blank_param_shape(client):
    """Explicit blank ``?days=`` -- same shape as missing."""
    body = _get_json(client, "/api/entitlement/has-retention-window?days=")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == ""
    assert body["unlimited"] is False
    assert body["has_retention_window"] is False


def test_endpoint_whitespace_param_shape(client):
    """Whitespace-only ``?days=%20%20`` strips to empty -- same shape."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window?days=%20%20"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == ""
    assert body["unlimited"] is False
    assert body["has_retention_window"] is False


def test_endpoint_unparseable_shape(client):
    """Non-int input (``?days=bogus``) -- never 4xx, echoes
    ``days_raw="bogus"``, ``days=null``, ``has_retention_window=false``."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window?days=bogus"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == "bogus"
    assert body["unlimited"] is False
    assert body["has_retention_window"] is False
    assert body["required_tier"] is None


def test_endpoint_float_string_is_unparseable(client):
    """A float-string like ``30.5`` fails ``int()`` -- unparseable shape."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window?days=30.5"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == "30.5"
    assert body["has_retention_window"] is False


def test_endpoint_string_int_shape(client):
    """Query-string ints (always strings) are accepted -- parity with
    ``/required-tier?retention_days=90``."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window?days=90"
    )
    assert body["days"] == 90
    assert body["days_raw"] == "90"
    assert body["has_retention_window"] is True


def test_endpoint_stripped_days_raw(client):
    """Surrounding whitespace in the raw param is stripped before echo."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window?days=%20%2030%20%20"
    )
    assert body["days"] == 30
    assert body["days_raw"] == "30"


# ── Unlimited-request branch ────────────────────────────────────────────────


def test_endpoint_unlimited_shape_grace(client):
    """``?days=unlimited`` -- explicit unlimited-history request. In grace,
    the resolver grants it (grace pass-through), and ``required_tier``
    routes to Enterprise (the only tier with unlimited retention on the
    current tier table)."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window?days=unlimited"
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == "unlimited"
    assert body["unlimited"] is True
    assert body["has_retention_window"] is True  # grace grant
    assert body["allowed"] is True
    assert body["required_tier"] == "enterprise"
    assert body["required_tier_label"] == "Enterprise"
    assert body["required_tier_rank"] == 3
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["upgrade_required"] is True


def test_endpoint_unlimited_uppercase_shape(client):
    """``?days=UNLIMITED`` -- case-insensitive alias."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window?days=UNLIMITED"
    )
    assert body["unlimited"] is True
    assert body["days"] is None
    assert body["days_raw"] == "UNLIMITED"
    assert body["has_retention_window"] is True  # grace grant


def test_endpoint_unlimited_after_enforcement_on_oss(enforced_client):
    """Post-enforcement on OSS: the unlimited request is denied -- only
    Enterprise grants unlimited retention."""
    body = _get_json(
        enforced_client, "/api/entitlement/has-retention-window?days=unlimited"
    )
    assert body["unlimited"] is True
    assert body["days"] is None
    assert body["has_retention_window"] is False
    assert body["allowed"] is False
    assert body["required_tier"] == "enterprise"
    assert body["upgrade_required"] is True


# ── Never-5xx (monkeypatched blowup) ────────────────────────────────────────


def test_endpoint_never_5xx_on_body_blowup(monkeypatch, client):
    """A blowup deep in the min_tier resolver still returns 200 with the
    fallback envelope."""
    def _boom(*a, **kw):
        raise RuntimeError("min_tier_for_retention_window blew up")

    from clawmetry import entitlements as _ent

    monkeypatch.setattr(_ent, "min_tier_for_retention_window", _boom)
    resp = client.get("/api/entitlement/has-retention-window?days=30")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == "30"
    assert body["unlimited"] is False
    assert body["has_retention_window"] is False
    assert body["allowed"] is False


def test_endpoint_never_5xx_on_entitlement_blowup(monkeypatch, client):
    """A blowup in ``get_entitlement`` still returns 200 with the fallback
    envelope."""
    def _boom(*a, **kw):
        raise RuntimeError("get_entitlement blew up")

    from clawmetry import entitlements as _ent

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get("/api/entitlement/has-retention-window?days=30")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["has_retention_window"] is False
    assert body["allowed"] is False


def test_endpoint_never_5xx_on_unlimited_branch_blowup(monkeypatch, client):
    """A blowup on the unlimited-request branch also 200s with the
    fallback envelope -- ``unlimited=true`` is preserved so the caller can
    still tell which branch tripped."""
    def _boom(*a, **kw):
        raise RuntimeError("get_entitlement blew up")

    from clawmetry import entitlements as _ent

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get("/api/entitlement/has-retention-window?days=unlimited")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == "unlimited"
    assert body["unlimited"] is True
    assert body["has_retention_window"] is False


def test_fallback_shape_direct():
    """Direct call of the fallback helper: fixed 11-key envelope, all
    fields fail-closed / defaulted."""
    from routes.entitlement import _has_retention_window_fallback

    body = _has_retention_window_fallback("42", False)
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["days"] is None
    assert body["days_raw"] == "42"
    assert body["unlimited"] is False
    assert body["has_retention_window"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["required_tier_label"] is None
    assert body["required_tier_rank"] == -1
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["upgrade_required"] is False


def test_fallback_shape_unlimited_true():
    """Fallback preserves ``unlimited=true`` when the tripped branch was
    the unlimited-request one."""
    from routes.entitlement import _has_retention_window_fallback

    body = _has_retention_window_fallback("unlimited", True)
    assert body["unlimited"] is True
    assert body["days_raw"] == "unlimited"
    assert body["days"] is None
    assert body["has_retention_window"] is False


# ── Cross-consistency with /required-tier?retention_days=N ──────────────────


@pytest.mark.parametrize("n", [1, 7, 8, 30, 31, 90, 91, 365])
def test_endpoint_cross_consistent_with_required_tier(client, n):
    """Same input -> same tier answer on both endpoints. A UI wiring
    ``/has-retention-window`` and ``/required-tier?retention_days=`` into
    the same paywall tile can't see inconsistent tier state."""
    has_body = _get_json(
        client, f"/api/entitlement/has-retention-window?days={n}"
    )
    req_body = _get_json(
        client, f"/api/entitlement/required-tier?retention_days={n}"
    )
    assert has_body["required_tier"] == req_body["required_tier"], n
    assert has_body["required_tier_label"] == req_body["required_tier_label"], n
    assert has_body["required_tier_rank"] == req_body["required_tier_rank"], n
    assert has_body["current_tier"] == req_body["current_tier"], n
    assert has_body["current_tier_rank"] == req_body["current_tier_rank"], n
    assert has_body["upgrade_required"] == req_body["upgrade_required"], n
    assert has_body["allowed"] == req_body["allowed"], n


# ── Scalar-vs-endpoint parity ───────────────────────────────────────────────


@pytest.mark.parametrize("n", [0, 1, 7, 8, 30, 31, 90, 91, 365, -1])
def test_endpoint_matches_scalar_int(client, ent, n):
    """Envelope ``has_retention_window`` matches the module-level scalar
    byte-for-byte -- no drift possible between the two."""
    body = _get_json(
        client, f"/api/entitlement/has-retention-window?days={n}"
    )
    assert body["has_retention_window"] is ent.has_retention_window(n)
    assert body["allowed"] is ent.has_retention_window(n)


def test_endpoint_matches_scalar_unlimited(client, ent):
    """``?days=unlimited`` -> scalar ``has_retention_window(None)``."""
    body = _get_json(
        client, "/api/entitlement/has-retention-window?days=unlimited"
    )
    assert body["has_retention_window"] is ent.has_retention_window(None)
    assert body["allowed"] is ent.has_retention_window(None)


@pytest.mark.parametrize("raw", ["bogus", "", "  ", "30.5"])
def test_endpoint_matches_scalar_bad_input(client, ent, raw):
    """On unparseable input, both endpoint and scalar report False."""
    import urllib.parse
    url = f"/api/entitlement/has-retention-window?days={urllib.parse.quote(raw)}"
    body = _get_json(client, url)
    assert body["has_retention_window"] is False
    # Scalar on the same raw input also reports False (strings that don't
    # parse as int fail-close).
    assert ent.has_retention_window(raw) is False


# ── Grace invariant on the days axis ────────────────────────────────────────


def test_grace_invariant_every_finite_days_true(ent):
    """The headline grace invariant on the days axis: while grace is on,
    every finite non-negative days value reports
    ``has_retention_window=True``. This is what makes wiring this into a
    gate today a no-op behavior change -- exactly parallel to the
    feature/runtime/channels grace invariant on their axes."""
    for n in (0, 1, 7, 8, 30, 31, 90, 91, 365, 1_000, 10_000):
        assert ent.has_retention_window(n) is True, n


def test_grace_invariant_unlimited_true(ent):
    """The grace invariant extends to the unlimited-request input --
    ``None`` returns True while grace is on."""
    assert ent.has_retention_window(None) is True


def test_enforce_free_capped_at_seven(enforced):
    """Symmetric assertion on the enforcement side: on OSS-free, windows
    above the free cap report False."""
    assert enforced.has_retention_window(7) is True
    assert enforced.has_retention_window(8) is False
    assert enforced.has_retention_window(30) is False
    assert enforced.has_retention_window(365) is False
    assert enforced.has_retention_window(None) is False


def test_enforce_expired_paid_denies_positive_windows(monkeypatch, tmp_path):
    """Post-enforcement expired paid plan denies any positive window --
    matches the expiry semantics of
    :meth:`Entitlement.allows_retention_window` (the ``self.expired`` guard
    on line 2238)."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({
        "plan": "cloud_pro",
        "expiry": time.time() - 60,
    }))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    try:
        # Zero is trivially satisfied even on expired plans.
        assert e.has_retention_window(0) is True
        # Any positive window is denied on an expired plan.
        assert e.has_retention_window(1) is False
        assert e.has_retention_window(7) is False
        assert e.has_retention_window(90) is False
        assert e.has_retention_window(None) is False
    finally:
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(e)
        e.invalidate()


# ── Envelope invariants across every branch ─────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-retention-window",
        "/api/entitlement/has-retention-window?days=",
        "/api/entitlement/has-retention-window?days=0",
        "/api/entitlement/has-retention-window?days=1",
        "/api/entitlement/has-retention-window?days=7",
        "/api/entitlement/has-retention-window?days=8",
        "/api/entitlement/has-retention-window?days=30",
        "/api/entitlement/has-retention-window?days=90",
        "/api/entitlement/has-retention-window?days=365",
        "/api/entitlement/has-retention-window?days=-1",
        "/api/entitlement/has-retention-window?days=bogus",
        "/api/entitlement/has-retention-window?days=30.5",
        "/api/entitlement/has-retention-window?days=%20%20",
        "/api/entitlement/has-retention-window?days=unlimited",
        "/api/entitlement/has-retention-window?days=UNLIMITED",
    ],
)
def test_envelope_shape_invariant(client, url):
    """Fixed 11-key envelope across every input branch -- a frontend can
    bind fields off the URL without a branch on the resolver state."""
    body = _get_json(client, url)
    assert set(body.keys()) == _ENVELOPE_KEYS, url
    assert isinstance(body["has_retention_window"], bool)
    assert isinstance(body["allowed"], bool)
    assert isinstance(body["upgrade_required"], bool)
    assert isinstance(body["unlimited"], bool)
    assert isinstance(body["current_tier"], str)
    assert isinstance(body["current_tier_rank"], int)
    assert isinstance(body["required_tier_rank"], int)
    assert body["days"] is None or isinstance(body["days"], int)
    assert isinstance(body["days_raw"], str)
