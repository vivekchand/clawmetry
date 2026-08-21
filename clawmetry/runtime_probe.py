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
#
# Sourced from the entitlement catalogue rather than duplicated: this module
# only labels a probe row ``free``, and a stale copy here would show a free
# runtime as locked in onboarding while the gate happily allowed it. The
# literal is kept solely as an import-failure fallback (this module is
# imported by the installer path, which must never hard-fail on an import).
try:  # pragma: no cover - trivial import shim
    from clawmetry.entitlements import FREE_RUNTIMES
except Exception:  # pragma: no cover - defensive; keep onboarding alive
    FREE_RUNTIMES = frozenset({"openclaw", "nemoclaw", "goose"})


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
    RuntimeProbe("n8n", "n8n", ("~/.n8n",), env="N8N_USER_FOLDER"),
    RuntimeProbe("antigravity", "Antigravity",
                 ("~/.gemini/antigravity", "~/.gemini/antigravity-cli",
                  "~/.gemini/antigravity-ide", "~/.gemini/jetski"),
                 env="CLAWMETRY_ANTIGRAVITY_HOME"),
    RuntimeProbe("copilot", "GitHub Copilot", ("~/.copilot/session-state",),
                 env="CLAWMETRY_COPILOT_HOME"),
    RuntimeProbe("grok", "Grok",
                 ("~/.grok/logs", "~/.grok/sessions", "~/.grok/bin/grok"),
                 env="CLAWMETRY_GROK_HOME"),
    # DeepSeek Harness (`dsh`) keeps everything under one home ($DSH_HOME,
    # default ~/.dsh); JSONL session logs live in <home>/sessions.
    RuntimeProbe("deepseek_harness", "DeepSeek Harness",
                 ("~/.dsh/sessions",), env="DSH_HOME"),
    # Exo harness state is WORKSPACE-relative (<workspace>/.exo/exoharness),
    # not home-anchored; the probe checks the common clone locations and the
    # CLAWMETRY_EXO_ROOTS override. The pro adapter does the deeper
    # well-known-parents scan.
    RuntimeProbe("exo", "Exo",
                 ("~/exo/.exo/exoharness", "~/.exo/exoharness"),
                 env="CLAWMETRY_EXO_ROOTS"),
    # Kimi CLI keeps everything under one share dir ($KIMI_SHARE_DIR,
    # default ~/.kimi); the standalone successor Kimi Code CLI uses
    # ~/.kimi-code. Same store shape, same runtime here.
    RuntimeProbe("kimi", "Kimi CLI",
                 ("~/.kimi/sessions", "~/.kimi-code/sessions"),
                 env="KIMI_SHARE_DIR"),
    # Google Gemini CLI keeps per-project chat recordings under
    # <home>/.gemini/tmp/<project-basename>/chats/. NOTE the env var names the
    # dir CONTAINING .gemini (unlike KIMI_SHARE_DIR/QWEN_HOME, which name the
    # data dir itself), so the probe globs both the plain ~/.gemini tree and
    # the CLAWMETRY override that points straight at a data dir.
    RuntimeProbe("gemini_cli", "Gemini CLI",
                 ("~/.gemini/tmp/*/chats", "~/.gemini/projects.json"),
                 env="CLAWMETRY_GEMINI_CLI_HOME"),
    # Cline CLI keeps sessions under the DATA leaf of its home -- ~/.cline
    # itself only holds hooks/ and worktrees/, which our own installer creates,
    # so probing the bare ~/.cline would false-positive on every machine that
    # has ClawMetry's hooks installed and no Cline at all.
    RuntimeProbe("cline", "Cline",
                 ("~/.cline/data/db/sessions.db", "~/.cline/data/sessions"),
                 env="CLAWMETRY_CLINE_DATA_DIR"),
    # OpenHands persists one directory per conversation. The probe requires the
    # conversations dir rather than the ~/.openhands root, because the CLI
    # creates ~/.openhands/profiles and ~/.openhands/cache on first launch even
    # when the persistence dir points elsewhere -- so the root existing is not
    # evidence that any conversation was ever recorded.
    RuntimeProbe("openhands", "OpenHands",
                 ("~/.openhands/conversations/*/base_state.json",),
                 env="CLAWMETRY_OPENHANDS_HOME"),
    # qm (github.com/yc-software/qm) has no on-disk session store — it's a
    # Node service backed by Postgres — so the probe looks for the npm
    # install artefacts (typical install layouts) plus a CLAWMETRY_QM_HOME
    # override. The adapter itself uses DATABASE_URL + qm's tables directly.
    RuntimeProbe("qm", "QM",
                 ("~/node_modules/@yc-software/qm",
                  "~/.qm", "~/qm/package.json",
                  "/opt/qm/package.json"),
                 env="CLAWMETRY_QM_HOME"),
    # Devin CLI (cli.devin.ai) keeps every session in ONE XDG-anchored SQLite
    # store; ~/.config/devin/config.json is the other half of a real install
    # (it exists even when the CLI has only ever run in ACP mode under an
    # IDE, which never creates sessions.db). Devin Cloud sessions are
    # API-only and cannot be probed from disk at all.
    RuntimeProbe("devin", "Devin",
                 ("~/.local/share/devin/cli/sessions.db",
                  "~/.local/share/cognition/cli/sessions.db",
                  "~/.local/share/chisel/cli/sessions.db",
                  "~/.config/devin/config.json",
                  "~/AppData/Local/devin/cli/sessions.db",
                  "~/AppData/Roaming/devin/config.json"),
                 env="CLAWMETRY_DEVIN_DB"),
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
    n = len(found)
    plural = "runtime" if n == 1 else "runtimes"
    lines = [f"Detected {n} AI agent {plural} on this machine:"]
    # Compact grid, 3 per row: ten detections should read as one confident
    # block of checkmarks, not a ten-line paywall ledger (per-line tier
    # labels moved into the two summary lines below).
    cell = max(len(p["label"]) for p in found) + 3
    for i in range(0, n, 3):
        row = "".join(f"[x] {p['label']:<{cell}}" for p in found[i : i + 3])
        lines.append("  " + row.rstrip())
    paid = [p for p in found if not p.get("free")]
    if paid:
        lines.append("")
    if len(paid) == 1:
        lines.append(
            f"A free 7-day Pro trial (sign in below) unlocks {paid[0]['label']} too, or paste a license key."
        )
    elif paid:
        lines.append(
            f"A free 7-day Pro trial (sign in below) unlocks the other {len(paid)}, or paste a license key."
        )
    return lines
