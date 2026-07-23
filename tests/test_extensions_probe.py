"""Tests for :func:`clawmetry.extensions.probe_plugins` — the side-effect-free
entry-point probe.

Pins the diagnostic surface ``clawmetry status`` (and any wrapper script)
reads to answer "is this install's ``clawmetry-pro`` entry point *importable*
right now?" without invoking any plugin code. Complements
``test_extensions_introspection.py``, which pins the in-process
``loaded_plugins`` / ``failed_plugins`` mirrors.

The important guarantee: ``ep.load()`` runs, ``ep.load()()`` does NOT. A
plugin that would raise inside ``register_all()`` still reads ``importable:
True`` here — the whole point of the probe is to be safe from any plugin
side effects.
"""
from __future__ import annotations

import pytest

import clawmetry.extensions as ext


class _FakeEntryPoint:
    """Stub mimicking ``importlib.metadata.EntryPoint``."""

    def __init__(self, fn, name="fake", value="mod:attr"):
        self._fn = fn
        self.name = name
        self.value = value

    def load(self):
        return self._fn


def _fake_eps(*triples):
    return [_FakeEntryPoint(fn, name=n, value=v) for fn, n, v in triples]


@pytest.fixture(autouse=True)
def _reset_loader():
    """Snapshot/restore the module-level mirrors so a probe run cannot leak
    state into adjacent suites — same isolation contract the introspection
    suite uses."""
    ext._loaded = False
    with ext._lock:
        ext._loaded_plugins.clear()
        ext._failed_plugins.clear()
        prior_registry = {k: list(v) for k, v in ext._registry.items()}
        ext._registry.clear()
    yield
    ext._loaded = False
    with ext._lock:
        ext._loaded_plugins.clear()
        ext._failed_plugins.clear()
        ext._registry.clear()
        ext._registry.update(prior_registry)


def test_probe_empty_when_no_entry_points(monkeypatch):
    monkeypatch.setattr(ext, "_select_entry_points", lambda group: [])
    assert ext.probe_plugins() == []


def test_probe_reports_importable_row(monkeypatch):
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps(
            (lambda: None, "clawmetry-pro", "clawmetry_pro.ext:register_all"),
        ),
    )
    rows = ext.probe_plugins()
    assert rows == [{
        "name": "clawmetry-pro",
        "value": "clawmetry_pro.ext:register_all",
        "importable": True,
        "error": None,
    }]


def test_probe_captures_import_error_string_only(monkeypatch):
    """A load-time error is captured as ``str(exc)`` — no traceback / frame
    locals — so a stack-frame path or secret never leaks into ``status --json``."""
    class _BadEP:
        name = "clawmetry-pro"
        value = "clawmetry_pro.ext:register_all"

        def load(self):
            secret = "/home/op/.clawmetry/license.key"  # noqa: F841
            raise RuntimeError("plain")

    monkeypatch.setattr(ext, "_select_entry_points", lambda group: [_BadEP()])
    rows = ext.probe_plugins()

    assert len(rows) == 1
    row = rows[0]
    assert row["name"] == "clawmetry-pro"
    assert row["value"] == "clawmetry_pro.ext:register_all"
    assert row["importable"] is False
    assert row["error"] == "plain"
    assert "Traceback" not in row["error"]
    assert "license.key" not in row["error"]


def test_probe_reports_multiple_entry_points_in_order(monkeypatch):
    """Row order matches attempt order — same convention ``failed_plugins``
    honours, so a wrapper script can zip these with an ordered "expected"
    list without re-sorting."""
    class _BadEP:
        name = "beta"
        value = "pkg_b:reg"

        def load(self):
            raise ValueError("nope")

    def _mixed(group):
        return [
            _FakeEntryPoint(lambda: None, name="alpha", value="pkg_a:reg"),
            _BadEP(),
            _FakeEntryPoint(lambda: None, name="gamma", value="pkg_c:reg"),
        ]

    monkeypatch.setattr(ext, "_select_entry_points", _mixed)
    rows = ext.probe_plugins()
    assert [r["name"] for r in rows] == ["alpha", "beta", "gamma"]
    assert [r["importable"] for r in rows] == [True, False, True]
    assert rows[1]["error"] == "nope"


def test_probe_does_not_invoke_the_callable(monkeypatch):
    """The whole reason the probe exists: importing the entry-point value
    must NOT invoke it. A plugin that raises inside ``register_all()`` still
    reads importable: True here — the invocation side of that lives in
    :func:`load_plugins`, which the CLI status probe deliberately does not
    call. Documents (and guards) the safety contract callers rely on.
    """
    invocations = {"n": 0}

    def _tracker():
        invocations["n"] += 1
        raise RuntimeError("do not run me")

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((_tracker, "clawmetry-pro", "pkg:reg")),
    )
    rows = ext.probe_plugins()

    assert invocations["n"] == 0
    assert rows[0]["importable"] is True
    assert rows[0]["error"] is None


def test_probe_does_not_touch_loaded_or_failed_mirrors(monkeypatch):
    """The probe is orthogonal to the in-process ``load_plugins`` mirrors —
    running it must not populate ``loaded_plugins()`` (or
    ``failed_plugins()``), otherwise a status probe would corrupt the
    ``/api/extensions`` view a daemon later reports."""
    def _bad():
        raise RuntimeError("kaboom")

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps(
            (lambda: None, "clawmetry-pro", "pkg:reg"),
            (_bad,        "broken",       "pkg:reg"),
        ),
    )
    ext.probe_plugins()

    assert ext.loaded_plugins() == []
    assert ext.failed_plugins() == []
    assert ext._loaded is False  # once-guard untouched


def test_probe_survives_entry_point_enumeration_failure(monkeypatch):
    """A corrupt distribution metadata file that makes ``_select_entry_points``
    raise degrades to an empty list — the never-raise contract every other
    diagnostic helper honours, so ``clawmetry status`` cannot 5xx on a broken
    ``importlib.metadata`` install.
    """
    def _explode(group):
        raise RuntimeError("bad metadata")

    monkeypatch.setattr(ext, "_select_entry_points", _explode)
    assert ext.probe_plugins() == []


def test_probe_row_has_stable_key_set(monkeypatch):
    """The row shape is a contract: exactly these four keys, no more, no
    less. Pinned so a future edit that adds a new key must consciously
    change the callers that ``jq .name`` off this list."""
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda: None, "alpha", "pkg:reg")),
    )
    row = ext.probe_plugins()[0]
    assert set(row.keys()) == {"name", "value", "importable", "error"}
