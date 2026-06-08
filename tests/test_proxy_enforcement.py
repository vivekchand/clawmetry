"""
Unit tests for the three new enforcement features in clawmetry/proxy.py:

  #2816  Auto smart model routing (heuristic cheap-task downgrade)
  #2817  Rapid-fire request-rate breaker (content-agnostic)
  #2818  Dollar-based cost-spiral breaker + auto exponential-backoff pause

No running server needed — these construct the configs + breakers + a temp
ProxyDB directly and assert behaviour at the threshold.
"""

import json
import time
from pathlib import Path

import pytest

from clawmetry.proxy import (
    ProxyConfig,
    ProxyDB,
    RateBreakerConfig,
    RateBreaker,
    CostSpiralConfig,
    CostSpiralBreaker,
    AutoRoutingConfig,
    AutoRouter,
    _estimate_tokens,
    _record_backoff_pause,
    _is_session_hitl_paused,
    _BACKOFF_LADDER_MINUTES,
)
from clawmetry.providers_pricing import (
    default_auto_downgrade_map,
    downgrade_model_name,
)


# ── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def db(tmp_path):
    return ProxyDB(db_path=tmp_path / "proxy_enf.db")


@pytest.fixture
def hitl_dir(tmp_path, monkeypatch):
    """Point _HITL_DIR at a temp dir so pause files don't touch real state."""
    import clawmetry.proxy as proxymod

    d = tmp_path / "hitl"
    d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(proxymod, "_HITL_DIR", d)
    return d


# ── Config round-trip (load/save wiring) ───────────────────────────────


def test_config_round_trip(tmp_path, monkeypatch):
    import clawmetry.proxy as proxymod

    cfg_file = tmp_path / "proxy.json"
    monkeypatch.setattr(proxymod, "PROXY_CONFIG_FILE", cfg_file)
    monkeypatch.setattr(proxymod, "CONFIG_DIR", tmp_path)

    cfg = ProxyConfig()
    cfg.rate_breaker = RateBreakerConfig(enabled=True, window_seconds=30, max_requests=7)
    cfg.cost_spiral = CostSpiralConfig(enabled=True, window_seconds=120, max_usd=3.5)
    cfg.auto_routing = AutoRoutingConfig(
        enabled=True, max_user_tokens=150, max_system_tokens=400,
        downgrade_map={"opus": "haiku"},
    )
    cfg.save()

    raw = json.loads(cfg_file.read_text())
    assert raw["rate_breaker"]["max_requests"] == 7
    assert raw["cost_spiral"]["max_usd"] == 3.5
    assert raw["auto_routing"]["enabled"] is True
    assert raw["auto_routing"]["downgrade_map"] == {"opus": "haiku"}

    loaded = ProxyConfig.load()
    assert loaded.rate_breaker.enabled is True
    assert loaded.rate_breaker.window_seconds == 30
    assert loaded.cost_spiral.max_usd == 3.5
    assert loaded.auto_routing.max_user_tokens == 150
    assert loaded.auto_routing.downgrade_map == {"opus": "haiku"}


def test_features_default_off():
    cfg = ProxyConfig()
    assert cfg.rate_breaker.enabled is False
    assert cfg.cost_spiral.enabled is False
    assert cfg.auto_routing.enabled is False


def test_auto_route_env_toggle_seeds_default_map(tmp_path, monkeypatch):
    import clawmetry.proxy as proxymod

    monkeypatch.setattr(proxymod, "PROXY_CONFIG_FILE", tmp_path / "nope.json")
    monkeypatch.setenv("CLAWMETRY_PROXY_AUTO_ROUTE", "1")
    loaded = ProxyConfig.load()
    assert loaded.auto_routing.enabled is True
    # No explicit map -> seeded from pricing defaults.
    assert loaded.auto_routing.downgrade_map.get("opus") == "haiku"


# ── #2817  Rate breaker ────────────────────────────────────────────────


def _seed_requests(db, session_id, n):
    for _ in range(n):
        db.record_usage(
            provider="anthropic", model="claude-opus-4",
            input_tokens=1, output_tokens=1, cost_usd=0.0,
            session_id=session_id, request_hash="h",
        )


def test_get_recent_request_count(db):
    _seed_requests(db, "s1", 5)
    assert db.get_recent_request_count("s1", 60) == 5
    assert db.get_recent_request_count("other", 60) == 0


def test_rate_breaker_disabled_by_default(db):
    rb = RateBreaker(RateBreakerConfig(), db)  # enabled=False
    _seed_requests(db, "s1", 50)
    breached, _ = rb.check("s1")
    assert breached is False


def test_rate_breaker_fires_at_threshold(db):
    rb = RateBreaker(
        RateBreakerConfig(enabled=True, window_seconds=60, max_requests=20), db
    )
    _seed_requests(db, "s1", 19)
    assert rb.check("s1")[0] is False  # 19 recorded -> 20th allowed
    _seed_requests(db, "s1", 1)  # now 20 recorded
    breached, reason = rb.check("s1")  # the 21st is blocked
    assert breached is True
    assert "rate exceeded" in reason.lower()


def test_rate_breaker_no_session(db):
    rb = RateBreaker(RateBreakerConfig(enabled=True, max_requests=1), db)
    assert rb.check("")[0] is False


# ── #2818  Cost-spiral breaker ─────────────────────────────────────────


def _seed_cost(db, session_id, usd, n=1):
    per = usd / n
    for _ in range(n):
        db.record_usage(
            provider="anthropic", model="claude-opus-4",
            input_tokens=1000, output_tokens=1000, cost_usd=per,
            session_id=session_id,
        )


def test_get_session_window_spending(db):
    _seed_cost(db, "s1", 1.50, n=3)
    total = db.get_session_window_spending("s1", time.time() - 300)
    assert abs(total - 1.50) < 1e-6
    assert db.get_session_window_spending("other", time.time() - 300) == 0.0


def test_cost_spiral_disabled_by_default(db):
    csb = CostSpiralBreaker(CostSpiralConfig(), db)
    _seed_cost(db, "s1", 100.0)
    assert csb.check("s1")[0] is False


def test_cost_spiral_fires_over_cap(db):
    csb = CostSpiralBreaker(
        CostSpiralConfig(enabled=True, window_seconds=300, max_usd=2.0), db
    )
    _seed_cost(db, "s1", 1.5)
    assert csb.check("s1")[0] is False  # under cap
    _seed_cost(db, "s1", 0.75)  # total 2.25 > 2.0
    breached, reason = csb.check("s1")
    assert breached is True
    assert "cost spiral" in reason.lower()


def test_cost_spiral_is_per_session(db):
    csb = CostSpiralBreaker(
        CostSpiralConfig(enabled=True, window_seconds=300, max_usd=2.0), db
    )
    _seed_cost(db, "a", 5.0)  # another session burns money
    assert csb.check("s1")[0] is False  # s1 itself spent nothing


# ── #2816  Auto router ─────────────────────────────────────────────────


def test_estimate_tokens():
    assert _estimate_tokens("") == 0
    assert _estimate_tokens("a" * 400) == 100


def test_downgrade_map_helpers():
    dm = default_auto_downgrade_map()
    assert downgrade_model_name("claude-opus-4-20250514", dm) == "claude-3-5-haiku-latest"
    assert downgrade_model_name("gpt-4o", dm) == "gpt-4o-mini"
    # Already-cheap target -> no downgrade.
    assert downgrade_model_name("gpt-4o-mini", dm) == ""
    assert downgrade_model_name("claude-3-5-haiku-latest", dm) == ""
    # Unknown -> no downgrade.
    assert downgrade_model_name("llama-3.1-70b", dm) == ""


def _ar(**kw):
    cfg = AutoRoutingConfig(enabled=True, downgrade_map=default_auto_downgrade_map())
    for k, v in kw.items():
        setattr(cfg, k, v)
    return AutoRouter(cfg)


def test_auto_router_disabled_does_nothing():
    ar = AutoRouter(AutoRoutingConfig(enabled=False))
    body = {"model": "claude-opus-4", "messages": [{"role": "user", "content": "hi"}]}
    assert ar.route("claude-opus-4", body) == (None, "")


def test_auto_router_downgrades_short_no_tool_opus():
    ar = _ar()
    body = {
        "model": "claude-opus-4-20250514",
        "messages": [{"role": "user", "content": "What is 2+2?"}],
    }
    new_model, reason = ar.route("claude-opus-4-20250514", body)
    assert new_model == "claude-3-5-haiku-latest"
    assert "auto-downgraded" in reason.lower()


def test_auto_router_skips_long_message():
    ar = _ar(max_user_tokens=50)
    long_text = "word " * 1000  # ~1250 tokens
    body = {
        "model": "claude-opus-4",
        "messages": [{"role": "user", "content": long_text}],
    }
    assert ar.route("claude-opus-4", body) == (None, "")


def test_auto_router_skips_when_tools_present():
    ar = _ar(require_no_tools=True)
    body = {
        "model": "claude-opus-4",
        "messages": [{"role": "user", "content": "hi"}],
        "tools": [{"name": "search", "input_schema": {}}],
    }
    assert ar.route("claude-opus-4", body) == (None, "")


def test_auto_router_skips_when_images_present():
    ar = _ar()
    body = {
        "model": "claude-opus-4",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "what is this"},
                {"type": "image", "source": {}},
            ],
        }],
    }
    assert ar.route("claude-opus-4", body) == (None, "")


def test_auto_router_skips_long_system_prompt():
    ar = _ar(max_system_tokens=50)
    body = {
        "model": "claude-opus-4",
        "system": "x" * 4000,  # ~1000 tokens
        "messages": [{"role": "user", "content": "hi"}],
    }
    assert ar.route("claude-opus-4", body) == (None, "")


def test_auto_router_heartbeat_pattern():
    ar = _ar(require_no_tools=True, include_heartbeat=True)
    body = {
        "model": "claude-opus-4",
        "messages": [{"role": "user", "content": "heartbeat ping"}],
    }
    new_model, _ = ar.route("claude-opus-4", body)
    assert new_model == "claude-3-5-haiku-latest"


def test_auto_router_openai_system_message():
    ar = _ar()
    body = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "hello"},
        ],
    }
    new_model, _ = ar.route("gpt-4o", body)
    assert new_model == "gpt-4o-mini"


# ── #2818  Auto-backoff pause (escalation + expiry) ────────────────────


def test_backoff_pause_escalation_ladder(hitl_dir):
    sid = "sess-esc"
    expected = list(_BACKOFF_LADDER_MINUTES) + [_BACKOFF_LADDER_MINUTES[-1]]
    for i, mins in enumerate(expected, start=1):
        until_ts, level = _record_backoff_pause(sid)
        assert level == i
        # Allow small slack for clock between write and assert.
        assert abs((until_ts - time.time()) - mins * 60) < 5


def test_backoff_pause_blocks_then_auto_resumes(hitl_dir):
    sid = "sess-exp"
    until_ts, level = _record_backoff_pause(sid)
    assert level == 1
    assert _is_session_hitl_paused(sid) is True  # within cool-off

    # Rewrite the pause file with an already-elapsed expiry to simulate cool-off.
    pf = hitl_dir / f"pause_{sid}.json"
    pf.write_text(json.dumps({"until_ts": time.time() - 1, "level": 1}))
    assert _is_session_hitl_paused(sid) is False  # auto-resumed


def test_legacy_operator_pause_still_works(hitl_dir):
    sid = "sess-legacy"
    (hitl_dir / f"pause_{sid}").write_text("")  # empty operator pause
    assert _is_session_hitl_paused(sid) is True
    # Manual resume = delete file.
    (hitl_dir / f"pause_{sid}").unlink()
    assert _is_session_hitl_paused(sid) is False


def test_malformed_pause_file_fails_safe(hitl_dir):
    sid = "sess-bad"
    (hitl_dir / f"pause_{sid}.json").write_text("{not json")
    # Corrupt file -> treated as paused (fail safe).
    assert _is_session_hitl_paused(sid) is True


def test_no_pause_returns_false(hitl_dir):
    assert _is_session_hitl_paused("never-paused") is False
    assert _is_session_hitl_paused("") is False


# ── Regression: review fixes (blocker + 2 majors) ──────────────────────

def test_auto_router_heartbeat_with_tools_blocked():
    """BLOCKER fix: a heartbeat-word turn that ALSO carries tools must NOT
    downgrade -- agent tool-use continuations ('continue'/'ok?') carry the full
    tool set and a weaker model handles them worse."""
    ar = _ar(require_no_tools=True, include_heartbeat=True)
    body = {
        "model": "claude-opus-4",
        "messages": [{"role": "user", "content": "continue"}],
        "tools": [{"name": "search", "input_schema": {}}],
    }
    assert ar.route("claude-opus-4", body) == (None, "")


def test_auto_router_heartbeat_with_image_blocked():
    """BLOCKER fix: heartbeat-word + image must NOT downgrade."""
    ar = _ar(include_heartbeat=True)
    body = {
        "model": "claude-opus-4",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "continue"},
                {"type": "image", "source": {}},
            ],
        }],
    }
    assert ar.route("claude-opus-4", body) == (None, "")


def test_downgrade_no_cross_provider_substring():
    """MAJOR fix: a loose substring key ('o1') must never substitute across
    providers -- a Gemini model string containing 'o1' must not become o1-mini."""
    dm = default_auto_downgrade_map()
    assert downgrade_model_name("gemini-pro-2025o1xx", dm) == ""
    # And a real OpenAI o1 still downgrades within OpenAI.
    assert downgrade_model_name("o1-preview", dm) == "o1-mini"


def test_downgrade_bare_family_splice_rejected():
    """MAJOR fix: a bare-family map ({'opus':'haiku'}) must not synthesize a
    non-existent id (claude-haiku-4-X) -- the unknown spliced id is rejected."""
    assert downgrade_model_name("claude-opus-4-20250514", {"opus": "haiku"}) == ""
    # The full-id default map still works for the same input.
    assert downgrade_model_name(
        "claude-opus-4-20250514", default_auto_downgrade_map()
    ) == "claude-3-5-haiku-latest"


def test_backoff_escalation_decays_after_quiet(hitl_dir):
    """MAJOR fix: after a long quiet gap the escalation level resets to the
    bottom rung instead of jumping to the cap on an isolated later breach."""
    import clawmetry.proxy as proxymod
    sid = "decay-sess"
    # Simulate a prior pause at level 3 whose cool-off lapsed long ago.
    old = proxymod.time.time() - (proxymod._BACKOFF_RESET_SECS + 600)
    (hitl_dir / f"pause_{sid}.json").write_text(
        json.dumps({"until_ts": old, "level": 3})
    )
    until_ts, level = _record_backoff_pause(sid)
    assert level == 1  # decayed back to the bottom rung
    assert until_ts > proxymod.time.time()


def test_prune_backoff_pauses(hitl_dir):
    """MAJOR fix: long-expired pause files are pruned so they can't accumulate."""
    import clawmetry.proxy as proxymod
    now = proxymod.time.time()
    # Long-expired -> pruned.
    (hitl_dir / "pause_old.json").write_text(
        json.dumps({"until_ts": now - proxymod._BACKOFF_PRUNE_SECS - 60, "level": 2})
    )
    # Recently expired (within retention) -> kept for escalation accounting.
    (hitl_dir / "pause_recent.json").write_text(
        json.dumps({"until_ts": now - 60, "level": 1})
    )
    # Still-active pause -> kept.
    (hitl_dir / "pause_active.json").write_text(
        json.dumps({"until_ts": now + 600, "level": 1})
    )
    removed = proxymod._prune_backoff_pauses()
    assert removed == 1
    assert not (hitl_dir / "pause_old.json").exists()
    assert (hitl_dir / "pause_recent.json").exists()
    assert (hitl_dir / "pause_active.json").exists()
