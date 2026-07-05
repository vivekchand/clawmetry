"""Tests for ``tier_unlocks_at_path`` / ``tier_locks_at_path`` +
``tier_unlocks_at_path_batch`` / ``tier_locks_at_path_batch`` and their
four HTTP endpoints.

Path-shaped what-if siblings of :func:`tier_unlocks_path` /
:func:`tier_locks_path` -- render the per-rung marginal-unlocks /
marginal-locks path between two tiers from a hypothetical
``perspective_tier`` in ONE round-trip. Fills the ``_at_path`` /
``_at_path_batch`` slots for the ``tier_unlocks`` / ``tier_locks``
families so a pricing-comparison walkthrough surface can call
``X_at_path(perspective, from, to)`` uniformly across every
``_at_path`` family member (matches the already-shipping
``capacity_diff_at_path`` / ``tier_catalog_at_path`` /
``feature_catalog_at_path`` / ``preview_at_path`` /
``feature_spec_at_path`` / ``runtime_spec_at_path`` /
``tier_spec_at_path`` / ``lock_reason_at_path`` pattern).

Pins:

* per-rung ``path`` byte-identical to :func:`tier_unlocks_path` /
  :func:`tier_locks_path` for every perspective -- the perspective is
  validated but does NOT shape the rows (parity with every other
  ``_at_path`` helper).
* batch ``tiers[].path`` byte-identical to
  :func:`tier_unlocks_path_batch` / :func:`tier_locks_path_batch` for
  every perspective.
* ``trial`` accepted as perspective and as endpoint / destination.
* case + whitespace normalisation on perspective, from, to.
* helper is decoupled from the resolver -- grace vs enforce yields
  byte-identical rows.
* unknown / empty / garbage ids return ``None`` and never raise; a
  per-destination failure short-circuits that id into ``unknown[]``.
* HTTP scalar: 400 on missing args, 404 with
  ``which: "tier" | "from" | "to"`` on unknown ids, 200 with the
  standard resolver-context tail every ``_at*`` endpoint carries.
* HTTP batch: 400 on missing tier / from / empty to, 404 with
  ``which: "tier" | "from"`` on unknown perspective / source, 200
  with bucketed ``unknown[]`` on partially-bad destination lists,
  never 5xxs on a synthesis failure.
"""
from __future__ import annotations

import importlib

import pytest


_SCALAR_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "path",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}
_BATCH_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "from",
    "from_label",
    "from_rank",
    "tiers",
    "unknown",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}
_BATCH_ITEM_KEYS = {"to", "to_label", "to_rank", "direction", "path"}


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
def enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(ent):
    from flask import Flask

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


def _perspectives(mod):
    """Every id the ``_at`` family accepts as a perspective."""
    return [
        mod.TIER_OSS,
        mod.TIER_CLOUD_FREE,
        mod.TIER_TRIAL,
        mod.TIER_CLOUD_STARTER,
        mod.TIER_CLOUD_PRO,
        mod.TIER_PRO,
        mod.TIER_ENTERPRISE,
    ]


# ─── tier_unlocks_at_path: helper ─────────────────────────────────────────────


def test_unlocks_helper_returns_list(ent):
    out = ent.tier_unlocks_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )
    assert isinstance(out, list)
    assert len(out) >= 1


def test_unlocks_helper_perspective_does_not_shape_rows(ent):
    """Every perspective yields the byte-identical rows the scalar path
    helper would return -- the perspective is validated but does NOT
    shape rows (parity with every other ``_at_path`` helper)."""
    scalar = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    for p in _perspectives(ent):
        assert ent.tier_unlocks_at_path(p, ent.TIER_OSS, ent.TIER_ENTERPRISE) == scalar


def test_unlocks_helper_trial_accepted_as_perspective(ent):
    assert ent.tier_unlocks_at_path(
        ent.TIER_TRIAL, ent.TIER_OSS, ent.TIER_CLOUD_PRO
    ) == ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_CLOUD_PRO)


def test_unlocks_helper_trial_accepted_as_endpoint(ent):
    out = ent.tier_unlocks_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_TRIAL
    )
    assert out is not None


def test_unlocks_helper_case_and_whitespace_normalised(ent):
    a = ent.tier_unlocks_at_path("  CLOUD_PRO  ", "  OSS  ", "  ENTERPRISE  ")
    b = ent.tier_unlocks_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert a == b


def test_unlocks_helper_identity_returns_empty_list(ent):
    assert ent.tier_unlocks_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO
    ) == []


def test_unlocks_helper_lateral_returns_single_row(ent):
    out = ent.tier_unlocks_at_path(
        ent.TIER_OSS, ent.TIER_CLOUD_PRO, ent.TIER_PRO
    )
    assert isinstance(out, list)
    assert len(out) == 1


def test_unlocks_helper_bad_perspective_returns_none(ent):
    assert ent.tier_unlocks_at_path(
        "bogus", ent.TIER_OSS, ent.TIER_ENTERPRISE
    ) is None


def test_unlocks_helper_bad_from_returns_none(ent):
    assert ent.tier_unlocks_at_path(
        ent.TIER_CLOUD_PRO, "bogus", ent.TIER_ENTERPRISE
    ) is None


def test_unlocks_helper_bad_to_returns_none(ent):
    assert ent.tier_unlocks_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, "bogus"
    ) is None


def test_unlocks_helper_garbage_never_raises(ent):
    assert ent.tier_unlocks_at_path(None, None, None) is None  # type: ignore[arg-type]
    assert ent.tier_unlocks_at_path("", "", "") is None
    assert ent.tier_unlocks_at_path("  ", "  ", "  ") is None


def test_unlocks_helper_grace_and_enforce_yield_identical(ent, enforced):
    for perspective in _perspectives(ent):
        assert ent.tier_unlocks_at_path(
            perspective, ent.TIER_OSS, ent.TIER_ENTERPRISE
        ) == enforced.tier_unlocks_at_path(
            perspective, ent.TIER_OSS, ent.TIER_ENTERPRISE
        )


def test_unlocks_helper_delegate_failure_returns_none(ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_unlocks_path", fake)
    assert ent.tier_unlocks_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    ) is None


# ─── tier_locks_at_path: helper ───────────────────────────────────────────────


def test_locks_helper_perspective_does_not_shape_rows(ent):
    scalar = ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    for p in _perspectives(ent):
        assert ent.tier_locks_at_path(p, ent.TIER_ENTERPRISE, ent.TIER_OSS) == scalar


def test_locks_helper_trial_accepted_as_perspective(ent):
    assert ent.tier_locks_at_path(
        ent.TIER_TRIAL, ent.TIER_ENTERPRISE, ent.TIER_OSS
    ) == ent.tier_locks_path(ent.TIER_ENTERPRISE, ent.TIER_OSS)


def test_locks_helper_identity_returns_empty_list(ent):
    assert ent.tier_locks_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO
    ) == []


def test_locks_helper_bad_perspective_returns_none(ent):
    assert ent.tier_locks_at_path(
        "bogus", ent.TIER_ENTERPRISE, ent.TIER_OSS
    ) is None


def test_locks_helper_garbage_never_raises(ent):
    assert ent.tier_locks_at_path(None, None, None) is None  # type: ignore[arg-type]
    assert ent.tier_locks_at_path("", "", "") is None


def test_locks_helper_grace_and_enforce_yield_identical(ent, enforced):
    for perspective in _perspectives(ent):
        assert ent.tier_locks_at_path(
            perspective, ent.TIER_ENTERPRISE, ent.TIER_OSS
        ) == enforced.tier_locks_at_path(
            perspective, ent.TIER_ENTERPRISE, ent.TIER_OSS
        )


def test_locks_helper_delegate_failure_returns_none(ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_locks_path", fake)
    assert ent.tier_locks_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE, ent.TIER_OSS
    ) is None


# ─── tier_unlocks_at_path_batch: helper ───────────────────────────────────────


def test_unlocks_batch_helper_returns_envelope(ent):
    out = ent.tier_unlocks_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE],
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"tiers", "unknown"}
    for row in out["tiers"]:
        assert set(row.keys()) == _BATCH_ITEM_KEYS


def test_unlocks_batch_helper_byte_equal_to_scalar_batch(ent):
    """Each row in the batch what-if envelope is byte-identical to the
    matching current-perspective batch envelope -- the perspective does
    not shape rows."""
    targets = [ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    scalar_batch = ent.tier_unlocks_path_batch(ent.TIER_OSS, targets)
    for p in _perspectives(ent):
        assert ent.tier_unlocks_at_path_batch(p, ent.TIER_OSS, targets) == scalar_batch


def test_unlocks_batch_helper_unknown_id_bucketed(ent):
    out = ent.tier_unlocks_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, "bogus_id"],
    )
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_CLOUD_STARTER]
    assert out["unknown"] == ["bogus_id"]


def test_unlocks_batch_helper_bad_perspective_returns_none(ent):
    assert ent.tier_unlocks_at_path_batch(
        "bogus", ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    ) is None


def test_unlocks_batch_helper_bad_from_returns_none(ent):
    """A bad ``from_tier`` propagates via the scalar delegate."""
    assert ent.tier_unlocks_at_path_batch(
        ent.TIER_CLOUD_PRO, "bogus", [ent.TIER_ENTERPRISE]
    ) is None


def test_unlocks_batch_helper_garbage_never_raises(ent):
    assert ent.tier_unlocks_at_path_batch(None, None, None) is None  # type: ignore[arg-type]
    assert ent.tier_unlocks_at_path_batch("", "", []) is None


def test_unlocks_batch_helper_delegate_failure_returns_none(ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_unlocks_path_batch", fake)
    assert ent.tier_unlocks_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, [ent.TIER_ENTERPRISE]
    ) is None


def test_unlocks_batch_helper_grace_and_enforce_identical(ent, enforced):
    targets = [ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE]
    for perspective in _perspectives(ent):
        assert ent.tier_unlocks_at_path_batch(
            perspective, ent.TIER_OSS, targets
        ) == enforced.tier_unlocks_at_path_batch(
            perspective, ent.TIER_OSS, targets
        )


# ─── tier_locks_at_path_batch: helper ─────────────────────────────────────────


def test_locks_batch_helper_byte_equal_to_scalar_batch(ent):
    targets = [ent.TIER_PRO, ent.TIER_CLOUD_STARTER, ent.TIER_OSS]
    scalar_batch = ent.tier_locks_path_batch(ent.TIER_ENTERPRISE, targets)
    for p in _perspectives(ent):
        assert ent.tier_locks_at_path_batch(
            p, ent.TIER_ENTERPRISE, targets
        ) == scalar_batch


def test_locks_batch_helper_unknown_id_bucketed(ent):
    out = ent.tier_locks_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
        [ent.TIER_OSS, "bogus_id"],
    )
    assert [row["to"] for row in out["tiers"]] == [ent.TIER_OSS]
    assert out["unknown"] == ["bogus_id"]


def test_locks_batch_helper_bad_perspective_returns_none(ent):
    assert ent.tier_locks_at_path_batch(
        "bogus", ent.TIER_ENTERPRISE, [ent.TIER_OSS]
    ) is None


def test_locks_batch_helper_delegate_failure_returns_none(ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_locks_path_batch", fake)
    assert ent.tier_locks_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE, [ent.TIER_OSS]
    ) is None


# ─── HTTP /api/entitlement/tier-unlocks-at-path ───────────────────────────────


def test_http_unlocks_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS


def test_http_unlocks_path_matches_helper(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    )
    body = r.get_json()
    assert body["path"] == ent.tier_unlocks_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE
    )


def test_http_unlocks_direction_upgrade(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    )
    assert r.get_json()["direction"] == "upgrade"


def test_http_unlocks_direction_identity(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier={ent.TIER_OSS}"
        f"&from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO}"
    )
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_http_unlocks_missing_tier_400(client):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path?from=oss&to=enterprise"
    )
    assert r.status_code == 400


def test_http_unlocks_missing_from_400(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 400


def test_http_unlocks_missing_to_400(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
    )
    assert r.status_code == 400


def test_http_unlocks_bad_perspective_404(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier=bogus&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "tier"


def test_http_unlocks_bad_from_404(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from=bogus&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "from"


def test_http_unlocks_bad_to_404(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}&to=bogus"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "to"


def test_http_unlocks_trial_perspective_accepted(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier={ent.TIER_TRIAL}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200


def test_http_unlocks_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_unlocks_at_path", fake)
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code < 500


# ─── HTTP /api/entitlement/tier-locks-at-path ─────────────────────────────────


def test_http_locks_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS


def test_http_locks_path_matches_helper(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS}"
    )
    assert r.get_json()["path"] == ent.tier_locks_at_path(
        ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE, ent.TIER_OSS
    )


def test_http_locks_direction_downgrade(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS}"
    )
    assert r.get_json()["direction"] == "downgrade"


def test_http_locks_missing_args_400(client, ent):
    for qs in (
        "",
        f"?tier={ent.TIER_CLOUD_PRO}",
        f"?from={ent.TIER_ENTERPRISE}",
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_ENTERPRISE}",
        f"?tier={ent.TIER_CLOUD_PRO}&to={ent.TIER_OSS}",
    ):
        r = client.get(f"/api/entitlement/tier-locks-at-path{qs}")
        assert r.status_code == 400, qs


def test_http_locks_bad_ids_404(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-at-path"
        f"?tier=bogus&from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "tier"


def test_http_locks_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_locks_at_path", fake)
    r = client.get(
        "/api/entitlement/tier-locks-at-path"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code < 500


# ─── HTTP /api/entitlement/tier-unlocks-at-path-batch ─────────────────────────


def test_http_unlocks_batch_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _BATCH_ENVELOPE_KEYS


def test_http_unlocks_batch_body_matches_helper(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO},{ent.TIER_ENTERPRISE}"
    )
    body = r.get_json()
    helper = ent.tier_unlocks_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        [ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE],
    )
    assert body["tiers"] == helper["tiers"]
    assert body["unknown"] == helper["unknown"]


def test_http_unlocks_batch_missing_tier_400(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 400


def test_http_unlocks_batch_missing_from_400(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 400


def test_http_unlocks_batch_empty_to_400(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
    )
    assert r.status_code == 400


def test_http_unlocks_batch_bad_perspective_404(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path-batch"
        f"?tier=bogus&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "tier"


def test_http_unlocks_batch_bad_from_404(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from=bogus&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "from"


def test_http_unlocks_batch_unknown_to_bucketed_200(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_OSS}"
        f"&to={ent.TIER_CLOUD_STARTER},bogus_id"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["to"] for row in body["tiers"]] == [ent.TIER_CLOUD_STARTER]
    assert body["unknown"] == ["bogus_id"]


def test_http_unlocks_batch_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_unlocks_at_path_batch", fake)
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code < 500


def test_http_unlocks_batch_trial_accepted(client, ent):
    r = client.get(
        "/api/entitlement/tier-unlocks-at-path-batch"
        f"?tier={ent.TIER_TRIAL}"
        f"&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE},{ent.TIER_TRIAL}"
    )
    assert r.status_code == 200


# ─── HTTP /api/entitlement/tier-locks-at-path-batch ───────────────────────────


def test_http_locks_batch_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_PRO},{ent.TIER_OSS}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _BATCH_ENVELOPE_KEYS


def test_http_locks_batch_body_matches_helper(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_PRO},{ent.TIER_CLOUD_STARTER},{ent.TIER_OSS}"
    )
    body = r.get_json()
    helper = ent.tier_locks_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
        [ent.TIER_PRO, ent.TIER_CLOUD_STARTER, ent.TIER_OSS],
    )
    assert body["tiers"] == helper["tiers"]
    assert body["unknown"] == helper["unknown"]


def test_http_locks_batch_missing_args_400(client, ent):
    for qs in (
        "",
        f"?tier={ent.TIER_CLOUD_PRO}",
        f"?from={ent.TIER_ENTERPRISE}",
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_ENTERPRISE}",
    ):
        r = client.get(f"/api/entitlement/tier-locks-at-path-batch{qs}")
        assert r.status_code == 400, qs


def test_http_locks_batch_bad_ids_404(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-at-path-batch"
        f"?tier=bogus&from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "tier"

    r = client.get(
        "/api/entitlement/tier-locks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from=bogus&to={ent.TIER_OSS}"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "from"


def test_http_locks_batch_unknown_to_bucketed_200(client, ent):
    r = client.get(
        "/api/entitlement/tier-locks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}"
        f"&from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS},bogus_id"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["to"] for row in body["tiers"]] == [ent.TIER_OSS]
    assert body["unknown"] == ["bogus_id"]


def test_http_locks_batch_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tier_locks_at_path_batch", fake)
    r = client.get(
        "/api/entitlement/tier-locks-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_ENTERPRISE}&to={ent.TIER_OSS}"
    )
    assert r.status_code < 500
