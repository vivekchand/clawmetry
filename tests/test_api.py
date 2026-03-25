"""
ClawMetry API endpoint tests.

Tests every API endpoint for:
- Correct HTTP status (200)
- Response structure / required keys

Tests are resilient: empty data is fine — we just check structure.
"""
import pytest
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get(api, base_url, path):
    """Make an authenticated GET request and return the response."""
    return api.get(f"{base_url}{path}", timeout=10)


def assert_ok(resp):
    assert resp.status_code == 200, (
        f"Expected 200 for {resp.url}, got {resp.status_code}: {resp.text[:200]}"
    )
    return resp.json()


def assert_keys(data, *keys):
    for k in keys:
        assert k in data, f"Missing key '{k}' in response: {list(data.keys())}"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestAuth:
    def test_auth_check_accessible(self, base_url):
        """Auth check endpoint is always accessible (no token needed)."""
        r = requests.get(f"{base_url}/api/auth/check", timeout=5)
        assert r.status_code == 200
        d = r.json()
        assert "valid" in d

    def test_auth_with_token(self, base_url, token):
        """Correct token is accepted."""
        if not token:
            pytest.skip("No gateway token configured")
        r = requests.get(
            f"{base_url}/api/auth/check",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        assert r.status_code == 200
        d = r.json()
        assert d.get("valid") is True


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------

class TestOverview:
    def test_status(self, api, base_url):
        r = get(api, base_url, "/api/overview")
        assert_ok(r)

    def test_required_keys(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/overview"))
        assert_keys(d, "model", "mainTokens")

    def test_model_is_string(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/overview"))
        assert isinstance(d["model"], str)
        assert len(d["model"]) > 0

    def test_main_tokens_is_number(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/overview"))
        assert isinstance(d["mainTokens"], (int, float))


class TestChannels:
    def test_status(self, api, base_url):
        r = get(api, base_url, "/api/channels")
        assert_ok(r)

    def test_returns_channels_list(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/channels"))
        assert "channels" in d
        assert isinstance(d["channels"], list)



class TestHealth:
    def test_status(self, api, base_url):
        r = get(api, base_url, "/api/health")
        assert_ok(r)

    def test_has_checks(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/health"))
        assert "checks" in d
        assert isinstance(d["checks"], list)


class TestSystemHealth:
    def test_status(self, api, base_url):
        r = get(api, base_url, "/api/system-health")
        assert_ok(r)

    def test_response_is_dict(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/system-health"))
        assert isinstance(d, dict)


class TestSessions:
    def test_status(self, api, base_url):
        r = get(api, base_url, "/api/sessions")
        assert_ok(r)

    def test_response_is_list_or_dict(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/sessions"))
        assert isinstance(d, (list, dict))


class TestCrons:
    def test_status(self, api, base_url):
        r = get(api, base_url, "/api/crons")
        assert_ok(r)

    def test_response_is_list_or_dict(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/crons"))
        assert isinstance(d, (list, dict))


class TestTranscripts:
    def test_status(self, api, base_url):
        r = get(api, base_url, "/api/transcripts")
        assert_ok(r)

    def test_response_is_list_or_dict(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/transcripts"))
        assert isinstance(d, (list, dict))


class TestUsage:
    def test_status(self, api, base_url):
        r = get(api, base_url, "/api/usage")
        assert_ok(r)

    def test_response_is_dict(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/usage"))
        assert isinstance(d, dict)



# ---------------------------------------------------------------------------
# Channel endpoints
# ---------------------------------------------------------------------------

FULL_CHANNEL_KEYS = ["messages", "todayIn", "todayOut"]
BASIC_CHANNEL_KEYS = ["messages"]

CHANNELS = {
    "telegram":  FULL_CHANNEL_KEYS,
    "imessage":  FULL_CHANNEL_KEYS,
    "whatsapp":  BASIC_CHANNEL_KEYS,
    "signal":    BASIC_CHANNEL_KEYS,
    "discord":   BASIC_CHANNEL_KEYS,
    "slack":     BASIC_CHANNEL_KEYS,
    "webchat":   BASIC_CHANNEL_KEYS,
}


@pytest.mark.parametrize("channel,required_keys", CHANNELS.items())
class TestChannelEndpoints:
    def test_status(self, api, base_url, channel, required_keys):
        r = get(api, base_url, f"/api/channel/{channel}")
        assert_ok(r)

    def test_required_keys(self, api, base_url, channel, required_keys):
        d = assert_ok(get(api, base_url, f"/api/channel/{channel}"))
        # iMessage may return a note on non-macOS platforms instead of full data
        if channel == "imessage" and "note" in d:
            assert isinstance(d["note"], str)
            return
        assert_keys(d, *required_keys)

    def test_messages_is_list(self, api, base_url, channel, required_keys):
        d = assert_ok(get(api, base_url, f"/api/channel/{channel}"))
        # iMessage may return a note on non-macOS platforms
        if channel == "imessage" and "note" in d:
            assert isinstance(d["note"], str)
            return
        assert isinstance(d["messages"], list), (
            f"channel/{channel}: 'messages' should be a list"
        )

    def test_today_counts_are_numbers(self, api, base_url, channel, required_keys):
        if "todayIn" not in required_keys:
            pytest.skip(f"channel/{channel} does not expose todayIn/todayOut")
        d = assert_ok(get(api, base_url, f"/api/channel/{channel}"))
        # iMessage may return a note on non-macOS platforms
        if channel == "imessage" and "note" in d:
            pytest.skip("iMessage not available on this platform")
        assert isinstance(d["todayIn"], (int, float))
        assert isinstance(d["todayOut"], (int, float))


# ---------------------------------------------------------------------------
# Heartbeat Gap Alerting
# ---------------------------------------------------------------------------

class TestHeartbeatStatus:
    def test_heartbeat_status_endpoint(self, api, base_url):
        """Heartbeat status endpoint returns 200 with expected keys."""
        d = assert_ok(get(api, base_url, "/api/heartbeat-status"))
        assert_keys(d, "status", "last_heartbeat_ts", "interval_seconds", "threshold_seconds")

    def test_heartbeat_status_values(self, api, base_url):
        """Status is one of: unknown, ok, warning, silent."""
        d = assert_ok(get(api, base_url, "/api/heartbeat-status"))
        assert d["status"] in ("unknown", "ok", "warning", "silent"), (
            f"Unexpected status: {d['status']}"
        )

    def test_heartbeat_interval_positive(self, api, base_url):
        """Interval should be a positive number of seconds."""
        d = assert_ok(get(api, base_url, "/api/heartbeat-status"))
        assert d["interval_seconds"] > 0

    def test_heartbeat_threshold_gt_interval(self, api, base_url):
        """Threshold should be greater than interval (1.5x)."""
        d = assert_ok(get(api, base_url, "/api/heartbeat-status"))
        assert d["threshold_seconds"] > d["interval_seconds"]

    def test_heartbeat_ping(self, api, base_url):
        """Heartbeat ping endpoint records a heartbeat event."""
        r = api.post(f"{base_url}/api/heartbeat-ping", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d.get("ok") is True

    def test_heartbeat_status_after_ping(self, api, base_url):
        """After ping, heartbeat status should be ok."""
        api.post(f"{base_url}/api/heartbeat-ping", timeout=10)
        d = assert_ok(get(api, base_url, "/api/heartbeat-status"))
        assert d["status"] == "ok", f"Expected 'ok' after ping, got '{d['status']}'"
        assert d["gap_seconds"] is not None
        assert d["gap_seconds"] < 5  # should be very recent

    def test_system_health_includes_heartbeat(self, api, base_url):
        """System health endpoint includes heartbeat status."""
        d = assert_ok(get(api, base_url, "/api/system-health"))
        assert "heartbeat" in d, "system-health should include heartbeat key"
        hb = d["heartbeat"]
        assert_keys(hb, "status", "interval_seconds")

    def test_system_health_includes_sandbox_field(self, api, base_url):
        """System health endpoint includes sandbox field (may be null)."""
        d = assert_ok(get(api, base_url, "/api/system-health"))
        assert "sandbox" in d, "system-health should include sandbox key"
        # sandbox is null when not in a sandboxed environment
        if d["sandbox"] is not None:
            assert "name" in d["sandbox"]
            assert "status" in d["sandbox"]

    def test_system_health_includes_inference_field(self, api, base_url):
        """System health endpoint includes inference field (may be null)."""
        d = assert_ok(get(api, base_url, "/api/system-health"))
        assert "inference" in d, "system-health should include inference key"
        if d["inference"] is not None:
            assert "provider" in d["inference"] or "model" in d["inference"]

    def test_system_health_includes_security_field(self, api, base_url):
        """System health endpoint includes security field (may be null)."""
        d = assert_ok(get(api, base_url, "/api/system-health"))
        assert "security" in d, "system-health should include security key"


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

class TestSecurity:
    def test_threats_endpoint(self, api, base_url):
        """Security threats endpoint returns 200."""
        d = assert_ok(get(api, base_url, "/api/security/threats"))

    def test_threats_response_structure(self, api, base_url):
        """Threats response has required keys."""
        d = assert_ok(get(api, base_url, "/api/security/threats"))
        assert_keys(d, "threats", "counts", "scanned_events")
        assert isinstance(d["threats"], list)
        assert isinstance(d["counts"], dict)
        assert_keys(d["counts"], "critical", "high", "medium", "low", "total")

    def test_threats_count_consistency(self, api, base_url):
        """Threat counts add up correctly."""
        d = assert_ok(get(api, base_url, "/api/security/threats"))
        counts = d["counts"]
        expected_total = counts["critical"] + counts["high"] + counts["medium"] + counts["low"]
        assert counts["total"] == expected_total, (
            f"Total {counts['total']} != sum of severities {expected_total}"
        )

    def test_signatures_endpoint(self, api, base_url):
        """Security signatures endpoint returns 200."""
        d = assert_ok(get(api, base_url, "/api/security/signatures"))

    def test_signatures_response_structure(self, api, base_url):
        """Signatures response has required keys."""
        d = assert_ok(get(api, base_url, "/api/security/signatures"))
        assert_keys(d, "signatures", "total")
        assert isinstance(d["signatures"], list)
        assert d["total"] >= 10, f"Expected at least 10 signatures, got {d['total']}"

    def test_signatures_have_required_fields(self, api, base_url):
        """Each signature has id, severity, description."""
        d = assert_ok(get(api, base_url, "/api/security/signatures"))
        for sig in d["signatures"]:
            assert_keys(sig, "id", "severity", "description", "tool_types")
            assert sig["severity"] in ("critical", "high", "medium", "low"), (
                f"Invalid severity: {sig['severity']}"
            )

    def test_threat_fields_if_present(self, api, base_url):
        """If threats exist, they have the right structure."""
        d = assert_ok(get(api, base_url, "/api/security/threats"))
        for t in d["threats"][:5]:  # check first 5
            assert_keys(t, "rule_id", "severity", "description", "detail", "time")


# ---------------------------------------------------------------------------
# Security Posture
# ---------------------------------------------------------------------------

class TestSecurityPosture:
    def test_posture_endpoint(self, api, base_url):
        """Security posture endpoint returns 200."""
        d = assert_ok(get(api, base_url, "/api/security/posture"))

    def test_posture_response_structure(self, api, base_url):
        """Posture response has score, checks, and counters."""
        d = assert_ok(get(api, base_url, "/api/security/posture"))
        assert_keys(d, "score", "checks", "passed", "failed", "warnings", "total")
        assert isinstance(d["checks"], list)
        assert d["score"] in ("A", "B", "C", "D", "F", "U"), (
            f"Unexpected score: {d['score']}"
        )

    def test_posture_checks_have_fields(self, api, base_url):
        """Each posture check has required fields."""
        d = assert_ok(get(api, base_url, "/api/security/posture"))
        for c in d["checks"]:
            assert_keys(c, "id", "label", "status", "detail", "severity", "weight")
            assert c["status"] in ("pass", "warn", "fail"), (
                f"Invalid check status: {c['status']}"
            )
            assert c["severity"] in ("critical", "high", "medium", "low"), (
                f"Invalid check severity: {c['severity']}"
            )

    def test_posture_counters_consistent(self, api, base_url):
        """Passed + warnings + failed = total."""
        d = assert_ok(get(api, base_url, "/api/security/posture"))
        assert d["passed"] + d["warnings"] + d["failed"] == d["total"], (
            f"Counters inconsistent: {d['passed']}+{d['warnings']}+{d['failed']} != {d['total']}"
        )


# ---------------------------------------------------------------------------
# Brain Activity
# ---------------------------------------------------------------------------

class TestBrainActivity:
    def test_brain_history_structure(self, api, base_url):
        """Brain history endpoint returns events, total, and sources."""
        d = assert_ok(get(api, base_url, "/api/brain-history"))
        assert_keys(d, "events", "total", "sources")
        assert isinstance(d["events"], list)
        assert isinstance(d["sources"], list)
        assert isinstance(d["total"], int)

    def test_brain_history_event_fields(self, api, base_url):
        """Brain events have required fields: time, source, type, detail."""
        d = assert_ok(get(api, base_url, "/api/brain-history"))
        for ev in d["events"][:10]:
            assert_keys(ev, "time", "source", "type", "detail", "color")

    def test_brain_history_sources_fields(self, api, base_url):
        """Source entries have id, label, color."""
        d = assert_ok(get(api, base_url, "/api/brain-history"))
        for s in d["sources"][:5]:
            assert_keys(s, "id", "label", "color")

    def test_brain_stream_sse_endpoint(self, api, base_url):
        """Brain stream SSE endpoint returns text/event-stream."""
        r = api.get(f"{base_url}/api/brain-stream", stream=True, timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        ct = r.headers.get("Content-Type", "")
        assert "text/event-stream" in ct, f"Expected text/event-stream, got {ct}"
        # Read initial connected event
        first_chunk = b""
        for chunk in r.iter_content(chunk_size=256):
            first_chunk += chunk
            if b"connected" in first_chunk or len(first_chunk) > 512:
                break
        r.close()
        assert b"connected" in first_chunk or b"data:" in first_chunk or b":\n" in first_chunk


class TestMemoryAnalytics:
    """Tests for memory analytics & bloat detection (GH #203)."""

    def test_memory_analytics_returns_200(self, api, base_url):
        """Memory analytics endpoint returns 200."""
        d = assert_ok(get(api, base_url, "/api/memory-analytics"))
        assert_keys(d, "totalBytes", "totalKB", "estTokens", "fileCount",
                     "files", "topFiles", "contextBudgets", "recommendations",
                     "hasBloat", "hasWarnings", "thresholds")

    def test_memory_analytics_context_budgets(self, api, base_url):
        """Context budgets contain all three model tiers."""
        d = assert_ok(get(api, base_url, "/api/memory-analytics"))
        budgets = d["contextBudgets"]
        for key in ("claude_200k", "gpt4_128k", "gemini_1m"):
            assert key in budgets, f"Missing budget tier '{key}'"
            assert_keys(budgets[key], "limit", "memoryTokens", "percentUsed", "status")

    def test_memory_analytics_custom_thresholds(self, api, base_url):
        """Custom warn/crit thresholds are reflected."""
        d = assert_ok(get(api, base_url, "/api/memory-analytics?warn_kb=4&crit_kb=8"))
        assert d["thresholds"]["warnKB"] == 4
        assert d["thresholds"]["critKB"] == 8

    def test_memory_analytics_files_have_status(self, api, base_url):
        """Each file entry has status (ok/warning/critical)."""
        d = assert_ok(get(api, base_url, "/api/memory-analytics"))
        for f in d["files"]:
            assert_keys(f, "path", "sizeBytes", "sizeKB", "estTokens", "status")
            assert f["status"] in ("ok", "warning", "critical")




class TestHeatmap:
    """Tests for the 30-day activity heatmap endpoint."""

    def test_heatmap_returns_200(self, api, base_url):
        """Heatmap endpoint returns 200."""
        r = api.get(f"{base_url}/api/heatmap", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"

    def test_heatmap_has_required_keys(self, api, base_url):
        """Response contains 'days' list and 'max' value."""
        d = assert_ok(get(api, base_url, "/api/heatmap"))
        assert_keys(d, "days", "max")
        assert isinstance(d["days"], list), "'days' must be a list"
        assert isinstance(d["max"], (int, float)), "'max' must be numeric"

    def test_heatmap_returns_30_days(self, api, base_url):
        """Heatmap covers exactly 30 days."""
        d = assert_ok(get(api, base_url, "/api/heatmap"))
        assert len(d["days"]) == 30, f"Expected 30 days, got {len(d['days'])}"

    def test_heatmap_each_day_has_24_hours(self, api, base_url):
        """Every day entry has exactly 24 hourly buckets."""
        d = assert_ok(get(api, base_url, "/api/heatmap"))
        for day in d["days"]:
            assert "hours" in day, f"Day entry missing 'hours': {day}"
            assert len(day["hours"]) == 24, (
                f"Expected 24 hourly buckets, got {len(day['hours'])} for {day.get('label')}"
            )

    def test_heatmap_day_has_label_and_date(self, api, base_url):
        """Every day entry has 'label' and 'date' fields."""
        d = assert_ok(get(api, base_url, "/api/heatmap"))
        for day in d["days"]:
            assert_keys(day, "label", "date", "hours")

    def test_heatmap_hours_are_non_negative_ints(self, api, base_url):
        """All hourly counts are non-negative integers."""
        d = assert_ok(get(api, base_url, "/api/heatmap"))
        for day in d["days"]:
            for count in day["hours"]:
                assert isinstance(count, int) and count >= 0, (
                    f"Invalid hourly count {count!r} in {day.get('label')}"
                )

    def test_heatmap_max_matches_data(self, api, base_url):
        """'max' equals the maximum hourly event count across all days."""
        d = assert_ok(get(api, base_url, "/api/heatmap"))
        computed_max = max(
            (max(day["hours"]) for day in d["days"]), default=0
        )
        assert d["max"] == computed_max, (
            f"'max' field {d['max']} does not match computed max {computed_max}"
        )
