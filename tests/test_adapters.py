"""Tests for the agent-adapter layer (clawmetry/adapters/).

Validates the registry, the OpenClawAdapter wrap, and the /api/agents
route. Does not require a running OpenClaw — the adapter handles the
"nothing installed" case gracefully.
"""
from __future__ import annotations

import pytest

from clawmetry.adapters import (
    AgentAdapter,
    Capability,
    DetectResult,
    Event,
    Session,
    registry,
)


class _FakeAdapter(AgentAdapter):
    name = "fake"
    display_name = "Fake Agent"

    def __init__(self, sessions=None, detected=True):
        self._sessions = sessions or []
        self._detected = detected

    def detect(self) -> DetectResult:
        return DetectResult(
            name=self.name,
            display_name=self.display_name,
            detected=self._detected,
            running=self._detected,
            session_count=len(self._sessions),
            capabilities=[c.value for c in self.capabilities()],
        )

    def list_sessions(self, limit: int = 100):
        return self._sessions[:limit]

    def capabilities(self):
        return {Capability.SESSIONS, Capability.EVENTS}


@pytest.fixture(autouse=True)
def _clean_registry():
    for a in list(registry.all_adapters()):
        registry.unregister(a.name)
    yield
    for a in list(registry.all_adapters()):
        registry.unregister(a.name)


@pytest.fixture(scope="module", autouse=True)
def _ensure_blueprints_registered():
    """Blueprints are wired in dashboard.main() — register ours for test_client()."""
    import dashboard as _d
    from routes.agents import bp_agents

    if "agents" not in _d.app.blueprints:
        _d.app.register_blueprint(bp_agents)
    yield


def test_register_and_get():
    a = _FakeAdapter()
    registry.register(a)
    assert registry.get("fake") is a
    assert registry.get("nonexistent") is None


def test_register_replaces_by_name():
    registry.register(_FakeAdapter(sessions=[1, 2]))
    registry.register(_FakeAdapter(sessions=[3]))
    got = registry.get("fake")
    assert got is not None
    assert got.detect().session_count == 1


def test_unregister():
    registry.register(_FakeAdapter())
    registry.unregister("fake")
    assert registry.get("fake") is None


def test_register_rejects_nameless():
    class BadAdapter(_FakeAdapter):
        name = ""

    with pytest.raises(ValueError):
        registry.register(BadAdapter())


def test_detect_all_catches_exceptions():
    class BrokenAdapter(_FakeAdapter):
        def detect(self):
            raise RuntimeError("boom")

    registry.register(_FakeAdapter())
    registry.register(BrokenAdapter())
    # Second adapter must get same name to avoid collision
    # so give it a different one:
    registry.unregister("fake")

    class OkAdapter(_FakeAdapter):
        name = "ok"

    class BadAdapter(_FakeAdapter):
        name = "bad"

        def detect(self):
            raise RuntimeError("boom")

    registry.register(OkAdapter())
    registry.register(BadAdapter())
    results = registry.detect_all()
    names = {r.name for r in results}
    assert "ok" in names
    assert "bad" in names
    bad = next(r for r in results if r.name == "bad")
    assert bad.detected is False
    assert "boom" in bad.meta.get("error", "")


def test_session_to_dict_includes_extra_only_when_nonempty():
    s = Session(agent="a", id="sid")
    d = s.to_dict()
    assert "extra" not in d
    s2 = Session(agent="a", id="sid", extra={"foo": "bar"})
    assert s2.to_dict()["extra"] == {"foo": "bar"}


def test_session_display_name_fallback():
    s = Session(agent="a", id="very-long-identifier-that-is-longer-than-24-chars")
    assert s.to_dict()["displayName"] == "very-long-identifier-tha"


def test_event_to_dict_roundtrip():
    e = Event(
        agent="a",
        session_id="sid",
        id="1",
        type="message",
        role="user",
        content="hi",
        ts=123.0,
    )
    d = e.to_dict()
    assert d["agent"] == "a"
    assert d["sessionId"] == "sid"
    assert d["type"] == "message"
    assert d["role"] == "user"


def test_detect_result_to_dict():
    r = DetectResult(
        name="x",
        display_name="X",
        detected=True,
        running=False,
        session_count=3,
        capabilities=["sessions"],
    )
    d = r.to_dict()
    assert d["name"] == "x"
    assert d["sessionCount"] == 3
    assert d["capabilities"] == ["sessions"]


def test_openclaw_adapter_detect_does_not_raise_without_dashboard_globals():
    # When dashboard.py globals are unset (WORKSPACE=None), detect() must
    # still return a valid DetectResult with detected=False rather than
    # crashing the /api/agents endpoint.
    from clawmetry.adapters.openclaw import OpenClawAdapter

    import dashboard as _d

    orig_ws = getattr(_d, "WORKSPACE", None)
    orig_sd = getattr(_d, "SESSIONS_DIR", None)
    try:
        _d.WORKSPACE = None
        _d.SESSIONS_DIR = None
        result = OpenClawAdapter().detect()
        assert isinstance(result, DetectResult)
        assert result.name == "openclaw"
        # May be detected=True if the real workspace is present on the test
        # machine — only assert the call does not raise.
    finally:
        _d.WORKSPACE = orig_ws
        _d.SESSIONS_DIR = orig_sd


def test_api_agents_route_shape():
    """Hit /api/agents via Flask test client."""
    import dashboard as _d

    # Ensure at least one adapter is registered (OpenClaw via production path)
    from clawmetry.adapters.openclaw import OpenClawAdapter

    registry.register(OpenClawAdapter())

    client = _d.app.test_client()
    resp = client.get("/api/agents")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "agents" in body
    assert isinstance(body["agents"], list)
    assert len(body["agents"]) >= 1
    first = body["agents"][0]
    for k in ("name", "displayName", "detected", "capabilities", "sessionCount"):
        assert k in first


def test_api_agents_404_for_unknown():
    import dashboard as _d

    client = _d.app.test_client()
    resp = client.get("/api/agents/nonexistent-agent-xyz")
    assert resp.status_code == 404


def test_api_agent_sessions_returns_unified_shape():
    import dashboard as _d

    registry.register(_FakeAdapter(
        sessions=[
            Session(agent="fake", id="s1", model="m", started_at=1.0),
            Session(agent="fake", id="s2", model="m", started_at=2.0),
        ]
    ))
    client = _d.app.test_client()
    resp = client.get("/api/agents/fake/sessions")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["sessions"]) == 2
    assert body["sessions"][0]["id"] == "s1"
    assert body["sessions"][0]["agent"] == "fake"
