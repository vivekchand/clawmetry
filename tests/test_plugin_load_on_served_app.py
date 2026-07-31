"""Guard: plugin blueprints must register on the Flask app that serves.

Regression test for the double-``app = Flask(...)`` bug: an early app
construction consumed ``_ext_load(app)`` (clawmetry-pro registered all its
Blueprints there), then a later construction replaced ``app`` and every
pro-only endpoint 404'd on licensed installs — while the OSS 402 stubs
skipped registration because ``clawmetry_pro.is_loaded()`` was True.

Source-level lint (no pro package needed in CI):
  1. ``dashboard.py`` constructs ``app = Flask(`` exactly once.
  2. ``_ext_load(app)`` is called after that construction.
"""
from __future__ import annotations

import re
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parent.parent / "dashboard.py"


def test_single_flask_app_construction():
    src = DASHBOARD.read_text(encoding="utf-8")
    sites = [m.start() for m in re.finditer(r"^app = Flask\(", src, re.M)]
    assert len(sites) == 1, (
        f"dashboard.py constructs `app = Flask(` {len(sites)} times; a second "
        "construction orphans every plugin Blueprint registered on the first "
        "(pro-only routes 404 on licensed installs). Keep exactly one."
    )


def test_ext_load_called_after_app_construction():
    src = DASHBOARD.read_text(encoding="utf-8")
    app_at = src.index("app = Flask(")
    calls = [m.start() for m in re.finditer(r"^_ext_load\(app\)", src, re.M)]
    assert calls, "dashboard.py never calls _ext_load(app) at module scope"
    assert all(c > app_at for c in calls), (
        "_ext_load(app) runs before the served app is constructed — plugin "
        "blueprints would land on a dead app object."
    )
