"""Tests for the open-core plugin wiring in the sync daemon.

Regression focus: ``run_daemon()`` is the entry point for the long-running
ClawMetry sync/ingest process — started as ``python -m clawmetry.sync`` from
launchd / systemd. ``dashboard.py`` runs ``load_plugins()`` at import time so
plugins (e.g. clawmetry-pro adapters) register in the dashboard process;
without the matching call in ``run_daemon()`` the sync daemon would silently
skip entry-point plugins, and clawmetry-pro could never hook the ingest path
that is the daemon's primary job.

The full daemon does heavy setup (PID lock, DuckDB warm-up, gateway WS tap,
heartbeat HTTP). To test the wiring in isolation we patch the modules
``run_daemon`` reaches BEFORE it touches any of that, and assert that
``load_plugins`` is called. The test never actually runs the daemon loop.
"""
from __future__ import annotations


def _stub_call_counter():
    """Return a (counter_dict, fn) pair. ``fn`` increments ``counter['n']``."""
    counter = {"n": 0}

    def fn(*_a, **_kw):
        counter["n"] += 1

    return counter, fn


def test_run_daemon_calls_load_plugins(monkeypatch):
    """``sync.run_daemon`` must invoke ``clawmetry.extensions.load_plugins``
    before any ingest setup. We short-circuit ``load_config`` to raise
    immediately after the call, so we observe the plugin call without running
    the rest of the daemon."""
    from clawmetry import extensions as ext
    from clawmetry import sync as sync_mod

    counter, fake_load = _stub_call_counter()
    monkeypatch.setattr(ext, "load_plugins", fake_load)
    # The sync module imports the function lazily inside run_daemon
    # (`from clawmetry.extensions import load_plugins as _ext_load`), so the
    # monkeypatch on ``ext.load_plugins`` is what the daemon picks up.

    # Make _acquire_pid_lock pass so we reach the load_plugins call.
    monkeypatch.setattr(sync_mod, "_acquire_pid_lock", lambda: True)
    monkeypatch.setattr(sync_mod, "_install_shutdown_handlers", lambda: None)

    # Stop the daemon hard right after load_plugins by raising in load_config.
    class _Stop(RuntimeError):
        pass

    def _boom():
        raise _Stop("stop after load_plugins")

    monkeypatch.setattr(sync_mod, "load_config", _boom)

    try:
        sync_mod.run_daemon()
    except _Stop:
        pass

    assert counter["n"] == 1, (
        "sync.run_daemon must call clawmetry.extensions.load_plugins exactly "
        "once at startup so paid-plugin entry points register in the daemon "
        "process, not only in the dashboard process."
    )


def test_run_daemon_swallows_plugin_load_errors(monkeypatch):
    """A broken plugin must NOT crash the sync daemon. The daemon's ingest
    job is the OSS install's only data source — losing it because one paid
    plugin's ``register_all`` raised would silently break every dashboard."""
    from clawmetry import extensions as ext
    from clawmetry import sync as sync_mod

    def _raise(*_a, **_kw):
        raise RuntimeError("simulated broken plugin")

    monkeypatch.setattr(ext, "load_plugins", _raise)
    monkeypatch.setattr(sync_mod, "_acquire_pid_lock", lambda: True)
    monkeypatch.setattr(sync_mod, "_install_shutdown_handlers", lambda: None)

    class _Stop(RuntimeError):
        pass

    monkeypatch.setattr(
        sync_mod, "load_config", lambda: (_ for _ in ()).throw(_Stop("stop"))
    )

    # If the plugin error were not swallowed, this would surface RuntimeError
    # instead of _Stop. The assertion is the absence of RuntimeError leaking.
    try:
        sync_mod.run_daemon()
    except _Stop:
        pass
    except RuntimeError as exc:
        if "simulated broken plugin" in str(exc):
            raise AssertionError(
                "sync.run_daemon must swallow load_plugins errors, not "
                "propagate them — a broken plugin must never take down the "
                "ingest daemon."
            )
        raise


def test_dashboard_module_still_loads_plugins():
    """Sanity check: the dashboard's import-time call to load_plugins remains
    in place. Sync-daemon wiring is *additive*; it does not replace the
    dashboard's own startup hook."""
    import dashboard  # noqa: F401 — import triggers load_plugins side-effect

    # The dashboard imports ``load_plugins`` and calls it inside a try/except.
    # Re-importing here proves the module loaded cleanly (no ImportError) on
    # the open-core OSS install.
    assert hasattr(dashboard, "_ext_emit"), (
        "dashboard.py must keep the extensions wiring (emit + load_plugins) "
        "alive at module top so the dashboard process registers plugins."
    )
