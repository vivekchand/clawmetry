"""Which git config settings make git execute a program.

One list, in a leaf, because two modules ask the same question and a copy in
each is a copy that drifts. Neither format overlaps the other: literal exec
keys (``core.hookspath``) and value-dependent ones (``alias.*``) are resolved
by the same predicate so both callers rate identically.

* :mod:`clawmetry.repo_scan` asks it of a ``.git/config`` on disk -- that is
  the whole basis of the ``repo_config_exec`` finding;
* :mod:`clawmetry.tool_risk` asks it of ``git -c <key>=<value>`` on a command
  line, which is the same arbitrary code execution passed a different way.

They disagreed: the scanner rated a poisoned ``core.hooksPath`` critical while
the classifier rated the identical key on the command line ``medium``, and a
``min_risk: high`` policy therefore held neither (clawmetry-pro#244).

This module imports only ``re``. It exists so ``tool_risk`` can share the
knowledge without importing ``repo_scan``: ``tool_risk`` is the leaf that
``approvals`` and the routes import, and it stays one by depending on this
constant module rather than on a scanner.

It is a PREDICATE, not a name set. Executability is partly value-dependent --
``alias.x`` is a shell command only when its value starts with ``!`` -- so a
name-only export would either miss that or promote every benign alias.

NOT here, deliberately: ``protocol.ext.allow``. It names no program; it enables
the ``ext::`` transport so the command arrives in the remote URL instead. A
caller that can see a whole command line handles it separately.
"""
from __future__ import annotations

import re

#: Git config keys whose VALUE is a program git runs.
_EXEC_KEYS = (
    "core.fsmonitor",
    "core.hookspath",
    "core.sshcommand",
    "core.editor",
    "core.pager",
    "core.askpass",
    "sequence.editor",
    "credential.helper",
    "uploadpack.packobjectshook",
    "diff.external",
    "gpg.program",
    "init.templatedir",
)

#: Key shapes whose value is a program. ``alias.*`` is value-dependent.
_EXEC_KEY_PATTERNS = (
    re.compile(r"^filter\..+\.(clean|smudge|process)$"),
    re.compile(r"^diff\..+\.(command|textconv)$"),
    re.compile(r"^merge\..+\.driver$"),
    re.compile(r"^alias\..+$"),          # only flagged when the value starts "!"
)

#: Values that are ordinary tools rather than payloads.
_KNOWN_GOOD_PREFIXES = (
    ("git-lfs", "clean"), ("git-lfs", "smudge"), ("git-lfs", "filter-process"),
    ("git", "lfs"),
    ("cat",), ("true",), ("false",),
    ("rustfmt",), ("gofmt",), ("black",), ("prettier",),
    ("less",), ("more",), ("delta",), ("diff-so-fancy",),
)

#: A value that chains, substitutes or redirects is never known-good, whatever
#: it starts with -- ``git-lfs clean -- %f; curl attacker`` starts with git-lfs.
#: Covers: sequence (;, &&, ||, &), pipe (|), substitution ($, `), redirect
#: (>, <), comment injection (#), history expansion (!), subshell/brace grouping
#: ( ) { }, and CR (\r) which some shells treat as a command separator.
_SHELL_METACHARS = re.compile(r"[;&|`$><\n\r!#(){}]")


def executes(full_key: str, value: str = "") -> bool:
    """Does setting ``full_key`` to ``value`` make git run a program?

    ``value`` defaults to empty for callers that see the key but not the value
    (``git --config-env=k=ENVVAR`` names an environment variable). That is
    conservative on purpose: literal exec keys still match, value-dependent
    ones do not fire on a value we cannot see.
    """
    key = str(full_key or "").strip().lower()
    val = str(value or "")
    if key in _EXEC_KEYS:
        return True
    for rx in _EXEC_KEY_PATTERNS:
        if rx.match(key):
            if key.startswith("alias."):
                return val.strip().startswith("!")
            return True
    return False


def value_known_good(value: str) -> bool:
    """Is this value a recognised ordinary tool rather than a payload?

    ``core.pager=less`` executes by definition and is an entirely ordinary
    thing to type, so a classifier that promotes on the key alone reports
    noise on a common command.
    """
    if _SHELL_METACHARS.search(value or ""):
        return False
    tokens = str(value or "").split()
    # An empty value sets the key to nothing, which runs nothing. Matches
    # repo_scan's long-standing behaviour exactly -- this module was extracted
    # from it, and a semantic change here would silently move every
    # repo_config_exec verdict.
    if not tokens:
        return True
    lowered = [t.lower() for t in tokens]
    for prefix in _KNOWN_GOOD_PREFIXES:
        if lowered[:len(prefix)] == list(prefix):
            return True
    return False
