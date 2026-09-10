"""Regression for field-failures #5800 / #5801 (``daemon_ingest_stalled`` on
Darwin py3.14 and Linux py3.12).

``run_daemon``'s steady-state ``while True:`` cycle wraps almost every ingest
call in its own ``try/except`` so one bad data source cannot take down the
rest -- see the many "non-fatal" log lines throughout the loop in
``clawmetry/sync.py``. Six calls (memory, the two session syncs, the
subagent/flow snapshot, session metadata, crons) were the exception: they ran
bare. A persistent exception in any one of them -- e.g. one session file that
parses the same wrong way on every retry -- aborted the WHOLE cycle before it
ever reached ``state["last_sync"] = ...``, and because ``state = load_state()``
re-reads the same broken input at the top of the next cycle too, that single
bad source froze ``last_sync`` forever. The daemon process stays up and the
separate lock-heartbeat thread (``_start_lock_heartbeat`` /
``_report_if_ingest_stalled``) keeps touching its heartbeat file the whole
time, so nothing looks dead -- until ``field_report.last_sync_age_secs()``
crosses ``CLAWMETRY_STALLED_INGEST_SECS`` (1h) and the daemon reports itself
as ``daemon_ingest_stalled``, which is exactly the two field failures this
pins.

This test parses ``clawmetry/sync.py`` with ``ast`` rather than importing it,
so it needs no daemon dependencies (DuckDB, cryptography, ...) and runs in the
fast syntax/lint job.
"""
from __future__ import annotations

import ast
import os

SYNC_PATH = os.path.join(
    os.path.dirname(__file__), "..", "clawmetry", "sync.py"
)

# The six calls that used to run outside any try/except in the steady-state
# loop. A persistent exception in any one of them must not stop the others,
# and must not stop `state["last_sync"]` from advancing.
TARGET_CALLS = frozenset({
    "sync_memory",
    "sync_sessions",
    "sync_claude_cli_sessions",
    "sync_system_snapshot",
    "sync_session_metadata",
    "sync_crons",
})


def _parse_sync_module() -> ast.Module:
    with open(SYNC_PATH, encoding="utf-8") as f:
        return ast.parse(f.read(), filename=SYNC_PATH)


def _find_run_daemon(tree: ast.Module) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run_daemon":
            return node
    raise AssertionError("clawmetry/sync.py must define run_daemon()")


def _subscript_key(slice_node):
    """The literal key of a ``foo[key]`` subscript, across ast.Index-era and
    modern (3.9+) subscript shapes."""
    node = slice_node
    if hasattr(ast, "Index") and isinstance(node, ast.Index):  # pragma: no cover
        node = node.value
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _sets_last_sync(node: ast.AST) -> bool:
    """True if ``node`` (or something inside it) assigns ``state["last_sync"]``."""
    for n in ast.walk(node):
        if not isinstance(n, ast.Assign):
            continue
        for target in n.targets:
            if (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == "state"
                and _subscript_key(target.slice) == "last_sync"
            ):
                return True
    return False


def _find_steady_state_loop(run_daemon: ast.FunctionDef) -> ast.While:
    """The infinite ``while True:`` cycle body that must reach
    ``state["last_sync"] = ...`` on every iteration that doesn't hard-crash."""
    candidates = [
        n for n in ast.walk(run_daemon)
        if isinstance(n, ast.While)
        and isinstance(n.test, ast.Constant)
        and n.test.value is True
    ]
    assert candidates, (
        "run_daemon() must contain a `while True:` steady-state sync cycle"
    )
    steady_state = [n for n in candidates if _sets_last_sync(n)]
    assert steady_state, (
        "Could not find the `while True:` loop that sets "
        "state['last_sync'] inside run_daemon() -- this test's structural "
        "assumptions about the sync cycle may be stale."
    )
    # There should be exactly one; if a refactor introduces more, checking
    # all of them is still correct (each must isolate its ingest calls).
    return steady_state[0]


def _find_cycle_try(loop: ast.While) -> ast.Try:
    """The single big ``try: ... except Exception: log "Sync cycle error"``
    that wraps the ENTIRE cycle body -- the outermost safety net that keeps
    the daemon process itself alive across a bad cycle. It must not be
    confused with an inner, per-call try/except: everything in this loop is
    "inside" the outer try, so checking against it alone would always read
    as guarded. What matters is whether a call has its OWN (nested) try
    between it and this outer one.
    """
    tries = [s for s in loop.body if isinstance(s, ast.Try)]
    assert len(tries) == 1, (
        "Expected exactly one top-level try/except wrapping the whole "
        f"steady-state cycle body, found {len(tries)}"
    )
    return tries[0]


def _unguarded_target_calls(loop: ast.While) -> set:
    """Names from TARGET_CALLS that are reachable inside the cycle's outer
    try body WITHOUT passing through a NESTED try first -- i.e. a raise
    there would propagate all the way out to the outer "Sync cycle error"
    handler, abandoning every ingest step still to come in that cycle
    (including `state["last_sync"] = ...`), instead of being logged and
    skipped so the cycle still completes.
    """
    outer_try = _find_cycle_try(loop)
    unguarded: set = set()

    def walk(node: ast.AST, under_try: bool) -> None:
        # A node can itself BE a (nested) Try -- e.g. when a top-level
        # statement of the outer try's body is `try: mem = sync_memory(...)
        # except: ...`. Check the node itself, not only its children, or
        # that whole nested try is missed and everything inside it is
        # judged by the (stale) flag its caller passed in.
        under_try = under_try or isinstance(node, ast.Try)
        for child in ast.iter_child_nodes(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id in TARGET_CALLS
                and not under_try
            ):
                unguarded.add(child.func.id)
            walk(child, under_try)

    # Walk each top-level statement of the OUTER try's body starting fresh
    # (under_try=False) -- entering the outer try itself must not count as
    # protection, or every call in the cycle would trivially look "guarded".
    for stmt in outer_try.body:
        walk(stmt, False)
    return unguarded


def test_steady_state_cycle_isolates_every_ingest_call():
    tree = _parse_sync_module()
    run_daemon = _find_run_daemon(tree)
    loop = _find_steady_state_loop(run_daemon)

    unguarded = _unguarded_target_calls(loop)
    assert not unguarded, (
        "run_daemon()'s steady-state while-loop calls "
        f"{sorted(unguarded)} without wrapping each in its own try/except, "
        "like every other ingest call in that loop already does. An "
        "exception there aborts the ENTIRE sync cycle before reaching "
        "`state[\"last_sync\"] = ...`, and since the next cycle reloads the "
        "same on-disk state, a persistent failure in just one of these "
        "freezes last_sync forever -- the daemon_ingest_stalled field "
        "failure (#5800, #5801), reported by a separate heartbeat thread "
        "that has no idea the main cycle stopped completing."
    )


def test_target_calls_are_still_present_in_the_loop():
    """Sanity check that the six calls this test protects still exist in the
    loop under their expected names -- guards against the regression test
    silently checking nothing after a rename/refactor."""
    tree = _parse_sync_module()
    run_daemon = _find_run_daemon(tree)
    loop = _find_steady_state_loop(run_daemon)

    found = {
        node.func.id
        for node in ast.walk(loop)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in TARGET_CALLS
    }
    assert found == TARGET_CALLS, (
        f"Expected all of {sorted(TARGET_CALLS)} in the steady-state loop, "
        f"found {sorted(found)}. Update TARGET_CALLS if these were "
        "intentionally renamed or removed."
    )
