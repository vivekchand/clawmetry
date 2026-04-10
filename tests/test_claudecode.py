"""
ClawMetry Claude Code Dashboard — API endpoint tests.

Tests every API endpoint for:
- Correct HTTP status (200 / 404)
- Response structure / required keys
- Correct JSONL parsing semantics (tool_result not labelled as user)

Tests are resilient: empty data is fine — we just check structure.

Run with:
    python dashboard_claudecode.py --port 8901 &
    CLAWMETRY_CC_URL=http://localhost:8901 pytest tests/test_claudecode.py -v
"""

import os
import sys
import subprocess
import time

import pytest
import requests


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CC_BASE_URL = os.environ.get("CLAWMETRY_CC_URL", "http://localhost:8901")


def _is_server_running(base_url):
    try:
        r = requests.get(f"{base_url}/api/health", timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture(scope="session")
def base_url():
    return CC_BASE_URL


@pytest.fixture(scope="session")
def api():
    return requests.Session()


@pytest.fixture(scope="session")
def mock_claude_home(tmp_path_factory):
    """Create a temporary CLAUDE_HOME with mock session data."""
    import tempfile
    import json

    tmpdir = tmp_path_factory.mktemp("mock_claude_home")
    projects_dir = tmpdir / "projects"
    projects_dir.mkdir()

    project_slug = "test-project"
    project_dir = projects_dir / project_slug
    project_dir.mkdir()

    session_id = "test-session-001"
    timestamp = "2026-04-03T10:00:00.000Z"
    jsonl_content = (
        json.dumps(
            {
                "type": "user",
                "timestamp": timestamp,
                "cwd": "/test/cwd",
                "gitBranch": "main",
                "version": "1.2.3",
                "entrypoint": "main.py",
                "message": {"role": "user", "content": "Hello, this is a test message"},
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "assistant",
                "timestamp": timestamp,
                "message": {
                    "role": "assistant",
                    "model": "claude-3-5-sonnet-20241022",
                    "content": [{"type": "text", "text": "Hello! How can I help you?"}],
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                },
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "user",
                "timestamp": timestamp,
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tool_1",
                            "content": "result",
                        }
                    ],
                },
            }
        )
    )

    jsonl_path = project_dir / f"{session_id}.jsonl"
    jsonl_path.write_text(jsonl_content)

    memory_dir = project_dir / "memory"
    memory_dir.mkdir()
    memory_file = memory_dir / "MEMORY.md"
    memory_file.write_text("# Test Project Memory\n\nThis is mock memory content.")

    return str(tmpdir)


@pytest.fixture(scope="session", autouse=True)
def server(base_url, mock_claude_home):
    """Ensure the Claude Code dashboard server is running before tests."""
    if _is_server_running(base_url):
        yield base_url
        return

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard = os.path.join(repo_root, "dashboard_claudecode.py")
    try:
        port = base_url.split(":")[-1].rstrip("/")
    except Exception:
        port = "8901"
    env = os.environ.copy()
    env["CLAWMETRY_CLAUDE_HOME"] = mock_claude_home
    proc = subprocess.Popen(
        [sys.executable, dashboard, "--port", port],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=env,
    )

    for _ in range(40):
        time.sleep(0.5)
        if _is_server_running(base_url):
            break
    else:
        stderr_out = proc.stderr.read(2000) if proc.stderr else b""
        proc.terminate()
        pytest.fail(
            f"Claude Code dashboard failed to start. "
            f"stderr: {stderr_out.decode(errors='replace')}"
        )

    yield base_url
    proc.terminate()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get(api, base_url, path):
    """Make a GET request and return the response."""
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
# Health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_ok(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/health"))
        assert d["status"] == "ok"

    def test_health_keys(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/health"))
        assert_keys(d, "status", "version", "claude_home", "projects_dir")

    def test_version_string(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/health"))
        assert isinstance(d["version"], str)
        assert len(d["version"]) > 0


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


class TestSessions:
    def test_sessions_ok(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/sessions"))
        assert_keys(d, "sessions", "total")

    def test_sessions_is_list(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/sessions"))
        assert isinstance(d["sessions"], list)

    def test_session_structure(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/sessions?limit=1"))
        if not d["sessions"]:
            pytest.skip("No Claude Code sessions available")
        sess = d["sessions"][0]
        assert_keys(
            sess,
            "session_id",
            "source",
            "project",
            "tokens",
            "cost_usd",
            "model",
            "start_ts",
            "messages",
        )
        assert sess["source"] == "claude_code"

    def test_session_filter_project(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/sessions?limit=1"))
        if not d["sessions"]:
            pytest.skip("No sessions")
        proj = d["sessions"][0]["project"]
        d2 = assert_ok(get(api, base_url, f"/api/sessions?project={proj}"))
        assert all(s["project"] == proj for s in d2["sessions"])

    def test_session_limit(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/sessions?limit=2"))
        assert len(d["sessions"]) <= 2


# ---------------------------------------------------------------------------
# Session Detail
# ---------------------------------------------------------------------------


class TestSessionDetail:
    def test_session_detail_ok(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/sessions?limit=1"))
        if not d["sessions"]:
            pytest.skip("No sessions")
        sid = d["sessions"][0]["session_id"]
        detail = assert_ok(get(api, base_url, f"/api/session/{sid}"))
        assert_keys(
            detail,
            "name",
            "session_id",
            "messageCount",
            "model",
            "totalTokens",
            "messages",
        )

    def test_session_detail_404(self, api, base_url):
        r = get(api, base_url, "/api/session/nonexistent-uuid-12345")
        assert r.status_code == 404

    def test_message_roles_semantic(self, api, base_url):
        """Verify tool_result events are NOT labelled as 'user'."""
        d = assert_ok(get(api, base_url, "/api/sessions?limit=5"))
        for sess in d["sessions"]:
            detail = assert_ok(get(api, base_url, f"/api/session/{sess['session_id']}"))
            roles = {m["role"] for m in detail["messages"]}
            assert "user" not in roles, (
                f"Session {sess['session_id']} has 'user' role — "
                f"should be 'human'. Roles found: {roles}"
            )
            # Valid roles
            valid = {"human", "assistant", "thinking", "tool_use", "tool_result"}
            unexpected = roles - valid
            assert not unexpected, (
                f"Unexpected roles in {sess['session_id']}: {unexpected}"
            )
            break  # Only need to check one session with messages

    def test_messages_have_timestamps(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/sessions?limit=1"))
        if not d["sessions"]:
            pytest.skip("No sessions")
        sid = d["sessions"][0]["session_id"]
        detail = assert_ok(get(api, base_url, f"/api/session/{sid}"))
        for msg in detail["messages"][:5]:
            assert "timestamp" in msg
            assert "role" in msg
            assert "content" in msg


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


class TestAnalytics:
    def test_analytics_ok(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/analytics"))
        assert_keys(
            d,
            "total_sessions",
            "total_tokens",
            "total_cost_usd",
            "daily_tokens",
            "model_usage",
            "tool_stats",
        )

    def test_analytics_types(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/analytics"))
        assert isinstance(d["total_sessions"], int)
        assert isinstance(d["total_tokens"], int)
        assert isinstance(d["total_cost_usd"], (int, float))
        assert isinstance(d["daily_tokens"], dict)
        assert isinstance(d["model_usage"], dict)

    def test_analytics_cost_positive(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/analytics"))
        assert d["total_cost_usd"] >= 0


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class TestProjects:
    def test_projects_ok(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/projects"))
        assert_keys(d, "projects")
        assert isinstance(d["projects"], list)

    def test_project_structure(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/projects"))
        if not d["projects"]:
            pytest.skip("No projects found")
        proj = d["projects"][0]
        assert_keys(
            proj,
            "slug",
            "name",
            "path",
            "sessions",
            "has_memory",
        )

    def test_memory_preview_present(self, api, base_url):
        """Projects with MEMORY.md should include a preview."""
        d = assert_ok(get(api, base_url, "/api/projects"))
        for proj in d["projects"]:
            if proj["has_memory"]:
                assert "memory_preview" in proj
                assert len(proj["memory_preview"]) > 0
                return
        pytest.skip("No projects with MEMORY.md found")


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


class TestUI:
    def test_index_loads(self, api, base_url):
        r = get(api, base_url, "/")
        assert r.status_code == 200
        assert "Claude Code" in r.text

    def test_favicon(self, api, base_url):
        r = get(api, base_url, "/favicon.ico")
        assert r.status_code == 200
        assert "svg" in r.headers.get("content-type", "")
