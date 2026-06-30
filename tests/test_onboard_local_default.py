"""Install-fork: onboard must NEVER silently mint a cloud account.

The pre-fork onboard defaulted a no-account / EOF answer to _instant_register,
so a headless `curl | bash` (no /dev/tty) silently created a cloud account.
That is exactly the surprise-account complaint that triggered a GDPR deletion.

These tests pin the new 3-way fork (default = local):
  * no-TTY / EOF  -> local only, marker written, _instant_register NOT called
  * --local flag  -> local only (no prompt read)
  * CLAWMETRY_LOCAL_ONLY=1 env -> local only
  * choosing [2]  -> cloud registration IS reached
"""
import argparse
import os

import pytest

import clawmetry.cli as cli


@pytest.fixture
def onboard_env(monkeypatch, tmp_path):
    """Isolate HOME + the nocloud marker, stub all side-effecting calls, and
    record whether cloud registration was attempted."""
    home = tmp_path / "home"
    (home / ".clawmetry").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CLAWMETRY_API_KEY", raising=False)
    monkeypatch.delenv("CLAWMETRY_NODE_ID", raising=False)
    monkeypatch.delenv("CLAWMETRY_LOCAL_ONLY", raising=False)

    marker = home / ".clawmetry" / "nocloud"
    monkeypatch.setattr("clawmetry.config.NOCLOUD_MARKER_PATH", str(marker))

    state = {"instant_register": 0, "start_daemon": 0}

    def _fake_instant_register(*a, **k):
        state["instant_register"] += 1
        return None  # registration "fails" -> harmless local fallback

    monkeypatch.setattr(cli, "_instant_register", _fake_instant_register)
    monkeypatch.setattr(cli, "_start_daemon", lambda *a, **k: state.__setitem__("start_daemon", state["start_daemon"] + 1))
    monkeypatch.setattr(cli, "_stop_existing_daemon", lambda *a, **k: None)
    monkeypatch.setattr(cli, "_maybe_apply_nemoclaw_preset", lambda *a, **k: None)
    monkeypatch.setattr("clawmetry.sync.save_config", lambda *a, **k: None)
    # Make stdin look like a TTY so onboard uses input() (which we control)
    # instead of opening /dev/tty.
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    return state, marker


def _args(**kw):
    base = dict(local=False, cloud=False, foreground=False, custom_node_id=None)
    base.update(kw)
    return argparse.Namespace(**base)


def test_eof_defaults_to_local_never_mints(onboard_env, monkeypatch):
    state, marker = onboard_env

    def _eof(_prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", _eof)
    cli._cmd_onboard(_args())

    assert state["instant_register"] == 0, "headless onboard must NOT create a cloud account"
    assert marker.exists(), "local-only marker must be written"
    assert state["start_daemon"] == 1, "local daemon should still start"


def test_local_flag_forces_local(onboard_env, monkeypatch):
    state, marker = onboard_env
    # Should never read input when --local is set.
    monkeypatch.setattr("builtins.input", lambda _p="": pytest.fail("should not prompt"))
    cli._cmd_onboard(_args(local=True))
    assert state["instant_register"] == 0
    assert marker.exists()


def test_env_local_only_forces_local(onboard_env, monkeypatch):
    state, marker = onboard_env
    monkeypatch.setenv("CLAWMETRY_LOCAL_ONLY", "1")
    monkeypatch.setattr("builtins.input", lambda _p="": pytest.fail("should not prompt"))
    cli._cmd_onboard(_args())
    assert state["instant_register"] == 0
    assert marker.exists()


def test_choice_2_reaches_cloud_registration(onboard_env, monkeypatch):
    state, _marker = onboard_env
    answers = iter(["2", "n"])  # [2] Cloud, then "no existing account" -> instant register

    def _ans(_prompt=""):
        return next(answers)

    monkeypatch.setattr("builtins.input", _ans)
    cli._cmd_onboard(_args())
    assert state["instant_register"] == 1, "[2] Cloud must reach instant registration"


def test_empty_enter_defaults_to_local(onboard_env, monkeypatch):
    state, marker = onboard_env
    monkeypatch.setattr("builtins.input", lambda _p="": "")  # just press Enter
    cli._cmd_onboard(_args())
    assert state["instant_register"] == 0
    assert marker.exists()


# ── `clawmetry onboard` always shows the options (founder ask 2026-06-30) ────

def _make_connected(home):
    """Write a config that looks already-connected (has an api_key)."""
    import json
    (home / ".clawmetry").mkdir(parents=True, exist_ok=True)
    (home / ".clawmetry" / "config.json").write_text(
        json.dumps({"api_key": "cm_existing", "node_id": "n1"}))


def test_already_connected_empty_enter_keeps_current(onboard_env, monkeypatch, tmp_path):
    state, marker = onboard_env
    _make_connected(tmp_path / "home")
    # Empty Enter while already connected -> keep current, change nothing.
    monkeypatch.setattr("builtins.input", lambda _p="": "")
    cli._cmd_onboard(_args())
    assert state["instant_register"] == 0
    assert state["start_daemon"] == 0
    assert not marker.exists(), "must NOT switch a connected user to local on empty Enter"


def test_already_connected_shows_options_and_choice_1_goes_local(onboard_env, monkeypatch, tmp_path, capsys):
    state, marker = onboard_env
    _make_connected(tmp_path / "home")
    monkeypatch.setattr("builtins.input", lambda _p="": "1")
    cli._cmd_onboard(_args())
    out = capsys.readouterr().out
    assert "[1] Local only" in out and "[2] Cloud" in out and "[3] License key" in out
    assert marker.exists(), "explicit [1] reconfigures a connected user to local"


def test_already_connected_choice_2_reaches_cloud(onboard_env, monkeypatch, tmp_path):
    state, _marker = onboard_env
    _make_connected(tmp_path / "home")
    answers = iter(["2", "n"])  # [2] Cloud, then "no existing account" -> instant register
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    cli._cmd_onboard(_args())
    assert state["instant_register"] == 1
