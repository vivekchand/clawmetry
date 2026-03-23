"""
Tests for per-skill cost attribution (clawmetry/skills.py).

Covers:
  - SKILL.md path detection and skill name extraction
  - Token/cost attribution window logic
  - Leaderboard aggregation
  - ClawHub metadata schema
  - API endpoints (leaderboard + executions)
"""
import json
import os
import tempfile
import pytest

from clawmetry.skills import (
    _extract_skill_name_from_path,
    _is_skill_read,
    _extract_usage_for_event,
    _build_clawhub_metadata,
    build_skill_leaderboard,
    CLAWHUB_SCHEMA_VERSION,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_tool_call_event(tool_name, args, tokens=100, cost=0.0015, timestamp="2026-01-01T00:00:00Z"):
    """Build a minimal transcript event with a tool call."""
    return {
        "type": "message",
        "timestamp": timestamp,
        "message": {
            "role": "assistant",
            "model": "claude-sonnet-4-6",
            "content": [
                {
                    "type": "toolCall",
                    "name": tool_name,
                    "arguments": args,
                }
            ],
            "usage": {
                "input": 80,
                "output": 20,
                "totalTokens": tokens,
                "cost": {"total": cost},
            },
        },
    }


def _make_assistant_event(tokens=200, cost=0.003, timestamp="2026-01-01T00:01:00Z", model="claude-sonnet-4-6"):
    """Build a plain assistant message event with usage."""
    return {
        "type": "message",
        "timestamp": timestamp,
        "message": {
            "role": "assistant",
            "model": model,
            "content": [{"type": "text", "text": "I will help you with this task."}],
            "usage": {
                "input": 150,
                "output": 50,
                "totalTokens": tokens,
                "cost": {"total": cost},
            },
        },
    }


def _write_jsonl(path, events):
    """Write a list of dicts as JSONL."""
    with open(path, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


# ── Unit: path extraction ────────────────────────────────────────────────────

class TestSkillNameExtraction:
    def test_unix_path(self):
        assert _extract_skill_name_from_path("/home/user/.openclaw/skills/coding-agent/SKILL.md") == "coding-agent"

    def test_windows_path(self):
        assert _extract_skill_name_from_path(r"C:\Users\user\skills\weather\SKILL.md") == "weather"

    def test_relative_path(self):
        assert _extract_skill_name_from_path("skills/gh-issues/SKILL.md") == "gh-issues"

    def test_no_match_returns_none(self):
        assert _extract_skill_name_from_path("/some/random/file.txt") is None

    def test_case_insensitive(self):
        result = _extract_skill_name_from_path("/skills/MySkill/skill.MD")
        assert result == "myskill"


# ── Unit: skill read detection ───────────────────────────────────────────────

class TestIsSkillRead:
    def test_detects_skill_read(self):
        ev = _make_tool_call_event(
            "read",
            {"file_path": "/home/user/skills/coding-agent/SKILL.md"},
        )
        result = _is_skill_read(ev)
        assert result == "coding-agent"

    def test_detects_path_arg(self):
        ev = _make_tool_call_event(
            "read",
            {"path": "/skills/weather/SKILL.md"},
        )
        result = _is_skill_read(ev)
        assert result == "weather"

    def test_ignores_non_skill_reads(self):
        ev = _make_tool_call_event(
            "read",
            {"file_path": "/some/other/file.py"},
        )
        assert _is_skill_read(ev) is None

    def test_ignores_other_tools(self):
        ev = _make_tool_call_event(
            "exec",
            {"command": "ls /skills/coding-agent/SKILL.md"},
        )
        assert _is_skill_read(ev) is None

    def test_not_a_message_event(self):
        ev = {"type": "system", "data": {}}
        assert _is_skill_read(ev) is None


# ── Unit: usage extraction ───────────────────────────────────────────────────

class TestExtractUsage:
    def test_extracts_from_message_usage(self):
        ev = _make_assistant_event(tokens=300, cost=0.005)
        tokens, cost = _extract_usage_for_event(ev)
        assert tokens == 300
        assert abs(cost - 0.005) < 1e-9

    def test_zero_when_no_usage(self):
        ev = {"type": "message", "message": {"role": "assistant", "content": []}}
        tokens, cost = _extract_usage_for_event(ev)
        assert tokens == 0
        assert cost == 0.0

    def test_estimates_cost_when_zero(self):
        ev = {
            "type": "message",
            "message": {
                "role": "assistant",
                "usage": {"totalTokens": 1000, "cost": {"total": 0.0}},
            },
        }
        tokens, cost = _extract_usage_for_event(ev)
        assert tokens == 1000
        assert cost > 0.0  # estimated


# ── Unit: ClawHub metadata ───────────────────────────────────────────────────

class TestClawHubMetadata:
    def test_schema_fields_present(self):
        meta = _build_clawhub_metadata(
            skill_name="gh-issues",
            session_id="abc-123",
            execution_id="abc-gh-issues-000",
            started_at="2026-01-01T00:00:00Z",
            ended_at="2026-01-01T01:00:00Z",
            tokens=5000,
            cost_usd=0.037,
            turns=10,
            success=True,
            node_id="my-node",
            model="claude-sonnet-4-6",
        )
        assert meta["schema_version"] == CLAWHUB_SCHEMA_VERSION
        assert meta["skill_name"] == "gh-issues"
        assert meta["session_id"] == "abc-123"
        assert meta["execution_id"] == "abc-gh-issues-000"
        assert meta["tokens"] == 5000
        assert abs(meta["cost_usd"] - 0.037) < 1e-9
        assert meta["turns"] == 10
        assert meta["success"] is True
        assert meta["source"] == "clawmetry"
        assert meta["node_id"] == "my-node"
        assert meta["model"] == "claude-sonnet-4-6"


# ── Integration: leaderboard ─────────────────────────────────────────────────

class TestBuildLeaderboard:
    def test_empty_dir_returns_empty(self, tmp_path):
        result = build_skill_leaderboard(str(tmp_path))
        assert result["leaderboard"] == []
        assert result["summary"]["total_executions"] == 0

    def test_nonexistent_dir_returns_empty(self):
        result = build_skill_leaderboard("/nonexistent/path/sessions")
        assert result["leaderboard"] == []

    def test_detects_single_skill(self, tmp_path):
        events = [
            # Skill load
            _make_tool_call_event(
                "read",
                {"file_path": "/skills/weather/SKILL.md"},
                tokens=50, cost=0.0,
                timestamp="2026-01-01T00:00:00Z",
            ),
            # Attribution turns
            _make_assistant_event(tokens=200, cost=0.003, timestamp="2026-01-01T00:01:00Z"),
            _make_assistant_event(tokens=150, cost=0.002, timestamp="2026-01-01T00:02:00Z"),
        ]
        _write_jsonl(tmp_path / "session1.jsonl", events)

        result = build_skill_leaderboard(str(tmp_path))
        lb = result["leaderboard"]
        assert len(lb) == 1
        assert lb[0]["skill_name"] == "weather"
        assert lb[0]["executions"] == 1
        assert lb[0]["total_tokens"] == 350
        assert abs(lb[0]["total_cost"] - 0.005) < 1e-9
        assert lb[0]["avg_turns"] == 2.0
        assert lb[0]["success_rate"] == 100.0

    def test_multiple_skills_in_one_session(self, tmp_path):
        events = [
            _make_tool_call_event("read", {"file_path": "/skills/weather/SKILL.md"},
                                  tokens=0, cost=0.0, timestamp="2026-01-01T00:00:00Z"),
            _make_assistant_event(tokens=300, cost=0.004, timestamp="2026-01-01T00:01:00Z"),
            # Second skill loaded
            _make_tool_call_event("read", {"file_path": "/skills/gh-issues/SKILL.md"},
                                  tokens=0, cost=0.0, timestamp="2026-01-01T00:02:00Z"),
            _make_assistant_event(tokens=500, cost=0.007, timestamp="2026-01-01T00:03:00Z"),
            _make_assistant_event(tokens=400, cost=0.006, timestamp="2026-01-01T00:04:00Z"),
        ]
        _write_jsonl(tmp_path / "session2.jsonl", events)

        result = build_skill_leaderboard(str(tmp_path))
        names = {r["skill_name"] for r in result["leaderboard"]}
        assert "weather" in names
        assert "gh-issues" in names

        gh = next(r for r in result["leaderboard"] if r["skill_name"] == "gh-issues")
        assert gh["total_tokens"] == 900
        assert gh["avg_turns"] == 2.0

    def test_leaderboard_sorted_by_cost(self, tmp_path):
        # Two sessions, two skills with different costs
        events_a = [
            _make_tool_call_event("read", {"file_path": "/skills/cheap-skill/SKILL.md"},
                                  tokens=0, cost=0.0),
            _make_assistant_event(tokens=100, cost=0.001),
        ]
        events_b = [
            _make_tool_call_event("read", {"file_path": "/skills/expensive-skill/SKILL.md"},
                                  tokens=0, cost=0.0),
            _make_assistant_event(tokens=10000, cost=1.5),
        ]
        _write_jsonl(tmp_path / "sessA.jsonl", events_a)
        _write_jsonl(tmp_path / "sessB.jsonl", events_b)

        result = build_skill_leaderboard(str(tmp_path))
        lb = result["leaderboard"]
        assert lb[0]["skill_name"] == "expensive-skill"
        assert lb[1]["skill_name"] == "cheap-skill"

    def test_clawhub_metadata_in_leaderboard(self, tmp_path):
        events = [
            _make_tool_call_event("read", {"file_path": "/skills/oracle/SKILL.md"},
                                  tokens=0, cost=0.0),
            _make_assistant_event(tokens=500, cost=0.007),
        ]
        _write_jsonl(tmp_path / "sess.jsonl", events)
        result = build_skill_leaderboard(str(tmp_path))
        lb = result["leaderboard"]
        assert len(lb) == 1
        cm = lb[0]["clawmetry_skill"]
        assert cm["schema_version"] == CLAWHUB_SCHEMA_VERSION
        assert cm["skill_name"] == "oracle"
        assert cm["aggregate"] is True
        assert cm["source"] == "clawmetry"

    def test_executions_have_clawhub_metadata(self, tmp_path):
        events = [
            _make_tool_call_event("read", {"file_path": "/skills/oracle/SKILL.md"},
                                  tokens=0, cost=0.0),
            _make_assistant_event(tokens=500, cost=0.007),
        ]
        _write_jsonl(tmp_path / "sess.jsonl", events)
        result = build_skill_leaderboard(str(tmp_path))
        execs = result["executions"]
        assert len(execs) == 1
        cm = execs[0]["clawmetry_skill"]
        assert cm["schema_version"] == CLAWHUB_SCHEMA_VERSION
        assert "execution_id" in cm
        assert cm["skill_name"] == "oracle"

    def test_summary_fields(self, tmp_path):
        events = [
            _make_tool_call_event("read", {"file_path": "/skills/weather/SKILL.md"},
                                  tokens=0, cost=0.0),
            _make_assistant_event(tokens=200, cost=0.003),
        ]
        _write_jsonl(tmp_path / "s.jsonl", events)
        result = build_skill_leaderboard(str(tmp_path))
        s = result["summary"]
        assert s["unique_skills"] == 1
        assert s["total_executions"] == 1
        assert s["total_tokens"] == 200
        assert "generated_at" in result


# ── API endpoint tests ────────────────────────────────────────────────────────

@pytest.fixture
def app_client(tmp_path, monkeypatch):
    """Create a test Flask client with a synthetic sessions dir.

    Blueprints in dashboard.py are registered inside main() so we need to
    trigger that registration before building the test client.
    """
    # Minimal session with one skill
    events = [
        _make_tool_call_event("read", {"file_path": "/skills/coding-agent/SKILL.md"},
                              tokens=0, cost=0.0, timestamp="2026-01-01T00:00:00Z"),
        _make_assistant_event(tokens=1000, cost=0.015, timestamp="2026-01-01T00:01:00Z"),
    ]
    _write_jsonl(tmp_path / "test_session.jsonl", events)

    import dashboard as _dash

    # Register blueprints (idempotent in Flask >= 2.x when allow_registrations is True,
    # but we guard with a flag to avoid double-registration across test runs)
    if not getattr(_dash.app, '_skills_bp_registered', False):
        _dash.app.register_blueprint(_dash.bp_skills)
        _dash.app._skills_bp_registered = True  # type: ignore[attr-defined]

    # Patch the sessions dir used by the dashboard
    monkeypatch.setattr(_dash, "SESSIONS_DIR", str(tmp_path))

    # Clear the skill cache so fresh data is returned for this test
    from clawmetry import skills as _skills_mod
    _skills_mod._skill_cache['data'] = None

    _dash.app.config["TESTING"] = True
    with _dash.app.test_client() as client:
        yield client


class TestSkillAPI:
    def test_leaderboard_endpoint(self, app_client):
        resp = app_client.get("/api/skills/leaderboard")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "leaderboard" in data
        assert "summary" in data
        lb = data["leaderboard"]
        assert len(lb) >= 1
        assert lb[0]["skill_name"] == "coding-agent"
        assert "clawmetry_skill" in lb[0]

    def test_executions_endpoint(self, app_client):
        resp = app_client.get("/api/skills/executions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "executions" in data
        assert "total" in data
        assert len(data["executions"]) >= 1

    def test_executions_skill_filter(self, app_client):
        resp = app_client.get("/api/skills/executions?skill=coding-agent")
        assert resp.status_code == 200
        data = resp.get_json()
        for ex in data["executions"]:
            assert ex["skill_name"] == "coding-agent"

    def test_executions_filter_no_match(self, app_client):
        resp = app_client.get("/api/skills/executions?skill=nonexistent-skill")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["executions"] == []
        assert data["total"] == 0

    def test_executions_limit(self, app_client):
        resp = app_client.get("/api/skills/executions?limit=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["executions"]) <= 1
