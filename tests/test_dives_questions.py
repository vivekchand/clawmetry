"""Tests for DIVES-5: suggested-questions gallery (routes.dives.DIVES_GALLERY_QUESTIONS).

Regression guards:
- Fixed schema per entry (question, chart_type, category).
- No duplicate question text.
- All chart_type values are known Chart.js types.
- All category values are in the allowed set.
- Entry count pinned — new entries require an intentional bump here.

Sub-issue: https://github.com/vivekchand/clawmetry/issues/1003
Closes: part of https://github.com/vivekchand/clawmetry/issues/999
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# routes/dives.py imports Flask at module level; mock it so this test runs
# even when Flask is not installed (pure data validation, no HTTP needed).
if "flask" not in sys.modules:
    _flask_mock = MagicMock()
    sys.modules["flask"] = _flask_mock
    sys.modules["flask"].Blueprint = MagicMock(return_value=MagicMock())
    sys.modules["flask"].jsonify = MagicMock()
    sys.modules["flask"].request = MagicMock()

from routes.dives import DIVES_GALLERY_QUESTIONS as SUGGESTED_QUESTIONS  # noqa: E402

_KNOWN_CHART_TYPES = frozenset({"bar", "line", "pie", "table", "number"})
_KNOWN_CATEGORIES = frozenset({"cost", "activity", "sessions", "crons", "system", "memory"})

# One-way ratchet — update intentionally when adding or removing entries.
_EXPECTED_COUNT = 15


# ---------------------------------------------------------------------------
# Whole-list invariants
# ---------------------------------------------------------------------------


def test_non_empty():
    assert len(SUGGESTED_QUESTIONS) > 0


def test_count_pinned():
    assert len(SUGGESTED_QUESTIONS) == _EXPECTED_COUNT, (
        f"SUGGESTED_QUESTIONS has {len(SUGGESTED_QUESTIONS)} entries, expected "
        f"{_EXPECTED_COUNT}. Update _EXPECTED_COUNT in this file if intentional."
    )


def test_no_duplicate_question_text():
    texts = [q["question"] for q in SUGGESTED_QUESTIONS]
    assert len(texts) == len(set(texts)), "Duplicate question text found"


def test_multiple_chart_types_present():
    types = {q["chart_type"] for q in SUGGESTED_QUESTIONS}
    assert len(types) >= 2, "Gallery should use at least two chart types"


def test_cost_and_activity_categories_present():
    cats = {q["category"] for q in SUGGESTED_QUESTIONS}
    assert "cost" in cats, "No cost-category questions in gallery"
    assert "activity" in cats, "No activity-category questions in gallery"


# ---------------------------------------------------------------------------
# Per-entry invariants (parametrised so failures name the offending entry)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("entry,idx", [(q, i) for i, q in enumerate(SUGGESTED_QUESTIONS)])
def test_entry_is_dict(entry, idx):
    assert isinstance(entry, dict), f"Entry {idx} is not a dict"


@pytest.mark.parametrize("entry,idx", [(q, i) for i, q in enumerate(SUGGESTED_QUESTIONS)])
def test_entry_has_question(entry, idx):
    assert "question" in entry, f"Entry {idx} missing 'question'"
    assert isinstance(entry["question"], str) and entry["question"].strip(), (
        f"Entry {idx}: 'question' must be a non-empty string"
    )


@pytest.mark.parametrize("entry,idx", [(q, i) for i, q in enumerate(SUGGESTED_QUESTIONS)])
def test_entry_question_min_length(entry, idx):
    assert len(entry["question"].strip()) >= 10, (
        f"Entry {idx} question too short: {entry['question']!r}"
    )


@pytest.mark.parametrize("entry,idx", [(q, i) for i, q in enumerate(SUGGESTED_QUESTIONS)])
def test_entry_chart_type_valid(entry, idx):
    assert "chart_type" in entry, f"Entry {idx} missing 'chart_type'"
    assert entry["chart_type"] in _KNOWN_CHART_TYPES, (
        f"Entry {idx} unknown chart_type {entry['chart_type']!r}; "
        f"valid: {sorted(_KNOWN_CHART_TYPES)}"
    )


@pytest.mark.parametrize("entry,idx", [(q, i) for i, q in enumerate(SUGGESTED_QUESTIONS)])
def test_entry_category_valid(entry, idx):
    assert "category" in entry, f"Entry {idx} missing 'category'"
    assert entry["category"] in _KNOWN_CATEGORIES, (
        f"Entry {idx} unknown category {entry['category']!r}; "
        f"valid: {sorted(_KNOWN_CATEGORIES)}"
    )
