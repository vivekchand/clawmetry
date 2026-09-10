"""An alarm that cannot clear is not an alarm (#5739).

`field-failure-issues.yml` files one deduped issue per failure signature and
refreshes it daily while it keeps happening. It had no third state. A
signature that STOPPED simply aged out of the aggregate window, and its issue
stayed open forever with the last comment still reading "Still occurring" --
which is how #5739 (one install, one event, silent afterwards) would have sat
on the tracker indefinitely.

These tests execute the reconcile step's real shell, extracted from the
workflow file, against a fake `gh`. Asserting on the YAML text would pass just
as happily for a step that parses and does nothing, which is the failure mode
this whole workflow exists to catch.

The load-bearing case is `test_an_unreachable_endpoint_closes_nothing`:
absence of evidence must never read as evidence of absence, or one network
blip sweeps the tracker.
"""
from __future__ import annotations

import json
import os
import subprocess
import textwrap

import pytest

yaml = pytest.importorskip("yaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "field-failure-issues.yml")

OPEN_ISSUES = [
    {"number": 5739, "title": "[field-failure] no_distribution on Windows (py 3.11)"},
    {"number": 5628, "title": "[field-failure] compiler_demand on Windows (py 3.14)"},
]
LIVE_5739 = "[field-failure] no_distribution on Windows (py 3.11)"
LIVE_5628 = "[field-failure] compiler_demand on Windows (py 3.14)"

FAKE_GH = textwrap.dedent(
    """\
    #!/bin/bash
    case "$1 $2" in
      "issue list")    cat "$FF_OPEN_ISSUES";;
      "issue comment") echo "COMMENT $3" >> "$FF_LOG";;
      "issue close")   echo "CLOSE $3" >> "$FF_LOG";;
      *) : ;;
    esac
    """
)


def _reconcile_script() -> str:
    doc = yaml.safe_load(open(WORKFLOW, encoding="utf-8"))
    steps = doc["jobs"]["file-issues"]["steps"]
    matching = [s for s in steps if s.get("name", "").startswith("Close issues")]
    assert matching, "the workflow has no step that closes resolved signatures"
    return matching[0]["run"]


def _run(tmp_path, live_titles):
    """Run the real reconcile step. `live_titles=None` means no snapshot at
    all, i.e. the endpoint was unreachable and the filing step bailed."""
    binp = tmp_path / "bin"
    binp.mkdir()
    gh = binp / "gh"
    gh.write_text(FAKE_GH)
    gh.chmod(0o755)

    (tmp_path / "open.json").write_text(json.dumps(OPEN_ISSUES))
    log = tmp_path / "log"
    log.write_text("")
    script = tmp_path / "reconcile.sh"
    script.write_text(_reconcile_script())

    # The step reads a fixed /tmp path, which is also what the real runner
    # gives it; each case sets or clears it.
    for f in ("/tmp/live-titles.txt", "/tmp/live-window.txt"):
        if os.path.exists(f):
            os.unlink(f)
    if live_titles is not None:
        with open("/tmp/live-titles.txt", "w") as fh:
            fh.write("".join(t + "\n" for t in live_titles))
        with open("/tmp/live-window.txt", "w") as fh:
            fh.write("30\n")

    env = dict(os.environ)
    env.update(
        PATH="{}:{}".format(binp, env["PATH"]),
        FF_OPEN_ISSUES=str(tmp_path / "open.json"),
        FF_LOG=str(log),
        REPO="vivekchand/clawmetry",
        GH_TOKEN="fake",
    )
    proc = subprocess.run(["bash", str(script)], env=env,
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    closed = sorted(
        line.split()[1] for line in log.read_text().splitlines()
        if line.startswith("CLOSE")
    )
    return closed, proc.stdout


def test_a_signature_that_still_occurs_is_left_open(tmp_path):
    closed, _ = _run(tmp_path, [LIVE_5739, LIVE_5628])
    assert closed == [], closed


def test_a_signature_that_stopped_is_closed(tmp_path):
    """The #5739 case: still-live 5628 stays, silent 5739 closes."""
    closed, _ = _run(tmp_path, [LIVE_5628])
    assert closed == ["5739"], closed


def test_zero_live_signatures_closes_every_open_issue(tmp_path):
    """An empty signature list is real data -- nothing is failing anywhere --
    and is precisely when the tracker should end up clean. The malformed-payload
    guard in the filing step is what keeps this from firing on a shape change."""
    closed, _ = _run(tmp_path, [])
    assert closed == ["5628", "5739"], closed


def test_an_unreachable_endpoint_closes_nothing(tmp_path):
    """No snapshot means no evidence of absence. A blip must not sweep the
    tracker, so the step exits without touching a single issue."""
    closed, out = _run(tmp_path, None)
    assert closed == [], closed
    assert "closing nothing" in out


def test_every_closure_says_what_it_does_not_know(tmp_path):
    """A closure comment that implies "fixed" would be a fabrication: from an
    aggregate, a shipped fix and the last affected machine going away are
    indistinguishable."""
    script = _reconcile_script()
    assert "not why" in script
    assert "not a claim that anything was repaired" in script
    assert "files a fresh issue" in script


def test_the_filing_step_refuses_a_payload_with_no_window(tmp_path):
    """The reconcile step trusts the snapshot completely, so the filing step
    must not write one from a payload it cannot recognise."""
    doc = yaml.safe_load(open(WORKFLOW, encoding="utf-8"))
    filing = doc["jobs"]["file-issues"]["steps"][0]["run"]
    assert "window_days" in filing
    assert "nothing filed or closed" in filing
    # The snapshot file is created only AFTER that guard.
    assert filing.index("window_days") < filing.index("/tmp/live-titles.txt")
