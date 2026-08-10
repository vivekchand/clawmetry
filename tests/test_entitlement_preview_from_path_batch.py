"""
tests/test_entitlement_preview_from_path_batch.py

Unit + HTTP tests for ``preview_from_path_batch`` and its
``/api/entitlement/preview-from-path-batch`` endpoint.

Mirror-direction twin of ``preview_path_batch`` / ``/preview-path-batch``:
fixes ONE destination and fans out over N candidate sources. Each per-
source ``path`` is pinned byte-equal to ``preview_path(from, to)`` so
the source-batch accessor cannot drift from the scalar path helper.
"""

from __future__ import annotations

import pytest


@pytest.fixture()
def ent():
    """Return the real entitlements module (no stubbing)."""
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
# Unit tests: preview_from_path_batch helper
# ---------------------------------------------------------------------------


class TestPreviewFromPathBatchHelper:
    def test_returns_none_for_unknown_to(self, ent):
        assert ent.preview_from_path_batch(["oss"], "bogus") is None

    def test_returns_none_for_empty_to(self, ent):
        assert ent.preview_from_path_batch(["oss"], "") is None
        assert ent.preview_from_path_batch(["oss"], None) is None

    def test_returns_none_for_non_string_to(self, ent):
        assert ent.preview_from_path_batch(["oss"], 123) is None

    def test_envelope_shape(self, ent):
        result = ent.preview_from_path_batch(["oss"], "enterprise")
        assert result is not None
        assert set(result.keys()) == {"tiers", "unknown"}
        assert isinstance(result["tiers"], list)
        assert isinstance(result["unknown"], list)

    def test_empty_sources_returns_empty_batch(self, ent):
        result = ent.preview_from_path_batch([], "enterprise")
        assert result == {"tiers": [], "unknown": []}

    def test_row_shape(self, ent):
        result = ent.preview_from_path_batch(["oss"], "enterprise")
        assert result is not None
        assert len(result["tiers"]) == 1
        row = result["tiers"][0]
        assert set(row.keys()) == {
            "from",
            "from_label",
            "from_rank",
            "direction",
            "path",
        }
        assert row["from"] == "oss"
        assert row["direction"] == "upgrade"
        assert isinstance(row["path"], list)

    def test_path_parity_with_preview_path(self, ent):
        """Each batch ``path`` is byte-equal to preview_path(from, to)."""
        to_tier = "enterprise"
        sources = ["oss", "cloud_starter", "cloud_pro", "pro", "enterprise"]
        result = ent.preview_from_path_batch(sources, to_tier)
        assert result is not None
        for row in result["tiers"]:
            scalar = ent.preview_path(row["from"], to_tier)
            assert row["path"] == scalar, (
                f"preview_from_path_batch row {row['from']!r} drifted "
                f"from preview_path({row['from']!r}, {to_tier!r})"
            )

    def test_direction_upgrade_lateral_downgrade_identity(self, ent):
        result = ent.preview_from_path_batch(
            ["oss", "cloud_pro", "pro", "enterprise"], "cloud_pro"
        )
        assert result is not None
        by_from = {row["from"]: row for row in result["tiers"]}
        assert by_from["oss"]["direction"] == "upgrade"
        assert by_from["cloud_pro"]["direction"] == "identity"
        assert by_from["enterprise"]["direction"] == "downgrade"
        # Cloud Pro and self-hosted Pro sit at the same rank
        if ent._TIER_RANK.get("pro") == ent._TIER_RANK.get("cloud_pro"):
            assert by_from["pro"]["direction"] == "lateral"

    def test_identity_row_has_empty_path(self, ent):
        result = ent.preview_from_path_batch(["cloud_pro"], "cloud_pro")
        assert result is not None
        assert result["tiers"][0]["direction"] == "identity"
        assert result["tiers"][0]["path"] == []

    def test_unknown_sources_bucketed(self, ent):
        result = ent.preview_from_path_batch(
            ["oss", "bogus", "also_bogus"], "enterprise"
        )
        assert result is not None
        assert "bogus" in result["unknown"]
        assert "also_bogus" in result["unknown"]
        assert len(result["tiers"]) == 1
        assert result["tiers"][0]["from"] == "oss"

    def test_all_unknown_sources(self, ent):
        result = ent.preview_from_path_batch(["bad1", "bad2"], "enterprise")
        assert result is not None
        assert result["tiers"] == []
        assert set(result["unknown"]) == {"bad1", "bad2"}

    def test_trial_accepted_as_source(self, ent):
        result = ent.preview_from_path_batch(["trial"], "enterprise")
        assert result is not None
        assert result["unknown"] == []
        assert len(result["tiers"]) == 1
        assert result["tiers"][0]["from"] == "trial"

    def test_csv_string_accepted(self, ent):
        """``_normalise_csv`` accepts a CSV string, not just a list."""
        result = ent.preview_from_path_batch(
            "oss, cloud_starter , cloud_pro", "enterprise"
        )
        assert result is not None
        ids = [row["from"] for row in result["tiers"]]
        assert ids == ["oss", "cloud_starter", "cloud_pro"]

    def test_dedup_and_order_preserved(self, ent):
        result = ent.preview_from_path_batch(
            ["cloud_pro", "oss", "cloud_pro", "oss"], "enterprise"
        )
        assert result is not None
        ids = [row["from"] for row in result["tiers"]]
        assert ids == ["cloud_pro", "oss"]

    def test_case_and_whitespace_normalised(self, ent):
        result = ent.preview_from_path_batch(["  OSS  "], "enterprise")
        assert result is not None
        assert result["tiers"][0]["from"] == "oss"

    def test_grace_independent(self, ent, monkeypatch):
        """Rows read from static tier maps -- grace on / off yields
        byte-identical output."""
        baseline = ent.preview_from_path_batch(
            ["oss", "cloud_starter"], "enterprise"
        )
        # Flip the resolver to a hypothetical enforce state; the rows must
        # not change because the helper walks the static _TIER_* tables.
        class _E:
            tier = "cloud_pro"
            grace = False

        monkeypatch.setattr(ent, "get_entitlement", lambda: _E())
        under_enforce = ent.preview_from_path_batch(
            ["oss", "cloud_starter"], "enterprise"
        )
        assert baseline == under_enforce

    def test_never_raises_on_weird_types(self, ent):
        """Bytes / ints / bad iterables collapse to a fail-safe shape."""
        # Bad to
        assert ent.preview_from_path_batch(["oss"], b"enterprise") is None
        # from_tiers=None -> _normalise_csv treats as empty
        result = ent.preview_from_path_batch(None, "enterprise")
        assert result == {"tiers": [], "unknown": []}


# ---------------------------------------------------------------------------
# HTTP endpoint tests: GET /api/entitlement/preview-from-path-batch
# ---------------------------------------------------------------------------


class TestPreviewFromPathBatchEndpoint:
    ENDPOINT = "/api/entitlement/preview-from-path-batch"

    def test_missing_to_returns_400(self, client):
        rv = client.get(f"{self.ENDPOINT}?from=oss")
        assert rv.status_code == 400
        assert rv.get_json().get("error") == "missing to"

    def test_blank_to_returns_400(self, client):
        rv = client.get(f"{self.ENDPOINT}?from=oss&to=")
        assert rv.status_code == 400

    def test_missing_from_returns_400(self, client):
        rv = client.get(f"{self.ENDPOINT}?to=enterprise")
        assert rv.status_code == 400

    def test_blank_from_returns_400(self, client):
        rv = client.get(f"{self.ENDPOINT}?from=&to=enterprise")
        assert rv.status_code == 400

    def test_unknown_to_returns_404_with_which(self, client):
        rv = client.get(f"{self.ENDPOINT}?from=oss&to=bogus")
        assert rv.status_code == 404
        body = rv.get_json()
        assert body.get("which") == "to"
        assert body.get("to") == "bogus"

    def test_valid_request_returns_200(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?from=oss,cloud_pro&to=enterprise"
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["to"] == "enterprise"
        assert isinstance(data["to_rank"], int)
        assert isinstance(data["tiers"], list)
        assert len(data["tiers"]) == 2
        assert isinstance(data["unknown"], list)
        assert data["unknown"] == []
        assert isinstance(data["current_tier"], str)
        assert isinstance(data["grace"], bool)
        assert isinstance(data["enforced"], bool)

    def test_envelope_key_set(self, client):
        rv = client.get(f"{self.ENDPOINT}?from=oss&to=enterprise")
        assert rv.status_code == 200
        assert set(rv.get_json().keys()) == {
            "to",
            "to_label",
            "to_rank",
            "tiers",
            "unknown",
            "current_tier",
            "grace",
            "enforced",
        }

    def test_row_key_set(self, client):
        rv = client.get(f"{self.ENDPOINT}?from=oss&to=enterprise")
        assert rv.status_code == 200
        row = rv.get_json()["tiers"][0]
        assert set(row.keys()) == {
            "from",
            "from_label",
            "from_rank",
            "direction",
            "path",
        }

    def test_unknown_sources_bucketed_not_404(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?from=oss,bogus,also_bogus&to=enterprise"
        )
        assert rv.status_code == 200
        body = rv.get_json()
        assert "bogus" in body["unknown"]
        assert "also_bogus" in body["unknown"]
        assert len(body["tiers"]) == 1
        assert body["tiers"][0]["from"] == "oss"

    def test_normalisation_dedup_and_case(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?from=  OSS  ,cloud_pro,oss&to=enterprise"
        )
        assert rv.status_code == 200
        ids = [row["from"] for row in rv.get_json()["tiers"]]
        assert ids == ["oss", "cloud_pro"]

    def test_trial_accepted_as_source(self, client):
        rv = client.get(f"{self.ENDPOINT}?from=trial&to=enterprise")
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["unknown"] == []
        assert body["tiers"][0]["from"] == "trial"

    def test_identity_path_empty(self, client):
        rv = client.get(f"{self.ENDPOINT}?from=cloud_pro&to=cloud_pro")
        assert rv.status_code == 200
        row = rv.get_json()["tiers"][0]
        assert row["direction"] == "identity"
        assert row["path"] == []

    def test_direction_labels_across_axis(self, client):
        rv = client.get(
            f"{self.ENDPOINT}?from=oss,cloud_pro,enterprise&to=cloud_pro"
        )
        assert rv.status_code == 200
        by_from = {row["from"]: row["direction"] for row in rv.get_json()["tiers"]}
        assert by_from["oss"] == "upgrade"
        assert by_from["cloud_pro"] == "identity"
        assert by_from["enterprise"] == "downgrade"

    def test_path_parity_endpoint_matches_helper(self, client, ent):
        """Each per-source ``path`` in the endpoint response is byte-
        equal to the helper output for the same source."""
        rv = client.get(
            f"{self.ENDPOINT}?from=oss,cloud_starter,cloud_pro&to=enterprise"
        )
        assert rv.status_code == 200
        for row in rv.get_json()["tiers"]:
            assert row["path"] == ent.preview_path(row["from"], "enterprise")

    def test_never_5xx_on_resolver_blowup(self, client, monkeypatch, ent):
        """If ``get_entitlement`` explodes, the endpoint still returns a
        grace-shape 200 rather than 5xxing."""
        def _boom():
            raise RuntimeError("resolver down")

        monkeypatch.setattr(ent, "get_entitlement", _boom)
        rv = client.get(f"{self.ENDPOINT}?from=oss&to=enterprise")
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["current_tier"] == "oss"
        assert body["grace"] is True

    def test_never_5xx_on_helper_blowup(self, client, monkeypatch, ent):
        """If the batch helper explodes the endpoint still returns the
        fail-closed envelope, not a 5xx."""
        def _boom(*_a, **_kw):
            raise RuntimeError("helper down")

        monkeypatch.setattr(ent, "preview_from_path_batch", _boom)
        rv = client.get(f"{self.ENDPOINT}?from=oss&to=enterprise")
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["tiers"] == []
        assert body["unknown"] == []

    def test_grace_true_when_helper_returns_none(self, client, monkeypatch, ent):
        """A ``None`` return from the helper collapses to the empty batch
        shape (matches ``preview_path_batch`` handler posture)."""
        monkeypatch.setattr(
            ent, "preview_from_path_batch", lambda *_a, **_kw: None
        )
        rv = client.get(f"{self.ENDPOINT}?from=oss&to=enterprise")
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["tiers"] == []
        assert body["unknown"] == []
