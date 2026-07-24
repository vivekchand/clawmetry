"""Tests for the entry-point plugin loader's introspection surface.

Pins the diagnostic API operators read to confirm ``clawmetry-pro`` (or any
other ``clawmetry.extensions`` entry point) has actually loaded on a node:

- ``clawmetry.extensions.loaded_plugins()`` — names of plugins that loaded
  successfully in this process.
- ``GET /api/extensions`` — wire shape carrying those names plus the
  registered-event hooks, never-raising on any introspection failure.
"""
from __future__ import annotations

import json

import pytest
from flask import Flask

import clawmetry.extensions as ext


class _FakeEntryPoint:
    """Stub mimicking importlib.metadata.EntryPoint."""

    def __init__(self, fn, name="fake"):
        self._fn = fn
        self.name = name

    def load(self):
        return self._fn


def _fake_eps(*pairs):
    return [_FakeEntryPoint(fn, name=n) for fn, n in pairs]


@pytest.fixture(autouse=True)
def _reset_loader():
    """Drop the once-guard + the loaded-name mirror + the failed-name mirror
    before every test so monkeypatched entry points actually run. Also
    snapshot/restore the event registry so handlers registered here can't
    leak into adjacent suites and handlers from adjacent suites can't leak
    in here."""
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


# ── loaded_plugins() ─────────────────────────────────────────────────────────


def test_loaded_plugins_empty_before_load():
    assert ext.loaded_plugins() == []


def test_loaded_plugins_returns_a_copy():
    """Caller mutation must not corrupt the registry."""
    ext.loaded_plugins().append("ghost")
    assert ext.loaded_plugins() == []


def test_loaded_plugins_records_successful_loads(monkeypatch):
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda: None, "alpha"), (lambda: None, "beta")),
    )
    ext.load_plugins()
    assert ext.loaded_plugins() == ["alpha", "beta"]


def test_loaded_plugins_excludes_failed_plugins(monkeypatch):
    """A plugin that raised during load must NOT appear — operators rely on
    this list to confirm successful wiring, not attempted wiring."""
    def boom():
        raise RuntimeError("boom")

    def good():
        return None

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((boom, "broken"), (good, "ok")),
    )
    ext.load_plugins()
    assert ext.loaded_plugins() == ["ok"]


def test_loaded_plugins_resets_on_reentry(monkeypatch):
    """If a test flips ``_loaded`` back to False, the next load_plugins()
    call must start the list fresh (no duplicates from the prior pass)."""
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda: None, "alpha")),
    )
    ext.load_plugins()
    assert ext.loaded_plugins() == ["alpha"]
    # Simulate a process where ``_loaded`` was reset (test fixture, reload, …).
    ext._loaded = False
    ext.load_plugins()
    assert ext.loaded_plugins() == ["alpha"]  # not ["alpha", "alpha"]


def test_loaded_plugins_records_app_style_plugins(monkeypatch):
    """A plugin with ``register_all(app)`` is also recorded once invoked."""
    received = []
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda app: received.append(app), "needs-app")),
    )
    sentinel = object()
    ext.load_plugins(app=sentinel)
    assert received == [sentinel]
    assert ext.loaded_plugins() == ["needs-app"]


# ── failed_plugins() ─────────────────────────────────────────────────────────


def test_failed_plugins_empty_before_load():
    assert ext.failed_plugins() == []


def test_failed_plugins_records_load_failures(monkeypatch):
    def boom():
        raise RuntimeError("kaboom")

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((boom, "broken")),
    )
    ext.load_plugins()
    failed = ext.failed_plugins()
    assert failed == [{"name": "broken", "error": "kaboom"}]
    # Companion mirror stays empty for the failed plugin.
    assert ext.loaded_plugins() == []


def test_failed_plugins_complementary_to_loaded(monkeypatch):
    """A given entry point appears in exactly one of the two lists per load."""
    def boom():
        raise ValueError("nope")

    def good():
        return None

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((good, "ok"), (boom, "broken")),
    )
    ext.load_plugins()
    assert ext.loaded_plugins() == ["ok"]
    assert [e["name"] for e in ext.failed_plugins()] == ["broken"]


def test_failed_plugins_preserves_attempt_order(monkeypatch):
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps(
            ((lambda: (_ for _ in ()).throw(RuntimeError("a"))), "first"),
            ((lambda: (_ for _ in ()).throw(RuntimeError("b"))), "second"),
        ),
    )
    ext.load_plugins()
    assert [e["name"] for e in ext.failed_plugins()] == ["first", "second"]


def test_failed_plugins_returns_a_copy(monkeypatch):
    """Caller mutation of the returned list or its dicts must not corrupt
    the registry."""
    def boom():
        raise RuntimeError("owned")

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((boom, "broken")),
    )
    ext.load_plugins()

    view = ext.failed_plugins()
    view.append({"name": "ghost", "error": "phantom"})
    view[0]["error"] = "tampered"

    fresh = ext.failed_plugins()
    assert fresh == [{"name": "broken", "error": "owned"}]


def test_failed_plugins_resets_on_reentry(monkeypatch):
    """A rerun of ``load_plugins`` must start with a clean failure list so a
    reloaded daemon doesn't report stale failures from a prior pass."""
    def boom():
        raise RuntimeError("first-round")

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((boom, "broken")),
    )
    ext.load_plugins()
    assert ext.failed_plugins() == [{"name": "broken", "error": "first-round"}]

    # Simulate a daemon reload where ``_loaded`` was reset; this time the
    # plugin behaves.
    ext._loaded = False
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda: None, "broken")),
    )
    ext.load_plugins()
    assert ext.failed_plugins() == []  # stale failure did not survive
    assert ext.loaded_plugins() == ["broken"]


def test_failed_plugins_captures_only_str_not_traceback(monkeypatch):
    """Only ``str(exc)`` lands in the mirror — never the traceback / frame
    locals — so paths and secrets in frames never leak into the diagnostic
    endpoint. Pinned so a future refactor cannot silently upgrade the
    capture to a traceback dump.
    """
    def boom():
        secret = "/Users/op/.clawmetry/license.key"  # noqa: F841
        raise RuntimeError("plain")

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((boom, "broken")),
    )
    ext.load_plugins()

    entry = ext.failed_plugins()[0]
    assert set(entry.keys()) == {"name", "error"}
    assert entry["error"] == "plain"
    assert "Traceback" not in entry["error"]
    assert "license.key" not in entry["error"]


# ── GET /api/extensions ──────────────────────────────────────────────────────


@pytest.fixture
def client():
    from routes.extensions import bp_extensions

    app = Flask(__name__)
    app.register_blueprint(bp_extensions)
    return app.test_client()


def test_api_extensions_shape_empty(client):
    resp = client.get("/api/extensions")
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body == {
        "plugins": [],
        "plugin_count": 0,
        "failed_plugins": [],
        "failed_plugin_count": 0,
        "probed_plugins": [],
        "probed_plugin_count": 0,
        "events": [],
        "handler_counts": {},
    }


def test_api_extensions_reports_loaded_plugins(client, monkeypatch):
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda: None, "clawmetry-pro")),
    )
    ext.load_plugins()

    body = json.loads(client.get("/api/extensions").data)
    assert body["plugins"] == ["clawmetry-pro"]
    assert body["plugin_count"] == 1


def test_api_extensions_reports_registered_events(client):
    ext.register("test.evt.api.a", lambda p: None)
    ext.register("test.evt.api.a", lambda p: None)  # 2 handlers for one event
    ext.register("test.evt.api.b", lambda p: None)

    body = json.loads(client.get("/api/extensions").data)
    assert "test.evt.api.a" in body["events"]
    assert "test.evt.api.b" in body["events"]
    assert body["handler_counts"]["test.evt.api.a"] >= 2
    assert body["handler_counts"]["test.evt.api.b"] >= 1


def test_api_extensions_never_raises(client, monkeypatch):
    """If introspection itself blows up, the endpoint still returns 200 with
    a safe empty shape — the dashboard always has something to render."""
    def explode():
        raise RuntimeError("introspection broken")

    monkeypatch.setattr(ext, "loaded_plugins", explode)

    resp = client.get("/api/extensions")
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body == {
        "plugins": [],
        "plugin_count": 0,
        "failed_plugins": [],
        "failed_plugin_count": 0,
        "probed_plugins": [],
        "probed_plugin_count": 0,
        "events": [],
        "handler_counts": {},
    }


def test_api_extensions_reports_failed_plugins(client, monkeypatch):
    def boom():
        raise RuntimeError("kaboom")

    def good():
        return None

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((good, "clawmetry-pro"), (boom, "flaky-plugin")),
    )
    ext.load_plugins()

    body = json.loads(client.get("/api/extensions").data)
    assert body["plugins"] == ["clawmetry-pro"]
    assert body["plugin_count"] == 1
    assert body["failed_plugins"] == [
        {"name": "flaky-plugin", "error": "kaboom"},
    ]
    assert body["failed_plugin_count"] == 1


def test_api_extensions_survives_missing_failed_plugins_helper(client, monkeypatch):
    """A mixed deploy where the routes package is new but the core ``clawmetry``
    is old (no :func:`failed_plugins`) must still populate the loaded-plugin
    side of the envelope instead of 5xx'ing the whole response.
    """
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda: None, "clawmetry-pro")),
    )
    ext.load_plugins()

    # Simulate the older wheel by making the accessor raise (an older wheel
    # would raise ``AttributeError`` on the missing symbol; behaviourally
    # equivalent from the route's perspective).
    def missing():
        raise AttributeError("failed_plugins")

    monkeypatch.setattr(ext, "failed_plugins", missing)

    body = json.loads(client.get("/api/extensions").data)
    assert body["plugins"] == ["clawmetry-pro"]
    assert body["plugin_count"] == 1
    assert body["failed_plugins"] == []
    assert body["failed_plugin_count"] == 0


# ── GET /api/extensions × probed_plugins ────────────────────────────────────


def _probe_fake_eps(*triples):
    """Build a fake entry-point list that matches the ``probe_plugins`` row
    shape — same helper the probe unit tests use, inlined here so the API
    test doesn't reach across modules for its stubs."""
    class _EP:
        def __init__(self, fn, name, value):
            self._fn = fn
            self.name = name
            self.value = value

        def load(self):
            return self._fn()

    return [_EP(fn, n, v) for fn, n, v in triples]


def test_api_extensions_reports_probed_plugins(client, monkeypatch):
    """The probe surfaces every visible entry point with its ``value`` string
    and whether ``ep.load()`` succeeds right now — even ones ``load_plugins``
    hasn't touched (a wheel installed post-startup, before a daemon reload)."""
    def _ok():
        return lambda: None

    def _bad():
        raise RuntimeError("import kaboom")

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _probe_fake_eps(
            (_ok,  "clawmetry-pro", "clawmetry_pro.ext:register_all"),
            (_bad, "flaky-plugin",  "flaky.mod:register_all"),
        ),
    )

    body = json.loads(client.get("/api/extensions").data)
    assert body["probed_plugin_count"] == 2
    assert body["probed_plugins"] == [
        {
            "name": "clawmetry-pro",
            "value": "clawmetry_pro.ext:register_all",
            "importable": True,
            "error": None,
        },
        {
            "name": "flaky-plugin",
            "value": "flaky.mod:register_all",
            "importable": False,
            "error": "import kaboom",
        },
    ]


def test_api_extensions_probed_independent_of_load_plugins(client, monkeypatch):
    """``probed_plugins`` reflects the CURRENT importability of every visible
    entry point — it must NOT require ``load_plugins`` to have run. That's
    the whole point: on a short-lived process (``clawmetry status`` shell,
    or a dashboard restart after a post-startup wheel install) the probe
    still populates while ``plugins`` reads empty.
    """
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _probe_fake_eps(
            (lambda: (lambda: None), "clawmetry-pro", "pkg:reg"),
        ),
    )
    # Deliberately do NOT call ext.load_plugins() — the ``plugins`` mirror
    # should stay empty while the probe still surfaces the entry point.

    body = json.loads(client.get("/api/extensions").data)
    assert body["plugins"] == []
    assert body["plugin_count"] == 0
    assert body["probed_plugin_count"] == 1
    assert body["probed_plugins"][0]["name"] == "clawmetry-pro"
    assert body["probed_plugins"][0]["importable"] is True


def test_api_extensions_survives_missing_probe_plugins_helper(client, monkeypatch):
    """A mixed deploy where the routes package is new but the core
    ``clawmetry`` is old (no :func:`probe_plugins`) must still populate the
    rest of the envelope instead of 5xx'ing the whole response — same
    contract we honour for the older ``failed_plugins`` accessor.
    """
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda: None, "clawmetry-pro")),
    )
    ext.load_plugins()

    def missing():
        raise AttributeError("probe_plugins")

    monkeypatch.setattr(ext, "probe_plugins", missing)

    body = json.loads(client.get("/api/extensions").data)
    assert body["plugins"] == ["clawmetry-pro"]
    assert body["plugin_count"] == 1
    assert body["probed_plugins"] == []
    assert body["probed_plugin_count"] == 0


def test_api_extensions_probed_row_never_leaks_traceback(client, monkeypatch):
    """A load-time error surfaces as ``str(exc)`` only — no traceback / frame
    locals — matching the same posture the ``failed_plugins`` mirror honours,
    so a stack-frame path never leaks into ``GET /api/extensions``.
    """
    def _leaky():
        secret = "/home/op/.clawmetry/license.key"  # noqa: F841
        raise RuntimeError("plain")

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _probe_fake_eps((_leaky, "clawmetry-pro", "pkg:reg")),
    )

    body = json.loads(client.get("/api/extensions").data)
    row = body["probed_plugins"][0]
    assert row["error"] == "plain"
    assert "Traceback" not in row["error"]
    assert "license.key" not in row["error"]
