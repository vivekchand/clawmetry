"""Published (harness, model) benchmark pairs for the Harness Engineering tab.

Serves the curated, versioned catalog shipped in clawmetry/data/
published_benchmarks.json. Third-party results only where possible; every
row carries its source URL, benchmark version, runner, and result date, and
rows older than one quarter are marked historical at read time (AC-HB-003.2).
The dashboard performs no network fetch for benchmark data (Blueprint ADR).
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data",
                          "published_benchmarks.json")
_QUARTER_SECS = 92 * 24 * 3600

_cache: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _cache
    if _cache is None:
        try:
            with open(_DATA_PATH, "r", encoding="utf-8") as fh:
                _cache = json.load(fh)
        except Exception:
            _cache = {"schema": 1, "pairs": []}
    return _cache


def _is_historical(result_date: str, now: float) -> bool:
    try:
        struct = time.strptime(result_date[:10], "%Y-%m-%d")
        return (now - time.mktime(struct)) > _QUARTER_SECS
    except Exception:
        return True  # an undatable row must not present itself as current


def published_pairs(
    *,
    harnesses: list[str] | None = None,
    models: list[str] | None = None,
    now: float | None = None,
) -> list[dict[str, Any]]:
    """The catalog, optionally filtered to the harnesses / models the user
    actually runs (AC-HB-003.3: never present a pair for a different model
    as predictive of the user's setup; the caller filters, the tab labels)."""
    now_ts = time.time() if now is None else now
    out = []
    for row in _load().get("pairs", []):
        if not isinstance(row, dict):
            continue
        if harnesses and row.get("harness") not in harnesses:
            continue
        if models and row.get("model") not in models:
            continue
        entry = dict(row)
        entry["historical"] = _is_historical(str(row.get("result_date") or ""), now_ts)
        out.append(entry)
    return out
