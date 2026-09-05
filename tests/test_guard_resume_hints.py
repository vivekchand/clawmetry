"""A stopped agent must be told apart from an uncontrollable one.

The field report: clicking Stop or Kill on a Claude Code session left the row
reading ``Running`` in the Status column and ``Not controllable`` in the
Control column — the tab contradicting itself, and neither half telling the
operator the one thing they now needed, which is how to get back into that
conversation.

Two contracts:

1. ``process_control.runtime_control_support`` answers ``state``, so a caller
   can tell "the process is gone" from "this runtime can never be signalled".
   Both used to arrive as ``controllable: False`` with only prose to separate
   them.
2. ``resume_hints.resume_hint`` answers, for EVERY runtime ClawMetry ships,
   either a real command line or an honest statement that no command exists.
   Never a plausible-looking flag: an operator who pastes a fabricated command
   and watches it fail stops believing the rest of the tab.
"""
import pytest

import clawmetry.process_control as pc
from clawmetry import resume_hints


# ── Every shipped runtime is answered, one way or another ────────────────
def test_every_shipped_runtime_has_an_entry():
    """A new runtime must not silently fall through to a shrug.

    ``entitlements`` is the authoritative runtime list (CLAUDE.md); this test
    is what makes adding a runtime without a resume answer a CI failure.
    """
    from clawmetry import entitlements
    shipped = set(entitlements.FREE_RUNTIMES) | set(entitlements.PAID_RUNTIMES)
    missing = sorted(shipped - resume_hints.known_runtimes())
    assert not missing, f"runtimes with no resume answer: {missing}"


def test_every_entry_says_something_actionable():
    """``unknown`` is allowed, blank is not — the UI must always have words."""
    from clawmetry import entitlements
    shipped = sorted(set(entitlements.FREE_RUNTIMES)
                     | set(entitlements.PAID_RUNTIMES))
    for rt in shipped:
        hint = resume_hints.resume_hint(rt, f"{rt}:abc-123")
        assert hint["kind"] in ("command", "app", "unknown"), rt
        assert hint["command"] or hint["note"], (
            f"{rt} offers neither a command nor an explanation")
        if hint["kind"] == "command":
            # A command we print must be attributable to something checkable.
            assert hint["source"], f"{rt} ships a command with no provenance"


# ── The namespaced id must not reach the command line ────────────────────
def test_command_carries_the_native_session_id():
    """The store namespaces ids ``<runtime>:<native>``; CLIs want the native
    half. Pasting ``claude --resume claude_code:47c0…`` fails, which is the
    same boundary that once made Pause/Stop/Kill inert on family runtimes."""
    hint = resume_hints.resume_hint(
        "claude_code", "claude_code:47c0dac8-d8ca-43ab-85b4-dea4bc74c12c")
    assert hint["kind"] == "command"
    assert hint["command"] == (
        "claude --resume 47c0dac8-d8ca-43ab-85b4-dea4bc74c12c")
    assert "claude_code:" not in hint["command"]


def test_bare_session_id_is_left_alone():
    hint = resume_hints.resume_hint("codex", "0199-abcd")
    assert hint["command"] == "codex resume 0199-abcd"


def test_a_colon_inside_a_native_id_survives():
    """Only an exact ``<runtime>:`` head is stripped."""
    hint = resume_hints.resume_hint("codex", "codex:a:b")
    assert hint["command"] == "codex resume a:b"


# ── Honesty ──────────────────────────────────────────────────────────────
def test_hosted_runtimes_offer_no_command():
    """A cloud-hosted agent has no local process AND no local resume command.
    Inventing one would be worse than the words."""
    for rt in ("replit", "lovable", "grok_bot", "n8n"):
        hint = resume_hints.resume_hint(rt, f"{rt}:1")
        assert hint["kind"] == "app", rt
        assert hint["command"] == "", rt
        assert hint["note"], rt


def test_unverified_runtime_says_so_rather_than_guessing():
    hint = resume_hints.resume_hint("nemoclaw", "nemoclaw:1")
    assert hint["kind"] == "unknown"
    assert hint["command"] == ""
    assert "nemoclaw" in hint["note"]


def test_unknown_runtime_never_raises():
    hint = resume_hints.resume_hint("not_a_runtime", "x")
    assert hint["kind"] == "unknown"
    assert hint["note"]


def test_exo_does_not_pretend_the_session_id_is_the_slug():
    """Exo resumes by conversation slug, not by the uuid we store. Printing the
    uuid would produce a line that fails, so the command keeps the placeholder
    and the note says where the slug comes from."""
    hint = resume_hints.resume_hint("exo", "exo:0199-uuid7")
    assert "0199-uuid7" not in hint["command"]
    assert "exo conversation list" in hint["note"]


# ── The runtime's own answer wins ─────────────────────────────────────────
def test_runtime_reported_resume_command_beats_the_table():
    """OpenClaw's gateway puts ``resumeCommand`` in session extra; it knows the
    live session key and this table only knows the command's shape."""
    hint = resume_hints.resume_hint(
        "openclaw", "sess-pty", {"resumeCommand": "openclaw attach sess-pty"})
    assert hint["command"] == "openclaw attach sess-pty"
    assert hint["source"] == "runtime"


def test_reported_alias_is_accepted():
    hint = resume_hints.resume_hint(
        "openclaw", "s1", {"resumeCmd": "openclaw attach s1"})
    assert hint["command"] == "openclaw attach s1"


def test_blank_reported_command_falls_back_to_the_table():
    hint = resume_hints.resume_hint("openclaw", "s1", {"resumeCommand": "   "})
    assert hint["command"] == "openclaw attach --session s1"


# ── control state ─────────────────────────────────────────────────────────
def _plat_ok(monkeypatch):
    monkeypatch.setattr(pc, "platform_support",
                        lambda: {"controllable": True, "reason": "", "note": ""})


def test_a_dead_claude_code_session_reads_exited_not_unsupported(monkeypatch):
    """This is the reported bug. Claude Code writes one per-pid session record
    per RUNNING process and removes it on exit, so absence is evidence the
    process ended — a fact the tab can act on, unlike "not controllable"."""
    _plat_ok(monkeypatch)
    monkeypatch.setattr(pc, "resolve_session",
                        lambda *a, **k: {"ok": False,
                                         "reason": "session_not_in_claude_map"})
    cap = pc.runtime_control_support("claude_code", "claude_code:dead", "")
    assert cap["controllable"] is False
    assert cap["state"] == "exited"


def test_an_exited_pid_reads_exited(monkeypatch):
    _plat_ok(monkeypatch)
    monkeypatch.setattr(pc, "resolve_session",
                        lambda *a, **k: {"ok": True, "pid": 999999})
    monkeypatch.setattr(pc, "is_alive", lambda pid: False)
    cap = pc.runtime_control_support("claude_code", "claude_code:x", "")
    assert cap["state"] == "exited"


def test_a_live_claude_code_session_reads_controllable(monkeypatch):
    _plat_ok(monkeypatch)
    monkeypatch.setattr(pc, "resolve_session",
                        lambda *a, **k: {"ok": True, "pid": 4242})
    monkeypatch.setattr(pc, "is_alive", lambda pid: True)
    cap = pc.runtime_control_support("claude_code", "claude_code:x", "")
    assert cap["controllable"] is True
    assert cap["state"] == "controllable"


def test_a_hosted_runtime_reads_unsupported_not_exited(monkeypatch):
    """grok_bot has no local process and never will. Offering "resume it" as if
    it had merely stopped would be a different lie from the one we fixed."""
    _plat_ok(monkeypatch)
    cap = pc.runtime_control_support("grok_bot", "grok_bot:1", "")
    assert cap["state"] == "unsupported"


def test_a_cursor_editor_session_reads_unsupported(monkeypatch):
    _plat_ok(monkeypatch)
    monkeypatch.setattr(
        pc, "resolve_session",
        lambda *a, **k: {"ok": False,
                         "reason": "cursor_editor_session_no_per_session_signal"})
    cap = pc.runtime_control_support("cursor", "cursor:1", "")
    assert cap["state"] == "unsupported"


def test_a_cursor_cli_session_with_no_process_reads_exited(monkeypatch):
    _plat_ok(monkeypatch)
    monkeypatch.setattr(
        pc, "resolve_session",
        lambda *a, **k: {"ok": False,
                         "reason": "cursor_cli_session_process_not_found"})
    cap = pc.runtime_control_support("cursor", "cursor:1", "")
    assert cap["state"] == "exited"


def test_an_unrecognised_resolver_reason_defaults_to_unknown(monkeypatch):
    """A new resolver code must not be read as "this agent stopped" by
    accident — that would put a Stopped pill on a session still burning money."""
    _plat_ok(monkeypatch)
    monkeypatch.setattr(pc, "resolve_session",
                        lambda *a, **k: {"ok": False, "reason": "brand_new_code"})
    cap = pc.runtime_control_support("cursor", "cursor:1", "")
    assert cap["state"] == "unknown"


def test_an_unsignalable_platform_reads_unsupported(monkeypatch):
    monkeypatch.setattr(pc, "platform_support",
                        lambda: {"controllable": False, "reason": "no primitive"})
    cap = pc.runtime_control_support("claude_code", "claude_code:1", "")
    assert cap["state"] == "unsupported"


def test_openclaw_is_controllable(monkeypatch):
    _plat_ok(monkeypatch)
    monkeypatch.setattr(pc, "openclaw_pause_capability",
                        lambda: {"effective": False, "detail": "no proxy"})
    cap = pc.runtime_control_support("openclaw", "s1", "")
    assert cap["state"] == "controllable"


@pytest.mark.parametrize("runtime", sorted(pc.SUPPORTED_RUNTIMES - {"claude_code"}))
def test_generically_supported_runtimes_declare_a_state(monkeypatch, runtime):
    _plat_ok(monkeypatch)
    cap = pc.runtime_control_support(runtime, f"{runtime}:1", "")
    assert cap.get("state"), f"{runtime} returned no state"
