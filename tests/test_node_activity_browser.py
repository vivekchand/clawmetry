"""Feature layout and real collector payload rendering in a local browser.

AC-OBS-NODE-007.1: evidence, event story, resource measurement and scrubber share selection.
AC-OBS-NODE-007.2: reduced motion retains evidence without a travel animation.
AC-OBS-NODE-007.3: unavailable collection remains unknown with useful guidance.
AC-OBS-NODE-007.4: each view fits a 320 pixel viewport without page overflow.
AC-OBS-NODE-CLARITY-005.1: stale retained rows keep a direct coverage path.

This isolated component check is not a release or hosted end-to-end proof.
"""
from pathlib import Path
import json
import threading
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("width", [320, 1280])
def test_process_search_and_usage_component(_shared_chromium, tmp_path, width):
    """Isolated UI contract with sample data, not live collector evidence.

    AC-OBS-NODE-SEARCH-001.1
    AC-OBS-NODE-SEARCH-001.2
    AC-OBS-NODE-SEARCH-001.3
    AC-OBS-NODE-SEARCH-002.2
    AC-OBS-NODE-SEARCH-002.3
    """
    now = int(time.time() * 1000)
    payload = {"available": True, "collected_at": now, "summary": {}, "events": [],
               "coverage": {"processes": {"state": "partial"}}, "preferences": {},
               "processes": [{"pid": i + 1, "name": "worker-" + str(i), "cpu_percent": 205 - i,
                              "observed_at": now, "stale": False} for i in range(205)]}
    payload["processes"].append({"pid": 9876, "name": "python3.12", "clawmetry_role": "collector",
                                 "cpu_percent": 0, "cpu_interval_seconds": 30, "memory_bytes": 1048576,
                                 "observed_at": now, "stale": False})
    css = (ROOT / "clawmetry/static/css/dashboard.css").read_text() + (ROOT / "clawmetry/static/css/node-activity.css").read_text()
    template = (ROOT / "clawmetry/templates/tabs/node-activity.html").read_text().replace('class="page"', 'class="page active"')
    shell = '<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><style>' + css + '</style><body style="padding:12px">' + template + '</body>'
    context = _shared_chromium.new_context(viewport={"width": width, "height": 900})
    try:
        page = context.new_page()
        errors, requests = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        def respond(route):
            requests.append(route.request.url)
            route.fulfill(content_type="application/json", body=json.dumps(payload))
        page.route("http://node.test/api/node-activity?limit=100", respond)
        page.route("http://node.test/", lambda route: route.fulfill(content_type="text/html", body=shell))
        page.goto("http://node.test/")
        page.evaluate("window._cmCurrentTab='node-activity'")
        page.add_script_tag(content=(ROOT / "clawmetry/static/js/node-activity.js").read_text())
        page.evaluate("loadNodeActivity()")
        assert "ClawMetry Collector" in page.locator("#na-clawmetry-processes").inner_text()
        assert "0%" in page.locator("#na-clawmetry-processes").inner_text()
        assert page.locator("#na-processes tbody tr").count() == 100
        page.get_by_role("button", name="Next process page").click()
        page.get_by_role("button", name="Next process page").click()
        assert "worker-204" in page.locator("#na-processes").inner_text()
        search = page.get_by_role("searchbox", name="Search processes")
        search.fill("WORKER-204")
        assert page.locator("#na-processes tbody tr").count() == 1
        assert "1 to 1 of 1" in page.locator("#na-process-results").inner_text()
        search.fill("9876")
        assert "ClawMetry Collector" in page.locator("#na-processes").inner_text()
        search.fill("clawmetry")
        assert "python3.12" in page.locator("#na-processes").inner_text()
        assert len(requests) == 1, "Search and pages must not fetch observations"
        page.locator("#na-refresh").click()
        page.wait_for_function("!cmNodeActivity.getState().pending")
        assert search.input_value() == "clawmetry"
        assert page.locator("#na-processes tbody tr").count() == 1
        search.fill("<img src=x onerror=alert(1)>")
        assert "No matching processes" in page.locator("#na-processes").inner_text()
        assert page.locator("#na-processes img").count() == 0
        page.get_by_role("button", name="Clear", exact=True).click()
        assert search.input_value() == ""
        assert page.locator("#na-processes tbody tr").count() == 100
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(tmp_path / ("process-search-" + str(width) + ".png")), full_page=True)
        assert not errors
    finally:
        context.close()


def test_node_activity_real_payload_at_narrow_width(_shared_chromium, tmp_path):
    pytest.importorskip("psutil")
    import duckdb
    from clawmetry.node_activity import collect_node_activity, unavailable
    from clawmetry.node_activity_store import NODE_ACTIVITY_DDL, NodeActivityStoreMixin

    class Store(NodeActivityStoreMixin):
        def __init__(self):
            self._conn = duckdb.connect(":memory:")
            self._write_lock = threading.Lock()
            self._read_only = False
            for sql in NODE_ACTIVITY_DDL:
                self._conn.execute(sql)

        def _fetch(self, sql, params):
            with self._write_lock:
                return self._conn.execute(sql, params).fetchall()

    store = Store()
    try:
        state = store.get_node_activity_state()
        observation = collect_node_activity(home=tmp_path, fingerprint_key=state["fingerprint_key"])
        store.record_node_activity(observation)
        # These are actual persisted test-store setting changes, not seeded telemetry.
        store.set_node_activity_preferences({"rule_new_listener": False})
        reviewed_id = store.query_node_activity()["events"][0]["id"]
        store.review_node_activity_event(reviewed_id, "investigate", "Review this earlier settings change")
        store.set_node_activity_preferences({"rule_new_listener": True})
        for index in range(110):
            store.set_node_activity_preferences({"rule_new_listener": bool(index % 2)})
        payload = store.query_node_activity()
    finally:
        store._conn.close()

    template = (ROOT / "clawmetry/templates/tabs/node-activity.html").read_text()
    css = (ROOT / "clawmetry/static/css/dashboard.css").read_text() + (ROOT / "clawmetry/static/css/node-activity.css").read_text()
    script = (ROOT / "clawmetry/static/js/node-activity.js").read_text()
    shell = '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><style>' + css + '</style><body style="padding:12px">' + template.replace('class="page"', 'class="page active"') + '</body></html>'
    context = _shared_chromium.new_context(viewport={"width": 320, "height": 900}, reduced_motion="reduce")
    try:
        page = context.new_page()
        current = {"data": payload}
        page.route("http://node.test/api/node-activity?limit=100", lambda route: route.fulfill(content_type="application/json", body=json.dumps(current["data"])))
        page.route("http://node.test/", lambda route: route.fulfill(content_type="text/html", body=shell))
        page.goto("http://node.test/")
        page.evaluate("window._cmCurrentTab='node-activity'")
        page.add_script_tag(content=script)
        page.evaluate("loadNodeActivity()")
        page.wait_for_selector(".na-event")
        for view in ("observe", "govern", "guard"):
            page.locator(f'[data-na-view="{view}"]').click()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), view
            assert page.locator(f'[data-na-panel="{view}"]').is_visible()
        # An investigation older than 100 routine events remains in Guard.
        page.locator(f'[data-na-open="{reviewed_id}"]').filter(visible=True).click()
        selected = page.locator(".na-event[aria-current=step]").get_attribute("data-na-event")
        assert selected == reviewed_id
        assert page.locator("#na-evidence").get_attribute("data-event-id") == selected
        assert page.locator("#na-map").count() == 0, "A category diagram must not imply attribution"
        assert page.locator(".na-technical").count() == 1
        assert not page.locator(".na-technical").evaluate("node => node.open"), "Raw evidence starts collapsed"
        # A measured actor requires attribution evidence, not an arbitrary label.
        for kind in ("human", "agent"):
            page.evaluate("([id, kind]) => { const event = cmNodeActivity.getState().data.events.find(event => event.id === id); event.actor = {kind, evidence: ['Contract-test attribution evidence']}; cmNodeActivity.select(id, true); }", [selected, kind])
            assert "Contract-test attribution evidence" in page.locator(".na-identity-note").inner_text()
        page.locator(".na-technical summary").click()
        assert page.locator(".na-technical").evaluate("node => node.open")
        assert "Before" in page.locator(".na-technical").inner_text()
        assert int(page.locator("#na-scrub").input_value()) < len(payload["events"]) - 100
        assert "Last retained measurement before this event" in page.locator(".na-resource-history").inner_text()
        assert "Values between collections are unknown" in page.locator(".na-resource-history").inner_text()
        assert "na-animate" not in page.locator("#na-evidence").get_attribute("class")
        assert "Monitoring options changed" in page.locator("#na-evidence").inner_text()
        page.locator('[data-na-view="govern"]').click()
        for name, coverage in payload["coverage"].items():
            assert f"Visible scope: {coverage['scope']}" in page.locator("#na-coverage").inner_text(), name
        page.locator('[data-na-view="observe"]').click()
        # AC-OBS-NODE-CLARITY-005.1: retained stale rows still need a coverage path.
        stale_payload = json.loads(json.dumps(payload))
        stale_payload["coverage"]["processes"] = {"state": "unavailable", "reason": "Permission denied."}
        for row in stale_payload["processes"]:
            row.update(stale=True, observed_at=1)
        current["data"] = stale_payload
        page.locator("#na-refresh").click()
        page.wait_for_function("document.querySelector('#na-processes').textContent.includes('Stale observation')")
        assert page.get_by_role("button", name="View process coverage", exact=True).count() == 1
        page.get_by_role("button", name="View process coverage", exact=True).click()
        assert page.locator('[data-na-panel="govern"]').is_visible()
        page.locator('[data-na-view="observe"]').click()
        current["data"] = unavailable("No stored observations are available. Open Govern to inspect collection.")
        page.locator("#na-refresh").click()
        page.wait_for_function("cmNodeActivity.getState().data.available===false")
        assert page.locator("#na-cpu").inner_text() == "Unknown"
        assert "Open Govern" in page.locator("#na-status").inner_text()
        assert page.locator(".na-event").count() == 0
        assert "No events were recorded" in page.locator("#na-events").inner_text()
        assert "View coverage" in page.locator("#na-listeners").inner_text()
        page.locator("#na-listeners [data-na-coverage]").click()
        assert page.locator('[data-na-panel="govern"]').is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    finally:
        context.close()
