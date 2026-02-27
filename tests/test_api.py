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


class TestSubagents:
    def test_status(self, api, base_url):
        r = get(api, base_url, "/api/subagents")
        assert_ok(r)

    def test_response_is_list_or_dict(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/subagents"))
        assert isinstance(d, (list, dict))


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
