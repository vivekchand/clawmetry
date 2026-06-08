"""CPU-budget guard for the OTLP/OpenLLMetry app rollup (FLYWHEEL 1e).

The distinct-agent_type spans scan that surfaces foreign OTLP apps in the
runtime switcher + Agent Inventory MUST run on the daemon's snapshot/rollup
timer (inside ``sync._build_runtime_summary`` -> ``_merge_otlp_apps_into_summary``)
and NEVER inside an HTTP request handler. A per-request GROUP BY over the spans
table would re-scan on every poll and blow the <=5-10% one-core budget.

This is a STRUCTURAL guard (not a perf measurement): it asserts the only
invocation of ``LocalStore.query_otlp_app_rollup`` in the package source lives
in ``clawmetry/sync.py`` (the cached rollup builder), and that no module under
``routes/`` invokes it. ``routes/local_query.py`` may name it in the
``_DAEMON_METHODS`` allowlist (a string, not a call) so the local Inventory route
can read the already-built rollup through the daemon proxy.
"""

from __future__ import annotations

import ast
import os

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _call_sites(path: str) -> list[int]:
    """Return line numbers where ``query_otlp_app_rollup`` is CALLED (an
    ``ast.Call`` whose func is an attribute access ``something.query_otlp_app_rollup``),
    ignoring it appearing only as a bare string literal (the allowlist)."""
    with open(path, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    hits: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr == "query_otlp_app_rollup":
                hits.append(node.lineno)
    return hits


def test_otlp_rollup_called_only_in_sync_not_in_handlers():
    sync_path = os.path.join(_REPO, "clawmetry", "sync.py")
    assert _call_sites(sync_path), (
        "expected sync.py to invoke query_otlp_app_rollup in the rollup builder")

    routes_dir = os.path.join(_REPO, "routes")
    offenders = {}
    for name in os.listdir(routes_dir):
        if not name.endswith(".py"):
            continue
        path = os.path.join(routes_dir, name)
        sites = _call_sites(path)
        if sites:
            offenders[name] = sites
    assert not offenders, (
        "query_otlp_app_rollup must NOT be CALLED from any HTTP handler "
        f"(per-request full scan banned by FLYWHEEL 1e). Offenders: {offenders}")


def test_otlp_rollup_lives_in_cached_rollup_builder():
    """The call site is inside ``_merge_otlp_apps_into_summary``, which is only
    reached from ``_build_runtime_summary`` (the daemon's cached rollup path),
    not a request handler."""
    sync_path = os.path.join(_REPO, "clawmetry", "sync.py")
    with open(sync_path, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=sync_path)

    enclosing = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Call)
                        and isinstance(inner.func, ast.Attribute)
                        and inner.func.attr == "query_otlp_app_rollup"):
                    enclosing = node.name
                    break
    assert enclosing == "_merge_otlp_apps_into_summary", (
        f"expected the call inside _merge_otlp_apps_into_summary, got {enclosing}")
