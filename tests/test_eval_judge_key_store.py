"""Judge API key can be set from the dashboard (local store), enabling evals
without an env var. The key lives chmod 600 on disk only, never echoed/synced.
"""
import os
import stat

import clawmetry.eval_runner as er


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(er, "_EVAL_KEYS_PATH", str(tmp_path / "eval_keys.json"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_save_present_resolve_and_clear(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert er.judge_keys_present() == {"anthropic": False, "openai": False}

    er.save_judge_key("anthropic", "sk-ant-secret123")
    assert er.judge_keys_present()["anthropic"] is True
    assert er._judge_api_key("claude-haiku-4-5") == "sk-ant-secret123"
    assert er._judge_key_present("claude-haiku-4-5") is True
    # gpt model has no key yet
    assert er._judge_key_present("gpt-4o-mini") is False

    er.save_judge_key("anthropic", "")  # clear
    assert er.judge_keys_present()["anthropic"] is False


def test_key_file_is_chmod_600(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    er.save_judge_key("openai", "sk-openai-xyz")
    mode = stat.S_IMODE(os.stat(er._EVAL_KEYS_PATH).st_mode)
    assert mode == 0o600, oct(mode)


def test_env_takes_precedence_over_stored(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    er.save_judge_key("anthropic", "sk-ant-stored")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fromenv")
    assert er._judge_api_key("claude-haiku-4-5") == "sk-ant-fromenv"


def test_unknown_provider_rejected(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    try:
        er.save_judge_key("googlegemini", "x")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_presence_never_leaks_value(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    er.save_judge_key("anthropic", "sk-ant-topsecret")
    present = er.judge_keys_present()
    assert "sk-ant-topsecret" not in str(present)
    assert present == {"anthropic": True, "openai": False}
