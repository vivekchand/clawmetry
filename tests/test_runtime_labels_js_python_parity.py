"""CI guard: Python ``RUNTIME_LABELS`` must match the JS ``_CM_RT_LABEL``
runtime-switcher dictionary.

``clawmetry/entitlements.py`` advertises a label for every known runtime; the
dashboard frontend hard-codes the same map in ``clawmetry/static/js/app.js``
as ``_CM_RT_LABEL``. The JS dict is the source of truth for:

* the runtime chip switcher (``_cmRenderRuntimeSwitcher`` only renders keys
  that exist in ``_CM_RT_LABEL``),
* the session-id-prefix runtime detector (``_cmRuntimeOf`` only recognises
  prefixes that exist in ``_CM_RT_LABEL`` -- anything else falls back to
  ``openclaw``),
* the global header switcher's display labels.

If a runtime is in the Python catalogue but missing from the JS dict, sessions
for that runtime are silently classified as OpenClaw and never get their own
chip. Burned 2026-06-02: ``nemoclaw`` was in ``RUNTIME_LABELS`` (Free tier)
but absent from ``_CM_RT_LABEL`` -- NemoClaw sessions vanished from the
switcher. This guard pins the two sides together so the next runtime can't
drift the same way.
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_APP_JS = os.path.join(_REPO_ROOT, "clawmetry", "static", "js", "app.js")


def _parse_js_label_dict() -> dict:
    """Pull the ``_CM_RT_LABEL = { ... }`` dict out of ``app.js`` and parse it
    into a Python dict. Tolerant of trailing commas and any whitespace/line
    layout; rejects entries that are not a simple ``ident: 'string'`` pair so
    the test fails loudly on malformed JS rather than silently passing."""
    with open(_APP_JS, "r", encoding="utf-8") as fh:
        src = fh.read()
    m = re.search(r"var\s+_CM_RT_LABEL\s*=\s*\{([^}]*)\}", src)
    assert m, f"_CM_RT_LABEL declaration not found in {_APP_JS}"
    body = m.group(1)
    out: dict = {}
    for pair in re.finditer(
        r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*'([^']*)'", body
    ):
        out[pair.group(1)] = pair.group(2)
    assert out, "_CM_RT_LABEL parsed empty -- JS layout changed, update the test"
    return out


@pytest.fixture(scope="module")
def js_labels() -> dict:
    return _parse_js_label_dict()


def test_every_python_runtime_has_js_label(js_labels):
    """Every key in ``RUNTIME_LABELS`` must appear in ``_CM_RT_LABEL``."""
    from clawmetry.entitlements import RUNTIME_LABELS

    missing = sorted(set(RUNTIME_LABELS) - set(js_labels))
    assert not missing, (
        f"_CM_RT_LABEL (clawmetry/static/js/app.js) is missing runtime(s) "
        f"present in Python RUNTIME_LABELS: {missing}. Add them to the JS "
        f"dict or the runtime chip switcher will silently drop those sessions."
    )


def test_every_js_runtime_has_python_label(js_labels):
    """Every key in ``_CM_RT_LABEL`` must appear in ``RUNTIME_LABELS`` -- a JS
    entry without a Python counterpart means the catalogue side does not know
    about the runtime and ``/api/runtimes`` will not advertise it."""
    from clawmetry.entitlements import RUNTIME_LABELS

    extra = sorted(set(js_labels) - set(RUNTIME_LABELS))
    assert not extra, (
        f"_CM_RT_LABEL has runtime(s) not in Python RUNTIME_LABELS: {extra}. "
        f"Add them to clawmetry/entitlements.py RUNTIME_LABELS (and the "
        f"FREE_RUNTIMES / PAID_RUNTIMES sets) or remove them from the JS dict."
    )


def test_label_strings_match_between_python_and_js(js_labels):
    """The display labels must agree -- a mismatch means the dashboard shows a
    different name than the API response and the chip will look inconsistent
    next to the tab title."""
    from clawmetry.entitlements import RUNTIME_LABELS

    mismatches = sorted(
        (rt, RUNTIME_LABELS[rt], js_labels[rt])
        for rt in RUNTIME_LABELS
        if rt in js_labels and RUNTIME_LABELS[rt] != js_labels[rt]
    )
    assert not mismatches, (
        f"Display-label drift between Python RUNTIME_LABELS and JS "
        f"_CM_RT_LABEL (id, py, js): {mismatches}"
    )


def test_free_runtimes_all_present_in_js(js_labels):
    """Free-tier runtimes must always render in the switcher -- they are the
    OSS install's actual runtimes. A missing one means the user can't filter
    to it and its sessions get bucketed under openclaw."""
    from clawmetry.entitlements import FREE_RUNTIMES

    missing = sorted(set(FREE_RUNTIMES) - set(js_labels))
    assert not missing, (
        f"_CM_RT_LABEL missing FREE_RUNTIMES: {missing}. The runtime switcher "
        f"will silently classify these sessions as openclaw."
    )
