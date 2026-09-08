"""The Home screen must not fetch data it renders into a hidden element.

`loadMiniWidgets()` runs on every Home render and called `loadSubAgents()`,
which fetched `/api/subagents` — a payload of every sub-agent on the node, 500
records on the machine this was found on — and wrote the result into
``#subagents-count``, ``#subagents-status`` and ``#subagents-preview``.

All three of those ids lived inside `overview.html`'s ``display:none``
"elements referenced by existing JS" block. The entire result was invisible.
One extra round trip per Home load, rendering into nothing.

FLYWHEEL, *performance is a feature — and a cost*: "at $9/node/mo we cannot
make hundreds of API calls per minute... Before adding any poller/fetch, ask:
does this need to run on *every* tab?" This one did not need to run at all.

The pattern is worth guarding rather than just fixing: a fetch whose output
goes to a hidden element is invisible in exactly the way that keeps it alive —
nothing looks broken, so nothing prompts anyone to remove it.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP_JS = (REPO / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
OVERVIEW = (REPO / "clawmetry" / "templates" / "tabs" / "overview.html").read_text(
    encoding="utf-8"
)


def _code(body: str) -> str:
    """Strip // comments — the fix leaves a comment explaining the removed
    fetch, and an assertion that matched comment text would fail on its own
    explanation."""
    return "\n".join(
        ln for ln in body.splitlines() if not ln.lstrip().startswith("//")
    )


def _body(name: str) -> str:
    m = re.search(r"^(?:async )?function %s\(" % re.escape(name), APP_JS, re.M)
    assert m, "function %s() not found" % name
    i = APP_JS.index("{", m.start())
    depth = 0
    for j in range(i, len(APP_JS)):
        if APP_JS[j] == "{":
            depth += 1
        elif APP_JS[j] == "}":
            depth -= 1
            if depth == 0:
                return APP_JS[i:j + 1]
    raise AssertionError("unbalanced braces in %s()" % name)


def test_the_invisible_subagents_widget_is_gone():
    assert "function loadSubAgents" not in APP_JS, (
        "loadSubAgents() fetched /api/subagents on every Home render and wrote "
        "the result into hidden elements"
    )


def test_home_render_does_not_fetch_subagents_into_nothing():
    body = _code(_body("loadMiniWidgets"))
    assert "loadSubAgents" not in body, (
        "loadMiniWidgets runs on every Home render; it must not trigger a "
        "/api/subagents fetch whose output is invisible"
    )
    assert "/api/subagents" not in body, (
        "the Home mini-widgets must not fetch the sub-agent list directly"
    )


def test_the_hidden_targets_are_gone_too():
    """Leaving the elements invites the fetch back."""
    for el in ("subagents-count", "subagents-status", "subagents-preview"):
        assert el not in OVERVIEW, (
            f"#{el} was a hidden render target for a fetch that ran on every "
            f"Home load; leaving it in place invites the fetch back"
        )


def test_only_one_subagents_fetch_remains_on_the_home_path():
    """Home should read the sub-agent list once, for the panel that shows it."""
    overview_tasks = _body("loadOverviewTasks")
    assert "/api/subagents" in overview_tasks, (
        "the Active Tasks panel is the one legitimate consumer on Home"
    )
    mini = _code(_body("loadMiniWidgets"))
    assert "/api/subagents" not in mini
