"""Regression tests for issue #5409.

OpenClaw PR #95341 added per-cron agent-turn model selection: Quick Create
lets users pick a model for each cron job, and the gateway now stamps the
configured (or defaulted) model on every cron job record.

Before this fix, ClawMetry only read ``j.get("model")`` with no alias
fallbacks and had no test verifying the field was captured end-to-end
through the DuckDB route path.
"""

import routes.crons as crons_mod
from routes.crons import _row_to_cron_job


def _make_row(**kwargs):
    row = {
        "cron_id": "job-1",
        "name": "nightly-check",
        "schedule": '{"kind": "cron", "expr": "0 2 * * *"}',
        "enabled": True,
        "last_run_at": None,
        "last_status": "ok",
        "next_run_at": None,
        "data": {},
    }
    row.update(kwargs)
    return row


def test_row_to_cron_job_surfaces_model():
    """model from the DuckDB crons row must appear in the job dict."""
    job = _row_to_cron_job(_make_row(model="claude-haiku-4-5"))
    assert job["model"] == "claude-haiku-4-5", (
        "_row_to_cron_job must surface the model column from the DuckDB row"
    )


def test_row_to_cron_job_model_absent_defaults_to_empty_string():
    """model should be an empty string when the column is absent."""
    job = _row_to_cron_job(_make_row())
    assert job["model"] == "", (
        "model must default to '' when not present in the row"
    )


def test_row_to_cron_job_model_none_treated_as_absent():
    """model=None must surface as '' (not None) so callers can always str-compare."""
    job = _row_to_cron_job(_make_row(model=None))
    assert job["model"] == "", (
        "model=None must surface as empty string"
    )


def test_try_local_store_crons_includes_model(monkeypatch):
    """_try_local_store_crons must include model in each returned job dict."""
    rows = [_make_row(model="claude-opus-5")]
    monkeypatch.setattr(crons_mod, "_ls_call", lambda method, **kw: rows)
    result = crons_mod._try_local_store_crons()
    assert result is not None
    assert result["jobs"][0]["model"] == "claude-opus-5", (
        "_try_local_store_crons must carry model through from the DuckDB row"
    )


def test_try_local_store_crons_model_absent_is_empty_string(monkeypatch):
    """Jobs without model must still parse without error; model surfaces as ''."""
    rows = [_make_row()]
    monkeypatch.setattr(crons_mod, "_ls_call", lambda method, **kw: rows)
    result = crons_mod._try_local_store_crons()
    assert result is not None
    assert result["jobs"][0]["model"] == "", (
        "model must be '' (not missing) when absent in a DuckDB row"
    )


def test_try_local_store_crons_returns_none_on_empty_store(monkeypatch):
    """No regression: an empty store still returns None (gateway fallback fires)."""
    monkeypatch.setattr(crons_mod, "_ls_call", lambda method, **kw: [])
    assert crons_mod._try_local_store_crons() is None
