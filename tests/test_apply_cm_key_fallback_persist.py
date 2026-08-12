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
