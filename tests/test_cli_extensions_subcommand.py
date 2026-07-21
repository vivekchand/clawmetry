"""Tests for the ``clawmetry extensions`` CLI subcommand.

Sibling of ``tests/test_cli_features_subcommand.py`` /
``tests/test_cli_runtimes_subcommand.py``: the subcommand is a thin read of
:mod:`clawmetry.extensions` in-process state -- the same source
``GET /api/extensions`` consumes -- and must never crash even when the
introspection helpers themselves raise. These tests cover the human tables,
``--json``, the empty-shape fallback, the older-``clawmetry`` degradation
path (no ``failed_plugins`` helper), a subset of failure modes on each of
the four introspection helpers, and the subparser/dispatch wiring so the
subcommand is reachable from ``clawmetry`` end-to-end.
"""
from __future__ import annotations

import argparse
import json

import pytest


@pytest.fixture
def cli_mod(monkeypatch):
    """Return the CLI module with the extensions registry reset to a clean
    state so tests never see plugins loaded by an earlier test."""
    import importlib

    import clawmetry.extensions as ext

    importlib.reload(ext)
    ext._registry.clear()
    ext._loaded_plugins.clear()
    ext._failed_plugins.clear()

    import clawmetry.cli as cli

    return cli


def _ns(**kw) -> argparse.Namespace:
    return argparse.Namespace(**kw)


def test_extensions_table_renders_empty_on_clean_install(cli_mod, capsys):
    """A stock OSS install with no entry-point plugins wired shows the empty
    state cleanly in each of the three sections -- and does not crash."""
    cli_mod._cmd_extensions(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry Extensions" in out
    assert "Loaded plugins: 0" in out
    assert "Failed plugins: 0" in out
    assert "Event hooks:    0" in out
    # Each section shows an explicit "(none)" instead of a blank block so an
    # operator can tell the difference between "no plugins" and "the CLI
    # crashed before printing".
    assert out.count("(none)") == 3


def test_extensions_json_shape_matches_http_endpoint(cli_mod, capsys):
    """The ``--json`` payload must be byte-for-byte compatible on the shared
    keys with ``GET /api/extensions`` so a wrapper script can consume either
    surface interchangeably."""
    cli_mod._cmd_extensions(_ns(as_json=True))
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload == {
        "plugins": [],
        "plugin_count": 0,
        "failed_plugins": [],
        "failed_plugin_count": 0,
        "events": [],
        "handler_counts": {},
    }


def test_extensions_json_matches_api_extensions_response(cli_mod, capsys):
    """When the /api/extensions HTTP surface is reachable, its response and
    the CLI's ``--json`` payload must not drift on the shared keys. Uses a
    real Flask test client instead of calling the view function directly so
    the Blueprint's ``jsonify()`` has the app context it needs."""
    from flask import Flask

    from routes.extensions import bp_extensions

    cli_mod._cmd_extensions(_ns(as_json=True))
    cli_payload = json.loads(capsys.readouterr().out.strip())

    app = Flask(__name__)
    app.register_blueprint(bp_extensions)
    resp = app.test_client().get("/api/extensions")
    assert resp.status_code == 200
    http_payload = resp.get_json()

    shared = {
        "plugins",
        "plugin_count",
        "failed_plugins",
        "failed_plugin_count",
        "events",
        "handler_counts",
    }
    assert shared <= set(cli_payload)
    assert shared <= set(http_payload)
    for key in shared:
        assert cli_payload[key] == http_payload[key], key


def test_extensions_surfaces_loaded_and_failed_state(cli_mod, capsys):
    """A synthetic registry (a loaded plugin + a failed plugin + one event
    with two handlers) must round-trip through both the human table and the
    JSON payload with the expected counts and per-row detail."""
    import clawmetry.extensions as ext

    ext._loaded_plugins.append("clawmetry-pro")
    ext._failed_plugins.append({"name": "clawmetry-broken", "error": "boom"})
    ext._registry["session.snapshot"] = [lambda p: None, lambda p: None]

    # Human table
    cli_mod._cmd_extensions(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "Loaded plugins: 1" in out
    assert "Failed plugins: 1" in out
    assert "Event hooks:    1" in out
    assert "clawmetry-pro" in out
    assert "clawmetry-broken" in out
    assert "boom" in out
    assert "session.snapshot" in out
    assert "2 handlers" in out

    # JSON
    cli_mod._cmd_extensions(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["plugins"] == ["clawmetry-pro"]
    assert payload["plugin_count"] == 1
    assert payload["failed_plugins"] == [
        {"name": "clawmetry-broken", "error": "boom"}
    ]
    assert payload["failed_plugin_count"] == 1
    assert payload["events"] == ["session.snapshot"]
    assert payload["handler_counts"] == {"session.snapshot": 2}


def test_extensions_single_handler_pluralization(cli_mod, capsys):
    """One handler prints ``1 handler`` (singular); the two-handler case is
    covered by the round-trip test above."""
    import clawmetry.extensions as ext

    ext._registry["cron.deliver"] = [lambda p: None]

    cli_mod._cmd_extensions(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "cron.deliver (1 handler)" in out
    assert "1 handlers" not in out  # never plural for a single handler


def test_extensions_survives_loaded_plugins_error(cli_mod, capsys, monkeypatch):
    """A poisoned :func:`loaded_plugins` must not crash the CLI or the HTTP
    surface -- the error is surfaced to stderr, the JSON payload keeps the
    parseable empty-list shape and pins the error under an ``error`` key."""
    import clawmetry.extensions as ext

    def _boom():
        raise RuntimeError("synthetic loaded_plugins failure")

    monkeypatch.setattr(ext, "loaded_plugins", _boom)
    cli_mod._cmd_extensions(_ns(as_json=True))
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["plugins"] == []
    assert payload["plugin_count"] == 0
    assert "synthetic loaded_plugins failure" in payload["error"]
    # Stderr also carries the error so a pipeline wrapper sees the failure
    # even if it discards stdout.
    assert "synthetic loaded_plugins failure" in captured.err


def test_extensions_degrades_when_failed_plugins_absent(
    cli_mod, capsys, monkeypatch
):
    """A downgrade path: an older in-process ``clawmetry`` may not ship
    :func:`failed_plugins` yet. The CLI must fall back to an empty list
    rather than 5xx'ing the command -- matches the ``/api/extensions``
    fallback posture documented in ``routes/extensions.py``."""
    import clawmetry.extensions as ext

    monkeypatch.delattr(ext, "failed_plugins", raising=False)
    cli_mod._cmd_extensions(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["failed_plugins"] == []
    assert payload["failed_plugin_count"] == 0
    # A missing helper is not an error -- the payload must NOT carry a
    # spurious ``error`` key that would trigger a red banner in a wrapper.
    assert "error" not in payload


def test_extensions_survives_registered_events_error(
    cli_mod, capsys, monkeypatch
):
    """A poisoned :func:`registered_events` must not crash the CLI. The
    payload keeps the empty-list shape and surfaces the failure inline."""
    import clawmetry.extensions as ext

    def _boom():
        raise RuntimeError("synthetic events failure")

    monkeypatch.setattr(ext, "registered_events", _boom)
    cli_mod._cmd_extensions(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["events"] == []
    assert payload["handler_counts"] == {}
    assert "synthetic events failure" in payload["error"]


def test_extensions_survives_extensions_module_missing(cli_mod, capsys):
    """If the ``clawmetry.extensions`` introspection helpers themselves are
    unavailable -- the most catastrophic failure this CLI has to handle --
    the whole payload must still populate with empty defaults and the
    failure must reach stderr. Simulates the failure by both (a) planting a
    poison stand-in in ``sys.modules`` and (b) rebinding the parent
    package's attribute, so ``from clawmetry import extensions as _ext``
    inside :func:`_cmd_extensions` binds to the poison instead of the real
    module -- CPython's ``from`` path prefers the parent's attribute, so
    the ``sys.modules`` swap alone is not enough."""
    import sys as _sys

    import clawmetry as _pkg

    saved_mod = _sys.modules.pop("clawmetry.extensions", None)
    saved_attr = getattr(_pkg, "extensions", None)

    class _Poison:
        def __getattr__(self, name):
            raise RuntimeError("synthetic import failure")

    poison = _Poison()
    _sys.modules["clawmetry.extensions"] = poison
    _pkg.extensions = poison
    try:
        cli_mod._cmd_extensions(_ns(as_json=True))
    finally:
        _sys.modules.pop("clawmetry.extensions", None)
        if saved_mod is not None:
            _sys.modules["clawmetry.extensions"] = saved_mod
        if saved_attr is not None:
            _pkg.extensions = saved_attr

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    # Every introspection helper access fails, so the payload keeps the
    # empty defaults and pins an inline error the wrapper can surface. The
    # exact error string comes from whichever helper is probed first --
    # what matters for the never-crash contract is that:
    #   1. every count/list is the empty default (no partial state), and
    #   2. an ``error`` key is present so the caller can see the failure.
    assert payload["plugins"] == []
    assert payload["plugin_count"] == 0
    assert payload["failed_plugins"] == []
    assert payload["failed_plugin_count"] == 0
    assert payload["events"] == []
    assert payload["handler_counts"] == {}
    assert "synthetic import failure" in payload["error"]
    assert "synthetic import failure" in captured.err


def test_extensions_subcommand_is_registered():
    """The subparser + dispatch table + the ``_subcmds`` tuple must all list
    ``extensions`` so the subcommand is reachable from ``clawmetry`` end to
    end -- guards against a partial merge that would silently route to the
    dashboard flag parser instead of the entitlement CLI."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    assert '"extensions"' in src
    assert "_cmd_extensions" in src
