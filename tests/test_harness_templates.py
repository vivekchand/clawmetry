"""Guard tests for the per-harness template framework (#2667).

Covers the registry/schema contract, the built-in free templates, the
Python<->JS render-type contract (the JS renderer must handle every render type
the Python registry allows), and the /api/harness/* endpoints.
"""
import os
import re

import pytest

from clawmetry import harness_templates as ht

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_JS = os.path.join(REPO, "clawmetry", "static", "js", "app.js")


def test_builtins_registered():
    rts = ht.runtimes()
    assert "openclaw" in rts and "nemoclaw" in rts, rts


def test_builtin_templates_validate():
    for rt in ("openclaw", "nemoclaw"):
        tmpl = ht.get(rt)
        assert tmpl, f"{rt} template missing"
        assert ht.validate(tmpl) == [], f"{rt}: {ht.validate(tmpl)}"


def test_register_rejects_malformed_without_raising():
    # bad render type
    assert ht.register({"runtime": "z1", "title": "Z", "sections": [
        {"id": "a", "title": "A", "source": "s", "render": "bogus"}]}) is False
    # missing sections
    assert ht.register({"runtime": "z2", "title": "Z"}) is False
    # table without columns
    assert ht.register({"runtime": "z3", "title": "Z", "sections": [
        {"id": "a", "title": "A", "source": "s", "render": "table"}]}) is False
    # duplicate section id
    assert ht.register({"runtime": "z4", "title": "Z", "sections": [
        {"id": "a", "title": "A", "source": "s", "render": "count"},
        {"id": "a", "title": "B", "source": "s2", "render": "count"}]}) is False
    for z in ("z1", "z2", "z3", "z4"):
        assert ht.get(z) is None


def test_register_accepts_and_overrides_by_runtime():
    t1 = {"runtime": "tmprt", "title": "One", "sections": [
        {"id": "a", "title": "A", "source": "summary.x", "render": "count"}]}
    t2 = {"runtime": "tmprt", "title": "Two", "sections": [
        {"id": "b", "title": "B", "source": "summary.y", "render": "count"}]}
    try:
        assert ht.register(t1) is True
        assert ht.get("tmprt")["title"] == "One"
        assert ht.register(t2) is True   # override by runtime
        assert ht.get("tmprt")["title"] == "Two"
    finally:
        ht.unregister("tmprt")


def test_js_renderer_handles_every_render_type():
    """The JS renderer's switch must cover every render type the Python
    registry permits — otherwise a template validates server-side but the
    client silently drops the section."""
    js = open(APP_JS, encoding="utf-8").read()
    # the dispatch switch is in renderHarnessSection
    assert "function renderHarnessSection" in js
    for rtype in ht.RENDER_TYPES:
        if rtype == "json":
            # json is the default arm, not an explicit case
            assert "_hrJson(" in js
            continue
        assert f"case '{rtype}':" in js, f"JS renderer missing case for render type {rtype!r}"


def test_harness_endpoints_smoke():
    """/api/harness/templates returns the registry; /api/harness/data never 500s."""
    from flask import Flask
    from routes.harness import bp_harness
    app = Flask(__name__)
    app.register_blueprint(bp_harness)
    client = app.test_client()

    r = client.get("/api/harness/templates")
    assert r.status_code == 200
    body = r.get_json()
    assert "openclaw" in body["templates"]

    r2 = client.get("/api/harness/data?runtime=openclaw")
    assert r2.status_code == 200
    d = r2.get_json()
    assert d["runtime"] == "openclaw"
    assert set(d["summary"].keys()) >= {"sessions", "cost_usd", "tokens"}
    assert isinstance(d["sessions"], list)
    assert isinstance(d.get("extra"), dict)
    # every session carries an `extra` dict so `sessions[].extra.*` always resolves
    for s in d["sessions"]:
        assert isinstance(s.get("extra"), dict)
