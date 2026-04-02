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

    def test_system_health_includes_service_status(self, api, base_url):
        """System health includes compact service_status dict for fleet sync."""
        d = assert_ok(get(api, base_url, "/api/system-health"))
        assert "service_status" in d, "system-health should include service_status key"
        ss = d["service_status"]
        assert isinstance(ss, dict), "service_status must be a dict"
        assert "gateway" in ss, "service_status.gateway must be present"
        assert isinstance(ss["gateway"], bool), "service_status.gateway must be bool"
        assert "channels" in ss, "service_status.channels must be present"
        assert isinstance(ss["channels"], list), "service_status.channels must be a list"
        assert "sync" in ss, "service_status.sync must be present"
        assert "resources" in ss, "service_status.resources must be present"
        assert ss["resources"] in ("ok", "warn", "critical"), \
            f"service_status.resources must be ok/warn/critical, got {ss['resources']}"

    def test_service_status_endpoint(self, api, base_url):
        """Dedicated /api/service-status endpoint returns compact status."""
        d = assert_ok(get(api, base_url, "/api/service-status"))
        assert "service_status" in d, "/api/service-status must return service_status key"
        ss = d["service_status"]
        assert isinstance(ss, dict)
        assert "gateway" in ss
        assert isinstance(ss["gateway"], bool)
        assert "channels" in ss
        assert isinstance(ss["channels"], list)
        assert "sync" in ss
        assert "resources" in ss
        assert ss["resources"] in ("ok", "warn", "critical")


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




class TestTraceClusters:
    """Tests for trace clustering endpoint (closes GH #406)."""

    def test_clusters_returns_200(self, api, base_url):
        """Trace clusters endpoint returns 200."""
        d = assert_ok(get(api, base_url, "/api/sessions/clusters"))
        assert_keys(d, "clusters", "total_sessions", "days", "generated_at")

    def test_clusters_is_list(self, api, base_url):
        """clusters field is a list."""
        d = assert_ok(get(api, base_url, "/api/sessions/clusters"))
        assert isinstance(d["clusters"], list)

    def test_clusters_total_sessions_is_int(self, api, base_url):
        """total_sessions is a non-negative integer."""
        d = assert_ok(get(api, base_url, "/api/sessions/clusters"))
        assert isinstance(d["total_sessions"], int)
        assert d["total_sessions"] >= 0

    def test_clusters_days_filter(self, api, base_url):
        """days query parameter is respected."""
        d = assert_ok(get(api, base_url, "/api/sessions/clusters?days=7"))
        assert d["days"] == 7

    def test_cluster_shape(self, api, base_url):
        """Each cluster has the expected fields."""
        d = assert_ok(get(api, base_url, "/api/sessions/clusters"))
        for c in d["clusters"]:
            assert_keys(c, "cluster_id", "label", "session_count", "total_tokens",
                         "total_cost_usd", "avg_cost_usd", "error_count",
                         "tool_category", "cost_tier", "has_errors",
                         "model_family", "top_tools")
            assert c["session_count"] >= 1
            assert c["total_tokens"] >= 0
            assert c["cost_tier"] in ("cheap", "medium", "expensive")
            assert isinstance(c["has_errors"], bool)


class TestActivityHeatmap:
    """Tests for activity heatmap endpoint (GH #69)."""

    def test_heatmap_default_7_days(self, api, base_url):
        """Heatmap default returns 7 days."""
        d = assert_ok(get(api, base_url, "/api/heatmap"))
        assert_keys(d, "days", "max", "n_days")
        assert d["n_days"] == 7
        assert len(d["days"]) == 7

    def test_heatmap_30_days(self, api, base_url):
        """Heatmap ?days=30 returns 30 days."""
        d = assert_ok(get(api, base_url, "/api/heatmap?days=30"))
        assert d["n_days"] == 30
        assert len(d["days"]) == 30

    def test_heatmap_max_clamped(self, api, base_url):
        """Heatmap days clamped to 90."""
        d = assert_ok(get(api, base_url, "/api/heatmap?days=999"))
        assert d["n_days"] == 90
        assert len(d["days"]) == 90

    def test_heatmap_day_structure(self, api, base_url):
        """Each day has label and 24 hourly buckets."""
        d = assert_ok(get(api, base_url, "/api/heatmap"))
        for day in d["days"]:
            assert "label" in day
            assert "hours" in day
            assert len(day["hours"]) == 24
            assert all(isinstance(h, int) and h >= 0 for h in day["hours"])

    def test_heatmap_max_nonneg(self, api, base_url):
        """max field is non-negative."""
        d = assert_ok(get(api, base_url, "/api/heatmap"))
        assert d["max"] >= 0

class TestModelAttribution:
    def test_model_attribution_returns_200(self, api, base_url):
        """Model attribution endpoint returns 200 with expected keys (GH #300)."""
        d = assert_ok(get(api, base_url, "/api/model-attribution"))
        assert_keys(d, "models", "primary_model", "total_turns", "model_count", "switches", "switch_count")

    def test_models_list_structure(self, api, base_url):
        """Each entry in models list has required fields."""
        d = assert_ok(get(api, base_url, "/api/model-attribution"))
        for m in d["models"]:
            assert_keys(m, "model", "turns", "sessions", "provider", "share_pct")
            assert isinstance(m["turns"], int)
            assert isinstance(m["sessions"], int)
            assert 0 <= m["share_pct"] <= 100

    def test_total_turns_consistency(self, api, base_url):
        """Sum of per-model turns equals total_turns."""
        d = assert_ok(get(api, base_url, "/api/model-attribution"))
        total = sum(m["turns"] for m in d["models"])
        assert total == d["total_turns"]

    def test_switches_is_list(self, api, base_url):
        """Switches field is a list capped at 50."""
        d = assert_ok(get(api, base_url, "/api/model-attribution"))
        assert isinstance(d["switches"], list)
        assert isinstance(d["switch_count"], int)
        assert len(d["switches"]) <= 50



class TestTokenVelocity:
    """Tests for GH #313 — token velocity alert endpoint."""

    def test_token_velocity_returns_200(self, api, base_url):
        """Token velocity endpoint returns HTTP 200."""
        r = get(api, base_url, "/api/token-velocity")
        assert r.status_code == 200, (
            f"Expected 200 for {r.url}, got {r.status_code}: {r.text[:200]}"
        )

    def test_token_velocity_structure(self, api, base_url):
        """Response contains required keys: alert, level, velocity_2min, flagged_sessions."""
        d = assert_ok(get(api, base_url, "/api/token-velocity"))
        assert_keys(d, "alert", "level", "velocity_2min", "flagged_sessions")
        assert isinstance(d["alert"], bool), "alert must be bool"
        assert isinstance(d["velocity_2min"], (int, float)), "velocity_2min must be a number"
        assert isinstance(d["flagged_sessions"], list), "flagged_sessions must be a list"

    def test_token_velocity_level_valid(self, api, base_url):
        """level field must be one of 'ok', 'warning', 'critical'."""
        d = assert_ok(get(api, base_url, "/api/token-velocity"))
        assert d["level"] in ("ok", "warning", "critical"), (
            f"Unexpected level: {d['level']!r}"
        )

    def test_token_velocity_cost_per_min_present(self, api, base_url):
        """cost_per_min field is present and non-negative."""
        d = assert_ok(get(api, base_url, "/api/token-velocity"))
        assert "cost_per_min" in d, "cost_per_min key missing"
        assert isinstance(d["cost_per_min"], (int, float)), "cost_per_min must be numeric"
        assert d["cost_per_min"] >= 0, "cost_per_min must be non-negative"

    def test_token_velocity_alert_matches_level(self, api, base_url):
        """alert bool must be False when level is 'ok', True otherwise."""
        d = assert_ok(get(api, base_url, "/api/token-velocity"))
        if d["level"] == "ok":
            assert d["alert"] is False, "alert should be False when level='ok'"
        else:
            assert d["alert"] is True, "alert should be True for warning/critical"
