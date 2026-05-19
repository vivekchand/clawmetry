"""Tests for ``clawmetry.dives_prompt``.

Covers the Dives prompt template and schema descriptor (issue #1001).  All
tests run without a live DuckDB connection or Anthropic API key.

Test groups:
  - Constants — PROMPT_VERSION, _DIVES_TABLES alignment with ALLOWED_TABLES
  - Few-shot examples — SQL validity, chart type validity
  - build_schema_descriptor — static mode (no store)
  - build_dives_prompt — shape, content, edge cases
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clawmetry.dives_prompt import (  # noqa: E402
    PROMPT_VERSION,
    SUPPORTED_CHART_TYPES,
    _DIVES_TABLES,
    _FEW_SHOT_EXAMPLES,
    build_dives_prompt,
    build_schema_descriptor,
)
from clawmetry.dives_sql_safety import ALLOWED_TABLES, validate_sql  # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_prompt_version_is_int():
    assert isinstance(PROMPT_VERSION, int)
    assert PROMPT_VERSION >= 1


def test_dives_tables_match_allowlist():
    """_DIVES_TABLES must be exactly the same set as ALLOWED_TABLES."""
    assert set(_DIVES_TABLES) == ALLOWED_TABLES


def test_supported_chart_types_non_empty():
    assert len(SUPPORTED_CHART_TYPES) >= 5
    assert "bar" in SUPPORTED_CHART_TYPES
    assert "line" in SUPPORTED_CHART_TYPES
    assert "number" in SUPPORTED_CHART_TYPES


# ---------------------------------------------------------------------------
# Few-shot examples
# ---------------------------------------------------------------------------


def test_few_shot_count():
    assert len(_FEW_SHOT_EXAMPLES) == 3


@pytest.mark.parametrize("ex", _FEW_SHOT_EXAMPLES)
def test_few_shot_sql_passes_validator(ex):
    sql = ex["answer"]["sql"]
    ok, reason = validate_sql(sql)
    assert ok, f"Few-shot SQL failed validator: {reason!r}\nSQL:\n{sql}"


@pytest.mark.parametrize("ex", _FEW_SHOT_EXAMPLES)
def test_few_shot_chart_type_supported(ex):
    ct = ex["answer"]["chart_type"]
    assert ct in SUPPORTED_CHART_TYPES, f"Unsupported chart_type {ct!r}"


@pytest.mark.parametrize("ex", _FEW_SHOT_EXAMPLES)
def test_few_shot_required_keys(ex):
    required = {"sql", "chart_type", "x", "y", "title", "description"}
    assert required.issubset(ex["answer"].keys()), (
        f"Missing keys: {required - ex['answer'].keys()}"
    )


# ---------------------------------------------------------------------------
# build_schema_descriptor (static mode — no store)
# ---------------------------------------------------------------------------


def test_schema_descriptor_contains_all_tables():
    desc = build_schema_descriptor(store=None)
    for table in _DIVES_TABLES:
        assert table in desc, f"Table {table!r} missing from descriptor"


def test_schema_descriptor_contains_key_columns():
    desc = build_schema_descriptor(store=None)
    # Spot-check a handful of column names across different tables.
    for col in ("cost_usd", "session_id", "event_type", "agent_type", "ts"):
        assert col in desc, f"Column {col!r} missing from descriptor"


def test_schema_descriptor_documents_blob_columns():
    desc = build_schema_descriptor(store=None)
    # BLOB columns must be mentioned (not silently dropped) so the LLM
    # knows to use json_extract_string() rather than selecting them raw.
    assert "BLOB" in desc


def test_schema_descriptor_is_string():
    assert isinstance(build_schema_descriptor(store=None), str)


# ---------------------------------------------------------------------------
# build_dives_prompt
# ---------------------------------------------------------------------------


def test_build_dives_prompt_returns_dict():
    result = build_dives_prompt("Total cost per agent today")
    assert isinstance(result, dict)
    assert "system" in result and "user" in result


def test_build_dives_prompt_user_equals_question():
    q = "How many sessions started in the last 7 days?"
    result = build_dives_prompt(q)
    assert result["user"] == q


def test_build_dives_prompt_strips_whitespace():
    q = "  What is the average cost per session?  "
    result = build_dives_prompt(q)
    assert result["user"] == q.strip()


def test_build_dives_prompt_system_contains_prompt_version():
    result = build_dives_prompt("anything")
    assert "PROMPT_VERSION" in result["system"]


def test_build_dives_prompt_system_contains_select_constraint():
    result = build_dives_prompt("anything")
    assert "SELECT" in result["system"]


def test_build_dives_prompt_system_contains_chart_types():
    result = build_dives_prompt("anything")
    for ct in SUPPORTED_CHART_TYPES:
        assert ct in result["system"], f"chart_type {ct!r} missing from system prompt"


def test_build_dives_prompt_system_contains_all_tables():
    result = build_dives_prompt("anything")
    for table in _DIVES_TABLES:
        assert table in result["system"], f"Table {table!r} missing from system prompt"


def test_build_dives_prompt_system_contains_few_shots():
    result = build_dives_prompt("anything")
    # Each few-shot question should appear in the system prompt.
    for ex in _FEW_SHOT_EXAMPLES:
        assert ex["question"] in result["system"]


def test_build_dives_prompt_empty_question_raises():
    with pytest.raises(ValueError, match="non-empty"):
        build_dives_prompt("")


def test_build_dives_prompt_whitespace_only_raises():
    with pytest.raises(ValueError, match="non-empty"):
        build_dives_prompt("   \t\n")


def test_build_dives_prompt_store_none_works():
    result = build_dives_prompt("How many events today?", store=None)
    assert result["user"] == "How many events today?"
