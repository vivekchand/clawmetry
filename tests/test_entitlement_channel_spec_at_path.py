"""Tests for
``clawmetry.entitlements.channel_spec_at_path(perspective, from, to, channel)``
+ the ``GET /api/entitlement/channel-spec-at-path`` endpoint.

Channel-axis twin of :func:`feature_spec_at_path` /
:func:`runtime_spec_at_path`: perspective is validated but does NOT
shape the ``path`` rows, so an upgrade-walkthrough surface can call
``X_at_path(perspective, from, to, ...)`` uniformly across the whole
``_at_path`` family (alongside ``preview_at_path``,
``tier_catalog_at_path``, ``channel_catalog_at_path``).

Pins:

* body byte-parity with :func:`channel_spec_path` for every
  ``(perspective, from, to, channel)`` quadruple; perspective
  invariance (rows byte-identical across shifting perspective for the
  same ``(from, to, channel)``)
* per-rung path row byte-equals :func:`channel_spec_at(rung, channel)`
  after dropping the three ``rung*`` keys (delegated from
  :func:`channel_spec_path`, pinned by
  ``test_entitlement_channel_spec_path``)
* always-free invariant: every chat-channel adapter is FREE at every
  tier, so every path row reports ``free=True`` / ``allowed=True`` /
  ``locked=False`` / ``entitled=True`` regardless of perspective
* unknown perspective / from / to / channel short-circuit to ``None``
* case + whitespace normalisation on all four ids
* trial accepted as perspective + endpoint (lateral / identity branch)
* grace vs enforce identical rows (delegates to
  :func:`channel_spec_path` which walks static per-tier maps)
* API surface: 400 on missing / blank args, 404 with ``which``
  bucketing on unknown tier ids, 404 with ``which: "channel"`` on
  unknown channel, 200 envelope with ``perspective_tier`` echo +
  standard ``_at*`` resolver-context tail on the happy path
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

# A representative slice of the 21 chat-channel adapters so the parity
# sweep touches multiple ids without ballooning the product() cost.
SAMPLE_CHANNELS = (
    "telegram",
    "signal",
    "discord",
    "whatsapp",
    "imessage",
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
    "channel",
    "path",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# ── scalar helper: shape + invariants ────────────────────────────────────────


def test_scalar_returns_list(ent):
    path = ent.channel_spec_at_path(
        "cloud_pro", "oss", "enterprise", "telegram"
    )
    assert isinstance(path, list)
    assert len(path) >= 1


def test_scalar_body_byte_parity_with_channel_spec_path(ent):
    """Perspective must NOT shape the rows -- delegation to
    :func:`channel_spec_path` is byte-identical for every perspective."""
    for perspective, f, t, ch in product(
        ALL_TIERS, ALL_TIERS, ALL_TIERS, SAMPLE_CHANNELS
    ):
        at_path = ent.channel_spec_at_path(perspective, f, t, ch)
        direct = ent.channel_spec_path(f, t, ch)
        assert at_path == direct, (perspective, f, t, ch)


def test_scalar_perspective_invariance(ent):
    """Rows must be byte-identical across every perspective for the same
    ``(from, to, channel)`` triple."""
    for f, t, ch in product(
        ("oss", "cloud_free"), ("enterprise", "pro"), SAMPLE_CHANNELS
    ):
        rows_by_perspective = [
            ent.channel_spec_at_path(p, f, t, ch) for p in ALL_TIERS
        ]
        first = rows_by_perspective[0]
        for other in rows_by_perspective[1:]:
            assert other == first


def test_scalar_per_rung_byte_equality_with_channel_spec_at(ent):
    """Dropping the three ``rung*`` keys from a path row yields exact
    byte-equality with :func:`channel_spec_at(rung, channel)` -- a
    property inherited from :func:`channel_spec_path`."""
    path = ent.channel_spec_at_path(
        "cloud_pro", "oss", "enterprise", "telegram"
    )
    for row in path:
        body = {k: v for k, v in row.items() if k not in _RUNG_KEYS}
        direct = ent.channel_spec_at(row["rung"], "telegram")
        assert body == direct


def test_scalar_per_rung_byte_equality_with_live_channel_spec(ent):
    """Every channel is FREE at every tier, so each rung's body is
    byte-identical to the LIVE :func:`channel_spec(channel)` row."""
    live = ent.channel_spec("telegram")
    path = ent.channel_spec_at_path(
        "cloud_pro", "oss", "enterprise", "telegram"
    )
    for row in path:
        body = {k: v for k, v in row.items() if k not in _RUNG_KEYS}
        assert body == live


def test_scalar_identity_returns_empty_path(ent):
    path = ent.channel_spec_at_path(
        "cloud_pro", "cloud_pro", "cloud_pro", "telegram"
    )
    assert path == []


def test_scalar_lateral_returns_single_row(ent):
    # cloud_pro and pro share a rank; lateral returns a single-row path.
    path = ent.channel_spec_at_path("oss", "cloud_pro", "pro", "telegram")
    assert isinstance(path, list)
    assert len(path) == 1
    assert path[0]["rung"] == "pro"


def test_scalar_upgrade_ranks_monotonic(ent):
    path = ent.channel_spec_at_path("oss", "oss", "enterprise", "telegram")
    ranks = [r["rung_rank"] for r in path]
    assert ranks == sorted(ranks)


def test_scalar_downgrade_ranks_monotonic(ent):
    path = ent.channel_spec_at_path("oss", "enterprise", "oss", "telegram")
    ranks = [r["rung_rank"] for r in path]
    assert ranks == sorted(ranks, reverse=True)


def test_scalar_trial_accepted_as_perspective(ent):
    path = ent.channel_spec_at_path(
        "trial", "oss", "enterprise", "telegram"
    )
    assert isinstance(path, list)


def test_scalar_trial_accepted_as_endpoint_identity(ent):
    path = ent.channel_spec_at_path(
        "cloud_pro", "trial", "trial", "telegram"
    )
    assert path == []


def test_scalar_every_channel_free_at_every_rung(ent):
    """Always-free invariant: every returned row must report
    ``free=True`` / ``allowed=True`` / ``locked=False`` /
    ``entitled=True`` at every rung, regardless of perspective."""
    for perspective, ch in product(ALL_TIERS, SAMPLE_CHANNELS):
        path = ent.channel_spec_at_path(perspective, "oss", "enterprise", ch)
        assert path
        for row in path:
            assert row["free"] is True
            assert row["allowed"] is True
            assert row["locked"] is False
            assert row["entitled"] is True


def test_scalar_unknown_perspective_returns_none(ent):
    assert ent.channel_spec_at_path(
        "bogus", "oss", "enterprise", "telegram"
    ) is None


def test_scalar_unknown_from_returns_none(ent):
    assert ent.channel_spec_at_path(
        "cloud_pro", "bogus", "enterprise", "telegram"
    ) is None


def test_scalar_unknown_to_returns_none(ent):
    assert ent.channel_spec_at_path(
        "cloud_pro", "oss", "bogus", "telegram"
    ) is None


def test_scalar_unknown_channel_returns_none(ent):
    assert ent.channel_spec_at_path(
        "cloud_pro", "oss", "enterprise", "no_such_channel"
    ) is None


def test_scalar_none_inputs_return_none(ent):
    assert ent.channel_spec_at_path(None, "oss", "enterprise", "telegram") is None
    assert ent.channel_spec_at_path("cloud_pro", None, "enterprise", "telegram") is None
    assert ent.channel_spec_at_path("cloud_pro", "oss", None, "telegram") is None
    assert ent.channel_spec_at_path("cloud_pro", "oss", "enterprise", None) is None


def test_scalar_blank_inputs_return_none(ent):
    assert ent.channel_spec_at_path("", "oss", "enterprise", "telegram") is None
    assert ent.channel_spec_at_path("   ", "oss", "enterprise", "telegram") is None


def test_scalar_whitespace_and_case_normalisation(ent):
    padded = ent.channel_spec_at_path(
        "  Cloud_Pro  ", "  OSS  ", "  ENTERPRISE  ", "  Telegram  "
    )
    canonical = ent.channel_spec_at_path(
        "cloud_pro", "oss", "enterprise", "telegram"
    )
    assert padded == canonical


def test_scalar_never_raises_on_weird_types(ent):
    for weird in (b"bytes", 123, 4.5, ["oss"], {"tier": "oss"}):
        # None of these should raise -- they should all short-circuit
        # to ``None``.
        assert ent.channel_spec_at_path(
            weird, "oss", "enterprise", "telegram"
        ) is None


def test_scalar_grace_vs_enforce_byte_identical(ent, monkeypatch):
    import clawmetry.entitlements as e

    grace_path = ent.channel_spec_at_path(
        "cloud_pro", "oss", "enterprise", "telegram"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    try:
        enforced_path = e.channel_spec_at_path(
            "cloud_pro", "oss", "enterprise", "telegram"
        )
        assert enforced_path == grace_path
    finally:
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(e)
        e.invalidate()


def test_scalar_delegate_crash_short_circuits_to_none(ent, monkeypatch):
    def boom(from_tier, to_tier, channel):
        raise RuntimeError("simulated delegate failure")

    monkeypatch.setattr(ent, "channel_spec_path", boom)
    assert ent.channel_spec_at_path(
        "cloud_pro", "oss", "enterprise", "telegram"
    ) is None


# ── HTTP scalar endpoint ─────────────────────────────────────────────────────


def test_http_envelope_shape(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&channel=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS


def test_http_missing_tier_400(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?from=oss&to=enterprise&channel=telegram"
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing tier"}


def test_http_missing_from_400(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&to=enterprise&channel=telegram"
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing from"}


def test_http_missing_to_400(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=oss&channel=telegram"
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing to"}


def test_http_missing_channel_400(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing channel"}


def test_http_blank_tier_400(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=%20%20&from=oss&to=enterprise&channel=telegram"
    )
    assert r.status_code == 400


def test_http_unknown_tier_404_which_tier(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=bogus&from=oss&to=enterprise&channel=telegram"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_http_unknown_from_404_which_from(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=bogus&to=enterprise&channel=telegram"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"
    assert body["from"] == "bogus"


def test_http_unknown_to_404_which_to(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=oss&to=bogus&channel=telegram"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "to"
    assert body["to"] == "bogus"


def test_http_unknown_channel_404_which_channel(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&channel=no_such_channel"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "channel"
    assert body["channel"] == "no_such_channel"


def test_http_identity_path_empty(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=cloud_pro&to=cloud_pro&channel=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_http_upgrade_direction(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&channel=telegram"
    )
    assert r.status_code == 200
    assert r.get_json()["direction"] == "upgrade"


def test_http_downgrade_direction(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=enterprise&to=oss&channel=telegram"
    )
    assert r.status_code == 200
    assert r.get_json()["direction"] == "downgrade"


def test_http_lateral_direction(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=oss&from=cloud_pro&to=pro&channel=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1


def test_http_trial_accepted(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=trial&from=oss&to=enterprise&channel=telegram"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "trial"


def test_http_whitespace_and_case_normalisation(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=%20Cloud_Pro%20&from=%20OSS%20&to=%20ENTERPRISE%20&channel=%20Telegram%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert body["channel"] == "telegram"


def test_http_path_byte_parity_with_channel_spec_path(client):
    at = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&channel=telegram"
    ).get_json()
    direct = client.get(
        "/api/entitlement/channel-spec-path"
        "?from=oss&to=enterprise&channel=telegram"
    ).get_json()
    assert at["path"] == direct["path"]


def test_http_perspective_invariance(client):
    paths = []
    for p in ALL_TIERS:
        body = client.get(
            "/api/entitlement/channel-spec-at-path"
            f"?tier={p}&from=oss&to=enterprise&channel=telegram"
        ).get_json()
        paths.append(body["path"])
    first = paths[0]
    for other in paths[1:]:
        assert other == first


def test_http_every_row_free_and_allowed(client):
    body = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&channel=telegram"
    ).get_json()
    for row in body["path"]:
        assert row["free"] is True
        assert row["allowed"] is True
        assert row["locked"] is False
        assert row["entitled"] is True


def test_http_never_5xxs_on_resolver_crash(client, monkeypatch):
    from clawmetry import entitlements as _ent

    def boom(*a, **k):
        raise RuntimeError("simulated")

    monkeypatch.setattr(_ent, "channel_spec_at_path", boom)
    r = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&channel=telegram"
    )
    # Grace envelope short-circuit -- 200 with an empty path, not 500.
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["path"] == []
    assert body["grace"] is True


def test_http_ranks_and_labels_populated(client):
    body = client.get(
        "/api/entitlement/channel-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&channel=telegram"
    ).get_json()
    assert isinstance(body["perspective_tier_rank"], int)
    assert isinstance(body["from_rank"], int)
    assert isinstance(body["to_rank"], int)
    assert body["from_label"]
    assert body["to_label"]
