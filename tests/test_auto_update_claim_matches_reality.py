"""The update banner must not claim auto-update is on when it cannot be.

Founder node, 2026-10-06. The banner read "Update available: v0.12.912. You
are on v0.12.908" with a ticked **"Auto-update on"** beside it, and the daemon
had not updated in days. `/api/update-check/status` on that node said:

    config.auto_update    True      <- what the banner rendered
    updater.env_disabled  True      <- what actually governs
    last_attempt_outcome  failed    target 0.12.904

`CLAWMETRY_AUTO_UPDATE=0` was set for the daemon process, which
`routes/update_check.py::_env_auto_update_disabled` treats as a hard kill
switch regardless of the stored preference. The endpoint has always reported
it as `updater.env_disabled`; the renderer read only `config.auto_update` and
threw the override away.

So the machine could never update, and the one surface that could have said so
said the opposite. That is the same defect as a card reporting a zero it
cannot stand behind, and it is why a node sat four releases behind while its
owner had every reason to believe it was current.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_JS = os.path.join(REPO, "clawmetry", "static", "js", "app.js")


def _render(is_on, env_disabled):
    """Run the shipped _renderAutoUpdateToggle against a fake DOM."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node not available")
    src = open(APP_JS, encoding="utf-8").read()
    m = re.search(r"function _renderAutoUpdateToggle\(isOn, envDisabled\) \{.*?\n\}", src, re.S)
    assert m, "the renderer's signature changed; the override may have been dropped"
    harness = """
var els = {
  'update-banner-auto': {style:{}, title:'', dataset:{}},
  'update-banner-auto-toggle': {style:{}, checked:null},
  'update-banner-auto-label': {textContent:''},
};
global.document = { getElementById: function(id){ return els[id] || null; } };
global.window = { CLOUD_MODE: false };
global.t = function(key, vars, dflt){ return dflt; };
%s
_renderAutoUpdateToggle(%s, %s);
console.log(JSON.stringify({
  label: els['update-banner-auto-label'].textContent,
  boxDisplay: els['update-banner-auto-toggle'].style.display,
  boxChecked: els['update-banner-auto-toggle'].checked,
  title: els['update-banner-auto'].title,
}));
""" % (m.group(0), "true" if is_on else "false", "true" if env_disabled else "false")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(harness)
        path = fh.name
    try:
        p = subprocess.run([node, path], capture_output=True, text=True, timeout=20)
        assert p.returncode == 0, p.stderr
        return json.loads(p.stdout.strip().splitlines()[-1])
    finally:
        os.unlink(path)


def test_the_kill_switch_is_never_reported_as_auto_update_on():
    """The exact founder state: stored preference on, env override off."""
    out = _render(is_on=True, env_disabled=True)
    assert "on this machine" in out["label"]
    assert "Auto-update on" != out["label"], (
        "the banner claimed auto-update was on for a node that cannot update")
    assert out["boxDisplay"] == "none", (
        "a control that cannot take effect must not be offered")
    assert "CLAWMETRY_AUTO_UPDATE=0" in out["title"], "say WHY, not just that"


def test_a_normal_node_is_unchanged():
    on = _render(is_on=True, env_disabled=False)
    assert on["label"] == "Auto-update on"
    assert on["boxChecked"] is True
    assert on["boxDisplay"] == ""

    off = _render(is_on=False, env_disabled=False)
    assert off["label"] == "Auto-update"
    assert off["boxChecked"] is False


def test_the_renderer_is_actually_given_the_override():
    """A correct renderer reached with the wrong arguments fixes nothing."""
    src = open(APP_JS, encoding="utf-8").read()
    assert "data.updater && data.updater.env_disabled" in src, (
        "the caller no longer forwards updater.env_disabled, so the renderer "
        "can never see the kill switch")


def test_the_endpoint_still_reports_the_override():
    """The frontend fix relies on this field; pin it so a backend tidy-up
    cannot silently remove the only honest signal."""
    src = open(os.path.join(REPO, "routes", "update_check.py"), encoding="utf-8").read()
    assert '"env_disabled": _env_auto_update_disabled()' in src
