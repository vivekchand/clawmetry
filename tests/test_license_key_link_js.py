"""The trial banner's "I have a license key" link opened nothing (2026-09-26).

Field report from a live dashboard on an active trial ("Your trial ends in
3 days"): clicking the link next to the Get-a-license CTA did nothing at
all — no modal, no error, no console noise.

The link calls ``shmShowLicense()``, which switched the self-host modal to
its 'license' step and stopped there. Called from inside the modal — its
only caller until the banner shipped — that is correct, because
``openSelfhostModal()`` has already set ``#selfhost-modal-overlay`` to
``display:flex``. The banner calls it with the overlay still ``none``, so
the step flipped behind a hidden parent and nothing painted.

The behaviour is pinned in ``test_license_key_link_js.js``, which loads the
shipped ``onboarding.js`` against a stub DOM and asserts a cold call raises
the overlay. This file also keeps the markup side honest: the banner link
must keep calling ``shmShowLicense``, and the modal must keep shipping the
paste step it opens onto.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_license_key_link_js.js")
_ROOT = os.path.dirname(_HERE)


def _read(relpath: str) -> str:
    with open(os.path.join(_ROOT, relpath), encoding="utf-8") as fh:
        return fh.read()


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_license_link_unit_suite() -> None:
    proc = subprocess.run(
        ["node", _JS_TEST], capture_output=True, text=True, timeout=30
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "license-key link tests failed:\n" + output
    assert "PASS" in output, "no PASS line in output:\n" + output


def test_show_license_raises_the_overlay_itself() -> None:
    """Pins the seam: the caller must not have to open the modal first."""
    js = _read("clawmetry/static/js/onboarding.js")
    anchor = js.find("window.shmShowLicense = function")
    assert anchor != -1, "shmShowLicense must exist in onboarding.js"
    body = js[anchor:anchor + 600]
    assert "selfhost-modal-overlay" in body, (
        "shmShowLicense must raise #selfhost-modal-overlay — a step switch "
        "inside a hidden overlay paints nothing and the link reads as dead"
    )
    assert "'flex'" in body


def test_banner_link_still_targets_the_paste_surface() -> None:
    html = _read("clawmetry/templates/partials/banners.html")
    anchor = html.find('id="license-expired-have-key"')
    assert anchor != -1, "the banner's license-key link is gone"
    assert "shmShowLicense" in html[anchor:anchor + 400]
    modal = _read("clawmetry/templates/partials/selfhost-modal.html")
    assert 'id="shm-step-license"' in modal, (
        "shmShowLicense opens onto #shm-step-license; without it the link "
        "is dead again"
    )
    assert 'id="shm-license-input"' in modal
