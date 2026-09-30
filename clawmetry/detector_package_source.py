"""clawmetry/detector_package_source.py: the ``untrusted_package_source`` Guard detector.

Defined here, registered in ``clawmetry/detectors.py`` (``DETECTOR_KINDS`` and
``_ALL_DETECTORS``). Tracked in vivekchand/clawmetry-pro#242.

What it reads: tool-call ARGUMENTS whose key says "this is a version or a
package" (``version``, ``package``, ``spec``, ``dependency``, ...) and whose
value names a package SOURCE instead: ``file:``, ``link:``, ``npm:``,
``git+ssh:``, ``github:``, an ``http(s)`` tarball, or a bare path.

Why: CVE-2026-59176 (functype-mcp-server). An MCP tool takes a ``version``
string, builds ``functype@<version>`` and runs ``pnpm add`` on it, then imports
the result. ``version: "file:/tmp/evil"`` installs and runs attacker code
inside the MCP server's process. That runs agent -> server, the opposite
direction from prompt injection, and the argument looks like a version number.

What it raises, recognition not suppression:

* ``critical`` when the source is a local path in a temp directory, or an
  absolute path outside the session's working directory (``facts["cwd"]``);
* ``warning`` for every other source: a git remote, a registry alias, a URL,
  a relative path, or an absolute path while the working directory is unknown.
  Some teams pin ``git+ssh:`` or ``file:`` on purpose, so the finding says
  which source it was rather than staying quiet.

Semver ranges, dist-tags (``latest``, ``next``) and bare commit SHAs are
versions, and never fire. A shell command's text (``npm i file:...``) is not
read here: that is ``tool_risk``'s surface. URLs are reported as scheme and
host only, so a token in ``https://user:token@host/x.tgz`` never reaches the
finding. Pure, bounded, never raises.
"""
from __future__ import annotations

import json
import os
import re
from typing import Iterable, Optional

# Argument-key words that mean "the value is a version or a package spec".
# Matched per word after splitting snake_case, kebab-case and camelCase, so
# ``packageSpec``, ``version_range`` and ``dep`` all count, and ``path``,
# ``file`` and ``command`` never do.
_SPEC_KEY_WORDS = frozenset({
    "version", "versions", "ver", "package", "packages", "pkg", "pkgs",
    "spec", "specs", "specifier", "dependency", "dependencies", "dep", "deps",
})
# Only a version-ish key reads ``owner/repo`` as the npm GitHub shorthand. A
# ``package`` key holding ``owner/repo`` is more often a name than a source.
_VERSION_KEY_WORDS = frozenset({"version", "versions", "ver"})

_LOCAL_SCHEMES = ("file:", "link:", "portal:")
_GIT_SCHEMES = ("git+ssh:", "git+https:", "git+http:", "git+file:", "git:",
                "github:", "gitlab:", "bitbucket:", "gist:")
_HOSTED_GIT = {"github": "github.com", "gitlab": "gitlab.com",
               "bitbucket": "bitbucket.org", "gist": "gist.github.com"}
_TEMP_DIRS = ("/tmp/", "/var/tmp/", "/private/tmp/", "/private/var/tmp/",
              "/dev/shm/", "/private/var/folders/", "/var/folders/")

_KEY_SPLIT = re.compile(r"[_\-.\s]+|(?<=[a-z0-9])(?=[A-Z])")
# ``name@tail`` or ``@scope/name@tail``: the tail is what npm resolves.
_NAME_AT = re.compile(r"^(@?[^@\s/:]+(?:/[^@\s/:]+)?)@(.+)$")
_GH_SHORTHAND = re.compile(r"^[A-Za-z0-9][\w.-]*/[\w.-]+(?:#[\w./-]+)?$")
_WIN_ABS = re.compile(r"^[A-Za-z]:[\\/]")
_URL_HOST = re.compile(r"^[a-z][a-z0-9+.-]*://(?:[^/@\s]*@)?([^/:?#\s]+)", re.I)
_SCP_HOST = re.compile(r"^(?:[^@/\s]+@)?([^:/\s]+):")

_MAX_DEPTH = 4
_MAX_VALUES = 200
_MAX_HITS = 5


def _core():
    from clawmetry import detectors as _d
    return _d


def _key_words(key) -> set:
    try:
        return {w.lower() for w in _KEY_SPLIT.split(str(key)) if w}
    except Exception:
        return set()


def _host_of(rest: str) -> str:
    m = _URL_HOST.match(rest)
    if m:
        return m.group(1).lower()
    m = _SCP_HOST.match(rest)
    return m.group(1).lower() if m else ""


def classify_spec(value, version_key: bool = False) -> Optional[dict]:
    """What package source a spec names, or ``None`` when it is a version.

    Returns ``{"source": kind, "where": str, "local_path": str}``. ``kind`` is
    ``local`` (``file:``/``link:``/``portal:`` or a bare path), ``git``,
    ``alias`` (``npm:other-package``) or ``url``. ``where`` is safe to show:
    a path, or a host, never credentials. Never raises.
    """
    try:
        if not isinstance(value, str):
            return None
        v = value.strip()
        if not v or len(v) > 2048:
            return None
        m = _NAME_AT.match(v)
        if m:
            v = m.group(2).strip()
        low = v.lower()
        for scheme in _LOCAL_SCHEMES:
            if low.startswith(scheme):
                path = v[len(scheme):]
                if path.startswith("//"):
                    path = path[2:]
                return {"source": "local", "where": path[:200], "local_path": path}
        if low.startswith(_GIT_SCHEMES):
            host = _HOSTED_GIT.get(low.split(":", 1)[0]) or _host_of(v)
            return {"source": "git", "where": host or "git remote", "local_path": ""}
        if low.startswith("npm:"):
            target = v[4:].strip()
            name = target.rsplit("@", 1)[0] if target.count("@") > (1 if target.startswith("@") else 0) else target
            return {"source": "alias", "where": name[:120] or "another package", "local_path": ""}
        if low.startswith(("http://", "https://")):
            return {"source": "url", "where": _host_of(v) or "a URL", "local_path": ""}
        if v.startswith(("/", "./", "../", "~/", "~\\", ".\\", "..\\")) or _WIN_ABS.match(v):
            return {"source": "local", "where": v[:200], "local_path": v}
        if version_key and _GH_SHORTHAND.match(v):
            return {"source": "git", "where": "github.com", "local_path": ""}
    except Exception:
        return None
    return None


def _is_temp(path: str) -> bool:
    p = path.replace("\\", "/")
    if not p.endswith("/"):
        p += "/"
    low = p.lower()
    if low.startswith(_TEMP_DIRS):
        return True
    # %TEMP% on Windows: C:\Users\x\AppData\Local\Temp and C:\Windows\Temp.
    return "/appdata/local/temp/" in low or low[1:].startswith(":/windows/temp/")


def _severity(hit: dict, cwd: str) -> tuple:
    """(severity, why) for one classified source."""
    if hit["source"] != "local":
        return "warning", None
    path = hit.get("local_path") or ""
    if _is_temp(path):
        return "critical", "a temporary directory"
    is_abs = path.startswith(("/", "~")) or bool(_WIN_ABS.match(path))
    if is_abs and cwd:
        try:
            full = os.path.normpath(os.path.expanduser(path))
            root = os.path.normpath(os.path.expanduser(cwd))
            if not (full == root or full.startswith(root.rstrip(os.sep) + os.sep)):
                return "critical", "a path outside the working directory"
        except Exception:
            return "warning", None
    return "warning", None


def _walk(args, key_words: set, depth: int, out: list, budget: list) -> None:
    """Collect ``(key, value, version_key)`` for string values under spec keys."""
    if depth > _MAX_DEPTH or budget[0] <= 0:
        return
    if isinstance(args, dict):
        for k, v in args.items():
            words = _key_words(k)
            _walk(v, words if words & _SPEC_KEY_WORDS else key_words, depth + 1, out, budget)
    elif isinstance(args, (list, tuple)):
        for v in list(args)[:50]:
            _walk(v, key_words, depth + 1, out, budget)
    elif isinstance(args, str):
        budget[0] -= 1
        if key_words & _SPEC_KEY_WORDS:
            out.append((sorted(key_words & _SPEC_KEY_WORDS)[0], args,
                        bool(key_words & _VERSION_KEY_WORDS)))


def _spec_values(args) -> list:
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except Exception:
            return []
    out: list = []
    _walk(args, set(), 0, out, [_MAX_VALUES])
    return out


_SOURCE_WORDS = {
    "local": "a local path",
    "git": "a git remote",
    "alias": "a different registry package",
    "url": "a URL",
}


def untrusted_package_source(events: Iterable[dict], session_id: str,
                             runtime: Optional[str] = None, *,
                             thresholds: Optional[dict] = None,
                             steps: Optional[list] = None,
                             facts: Optional[dict] = None) -> Optional[dict]:
    """Flag a tool argument that names a package source where a version goes.
    See the module docstring for severities. Never raises."""
    try:
        d = _core()
        runtime, _th, steps = d._prepare(events, steps, thresholds, runtime, session_id)
        evlist = d._chronological(events)
        cwd = str((facts or {}).get("cwd") or "").strip()
        hits: list = []
        first = None
        worst = "warning"
        seen = set()
        for s in steps:
            if s.get("kind") != "tool_call":
                continue
            i = s.get("i")
            if not isinstance(i, int) or not 0 <= i < len(evlist) or i in seen:
                continue
            seen.add(i)
            ev = evlist[i] or {}
            et = str(ev.get("event_type") or "").strip().lower()
            data = d._coerce_dict(ev.get("data"))
            for call in d._iter_tool_calls_from_data(et, data):
                for key, value, version_key in _spec_values(call.get("args")):
                    c = classify_spec(value, version_key)
                    if not c:
                        continue
                    sev, why = _severity(c, cwd)
                    hit = {"tool": str(call.get("tool") or "")[:120], "arg": key,
                           "source": c["source"], "where": c["where"]}
                    if why:
                        hit["why"] = why
                    if sev == "critical" and worst != "critical":
                        worst = "critical"
                        first = (i, hit)
                    elif first is None:
                        first = (i, hit)
                    if len(hits) < _MAX_HITS:
                        hits.append(hit)
        if not first:
            return None
        idx, lead = first
        what = _SOURCE_WORDS.get(lead["source"], "a package source")
        where = f" ({lead['where']})" if lead.get("where") else ""
        if worst == "critical":
            title = f"A tool was asked to install a package from {lead['why']}"
            detail = (f"`{lead['tool']}` got a `{lead['arg']}` argument that names "
                      f"{what}{where} instead of a version. A tool that installs it "
                      "runs that code in its own process, with no prompt, which is "
                      "how CVE-2026-59176 worked. Check what is at that path and "
                      "why the agent chose it.")
        else:
            title = f"A tool was asked to install a package from {what}"
            detail = (f"`{lead['tool']}` got a `{lead['arg']}` argument that names "
                      f"{what}{where} instead of a version. That is sometimes "
                      "deliberate (an internal package pinned to git or a path), and "
                      "it is also how an argument can make a tool install and run "
                      "code nobody chose. Worth confirming it is the source you "
                      "expect.")
        return d._incident(
            "untrusted_package_source", session_id, runtime, worst, title, detail,
            {"hits": hits, "count": len(hits),
             "sources": sorted({h["source"] for h in hits}),
             "tools": sorted({h["tool"] for h in hits}),
             "observed": "tool_arguments"},
            idx)
    except Exception:
        return None
