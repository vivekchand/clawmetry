"""Opt-in auto-update: the background update-check worker installs a newer
release automatically only when the `auto_update` config is on, and never
re-triggers pip once a restart is already pending.

The upgrade itself goes through the same vetted path as the manual "Update
now" button (routes.meta.perform_self_update), which is mocked here — these
tests are about the *gating*, not the pip/restart mechanics.
"""
from __future__ import annotations

import importlib


def _uc():
    import routes.update_check as uc
    return importlib.reload(uc)


def _mock_self_update(monkeypatch, calls, ok=True):
    import routes.meta as meta

    def _fake(reason="manual"):
        calls.append(reason)
        return ({"ok": ok, "old_version": "0.12.1", "new_version": "0.12.2"},
                200 if ok else 500)

    monkeypatch.setattr(meta, "perform_self_update", _fake)


def test_auto_update_off_does_not_upgrade(monkeypatch):
    uc = _uc()
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": False})
    calls = []
    _mock_self_update(monkeypatch, calls)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == [], "must not upgrade when auto_update is off"


def test_auto_update_on_upgrades_once(monkeypatch):
    uc = _uc()
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    calls = []
    _mock_self_update(monkeypatch, calls)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"], "must upgrade once when auto_update is on"
    # Guard: a second check before the restart lands must NOT re-trigger pip.
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"], "must not re-trigger while a restart is pending"


def test_auto_update_failure_allows_retry(monkeypatch):
    uc = _uc()
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    calls = []
    _mock_self_update(monkeypatch, calls, ok=False)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"]
    # The upgrade failed (no restart scheduled) → the next check may retry.
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto", "auto"], "a failed auto-update must be retryable"


def test_auto_update_in_allowed_config_keys(monkeypatch):
    """The config setter must accept `auto_update` (else the toggle is a no-op)."""
    from flask import Flask
    uc = _uc()
    captured = {}
    monkeypatch.setattr(uc, "_set_update_check_config", lambda u: captured.update(u))
    app = Flask(__name__)
    with app.test_request_context(json={"auto_update": True, "bogus": "x"}):
        uc.api_update_check_config_post()
    assert captured == {"auto_update": True}, "auto_update must pass the allow-list, bogus keys filtered"
