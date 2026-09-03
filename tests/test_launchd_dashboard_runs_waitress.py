"""The launchd dashboard service must run waitress, not Flask's debug server.

``dashboard.py``'s ``--debug`` flag defaults to True, so any launcher that
omits ``--no-debug`` gets the werkzeug development server with the stat
reloader: it restarts on every file change (every self-update), polls the
whole import tree every second, and answered "Debugger is active!" under
launchd on 2026-09-02. The systemd unit, the desktop app and CI all pass
``--no-debug``; the launchd generator in ``clawmetry/cli.py`` did not.
"""
from __future__ import annotations

import pathlib
import re


def _cli_source() -> str:
    return pathlib.Path(__file__).resolve().parents[1].joinpath(
        "clawmetry", "cli.py").read_text()


def test_launchd_program_arguments_include_no_debug():
    src = _cli_source()
    m = re.search(r"_launchd_cmd\s*=\s*\[(.*?)\]", src, re.S)
    assert m, "launchd command list not found in clawmetry/cli.py"
    assert '"--no-debug"' in m.group(1), m.group(1)


def test_dashboard_debug_flag_still_defaults_on_so_the_guard_matters():
    """If this ever flips, the launchd guard above becomes redundant rather
    than wrong; the assertion documents why it exists."""
    src = pathlib.Path(__file__).resolve().parents[1].joinpath("dashboard.py").read_text()
    assert re.search(r'"--debug",\s*dest="debug",\s*action="store_true",\s*default=True', src)
