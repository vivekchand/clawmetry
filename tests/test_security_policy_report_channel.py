"""SECURITY.md must not send reporters to a form that answers 404.

GitHub's private vulnerability reporting is not enabled on this repository,
so ``/security/advisories/new`` is not a form an external reporter can reach:
unauthenticated and non-member visitors get a 404. SECURITY.md advertised it
anyway, and a reporter followed it, hit the 404, and fell back to email --
saying so in their report (2026-10-25, GHSA-6r57-3vhv-2wpf).

A dead reporting channel in a security policy costs reports that are never
sent, which is the one failure mode this file exists to prevent. These checks
hold the policy to naming a channel that works. If private reporting is
turned on later, the link becomes correct and this test is what should be
updated to require it.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
POLICY = ROOT / "SECURITY.md"


@pytest.fixture(scope="module")
def policy_text():
    assert POLICY.is_file(), "SECURITY.md is missing"
    text = POLICY.read_text(encoding="utf-8")
    assert text.strip(), "SECURITY.md is empty"
    return text


def test_policy_does_not_link_the_disabled_advisory_form(policy_text):
    assert "advisories/new" not in policy_text, (
        "SECURITY.md links GitHub's private advisory form, which is not "
        "enabled on this repository and answers 404 for external reporters. "
        "Either enable private vulnerability reporting or drop the link."
    )


def test_policy_names_the_security_mailbox(policy_text):
    assert "security@clawmetry.com" in policy_text, (
        "SECURITY.md must name the private reporting mailbox."
    )


def test_policy_still_tells_reporters_not_to_use_a_public_issue(policy_text):
    assert re.search(r"not open a public issue", policy_text), (
        "SECURITY.md must keep telling reporters not to file a security bug "
        "as a public issue."
    )


def test_the_guard_would_fail_on_the_text_it_was_written_against():
    """The regression this pins, demonstrated red against the old wording."""
    before = (
        "- **Report a vulnerability:** security@clawmetry.com, or a\n"
        "  [private GitHub advisory]"
        "(https://github.com/vivekchand/clawmetry/security/advisories/new).\n"
    )
    assert "advisories/new" in before, "fixture no longer carries the dead link"
    assert "advisories/new" not in POLICY.read_text(encoding="utf-8")
