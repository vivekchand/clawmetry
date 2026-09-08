"""The runtime switcher must default to the single runtime that actually has
sessions when the user has never chosen one (founder 2026-07-28: a
Claude-Code-only machine listed OpenClaw 0 / NemoClaw 0 / Claude Code 3 and
still made the user pick by hand). JS contract guard in the shipped app.js."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _app_js():
    with open(os.path.join(ROOT, "clawmetry", "static", "js", "app.js"),
              encoding="utf-8") as fh:
        return fh.read()


def test_smart_default_present_and_guarded():
    src = _app_js()
    assert "localStorage.getItem('cm-runtime-filter') === null" in src, \
        "smart default must fire only when the user never chose a runtime"
    assert "_nonzero.length === 1" in src, \
        "smart default must require exactly one runtime with sessions"
    assert "_cmRuntimeFilterUrlPin() === null" in src, \
        "URL-pinned tabs must keep their pinned runtime"
