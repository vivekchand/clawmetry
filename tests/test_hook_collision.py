"""Hook collision: ClawMetry must never delete a hook it did not write.

WO-8.  GitKraken's GitLens shells out to ``gk ai hook install claude-code
--force`` on a very large install base, and ``numbat`` is already co-resident
on developer machines.  All of them write ``~/.claude/settings.json``.  The
merge behaviour on the other side lives in a closed binary, so what is tested
here is the half that is ours: what ClawMetry does to a foreign hook.

A foreign writer can land in two shapes, and only the first was ever handled:

  separate  — its own {matcher, hooks} entry.  What numbat does today.
  merged    — its command appended into the hooks list of an entry that
              already exists.  The --force hazard.

Against the merged shape the pre-fix code destroyed the foreign hook twice
over: ``clawmetry hooks uninstall`` dropped the whole entry, and the daemon
gate's reinstall — which runs every ~2s — dropped it within seconds of it
landing.  Both are regression-locked below.

The end-to-end matrix (both installers x both shapes x both orders, with a
diff at every step) is ``scripts/hook_collision_matrix.py``; it uses a real
``gk`` binary when one is on PATH.
"""
from __future__ import annotations

import importlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import hook_ownership as ho  # noqa: E402

FOREIGN_CMD = "gk ai hook run pre-tool"
FOREIGN = {"type": "command", "command": FOREIGN_CMD, "timeout": 30}
NUMBAT = {"type": "command", "command": "/opt/numbat hook pre-tool",
          "timeout": 10}
OUR_MARKERS = ("clawmetry hooks run", "clawmetry hook claude-code")


def _read(path):
    with open(path) as f:
        txt = f.read().strip()
    return json.loads(txt) if txt else {}


def _blob(path):
    return json.dumps(_read(path))


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Sandbox HOME + CLAUDE_CONFIG_DIR, then re-import the modules whose
    paths are resolved at import time."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    cfg = tmp_path / ".claude"
    cfg.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    import clawmetry.claude_code_gate as g
    import clawmetry.hooks_claude_code as h
    importlib.reload(h)
    importlib.reload(g)
    yield {"settings": str(cfg / "settings.json"), "h": h, "g": g}
    importlib.reload(h)
    importlib.reload(g)


# ── the ownership primitive ────────────────────────────────────────────────

def test_prune_keeps_foreign_hook_sharing_our_entry():
    entries = [{"matcher": "*", "hooks": [
        {"command": "clawmetry hooks run pretooluse"}, dict(FOREIGN)]}]
    kept, removed = ho.prune_our_hooks(entries, OUR_MARKERS)
    assert removed == 1
    assert kept == [{"matcher": "*", "hooks": [FOREIGN]}]


def test_prune_drops_entry_only_when_nothing_survives():
    entries = [{"matcher": "*", "hooks": [
        {"command": "clawmetry hooks run pretooluse"}]}]
    kept, removed = ho.prune_our_hooks(entries, OUR_MARKERS)
    assert (kept, removed) == ([], 1)


def test_prune_never_touches_a_purely_foreign_entry():
    entries = [{"matcher": "Bash", "hooks": [dict(FOREIGN), dict(NUMBAT)]}]
    kept, removed = ho.prune_our_hooks(entries, OUR_MARKERS)
    assert removed == 0 and kept == entries


def test_prune_passes_through_malformed_foreign_rows():
    """A foreign writer's broken row is still not ours to repair."""
    entries = ["not-a-dict", {"hooks": "also-not-a-list"},
               {"matcher": "*", "hooks": [{"command": "clawmetry hooks run x"}]}]
    kept, removed = ho.prune_our_hooks(entries, OUR_MARKERS)
    assert removed == 1
    assert kept == ["not-a-dict", {"hooks": "also-not-a-list"}]


# ── manual installer: `clawmetry hooks install` / `uninstall` ──────────────

def test_manual_uninstall_preserves_foreign_hook_merged_into_our_entry(home):
    """The bug: uninstall dropped the whole entry, taking gk's hook."""
    h, path = home["h"], home["settings"]
    h.install(settings_path=path)
    s = _read(path)
    s["hooks"]["PreToolUse"][0]["hooks"].append(dict(FOREIGN))  # gk --force
    with open(path, "w") as f:
        json.dump(s, f)

    h.uninstall(settings_path=path)

    assert FOREIGN_CMD in _blob(path), "uninstall deleted a foreign hook"
    assert not any(m in _blob(path) for m in OUR_MARKERS), "ours must be gone"


def test_manual_install_preserves_a_separate_foreign_entry(home):
    h, path = home["h"], home["settings"]
    with open(path, "w") as f:
        json.dump({"hooks": {"PreToolUse": [
            {"matcher": "Bash", "hooks": [dict(FOREIGN)]}]}}, f)
    h.install(settings_path=path)
    assert FOREIGN_CMD in _blob(path)
    assert any(m in _blob(path) for m in OUR_MARKERS)


def test_manual_uninstall_leaves_unrelated_events_alone(home):
    h, path = home["h"], home["settings"]
    h.install(settings_path=path)
    s = _read(path)
    s["hooks"]["SessionStart"] = [{"hooks": [dict(NUMBAT)]}]
    with open(path, "w") as f:
        json.dump(s, f)
    h.uninstall(settings_path=path)
    assert _read(path)["hooks"]["SessionStart"] == [{"hooks": [NUMBAT]}]


# ── daemon gate: the every-2s reinstall ────────────────────────────────────

def _policies():
    return [{"action": "require_approval", "timeout": 300}]


def test_gate_refresh_preserves_foreign_hook_merged_into_our_entry(home):
    """The worse bug: this path runs every ~2s, so a merged foreign hook
    was deleted within seconds of landing."""
    g, path = home["g"], home["settings"]
    g._install(_policies())
    s = _read(path)
    s["hooks"]["PreToolUse"][0]["hooks"].append(dict(FOREIGN))
    with open(path, "w") as f:
        json.dump(s, f)

    g._install(_policies())

    assert FOREIGN_CMD in _blob(path), "gate refresh deleted a foreign hook"


def test_gate_refresh_is_idempotent_after_a_collision(home):
    """Post-fix the entry splits once and then settles — no rewrite churn
    against settings.json every 2 seconds."""
    g, path = home["g"], home["settings"]
    g._install(_policies())
    s = _read(path)
    s["hooks"]["PreToolUse"][0]["hooks"].append(dict(FOREIGN))
    with open(path, "w") as f:
        json.dump(s, f)
    g._install(_policies())
    settled = _blob(path)
    g._install(_policies())
    assert _blob(path) == settled


def test_gate_uninstall_preserves_foreign_hook_merged_into_our_entry(home):
    g, path = home["g"], home["settings"]
    g._install(_policies())
    s = _read(path)
    s["hooks"]["PreToolUse"][0]["hooks"].append(dict(FOREIGN))
    with open(path, "w") as f:
        json.dump(s, f)
    g._uninstall()
    assert FOREIGN_CMD in _blob(path), "gate uninstall deleted a foreign hook"
    assert g.HOOK_CMD_MARKER not in _blob(path)


def test_gate_does_not_prune_the_mirror_hook(home):
    """The mirror hook is ClawMetry's but owned by a different installer."""
    g, path = home["g"], home["settings"]
    g._install(_policies())
    s = _read(path)
    s["hooks"]["PreToolUse"][0]["hooks"].append(
        {"type": "command",
         "command": f"{g.MIRROR_CMD_MARKER} --base http://127.0.0.1:8900"})
    with open(path, "w") as f:
        json.dump(s, f)
    g._install(_policies())
    assert g.MIRROR_CMD_MARKER in _blob(path)


# ── both install orders survive, end to end ────────────────────────────────

@pytest.mark.parametrize("order", ["ours-first", "foreign-first"])
@pytest.mark.parametrize("shape", ["separate", "merged"])
def test_install_order_matrix_preserves_both(home, order, shape):
    h, g, path = home["h"], home["g"], home["settings"]

    def foreign():
        s = _read(path) if os.path.exists(path) else {}
        pre = s.setdefault("hooks", {}).setdefault("PreToolUse", [])
        if shape == "merged" and pre:
            pre[0].setdefault("hooks", []).append(dict(FOREIGN))
        else:
            pre.append({"matcher": "Bash", "hooks": [dict(FOREIGN)]})
        with open(path, "w") as f:
            json.dump(s, f)

    if order == "ours-first":
        h.install(settings_path=path)
        foreign()
    else:
        foreign()
        h.install(settings_path=path)

    g._install(_policies())          # daemon gate joins the same file
    assert FOREIGN_CMD in _blob(path)

    h.uninstall(settings_path=path)
    g._uninstall()
    assert FOREIGN_CMD in _blob(path), "a foreign hook was lost"
    assert not any(m in _blob(path) for m in OUR_MARKERS)


# ── bounded timeouts ───────────────────────────────────────────────────────

def test_installed_hook_timeout_is_bounded(home):
    """A wedged hook must not sit on a tool call for seven days."""
    g = home["g"]
    assert g._timeout_from_policies([]) <= ho.DEFAULT_HOOK_TIMEOUT_CEILING_S
    from clawmetry import runtime_gates as rg
    importlib.reload(rg)
    # Copilot's preToolUse gate is FAIL-CLOSED, so this one matters most.
    assert rg._timeout_from_policies([]) <= ho.DEFAULT_HOOK_TIMEOUT_CEILING_S
    assert home["h"]._PRETOOL_TIMEOUT_S <= ho.DEFAULT_HOOK_TIMEOUT_CEILING_S


def test_short_policy_window_passes_through_unclamped():
    assert ho.clamp_hook_timeout(360) == 360


def test_ceiling_is_documented_and_opt_out_restores_old_behaviour(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_HOOK_TIMEOUT_MAX_S", "0")
    assert ho.clamp_hook_timeout(604860) == 604860
    monkeypatch.setenv("CLAWMETRY_HOOK_TIMEOUT_MAX_S", "120")
    assert ho.clamp_hook_timeout(604860) == 120
    monkeypatch.setenv("CLAWMETRY_HOOK_TIMEOUT_MAX_S", "garbage")
    assert ho.clamp_hook_timeout(604860) == ho.DEFAULT_HOOK_TIMEOUT_CEILING_S
