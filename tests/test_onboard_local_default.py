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
        _ns = a[0] if a else None
        state["connect_keep_local"] = bool(getattr(_ns, "keep_local", False))
        state["marker_at_connect"] = marker.exists()
        return None

    monkeypatch.setattr(cli, "_instant_register", _fake_instant_register)
    monkeypatch.setattr(cli, "_cmd_connect", _fake_connect)
    monkeypatch.setattr("webbrowser.open", lambda *a, **k: False)

    def _no_network(*a, **k):
        raise OSError("no network in tests")

    # The signup-trial helper swallows this -> trial becomes a no-op unless a
    # test overrides urlopen with a fake response.
    monkeypatch.setattr("urllib.request.urlopen", _no_network)
    # Local-only finish health-checks + starts the real dashboard; stub it
    # (default: "came up fine") so tests never spawn servers. Tests assert
    # the printed truth by overriding the return value.
    monkeypatch.setattr(cli, "_ensure_local_dashboard",
                        lambda *a, **k: state.__setitem__("dash", state.get("dash", 0) + 1) or True)
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


def test_selfhosted_trial_reaches_connect_keep_local(onboard_env, monkeypatch):
    state, marker = onboard_env
    answers = iter(["1", "n", "y"])  # Self-Hosted -> no key -> yes, trial sign-in
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    cli._cmd_onboard(_args())
    assert state["connect"] == 1, "the trial path must reach the authenticated connect flow"
    assert state.get("connect_keep_local") is True, "connect must run in keep-local mode"
    assert state.get("marker_at_connect") is True, "self-hosted trial keeps the nocloud marker"
    assert state["instant_register"] == 0, "anonymous instant registration must be unreachable"
    # Connect stub wrote no config -> sign-in incomplete -> free-local fallback.
    assert marker.exists() and state["start_daemon"] == 1


def test_selfhosted_trial_declined_is_free_local(onboard_env, monkeypatch, capsys):
    state, marker = onboard_env
    answers = iter(["1", "n", "n"])  # Self-Hosted -> no key -> no trial
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    cli._cmd_onboard(_args())
    assert state["connect"] == 0 and state["instant_register"] == 0
    assert marker.exists() and state["start_daemon"] == 1
    assert "Free plan: OpenClaw + NeMo" in capsys.readouterr().out


def test_empty_enters_default_to_selfhosted_trial_signin(onboard_env, monkeypatch):
    """Enter-Enter-Enter = Self-Hosted -> no key -> trial (founder 2026-07-30):
    the default path signs in, keep-local. A human pressing Enter at visible
    prompts is not a silent mint."""
    state, marker = onboard_env
    monkeypatch.setattr("builtins.input", lambda _p="": "")  # Enter everywhere
    cli._cmd_onboard(_args())
    assert state["connect"] == 1
    assert state.get("connect_keep_local") is True
    assert state["instant_register"] == 0
    assert marker.exists(), "incomplete sign-in must fall back to free local"


def test_selfhosted_key_later_points_at_selfhosted_pricing(onboard_env, monkeypatch, capsys):
    state, marker = onboard_env
    answers = iter(["1", "y", ""])  # Self-Hosted -> have a key -> paste later
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    cli._cmd_onboard(_args())
    out = capsys.readouterr().out
    assert "clawmetry.com/pricing?deploy=self" in out
    assert state["connect"] == 0 and state["instant_register"] == 0
    assert marker.exists() and state["start_daemon"] == 1


def test_choice_1_success_skips_local_fallback(onboard_env, monkeypatch, tmp_path):
    """Connect success (api_key in config) must NOT fall back to local-only.
    (Trial mint + activation happens inside connect itself now — pinned by
    test_activate_signup_trial_* below.)"""
    import json as _json

    state, marker = onboard_env
    home = tmp_path / "home"

    def _connect_writes_config(*a, **k):
        state["connect"] += 1
        (home / ".clawmetry" / "config.json").write_text(
            _json.dumps({"api_key": "cm_fresh_signup", "node_id": "n1"}))

    monkeypatch.setattr(cli, "_cmd_connect", _connect_writes_config)
    monkeypatch.setattr("builtins.input", lambda _p="": "2")
    cli._cmd_onboard(_args())
    assert state["connect"] == 1
    assert not marker.exists(), "successful cloud sign-in clears local-only"
    assert state["start_daemon"] == 0, "connect owns the daemon on this path"


def _trial_env(monkeypatch, tmp_path, response: dict):
    """HOME with a cm_ config + faked trial endpoint + recorded activation."""
    import io
    import json as _json

    home = tmp_path / "home2"
    (home / ".clawmetry").mkdir(parents=True)
    (home / ".clawmetry" / "config.json").write_text(
        _json.dumps({"api_key": "cm_fresh_signup", "node_id": "n1"}))
    monkeypatch.setenv("HOME", str(home))

    posted = {}

    class _FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _fake_urlopen(req, timeout=0):
        posted["url"] = req.full_url
        posted["body"] = _json.loads(req.data.decode())
        return _FakeResp(_json.dumps(response).encode())

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    activated = {}
    import clawmetry.license as _lic
    monkeypatch.setattr(_lic, "activate",
                        lambda key, node_id=None, actor="": activated.__setitem__("key", key) or (True, "ok"))
    monkeypatch.setattr(_lic, "_node_id", lambda: "n1")
    return posted, activated


def test_activate_signup_trial_mints_and_activates(monkeypatch, tmp_path, capsys):
    import time as _t

    posted, activated = _trial_env(monkeypatch, tmp_path, {
        "ok": True, "key": "CLAW1.trial.key", "tier": "trial",
        "expires_at": int(_t.time()) + 7 * 86400,
        "reused": False, "expired": False,
    })
    assert cli._activate_signup_trial() is True
    assert posted["url"].endswith("/api/license/trial/signup")
    assert posted["body"] == {"api_key": "cm_fresh_signup"}
    assert activated.get("key") == "CLAW1.trial.key"
    assert "Pro trial active" in capsys.readouterr().out


def test_activate_signup_trial_expired_is_honest(monkeypatch, tmp_path, capsys):
    import time as _t

    posted, activated = _trial_env(monkeypatch, tmp_path, {
        "ok": True, "key": "CLAW1.trial.key", "tier": "trial",
        "expires_at": int(_t.time()) - 86400,
        "reused": True, "expired": True,
    })
    assert cli._activate_signup_trial() is False
    assert activated == {}, "an expired trial key must never be activated"
    out = capsys.readouterr().out
    assert "trial has ended" in out and "pricing" in out


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


def test_already_connected_shows_two_options_and_shared_plans(onboard_env, monkeypatch, tmp_path, capsys):
    state, marker = onboard_env
    _make_connected(tmp_path / "home")
    answers = iter(["1", "y", ""])  # Self-Hosted -> have key -> later
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    cli._cmd_onboard(_args())
    out = capsys.readouterr().out
    assert "[1] Self-Hosted" in out and "[2] Cloud" in out
    assert "Plans" in out and "Starter $9/node/mo" in out and "Pro    $19/node/mo" in out
    assert out.count("$9") == 1 and out.count("$19") == 1, "plans stated once, not per option"
    assert "watch OpenClaw + NVIDIA NemoClaw" in out
    assert "everything in Free +" in out and "everything in Starter +" in out, "tiers must read as stacked"
    assert marker.exists(), "explicit Self-Hosted reconfigures a connected user to local"


def test_already_connected_choice_2_reaches_connect(onboard_env, monkeypatch, tmp_path):
    state, _marker = onboard_env
    _make_connected(tmp_path / "home")
    monkeypatch.setattr("builtins.input", lambda _p="": "2")
    cli._cmd_onboard(_args())
    assert state["connect"] == 1
    assert state["instant_register"] == 0


# ── local dashboard truth + marker pre-clear (founder report 2026-07-29) ─────
#
# Onboard printed http://localhost:8900 while nothing listened, said "your
# data is syncing to the cloud" on a local-only node, and [1] Sign in was
# re-asked "keep local-only?" by connect's marker prompt.


def test_local_finish_health_checks_dashboard(onboard_env, monkeypatch, capsys):
    state, marker = onboard_env
    cli._cmd_onboard(_args(local=True))
    assert state.get("dash") == 1, "local finish must health-check/start the dashboard"
    out = capsys.readouterr().out
    assert "http://localhost:8900" in out and "live now" in out


def test_local_finish_admits_when_dashboard_is_down(onboard_env, monkeypatch, capsys):
    state, marker = onboard_env
    monkeypatch.setattr(cli, "_ensure_local_dashboard", lambda *a, **k: False)
    cli._cmd_onboard(_args(local=True))
    out = capsys.readouterr().out
    assert "did not come up" in out, "a dead port must never be presented as a live URL"
    assert "dashboard.log" in out


def test_cloud_choice_clears_marker_before_connect(onboard_env, monkeypatch):
    """[2] Cloud must not be re-asked 'keep local-only?': the marker is
    cleared before connect runs (an incomplete sign-in re-writes it)."""
    state, marker = onboard_env
    marker.write_text("")
    monkeypatch.setattr("builtins.input", lambda _p="": "2")
    cli._cmd_onboard(_args())
    assert state["connect"] == 1
    assert state.get("marker_at_connect") is False
    assert not state.get("connect_keep_local")
    assert marker.exists(), "failed sign-in must restore the local-only marker"


def test_daemon_mode_line_is_truthful():
    assert "Nothing leaves this machine" in cli._daemon_mode_line({"local_only": True})
    line = cli._daemon_mode_line({"api_key": "cm_x", "local_only": False})
    # Cloud copy only when the nocloud marker is absent too; both variants
    # are legitimate here depending on the test host's marker state.
    assert ("syncing to the cloud" in line) or ("Nothing leaves this machine" in line)


def test_daemon_mode_line_cloud_when_marker_absent(monkeypatch, tmp_path):
    monkeypatch.setattr("clawmetry.config.NOCLOUD_MARKER_PATH", str(tmp_path / "nope"))
    assert "syncing to the cloud" in cli._daemon_mode_line({"api_key": "cm_x"})


def test_ensure_local_dashboard_true_when_already_serving(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: object())
    spawned = []
    monkeypatch.setattr("subprocess.Popen", lambda *a, **k: spawned.append(a))
    assert cli._ensure_local_dashboard() is True
    assert spawned == [], "an already-serving port must not spawn anything"


def test_ensure_local_dashboard_spawns_then_polls(monkeypatch):
    """Silent port -> start (subprocess fallback branch) -> poll flips alive."""
    calls = {"n": 0}

    def _urlopen(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("refused")
        return object()

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    monkeypatch.setattr("platform.system", lambda: "OtherOS")
    spawned = []
    monkeypatch.setattr("subprocess.Popen", lambda cmd, **k: spawned.append(cmd) or object())
    monkeypatch.setattr("time.sleep", lambda *_: None)
    assert cli._ensure_local_dashboard(wait_secs=2) is True
    assert len(spawned) == 1
    assert "--port" in spawned[0] and "8900" in spawned[0]
