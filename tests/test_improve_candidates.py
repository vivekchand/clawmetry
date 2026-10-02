from routes.improve import _build_candidates


def _message(text, *, session="session-1", workspace="/work/app", ts="2026-10-01T12:00:00Z"):
    return {
        "session_id": session,
        "workspace_id": workspace,
        "agent_type": "codex",
        "ts": ts,
        "data": {"role": "user", "content": text},
    }


def test_build_candidates_groups_repeated_preferences_and_reports_scope():
    result = _build_candidates([
        _message("From now on, keep the answer concise.", session="one"),
        _message("Going forward, please keep the answer concise!", session="two", workspace="/work/other"),
        _message("The agent used the wrong file.", session="three"),
    ], window_days=30)

    assert result["message_count"] == 3
    assert result["conversation_count"] == 3
    assert result["project_count"] == 2
    preference = next(item for item in result["signals"] if item["kind"] == "preference")
    assert preference["seen_count"] == 2
    assert preference["conversation_count"] == 2
    assert preference["confidence"] == "high"
    assert preference["scope"] == "workspace"
    assert preference["pain_score"] == 3


def test_build_candidates_ignores_internal_and_blume_analysis_runs():
    result = _build_candidates([
        _message("Do not change this preference.", session="clawmetry-fix"),
        _message("Always use this rule.", session="blume-run", workspace="/Users/me/.blume/harnessruns123"),
        _message("Always use this rule.", session="real-session"),
    ], window_days=30)

    assert result["message_count"] == 1
    assert len(result["signals"]) == 1
