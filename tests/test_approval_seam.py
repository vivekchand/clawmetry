"""Tests for the OSS↔paid approval seam (clawmetry/approval_events.py).

The contract this pins is a safety property, not a feature: with NO paid
package installed, every question the OSS gate asks must answer in the
direction that leaves the node in its pre-mirror state. A regression here
is not "notifications stopped working" — it is a hook installed into a
user's Claude Code settings pointing at a feature that no longer answers.

Covers:
  1. ``extensions.call`` — first non-None wins, None means "no opinion",
     a raising handler is skipped not fatal, empty registry → default.
  2. ``approval_events`` — mirror OFF and window clamped with nothing
     registered; a registered handler wins; emit paths never raise.
  3. The three OSS call sites that ask questions read the seam, so a
     node without the paid layer never arms the mirror.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def ext():
    """extensions module with an empty registry per test."""
    import clawmetry.extensions as e
    importlib.reload(e)
    return e


@pytest.fixture
def events(ext, monkeypatch):
    """approval_events with the transitional local-handler block disabled,
    so these tests see the TRUE no-paid-package behaviour rather than the
    OSS impl that is still registering itself during the move."""
    import clawmetry.approval_events as ae
    importlib.reload(ae)
    monkeypatch.setattr(ae, "extensions", ext)
    monkeypatch.setattr(ae, "_ensure_local_handlers", lambda: None)
    return ae


# ── 1. extensions.call ─────────────────────────────────────────────────────

def test_call_returns_default_with_no_handler(ext):
    assert ext.call("nobody.listening", {}, default="fallback") == "fallback"
    assert ext.call("nobody.listening") is None


def test_call_returns_first_non_none(ext):
    ext.register("q", lambda p: None)          # no opinion
    ext.register("q", lambda p: "second")      # answers
    ext.register("q", lambda p: "third")       # never reached
    assert ext.call("q", {}) == "second"


def test_call_treats_false_as_a_real_answer(ext):
    """False means "no"; only None means "ask the next handler"."""
    ext.register("q", lambda p: False)
    ext.register("q", lambda p: True)
    assert ext.call("q", {}, default=True) is False


def test_call_skips_a_raising_handler(ext):
    def boom(p):
        raise RuntimeError("plugin is broken")
    ext.register("q", boom)
    ext.register("q", lambda p: "survived")
    assert ext.call("q", {}) == "survived"


def test_call_returns_default_when_every_handler_raises(ext):
    ext.register("q", lambda p: (_ for _ in ()).throw(ValueError()))
    assert ext.call("q", {}, default="safe") == "safe"


def test_call_passes_the_payload(ext):
    ext.register("q", lambda p: p.get("runtime"))
    assert ext.call("q", {"runtime": "claude_code"}) == "claude_code"


# ── 2. approval_events with nothing registered ─────────────────────────────

def test_mirror_is_off_with_no_paid_package(events):
    """THE safety property: no delivery layer → the mirror never arms."""
    assert events.mirror_wanted("claude_code") is False


def test_mirror_window_falls_back_to_the_default(events):
    assert events.mirror_window_s("claude_code") == \
        events.DEFAULT_MIRROR_WINDOW_S


def test_announce_paths_never_raise_with_no_handler(events):
    events.notify_pending({"id": "a1", "runtime": "claude_code"})
    events.notify_resolved("a1", "approve", "dashboard")
    events.daemon_ready("node-1")


def test_a_registered_handler_wins(events, ext):
    ext.register(events.MIRROR_WANTED, lambda p: True)
    ext.register(events.MIRROR_WINDOW, lambda p: 600)
    assert events.mirror_wanted("claude_code") is True
    assert events.mirror_window_s("claude_code") == 600


def test_window_is_clamped_at_the_seam(events, ext):
    """A plugin cannot hand back a window shorter than a human can answer
    or longer than the session it blocks."""
    ext.register(events.MIRROR_WINDOW, lambda p: 1)
    assert events.mirror_window_s() == 30
    importlib.reload(ext)
    ext.register(events.MIRROR_WINDOW, lambda p: 99999)
    assert events.mirror_window_s() == 3600


def test_garbage_from_a_handler_falls_back(events, ext):
    ext.register(events.MIRROR_WINDOW, lambda p: "not-a-number")
    assert events.mirror_window_s() == events.DEFAULT_MIRROR_WINDOW_S


def test_notify_pending_reaches_a_handler(events, ext):
    seen = []
    ext.register(events.APPROVAL_PENDING, lambda p: seen.append(p))
    events.notify_pending({"id": "a9", "runtime": "openclaw"})
    assert seen and seen[0]["id"] == "a9"


def test_daemon_ready_reaches_a_handler(events, ext):
    """How the paid layer starts its inbound poller without the daemon
    importing it by name."""
    started = []
    ext.register(events.DAEMON_READY, lambda p: started.append(p["node_id"]))
    events.daemon_ready("node-7")
    assert started == ["node-7"]


# ── 3. the OSS call sites read the seam ────────────────────────────────────

def test_gate_does_not_arm_the_mirror_without_the_paid_layer(monkeypatch):
    import clawmetry.claude_code_gate as g
    import clawmetry.approval_events as ae
    monkeypatch.setattr(ae, "mirror_wanted", lambda runtime="claude_code": False)
    assert g._mirror_wanted() is False


def test_gate_reads_the_window_from_the_seam(monkeypatch):
    import clawmetry.claude_code_gate as g
    import clawmetry.approval_events as ae
    monkeypatch.setattr(ae, "mirror_window_s", lambda runtime="claude_code": 420)
    assert g.mirror_timeout_s() == 420


def test_gate_survives_a_broken_seam(monkeypatch):
    """Belt-and-braces: even if the seam itself explodes, the gate answers
    'do not arm' rather than propagating into the watcher loop."""
    import clawmetry.claude_code_gate as g
    import clawmetry.approval_events as ae

    def boom(runtime="claude_code"):
        raise RuntimeError("seam down")
    monkeypatch.setattr(ae, "mirror_wanted", boom)
    monkeypatch.setattr(ae, "mirror_window_s", boom)
    assert g._mirror_wanted() is False
    assert g.mirror_timeout_s() == 180


def test_oss_call_sites_do_not_import_the_impl_directly():
    """Guard the boundary: once the impl moves to clawmetry-pro these
    modules must not name it. They talk to approval_events instead."""
    import re
    for rel in ("clawmetry/approvals.py", "clawmetry/claude_code_gate.py",
                "clawmetry/sync.py", "routes/hooks.py", "routes/policy.py"):
        src = open(os.path.join(_REPO_ROOT, rel)).read()
        hits = re.findall(r"import\s+approval_(notify|inbound)", src)
        assert not hits, f"{rel} imports the delivery impl directly: {hits}"
