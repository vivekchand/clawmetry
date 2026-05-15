#!/usr/bin/env python3
"""Lint: every daemon-proxy method call must be in the allowlist.

Closes the process gap that produced PRs #1258 → #1260 → #1266 (issue #1267).
PR #1258 added `local_store_via_daemon("query_alert_rules", ...)` calls but
forgot to register `query_alert_rules` in `routes/local_query.py:_DAEMON_METHODS`.
The daemon returned 400 "method not allowed" for every call, the dashboard
fast-paths returned None, and the handler fell through to the slow legacy
path — surfacing as a 7s `/api/alerts/rules` cliff that #1260 had to fix.

This lint catches the pattern at PR-time:
  1. Walks routes/*.py for `local_store_via_daemon("X", ...)`
     and `_ls_call("X", ...)` (the per-blueprint wrapper).
  2. Reads `_DAEMON_METHODS` from routes/local_query.py via AST.
  3. Asserts every captured method name is in the allowlist.

Run via `make lint` or `python3 scripts/lint_daemon_allowlist.py`.
Exits 0 on clean, 1 with a precise diff on any miss.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parent.parent
ALLOWLIST_FILE = ROOT / "routes" / "local_query.py"
ROUTES_DIR = ROOT / "routes"

# Match `local_store_via_daemon("name", ...)` and `_ls_call("name", ...)`.
# We only care about the first string-literal argument. Single + double quotes.
CALL_RE = re.compile(
    r'\b(?:local_store_via_daemon|_ls_call)\(\s*["\']([^"\']+)["\']'
)


def read_allowlist() -> set[str]:
    """Parse `_DAEMON_METHODS = frozenset({...})` from routes/local_query.py.

    Uses AST (not regex) so changes to formatting / inline comments don't
    break the lint.
    """
    src = ALLOWLIST_FILE.read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "_DAEMON_METHODS"):
            continue
        # Expect `frozenset({"a", "b", ...})`.
        if not isinstance(node.value, ast.Call):
            continue
        if not (isinstance(node.value.func, ast.Name)
                and node.value.func.id == "frozenset"):
            continue
        if not node.value.args:
            continue
        arg = node.value.args[0]
        if not isinstance(arg, ast.Set):
            continue
        return {
            elt.value for elt in arg.elts
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        }
    raise RuntimeError(
        f"could not find `_DAEMON_METHODS = frozenset(...)` in {ALLOWLIST_FILE}"
    )


def find_callers() -> dict[str, list[tuple[str, int]]]:
    """Return {method_name: [(file, line), ...]} for every daemon-proxy call.

    Filters captures to those starting with `query_` so we don't pick up
    `event_type="message"` / `agent_id="..."` keyword args that happen to
    sit inside the call.
    """
    out: dict[str, list[tuple[str, int]]] = {}
    for path in sorted(ROUTES_DIR.glob("*.py")):
        if path.name == "local_query.py":
            # The allowlist file itself is not a caller; skip.
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            for m in CALL_RE.finditer(line):
                method = m.group(1)
                if not method.startswith("query_"):
                    continue
                out.setdefault(method, []).append((str(path.relative_to(ROOT)), lineno))
    return out


def main() -> int:
    allowed = read_allowlist()
    callers = find_callers()
    missing = {m: sites for m, sites in callers.items() if m not in allowed}

    if not missing:
        print(
            f"daemon-allowlist OK — {len(callers)} distinct query_* method"
            f"{'s' if len(callers) != 1 else ''} called from routes/, "
            f"all in _DAEMON_METHODS ({len(allowed)} entries)"
        )
        return 0

    print("daemon-allowlist FAIL — call sites use methods missing from "
          "_DAEMON_METHODS:\n", file=sys.stderr)
    for method in sorted(missing):
        print(f"  {method!r} called at:", file=sys.stderr)
        for path, line in missing[method]:
            print(f"    {path}:{line}", file=sys.stderr)
    print(file=sys.stderr)
    print(
        "Add the missing method(s) to _DAEMON_METHODS in routes/local_query.py.\n"
        "If a method name should NOT route through the daemon proxy, refactor\n"
        "the call site to use `local_store.get_store(read_only=True)` directly\n"
        "with a documented single-process-only justification.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
