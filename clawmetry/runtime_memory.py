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
import json
import os
import re as _re
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
    """One supported runtime's memory + skills roots.

    ``note`` explains a deliberately empty (or unusual) catalog so the UI
    can render an honest empty state instead of a bare "nothing found"
    (QM keeps everything in Postgres — there is nothing on disk to list).
    """

    id: str
    label: str
    roots: tuple = field(default_factory=tuple)
    note: str = ""


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


# ── Real-project resolution ─────────────────────────────────────────────
#
# ``_workspace_root()`` returns the *OpenClaw* workspace, which is the right
# project base for OpenClaw and nothing else. Every other runtime's
# ``scope="project"`` roots used to resolve against it, so the Cursor tab
# showed ``~/.openclaw/workspace/.cursor/rules`` (never exists) while the
# user's real repos went unscanned — the "why is it looking in the openclaw
# folder" report. The helpers below recover the repos the user actually
# works in from the runtimes' own registries, and _expand_project_roots()
# re-bases every project-scoped root over them.

def _encode_seg(name: str) -> str:
    return _re.sub(r"[^A-Za-z0-9-]", "-", name)


def _decode_project_slug(slug: str, max_nodes: int = 400) -> Optional[str]:
    """Resolve one Claude-style encoded-cwd slug back to a real directory.

    ``/Users/x/my.repo`` is recorded as ``-Users-x-my-repo`` — every
    non-alphanumeric character becomes ``-`` — so the encoding is LOSSY and
    the only safe decode is to walk the filesystem, matching encoded child
    names level by level. First full match wins (DFS over sorted children).
    Bounded by ``max_nodes`` directory listings. Never raises.
    """
    if not slug or not slug.startswith("-"):
        return None
    budget = [max_nodes]

    def walk(cur: str, rest: str) -> Optional[str]:
        if not rest:
            return cur
        if budget[0] <= 0:
            return None
        budget[0] -= 1
        try:
            children = sorted(os.listdir(cur))
        except OSError:
            return None
        for child in children:
            full = os.path.join(cur, child)
            if not os.path.isdir(full):
                continue
            # Accept both observed encodings: everything-non-alnum → "-"
            # (Claude Code) and the variant that preserves underscores.
            encs = {_encode_seg(child),
                    _re.sub(r"[^A-Za-z0-9_-]", "-", child)}
            for enc in encs:
                if rest == enc:
                    return full
                if rest.startswith(enc + "-"):
                    hit = walk(full, rest[len(enc) + 1:])
                    if hit:
                        return hit
        return None

    try:
        return walk(os.path.abspath(os.sep), slug[1:])
    except Exception:
        return None


def _slug_project_dirs(projects_root: str, limit: int = 4) -> list:
    """Most-recently-used real project dirs from a slug registry
    (``~/.claude/projects`` / ``~/.qwen/projects``). Never raises."""
    out: list = []
    try:
        slugs = sorted(
            ((os.path.getmtime(os.path.join(projects_root, s)), s)
             for s in os.listdir(projects_root)
             if os.path.isdir(os.path.join(projects_root, s))),
            reverse=True)
    except OSError:
        return out
    for _, slug in slugs:
        real = _decode_project_slug(slug)
        if real and real not in out:
            out.append(real)
            if len(out) >= limit:
                break
    return out


# (path, mtime) -> parsed project list, so a request doesn't re-parse the
# ~100KB ~/.claude.json on every catalog build.
_REGISTRY_CACHE: dict = {}


def _claude_registry_projects(limit: int = 8) -> list:
    """Absolute project paths from Claude Code's ``~/.claude.json`` registry.

    The registry's ``projects`` map is keyed by the real cwd (no lossy
    encoding), which makes it the best available answer to "which repos does
    this user actually work in" — good enough to *look in* for any runtime,
    because a candidate repo only ever surfaces when the runtime's own file
    (``.cursor/rules``, ``AGENTS.md``, …) actually exists there.
    """
    reg = os.path.expanduser("~/.claude.json")
    try:
        mtime = os.path.getmtime(reg)
    except OSError:
        return []
    key = (reg, mtime)
    cached = _REGISTRY_CACHE.get(key)
    if cached is None:
        try:
            with open(reg, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            cached = [p for p in (data.get("projects") or {})
                      if isinstance(p, str) and os.path.isabs(p)]
        except Exception:
            cached = []
        _REGISTRY_CACHE.clear()
        _REGISTRY_CACHE[key] = cached
    return [p for p in cached if os.path.isdir(p)][:limit]


def _candidate_project_dirs(ws: str, limit: int = 10) -> list:
    """Real project dirs to re-base project-scoped roots over.

    Sources: Claude Code's path registry, Qwen Code's slug registry, and the
    process cwd. ``ws`` (the OpenClaw workspace, already covered by the
    primary RootSpecs) is excluded. Never raises.
    """
    out: list = []
    seen = {os.path.abspath(ws)}

    def add(p):
        ap = os.path.abspath(p)
        if ap not in seen and os.path.isdir(ap):
            seen.add(ap)
            out.append(ap)

    try:
        add(os.getcwd())
    except OSError:
        pass
    # AIDER_HISTORY_DIRS is ClawMetry's own documented aider override
    # (colon-separated project dirs) — the session ingest honours it, so
    # the file browser must look in the same repos.
    for p in (os.environ.get("AIDER_HISTORY_DIRS") or "").split(os.pathsep):
        if p.strip():
            add(os.path.expanduser(p.strip()))
    for p in _claude_registry_projects():
        add(p)
    for p in _slug_project_dirs(os.path.expanduser("~/.qwen/projects")):
        add(p)
    return out[:limit]


def _expand_project_roots(catalog: list, ws: str) -> list:
    """Clone each project-scoped root over every real project dir where the
    cloned path exists.

    The ws-based primary spec is kept (it still shows "we looked here" for
    the workspace), and a clone is only added when the target actually
    exists — so runtimes the user never touched in a repo stay exactly as
    quiet as before, while real per-repo files finally surface.
    """
    candidates = _candidate_project_dirs(ws)
    if not candidates:
        return catalog
    ws_abs = os.path.abspath(ws)
    for entry in catalog:
        extra: list = []
        for spec in entry.roots:
            if spec.scope != "project":
                continue
            root = os.path.abspath(spec.expanded_root())
            if root != ws_abs and not root.startswith(ws_abs + os.sep):
                continue
            rel = os.path.relpath(root, ws_abs)
            for cand in candidates:
                clone = os.path.normpath(os.path.join(cand, rel))
                if not os.path.exists(clone):
                    continue
                base = spec.label or os.path.basename(root)
                extra.append(RootSpec(
                    spec.category, clone, spec.include_globs,
                    "%s — %s" % (base, os.path.basename(cand)),
                    "project", spec.max_depth,
                ))
        if extra:
            entry.roots = tuple(entry.roots) + tuple(extra)
    return catalog


def _nanoclaw_checkout() -> str:
    """NanoClaw keeps everything CHECKOUT-relative (no ~/.nanoclaw, no env
    in the vendor tree — see docs/PRD_NANOCLAW.md: data dir is
    cwd-relative). Mirror the pro adapter's discovery: explicit
    CLAWMETRY_NANOCLAW_DIR, then cwd, then common checkout globs. Returns
    the first candidate that looks like a NanoClaw checkout, else the env /
    first-glob fallback so the tab can still render the paths it tried.
    """
    def looks_like(d: str) -> bool:
        return (os.path.isdir(os.path.join(d, "groups"))
                or os.path.isdir(os.path.join(d, ".claude", "skills")))

    env = os.environ.get("CLAWMETRY_NANOCLAW_DIR")
    if env:
        return os.path.expanduser(env)
    try:
        cwd = os.getcwd()
        if looks_like(cwd):
            return cwd
    except OSError:
        pass
    for pat in ("~/nanoclaw*", "~/projects/nanoclaw*", "~/src/nanoclaw*",
                "~/code/nanoclaw*", "~/dev/nanoclaw*"):
        for hit in sorted(_glob.glob(os.path.expanduser(pat))):
            if looks_like(hit):
                return hit
    return os.path.expanduser("~/nanoclaw")


def _exo_workspace() -> str:
    """Exo keeps state WORKSPACE-relative (``<workspace>/.exo``; the CLI's
    ``--root`` default). Mirror the pro adapter's discovery: first
    ``CLAWMETRY_EXO_ROOTS`` entry, then common checkout globs. Returns the
    first candidate with an ``.exo`` state dir, else the first-glob
    fallback so the tab can still render the paths it tried."""
    def looks_like(d: str) -> bool:
        return os.path.isdir(os.path.join(d, ".exo"))

    env = os.environ.get("CLAWMETRY_EXO_ROOTS") or ""
    for part in env.split(os.pathsep):
        part = part.strip()
        if part:
            root = os.path.expanduser(part)
            # accept the workspace itself or its .exo dir
            return root[:-5] if root.endswith(os.sep + ".exo") else root
    for pat in ("~/exo*", "~/projects/exo*", "~/src/exo*",
                "~/code/exo*", "~/dev/exo*"):
        for hit in sorted(_glob.glob(os.path.expanduser(pat))):
            if looks_like(hit):
                return hit
    return os.path.expanduser("~/exo")


def _claude_plugin_skill_roots(claude_home: str) -> list:
    """RootSpecs for Claude Code skills that ship inside installed plugins.

    Most Claude Code users never create ``~/.claude/skills`` — their skills
    arrive as plugins — so without this the Skills tab reads "nothing found"
    on a machine with dozens of live skills.

    The authority is ``plugins/installed_plugins.json``, NOT a walk of
    ``~/.claude/plugins``:

      - ``marketplaces/`` is the catalogue of AVAILABLE plugins. Walking it
        lists skills the user has not installed.
      - ``cache/`` retains superseded versions side by side (telegram 0.0.6
        next to the live 0.0.7), so a blind walk double-counts.

    Reading the manifest gives exactly the installPaths that are live. Never
    raises — a malformed manifest just yields no plugin roots.
    """
    manifest = os.path.join(claude_home, "plugins", "installed_plugins.json")
    out: list = []
    try:
        with open(manifest, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return out
    seen: set = set()
    for name, entries in (data.get("plugins") or {}).items():
        if not isinstance(entries, list):
            continue
        for ent in entries:
            path = (ent or {}).get("installPath") or ""
            if not path:
                continue
            skills_dir = os.path.join(path, "skills")
            if skills_dir in seen or not os.path.isdir(skills_dir):
                continue
            seen.add(skills_dir)
            short = str(name).split("@")[0]
            out.append(RootSpec(
                "skills", skills_dir, ("**/SKILL.md",),
                f"Plugin: {short}",
                "project" if (ent or {}).get("scope") == "project" else "global",
                max_depth=4,
            ))
    return out


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
            # Globs matter here: agents/<id>/sessions/*.jsonl lives at depth
            # 2, so an unfiltered walk lists every session transcript as a
            # "sub-agent" and re-lists agents/main/memory/*.md.
            RootSpec("agents", os.path.join(oc_home, "agents"),
                     ("*.md", "*.json"), "Sub-agents", "global", max_depth=2),
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
            # max_depth=2: the memory files sit at <slug>/memory/*.md and
            # <slug>/MEMORY.md; anything deeper is session-transcript UUID
            # dirs the walk has no business descending.
            RootSpec("memory", os.path.join(claude_home, "projects"),
                     ("**/memory/*.md", "**/MEMORY.md"),
                     "Per-project auto-memory", "global", max_depth=2),
            RootSpec("skills", os.path.join(claude_home, "skills"),
                     label="Global skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".claude", "skills"),
                     label="Project skills", scope="project"),
            # Plugin skills are appended below from installed_plugins.json —
            # see _claude_plugin_skill_roots() for why that file and not a
            # walk of ~/.claude/plugins.
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
            RootSpec("hooks", os.path.join(claude_home, "settings.local.json"),
                     label="Global settings.local.json", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".claude", "settings.json"),
                     label="Project settings.json", scope="project"),
            RootSpec("hooks", os.path.join(ws, ".claude", "settings.local.json"),
                     label="Project settings.local.json", scope="project"),
        ) + tuple(_claude_plugin_skill_roots(claude_home)),
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
            RootSpec("memory", os.path.join(codex_home, "memories"),
                     ("*.md",), "Auto-memories", "global"),
            RootSpec("skills", os.path.join(codex_home, "skills"),
                     label="User skills", scope="global"),
            # ``.system`` is dot-prefixed, so the walk of skills/ above never
            # descends into it — the 5 built-ins (imagegen, skill-creator, …)
            # need their own root.
            RootSpec("skills", os.path.join(codex_home, "skills", ".system"),
                     label="Built-in skills", scope="global"),
            RootSpec("commands", os.path.join(codex_home, "prompts"),
                     ("*.md",), "Custom prompts", "global"),
            RootSpec("hooks", os.path.join(codex_home, "config.toml"),
                     label="Global config.toml", scope="global"),
            RootSpec("hooks", os.path.join(codex_home, "hooks.json"),
                     label="hooks.json", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".codex", "config.toml"),
                     label="Project .codex/config.toml", scope="project"),
        ),
    ))

    # ── Cursor ──────────────────────────────────────────────────────
    cursor_home = os.path.join(home, ".cursor")
    catalog.append(RuntimeCatalogEntry(
        id="cursor", label="Cursor",
        roots=(
            RootSpec("memory", os.path.join(ws, ".cursor", "rules"),
                     ("*.mdc", "*.md"), "Project rules", "project"),
            RootSpec("memory", os.path.join(ws, ".cursorrules"),
                     label=".cursorrules (legacy)", scope="project"),
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("memory", os.path.join(cursor_home, "rules"),
                     ("*.mdc", "*.md"), "Global rules", "global"),
            RootSpec("skills", os.path.join(cursor_home, "skills"),
                     label="Global skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".cursor", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("agents", os.path.join(cursor_home, "agents"),
                     ("*.md",), "Global sub-agents", "global"),
            RootSpec("agents", os.path.join(ws, ".cursor", "agents"),
                     ("*.md",), "Project sub-agents", "project"),
            RootSpec("commands", os.path.join(cursor_home, "commands"),
                     ("*.md",), "Global commands", "global"),
            RootSpec("commands", os.path.join(ws, ".cursor", "commands"),
                     ("*.md",), "Project commands", "project"),
            RootSpec("hooks", os.path.join(cursor_home, "hooks.json"),
                     label="Global hooks.json", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".cursor", "hooks.json"),
                     label="Project hooks.json", scope="project"),
            RootSpec("hooks", os.path.join(cursor_home, "mcp.json"),
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
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            # Workspace rules: current default is .agents/rules, with
            # .agent/rules (singular) kept for backward support.
            RootSpec("memory", os.path.join(ws, ".agents", "rules"),
                     ("*.md",), "Workspace rules", "project"),
            RootSpec("memory", os.path.join(ws, ".agent", "rules"),
                     ("*.md",), "Workspace rules (legacy)", "project"),
            RootSpec("memory", os.path.join(gemini_home, "antigravity-cli", "knowledge"),
                     label="Knowledge base (CLI)", scope="global"),
            # Skills ship per product surface: the CLI's builtins
            # (antigravity-cli/builtin/skills is where real installs hold
            # e.g. agy-customizations), the CLI + IDE user dirs, and the
            # cross-product config/skills path from Google's skills codelab.
            RootSpec("skills", os.path.join(gemini_home, "antigravity-cli", "builtin", "skills"),
                     label="Builtin skills (CLI)", scope="global"),
            RootSpec("skills", os.path.join(gemini_home, "antigravity-cli", "skills"),
                     label="Global skills (CLI)", scope="global"),
            RootSpec("skills", os.path.join(gemini_home, "antigravity", "skills"),
                     label="Global skills (IDE)", scope="global"),
            RootSpec("skills", os.path.join(gemini_home, "config", "skills"),
                     label="Global skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".agents", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("skills", os.path.join(gemini_home, "extensions"),
                     label="Extensions", scope="global"),
            RootSpec("commands", os.path.join(gemini_home, "commands"),
                     ("*.toml", "*.md"), "Custom commands", "global"),
            RootSpec("commands", os.path.join(ws, ".agents", "workflows"),
                     ("*.md",), "Workflows", "project"),
            RootSpec("hooks", os.path.join(gemini_home, "settings.json"),
                     label="settings.json", scope="global"),
            RootSpec("hooks", os.path.join(gemini_home, "config", "hooks.json"),
                     label="Hooks config", scope="global"),
        ),
    ))

    # ── Aider ───────────────────────────────────────────────────────
    catalog.append(RuntimeCatalogEntry(
        id="aider", label="Aider",
        roots=(
            RootSpec("memory", os.path.join(ws, "CONVENTIONS.md"),
                     label="CONVENTIONS.md", scope="project"),
            # Aider writes its history files into each project's working
            # directory (git repo root) — there is no central ~/.aider
            # sessions dir, so the history roots are project-scoped.
            RootSpec("memory", os.path.join(ws, ".aider.chat.history.md"),
                     label="Chat history", scope="project"),
            RootSpec("memory", os.path.join(ws, ".aider.input.history"),
                     label="Input history", scope="project"),
            RootSpec("hooks", os.path.join(home, ".aider.conf.yml"),
                     label="Global .aider.conf.yml", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".aider.conf.yml"),
                     label="Project .aider.conf.yml", scope="project"),
            RootSpec("hooks", os.path.join(home, ".aider.model.settings.yml"),
                     label="Global .aider.model.settings.yml", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".aider.model.settings.yml"),
                     label=".aider.model.settings.yml", scope="project"),
            RootSpec("hooks", os.path.join(home, ".aider.model.metadata.json"),
                     label=".aider.model.metadata.json", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".aider.model.metadata.json"),
                     label="Project .aider.model.metadata.json", scope="project"),
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
            # opencode also discovers the cross-runtime ~/.agents/skills
            # alias and the Claude-compat .claude/skills paths.
            RootSpec("skills", os.path.join(home, ".agents", "skills"),
                     label="Shared agent skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".agents", "skills"),
                     label="Project shared skills", scope="project"),
            RootSpec("skills", os.path.join(home, ".claude", "skills"),
                     label="Claude-compat skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".claude", "skills"),
                     label="Project Claude-compat skills", scope="project"),
            RootSpec("hooks", os.path.join(opencode_home, "plugins"),
                     ("*.ts", "*.js"), "Global plugins", "global"),
            RootSpec("hooks", os.path.join(ws, ".opencode", "plugins"),
                     ("*.ts", "*.js"), "Project plugins", "project"),
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
            # Bare-name globs match at any depth, so this single root also
            # covers memories/pinned/*.md.
            RootSpec("memory", os.path.join(qwen_home, "memories"),
                     ("*.md",), "Auto-memories", "global"),
            RootSpec("memory", os.path.join(qwen_home, "projects"),
                     ("**/memory/*.md", "**/MEMORY.md"),
                     "Per-project memory", "global", max_depth=2),
            RootSpec("skills", os.path.join(qwen_home, "skills"),
                     label="Personal skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".qwen", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("skills", os.path.join(home, ".agents", "skills"),
                     label="Shared agent skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".agents", "skills"),
                     label="Project shared skills", scope="project"),
            RootSpec("commands", os.path.join(qwen_home, "commands"),
                     ("*.toml", "*.md"), "Custom commands", "global"),
            RootSpec("hooks", os.path.join(qwen_home, "settings.json"),
                     label="settings.json", scope="global"),
        ),
    ))

    # ── GitHub Copilot (VSCode + CLI) ───────────────────────────────
    copilot_home = _env_root("CLAWMETRY_COPILOT_HOME",
                             os.path.join(home, ".copilot"))
    catalog.append(RuntimeCatalogEntry(
        id="copilot", label="GitHub Copilot",
        roots=(
            # The CLI's global home (~/.copilot) — before these landed the
            # entry was 100% project-scoped, so the tab could only ever show
            # OpenClaw-workspace paths.
            RootSpec("skills", os.path.join(copilot_home, "skills"),
                     label="Copilot CLI skills", scope="global"),
            RootSpec("skills", os.path.join(copilot_home, "installed-plugins"),
                     ("**/SKILL.md",), "Installed plugins", "global"),
            RootSpec("skills", os.path.join(home, ".agents", "skills"),
                     label="Shared agent skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".agents", "skills"),
                     label="Project shared skills", scope="project"),
            RootSpec("hooks", os.path.join(copilot_home, "hooks"),
                     ("*.json",), "Copilot hooks", "global"),
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
            # Goose "extensions" are MCP servers declared inside config.yaml,
            # not a directory — the old skills root at
            # ~/.config/goose/extensions could never populate. Real skills:
            RootSpec("skills", os.path.join(home, ".agents", "skills"),
                     label="Shared agent skills", scope="global"),
            RootSpec("skills", os.path.join(home, ".agents", "plugins"),
                     ("**/SKILL.md",), "Plugin skills", "global"),
            RootSpec("skills", os.path.join(goose_home, "skills"),
                     label="Goose skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".agents", "skills"),
                     label="Project shared skills", scope="project"),
            RootSpec("skills", os.path.join(ws, ".goose", "skills"),
                     label="Project skills (legacy)", scope="project"),
            RootSpec("commands", os.path.join(goose_home, "recipes"),
                     ("*.yaml", "*.json"), "Recipe library", "global"),
            RootSpec("commands", os.path.join(ws, ".goose", "recipes"),
                     ("*.yaml", "*.json"), "Project recipes", "project"),
        ),
    ))

    # ── NVIDIA NemoClaw (free) ──────────────────────────────────────
    nemo_home = os.path.expanduser("~/.nemoclaw")
    catalog.append(RuntimeCatalogEntry(
        id="nemoclaw", label="NVIDIA NemoClaw",
        roots=(
            # Only roots the nemo adapter / governance code actually read —
            # the old memory/ + config.yaml roots existed nowhere.
            RootSpec("agents", os.path.join(nemo_home, "agents.yaml"),
                     label="agents.yaml (agent manifest)", scope="global"),
            RootSpec("skills", os.path.join(nemo_home, "skills"),
                     label="Installed skills", scope="global"),
            RootSpec("skills", os.path.join(nemo_home, "source", "nemoclaw-blueprint", "skills"),
                     label="Blueprint skills", scope="global"),
            RootSpec("hooks",
                     _env_root("NEMOCLAW_MODEL_ROUTER_CONFIG",
                               os.path.join(nemo_home, "model-router-config.yaml")),
                     label="model-router-config.yaml", scope="global"),
            RootSpec("hooks", os.path.join(nemo_home, "proxy-config.yaml"),
                     label="proxy-config.yaml", scope="global"),
            RootSpec("hooks", os.path.join(nemo_home, "sandboxes.json"),
                     label="sandboxes.json", scope="global"),
            RootSpec("hooks", os.path.join(nemo_home, "source", "nemoclaw-blueprint", "policies"),
                     ("*.yaml", "*.yml"), "Governance policies", "global"),
        ),
    ))

    # ── Hermes ──────────────────────────────────────────────────────
    hermes_home = _env_root("HERMES_HOME", os.path.expanduser("~/.hermes"))
    catalog.append(RuntimeCatalogEntry(
        id="hermes", label="Hermes",
        roots=(
            # Hermes writes ~/.hermes/memories (plural) — the singular
            # memory/ never exists, which is why the tab rendered empty.
            RootSpec("memory", os.path.join(hermes_home, "memories"),
                     ("*.md",), "Agent memory", "global"),
            RootSpec("memory", os.path.join(hermes_home, "SOUL.md"),
                     label="SOUL.md", scope="global"),
            RootSpec("skills", os.path.join(hermes_home, "skills"),
                     label="Installed skills", scope="global"),
            RootSpec("hooks", os.path.join(hermes_home, "hooks"),
                     label="Hooks", scope="global"),
            RootSpec("hooks", os.path.join(hermes_home, "state.db"),
                     label="state.db", scope="global"),
        ),
    ))

    # ── PicoClaw (edge harness) ─────────────────────────────────────
    # Vendor layout: <home>/workspace holds the persona files + memory/
    # (MEMORY.md lives INSIDE memory/, plus daily notes memory/YYYYMM/*.md);
    # skills resolve workspace > global (<home>/skills) > builtin.
    pico_home = _env_root("PICOCLAW_HOME", os.path.expanduser("~/.picoclaw"))
    pico_ws = os.path.join(pico_home, "workspace")
    catalog.append(RuntimeCatalogEntry(
        id="picoclaw", label="PicoClaw",
        roots=(
            RootSpec("memory", os.path.join(pico_ws, "memory"),
                     ("*.md",), "Agent memory", "global"),
            RootSpec("memory", os.path.join(pico_ws, "AGENT.md"),
                     label="AGENT.md", scope="global"),
            RootSpec("memory", os.path.join(pico_ws, "SOUL.md"),
                     label="SOUL.md", scope="global"),
            RootSpec("memory", os.path.join(pico_ws, "USER.md"),
                     label="USER.md", scope="global"),
            RootSpec("memory", os.path.join(pico_ws, "IDENTITY.md"),
                     label="IDENTITY.md", scope="global"),
            RootSpec("skills", os.path.join(pico_ws, "skills"),
                     label="Workspace skills", scope="global"),
            RootSpec("skills", os.path.join(pico_home, "skills"),
                     label="Global skills", scope="global"),
        ),
    ))

    # ── NanoClaw (edge harness) ─────────────────────────────────────
    # NanoClaw keeps everything CHECKOUT-relative — there is NO ~/.nanoclaw.
    # Memory is groups/CLAUDE.md (global) + groups/<channel>_<group>/CLAUDE.md
    # (per-group); skills live at <checkout>/.claude/skills.
    nano_dir = _nanoclaw_checkout()
    catalog.append(RuntimeCatalogEntry(
        id="nanoclaw", label="NanoClaw",
        roots=(
            RootSpec("memory", os.path.join(nano_dir, "groups"),
                     ("CLAUDE.md",), "Group memory (CLAUDE.md)", "global",
                     max_depth=2),
            RootSpec("skills", os.path.join(nano_dir, ".claude", "skills"),
                     label="Skills", scope="global"),
        ),
    ))

    # ── Pi (pi coding agent) ────────────────────────────────────────
    # Pi's "memory" is its context files (AGENTS.md / CLAUDE.md and the
    # system-prompt overrides), not a memory/ dir — that root never existed.
    pi_agent = _env_root("PI_CODING_AGENT_DIR",
                         os.path.expanduser("~/.pi/agent"))
    catalog.append(RuntimeCatalogEntry(
        id="pi", label="Pi",
        roots=(
            RootSpec("memory", os.path.join(pi_agent, "AGENTS.md"),
                     label="Global AGENTS.md", scope="global"),
            RootSpec("memory", os.path.join(pi_agent, "CLAUDE.md"),
                     label="Global CLAUDE.md", scope="global"),
            RootSpec("memory", os.path.join(pi_agent, "SYSTEM.md"),
                     label="SYSTEM.md", scope="global"),
            RootSpec("memory", os.path.join(pi_agent, "APPEND_SYSTEM.md"),
                     label="APPEND_SYSTEM.md", scope="global"),
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("skills", os.path.join(pi_agent, "skills"),
                     label="Installed skills", scope="global"),
            RootSpec("skills", os.path.join(home, ".agents", "skills"),
                     label="Shared agent skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".pi", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("skills", os.path.join(ws, ".agents", "skills"),
                     label="Project shared skills", scope="project"),
            RootSpec("commands", os.path.join(pi_agent, "prompts"),
                     ("*.md",), "Prompt templates", "global"),
            RootSpec("commands", os.path.join(ws, ".pi", "prompts"),
                     ("*.md",), "Project prompt templates", "project"),
            RootSpec("hooks", os.path.join(pi_agent, "extensions"),
                     ("*.ts", "*.js"), "Extensions", "global"),
            RootSpec("hooks", os.path.join(ws, ".pi", "extensions"),
                     ("*.ts", "*.js"), "Project extensions", "project"),
        ),
    ))

    # ── DeepAgents (LangChain dcode) ────────────────────────────────
    # The layout is PER-AGENT: ~/.deepagents/<agent_name>/{AGENTS.md,
    # memories/, skills/} (default agent name is literally "agent"). Glob
    # roots on the home cover every agent name; the old flat memory/ +
    # AGENTS.md + skills/ roots never existed. The dot-prefixed .state/
    # (sessions.db checkpoint store) is skipped by the walker — sessions
    # are not memory.
    deep_home = os.path.expanduser("~/.deepagents")
    catalog.append(RuntimeCatalogEntry(
        id="deepagents", label="DeepAgents",
        roots=(
            RootSpec("memory", deep_home,
                     ("*/AGENTS.md", "*/memories/*.md"),
                     "Per-agent memory", "global", max_depth=3),
            RootSpec("skills", deep_home,
                     ("*/skills/*",), "Per-agent skills", "global"),
            RootSpec("skills", os.path.join(home, ".agents", "skills"),
                     label="Shared agent skills", scope="global"),
            RootSpec("memory", os.path.join(ws, ".deepagents", "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("skills", os.path.join(ws, ".deepagents", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("skills", os.path.join(ws, ".agents", "skills"),
                     label="Project shared skills", scope="project"),
        ),
    ))

    # ── n8n ─────────────────────────────────────────────────────────
    # N8N_USER_FOLDER is the PARENT that contains .n8n (n8n's own
    # semantics, matched by the ingest adapter) — hence the subpath.
    n8n_home = _env_root("N8N_USER_FOLDER", os.path.expanduser("~/.n8n"),
                         ".n8n")
    catalog.append(RuntimeCatalogEntry(
        id="n8n", label="n8n",
        roots=(
            # SECURITY: never add ~/.n8n/config here — it is the JSON file
            # holding n8n's credential encryptionKey. Surfacing it would
            # expose the key in the tab AND ship it through cloud sync.
            # database.sqlite is likewise excluded: a binary blob owned by
            # the ingest adapter, not browsable memory.
            RootSpec("skills", os.path.join(n8n_home, "custom"),
                     label="Custom nodes", scope="global"),
            RootSpec("skills", os.path.join(n8n_home, "nodes"),
                     ("package.json",), "Installed community nodes",
                     "global", max_depth=1),
        ),
    ))

    # ── Grok Build (xAI) ────────────────────────────────────────────
    grok_home = _env_root("CLAWMETRY_GROK_HOME", os.path.expanduser("~/.grok"))
    catalog.append(RuntimeCatalogEntry(
        id="grok", label="Grok Build",
        roots=(
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("memory", os.path.join(ws, "CLAUDE.md"),
                     label="Project CLAUDE.md", scope="project"),
            # max_depth=1 so this config-dir root doesn't re-list the
            # hooks/*.json surfaced by the dedicated hooks root below.
            RootSpec("memory", grok_home, ("*.md", "*.json", "*.toml"),
                     "Grok config dir", "global", max_depth=1),
            RootSpec("skills", os.path.join(grok_home, "skills"),
                     label="Grok skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".grok", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("hooks", os.path.join(grok_home, "hooks"),
                     label="Grok hooks", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".grok", "hooks"),
                     label="Project hooks", scope="project"),
        ),
    ))

    # ── Grok Bot (xAI, Anysphere "sand" desktop client) ─────────────
    # NOT ~/.grok -- that is Grok Build above, a different product. Grok Bot
    # keeps its agent-side files on the bot's own cloud VM; the only local
    # surface is the desktop client's settings, which is where the MCP server
    # list and the egress-tunnel switch live. No skills or hooks roots are
    # declared because Grok Bot ships neither locally: an empty root would
    # render as "none configured" when the truth is "not observable here".
    grok_bot_home = _env_root("CLAWMETRY_GROK_BOT_HOME",
                              os.path.expanduser("~/.grokbot"))
    catalog.append(RuntimeCatalogEntry(
        id="grok_bot", label="Grok Bot",
        roots=(
            RootSpec("memory", grok_bot_home, ("*.json",),
                     "Grok Bot client settings", "global", max_depth=1),
        ),
        note=("Grok Bot agents run on xAI-hosted cloud VMs; their instructions, "
              "skills and files live on the VM, not on this machine. The only "
              "local surface is the desktop client's own settings (MCP servers "
              "and the egress-tunnel switch). An empty skills list here means "
              "\u201cnot observable from this machine\u201d, not \u201cnone configured\u201d."),
    ))

    # ── DeepSeek Harness (dsh) ──────────────────────────────────────
    dsh_home = _env_root("DSH_HOME", os.path.expanduser("~/.dsh"))
    dsh_agents = _env_root("DSH_AGENTS_HOME",
                           os.path.expanduser("~/.agents"))
    catalog.append(RuntimeCatalogEntry(
        id="deepseek_harness", label="DeepSeek Harness",
        roots=(
            RootSpec("memory", os.path.join(dsh_home, "AGENTS.md"),
                     label="Global AGENTS.md", scope="global"),
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("skills", os.path.join(dsh_home, "skills"),
                     label="Installed skills", scope="global"),
            RootSpec("skills", os.path.join(dsh_home, "plugins"),
                     ("**/SKILL.md",), "Installed plugins", "global"),
            RootSpec("skills", os.path.join(dsh_agents, "skills"),
                     label="Shared agent skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".agents", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("hooks", os.path.join(dsh_home, "settings.yaml"),
                     label="settings.yaml", scope="global"),
        ),
    ))

    # ── Exo harness (exoharness/exo) ────────────────────────────────
    # State is workspace-relative: <workspace>/.exo. The self-prompt lives
    # in the checkout (exo/prompts/me.md), the local profile in
    # .exo/exo-profile.md, and agent-editable tool modules under
    # .exo/{tools,agent-tools,tool-sources}. Durable memory artifacts are
    # binary blobs inside the event store, not files — the adapter, not
    # this catalog, surfaces those.
    exo_ws = _exo_workspace()
    catalog.append(RuntimeCatalogEntry(
        id="exo", label="Exo",
        roots=(
            RootSpec("memory", os.path.join(exo_ws, ".exo", "exo-profile.md"),
                     label="Local profile", scope="global"),
            RootSpec("memory", os.path.join(exo_ws, "exo", "prompts"),
                     ("*.md",), "Self-prompts", "global"),
            RootSpec("skills", os.path.join(exo_ws, ".exo", "tools"),
                     label="Tool registry", scope="global"),
            RootSpec("skills", os.path.join(exo_ws, ".exo", "agent-tools"),
                     label="Agent tools", scope="global"),
            RootSpec("skills", os.path.join(exo_ws, ".exo", "tool-sources"),
                     label="Tool sources", scope="global"),
        ),
    ))

    # ── Gemini CLI (google-gemini/gemini-cli) ───────────────────────
    # Memory is GEMINI.md (DEFAULT_CONTEXT_FILENAME in the v0.56.0 bundle),
    # loaded globally from <home>/.gemini/GEMINI.md and per-project from
    # ./GEMINI.md and ./.gemini/GEMINI.md. Skills/commands/policies live under
    # the global .gemini dir (getUserSkillsDir / getUserCommandsDir /
    # getUserPoliciesDir), with project-local mirrors under <ws>/.gemini.
    # NOTE the env var names the dir CONTAINING .gemini, unlike KIMI_SHARE_DIR.
    gemini_home = os.path.join(
        _env_root("GEMINI_CLI_HOME", os.path.expanduser("~")), ".gemini")
    catalog.append(RuntimeCatalogEntry(
        id="gemini_cli", label="Gemini CLI", roots=(
            RootSpec("memory", os.path.join(gemini_home, "GEMINI.md"),
                     label="Global GEMINI.md", scope="global"),
            RootSpec("memory", os.path.join(ws, "GEMINI.md"),
                     label="Project GEMINI.md", scope="project"),
            RootSpec("memory", os.path.join(ws, ".gemini", "GEMINI.md"),
                     label="Project .gemini/GEMINI.md", scope="project"),
            RootSpec("skills", os.path.join(gemini_home, "skills"),
                     label="Installed skills", scope="global"),
            RootSpec("skills", os.path.join(ws, ".gemini", "skills"),
                     label="Project skills", scope="project"),
            RootSpec("skills", os.path.join(gemini_home, "commands"),
                     label="Custom commands", scope="global"),
            RootSpec("hooks", os.path.join(gemini_home, "settings.json"),
                     label="settings.json", scope="global"),
        ),
    ))

    # ── OpenWorker (github.com/andrewyng/openworker) ────────────────
    # Instructions are AGENTS.md, and OpenWorker reads BOTH a project one and a
    # user-global one it keeps in its own state dir (coworker/project.py returns
    # state_dir()/AGENTS.md). Skills live in state_dir()/skills as folders
    # (skills/store.py: "folder-is-truth"); mcp.json is its MCP client config.
    ow_home = _env_root("COWORKER_STATE_DIR",
                        os.path.expanduser("~/.config/coworker"))
    catalog.append(RuntimeCatalogEntry(
        id="openworker", label="OpenWorker", roots=(
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("memory", os.path.join(ow_home, "AGENTS.md"),
                     label="Global AGENTS.md", scope="global"),
            RootSpec("skills", os.path.join(ow_home, "skills"),
                     ("*/SKILL.md", "*/*.md"), "Skills", "global"),
            RootSpec("mcp", os.path.join(ow_home, "mcp.json"),
                     label="mcp.json", scope="global"),
        ),
    ))

    # ── OpenHands (github.com/OpenHands/OpenHands) ──────────────────
    # Repo instructions are AGENTS.md (and the legacy .openhands/microagents
    # tree, which OpenHands still reads). Skills and MCP config live under the
    # user home; hooks.json is the CLI's hook config.
    oh_home = _env_root("OPENHANDS_PERSISTENCE_DIR",
                        os.path.expanduser("~/.openhands"))
    catalog.append(RuntimeCatalogEntry(
        id="openhands", label="OpenHands", roots=(
            RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                     label="Project AGENTS.md", scope="project"),
            RootSpec("memory", os.path.join(ws, ".openhands", "microagents"),
                     ("**/*.md",), "Project microagents", "project"),
            RootSpec("skills", os.path.join(oh_home, "cache", "skills"),
                     label="Cached skills", scope="global"),
            RootSpec("hooks", os.path.join(oh_home, "hooks.json"),
                     label="hooks.json", scope="global"),
        ),
    ))

    # ── Cline (github.com/cline/cline) ──────────────────────────────
    # Rules are .clinerules -- a FILE or a DIRECTORY of .md files, both
    # supported by Cline -- project-local and global. Workflows live beside
    # them. The CLI home also carries hooks/ and installed skills.
    cline_home = _env_root("CLINE_DIR", os.path.expanduser("~/.cline"))
    catalog.append(RuntimeCatalogEntry(
        id="cline", label="Cline", roots=(
            RootSpec("memory", os.path.join(ws, ".clinerules"),
                     label="Project .clinerules", scope="project"),
            RootSpec("memory", os.path.join(cline_home, "rules"),
                     label="Global rules", scope="global"),
            RootSpec("skills", os.path.join(ws, ".clinerules", "workflows"),
                     ("**/*.md",), "Project workflows", "project"),
            RootSpec("skills", os.path.join(cline_home, "skills"),
                     label="Installed skills", scope="global"),
            RootSpec("hooks", os.path.join(cline_home, "hooks"),
                     label="Hooks", scope="global"),
        ),
    ))

    # ── Kimi CLI / Kimi Code CLI (MoonshotAI/kimi-cli) ──────────────
    # One share dir ($KIMI_SHARE_DIR, default ~/.kimi; the standalone Kimi
    # Code CLI uses ~/.kimi-code). Memory is AGENTS.md, checked at
    # <dir>/.kimi/AGENTS.md AND <dir>/AGENTS.md from project root to cwd
    # (kimi_cli/soul/agent.py). Skills are discovered brand-group first —
    # ~/.kimi/skills, then ~/.claude/skills and ~/.codex/skills, plus the
    # cross-vendor ~/.agents/skills and ~/.config/agents/skills — and the
    # same names project-locally (kimi_cli/skill/__init__.py). We list the
    # kimi-owned roots; the borrowed Claude/Codex ones already appear under
    # those runtimes and are not double-counted here.
    kimi_home = _env_root("KIMI_SHARE_DIR", os.path.expanduser("~/.kimi"))
    kimi_code_home = os.path.expanduser("~/.kimi-code")
    kimi_roots = [
        RootSpec("memory", os.path.join(kimi_home, "AGENTS.md"),
                 label="Global AGENTS.md", scope="global"),
        RootSpec("memory", os.path.join(ws, ".kimi", "AGENTS.md"),
                 label="Project .kimi/AGENTS.md", scope="project"),
        RootSpec("memory", os.path.join(ws, "AGENTS.md"),
                 label="Project AGENTS.md", scope="project"),
        RootSpec("skills", os.path.join(kimi_home, "skills"),
                 label="Installed skills", scope="global"),
        RootSpec("skills", os.path.join(kimi_home, "plugins"),
                 ("**/SKILL.md",), "Installed plugins", "global"),
        RootSpec("skills", os.path.join(ws, ".kimi", "skills"),
                 label="Project skills", scope="project"),
        RootSpec("hooks", os.path.join(kimi_home, "config.toml"),
                 label="config.toml (hooks)", scope="global"),
    ]
    if os.path.isdir(kimi_code_home):
        kimi_roots += [
            RootSpec("memory", os.path.join(kimi_code_home, "AGENTS.md"),
                     label="Kimi Code global AGENTS.md", scope="global"),
            RootSpec("skills", os.path.join(kimi_code_home, "skills"),
                     label="Kimi Code skills", scope="global"),
            RootSpec("hooks", os.path.join(kimi_code_home, "config.toml"),
                     label="Kimi Code config.toml (hooks)", scope="global"),
        ]
    catalog.append(RuntimeCatalogEntry(
        id="kimi", label="Kimi CLI", roots=tuple(kimi_roots),
    ))

    # ── Devin CLI (cli.devin.ai) ────────────────────────────────────
    # Paths are the CLI's own answer, not a guess: `devin skills paths`
    # prints the four skill roots below and `devin rules paths` prints
    # .windsurf/rules as Devin's always-on rules (Windsurf is Cognition's
    # too, so that IS Devin's rule format). `devin rules paths` also lists
    # .cursor/rules as a conditional import; that root belongs to the
    # Cursor entry and is deliberately NOT duplicated here, or the same
    # file would be attributed to two runtimes.
    devin_cfg = _env_root("DEVIN_CONFIG_DIR",
                          os.path.expanduser("~/.config/devin"))
    devin_agents = os.path.expanduser("~/.agents")
    catalog.append(RuntimeCatalogEntry(
        id="devin", label="Devin",
        roots=(
            RootSpec("skills", os.path.join(devin_cfg, "skills"),
                     ("**/SKILL.md",), "User skills", "global"),
            RootSpec("skills", os.path.join(devin_agents, "skills"),
                     ("**/SKILL.md",), "Shared agent skills", "global"),
            RootSpec("skills", os.path.join(ws, ".devin", "skills"),
                     ("**/SKILL.md",), "Project skills", "project"),
            RootSpec("skills", os.path.join(ws, ".agents", "skills"),
                     ("**/SKILL.md",), "Shared project skills", "project"),
            RootSpec("memory", os.path.join(ws, ".windsurf", "rules"),
                     ("*.md",), "Always-on rules", "project"),
            RootSpec("hooks", os.path.join(devin_cfg, "config.json"),
                     label="config.json", scope="global"),
            RootSpec("hooks", os.path.join(devin_cfg, "mcp_config.json"),
                     label="mcp_config.json", scope="global"),
            RootSpec("hooks", os.path.join(ws, ".devin", "mcp_config.json"),
                     label="Project MCP servers", scope="project"),
        ),
    ))

    # ── QM (yc-software/qm) ─────────────────────────────────────────
    # QM persists everything to Postgres — there is nothing on disk to
    # browse. An explicit empty entry keeps /api/runtimes/qm/files from
    # 404ing and lets the UI render an honest empty state; the memory /
    # skills a QM user actually has live in the delegated child runtimes
    # (Pi, opencode, Codex, Claude Code), which have their own entries.
    catalog.append(RuntimeCatalogEntry(
        id="qm", label="QM",
        roots=(),
        note=("QM stores sessions and memory in Postgres — no on-disk "
              "memory or skills files. Instruction files live in the "
              "delegated child runtimes (Pi, opencode, Codex, Claude Code)."),
    ))

    return _expand_project_roots(catalog, ws)


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
    # followlinks=True: a skill directory is very often a SYMLINK
    # (``<repo>/.claude/skills/x -> <repo>/.agents/skills/x`` is how one skill
    # serves several runtimes). os.walk defaults to followlinks=False, which
    # reports the link in ``dirs`` and never descends — the skill vanishes
    # with no error. ``visited`` on realpath keeps a symlink cycle from
    # walking forever.
    visited: set = set()
    for cur_dir, dirs, files in os.walk(root_abs, followlinks=True):
        try:
            real = os.path.realpath(cur_dir)
        except OSError:
            real = cur_dir
        if real in visited:
            dirs[:] = []
            continue
        visited.add(real)
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
                    files = _walk_dir(root, spec.include_globs, spec.max_depth)
                    n = len(files)
                    if spec.category == "skills":
                        # A skill is a SKILL.md-bearing directory, and one
                        # skill ships many files (references/, scripts/…).
                        # Counting raw files reported Hermes as "406
                        # skills" when it has 83 — count skills, not files,
                        # whenever the root follows the SKILL.md convention.
                        skill_md = sum(
                            1 for f in files
                            if os.path.basename(f["path"]) == "SKILL.md")
                        if skill_md:
                            n = skill_md
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
        item = {
            "id": entry.id,
            "label": entry.label,
            "present": present,
            "counts": counts,
            "roots": roots_info,
        }
        if entry.note:
            item["note"] = entry.note
        out.append(item)
    return out


#: The Skills tab's buckets. The catalog has five categories and the UI has
#: two tabs: Memory owns ``memory``, Skills owns everything else — the things
#: an agent can invoke or is configured by. Splitting Skills down to the
#: ``skills`` bucket alone would leave slash commands, sub-agent definitions
#: and hooks collected but displayed nowhere.
SKILLS_TAB_CATEGORIES: tuple = ("skills", "commands", "agents", "hooks")


def runtime_is_locked(runtime_id: str) -> bool:
    """True when this runtime needs a paid entitlement the caller lacks.

    THE single predicate for the memory/skills paywall. Three callers must
    agree or the paywall leaks:

      * ``routes/runtime_memory.py`` — returns 402 / omits from the ``all``
        sweep.
      * the sync daemon's ingest — never writes a locked runtime's files.
      * the sync daemon's cache-push build — never SHIPS them, which is a
        separate decision: rows written while entitled would otherwise keep
        riding the heartbeat after the entitlement lapsed.

    Free runtimes are never locked. For paid runtimes ``allows_runtime`` on
    the resolved entitlement is authoritative (it already honours grace mode).
    Any exception falls OPEN — a resolver hiccup must not blank out a paying
    user's memory, and the read endpoints re-check on every request.
    """
    try:
        from clawmetry.entitlements import FREE_RUNTIMES, get_entitlement
    except Exception:
        return False
    if runtime_id in FREE_RUNTIMES:
        return False
    try:
        return not bool(get_entitlement().allows_runtime(runtime_id))
    except Exception:
        return False


def parse_categories(category) -> set:
    """Normalise a category filter into a set of valid category names.

    Accepts ``None`` (no filter), one name, a comma-separated string, or an
    iterable. Unknown names are dropped rather than raising — the caller
    validates for a 400; this stays permissive so an internal caller can't
    trip on a stray empty segment.
    """
    if not category:
        return set()
    if isinstance(category, str):
        parts = [c.strip() for c in category.split(",")]
    else:
        parts = [str(c).strip() for c in category]
    return {c for c in parts if c in CATEGORIES}


def _entry_by_id(runtime_id: str) -> Optional[RuntimeCatalogEntry]:
    for entry in _catalog():
        if entry.id == runtime_id:
            return entry
    return None


def list_files(runtime_id: str, category: Optional[str] = None) -> dict:
    """List every file for one runtime, grouped by root.

    Returns ``{'runtime': id, 'label': str, 'groups': [{root, label,
    category, scope, exists, files: [...]}]}``.

    ``category`` filters roots. It accepts one bucket (``"memory"``) or a
    comma-separated set (``"skills,commands,agents,hooks"``) — the catalog
    has five categories and the UI has two tabs, so the Skills tab asks for
    the four non-memory buckets in one call rather than leaving commands,
    sub-agent definitions and hooks with nowhere to appear.

    ``files`` entries are ``{path, size, mtime}`` with ``path`` relative to
    the group's root. A root that is a single file gets one entry with
    ``path=''`` (empty relpath) so the client can still address it.
    """
    entry = _entry_by_id(runtime_id)
    if entry is None:
        return {"runtime": runtime_id, "label": "", "groups": [], "error": "unknown_runtime"}
    return _files_for_entry(entry, category)


def _files_for_entry(entry: RuntimeCatalogEntry,
                     category: Optional[str] = None) -> dict:
    """:func:`list_files` body, taking an already-resolved catalog entry so
    :func:`list_all_files` can sweep one catalog build instead of twenty."""
    wanted = parse_categories(category)
    groups: list = []
    for spec in entry.roots:
        if wanted and spec.category not in wanted:
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
    for g in groups:
        g["runtime"] = entry.id
        g["runtime_label"] = entry.label
    payload = {"runtime": entry.id, "label": entry.label, "groups": groups}
    if entry.note:
        payload["note"] = entry.note
    return payload


def list_all_files(category: Optional[str] = None,
                   allowed: Optional[Iterable] = None) -> dict:
    """Aggregate :func:`list_files` across every catalogued runtime.

    Backs the "All runtimes" scope of the Memory / Skills browser. Only
    groups that actually exist on disk are returned — the per-runtime
    view is where we spell out the paths we looked at and came up empty,
    because listing every absent root for 28 runtimes would be a wall of
    noise rather than an answer.

    ``allowed``, when given, restricts the sweep to that set of runtime
    ids (the caller passes the entitled ones so a locked paid runtime's
    file paths never leak into an aggregate the user can't open).
    """
    allowed_set = set(allowed) if allowed is not None else None
    groups: list = []
    for entry in _catalog():
        if allowed_set is not None and entry.id not in allowed_set:
            continue
        payload = _files_for_entry(entry, category=category)
        for g in payload.get("groups") or ():
            if g.get("exists") and (g.get("files") or []):
                groups.append(g)
    return {"runtime": "all", "label": "All runtimes", "groups": groups}


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


# ── Project-relative root contract (consumed by repo_readiness) ─────────────
#
# ``clawmetry/repo_readiness.py`` scores an arbitrary code repo on how legible
# it is to an agent. The set of files a runtime reads INSIDE a repo
# (``CLAUDE.md``, ``AGENTS.md``, ``.cursor/rules/``, ``.github/prompts/``, …)
# is already declared once, here, as the ``scope="project"`` RootSpecs. This
# helper exposes those declarations as repo-relative paths so the scorer
# DERIVES its file list from the catalog instead of hand-maintaining a second
# copy that would silently drift every time a runtime is added.
#
# Only roots that live at or under the workspace root are returned: the
# ``_expand_project_roots`` clones point at OTHER checkouts and are not part of
# the per-repo contract.

def project_relative_roots(categories: Optional[Iterable] = None) -> list:
    """Every ``scope="project"`` root as a repo-relative path.

    Returns ``[{runtime, runtime_label, category, rel, label, globs}, …]``
    where ``rel`` is the path relative to the repo root (e.g. ``CLAUDE.md``,
    ``.claude/skills``). Deduped, stably ordered, never raises.
    """
    wanted = parse_categories(categories) if categories is not None else set(CATEGORIES)
    try:
        ws = os.path.abspath(_workspace_root())
    except OSError:
        return []
    out: list = []
    seen = set()
    try:
        catalog = _catalog()
    except Exception:
        return []
    for entry in catalog:
        for spec in entry.roots:
            if spec.scope != "project" or spec.category not in wanted:
                continue
            try:
                root = os.path.abspath(spec.expanded_root())
                rel = os.path.relpath(root, ws)
            except (OSError, ValueError):
                continue
            # Skip clones that live outside this repo, and the degenerate
            # "the repo root itself is the root" case.
            if rel == os.curdir or rel.startswith(os.pardir) or os.path.isabs(rel):
                continue
            key = (entry.id, spec.category, rel)
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "runtime": entry.id,
                "runtime_label": entry.label,
                "category": spec.category,
                "rel": rel.replace(os.sep, "/"),
                "label": spec.label or os.path.basename(rel),
                "globs": tuple(spec.include_globs or ()),
            })
    return out
