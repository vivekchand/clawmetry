"""clawmetry/runtime_probe.py — zero-dependency presence probes for every
supported agent runtime (#3917, founder request 2026-07-22).

The adapter registry can only detect runtimes whose adapters are REGISTERED,
so a free (OSS-only) install is blind to the ten Pro runtimes: a machine full
of Cursor or Claude Code sessions onboards with no hint that ClawMetry could
watch them, and no hint that doing so needs a license key or the Cloud plan.
That is the conversion moment, wasted.

These probes are presence checks over each runtime's default on-disk data
location, nothing more: no parsing, no session reading, no gated behaviour.
The Pro adapters remain the single source of truth for real detection and
ingestion; a probe hit only drives honest onboarding copy ("Cursor was found
on this machine; the free tier does not watch it").

Path notes: each entry mirrors the default location the corresponding
adapter reads (verified live on Windows 2026-07-20 by planting fixture data
at exactly these paths and watching the adapters ingest it). ``~`` expands
per-OS; env overrides honoured where the adapter honours them.
"""
from __future__ import annotations

import glob as _glob
import os
from dataclasses import dataclass

# Runtimes the free tier watches (FLYWHEEL: free on every plan).
FREE_RUNTIMES = frozenset({"openclaw", "nemoclaw"})


@dataclass
class RuntimeProbe:
    """One supported runtime: id, human label, and where its data lives."""

    id: str
    label: str
    paths: tuple  # candidate globs, relative to ~ unless absolute / env-based
    env: str = ""  # optional env var naming the data dir (adapter-honoured)

    def found(self) -> bool:
        """True when any candidate location exists. Never raises."""
        try:
            if self.env:
                root = os.environ.get(self.env)
                if root and os.path.exists(os.path.expanduser(root)):
                    return True
            for p in self.paths:
                expanded = os.path.expanduser(p)
                if _glob.glob(expanded):
                    return True
        except Exception:
            return False
        return False


# One entry per supported runtime. Keep ids in sync with the entitlement
# catalogue (clawmetry/entitlements.py) — tests assert the parity.
RUNTIME_PROBES: tuple = (
    RuntimeProbe("openclaw", "OpenClaw", ("~/.openclaw/openclaw.json", "~/.openclaw/gateway"), env="OPENCLAW_HOME"),
    RuntimeProbe("nemoclaw", "NVIDIA NemoClaw", ("~/.nemoclaw", "~/.openclaw/sandboxes")),
    RuntimeProbe("claude_code", "Claude Code", ("~/.claude/projects",)),
    RuntimeProbe("codex", "Codex", ("~/.codex/sessions", "~/.codex/archived_sessions")),
    RuntimeProbe("cursor", "Cursor", (
        "~/AppData/Roaming/Cursor/User/globalStorage/state.vscdb",
        "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb",
        "~/.config/Cursor/User/globalStorage/state.vscdb",
    )),
    RuntimeProbe("aider", "Aider", ("~/.aider*",), env="AIDER_HISTORY_DIRS"),
    RuntimeProbe("goose", "Goose", ("~/.local/share/goose/sessions",)),
    RuntimeProbe("opencode", "opencode", ("~/.local/share/opencode",)),
    RuntimeProbe("qwen_code", "Qwen Code", ("~/.qwen/projects",)),
    RuntimeProbe("hermes", "Hermes", ("~/.hermes",), env="HERMES_HOME"),
    RuntimeProbe("picoclaw", "PicoClaw", ("~/.picoclaw/workspace",)),
    RuntimeProbe("nanoclaw", "NanoClaw", ("~/.nanoclaw",)),
    RuntimeProbe("pi", "Pi", ("~/.pi/agent/sessions",)),
    RuntimeProbe("deepagents", "DeepAgents", ("~/.deepagents/.state", "~/.deepagents")),
)


def probe_runtimes() -> list:
    """Presence-probe every supported runtime.

    Returns ``[{id, label, free, found}]`` in catalogue order. Never raises.
    """
    out = []
    for probe in RUNTIME_PROBES:
        try:
            hit = probe.found()
        except Exception:
            hit = False
        out.append(
            {
                "id": probe.id,
                "label": probe.label,
                "free": probe.id in FREE_RUNTIMES,
                "found": hit,
            }
        )
    return out


def render_detection_lines(probes: list) -> list:
    """Plain-words onboarding copy for the probe results.

    Pure function (list of printable lines, no ANSI) so the wizard can style
    it and tests can pin it. Empty list when nothing was detected: the
    wizard then keeps its current copy.
    """
    found = [p for p in probes if p.get("found")]
    if not found:
        return []
    lines = ["Detected AI agent runtimes on this machine:"]
    for p in found:
        tier = "free" if p.get("free") else "Pro"
        lines.append(f"  [x] {p['label']}  ({tier})")
    lines.append("")
    lines.append("Free forever: OpenClaw and NVIDIA NemoClaw.")
    paid = [p for p in found if not p.get("free")]
    if paid:
        names = ", ".join(p["label"] for p in paid)
        lines.append(
            f"To watch {names}: enter a license key (clawmetry activate <key>,"
        )
        lines.append(
            "purchase at clawmetry.com/pricing) or pick [2] Cloud below to sign up."
        )
    return lines
