"""Anti-hallucination guard: the per-runtime sidebar tab visibility must DERIVE
from each adapter's DECLARED ``Capability`` enum, never from an LLM's prose.

Burned 2026-06-03: a workflow agent hallucinated NemoClaw as a "NeMo toolkit"
(it is sandboxed OpenClaw running the OpenClaw adapter); the tab config inherited
the error. Fix = derive the frontend's ``_CM_RT_CAPS`` from the contract. This
test re-extracts the contract and asserts the frontend matches, so the guarantee
is mechanical, not "trust me".

Scope: the OSS adapter (openclaw) — its declared capabilities must equal the
frontend's ``_CM_RT_CAPS.openclaw``. The closed pro adapters are guarded by the
parallel test in clawmetry-pro. Also checks internal consistency (every cap used
in ``_CM_RT_CAPS`` is mapped in ``_CM_CAP_TABS``).
"""
from __future__ import annotations

import os
import re

_HERE = os.path.dirname(__file__)
_APP_JS = os.path.join(_HERE, "..", "clawmetry", "static", "js", "app.js")
_OPENCLAW = os.path.join(_HERE, "..", "clawmetry", "adapters", "openclaw.py")


def _declared_caps_openclaw() -> set:
    """Extract the Capability.* names returned by openclaw.py's capabilities()."""
    src = open(_OPENCLAW, encoding="utf-8").read()
    m = re.search(r"def capabilities\(self\).*?\{(.*?)\}", src, re.S)
    assert m, "openclaw.py capabilities() not found"
    return set(re.findall(r"Capability\.([A-Z_]+)", m.group(1)))


def _frontend_caps() -> dict:
    """Parse the _CM_RT_CAPS map from app.js -> {runtime: set(caps)}."""
    src = open(_APP_JS, encoding="utf-8").read()
    m = re.search(r"var _CM_RT_CAPS = \{(.*?)\n\};", src, re.S)
    assert m, "_CM_RT_CAPS not found in app.js"
    out = {}
    for line in m.group(1).splitlines():
        lm = re.match(r"\s*(\w+):\s*\[(.*?)\]", line)
        if lm:
            caps = set(re.findall(r"'([A-Z_]+)'", lm.group(2)))
            out[lm.group(1)] = caps
    return out


def _cap_tabs_keys() -> set:
    src = open(_APP_JS, encoding="utf-8").read()
    m = re.search(r"var _CM_CAP_TABS = \{(.*?)\n\};", src, re.S)
    assert m, "_CM_CAP_TABS not found in app.js"
    return set(re.findall(r"\n\s*([A-Z_]+):", m.group(1)))


def test_openclaw_frontend_caps_match_declared():
    declared = _declared_caps_openclaw()
    fe = _frontend_caps()
    assert "openclaw" in fe, "openclaw missing from _CM_RT_CAPS"
    assert fe["openclaw"] == declared, (
        f"_CM_RT_CAPS.openclaw drifted from openclaw.py capabilities(): "
        f"frontend-only={fe['openclaw'] - declared}, declared-only={declared - fe['openclaw']}"
    )


def test_nemoclaw_inherits_openclaw_caps():
    # NemoClaw = sandboxed OpenClaw (runs the OpenClaw adapter) -> identical caps.
    fe = _frontend_caps()
    assert fe.get("nemoclaw") == fe.get("openclaw"), (
        "nemoclaw must share OpenClaw's capabilities (it is sandboxed OpenClaw)"
    )


def test_every_used_capability_is_mapped_to_tabs():
    fe = _frontend_caps()
    mapped = _cap_tabs_keys()
    used = set().union(*fe.values()) if fe else set()
    # LOGS = a node-wide tab outside this sidebar set; BRAIN = the brain tab is
    # already enabled by EVENTS (every adapter with the live stream). Both are
    # intentionally not unique keys in _CM_CAP_TABS.
    unmapped = used - mapped - {"LOGS", "BRAIN"}
    assert not unmapped, f"capabilities used in _CM_RT_CAPS but not mapped in _CM_CAP_TABS: {unmapped}"
