"""Evals must skip QUIETLY when no judge API key is configured.

Evals are default-on, but the judge calls a real LLM (Anthropic/OpenAI) that
needs an API key. With no key the scheduler used to attempt every session and
log a WARNING each ("judge call failed ... ANTHROPIC_API_KEY not set"), spamming
sync.log and implying the feature is broken. Now it returns a quiet SKIP and
never invokes the judge, so nothing spams and nothing spends.
"""
import clawmetry.eval_runner as er


def test_score_session_skips_when_no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(er, "_NO_KEY_LOGGED", False, raising=False)

    called = {"judge": False}

    def _spy(model, prompt, *, timeout=0):
        called["judge"] = True
        return "Score: 9"

    runner = er.EvalRunner()
    result = runner.score_session("sess-1", judge_call=_spy)

    assert result is not None
    assert result.skipped is True
    assert "no judge API key" in (result.skip_reason or "")
    assert called["judge"] is False, "judge must NOT be called without a key"


def test_score_session_proceeds_with_key(monkeypatch):
    # With a key, the no-key guard must NOT short-circuit (it should get far
    # enough to attempt transcript collection / judging). We assert it does
    # NOT return the no-key skip reason.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setattr(er, "_NO_KEY_LOGGED", False, raising=False)
    # Empty store -> no transcript -> a DIFFERENT skip, never the no-key one.
    runner = er.EvalRunner(store=_EmptyStore())
    result = runner.score_session("sess-2", judge_call=lambda *a, **k: "Score: 5")
    assert result is None or "no judge API key" not in (result.skip_reason or "")


class _EmptyStore:
    """Minimal store stub: returns no events so transcript collection yields
    nothing (a non-key skip path)."""

    def query_events(self, *a, **k):
        return []

    def execute(self, *a, **k):
        return []
