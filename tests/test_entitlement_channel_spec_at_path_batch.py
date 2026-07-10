"""Tests for ``clawmetry.entitlements.channel_spec_at_path_batch(
perspective, from, to, channels)`` + its HTTP endpoint
``GET /api/entitlement/channel-spec-at-path-batch``.

Batch what-if sibling of :func:`channel_spec_at_path`: walks per-rung
single-channel spec rows for N channels between two tiers from a
hypothetical ``perspective_tier`` in ONE round-trip. Fills the
``_at_path_batch`` slot of the ``channel-spec`` family alongside
:func:`channel_spec`, :func:`channel_spec_at`,
:func:`channel_spec_batch`, :func:`channel_spec_at_batch`,
:func:`channel_spec_path`, :func:`channel_spec_path_batch` and
:func:`channel_spec_at_path` -- channel-axis twin of
:func:`feature_spec_at_path_batch` and
:func:`runtime_spec_at_path_batch`.

Pins:

* body byte-identical to :func:`channel_spec_path_batch` for every
  perspective -- the perspective is validated but does NOT shape the
  rows (parity with every other ``_at_path_batch`` helper the
  ``feature_spec_at_path_batch`` / ``runtime_spec_at_path_batch`` family
  ships).
* per-channel ``path`` byte-identical to the scalar
  :func:`channel_spec_at_path` payload for the same
  ``(perspective, from, to, channel)`` quadruple -- scalar / batch
  no-drift contract.
* rung walk channel-agnostic (every chat-channel adapter is FREE at
  every tier), so all per-channel paths share the same length and
  rung sequence.
* every row remains ``free=True`` / ``allowed=True`` / ``locked=False``
  / ``entitled=True`` regardless of perspective (always-free invariant
  inherited from the delegate).
* per-destination ``direction`` derived from the same ranks the scalar
  endpoint uses (identity / lateral / upgrade / downgrade).
* ``trial`` accepted as perspective, from and to.
* case + whitespace normalisation on perspective, from, to and
  channels; supplied-order preserved; duplicates dropped.
* helper is decoupled from the resolver -- grace vs enforce yields
  byte-identical rows.
* unknown / empty / garbage perspective / from / to return ``None``
  and never raise; a delegate crash short-circuits to ``None`` and
  logs a warning.
* per-channel row failure short-circuits that id into ``unknown[]``
  while the rest of the batch keeps building.
* API: 400 on missing / empty args, 404 with ``which: "tier" | "from"
  | "to"`` on unknown tier ids, 200 with bucketed unknowns for unknown
  channel ids, standard resolver-context tail every ``_at*`` endpoint
  carries, never 5xx on a helper crash.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ITEM_KEYS = {"channel", "path"}
_RUNG_KEYS = {"rung", "rung_label", "rung_rank"}
_SPEC_KEYS = {"id", "label", "free", "tier", "allowed", "locked", "entitled"}
_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "channels",
    "unknown",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

ALL_TIERS = (
    "oss",
    "cloud_free",
    "trial",
    "cloud_starter",
    "cloud_pro",
    "pro",
    "enterprise",
)

SAMPLE_CHANNELS = ("telegram", "signal", "discord", "whatsapp", "imessage")


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


# ── helper-level: shape ──────────────────────────────────────────────────────


def test_helper_returns_dict_shape(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram", "signal"],
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"channels", "unknown"}
    assert isinstance(out["channels"], list)
    assert isinstance(out["unknown"], list)


def test_helper_each_item_carries_channel_and_path(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram", "signal"],
    )
    for item in out["channels"]:
        assert set(item.keys()) == _ITEM_KEYS
        assert isinstance(item["channel"], str)
        assert isinstance(item["path"], list)


def test_helper_each_path_row_has_rung_and_spec_keys(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram", "signal"],
    )
    for item in out["channels"]:
        for row in item["path"]:
            assert set(row).issuperset(_RUNG_KEYS)
            assert set(row).issuperset(_SPEC_KEYS)


# ── parity + invariance pins ─────────────────────────────────────────────────


def test_helper_body_byte_equal_to_batch_delegate(ent):
    """Pin: body is byte-identical to :func:`channel_spec_path_batch`
    for every perspective. The perspective is validated but does NOT
    shape rows."""
    chans = ["telegram", "signal", "discord"]
    delegate = ent.channel_spec_path_batch(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, chans
    )
    for perspective in ALL_TIERS:
        out = ent.channel_spec_at_path_batch(
            perspective, ent.TIER_OSS, ent.TIER_ENTERPRISE, chans
        )
        assert out == delegate


def test_helper_per_item_path_byte_equal_to_scalar_at_path(ent):
    """Pin: per-channel ``path`` is byte-identical to the scalar
    :func:`channel_spec_at_path` payload for the same quadruple --
    scalar/batch no-drift contract."""
    chans = ["telegram", "signal", "discord", "slack"]
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, chans
    )
    by_id = {item["channel"]: item["path"] for item in out["channels"]}
    for cid in chans:
        scalar = ent.channel_spec_at_path(
            ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, cid
        )
        assert by_id[cid] == scalar


def test_helper_perspective_invariance_across_all_tiers(ent):
    """Perspective is validated but does NOT reshape ``path`` rows --
    the same ``(from, to, channels)`` yields byte-identical bodies for
    every purchasable perspective."""
    chans = ["telegram", "signal"]
    reference = ent.channel_spec_at_path_batch(
        ent.TIER_OSS, ent.TIER_OSS, ent.TIER_ENTERPRISE, chans
    )
    for perspective in ALL_TIERS:
        assert (
            ent.channel_spec_at_path_batch(
                perspective, ent.TIER_OSS, ent.TIER_ENTERPRISE, chans
            )
            == reference
        )


def test_helper_rung_walk_channel_agnostic(ent):
    """The walked rung sequence is channel-agnostic -- all per-item
    paths share the same rung sequence."""
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram", "signal", "discord"],
    )
    rung_sequences = [
        [row["rung"] for row in item["path"]] for item in out["channels"]
    ]
    assert len(rung_sequences) == 3
    assert rung_sequences[0] == rung_sequences[1] == rung_sequences[2]


def test_helper_every_row_free_and_allowed(ent):
    """Every chat-channel adapter is FREE at every tier -- so every row
    at every rung reports ``free=True`` / ``allowed=True`` /
    ``locked=False`` / ``entitled=True``, regardless of perspective or
    direction."""
    for perspective in ALL_TIERS:
        for endpoints in (
            (ent.TIER_OSS, ent.TIER_ENTERPRISE),
            (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        ):
            out = ent.channel_spec_at_path_batch(
                perspective,
                endpoints[0],
                endpoints[1],
                ["telegram", "slack", "discord"],
            )
            for item in out["channels"]:
                for row in item["path"]:
                    assert row["free"] is True
                    assert row["allowed"] is True
                    assert row["locked"] is False
                    assert row["entitled"] is True


# ── input normalisation ──────────────────────────────────────────────────────


def test_helper_supply_order_preserved(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["signal", "telegram", "discord"],
    )
    assert [item["channel"] for item in out["channels"]] == [
        "signal",
        "telegram",
        "discord",
    ]


def test_helper_normalises_channels(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["  TELEGRAM  ", "signal", "telegram", ""],
    )
    assert [item["channel"] for item in out["channels"]] == [
        "telegram",
        "signal",
    ]


def test_helper_normalises_perspective(ent):
    out = ent.channel_spec_at_path_batch(
        "  CLOUD_PRO  ",
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram"],
    )
    assert out is not None
    assert [item["channel"] for item in out["channels"]] == ["telegram"]


def test_helper_normalises_from_and_to(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        "  OSS  ",
        "  ENTERPRISE  ",
        ["telegram"],
    )
    assert out is not None
    assert [item["channel"] for item in out["channels"]] == ["telegram"]


# ── unknown-id handling ──────────────────────────────────────────────────────


def test_helper_unknown_channels_echoed(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram", "bogus_channel", "still_bogus"],
    )
    assert [item["channel"] for item in out["channels"]] == ["telegram"]
    assert set(out["unknown"]) == {"bogus_channel", "still_bogus"}


def test_helper_all_unknown_channels_yields_empty_channels(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["bogus_1", "bogus_2"],
    )
    assert out == {"channels": [], "unknown": ["bogus_1", "bogus_2"]}


# ── direction branches (delegates return the same body regardless of ───────
#    the perspective; direction is derived downstream on the HTTP layer) ────


def test_helper_identity_yields_empty_paths(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_OSS,
        ent.TIER_CLOUD_PRO,
        ent.TIER_CLOUD_PRO,
        ["telegram", "signal"],
    )
    assert out["unknown"] == []
    for item in out["channels"]:
        assert item["path"] == []


def test_helper_lateral_yields_one_row_paths(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_OSS,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ["telegram", "signal"],
    )
    for item in out["channels"]:
        assert len(item["path"]) == 1
        assert item["path"][0]["rung"] == ent.TIER_PRO


def test_helper_downgrade_walks_descending(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
        ent.TIER_OSS,
        ["telegram"],
    )
    assert out is not None
    for item in out["channels"]:
        ranks = [row["rung_rank"] for row in item["path"]]
        assert ranks == sorted(ranks, reverse=True)


def test_helper_upgrade_walks_ascending(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram"],
    )
    assert out is not None
    for item in out["channels"]:
        ranks = [row["rung_rank"] for row in item["path"]]
        assert ranks == sorted(ranks)


def test_helper_trial_accepted_as_perspective(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_TRIAL, ent.TIER_OSS, ent.TIER_ENTERPRISE, ["telegram"]
    )
    assert out is not None
    assert [item["channel"] for item in out["channels"]] == ["telegram"]


def test_helper_trial_accepted_as_from_and_to(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_TRIAL,
        ent.TIER_TRIAL,
        ["telegram"],
    )
    assert out is not None
    assert out["channels"][0]["path"] == []


# ── error / edge branches ────────────────────────────────────────────────────


def test_helper_unknown_perspective_returns_none(ent):
    assert (
        ent.channel_spec_at_path_batch(
            "not_a_tier",
            ent.TIER_OSS,
            ent.TIER_ENTERPRISE,
            ["telegram"],
        )
        is None
    )


def test_helper_empty_perspective_returns_none(ent):
    assert (
        ent.channel_spec_at_path_batch(
            "", ent.TIER_OSS, ent.TIER_ENTERPRISE, ["telegram"]
        )
        is None
    )


def test_helper_none_perspective_returns_none(ent):
    assert (
        ent.channel_spec_at_path_batch(
            None,  # type: ignore[arg-type]
            ent.TIER_OSS,
            ent.TIER_ENTERPRISE,
            ["telegram"],
        )
        is None
    )


def test_helper_unknown_from_tier_returns_none(ent):
    assert (
        ent.channel_spec_at_path_batch(
            ent.TIER_CLOUD_PRO,
            "not_a_tier",
            ent.TIER_ENTERPRISE,
            ["telegram"],
        )
        is None
    )


def test_helper_unknown_to_tier_returns_none(ent):
    assert (
        ent.channel_spec_at_path_batch(
            ent.TIER_CLOUD_PRO,
            ent.TIER_OSS,
            "not_a_tier",
            ["telegram"],
        )
        is None
    )


def test_helper_empty_channels_yields_empty_envelope(ent):
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, []
    )
    assert out == {"channels": [], "unknown": []}


def test_helper_garbage_inputs_never_raise(ent):
    assert ent.channel_spec_at_path_batch("", "", "", []) is None
    assert (
        ent.channel_spec_at_path_batch(None, None, None, None)  # type: ignore[arg-type]
        is None
    )
    assert (
        ent.channel_spec_at_path_batch("  ", "  ", "  ", "  ") is None
    )
    assert (
        ent.channel_spec_at_path_batch(
            ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, 42
        )
        == {"channels": [], "unknown": []}
    )


def test_helper_delegate_crash_returns_none(ent, monkeypatch):
    """A top-level delegation failure short-circuits to ``None`` and
    logs a warning."""

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "channel_spec_path_batch", boom)
    assert (
        ent.channel_spec_at_path_batch(
            ent.TIER_CLOUD_PRO,
            ent.TIER_OSS,
            ent.TIER_ENTERPRISE,
            ["telegram"],
        )
        is None
    )


def test_helper_row_failure_short_circuits_item(ent, monkeypatch):
    """A per-channel failure inside the delegate lands the channel in
    ``unknown[]`` while the rest of the batch keeps building."""
    real = ent.channel_spec_path

    def fake(f, t, cid):
        if cid == "signal":
            raise RuntimeError("boom")
        return real(f, t, cid)

    monkeypatch.setattr(ent, "channel_spec_path", fake)
    out = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO,
        ent.TIER_OSS,
        ent.TIER_ENTERPRISE,
        ["telegram", "signal"],
    )
    assert [item["channel"] for item in out["channels"]] == ["telegram"]
    assert "signal" in out["unknown"]


def test_helper_grace_and_enforce_yield_identical_output(ent, monkeypatch):
    """Resolver-independent: delegates to the same static per-tier
    maps so grace vs enforce yields byte-identical rows."""
    chans = ["telegram", "signal", "discord"]
    grace = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, chans
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.channel_spec_at_path_batch(
        ent.TIER_CLOUD_PRO, ent.TIER_OSS, ent.TIER_ENTERPRISE, chans
    )
    assert grace == enforced


# ── HTTP: /api/entitlement/channel-spec-at-path-batch ────────────────────────


def test_api_400_on_missing_tier(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        "?from=oss&to=enterprise&channels=telegram"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        "?tier=cloud_pro&to=enterprise&channels=telegram"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing from"


def test_api_400_on_missing_to(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&channels=telegram"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing to"


def test_api_400_on_missing_channels(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "supply channels=<csv>"


def test_api_400_on_empty_channels(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&channels="
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "supply channels=<csv>"


def test_api_404_on_unknown_perspective(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        "?tier=not_a_tier&from=oss&to=enterprise&channels=telegram"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"


def test_api_404_on_unknown_from_tier(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        "?tier=cloud_pro&from=not_a_tier&to=enterprise&channels=telegram"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "from"


def test_api_404_on_unknown_to_tier(client):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=not_a_tier&channels=telegram"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "to"


def test_api_happy_path_envelope_keys(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram,signal"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["direction"] == "upgrade"
    assert [item["channel"] for item in body["channels"]] == [
        "telegram",
        "signal",
    ]
    for item in body["channels"]:
        assert item["path"][-1]["rung"] == ent.TIER_ENTERPRISE


def test_api_direction_downgrade(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS}&channels=telegram"
    )
    body = r.get_json()
    assert body["direction"] == "downgrade"


def test_api_direction_lateral(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_PRO}&channels=telegram"
    )
    body = r.get_json()
    assert body["direction"] == "lateral"
    for item in body["channels"]:
        assert len(item["path"]) == 1
        assert item["path"][0]["rung"] == ent.TIER_PRO


def test_api_direction_identity(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO}&channels=telegram,signal"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    for item in body["channels"]:
        assert item["path"] == []


def test_api_unknown_channel_id_echoed(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram,bogus_channel"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["channel"] for item in body["channels"]] == ["telegram"]
    assert body["unknown"] == ["bogus_channel"]


def test_api_normalises_channels(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
        "&channels=%20TELEGRAM%20,signal,telegram"
    )
    body = r.get_json()
    assert [item["channel"] for item in body["channels"]] == [
        "telegram",
        "signal",
    ]


def test_api_normalises_tier_ids(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier=%20CLOUD_PRO%20&from=%20OSS%20"
        "&to=%20ENTERPRISE%20&channels=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE


def test_api_trial_accepted_as_perspective(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_TRIAL}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_TRIAL


def test_api_trial_accepted_as_endpoint(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_TRIAL}"
        f"&to={ent.TIER_TRIAL}&channels=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["channels"][0]["path"] == []


def test_api_per_item_path_matches_scalar_at_path_route(client, ent):
    """Pin: per-channel ``path`` in the batch response byte-equals the
    scalar ``/api/entitlement/channel-spec-at-path`` response for the
    same quadruple."""
    batch = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram,signal,discord"
    ).get_json()
    for item in batch["channels"]:
        scalar = client.get(
            "/api/entitlement/channel-spec-at-path"
            f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
            f"&to={ent.TIER_ENTERPRISE}&channel={item['channel']}"
        ).get_json()
        assert item["path"] == scalar["path"]


def test_api_per_item_path_matches_current_batch_route(client, ent):
    """Pin: per-channel ``path`` in the ``_at_path_batch`` response
    byte-equals the ``/channel-spec-path-batch`` response for the same
    ``(from, to, channels)`` triple -- perspective does not shape rows."""
    at_batch = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram,signal,discord"
    ).get_json()
    current = client.get(
        "/api/entitlement/channel-spec-path-batch"
        f"?from={ent.TIER_OSS}&to={ent.TIER_ENTERPRISE}"
        "&channels=telegram,signal,discord"
    ).get_json()
    assert at_batch["channels"] == current["channels"]
    assert at_batch["unknown"] == current["unknown"]


def test_api_envelope_ranks_populated(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram"
    )
    body = r.get_json()
    assert (
        isinstance(body["perspective_tier_rank"], int)
        and body["perspective_tier_rank"] >= 0
    )
    assert isinstance(body["from_rank"], int) and body["from_rank"] >= 0
    assert isinstance(body["to_rank"], int) and body["to_rank"] >= 0
    assert body["from_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["to_label"] == ent.tier_label(ent.TIER_ENTERPRISE)


def test_api_envelope_resolver_context_tail_present(client, ent):
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram"
    )
    body = r.get_json()
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert "grace" in body
    assert "enforced" in body
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


def test_api_never_5xx_on_helper_failure(client, ent, monkeypatch):
    """If ``channel_spec_at_path_batch`` raises deep in the helper, the
    endpoint must fall back to an empty envelope instead of 5xxing."""
    import clawmetry.entitlements as _ent

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(_ent, "channel_spec_at_path_batch", boom)
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channels"] == []
    assert body["unknown"] == []
    assert body["perspective_tier"] == ent.TIER_CLOUD_PRO


def test_api_row_failure_short_circuits_item(client, ent, monkeypatch):
    """A helper-level per-channel failure lands the channel in
    ``unknown[]`` while the rest of the batch keeps building -- the
    endpoint should render this without dropping to 5xx."""
    import clawmetry.entitlements as _ent

    real = _ent.channel_spec_path

    def fake(f, t, cid):
        if cid == "signal":
            raise RuntimeError("boom")
        return real(f, t, cid)

    monkeypatch.setattr(_ent, "channel_spec_path", fake)
    r = client.get(
        "/api/entitlement/channel-spec-at-path-batch"
        f"?tier={ent.TIER_CLOUD_PRO}&from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channels=telegram,signal"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [item["channel"] for item in body["channels"]] == ["telegram"]
    assert "signal" in body["unknown"]
