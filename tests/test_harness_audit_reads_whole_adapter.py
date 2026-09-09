"""The harness audit must not report absence from a file it only partly read.

`scripts/harness/audit.py` asks a model to list signals a runtime exposes that
ClawMetry's adapter does NOT capture. That task is uniquely vulnerable to
truncation: the model is reasoning about ABSENCE, so a clipped file reads
exactly like a missing feature, and it has no way to tell the difference.

It happened twice. The cap was raised to 60k after aider's conditional COST at
line ~527 was cut and the audit wrongly flagged "no COST". Then
`clawmetry/adapters/openclaw.py` grew to 193k, so 69% of it went unread again,
silently, for BOTH runtimes this audit covers -- while the prompt kept telling
the model the adapter was "provided in full". That is how #5750 was filed at
severity **high** against a `NEMOCLAW_TRACE_FILE` reader sitting at line 1690,
roughly 18k characters past the cut, with `nemoclawOnboardTraceStatus` on the
detection record and REQ-OBS-RSO-034 specifying the whole capability.

The cost is not a wasted CI minute. It is a high-severity issue in the tracker
that a human or an agent has to read, reproduce and disprove, against code that
was already shipped.

These guards auto-discover from the manifest, so an adapter that grows past the
budget tomorrow fails here instead of quietly filing fiction.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts", "harness"))

audit = pytest.importorskip("audit")


def _harnesses():
    with open(os.path.join(REPO, "scripts", "harness", "manifest.json")) as f:
        m = json.load(f)
    rows = m if isinstance(m, list) else m.get("harnesses", m)
    out = []
    for h in rows:
        if not isinstance(h, dict) or not h.get("adapter"):
            continue
        if os.path.exists(os.path.join(REPO, h["adapter"])):
            out.append(h)
    return out


@pytest.mark.parametrize("h", _harnesses(), ids=lambda h: h.get("runtime", "?"))
def test_the_audited_adapter_is_read_whole(h):
    """The budget must exceed every adapter this repo actually audits."""
    src, trimmed = audit._adapter_source(h)
    on_disk = os.path.getsize(os.path.join(REPO, h["adapter"]))
    assert not trimmed, (
        f"{h['adapter']} is {on_disk} bytes and exceeds the audit's source "
        f"budget, so the model would judge absence from a partial file"
    )
    # The tail is where capabilities() and cost-derivation live.
    with open(os.path.join(REPO, h["adapter"]), encoding="utf-8",
              errors="replace") as f:
        whole = f.read()
    assert src.endswith(whole[-200:]), "the adapter's tail did not survive"


@pytest.mark.parametrize("h", _harnesses(), ids=lambda h: h.get("runtime", "?"))
def test_the_prompt_never_claims_completeness_it_does_not_have(h):
    """The regression that made #5750 confident.

    Telling a model the file is complete when it is not is worse than saying
    nothing: it converts "I did not see it" into "it is not there".
    """
    src, trimmed = audit._adapter_source(h)
    whole = audit._build_prompt(h, "surface", src, "caps", "", trimmed=False)
    assert "COMPLETE file" in whole

    clipped = audit._build_prompt(h, "surface", src[:1000], "caps", "", trimmed=True)
    assert "TRIMMED" in clipped
    assert "COMPLETE file, start to end" not in clipped
    assert "provided in\nfull" not in clipped and "provided in full" not in clipped


def test_the_index_is_complete_even_when_the_body_is_not():
    """The index is what keeps an absence claim checkable under trimming."""
    src = (
        'def alpha():\n    pass\n'
        + "# filler\n" * 500
        + 'def omega():\n    x = os.environ.get("NEMOCLAW_TRACE_FILE", "")\n'
    )
    idx = audit._adapter_index(src)
    assert "alpha" in idx and "omega" in idx
    assert "NEMOCLAW_TRACE_FILE" in idx


def test_the_index_reaches_symbols_past_the_old_60k_cap():
    """Concretely: the thing #5750 said did not exist."""
    h = next((x for x in _harnesses()
              if x.get("adapter", "").endswith("openclaw.py")), None)
    if h is None:
        pytest.skip("openclaw adapter not in the manifest")
    src, _ = audit._adapter_source(h)
    assert "NEMOCLAW_TRACE_FILE" in src, "the reader must be in the body now"
    assert src.index("NEMOCLAW_TRACE_FILE") > 60000, (
        "this symbol is the regression witness: it must sit past the old cap, "
        "or this test stops proving anything"
    )
    assert "NEMOCLAW_TRACE_FILE" in audit._adapter_index(src)
