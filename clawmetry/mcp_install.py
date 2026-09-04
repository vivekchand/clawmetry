"""Register the ClawMetry MCP server with each runtime's MCP configuration
(WO-59, REQ-SELF-001).

One command, every MCP-capable runtime, and the same three rules the hook
installer (``clawmetry/hooks_claude_code.py`` + ``hook_ownership.py``)
already enforces for ``~/.claude/settings.json``:

* **merge**: the server entry is added to whatever is already there;
* **never delete a foreign entry**: another tool's server is not ours to
  touch, and neither is a ``clawmetry`` entry the operator wrote by hand;
* **uninstall removes only what install added**: a marker file
  (``~/.clawmetry/mcp_installed.json``) records each registration, and an
  entry is removed only when the marker says we wrote it AND the entry
  still looks like ours.

Formats. Each installer below was checked against the vendor's own
documentation (or, for Codex, by running the vendor's ``codex mcp add``
into a scratch ``CODEX_HOME`` and reading what it wrote). A runtime whose
format could not be verified is reported as ``unknown_format`` and its file
is never written; a runtime with no MCP client is reported as
``no_mcp_support``. Guessing a config format is how a runtime stops
starting, so we do not.

Stdlib only: this runs from ``clawmetry mcp install`` without the dashboard.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

SERVER_NAME = "clawmetry"
MARKER_PATH = os.path.expanduser("~/.clawmetry/mcp_installed.json")

# Statuses (install / status / uninstall share one vocabulary).
REGISTERED = "registered"            # install wrote it, or status: ours is present
ALREADY_PRESENT = "already_present"  # an entry named clawmetry exists (ours or not)
NOT_INSTALLED = "not_installed"
NO_MCP_SUPPORT = "no_mcp_support"
UNKNOWN_FORMAT = "unknown_format"
WOULD_REGISTER = "would_register"    # --dry-run
REMOVED = "removed"
LEFT_IN_PLACE = "left_in_place"      # present but not ours: never deleted
ERROR = "error"

# TOML block markers. Codex's config is TOML and Python 3.9 has no TOML
# writer (or reader), so our section is delimited by comment markers and
# only text between them is ever removed.
_TOML_BEGIN = "# clawmetry-mcp:begin (managed by `clawmetry mcp install`; do not edit inside)"
_TOML_END = "# clawmetry-mcp:end"

# ── Runtime registry ─────────────────────────────────────────────────────────
#
# ``format``:
#   json_mcpservers  {"mcpServers": {name: {command, args[, type]}}}
#   json_opencode    {"mcp": {name: {"type": "local", "command": [..], "enabled": true}}}
#   toml_mcp_servers [mcp_servers.name] command = ".." args = [".."]
#
# ``verified``: how the format was checked. Recorded here on purpose so a
# future reader can re-check the same source when a vendor moves things.
SUPPORTED: Dict[str, Dict[str, Any]] = {
    "claude_code": {
        "label": "Claude Code",
        "path": "~/.claude.json",
        "format": "json_mcpservers",
        "entry_type": "stdio",
        "guidance_file": "CLAUDE.md",
        "verified": "code.claude.com/docs/en/mcp (user scope: mcpServers in ~/.claude.json)",
    },
    "cursor": {
        "label": "Cursor",
        "path": "~/.cursor/mcp.json",
        "format": "json_mcpservers",
        "entry_type": "",
        "guidance_file": "AGENTS.md",
        "verified": "cursor.com/docs/context/mcp (global: ~/.cursor/mcp.json, mcpServers)",
    },
    "codex": {
        "label": "Codex CLI",
        "path": "~/.codex/config.toml",
        "format": "toml_mcp_servers",
        "entry_type": "",
        "guidance_file": "AGENTS.md",
        "verified": "`codex mcp add` output into a scratch CODEX_HOME: "
                    "[mcp_servers.<name>] command/args",
    },
    "gemini_cli": {
        "label": "Gemini CLI",
        "path": "~/.gemini/settings.json",
        "format": "json_mcpservers",
        "entry_type": "",
        "guidance_file": "GEMINI.md",
        "verified": "geminicli.com/docs/tools/mcp-server (mcpServers in ~/.gemini/settings.json)",
    },
    "opencode": {
        "label": "OpenCode",
        "path": "~/.config/opencode/opencode.json",
        "format": "json_opencode",
        "entry_type": "local",
        "guidance_file": "AGENTS.md",
        "verified": "opencode.ai/docs/mcp-servers + /docs/config (mcp: {type: local, command: [..]})",
    },
    "windsurf": {
        "label": "Windsurf",
        "path": "~/.codeium/windsurf/mcp_config.json",
        "format": "json_mcpservers",
        "entry_type": "",
        "guidance_file": "AGENTS.md",
        "verified": "docs.windsurf.com/windsurf/cascade/mcp (mcpServers in mcp_config.json)",
    },
}

# Runtimes with no MCP client to register with. Named plainly rather than
# shown as an empty row (REQ-SELF: "runtimes without MCP support are told
# so"). Keep the reason short and checkable.
NO_MCP: Dict[str, str] = {
    "aider": "Aider has no MCP client; tools are built in.",
    "lovable": "Lovable is a hosted builder with no local MCP configuration.",
    "replit": "Replit Agent is hosted; there is no local MCP configuration to write.",
    "grok_bot": "Grok Bot is a chat bot with no MCP client.",
    "picoclaw": "PicoClaw has no MCP client.",
    "nanoclaw": "NanoClaw has no MCP client.",
    "exo": "Exo is an inference cluster, not an agent with tools.",
    "openworker": "OpenWorker has no MCP client.",
    "deepseek_harness": "The DeepSeek harness has no MCP client.",
}

# Everything else that ClawMetry observes is ``unknown_format``: the runtime
# may well speak MCP, but its config location was not verified against the
# vendor's documentation, so the installer will not write to it.
_UNKNOWN_NOTE = ("MCP configuration location not verified against the vendor's "
                 "documentation; register the server by hand (see `clawmetry mcp status`).")


def _all_runtime_ids() -> List[str]:
    """Every runtime ClawMetry knows, from the entitlement catalogue when it
    is importable, plus the installer's own targets (Windsurf is not an
    observed runtime but is an MCP host)."""
    ids: List[str] = []
    try:
        from clawmetry import entitlements as _e
        ids.extend(sorted(set(_e.FREE_RUNTIMES) | set(_e.PAID_RUNTIMES)))
    except Exception:
        pass
    for rid in list(SUPPORTED) + list(NO_MCP):
        if rid not in ids:
            ids.append(rid)
    return ids


# ── Server command ───────────────────────────────────────────────────────────

def resolve_server_command() -> Tuple[str, List[str]]:
    """``(command, args)`` that starts the MCP server.

    Prefers an absolute ``clawmetry`` binary (the one on PATH, else the one
    beside this interpreter) so the entry keeps working from an IDE that
    does not inherit the shell PATH; falls back to ``python -m clawmetry``.
    """
    found = shutil.which("clawmetry")
    if found:
        return os.path.abspath(found), ["mcp"]
    sibling = os.path.join(os.path.dirname(sys.executable or ""), "clawmetry")
    if sibling and os.path.isfile(sibling) and os.access(sibling, os.X_OK):
        return sibling, ["mcp"]
    return sys.executable or "python3", ["-m", "clawmetry", "mcp"]


def _entry_is_ours(entry: Any) -> bool:
    """An entry is ours when it launches ``clawmetry mcp`` (any spelling).
    Used together with the marker: both must agree before a removal."""
    try:
        blob = json.dumps(entry, default=str).lower()
    except Exception:
        return False
    return "clawmetry" in blob and "mcp" in blob


# ── Marker file ──────────────────────────────────────────────────────────────

def _read_marker(marker_path: str) -> dict:
    try:
        with open(marker_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_marker(marker_path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(marker_path) or ".", exist_ok=True)
    tmp = marker_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
    os.replace(tmp, marker_path)


# ── JSON files ───────────────────────────────────────────────────────────────

def _read_json_file(path: str) -> Tuple[Optional[dict], str]:
    """``(data, problem)``. ``data`` is ``{}`` for a missing or empty file and
    ``None`` when the file exists but is not plain JSON (JSONC comments,
    trailing commas): we will not rewrite a file we cannot round-trip."""
    if not os.path.exists(path):
        return {}, ""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        return None, f"cannot read: {e}"
    if not text.strip():
        return {}, ""
    try:
        data = json.loads(text)
    except ValueError:
        return None, "file is not plain JSON (comments or trailing commas); edit it by hand"
    if not isinstance(data, dict):
        return None, "top level is not an object"
    return data, ""


def _write_json_file(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def _json_entry(spec: dict, command: str, args: List[str]) -> dict:
    if spec["format"] == "json_opencode":
        return {"type": "local", "command": [command] + list(args), "enabled": True}
    entry: Dict[str, Any] = {}
    if spec.get("entry_type"):
        entry["type"] = spec["entry_type"]
    entry["command"] = command
    entry["args"] = list(args)
    return entry


def _json_container_key(spec: dict) -> str:
    return "mcp" if spec["format"] == "json_opencode" else "mcpServers"


# ── TOML (Codex) ─────────────────────────────────────────────────────────────

def _toml_str(s: str) -> str:
    return json.dumps(s)  # JSON string escaping is valid TOML basic-string escaping


def _toml_block(command: str, args: List[str], name: str = SERVER_NAME) -> str:
    arr = "[" + ", ".join(_toml_str(a) for a in args) + "]"
    return (f"{_TOML_BEGIN}\n[mcp_servers.{name}]\n"
            f"command = {_toml_str(command)}\nargs = {arr}\n{_TOML_END}\n")


def _toml_has_section(text: str, name: str = SERVER_NAME) -> bool:
    pat = re.compile(r"^\s*\[mcp_servers\." + re.escape(name) + r"(?:\.[A-Za-z0-9_-]+)?\]\s*$",
                     re.MULTILINE)
    return bool(pat.search(text))


def _toml_has_our_block(text: str) -> bool:
    return _TOML_BEGIN in text and _TOML_END in text


def _toml_strip_our_block(text: str) -> str:
    start = text.find(_TOML_BEGIN)
    end = text.find(_TOML_END, start)
    if start < 0 or end < 0:
        return text
    end += len(_TOML_END)
    if end < len(text) and text[end] == "\n":
        end += 1
    head = text[:start].rstrip("\n")
    tail = text[end:].lstrip("\n")
    if head and tail:
        return head + "\n\n" + tail
    return (head + "\n") if head else tail


# ── Installer ────────────────────────────────────────────────────────────────

class Installer:
    """Per-home installer so tests (and a future ``--home``) never touch the
    operator's real files."""

    def __init__(self, home: Optional[str] = None, marker_path: Optional[str] = None,
                 command: Optional[str] = None, args: Optional[List[str]] = None):
        self.home = os.path.expanduser(home or "~")
        self.marker_path = marker_path or (
            os.path.join(self.home, ".clawmetry", "mcp_installed.json")
            if home else MARKER_PATH)
        if command is None:
            command, resolved_args = resolve_server_command()
            args = resolved_args if args is None else args
        self.command = command
        self.args = list(args or ["mcp"])

    # -- helpers ---------------------------------------------------------------
    def path_for(self, runtime: str) -> str:
        spec = SUPPORTED[runtime]
        rel = spec["path"]
        if rel.startswith("~/"):
            return os.path.join(self.home, rel[2:])
        return os.path.expanduser(rel)

    def _classify(self, runtime: str) -> Optional[dict]:
        """A terminal result for runtimes we cannot write, else ``None``."""
        rid = str(runtime or "").strip().lower()
        if rid in SUPPORTED:
            return None
        if rid in NO_MCP:
            return {"runtime": rid, "status": NO_MCP_SUPPORT, "path": "",
                    "detail": NO_MCP[rid]}
        return {"runtime": rid, "status": UNKNOWN_FORMAT, "path": "",
                "detail": _UNKNOWN_NOTE}

    def _marker_says_ours(self, runtime: str) -> bool:
        rec = _read_marker(self.marker_path).get(runtime)
        return isinstance(rec, dict) and bool(rec.get("server_name"))

    # -- status ----------------------------------------------------------------
    def status(self, runtime: str) -> dict:
        term = self._classify(runtime)
        if term:
            return term
        spec = SUPPORTED[runtime]
        path = self.path_for(runtime)
        base = {"runtime": runtime, "path": path, "label": spec["label"],
                "verified": spec["verified"]}
        if spec["format"] == "toml_mcp_servers":
            try:
                text = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else ""
            except OSError as e:
                return dict(base, status=ERROR, detail=str(e))
            if _toml_has_our_block(text) and self._marker_says_ours(runtime):
                return dict(base, status=REGISTERED, detail="registered by clawmetry mcp install")
            if _toml_has_section(text):
                return dict(base, status=ALREADY_PRESENT,
                            detail="a [mcp_servers.clawmetry] section exists that ClawMetry did not write")
            return dict(base, status=NOT_INSTALLED, detail="")
        data, problem = _read_json_file(path)
        if data is None:
            return dict(base, status=UNKNOWN_FORMAT, detail=problem)
        container = data.get(_json_container_key(spec))
        entry = container.get(SERVER_NAME) if isinstance(container, dict) else None
        if entry is None:
            return dict(base, status=NOT_INSTALLED, detail="")
        if _entry_is_ours(entry) and self._marker_says_ours(runtime):
            return dict(base, status=REGISTERED, detail="registered by clawmetry mcp install")
        return dict(base, status=ALREADY_PRESENT,
                    detail="an entry named clawmetry exists that ClawMetry did not write")

    # -- install ---------------------------------------------------------------
    def install(self, runtime: str, dry_run: bool = False) -> dict:
        term = self._classify(runtime)
        if term:
            return term
        current = self.status(runtime)
        if current["status"] == REGISTERED:
            return dict(current, status=ALREADY_PRESENT,
                        detail="already registered by clawmetry mcp install")
        if current["status"] in (ALREADY_PRESENT, UNKNOWN_FORMAT, ERROR):
            return current
        spec = SUPPORTED[runtime]
        path = current["path"]
        base = {"runtime": runtime, "path": path, "label": spec["label"],
                "verified": spec["verified"]}
        if dry_run:
            return dict(base, status=WOULD_REGISTER,
                        detail=f"would add server '{SERVER_NAME}' -> {self.command} {' '.join(self.args)}")
        try:
            if spec["format"] == "toml_mcp_servers":
                text = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else ""
                if text and not text.endswith("\n"):
                    text += "\n"
                if text.strip():
                    text += "\n"
                text += _toml_block(self.command, self.args)
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as fh:
                    fh.write(text)
                os.replace(tmp, path)
            else:
                data, problem = _read_json_file(path)
                if data is None:
                    return dict(base, status=UNKNOWN_FORMAT, detail=problem)
                key = _json_container_key(spec)
                container = data.get(key)
                if container is None:
                    container = {}
                    data[key] = container
                if not isinstance(container, dict):
                    return dict(base, status=UNKNOWN_FORMAT,
                                detail=f"'{key}' is not an object; edit it by hand")
                container[SERVER_NAME] = _json_entry(spec, self.command, self.args)
                _write_json_file(path, data)
            marker = _read_marker(self.marker_path)
            marker[runtime] = {
                "server_name": SERVER_NAME, "path": path,
                "command": self.command, "args": list(self.args),
                "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            _write_marker(self.marker_path, marker)
        except Exception as e:  # noqa: BLE001
            return dict(base, status=ERROR, detail=str(e))
        return dict(base, status=REGISTERED, detail="registered")

    # -- uninstall -------------------------------------------------------------
    def uninstall(self, runtime: str) -> dict:
        term = self._classify(runtime)
        if term:
            return term
        current = self.status(runtime)
        spec = SUPPORTED[runtime]
        path = current["path"]
        base = {"runtime": runtime, "path": path, "label": spec["label"]}
        if current["status"] == NOT_INSTALLED:
            return dict(base, status=NOT_INSTALLED, detail="")
        if current["status"] == ALREADY_PRESENT:
            return dict(base, status=LEFT_IN_PLACE,
                        detail="entry named clawmetry was not written by ClawMetry; left as is")
        if current["status"] in (UNKNOWN_FORMAT, ERROR):
            return current
        try:
            if spec["format"] == "toml_mcp_servers":
                text = open(path, "r", encoding="utf-8").read()
                new_text = _toml_strip_our_block(text)
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as fh:
                    fh.write(new_text)
                os.replace(tmp, path)
            else:
                data, problem = _read_json_file(path)
                if data is None:
                    return dict(base, status=UNKNOWN_FORMAT, detail=problem)
                key = _json_container_key(spec)
                container = data.get(key)
                if isinstance(container, dict) and _entry_is_ours(container.get(SERVER_NAME)):
                    del container[SERVER_NAME]
                    # An empty container we created is ours to drop; one the
                    # operator had before stays (a foreign key may be empty
                    # on purpose). We only know the difference from the
                    # marker, so keep it: an empty object is harmless.
                _write_json_file(path, data)
            marker = _read_marker(self.marker_path)
            marker.pop(runtime, None)
            _write_marker(self.marker_path, marker)
        except Exception as e:  # noqa: BLE001
            return dict(base, status=ERROR, detail=str(e))
        return dict(base, status=REMOVED, detail="removed the entry ClawMetry added")

    # -- fan-out ---------------------------------------------------------------
    def targets(self, runtime: Optional[str]) -> List[str]:
        rid = (runtime or "all").strip().lower()
        if rid in ("", "all"):
            return list(SUPPORTED)
        return [rid]

    def install_all(self, runtime: Optional[str] = None, dry_run: bool = False) -> List[dict]:
        return [self.install(r, dry_run=dry_run) for r in self.targets(runtime)]

    def uninstall_all(self, runtime: Optional[str] = None) -> List[dict]:
        return [self.uninstall(r) for r in self.targets(runtime)]

    def status_all(self, runtime: Optional[str] = None) -> List[dict]:
        rid = (runtime or "all").strip().lower()
        ids = _all_runtime_ids() if rid in ("", "all") else [rid]
        return [self.status(r) for r in ids]


# ── Guidance snippet (offered, never written without consent) ────────────────

GUIDANCE_MARKER = "<!-- clawmetry-mcp:guidance -->"


def guidance_snippet(runtime: str = "") -> str:
    """The instructions-file snippet an operator may paste. Written to a
    file only by :func:`write_guidance`, which only ``--write-guidance``
    calls."""
    return (
        f"{GUIDANCE_MARKER}\n"
        "## Reporting to your operators\n\n"
        "ClawMetry's MCP server is available. Before finishing a task, use the\n"
        "`report_to_operator` tool for anything that got in the way: a tool that\n"
        "kept failing, context or a permission you were missing, something you\n"
        "could not do, a task you could not finish, a block you worked around, or\n"
        "anything else the people who run you would want to know. Keep each note\n"
        "to a sentence or two.\n"
    )


def guidance_file_for(runtime: str) -> str:
    spec = SUPPORTED.get(str(runtime or "").lower())
    return spec["guidance_file"] if spec else "AGENTS.md"


def write_guidance(runtime: str, project_dir: str) -> dict:
    """Append the snippet to the runtime's instructions file in
    ``project_dir``. Idempotent via :data:`GUIDANCE_MARKER`. Only ever
    called with explicit consent (``--write-guidance``)."""
    name = guidance_file_for(runtime)
    path = os.path.join(os.path.abspath(project_dir), name)
    try:
        existing = ""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                existing = fh.read()
        if GUIDANCE_MARKER in existing:
            return {"runtime": runtime, "path": path, "status": ALREADY_PRESENT}
        with open(path, "a", encoding="utf-8") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            if existing:
                fh.write("\n")
            fh.write(guidance_snippet(runtime))
        return {"runtime": runtime, "path": path, "status": "written"}
    except Exception as e:  # noqa: BLE001
        return {"runtime": runtime, "path": path, "status": ERROR, "detail": str(e)}


# ── Support matrix for the dashboard ─────────────────────────────────────────

def support_matrix(home: Optional[str] = None) -> List[dict]:
    """One row per runtime: ``mcp`` is ``supported`` / ``not_supported`` /
    ``unknown``; ``status`` is the live registration state."""
    inst = Installer(home=home)
    rows: List[dict] = []
    for rid in _all_runtime_ids():
        st = inst.status(rid)
        if rid in SUPPORTED:
            mcp = "supported"
        elif rid in NO_MCP:
            mcp = "not_supported"
        else:
            mcp = "unknown"
        # An ``error`` row carries an OSError message in ``detail``. The CLI
        # prints it; the dashboard route does not, so the served row gets a
        # fixed sentence instead of exception text.
        detail = st.get("detail", "")
        if st.get("status") == ERROR:
            detail = "could not read this runtime's configuration file"
        rows.append({
            "runtime": rid,
            "label": SUPPORTED.get(rid, {}).get("label", rid),
            "mcp": mcp,
            "status": st.get("status"),
            "path": st.get("path", ""),
            "detail": detail,
        })
    return rows


# ── CLI ──────────────────────────────────────────────────────────────────────

_STATUS_WORDS = {
    REGISTERED: "registered",
    ALREADY_PRESENT: "already present",
    NOT_INSTALLED: "not installed",
    NO_MCP_SUPPORT: "no MCP support",
    UNKNOWN_FORMAT: "unknown config format",
    WOULD_REGISTER: "would register (dry run)",
    REMOVED: "removed",
    LEFT_IN_PLACE: "left in place (not ours)",
    ERROR: "error",
}


def _print_rows(rows: List[dict]) -> None:
    width = max([len(r["runtime"]) for r in rows] + [8])
    for r in rows:
        word = _STATUS_WORDS.get(r.get("status"), str(r.get("status")))
        line = f"  {r['runtime']:<{width}}  {word}"
        if r.get("path"):
            line += f"  {r['path']}"
        if r.get("detail") and r.get("status") not in (REGISTERED, NOT_INSTALLED):
            line += f"  ({r['detail']})"
        print(line)


def cli_main(argv: Optional[List[str]] = None) -> int:
    """``clawmetry mcp install [--runtime <id>|all] [--dry-run]
    [--write-guidance]`` | ``uninstall`` | ``status``. Exit 0 always for
    status; install/uninstall exit 1 only on a write error."""
    import argparse
    p = argparse.ArgumentParser(prog="clawmetry mcp", add_help=True)
    p.add_argument("mcp_cmd", nargs="?", default="serve",
                   choices=["serve", "install", "uninstall", "status"])
    p.add_argument("--runtime", default="all",
                   help="one runtime id (claude_code, cursor, codex, gemini_cli, "
                        "opencode, windsurf) or 'all'")
    p.add_argument("--dry-run", action="store_true",
                   help="show what install would write; write nothing")
    p.add_argument("--write-guidance", action="store_true",
                   help="also append the guidance snippet to the runtime's instructions "
                        "file in the current directory (never done without this flag)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args(argv)

    if args.mcp_cmd == "serve":
        from clawmetry.mcp_server import run
        run()
        return 0

    inst = Installer()
    if args.mcp_cmd == "status":
        rows = inst.status_all(args.runtime)
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            print("ClawMetry MCP server registration:")
            _print_rows(rows)
            print(f"\n  server command: {inst.command} {' '.join(inst.args)}")
        return 0

    if args.mcp_cmd == "install":
        rows = inst.install_all(args.runtime, dry_run=args.dry_run)
        guidance: List[dict] = []
        if args.write_guidance and not args.dry_run:
            for r in rows:
                if r.get("status") in (REGISTERED, ALREADY_PRESENT):
                    guidance.append(write_guidance(r["runtime"], os.getcwd()))
        if args.json:
            print(json.dumps({"results": rows, "guidance": guidance}, indent=2))
        else:
            print("ClawMetry MCP server install:")
            _print_rows(rows)
            print(f"\n  server command: {inst.command} {' '.join(inst.args)}")
            if guidance:
                print("\n  guidance written:")
                for g in guidance:
                    print(f"    {g['runtime']}: {g['status']}  {g['path']}")
            else:
                print("\nOffered guidance for your instructions file (CLAUDE.md, AGENTS.md, "
                      "GEMINI.md). Not written. Re-run with --write-guidance to append it to "
                      "the file in the current directory:\n")
                for line in guidance_snippet().splitlines():
                    if line.startswith("<!--"):
                        continue
                    print("    " + line)
        return 1 if any(r.get("status") == ERROR for r in rows) else 0

    rows = inst.uninstall_all(args.runtime)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print("ClawMetry MCP server uninstall:")
        _print_rows(rows)
    return 1 if any(r.get("status") == ERROR for r in rows) else 0
