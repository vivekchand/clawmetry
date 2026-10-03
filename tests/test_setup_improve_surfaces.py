"""Contracts for the Blume-inspired Setup and Improve surfaces."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_setup_and_improve_are_reachable_from_the_primary_nav():
    html = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    assert 'data-tab="setup"' in html
    assert 'data-tab="improve"' in html
    assert "tabs/setup.html" in html
    assert "tabs/improve.html" in html
    assert "js/setup.js" in html
    assert "js/improve.js" in html


def test_setup_and_improve_have_live_loaders_and_read_only_copy():
    app = (ROOT / "clawmetry/static/js/app.js").read_text(encoding="utf-8")
    setup = (ROOT / "clawmetry/static/js/setup.js").read_text(encoding="utf-8")
    improve = (ROOT / "clawmetry/static/js/improve.js").read_text(encoding="utf-8")
    assert "name === 'setup'" in app and "loadSetup" in app
    assert "name === 'improve'" in app and "loadImprove" in app
    assert "/api/runtimes/memory-catalog" in setup
    assert "/api/improve/candidates" in improve
    assert "No files change from this view." in (
        ROOT / "clawmetry/templates/tabs/improve.html"
    ).read_text(encoding="utf-8")
