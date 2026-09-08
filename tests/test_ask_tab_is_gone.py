"""The Ask tab is not in the product, and must not creep back.

Ask (Dives) asked a hosted user to ``export ANTHROPIC_API_KEY`` on a machine
they were not looking at, and its "Open Settings" link went to the Security
tab -- which has no key field anywhere on it. A nav item that cannot do its
one job for a trial user, plus a link to a setting that does not exist, is a
trust leak, not a feature with a bug. Removed 2026-09-07 rather than shipped
with an apology banner (FLYWHEEL.md, "Minimal that works beats broad that
half-works": cut, don't caveat).

What is deliberately KEPT: ``routes/dives.py`` and ``clawmetry/dives_*`` --
the SQL allowlist and prompt builder are load-bearing for Briefs, Insights,
Reports and Signals, which are shipped features with their own surfaces.
This gate is about the USER-FACING tab only.

If Ask is ever rebuilt, it needs a path that works for a hosted trial user
with nothing exported -- then delete this file in the same PR.
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


def test_no_ask_nav_item():
    """The sidebar entry is gone -- nothing routes a user to a dead tab."""
    html = _read('dashboard.py')
    assert "switchTab('dives')" not in html
    assert 'data-tab="dives"' not in html


def test_no_dives_tab_template_or_page_script():
    """The page itself and its loader are deleted, not merely unlinked."""
    assert _read('clawmetry', 'templates', 'tabs', 'dives.html') is None
    assert _read('clawmetry', 'static', 'js', 'dives.js') is None
    dash = _read('dashboard.py')
    assert "tabs/dives.html" not in dash
    assert "js/dives.js" not in dash


def test_app_js_has_no_dives_tab_registration():
    """A tab left in the registries renders an empty page on deep links."""
    app_js = _read('clawmetry', 'static', 'js', 'app.js')
    assert 'dives' not in app_js


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
