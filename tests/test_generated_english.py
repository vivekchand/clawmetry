"""Generated explanation boundaries preserve their non-prose contracts.

AC-STE-005.1: every tested generation path requests the common writing rules.
AC-STE-005.2: fallbacks preserve queries, scores, IDs, evidence, and known usage.
AC-STE-005.3: rejected alert narration retains the caller's original alert.
AC-STE-005.4: structured responses validate only explanation fields after parsing.
AC-STE-005.5: language failures cause no additional model call.
"""
import copy
import json

import pytest
from flask import Flask

from clawmetry.english import (
    EXPLANATION_MESSAGES, GENERATION_INSTRUCTIONS, WRITING_INSTRUCTIONS,
    explanation_or_fallback,
)


@pytest.fixture(scope="session")
def server():
    """All routes use a test client and all model transports are mocked."""
    yield None


@pytest.mark.parametrize("text", ["We can't explain it.", "word " * 21, None,
                                  "<b>The answer</b>", "```hidden text```", ""])
def test_explanation_fallback_does_not_rewrite_bad_prose(text):
    assert explanation_or_fallback(text, "advisor") == EXPLANATION_MESSAGES["advisor"]


@pytest.mark.parametrize("event_type,prose,accepted", [
    ("threshold", "The session used 50 tokens. Check its events.", True),
    ("threshold", "We can't explain it.", False),
    ("brief", "One. Two. Three. Four.", True),
    ("threshold", "One. Two. Three. Four.", False),
    ("loop", None, False),
])
def test_narrator_preserves_context_and_original_alert(monkeypatch, event_type, prose, accepted):
    from clawmetry import narrator
    monkeypatch.setattr(narrator, "is_enabled", lambda: True)
    monkeypatch.setattr(narrator, "_egress_suppressed", lambda: False)
    monkeypatch.setattr(narrator, "_check_coalesce", lambda *a: True)
    monkeypatch.setattr(narrator, "_resolve_api_key", lambda: "test-key")
    calls = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self):
            return json.dumps({"content": [{"type": "text", "text": prose}]}).encode()
    def send(request, **kwargs):
        calls.append(json.loads(request.data))
        return Response()
    monkeypatch.setattr(narrator.urllib.request, "urlopen", send)
    context = {"session_id": "s-1", "tokens": 50, "cost": None}
    original = copy.deepcopy(context)
    raw_alert = "Original alert: s-1, 50 tokens, cost unknown."
    result = narrator.narrate(event_type, context)
    assert (result or raw_alert) == (prose if accepted else raw_alert)
    assert context == original
    assert len(calls) == 1
    assert GENERATION_INSTRUCTIONS in calls[0]["system"]
    assert '"cost": null' in calls[0]["messages"][0]["content"]

    # Exercise the real dispatch caller, with persistence and every outbound
    # channel replaced by spies. Only the mocked model transport can run.
    import dashboard
    from unittest.mock import MagicMock
    calls.clear()
    delivered = []
    database = MagicMock()
    monkeypatch.setattr(dashboard, "_budget_alert_cooldowns", {})
    monkeypatch.setattr(dashboard, "_fleet_db", lambda: database)
    monkeypatch.setattr(dashboard, "_dispatch_alert", lambda **kw: delivered.append(kw))
    dashboard._fire_alert("test-rule", event_type, raw_alert, channels=["banner"], builtin=False)
    assert len(delivered) == len(calls) == 1
    assert delivered[0]["message"] == (prose if accepted else raw_alert)
    assert database.execute.call_args.args[1][2] == raw_alert


def test_brief_fallback_preserves_table_without_inventing_a_cause():
    from clawmetry.briefs import compose_post
    rows = [{"session_id": "s-1", "cost": None, "tokens": 50}]
    before = copy.deepcopy(rows)
    text = compose_post({"title": "My brief"}, rows=rows, narrative=None,
                        error=None, link="https://example.com")
    assert EXPLANATION_MESSAGES["brief"] in text
    assert "s-1" in text and "50" in text
    assert "credential" not in text and rows == before


@pytest.mark.parametrize("mode", ["direct", "claude_cli"])
@pytest.mark.parametrize("prose", ["Session s-1 used 50 tokens. The cost is unknown.",
                                   "We can't explain it.", None])
def test_advisor_retains_known_usage_and_context(monkeypatch, mode, prose):
    from routes import advisor
    ctx = {"events": ["[2026-10-02T10:00:00] s-1 model.completed: 50 tokens, cost unknown"],
           "_source": "local_store"}
    before = copy.deepcopy(ctx)
    monkeypatch.setattr(advisor, "_load_anthropic_auth", lambda: (mode, "test-key"))
    monkeypatch.setattr(advisor, "_gather_context", lambda: ctx)
    calls = []
    def generate(*args, **kwargs):
        calls.append((args, kwargs))
        return {"model": "test-model", "content": [{"type": "text", "text": prose}],
                "usage": {"input_tokens": 31, "output_tokens": 17}}
    monkeypatch.setattr(advisor, "_call_anthropic_api", generate)
    monkeypatch.setattr(advisor, "_call_via_claude_cli", generate)
    app = Flask(__name__)
    app.register_blueprint(advisor.bp_advisor)
    response = app.test_client().post("/api/advisor/ask", json={"question": "What happened?"})
    assert response.status_code == 200
    result = response.get_json()
    assert result["answer"] == explanation_or_fallback(prose, "advisor")
    assert (result["input_tokens"], result["output_tokens"]) == (31, 17)
    assert result["model"] == "test-model" and result["events_in_context"] == 1
    assert result["_source"] == "local_store" and ctx == before
    assert len(calls) == 1
    assert GENERATION_INSTRUCTIONS in advisor.SYSTEM_PROMPT


@pytest.mark.parametrize("mode", ["direct", "claude_cli"])
@pytest.mark.parametrize("valid", [True, False])
def test_chart_checks_prose_after_json_without_changing_sql(monkeypatch, mode, valid):
    from routes import advisor, dives
    spec = {"sql": "SELECT agent_id, sum(cost) AS cost FROM events GROUP BY agent_id",
            "chart_type": "bar", "x": "agent_id", "y": "cost",
            "title": "Cost by agent" if valid else "We can't show it.",
            "description": "The query groups costs by agent." if valid else "Use this; do that."}
    original = copy.deepcopy(spec)
    calls = []
    monkeypatch.setattr(advisor, "_load_anthropic_auth", lambda: (mode, "test-key"))
    def generate(*args, **kwargs):
        calls.append(kwargs)
        return {"content": [{"type": "text", "text": json.dumps(spec)}]}
    monkeypatch.setattr(advisor, "_call_anthropic_api", generate)
    monkeypatch.setattr(advisor, "_call_via_claude_cli", generate)
    result = dives._call_llm_for_sql("Show costs by agent", None)
    for key in ("sql", "chart_type", "x", "y"):
        assert result[key] == original[key]
    assert spec == original and len(calls) == 1
    assert result["title"] == (spec["title"] if valid else EXPLANATION_MESSAGES["chart_title"])
    assert result["description"] == (spec["description"] if valid else EXPLANATION_MESSAGES["chart_description"])
    assert WRITING_INSTRUCTIONS in calls[0]["system"]
    assert "Return plain text." not in calls[0]["system"]


@pytest.mark.parametrize("reason", ["The session completed the requested task.",
                                   "It can't complete the task.", "", "Good. " * 60])
def test_classic_judge_keeps_score_without_style_retry(monkeypatch, reason):
    from clawmetry import eval_runner
    monkeypatch.setattr(eval_runner, "is_enabled", lambda: True)
    monkeypatch.setattr(eval_runner, "_judge_key_present", lambda *a: True)
    monkeypatch.setattr(eval_runner, "load_rubric", lambda *a: dict(eval_runner.DEFAULT_RUBRIC))
    monkeypatch.setattr(eval_runner, "_record_judge_status", lambda *a: None)
    class Store:
        persisted = []
        def persist_eval_score(self, **kwargs): self.persisted.append(kwargs)
    store = Store()
    runner = eval_runner.EvalRunner(store=store)
    evidence = "User: Check this task.\nAssistant: The task is complete."
    monkeypatch.setattr(runner, "_collect_transcript", lambda *a: (evidence, 50))
    calls = []
    def judge(model, prompt, **kwargs):
        calls.append(prompt)
        return "SCORE: 4\nREASON: " + reason
    result = runner.score_session("s-1", judge_call=judge)
    assert result.score == 4.0 and result.session_id == "s-1"
    expected = explanation_or_fallback(reason, "evaluation", max_chars=280)
    assert result.reason == expected
    assert len(store.persisted) == 1 and store.persisted[0]["score"] == 4.0
    assert store.persisted[0]["reason"] == expected
    assert len(calls) == 1 and WRITING_INSTRUCTIONS in calls[0]
    assert evidence in calls[0]
