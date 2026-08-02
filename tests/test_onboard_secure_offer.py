"""Onboard's agent-security-monitoring offer (numbat via `clawmetry secure`).

Pins the founder decision (2026-08-02): the wizard ASKS with a visible
default-yes [Y/n] instead of auto-enabling — hook install edits each
harness's own config, so it must never happen without an answer. The
wizard's yes is the consent, so cmd_enable runs with yes=True and must not
re-prompt; every no-answer path (decline, EOF) leaves agent configs alone.
"""
import argparse

import pytest

import clawmetry.cli as cli
import clawmetry.secure as secure


@pytest.fixture
def secure_env(monkeypatch):
    """Stub the secure module: no existing install, record enable calls."""
    state = {"enable": []}

    def _fake_enable(args):
        state["enable"].append(args)
        return 0

    monkeypatch.setattr(secure, "find_numbat", lambda: None)
    monkeypatch.setattr(secure, "cmd_enable", _fake_enable)
    return state


def _offer(answer_fn):
    plain = lambda t: t
    cli._maybe_offer_secure(answer_fn, plain, plain, plain)


def test_empty_enter_enables_with_consent_flag(secure_env, capsys):
    _offer(lambda _p="": "")
    assert len(secure_env["enable"]) == 1, "default Enter must enable"
    ns = secure_env["enable"][0]
    assert ns.yes is True, "the wizard answer IS the consent — no re-prompt"
    assert getattr(ns, "emit_all", False) is False, "onboard wires findings-only"
    out = capsys.readouterr().out
    assert "clawmetry secure disable" in out, "undo path must be shown up front"


def test_explicit_yes_enables(secure_env):
    _offer(lambda _p="": "y")
    assert len(secure_env["enable"]) == 1


def test_decline_leaves_configs_alone_and_hints(secure_env, capsys):
    _offer(lambda _p="": "n")
    assert secure_env["enable"] == [], "decline must not touch agent configs"
    assert "clawmetry secure enable" in capsys.readouterr().out


def test_eof_never_enables(secure_env):
    def _eof(_p=""):
        raise EOFError

    _offer(_eof)
    assert secure_env["enable"] == [], "no interactive answer -> never enable"


def test_existing_install_skips_offer_entirely(secure_env, monkeypatch, capsys):
    monkeypatch.setattr(secure, "find_numbat", lambda: "/usr/local/bin/numbat")
    _offer(lambda _p="": pytest.fail("must not prompt when numbat is present"))
    assert secure_env["enable"] == []
    assert "Agent security monitoring" not in capsys.readouterr().out


def test_enable_failure_is_soft_and_hints_retry(secure_env, monkeypatch, capsys):
    monkeypatch.setattr(secure, "cmd_enable",
                        lambda a: (_ for _ in ()).throw(RuntimeError("boom")))
    _offer(lambda _p="": "y")  # must not raise out of onboarding
    assert "Try again later" in capsys.readouterr().out


def test_post_onboard_offers_runs_both_extras(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "_maybe_apply_nemoclaw_preset",
                        lambda *a, **k: calls.append("nemoclaw"))
    monkeypatch.setattr(cli, "_maybe_offer_secure",
                        lambda *a, **k: calls.append("secure"))
    plain = lambda t: t
    cli._post_onboard_offers(lambda _p="": "", plain, plain, plain)
    assert calls == ["nemoclaw", "secure"]
