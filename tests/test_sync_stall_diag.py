"""Regression for #5932: when the daemon reports ``daemon_ingest_stalled`` it
must also write a full thread-stack dump to ``~/.clawmetry/daemon_stall_diag.txt``
so Windows+py3.13 hangs are diagnosable from a support case.

``clawmetry/sync.py`` cannot be imported in fast-CI (it needs DuckDB,
cryptography, ...), so this test uses ``ast`` to verify the dump is wired into
``_report_if_ingest_stalled`` -- the same approach used by
``test_sync_cycle_fault_isolation.py``.

Four things are asserted:
1. The dump is written inside a *nested* try block that fires after
   ``report_daemon_failure`` (so a write failure never kills the watchdog).
2. The nested try captures all thread stacks via ``sys._current_frames()`` and
   ``format_stack``.
3. The output includes ``--- Thread`` markers so threads are identifiable.
4. The outer ``except Exception`` on the whole function body is still present,
   keeping the heartbeat thread alive regardless of what the dump code does.
"""
from __future__ import annotations

import ast
import os

SYNC_PATH = os.path.join(
    os.path.dirname(__file__), "..", "clawmetry", "sync.py"
)


def _parse() -> ast.Module:
    with open(SYNC_PATH, encoding="utf-8") as f:
        return ast.parse(f.read(), filename=SYNC_PATH)


def _find_stall_func(tree: ast.Module) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "_report_if_ingest_stalled"
        ):
            return node
    raise AssertionError(
        "clawmetry/sync.py must define _report_if_ingest_stalled()"
    )


def _has_except_exception(node: ast.AST) -> bool:
    """True if ``node`` has an ``except Exception`` (or bare ``except``) handler."""
    for n in ast.walk(node):
        if not isinstance(n, ast.ExceptHandler):
            continue
        if n.type is None:
            return True
        if isinstance(n.type, ast.Name) and n.type.id == "Exception":
            return True
    return False


def _source_strings(node: ast.AST) -> list:
    """All string constants in the AST subtree."""
    return [
        n.value
        for n in ast.walk(node)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    ]


def _calls_named(node: ast.AST, name: str) -> bool:
    """True if there is a function call whose callee ends with ``name``."""
    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Name) and f.id == name:
            return True
        if isinstance(f, ast.Attribute) and f.attr == name:
            return True
    return False


def _outer_try(func: ast.FunctionDef) -> ast.Try:
    """The single outer ``try`` block that is the direct body of the function."""
    tries = [s for s in func.body if isinstance(s, ast.Try)]
    assert tries, "_report_if_ingest_stalled must have an outer try block"
    return tries[0]


def _find_nested_diag_try(outer: ast.Try) -> ast.Try:
    """A nested try block inside the outer try that writes daemon_stall_diag.txt."""
    for node in ast.walk(outer):
        if not isinstance(node, ast.Try):
            continue
        if node is outer:
            continue
        strs = _source_strings(node)
        if any("daemon_stall_diag.txt" in s for s in strs):
            return node
    raise AssertionError(
        "_report_if_ingest_stalled must contain a nested try block that "
        "references daemon_stall_diag.txt"
    )


# -- tests --------------------------------------------------------------------


def test_stall_diag_nested_try_exists() -> None:
    tree = _parse()
    func = _find_stall_func(tree)
    outer = _outer_try(func)
    # raises if not found
    _find_nested_diag_try(outer)


def test_stall_diag_captures_all_threads() -> None:
    tree = _parse()
    func = _find_stall_func(tree)
    outer = _outer_try(func)
    nested = _find_nested_diag_try(outer)
    assert _calls_named(nested, "_current_frames"), (
        "The diagnostic try block must call sys._current_frames() to capture "
        "all running threads"
    )
    assert _calls_named(nested, "format_stack"), (
        "The diagnostic try block must call traceback.format_stack() to render "
        "the captured frames"
    )


def test_stall_diag_includes_thread_markers() -> None:
    tree = _parse()
    func = _find_stall_func(tree)
    outer = _outer_try(func)
    nested = _find_nested_diag_try(outer)
    strs = _source_strings(nested)
    assert any("--- Thread" in s for s in strs), (
        "The diagnostic dump must include '--- Thread' separators so individual "
        "threads are identifiable in the output file"
    )


def test_stall_diag_write_path_is_clawmetry_dir() -> None:
    tree = _parse()
    func = _find_stall_func(tree)
    outer = _outer_try(func)
    nested = _find_nested_diag_try(outer)
    strs = _source_strings(nested)
    assert any(".clawmetry" in s for s in strs), (
        "The diagnostic file must be written under ~/.clawmetry/ "
        "(found no such path literal in the nested try block)"
    )


def test_stall_func_outer_except_exception_survives() -> None:
    """The whole body of _report_if_ingest_stalled must be wrapped in
    ``except Exception`` so a crash in the dump code never kills the watchdog
    heartbeat thread."""
    tree = _parse()
    func = _find_stall_func(tree)
    outer = _outer_try(func)
    assert _has_except_exception(outer), (
        "_report_if_ingest_stalled must have an outer `except Exception` "
        "handler so the heartbeat thread survives any failure in the watchdog"
    )
