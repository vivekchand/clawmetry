"""Tests for ``clawmetry.entitlements.lock_reason_path(from, to, item, kind)``
+ the ``GET /api/entitlement/lock-reason-path`` endpoint.

Single-item path-walking sibling of :func:`lock_reason_at` and lock-row
analogue of :func:`feature_spec_path` / :func:`runtime_spec_path`. Lets a
paywall "how does THIS one lock-row evolve as I climb the ladder" UI
render every rung's ``locked`` / ``allowed`` / ``reason`` sentence off
ONE round-trip without fetching the full
:func:`lock_reasons_at_batch` payload at every rung.

Pins:

* rung walk byte-stable against :func:`tier_path`,
  :func:`tier_spec_path`, :func:`capacity_diff_path`,
  :func:`tier_unlocks_path`, :func:`tier_locks_path`,
  :func:`preview_path`, :func:`feature_spec_path` and
  :func:`runtime_spec_path` (same ``_PURCHASABLE_TIERS`` filter + same
  sort + same destination-sibling exclusion)
* per-rung row carries the 8-key ``_lock_row`` body PLUS the three
  rung-identification keys (``rung``, ``rung_label``, ``rung_rank``);
  dropping the three ``rung*`` keys yields exact byte-equality with the
  matching axis row of :func:`lock_reasons_at_batch` for the same rung
* paid-feature unlock boundary visible: ``allowed`` flips from
  ``False`` to ``True`` at the rung where the feature's min tier is
  reached; ``reason`` flips from a sentence to ``None``
* free feature surfaces ``allowed=True`` / ``reason=None`` at every
  rung
* enterprise-only feature stays ``allowed=False`` until the enterprise
  rung
* runtime alias normalisation (``claude-code`` -> ``claude_code``)
* capacity axes (``channels`` / ``retention_days`` / ``nodes``)
  resolve against the per-tier caps so e.g. 100 nodes at Enterprise is
  unlocked, not locked
* identity returns ``[]``; lateral returns a single-row path; trial
  accepted as endpoint
* unknown / empty / garbage tier / item ids return ``None`` and never
  raise; non-positive / non-int capacity values return ``None``
* grace vs enforce yields identical rows (helper synthesises a fresh
  ``Entitlement`` per rung with ``grace=False`` regardless of the live
  resolver state)
* API surface: 400 on missing args / no axis / multi-axis; 404 on
  unknown ids; 200 envelope on happy path; alias echo returns canonical
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "key",
    "kind",
    "path",
}

_RUNG_KEYS = {"rung", "rung_label", "rung_rank"}

_ROW_KEYS = {
    "key",
    "kind",
    "reason",
    "locked",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
}


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


# ── helper: shape + invariants ───────────────────────────────────────────────


def test_returns_list(ent):
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_carries_rung_and_lock_keys(ent):
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    for row in path:
        assert set(row).issuperset(_RUNG_KEYS)
        assert set(row).issuperset(_ROW_KEYS)
        assert row["rung_label"] == ent.tier_label(row["rung"])
        assert row["rung_rank"] == ent.tier_rank(row["rung"])


def test_per_rung_byte_equality_with_lock_reasons_at_batch(ent):
    """Dropping the three ``rung*`` keys from a path row yields exact
    byte-equality with the matching axis row of
    :func:`lock_reasons_at_batch` for the same perspective tier."""
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    for row in path:
        body = {k: v for k, v in row.items() if k not in _RUNG_KEYS}
        batch = ent.lock_reasons_at_batch(row["rung"], features=["custom_alerts"])
        assert batch is not None
        assert batch["features"] == [body]


def test_runtime_axis_byte_equality_with_lock_reasons_at_batch(ent):
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code", kind="runtime"
    )
    for row in path:
        body = {k: v for k, v in row.items() if k not in _RUNG_KEYS}
        batch = ent.lock_reasons_at_batch(row["rung"], runtimes=["claude_code"])
        assert batch is not None
        assert batch["runtimes"] == [body]


def test_static_lock_keys_constant_across_rungs_for_paid_feature(ent):
    """The ``key`` / ``kind`` / ``required_tier`` keys describe the item
    itself, not the perspective -- they must NOT vary rung by rung."""
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    static = {"key", "kind", "required_tier", "required_tier_label", "required_tier_rank"}
    first = {k: path[0][k] for k in static}
    for row in path[1:]:
        assert {k: row[k] for k in static} == first


def test_first_row_is_first_step_above_from(ent):
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    assert path[0]["rung"] == ent.TIER_CLOUD_STARTER


def test_last_row_is_destination(ent):
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    assert path[-1]["rung"] == ent.TIER_ENTERPRISE


def test_rung_walk_byte_stable_against_feature_spec_path(ent):
    """Rung ids must match :func:`feature_spec_path`'s rung ids
    byte-for-byte -- same ``_PURCHASABLE_TIERS`` filter + same sort +
    same destination-sibling exclusion."""
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_CLOUD_FREE, ent.TIER_PRO),
        (ent.TIER_OSS, ent.TIER_CLOUD_PRO),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_PRO, ent.TIER_CLOUD_FREE),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        lock_rungs = [
            r["rung"]
            for r in ent.lock_reason_path(f, t, "custom_alerts", kind="feature")
        ]
        feat_rungs = [
            r["rung"] for r in ent.feature_spec_path(f, t, "custom_alerts")
        ]
        assert lock_rungs == feat_rungs


def test_rung_walk_byte_stable_against_tier_path(ent):
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        lock_rungs = [
            r["rung"]
            for r in ent.lock_reason_path(f, t, "custom_alerts", kind="feature")
        ]
        diff_rungs = [r["to"] for r in ent.tier_path(f, t)]
        assert lock_rungs == diff_rungs


def test_rung_walk_invariant_across_items_and_axes(ent):
    """The walked rung sequence is item- and axis-agnostic -- swapping
    the feature / runtime / channels query must not move the rungs."""
    a = [
        r["rung"]
        for r in ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
        )
    ]
    b = [
        r["rung"]
        for r in ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code", kind="runtime"
        )
    ]
    c = [
        r["rung"]
        for r in ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "10", kind="channels"
        )
    ]
    assert a == b == c


# ── unlock boundary semantics ────────────────────────────────────────────────


def test_paid_feature_unlock_boundary_visible(ent):
    """``custom_alerts`` is a Pro-only feature -- ``allowed`` flips
    from ``False`` to ``True`` exactly at the cloud_pro rung; ``reason``
    flips from a sentence to ``None``."""
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    by_rung = {row["rung"]: row for row in path}
    assert by_rung[ent.TIER_CLOUD_STARTER]["allowed"] is False
    assert by_rung[ent.TIER_CLOUD_STARTER]["locked"] is True
    assert isinstance(by_rung[ent.TIER_CLOUD_STARTER]["reason"], str)
    for rung in (ent.TIER_CLOUD_PRO, ent.TIER_PRO, ent.TIER_ENTERPRISE):
        assert by_rung[rung]["allowed"] is True
        assert by_rung[rung]["locked"] is False
        assert by_rung[rung]["reason"] is None


def test_free_feature_allowed_at_every_rung(ent):
    """``sessions`` is a free feature -- ``allowed`` is ``True`` and
    ``reason`` is ``None`` at every walked rung."""
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "sessions", kind="feature"
    )
    for row in path:
        assert row["allowed"] is True
        assert row["locked"] is False
        assert row["reason"] is None


def test_enterprise_only_feature_locked_until_enterprise(ent):
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "siem_export", kind="feature"
    )
    by_rung = {row["rung"]: row for row in path}
    for rung in (ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_PRO):
        assert by_rung[rung]["allowed"] is False
        assert by_rung[rung]["locked"] is True
    assert by_rung[ent.TIER_ENTERPRISE]["allowed"] is True
    assert by_rung[ent.TIER_ENTERPRISE]["reason"] is None


def test_free_runtime_allowed_at_every_rung(ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, rt, kind="runtime"
    )
    for row in path:
        assert row["allowed"] is True
        assert row["reason"] is None


def test_paid_runtime_locked_below_starter(ent):
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code", kind="runtime"
    )
    by_rung = {row["rung"]: row for row in path}
    for rung in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        assert by_rung[rung]["allowed"] is True
        assert by_rung[rung]["reason"] is None


def test_runtime_alias_canonicalised_in_row_key(ent):
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude-code", kind="runtime"
    )
    assert path is not None and path
    for row in path:
        assert row["key"] == "claude_code"


# ── capacity axes ────────────────────────────────────────────────────────────


def test_channels_axis_unlock_boundary(ent):
    """At Enterprise (unlimited channels), 100 channels is allowed; at
    OSS the same count exceeds the free cap."""
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "100", kind="channels"
    )
    assert path is not None and path
    # destination Enterprise must be allowed
    last = path[-1]
    assert last["rung"] == ent.TIER_ENTERPRISE
    assert last["allowed"] is True
    assert last["reason"] is None


def test_nodes_axis_unlock_boundary(ent):
    """At Enterprise (typically high node cap), 100 nodes is allowed
    even though OSS caps at 1 node."""
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "100", kind="nodes"
    )
    assert path is not None and path
    last = path[-1]
    assert last["rung"] == ent.TIER_ENTERPRISE
    assert last["allowed"] is True


def test_capacity_non_positive_returns_none(ent):
    assert (
        ent.lock_reason_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "0", kind="channels")
        is None
    )
    assert (
        ent.lock_reason_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "-5", kind="nodes")
        is None
    )


def test_capacity_non_int_returns_none(ent):
    assert (
        ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "bogus", kind="channels"
        )
        is None
    )


# ── kind inference ───────────────────────────────────────────────────────────


def test_kind_none_infers_feature(ent):
    a = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind=None
    )
    b = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    assert a == b


def test_kind_none_infers_runtime(ent):
    a = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code", kind=None
    )
    b = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "claude_code", kind="runtime"
    )
    assert a == b


def test_kind_none_on_unknown_item_returns_none(ent):
    assert (
        ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "not_a_real_item", kind=None
        )
        is None
    )


# ── direction semantics ──────────────────────────────────────────────────────


def test_ascending_walk_is_non_decreasing_in_rank(ent):
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    ranks = [row["rung_rank"] for row in path]
    assert ranks == sorted(ranks)


def test_descending_walk_is_non_increasing_in_rank(ent):
    path = ent.lock_reason_path(
        ent.TIER_ENTERPRISE, ent.TIER_OSS, "custom_alerts", kind="feature"
    )
    ranks = [row["rung_rank"] for row in path]
    assert ranks == sorted(ranks, reverse=True)


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2 -- the path must end at
    ``pro`` and exclude the same-rank sibling."""
    rungs = [
        r["rung"]
        for r in ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_PRO, "custom_alerts", kind="feature"
        )
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
        assert (
            ent.lock_reason_path(tid, tid, "custom_alerts", kind="feature") == []
        )


def test_lateral_single_row(ent):
    path = ent.lock_reason_path(
        ent.TIER_CLOUD_PRO, ent.TIER_PRO, "custom_alerts", kind="feature"
    )
    assert len(path) == 1
    assert path[0]["rung"] == ent.TIER_PRO


def test_trial_endpoint_via_lateral(ent):
    path = ent.lock_reason_path(
        ent.TIER_CLOUD_PRO, ent.TIER_TRIAL, "custom_alerts", kind="feature"
    )
    assert len(path) == 1
    assert path[0]["rung"] == ent.TIER_TRIAL


def test_trial_excluded_from_walked_intermediate_rungs(ent):
    path = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    for row in path:
        assert row["rung"] != ent.TIER_TRIAL


# ── unknown / empty / garbage inputs ─────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    assert (
        ent.lock_reason_path(
            "not_a_tier", ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
        )
        is None
    )
    assert (
        ent.lock_reason_path(
            ent.TIER_OSS, "still_not", "custom_alerts", kind="feature"
        )
        is None
    )


def test_unknown_feature_returns_none(ent):
    assert (
        ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "not_a_feature", kind="feature"
        )
        is None
    )


def test_unknown_runtime_returns_none(ent):
    assert (
        ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "not_a_runtime", kind="runtime"
        )
        is None
    )


def test_unknown_kind_returns_none(ent):
    assert (
        ent.lock_reason_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="bogus"
        )
        is None
    )


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.lock_reason_path("", "", "", kind="feature") is None
    assert (
        ent.lock_reason_path(None, None, None, kind=None)  # type: ignore[arg-type]
        is None
    )
    assert ent.lock_reason_path("  ", "  ", "  ", kind="feature") is None
    assert (
        ent.lock_reason_path(123, 456, 789, kind="feature")  # type: ignore[arg-type]
        is None
    )


def test_case_and_whitespace_normalised(ent):
    a = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    b = ent.lock_reason_path(
        "  OSS ", " ENTERPRISE  ", "  CUSTOM_ALERTS ", kind="feature"
    )
    assert a == b


# ── resolver-independence ────────────────────────────────────────────────────


def test_grace_and_enforce_yield_identical_rows(ent, monkeypatch):
    grace_rows = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_rows = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    assert grace_rows == enforced_rows


def test_synth_failure_returns_none(ent, monkeypatch):
    """A synthesis failure inside the rung loop must short-circuit the
    whole helper to ``None`` -- never 5xx, never partial rows."""
    monkeypatch.setattr(
        ent,
        "_lock_row",
        lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    result = ent.lock_reason_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "custom_alerts", kind="feature"
    )
    assert result is None


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/lock-reason-path?to=cloud_pro&feature=custom_alerts"
    )
    assert r.status_code == 400


def test_api_400_on_missing_to(client):
    r = client.get(
        "/api/entitlement/lock-reason-path?from=oss&feature=custom_alerts"
    )
    assert r.status_code == 400


def test_api_400_on_no_axis(client):
    r = client.get("/api/entitlement/lock-reason-path?from=oss&to=enterprise")
    assert r.status_code == 400


def test_api_400_on_multi_axis(client):
    r = client.get(
        "/api/entitlement/lock-reason-path?from=oss&to=enterprise"
        "&feature=custom_alerts&runtime=claude_code"
    )
    assert r.status_code == 400


def test_api_404_on_unknown_tier(client):
    r = client.get(
        "/api/entitlement/lock-reason-path?from=oss&to=not_a_tier"
        "&feature=custom_alerts"
    )
    assert r.status_code == 404
    assert r.get_json()["error"] == "unknown tier or item"


def test_api_404_on_unknown_feature(client):
    r = client.get(
        "/api/entitlement/lock-reason-path?from=oss&to=enterprise&feature=bogus"
    )
    assert r.status_code == 404


def test_api_404_on_unknown_runtime(client):
    r = client.get(
        "/api/entitlement/lock-reason-path?from=oss&to=enterprise&runtime=bogus"
    )
    assert r.status_code == 404


def test_api_404_on_unparseable_capacity(client):
    r = client.get(
        "/api/entitlement/lock-reason-path?from=oss&to=enterprise&channels=bogus"
    )
    assert r.status_code == 404


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/lock-reason-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["key"] == "custom_alerts"
    assert body["kind"] == "feature"
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["rung"] == ent.TIER_ENTERPRISE


def test_api_happy_path_descending(client, ent):
    r = client.get(
        f"/api/entitlement/lock-reason-path?from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS}&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["rung"] == ent.TIER_OSS


def test_api_identity_empty_path(client, ent):
    r = client.get(
        f"/api/entitlement/lock-reason-path?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO}&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        f"/api/entitlement/lock-reason-path?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_PRO}&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["rung"] == ent.TIER_PRO


def test_api_runtime_alias_echoed_canonical(client):
    r = client.get(
        "/api/entitlement/lock-reason-path?from=oss&to=enterprise"
        "&runtime=claude-code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["key"] == "claude_code"
    assert body["kind"] == "runtime"
    for row in body["path"]:
        assert row["key"] == "claude_code"


def test_api_channels_axis(client, ent):
    r = client.get(
        f"/api/entitlement/lock-reason-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=10"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["kind"] == "channels"
    assert body["key"] == "10"
    assert body["path"]


def test_api_rungs_match_feature_spec_path_route(client, ent):
    """API-level byte-equality: rung ids from ``/lock-reason-path`` match
    rung ids from ``/feature-spec-path`` on the same axis-and-endpoint
    bundle."""
    a = client.get(
        f"/api/entitlement/lock-reason-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&feature=custom_alerts"
    ).get_json()
    b = client.get(
        f"/api/entitlement/feature-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&feature=custom_alerts"
    ).get_json()
    assert [r["rung"] for r in a["path"]] == [r["rung"] for r in b["path"]]
