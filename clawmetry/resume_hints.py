"""How a human restarts a session ClawMetry can no longer control.

Guard's Stop and Kill end a process. The next question is always the same —
*how do I get back into that conversation?* — and until now the tab answered it
with "Not controllable", which says what ClawMetry cannot do rather than what
the operator can. This module is that answer: one resume instruction per
runtime, resolved for a specific session id.

Every entry is a CHECKABLE FACT, not a guess, and carries the ``source`` it was
read from so a reader can re-verify it when a CLI changes. Where a runtime has
no local resume path (a cloud-hosted agent, an IDE-embedded conversation) the
entry says so in words instead of inventing a flag — a command that does not
exist is worse than an honest "reopen it in the app", because the operator
pastes it, it fails, and now they distrust the whole tab.

Three kinds, and the UI must render all three:

``command``
    A real command line. ``{session}`` is substituted with the runtime's NATIVE
    session id (the store namespaces ids as ``<runtime>:<native>``; every CLI
    below wants the native half, which is exactly the boundary bug that made
    Pause/Stop/Kill inert on family runtimes).
``app``
    No command line exists; the session is reopened inside a product surface.
    ``note`` says which one.
``unknown``
    We have not verified a resume path for this runtime. Say that, and show the
    session id so it can at least be copied. Never fill this bucket with a
    plausible-looking flag.

Precedence: a resume command the RUNTIME ITSELF reports (OpenClaw's gateway
puts ``resumeCommand`` in ``Session.extra``; see
``clawmetry/adapters/openclaw.py``) always beats this table, because it knows
the live session key and this file only knows the shape.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

# Verified 2026-09-05 by running ``--help`` against the real binary on macOS
# unless the source column names a document instead.
#
# ``command``  the command line, with ``{session}`` where the id goes.
# ``note``     what an operator needs to know beyond the command itself.
# ``source``   where the fact came from, so it can be re-checked.
_HINTS: Dict[str, Dict[str, str]] = {
    # ── Verified against a locally installed binary ────────────────────────
    "claude_code": {
        "command": "claude --resume {session}",
        "note": "Run it from the session's working directory.",
        "source": "claude --help (Claude Code, 2026-09-05)",
    },
    "codex": {
        "command": "codex resume {session}",
        "note": "`codex resume --last` continues the most recent session instead.",
        "source": "codex resume --help: [SESSION_ID] (2026-09-05)",
    },
    "goose": {
        "command": "goose session --resume --session-id {session}",
        "note": "`goose session -r` alone resumes the most recent session.",
        "source": "goose session --help (2026-09-05)",
    },
    "opencode": {
        "command": "opencode --session {session}",
        "note": "`opencode -c` continues the last session instead.",
        "source": "opencode --help: -s, --session (2026-09-05)",
    },
    "copilot": {
        "command": "copilot --session-id {session}",
        "note": "`copilot --continue` resumes the most recent session instead.",
        "source": "copilot --help: --session-id <id> (2026-09-05)",
    },
    "qwen_code": {
        "command": "qwen --resume {session}",
        "note": "Needs chat recording enabled (`--chat-recording`, the default).",
        "source": "qwen --help: -r, --resume (2026-09-05)",
    },
    "cursor": {
        "command": "cursor-agent --resume {session}",
        "note": "Cursor CLI sessions only. A conversation opened inside the "
                "Cursor editor is reopened from the editor's chat history.",
        "source": "cursor-agent --help: --resume [chatId] (2026-09-05)",
    },
    "pi": {
        "command": "pi --session {session}",
        "note": "`pi -c` continues the previous session instead.",
        "source": "pi --help: --session <path|id> (2026-09-05)",
    },
    "openhands": {
        "command": "openhands --resume {session}",
        "note": "`openhands --resume --last` resumes the most recent conversation.",
        "source": "openhands --help: --resume [RESUME] (SDK v1.21.0, 2026-09-05)",
    },
    "devin": {
        "command": "devin --resume {session}",
        "note": "Local CLI sessions. A run started in Devin Cloud is reopened "
                "from the Devin web app.",
        "source": "devin --help: -r, --resume [<SESSION_ID>] (2026-09-05)",
    },
    "hermes": {
        "command": "hermes --resume {session}",
        "note": "Accepts the session id or its title.",
        "source": "hermes --help: --resume SESSION (2026-09-05)",
    },
    "openclaw": {
        "command": "openclaw attach --session {session}",
        "note": "Attaches to the gateway session. The gateway may report its "
                "own resume command, which wins over this one.",
        "source": "openclaw attach --help (OpenClaw 2026.7.1, 2026-09-05)",
    },

    # ── Verified against upstream documentation ───────────────────────────
    "gemini_cli": {
        "command": "gemini --resume {session}",
        "note": "`gemini --resume` with no id opens the session picker.",
        "source": "google-gemini/gemini-cli docs/cli/session-management.md",
    },
    "cline": {
        "command": "cline --id {session}",
        "note": "`cline history` lists the saved sessions.",
        "source": "cline/cline docs/cli/cli-reference.mdx: --id <session-id>",
    },
    "grok": {
        "command": "grok --resume {session}",
        "note": "`grok -c` continues the most recent session for this directory.",
        "source": "docs.x.ai Grok Build sessions guide",
    },
    "kimi": {
        "command": "kimi --resume {session}",
        "note": "`kimi -r <id>` is the short form.",
        "source": "MoonshotAI/kimi-cli docs/en/guides/sessions.md",
    },
    "deepseek_harness": {
        "command": "dsh --resume {session}",
        "note": "The TUI's own `/resume` picker does the same thing in place.",
        "source": "deepseek-ai/deepseek-harness TUI resume-command design note",
    },
    "deepagents": {
        "command": "dcode -r {session}",
        "note": "`dcode -r` with no id resumes the most recent thread. Headless "
                "runs (`dcode -n`) always start a new thread and cannot be resumed.",
        "source": "langchain-ai/deepagents openwiki/workflows/run-dcode-session.md",
    },
    "exo": {
        # Exo resumes by conversation SLUG, not by the uuid we store, so this
        # one deliberately does not substitute the session id — printing it in
        # the command would produce a line that fails.
        "command": "exo repl --conversation <slug>",
        "note": "Exo resumes by conversation slug, not by id. Run "
                "`exo conversation list` to find the slug for this conversation.",
        "source": "exoharness/exo quick-start guide",
    },

    # ── No command line exists: the session reopens inside a product ──────
    "aider": {
        "command": "",
        "note": "Aider has no per-session id. Restart `aider` in the same "
                "repository and add `--restore-chat-history` to reload the "
                "conversation from .aider.chat.history.md.",
        "source": "aider --help: --restore-chat-history (2026-09-05)",
    },
    "antigravity": {
        "command": "",
        "note": "Reopen the conversation from Antigravity's own history "
                "(the IDE and CLI flavours share one store under ~/.gemini).",
        "source": "clawmetry adapter: ~/.gemini/antigravity*/brain/<uuid>",
    },
    "openworker": {
        "command": "",
        "note": "OpenWorker is a desktop app. Reopen the conversation in the "
                "OpenWorker window.",
        "source": "clawmetry adapter: Tauri desktop app, local agent server",
    },
    "qm": {
        "command": "",
        "note": "qm runs from Slack and its web UI. Reopen the run in the qm "
                "web UI or reply in its Slack thread.",
        "source": "clawmetry adapter: qm.ycombinator.com, per-scope sandboxes",
    },
    "n8n": {
        "command": "",
        "note": "n8n has no resume. Re-run the execution from the n8n editor "
                "(Executions -> the run -> Retry).",
        "source": "clawmetry adapter: n8n execution_entity store",
    },
    "grok_bot": {
        "command": "",
        "note": "A Grok Bot agent runs on xAI's cloud VM, not on this machine. "
                "Continue the conversation in the Grok app.",
        "source": "clawmetry process_control: no per-bot local process",
    },
    "replit": {
        "command": "",
        "note": "Replit Agent runs on Replit's infrastructure. Reopen the "
                "Repl and continue in its Agent pane.",
        "source": "clawmetry process_control: agent loop is not in the container",
    },
    "lovable": {
        "command": "",
        "note": "Lovable runs in the browser. Reopen the project chat at "
                "lovable.dev.",
        "source": "clawmetry adapter: hosted project chat",
    },

    # ── Not yet verified. Honest blank rather than a plausible flag ───────
    "nemoclaw": {
        "command": "",
        "note": "",
        "source": "",
    },
    "nanoclaw": {
        "command": "",
        "note": "",
        "source": "",
    },
    "picoclaw": {
        "command": "",
        "note": "",
        "source": "",
    },
}

# What the UI says when a runtime has no verified resume path at all. It names
# the runtime so the sentence reads as a fact about that runtime rather than as
# a broken feature.
_UNKNOWN_NOTE = ("ClawMetry has not verified a resume command for {runtime}. "
                 "Copy the session id and reopen it the way you started it.")


def _native_session_id(runtime: str, session_id: str) -> str:
    """Strip the store's ``<runtime>:`` namespace, leaving the runtime's own id.

    Delegates to ``process_control.native_session_id`` so there is one
    definition of this boundary; falls back to the same exact-head strip when
    process_control cannot be imported (cloud instances ship without it).
    """
    sid = str(session_id or "")
    rt = str(runtime or "").strip().lower()
    try:
        from clawmetry import process_control as _pc
        return _pc.native_session_id(rt, sid)
    except Exception:  # noqa: BLE001 — never break a hint over an import
        head = rt + ":"
        return sid[len(head):] if rt and sid.startswith(head) else sid


def resume_hint(runtime: str, session_id: str = "",
                extra: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """How to resume this session by hand: ``{kind, command, note, source}``.

    ``kind`` is ``command`` (a real command line, id already substituted),
    ``app`` (no command line; ``note`` says where to reopen it) or ``unknown``
    (we have not verified one). Never raises and never returns a command it
    cannot stand behind.

    ``extra`` is the session's metadata. A ``resumeCommand`` reported by the
    runtime itself wins over the table: the gateway knows the live session key,
    this file only knows the command's shape.
    """
    rt = str(runtime or "").strip().lower()
    native = _native_session_id(rt, session_id)

    if isinstance(extra, Mapping):
        for key in ("resumeCommand", "resumeCmd", "resume_command"):
            reported = extra.get(key)
            if isinstance(reported, str) and reported.strip():
                return {
                    "runtime": rt,
                    "kind": "command",
                    "command": reported.strip()[:400],
                    "note": "Reported by the runtime itself.",
                    "source": "runtime",
                    "session_id": native,
                }

    entry = _HINTS.get(rt)
    if not entry:
        return {"runtime": rt, "kind": "unknown", "command": "",
                "note": _UNKNOWN_NOTE.format(runtime=rt or "this runtime"),
                "source": "", "session_id": native}

    template = entry.get("command") or ""
    note = entry.get("note") or ""
    if template:
        command = template.replace("{session}", native) if native else template
        return {"runtime": rt, "kind": "command", "command": command,
                "note": note, "source": entry.get("source", ""),
                "session_id": native}
    if note:
        return {"runtime": rt, "kind": "app", "command": "", "note": note,
                "source": entry.get("source", ""), "session_id": native}
    return {"runtime": rt, "kind": "unknown", "command": "",
            "note": _UNKNOWN_NOTE.format(runtime=rt), "source": "",
            "session_id": native}


def known_runtimes() -> frozenset:
    """Runtimes this table has an entry for (verified or explicitly blank)."""
    return frozenset(_HINTS)
