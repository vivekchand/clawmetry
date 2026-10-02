"""The Sessions row controls reach a function that takes their arguments.

`app.js` is one classic script, so two top-level `function guardControl`
declarations do not coexist: the later one replaces the earlier one for every
caller. That is what happened to the per-row Pause / Resume / Stop buttons.
The row handler called `guardControl(sid, action, runtime, cwd)`; the Guard
tab later added `guardControl(sessionId, runtime, cwd, action)`. From then on
a row click sent the action as the runtime and the working directory as the
action, the server refused it, and no control ever reached the agent.

Nothing failed loudly, so this pins three things:

1. No top-level function name is declared twice with different parameters.
2. The row handler calls a function declared with the order it passes.
3. The Guard tab buttons still pass the order `guardControl` declares.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

APP_JS = (Path(__file__).resolve().parents[1]
          / "clawmetry" / "static" / "js" / "app.js")

_DECL = re.compile(r"^(?:async )?function ([A-Za-z_$][\w$]*)\(([^)]*)\)", re.M)


def _declarations() -> dict:
    found = defaultdict(list)
    for name, params in _DECL.findall(APP_JS.read_text()):
        found[name].append([p.strip() for p in params.split(",") if p.strip()])
    return found


def test_no_top_level_function_is_redeclared_with_other_parameters():
    clashes = {
        name: sigs for name, sigs in _declarations().items()
        if len(sigs) > 1 and any(s != sigs[0] for s in sigs)
    }
    assert not clashes, (
        "app.js declares these top-level functions more than once with "
        "different parameters; the last declaration silently wins for every "
        "caller: %r" % clashes
    )


def test_row_handler_calls_a_function_with_its_argument_order():
    src = APP_JS.read_text()
    call = re.search(
        r"closest\('\.cm-guard-btn'\);\s*if \(gb\) \{\s*ev\.stopPropagation\(\);"
        r"\s*([A-Za-z_$][\w$]*)\(gb\.dataset\.sid, gb\.dataset\.action, "
        r"gb\.dataset\.rt, gb\.dataset\.cwd\);",
        src,
    )
    assert call, "the delegated .cm-guard-btn handler changed shape"
    sigs = _declarations()[call.group(1)]
    assert sigs == [["sessionId", "action", "runtime", "cwd"]], (
        "%s is called as (sid, action, runtime, cwd) but is declared as %r"
        % (call.group(1), sigs)
    )


def test_guard_tab_buttons_pass_the_order_guard_control_declares():
    src = APP_JS.read_text()
    assert _declarations()["guardControl"] == [
        ["sessionId", "runtime", "cwd", "action"]
    ]
    calls = re.findall(r'onclick="guardControl\(([^)]*)\)"', src)
    assert len(calls) >= 3
    for args in calls:
        assert args.startswith("this.dataset.sid,this.dataset.rt,this.dataset.cwd,"), args
