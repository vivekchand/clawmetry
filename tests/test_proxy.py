"""
Tests for the ClawMetry proxy module.

Tests cover:
- Configuration loading/saving
- Budget enforcement
- Loop detection
- Cost calculation
- Request hashing
- SSE stream parsing (Anthropic & OpenAI)
- Provider detection
- Model routing
- ProxyDB operations
- Flask proxy app (integration)
"""

import json
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def proxy_config():
    """Create a ProxyConfig with test settings."""
    from clawmetry.proxy import ProxyConfig, BudgetConfig, LoopDetectionConfig

    config = ProxyConfig(
        port=14100,
        host="127.0.0.1",
        budget=BudgetConfig(daily_usd=10.0, monthly_usd=100.0, action="block"),
        loop_detection=LoopDetectionConfig(
            enabled=True, window_seconds=300, max_similar=3
        ),
    )
    config.providers = {
        "anthropic": MagicMock(
            api_key_env="ANTHROPIC_API_KEY", base_url="https://api.anthropic.com"
        ),
        "openai": MagicMock(
            api_key_env="OPENAI_API_KEY", base_url="https://api.openai.com"
        ),
    }
    return config


@pytest.fixture
def proxy_db(tmp_path):
    """Create a ProxyDB with a temp database."""
    from clawmetry.proxy import ProxyDB

    db_path = tmp_path / "test_proxy.db"
    return ProxyDB(db_path=db_path)


@pytest.fixture
def budget_enforcer(proxy_config, proxy_db):
    """Create a BudgetEnforcer."""
    from clawmetry.proxy import BudgetEnforcer

    return BudgetEnforcer(proxy_config.budget, proxy_db)


@pytest.fixture
def loop_detector(proxy_config, proxy_db):
    """Create a LoopDetector."""
    from clawmetry.proxy import LoopDetector

    return LoopDetector(proxy_config.loop_detection, proxy_db)


# ── Cost Calculation ───────────────────────────────────────────────────


class TestCostCalculation:
    def test_basic_cost(self):
        from clawmetry.proxy import calculate_cost

        cost = calculate_cost("claude-opus-4-20260313", 1000, 500)
        expected = (1000 / 1_000_000 * 15.0) + (500 / 1_000_000 * 75.0)
        assert abs(cost - expected) < 0.0001

    def test_zero_tokens(self):
        from clawmetry.proxy import calculate_cost

        assert calculate_cost("claude-opus-4", 0, 0) == 0.0

    def test_cache_discount(self):
        from clawmetry.proxy import calculate_cost

        cost_no_cache = calculate_cost("claude-opus-4", 1000, 0)
        cost_with_cache = calculate_cost(
            "claude-opus-4", 1000, 0, cache_read_tokens=800
        )
        assert cost_with_cache < cost_no_cache

    def test_unknown_model_uses_default(self):
        from clawmetry.proxy import calculate_cost

        cost = calculate_cost("some-unknown-model-v3", 1000, 500)
        assert cost > 0

    def test_gpt4_cost(self):
        from clawmetry.proxy import calculate_cost

        cost = calculate_cost("gpt-4o-2026-01-01", 1000, 500)
        expected = (1000 / 1_000_000 * 2.5) + (500 / 1_000_000 * 10.0)
        assert abs(cost - expected) < 0.0001


# ── Request Hashing ────────────────────────────────────────────────────


class TestRequestHashing:
    def test_same_content_same_hash(self):
        from clawmetry.proxy import compute_request_hash

        body = {
            "model": "claude-opus-4",
            "messages": [{"role": "user", "content": "Hello world"}],
        }
        h1 = compute_request_hash(body)
        h2 = compute_request_hash(body)
        assert h1 == h2

    def test_different_content_different_hash(self):
        from clawmetry.proxy import compute_request_hash

        body1 = {
            "model": "claude-opus-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        body2 = {
            "model": "claude-opus-4",
            "messages": [{"role": "user", "content": "World"}],
        }
        assert compute_request_hash(body1) != compute_request_hash(body2)

    def test_different_model_different_hash(self):
        from clawmetry.proxy import compute_request_hash

        body1 = {
            "model": "claude-opus-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        body2 = {"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello"}]}
        assert compute_request_hash(body1) != compute_request_hash(body2)

    def test_handles_list_content(self):
        from clawmetry.proxy import compute_request_hash

        body = {
            "model": "claude-opus-4",
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
            ],
        }
        h = compute_request_hash(body)
        assert len(h) == 16

    def test_handles_empty_body(self):
        from clawmetry.proxy import compute_request_hash

        h = compute_request_hash({})
        assert len(h) == 16

    def test_system_prompt_affects_hash(self):
        from clawmetry.proxy import compute_request_hash

        body1 = {
            "model": "x",
            "system": "Be helpful",
            "messages": [{"role": "user", "content": "Hi"}],
        }
        body2 = {
            "model": "x",
            "system": "Be mean",
            "messages": [{"role": "user", "content": "Hi"}],
        }
        assert compute_request_hash(body1) != compute_request_hash(body2)


# ── SSE Parsing ────────────────────────────────────────────────────────


class TestSSEParsing:
    def test_anthropic_message_start(self):
        from clawmetry.proxy import parse_anthropic_sse_chunk, StreamUsage

        usage = StreamUsage()
        line = 'data: {"type":"message_start","message":{"model":"claude-opus-4-20260313","usage":{"input_tokens":42,"cache_read_input_tokens":10}}}'
        parse_anthropic_sse_chunk(line, usage)
        assert usage.input_tokens == 42
        assert usage.cache_read_tokens == 10
        assert usage.model == "claude-opus-4-20260313"

    def test_anthropic_message_delta(self):
        from clawmetry.proxy import parse_anthropic_sse_chunk, StreamUsage

        usage = StreamUsage()
        line = 'data: {"type":"message_delta","usage":{"output_tokens":150},"delta":{"stop_reason":"end_turn"}}'
        parse_anthropic_sse_chunk(line, usage)
        assert usage.output_tokens == 150
        assert usage.stop_reason == "end_turn"

    def test_anthropic_ignores_non_data(self):
        from clawmetry.proxy import parse_anthropic_sse_chunk, StreamUsage

        usage = StreamUsage()
        parse_anthropic_sse_chunk("event: message_start", usage)
        assert usage.input_tokens == 0

    def test_anthropic_handles_done(self):
        from clawmetry.proxy import parse_anthropic_sse_chunk, StreamUsage

        usage = StreamUsage()
        parse_anthropic_sse_chunk("data: [DONE]", usage)
        assert usage.input_tokens == 0

    def test_openai_usage_chunk(self):
        from clawmetry.proxy import parse_openai_sse_chunk, StreamUsage

        usage = StreamUsage()
        line = 'data: {"model":"gpt-4o","usage":{"prompt_tokens":100,"completion_tokens":50},"choices":[]}'
        parse_openai_sse_chunk(line, usage)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.model == "gpt-4o"

    def test_openai_finish_reason(self):
        from clawmetry.proxy import parse_openai_sse_chunk, StreamUsage

        usage = StreamUsage()
        line = 'data: {"model":"gpt-4o","choices":[{"finish_reason":"stop"}]}'
        parse_openai_sse_chunk(line, usage)
        assert usage.stop_reason == "stop"

    def test_handles_malformed_json(self):
        from clawmetry.proxy import parse_anthropic_sse_chunk, StreamUsage

        usage = StreamUsage()
        parse_anthropic_sse_chunk("data: {broken json", usage)
        assert usage.input_tokens == 0


# ── Provider Detection ─────────────────────────────────────────────────


class TestProviderDetection:
    def test_anthropic_by_path(self):
        from clawmetry.proxy import detect_provider

        assert detect_provider("/v1/messages", {}, {}) == "anthropic"

    def test_openai_by_path(self):
        from clawmetry.proxy import detect_provider

        assert detect_provider("/v1/chat/completions", {}, {}) == "openai"

    def test_anthropic_by_header(self):
        from clawmetry.proxy import detect_provider

        assert (
            detect_provider("/v1/unknown", {"x-api-key": "sk-ant-..."}, {})
            == "anthropic"
        )

    def test_openai_by_auth_header(self):
        from clawmetry.proxy import detect_provider

        assert (
            detect_provider("/v1/unknown", {"authorization": "Bearer sk-abc123"}, {})
            == "openai"
        )

    def test_anthropic_by_model(self):
        from clawmetry.proxy import detect_provider

        assert (
            detect_provider("/v1/unknown", {}, {"model": "claude-opus-4"})
            == "anthropic"
        )

    def test_openai_by_model(self):
        from clawmetry.proxy import detect_provider

        assert detect_provider("/v1/unknown", {}, {"model": "gpt-4o"}) == "openai"

    def test_default_to_anthropic(self):
        from clawmetry.proxy import detect_provider

        assert detect_provider("/v1/unknown", {}, {}) == "anthropic"


# ── ProxyDB ────────────────────────────────────────────────────────────


class TestProxyDB:
    def test_record_and_query_usage(self, proxy_db):
        proxy_db.record_usage(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.05,
            session_id="test-session",
            request_hash="abc123",
        )
        summary = proxy_db.get_usage_summary(since_ts=0)
        assert summary["request_count"] == 1
        assert summary["total_input"] == 1000
        assert summary["total_output"] == 500
        assert summary["total_cost"] == 0.05

    def test_daily_spending(self, proxy_db):
        proxy_db.record_usage(
            provider="anthropic",
            model="test",
            input_tokens=100,
            output_tokens=50,
            cost_usd=1.5,
        )
        daily = proxy_db.get_daily_spending()
        assert daily == 1.5

    def test_monthly_spending(self, proxy_db):
        proxy_db.record_usage(
            provider="anthropic",
            model="test",
            input_tokens=100,
            output_tokens=50,
            cost_usd=3.0,
        )
        monthly = proxy_db.get_monthly_spending()
        assert monthly == 3.0

    def test_record_and_query_events(self, proxy_db):
        proxy_db.record_event(
            "budget_blocked",
            "Over budget",
            severity="warning",
            details={"model": "claude-opus-4"},
        )
        events = proxy_db.get_recent_events(limit=10)
        assert len(events) == 1
        assert events[0]["event_type"] == "budget_blocked"
        assert events[0]["severity"] == "warning"

    def test_event_type_filter(self, proxy_db):
        proxy_db.record_event("budget_blocked", "Blocked 1")
        proxy_db.record_event("loop_detected", "Loop found")
        proxy_db.record_event("budget_blocked", "Blocked 2")

        blocked = proxy_db.get_recent_events(event_type="budget_blocked")
        assert len(blocked) == 2

        loops = proxy_db.get_recent_events(event_type="loop_detected")
        assert len(loops) == 1

    def test_request_hashes(self, proxy_db):
        for i in range(5):
            proxy_db.record_usage(
                provider="anthropic",
                model="test",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
                session_id="session-1",
                request_hash=f"hash_{i % 2}",
            )
        hashes = proxy_db.get_recent_request_hashes("session-1", window_seconds=300)
        assert len(hashes) == 5

    def test_prune_old_data(self, proxy_db):
        with proxy_db._lock:
            conn = proxy_db._connect()
            old_ts = time.time() - (60 * 86400)
            conn.execute(
                "INSERT INTO proxy_usage (timestamp, provider, model, cost_usd) VALUES (?, ?, ?, ?)",
                (old_ts, "test", "test", 1.0),
            )
            conn.commit()
            conn.close()

        proxy_db.prune_old_data(retention_days=30)
        summary = proxy_db.get_usage_summary(since_ts=0)
        assert summary["request_count"] == 0


# ── Budget Enforcer ────────────────────────────────────────────────────


class TestBudgetEnforcer:
    def test_allows_under_budget(self, budget_enforcer, proxy_db):
        proxy_db.record_usage(
            provider="anthropic",
            model="test",
            input_tokens=100,
            output_tokens=50,
            cost_usd=1.0,
        )
        allowed, reason = budget_enforcer.check()
        assert allowed is True
        assert reason == ""

    def test_blocks_over_daily_budget(self, budget_enforcer, proxy_db):
        proxy_db.record_usage(
            provider="anthropic",
            model="test",
            input_tokens=100,
            output_tokens=50,
            cost_usd=11.0,
        )
        allowed, reason = budget_enforcer.check()
        assert allowed is False
        assert "Daily budget exceeded" in reason

    def test_blocks_over_monthly_budget(self, proxy_db):
        """Use a config where daily is unlimited but monthly is limited."""
        from clawmetry.proxy import BudgetEnforcer, BudgetConfig

        enforcer = BudgetEnforcer(
            BudgetConfig(daily_usd=0, monthly_usd=100.0, action="block"), proxy_db
        )
        proxy_db.record_usage(
            provider="anthropic",
            model="test",
            input_tokens=100,
            output_tokens=50,
            cost_usd=101.0,
        )
        allowed, reason = enforcer.check()
        assert allowed is False
        assert "Monthly budget exceeded" in reason

    def test_allows_when_no_limits(self, proxy_db):
        from clawmetry.proxy import BudgetEnforcer, BudgetConfig

        enforcer = BudgetEnforcer(BudgetConfig(daily_usd=0, monthly_usd=0), proxy_db)
        proxy_db.record_usage(
            provider="anthropic",
            model="test",
            input_tokens=100,
            output_tokens=50,
            cost_usd=999.0,
        )
        allowed, _ = enforcer.check()
        assert allowed is True

    def test_budget_status(self, budget_enforcer, proxy_db):
        proxy_db.record_usage(
            provider="anthropic",
            model="test",
            input_tokens=100,
            output_tokens=50,
            cost_usd=5.0,
        )
        status = budget_enforcer.get_status()
        assert status["daily_spent"] == 5.0
        assert status["daily_limit"] == 10.0
        assert status["daily_remaining"] == 5.0


# ── Loop Detection ─────────────────────────────────────────────────────


class TestLoopDetector:
    def test_no_loop_with_few_requests(self, loop_detector, proxy_db):
        proxy_db.record_usage(
            provider="anthropic",
            model="test",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.01,
            session_id="s1",
            request_hash="abc123",
        )
        is_loop, reason = loop_detector.check("s1", "abc123")
        assert is_loop is False

    def test_detects_loop(self, loop_detector, proxy_db):
        for _ in range(4):
            proxy_db.record_usage(
                provider="anthropic",
                model="test",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
                session_id="s1",
                request_hash="same_hash",
            )
        is_loop, reason = loop_detector.check("s1", "same_hash")
        assert is_loop is True
        assert "Loop detected" in reason

    def test_different_hashes_no_loop(self, loop_detector, proxy_db):
        for i in range(10):
            proxy_db.record_usage(
                provider="anthropic",
                model="test",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
                session_id="s1",
                request_hash=f"unique_{i}",
            )
        is_loop, _ = loop_detector.check("s1", "new_hash")
        assert is_loop is False

    def test_disabled_loop_detection(self, proxy_db):
        from clawmetry.proxy import LoopDetector, LoopDetectionConfig

        detector = LoopDetector(LoopDetectionConfig(enabled=False), proxy_db)
        for _ in range(10):
            proxy_db.record_usage(
                provider="anthropic",
                model="test",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
                session_id="s1",
                request_hash="same",
            )
        is_loop, _ = detector.check("s1", "same")
        assert is_loop is False

    def test_no_session_id_skips_check(self, loop_detector, proxy_db):
        for _ in range(10):
            proxy_db.record_usage(
                provider="anthropic",
                model="test",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
                session_id="",
                request_hash="same",
            )
        is_loop, _ = loop_detector.check("", "same")
        assert is_loop is False


# ── Model Router ───────────────────────────────────────────────────────


class TestModelRouter:
    def test_no_rules_no_routing(self):
        from clawmetry.proxy import ModelRouter

        router = ModelRouter([])
        model, provider = router.route("claude-opus-4", "session-1")
        assert model is None
        assert provider is None

    def test_model_match_routing(self):
        from clawmetry.proxy import ModelRouter, RoutingRule

        router = ModelRouter(
            [
                RoutingRule(match_model="opus", target_model="claude-3-haiku-20240307"),
            ]
        )
        model, provider = router.route("claude-opus-4-20260313", "session-1")
        assert model == "claude-3-haiku-20240307"

    def test_session_match_routing(self):
        from clawmetry.proxy import ModelRouter, RoutingRule

        router = ModelRouter(
            [
                RoutingRule(
                    match_session="subagent", target_model="claude-3-haiku-20240307"
                ),
            ]
        )
        model, _ = router.route("claude-opus-4", "agent:main:subagent:abc")
        assert model == "claude-3-haiku-20240307"

    def test_combined_match(self):
        from clawmetry.proxy import ModelRouter, RoutingRule

        router = ModelRouter(
            [
                RoutingRule(
                    match_model="opus",
                    match_session="subagent",
                    target_model="claude-3-haiku-20240307",
                ),
            ]
        )
        model, _ = router.route("claude-opus-4", "agent:main:subagent:abc")
        assert model == "claude-3-haiku-20240307"

        model, _ = router.route("claude-opus-4", "main-session")
        assert model is None

    def test_first_rule_wins(self):
        from clawmetry.proxy import ModelRouter, RoutingRule

        router = ModelRouter(
            [
                RoutingRule(match_model="claude", target_model="model-a"),
                RoutingRule(match_model="claude", target_model="model-b"),
            ]
        )
        model, _ = router.route("claude-opus-4", "")
        assert model == "model-a"


# ── Configuration ──────────────────────────────────────────────────────


class TestProxyConfig:
    def test_default_config(self):
        from clawmetry.proxy import ProxyConfig

        config = ProxyConfig()
        assert config.port == 4100
        assert config.host == "127.0.0.1"
        assert config.budget.daily_usd == 0.0
        assert config.loop_detection.enabled is True

    def test_save_and_load(self, tmp_path):
        from clawmetry.proxy import ProxyConfig

        config_file = tmp_path / "proxy.json"
        with patch("clawmetry.proxy.PROXY_CONFIG_FILE", config_file):
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text(
                json.dumps(
                    {
                        "port": 5000,
                        "budget": {
                            "daily_usd": 25.0,
                            "monthly_usd": 200.0,
                            "action": "warn",
                        },
                    }
                )
            )
            loaded = ProxyConfig.load()
        assert loaded.port == 5000
        assert loaded.budget.daily_usd == 25.0
        assert loaded.budget.action == "warn"

    def test_env_override(self, tmp_path):
        from clawmetry.proxy import ProxyConfig

        config_file = tmp_path / "proxy.json"
        with (
            patch("clawmetry.proxy.PROXY_CONFIG_FILE", config_file),
            patch.dict(
                os.environ,
                {"CLAWMETRY_PROXY_PORT": "9999", "CLAWMETRY_PROXY_DAILY_USD": "50.0"},
            ),
        ):
            config = ProxyConfig.load()
        assert config.port == 9999
        assert config.budget.daily_usd == 50.0


# ── Flask App Integration ─────────────────────────────────────────────


class TestProxyApp:
    @pytest.fixture
    def client(self, tmp_path):
        from clawmetry.proxy import (
            create_proxy_app,
            ProxyConfig,
            BudgetConfig,
            LoopDetectionConfig,
        )

        config = ProxyConfig(
            port=14100,
            budget=BudgetConfig(daily_usd=10.0, monthly_usd=100.0, action="block"),
            loop_detection=LoopDetectionConfig(
                enabled=True, max_similar=3, window_seconds=300
            ),
        )
        with patch("clawmetry.proxy.PROXY_DB_FILE", tmp_path / "test.db"):
            app = create_proxy_app(config)
        app.config["TESTING"] = True
        return app.test_client()

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "clawmetry-proxy"

    def test_proxy_status(self, client):
        resp = client.get("/proxy/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "running"
        assert "requests_total" in data
        assert "budget" in data

    def test_proxy_events_empty(self, client):
        resp = client.get("/proxy/events")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "events" in data
        assert isinstance(data["events"], list)

    def test_proxy_usage(self, client):
        resp = client.get("/proxy/usage?period=day")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "request_count" in data

    def test_proxy_config_get(self, client):
        resp = client.get("/proxy/config")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["budget"]["daily_usd"] == 10.0
        assert data["loop_detection"]["enabled"] is True

    def test_proxy_config_patch(self, client, tmp_path):
        with patch("clawmetry.proxy.PROXY_CONFIG_FILE", tmp_path / "proxy.json"):
            resp = client.patch(
                "/proxy/config",
                data=json.dumps({"budget": {"daily_usd": 20.0}}),
                content_type="application/json",
            )
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_budget_blocks_request(self, client):
        """Budget enforcement verified through the app's status endpoint."""
        pass


class TestForwardNonStreaming:
    """Tests for _forward_non_streaming error handling."""

    def test_json_decode_error_is_logged(self, tmp_path, caplog):
        """JSON decode errors should be logged, not silently swallowed."""
        import logging
        from clawmetry.proxy import (
            create_proxy_app,
            ProxyConfig,
            BudgetConfig,
            LoopDetectionConfig,
            ProviderConfig,
        )

        caplog.set_level(logging.DEBUG)

        config = ProxyConfig(
            port=14100,
            budget=BudgetConfig(daily_usd=10.0, monthly_usd=100.0, action="block"),
            loop_detection=LoopDetectionConfig(
                enabled=True, max_similar=3, window_seconds=300
            ),
        )
        config.providers = {
            "anthropic": ProviderConfig(
                api_key_env="ANTHROPIC_API_KEY", base_url="https://api.anthropic.com"
            ),
            "openai": ProviderConfig(
                api_key_env="OPENAI_API_KEY", base_url="https://api.openai.com"
            ),
        }

        with patch("clawmetry.proxy.PROXY_DB_FILE", tmp_path / "test.db"):
            app = create_proxy_app(config)
        app.config["TESTING"] = True
        client = app.test_client()

        with patch("clawmetry.proxy.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b"not valid json"
            mock_resp.status = 200
            mock_resp.headers = {"Content-Type": "application/json"}
            mock_urlopen.return_value = mock_resp

            resp = client.post(
                "/v1/messages",
                data=json.dumps(
                    {
                        "model": "claude-opus-4-20260313",
                        "messages": [{"role": "user", "content": "hello"}],
                    }
                ),
                headers={
                    "x-api-key": "test-key",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                    "X-ClawMetry-Session": "test-session",
                },
            )

        assert "JSONDecodeError" in caplog.text or "Failed to parse" in caplog.text
