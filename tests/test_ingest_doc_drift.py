"""Drift CI for the ingest/1 contract (issue #5682).

Fails when docs/INGEST.md drifts from clawmetry/ingest_contract.py:

* The committed docs/INGEST.md is exactly the generator output.
* Contract constants that the server reads are sanity-checked against
  the contract module so a rename is caught before the doc update.
"""
from __future__ import annotations

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_committed_doc_matches_generator():
    spec = importlib.util.spec_from_file_location(
        "gen_ingest_doc", ROOT / "scripts" / "gen_ingest_doc.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    doc = ROOT / "docs" / "INGEST.md"
    assert doc.exists(), "docs/INGEST.md missing — run: python3 scripts/gen_ingest_doc.py"
    assert doc.read_text() == mod.render(), (
        "docs/INGEST.md drifted from the contract. "
        "Regenerate: python3 scripts/gen_ingest_doc.py"
    )


def test_otlp_endpoints_are_known_signals():
    from clawmetry.ingest_contract import OTLP_ENDPOINTS
    valid_signals = {"/v1/metrics", "/v1/traces", "/v1/logs"}
    assert set(OTLP_ENDPOINTS) == valid_signals, (
        f"OTLP_ENDPOINTS changed: {set(OTLP_ENDPOINTS)} != {valid_signals}. "
        "Update the contract version and regenerate the doc."
    )


def test_otlp_content_types_include_json_and_protobuf():
    from clawmetry.ingest_contract import OTLP_CONTENT_TYPES
    assert "application/json" in OTLP_CONTENT_TYPES
    assert "application/x-protobuf" in OTLP_CONTENT_TYPES


def test_otlp_max_decompressed_is_positive_int():
    from clawmetry.ingest_contract import OTLP_MAX_DECOMPRESSED_MB
    assert isinstance(OTLP_MAX_DECOMPRESSED_MB, int)
    assert OTLP_MAX_DECOMPRESSED_MB > 0


def test_gen_ai_attrs_read_covers_required_fields():
    from clawmetry.ingest_contract import GEN_AI_ATTRS_READ
    required = {
        "gen_ai.request.model",
        "gen_ai.usage.input_tokens",
        "gen_ai.usage.output_tokens",
        "gen_ai.conversation.id",
    }
    missing = required - set(GEN_AI_ATTRS_READ)
    assert not missing, f"Required gen_ai attrs missing from contract: {missing}"


def test_run_endpoints_include_free_runtimes_list():
    from clawmetry.ingest_contract import RUN_ENDPOINTS
    free = [k for k, v in RUN_ENDPOINTS.items() if v["tier"] == "free"]
    assert any("/api/v1/runtimes" in k for k in free), (
        "GET /api/v1/runtimes must be a free endpoint in the contract"
    )


def test_contract_version_format():
    from clawmetry.ingest_contract import CONTRACT_VERSION
    assert CONTRACT_VERSION.startswith("ingest/"), CONTRACT_VERSION
