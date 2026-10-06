"""Guards for the GitHub bridge (scripts/bug_report_sync.py).

The issue it files is PUBLIC. Two things must therefore hold for every
report, forever:

  * nothing identifying the reporter reaches the issue, and
  * the title cannot match close-bot-noise.yml's auto-close prefixes, or a
    real user's report would be closed by a bot within seconds of being
    filed.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SPEC = importlib.util.spec_from_file_location(
    "bug_report_sync", os.path.join(_ROOT, "scripts", "bug_report_sync.py"))
sync = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sync)

_REPORT = {
    "ticket": "CM-4F2K9Q1X",
    "title": "Cost tab shows zero for Claude Code",
    "body": "Opened Cost, every runtime reads $0.00 although sessions ran.",
    "severity": "major",
    "version": "0.12.909",
    "runtime": "claude_code",
    "platform": "macOS-15.3-arm64",
    "python_version": "3.11.9",
    "source": "local",
    "surface": "usage",
}


def test_issue_body_carries_the_report_and_the_environment():
    body = sync.issue_body(_REPORT)
    assert "every runtime reads $0.00" in body
    assert "0.12.909" in body and "claude_code" in body
    assert "CM-4F2K9Q1X" in body, "the ticket is the join key back to the reporter"
    assert "major" in body


def test_issue_body_never_carries_the_reporter():
    """Defence in depth: the intake does not send the email in the sync
    payload, and this must not print one even if a future payload did."""
    leaky = dict(_REPORT, reporter_email="someone@example.com",
                 node_id="node-abc", install_id="install-xyz")
    body = sync.issue_body(leaky)
    assert "someone@example.com" not in body
    assert "node-abc" not in body and "install-xyz" not in body
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", body), \
        "an email address reached a public issue body"


def test_empty_description_still_reads_as_a_sentence():
    body = sync.issue_body(dict(_REPORT, body=""))
    assert "No further detail given" in body


def test_title_cannot_be_auto_closed_as_bot_noise():
    """close-bot-noise.yml closes any issue whose title starts with one of
    its agent/scan prefixes. A user's report must never match one.

    The ticket id leads the title precisely so it cannot: every auto-close
    prefix is a word in brackets, and ``[CM-...]`` is not one of them.
    """
    subject = f"[{_REPORT['ticket']}] {_REPORT['title']}"
    assert re.match(r"^\[CM-[0-9A-Z]{8}\] \S", subject)

    path = os.path.join(_ROOT, ".github", "workflows", "close-bot-noise.yml")
    if not os.path.exists(path):          # not on this branch yet
        pytest.skip("close-bot-noise.yml not present on this branch")
    prefixes = re.findall(r"startsWith\(github\.event\.issue\.title,\s*'([^']+)'\)",
                          open(path, encoding="utf-8").read())
    assert prefixes, "could not read the auto-close prefixes"
    for prefix in prefixes:
        assert not subject.startswith(prefix), \
            f"a user's bug report would be auto-closed by the {prefix!r} rule"


def test_severity_labels_cover_every_severity_the_intake_accepts():
    sys.path.insert(0, _ROOT)
    import routes.support as support
    for sev in support.SEVERITIES:
        assert sev in sync.SEVERITY_LABEL, f"{sev} has no GitHub label"


def test_no_token_is_a_quiet_no_op_not_a_crash(monkeypatch, capsys):
    """A fork or a repo without the secret must not red every 15 minutes."""
    monkeypatch.setattr(sync, "TOKEN", "")
    assert sync.main() == 0
    assert "nothing to do" in capsys.readouterr().out.lower()


def test_workflow_is_scheduled_and_scoped():
    wf = open(os.path.join(_ROOT, ".github", "workflows",
                           "bug-report-sync.yml"), encoding="utf-8").read()
    assert "schedule:" in wf and "cron:" in wf
    assert "issues: write" in wf, "the job cannot file an issue without this"
    assert "CLAWMETRY_BUGSYNC_TOKEN" in wf
    assert "github.repository == 'vivekchand/clawmetry'" in wf, \
        "a fork would run this on its own schedule"


def test_a_screenshot_is_named_but_never_embedded_in_the_public_issue():
    """The reporter sent the image to us. Saying it exists is useful; putting
    it on a public tracker is a disclosure they did not agree to."""
    body = sync.issue_body(dict(_REPORT, has_screenshot=True))
    assert "screenshot" in body.lower()
    assert "data:image" not in body
    assert "held privately" in body


def test_no_screenshot_means_no_mention():
    assert "screenshot" not in sync.issue_body(_REPORT).lower()
