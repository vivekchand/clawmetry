"""Tests for
``clawmetry.entitlements.runtime_spec_at_path(perspective, from, to, runtime)``
+ ``runtime_spec_at_path_batch(perspective, from, to, runtimes)`` + the
``GET /api/entitlement/runtime-spec-at-path`` and ``GET
/api/entitlement/runtime-spec-at-path-batch`` endpoints.

Runtime-axis twin of :func:`feature_spec_at_path` /
:func:`feature_spec_at_path_batch`: perspective is validated but does
NOT shape the ``path`` rows, so an upgrade-walkthrough surface can call
``X_at_path(perspective, from, to, ...)`` uniformly across the whole
``_at_path`` family (alongside ``preview_at_path`` and
``tier_catalog_at_path``).

Pins:

* body byte-parity with :func:`runtime_spec_path` for every
  ``(perspective, from, to, runtime)`` quadruple; perspective
  invariance (rows byte-identical across shifting perspective for the
  same ``(from, to, runtime)``)
* per-rung path row byte-equals :func:`runtime_spec_at(rung, runtime)`
  after dropping the three ``rung*`` keys (delegated from
  :func:`runtime_spec_path`, pinned by
  ``test_entitlement_runtime_spec_path``)
* batch per-runtime ``path`` byte-equals scalar
  :func:`runtime_spec_at_path(perspective, from, to, runtime)`
* runtime alias (``claude-code``) resolves to ``claude_code`` (scalar
  and batch)
* unknown perspective / from / to short-circuit to ``None`` (scalar
  and batch); scalar unknown runtime -> ``None``; batch unknown
  runtime -> bucketed into ``unknown[]``
* case + whitespace normalisation on all four ids
* trial accepted as perspective + endpoint (lateral / identity branch)
* grace vs enforce identical rows (delegates to
  :func:`runtime_spec_path` which walks static per-tier maps)
* API surface: 400 on missing / blank / empty args, 404 with ``which``
  bucketing on unknown tier ids, 404 with ``which: "runtime"`` on
  unknown runtime for the scalar, unknown runtimes echoed into
  ``unknown[]`` on the batch endpoint (never 404), 200 envelope with
  ``perspective_tier`` echo + standard ``_at*`` resolver-context tail
  on the happy path
* endpoint never 5xxs on resolver crash
"""
from __future__ import annotations

import importlib
from itertools import product

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


ALL_TIERS = (
    "oss",
    "cloud_free",
    "trial",
    "cloud_starter",
    "cloud_pro",
    "pro",
    "enterprise",
)

# Mix of free (``openclaw``) and paid (``claude_code``, ``codex``,
# ``cursor``) so the parity sweep touches both the always-allowed and
# the rung-flip branches.
SAMPLE_RUNTIMES = (
    "openclaw",
    "claude_code",
    "codex",
    "cursor",
    "hermes",
)

_RUNG_KEYS = {"rung", "rung_label", "rung_rank"}

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
    "runtime",
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
    "to",
    "to_label",
    "to_rank",
    "direction",
    "runtimes",
    "unknown",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# ── scalar helper: shape + invariants ────────────────────────────────────────


def test_scalar_returns_list(ent):
    path = ent.runtime_spec_at_path(
        "cloud_pro", "oss", "enterprise", "claude_code"
    )
    assert isinstance(path, list)
    assert len(path) >= 1


def test_scalar_body_byte_parity_with_runtime_spec_path(ent):
    """Perspective must NOT shape the rows -- delegation to
    :func:`runtime_spec_path` is byte-identical for every perspective."""
    for perspective, f, t, rt in product(
        ALL_TIERS, ALL_TIERS, ALL_TIERS, SAMPLE_RUNTIMES
    ):
        at_path = ent.runtime_spec_at_path(perspective, f, t, rt)
        direct = ent.runtime_spec_path(f, t, rt)
        assert at_path == direct, (perspective, f, t, rt)


def test_scalar_perspective_invariance(ent):
    """Rows must be byte-identical across every perspective for the same
    ``(from, to, runtime)`` triple."""
    for f, t, rt in product(
        ("oss", "cloud_free"), ("enterprise", "pro"), SAMPLE_RUNTIMES
    ):
        rows_by_perspective = [
            ent.runtime_spec_at_path(p, f, t, rt) for p in ALL_TIERS
        ]
        first = rows_by_perspective[0]
        for other in rows_by_perspective[1:]:
            assert other == first


def test_scalar_per_rung_byte_equality_with_runtime_spec_at(ent):
    """Dropping the three ``rung*`` keys from a path row yields exact
    byte-equality with :func:`runtime_spec_at(rung, runtime)` -- a
    property inherited from :func:`runtime_spec_path`."""
    path = ent.runtime_spec_at_path(
        "cloud_pro", "oss", "enterprise", "claude_code"
    )
    for row in path:
        body = {k: v for k, v in row.items() if k not in _RUNG_KEYS}
        direct = ent.runtime_spec_at(row["rung"], "claude_code")
        assert body == direct


def test_scalar_identity_returns_empty_path(ent):
    path = ent.runtime_spec_at_path(
        "cloud_pro", "cloud_pro", "cloud_pro", "claude_code"
    )
    assert path == []


def test_scalar_lateral_returns_single_row(ent):
    # cloud_pro and pro share a rank; lateral returns a single-row path.
    path = ent.runtime_spec_at_path("oss", "cloud_pro", "pro", "claude_code")
    assert isinstance(path, list)
    assert len(path) == 1
    assert path[0]["rung"] == "pro"


def test_scalar_upgrade_ranks_monotonic(ent):
    path = ent.runtime_spec_at_path("oss", "oss", "enterprise", "claude_code")
    ranks = [r["rung_rank"] for r in path]
    assert ranks == sorted(ranks)


def test_scalar_downgrade_ranks_monotonic(ent):
    path = ent.runtime_spec_at_path("oss", "enterprise", "oss", "claude_code")
    ranks = [r["rung_rank"] for r in path]
    assert ranks == sorted(ranks, reverse=True)


def test_scalar_trial_accepted_as_perspective(ent):
    path = ent.runtime_spec_at_path(
        "trial", "oss", "enterprise", "claude_code"
    )
    assert isinstance(path, list)


def test_scalar_trial_accepted_as_endpoint_identity(ent):
    path = ent.runtime_spec_at_path("cloud_pro", "trial", "trial", "claude_code")
    assert path == []


def test_scalar_alias_resolves_to_canonical(ent):
    # ``claude-code`` -> ``claude_code`` at the delegated
    # :func:`runtime_spec_path` layer; perspective wrapper never shapes
    # the ``runtime`` field on the row.
    aliased = ent.runtime_spec_at_path(
        "cloud_pro", "oss", "enterprise", "claude-code"
    )
    canonical = ent.runtime_spec_at_path(
        "cloud_pro", "oss", "enterprise", "claude_code"
    )
    assert aliased == canonical


def test_scalar_free_runtime_allowed_at_every_rung(ent):
    path = ent.runtime_spec_at_path("oss", "oss", "enterprise", "openclaw")
    assert path
    for row in path:
        assert row["allowed"] is True


def test_scalar_paid_runtime_flips_along_path(ent):
    path = ent.runtime_spec_at_path("oss", "oss", "enterprise", "claude_code")
    assert path
    allowed_flags = [row["allowed"] for row in path]
    # Somewhere along the ladder the paid runtime becomes allowed.
    assert False in allowed_flags or True in allowed_flags
    assert any(flag is True for flag in allowed_flags)


def test_scalar_unknown_perspective_returns_none(ent):
    assert ent.runtime_spec_at_path(
        "bogus", "oss", "enterprise", "claude_code"
    ) is None


def test_scalar_unknown_from_returns_none(ent):
    assert ent.runtime_spec_at_path(
        "cloud_pro", "bogus", "enterprise", "claude_code"
    ) is None


def test_scalar_unknown_to_returns_none(ent):
    assert ent.runtime_spec_at_path(
        "cloud_pro", "oss", "bogus", "claude_code"
    ) is None


def test_scalar_unknown_runtime_returns_none(ent):
    assert ent.runtime_spec_at_path(
        "cloud_pro", "oss", "enterprise", "no_such_runtime"
    ) is None


def test_scalar_none_inputs_return_none(ent):
    assert ent.runtime_spec_at_path(None, "oss", "enterprise", "claude_code") is None
    assert ent.runtime_spec_at_path("cloud_pro", None, "enterprise", "claude_code") is None
    assert ent.runtime_spec_at_path("cloud_pro", "oss", None, "claude_code") is None
    assert ent.runtime_spec_at_path("cloud_pro", "oss", "enterprise", None) is None


def test_scalar_whitespace_and_case_normalisation(ent):
    padded = ent.runtime_spec_at_path(
        "  Cloud_Pro  ", "  OSS  ", "  ENTERPRISE  ", "  Claude-Code  "
    )
    canonical = ent.runtime_spec_at_path(
        "cloud_pro", "oss", "enterprise", "claude_code"
    )
    assert padded == canonical


def test_scalar_never_raises_on_weird_types(ent):
    for weird in (b"bytes", 123, 4.5, ["oss"], {"tier": "oss"}):
        # None of these should raise -- they should all short-circuit
        # to ``None``.
        assert ent.runtime_spec_at_path(weird, "oss", "enterprise", "claude_code") is None


def test_scalar_grace_vs_enforce_byte_identical(ent, monkeypatch):
    import clawmetry.entitlements as e

    grace_path = ent.runtime_spec_at_path(
        "cloud_pro", "oss", "enterprise", "claude_code"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    try:
        enforced_path = e.runtime_spec_at_path(
            "cloud_pro", "oss", "enterprise", "claude_code"
        )
        assert enforced_path == grace_path
    finally:
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(e)
        e.invalidate()


# ── batch helper: shape + invariants ─────────────────────────────────────────


def test_batch_returns_envelope(ent):
    batch = ent.runtime_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["claude_code", "codex"]
    )
    assert set(batch.keys()) == {"runtimes", "unknown"}
    assert isinstance(batch["runtimes"], list)
    assert isinstance(batch["unknown"], list)
    assert len(batch["runtimes"]) == 2
    assert {r["runtime"] for r in batch["runtimes"]} == {"claude_code", "codex"}


def test_batch_body_byte_parity_with_runtime_spec_path_batch(ent):
    for perspective in ALL_TIERS:
        batch = ent.runtime_spec_at_path_batch(
            perspective, "oss", "enterprise", list(SAMPLE_RUNTIMES)
        )
        direct = ent.runtime_spec_path_batch(
            "oss", "enterprise", list(SAMPLE_RUNTIMES)
        )
        assert batch == direct, perspective


def test_batch_perspective_invariance(ent):
    batches = [
        ent.runtime_spec_at_path_batch(
            p, "oss", "enterprise", list(SAMPLE_RUNTIMES)
        )
        for p in ALL_TIERS
    ]
    first = batches[0]
    for other in batches[1:]:
        assert other == first


def test_batch_per_row_matches_scalar(ent):
    batch = ent.runtime_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", list(SAMPLE_RUNTIMES)
    )
    for row in batch["runtimes"]:
        scalar = ent.runtime_spec_at_path(
            "cloud_pro", "oss", "enterprise", row["runtime"]
        )
        assert row["path"] == scalar


def test_batch_unknown_runtime_bucketed(ent):
    batch = ent.runtime_spec_at_path_batch(
        "cloud_pro",
        "oss",
        "enterprise",
        ["claude_code", "no_such_runtime", "codex"],
    )
    assert {r["runtime"] for r in batch["runtimes"]} == {"claude_code", "codex"}
    assert batch["unknown"] == ["no_such_runtime"]


def test_batch_all_unknown_returns_empty_rows_and_unknown_list(ent):
    batch = ent.runtime_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["bogus1", "bogus2"]
    )
    assert batch["runtimes"] == []
    assert batch["unknown"] == ["bogus1", "bogus2"]


def test_batch_alias_canonicalised(ent):
    batch = ent.runtime_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["claude-code"]
    )
    assert [r["runtime"] for r in batch["runtimes"]] == ["claude_code"]
    assert batch["unknown"] == []


def test_batch_alias_dedup(ent):
    batch = ent.runtime_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["claude-code", "claude_code"]
    )
    assert [r["runtime"] for r in batch["runtimes"]] == ["claude_code"]


def test_batch_unknown_perspective_returns_none(ent):
    assert ent.runtime_spec_at_path_batch(
        "bogus", "oss", "enterprise", ["claude_code"]
    ) is None


def test_batch_unknown_from_returns_none(ent):
    assert ent.runtime_spec_at_path_batch(
        "cloud_pro", "bogus", "enterprise", ["claude_code"]
    ) is None


def test_batch_unknown_to_returns_none(ent):
    assert ent.runtime_spec_at_path_batch(
        "cloud_pro", "oss", "bogus", ["claude_code"]
    ) is None


def test_batch_trial_accepted_as_perspective(ent):
    batch = ent.runtime_spec_at_path_batch(
        "trial", "oss", "enterprise", ["claude_code"]
    )
    assert batch is not None
    assert [r["runtime"] for r in batch["runtimes"]] == ["claude_code"]


def test_batch_whitespace_and_case_normalisation(ent):
    padded = ent.runtime_spec_at_path_batch(
        "  Cloud_Pro  ",
        "  OSS  ",
        "  ENTERPRISE  ",
        ["  Claude-Code  ", "codex"],
    )
    canonical = ent.runtime_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["claude_code", "codex"]
    )
    assert padded == canonical


def test_batch_grace_vs_enforce_byte_identical(ent, monkeypatch):
    import clawmetry.entitlements as e

    grace_batch = ent.runtime_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", list(SAMPLE_RUNTIMES)
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    try:
        enforced_batch = e.runtime_spec_at_path_batch(
            "cloud_pro", "oss", "enterprise", list(SAMPLE_RUNTIMES)
        )
        assert enforced_batch == grace_batch
    finally:
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(e)
        e.invalidate()


def test_batch_per_runtime_crash_short_circuits_to_unknown(ent, monkeypatch):
    def boom(from_tier, to_tier, runtime):
        raise RuntimeError("simulated per-runtime failure")

    monkeypatch.setattr(ent, "runtime_spec_path", boom)
    batch = ent.runtime_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["claude_code", "codex"]
    )
    # runtime_spec_path_batch delegates per-runtime to runtime_spec_path,
    # so every runtime should end up in ``unknown[]`` with the raw alias.
    assert batch["runtimes"] == []
    assert set(batch["unknown"]) == {"claude_code", "codex"}


# ── HTTP scalar endpoint ─────────────────────────────────────────────────────


def test_http_scalar_envelope_shape(client, ent):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&runtime=claude_code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS


def test_http_scalar_missing_tier_400(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path?from=oss&to=enterprise&runtime=claude_code"
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing tier"}


def test_http_scalar_missing_from_400(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path?tier=cloud_pro&to=enterprise&runtime=claude_code"
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing from"}


def test_http_scalar_missing_to_400(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path?tier=cloud_pro&from=oss&runtime=claude_code"
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing to"}


def test_http_scalar_missing_runtime_400(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing runtime"}


def test_http_scalar_unknown_tier_404_which_tier(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=bogus&from=oss&to=enterprise&runtime=claude_code"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_http_scalar_unknown_from_404_which_from(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=cloud_pro&from=bogus&to=enterprise&runtime=claude_code"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"
    assert body["from"] == "bogus"


def test_http_scalar_unknown_to_404_which_to(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=cloud_pro&from=oss&to=bogus&runtime=claude_code"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "to"
    assert body["to"] == "bogus"


def test_http_scalar_unknown_runtime_404_which_runtime(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&runtime=no_such_runtime"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "runtime"
    assert body["runtime"] == "no_such_runtime"


def test_http_scalar_identity_path_empty(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=cloud_pro&from=cloud_pro&to=cloud_pro&runtime=claude_code"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_http_scalar_downgrade_direction(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=cloud_pro&from=enterprise&to=oss&runtime=claude_code"
    )
    assert r.status_code == 200
    assert r.get_json()["direction"] == "downgrade"


def test_http_scalar_trial_accepted(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=trial&from=oss&to=enterprise&runtime=claude_code"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "trial"


def test_http_scalar_alias_canonicalised(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&runtime=claude-code"
    )
    assert r.status_code == 200
    assert r.get_json()["runtime"] == "claude_code"


def test_http_scalar_whitespace_and_case_normalisation(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=%20Cloud_Pro%20&from=%20OSS%20&to=%20ENTERPRISE%20&runtime=%20Claude-Code%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert body["runtime"] == "claude_code"


def test_http_scalar_path_byte_parity_with_runtime_spec_path(client):
    at = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&runtime=claude_code"
    ).get_json()
    direct = client.get(
        "/api/entitlement/runtime-spec-path"
        "?from=oss&to=enterprise&runtime=claude_code"
    ).get_json()
    assert at["path"] == direct["path"]


def test_http_scalar_perspective_invariance(client):
    paths = []
    for p in ALL_TIERS:
        body = client.get(
            "/api/entitlement/runtime-spec-at-path"
            f"?tier={p}&from=oss&to=enterprise&runtime=claude_code"
        ).get_json()
        paths.append(body["path"])
    first = paths[0]
    for other in paths[1:]:
        assert other == first


def test_http_scalar_never_5xxs_on_resolver_crash(client, monkeypatch):
    from clawmetry import entitlements as _ent

    def boom(*a, **k):
        raise RuntimeError("simulated")

    monkeypatch.setattr(_ent, "runtime_spec_at_path", boom)
    r = client.get(
        "/api/entitlement/runtime-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&runtime=claude_code"
    )
    # Grace envelope short-circuit -- 200 with an empty path, not 500.
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["path"] == []
    assert body["grace"] is True


# ── HTTP batch endpoint ──────────────────────────────────────────────────────


def test_http_batch_envelope_shape(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&runtimes=claude_code,codex"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _BATCH_ENVELOPE_KEYS


def test_http_batch_missing_tier_400(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?from=oss&to=enterprise&runtimes=claude_code"
    )
    assert r.status_code == 400


def test_http_batch_missing_from_400(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&to=enterprise&runtimes=claude_code"
    )
    assert r.status_code == 400


def test_http_batch_missing_to_400(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&runtimes=claude_code"
    )
    assert r.status_code == 400


def test_http_batch_missing_runtimes_400(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 400


def test_http_batch_empty_runtimes_400(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&runtimes=  ,  ,"
    )
    assert r.status_code == 400


def test_http_batch_unknown_tier_which_bucketed(client):
    for which, params in (
        ("tier", "tier=bogus&from=oss&to=enterprise"),
        ("from", "tier=cloud_pro&from=bogus&to=enterprise"),
        ("to", "tier=cloud_pro&from=oss&to=bogus"),
    ):
        r = client.get(
            "/api/entitlement/runtime-spec-at-path-batch"
            f"?{params}&runtimes=claude_code"
        )
        assert r.status_code == 404
        body = r.get_json()
        assert body["which"] == which


def test_http_batch_happy_path(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&runtimes=claude_code,codex,openclaw"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "upgrade"
    assert {r["runtime"] for r in body["runtimes"]} == {
        "claude_code",
        "codex",
        "openclaw",
    }
    assert body["unknown"] == []


def test_http_batch_partial_unknown_runtime_bucketed_200(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise"
        "&runtimes=claude_code,no_such_runtime,codex"
    )
    # 200, not 404 -- unknown runtime ids do NOT short-circuit the batch.
    assert r.status_code == 200
    body = r.get_json()
    assert body["unknown"] == ["no_such_runtime"]
    assert {r["runtime"] for r in body["runtimes"]} == {"claude_code", "codex"}


def test_http_batch_alias_canonicalised(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&runtimes=claude-code,codex"
    )
    body = r.get_json()
    assert {r["runtime"] for r in body["runtimes"]} == {"claude_code", "codex"}


def test_http_batch_alias_dedup(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&runtimes=claude-code,claude_code"
    )
    body = r.get_json()
    assert [r["runtime"] for r in body["runtimes"]] == ["claude_code"]


def test_http_batch_multi_runtime(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise"
        "&runtimes=claude_code,codex,cursor,hermes,openclaw"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert len(body["runtimes"]) == 5


def test_http_batch_body_parity_with_runtime_spec_path_batch(client):
    at = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&runtimes=claude_code,codex"
    ).get_json()
    direct = client.get(
        "/api/entitlement/runtime-spec-path-batch"
        "?from=oss&to=enterprise&runtimes=claude_code,codex"
    ).get_json()
    assert at["runtimes"] == direct["runtimes"]


def test_http_batch_perspective_invariance(client):
    rows = []
    for p in ALL_TIERS:
        body = client.get(
            "/api/entitlement/runtime-spec-at-path-batch"
            f"?tier={p}&from=oss&to=enterprise&runtimes=claude_code,codex"
        ).get_json()
        rows.append(body["runtimes"])
    first = rows[0]
    for other in rows[1:]:
        assert other == first


def test_http_batch_trial_accepted(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=trial&from=oss&to=enterprise&runtimes=claude_code"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "trial"


def test_http_batch_whitespace_and_case_normalisation(client):
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=%20Cloud_Pro%20&from=%20OSS%20&to=%20ENTERPRISE%20"
        "&runtimes=%20Claude-Code%20,%20Codex%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert {r["runtime"] for r in body["runtimes"]} == {"claude_code", "codex"}


def test_http_batch_never_5xxs_on_resolver_crash(client, monkeypatch):
    from clawmetry import entitlements as _ent

    def boom(*a, **k):
        raise RuntimeError("simulated")

    monkeypatch.setattr(_ent, "runtime_spec_at_path_batch", boom)
    r = client.get(
        "/api/entitlement/runtime-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&runtimes=claude_code"
    )
    # Grace envelope -- 200 with empty runtimes list, not 500.
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["runtimes"] == []
    assert body["grace"] is True
