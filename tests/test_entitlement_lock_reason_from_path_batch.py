"""Tests for ``lock_reason_from_path_batch`` / ``lock_reasons_from_path_batch``
plus their HTTP endpoints.

Mirror-direction siblings of ``lock_reason_path`` /
``lock_reason_path_batch`` on the source axis. Where the scalar path
helpers fix ONE ``(from, to)`` pair (and one item, or a matrix of
items), these fix the destination + item(s) and fan out over a
caller-supplied set of SOURCE tiers. Source-axis lock-row companions
of ``tier_unlocks_from_path_batch`` / ``tier_locks_from_path_batch``
(marginal grants / losses) and ``preview_from_path_batch`` /
``capacity_diff_from_path_batch`` (cumulative state / capacity slice).

Each per-source ``path`` must be byte-identical to the matching
``lock_reason_path`` payload for the same ``(from, to, item, kind)``
tuple; each per-source ``matrix`` must be byte-identical to the
matching ``lock_reason_path_batch`` payload for the same
``(from, to, features, runtimes, channels, retention_days, nodes)``
tuple -- pinned by the parity tests below so the scalar-batch and
source-batch multi-axis helpers cannot drift.

Coverage:

* helper envelope + per-row shape for both scalars
* per-source ``path`` byte-equal to ``lock_reason_path`` for the same
  ``(from, to, item, kind)`` (parity anchor)
* per-source ``matrix`` byte-equal to ``lock_reason_path_batch`` for
  the same ``(from, to, features, runtimes, channels, retention_days,
  nodes)`` (multi-axis parity anchor)
* per-source ``direction`` derived from tier ranks relative to the
  shared ``to`` (upgrade / downgrade / lateral / identity)
* input normalised (whitespace stripped, lowercased, duplicates
  dropped, first-seen order preserved) for both source csv and item
  bundles
* unknown source ids echoed in the outer ``unknown[]`` instead of
  short-circuiting the whole batch
* unknown item ids collapse the single-item helper to ``None``
  (whole-batch failure, matches the scalar's short-circuit) but land
  in the per-source ``matrix.unknown`` for the multi-axis helper
* identity ``from == to`` yields a row whose ``path`` is ``[]``
* lateral (same rank, different id) yields a row whose ``path`` has
  one step
* ``trial`` accepted as a source
* runtime aliases accepted (``claude-code`` -> ``claude_code``)
* capacity axes require an explicit ``kind`` on the single-item
  helper; non-int / non-positive collapses to ``None`` (helper) /
  404 (HTTP)
* helpers never raise -- per-source failures short-circuit that id
  into ``unknown[]`` and the rest of the batch keeps building
* HTTP endpoints 400 on missing / empty input / missing axis / two
  axes (single-item), 404 on unknown destination / unknown item,
  never 5xx on a helper failure
* grace vs enforce yields byte-identical rows across the whole
  envelope (resolver-independence)
"""
from __future__ import annotations

import importlib

import pytest


_ITEM_KEYS = {"from", "from_label", "from_rank", "direction", "path"}
_MATRIX_ITEM_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "direction",
    "matrix",
}
_HELPER_ENVELOPE_KEYS = {"tiers", "unknown"}
_HTTP_SCALAR_ENVELOPE_KEYS = {
    "to",
    "to_label",
    "to_rank",
    "key",
    "kind",
    "tiers",
    "unknown",
}
_HTTP_MATRIX_ENVELOPE_KEYS = {
    "to",
    "to_label",
    "to_rank",
    "tiers",
    "unknown",
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
    from flask import Flask
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── lock_reason_from_path_batch: helper-level ────────────────────────────────


def test_single_helper_returns_dict_shape(ent):
    out = ent.lock_reason_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER],
        ent.TIER_ENTERPRISE,
        "sso",
        kind="feature",
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_ENVELOPE_KEYS
    assert isinstance(out["tiers"], list)
    assert isinstance(out["unknown"], list)


def test_single_helper_each_row_carries_expected_keys(ent):
    out = ent.lock_reason_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER],
        ent.TIER_ENTERPRISE,
        "sso",
        kind="feature",
    )
    for row in out["tiers"]:
        assert set(row.keys()) == _ITEM_KEYS
        assert isinstance(row["from"], str)
        assert isinstance(row["from_label"], str)
        assert isinstance(row["from_rank"], int)
        assert row["direction"] in {
            "upgrade",
            "downgrade",
            "lateral",
            "identity",
        }
        assert isinstance(row["path"], list)


def test_single_helper_per_row_path_byte_equal_to_scalar(ent):
    """Pin: per-source ``path`` is byte-identical to the scalar
    :func:`lock_reason_path` payload for the same
    ``(from, to, item, kind)`` tuple."""
    sources = [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO]
    out = ent.lock_reason_from_path_batch(
        sources, ent.TIER_ENTERPRISE, "sso", kind="feature"
    )
    by_id = {row["from"]: row["path"] for row in out["tiers"]}
    for fid in sources:
        assert by_id[fid] == ent.lock_reason_path(
            fid, ent.TIER_ENTERPRISE, "sso", kind="feature"
        )


def test_single_helper_per_row_matches_runtime_axis(ent):
    sources = [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO]
    out = ent.lock_reason_from_path_batch(
        sources, ent.TIER_ENTERPRISE, "claude_code", kind="runtime"
    )
    by_id = {row["from"]: row["path"] for row in out["tiers"]}
    for fid in sources:
        assert by_id[fid] == ent.lock_reason_path(
            fid, ent.TIER_ENTERPRISE, "claude_code", kind="runtime"
        )


def test_single_helper_per_row_matches_capacity_axis(ent):
    sources = [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO]
    out = ent.lock_reason_from_path_batch(
        sources, ent.TIER_ENTERPRISE, 50, kind="channels"
    )
    by_id = {row["from"]: row["path"] for row in out["tiers"]}
    for fid in sources:
        assert by_id[fid] == ent.lock_reason_path(
            fid, ent.TIER_ENTERPRISE, 50, kind="channels"
        )


def test_single_helper_direction_matches_ranks(ent):
    """Direction is derived per source relative to the shared ``to``."""
    sources = [
        ent.TIER_OSS,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.lock_reason_from_path_batch(
        sources, ent.TIER_CLOUD_PRO, "sso", kind="feature"
    )
    by_id = {row["from"]: row["direction"] for row in out["tiers"]}
    assert by_id[ent.TIER_OSS] == "upgrade"
    assert by_id[ent.TIER_CLOUD_PRO] == "identity"
    assert by_id[ent.TIER_PRO] == "lateral"
    assert by_id[ent.TIER_ENTERPRISE] == "downgrade"


def test_single_helper_supply_order_preserved(ent):
    sources = [ent.TIER_ENTERPRISE, ent.TIER_CLOUD_STARTER, ent.TIER_OSS]
    out = ent.lock_reason_from_path_batch(
        sources, ent.TIER_CLOUD_PRO, "sso", kind="feature"
    )
    assert [row["from"] for row in out["tiers"]] == sources


def test_single_helper_normalises_input(ent):
    out = ent.lock_reason_from_path_batch(
        ["  CLOUD_STARTER  ", "cloud_pro", "cloud_starter", ""],
        ent.TIER_ENTERPRISE,
        "sso",
        kind="feature",
    )
    assert [row["from"] for row in out["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ]


def test_single_helper_accepts_csv_string(ent):
    out = ent.lock_reason_from_path_batch(
        "cloud_starter,cloud_pro,oss",
        ent.TIER_ENTERPRISE,
        "sso",
        kind="feature",
    )
    assert [row["from"] for row in out["tiers"]] == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
    ]


def test_single_helper_unknown_source_ids_bucketed(ent):
    out = ent.lock_reason_from_path_batch(
        [ent.TIER_OSS, "bogus_id", "still_bogus"],
        ent.TIER_ENTERPRISE,
        "sso",
        kind="feature",
    )
    assert [row["from"] for row in out["tiers"]] == [ent.TIER_OSS]
    assert set(out["unknown"]) == {"bogus_id", "still_bogus"}


def test_single_helper_identity_row_carries_empty_path(ent):
    out = ent.lock_reason_from_path_batch(
        [ent.TIER_CLOUD_PRO],
        ent.TIER_CLOUD_PRO,
        "sso",
        kind="feature",
    )
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["direction"] == "identity"
    assert out["tiers"][0]["path"] == []


def test_single_helper_lateral_row_has_single_step(ent):
    out = ent.lock_reason_from_path_batch(
        [ent.TIER_PRO],
        ent.TIER_CLOUD_PRO,
        "sso",
        kind="feature",
    )
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["direction"] == "lateral"
    assert len(out["tiers"][0]["path"]) == 1
    assert out["tiers"][0]["path"][0]["rung"] == ent.TIER_CLOUD_PRO


def test_single_helper_trial_accepted_as_source(ent):
    out = ent.lock_reason_from_path_batch(
        [ent.TIER_TRIAL],
        ent.TIER_ENTERPRISE,
        "sso",
        kind="feature",
    )
    assert out["unknown"] == []
    assert len(out["tiers"]) == 1
    assert out["tiers"][0]["from"] == ent.TIER_TRIAL


def test_single_helper_runtime_alias_accepted(ent):
    """Runtime aliases (``claude-code``) resolve via
    :func:`canonical_runtime` -- matches :func:`lock_reason_path`."""
    out = ent.lock_reason_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER],
        ent.TIER_CLOUD_PRO,
        "claude-code",
        kind="runtime",
    )
    assert out is not None
    assert len(out["tiers"]) == 2
    canon = ent.canonical_runtime("claude-code")
    for row in out["tiers"]:
        for path_row in row["path"]:
            assert path_row["key"] == canon


def test_single_helper_unknown_to_returns_none(ent):
    assert (
        ent.lock_reason_from_path_batch(
            [ent.TIER_OSS], "not_a_tier", "sso", kind="feature"
        )
        is None
    )


def test_single_helper_unknown_item_returns_none(ent):
    """A bad item is a whole-batch failure (the whole batch pivots off
    ONE item, so there is no partial-recovery story)."""
    assert (
        ent.lock_reason_from_path_batch(
            [ent.TIER_OSS], ent.TIER_ENTERPRISE, "not_a_feature", kind="feature"
        )
        is None
    )


def test_single_helper_unknown_runtime_returns_none(ent):
    assert (
        ent.lock_reason_from_path_batch(
            [ent.TIER_OSS],
            ent.TIER_ENTERPRISE,
            "not_a_runtime",
            kind="runtime",
        )
        is None
    )


def test_single_helper_bad_capacity_returns_none(ent):
    assert (
        ent.lock_reason_from_path_batch(
            [ent.TIER_OSS], ent.TIER_ENTERPRISE, "abc", kind="channels"
        )
        is None
    )
    assert (
        ent.lock_reason_from_path_batch(
            [ent.TIER_OSS], ent.TIER_ENTERPRISE, 0, kind="channels"
        )
        is None
    )
    assert (
        ent.lock_reason_from_path_batch(
            [ent.TIER_OSS], ent.TIER_ENTERPRISE, -1, kind="channels"
        )
        is None
    )


def test_single_helper_missing_item_returns_none(ent):
    assert (
        ent.lock_reason_from_path_batch(
            [ent.TIER_OSS], ent.TIER_ENTERPRISE, ""
        )
        is None
    )
    assert (
        ent.lock_reason_from_path_batch(
            [ent.TIER_OSS], ent.TIER_ENTERPRISE, None
        )
        is None
    )


def test_single_helper_kind_inferred_when_omitted(ent):
    """When ``kind`` is None the helper auto-detects (feature id in
    :data:`ALL_FEATURES` -> feature; runtime id in
    :data:`ALL_RUNTIMES` -> runtime), matching
    :func:`lock_reason_path`."""
    feats = ent.lock_reason_from_path_batch(
        [ent.TIER_OSS], ent.TIER_ENTERPRISE, "sso"
    )
    with_kind = ent.lock_reason_from_path_batch(
        [ent.TIER_OSS], ent.TIER_ENTERPRISE, "sso", kind="feature"
    )
    assert feats == with_kind

    rt = ent.lock_reason_from_path_batch(
        [ent.TIER_OSS], ent.TIER_ENTERPRISE, "claude_code"
    )
    with_kind = ent.lock_reason_from_path_batch(
        [ent.TIER_OSS], ent.TIER_ENTERPRISE, "claude_code", kind="runtime"
    )
    assert rt == with_kind


def test_single_helper_empty_from_list_yields_empty_envelope(ent):
    out = ent.lock_reason_from_path_batch(
        [], ent.TIER_ENTERPRISE, "sso", kind="feature"
    )
    assert out == {"tiers": [], "unknown": []}


def test_single_helper_garbage_inputs_never_raise(ent):
    assert (
        ent.lock_reason_from_path_batch([], "", "sso", kind="feature") is None
    )
    assert (
        ent.lock_reason_from_path_batch(None, None, "sso", kind="feature")
        is None
    )  # type: ignore[arg-type]
    assert (
        ent.lock_reason_from_path_batch("  ", "  ", "sso", kind="feature")
        is None
    )


def test_single_helper_grace_and_enforce_yield_identical_output(
    ent, monkeypatch
):
    sources = [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO]
    grace = ent.lock_reason_from_path_batch(
        sources, ent.TIER_ENTERPRISE, "sso", kind="feature"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.lock_reason_from_path_batch(
        sources, ent.TIER_ENTERPRISE, "sso", kind="feature"
    )
    assert grace == enforced


def test_single_helper_row_failure_short_circuits_id(ent, monkeypatch):
    real = ent.lock_reason_path

    def fake(f, t, item, *, kind=None):
        if f == ent.TIER_CLOUD_STARTER:
            raise RuntimeError("boom")
        return real(f, t, item, kind=kind)

    monkeypatch.setattr(ent, "lock_reason_path", fake)
    out = ent.lock_reason_from_path_batch(
        [ent.TIER_CLOUD_STARTER, ent.TIER_OSS],
        ent.TIER_ENTERPRISE,
        "sso",
        kind="feature",
    )
    assert [row["from"] for row in out["tiers"]] == [ent.TIER_OSS]
    assert ent.TIER_CLOUD_STARTER in out["unknown"]


# ── lock_reasons_from_path_batch (multi-axis): helper-level ─────────────────


def test_matrix_helper_returns_dict_shape(ent):
    out = ent.lock_reasons_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER],
        ent.TIER_ENTERPRISE,
        features=["sso", "sessions"],
        runtimes=["claude_code"],
        channels=50,
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_ENVELOPE_KEYS


def test_matrix_helper_each_row_carries_expected_keys(ent):
    out = ent.lock_reasons_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER],
        ent.TIER_ENTERPRISE,
        features=["sso"],
    )
    for row in out["tiers"]:
        assert set(row.keys()) == _MATRIX_ITEM_KEYS
        assert row["direction"] in {
            "upgrade",
            "downgrade",
            "lateral",
            "identity",
        }
        assert set(row["matrix"].keys()) == {
            "features",
            "runtimes",
            "channels",
            "retention_days",
            "nodes",
            "unknown",
        }


def test_matrix_helper_per_row_matrix_byte_equal_to_scalar_batch(ent):
    """Pin: per-source ``matrix`` is byte-identical to
    :func:`lock_reason_path_batch` for the same
    ``(from, to, features, runtimes, channels, retention_days, nodes)``
    tuple -- so the source-batch and scalar-batch multi-axis helpers
    cannot drift."""
    sources = [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO]
    features = ["sso", "sessions"]
    runtimes = ["claude_code", "cursor"]
    out = ent.lock_reasons_from_path_batch(
        sources,
        ent.TIER_ENTERPRISE,
        features=features,
        runtimes=runtimes,
        channels=50,
        retention_days=90,
        nodes=5,
    )
    by_id = {row["from"]: row["matrix"] for row in out["tiers"]}
    for fid in sources:
        expected = ent.lock_reason_path_batch(
            fid,
            ent.TIER_ENTERPRISE,
            features=features,
            runtimes=runtimes,
            channels=50,
            retention_days=90,
            nodes=5,
        )
        assert by_id[fid] == expected


def test_matrix_helper_direction_matches_ranks(ent):
    sources = [
        ent.TIER_OSS,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]
    out = ent.lock_reasons_from_path_batch(
        sources, ent.TIER_CLOUD_PRO, features=["sso"]
    )
    by_id = {row["from"]: row["direction"] for row in out["tiers"]}
    assert by_id[ent.TIER_OSS] == "upgrade"
    assert by_id[ent.TIER_CLOUD_PRO] == "identity"
    assert by_id[ent.TIER_PRO] == "lateral"
    assert by_id[ent.TIER_ENTERPRISE] == "downgrade"


def test_matrix_helper_unknown_source_bucketed(ent):
    out = ent.lock_reasons_from_path_batch(
        [ent.TIER_OSS, "bogus_id"],
        ent.TIER_ENTERPRISE,
        features=["sso"],
    )
    assert [row["from"] for row in out["tiers"]] == [ent.TIER_OSS]
    assert out["unknown"] == ["bogus_id"]


def test_matrix_helper_unknown_item_bucketed_per_source(ent):
    """A bad item lands in each per-source ``matrix.unknown`` rather
    than collapsing the whole batch (matches the item-batch behaviour
    of :func:`lock_reason_path_batch`)."""
    out = ent.lock_reasons_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER],
        ent.TIER_ENTERPRISE,
        features=["sso", "not_a_feature"],
    )
    for row in out["tiers"]:
        assert "not_a_feature" in row["matrix"]["unknown"]["features"]
        assert [f["key"] for f in row["matrix"]["features"]] == ["sso"]


def test_matrix_helper_returns_none_when_no_axis_supplied(ent):
    assert (
        ent.lock_reasons_from_path_batch(
            [ent.TIER_OSS], ent.TIER_ENTERPRISE
        )
        is None
    )
    # Non-positive capacity + no other axis still counts as no axis
    assert (
        ent.lock_reasons_from_path_batch(
            [ent.TIER_OSS], ent.TIER_ENTERPRISE, channels=0
        )
        is None
    )


def test_matrix_helper_unknown_to_returns_none(ent):
    assert (
        ent.lock_reasons_from_path_batch(
            [ent.TIER_OSS], "not_a_tier", features=["sso"]
        )
        is None
    )


def test_matrix_helper_identity_row_matrix_still_present(ent):
    """Identity ``from == to`` still returns a per-source matrix (the
    inner ``lock_reason_path_batch`` collapses each path to ``[]`` on
    identity, but the axis rows still hydrate)."""
    out = ent.lock_reasons_from_path_batch(
        [ent.TIER_ENTERPRISE],
        ent.TIER_ENTERPRISE,
        features=["sso"],
    )
    assert len(out["tiers"]) == 1
    row = out["tiers"][0]
    assert row["direction"] == "identity"
    assert row["matrix"]["features"][0]["key"] == "sso"
    assert row["matrix"]["features"][0]["path"] == []


def test_matrix_helper_bundle_reused_across_sources(ent):
    """The feature / runtime bundles are canonicalised once at the top
    so the fan-out cannot exhaust a one-shot iterable on the first
    delegate."""

    def one_shot_features():
        for x in ("sso", "sessions"):
            yield x

    def one_shot_runtimes():
        for x in ("claude_code",):
            yield x

    out = ent.lock_reasons_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO],
        ent.TIER_ENTERPRISE,
        features=one_shot_features(),
        runtimes=one_shot_runtimes(),
    )
    for row in out["tiers"]:
        assert [f["key"] for f in row["matrix"]["features"]] == [
            "sso",
            "sessions",
        ]
        assert [r["key"] for r in row["matrix"]["runtimes"]] == [
            "claude_code"
        ]


def test_matrix_helper_grace_and_enforce_yield_identical_output(
    ent, monkeypatch
):
    sources = [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO]
    grace = ent.lock_reasons_from_path_batch(
        sources,
        ent.TIER_ENTERPRISE,
        features=["sso"],
        runtimes=["claude_code"],
        channels=50,
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.lock_reasons_from_path_batch(
        sources,
        ent.TIER_ENTERPRISE,
        features=["sso"],
        runtimes=["claude_code"],
        channels=50,
    )
    assert grace == enforced


def test_matrix_helper_row_failure_short_circuits_id(ent, monkeypatch):
    real = ent.lock_reason_path_batch

    def fake(f, t, **kw):
        if f == ent.TIER_CLOUD_STARTER:
            raise RuntimeError("boom")
        return real(f, t, **kw)

    monkeypatch.setattr(ent, "lock_reason_path_batch", fake)
    out = ent.lock_reasons_from_path_batch(
        [ent.TIER_CLOUD_STARTER, ent.TIER_OSS],
        ent.TIER_ENTERPRISE,
        features=["sso"],
    )
    assert [row["from"] for row in out["tiers"]] == [ent.TIER_OSS]
    assert ent.TIER_CLOUD_STARTER in out["unknown"]


# ── /api/entitlement/lock-reason-from-path-batch endpoint ────────────────────


def test_http_single_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&feature=sso"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _HTTP_SCALAR_ENVELOPE_KEYS
    assert body["key"] == "sso"
    assert body["kind"] == "feature"


def test_http_single_body_matches_helper(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS},{ent.TIER_CLOUD_STARTER},{ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_ENTERPRISE}&feature=sso"
    )
    body = r.get_json()
    helper = ent.lock_reason_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO],
        ent.TIER_ENTERPRISE,
        "sso",
        kind="feature",
    )
    assert body["tiers"] == helper["tiers"]
    assert body["unknown"] == helper["unknown"]
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["to_rank"] == ent.tier_rank(ent.TIER_ENTERPRISE)
    assert body["to_label"] == ent.tier_label(ent.TIER_ENTERPRISE)


def test_http_single_runtime_alias_canonicalised(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_PRO}&runtime=claude-code"
    )
    body = r.get_json()
    canon = ent.canonical_runtime("claude-code")
    assert body["key"] == canon
    assert body["kind"] == "runtime"


def test_http_single_capacity_axis(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&channels=50"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["kind"] == "channels"
    assert body["key"] == "50"


def test_http_single_missing_to_400(client):
    r = client.get("/api/entitlement/lock-reason-from-path-batch")
    assert r.status_code == 400


def test_http_single_missing_from_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?to={ent.TIER_ENTERPRISE}&feature=sso"
    )
    assert r.status_code == 400


def test_http_single_missing_axis_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 400


def test_http_single_two_axes_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
        "&feature=sso&runtime=claude_code"
    )
    assert r.status_code == 400


def test_http_single_bad_to_404(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS}&to=bogus&feature=sso"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_http_single_bad_feature_404(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&feature=not_a_feature"
    )
    assert r.status_code == 404


def test_http_single_bad_runtime_404(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&runtime=not_a_runtime"
    )
    assert r.status_code == 404


def test_http_single_bad_capacity_404(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&nodes=abc"
    )
    assert r.status_code == 404


def test_http_single_unknown_source_bucketed_200(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS},bogus&to={ent.TIER_ENTERPRISE}&feature=sso"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["from"] for row in body["tiers"]] == [ent.TIER_OSS]
    assert body["unknown"] == ["bogus"]


def test_http_single_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "lock_reason_from_path_batch", fake)
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&feature=sso"
    )
    assert r.status_code < 500


def test_http_single_trial_source_accepted(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-from-path-batch"
        f"?from={ent.TIER_TRIAL}&to={ent.TIER_ENTERPRISE}&feature=sso"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["unknown"] == []
    assert len(body["tiers"]) == 1
    assert body["tiers"][0]["from"] == ent.TIER_TRIAL


# ── /api/entitlement/lock-reasons-from-path-batch endpoint ──────────────────


def test_http_matrix_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/lock-reasons-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&features=sso"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _HTTP_MATRIX_ENVELOPE_KEYS


def test_http_matrix_body_matches_helper(client, ent):
    r = client.get(
        "/api/entitlement/lock-reasons-from-path-batch"
        f"?from={ent.TIER_OSS},{ent.TIER_CLOUD_STARTER}"
        f"&to={ent.TIER_ENTERPRISE}"
        "&features=sso,sessions&runtimes=claude_code&channels=50"
    )
    body = r.get_json()
    helper = ent.lock_reasons_from_path_batch(
        [ent.TIER_OSS, ent.TIER_CLOUD_STARTER],
        ent.TIER_ENTERPRISE,
        features=["sso", "sessions"],
        runtimes=["claude_code"],
        channels=50,
    )
    assert body["tiers"] == helper["tiers"]
    assert body["unknown"] == helper["unknown"]
    assert body["to"] == ent.TIER_ENTERPRISE


def test_http_matrix_missing_to_400(client):
    r = client.get("/api/entitlement/lock-reasons-from-path-batch")
    assert r.status_code == 400


def test_http_matrix_missing_from_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reasons-from-path-batch"
        f"?to={ent.TIER_ENTERPRISE}&features=sso"
    )
    assert r.status_code == 400


def test_http_matrix_missing_axis_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reasons-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
    )
    assert r.status_code == 400


def test_http_matrix_bad_to_404(client, ent):
    r = client.get(
        "/api/entitlement/lock-reasons-from-path-batch"
        f"?from={ent.TIER_OSS}&to=bogus&features=sso"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_http_matrix_unknown_source_bucketed_200(client, ent):
    r = client.get(
        "/api/entitlement/lock-reasons-from-path-batch"
        f"?from={ent.TIER_OSS},bogus&to={ent.TIER_ENTERPRISE}&features=sso"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["from"] for row in body["tiers"]] == [ent.TIER_OSS]
    assert body["unknown"] == ["bogus"]


def test_http_matrix_unknown_item_bucketed_per_source(client, ent):
    r = client.get(
        "/api/entitlement/lock-reasons-from-path-batch"
        f"?from={ent.TIER_OSS},{ent.TIER_CLOUD_STARTER}"
        f"&to={ent.TIER_ENTERPRISE}&features=sso,not_a_feature"
    )
    assert r.status_code == 200
    body = r.get_json()
    for row in body["tiers"]:
        assert "not_a_feature" in row["matrix"]["unknown"]["features"]


def test_http_matrix_never_5xx_on_helper_failure(client, ent, monkeypatch):
    def fake(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "lock_reasons_from_path_batch", fake)
    r = client.get(
        "/api/entitlement/lock-reasons-from-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}&features=sso"
    )
    assert r.status_code < 500


# ── cross-helper parity: the scalar and multi-axis source batches must
#   line up rung-for-rung against their scalar-batch cousins ────────────────


def test_cross_helper_single_axis_matches_matrix_slice(ent):
    """The single-item source batch produces the same per-source ``path``
    a multi-axis source-batch call produces for that same item inside
    its ``matrix.features[]``. Both delegate to the same
    :func:`lock_reason_path`, so the two APIs cannot drift on the
    lock-row body."""
    sources = [ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO]
    single = ent.lock_reason_from_path_batch(
        sources, ent.TIER_ENTERPRISE, "sso", kind="feature"
    )
    matrix = ent.lock_reasons_from_path_batch(
        sources, ent.TIER_ENTERPRISE, features=["sso"]
    )
    single_by = {row["from"]: row["path"] for row in single["tiers"]}
    matrix_by = {
        row["from"]: row["matrix"]["features"][0]["path"]
        for row in matrix["tiers"]
    }
    for fid in sources:
        assert single_by[fid] == matrix_by[fid]
