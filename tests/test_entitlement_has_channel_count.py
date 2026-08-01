"""Tests for the ``has_channel_count`` boolean-gate scalar and its paired
``/api/entitlement/has-channel-count`` endpoint -- the capacity-axis sibling of
:func:`clawmetry.entitlements.has_feature` / :func:`~clawmetry.entitlements.has_runtime`.

Where the string-id ``has_feature`` / ``has_runtime`` scalars answer "does the
CURRENT resolved entitlement grant this feature/runtime?", ``has_channel_count``
answers the same question on the ``channels`` capacity axis: "does the resolved
entitlement admit this many chat-channel adapters concurrently?" -- one boolean
plus the surrounding tier envelope so a paywall tile on the channels surface
can bind ``allowed`` directly off the URL.

This file pins:

1. Scalar-helper behaviour under both rollout modes (grace vs enforce) for
   zero / negative / positive / non-int / None input.
2. Endpoint envelope shape parity (fixed 10-key set) across every input
   branch so a frontend can bind fields off the URL without a branch on the
   underlying resolver state.
3. Never-5xx via monkeypatched blowup: happy-path body builder AND
   :func:`min_tier_for_channel_count`.
4. Cross-consistency with the sibling ``/api/entitlement/required-tier?channels=<N>``
   endpoint -- same ``required_tier`` / ``current_tier`` for the same
   ``count`` so a UI wiring both URLs into the same paywall tile can't see
   inconsistent tier state.
5. The grace-mode invariant: ``has_channel_count`` reports ``True`` for every
   finite count while ``grace`` is on, so wiring this into a capacity gate
   today changes no current behavior.
6. Scalar-vs-endpoint parity: envelope ``has_channel_count`` matches the
   module-level scalar byte-for-byte on the same input.
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
    reuses the same fixture shape ``tests/test_entitlement_channel_limit.py``
    uses so the assertions here reproduce the same install state the
    sibling :meth:`Entitlement.allows_channel_count` tests are pinned
    against."""
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


@pytest.fixture
def enforced_cloud_starter(monkeypatch, tmp_path):
    """Enforcement on, cloud_starter plan wired via the disk cache the
    resolver reads. Starter's ``_TIER_CHANNEL_LIMIT`` is ``None`` (unlimited)
    so every count is admitted -- lets a test pin the "paid tier grants
    everything" branch symmetrically with the OSS-cap branch."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_starter"}))
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
    "count",
    "count_raw",
    "has_channel_count",
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


# ── has_channel_count scalar ────────────────────────────────────────────────


def test_scalar_zero_is_true(ent):
    """A zero count is trivially satisfied -- matches
    :meth:`Entitlement.allows_channel_count`'s grace-on-zero contract and
    :func:`min_tier_for_channel_count`'s ``TIER_OSS`` fallback."""
    assert ent.has_channel_count(0) is True


def test_scalar_negative_is_true(ent):
    """Negative counts collapse to True (trivially satisfied)."""
    for n in (-1, -100, -999):
        assert ent.has_channel_count(n) is True, n


def test_scalar_positive_true_in_grace(ent):
    """Grace invariant on the count axis: every finite positive count
    reports True while ``ent.grace`` is on. Wiring this into a gate today
    changes no behavior."""
    for n in (1, 3, 4, 21, 100, 10_000):
        assert ent.has_channel_count(n) is True, n


def test_scalar_positive_after_enforcement(enforced):
    """Post-enforcement on OSS: counts within the free cap of 3 return True,
    counts above collapse to False."""
    assert enforced.has_channel_count(1) is True
    assert enforced.has_channel_count(3) is True
    assert enforced.has_channel_count(4) is False
    assert enforced.has_channel_count(21) is False


def test_scalar_positive_after_enforcement_paid_is_unlimited(enforced_cloud_starter):
    """Post-enforcement on cloud_starter: unlimited channels."""
    for n in (1, 3, 4, 21, 100, 10_000):
        assert enforced_cloud_starter.has_channel_count(n) is True, n


def test_scalar_non_int_is_false(ent):
    """Non-int input collapses to False -- fail-closed matches
    :func:`has_feature` / :func:`has_runtime` on unknown/junk input, even
    though the underlying :meth:`Entitlement.allows_channel_count` is
    permissive on parse failure (the scalar has a strict callsite-typo
    posture that catches ``has_channel_count("five")`` at the callsite)."""
    for arg in ("bogus", "  ", "", "5.5", "one", [], {}, (1,)):
        assert ent.has_channel_count(arg) is False, arg


def test_scalar_none_is_false(ent):
    """None collapses to False (fail-closed) -- differs from
    :meth:`Entitlement.allows_channel_count(None)` which is True; the scalar
    surfaces the callsite bug instead of silently granting."""
    assert ent.has_channel_count(None) is False  # type: ignore[arg-type]


def test_scalar_bool_is_true_because_int_subclass(ent):
    """Python bools ARE ints (``True == 1``, ``False == 0``): the scalar
    delegates to ``int(count)`` so ``True`` -> 1 -> allowed (grace), ``False``
    -> 0 -> trivially satisfied. Documented here to catch a future refactor
    that adds a bool-rejection branch."""
    assert ent.has_channel_count(True) is True
    assert ent.has_channel_count(False) is True


def test_scalar_string_int_is_accepted(ent):
    """String-int (``"5"``) is accepted -- ``int("5")`` succeeds. Lets a
    query-string caller (which always sees strings) hit the scalar without
    manual pre-parsing."""
    for n in ("1", "3", "21", "100"):
        assert ent.has_channel_count(n) is True, n


def test_scalar_never_raises_on_resolver_blowup(monkeypatch, ent):
    """Any blowup in ``get_entitlement`` collapses to False so a caller can
    bind this into a boolean AND-chain without a try/except."""
    def _boom(*a, **kw):
        raise RuntimeError("resolver blew up")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    for arg in (1, 3, 21, 100, 0, -5):
        assert ent.has_channel_count(arg) is False, arg


def test_scalar_never_raises_on_allows_channel_count_blowup(monkeypatch, ent):
    """Blowup deeper in :meth:`Entitlement.allows_channel_count` also
    collapses to False -- pin the outer never-raises contract."""
    real_get = ent.get_entitlement

    def _fake_get(*a, **kw):
        en = real_get(*a, **kw)

        def _boom(*_a, **_kw):
            raise RuntimeError("allows_channel_count blew up")

        en.allows_channel_count = _boom  # type: ignore[method-assign]
        return en

    monkeypatch.setattr(ent, "get_entitlement", _fake_get)
    assert ent.has_channel_count(5) is False


# ── /api/entitlement/has-channel-count envelope ─────────────────────────────


def test_endpoint_positive_shape_grace(client):
    """Grace-mode positive count: has_channel_count=True (grace grant) and
    required_tier=None-or-oss (the free floor covers small counts, larger
    counts route to Starter+ as their min tier)."""
    body = _get_json(client, "/api/entitlement/has-channel-count?count=5")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] == 5
    assert body["count_raw"] == "5"
    assert body["has_channel_count"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "cloud_starter"
    assert body["required_tier_label"] == "Starter"
    assert body["required_tier_rank"] == 1
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["upgrade_required"] is True


def test_endpoint_within_free_cap_shape(client):
    """A count within the OSS free cap (<=3) routes to
    ``required_tier="oss"`` (the free floor covers it)."""
    body = _get_json(client, "/api/entitlement/has-channel-count?count=1")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] == 1
    assert body["required_tier"] == "oss"
    assert body["required_tier_label"] == "OSS"
    assert body["required_tier_rank"] == 0
    assert body["has_channel_count"] is True
    assert body["upgrade_required"] is False


def test_endpoint_zero_shape(client):
    """Zero collapses to trivially-satisfied: ``has_channel_count=True``
    with ``required_tier="oss"``. Mirrors :func:`min_tier_for_channel_count`
    and :meth:`Entitlement.allows_channel_count`."""
    body = _get_json(client, "/api/entitlement/has-channel-count?count=0")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] == 0
    assert body["has_channel_count"] is True
    assert body["required_tier"] == "oss"
    assert body["required_tier_rank"] == 0
    assert body["upgrade_required"] is False


def test_endpoint_negative_shape(client):
    """Negative counts route the same way zero does (trivially satisfied)."""
    body = _get_json(client, "/api/entitlement/has-channel-count?count=-5")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] == -5
    assert body["has_channel_count"] is True
    assert body["required_tier"] == "oss"
    assert body["upgrade_required"] is False


def test_endpoint_missing_param_shape(client):
    """Missing ``?count=`` -- never 4xx (matches the never-crash posture of
    ``/api/entitlement/required-tier?channels=`` on unparseable input).
    ``count=null``, ``has_channel_count=false``, ``required_tier=null``."""
    body = _get_json(client, "/api/entitlement/has-channel-count")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] is None
    assert body["count_raw"] == ""
    assert body["has_channel_count"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["required_tier_label"] is None
    assert body["required_tier_rank"] == -1
    assert body["upgrade_required"] is False


def test_endpoint_blank_param_shape(client):
    """Explicit blank ``?count=`` -- same shape as missing."""
    body = _get_json(client, "/api/entitlement/has-channel-count?count=")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] is None
    assert body["count_raw"] == ""
    assert body["has_channel_count"] is False


def test_endpoint_whitespace_param_shape(client):
    """Whitespace-only ``?count=%20%20`` strips to empty -- same shape."""
    body = _get_json(client, "/api/entitlement/has-channel-count?count=%20%20")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] is None
    assert body["count_raw"] == ""
    assert body["has_channel_count"] is False


def test_endpoint_unparseable_shape(client):
    """Non-int input (``?count=bogus``) -- never 4xx, echoes
    ``count_raw="bogus"``, ``count=null``, ``has_channel_count=false``."""
    body = _get_json(client, "/api/entitlement/has-channel-count?count=bogus")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] is None
    assert body["count_raw"] == "bogus"
    assert body["has_channel_count"] is False
    assert body["required_tier"] is None


def test_endpoint_float_string_is_unparseable(client):
    """A float-string like ``5.5`` fails ``int()`` -- unparseable shape."""
    body = _get_json(client, "/api/entitlement/has-channel-count?count=5.5")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] is None
    assert body["count_raw"] == "5.5"
    assert body["has_channel_count"] is False


def test_endpoint_string_int_shape(client):
    """Query-string ints (always strings) are accepted -- parity with
    ``/required-tier?channels=5``."""
    body = _get_json(client, "/api/entitlement/has-channel-count?count=21")
    assert body["count"] == 21
    assert body["count_raw"] == "21"
    assert body["has_channel_count"] is True


def test_endpoint_stripped_count_raw(client):
    """Surrounding whitespace in the raw param is stripped before echo."""
    body = _get_json(client, "/api/entitlement/has-channel-count?count=%20%205%20%20")
    assert body["count"] == 5
    assert body["count_raw"] == "5"


# ── Never-5xx (monkeypatched blowup) ────────────────────────────────────────


def test_endpoint_never_5xx_on_body_blowup(monkeypatch, client):
    """A blowup deep in the min_tier resolver still returns 200 with the
    fallback envelope."""
    def _boom(*a, **kw):
        raise RuntimeError("min_tier_for_channel_count blew up")

    from clawmetry import entitlements as _ent

    monkeypatch.setattr(_ent, "min_tier_for_channel_count", _boom)
    resp = client.get("/api/entitlement/has-channel-count?count=5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] is None
    assert body["count_raw"] == "5"
    assert body["has_channel_count"] is False
    assert body["allowed"] is False


def test_endpoint_never_5xx_on_entitlement_blowup(monkeypatch, client):
    """A blowup in ``get_entitlement`` still returns 200 with the fallback
    envelope."""
    def _boom(*a, **kw):
        raise RuntimeError("get_entitlement blew up")

    from clawmetry import entitlements as _ent

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    resp = client.get("/api/entitlement/has-channel-count?count=5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] is None
    assert body["has_channel_count"] is False
    assert body["allowed"] is False


def test_fallback_shape_direct():
    """Direct call of the fallback helper: fixed 10-key envelope, all fields
    fail-closed / defaulted."""
    from routes.entitlement import _has_channel_count_fallback

    body = _has_channel_count_fallback("42")
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["count"] is None
    assert body["count_raw"] == "42"
    assert body["has_channel_count"] is False
    assert body["allowed"] is False
    assert body["required_tier"] is None
    assert body["required_tier_label"] is None
    assert body["required_tier_rank"] == -1
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
    assert body["upgrade_required"] is False


# ── Cross-consistency with /required-tier?channels=N ────────────────────────


@pytest.mark.parametrize("n", [1, 3, 4, 5, 21, 100])
def test_endpoint_cross_consistent_with_required_tier(client, n):
    """Same input -> same tier answer on both endpoints. A UI wiring
    ``/has-channel-count`` and ``/required-tier?channels=`` into the same
    paywall tile can't see inconsistent tier state."""
    has_body = _get_json(client, f"/api/entitlement/has-channel-count?count={n}")
    req_body = _get_json(client, f"/api/entitlement/required-tier?channels={n}")
    assert has_body["required_tier"] == req_body["required_tier"], n
    assert has_body["required_tier_label"] == req_body["required_tier_label"], n
    assert has_body["required_tier_rank"] == req_body["required_tier_rank"], n
    assert has_body["current_tier"] == req_body["current_tier"], n
    assert has_body["current_tier_rank"] == req_body["current_tier_rank"], n
    assert has_body["upgrade_required"] == req_body["upgrade_required"], n
    assert has_body["allowed"] == req_body["allowed"], n


# ── Scalar-vs-endpoint parity ───────────────────────────────────────────────


@pytest.mark.parametrize("n", [0, 1, 3, 4, 5, 21, 100, -1])
def test_endpoint_matches_scalar_int(client, ent, n):
    """Envelope ``has_channel_count`` matches the module-level scalar
    byte-for-byte -- no drift possible between the two."""
    body = _get_json(client, f"/api/entitlement/has-channel-count?count={n}")
    assert body["has_channel_count"] is ent.has_channel_count(n)
    assert body["allowed"] is ent.has_channel_count(n)


@pytest.mark.parametrize("raw", ["bogus", "", "  ", "5.5"])
def test_endpoint_matches_scalar_bad_input(client, ent, raw):
    """On unparseable input, both endpoint and scalar report False."""
    # URL-encode manually so the whitespace-only case survives Werkzeug's
    # query-string parser without being coalesced to an empty value.
    import urllib.parse
    url = f"/api/entitlement/has-channel-count?count={urllib.parse.quote(raw)}"
    body = _get_json(client, url)
    assert body["has_channel_count"] is False
    # Scalar on the same raw input also reports False (strings that don't
    # parse as int fail-close).
    assert ent.has_channel_count(raw) is False


# ── Grace invariant on the count axis ───────────────────────────────────────


def test_grace_invariant_every_finite_count_true(ent):
    """The headline grace invariant on the count axis: while grace is on,
    every finite non-negative count reports ``has_channel_count=True``. This
    is what makes wiring this into a gate today a no-op behavior change --
    exactly parallel to the feature/runtime grace invariant on their axes."""
    for n in (0, 1, 2, 3, 4, 5, 10, 21, 100, 1_000, 10_000):
        assert ent.has_channel_count(n) is True, n


def test_enforce_free_capped_at_three(enforced):
    """Symmetric assertion on the enforcement side: on OSS-free, counts
    above the free cap report False."""
    assert enforced.has_channel_count(3) is True
    assert enforced.has_channel_count(4) is False
    assert enforced.has_channel_count(21) is False


def test_enforce_expired_paid_collapses_to_free_cap(monkeypatch, tmp_path):
    """Post-enforcement expired paid plan collapses to the free cap of 3 --
    matches the expiry semantics of :meth:`Entitlement.allows_channel_count`."""
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
        assert e.has_channel_count(3) is True
        assert e.has_channel_count(4) is False
    finally:
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(e)
        e.invalidate()


# ── Envelope invariants across every branch ─────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-channel-count",
        "/api/entitlement/has-channel-count?count=",
        "/api/entitlement/has-channel-count?count=0",
        "/api/entitlement/has-channel-count?count=1",
        "/api/entitlement/has-channel-count?count=3",
        "/api/entitlement/has-channel-count?count=4",
        "/api/entitlement/has-channel-count?count=21",
        "/api/entitlement/has-channel-count?count=100",
        "/api/entitlement/has-channel-count?count=-1",
        "/api/entitlement/has-channel-count?count=bogus",
        "/api/entitlement/has-channel-count?count=5.5",
        "/api/entitlement/has-channel-count?count=%20%20",
    ],
)
def test_envelope_shape_invariant(client, url):
    """Fixed 10-key envelope across every input branch -- a frontend can
    bind fields off the URL without a branch on the resolver state."""
    body = _get_json(client, url)
    assert set(body.keys()) == _ENVELOPE_KEYS, url
    assert isinstance(body["has_channel_count"], bool)
    assert isinstance(body["allowed"], bool)
    assert isinstance(body["upgrade_required"], bool)
    assert isinstance(body["current_tier"], str)
    assert isinstance(body["current_tier_rank"], int)
    assert isinstance(body["required_tier_rank"], int)
    assert body["count"] is None or isinstance(body["count"], int)
    assert isinstance(body["count_raw"], str)
