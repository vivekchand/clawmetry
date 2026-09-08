"""OTP sign-in recovery (founder live-hit 2026-07-30).

A typo'd email or a code that never arrives used to dead-end the wizard:
no resend, no change-email, a stray Enter burned one of the 3 attempts,
and three failures dropped to a raw paste-an-API-key prompt. These tests
drive _get_api_key_interactive with a scripted server + scripted input and
pin every recovery path.
"""
import pytest

import clawmetry.cli as cli


class _Server:
    """Scripted /api/auth/email-otp endpoint; records every call."""

    def __init__(self, good_email="right@x.com", good_otp="123456"):
        self.calls = []
        self.good_email = good_email
        self.good_otp = good_otp

    def post(self, url, body, timeout=15):
        action = body.get("action")
        self.calls.append((action, body.get("email"), body.get("otp")))
        if action == "send":
            return {}, 200
        if action == "verify":
            if body.get("email") == self.good_email and body.get("otp") == self.good_otp:
                return {"api_key": "cm_recovered", "is_new": True}, 200
            return {"error": "Invalid code."}, 401
        return {"error": "unexpected"}, 400


@pytest.fixture
def wizard(monkeypatch):
    server = _Server()
    monkeypatch.setattr(cli, "_post_json", server.post)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    def run(inputs):
        feed = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _p="": next(feed))
        return cli._get_api_key_interactive(), server

    return run


def test_corrected_email_at_code_prompt_resends_and_signs_in(wizard):
    """Typing the right email AT THE CODE PROMPT switches to it: a new code
    is sent there and verification succeeds — no restart."""
    key, server = wizard(["typo@x.com", "right@x.com", "123456"])
    assert key == "cm_recovered"
    sends = [c[1] for c in server.calls if c[0] == "send"]
    assert sends == ["typo@x.com", "right@x.com"]
    assert ("verify", "right@x.com", "123456") in server.calls


def test_r_resends_code_without_burning_attempts(wizard):
    key, server = wizard(["right@x.com", "r", "r", "123456"])
    assert key == "cm_recovered"
    assert [c[0] for c in server.calls].count("send") == 3  # initial + 2 resends
    assert ("verify", "right@x.com", "123456") in server.calls


def test_blank_enter_never_burns_an_attempt(wizard):
    key, server = wizard(["right@x.com", "", "", "", "", "123456"])
    assert key == "cm_recovered"
    assert [c[0] for c in server.calls].count("verify") == 1


def test_three_wrong_codes_still_recoverable_with_new_email(wizard):
    key, server = wizard([
        "typo@x.com", "000000", "000001", "000002",  # 3 wrong codes
        "right@x.com",                                # recovery prompt: new email
        "123456",
    ])
    assert key == "cm_recovered"
    sends = [c[1] for c in server.calls if c[0] == "send"]
    assert sends == ["typo@x.com", "right@x.com"]


def test_invalid_email_gets_one_retry(wizard):
    key, server = wizard(["not-an-email", "right@x.com", "123456"])
    assert key == "cm_recovered"
