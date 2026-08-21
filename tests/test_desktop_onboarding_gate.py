"""Guards for the desktop onboarding/auth gate.

Bugs pinned here (founder report 2026-08-10: a fresh install landed on the
signed-in dashboard without any login):

* the onboarding stamp was a pure existence check — a corrupt stamp, or one
  recording ``signed_in=False``, still suppressed the pane forever;
* startup never re-validated stored credentials against the cloud;
* a walk-away timeout (5 min) permanently stamped onboarding completed;
* a FAILED ``clawmetry connect`` still stamped completed;
* the single-instance guard attached to any running daemon with zero
  onboarding check.
"""

from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from desktop import onboarding  # noqa: E402


# ── stamp semantics ───────────────────────────────────────────────────────

def test_missing_stamp_is_first_launch(tmp_path):
    assert onboarding.read_stamp(tmp_path) is None
    assert onboarding.is_first_launch(tmp_path) is True


def test_valid_stamp_suppresses_onboarding(tmp_path):
    onboarding.mark_onboarding_completed(
        tmp_path, signed_in=True, provider="github", email="a@b.c",
    )
    stamp = onboarding.read_stamp(tmp_path)
    assert stamp and stamp["signed_in"] is True and stamp["provider"] == "github"
    assert onboarding.is_first_launch(tmp_path) is False


def test_corrupt_stamp_fails_toward_showing_the_pane(tmp_path):
    # Truncated/garbage stamps must re-onboard, never silently skip.
    (tmp_path / onboarding.ONBOARDING_STAMP_NAME).write_text('{"comp')
    assert onboarding.read_stamp(tmp_path) is None
    assert onboarding.is_first_launch(tmp_path) is True

    (tmp_path / onboarding.ONBOARDING_STAMP_NAME).write_text('[1,2,3]')
    assert onboarding.is_first_launch(tmp_path) is True


def test_stamp_write_is_atomic(tmp_path):
    onboarding.mark_onboarding_completed(tmp_path, signed_in=False)
    # No temp file left behind, and the stamp parses.
    leftovers = [p.name for p in tmp_path.iterdir()]
    assert leftovers == [onboarding.ONBOARDING_STAMP_NAME]


def test_clear_onboarding_stamp(tmp_path):
    onboarding.mark_onboarding_completed(tmp_path, signed_in=True)
    onboarding.clear_onboarding_stamp(tmp_path)
    assert onboarding.is_first_launch(tmp_path) is True
    onboarding.clear_onboarding_stamp(tmp_path)  # idempotent, never raises


# ── stored-credentials re-validation ──────────────────────────────────────

def _fake_home(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.delenv("CLAWMETRY_NO_CLOUD", raising=False)
    return tmp_path


def test_credentials_absent_when_no_files(tmp_path, monkeypatch):
    _fake_home(monkeypatch, tmp_path)
    assert onboarding.stored_credentials_state() == "absent"


def test_credentials_absent_ignores_non_cm_keys(tmp_path, monkeypatch):
    home = _fake_home(monkeypatch, tmp_path)
    (home / ".clawmetry").mkdir()
    (home / ".clawmetry" / "config.json").write_text(json.dumps({"api_key": "bogus"}))
    assert onboarding.stored_credentials_state() == "absent"


def test_selfhost_nocloud_marker_skips_cloud_validation(tmp_path, monkeypatch):
    home = _fake_home(monkeypatch, tmp_path)
    (home / ".clawmetry").mkdir()
    (home / ".clawmetry" / "config.json").write_text(json.dumps({"api_key": "cm_x"}))
    (home / ".clawmetry" / "nocloud").write_text("")

    def _boom(*a, **k):  # the cloud must never be called
        raise AssertionError("self-host install must not phone home")

    monkeypatch.setattr(onboarding.urllib.request, "urlopen", _boom)
    assert onboarding.stored_credentials_state() == "valid"


def _resp(status):
    class _R(io.BytesIO):
        def __init__(self):
            super().__init__(b"{}")
            self.status = status

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    return _R()


def test_rejected_key_is_invalid(tmp_path, monkeypatch):
    home = _fake_home(monkeypatch, tmp_path)
    (home / ".openclaw").mkdir()
    (home / ".openclaw" / "openclaw.json").write_text(
        json.dumps({"clawmetry": {"cloudToken": "cm_revoked"}})
    )

    def _reject(url, timeout=0):
        raise urllib.error.HTTPError(url, 401, "unauthorized", {}, io.BytesIO(b""))

    monkeypatch.setattr(onboarding.urllib.request, "urlopen", _reject)
    assert onboarding.stored_credentials_state() == "invalid"


def test_accepted_key_is_valid(tmp_path, monkeypatch):
    home = _fake_home(monkeypatch, tmp_path)
    (home / ".clawmetry").mkdir()
    (home / ".clawmetry" / "config.json").write_text(json.dumps({"api_key": "cm_ok"}))
    monkeypatch.setattr(
        onboarding.urllib.request, "urlopen", lambda url, timeout=0: _resp(200)
    )
    assert onboarding.stored_credentials_state() == "valid"


def test_network_trouble_fails_open(tmp_path, monkeypatch):
    # An offline laptop must never be locked out of its own dashboard.
    home = _fake_home(monkeypatch, tmp_path)
    (home / ".clawmetry").mkdir()
    (home / ".clawmetry" / "config.json").write_text(json.dumps({"api_key": "cm_ok"}))

    def _offline(url, timeout=0):
        raise OSError("network unreachable")

    monkeypatch.setattr(onboarding.urllib.request, "urlopen", _offline)
    assert onboarding.stored_credentials_state() == "unknown"


# ── boot-gate wiring in app.py (source-level guards) ──────────────────────
# app.py's _boot runs a webview + threads CI can't drive; these assertions
# lock the decision wiring the fixes introduced so a refactor can't quietly
# revert to stamp-existence-only behavior.

APP_SRC = (REPO_ROOT / "desktop" / "app.py").read_text(encoding="utf-8")


def test_boot_revalidates_credentials():
    assert "stored_credentials_state" in APP_SRC
    assert "clear_onboarding_stamp" in APP_SRC


def test_timeout_does_not_stamp_only_explicit_skip_does():
    assert "api._skipped" in APP_SRC, (
        "only an explicit skip may stamp onboarding completed; a walk-away "
        "timeout must re-prompt next launch"
    )


def test_failed_connect_does_not_stamp():
    # The stamp write must be inside the ok_key branch.
    idx = APP_SRC.index("ok_key, msg_key = onboarding.apply_cm_key")
    tail = APP_SRC[idx: idx + 1200]
    assert "if ok_key:" in tail.split("mark_onboarding_completed")[0], (
        "a failed connect must not stamp onboarding completed"
    )


def test_attach_path_respects_first_launch():
    assert 'existing[0] == "attach" and onboarding.is_first_launch' in APP_SRC, (
        "the single-instance attach path must not bypass onboarding on a "
        "first-launch install (orphan daemon from a broken uninstall)"
    )


def test_webview_uses_private_storage_path():
    assert APP_SRC.count("storage_path=_webview_storage_dir()") >= 2, (
        "every webview.start must use the private ClawMetry profile so the "
        "uninstaller can remove browser state"
    )
