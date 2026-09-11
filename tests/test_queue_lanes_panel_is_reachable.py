"""The Queue Lanes rollup must actually be reached, and must never spin.

`/api/run-ledger` has been served, tested and shipped in every wheel since
#2100. PR #5668 then cut the unreachable "Sub-Agents & Queue Lanes" tab, and
took the endpoint's only UI consumer with it: measured on `origin/main` before
this panel landed, `grep -c run-ledger` over `app.js` and every shipped tab
template returned **0**. Issue #5721 is that gap.

`tests/test_every_tab_is_reachable.py` covers *tabs*: a template with no
`switchTab` caller. A panel inside an existing tab needs its own check, because
nothing about it is a tab: it is a `<div id=...>` that only exists on screen if
some function writes to it, and only runs if some other function calls that.
Both halves of that chain are asserted here.

The second half of the guard is the honest empty state. `/api/run-ledger`
deliberately never raises: a fresh sync, an OpenClaw predating the run ledger,
or a daemon mid-restart all return `{"lanes": [], "runs": []}`. A panel that
renders "Loading..." over that lies forever, which is exactly what got the old
tab hidden in 44acaa72f ("perpetually stuck on Loading... with no useful
content") and what put six dead panels on the cloud Security tab. So the empty
branch must say it is finished and name why it is empty.

Static checks over the shipped assets. No server, no store, no browser.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
APP_JS = (REPO / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
CRONS_HTML = (
    REPO / "clawmetry" / "templates" / "tabs" / "crons.html"
).read_text(encoding="utf-8")
SCHEDULER_PY = (REPO / "routes" / "scheduler.py").read_text(encoding="utf-8")

PANEL_ID = "cron-queue-lanes"


def _render_body() -> str:
    """`renderQueueLanes`'s body, as shipped, with `//` comments stripped.

    The comments explain what the empty state must not say, and quote the copy
    it must not use. Matching raw text would fail on the explanation rather
    than on the code: assert on what runs, not on the prose describing it.
    """
    i = APP_JS.index("function renderQueueLanes(")
    j = APP_JS.index("\nasync function loadQueueLanes(", i)
    return "\n".join(
        ln for ln in APP_JS[i:j].splitlines() if not ln.lstrip().startswith("//")
    )


def test_the_panel_container_exists_in_the_crons_tab():
    assert f'id="{PANEL_ID}"' in CRONS_HTML, (
        f"no #{PANEL_ID} container in the Crons tab, so nothing the renderer "
        "writes can ever appear on screen"
    )


def test_something_writes_to_the_panel():
    assert f"getElementById('{PANEL_ID}')" in APP_JS, (
        f"#{PANEL_ID} is in the template but no JS looks it up: an empty div "
        "that ships in every wheel"
    )


def test_the_loader_is_actually_called():
    """A loader nobody calls is the #5668 shape all over again."""
    callers = [
        ln.strip()
        for ln in APP_JS.splitlines()
        if "loadQueueLanes()" in ln
        and not ln.strip().startswith("async function")
        and not ln.strip().startswith("//")
    ]
    # The Retry button inside the error branch calls itself; that is not a
    # caller for reachability purposes.
    real = [ln for ln in callers if "onclick=" not in ln]
    assert real, (
        "loadQueueLanes() is defined and never called from a tab loader, so "
        "the panel renders on no code path"
    )


def test_the_loader_reaches_the_endpoint_that_had_no_consumer():
    assert "/api/run-ledger" in APP_JS, (
        "the panel does not read /api/run-ledger, which is the endpoint #5721 "
        "exists to give a home to"
    )


def test_cloud_reads_the_snapshot_slice_not_the_endpoint():
    """On the hosted server /api/run-ledger is an oss-passthrough with no local
    DuckDB behind it, so it honestly returns empty lists. Fetching it in
    CLOUD_MODE would paint the empty state over a node that has runs: the
    false-empty-tab bug class, again."""
    i = APP_JS.index("async function loadQueueLanes(")
    body = APP_JS[i:i + 2000]
    assert "CLOUD_MODE" in body and "runLedger" in body, (
        "loadQueueLanes has no CLOUD_MODE branch reading the `runLedger` "
        "snapshot slice, so the hosted panel would always look empty"
    )


def test_the_empty_state_says_it_is_finished_and_why():
    body = _render_body()
    i = body.index("if (!lanes.length)")
    j = body.index("return html", i)
    empty = body[i:j]

    assert "Loading" not in empty, (
        "the empty branch says 'Loading', the exact copy that got the old "
        "Queue Lanes tab hidden in 44acaa72f"
    )
    # Both causes named, so a reader can tell "your OpenClaw is too old" from
    # "nothing has run yet" without opening a shell.
    assert "openclaw.sqlite" in empty, "empty state does not name the ledger it read"
    assert "2026" in empty, "empty state does not name an OpenClaw version floor"
    assert re.search(r"not a spinner|finished state", empty), (
        "empty state does not tell the reader it has stopped working"
    )


def test_a_failed_load_is_not_reported_as_an_empty_ledger():
    """The catch branch must say the fetch failed. Falling through to
    renderQueueLanes([]) would claim the node has no background runs because
    the request timed out."""
    i = APP_JS.index("async function loadQueueLanes(")
    j = APP_JS.index("\nasync function loadCronHealth(", i)
    catch = APP_JS[APP_JS.index("} catch (e) {", i):j]
    assert "Failed to load queue lanes" in catch
    assert "renderQueueLanes" not in catch, (
        "the error path renders the lanes view, so a failed fetch is "
        "indistinguishable from an empty ledger"
    )


def test_the_route_docstring_does_not_pin_the_superseded_ledger_path():
    """OpenClaw 2026.6.5+ moved `task_runs` into the unified
    `state/openclaw.sqlite`; `sync._openclaw_task_ledger_paths()` reads both.
    A docstring naming only `tasks/runs.sqlite` sent this investigation to a
    directory that does not exist on a current install."""
    head = SCHEDULER_PY[:SCHEDULER_PY.index('"""', 3) + 3]
    assert "state/openclaw.sqlite" in head, (
        "routes/scheduler.py still documents only the 2026.5.x ledger path"
    )
