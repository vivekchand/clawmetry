"""Regression tests for issue #3672.

CHANGELOG #98021 ("GPT-5.6 Ultra and runtime switching") added Sol, Terra,
and Luna as named runtime aliases switched atomically with model and thinking
mode.  ClawMetry was not capturing either field: ``list_sessions()`` never
placed ``runtimeAlias`` or ``thinkingMode`` in ``Session.extra``.
"""

import clawmetry.adapters.openclaw as ocmod


class _FakeDash:
    def __init__(self, **fields):
        self._fields = fields

    def _get_sessions(self):
        row = {"sessionId": "sess-3672-1"}
        row.update(self._fields)
        return [row]


def test_list_sessions_surfaces_runtime_alias(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash(runtimeAlias="sol"))
    sessions = ocmod.OpenClawAdapter().list_sessions(limit=10)
    assert len(sessions) == 1
    assert sessions[0].extra.get("runtimeAlias") == "sol", (
        "list_sessions() must surface 'runtimeAlias' in Session.extra"
    )


def test_list_sessions_surfaces_runtime_alias_via_selected_alias(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash(selectedRuntimeAlias="terra"))
    sessions = ocmod.OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("runtimeAlias") == "terra", (
        "list_sessions() must handle 'selectedRuntimeAlias' as a fallback key"
    )


def test_list_sessions_surfaces_runtime_alias_via_model_runtime_alias(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash(modelRuntimeAlias="luna"))
    sessions = ocmod.OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("runtimeAlias") == "luna", (
        "list_sessions() must handle 'modelRuntimeAlias' as a second fallback key"
    )


def test_list_sessions_omits_runtime_alias_when_absent(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash())
    sessions = ocmod.OpenClawAdapter().list_sessions(limit=10)
    assert "runtimeAlias" not in sessions[0].extra, (
        "runtimeAlias must be absent when the session record omits it"
    )


def test_list_sessions_surfaces_thinking_mode_true(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash(thinkingMode=True))
    sessions = ocmod.OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("thinkingMode") is True, (
        "list_sessions() must surface thinkingMode=True in Session.extra"
    )


def test_list_sessions_surfaces_thinking_mode_false(monkeypatch):
    """thinkingMode=False must NOT be dropped (thinking disabled is meaningful)."""
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash(thinkingMode=False))
    sessions = ocmod.OpenClawAdapter().list_sessions(limit=10)
    assert "thinkingMode" in sessions[0].extra, (
        "list_sessions() must not drop thinkingMode=False"
    )
    assert sessions[0].extra["thinkingMode"] is False


def test_list_sessions_surfaces_thinking_mode_via_is_thinking_enabled(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash(isThinkingEnabled=True))
    sessions = ocmod.OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("thinkingMode") is True, (
        "list_sessions() must handle 'isThinkingEnabled' as a fallback key"
    )


def test_list_sessions_surfaces_thinking_mode_string(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash(thinkingMode="extended"))
    sessions = ocmod.OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("thinkingMode") == "extended", (
        "list_sessions() must preserve string thinkingMode values unchanged"
    )


def test_list_sessions_omits_thinking_mode_when_absent(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash())
    sessions = ocmod.OpenClawAdapter().list_sessions(limit=10)
    assert "thinkingMode" not in sessions[0].extra, (
        "thinkingMode must be absent when the session record omits it"
    )
