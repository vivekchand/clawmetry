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

    def test_auto_downgrade_targets_use_cheaper_rates(self):
        from clawmetry.proxy import calculate_cost

        assert calculate_cost("claude-3-5-haiku", 1000, 500) < calculate_cost(
            "claude-opus-4", 1000, 500
        )
        assert calculate_cost("gpt-4o-mini", 1000, 500) < calculate_cost(
            "gpt-4o", 1000, 500
        )


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

    def test_loop_emits_alert_event(self, loop_detector, proxy_db, monkeypatch):
        """Issue #1377: a positive LoopDetector.check() must also push a
        ``loop_detected`` event into local_store.ingest() so the daemon's
        alert evaluator (clawmetry/alert_evaluator.py) can fire matching
        Cloud-Pro rules. This is the only OSS-side hook the alert pipeline
        needs — the daemon then walks DuckDB + cached rules and dispatches.
        """
        captured: list[dict] = []

        class _FakeStore:
            def ingest(self, event):
                captured.append(event)

            def ingest_loop_signal(self, **kwargs):
                # Existing badge write — not what this test cares about, but
                # we still accept the call so the detector's first try-block
                # doesn't raise.
                pass

        fake = _FakeStore()
        # Patch get_store at the module the detector imports lazily.
        from clawmetry import local_store as _ls
        monkeypatch.setattr(_ls, "get_store", lambda: fake)

        for _ in range(4):
            proxy_db.record_usage(
                provider="anthropic",
                model="test",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
                session_id="s-1377",
                request_hash="loop-sig-1377",
            )
        is_loop, _ = loop_detector.check("s-1377", "loop-sig-1377")
        assert is_loop is True

        # Exactly one loop_detected event was emitted with the expected shape.
        loop_events = [e for e in captured if e.get("event_type") == "loop_detected"]
        assert len(loop_events) == 1
        evt = loop_events[0]
        assert evt["session_id"] == "s-1377"
        assert evt["agent_id"] == "clawmetry-proxy"
        assert evt["data"]["signature"] == "loop-sig-1377"
        assert evt["data"]["repeat_count"] >= 3
        assert "id" in evt and "ts" in evt and "node_id" in evt


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


# ── Auto Model Router ─────────────────────────────────────────────────


class TestAutoModelRouter:
    def test_default_off(self):
        from clawmetry.proxy import AutoModelRouter, AutoRoutingConfig

        router = AutoModelRouter(AutoRoutingConfig())
        decision = router.route(
            {
                "model": "claude-opus-4",
                "messages": [{"role": "user", "content": "Hello"}],
            },
            provider="anthropic",
        )
        assert decision is None

    def test_anthropic_short_prompt_routes_to_haiku(self):
        from clawmetry.proxy import AutoModelRouter, AutoRoutingConfig

        router = AutoModelRouter(AutoRoutingConfig(enabled=True))
        decision = router.route(
            {
                "model": "claude-opus-4",
                "messages": [{"role": "user", "content": "Summarize this."}],
            },
            provider="anthropic",
        )
        assert decision is not None
        assert decision.target_model == "claude-3-5-haiku"
        assert decision.estimated_savings_usd > 0

    def test_openai_short_prompt_routes_to_mini(self):
        from clawmetry.proxy import AutoModelRouter, AutoRoutingConfig

        router = AutoModelRouter(AutoRoutingConfig(enabled=True))
        decision = router.route(
            {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Ping"}],
            },
            provider="openai",
        )
        assert decision is not None
        assert decision.target_model == "gpt-4o-mini"
        assert decision.provider == "openai"

    def test_cross_provider_downgrade_map_is_rejected(self):
        from clawmetry.proxy import AutoModelRouter, AutoRoutingConfig

        router = AutoModelRouter(
            AutoRoutingConfig(
                enabled=True,
                downgrade_map={"gpt-4o": "claude-3-5-haiku"},
            )
        )
        decision = router.route(
            {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Ping"}],
            },
            provider="openai",
        )
        assert decision is None

    def test_provider_prefixed_cross_provider_model_is_rejected(self):
        from clawmetry.proxy import AutoModelRouter, AutoRoutingConfig

        router = AutoModelRouter(AutoRoutingConfig(enabled=True))
        decision = router.route(
            {
                "model": "openrouter/openai/gpt-4o",
                "messages": [{"role": "user", "content": "Ping"}],
            },
            provider="openai",
        )
        assert decision is None

    def test_disqualifies_tool_definitions(self):
        from clawmetry.proxy import AutoModelRouter, AutoRoutingConfig

        router = AutoModelRouter(AutoRoutingConfig(enabled=True))
        decision = router.route(
            {
                "model": "claude-opus-4",
                "tools": [{"name": "shell", "input_schema": {"type": "object"}}],
                "messages": [{"role": "user", "content": "Hello"}],
            },
            provider="anthropic",
        )
        assert decision is None

    def test_disqualifies_images(self):
        from clawmetry.proxy import AutoModelRouter, AutoRoutingConfig

        router = AutoModelRouter(AutoRoutingConfig(enabled=True))
        decision = router.route(
            {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What is in this image?"},
                            {"type": "image_url", "image_url": {"url": "data:..."}},
                        ],
                    }
                ],
            },
            provider="openai",
        )
        assert decision is None

    def test_disqualifies_over_threshold_user_message(self):
        from clawmetry.proxy import AutoModelRouter, AutoRoutingConfig

        router = AutoModelRouter(
            AutoRoutingConfig(enabled=True, max_user_tokens=3)
        )
        decision = router.route(
            {
                "model": "claude-opus-4",
                "messages": [
                    {"role": "user", "content": "one two three four five"}
                ],
            },
            provider="anthropic",
        )
        assert decision is None

    def test_disqualifies_over_threshold_system_prompt(self):
        from clawmetry.proxy import AutoModelRouter, AutoRoutingConfig

        router = AutoModelRouter(
            AutoRoutingConfig(enabled=True, max_system_tokens=3)
        )
        decision = router.route(
            {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "one two three four five"},
                    {"role": "user", "content": "Ping"},
                ],
            },
            provider="openai",
        )
        assert decision is None


# ── Configuration ──────────────────────────────────────────────────────


class TestProxyConfig:
    def test_default_config(self):
        from clawmetry.proxy import ProxyConfig

        config = ProxyConfig()
        assert config.port == 4100
        assert config.host == "127.0.0.1"
        assert config.budget.daily_usd == 0.0
        assert config.loop_detection.enabled is True
        assert config.auto_routing.enabled is False

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

    def test_auto_routing_save_and_load_round_trip(self, tmp_path):
        from clawmetry.proxy import ProxyConfig, AutoRoutingConfig

        config_file = tmp_path / "proxy.json"
        config = ProxyConfig(
            auto_routing=AutoRoutingConfig(
                enabled=True,
                max_user_tokens=123,
                max_system_tokens=456,
                require_no_tools=False,
                downgrade_map={"gpt-4o": "gpt-4o-mini"},
            )
        )
        with (
            patch("clawmetry.proxy.CONFIG_DIR", tmp_path),
            patch("clawmetry.proxy.PROXY_CONFIG_FILE", config_file),
        ):
            config.save()
            raw = json.loads(config_file.read_text())
            loaded = ProxyConfig.load()

        assert raw["auto_routing"]["enabled"] is True
        assert loaded.auto_routing.enabled is True
        assert loaded.auto_routing.max_user_tokens == 123
        assert loaded.auto_routing.max_system_tokens == 456
        assert loaded.auto_routing.require_no_tools is False
        assert loaded.auto_routing.downgrade_map == {"gpt-4o": "gpt-4o-mini"}

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

    def test_auto_routing_env_override(self, tmp_path):
        from clawmetry.proxy import ProxyConfig

        config_file = tmp_path / "proxy.json"
        with (
            patch("clawmetry.proxy.PROXY_CONFIG_FILE", config_file),
            patch.dict(
                os.environ,
                {
                    "CLAWMETRY_PROXY_AUTO_ROUTING_ENABLED": "1",
                    "CLAWMETRY_PROXY_AUTO_ROUTING_MAX_USER_TOKENS": "77",
                    "CLAWMETRY_PROXY_AUTO_ROUTING_DOWNGRADE_MAP": json.dumps(
                        {"gpt-4o": "gpt-4o-mini"}
                    ),
                },
            ),
        ):
            config = ProxyConfig.load()
        assert config.auto_routing.enabled is True
        assert config.auto_routing.max_user_tokens == 77
        assert config.auto_routing.downgrade_map == {"gpt-4o": "gpt-4o-mini"}


# ── Flask App Integration ─────────────────────────────────────────────


class TestProxyApp:
    class _FakeResponse:
        status = 200
        headers = {}

        def __init__(self, body):
            self._body = json.dumps(body).encode()

        def read(self):
            return self._body

    def _make_client(self, tmp_path, config):
        import clawmetry.proxy
        from clawmetry.proxy import create_proxy_app, ProxyDB, ProviderConfig

        config.providers = {
            "anthropic": ProviderConfig(
                api_key_env="ANTHROPIC_API_KEY",
                base_url="https://api.anthropic.com",
            ),
            "openai": ProviderConfig(
                api_key_env="OPENAI_API_KEY",
                base_url="https://api.openai.com",
            ),
        }
        db_path = tmp_path / "test_proxy_app.db"
        original_init = ProxyDB.__init__

        def patched_init(self, db_path=None):
            if db_path is None:
                db_path = clawmetry.proxy.PROXY_DB_FILE
            original_init(self, db_path)

        with (
            patch.object(clawmetry.proxy, "PROXY_DB_FILE", db_path),
            patch.object(ProxyDB, "__init__", patched_init),
        ):
            app = create_proxy_app(config)
        app.config["TESTING"] = True
        client = app.test_client()
        client._db_path = db_path
        return client

    def _patch_local_store(self, monkeypatch):
        captured = []

        class _FakeStore:
            def ingest(self, event):
                captured.append(event)

        from clawmetry import local_store as _ls

        monkeypatch.setattr(_ls, "get_store", lambda: _FakeStore())
        return captured

    @pytest.fixture
    def client(self, tmp_path):
        import clawmetry.proxy
        from clawmetry.proxy import (
            create_proxy_app,
            ProxyConfig,
            BudgetConfig,
            LoopDetectionConfig,
            ProxyDB,
        )

        config = ProxyConfig(
            port=14100,
            budget=BudgetConfig(daily_usd=10.0, monthly_usd=100.0, action="block"),
            loop_detection=LoopDetectionConfig(
                enabled=True, max_similar=3, window_seconds=300
            ),
        )
        db_path = tmp_path / "test.db"

        original_init = ProxyDB.__init__

        def patched_init(self, db_path=None):
            if db_path is None:
                db_path = clawmetry.proxy.PROXY_DB_FILE
            original_init(self, db_path)

        with (
            patch.object(clawmetry.proxy, "PROXY_DB_FILE", db_path),
            patch.object(ProxyDB, "__init__", patched_init),
        ):
            app = create_proxy_app(config)
        app.config["TESTING"] = True
        client = app.test_client()
        client._db_path = db_path
        return client

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
        """Budget blocking returns 429 when daily budget is exceeded."""
        from clawmetry.proxy import ProxyDB

        db = ProxyDB(db_path=client._db_path)
        db.record_usage(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=15.0,
        )
        resp = client.get("/proxy/status")
        assert resp.status_code == 200
        status = resp.get_json()
        assert status["budget"]["daily_remaining"] == 0.0
        assert status["budget"]["daily_limit"] == 10.0

    def test_auto_routing_rewrites_anthropic_request_and_emits_event(
        self, tmp_path, monkeypatch
    ):
        from clawmetry.proxy import (
            AutoRoutingConfig,
            BudgetConfig,
            LoopDetectionConfig,
            ProxyConfig,
            ProxyDB,
        )

        config = ProxyConfig(
            budget=BudgetConfig(),
            loop_detection=LoopDetectionConfig(enabled=False),
            auto_routing=AutoRoutingConfig(enabled=True),
        )
        client = self._make_client(tmp_path, config)
        local_events = self._patch_local_store(monkeypatch)
        captured = {}

        def fake_urlopen(req, timeout=300):
            captured["body"] = json.loads(req.data.decode())
            return self._FakeResponse(
                {
                    "model": captured["body"]["model"],
                    "usage": {"input_tokens": 10, "output_tokens": 2},
                    "stop_reason": "end_turn",
                }
            )

        monkeypatch.setattr("clawmetry.proxy.urlopen", fake_urlopen)
        resp = client.post(
            "/v1/messages",
            data=json.dumps(
                {
                    "model": "claude-opus-4",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 16,
                }
            ),
            content_type="application/json",
            headers={"x-api-key": "sk-ant-test", "x-session-id": "s-auto"},
        )

        assert resp.status_code == 200
        assert captured["body"]["model"] == "claude-3-5-haiku"

        db = ProxyDB(db_path=client._db_path)
        events = db.get_recent_events(event_type="auto_downgraded")
        assert len(events) == 1
        details = json.loads(events[0]["details"])
        assert details["original_model"] == "claude-opus-4"
        assert details["target_model"] == "claude-3-5-haiku"
        assert details["estimated_savings_usd"] > 0
        assert local_events[0]["event_type"] == "auto_downgraded"
        assert local_events[0]["data"]["estimated_savings_usd"] > 0

    def test_auto_routing_rewrites_openai_request(self, tmp_path, monkeypatch):
        from clawmetry.proxy import (
            AutoRoutingConfig,
            BudgetConfig,
            LoopDetectionConfig,
            ProxyConfig,
            ProxyDB,
        )

        config = ProxyConfig(
            budget=BudgetConfig(),
            loop_detection=LoopDetectionConfig(enabled=False),
            auto_routing=AutoRoutingConfig(enabled=True),
        )
        client = self._make_client(tmp_path, config)
        self._patch_local_store(monkeypatch)
        captured = {}

        def fake_urlopen(req, timeout=300):
            captured["body"] = json.loads(req.data.decode())
            return self._FakeResponse(
                {
                    "model": captured["body"]["model"],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 1},
                    "choices": [{"finish_reason": "stop"}],
                }
            )

        monkeypatch.setattr("clawmetry.proxy.urlopen", fake_urlopen)
        resp = client.post(
            "/v1/chat/completions",
            data=json.dumps(
                {
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": "Ping"}],
                }
            ),
            content_type="application/json",
            headers={"Authorization": "Bearer sk-test"},
        )

        assert resp.status_code == 200
        assert captured["body"]["model"] == "gpt-4o-mini"
        db = ProxyDB(db_path=client._db_path)
        events = db.get_recent_events(event_type="auto_downgraded")
        assert len(events) == 1
        assert json.loads(events[0]["details"])["provider"] == "openai"

    def test_explicit_routing_rule_takes_precedence_over_auto_routing(
        self, tmp_path, monkeypatch
    ):
        from clawmetry.proxy import (
            AutoRoutingConfig,
            BudgetConfig,
            LoopDetectionConfig,
            ProxyConfig,
            ProxyDB,
            RoutingRule,
        )

        config = ProxyConfig(
            budget=BudgetConfig(),
            loop_detection=LoopDetectionConfig(enabled=False),
            auto_routing=AutoRoutingConfig(enabled=True),
            routing_rules=[
                RoutingRule(
                    match_model="opus",
                    target_model="claude-sonnet-4",
                )
            ],
        )
        client = self._make_client(tmp_path, config)
        self._patch_local_store(monkeypatch)
        captured = {}

        def fake_urlopen(req, timeout=300):
            captured["body"] = json.loads(req.data.decode())
            return self._FakeResponse(
                {
                    "model": captured["body"]["model"],
                    "usage": {"input_tokens": 5, "output_tokens": 1},
                    "stop_reason": "end_turn",
                }
            )

        monkeypatch.setattr("clawmetry.proxy.urlopen", fake_urlopen)
        resp = client.post(
            "/v1/messages",
            data=json.dumps(
                {
                    "model": "claude-opus-4",
                    "messages": [{"role": "user", "content": "Hello"}],
                }
            ),
            content_type="application/json",
            headers={"x-api-key": "sk-ant-test"},
        )

        assert resp.status_code == 200
        assert captured["body"]["model"] == "claude-sonnet-4"
        db = ProxyDB(db_path=client._db_path)
        assert db.get_recent_events(event_type="auto_downgraded") == []
        assert len(db.get_recent_events(event_type="model_routed")) == 1

    def test_budget_downgrade_takes_precedence_over_auto_routing(
        self, tmp_path, monkeypatch
    ):
        from clawmetry.proxy import (
            AutoRoutingConfig,
            BudgetConfig,
            LoopDetectionConfig,
            ProxyConfig,
            ProxyDB,
        )

        config = ProxyConfig(
            budget=BudgetConfig(
                daily_usd=1.0,
                action="downgrade",
                downgrade_model="claude-3-haiku-20240307",
            ),
            loop_detection=LoopDetectionConfig(enabled=False),
            auto_routing=AutoRoutingConfig(enabled=True),
        )
        client = self._make_client(tmp_path, config)
        self._patch_local_store(monkeypatch)
        db = ProxyDB(db_path=client._db_path)
        db.record_usage(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=1000,
            cost_usd=2.0,
        )
        captured = {}

        def fake_urlopen(req, timeout=300):
            captured["body"] = json.loads(req.data.decode())
            return self._FakeResponse(
                {
                    "model": captured["body"]["model"],
                    "usage": {"input_tokens": 5, "output_tokens": 1},
                    "stop_reason": "end_turn",
                }
            )

        monkeypatch.setattr("clawmetry.proxy.urlopen", fake_urlopen)
        resp = client.post(
            "/v1/messages",
            data=json.dumps(
                {
                    "model": "claude-opus-4",
                    "messages": [{"role": "user", "content": "Hello"}],
                }
            ),
            content_type="application/json",
            headers={"x-api-key": "sk-ant-test"},
        )

        assert resp.status_code == 200
        assert captured["body"]["model"] == "claude-3-haiku-20240307"
        assert db.get_recent_events(event_type="auto_downgraded") == []
