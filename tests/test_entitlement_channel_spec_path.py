"""Tests for ``clawmetry.entitlements.channel_spec_path(from, to, channel)``
+ the ``GET /api/entitlement/channel-spec-path`` endpoint.

Channel-axis twin of :func:`feature_spec_path` / :func:`runtime_spec_path`
-- the single-channel sibling of :func:`channel_catalog_path` and
perspective-walked sibling of :func:`channel_spec`. Lets a paywall /
channel-picker "how does THIS one channel look as I climb the ladder" UI
render every rung's ``allowed`` / ``locked`` / ``entitled`` status off
ONE round-trip.

Pins:

* rung walk byte-stable against :func:`tier_path`,
  :func:`tier_spec_path`, :func:`feature_spec_path`,
  :func:`runtime_spec_path` and :func:`channel_catalog_path` (same
  ``_PURCHASABLE_TIERS`` filter + same sort + same destination-sibling
  exclusion)
* per-rung row carries the ``_channel_spec_row`` body PLUS the three
  rung-identification keys (``rung``, ``rung_label``, ``rung_rank``);
  dropping the three ``rung*`` keys yields exact byte-equality with the
  LIVE :func:`channel_spec` row (every chat-channel adapter is FREE at
  every tier, so the row is invariant across the rung walk)
* the row equals the corresponding row in :func:`channel_catalog_path`
  once the outer ``channels`` list is projected onto the target channel
* every rung row is ``free=True`` / ``allowed=True`` / ``locked=False``
  / ``entitled=True`` regardless of the walked tier
* identity returns ``[]``
* lateral (same rank, different id) returns a single-row path
* trial accepted as an endpoint (lateral branch for ``to=trial``;
  ``from=trial`` walks intermediate rungs above)
* unknown / empty / garbage tier or channel ids return ``None`` and
  never raise
* grace vs enforce yields identical rows (helper walks the static
  per-tier maps via :func:`_channel_spec_row` +
  :func:`_hypothetical_entitlement`)
* API surface: 400 on missing args, 404 on unknown ids (with ``which``
  echoing ``tier`` or ``channel``), 200 envelope on happy path (incl.
  direction tag and ``channel`` echo), byte-equal with
  ``/channel-catalog-path`` when the outer catalog rows are projected
  onto the target channel
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
    "channel",
    "path",
}

_RUNG_KEYS = {"rung", "rung_label", "rung_rank"}
_SPEC_KEYS = {"id", "label", "free", "tier", "allowed", "locked", "entitled"}


# ── helper-level: shape + invariants ─────────────────────────────────────────


def test_returns_list(ent):
    path = ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram")
    assert isinstance(path, list)
    assert len(path) >= 1


def test_each_row_carries_rung_keys(ent):
    path = ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram")
    for row in path:
        assert set(row).issuperset(_RUNG_KEYS)
        assert row["rung_label"] == ent.tier_label(row["rung"])
        assert row["rung_rank"] == ent.tier_rank(row["rung"])


def test_each_row_carries_spec_keys(ent):
    path = ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram")
    for row in path:
        body = {k: v for k, v in row.items() if k not in _RUNG_KEYS}
        assert set(body.keys()) == _SPEC_KEYS


def test_per_rung_body_byte_equals_channel_spec(ent):
    """Dropping the three ``rung*`` keys from a path row yields exact
    byte-equality with :func:`channel_spec(channel)` -- every chat
    channel is FREE at every tier, so the row is invariant across the
    walk."""
    live = ent.channel_spec("telegram")
    path = ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram")
    for row in path:
        body = {k: v for k, v in row.items() if k not in _RUNG_KEYS}
        assert body == live


def test_per_rung_row_matches_channel_catalog_path_projection(ent):
    """The per-rung row must byte-equal the corresponding channel row
    from :func:`channel_catalog_path` after projecting the outer
    ``channels`` list onto the target channel id."""
    cat_path = ent.channel_catalog_path(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    spec_path = ent.channel_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram"
    )
    assert len(cat_path) == len(spec_path)
    for cat_row, spec_row in zip(cat_path, spec_path):
        # Project the catalog row onto the target channel + rung keys.
        projected = {
            "rung": cat_row["tier"],
            "rung_label": cat_row["tier_label"],
            "rung_rank": cat_row["tier_rank"],
            **next(c for c in cat_row["channels"] if c["id"] == "telegram"),
        }
        assert spec_row == projected


def test_all_rows_always_free_and_allowed(ent):
    for tid in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        for ch in ("telegram", "signal", "webchat"):
            for row in ent.channel_spec_path(ent.TIER_OSS, tid, ch):
                assert row["free"] is True
                assert row["allowed"] is True
                assert row["locked"] is False
                assert row["entitled"] is True
                assert row["tier"] == "free"


def test_first_row_is_first_step_above_from(ent):
    path = ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram")
    assert path[0]["rung"] == ent.TIER_CLOUD_STARTER


def test_last_row_is_destination(ent):
    path = ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram")
    assert path[-1]["rung"] == ent.TIER_ENTERPRISE


def test_rung_walk_byte_stable_against_tier_spec_path(ent):
    """Rung ids must match :func:`tier_spec_path`'s rung ``id`` field
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
        chan_rungs = [
            r["rung"] for r in ent.channel_spec_path(f, t, "telegram")
        ]
        spec_rungs = [r["id"] for r in ent.tier_spec_path(f, t)]
        assert chan_rungs == spec_rungs


def test_rung_walk_byte_stable_against_channel_catalog_path(ent):
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        chan_rungs = [
            r["rung"] for r in ent.channel_spec_path(f, t, "telegram")
        ]
        cat_rungs = [r["tier"] for r in ent.channel_catalog_path(f, t)]
        assert chan_rungs == cat_rungs


def test_rung_walk_byte_stable_against_tier_path(ent):
    for f, t in (
        (ent.TIER_OSS, ent.TIER_ENTERPRISE),
        (ent.TIER_ENTERPRISE, ent.TIER_OSS),
        (ent.TIER_TRIAL, ent.TIER_ENTERPRISE),
    ):
        chan_rungs = [
            r["rung"] for r in ent.channel_spec_path(f, t, "telegram")
        ]
        diff_rungs = [r["to"] for r in ent.tier_path(f, t)]
        assert chan_rungs == diff_rungs


def test_rung_walk_invariant_across_channels(ent):
    """The walked rung sequence is channel-agnostic -- swapping the
    channel must not move the rungs."""
    a = [
        r["rung"]
        for r in ent.channel_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram"
        )
    ]
    b = [
        r["rung"]
        for r in ent.channel_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "signal"
        )
    ]
    c = [
        r["rung"]
        for r in ent.channel_spec_path(
            ent.TIER_OSS, ent.TIER_ENTERPRISE, "webchat"
        )
    ]
    assert a == b == c


def test_ascending_walk_is_non_decreasing_in_rank(ent):
    path = ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram")
    walk_ranks = [row["rung_rank"] for row in path]
    assert walk_ranks == sorted(walk_ranks)


def test_descending_walk_is_non_increasing_in_rank(ent):
    path = ent.channel_spec_path(ent.TIER_ENTERPRISE, ent.TIER_OSS, "telegram")
    walk_ranks = [row["rung_rank"] for row in path]
    assert walk_ranks == sorted(walk_ranks, reverse=True)


def test_path_terminates_at_to_not_a_sibling(ent):
    """``pro`` and ``cloud_pro`` share rank 2 -- the path must end
    exactly at ``pro`` and exclude the same-rank sibling."""
    rungs = [
        r["rung"]
        for r in ent.channel_spec_path(ent.TIER_OSS, ent.TIER_PRO, "telegram")
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
        assert ent.channel_spec_path(tid, tid, "telegram") == []


def test_lateral_single_row(ent):
    """``cloud_pro`` and ``pro`` share rank 2 -- lateral branch yields
    a one-row path."""
    path = ent.channel_spec_path(ent.TIER_CLOUD_PRO, ent.TIER_PRO, "telegram")
    assert len(path) == 1
    assert path[0]["rung"] == ent.TIER_PRO


def test_trial_endpoint_via_lateral(ent):
    path = ent.channel_spec_path(ent.TIER_CLOUD_PRO, ent.TIER_TRIAL, "telegram")
    assert len(path) == 1
    assert path[0]["rung"] == ent.TIER_TRIAL


def test_trial_excluded_from_walked_intermediate_rungs(ent):
    path = ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram")
    for row in path:
        assert row["rung"] != ent.TIER_TRIAL


def test_every_known_channel_round_trips(ent):
    """Every id in ``ALL_CHANNELS`` yields a non-``None`` path."""
    for ch in ent.ALL_CHANNELS:
        path = ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, ch)
        assert path is not None, ch
        assert len(path) >= 1, ch
        for row in path:
            assert row["id"] == ch, ch


def test_unknown_tier_returns_none(ent):
    assert (
        ent.channel_spec_path("not_a_tier", ent.TIER_ENTERPRISE, "telegram")
        is None
    )
    assert (
        ent.channel_spec_path(ent.TIER_OSS, "still_not", "telegram") is None
    )


def test_unknown_channel_returns_none(ent):
    assert (
        ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "not_a_channel")
        is None
    )
    assert ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "") is None


def test_empty_and_garbage_inputs_never_raise(ent):
    assert ent.channel_spec_path("", "", "") is None
    assert ent.channel_spec_path(None, None, None) is None  # type: ignore[arg-type]
    assert ent.channel_spec_path("  ", "  ", "  ") is None
    assert ent.channel_spec_path(123, 456, 789) is None  # type: ignore[arg-type]


def test_case_and_whitespace_normalised(ent):
    a = ent.channel_spec_path(ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram")
    b = ent.channel_spec_path(
        "  OSS ", " ENTERPRISE  ", "  TELEGRAM "
    )
    assert a == b


def test_grace_and_enforce_yield_identical_rows(ent, monkeypatch):
    grace_rows = ent.channel_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced_rows = ent.channel_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram"
    )
    assert grace_rows == enforced_rows


def test_resolver_failure_still_returns_rows(ent, monkeypatch):
    """The helper walks via :func:`_hypothetical_entitlement`, not the
    live resolver, so a blown ``get_entitlement`` must NOT cause the
    walk to return ``None`` -- rows are still built."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    path = ent.channel_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram"
    )
    assert path is not None
    assert len(path) >= 1
    for row in path:
        assert row["free"] is True


def test_synth_failure_short_circuits_that_rung(ent, monkeypatch):
    """A :func:`_hypothetical_entitlement` explosion drops the rung
    without breaking the walk."""
    real = ent._hypothetical_entitlement

    def flaky(tier):
        if tier == ent.TIER_CLOUD_PRO:
            raise RuntimeError("simulated synth failure")
        return real(tier)

    monkeypatch.setattr(ent, "_hypothetical_entitlement", flaky)
    path = ent.channel_spec_path(
        ent.TIER_OSS, ent.TIER_ENTERPRISE, "telegram"
    )
    assert path is not None
    rungs = [row["rung"] for row in path]
    assert ent.TIER_CLOUD_PRO not in rungs
    assert ent.TIER_ENTERPRISE in rungs


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_400_on_missing_from(client):
    r = client.get(
        "/api/entitlement/channel-spec-path?to=cloud_pro&channel=telegram"
    )
    assert r.status_code == 400


def test_api_400_on_missing_to(client):
    r = client.get(
        "/api/entitlement/channel-spec-path?from=oss&channel=telegram"
    )
    assert r.status_code == 400


def test_api_400_on_missing_channel(client):
    r = client.get("/api/entitlement/channel-spec-path?from=oss&to=enterprise")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "missing channel"


def test_api_400_on_blank_from(client):
    r = client.get(
        "/api/entitlement/channel-spec-path?from=%20%20&to=enterprise&channel=telegram"
    )
    assert r.status_code == 400


def test_api_400_on_blank_channel(client):
    r = client.get(
        "/api/entitlement/channel-spec-path?from=oss&to=enterprise&channel=%20%20"
    )
    assert r.status_code == 400


def test_api_404_on_unknown_tier(client):
    r = client.get(
        "/api/entitlement/channel-spec-path?from=oss&to=not_a_tier&channel=telegram"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"
    assert "error" in body


def test_api_404_on_unknown_channel(client):
    r = client.get(
        "/api/entitlement/channel-spec-path?from=oss&to=enterprise&channel=bogus_xyz"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "channel"
    assert body["channel"] == "bogus_xyz"


def test_api_happy_path_ascending(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channel=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_ENTERPRISE
    assert body["channel"] == "telegram"
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]
    assert body["path"][-1]["rung"] == ent.TIER_ENTERPRISE


def test_api_happy_path_descending(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path?from={ent.TIER_ENTERPRISE}"
        f"&to={ent.TIER_OSS}&channel=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "downgrade"
    assert body["path"][-1]["rung"] == ent.TIER_OSS


def test_api_identity_empty_path(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_CLOUD_PRO}&channel=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_api_lateral_single_row(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path?from={ent.TIER_CLOUD_PRO}"
        f"&to={ent.TIER_PRO}&channel=telegram"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "lateral"
    assert len(body["path"]) == 1
    assert body["path"][0]["rung"] == ent.TIER_PRO


def test_api_rungs_match_tier_spec_path_route(client, ent):
    """API-level byte-equality: rung ids from ``/channel-spec-path``
    match rung ids from ``/tier-spec-path``."""
    a = client.get(
        f"/api/entitlement/channel-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channel=telegram"
    ).get_json()
    b = client.get(
        f"/api/entitlement/tier-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    assert [r["rung"] for r in a["path"]] == [r["id"] for r in b["path"]]


def test_api_rungs_match_channel_catalog_path_route(client, ent):
    """API-level byte-equality: rung ids from ``/channel-spec-path``
    match rung ids from ``/channel-catalog-path``."""
    a = client.get(
        f"/api/entitlement/channel-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channel=telegram"
    ).get_json()
    b = client.get(
        f"/api/entitlement/channel-catalog-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    assert [r["rung"] for r in a["path"]] == [r["tier"] for r in b["path"]]


def test_api_row_projects_onto_channel_catalog_path_row(client, ent):
    """Each ``/channel-spec-path`` row is byte-identical to the
    corresponding channel row from ``/channel-catalog-path`` after
    projecting the outer ``channels`` list onto the target channel id."""
    a = client.get(
        f"/api/entitlement/channel-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channel=telegram"
    ).get_json()
    b = client.get(
        f"/api/entitlement/channel-catalog-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}"
    ).get_json()
    for spec_row, cat_row in zip(a["path"], b["path"]):
        projected = {
            "rung": cat_row["tier"],
            "rung_label": cat_row["tier_label"],
            "rung_rank": cat_row["tier_rank"],
            **next(c for c in cat_row["channels"] if c["id"] == "telegram"),
        }
        assert spec_row == projected


def test_api_body_channel_field_is_lowercased(client, ent):
    r = client.get(
        f"/api/entitlement/channel-spec-path?from={ent.TIER_OSS}"
        f"&to={ent.TIER_ENTERPRISE}&channel=TELEGRAM"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["channel"] == "telegram"
