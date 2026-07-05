"""Tests for
``clawmetry.entitlements.lock_reason_at_path(perspective, from, to, item, kind)``
+ ``lock_reason_at_path_batch(perspective, from, to, ...)`` + the ``GET
/api/entitlement/lock-reason-at-path`` and ``GET
/api/entitlement/lock-reason-at-path-batch`` endpoints.

Perspective-validated what-if wrapper around ``lock_reason_path`` /
``lock_reason_path_batch``. Fills the ``_at_path`` /
``_at_path_batch`` slot of the ``lock_reason`` family, matching the
already-shipping ``feature_spec_at_path`` / ``runtime_spec_at_path`` /
``tier_spec_at_path`` / ``feature_catalog_at_path`` /
``runtime_catalog_at_path`` / ``tier_catalog_at_path`` /
``capacity_diff_at_path`` / ``preview_at_path`` pattern on the eight
other axes -- so every ``*_path`` helper now has a perspective-
validated ``_at_path`` sibling.

Pins:

* scalar body byte-parity with :func:`lock_reason_path` for every
  ``(perspective, from, to, item, kind)`` quintuple (perspective must
  NOT shape the rows)
* batch per-axis ``path`` byte-identical to
  :func:`lock_reason_path_batch` for the same
  ``(from, to, features, runtimes, channels, retention_days, nodes)``
* perspective invariance (rows byte-identical across shifting
  perspective for the same downstream args) on all 5 axes
* unknown / empty perspective -> ``None`` (scalar and batch);
  delegates identical short-circuit posture to
  :func:`lock_reason_path` on unknown from / to / item
* runtime alias (``claude-code``) canonicalises to ``claude_code`` on
  the scalar and echoes into either ``runtimes[]`` or ``unknown[]`` in
  the batch
* trial accepted as perspective + endpoint (lateral / identity branch)
* grace vs enforce identical rows (helper synthesises a fresh
  ``Entitlement`` per rung with ``grace=False`` regardless of the live
  resolver state)
* never raises: a delegation failure logs a warning and returns
  ``None`` / short-circuits into ``unknown[]``
* API: 400 on missing tier / from / to / no axis / multi-axis (scalar
  only); 404 on unknown tier ids (with ``which`` bucketing); 404 on
  unknown feature / runtime / capacity for the scalar; unknown feature
  / runtime IDs echoed in ``unknown[]`` for the batch (never 404s);
  200 envelope carries ``perspective_tier`` echo + standard ``_at*``
  resolver-context tail (``current_tier``, ``current_tier_rank``,
  ``grace``, ``enforced``)
* endpoint never 5xxs on a resolver crash
"""
from __future__ import annotations

import importlib
from itertools import product

import pytest
from flask import Flask


ALL_TIERS = (
    "oss",
    "cloud_free",
    "trial",
    "cloud_starter",
    "cloud_pro",
    "pro",
    "enterprise",
)

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
    "key",
    "kind",
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
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
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


def _pick_paid_feature(ent) -> str:
    return sorted(ent.PAID_FEATURES)[0]


def _pick_paid_runtime(ent) -> str:
    return sorted(ent.PAID_RUNTIMES)[0]


# ── scalar helper: shape ─────────────────────────────────────────────────────


def test_scalar_returns_list(ent):
    path = ent.lock_reason_at_path(
        "cloud_pro", "oss", "enterprise", _pick_paid_feature(ent),
        kind="feature",
    )
    assert isinstance(path, list)
    assert len(path) >= 1


def test_scalar_each_row_carries_rung_and_lock_keys(ent):
    path = ent.lock_reason_at_path(
        "cloud_pro", "oss", "enterprise", _pick_paid_feature(ent),
        kind="feature",
    )
    for row in path:
        assert set(row).issuperset(_RUNG_KEYS)
        assert set(row).issuperset(_ROW_KEYS)
        assert row["rung_label"] == ent.tier_label(row["rung"])
        assert row["rung_rank"] == ent.tier_rank(row["rung"])


# ── scalar helper: body byte-parity with lock_reason_path ────────────────────


def test_scalar_body_byte_parity_with_lock_reason_path_feature(ent):
    """Perspective must NOT shape the rows."""
    feat = _pick_paid_feature(ent)
    for perspective, f, t in product(ALL_TIERS, ALL_TIERS, ALL_TIERS):
        at_path = ent.lock_reason_at_path(
            perspective, f, t, feat, kind="feature"
        )
        base = ent.lock_reason_path(f, t, feat, kind="feature")
        assert at_path == base, (perspective, f, t)


def test_scalar_body_byte_parity_with_lock_reason_path_runtime(ent):
    rt = _pick_paid_runtime(ent)
    for perspective, f, t in product(ALL_TIERS, ALL_TIERS, ALL_TIERS):
        at_path = ent.lock_reason_at_path(
            perspective, f, t, rt, kind="runtime"
        )
        base = ent.lock_reason_path(f, t, rt, kind="runtime")
        assert at_path == base, (perspective, f, t)


@pytest.mark.parametrize(
    "kind,value",
    [
        ("channels", 25),
        ("retention_days", 365),
        ("nodes", 50),
    ],
)
def test_scalar_body_byte_parity_capacity_axes(ent, kind, value):
    for perspective, f, t in product(ALL_TIERS, ALL_TIERS, ALL_TIERS):
        at_path = ent.lock_reason_at_path(
            perspective, f, t, value, kind=kind
        )
        base = ent.lock_reason_path(f, t, value, kind=kind)
        assert at_path == base, (perspective, kind, f, t)


def test_scalar_perspective_invariance_free_runtime(ent):
    """A free runtime (``openclaw``) is allowed at every rung; perspective
    still shouldn't move any bytes."""
    for perspective in ALL_TIERS:
        rows = ent.lock_reason_at_path(
            perspective, "oss", "enterprise", "openclaw", kind="runtime"
        )
        base = ent.lock_reason_path(
            "oss", "enterprise", "openclaw", kind="runtime"
        )
        assert rows == base


def test_scalar_perspective_kind_none_auto_dispatches(ent):
    """`kind=None` auto-detects feature vs runtime just like the delegate."""
    feat = _pick_paid_feature(ent)
    rt = _pick_paid_runtime(ent)
    for perspective in ALL_TIERS:
        f_out = ent.lock_reason_at_path(perspective, "oss", "enterprise", feat)
        r_out = ent.lock_reason_at_path(perspective, "oss", "enterprise", rt)
        assert f_out == ent.lock_reason_path(
            "oss", "enterprise", feat, kind="feature"
        )
        assert r_out == ent.lock_reason_path(
            "oss", "enterprise", rt, kind="runtime"
        )


def test_scalar_runtime_alias_normalises(ent):
    canon = ent.lock_reason_at_path(
        "cloud_pro", "oss", "enterprise", "claude_code", kind="runtime"
    )
    alias = ent.lock_reason_at_path(
        "cloud_pro", "oss", "enterprise", "claude-code", kind="runtime"
    )
    assert canon == alias


# ── scalar helper: perspective validation ────────────────────────────────────


@pytest.mark.parametrize("bad", ["", "   ", "bogus", "not_a_tier", None])
def test_scalar_unknown_perspective_returns_none(ent, bad):
    out = ent.lock_reason_at_path(
        bad, "oss", "enterprise", _pick_paid_feature(ent), kind="feature"
    )
    assert out is None


def test_scalar_perspective_whitespace_case_normalised(ent):
    a = ent.lock_reason_at_path(
        "  Cloud_Pro  ", "oss", "enterprise",
        _pick_paid_feature(ent), kind="feature",
    )
    b = ent.lock_reason_at_path(
        "cloud_pro", "oss", "enterprise",
        _pick_paid_feature(ent), kind="feature",
    )
    assert a == b


def test_scalar_unknown_from_or_to_short_circuits(ent):
    """Perspective-valid but tier ids unknown -> ``None`` (delegated)."""
    assert (
        ent.lock_reason_at_path(
            "cloud_pro", "bogus", "enterprise",
            _pick_paid_feature(ent), kind="feature",
        )
        is None
    )
    assert (
        ent.lock_reason_at_path(
            "cloud_pro", "oss", "bogus",
            _pick_paid_feature(ent), kind="feature",
        )
        is None
    )


def test_scalar_unknown_item_short_circuits(ent):
    """Perspective-valid but item id unknown -> ``None`` (delegated)."""
    out = ent.lock_reason_at_path(
        "cloud_pro", "oss", "enterprise", "bogus_id", kind="feature"
    )
    assert out is None


def test_scalar_trial_perspective_accepted(ent):
    """``trial`` is a valid perspective / from / to (matches delegate)."""
    out = ent.lock_reason_at_path(
        "trial", "trial", "trial",
        _pick_paid_feature(ent), kind="feature",
    )
    assert out == []


def test_scalar_never_raises_on_delegate_crash(ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(ent, "lock_reason_path", _boom)
    out = ent.lock_reason_at_path(
        "cloud_pro", "oss", "enterprise",
        _pick_paid_feature(ent), kind="feature",
    )
    assert out is None


# ── scalar helper: grace vs enforce ──────────────────────────────────────────


def test_scalar_grace_vs_enforce_identical_rows(ent, monkeypatch):
    feat = _pick_paid_feature(ent)
    grace_rows = ent.lock_reason_at_path(
        "cloud_pro", "oss", "enterprise", feat, kind="feature"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforce_rows = ent.lock_reason_at_path(
        "cloud_pro", "oss", "enterprise", feat, kind="feature"
    )
    assert grace_rows == enforce_rows


# ── batch helper: shape + parity ─────────────────────────────────────────────


def test_batch_returns_dict_with_5_axes_plus_unknown(ent):
    out = ent.lock_reason_at_path_batch(
        "cloud_pro",
        "oss",
        "enterprise",
        features=[_pick_paid_feature(ent)],
        runtimes=[_pick_paid_runtime(ent)],
        channels=99,
        retention_days=365,
        nodes=50,
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
        "unknown",
    }
    assert isinstance(out["features"], list)
    assert isinstance(out["runtimes"], list)
    assert isinstance(out["unknown"], dict)
    assert set(out["unknown"].keys()) == {"features", "runtimes"}


def test_batch_body_byte_parity_with_lock_reason_path_batch(ent):
    for perspective in ALL_TIERS:
        got = ent.lock_reason_at_path_batch(
            perspective,
            "oss",
            "enterprise",
            features=[_pick_paid_feature(ent), "custom_alerts"],
            runtimes=[_pick_paid_runtime(ent), "openclaw", "claude-code"],
            channels=99,
            retention_days=365,
            nodes=50,
        )
        base = ent.lock_reason_path_batch(
            "oss",
            "enterprise",
            features=[_pick_paid_feature(ent), "custom_alerts"],
            runtimes=[_pick_paid_runtime(ent), "openclaw", "claude-code"],
            channels=99,
            retention_days=365,
            nodes=50,
        )
        assert got == base, perspective


def test_batch_unknown_ids_echoed_not_404(ent):
    out = ent.lock_reason_at_path_batch(
        "cloud_pro",
        "oss",
        "enterprise",
        features=[_pick_paid_feature(ent), "bogus_feat"],
        runtimes=["bogus_runtime"],
    )
    assert any(row["key"] == _pick_paid_feature(ent) for row in out["features"])
    assert "bogus_feat" in out["unknown"]["features"]
    assert "bogus_runtime" in out["unknown"]["runtimes"]


def test_batch_alias_canonicalises_and_dedupes(ent):
    out = ent.lock_reason_at_path_batch(
        "cloud_pro",
        "oss",
        "enterprise",
        runtimes=["claude-code", "claude_code"],
    )
    ids = [row["key"] for row in out["runtimes"]]
    assert ids.count("claude_code") == 1


@pytest.mark.parametrize("bad", ["", "   ", "bogus", None])
def test_batch_unknown_perspective_returns_none(ent, bad):
    out = ent.lock_reason_at_path_batch(
        bad,
        "oss",
        "enterprise",
        features=[_pick_paid_feature(ent)],
    )
    assert out is None


def test_batch_unknown_from_or_to_short_circuits(ent):
    for bad in [("bogus", "enterprise"), ("oss", "bogus")]:
        out = ent.lock_reason_at_path_batch(
            "cloud_pro",
            bad[0],
            bad[1],
            features=[_pick_paid_feature(ent)],
        )
        assert out is None


def test_batch_never_raises_on_delegate_crash(ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(ent, "lock_reason_path_batch", _boom)
    out = ent.lock_reason_at_path_batch(
        "cloud_pro",
        "oss",
        "enterprise",
        features=[_pick_paid_feature(ent)],
    )
    assert out is None


def test_batch_grace_vs_enforce_identical_rows(ent, monkeypatch):
    kwargs = dict(
        perspective_tier="cloud_pro",
        from_tier="oss",
        to_tier="enterprise",
        features=[_pick_paid_feature(ent)],
    )
    grace = ent.lock_reason_at_path_batch(
        kwargs["perspective_tier"],
        kwargs["from_tier"],
        kwargs["to_tier"],
        features=kwargs["features"],
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.lock_reason_at_path_batch(
        kwargs["perspective_tier"],
        kwargs["from_tier"],
        kwargs["to_tier"],
        features=kwargs["features"],
    )
    assert grace == enforced


# ── HTTP scalar: 400 / 404 rules ─────────────────────────────────────────────


def test_http_scalar_missing_tier_is_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?from=oss&to=enterprise&feature={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 400
    assert "tier" in r.get_json().get("error", "").lower()


def test_http_scalar_missing_from_is_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?tier=cloud_pro&to=enterprise&feature={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 400
    assert "from" in r.get_json().get("error", "").lower()


def test_http_scalar_missing_to_is_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?tier=cloud_pro&from=oss&feature={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 400
    assert "to" in r.get_json().get("error", "").lower()


def test_http_scalar_no_axis_is_400(client):
    r = client.get(
        "/api/entitlement/lock-reason-at-path?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 400
    body = r.get_json()["error"]
    assert "supply exactly one" in body


def test_http_scalar_multi_axis_is_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?tier=cloud_pro&from=oss&to=enterprise&feature={_pick_paid_feature(ent)}"
        "&channels=5"
    )
    assert r.status_code == 400
    assert "only one" in r.get_json()["error"]


def test_http_scalar_unknown_tier_is_404_with_which(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?tier=bogus&from=oss&to=enterprise&feature={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_http_scalar_unknown_from_is_404_with_which(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?tier=cloud_pro&from=bogus&to=enterprise&feature={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"


def test_http_scalar_unknown_to_is_404_with_which(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?tier=cloud_pro&from=oss&to=bogus&feature={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "to"


def test_http_scalar_unknown_feature_is_404(client):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&feature=bogus"
    )
    assert r.status_code == 404


def test_http_scalar_unknown_runtime_is_404(client):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&runtime=bogus"
    )
    assert r.status_code == 404


def test_http_scalar_bad_capacity_is_404(client):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&channels=abc"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["kind"] == "channels"


# ── HTTP scalar: happy path ──────────────────────────────────────────────────


def test_http_scalar_happy_path_envelope(client, ent):
    feat = _pick_paid_feature(ent)
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?tier=cloud_pro&from=oss&to=enterprise&feature={feat}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    assert body["perspective_tier_rank"] == ent.tier_rank("cloud_pro")
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert body["key"] == feat
    assert body["kind"] == "feature"
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list)
    assert len(body["path"]) >= 1


def test_http_scalar_body_path_byte_parity_with_lock_reason_path(client, ent):
    feat = _pick_paid_feature(ent)
    r_at = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?tier=cloud_pro&from=oss&to=enterprise&feature={feat}"
    ).get_json()
    r_base = client.get(
        "/api/entitlement/lock-reason-path"
        f"?from=oss&to=enterprise&feature={feat}"
    ).get_json()
    assert r_at["path"] == r_base["path"]


def test_http_scalar_runtime_alias_echoes_canonical(client):
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&runtime=claude-code"
    )
    assert r.status_code == 200
    assert r.get_json()["key"] == "claude_code"


def test_http_scalar_identity_returns_empty_path(client, ent):
    feat = _pick_paid_feature(ent)
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?tier=cloud_pro&from=enterprise&to=enterprise&feature={feat}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_http_scalar_never_5xx_on_resolver_crash(client, ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(ent, "lock_reason_at_path", _boom)
    r = client.get(
        "/api/entitlement/lock-reason-at-path"
        f"?tier=cloud_pro&from=oss&to=enterprise&feature={_pick_paid_feature(ent)}"
    )
    assert r.status_code < 500


# ── HTTP batch ───────────────────────────────────────────────────────────────


def test_http_batch_missing_tier_is_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        f"?from=oss&to=enterprise&features={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 400


def test_http_batch_missing_from_or_to_is_400(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        f"?tier=cloud_pro&to=enterprise&features={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 400
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        f"?tier=cloud_pro&from=oss&features={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 400


def test_http_batch_no_axis_is_400(client):
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 400
    assert "supply at least one" in r.get_json()["error"]


def test_http_batch_unknown_tier_is_404_with_which(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        f"?tier=bogus&from=oss&to=enterprise&features={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_http_batch_unknown_from_is_404_with_which(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        f"?tier=cloud_pro&from=bogus&to=enterprise&features={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "from"


def test_http_batch_unknown_to_is_404_with_which(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        f"?tier=cloud_pro&from=oss&to=bogus&features={_pick_paid_feature(ent)}"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "to"


def test_http_batch_happy_path_envelope(client, ent):
    feat = _pick_paid_feature(ent)
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        f"?tier=cloud_pro&from=oss&to=enterprise&features={feat}"
        f"&runtimes={_pick_paid_runtime(ent)}"
        "&channels=99&retention_days=365&nodes=50"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _BATCH_ENVELOPE_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    assert body["perspective_tier_rank"] == ent.tier_rank("cloud_pro")
    assert body["direction"] == "upgrade"
    assert len(body["features"]) == 1
    assert len(body["runtimes"]) == 1
    assert body["channels"] is not None
    assert body["retention_days"] is not None
    assert body["nodes"] is not None
    assert body["unknown"] == {"features": [], "runtimes": []}


def test_http_batch_body_byte_parity_with_lock_reason_path_batch(client, ent):
    """Per-axis body must be byte-identical to /lock-reason-path-batch."""
    feat = _pick_paid_feature(ent)
    query = (
        f"from=oss&to=enterprise&features={feat},custom_alerts"
        f"&runtimes={_pick_paid_runtime(ent)},openclaw,claude-code"
        "&channels=99&retention_days=365&nodes=50"
    )
    at = client.get(
        f"/api/entitlement/lock-reason-at-path-batch?tier=cloud_pro&{query}"
    ).get_json()
    base = client.get(
        f"/api/entitlement/lock-reason-path-batch?{query}"
    ).get_json()
    for key in ("features", "runtimes", "channels", "retention_days", "nodes", "unknown"):
        assert at[key] == base[key], key


def test_http_batch_unknown_ids_echoed_not_404(client, ent):
    feat = _pick_paid_feature(ent)
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        f"?tier=cloud_pro&from=oss&to=enterprise&features={feat},bogus_feat"
        "&runtimes=bogus_runtime"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert "bogus_feat" in body["unknown"]["features"]
    assert "bogus_runtime" in body["unknown"]["runtimes"]


def test_http_batch_runtime_alias_dedupes(client, ent):
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&runtimes=claude-code,claude_code"
    )
    assert r.status_code == 200
    body = r.get_json()
    canon_ids = [row["key"] for row in body["runtimes"]]
    assert canon_ids.count("claude_code") == 1


def test_http_batch_identity_yields_empty_paths(client, ent):
    feat = _pick_paid_feature(ent)
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        f"?tier=cloud_pro&from=enterprise&to=enterprise&features={feat}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    for row in body["features"]:
        assert row["path"] == []


def test_http_batch_never_5xx_on_resolver_crash(client, ent, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(ent, "lock_reason_at_path_batch", _boom)
    r = client.get(
        "/api/entitlement/lock-reason-at-path-batch"
        f"?tier=cloud_pro&from=oss&to=enterprise&features={_pick_paid_feature(ent)}"
    )
    assert r.status_code < 500
    body = r.get_json()
    # Grace-shape envelope: perspective echoed, empty rows, grace=True.
    assert body["perspective_tier"] == "cloud_pro"
    assert body["features"] == []
    assert body["grace"] is True
