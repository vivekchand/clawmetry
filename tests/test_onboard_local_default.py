"""Install-fork: onboard must NEVER silently mint a cloud account.

The pre-fork onboard defaulted a no-account / EOF answer to _instant_register,
so a headless `curl | bash` (no /dev/tty) silently created a cloud account.
That is exactly the surprise-account complaint that triggered a GDPR deletion.

These tests pin the sign-in-first fork (founder, 2026-07-29). "Silently" is
the load-bearing word: the interactive default keypress is now [1] Sign in
(a human pressing Enter at a visible menu), but every NON-interactive path
stays account-free:
  * no-TTY / EOF  -> local only, marker written, no account flow reached
  * --local flag / CLAWMETRY_LOCAL_ONLY=1 -> local only (no prompt read)
  * [1] / Enter   -> the AUTHENTICATED connect flow (never _instant_register;
                     anonymous instant registration is no longer reachable
                     from onboard) and, on success, the 7-day trial license
  * [2]           -> license key (have/need fork)
  * [3]           -> local only
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

    state = {"instant_register": 0, "start_daemon": 0, "connect": 0}

    def _fake_instant_register(*a, **k):
        state["instant_register"] += 1
        return None  # registration "fails" -> harmless local fallback

    def _fake_connect(*a, **k):
        # Default stub: sign-in attempted but NOT completed (no config
        # written) -> onboard must fall back to local. Tests that need a
        # successful sign-in override this with a config-writing stub.
        state["connect"] += 1
        return None

    monkeypatch.setattr(cli, "_instant_register", _fake_instant_register)
    monkeypatch.setattr(cli, "_cmd_connect", _fake_connect)
    monkeypatch.setattr("webbrowser.open", lambda *a, **k: False)

    def _no_network(*a, **k):
        raise OSError("no network in tests")

    # The signup-trial helper swallows this -> trial becomes a no-op unless a
    # test overrides urlopen with a fake response.
    monkeypatch.setattr("urllib.request.urlopen", _no_network)
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


def test_choice_1_reaches_authenticated_connect(onboard_env, monkeypatch):
    state, marker = onboard_env
    monkeypatch.setattr("builtins.input", lambda _p="": "1")
    cli._cmd_onboard(_args())
    assert state["connect"] == 1, "[1] Sign in must reach the authenticated connect flow"
    assert state["instant_register"] == 0, "anonymous instant registration must be unreachable"
    # Connect stub wrote no config -> sign-in incomplete -> local fallback.
    assert marker.exists() and state["start_daemon"] == 1


def test_empty_enter_defaults_to_sign_in(onboard_env, monkeypatch):
    """The interactive default keypress is [1] Sign in (founder 2026-07-29).
    A human pressing Enter at the visible menu is not a silent mint."""
    state, marker = onboard_env
    monkeypatch.setattr("builtins.input", lambda _p="": "")  # just press Enter
    cli._cmd_onboard(_args())
    assert state["connect"] == 1
    assert state["instant_register"] == 0
    assert marker.exists(), "incomplete sign-in must fall back to local"


def test_choice_2_no_key_points_at_selfhosted_pricing(onboard_env, monkeypatch, capsys):
    state, marker = onboard_env
    opened = []
    monkeypatch.setattr("webbrowser.open", lambda url, *a, **k: opened.append(url) or True)
    answers = iter(["2", "n"])  # [2] License key, then "don't have one yet"
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    cli._cmd_onboard(_args())
    out = capsys.readouterr().out
    assert "clawmetry.com/pricing?deploy=self" in out
    assert opened == ["https://clawmetry.com/pricing?deploy=self"]
    assert state["connect"] == 0 and state["instant_register"] == 0
    assert marker.exists() and state["start_daemon"] == 1


def test_choice_1_success_activates_signup_trial(onboard_env, monkeypatch, tmp_path, capsys):
    """Connect success (api_key in config) must fetch the signup trial and
    activate the returned key locally."""
    import io
    import json as _json

    state, marker = onboard_env
    home = tmp_path / "home"

    def _connect_writes_config(*a, **k):
        state["connect"] += 1
        (home / ".clawmetry" / "config.json").write_text(
            _json.dumps({"api_key": "cm_fresh_signup", "node_id": "n1"}))

    monkeypatch.setattr(cli, "_cmd_connect", _connect_writes_config)

    posted = {}

    class _FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _fake_urlopen(req, timeout=0):
        posted["url"] = req.full_url
        posted["body"] = _json.loads(req.data.decode())
        import time as _t
        return _FakeResp(_json.dumps({
            "ok": True, "key": "CLAW1.trial.key", "tier": "trial",
            "expires_at": int(_t.time()) + 7 * 86400,
            "reused": False, "expired": False,
        }).encode())

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    activated = {}
    import clawmetry.license as _lic
    monkeypatch.setattr(_lic, "activate",
                        lambda key, node_id=None, actor="": activated.__setitem__("key", key) or (True, "ok"))
    monkeypatch.setattr(_lic, "_node_id", lambda: "n1")

    monkeypatch.setattr("builtins.input", lambda _p="": "1")
    cli._cmd_onboard(_args())

    assert posted["url"].endswith("/api/license/trial/signup")
    assert posted["body"] == {"api_key": "cm_fresh_signup"}
    assert activated.get("key") == "CLAW1.trial.key"
    out = capsys.readouterr().out
    assert "Pro trial active" in out
    assert not marker.exists(), "successful sign-in is a cloud setup, not local-only"


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


def test_already_connected_shows_options_and_choice_3_goes_local(onboard_env, monkeypatch, tmp_path, capsys):
    state, marker = onboard_env
    _make_connected(tmp_path / "home")
    monkeypatch.setattr("builtins.input", lambda _p="": "3")
    cli._cmd_onboard(_args())
    out = capsys.readouterr().out
    assert "[1] Sign in / Sign up" in out and "[2] License key" in out and "[3] Skip for now" in out
    assert marker.exists(), "explicit [3] reconfigures a connected user to local"


def test_already_connected_choice_1_reaches_connect(onboard_env, monkeypatch, tmp_path):
    state, _marker = onboard_env
    _make_connected(tmp_path / "home")
    monkeypatch.setattr("builtins.input", lambda _p="": "1")
    cli._cmd_onboard(_args())
    assert state["connect"] == 1
    assert state["instant_register"] == 0
