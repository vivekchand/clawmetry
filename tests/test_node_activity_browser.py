"""Feature layout and real collector payload rendering in a local browser.

AC-OBS-NODE-007.1: evidence, map, resource measurement and scrubber share selection.
AC-OBS-NODE-007.2: reduced motion retains evidence without a travel animation.
AC-OBS-NODE-007.3: unavailable collection remains unknown with useful guidance.
AC-OBS-NODE-007.4: each view fits a 320 pixel viewport without page overflow.

This isolated component check is not a release or hosted end-to-end proof.
"""
from pathlib import Path
import json
import threading

import pytest

ROOT = Path(__file__).resolve().parents[1]


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
        assert page.locator("#na-map").get_attribute("data-event-id") == selected
        assert page.locator("#na-evidence").get_attribute("data-event-id") == selected
        assert page.locator("#na-map .na-map-actor-gap").evaluate("node => getComputedStyle(node).visibility") == "hidden", "Unknown attribution must not draw a connector from the Agent row"
        assert page.locator('[data-na-actor="unattributed"]').evaluate("node => node.classList.contains('na-selected')")
        # Exercise the actor contract independently of this collector's unknown identity.
        # A human or agent highlight must not inherit the same centered actor edge.
        for kind in ("human", "agent"):
            page.evaluate("([id, kind]) => { const event = cmNodeActivity.getState().data.events.find(event => event.id === id); event.actor = {kind, evidence: ['Contract-test attribution evidence']}; cmNodeActivity.select(id, true); }", [selected, kind])
            assert page.locator(f'[data-na-actor="{kind}"]').evaluate("node => node.classList.contains('na-selected')")
            assert page.locator("#na-map .na-map-actor-gap").evaluate("node => getComputedStyle(node).visibility") == "hidden", kind
            assert page.locator("#na-map .na-map-connection:not(.na-map-actor-gap)").evaluate("node => getComputedStyle(node).visibility") == "visible"
        assert int(page.locator("#na-scrub").input_value()) < len(payload["events"]) - 100
        assert "Last retained measurement before this event" in page.locator(".na-resource-history").inner_text()
        assert "Values between collections are unknown" in page.locator(".na-resource-history").inner_text()
        assert "na-animate" not in page.locator("#na-map").get_attribute("class")
        assert "Monitoring options changed" in page.locator("#na-evidence").inner_text()
        page.locator('[data-na-view="govern"]').click()
        for name, coverage in payload["coverage"].items():
            assert f"Visible scope: {coverage['scope']}" in page.locator("#na-coverage").inner_text(), name
        page.locator('[data-na-view="observe"]').click()
        current["data"] = unavailable("No stored observations are available. Open Govern to inspect collection.")
        page.locator("#na-refresh").click()
        page.wait_for_function("cmNodeActivity.getState().data.available===false")
        assert page.locator("#na-cpu").inner_text() == "Unknown"
        assert "Open Govern" in page.locator("#na-status").inner_text()
        assert page.locator(".na-event").count() == 0
        assert "No events were recorded" in page.locator("#na-events").inner_text()
    finally:
        context.close()
