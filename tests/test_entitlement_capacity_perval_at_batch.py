"""Tests for the per-value ``_at_batch`` capacity-axis helpers and endpoints:

* :func:`clawmetry.entitlements.min_tier_for_channel_count_at_batch`
* :func:`clawmetry.entitlements.min_tier_for_retention_window_at_batch`
* :func:`clawmetry.entitlements.min_tier_for_node_count_at_batch`
* :func:`clawmetry.entitlements.tiers_for_channel_count_at_batch`
* :func:`clawmetry.entitlements.tiers_for_retention_window_at_batch`
* :func:`clawmetry.entitlements.tiers_for_node_count_at_batch`
* ``GET /api/entitlement/min-tier-for-channel-count-at-batch?tier=<p>&counts=…``
* ``GET /api/entitlement/min-tier-for-node-count-at-batch?tier=<p>&counts=…``
* ``GET /api/entitlement/min-tier-for-retention-window-at-batch?tier=<p>&days=…``
* ``GET /api/entitlement/tiers-for-channel-count-at-batch?tier=<p>&counts=…``
* ``GET /api/entitlement/tiers-for-node-count-at-batch?tier=<p>&counts=…``
* ``GET /api/entitlement/tiers-for-retention-window-at-batch?tier=<p>&days=…``

Fill the last ``_at_batch`` slots on the three scalar capacity axes
(channel_count / retention_window / node_count) alongside the existing
per-value ``/min-tier-for-<axis>-batch`` / ``/tiers-for-<axis>-batch``
(no perspective) and the singular ``/min-tier-for-<axis>-at`` /
``/tiers-for-<axis>-at`` (perspective + single value) so a pricing-
matrix walkthrough can hit every per-value ``_at_batch`` axis at a
fixed ``tier=<perspective>`` with a uniform URL.

These tests pin:

  * helper: perspective validation (empty / non-string / unknown -> None)
  * helper: per-row parity with the bare batch (rows are perspective-
    independent -- the ``_at`` prefix does NOT shape rows)
  * helper: bad-input rows collapse to the all-``None`` shape rather
    than raising or dropping (delegates to the bare batch)
  * helper: retention batch admits ``None`` / case-insensitive
    ``"unlimited"`` as the unlimited sentinel; the two count axes reject
  * helper: empty / None / non-iterable values -> ``[]``
  * helper: grace vs enforce parity (byte-identical rows across modes)
  * helper: never raises on a delegate crash (returns ``None``)
  * API: happy path envelope + per-row body byte-identical to the bare
    per-value batch endpoint body (minus the perspective envelope)
  * API: cross-endpoint parity vs
    ``/min-tier-for-<axis>-batch?<param>=<vs>`` /
    ``/tiers-for-<axis>-batch?<param>=<vs>`` for every value in the batch
  * API: 400 on missing / blank ``tier=`` or values arg
  * API: 404 on unknown ``tier=``
  * API: non-int tokens do not fail the batch (per-row all-``None`` row)
  * API: unlimited round-trips to ``item=null`` / ``label="unlimited"``
    (retention only, case-insensitive)
  * API: resolver + perspective envelope carried on happy path
  * API: never-5xxs on a delegate crash (returns perspective-carrying
    grace body with empty rows)
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
    "kind",
    "count",
    "rows",
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


_MIN_TIER_ROW_KEYS = {
    "item",
    "kind",
    "label",
    "free",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
}


_TIERS_ROW_KEYS = {
    "item",
    "kind",
    "label",
    "free",
    "min_tier",
    "min_tier_label",
    "min_tier_rank",
    "tiers",
}


_MIN_TIER_HELPERS = (
    ("min_tier_for_channel_count_at_batch", [1, 5, 25]),
    ("min_tier_for_node_count_at_batch", [1, 3, 10]),
    ("min_tier_for_retention_window_at_batch", [7, 30, 90]),
)

_TIERS_HELPERS = (
    ("tiers_for_channel_count_at_batch", [1, 5, 25]),
    ("tiers_for_node_count_at_batch", [1, 3, 10]),
    ("tiers_for_retention_window_at_batch", [7, 30, 90]),
)


# ── Helper: min_tier_for_<axis>_at_batch shape / delegation ──────────────


@pytest.mark.parametrize("name,values", _MIN_TIER_HELPERS)
def test_min_tier_at_batch_returns_list(ent, name, values):
    fn = getattr(ent, name)
    rows = fn(ent.TIER_CLOUD_STARTER, values)
    assert isinstance(rows, list)
    assert len(rows) == len(values)


@pytest.mark.parametrize("name,values", _MIN_TIER_HELPERS)
def test_min_tier_at_batch_empty_perspective_is_none(ent, name, values):
    assert getattr(ent, name)("", values) is None


@pytest.mark.parametrize("name,values", _MIN_TIER_HELPERS)
def test_min_tier_at_batch_none_perspective_is_none(ent, name, values):
    assert getattr(ent, name)(None, values) is None


@pytest.mark.parametrize("name,values", _MIN_TIER_HELPERS)
def test_min_tier_at_batch_unknown_perspective_is_none(ent, name, values):
    assert getattr(ent, name)("no-such-tier", values) is None


@pytest.mark.parametrize("name,values", _MIN_TIER_HELPERS)
def test_min_tier_at_batch_non_string_perspective_is_none(ent, name, values):
    assert getattr(ent, name)(42, values) is None


@pytest.mark.parametrize("name,values", _MIN_TIER_HELPERS)
def test_min_tier_at_batch_none_values_delegates_to_empty(ent, name, values):
    """``None`` iterable propagates through the delegate."""
    assert getattr(ent, name)(ent.TIER_CLOUD_STARTER, None) == []


@pytest.mark.parametrize("name,values", _MIN_TIER_HELPERS)
def test_min_tier_at_batch_row_equals_bare_batch_all_perspectives(
    ent, name, values
):
    """Rows are perspective-independent -- byte-equal to the bare batch
    delegate for every ``perspective_tier`` in :data:`_TIER_ORDER`."""
    bare_name = name.replace("_at_batch", "_batch")
    bare = getattr(ent, bare_name)(values)
    for perspective in ent._TIER_ORDER:
        assert getattr(ent, name)(perspective, values) == bare


def test_min_tier_at_batch_retention_admits_unlimited(ent):
    rows = ent.min_tier_for_retention_window_at_batch(
        ent.TIER_CLOUD_STARTER, [7, None, "unlimited", "UNLIMITED"]
    )
    keys = [row["key"] for row in rows]
    assert "unlimited" in keys
    unl = next(r for r in rows if r["key"] == "unlimited")
    assert unl["min_tier"] == ent.TIER_ENTERPRISE


@pytest.mark.parametrize(
    "name,values",
    [
        ("min_tier_for_channel_count_at_batch", [1, 5]),
        ("min_tier_for_node_count_at_batch", [1, 3]),
    ],
)
def test_min_tier_at_batch_count_axes_reject_unlimited(ent, name, values):
    """``unlimited`` on the two integer-only count axes must NOT
    silently mis-route to Enterprise; it collapses to the all-``None``
    shape via the singular helper's None-on-bad-input posture."""
    rows = getattr(ent, name)(ent.TIER_CLOUD_STARTER, ["unlimited"])
    assert len(rows) == 1
    assert rows[0]["min_tier"] is None


@pytest.mark.parametrize("name,values", _MIN_TIER_HELPERS)
def test_min_tier_at_batch_grace_vs_enforce_same_rows(
    monkeypatch, ent, name, values
):
    grace = getattr(ent, name)(ent.TIER_CLOUD_STARTER, values)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = getattr(ent, name)(ent.TIER_CLOUD_STARTER, values)
    assert grace == enforced


@pytest.mark.parametrize("name,values", _MIN_TIER_HELPERS)
def test_min_tier_at_batch_never_raises(ent, monkeypatch, name, values):
    bare_name = name.replace("_at_batch", "_batch")

    def _boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, bare_name, _boom)
    assert getattr(ent, name)(ent.TIER_CLOUD_STARTER, values) is None


# ── Helper: tiers_for_<axis>_at_batch shape / delegation ─────────────────


@pytest.mark.parametrize("name,values", _TIERS_HELPERS)
def test_tiers_at_batch_returns_list(ent, name, values):
    fn = getattr(ent, name)
    rows = fn(ent.TIER_CLOUD_STARTER, values)
    assert isinstance(rows, list)
    assert len(rows) == len(values)


@pytest.mark.parametrize("name,values", _TIERS_HELPERS)
def test_tiers_at_batch_empty_perspective_is_none(ent, name, values):
    assert getattr(ent, name)("", values) is None


@pytest.mark.parametrize("name,values", _TIERS_HELPERS)
def test_tiers_at_batch_unknown_perspective_is_none(ent, name, values):
    assert getattr(ent, name)("no-such-tier", values) is None


@pytest.mark.parametrize("name,values", _TIERS_HELPERS)
def test_tiers_at_batch_none_values_delegates_to_empty(ent, name, values):
    assert getattr(ent, name)(ent.TIER_CLOUD_STARTER, None) == []


@pytest.mark.parametrize("name,values", _TIERS_HELPERS)
def test_tiers_at_batch_row_equals_bare_batch_all_perspectives(
    ent, name, values
):
    bare_name = name.replace("_at_batch", "_batch")
    bare = getattr(ent, bare_name)(values)
    for perspective in ent._TIER_ORDER:
        assert getattr(ent, name)(perspective, values) == bare


def test_tiers_at_batch_retention_admits_unlimited(ent):
    rows = ent.tiers_for_retention_window_at_batch(
        ent.TIER_CLOUD_STARTER, [7, "unlimited"]
    )
    labels = [r.get("label") for r in rows]
    assert "unlimited" in labels
    unl = next(r for r in rows if r["label"] == "unlimited")
    assert unl["min_tier"] == ent.TIER_ENTERPRISE
    assert unl["item"] is None


@pytest.mark.parametrize("name,values", _TIERS_HELPERS)
def test_tiers_at_batch_grace_vs_enforce_same_rows(
    monkeypatch, ent, name, values
):
    grace = getattr(ent, name)(ent.TIER_CLOUD_STARTER, values)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = getattr(ent, name)(ent.TIER_CLOUD_STARTER, values)
    assert grace == enforced


@pytest.mark.parametrize("name,values", _TIERS_HELPERS)
def test_tiers_at_batch_never_raises(ent, monkeypatch, name, values):
    bare_name = name.replace("_at_batch", "_batch")

    def _boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, bare_name, _boom)
    assert getattr(ent, name)(ent.TIER_CLOUD_STARTER, values) is None


# ── API: min-tier-for-<axis>-at-batch endpoints ──────────────────────────


_MIN_TIER_ENDPOINTS = (
    ("channel-count", "counts", "1,5,10", "channel_count"),
    ("node-count", "counts", "1,3,5", "node_count"),
    ("retention-window", "days", "7,30,90", "retention_window"),
)


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_happy_path(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}={values}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["kind"] == kind
    assert body["count"] == len(values.split(","))
    assert body["perspective_tier"] == "cloud_pro"
    assert body["perspective_tier_label"] == "Pro"
    for row in body["rows"]:
        assert set(row.keys()) == _MIN_TIER_ROW_KEYS
        assert row["kind"] == kind


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_rows_equal_bare(client, path, arg, values, kind):
    r_at = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}={values}"
    )
    r_bare = client.get(
        f"/api/entitlement/min-tier-for-{path}-batch?{arg}={values}"
    )
    assert r_at.status_code == 200
    assert r_bare.status_code == 200
    assert r_at.get_json()["rows"] == r_bare.get_json()["rows"]


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_row_equals_singular_per_value(
    client, path, arg, values, kind
):
    """Every row byte-equals the perspective-scoped singular endpoint
    body minus the resolver envelope."""
    singular_arg = "days" if arg == "days" else "count"
    r_at = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}={values}"
    )
    body = r_at.get_json()
    for token, row in zip(values.split(","), body["rows"]):
        singular = client.get(
            f"/api/entitlement/min-tier-for-{path}-at"
            f"?tier=cloud_pro&{singular_arg}={token}"
        )
        sbody = singular.get_json()
        for key in _MIN_TIER_ROW_KEYS:
            assert row[key] == sbody[key], (
                f"row/singular drift on {key}={token}: {row[key]!r} vs "
                f"{sbody[key]!r}"
            )


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_missing_tier_400(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch?{arg}={values}"
    )
    assert r.status_code == 400
    assert "tier" in r.get_json()["error"]


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_blank_tier_400(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch"
        f"?tier=&{arg}={values}"
    )
    assert r.status_code == 400


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_missing_values_400(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch?tier=cloud_pro"
    )
    assert r.status_code == 400


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_blank_values_400(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}="
    )
    assert r.status_code == 400


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_unknown_tier_404(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch"
        f"?tier=no-such-tier&{arg}={values}"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert "unknown" in body["error"]
    assert body["tier"] == "no-such-tier"


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_non_int_row_does_not_fail_batch(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}=1,bogus,5"
    )
    assert r.status_code == 200
    body = r.get_json()
    # 1 + 5 + bogus (echoes as key 'bogus' via delegate's None-on-bad-input)
    assert body["count"] == 3
    bogus_row = next(r for r in body["rows"] if r["label"] is None)
    assert bogus_row["required_tier"] is None


def test_api_min_tier_at_batch_retention_unlimited(client):
    r = client.get(
        "/api/entitlement/min-tier-for-retention-window-at-batch"
        "?tier=cloud_pro&days=7,UNLIMITED"
    )
    assert r.status_code == 200
    body = r.get_json()
    unl = next(row for row in body["rows"] if row["label"] == "unlimited")
    assert unl["item"] is None
    assert unl["required_tier"] == "enterprise"


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch, path, arg, values, kind
):
    def _boom(*_a, **_k):
        raise RuntimeError("resolver on fire")

    monkeypatch.setattr(
        ent,
        f"min_tier_for_{kind}_at_batch",
        _boom,
    )
    r = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}={values}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["rows"] == []
    assert body["count"] == 0
    assert body["perspective_tier"] == "cloud_pro"


# ── API: tiers-for-<axis>-at-batch endpoints ─────────────────────────────


_TIERS_ENDPOINTS = _MIN_TIER_ENDPOINTS


@pytest.mark.parametrize(
    "path,arg,values,kind", _TIERS_ENDPOINTS
)
def test_api_tiers_at_batch_happy_path(client, path, arg, values, kind):
    r = client.get(
        f"/api/entitlement/tiers-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}={values}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["kind"] == kind
    assert body["count"] == len(values.split(","))
    assert body["perspective_tier"] == "cloud_pro"
    for row in body["rows"]:
        assert set(row.keys()) == _TIERS_ROW_KEYS
        assert row["kind"] == kind


@pytest.mark.parametrize(
    "path,arg,values,kind", _TIERS_ENDPOINTS
)
def test_api_tiers_at_batch_rows_equal_bare(
    client, path, arg, values, kind
):
    r_at = client.get(
        f"/api/entitlement/tiers-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}={values}"
    )
    r_bare = client.get(
        f"/api/entitlement/tiers-for-{path}-batch?{arg}={values}"
    )
    assert r_at.status_code == 200
    assert r_bare.status_code == 200
    assert r_at.get_json()["rows"] == r_bare.get_json()["rows"]


@pytest.mark.parametrize(
    "path,arg,values,kind", _TIERS_ENDPOINTS
)
def test_api_tiers_at_batch_missing_tier_400(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/tiers-for-{path}-at-batch?{arg}={values}"
    )
    assert r.status_code == 400


@pytest.mark.parametrize(
    "path,arg,values,kind", _TIERS_ENDPOINTS
)
def test_api_tiers_at_batch_missing_values_400(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/tiers-for-{path}-at-batch?tier=cloud_pro"
    )
    assert r.status_code == 400


@pytest.mark.parametrize(
    "path,arg,values,kind", _TIERS_ENDPOINTS
)
def test_api_tiers_at_batch_unknown_tier_404(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/tiers-for-{path}-at-batch"
        f"?tier=no-such-tier&{arg}={values}"
    )
    assert r.status_code == 404


@pytest.mark.parametrize(
    "path,arg,values,kind", _TIERS_ENDPOINTS
)
def test_api_tiers_at_batch_non_int_row_does_not_fail_batch(
    client, path, arg, values, kind
):
    r = client.get(
        f"/api/entitlement/tiers-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}=1,bogus,5"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 3
    bogus_row = next(row for row in body["rows"] if row["label"] is None)
    assert bogus_row["min_tier"] is None
    assert bogus_row["tiers"] == []


def test_api_tiers_at_batch_retention_unlimited(client):
    r = client.get(
        "/api/entitlement/tiers-for-retention-window-at-batch"
        "?tier=cloud_pro&days=7,unlimited"
    )
    assert r.status_code == 200
    body = r.get_json()
    unl = next(row for row in body["rows"] if row["label"] == "unlimited")
    assert unl["item"] is None
    assert unl["min_tier"] == "enterprise"


@pytest.mark.parametrize(
    "path,arg,values,kind", _TIERS_ENDPOINTS
)
def test_api_tiers_at_batch_never_5xxs_on_delegate_crash(
    client, ent, monkeypatch, path, arg, values, kind
):
    def _boom(*_a, **_k):
        raise RuntimeError("resolver on fire")

    monkeypatch.setattr(
        ent,
        f"tiers_for_{kind}_at_batch",
        _boom,
    )
    r = client.get(
        f"/api/entitlement/tiers-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}={values}"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["rows"] == []
    assert body["count"] == 0
    assert body["perspective_tier"] == "cloud_pro"


# ── Cross-endpoint envelope-parity ───────────────────────────────────────


def test_uniform_envelope_keys_across_min_tier_endpoints(client):
    """All three ``min-tier-for-<axis>-at-batch`` endpoints emit the
    same envelope keys so a pricing UI switching axes reads the same
    shape."""
    envelopes = []
    for path, arg, values, _ in _MIN_TIER_ENDPOINTS:
        r = client.get(
            f"/api/entitlement/min-tier-for-{path}-at-batch"
            f"?tier=cloud_pro&{arg}={values}"
        )
        envelopes.append(set(r.get_json().keys()))
    assert envelopes[0] == envelopes[1] == envelopes[2] == _ENVELOPE_KEYS


def test_uniform_envelope_keys_across_tiers_endpoints(client):
    envelopes = []
    for path, arg, values, _ in _TIERS_ENDPOINTS:
        r = client.get(
            f"/api/entitlement/tiers-for-{path}-at-batch"
            f"?tier=cloud_pro&{arg}={values}"
        )
        envelopes.append(set(r.get_json().keys()))
    assert envelopes[0] == envelopes[1] == envelopes[2] == _ENVELOPE_KEYS


# ── Perspective-independence: URL parity across perspectives ─────────────


@pytest.mark.parametrize(
    "path,arg,values,kind", _MIN_TIER_ENDPOINTS
)
def test_api_min_tier_at_batch_rows_perspective_independent(
    client, path, arg, values, kind
):
    """Rows are perspective-independent -- byte-equal across every
    valid ``tier=<p>`` argument."""
    baseline = client.get(
        f"/api/entitlement/min-tier-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}={values}"
    ).get_json()["rows"]
    for tier in ("oss", "cloud_starter", "trial", "enterprise"):
        r = client.get(
            f"/api/entitlement/min-tier-for-{path}-at-batch"
            f"?tier={tier}&{arg}={values}"
        )
        assert r.get_json()["rows"] == baseline


@pytest.mark.parametrize(
    "path,arg,values,kind", _TIERS_ENDPOINTS
)
def test_api_tiers_at_batch_rows_perspective_independent(
    client, path, arg, values, kind
):
    baseline = client.get(
        f"/api/entitlement/tiers-for-{path}-at-batch"
        f"?tier=cloud_pro&{arg}={values}"
    ).get_json()["rows"]
    for tier in ("oss", "cloud_starter", "trial", "enterprise"):
        r = client.get(
            f"/api/entitlement/tiers-for-{path}-at-batch"
            f"?tier={tier}&{arg}={values}"
        )
        assert r.get_json()["rows"] == baseline
