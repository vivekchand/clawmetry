"""English policy regression coverage.

AC-STE-003.1: both transports use the common instructions.
AC-STE-003.2: rejected prose retains rows and uses a fixed fallback.
AC-STE-003.3: rejected prose retains known token usage.
AC-STE-003.4: validation makes no additional model call.
"""
import copy
import json

import pytest

from clawmetry import insights
from clawmetry.english import GENERATION_INSTRUCTIONS, check_text


@pytest.fixture(scope="session")
def server():
    """Model transports and query results are isolated in these unit tests."""
    yield None


@pytest.mark.parametrize("mode", ["direct", "relay"])
@pytest.mark.parametrize("prose", ["We can't show it.", "word " * 26, "", None,
                                   "<script>Do something.</script>", "```hidden text```"])
def test_rejected_prose_keeps_rows_tokens_and_makes_no_retry(monkeypatch, caplog, mode, prose):
    rows = [{"session": "original evidence", "tokens": 50, "cost": None}]
    before = copy.deepcopy(rows)
    calls = []
    def generate(*args):
        calls.append(args)
        return prose, 42
    name = "_synthesize_via_relay" if mode == "relay" else "_synthesize_via_anthropic"
    monkeypatch.setattr(insights, name, generate)
    result, tokens = insights._synthesize_narrative("not-a-real-key", "Title", "Hint", rows, mode)
    assert len(calls) == 1
    assert rows == before
    assert tokens == 42
    assert "unavailable" in result and "1 row" in result
    assert not check_text(result)
    assert "not-a-real-key" not in caplog.text
    assert "original evidence" not in caplog.text


@pytest.mark.parametrize("mode", ["direct", "relay"])
def test_valid_prose_is_unchanged(monkeypatch, mode):
    expected = "The agent used 50 tokens. The cost is unknown."
    name = "_synthesize_via_relay" if mode == "relay" else "_synthesize_via_anthropic"
    monkeypatch.setattr(insights, name, lambda *args: (expected, 80))
    assert insights._synthesize_narrative("key", "Title", "Hint", [{"tokens": 50}], mode) == (expected, 80)


def test_empty_rows_do_not_call_a_model(monkeypatch):
    def forbidden(*args):
        pytest.fail("An empty result must not call a model")
    monkeypatch.setattr(insights, "_synthesize_via_anthropic", forbidden)
    result, tokens = insights._synthesize_narrative("key", "Title", "Hint", [])
    assert tokens == 0 and not check_text(result)


def test_both_transports_send_same_policy_and_preserve_empty_response_cost(monkeypatch):
    requests = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self):
            return json.dumps({"text": [], "tokens": 12, "content": [],
                               "usage": {"input_tokens": 10, "output_tokens": 2}}).encode()
    def send(request, **kwargs):
        requests.append(json.loads(request.data))
        return Response()
    monkeypatch.setattr(insights.urllib.request, "urlopen", send)
    for mode in ("direct", "relay"):
        result, tokens = insights._synthesize_narrative("key", "Title", "Hint", [{"tokens": 50}], mode)
        assert tokens == 12 and "unavailable" in result
    assert GENERATION_INSTRUCTIONS in requests[0]["messages"][0]["content"]
    assert GENERATION_INSTRUCTIONS in requests[1]["prompt"]


def test_summary_keeps_missing_cost_distinct_from_zero(monkeypatch):
    monkeypatch.setattr(insights, "_resolve_synthesis_credential", lambda cfg: ("none", None))
    monkeypatch.setattr(insights, "_run_sql_via_daemon", lambda *args: [
        {"events": 2, "sessions": 1, "tokens": 100, "cost": None}])
    digest = insights.WeeklyDigestGenerator({"enabled": True}).generate()
    assert "Cost not recorded" in digest.summary
    assert "$0.00" not in digest.summary
    assert not check_text(digest.summary)


@pytest.mark.parametrize("mode", ["none", "direct", "relay"])
def test_activity_turn_uses_its_own_fallback(monkeypatch, mode):
    import importlib
    from flask import Flask
    from clawmetry.english import TURN_MESSAGES
    from routes import brain

    # Older insight tests reload this module. Patch the same current module
    # that the route imports, regardless of collection or execution order.
    current_insights = importlib.import_module("clawmetry.insights")

    rows = [{"id": "turn-1", "event_type": "assistant", "text": "original evidence"}]
    before = copy.deepcopy(rows)
    monkeypatch.setattr(brain, "_fetch_session_chain", lambda *args: rows)
    monkeypatch.setattr(current_insights, "load_config", lambda: {})
    monkeypatch.setattr(current_insights, "_resolve_synthesis_credential", lambda cfg: (mode, "key"))
    calls = []
    def generate(*args):
        calls.append(args)
        return "We can't explain it.", 12
    monkeypatch.setattr(current_insights, "_synthesize_via_anthropic", generate)
    monkeypatch.setattr(current_insights, "_synthesize_via_relay", generate)
    app = Flask(__name__)
    app.register_blueprint(brain.bp_brain)
    response = app.test_client().get("/api/brain/why/session-1/turn-1")
    assert response.status_code == 200
    narration = response.get_json()["narration"]
    expected_model = "none" if mode == "none" else current_insights.SYNTHESIS_MODEL if mode == "direct" else None
    assert response.get_json()["model"] == expected_model
    assert narration == TURN_MESSAGES["connect" if mode == "none" else "unavailable"]
    assert "table" not in narration and "week" not in narration
    assert not check_text(narration)
    assert rows == before
    assert len(calls) == (0 if mode == "none" else 1)
