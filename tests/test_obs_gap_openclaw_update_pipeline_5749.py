"""Regression tests for the update-pipeline state gateway event scanner.

Closes: vivekchand/clawmetry#5749
"""
import pytest
from clawmetry.adapters.openclaw import _openclaw_update_pipeline_state


# ---------------------------------------------------------------------------
# candidate-state events
# ---------------------------------------------------------------------------

def test_candidate_state_detected():
    events = [
        {"msg": "update candidate activated: core v2026.9.3", "ts": "2026-09-09T10:00:00Z"},
    ]
    result = _openclaw_update_pipeline_state(events)
    assert result["updatePipelineStateDetected"] is True
    assert result["updatePipelineCandidateState"] is True
    assert result["updatePipelineTs"] == "2026-09-09T10:00:00Z"
    assert "candidate" in result["updatePipelineMsg"].lower()


def test_candidate_activation_keyword():
    events = [
        {"msg": "candidate state: activation pending for plugin clawrouter"},
    ]
    result = _openclaw_update_pipeline_state(events)
    assert result["updatePipelineStateDetected"] is True
    assert result["updatePipelineCandidateState"] is True
    assert result.get("updatePipelineAbandoned") is None


# ---------------------------------------------------------------------------
# abandoned-update recovery events
# ---------------------------------------------------------------------------

def test_abandoned_update_recovery_detected():
    events = [
        {"msg": "abandoned update record recovered — gateway continuing", "ts": "2026-09-09T11:00:00Z"},
    ]
    result = _openclaw_update_pipeline_state(events)
    assert result["updatePipelineStateDetected"] is True
    assert result["updatePipelineAbandoned"] is True
    assert result["updatePipelineTs"] == "2026-09-09T11:00:00Z"


def test_abandon_update_keyword():
    events = [
        {"msg": "abandon update: rolling back to stable"},
    ]
    result = _openclaw_update_pipeline_state(events)
    assert result["updatePipelineStateDetected"] is True
    assert result["updatePipelineAbandoned"] is True
    assert result.get("updatePipelineCandidateState") is None


# ---------------------------------------------------------------------------
# activation event
# ---------------------------------------------------------------------------

def test_activation_update_keyword():
    events = [
        {"msg": "activation update completed for core 2026.9.3"},
    ]
    result = _openclaw_update_pipeline_state(events)
    assert result["updatePipelineStateDetected"] is True


# ---------------------------------------------------------------------------
# both candidate + abandoned in same session
# ---------------------------------------------------------------------------

def test_both_candidate_and_abandoned():
    events = [
        {"msg": "candidate update rehearsal started", "ts": "2026-09-09T10:00:00Z"},
        {"msg": "abandoned update recovery triggered", "ts": "2026-09-09T10:01:00Z"},
    ]
    result = _openclaw_update_pipeline_state(events)
    assert result["updatePipelineStateDetected"] is True
    assert result["updatePipelineCandidateState"] is True
    assert result["updatePipelineAbandoned"] is True
    # first event's msg + ts wins
    assert result["updatePipelineTs"] == "2026-09-09T10:00:00Z"
    assert "candidate" in result["updatePipelineMsg"].lower()


# ---------------------------------------------------------------------------
# no matching events → empty dict
# ---------------------------------------------------------------------------

def test_no_update_events_returns_empty():
    events = [
        {"msg": "gateway started", "ts": "2026-09-09T00:00:00Z"},
        {"msg": "backup completed successfully"},
        {"msg": "oom: model server killed"},
    ]
    assert _openclaw_update_pipeline_state(events) == {}


def test_empty_events_list():
    assert _openclaw_update_pipeline_state([]) == {}


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------

def test_none_msg_skipped():
    events = [{"msg": None}, {"msg": "candidate update rehearsal"}]
    result = _openclaw_update_pipeline_state(events)
    assert result["updatePipelineStateDetected"] is True


def test_no_ts_field_omitted():
    events = [{"msg": "candidate update rehearsal started"}]
    result = _openclaw_update_pipeline_state(events)
    assert result["updatePipelineStateDetected"] is True
    assert "updatePipelineTs" not in result


# ---------------------------------------------------------------------------
# exception safety
# ---------------------------------------------------------------------------

def test_exception_safety_none():
    assert _openclaw_update_pipeline_state(None) == {}  # type: ignore[arg-type]


def test_exception_safety_not_a_list():
    assert _openclaw_update_pipeline_state("not-a-list") == {}  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# non-update migration event is NOT matched (different scanner)
# ---------------------------------------------------------------------------

def test_migration_warning_not_matched():
    # _gateway_migration_warning handles warn-level "migration" events;
    # _openclaw_update_pipeline_state should not double-count them unless
    # they also contain update-pipeline keywords.
    events = [
        {"level": "warning", "msg": "migration warning: schema v14 requires manual step"},
    ]
    # "migration" alone has no update/candidate/abandon keyword → no match
    assert _openclaw_update_pipeline_state(events) == {}
