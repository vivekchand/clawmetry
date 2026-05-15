"""Unit tests for clawmetry/latency_tracker.py (issue #1283)."""
from __future__ import annotations

import time

from clawmetry import latency_tracker


def setup_function(_):
    latency_tracker.reset()


def test_record_and_stats_basic():
    for ms in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        latency_tracker.record("api_overview", float(ms))

    stats = latency_tracker.get_stats(top_n=5, slow_threshold_ms=500.0)

    assert stats["endpoint_count"] == 1
    assert len(stats["endpoints"]) == 1
    row = stats["endpoints"][0]
    assert row["endpoint"] == "api_overview"
    assert row["count"] == 10
    # p50 of 1..10 is around 50, p95 is around 90-100
    assert 40 <= row["p50_ms"] <= 60
    assert 90 <= row["p95_ms"] <= 100
    assert row["max_ms"] == 100
    assert row["is_slow"] is False


def test_slow_threshold_flag():
    latency_tracker.record("api_sessions", 800.0)
    stats = latency_tracker.get_stats(slow_threshold_ms=500.0)
    assert stats["endpoints"][0]["is_slow"] is True

    stats2 = latency_tracker.get_stats(slow_threshold_ms=1000.0)
    assert stats2["endpoints"][0]["is_slow"] is False


def test_top_n_limit_and_sort():
    for label, latency in [("a", 10), ("b", 50), ("c", 100), ("d", 200)]:
        latency_tracker.record(label, float(latency))

    stats = latency_tracker.get_stats(top_n=2)
    eps = [r["endpoint"] for r in stats["endpoints"]]
    assert eps == ["d", "c"]  # Sorted by p95 desc, top 2


def test_window_drops_old_records(monkeypatch):
    fixed_now = [1_000_000.0]

    def fake_time():
        return fixed_now[0]

    monkeypatch.setattr(time, "time", fake_time)

    latency_tracker.record("old", 999.0)
    fixed_now[0] += 6 * 60  # advance past the 5-min window
    latency_tracker.record("fresh", 50.0)

    stats = latency_tracker.get_stats()
    eps = [r["endpoint"] for r in stats["endpoints"]]
    assert "fresh" in eps
    assert "old" not in eps


def test_ignores_negative_or_empty():
    latency_tracker.record("", 100.0)
    latency_tracker.record("api_x", -1.0)
    stats = latency_tracker.get_stats()
    assert stats["endpoint_count"] == 0


def test_humanise_endpoint_static_overrides():
    # Curated map wins over mechanical transform.
    assert latency_tracker.humanise_endpoint(
        "components.api_component_tool") == "Tool detail panel"
    assert latency_tracker.humanise_endpoint(
        "health.api_system_health") == "System health"
    assert latency_tracker.humanise_endpoint(
        "usage.api_anomalies") == "Cost anomalies"


def test_humanise_endpoint_mechanical_fallback():
    # Unknown endpoint: drop api_ prefix, ›-separated, title-cased.
    assert latency_tracker.humanise_endpoint(
        "newblueprint.api_something_new") == "Newblueprint › Something New"
    # Endpoint without api_ prefix: keep func words as-is.
    assert latency_tracker.humanise_endpoint(
        "myblue.helper_method") == "Myblue › Helper Method"


def test_humanise_endpoint_edge_cases():
    # No dot at all: return as-is.
    assert latency_tracker.humanise_endpoint("static") == "static"
    # Empty input: return as-is.
    assert latency_tracker.humanise_endpoint("") == ""


def test_get_stats_includes_humanised_label():
    latency_tracker.record("components.api_component_tool", 50.0)
    stats = latency_tracker.get_stats()
    row = stats["endpoints"][0]
    assert row["endpoint"] == "components.api_component_tool"  # raw preserved
    assert row["label"] == "Tool detail panel"  # humanised added
