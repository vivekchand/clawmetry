"""Universal self-heal for a stuck auto_update=False row.

Root cause: clawmetry/sync.py::_sync_auto_update_with_plan already
re-asserts auto_update=True on every cloud heartbeat, but ONLY for entitled
PAID cloud tiers (`if not tier or tier == "cloud_free": return`) -- a
self-hosted or free-tier node whose persisted update_check_config row has a
stale False (written before the 0.12.494 default flip, or via some old UI
toggle) had NO path back to True. This is the asymmetry the user flagged
("self hosted or cloud sync -- whatever it is -- should still auto update").

_heal_stale_auto_update_flag makes the heal universal -- any role, any
tier, connected or not -- while still respecting a real, explicit opt-out
recorded via POST /api/update-check/config (auto_update_user_set=True).
"""
from __future__ import annotations

import importlib


def _uc():
    import routes.update_check as uc
    return importlib.reload(uc)


def test_heals_stale_unset_false_to_true(monkeypatch):
    uc = _uc()
    captured = {}
    monkeypatch.setattr(uc, "_set_update_check_config", lambda u: captured.update(u))
    config = {"auto_update": False, "auto_update_user_set": False}
    uc._heal_stale_auto_update_flag(config)
    assert captured == {"auto_update": True}
    assert config["auto_update"] is True, "caller's in-memory config must reflect the heal immediately"


def test_respects_explicit_user_opt_out(monkeypatch):
    uc = _uc()
    calls = []
    monkeypatch.setattr(uc, "_set_update_check_config", lambda u: calls.append(u))
    config = {"auto_update": False, "auto_update_user_set": True}
    uc._heal_stale_auto_update_flag(config)
    assert calls == [], "a real user opt-out must never be overridden"
    assert config["auto_update"] is False


def test_noop_when_already_true(monkeypatch):
    uc = _uc()
    calls = []
    monkeypatch.setattr(uc, "_set_update_check_config", lambda u: calls.append(u))
    uc._heal_stale_auto_update_flag({"auto_update": True, "auto_update_user_set": False})
    assert calls == []


def test_never_raises_on_persistence_failure(monkeypatch):
    uc = _uc()

    def boom(u):
        raise RuntimeError("fleet db locked")
    monkeypatch.setattr(uc, "_set_update_check_config", boom)
    uc._heal_stale_auto_update_flag({"auto_update": False, "auto_update_user_set": False})  # must not raise


def test_worker_boot_applies_the_heal(monkeypatch):
    """_update_check_worker must call the heal exactly once at boot,
    before the startup check, for every role -- not just for paid cloud
    tiers via the heartbeat-only _sync_auto_update_with_plan path."""
    uc = _uc()

    class _StopEvent:
        def __init__(self):
            self.calls = 0

        def wait(self, secs):
            self.calls += 1
            # First call is the boot-settle delay -- let it through (False)
            # so the worker reaches the heal; stop it right after.
            return self.calls > 1

        def is_set(self):
            return self.calls > 1

    # Pin the fast-loop check so the second stop_event.wait() (the fast-loop
    # interval) is reached deterministically and the worker exits there,
    # instead of falling into the banner-only branch and hitting real
    # network code (_check_for_update -> pypi.org).
    uc._process_role = "daemon"
    monkeypatch.setattr(uc, "_get_update_check_config",
                         lambda: {"auto_update": False, "auto_update_user_set": False,
                                  "check_on_startup": False, "enabled": False})
    healed = []
    monkeypatch.setattr(uc, "_heal_stale_auto_update_flag", lambda cfg: healed.append(cfg))
    uc._update_check_worker(_StopEvent())
    assert len(healed) == 1
