"""The first-run report must not call a working install empty (#5766).

Reported from a hosted node page whose header read "Claude Code · 1281
sessions" while the panel underneath it said "No agent sessions on this
machine yet ... No supported runtime was detected".

Two independent faults, one guarded here per fault:

  * the count gate treated a MISSING key as a zero. `/api/overview` has no
    single canonical session-count field — OSS serves `sessions` and
    `sessionCount`, and the cloud node page builds the payload client-side
    out of the encrypted snapshot with `sessionCount` only. The behaviour is
    pinned in ``test_first_run_gate_js.js`` against the shipped source;
  * the panel is a LOCAL-machine diagnostic. It probes this machine's
    runtime paths and prescribes ``clawmetry connect`` / ``clawmetry
    --sample``. On a hosted node page the probe runs inside the cloud
    container, so it answered for the server while the reader was looking at
    their laptop. It must not render there at all.

Recorded as ADR-006 on the Sample Mode and First-Run Report blueprint
(89dfab4d-d6c1-4c72-9222-0e68acd0eeaa), which also carries the amended
scope contract: local dashboards only, and only on a payload that
positively reports zero.

The Node suite is a required gate here rather than a sibling of
``test_appjs_units.py``: that file is green locally and named in no CI job,
which is how a guard rots without anyone noticing.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_first_run_gate_js.js")
_APP_JS = os.path.join(_HERE, "..", "clawmetry", "static", "js", "app.js")


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_first_run_gate_unit_suite() -> None:
    proc = subprocess.run(
        ["node", _JS_TEST], capture_output=True, text=True, timeout=30
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "first-run gate tests failed:\n" + output
    assert "PASS" in output, "no PASS line in output:\n" + output


def _render_body() -> str:
    src = open(_APP_JS, encoding="utf-8").read()
    m = re.search(r"^async function renderFirstRunReport\b[\s\S]*?^\}", src, re.M)
    assert m, "renderFirstRunReport not found in app.js"
    return m.group(0)


def test_panel_never_renders_on_a_hosted_node_page() -> None:
    """A local-machine diagnostic has no honest answer on cloud."""
    body = _render_body()
    gate = re.search(
        r"if \(window\.CLOUD_MODE\) \{[^}]*el\.style\.display = 'none';[^}]*return;",
        body,
    )
    assert gate, "renderFirstRunReport does not bail out under window.CLOUD_MODE"
    # And it must bail BEFORE it probes for runtimes — the probe is the part
    # that answers about the wrong machine.
    assert body.index("CLOUD_MODE") < body.index("runtime-detection"), (
        "the CLOUD_MODE bail-out must come before the runtime-detection probe"
    )


def test_the_gate_asks_looks_empty_not_a_raw_key_lookup() -> None:
    """Pins the seam so a later edit cannot re-inline a three-key guess."""
    body = _render_body()
    assert "_frrLooksEmpty(overview)" in body, (
        "the emptiness decision must go through _frrLooksEmpty"
    )


def test_session_key_list_covers_the_cloud_payload() -> None:
    """`sessionCount` is the ONLY count the cloud node page ships."""
    src = open(_APP_JS, encoding="utf-8").read()
    m = re.search(r"var _FRR_SESSION_KEYS = \[([\s\S]*?)\];", src)
    assert m, "_FRR_SESSION_KEYS not found in app.js"
    keys = set(re.findall(r"'([^']+)'", m.group(1)))
    for required in ("sessions", "sessionCount"):
        assert required in keys, f"{required} missing from _FRR_SESSION_KEYS: {keys}"
