"""Guard: apply_cm_key persists the cm_ key locally even when the
``clawmetry connect`` subprocess fails.

Bug pinned here (founder live-hit 2026-08-12): user completed OTP in
the desktop shell's own onboarding pane, ``verify_email_otp`` minted a
real cm_ key, and ``apply_cm_key`` then shelled out to
``clawmetry connect --key cm_… --start-sync-now``. For a downstream
reason (daemon start, launchctl denial, Pro-wheel provisioning network
hiccup, an interactive ownership prompt hanging the non-interactive
subprocess) the subprocess exited non-zero. The old shell:
  * marked the stamp ``signed_in=False, mode=""`` (based on ok_key)
  * never wrote the cm_ key anywhere on disk
  * bounced the user to the dashboard, whose onboarding gate then
    re-prompted the SAME "cloud vs self-host" modal on every relaunch.

The fix: even when the subprocess fails, persist the key at the same
location ``dashboard._write_cloud_token`` uses
(``~/.openclaw/openclaw.json → clawmetry.cloudToken``). That path is
what ``dashboard._read_cloud_token`` / ``_cloud_connected`` / the
cloud-cta status route inspect — so the dashboard flips to "connected"
and the onboarding gate stops re-prompting.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from desktop import onboarding as desk_onb  # noqa: E402


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect ``~`` so we don't touch the developer's real config."""
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


def _openclaw_token(fake_home: Path) -> str:
    p = fake_home / ".openclaw" / "openclaw.json"
    if not p.exists():
        return ""
    try:
        data = json.loads(p.read_text())
    except (ValueError, OSError):
        return ""
    return ((data.get("clawmetry") or {}).get("cloudToken") or "")


# ---------------------------------------------------------------------------
# _fallback_persist_cm_key: pure I/O contract
# ---------------------------------------------------------------------------


def test_fallback_writes_token_to_openclaw_sidecar(fake_home):
    ok = desk_onb._fallback_persist_cm_key("cm_abc123")
    assert ok is True
    assert _openclaw_token(fake_home) == "cm_abc123"


def test_fallback_rejects_non_cm_key(fake_home):
    assert desk_onb._fallback_persist_cm_key("") is False
    assert desk_onb._fallback_persist_cm_key("not-a-cm-key") is False
    # And no file is written when the key is rejected.
    assert not (fake_home / ".openclaw" / "openclaw.json").exists()


def test_fallback_preserves_existing_openclaw_json(fake_home):
    """We must not clobber the user's OpenClaw config — only touch the
    ``clawmetry.cloudToken`` sub-key. This mirrors how
    ``dashboard._write_cloud_token`` handles the same file."""
    oc = fake_home / ".openclaw" / "openclaw.json"
    oc.parent.mkdir(parents=True, exist_ok=True)
    oc.write_text(json.dumps({
        "tools": {"exec": {"host": "gateway"}},
        "meta": {"lastTouchedVersion": "2026.7.1"},
    }))

    desk_onb._fallback_persist_cm_key("cm_xyz789")

    data = json.loads(oc.read_text())
    assert data["clawmetry"]["cloudToken"] == "cm_xyz789"
    assert data["tools"]["exec"]["host"] == "gateway", (
        "fallback must be a merge, not a replace — losing the OpenClaw "
        "tools/meta config would break OpenClaw itself."
    )
    assert data["meta"]["lastTouchedVersion"] == "2026.7.1"


def test_fallback_merges_with_existing_clawmetry_block(fake_home):
    oc = fake_home / ".openclaw" / "openclaw.json"
    oc.parent.mkdir(parents=True, exist_ok=True)
    oc.write_text(json.dumps({
        "clawmetry": {"gatewayToken": "gw_existing"},
    }))

    desk_onb._fallback_persist_cm_key("cm_new_key")

    data = json.loads(oc.read_text())
    assert data["clawmetry"]["cloudToken"] == "cm_new_key"
    assert data["clawmetry"]["gatewayToken"] == "gw_existing", (
        "Existing sibling keys under clawmetry must survive — a bare "
        "assignment would wipe gatewayToken and break gateway auth."
    )


def test_fallback_handles_corrupt_openclaw_json(fake_home):
    """A malformed openclaw.json shouldn't take down the fallback path
    — we're on a failing branch already, we cannot compound the failure.
    Rewrite it clean so the token lands."""
    oc = fake_home / ".openclaw" / "openclaw.json"
    oc.parent.mkdir(parents=True, exist_ok=True)
    oc.write_text("{not valid json")

    ok = desk_onb._fallback_persist_cm_key("cm_recover")

    assert ok is True
    data = json.loads(oc.read_text())
    assert data["clawmetry"]["cloudToken"] == "cm_recover"


def test_fallback_never_raises_on_oserror(fake_home, monkeypatch):
    """Home path unwriteable? Return False, don't raise. The onboarding
    stamp path will still get the recovery message from apply_cm_key."""
    # Make ~/.openclaw exist as a FILE where the fallback expects a dir.
    # openclaw.json.parent.mkdir(parents=True, exist_ok=True) then fails.
    (fake_home / ".openclaw").write_text("blocking")

    # Must not raise.
    ok = desk_onb._fallback_persist_cm_key("cm_noraise")
    assert ok is False


# ---------------------------------------------------------------------------
# apply_cm_key: subprocess failure → fallback still persists the key
# ---------------------------------------------------------------------------


class _FakeCompleted:
    def __init__(self, rc, stdout="", stderr=""):
        self.returncode = rc
        self.stdout = stdout
        self.stderr = stderr


def test_apply_cm_key_success_does_not_double_write(fake_home, tmp_path, monkeypatch):
    """On the happy path, the CLI's own connect command writes the
    config; the fallback should not fire (avoids racing the CLI)."""
    venv_bin = tmp_path / "clawmetry"
    venv_bin.write_text("#!/bin/sh\n")
    venv_bin.chmod(0o755)

    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **kw: _FakeCompleted(0, "ok", ""))
    called = []
    monkeypatch.setattr(desk_onb, "_fallback_persist_cm_key",
                        lambda k: called.append(k) or True)

    ok, msg = desk_onb.apply_cm_key(venv_bin, "cm_success", mode="cloud")

    assert ok is True
    assert msg == "signed in"
    assert called == [], (
        "Happy path must NOT invoke the fallback — the CLI's own connect "
        "flow has already written config.json + started the daemon."
    )


def test_apply_cm_key_subprocess_failure_persists_key(fake_home, tmp_path, monkeypatch):
    """The regression this whole PR is about: subprocess fails (any
    downstream reason), key must still be persisted locally, dashboard
    must see the machine as paired."""
    venv_bin = tmp_path / "clawmetry"
    venv_bin.write_text("#!/bin/sh\n")
    venv_bin.chmod(0o755)

    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **kw: _FakeCompleted(1, "", "launchctl: denied"))

    ok, msg = desk_onb.apply_cm_key(venv_bin, "cm_realkey", mode="cloud")

    assert ok is False
    assert "launchctl" in msg
    assert _openclaw_token(fake_home) == "cm_realkey", (
        "Subprocess failed but the key is real (OTP minted it moments "
        "ago). Without this write the dashboard's onboarding gate "
        "re-prompts on every relaunch (founder report 2026-08-12)."
    )


def test_apply_cm_key_timeout_persists_key(fake_home, tmp_path, monkeypatch):
    venv_bin = tmp_path / "clawmetry"
    venv_bin.write_text("#!/bin/sh\n")
    venv_bin.chmod(0o755)

    def _boom(*a, **kw):
        raise subprocess.TimeoutExpired(cmd=a[0], timeout=60)
    monkeypatch.setattr(subprocess, "run", _boom)

    ok, msg = desk_onb.apply_cm_key(venv_bin, "cm_timeout", mode="cloud")

    assert ok is False
    assert "timed out" in msg
    assert _openclaw_token(fake_home) == "cm_timeout"


def test_apply_cm_key_generic_exception_persists_key(fake_home, tmp_path, monkeypatch):
    venv_bin = tmp_path / "clawmetry"
    venv_bin.write_text("#!/bin/sh\n")
    venv_bin.chmod(0o755)

    def _boom(*a, **kw):
        raise RuntimeError("connection refused")
    monkeypatch.setattr(subprocess, "run", _boom)

    ok, msg = desk_onb.apply_cm_key(venv_bin, "cm_exc", mode="cloud")

    assert ok is False
    assert "sign-in error" in msg
    assert _openclaw_token(fake_home) == "cm_exc"


def test_apply_cm_key_missing_venv_persists_key(fake_home, tmp_path):
    """Even the earliest bail (venv not ready) should still record the
    key — the user's identity IS real; we just can't run connect yet."""
    ok, msg = desk_onb.apply_cm_key(
        tmp_path / "does-not-exist", "cm_earlybail", mode="cloud",
    )
    assert ok is False
    assert "venv is not ready" in msg
    assert _openclaw_token(fake_home) == "cm_earlybail"


def test_apply_cm_key_selfhost_failure_also_persists(fake_home, tmp_path, monkeypatch):
    """Self-host mode has the same failure surface — subprocess exit
    non-zero means the machine's local trial pack didn't provision, but
    identity is still real. Persist so the dashboard doesn't re-prompt."""
    venv_bin = tmp_path / "clawmetry"
    venv_bin.write_text("#!/bin/sh\n")
    venv_bin.chmod(0o755)

    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **kw: _FakeCompleted(2, "", "trial mint failed"))

    ok, msg = desk_onb.apply_cm_key(venv_bin, "cm_selfhost", mode="selfhost")

    assert ok is False
    assert _openclaw_token(fake_home) == "cm_selfhost"


# ─── Trial mint on the fallback path (founder ask 2026-08-13) ────────────
# The subprocess fallback used to just persist the cm_ key. That left the
# dashboard reporting "Cloud Connected" but the account on FREE with no
# trial, because _activate_signup_trial only runs inside the (crashed)
# `clawmetry connect` subprocess. The fallback must now ALSO mint the
# trial directly via /api/license/trial/signup.


def test_fallback_mints_trial_after_subprocess_failure(fake_home, monkeypatch):
    """When the connect subprocess fails, the fallback must also POST to
    /api/license/trial/signup so the user actually gets the trial they
    just signed up for. Regression guard for founder report 2026-08-13:
    dashboard showed Cloud Connected but Plan stayed Free because the
    subprocess crashed on an EOFError before reaching
    _activate_signup_trial."""
    posted = {}

    class _FakeResp:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return json.dumps({"ok": True, "key": "LIC_test",
                               "expires_at": 9999999999}).encode()

    def _fake_urlopen(req, timeout=15, context=None):
        posted["url"] = req.full_url
        posted["body"] = json.loads(req.data.decode())
        return _FakeResp()

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    monkeypatch.setattr(desk_onb, "_ssl_context", lambda: None)

    # activate() writes ~/.clawmetry/license — capture the call
    activated = {}
    class _FakeLic:
        @staticmethod
        def activate(key, node_id=None):
            activated["key"] = key
            activated["node_id"] = node_id
            return True, "ok"
        @staticmethod
        def _node_id():
            return "test-node"
    monkeypatch.setitem(sys.modules, "clawmetry.license", _FakeLic)

    ok = desk_onb._fallback_persist_cm_key("cm_founder_trial")

    assert ok is True
    assert posted.get("body", {}).get("api_key") == "cm_founder_trial", (
        "_fallback_persist_cm_key must POST the cm_ key to "
        "/api/license/trial/signup — otherwise cloud users hit "
        "subprocess failures land on FREE with no trial"
    )
    assert "/api/license/trial/signup" in posted.get("url", "")
    assert activated.get("key") == "LIC_test", (
        "returned license key must be activated locally via "
        "clawmetry.license.activate — otherwise the license file is "
        "never written and `clawmetry status` still says Free"
    )


def test_fallback_trial_mint_never_raises_on_network_error(fake_home, monkeypatch):
    """Trial mint is best-effort — network failures must not break
    pairing. The cm_ key is already saved; the trial can retry later."""
    def _fake_urlopen(*a, **kw):
        raise OSError("network unreachable")
    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    ok = desk_onb._fallback_persist_cm_key("cm_offline_test")

    assert ok is True, "network failure must not undo the pairing"
    assert _openclaw_token(fake_home) == "cm_offline_test"


def test_fallback_trial_mint_swallows_activate_errors(fake_home, monkeypatch):
    """A broken clawmetry.license import must not abort the pairing —
    this fallback runs precisely because the venv might be busted."""
    class _FakeResp:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return json.dumps({"ok": True, "key": "LIC_x"}).encode()

    monkeypatch.setattr("urllib.request.urlopen",
                        lambda *a, **kw: _FakeResp())
    monkeypatch.setattr(desk_onb, "_ssl_context", lambda: None)

    class _BrokenLic:
        @staticmethod
        def activate(*a, **kw):
            raise RuntimeError("boom")
        @staticmethod
        def _node_id():
            return "n"
    monkeypatch.setitem(sys.modules, "clawmetry.license", _BrokenLic)

    ok = desk_onb._fallback_persist_cm_key("cm_broken_venv")

    assert ok is True


def test_fallback_trial_mint_swallows_server_no_key(fake_home, monkeypatch):
    """Server returns ok:false or omits key → don't try to activate."""
    class _FakeResp:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return json.dumps({"ok": False, "error": "unknown"}).encode()

    monkeypatch.setattr("urllib.request.urlopen",
                        lambda *a, **kw: _FakeResp())
    monkeypatch.setattr(desk_onb, "_ssl_context", lambda: None)

    activate_calls = []
    class _NoLic:
        @staticmethod
        def activate(*a, **kw):
            activate_calls.append(a)
            return True, ""
    monkeypatch.setitem(sys.modules, "clawmetry.license", _NoLic)

    ok = desk_onb._fallback_persist_cm_key("cm_bad_signup")

    assert ok is True
    assert activate_calls == [], (
        "must not activate when server returned no key"
    )


# ─── cli.py: --start-sync-now / non-TTY stdin must skip input() ──────────
# The interactive encryption-key prompt raised EOFError inside the desktop
# pane's non-interactive subprocess, killing `clawmetry connect` before
# _activate_signup_trial could run. --start-sync-now (and any non-TTY
# invocation) must now auto-select a key silently.


def test_connect_start_sync_now_skips_interactive_enc_key_prompt():
    """The specific EOFError → founder-on-Free path. Verifies via source
    inspection that the non-interactive branches never call _input for
    the encryption key. A previous behavior test would be too coupled
    to _cmd_connect's many pre-conditions to run in-process; the source
    guard is what durably prevents the regression."""
    import inspect

    from clawmetry import cli
    src = inspect.getsource(cli._cmd_connect)

    # The guard variable must exist and be composed of exactly the
    # three signals we settled on. Change the assertion when you
    # intentionally widen or narrow the trigger.
    assert '_non_interactive = (' in src, (
        "_cmd_connect must gate enc-key prompts on a _non_interactive "
        "flag — apply_cm_key subprocesses have no TTY and input() "
        "raises EOFError otherwise (founder 2026-08-13)"
    )
    assert 'getattr(args, "start_sync_now"' in src
    assert '_keep_local_signin' in src
    assert 'sys.stdin.isatty()' in src

    # Each of the three branches that used to unconditionally prompt
    # (_kc_key, _saved_enc_key, no-key-at-all) must now have an
    # `if _non_interactive:` guard. Count them.
    assert src.count('if _non_interactive:') == 3, (
        f"expected 3 `if _non_interactive:` guards (one per enc-key "
        f"branch that previously always prompted); found "
        f"{src.count('if _non_interactive:')}. Missing a guard means "
        "some non-interactive callers still crash on EOFError."
    )


def test_connect_non_interactive_when_stdin_not_a_tty():
    """The trigger must fire on ANY non-TTY stdin, not just the flags —
    a user redirecting `echo | clawmetry connect ...` shouldn't hang
    either. Belt+braces beyond --start-sync-now."""
    import inspect
    from clawmetry import cli
    src = inspect.getsource(cli._cmd_connect)

    # sys.stdin.isatty() must be part of the OR chain, not just any
    # mention elsewhere in the function. Walk the parens to find the
    # true closing `)` of `_non_interactive = (...)`.
    start = src.index('_non_interactive = (')
    depth = 0
    end = None
    for i in range(start + len('_non_interactive = '), len(src)):
        if src[i] == '(':
            depth += 1
        elif src[i] == ')':
            depth -= 1
            if depth == 0:
                end = i
                break
    assert end is not None, "malformed _non_interactive assignment"
    ni_block = src[start:end + 1]
    assert 'not sys.stdin.isatty()' in ni_block, (
        "non-interactive gate must also fire when stdin isn't a TTY, "
        "so piped/redirected invocations don't crash on input()"
    )
