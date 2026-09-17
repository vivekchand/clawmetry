"""A card that reads local-only data must not ASK for it on the hosted
dashboard (#6060).

``/api/guard/inventory`` is deliberately ``cloud-disabled`` in
clawmetry-cloud's ``cloud_route_policy``: the component inventory is collected
by the daemon on the machine the agents run on, it is not in the encrypted
snapshot, and a passthrough would report "nothing inventoried" for a node that
has an inventory. The route answers 410 Gone, and that is correct.

What was wrong was on this side. The Guard tab's inventory card fetched the
route unconditionally, including on the hosted dashboard. Handling the 410 in
``.then()`` renders the right words but does not stop the BROWSER logging
``Failed to load resource: the server responded with a status of 410`` first,
and the cloud-contract deploy spec counts every console error. Three of its
assertions failed on that one line, production stayed on 0.12.883, and both
0.12.884 and 0.12.885 failed to promote.

Behaviour is pinned in ``test_guard_inventory_hosted_js.js`` against shipped
source. The checks below pin the seams that are not worth running in a VM.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_guard_inventory_hosted_js.js")
_APP_JS = os.path.join(_HERE, "..", "clawmetry", "static", "js", "app.js")
_GUARD_HTML = os.path.join(_HERE, "..", "clawmetry", "templates", "tabs", "guard.html")


def _src() -> str:
    with open(_APP_JS, encoding="utf-8") as fh:
        return fh.read()


def _function(name: str) -> str:
    m = re.search(r"^function " + name + r"\b[\s\S]*?^\}", _src(), re.M)
    assert m, f"{name} not found in app.js"
    return m.group(0)


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_hosted_inventory_card_unit_suite() -> None:
    proc = subprocess.run(["node", _JS_TEST], capture_output=True, text=True, timeout=60)
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "hosted inventory card tests failed:\n" + output
    assert "PASS" in output, "no PASS line in output:\n" + output


def test_the_hosted_branch_returns_before_the_fetch() -> None:
    """The order is the whole fix: a CLOUD_MODE check after the fetch would
    render the same sentence and still leave the console error behind."""
    body = _function("loadGuardInventory")
    guard = body.index("window.CLOUD_MODE")
    call = body.index("fetch('/api/guard/inventory')")
    assert guard < call, "the CLOUD_MODE branch must come before the fetch"
    assert "return;" in body[guard:call], "the CLOUD_MODE branch must return"


def test_the_card_still_renders_on_a_hosted_load() -> None:
    """Suppressing the request is only acceptable because the card still says
    something true. A silent empty card is not a fix."""
    body = _function("loadGuardInventory")
    hosted = body[body.index("window.CLOUD_MODE"):body.index("fetch('/api/guard/inventory')")]
    assert "innerHTML" in hosted, "the hosted branch must write the card"
    assert "GUARD_INVENTORY_LOCAL_ONLY" in hosted


def test_the_local_only_sentence_is_honest_and_specific() -> None:
    """It must not imply nothing was found, and must not imply an error."""
    m = re.search(r"^var GUARD_INVENTORY_LOCAL_ONLY\s*=\s*\n?\s*'([^']+)';", _src(), re.M)
    assert m, "GUARD_INVENTORY_LOCAL_ONLY not found in app.js"
    sentence = m.group(1)
    assert "machine your agents run on" in sentence
    assert "localhost:8900" in sentence
    for lie in ("Nothing inventoried", "No MCP servers", "Could not", "error"):
        assert lie not in sentence, f"the local-only sentence must not say {lie!r}"


def test_a_genuine_failure_is_still_logged() -> None:
    """Only the deliberate 'disabled here' answer is quiet. A 500, a dropped
    connection or a body that is not JSON stays visible to whoever looks."""
    body = _function("loadGuardInventory")
    assert "console.error" in body, "a real failure must reach the console"
    assert re.search(r"if \(!r\.ok\) throw", body), (
        "a non-OK response that is not the deliberate 410 must reach the catch"
    )


def test_the_agent_graph_sibling_got_the_same_treatment() -> None:
    """/api/local/agent-graph is cloud-disabled for the same reason and had
    the same unconditional fetch, one tab click away from the same failure."""
    body = _function("loadAgentGraph")
    guard = body.index("window.CLOUD_MODE")
    call = body.index("fetch('/api/local/agent-graph")
    assert guard < call, "the CLOUD_MODE branch must come before the fetch"
    assert "agent_graph_local_only" in body[guard:call]


def test_the_card_markup_still_exists_for_the_message_to_land_in() -> None:
    with open(_GUARD_HTML, encoding="utf-8") as fh:
        tpl = fh.read()
    assert 'id="guard-inventory-body"' in tpl
