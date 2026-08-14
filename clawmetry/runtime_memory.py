"""clawmetry/runtime_memory.py — Per-runtime Memory & Skills file browser.

Each supported runtime stores its long-lived context in different places:
Claude Code lives in ``CLAUDE.md`` + ``~/.claude/skills``, Codex in
``AGENTS.md`` + ``~/.codex/prompts``, Cursor in ``.cursor/rules/*.mdc``, etc.
Historically the Memory and Skills tabs in the dashboard only knew about the
OpenClaw layout (``~/.openclaw/agents/main/memory`` + ``~/.openclaw/skills``),
which meant users running any of the other 17 runtimes saw an empty tab even
when their agent had a rich local knowledge base on disk.

This module is the single source of truth for **where every supported runtime
keeps memory / skills / commands / agents / hooks on disk**. The tabs, the
routes, and the sync daemon all read the catalog here rather than hard-coding
paths in their own copies.

Design notes:

- We enumerate ROOTS as ``(runtime, category, root_path, include_globs)``.
  A "root" is a directory (or a single well-known file) that we scan;
  ``include_globs`` are relative filename patterns under it. When ``root_path``
  itself is a single file, it is surfaced directly with no walk.
- Read paths are traversal-safe: ``read_runtime_file`` normalises the requested
  path against every registered root for that runtime and rejects anything
  that escapes.
- Every helper is defensive — a missing directory, unreadable file, or bad
  glob returns an empty result rather than raising. The dashboard is used by
  non-technical users on messy laptops; crashing on a missing ``~/.codex``
  would be a regression from the OpenClaw-only status quo.
- Paths honour the same env-var escape hatches as ``runtime_probe.py``
  (``OPENCLAW_HOME``, ``HERMES_HOME``, ``CLAWMETRY_ANTIGRAVITY_HOME``, …)
  so power users who moved their data dir still see it.

If you add a new runtime, add an entry to :data:`RUNTIME_CATALOG` and — if
its adapter reads a per-project file (like ``AGENTS.md`` / ``GEMINI.md``) —
include it under the ``project`` roots so the workspace-relative file shows
up alongside the global ones.

Relationship to the AgentAdapter layer
--------------------------------------
This module is intentionally NOT sourced from ``clawmetry.adapters``.
Adapters normalise live Session / Event streams for a runtime; this catalog
resolves on-disk memory / skills paths. A runtime's adapter can be
unshipped (Pro tier not installed on a free machine) while the runtime's
memory files still exist on the user's filesystem, so the browser must
resolve independently. When both exist, the OpenClaw adapter's session
paths and this catalog's memory roots share the same on-disk prefix
(``~/.openclaw/…``) but neither imports the other.
"""
from __future__ import annotations

import glob as _glob
import os
from dataclasses import dataclass, field
from typing import Iterable, Optional


# Category taxonomy shown in the UI. "memory" == free-form markdown notes
# the agent re-reads at the top of every conversation (CLAUDE.md, MEMORY.md,
# AGENTS.md, .cursorrules, …). "skills" == packaged capability directories
# (SKILL.md-style). "commands" == slash-command / prompt files. "agents" ==
# named sub-agent definitions (Claude Code's ``~/.claude/agents/*.md``).
# "hooks" == event hooks (settings-level, not a folder browser, but listed
# for completeness where the runtime exposes them as files).
CATEGORIES: tuple = ("memory", "skills", "commands", "agents", "hooks")


@dataclass
class RootSpec:
    """One filesystem root scanned by the browser.

    ``root`` is either an absolute directory OR an absolute single file.
    When it's a file, the browser surfaces it as one entry (no walk).
    When it's a directory, ``include_globs`` limits which files under it
    are listed — an empty tuple means "everything, recursive".
    """

    category: str
    root: str
    include_globs: tuple = ()
    label: str = ""
    scope: str = "global"  # "global" (per-user) or "project" (per-repo)
    max_depth: int = 6

    def expanded_root(self) -> str:
        return os.path.expanduser(os.path.expandvars(self.root))


@dataclass
class RuntimeCatalogEntry:
    """One supported runtime's memory + skills roots."""

    id: str
    label: str
    roots: tuple = field(default_factory=tuple)


def _env_root(env: str, fallback: str, subpath: str = "") -> str:
    """Prefer ``$env`` if it points at an existing dir, else ``fallback``.

    ``subpath`` (optional) is appended when the env var supplies a data-dir.
    """
    val = os.environ.get(env)
    if val:
        base = os.path.expanduser(val)
        return os.path.join(base, subpath) if subpath else base
    return fallback


def _workspace_root() -> str:
    """Best-guess project workspace (for per-project memory files).

    Uses the dashboard's resolved WORKSPACE when the module is imported in
    the Flask process, else the CWD. Never raises.
    """
    try:
        import dashboard as _d
        ws = getattr(_d, "WORKSPACE", None)
        if ws and os.path.isdir(ws):
            return ws
    except Exception:
        pass
    return os.getcwd()


def _openclaw_home() -> str:
    return _env_root("OPENCLAW_HOME", os.path.expanduser("~/.openclaw"))


def _catalog() -> list:
    """Build the canonical runtime → roots catalog.

    Called on every request (cheap — just string ops, no I/O). Rebuilt on
    each call so env-var / workspace changes take effect without restart.
    """
    ws = _workspace_root()
    oc_home = _openclaw_home()
    home = os.path.expanduser("~")

    catalog: list = []

    # ── OpenClaw (free) ─────────────────────────────────────────────
    catalog.append(RuntimeCatalogEntry(
        id="openclaw", label="OpenClaw",
        roots=(
            RootSpec("memory", os.path.join(oc_home, "agents/main/memory"),
                     ("*.md",), "Agent memory", "global"),
            RootSpec("memory", os.path.join(ws, "memory"),
                     ("*.md",), "Workspace memory", "project"),
            RootSpec("memory", os.path.join(ws, "MEMORY.md"), label="MEMORY.md", scope="project"),
            RootSpec("memory", os.path.join(ws, "SOUL.md"), label="SOUL.md", scope="project"),
            RootSpec("memory", os.path.join(ws, "AGENTS.md"), label="AGENTS.md", scope="project"),
            RootSpec("memory", os.path.join(ws, "IDENTITY.md"), label="IDENTITY.md", scope="project"),
            RootSpec("memory", os.path.join(ws, "USER.md"), label="USER.md", scope="project"),
            RootSpec("memory", os.path.join(ws, "TOOLS.md"), label="TOOLS.md", scope="project"),
            RootSpec("skills", os.path.join(oc_home, "skills"),
                     label="Installed skills", scope="global"),
            RootSpec("skills", os.path.join(oc_home, "plugin-skills"),
                     label="Plugin skills", scope="global"),
            RootSpec("skills", os.path.join(ws, "skills"),
                     label="Workspace skills", scope="project"),
            RootSpec("agents", os.path.join(oc_home, "agents"),
                     label="Sub-agents", scope="global", max_depth=2),
            RootSpec("hooks", os.path.join(oc_home, "openclaw.json"),
                     label="Config", scope="global"),
        ),
    ))

    # ── Claude Code (Anthropic CLI) ─────────────────────────────────
    claude_home = os.path.join(home, ".claude")
    catalog.append(RuntimeCatalogEntry(
        id="claude_code", label="Claude Code",
        roots=(
            RootSpec("memory", os.path.join(claude_home, "CLAUDE.md"),
                     label="Global CLAUDE.md", scope="global"),
            RootSpec("memory", os.path.join(ws, "CLAUDE.md"),
                     label="Project CLAUDE.md", scope="project"),
            RootSpec("memory", os.path.join(ws, "CLAUDE.local.md"),
                     label="Project CLAUDE.local.md", scope="project"),
            RootSpec("memory", os.path.join(ws, ".claude", "CLAUDE.md"),
                     label="Project .claude/CLAUDE.md", scope="project"),
            RootSpec("memory", os.path.join(claude_home, "projects"),
                     ("**/memory/*.md", "**/MEMORY.md"),
                     "Per-project auto-memory", "global"),
            RootSpec("skills", os.path.join(claude_home, "skills"),
                     label="Global skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".claude", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("agents", os.path.join(claude_home, "agents"),
                     ("*.md",), "Global sub-agents", "global"),
            RootSpec("agents", os.path.join(ws, ".claude", "agents"),
                     ("*.md",), "Project sub-agents", "project"),
            RootSpec("commands", os.path.join(claude_home, "commands"),
                     ("*.md",), "Global slash commands", "global"),
            RootSpec("commands", os.path.join(ws, ".claude", "commands"),
                     ("*.md",), "Project slash commands", "project"),
            RootSpec("hooks", os.path.join(claude_home, "hooks"),
                     label="Global hooks dir", scope="global"),
            RootSpec("hooks", os.path.join(claude_home, "settings.json"),
                     label="Global settings.json", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".claude", "settings.json"),
                     label="Project settings.json", scope="project"),
            RootSpec("hooks", os.path.join(ws, ".claude", "settings.local.json"),
                     label="Project settings.local.json", scope="project"),
        ),
    ))

    # ── Codex (OpenAI CLI) ──────────────────────────────────────────
    codex_home = _env_root("CODEX_HOME", os.path.join(home, ".codex"))
    catalog.append(RuntimeCatalogEntry(
        id="codex", label="Codex",
        roots=(
            RootSpec("memory", os.path.join(codex_home, "AGENTS.md"),
                     label="Global AGENTS.md", scope="global"),
            RootSpec("memory", os.path.join(codex_home, "instructions.md"),
                     label="instructions.md", scope="global"),
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("memory", os.path.join(ws, ".agents.md"),
                     label=".agents.md", scope="project"),
            RootSpec("memory", os.path.join(ws, "TEAM_GUIDE.md"),
                     label="TEAM_GUIDE.md", scope="project"),
            RootSpec("commands", os.path.join(codex_home, "prompts"),
                     ("*.md",), "Custom prompts", "global"),
            RootSpec("hooks", os.path.join(codex_home, "config.toml"),
                     label="Global config.toml", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".codex", "config.toml"),
                     label="Project .codex/config.toml", scope="project"),
        ),
    ))

    # ── Cursor ──────────────────────────────────────────────────────
    catalog.append(RuntimeCatalogEntry(
        id="cursor", label="Cursor",
        roots=(
            RootSpec("memory", os.path.join(ws, ".cursor", "rules"),
                     ("*.mdc", "*.md"), "Project rules", "project"),
            RootSpec("memory", os.path.join(ws, ".cursorrules"),
                     label=".cursorrules (legacy)", scope="project"),
            RootSpec("memory", os.path.join(home, ".cursor", "rules"),
                     ("*.mdc", "*.md"), "Global rules", "global"),
            RootSpec("hooks", os.path.join(home, ".cursor", "mcp.json"),
                     label="Global mcp.json", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".cursor", "mcp.json"),
                     label="Project mcp.json", scope="project"),
        ),
    ))

    # ── Antigravity / Gemini CLI ────────────────────────────────────
    gemini_home = _env_root("CLAWMETRY_ANTIGRAVITY_HOME",
                            os.path.join(home, ".gemini"))
    catalog.append(RuntimeCatalogEntry(
        id="antigravity", label="Antigravity",
        roots=(
            RootSpec("memory", os.path.join(gemini_home, "GEMINI.md"),
                     label="Global GEMINI.md", scope="global"),
            RootSpec("memory", os.path.join(ws, "GEMINI.md"),
                     label="Project GEMINI.md", scope="project"),
            RootSpec("memory", os.path.join(ws, ".agents", "GEMINI.md"),
                     label="Project .agents/GEMINI.md", scope="project"),
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("memory", os.path.join(gemini_home, "AGENTS.md"),
                     label="Global AGENTS.md", scope="global"),
            RootSpec("skills", os.path.join(gemini_home, "config", "skills"),
                     label="Global skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".agents", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("skills", os.path.join(gemini_home, "extensions"),
                     label="Extensions", scope="global"),
            RootSpec("commands", os.path.join(gemini_home, "commands"),
                     ("*.toml", "*.md"), "Custom commands", "global"),
            RootSpec("hooks", os.path.join(gemini_home, "settings.json"),
                     label="settings.json", scope="global"),
        ),
    ))

    # ── Aider ───────────────────────────────────────────────────────
    catalog.append(RuntimeCatalogEntry(
        id="aider", label="Aider",
        roots=(
            RootSpec("memory", os.path.join(ws, "CONVENTIONS.md"),
                     label="CONVENTIONS.md", scope="project"),
            RootSpec("memory", os.path.join(home, ".aider.chat.history.md"),
                     label="Chat history", scope="global"),
            RootSpec("hooks", os.path.join(home, ".aider.conf.yml"),
                     label="Global .aider.conf.yml", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".aider.conf.yml"),
                     label="Project .aider.conf.yml", scope="project"),
            RootSpec("hooks", os.path.join(ws, ".aider.model.settings.yml"),
                     label=".aider.model.settings.yml", scope="project"),
            RootSpec("hooks", os.path.join(home, ".aider.model.metadata.json"),
                     label=".aider.model.metadata.json", scope="global"),
        ),
    ))

    # ── opencode ────────────────────────────────────────────────────
    opencode_home = os.path.join(home, ".config", "opencode")
    catalog.append(RuntimeCatalogEntry(
        id="opencode", label="opencode",
        roots=(
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("memory", os.path.join(opencode_home, "AGENTS.md"),
                     label="Global AGENTS.md", scope="global"),
            RootSpec("skills", os.path.join(opencode_home, "skills"),
                     label="Global skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".opencode", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("agents", os.path.join(opencode_home, "agents"),
                     ("*.md",), "Custom agents", "global"),
            RootSpec("agents", os.path.join(ws, ".opencode", "agents"),
                     ("*.md",), "Project agents", "project"),
            RootSpec("agents", os.path.join(opencode_home, "modes"),
                     ("*.md", "*.json"), "Global modes", "global"),
            RootSpec("commands", os.path.join(opencode_home, "commands"),
                     ("*.md",), "Global commands", "global"),
            RootSpec("commands", os.path.join(ws, ".opencode", "commands"),
                     ("*.md",), "Project commands", "project"),
            RootSpec("hooks", os.path.join(opencode_home, "opencode.json"),
                     label="Global opencode.json", scope="global"),
            RootSpec("hooks", os.path.join(ws, "opencode.json"),
                     label="Project opencode.json", scope="project"),
        ),
    ))

    # ── Qwen Code ───────────────────────────────────────────────────
    qwen_home = os.path.join(home, ".qwen")
    catalog.append(RuntimeCatalogEntry(
        id="qwen_code", label="Qwen Code",
        roots=(
            RootSpec("memory", os.path.join(qwen_home, "QWEN.md"),
                     label="Global QWEN.md", scope="global"),
            RootSpec("memory", os.path.join(ws, "QWEN.md"),
                     label="Project QWEN.md", scope="project"),
            RootSpec("memory", os.path.join(qwen_home, "memories"),
                     ("*.md",), "Auto-memories", "global"),
            RootSpec("memory", os.path.join(qwen_home, "memories", "pinned"),
                     ("*.md",), "Pinned memories", "global"),
            RootSpec("commands", os.path.join(qwen_home, "commands"),
                     ("*.toml", "*.md"), "Custom commands", "global"),
            RootSpec("hooks", os.path.join(qwen_home, "settings.json"),
                     label="settings.json", scope="global"),
        ),
    ))

    # ── GitHub Copilot (VSCode) ─────────────────────────────────────
    catalog.append(RuntimeCatalogEntry(
        id="copilot", label="GitHub Copilot",
        roots=(
            RootSpec("memory", os.path.join(ws, ".github", "copilot-instructions.md"),
                     label="copilot-instructions.md", scope="project"),
            RootSpec("memory", os.path.join(ws, ".github", "instructions"),
                     ("*.instructions.md", "*.md"), "Path-scoped instructions", "project"),
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="AGENTS.md", scope="project"),
            RootSpec("commands", os.path.join(ws, ".github", "prompts"),
                     ("*.prompt.md", "*.md"), "Reusable prompts", "project"),
            RootSpec("agents", os.path.join(ws, ".github", "chatmodes"),
                     ("*.chatmode.md", "*.md"), "Custom chat modes", "project"),
            RootSpec("hooks", os.path.join(ws, ".vscode", "settings.json"),
                     label=".vscode/settings.json", scope="project"),
        ),
    ))

    # ── Goose (Block) ───────────────────────────────────────────────
    goose_home = os.path.join(home, ".config", "goose")
    catalog.append(RuntimeCatalogEntry(
        id="goose", label="Goose",
        roots=(
            RootSpec("memory", os.path.join(goose_home, ".goosehints"),
                     label="Global .goosehints", scope="global"),
            RootSpec("memory", os.path.join(ws, ".goosehints"),
                     label="Project .goosehints", scope="project"),
            RootSpec("memory", os.path.join(goose_home, "memory"),
                     ("*.md",), "Global memory dir", "global"),
            RootSpec("memory", os.path.join(ws, ".goose", "memory"),
                     ("*.md",), "Project memory dir", "project"),
            RootSpec("hooks", os.path.join(goose_home, "config.yaml"),
                     label="config.yaml", scope="global"),
            RootSpec("skills", os.path.join(goose_home, "extensions"),
                     label="Extensions", scope="global"),
        ),
    ))

    # ── NVIDIA NemoClaw (free) ──────────────────────────────────────
    nemo_home = os.path.expanduser("~/.nemoclaw")
    catalog.append(RuntimeCatalogEntry(
        id="nemoclaw", label="NVIDIA NemoClaw",
        roots=(
            RootSpec("memory", os.path.join(nemo_home, "memory"),
                     ("*.md",), "Agent memory", "global"),
            RootSpec("memory", os.path.join(nemo_home, "agents.yaml"),
                     label="agents.yaml", scope="global"),
            RootSpec("skills", os.path.join(nemo_home, "skills"),
                     label="Installed skills", scope="global"),
            RootSpec("skills", os.path.join(nemo_home, "source", "nemoclaw-blueprint", "skills"),
                     label="Blueprint skills", scope="global"),
            RootSpec("hooks", os.path.join(nemo_home, "config.yaml"),
                     label="config.yaml", scope="global"),
            RootSpec("hooks", os.path.join(nemo_home, "model-router-config.yaml"),
                     label="model-router-config.yaml", scope="global"),
            RootSpec("hooks", os.path.join(nemo_home, "sandboxes.json"),
                     label="sandboxes.json", scope="global"),
        ),
    ))

    # ── Hermes ──────────────────────────────────────────────────────
    hermes_home = _env_root("HERMES_HOME", os.path.expanduser("~/.hermes"))
    catalog.append(RuntimeCatalogEntry(
        id="hermes", label="Hermes",
        roots=(
            RootSpec("memory", os.path.join(hermes_home, "memory"),
                     ("*.md",), "Agent memory", "global"),
            RootSpec("skills", os.path.join(hermes_home, "skills"),
                     label="Installed skills", scope="global"),
            RootSpec("hooks", os.path.join(hermes_home, "state.db"),
                     label="state.db", scope="global"),
        ),
    ))

    # ── PicoClaw / NanoClaw (edge harnesses) ───────────────────────
    for rid, label, root in (
        ("picoclaw", "PicoClaw", os.path.expanduser("~/.picoclaw/workspace")),
        ("nanoclaw", "NanoClaw", os.path.expanduser("~/.nanoclaw")),
    ):
        catalog.append(RuntimeCatalogEntry(
            id=rid, label=label,
            roots=(
                RootSpec("memory", os.path.join(root, "memory"),
                         ("*.md",), "Agent memory", "global"),
                RootSpec("memory", os.path.join(root, "MEMORY.md"),
                         label="MEMORY.md", scope="global"),
                RootSpec("skills", os.path.join(root, "skills"),
                         label="Installed skills", scope="global"),
            ),
        ))

    # ── Pi (Inflection) ─────────────────────────────────────────────
    pi_home = os.path.expanduser("~/.pi")
    catalog.append(RuntimeCatalogEntry(
        id="pi", label="Pi",
        roots=(
            RootSpec("memory", os.path.join(pi_home, "agent", "memory"),
                     ("*.md",), "Agent memory", "global"),
        ),
    ))

    # ── DeepAgents (LangChain) ──────────────────────────────────────
    deep_home = os.path.expanduser("~/.deepagents")
    catalog.append(RuntimeCatalogEntry(
        id="deepagents", label="DeepAgents",
        roots=(
            RootSpec("memory", os.path.join(deep_home, "memory"),
                     ("*.md",), "Agent memory", "global"),
            RootSpec("memory", os.path.join(deep_home, "AGENTS.md"),
                     label="Global AGENTS.md", scope="global"),
            RootSpec("memory", os.path.join(ws, ".deepagents", "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("skills", os.path.join(deep_home, "skills"),
                     label="Installed skills", scope="global"),
        ),
    ))

    # ── n8n ─────────────────────────────────────────────────────────
    n8n_home = _env_root("N8N_USER_FOLDER", os.path.expanduser("~/.n8n"))
    catalog.append(RuntimeCatalogEntry(
        id="n8n", label="n8n",
        roots=(
            RootSpec("skills", os.path.join(n8n_home, "custom"),
                     label="Custom nodes", scope="global"),
            RootSpec("hooks", os.path.join(n8n_home, "config"),
                     label="config", scope="global"),
            RootSpec("hooks", os.path.join(n8n_home, "database.sqlite"),
                     label="database.sqlite", scope="global"),
        ),
    ))

    # ── Grok Build (xAI) ────────────────────────────────────────────
    grok_home = os.path.expanduser("~/.grok")
    catalog.append(RuntimeCatalogEntry(
        id="grok", label="Grok",
        roots=(
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("memory", grok_home, ("*.md", "*.json", "*.toml"),
                     "Grok config dir", "global", max_depth=2),
        ),
    ))

    return catalog


_ALLOWED_DOTFILES = frozenset({".cursorrules", ".goosehints", ".agents.md",
                                ".aider.conf.yml", ".aider.chat.history.md",
                                ".aider.model.settings.yml",
                                ".aider.model.metadata.json"})


def _match_globs(name: str, rel_path: str, globs: Iterable) -> bool:
    """True when ``name`` (or ``rel_path`` for path-shaped globs) matches
    any of the fnmatch-style globs.

    Empty glob list means "any file matches" (used for skills roots that
    surface every subdirectory / file).

    Globs that contain ``/`` are matched against the full relative path
    (using ``fnmatch`` — good enough for the ``**/memory/*.md`` shape
    the Claude Code auto-memory root needs). Bare-name globs match the
    filename only.
    """
    from fnmatch import fnmatch
    globs_t = tuple(globs or ())
    if not globs_t:
        return True
    rel_norm = rel_path.replace(os.sep, "/")
    for g in globs_t:
        if "/" in g:
            # Path-shaped glob. Expand ``**`` to a segment wildcard by
            # matching the trailing segment pattern anywhere in the path.
            if fnmatch(rel_norm, g.replace("**/", "*/").replace("**", "*")):
                return True
            # Also try the strict fnmatch (handles single-star segments).
            if fnmatch(rel_norm, g):
                return True
            continue
        if fnmatch(name, g):
            return True
    return False


def _walk_dir(root: str, include_globs: tuple, max_depth: int) -> list:
    """Depth-limited recursive walk.

    Returns ``[{'path': rel_posix, 'size': int, 'mtime': int}]``. Sorted by
    path. Never raises — returns [] on any error.
    """
    out: list = []
    if not root or not os.path.isdir(root):
        return out
    root_abs = os.path.abspath(root)
    for cur_dir, dirs, files in os.walk(root_abs):
        rel_dir = os.path.relpath(cur_dir, root_abs)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        if depth > max_depth:
            dirs[:] = []
            continue
        # Skip noise but keep well-known dotdirs that hold agent config.
        dirs[:] = [
            d for d in dirs
            if (not d.startswith(".")
                or d in (".claude", ".cursor", ".github", ".vscode",
                         ".codex", ".opencode", ".agents", ".goose",
                         ".openclaw", ".deepagents"))
            and d not in ("__pycache__", "node_modules", ".git", "venv",
                          ".venv", "dist", "build", ".mypy_cache")
        ]
        for fname in sorted(files):
            if fname.startswith(".") and fname not in _ALLOWED_DOTFILES:
                continue
            fpath = os.path.join(cur_dir, fname)
            rel = os.path.relpath(fpath, root_abs).replace(os.sep, "/")
            if not _match_globs(fname, rel, include_globs):
                continue
            try:
                st = os.stat(fpath)
            except OSError:
                continue
            out.append({
                "path": rel,
                "size": int(st.st_size),
                "mtime": int(st.st_mtime),
            })
    out.sort(key=lambda e: e["path"])
    return out


def list_runtimes() -> list:
    """List every catalogued runtime with a per-category found-file count.

    Shape: ``[{id, label, present, counts: {memory, skills, commands,
    agents, hooks}, roots: [{category, root, exists, scope, label}]}]``.
    Roots include ``exists`` so the UI can render greyed-out entries for
    runtimes the user hasn't installed. Never raises.
    """
    out: list = []
    for entry in _catalog():
        counts = {c: 0 for c in CATEGORIES}
        roots_info: list = []
        present = False
        for spec in entry.roots:
            root = spec.expanded_root()
            exists = os.path.exists(root)
            n = 0
            if exists:
                present = True
                if os.path.isdir(root):
                    n = len(_walk_dir(root, spec.include_globs, spec.max_depth))
                else:
                    n = 1
                counts[spec.category] = counts.get(spec.category, 0) + n
            roots_info.append({
                "category": spec.category,
                "root": root,
                "exists": exists,
                "scope": spec.scope,
                "label": spec.label or os.path.basename(root),
                "count": n,
            })
        out.append({
            "id": entry.id,
            "label": entry.label,
            "present": present,
            "counts": counts,
            "roots": roots_info,
        })
    return out


def _entry_by_id(runtime_id: str) -> Optional[RuntimeCatalogEntry]:
    for entry in _catalog():
        if entry.id == runtime_id:
            return entry
    return None


def list_files(runtime_id: str, category: Optional[str] = None) -> dict:
    """List every file for one runtime, grouped by root.

    Returns ``{'runtime': id, 'label': str, 'groups': [{root, label,
    category, scope, exists, files: [...]}]}``.

    ``category``, when set, filters roots to that one bucket. ``files``
    entries are ``{path, size, mtime}`` with ``path`` relative to the
    group's root. A root that is a single file gets one entry with
    ``path=''`` (empty relpath) so the client can still address it.
    """
    entry = _entry_by_id(runtime_id)
    if entry is None:
        return {"runtime": runtime_id, "label": "", "groups": [], "error": "unknown_runtime"}

    groups: list = []
    for spec in entry.roots:
        if category and spec.category != category:
            continue
        root = spec.expanded_root()
        exists = os.path.exists(root)
        files: list = []
        if exists:
            if os.path.isdir(root):
                files = _walk_dir(root, spec.include_globs, spec.max_depth)
            else:
                # single-file root: surface it directly
                try:
                    st = os.stat(root)
                    files = [{
                        "path": "",
                        "size": int(st.st_size),
                        "mtime": int(st.st_mtime),
                    }]
                except OSError:
                    files = []
        groups.append({
            "category": spec.category,
            "root": root,
            "label": spec.label or os.path.basename(root),
            "scope": spec.scope,
            "exists": exists,
            "files": files,
        })
    return {"runtime": entry.id, "label": entry.label, "groups": groups}


def read_runtime_file(runtime_id: str, root: str, path: str,
                      max_bytes: int = 500_000) -> dict:
    """Read one file under one of ``runtime_id``'s registered roots.

    Returns ``{'ok': True, 'path', 'content', 'size', 'mtime', 'language'}``
    or ``{'ok': False, 'error': str, 'status': int}``. ``path`` is
    interpreted **relative to ``root``**; ``root`` MUST match one of the
    runtime's catalog roots verbatim (post-expansion), so callers can only
    read what the UI has already listed.
    """
    entry = _entry_by_id(runtime_id)
    if entry is None:
        return {"ok": False, "error": "unknown_runtime", "status": 404}

    # Match root against catalog (post-expansion)
    matched_spec: Optional[RootSpec] = None
    root_norm = os.path.abspath(os.path.expanduser(root))
    for spec in entry.roots:
        if os.path.abspath(spec.expanded_root()) == root_norm:
            matched_spec = spec
            break
    if matched_spec is None:
        return {"ok": False, "error": "root not in catalog for runtime", "status": 403}

    if os.path.isdir(root_norm):
        full = os.path.normpath(os.path.join(root_norm, path or ""))
        if not full.startswith(root_norm + os.sep) and full != root_norm:
            return {"ok": False, "error": "path escapes root", "status": 403}
    else:
        # Single-file root: path must be empty (or match basename)
        if path and path not in ("", os.path.basename(root_norm)):
            return {"ok": False, "error": "path outside single-file root", "status": 403}
        full = root_norm

    if not os.path.isfile(full):
        return {"ok": False, "error": "not a file", "status": 404}

    try:
        with open(full, "rb") as fh:
            raw = fh.read(max_bytes)
    except OSError as e:
        return {"ok": False, "error": str(e), "status": 500}

    try:
        content = raw.decode("utf-8")
        binary = False
    except UnicodeDecodeError:
        content = raw.decode("utf-8", errors="replace")
        binary = True

    ext = os.path.splitext(full)[1].lower().lstrip(".")
    lang = {
        "md": "markdown", "mdc": "markdown", "markdown": "markdown",
        "py": "python", "sh": "bash", "js": "javascript", "ts": "typescript",
        "json": "json", "yaml": "yaml", "yml": "yaml", "toml": "toml",
        "html": "html", "css": "css", "sql": "sql",
    }.get(ext, "text")

    try:
        st = os.stat(full)
        size = int(st.st_size)
        mtime = int(st.st_mtime)
    except OSError:
        size = len(raw)
        mtime = 0

    return {
        "ok": True,
        "path": path,
        "content": content,
        "size": size,
        "mtime": mtime,
        "language": lang,
        "binary": binary,
        "truncated": size > len(raw),
    }
