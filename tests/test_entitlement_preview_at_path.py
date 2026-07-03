"""
tests/test_entitlement_preview_at_path.py

Unit + HTTP tests for ``preview_at_path`` / ``preview_at_path_batch``
and their ``/api/entitlement/preview-at-path`` /
``/api/entitlement/preview-at-path-batch`` endpoints.

The ``_at_path`` slot for the preview family is a what-if sibling of
``preview_path``: perspective is validated but does NOT shape the rows.
Each row body is byte-identical to a row from ``preview_path`` /
``preview_path_batch`` for the same ``(from, to)`` pair -- pinned here
so the scalar / batch what-if path accessors cannot drift from the
current-perspective siblings that also back ``preview_at`` /
``preview_at_batch``.
"""

from __future__ import annotations

import json

import pytest


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def ent():
    """Return the real entitlements module (no stubbing).

    The helpers are catalogue-derived and resolver-independent, so we
    can exercise them against the real ``_TIER_FEATURES`` / ``_TIER_ORDER``
    directly. This also makes the byte-parity checks against
    ``preview_path`` / ``preview_path_batch`` meaningful.
    """
    from clawmetry import entitlements as _ent
    return _ent


@pytest.fixture()
def client():
    """Flask test client with ``bp_entitlement`` registered."""
    from flask import Flask

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


ALL_TIERS = (
    "oss",
    "cloud_free",
    "trial",
    "cloud_starter",
    "cloud_pro",
    "pro",
    "enterprise",
)


# ---------------------------------------------------------------------------
# Unit tests: preview_at_path helper
# ---------------------------------------------------------------------------


class TestPreviewAtPathHelper:
    def test_returns_none_for_unknown_perspective(self, ent):
        assert ent.preview_at_path("bogus", "oss", "enterprise") is None

    def test_returns_none_for_unknown_from(self, ent):
        assert ent.preview_at_path("cloud_pro", "bogus", "enterprise") is None

    def test_returns_none_for_unknown_to(self, ent):
        assert ent.preview_at_path("cloud_pro", "oss", "bogus") is None

    def test_returns_none_for_none_inputs(self, ent):
        assert ent.preview_at_path(None, "oss", "enterprise") is None
        assert ent.preview_at_path("cloud_pro", None, "enterprise") is None
        assert ent.preview_at_path("cloud_pro", "oss", None) is None

    def test_identity_path_is_empty(self, ent):
        assert ent.preview_at_path("cloud_pro", "pro", "pro") == []

    def test_body_parity_with_preview_path(self, ent):
        """Body of preview_at_path is byte-identical to preview_path."""
        for f in ALL_TIERS:
            for t in ALL_TIERS:
                scalar = ent.preview_path(f, t)
                if scalar is None:
                    continue
                for perspective in ALL_TIERS:
                    got = ent.preview_at_path(perspective, f, t)
                    assert got == scalar, (
                        f"preview_at_path({perspective!r}, {f!r}, {t!r}) "
                        f"drifted from preview_path({f!r}, {t!r})"
                    )

    def test_perspective_does_not_shape_body(self, ent):
        """Rows are byte-identical across shifting perspectives."""
        f, t = "oss", "enterprise"
        baseline = ent.preview_at_path("cloud_pro", f, t)
        assert baseline is not None
        for perspective in ALL_TIERS:
            assert ent.preview_at_path(perspective, f, t) == baseline

    def test_trial_accepted_as_perspective(self, ent):
        """Perspective is lenient (matches preview_at)."""
        row = ent.preview_at_path("trial", "oss", "enterprise")
        assert row is not None
        assert row == ent.preview_path("oss", "enterprise")

    def test_case_and_whitespace_normalised(self, ent):
        """Perspective is stripped + lowercased."""
        row = ent.preview_at_path("  CLOUD_PRO  ", "oss", "enterprise")
        assert row is not None
        assert row == ent.preview_path("oss", "enterprise")

    def test_upgrade_path_length(self, ent):
        """Upgrade from OSS to enterprise walks through the intermediate rungs."""
        path = ent.preview_at_path("cloud_pro", "oss", "enterprise")
        assert path is not None
        assert len(path) >= 1
        tiers = [r["tier"] for r in path]
        assert tiers[-1] == "enterprise"

    def test_downgrade_path(self, ent):
        path = ent.preview_at_path("cloud_pro", "enterprise", "oss")
        assert path is not None
        assert len(path) >= 1

    def test_never_raises_on_weird_types(self, ent):
        """Bytes / ints don't blow up -- helper returns None instead."""
        assert ent.preview_at_path(123, "oss", "enterprise") is None
        assert ent.preview_at_path("cloud_pro", 123, "enterprise") is None
        assert ent.preview_at_path("cloud_pro", "oss", 123) is None


# ---------------------------------------------------------------------------
# Unit tests: preview_at_path_batch helper
# ---------------------------------------------------------------------------


class TestPreviewAtPathBatchHelper:
    def test_returns_none_for_unknown_perspective(self, ent):
        assert (
            ent.preview_at_path_batch("bogus", "oss", ["enterprise"]) is None
        )

    def test_returns_none_for_unknown_from(self, ent):
        assert (
            ent.preview_at_path_batch("cloud_pro", "bogus", ["enterprise"])
            is None
        )

    def test_none_inputs_return_none(self, ent):
        assert ent.preview_at_path_batch(None, "oss", ["enterprise"]) is None
        assert ent.preview_at_path_batch("cloud_pro", None, ["enterprise"]) is None

    def test_envelope_shape(self, ent):
        result = ent.preview_at_path_batch("cloud_pro", "oss", ["enterprise"])
        assert result is not None
        assert set(result.keys()) == {"tiers", "unknown"}
        assert isinstance(result["tiers"], list)
        assert isinstance(result["unknown"], list)

    def test_body_parity_with_preview_path_batch(self, ent):
        """Body is byte-identical to preview_path_batch."""
        targets = ["oss", "cloud_starter", "cloud_pro", "enterprise", "trial"]
        for f in ("oss", "cloud_pro", "enterprise", "trial"):
            scalar = ent.preview_path_batch(f, targets)
            if scalar is None:
                continue
            for perspective in ALL_TIERS:
                got = ent.preview_at_path_batch(perspective, f, targets)
                assert got == scalar, (
                    f"preview_at_path_batch({perspective!r}, {f!r}, ...) "
                    f"drifted from preview_path_batch({f!r}, ...)"
                )

    def test_perspective_invariance(self, ent):
        """Batch is byte-identical across shifting perspectives."""
        f = "oss"
        targets = ["cloud_starter", "cloud_pro", "enterprise"]
        baseline = ent.preview_at_path_batch("cloud_pro", f, targets)
        assert baseline is not None
        for perspective in ALL_TIERS:
            assert ent.preview_at_path_batch(perspective, f, targets) == baseline

    def test_row_parity_with_scalar_at_path(self, ent):
        """Each batch row's path equals the scalar preview_at_path."""
        f = "oss"
        targets = ["cloud_starter", "cloud_pro", "enterprise"]
        batch = ent.preview_at_path_batch("cloud_pro", f, targets)
        assert batch is not None
        for row in batch["tiers"]:
            scalar = ent.preview_at_path("cloud_pro", f, row["to"])
            assert row["path"] == scalar

    def test_unknown_destinations_bucketed(self, ent):
        result = ent.preview_at_path_batch(
            "cloud_pro", "oss", ["enterprise", "bogus", "also_bogus"]
        )
        assert result is not None
        assert "bogus" in result["unknown"]
        assert "also_bogus" in result["unknown"]
        assert len(result["tiers"]) == 1
        assert result["tiers"][0]["to"] == "enterprise"

    def test_all_unknown_destinations(self, ent):
        result = ent.preview_at_path_batch(
            "cloud_pro", "oss", ["bad1", "bad2"]
        )
        assert result is not None
        assert result["tiers"] == []
        assert set(result["unknown"]) == {"bad1", "bad2"}

    def test_trial_accepted_as_destination(self, ent):
        result = ent.preview_at_path_batch(
            "cloud_pro", "oss", ["trial"]
        )
        assert result is not None
        assert result["unknown"] == []
        assert len(result["tiers"]) == 1

    def test_case_and_whitespace_normalised_in_perspective(self, ent):
        result = ent.preview_at_path_batch(
            "  CLOUD_PRO  ", "oss", ["enterprise"]
        )
        assert result is not None
        assert result == ent.preview_path_batch("oss", ["enterprise"])


# ---------------------------------------------------------------------------
# HTTP endpoint tests: GET /api/entitlement/preview-at-path
# ---------------------------------------------------------------------------


class TestPreviewAtPathEndpoint:
    ENDPOINT = "/api/entitlement/preview-at-path"

    def test_missing_tier_returns_400(self, client):
        rv = client.get(f"{self.ENDPOINT}?from=oss&to=enterprise")
        assert rv.status_code == 400

    def test_missing_from_returns_400(self, client):
        rv = client.get(f"{self.ENDPOINT}?tier=cloud_pro&to=enterprise")
        assert rv.status_code == 400

    def test_missing_to_returns_400(self, client):
        rv = client.get(f"{self.ENDPOINT}?tier=cloud_pro&from=oss")
        assert rv.status_code == 400

    def test_unknown_tier_returns_404_with_which(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?tier=bogus&from=oss&to=enterprise"
        )
        assert rv.status_code == 404
        assert rv.get_json().get("which") == "tier"

    def test_unknown_from_returns_404_with_which(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?tier=cloud_pro&from=bogus&to=enterprise"
        )
        assert rv.status_code == 404
        assert rv.get_json().get("which") == "from"

    def test_unknown_to_returns_404_with_which(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?tier=cloud_pro&from=oss&to=bogus"
        )
        assert rv.status_code == 404
        assert rv.get_json().get("which") == "to"

    def test_valid_request_returns_200(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?tier=cloud_pro&from=oss&to=enterprise"
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["perspective_tier"] == "cloud_pro"
        assert data["from"] == "oss"
        assert data["to"] == "enterprise"
        assert data["direction"] == "upgrade"
        assert isinstance(data["path"], list)

    def test_trial_accepted_as_perspective(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?tier=trial&from=oss&to=enterprise"
        )
        assert rv.status_code == 200
        assert rv.get_json()["perspective_tier"] == "trial"

    def test_identity_returns_empty_path(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?tier=cloud_pro&from=pro&to=pro"
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["direction"] == "identity"
        assert data["path"] == []

    def test_downgrade_direction(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?tier=cloud_pro&from=enterprise&to=oss"
        )
        assert rv.status_code == 200
        assert rv.get_json()["direction"] == "downgrade"

    def test_response_envelope_fields(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?tier=cloud_pro&from=oss&to=pro"
        )
        assert rv.status_code == 200
        data = rv.get_json()
        for key in (
            "perspective_tier",
            "perspective_tier_rank",
            "from",
            "from_label",
            "from_rank",
            "to",
            "to_label",
            "to_rank",
            "direction",
            "path",
            "current_tier",
            "current_tier_rank",
            "grace",
            "enforced",
        ):
            assert key in data, f"missing key {key!r} in {sorted(data)}"

    def test_case_and_whitespace_normalised(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?tier=%20CLOUD_PRO%20&from=OSS&to=Enterprise"
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["perspective_tier"] == "cloud_pro"
        assert data["from"] == "oss"
        assert data["to"] == "enterprise"

    def test_path_body_parity_with_preview_path(self, client, ent):
        rv = client.get(
            f"{self.ENDPOINT}?tier=cloud_pro&from=oss&to=enterprise"
        )
        assert rv.status_code == 200
        assert rv.get_json()["path"] == ent.preview_path("oss", "enterprise")

    def test_perspective_invariance_over_http(self, client, ent):
        """HTTP body's path is byte-identical across perspectives."""
        base = client.get(
            f"{self.ENDPOINT}?tier=cloud_pro&from=oss&to=enterprise"
        ).get_json()["path"]
        for perspective in ALL_TIERS:
            rv = client.get(
                f"{self.ENDPOINT}?tier={perspective}&from=oss&to=enterprise"
            )
            assert rv.status_code == 200
            assert rv.get_json()["path"] == base


# ---------------------------------------------------------------------------
# HTTP endpoint tests: POST /api/entitlement/preview-at-path-batch
# ---------------------------------------------------------------------------


class TestPreviewAtPathBatchEndpoint:
    ENDPOINT = "/api/entitlement/preview-at-path-batch"

    def _post(self, client, payload):
        return client.post(
            self.ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_missing_tier_returns_400(self, client):
        rv = self._post(client, {"from": "oss", "to": ["enterprise"]})
        assert rv.status_code == 400

    def test_missing_from_returns_400(self, client):
        rv = self._post(client, {"tier": "cloud_pro", "to": ["enterprise"]})
        assert rv.status_code == 400

    def test_missing_to_returns_400(self, client):
        rv = self._post(client, {"tier": "cloud_pro", "from": "oss"})
        assert rv.status_code == 400

    def test_empty_to_list_returns_400(self, client):
        rv = self._post(
            client, {"tier": "cloud_pro", "from": "oss", "to": []}
        )
        assert rv.status_code == 400

    def test_unknown_tier_returns_404_with_which(self, client):
        rv = self._post(
            client,
            {"tier": "bogus", "from": "oss", "to": ["enterprise"]},
        )
        assert rv.status_code == 404
        assert rv.get_json().get("which") == "tier"

    def test_unknown_from_returns_404_with_which(self, client):
        rv = self._post(
            client,
            {"tier": "cloud_pro", "from": "bogus", "to": ["enterprise"]},
        )
        assert rv.status_code == 404
        assert rv.get_json().get("which") == "from"

    def test_valid_request_returns_200(self, client):
        rv = self._post(
            client,
            {"tier": "cloud_pro", "from": "oss", "to": ["enterprise"]},
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["perspective_tier"] == "cloud_pro"
        assert data["from"] == "oss"
        assert data["unknown"] == []
        assert len(data["tiers"]) == 1
        assert data["tiers"][0]["to"] == "enterprise"

    def test_partial_unknown_destinations(self, client):
        rv = self._post(
            client,
            {
                "tier": "cloud_pro",
                "from": "oss",
                "to": ["enterprise", "bogus_dest"],
            },
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert "bogus_dest" in data["unknown"]
        assert len(data["tiers"]) == 1

    def test_response_envelope_fields(self, client):
        rv = self._post(
            client,
            {"tier": "cloud_pro", "from": "oss", "to": ["pro"]},
        )
        assert rv.status_code == 200
        data = rv.get_json()
        for key in (
            "perspective_tier",
            "perspective_tier_rank",
            "from",
            "from_label",
            "from_rank",
            "tiers",
            "unknown",
            "current_tier",
            "current_tier_rank",
            "grace",
            "enforced",
        ):
            assert key in data, f"missing key {key!r}"

    def test_multiple_destinations(self, client):
        rv = self._post(
            client,
            {
                "tier": "cloud_pro",
                "from": "oss",
                "to": ["cloud_starter", "enterprise", "pro"],
            },
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert len(data["tiers"]) == 3
        assert data["unknown"] == []

    def test_body_parity_with_preview_path_batch_endpoint(self, client, ent):
        """Batch tiers[] rows match the current-perspective sibling."""
        rv = self._post(
            client,
            {
                "tier": "cloud_pro",
                "from": "oss",
                "to": ["cloud_starter", "enterprise"],
            },
        )
        assert rv.status_code == 200
        got_tiers = rv.get_json()["tiers"]
        expected = ent.preview_path_batch(
            "oss", ["cloud_starter", "enterprise"]
        )["tiers"]
        assert got_tiers == expected

    def test_perspective_invariance_over_http(self, client):
        payload = lambda p: {  # noqa: E731
            "tier": p,
            "from": "oss",
            "to": ["cloud_starter", "enterprise"],
        }
        base = self._post(client, payload("cloud_pro")).get_json()["tiers"]
        for perspective in ALL_TIERS:
            rv = self._post(client, payload(perspective))
            assert rv.status_code == 200
            assert rv.get_json()["tiers"] == base

    def test_trial_accepted_as_perspective(self, client):
        rv = self._post(
            client,
            {"tier": "trial", "from": "oss", "to": ["enterprise"]},
        )
        assert rv.status_code == 200
        assert rv.get_json()["perspective_tier"] == "trial"

    def test_trial_accepted_as_destination(self, client):
        rv = self._post(
            client,
            {"tier": "cloud_pro", "from": "oss", "to": ["trial"]},
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["unknown"] == []
        assert len(data["tiers"]) == 1
