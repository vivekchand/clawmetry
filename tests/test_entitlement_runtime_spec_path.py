"""Tests for ``clawmetry.entitlements.runtime_spec_path(from, to, runtime)``
+ the ``GET /api/entitlement/runtime-spec-path`` endpoint.

Runtime-axis twin of :func:`feature_spec_path` -- the single-runtime
sibling of :func:`tier_spec_path` and perspective-walked sibling of
:func:`runtime_spec_at`. Lets a paywall "how does THIS one runtime
unlock as I climb the ladder" UI render every rung's ``allowed`` /
``locked`` / ``entitled`` status off ONE round-trip without fetching
the full :func:`runtime_catalog_at` at every rung.

Pins:

* rung walk byte-stable against :func:`tier_path`,
  :func:`tier_spec_path`, :func:`feature_spec_path`,
  :func:`capacity_diff_path`, :func:`tier_unlocks_path`,
  :func:`tier_locks_path` and :func:`preview_path`
* per-rung row carries the singular :func:`runtime_spec_at` body PLUS
  the three rung-identification keys (``rung``, ``rung_label``,
  ``rung_rank``); dropping the three ``rung*`` keys yields exact
  byte-equality with :func:`runtime_spec_at(rung, runtime)`
* free runtime (``openclaw``) surfaces ``allowed=True`` at every rung
* paid runtime (``claude_code``) flips from ``False`` to ``True`` at
  the rung where the runtime becomes allowed
* runtime alias (``claude-code``) resolves to ``claude_code``
* identity returns ``[]``
* lateral (same rank, different id) returns a single-row path
* trial accepted as an endpoint (lateral branch for ``to=trial``;
  ``from=trial`` walks intermediate rungs above)
* unknown / empty / garbage tier or runtime ids return ``None`` and
  never raise
* grace vs enforce yields identical rows (helper walks the static
  per-tier maps via :func:`runtime_spec_at`)
* API surface: 400 on missing args, 404 on unknown ids, 200 envelope
  on happy path (incl. direction tag and ``runtime`` echo with the
  canonical id, not the alias)
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


_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "runtime",
    "path",
}

_RUNG_KEYS = {"rung", "rung_label", "rung_rank"}


# ── helper-level: shape + invariants ─────────────────────────────────────────


def test_returns_list(ent):
    path = ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code")
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_carries_rung_keys(ent):
    path = ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code")
    for row in path:
        assert set(row).issuperset(_RUNG_KEYS)
        assert row["rung_label"] == ent.tier_label(row["rung"])
        assert row["rung_rank"] == ent.tier_rank(row["rung"])


def test_per_rung_byte_equality_with_singular_runtime_spec_at(ent):
    """Dropping the three ``rung*`` keys yields exact byte-equality with
    :func:`runtime_spec_at(rung, runtime)`."""
    path = ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code")
    for row in path:
        body = {k: v for k, v in row.items() if k not in _RUNG_KEYS}
        direct = ent.runtime_spec_at(row["rung"], "claude_code")
        assert body == direct


def test_static_runtime_property_keys_constant_across_rungs(ent):
    path = ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code")
    static = {"id", "label", "tier", "tiers", "free"}
    first = {k: path[0][k] for k in static}
    for row in path[1:]:
        assert {k: row[k] for k in static} == first


def test_rung_walk_byte_stable_against_tier_spec_path(ent):
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        rt_rungs = [
            r["rung"] for r in ent.runtime_spec_path(f, t, "claude_code")
        ]
        spec_rungs = [r["id"] for r in ent.tier_spec_path(f, t)]
        assert rt_rungs == spec_rungs


def test_rung_walk_byte_stable_against_feature_spec_path(ent):
    """Cross-axis byte-stability: feature_spec_path and
    runtime_spec_path must walk the same rungs."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
    ):
        rt_rungs = [
            r["rung"] for r in ent.runtime_spec_path(f, t, "claude_code")
        ]
        feat_rungs = [
            r["rung"] for r in ent.feature_spec_path(f, t, "custom_alerts")
        ]
        assert rt_rungs == feat_rungs


def test_rung_walk_invariant_across_runtimes(ent):
    """The walked rung sequence is runtime-agnostic -- swapping the
    runtime must not move the rungs."""
    a = [
        r["rung"]
        for r in ent.runtime_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code"
        )
    ]
    b = [
        r["rung"]
        for r in ent.runtime_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "openclaw"
        )
    ]
    c = [
        r["rung"]
        for r in ent.runtime_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "codex"
        )
    ]
    assert a == b == c


def test_free_runtime_allowed_at_every_rung(ent):
    """``openclaw`` is in :data:`FREE_RUNTIMES` -- ``allowed`` must be
    ``True`` at every walked rung."""
    path = ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "openclaw")
    for row in path:
        assert row["allowed"] is True
        assert row["locked"] is False
        assert row["entitled"] is True
        assert row["free"] is True


def test_paid_runtime_unlock_boundary_visible(ent):
    """``claude_code`` is a paid runtime -- ``allowed`` is ``False`` at
    the free / oss rung and ``True`` at every purchasable rung that
    unlocks paid runtimes (cloud_starter, cloud_pro, pro, enterprise)."""
    path = ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code")
    for row in path:
        if row["rung"] in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
            assert row["allowed"] is False
        else:
            assert row["allowed"] is True


def test_runtime_alias_resolves(ent):
    """``claude-code`` (alias) must resolve to ``claude_code`` and
    produce a path byte-identical to the canonical id."""
    aliased = ent.runtime_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude-code"
    )
    canonical = ent.runtime_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code"
    )
    assert aliased == canonical


def test_ascending_walk_is_non_decreasing_in_rank(ent):
    path = ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code")
    walk_ranks = [row["rung_rank"] for row in path]
    assert walk_ranks == sorted(walk_ranks)


def test_descending_walk_is_non_increasing_in_rank(ent):
    path = ent.runtime_spec_path(ent.TIER_ENTERPRISE, ent.TIER_OSS, "claude_code")
    walk_ranks = [row["rung_rank"] for row in path]
    assert walk_ranks == sorted(walk_ranks, reverse=True)


def test_path_terminates_at_to_not_a_sibling(ent):
    rungs = [
        r["rung"]
        for r in ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_PRO, "claude_code")
    ]
    assert rungs[-1] == ent.TIER_PRO
    assert ent.TIER_CLOUD_PRO not in rungs


def test_identity_returns_empty(ent):
    for tid in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        assert ent.runtime_spec_path(tid, tid, "claude_code") == []


def test_lateral_single_row(ent):
    path = ent.runtime_spec_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO, "claude_code")
    assert len(path) == 1
    assert path[0]["rung"] == ent.TIER_PRO


def test_trial_endpoint_via_lateral(ent):
    path = ent.runtime_spec_path(ent.TIER_CLOUD_PRO, ent.TIER_TRIAL, "claude_code")
    assert len(path) == 1
    assert path[0]["rung"] == ent.TIER_TRIAL


def test_trial_excluded_from_walked_intermediate_rungs(ent):
    path = ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code")
    for row in path:
        assert row["rung"] != ent.TIER_TRIAL


def test_unknown_tier_returns_none(ent):
    assert (
        ent.runtime_spec_path("not_a_tier", ent.TIER_ENTERPRISE, "claude_code")
        is None
    )
    assert (
        ent.runtime_spec_path(ent.TIER_OSS, "still_not", "claude_code") is None
    )


def test_unknown_runtime_returns_none(ent):
    assert (
        ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "not_a_runtime")
        is None
    )
    assert ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.runtime_spec_path("", "", "") is None
    assert ent.runtime_spec_path(None, None, None) is None  # type: ignore[arg-type]
    assert ent.runtime_spec_path("  ", "  ", "  ") is None
    assert ent.runtime_spec_path(123, 456, 789) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.runtime_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code")
    b = ent.runtime_spec_path("  OSS ", " ENTERPRISE  ", "  CLAUDE_CODE ")
    assert a == b


def test_grace_and_enforce_yield_identical_rows(ent, monkeypatch):
    grace_rows = ent.runtime_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_rows = ent.runtime_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code"
    )
    assert grace_rows == enforced_rows


def test_resolver_failure_returns_none(ent, monkeypatch):
    monkeypatch.setattr(
        ent,
        "runtime_spec_at",
        lambda _t, _r: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    result = ent.runtime_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code"
    )
    assert result is None


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/runtime-spec-path?to=cloud_pro&runtime=claude_code"
    )
    assert r.status_code == 400


def test_api_400_on_missing_to(client):
    r = client.get(
        "/api/entitlement/runtime-spec-path?from=oss&runtime=claude_code"
    )
    assert r.status_code == 400


def test_api_400_on_missing_runtime(client):
    r = client.get("/api/entitlement/runtime-spec-path?from=oss&to=enterprise")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "missing runtime"


def test_api_404_on_unknown_tier(client):
    r = client.get(
        "/api/entitlement/runtime-spec-path?from=oss&to=not_a_tier&runtime=claude_code"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier or runtime"


def test_api_404_on_unknown_runtime(client):
    r = client.get(
        "/api/entitlement/runtime-spec-path?from=oss&to=enterprise&runtime=bogus"
    )
    assert r.status_code == 404


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/runtime-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&runtime=claude_code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["runtime"] == "claude_code"
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["rung"] == ent.TIER_ENTERPRISE


def test_api_happy_path_descending(client, ent):
    r = client.get(
        f"/api/entitlement/runtime-spec-path?from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS}&runtime=claude_code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["rung"] == ent.TIER_OSS


def test_api_identity_empty_path(client, ent):
    r = client.get(
        f"/api/entitlement/runtime-spec-path?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO}&runtime=claude_code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        f"/api/entitlement/runtime-spec-path?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_PRO}&runtime=claude_code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["rung"] == ent.TIER_PRO


def test_api_alias_echoes_canonical_id(client, ent):
    """``runtime=claude-code`` (alias) must echo the canonical
    ``claude_code`` in the envelope -- mirrors the
    ``/api/entitlement/required-tier`` and ``/runtime-spec-at`` behaviour."""
    r = client.get(
        f"/api/entitlement/runtime-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&runtime=claude-code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["runtime"] == "claude_code"


def test_api_rungs_match_tier_spec_path_route(client, ent):
    a = client.get(
        f"/api/entitlement/runtime-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&runtime=claude_code"
    ).get_json()
    b = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    assert [r["rung"] for r in a["path"]] == [r["id"] for r in b["path"]]
