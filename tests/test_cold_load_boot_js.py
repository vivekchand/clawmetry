"""Dashboard cold load: no startup storm, no duplicate requests (#5935).

On a cold start the dashboard's own startup requests timed out
(``Initial load failed timeout``, ``System health load failed timeout``,
``loadCrons failed timeout``) and their tiles rendered empty. Measured in a
headless browser against a scratch install: 121 API requests in one page load,
103 in the first 10 s, 22 in flight at the peak, against the browser's six
connections per origin. Requests spent 66 s combined in the browser's own queue
while the server answered most of them in milliseconds.

Behaviour of the startup path is pinned in ``test_cold_load_boot_js.js``
against shipped source. The checks below pin the seams that are not worth
running in a VM: that opening Overview loads what startup no longer preloads,
that the Flow tool prefetch waits for a screen that uses it, and that the
duplicate ``/api/overview`` callers share one in-flight request.

Factory requirement 08aff8e1-2a68-41c2-8052-da53bbbdd749 (AC 2, 3, 5).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JS_TEST = os.path.join(_HERE, "test_cold_load_boot_js.js")
_APP_JS = os.path.join(_HERE, "..", "clawmetry", "static", "js", "app.js")
_OVERVIEW_HTML = os.path.join(_HERE, "..", "clawmetry", "templates", "tabs", "overview.html")


def _src() -> str:
    with open(_APP_JS, encoding="utf-8") as fh:
        return fh.read()


def _function(name: str, is_async: bool = False) -> str:
    prefix = "async " if is_async else ""
    m = re.search(r"^" + prefix + r"function " + name + r"\b[\s\S]*?^\}", _src(), re.M)
    assert m, f"{name} not found in app.js"
    return m.group(0)


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_cold_load_boot_unit_suite() -> None:
    proc = subprocess.run(["node", _JS_TEST], capture_output=True, text=True, timeout=60)
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "cold-load boot tests failed:\n" + output
    assert "PASS" in output, "no PASS line in output:\n" + output


def test_opening_overview_loads_what_startup_no_longer_preloads() -> None:
    """Startup skips system health and tasks off-Overview, so the first visit
    must load them at once rather than on the next 10-30 s refresh tick."""
    body = _function("switchTab")
    assert re.search(r"_cmLoadedWithin\('systemHealth',\s*\d+\)\)\s*loadSystemHealth\(\)", body), (
        "switchTab('overview') does not load system health on the first visit"
    )
    assert re.search(r"_cmLoadedWithin\('overviewTasks',\s*\d+\)\)\s*loadOverviewTasks\(\)", body), (
        "switchTab('overview') does not load Overview tasks on the first visit"
    )


def test_loads_record_success_so_starters_do_not_repeat_them() -> None:
    assert "_cmMarkLoaded('systemHealth')" in _function("loadSystemHealth", is_async=True)
    assert "_cmMarkLoaded('overviewTasks')" in _function("loadOverviewTasks", is_async=True)


def test_flow_tool_prefetch_waits_for_a_screen_that_uses_it() -> None:
    """Twelve /api/component/tool/* requests fired 2 s into every page load,
    whatever screen it landed on."""
    src = _src()
    assert "setTimeout(_prefetchToolData, 2000)" not in src, (
        "the Flow tool-detail prefetch still fires unconditionally at startup"
    )
    assert re.search(r"function _prefetchToolDataIfVisible\b", src), (
        "no tab-gated wrapper around the Flow tool-detail prefetch"
    )


_FRONTEND_ROOTS = (
    os.path.join(_HERE, "..", "clawmetry", "static", "js"),
    os.path.join(_HERE, "..", "clawmetry", "templates"),
)
# A quoted string that names the /api/overview endpoint itself (optionally with
# a query string), in any quote style. /api/overview-foo is a different route.
_OVERVIEW_LITERAL = re.compile(r"""(['"`])[^'"`\n]*/api/overview(?![\w-])[^'"`\n]*\1""")
_COMMENT_LINE = re.compile(r"^\s*(//|\*|/\*|<!--|\{#)")
_TRAILING_COMMENT = re.compile(r"\s//\s.*$")


def _frontend_files() -> list:
    """Every JS and HTML file the dashboard serves, discovered, not listed:
    a new tab template or script that fetches /api/overview is covered the
    day it lands."""
    found = []
    for root in _FRONTEND_ROOTS:
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                if name.endswith((".js", ".html")):
                    found.append(os.path.normpath(os.path.join(dirpath, name)))
    return sorted(found)


def _overview_requests(path: str) -> list:
    """(line number, line) for each /api/overview URL literal outside a comment."""
    hits = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            if _COMMENT_LINE.match(line):
                continue
            if _OVERVIEW_LITERAL.search(_TRAILING_COMMENT.sub("", line)):
                hits.append((n, line.strip()))
    return hits


def test_every_overview_request_goes_through_the_shared_helper() -> None:
    """AC 3, the whole class: across every served script and template, the ONLY
    place that names the /api/overview URL is _cmFetchOverviewShared. A direct
    fetch anywhere else (the heartbeat card's old fallback was one) sends a
    second request with its own timer, which is what this PR removed."""
    files = _frontend_files()
    names = {os.path.basename(p) for p in files}
    assert {"app.js", "overview.html"} <= names, f"scan found no dashboard sources: {sorted(names)[:5]}"
    assert len(files) >= 10, f"scan found only {len(files)} frontend files; the roots moved"

    app_js = os.path.normpath(_APP_JS)
    src = _src()
    helper = re.search(r"^function _cmFetchOverviewShared\b[\s\S]*?^\}", src, re.M)
    assert helper, "_cmFetchOverviewShared is gone from app.js"
    helper_lines = range(src.count("\n", 0, helper.start()) + 1, src.count("\n", 0, helper.end()) + 2)

    stray = []
    inside_helper = 0
    for path in files:
        for n, line in _overview_requests(path):
            if path == app_js and n in helper_lines:
                inside_helper += 1
            else:
                stray.append(f"{os.path.relpath(path, os.path.join(_HERE, '..'))}:{n}: {line[:120]}")
    assert inside_helper == 1, f"_cmFetchOverviewShared names /api/overview {inside_helper} times, expected 1"
    assert not stray, (
        "/api/overview requested outside _cmFetchOverviewShared(); call the shared helper instead:\n  "
        + "\n  ".join(stray)
    )


def test_duplicate_overview_callers_share_one_request() -> None:
    """AC 3: the named consumers go through the one shared overview request.
    Behaviour (concurrent callers -> one fetch) is pinned in the Node suite."""
    for name, is_async in (("loadAll", True), ("_cmLoadDetectedRuntimes", True),
                           ("initFlow", False), ("updateFlowStats", False)):
        assert "_cmFetchOverviewShared()" in _function(name, is_async=is_async), (
            f"{name} does not use the shared overview request"
        )
    with open(_OVERVIEW_HTML, encoding="utf-8") as fh:
        html = fh.read()
    assert "_cmFetchOverviewShared()" in html, (
        "the Overview heartbeat card sends its own /api/overview beside loadAll's"
    )


def test_overview_budget_outlasts_a_busy_server() -> None:
    """Every /api/overview caller shares one in-flight request, and the FIRST
    caller's timer aborts it for all of them. With the daemon busy writing,
    opening Overview took longer than 3 s on the server; loadAll's 3 s budget
    aborted it twice and left the tiles on 'Load failed - retrying...'."""
    src = _src()
    m = re.search(r"^var _CM_OVERVIEW_BUDGET_MS = (\d+);", src, re.M)
    assert m, "no single budget for the shared /api/overview request"
    assert int(m.group(1)) >= 10000, (
        f"the shared /api/overview request is aborted after {m.group(1)} ms"
    )
    literal = [int(ms) for ms in re.findall(r"fetchJsonWithTimeout\('/api/overview',\s*(\d+)\)", src)]
    assert not literal, f"an /api/overview caller sets its own budget: {literal} ms"


def test_slow_usage_never_draws_measured_looking_zeros() -> None:
    """AC 5: when /api/usage was slow on a cold start, loadAll drew $0.00 and
    0 tokens into the Overview tiles, which read as 'no spend on this machine'."""
    body = _function("loadAll", is_async=True).replace(" ", "")
    assert "todayCost:0" not in body, "loadAll still renders zero usage it never measured"
    assert "_cmUsageTilesStillLoading" in body, (
        "loadAll does not put the usage tiles back on their loading placeholders"
    )


def test_failures_read_as_sentences_not_raw_error_codes() -> None:
    """AC 5: a busy server is not 'Failed to load: timeout'."""
    for name in ("loadSystemHealth", "loadCrons"):
        body = _function(name, is_async=True)
        catch = body[body.rindex("catch") :]
        assert "e.message" not in catch and "String(e" not in catch, (
            f"{name} still renders the raw error text to the user"
        )
