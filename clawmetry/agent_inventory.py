"""Agent supply chain: what each agent runtime loads from disk, and what changed.

An agent loads more than its own code at session start: MCP servers named in a
config file, skills (folders with a ``SKILL.md``), plugins, instruction files
(``CLAUDE.md``, ``AGENTS.md``, ``GEMINI.md``) and hook and settings files. Any
of them can be swapped or added without the agent calling a tool, so the tool
stream stays clean until the component is used. OWASP Agentic 2026 calls this
ASI04; MITRE ATLAS calls the entry point AML.T0010.005 and the config edit
AML.T0081 (see ``framework_map.py``).

This module answers three questions, and nothing else:

* **what is configured** (:func:`collect_global`, :func:`collect_workspace`):
  one record per component with its kind, name, scope, source file, the
  runtimes that read it, a declared version and a content hash;
* **what changed since last time** (:func:`diff_inventory`): new, changed and
  removed, with the first scan of a scope recorded as a silent baseline;
* **which running session should hear about it**
  (:func:`incidents_for_session`): Guard incidents in the ``repo_scan`` shape.

Read-only by construction. It opens files and hashes bytes; it never starts,
connects to or executes a component, which is also why an MCP server's tool
descriptions are out of reach (only the running server knows them).

Secrets: an MCP server entry's ``env`` / ``headers`` VALUES are dropped before
hashing (rotating a token is not a supply-chain change) and its command
arguments are never copied into a record (they can carry a token). The hash
still covers the arguments, so a changed package pin is a change.

Requirement: REQ-GOV-SCI-001..003, Factory requirement
7fcf8127-0ba0-48b0-9926-855b1f137da4. Never raises.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

#: Every component kind the inventory records.
INVENTORY_KINDS = ("mcp_server", "skill", "plugin", "instructions", "hooks")
#: Kinds whose change raises ``agent_component_change``.
COMPONENT_KINDS = ("mcp_server", "skill", "plugin")
#: Kinds whose change raises ``agent_config_tamper`` (REQ-GOV-SCI-003).
CONFIG_KINDS = ("instructions", "hooks")

CHANGE_KIND = "agent_component_change"
CONFIG_CHANGE_KIND = "agent_config_tamper"
#: The loop_signals signature the config-file finding is stored under. It is
#: NOT ``daemon_detect_agent_config_tamper``, which ``repo_scan``'s hook-command
#: finding already owns on the same session: one row per (session, signature),
#: so sharing it would make the two findings overwrite each other every tick.
CONFIG_CHANGE_SIGNATURE = "daemon_detect_agent_config_tamper_inventory"

#: How long after a change a running session is still told about it.
DEFAULT_WINDOW_SECS = 3600


def window_secs() -> int:
    """The change window, ``CLAWMETRY_AGENT_INVENTORY_WINDOW_SECS`` or 1 hour."""
    try:
        return max(60, int(os.environ.get("CLAWMETRY_AGENT_INVENTORY_WINDOW_SECS")
                           or DEFAULT_WINDOW_SECS))
    except (TypeError, ValueError):
        return DEFAULT_WINDOW_SECS


_MAX_JSON_BYTES = 16 * 1024 * 1024
_MAX_DIR_FILES = 400
_MAX_DIR_DEPTH = 6
_MAX_FILE_BYTES = 4 * 1024 * 1024
_MAX_NAME = 80
_SKIP_DIRS = frozenset({".git", "__pycache__"})

_RUNTIME_LABELS = {
    "claude_code": "Claude Code", "codex": "Codex", "cursor": "Cursor",
    "gemini_cli": "Gemini CLI", "opencode": "opencode", "openclaw": "OpenClaw",
}
_KIND_LABELS = {
    "mcp_server": "MCP server", "skill": "skill", "plugin": "plugin",
    "instructions": "instruction file", "hooks": "hook or settings file",
}


# ── paths ────────────────────────────────────────────────────────────────────
def _home(home: Optional[str]) -> str:
    return os.path.abspath(home or os.path.expanduser("~"))


def _codex_home(home: str) -> str:
    val = os.environ.get("CODEX_HOME")
    return os.path.abspath(os.path.expanduser(val)) if val else os.path.join(home, ".codex")


def _openclaw_home(home: str) -> str:
    val = os.environ.get("OPENCLAW_HOME")
    return os.path.abspath(os.path.expanduser(val)) if val else os.path.join(home, ".openclaw")


def _label(path: str, base: str, prefix: str) -> str:
    """A short, honest name for a source file: ``~/.claude.json`` or ``.mcp.json``."""
    try:
        rel = os.path.relpath(path, base)
        if not rel.startswith(os.pardir):
            return (prefix + rel).replace(os.sep, "/")
    except ValueError:
        pass
    parts = path.replace(os.sep, "/").split("/")
    return ".../" + "/".join(parts[-3:])


def _clean_name(value: Any) -> str:
    """Config-supplied text is attacker-controllable: bound it, drop controls."""
    flat = "".join(ch for ch in str(value or "") if ch.isprintable())
    flat = " ".join(flat.split())
    return (flat[:_MAX_NAME] + "...") if len(flat) > _MAX_NAME else flat


# ── hashing ──────────────────────────────────────────────────────────────────
def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str).encode("utf-8")


#: path -> (mtime_ns, size, sha). A steady state costs a stat per file.
_FILE_HASH_CACHE: Dict[str, Tuple[int, int, str]] = {}
_FILE_HASH_CACHE_MAX = 20000


def _file_sha(path: str) -> str:
    try:
        st = os.stat(path)
    except OSError:
        return ""
    hit = _FILE_HASH_CACHE.get(path)
    if hit and hit[0] == st.st_mtime_ns and hit[1] == st.st_size:
        return hit[2]
    if st.st_size > _MAX_FILE_BYTES:
        digest = _sha(b"oversize:%d:%d" % (st.st_size, st.st_mtime_ns))
    else:
        try:
            with open(path, "rb") as fh:
                digest = _sha(fh.read())
        except OSError:
            return ""
    if len(_FILE_HASH_CACHE) >= _FILE_HASH_CACHE_MAX:
        _FILE_HASH_CACHE.clear()
    _FILE_HASH_CACHE[path] = (st.st_mtime_ns, st.st_size, digest)
    return digest


def _dir_sha(root: str) -> Tuple[str, bool]:
    """``(hash, complete)`` over every file under ``root`` (relative path +
    content). ``complete`` is False when the walk hit its file or depth bound,
    so a record can say its hash does not cover everything."""
    entries: List[Tuple[str, str]] = []
    complete = True
    base_depth = root.rstrip(os.sep).count(os.sep)
    try:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS)
            if dirpath.count(os.sep) - base_depth >= _MAX_DIR_DEPTH:
                if dirnames:
                    complete = False
                dirnames[:] = []
            for name in sorted(filenames):
                if len(entries) >= _MAX_DIR_FILES:
                    complete = False
                    break
                full = os.path.join(dirpath, name)
                if os.path.islink(full):
                    continue
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                entries.append((rel, _file_sha(full)))
            if len(entries) >= _MAX_DIR_FILES:
                complete = False
                break
    except OSError:
        pass
    return _sha(_canon(sorted(entries))), complete


#: A source file's read outcome. ``UNREADABLE`` is a file that exists but could
#: not be read, parsed or was over the size cap: it says nothing about what the
#: file declares, so its previously recorded components must be kept, not
#: reported removed (and then "new" again when the next read succeeds). The
#: runtimes rewrite these files in place (Claude Code rewrites ~/.claude.json
#: constantly), so a torn read is routine, not exotic.
ABSENT, OK, UNREADABLE = "absent", "ok", "unreadable"


class Collection(list):
    """A scope's components plus what the collection could not see.

    ``unreadable`` holds the ``source`` labels of files that exist but could
    not be read; ``complete`` is False when a whole collection step failed.
    :func:`diff_inventory` keeps previous rows it cannot vouch for.
    """

    def __init__(self, items=(), unreadable=(), complete: bool = True):
        super().__init__(items)
        self.unreadable = set(unreadable)
        self.complete = bool(complete)


def _read_text_status(path: str, limit: int = _MAX_JSON_BYTES) -> Tuple[str, Optional[str]]:
    try:
        if not os.path.isfile(path):
            return ABSENT, None
        if os.path.getsize(path) > limit:
            return UNREADABLE, None
        with open(path, encoding="utf-8", errors="replace") as fh:
            return OK, fh.read()
    except OSError:
        # Gone between the check and the open is an absence; anything else
        # (permissions, I/O) is a file we could not read.
        return (UNREADABLE if os.path.lexists(path) else ABSENT), None


def _read_text(path: str, limit: int = _MAX_JSON_BYTES) -> Optional[str]:
    status, text = _read_text_status(path, limit)
    return text if status == OK else None


def _read_json_status(path: str) -> Tuple[str, Any]:
    status, text = _read_text_status(path)
    if status != OK:
        return status, None
    try:
        return OK, json.loads(text)
    except ValueError:
        return UNREADABLE, None


def _read_json(path: str) -> Optional[Any]:
    status, data = _read_json_status(path)
    return data if status == OK else None


# ── records ──────────────────────────────────────────────────────────────────
def component_id(kind: str, scope: str, workspace: str, source: str, name: str) -> str:
    # An identity, not a security digest: nonsecret_hash so a host with a
    # restricted crypto provider does not raise here.
    from clawmetry import nonsecret_hash as _nsh
    return _nsh.sha1("|".join((kind, scope, workspace, source, name))
                     .encode("utf-8")).hexdigest()[:32]


def _component(kind: str, name: str, scope: str, workspace: str, source: str,
               readers: Iterable[str], content_hash: str, version: str = "",
               details: Optional[dict] = None) -> dict:
    name = _clean_name(name)
    return {
        "component_id": component_id(kind, scope, workspace, source, name),
        "kind": kind,
        "name": name,
        "scope": scope,
        "workspace": workspace,
        "source": source,
        "readers": list(readers),
        "version": _clean_name(version)[:40],
        "content_hash": content_hash,
        "details": details or {},
    }


# ── MCP servers ──────────────────────────────────────────────────────────────
# (readers, scope, path relative to home or workspace, container key). Each is
# a documented location; ``clawmetry/mcp_install.py`` records where each
# global one was verified.
_MCP_JSON_SOURCES = (
    (("claude_code",), "global", ".claude.json", "mcpServers"),
    (("cursor",), "global", os.path.join(".cursor", "mcp.json"), "mcpServers"),
    (("gemini_cli",), "global", os.path.join(".gemini", "settings.json"), "mcpServers"),
    (("opencode",), "global", os.path.join(".config", "opencode", "opencode.json"), "mcp"),
    (("claude_code",), "project", ".mcp.json", "mcpServers"),
    (("cursor",), "project", os.path.join(".cursor", "mcp.json"), "mcpServers"),
    (("gemini_cli",), "project", os.path.join(".gemini", "settings.json"), "mcpServers"),
)
#: Keys whose VALUES are credentials by convention. Their key names are kept
#: (adding a variable is a change); their values are not.
_SECRET_MAPS = ("env", "headers", "environment", "http_headers", "env_http_headers")


def _command_basename(command: Any) -> str:
    if isinstance(command, list):
        command = command[0] if command else ""
    tokens = str(command or "").strip().split()
    # "API_KEY=... node server.js": a leading assignment is an environment
    # value, often a credential, never the program. Skip it.
    while tokens and _ENV_ASSIGNMENT.match(tokens[0]):
        tokens.pop(0)
    return os.path.basename(tokens[0]) if tokens else ""


_ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _url_host(url: Any) -> str:
    m = re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://([^/?#@]*@)?([^/?#:]+)", str(url or ""))
    return m.group(2).lower() if m else ""


def mcp_entry_fingerprint(entry: Any) -> Tuple[str, dict]:
    """``(content_hash, details)`` for one MCP server entry.

    Environment and header values are dropped before hashing; command
    arguments are hashed but never returned. ``details`` holds only the
    transport, the command's basename and the URL's host.
    """
    if not isinstance(entry, dict):
        return _sha(_canon(entry)), {}
    shaped = dict(entry)
    for key in _SECRET_MAPS:
        if isinstance(shaped.get(key), dict):
            shaped[key] = sorted(str(k) for k in shaped[key].keys())
    command = entry.get("command")
    url = entry.get("url") or entry.get("serverUrl") or entry.get("httpUrl")
    transport = str(entry.get("type") or entry.get("transport") or "")
    if not transport:
        transport = "http" if url else ("stdio" if command else "")
    details = {"transport": _clean_name(transport)[:20],
               "command": _clean_name(_command_basename(command))[:60],
               "host": _url_host(url)}
    return _sha(_canon(shaped)), details


def _mcp_from_map(servers: Any, readers, scope, workspace, source) -> List[dict]:
    out: List[dict] = []
    if not isinstance(servers, dict):
        return out
    for name, entry in servers.items():
        digest, details = mcp_entry_fingerprint(entry)
        out.append(_component("mcp_server", name, scope, workspace, source,
                              readers, digest, details=details))
    return out


_TOML_SECTION = re.compile(r"^\s*\[([^\]]+)\]\s*(?:#.*)?$")
_TOML_MCP = re.compile(r'^mcp_servers\.("([^"]+)"|[A-Za-z0-9_-]+)(\.(.+))?$')


def _codex_mcp(path: str, source: str, unreadable: Optional[set] = None) -> List[dict]:
    """``[mcp_servers.<name>]`` tables in Codex's config.toml.

    Not a TOML parser (Python 3.9 has none in the standard library). It groups
    each server's lines, including sub-tables, drops the values of secret
    tables and ``env = {...}`` lines, and hashes what is left.
    """
    status, text = _read_text_status(path)
    if status == UNREADABLE and unreadable is not None:
        unreadable.add(source)
    if text is None:
        return []
    servers: Dict[str, List[str]] = {}
    current: Optional[str] = None
    secret_table = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        sec = _TOML_SECTION.match(line)
        if sec:
            m = _TOML_MCP.match(sec.group(1).strip())
            if m:
                current = m.group(2) or m.group(1)
                sub = (m.group(4) or "").strip()
                secret_table = sub in _SECRET_MAPS
                servers.setdefault(current, []).append("[%s]" % sub)
            else:
                current = None
            continue
        if current is None:
            continue
        key = line.split("=", 1)[0].strip()
        if secret_table:
            servers[current].append(key)
        elif key in _SECRET_MAPS:
            servers[current].append(key + "=" + ",".join(
                sorted(re.findall(r"([A-Za-z0-9_-]+)\s*=", line.split("=", 1)[1]))))
        else:
            servers[current].append(line)
    out = []
    for name, lines in servers.items():
        body = "\n".join(lines)
        cmd = re.search(r'^command\s*=\s*"([^"]*)"', body, re.M)
        url = re.search(r'^url\s*=\s*"([^"]*)"', body, re.M)
        details = {"transport": "http" if url else ("stdio" if cmd else ""),
                   "command": _clean_name(_command_basename(cmd.group(1) if cmd else ""))[:60],
                   "host": _url_host(url.group(1) if url else "")}
        out.append(_component("mcp_server", name, "global", "", source, ("codex",),
                              _sha(body.encode("utf-8")), details=details))
    return out


# ── skills and plugins ───────────────────────────────────────────────────────
_SKILL_ROOTS = (
    (("claude_code",), "global", os.path.join(".claude", "skills")),
    (("cursor",), "global", os.path.join(".cursor", "skills")),
    (("claude_code",), "project", os.path.join(".claude", "skills")),
    (("cursor",), "project", os.path.join(".cursor", "skills")),
)
_FRONTMATTER_VERSION = re.compile(r"^version\s*:\s*['\"]?([^'\"\n]+)", re.M)


def _skill_version(skill_dir: str) -> str:
    text = _read_text(os.path.join(skill_dir, "SKILL.md"), limit=256 * 1024) or ""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    m = _FRONTMATTER_VERSION.search(text[3:end if end > 0 else 2048])
    return m.group(1).strip() if m else ""


def _skills_under(root: str, readers, scope, workspace, source_base, prefix) -> List[dict]:
    out: List[dict] = []
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return out
    for name in names:
        skill_dir = os.path.join(root, name)
        if name.startswith(".") or os.path.islink(skill_dir):
            continue
        if not os.path.isfile(os.path.join(skill_dir, "SKILL.md")):
            continue
        digest, complete = _dir_sha(skill_dir)
        out.append(_component(
            "skill", name, scope, workspace,
            _label(os.path.join(skill_dir, "SKILL.md"), source_base, prefix),
            readers, digest, version=_skill_version(skill_dir),
            details={"hash_complete": complete}))
    return out


def _claude_plugins(home: str, workspace: str, unreadable: Optional[set] = None) -> List[dict]:
    """Installed Claude Code plugins, from the manifest Claude Code writes.

    The manifest, not a walk of ``~/.claude/plugins``: ``marketplaces/`` lists
    plugins that are available but not installed, and ``cache/`` keeps old
    versions side by side (see ``runtime_memory._claude_plugin_skill_roots``).
    With ``workspace`` empty this returns user-scoped plugins; with a
    workspace, only plugins installed for that project.
    """
    manifest = os.path.join(home, ".claude", "plugins", "installed_plugins.json")
    source = _label(manifest, home, "~/")
    status, data = _read_json_status(manifest)
    if status == UNREADABLE and unreadable is not None:
        unreadable.add(source)
    if not isinstance(data, dict) or not isinstance(data.get("plugins"), dict):
        return []
    out: List[dict] = []
    for full_name, entries in data["plugins"].items():
        if not isinstance(entries, list):
            continue
        for ent in entries:
            if not isinstance(ent, dict):
                continue
            project = str(ent.get("projectPath") or "")
            if workspace:
                try:
                    if not project or os.path.realpath(project) != workspace:
                        continue
                except (OSError, ValueError):
                    continue
                scope = "project"
            else:
                if project:
                    continue
                scope = "global"
            install = str(ent.get("installPath") or "")
            tree_hash, complete = (_dir_sha(install) if install and os.path.isdir(install)
                                   else ("", False))
            version = str(ent.get("version") or "") or str(ent.get("gitCommitSha") or "")[:12]
            digest = _sha(_canon({"version": ent.get("version"),
                                  "gitCommitSha": ent.get("gitCommitSha"),
                                  "tree": tree_hash}))
            name, _, market = str(full_name).partition("@")
            out.append(_component("plugin", name, scope, workspace if workspace else "",
                                  source, ("claude_code",), digest, version=version,
                                  details={"marketplace": _clean_name(market)[:60],
                                           "hash_complete": complete}))
    return out


# ── instruction, hook and settings files ────────────────────────────────────
#: Runtimes documented to read a project's AGENTS.md (see runtime_memory.py
#: and mcp_install.py's ``guidance_file``).
_AGENTS_MD_READERS = ("codex", "cursor", "opencode", "openclaw")
_INSTRUCTION_FILES = (
    (("claude_code",), "global", os.path.join(".claude", "CLAUDE.md")),
    (("gemini_cli",), "global", os.path.join(".gemini", "GEMINI.md")),
    (("claude_code",), "project", "CLAUDE.md"),
    (("claude_code",), "project", "CLAUDE.local.md"),
    (("claude_code",), "project", os.path.join(".claude", "CLAUDE.md")),
    (_AGENTS_MD_READERS, "project", "AGENTS.md"),
    (("gemini_cli",), "project", "GEMINI.md"),
)
_HOOK_FILES = (
    (("claude_code",), "global", os.path.join(".claude", "settings.json")),
    (("claude_code",), "global", os.path.join(".claude", "settings.local.json")),
    (("cursor",), "global", os.path.join(".cursor", "hooks.json")),
    # Cursor Desktop executes hooks from a project's .claude/settings.local.json
    # too (repo_scan._AGENT_HOOK_FILES records the advisory).
    (("claude_code", "cursor"), "project", os.path.join(".claude", "settings.json")),
    (("claude_code", "cursor"), "project", os.path.join(".claude", "settings.local.json")),
    (("cursor",), "project", os.path.join(".cursor", "hooks.json")),
)


def _is_clawmetry_hook(command: str) -> bool:
    try:
        from clawmetry.repo_scan import _is_clawmetry_hook as _own
        return bool(_own(command))
    except Exception:  # noqa: BLE001
        return False


_DROP = object()


def _strip_own_hooks(node: Any) -> Any:
    """The settings tree with every hook entry ClawMetry installed removed,
    so installing or updating our own gate is not reported as tampering.

    Dropping our entry must leave the tree exactly as if it had never been
    written, so a container emptied by the strip goes too: a matcher group
    whose only hook was ours, the event list that held it, the ``hooks`` map.
    """
    out = _strip(node)
    return {} if out is _DROP else out


def _strip(node: Any) -> Any:
    if isinstance(node, dict):
        if isinstance(node.get("command"), str) and _is_clawmetry_hook(node["command"]):
            return _DROP
        out = {}
        for k, v in node.items():
            s = _strip(v)
            if s is not _DROP:
                out[k] = s
        if isinstance(node.get("hooks"), list) and node["hooks"] and "hooks" not in out:
            return _DROP          # a matcher group that only held our hooks
        return _DROP if (node and not out) else out
    if isinstance(node, list):
        items = [s for s in (_strip(v) for v in node) if s is not _DROP]
        return _DROP if (node and not items) else items
    return node


def _count_hooks(node: Any) -> int:
    if isinstance(node, dict):
        own = 1 if isinstance(node.get("command"), str) else 0
        return own + sum(_count_hooks(v) for k, v in node.items() if k != "command")
    if isinstance(node, list):
        return sum(_count_hooks(v) for v in node)
    return 0


def hook_file_fingerprint(path: str) -> Optional[Tuple[str, dict]]:
    """``(content_hash, details)`` for a hook or settings file, or None when
    absent or unreadable. Hook entries ClawMetry installed are excluded from
    both hashes. A file that does not parse comes back with ``parsed: False``;
    the inventory treats that as unreadable (a runtime loads no hook from it,
    and it is usually a torn read of a file being rewritten)."""
    text = _read_text(path)
    if text is None:
        return None
    gitignored = path.endswith(".local.json")
    try:
        data = _strip_own_hooks(json.loads(text))
    except ValueError:
        digest = _sha(text.encode("utf-8"))
        return digest, {"hooks_hash": digest, "hook_count": 0,
                        "gitignored_by_convention": gitignored, "parsed": False}
    is_hooks_file = os.path.basename(path) == "hooks.json"
    hooks = data if is_hooks_file else (data.get("hooks") if isinstance(data, dict) else None)
    return _sha(_canon(data)), {
        "hooks_hash": _sha(_canon(hooks)) if hooks else "",
        "hook_count": _count_hooks(hooks),
        "gitignored_by_convention": gitignored,
        "parsed": True,
    }


def _files(specs, scope: str, base: str, prefix: str, workspace: str,
           kind: str, unreadable: Optional[set] = None) -> List[dict]:
    out: List[dict] = []
    for readers, spec_scope, rel in specs:
        if spec_scope != scope:
            continue
        path = os.path.join(base, rel)
        source = _label(path, base, prefix)
        if kind == "hooks":
            fp = hook_file_fingerprint(path)
            if fp is None or fp[1].get("parsed") is False:
                if os.path.isfile(path) and unreadable is not None:
                    unreadable.add(source)
                continue
            digest, details = fp
        else:
            if not os.path.isfile(path):
                continue
            digest, details = _file_sha(path), {}
            if not digest:
                if unreadable is not None:
                    unreadable.add(source)
                continue
        out.append(_component(kind, source, scope, workspace, source, readers,
                              digest, details=details))
    return out


# ── collection ───────────────────────────────────────────────────────────────
def collect_global(home: Optional[str] = None) -> List[dict]:
    """Every component the user's home configuration declares, as a
    :class:`Collection` that also names the sources it could not read.
    Never raises."""
    h = _home(home)
    out: List[dict] = []
    unreadable: set = set()

    def _global_mcp():
        res = []
        for readers, scope, rel, key in _MCP_JSON_SOURCES:
            if scope != "global":
                continue
            path = os.path.join(h, rel)
            status, data = _read_json_status(path)
            if status == UNREADABLE:
                unreadable.add(_label(path, h, "~/"))
            if isinstance(data, dict):
                res.extend(_mcp_from_map(data.get(key), readers, "global", "",
                                         _label(path, h, "~/")))
        return res

    steps = (
        _global_mcp,
        lambda: _codex_mcp(os.path.join(_codex_home(h), "config.toml"),
                           _label(os.path.join(_codex_home(h), "config.toml"), h, "~/"),
                           unreadable),
        lambda: [c for readers, scope, rel in _SKILL_ROOTS if scope == "global"
                 for c in _skills_under(os.path.join(h, rel), readers, "global", "", h, "~/")],
        lambda: _skills_under(os.path.join(_codex_home(h), "skills"), ("codex",),
                              "global", "", h, "~/"),
        lambda: _skills_under(os.path.join(_openclaw_home(h), "skills"), ("openclaw",),
                              "global", "", h, "~/"),
        lambda: _claude_plugins(h, "", unreadable),
        lambda: _files(_INSTRUCTION_FILES, "global", h, "~/", "", "instructions", unreadable),
        lambda: _files(((("codex",), "global", os.path.relpath(
            os.path.join(_codex_home(h), "AGENTS.md"), h)),), "global", h, "~/", "",
            "instructions", unreadable),
        lambda: _files(_HOOK_FILES, "global", h, "~/", "", "hooks", unreadable),
        lambda: _files(((("codex",), "global", os.path.relpath(
            os.path.join(_codex_home(h), "hooks.json"), h)),), "global", h, "~/", "",
            "hooks", unreadable),
    )
    complete = True
    for step in steps:
        try:
            out.extend(step() or [])
        except Exception:  # noqa: BLE001 - one broken source costs its records
            complete = False
            continue
    return Collection(_dedupe(out), unreadable, complete)


def workspace_is_scannable(workspace: str, home: Optional[str] = None) -> bool:
    """A project scope is a real directory that is neither ``/`` nor the home
    directory (whose files are the global scope already; the daemon's launchd
    cwd is ``/``)."""
    try:
        ws = os.path.realpath(workspace or "")
        return bool(workspace) and os.path.isdir(ws) and ws != os.path.realpath(_home(home)) \
            and ws != os.path.realpath(os.sep)
    except (OSError, ValueError):
        return False


def collect_workspace(workspace: str, home: Optional[str] = None) -> List[dict]:
    """Every component a project directory declares, as a :class:`Collection`.
    Never raises."""
    if not workspace_is_scannable(workspace, home):
        return Collection()
    h = _home(home)
    ws = os.path.realpath(workspace)
    out: List[dict] = []
    unreadable: set = set()

    def _claude_local_scope():
        status, data = _read_json_status(os.path.join(h, ".claude.json"))
        if status == UNREADABLE:
            unreadable.add(CLAUDE_PROJECT_SOURCE)
        projects = data.get("projects") if isinstance(data, dict) else None
        if not isinstance(projects, dict):
            return []
        for key, proj in projects.items():
            try:
                if os.path.realpath(str(key)) != ws or not isinstance(proj, dict):
                    continue
            except (OSError, ValueError):
                continue
            return _mcp_from_map(proj.get("mcpServers"), ("claude_code",), "project", ws,
                                 CLAUDE_PROJECT_SOURCE)
        return []

    def _project_mcp():
        res = []
        for readers, scope, rel, key in _MCP_JSON_SOURCES:
            if scope != "project":
                continue
            label = rel.replace(os.sep, "/")
            status, data = _read_json_status(os.path.join(ws, rel))
            if status == UNREADABLE:
                unreadable.add(label)
            if isinstance(data, dict):
                res.extend(_mcp_from_map(data.get(key), readers, "project", ws, label))
        return res

    steps = (
        _project_mcp,
        _claude_local_scope,
        lambda: [c for readers, scope, rel in _SKILL_ROOTS if scope == "project"
                 for c in _skills_under(os.path.join(ws, rel), readers, "project", ws, ws, "")],
        lambda: _claude_plugins(h, ws, unreadable),
        lambda: _files(_INSTRUCTION_FILES, "project", ws, "", ws, "instructions", unreadable),
        lambda: _files(_HOOK_FILES, "project", ws, "", ws, "hooks", unreadable),
    )
    complete = True
    for step in steps:
        try:
            out.extend(step() or [])
        except Exception:  # noqa: BLE001
            complete = False
            continue
    return Collection(_dedupe(out), unreadable, complete)


#: The source label of a project's MCP servers stored in ~/.claude.json.
CLAUDE_PROJECT_SOURCE = "~/.claude.json (this project)"


def _dedupe(items: List[dict]) -> List[dict]:
    seen: Dict[str, dict] = {}
    for c in items:
        seen.setdefault(c["component_id"], c)
    return list(seen.values())


# ── diff ─────────────────────────────────────────────────────────────────────
def diff_inventory(previous: Iterable[dict], current: Iterable[dict], *,
                   baseline: bool, now_ms: int,
                   unreadable_sources: Optional[Iterable[str]] = None,
                   complete: Optional[bool] = None) -> Tuple[List[dict], List[dict]]:
    """``(rows_to_write, changes)`` for one scope.

    ``previous`` are the stored rows of that scope, ``current`` a fresh
    collection. On a ``baseline`` pass (the scope has never been inventoried)
    every component is recorded with ``last_change="baseline"`` and no change
    is reported: "everything is new" on install is noise, not a finding.

    A previous row whose ``source`` is in ``unreadable_sources`` (a file that
    exists but could not be read or parsed), or any previous row when the
    collection was not ``complete``, is kept as stored rather than reported
    removed. A removed component that comes back with the hash it had is
    restored without a change: both cases are reads ClawMetry could not
    vouch for, and reporting them turned one torn read of ~/.claude.json into
    a "New MCP server" warning on every running session. Both default to
    what a :class:`Collection` carries.
    """
    if unreadable_sources is None:
        unreadable_sources = getattr(current, "unreadable", ()) or ()
    keep_sources = {str(s) for s in unreadable_sources}
    if complete is None:
        complete = bool(getattr(current, "complete", True))
    prev = {r.get("component_id"): r for r in previous if isinstance(r, dict)}
    rows: List[dict] = []
    changes: List[dict] = []
    for comp in current:
        p = prev.pop(comp["component_id"], None)
        was_removed = p is not None and p.get("status") == "removed"
        restored = was_removed and p.get("content_hash") == comp["content_hash"]
        row = dict(comp)
        row["details"] = dict(comp.get("details") or {})
        row["status"] = "present"
        row["last_seen"] = now_ms
        if comp.get("kind") == "hooks":
            # The stored row is all a later tick sees, so the hook hash this
            # change replaced travels in it: grading needs "did the HOOKS
            # change", not merely "did the file change".
            pdet = (p or {}).get("details") or {}
            if p is None or (was_removed and not restored):
                row["details"]["previous_hooks_hash"] = ""
            elif p.get("content_hash") != comp["content_hash"]:
                row["details"]["previous_hooks_hash"] = str(pdet.get("hooks_hash") or "")
            else:
                row["details"]["previous_hooks_hash"] = str(pdet.get("previous_hooks_hash") or "")
        if restored:
            row.update(first_seen=int(p.get("first_seen") or now_ms),
                       previous_hash=str(p.get("previous_hash") or ""),
                       last_change="restored", changed_at=now_ms,
                       change_count=int(p.get("change_count") or 0))
        elif p is None or was_removed:
            row["first_seen"] = int((p or {}).get("first_seen") or now_ms)
            row["previous_hash"] = str((p or {}).get("content_hash") or "") if p else ""
            if baseline and p is None:
                row.update(last_change="baseline", changed_at=0, change_count=0)
            else:
                row.update(last_change="new", changed_at=now_ms,
                           change_count=int((p or {}).get("change_count") or 0) + 1)
                changes.append(_change(row, p))
        elif p.get("content_hash") != comp["content_hash"]:
            row.update(first_seen=int(p.get("first_seen") or now_ms),
                       previous_hash=str(p.get("content_hash") or ""),
                       last_change="changed", changed_at=now_ms,
                       change_count=int(p.get("change_count") or 0) + 1)
            changes.append(_change(row, p))
        else:
            row.update(first_seen=int(p.get("first_seen") or now_ms),
                       previous_hash=str(p.get("previous_hash") or ""),
                       last_change=str(p.get("last_change") or "baseline"),
                       changed_at=int(p.get("changed_at") or 0),
                       change_count=int(p.get("change_count") or 0))
        rows.append(row)
    for p in prev.values():
        if p.get("status") == "removed":
            continue
        if not complete or str(p.get("source") or "") in keep_sources:
            continue  # not seen, not gone either: the stored row stands
        row = dict(p)
        row.update(status="removed", last_change="removed", changed_at=now_ms,
                   change_count=int(p.get("change_count") or 0) + 1)
        rows.append(row)
        changes.append(_change(row, p))
    return rows, changes


def _change(row: dict, previous: Optional[dict]) -> dict:
    out = {k: row.get(k) for k in ("component_id", "kind", "name", "scope", "workspace",
                                   "source", "readers", "version", "content_hash",
                                   "previous_hash", "last_change", "changed_at", "details")}
    out["previous_details"] = dict((previous or {}).get("details") or {})
    return out


# ── incidents ────────────────────────────────────────────────────────────────
def _applies(row: dict, runtime: str, cwd: str) -> bool:
    if runtime not in (row.get("readers") or []):
        return False
    if row.get("scope") == "global":
        return True
    try:
        return bool(cwd) and os.path.realpath(cwd) == row.get("workspace")
    except (OSError, ValueError):
        return False


def _config_severity(row: dict) -> Tuple[str, bool]:
    """``(severity, hooks_changed)`` for a changed instruction/hook file."""
    if row.get("kind") != "hooks":
        return "info", False
    det = row.get("details") or {}
    hooks_changed = str(det.get("hooks_hash") or "") != str(det.get("previous_hooks_hash") or "")
    if not hooks_changed:
        return "info", False
    return ("critical" if det.get("gitignored_by_convention") else "warning"), True


def _frameworks(kind: str) -> dict:
    try:
        from clawmetry.framework_map import framework_tags
        return framework_tags(kind)
    except Exception:  # noqa: BLE001
        return {}


def _readers_phrase(readers: Iterable[str]) -> str:
    names = [_RUNTIME_LABELS.get(r, r) for r in readers]
    if len(names) <= 1:
        return names[0] if names else "the agent"
    return ", ".join(names[:-1]) + " and " + names[-1]


def _evidence_rows(rows: List[dict]) -> List[dict]:
    return [{
        "kind": r.get("kind"), "name": r.get("name"), "scope": r.get("scope"),
        "source": r.get("source"), "change": r.get("last_change"),
        "changed_at": r.get("changed_at"), "version": r.get("version") or "",
        "content_hash": str(r.get("content_hash") or "")[:12],
        "previous_hash": str(r.get("previous_hash") or "")[:12],
        "readers": list(r.get("readers") or []),
    } for r in rows[:10]]


def _base_incident(kind: str, session_id: str, runtime: str, severity: str,
                   title: str, detail: str, evidence: dict) -> dict:
    return {
        "kind": kind, "session_id": session_id, "runtime": runtime,
        "severity": severity, "title": title, "detail": detail,
        "evidence": evidence, "first_bad_step": None,
        # A changed component is not a stretch of expensive tokens: no spend,
        # and "unknown" rather than an invented figure (CLAUDE.md).
        "spend_at_risk_usd": 0.0, "spend_basis": "unknown",
        "frameworks": _frameworks(kind),
    }


def incidents_for_session(recent: Iterable[dict], session_id: str, runtime: str,
                          cwd: str = "", *, now_ms: Optional[int] = None,
                          window_secs: int = DEFAULT_WINDOW_SECS) -> List[dict]:
    """Guard incidents for one running session from recent inventory changes.

    ``recent`` are stored rows (or :func:`diff_inventory` changes). Only
    ``new`` and ``changed`` inside the window count; a removal is recorded in
    the inventory and raises nothing. At most one incident per kind.
    """
    now_ms = int(now_ms if now_ms is not None else time.time() * 1000)
    horizon = now_ms - int(window_secs) * 1000
    hits = [r for r in recent if isinstance(r, dict)
            and r.get("last_change") in ("new", "changed")
            and int(r.get("changed_at") or 0) >= horizon
            and _applies(r, runtime, cwd)]
    if not hits:
        return []
    hits.sort(key=lambda r: -int(r.get("changed_at") or 0))
    out: List[dict] = []

    comps = [r for r in hits if r.get("kind") in COMPONENT_KINDS]
    if comps:
        first = comps[0]
        verb = "added" if first.get("last_change") == "new" else "changed"
        if len(comps) == 1:
            title = "%s %s %s: %s" % (
                "New" if verb == "added" else "Changed",
                _KIND_LABELS.get(first["kind"], first["kind"]),
                "for " + _RUNTIME_LABELS.get(runtime, runtime), first.get("name"))
        else:
            title = "%d MCP servers, skills or plugins added or changed" % len(comps)
        names = ", ".join("%s (%s, %s)" % (r.get("name"), _KIND_LABELS.get(r["kind"], r["kind"]),
                                           "added" if r.get("last_change") == "new" else "changed")
                          for r in comps[:5])
        detail = (
            "Something this %s session loads was %s since ClawMetry last looked: %s. "
            "Read from %s. A new or swapped MCP server, skill or plugin runs with the "
            "agent's credentials the next time it is used, and nothing in the tool "
            "stream shows the change. ClawMetry read the configuration only; it did not "
            "start or run the component. If you or your agent installed or updated it, "
            "this is expected." % (
                _RUNTIME_LABELS.get(runtime, runtime), verb if len(comps) == 1 else
                "added or changed", names, first.get("source")))
        out.append(_base_incident(
            CHANGE_KIND, session_id, runtime, "warning", title, detail,
            {"observed": "agent_inventory", "components": _evidence_rows(comps),
             "count": len(comps)}))

    configs = [r for r in hits if r.get("kind") in CONFIG_KINDS]
    if configs:
        graded = [(r,) + _config_severity(r) for r in configs]
        rank = {"info": 0, "warning": 1, "critical": 2}
        severity = max((g[1] for g in graded), key=lambda s: rank[s])
        hooks_changed = any(g[2] for g in graded)
        files = [r.get("source") for r in configs]
        head = files[0] if len(files) == 1 else "%d agent files" % len(files)
        title = ("%s changed: hook entries %s" % (head, "added or changed")
                 if hooks_changed else "%s changed" % head)
        detail = (
            "%s changed since ClawMetry last looked (%s), and %s reads %s at session "
            "start. %s"
            "If you or your agent edited %s, this is expected; otherwise read the "
            "change before the next session. ClawMetry will not edit it for you." % (
                ", ".join(files[:5]), "the hook entries changed" if hooks_changed
                else "no hook entry changed", _readers_phrase(configs[0].get("readers") or []),
                "it" if len(files) == 1 else "them",
                ("A hook runs a program with your credentials in the environment, and "
                 "a gitignored settings.local.json does not show up in git status. "
                 if severity == "critical" else
                 "A hook runs a program with your credentials in the environment. "
                 if hooks_changed else ""),
                "it" if len(files) == 1 else "them"))
        inc = _base_incident(
            CONFIG_CHANGE_KIND, session_id, runtime, severity, title, detail,
            {"observed": "agent_inventory", "components": _evidence_rows(configs),
             "count": len(configs), "hooks_changed": hooks_changed})
        inc["signal_signature"] = CONFIG_CHANGE_SIGNATURE
        out.append(inc)
    return out
