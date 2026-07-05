"""Tests for ``clawmetry.entitlements.preview_at`` +
``clawmetry.entitlements.preview_at_batch`` + the matching
``/api/entitlement/preview-at`` and ``/api/entitlement/preview-at-batch``
endpoints.

What-if sibling of :func:`preview` / :func:`preview_batch`: rendering the
full :meth:`Entitlement.to_dict` snapshot at a target tier from the
perspective of a hypothetical source tier. Fills the ``_at`` /
``_at_batch`` slots in the preview family alongside
:func:`tier_spec_at` / :func:`tier_spec_at_batch`,
:func:`feature_spec_at` / :func:`feature_spec_at_batch`,
:func:`runtime_spec_at` / :func:`runtime_spec_at_batch` so a
pricing-comparison UI can call ``X_at(perspective, target)`` uniformly
across the whole ``_at`` family.

Pins:

  - scalar body is byte-identical to :func:`_preview_row(target)` for
    every perspective (the perspective is validated but does not shape
    the row); pinned so the singular preview_at can never drift from
    the private row builder that also backs :func:`preview_path` /
    :func:`preview_path_batch`
  - each batch row body is byte-identical to
    :func:`preview_at(perspective, target)` for the same target (and
    therefore also byte-identical to :func:`_preview_row(target)`) --
    the scalar / batch no-drift contract
  - full :meth:`Entitlement.to_dict` shape with ``source="preview"``
    and ``grace=False`` so concrete per-tier capacity surfaces (a
    grace-mode preview would zero those out)
  - ``trial`` IS accepted as both perspective and target (lenient
    ``_at`` posture matching :func:`tier_spec_at`) -- unlike singular
    :func:`preview` which rejects trial
  - inputs normalised (whitespace stripped, lowercased, duplicates
    dropped, first-seen order preserved)
  - unknown target ids echoed in ``unknown[]`` instead of
    short-circuiting; unknown perspective ``tier`` returns ``None``
    (helper) / 400 (missing / blank) / 404 (unknown)
  - resolver-independent -- grace vs enforce yields byte-identical rows
  - never raises -- a per-row failure short-circuits that id into
    ``unknown[]`` and the rest of the batch keeps building; the
    endpoint always returns a 200 with the grace envelope on resolver
    crash so the pricing-page UI keeps rendering
"""
from __future__ import annotations

import importlib

import pytest


_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default -- ``preview_at`` is independent of
    either knob, so the fixture only needs to keep the live resolver
    from surprising the test."""
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


# ── scalar helper: perspective handling ──────────────────────────────────────


def test_scalar_unknown_perspective_returns_none(ent):
    assert ent.preview_at("bogus", "cloud_pro") is None


def test_scalar_blank_perspective_returns_none(ent):
    assert ent.preview_at("", "cloud_pro") is None
    assert ent.preview_at("   ", "cloud_pro") is None


def test_scalar_none_perspective_returns_none(ent):
    assert ent.preview_at(None, "cloud_pro") is None


def test_scalar_int_perspective_returns_none(ent):
    assert ent.preview_at(0, "cloud_pro") is None


def test_scalar_perspective_whitespace_and_case_normalised(ent):
    got = ent.preview_at("  CLOUD_PRO  ", "cloud_pro")
    assert got is not None
    assert got["tier"] == "cloud_pro"


def test_scalar_trial_accepted_as_perspective(ent):
    got = ent.preview_at(ent.TIER_TRIAL, "cloud_pro")
    assert got is not None
    assert got["tier"] == "cloud_pro"


# ── scalar helper: target handling ───────────────────────────────────────────


def test_scalar_unknown_target_returns_none(ent):
    assert ent.preview_at("cloud_pro", "bogus") is None


def test_scalar_blank_target_returns_none(ent):
    assert ent.preview_at("cloud_pro", "") is None
    assert ent.preview_at("cloud_pro", "   ") is None


def test_scalar_none_target_returns_none(ent):
    assert ent.preview_at("cloud_pro", None) is None


def test_scalar_trial_accepted_as_target(ent):
    """Unlike :func:`preview` (which rejects trial), :func:`preview_at`
    accepts trial as a target -- lenient ``_at`` posture."""
    got = ent.preview_at("cloud_pro", ent.TIER_TRIAL)
    assert got is not None
    assert got["tier"] == ent.TIER_TRIAL


def test_scalar_target_whitespace_and_case_normalised(ent):
    got = ent.preview_at("cloud_pro", "  CLOUD_PRO  ")
    assert got is not None
    assert got["tier"] == "cloud_pro"


# ── scalar helper: row shape + parity ────────────────────────────────────────


def test_scalar_row_shape_matches_preview_batch(ent):
    """The scalar row shape matches every row in
    :func:`preview_batch` byte-for-byte -- same
    ``Entitlement.to_dict`` shape, ``source="preview"``,
    ``grace=False``."""
    expected = set(ent._build(ent.TIER_CLOUD_PRO, "preview").to_dict().keys())
    row = ent.preview_at("cloud_pro", "cloud_pro")
    assert row is not None
    assert set(row.keys()) == expected


def test_scalar_parity_with_preview_row_across_all_perspectives(ent):
    """For every (perspective, target) pair, the scalar row is
    byte-identical to :func:`_preview_row(target)` -- the perspective is
    validated but does not shape the row. Pins the scalar-and-private-row
    no-drift contract."""
    for perspective in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            assert ent.preview_at(perspective, target) == ent._preview_row(
                target
            ), (perspective, target)


def test_scalar_source_is_preview(ent):
    """Every scalar row carries ``source="preview"`` so a UI never
    mistakes it for a live entitlement."""
    for perspective in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            row = ent.preview_at(perspective, target)
            assert row is not None
            assert row["source"] == "preview"


def test_scalar_grace_is_false(ent):
    """Every scalar row carries ``grace=False`` so per-tier capacity
    surfaces -- a grace-mode preview would zero those out."""
    for perspective in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            row = ent.preview_at(perspective, target)
            assert row is not None
            assert row["grace"] is False
            assert row["enforced"] is True


def test_scalar_perspective_does_not_shape_row(ent):
    """The perspective is validated but the returned row is identical
    across all perspectives -- byte-parity with :func:`_preview_row`."""
    baseline = ent.preview_at("oss", "cloud_pro")
    for perspective in ent._TIER_ORDER:
        assert ent.preview_at(perspective, "cloud_pro") == baseline, perspective


# ── batch helper: perspective handling ───────────────────────────────────────


def test_batch_unknown_perspective_returns_none(ent):
    assert ent.preview_at_batch("bogus", ["oss"]) is None


def test_batch_blank_perspective_returns_none(ent):
    assert ent.preview_at_batch("", ["oss"]) is None
    assert ent.preview_at_batch("   ", ["oss"]) is None


def test_batch_none_perspective_returns_none(ent):
    assert ent.preview_at_batch(None, ["oss"]) is None


def test_batch_int_perspective_returns_none(ent):
    assert ent.preview_at_batch(0, ["oss"]) is None


def test_batch_perspective_whitespace_and_case_normalised(ent):
    got = ent.preview_at_batch("  CLOUD_PRO  ", ["cloud_pro"])
    assert got is not None
    assert got["tiers"][0]["tier"] == "cloud_pro"


def test_batch_trial_accepted_as_perspective(ent):
    got = ent.preview_at_batch(ent.TIER_TRIAL, [ent.TIER_TRIAL])
    assert got is not None
    assert got["tiers"][0]["tier"] == ent.TIER_TRIAL


# ── batch helper: targets input handling ─────────────────────────────────────


def test_batch_empty_targets_returns_empty_envelope(ent):
    got = ent.preview_at_batch("cloud_pro", [])
    assert got == {"tiers": [], "unknown": []}


def test_batch_none_targets_returns_empty_envelope(ent):
    got = ent.preview_at_batch("cloud_pro", None)
    assert got == {"tiers": [], "unknown": []}


def test_batch_targets_string_csv_input(ent):
    got = ent.preview_at_batch(
        "cloud_pro", "oss,cloud_starter,cloud_pro"
    )
    assert got is not None
    assert [row["tier"] for row in got["tiers"]] == [
        "oss",
        "cloud_starter",
        "cloud_pro",
    ]


def test_batch_targets_whitespace_and_case_normalised(ent):
    got = ent.preview_at_batch("cloud_pro", ["  OSS ", "Cloud_Pro"])
    assert got is not None
    assert [row["tier"] for row in got["tiers"]] == ["oss", "cloud_pro"]


def test_batch_targets_duplicates_dropped_first_seen_wins(ent):
    got = ent.preview_at_batch(
        "cloud_pro", ["oss", "cloud_pro", "oss", "cloud_pro"]
    )
    assert got is not None
    assert [row["tier"] for row in got["tiers"]] == ["oss", "cloud_pro"]


def test_batch_targets_supply_order_preserved(ent):
    got = ent.preview_at_batch(
        "cloud_pro", ["cloud_pro", "oss", "enterprise", "cloud_starter"]
    )
    assert got is not None
    assert [row["tier"] for row in got["tiers"]] == [
        "cloud_pro",
        "oss",
        "enterprise",
        "cloud_starter",
    ]


def test_batch_targets_unknown_ids_echoed_in_unknown(ent):
    got = ent.preview_at_batch(
        "cloud_pro", ["oss", "bogus", "cloud_pro", "also_bogus"]
    )
    assert got is not None
    assert [row["tier"] for row in got["tiers"]] == ["oss", "cloud_pro"]
    assert got["unknown"] == ["bogus", "also_bogus"]


def test_batch_targets_unknown_only_returns_empty_tiers(ent):
    got = ent.preview_at_batch("cloud_pro", ["bogus", "also_bogus"])
    assert got is not None
    assert got["tiers"] == []
    assert got["unknown"] == ["bogus", "also_bogus"]


def test_batch_trial_accepted_as_target(ent):
    """Lenient ``_at`` posture matching :func:`preview_at` -- trial is
    a valid target even though ``preview_batch`` excludes it."""
    got = ent.preview_at_batch("cloud_pro", [ent.TIER_TRIAL])
    assert got is not None
    assert got["tiers"][0]["tier"] == ent.TIER_TRIAL


# ── batch helper: row shape + parity ─────────────────────────────────────────


def test_batch_row_shape_matches_to_dict(ent):
    expected = set(ent._build(ent.TIER_CLOUD_PRO, "preview").to_dict().keys())
    got = ent.preview_at_batch(
        "cloud_pro", ["oss", "cloud_pro", "enterprise"]
    )
    assert got is not None
    for row in got["tiers"]:
        assert set(row.keys()) == expected


def test_batch_parity_with_scalar_preview_at(ent):
    """For every (perspective, target) pair, the batch row is
    byte-identical to the scalar :func:`preview_at`. Pins the
    scalar/batch no-drift contract."""
    for perspective in ent._TIER_ORDER:
        got = ent.preview_at_batch(perspective, list(ent._TIER_ORDER))
        assert got is not None
        rows_by_id = {row["tier"]: row for row in got["tiers"]}
        for target in ent._TIER_ORDER:
            assert rows_by_id[target] == ent.preview_at(
                perspective, target
            ), (perspective, target)


def test_batch_parity_with_preview_row(ent):
    """Each returned row also matches :func:`_preview_row(target)` --
    three-way parity (scalar / private / batch), pinning the same
    invariant :func:`preview_path` / :func:`preview_path_batch` rely on."""
    for perspective in ent._TIER_ORDER:
        got = ent.preview_at_batch(perspective, list(ent._TIER_ORDER))
        assert got is not None
        for row in got["tiers"]:
            assert row == ent._preview_row(row["tier"]), (
                perspective,
                row["tier"],
            )


def test_batch_source_is_preview(ent):
    got = ent.preview_at_batch("cloud_pro", list(ent._TIER_ORDER))
    assert got is not None
    for row in got["tiers"]:
        assert row["source"] == "preview"


def test_batch_grace_is_false(ent):
    got = ent.preview_at_batch("cloud_pro", list(ent._TIER_ORDER))
    assert got is not None
    for row in got["tiers"]:
        assert row["grace"] is False
        assert row["enforced"] is True


def test_batch_perspective_does_not_shape_rows(ent):
    """Same targets across shifting perspective yields byte-identical
    tiers[] -- confirms the perspective is validated only, not folded
    into the row body."""
    baseline = ent.preview_at_batch(
        "oss", ["oss", "cloud_pro", "enterprise"]
    )
    for perspective in ent._TIER_ORDER:
        got = ent.preview_at_batch(
            perspective, ["oss", "cloud_pro", "enterprise"]
        )
        assert got == baseline, perspective


# ── resolver independence ────────────────────────────────────────────────────


def test_scalar_resolver_independent_across_enforcement(ent, monkeypatch):
    grace = ent.preview_at("cloud_pro", "cloud_pro")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.preview_at("cloud_pro", "cloud_pro")
    assert grace == enforced


def test_batch_resolver_independent_across_enforcement(ent, monkeypatch):
    grace = ent.preview_at_batch(
        "cloud_pro", ["oss", "cloud_pro", "enterprise"]
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.preview_at_batch(
        "cloud_pro", ["oss", "cloud_pro", "enterprise"]
    )
    assert grace == enforced


# ── never-raises ─────────────────────────────────────────────────────────────


def test_batch_never_raises_when_row_builder_crashes(ent, monkeypatch):
    """A per-row failure short-circuits that id into ``unknown[]`` and
    the rest of the batch keeps building."""
    orig = ent._preview_row

    def _boom(tier):
        if tier == "cloud_pro":
            raise RuntimeError("boom")
        return orig(tier)

    monkeypatch.setattr(ent, "_preview_row", _boom)
    got = ent.preview_at_batch(
        "enterprise", ["oss", "cloud_pro", "enterprise"]
    )
    assert got is not None
    assert [row["tier"] for row in got["tiers"]] == ["oss", "enterprise"]
    assert got["unknown"] == ["cloud_pro"]


# ── HTTP endpoint: /preview-at ───────────────────────────────────────────────


def test_endpoint_scalar_returns_row(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at?tier=cloud_pro&target=cloud_pro"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == "cloud_pro"
    assert body["target"] == "cloud_pro"
    assert body["preview"]["tier"] == "cloud_pro"


def test_endpoint_scalar_target_trial_accepted(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at?tier=cloud_pro&target=trial"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["preview"]["tier"] == ent.TIER_TRIAL


def test_endpoint_scalar_missing_tier_returns_400(client, ent):
    resp = client.get("/api/entitlement/preview-at?target=cloud_pro")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "missing tier"


def test_endpoint_scalar_missing_target_returns_400(client, ent):
    resp = client.get("/api/entitlement/preview-at?tier=cloud_pro")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "missing target"


def test_endpoint_scalar_unknown_tier_returns_404(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at?tier=bogus&target=cloud_pro"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_endpoint_scalar_unknown_target_returns_404(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at?tier=cloud_pro&target=bogus"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown target"
    assert body["which"] == "target"
    assert body["target"] == "bogus"


def test_endpoint_scalar_lowercases_and_trims(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at?tier=%20CLOUD_PRO%20&target=%20CLOUD_PRO%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == "cloud_pro"
    assert body["target"] == "cloud_pro"


def test_endpoint_scalar_parity_with_helper(client, ent):
    for perspective in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            resp = client.get(
                f"/api/entitlement/preview-at"
                f"?tier={perspective}&target={target}"
            )
            assert resp.status_code == 200, (perspective, target)
            assert resp.get_json()["preview"] == ent.preview_at(
                perspective, target
            ), (perspective, target)


# ── HTTP endpoint: /preview-at-batch ─────────────────────────────────────────


def test_endpoint_batch_returns_rows_and_envelope(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch"
        "?tier=cloud_pro&targets=oss,cloud_pro,enterprise"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert [row["tier"] for row in body["tiers"]] == [
        "oss",
        "cloud_pro",
        "enterprise",
    ]
    assert body["unknown"] == []
    assert _ENVELOPE_KEYS.issubset(body.keys())
    assert body["perspective_tier"] == "cloud_pro"
    assert body["perspective_tier_rank"] == ent.tier_rank("cloud_pro")


def test_endpoint_batch_missing_tier_returns_400(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch?targets=oss"
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "missing tier"


def test_endpoint_batch_blank_tier_returns_400(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch?tier=%20%20&targets=oss"
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "missing tier"


def test_endpoint_batch_unknown_tier_returns_404(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch?tier=bogus&targets=oss"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_endpoint_batch_missing_targets_returns_400(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch?tier=cloud_pro"
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "supply targets=<csv>"


def test_endpoint_batch_blank_targets_returns_400(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch?tier=cloud_pro&targets=,,,"
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "supply targets=<csv>"


def test_endpoint_batch_unknown_only_returns_200(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch"
        "?tier=cloud_pro&targets=bogus,also_bogus"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == ["bogus", "also_bogus"]
    assert body["perspective_tier"] == "cloud_pro"


def test_endpoint_batch_lowercases_tier_and_targets(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch"
        "?tier=CLOUD_PRO&targets=OSS,Cloud_Pro"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert [row["tier"] for row in body["tiers"]] == ["oss", "cloud_pro"]


def test_endpoint_batch_envelope_carries_current_tier(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch?tier=cloud_pro&targets=oss"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    resolved = ent.get_entitlement()
    assert body["current_tier"] == resolved.tier
    assert body["current_tier_rank"] == ent.tier_rank(resolved.tier)
    assert body["grace"] is bool(resolved.grace)
    assert body["enforced"] == ent.is_enforced()


def test_endpoint_batch_trial_accepted_as_target(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch?tier=cloud_pro&targets=trial"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"][0]["tier"] == ent.TIER_TRIAL


def test_endpoint_batch_row_parity_with_helper(client, ent):
    resp = client.get(
        "/api/entitlement/preview-at-batch"
        "?tier=cloud_pro&targets=oss,cloud_starter,cloud_pro,enterprise"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    helper = ent.preview_at_batch(
        "cloud_pro", ["oss", "cloud_starter", "cloud_pro", "enterprise"]
    )
    assert body["tiers"] == helper["tiers"]
    assert body["unknown"] == helper["unknown"]


def test_endpoint_batch_never_5xxs_when_resolver_crashes(
    client, ent, monkeypatch
):
    def _boom(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "preview_at_batch", _boom)
    resp = client.get(
        "/api/entitlement/preview-at-batch?tier=cloud_pro&targets=oss"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["unknown"] == []
    assert body["perspective_tier"] == "cloud_pro"
    assert body["current_tier"] == "oss"
    assert body["grace"] is True
    assert body["enforced"] is False
