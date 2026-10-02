"""Contract tests for the conversational dashboard builder.

Ask is a local, read-only natural-language query surface. It must remain
reachable, persist saved panels through DuckDB, and explain provider setup
without pretending that a browser can export a shell variable for a remote
machine.
"""
from __future__ import annotations

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*parts):
    path = os.path.join(_ROOT, *parts)
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def test_ask_nav_item_is_live():
    """Ask is a live entry point for persistent dashboard panels."""
    html = _read('dashboard.py')
    assert "switchTab('dives')" in html
    assert 'data-tab="dives"' in html


def test_dives_tab_template_and_page_script_are_shipped():
    """The conversational dashboard builder is shipped with its page loader."""
    assert _read('clawmetry', 'templates', 'tabs', 'dives.html') is not None
    assert _read('clawmetry', 'static', 'js', 'dives.js') is not None
    dash = _read('dashboard.py')
    assert "tabs/dives.html" in dash
    assert "js/dives.js" in dash


def test_app_js_registers_dives_tab_loader():
    """The tab transition must load saved panels and the Ask page."""
    app_js = _read('clawmetry', 'static', 'js', 'app.js')
    assert "name === 'dives'" in app_js
    assert 'loadDivesPage' in app_js


def test_home_surfaces_safe_agent_efficiency_playbook():
    """The main page links operating habits to the evidence tabs that measure them."""
    html = _read('clawmetry', 'templates', 'tabs', 'overview.html')
    assert 'id="agent-efficiency-playbook"' in html
    for tab in ('brain', 'context-economics', 'guard', 'models'):
        assert f"switchTab('{tab}')" in html
        assert f'id="page-{tab}"' in _read('clawmetry', 'templates', 'tabs', tab + '.html')


def test_the_anthropic_key_banner_is_gone_from_the_ui():
    """The copy that started this: a hosted user told to export a shell var.

    The daemon may still answer ``no_auth`` on the API; what must not exist
    is a rendered banner telling a browser user to export an env var.
    """
    for rel in (('dashboard.py',),
                ('clawmetry', 'static', 'js', 'app.js')):
        body = _read(*rel)
        assert 'No Anthropic API key found' not in (body or ''), rel


def test_dives_backend_is_still_importable():
    """The cut is the tab, not the SQL-safety layer Briefs/Insights use."""
    from clawmetry.dives_sql_safety import validate_sql
    ok, _ = validate_sql('SELECT 1')
    assert ok in (True, False)  # importable and callable; behaviour is its own suite
