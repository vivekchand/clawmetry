"""Regression tests for issue #3538.

OpenClaw 2026.7.1 added per-agent ``utilityModel`` routing so cheaper models
generate session/topic/thread titles instead of the main conversation model.
ClawMetry was not reading these fields: ``list_sessions()`` never placed
``utilityModel``, ``utilityModelTokens``, ``utilityModelInputTokens``,
``utilityModelOutputTokens``, or ``utilityModelCostUsd`` into ``Session.extra``,
so utilityModel-driven calls were invisible in usage attribution.
"""

import clawmetry.adapters.openclaw as ocmod
from clawmetry.adapters.openclaw import OpenClawAdapter


class _FakeDash:
    def __init__(self, extra_fields=None):
        self._fields = extra_fields or {}

    def _get_sessions(self):
        record = {"sessionId": "sess-um-1"}
        record.update(self._fields)
        return [record]


def test_list_sessions_surfaces_utility_model(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"utilityModel": "claude-haiku-4-5"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert len(sessions) == 1
    assert sessions[0].extra.get("utilityModel") == "claude-haiku-4-5", (
        "list_sessions() must surface utilityModel from the gateway record"
    )


def test_list_sessions_surfaces_title_model_alias(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"titleModel": "claude-haiku-4-5"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("utilityModel") == "claude-haiku-4-5", (
        "titleModel alias must be accepted when utilityModel is absent"
    )


def test_list_sessions_surfaces_session_title_model_alias(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d", lambda: _FakeDash({"sessionTitleModel": "claude-haiku-4-5"})
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("utilityModel") == "claude-haiku-4-5", (
        "sessionTitleModel alias must be accepted when utilityModel is absent"
    )


def test_list_sessions_surfaces_utility_model_tokens(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d",
        lambda: _FakeDash({"utilityModel": "claude-haiku-4-5", "utilityModelTokens": 120}),
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("utilityModelTokens") == 120, (
        "utilityModelTokens must be surfaced as int in Session.extra"
    )


def test_list_sessions_surfaces_utility_model_total_tokens_alias(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d",
        lambda: _FakeDash({"utilityModel": "m", "utilityModelTotalTokens": 99}),
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("utilityModelTokens") == 99, (
        "utilityModelTotalTokens alias must map to utilityModelTokens"
    )


def test_list_sessions_surfaces_utility_model_input_output_tokens(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d",
        lambda: _FakeDash({
            "utilityModel": "m",
            "utilityModelInputTokens": 80,
            "utilityModelOutputTokens": 40,
        }),
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("utilityModelInputTokens") == 80
    assert sessions[0].extra.get("utilityModelOutputTokens") == 40


def test_list_sessions_surfaces_utility_model_cost_usd(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d",
        lambda: _FakeDash({"utilityModel": "m", "utilityModelCostUsd": 0.0012}),
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    cost = sessions[0].extra.get("utilityModelCostUsd")
    assert isinstance(cost, float) and abs(cost - 0.0012) < 1e-9, (
        "utilityModelCostUsd must be surfaced as float"
    )


def test_list_sessions_surfaces_utility_model_cost_alias(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d",
        lambda: _FakeDash({"utilityModel": "m", "utilityModelCost": 0.0008}),
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    cost = sessions[0].extra.get("utilityModelCostUsd")
    assert isinstance(cost, float) and abs(cost - 0.0008) < 1e-9, (
        "utilityModelCost alias must map to utilityModelCostUsd"
    )


def test_list_sessions_omits_utility_model_fields_when_absent(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash())
    sessions = OpenClawAdapter().list_sessions(limit=10)
    extra = sessions[0].extra
    for key in (
        "utilityModel",
        "utilityModelTokens",
        "utilityModelInputTokens",
        "utilityModelOutputTokens",
        "utilityModelCostUsd",
    ):
        assert key not in extra, f"{key!r} must not appear when absent from gateway record"


def test_list_sessions_coerces_token_strings_to_int(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d",
        lambda: _FakeDash({"utilityModel": "m", "utilityModelTokens": "55"}),
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("utilityModelTokens") == 55, (
        "string token values must be coerced to int"
    )
