"""AC-ASSIST-008.5/.6: actual native Sources DOM, keyboard and history.

Uses the shipped template/CSS/JS with synthetic API fixtures, never a live
provider or the user's browser. This is layout/integration regression proof.
"""
import copy
import json
import os
from pathlib import Path

import pytest

from tests.test_assistant_evidence_frontend import SESSION, SOURCE


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("width,theme", [(1440, "dark"), (390, "light"), (320, "dark")])
def test_sources_keyboard_history_layout_and_session_route(_shared_chromium, width, theme):
    from playwright.sync_api import expect

    context = _shared_chromium.new_context(viewport={"width": width, "height": 940})
    page = context.new_page()
    requests, errors = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    source = copy.deepcopy(SOURCE)
    # Literal hostile markup and an unbroken command argument must wrap as text.
    source["preview"][0]["fields"]["command"] += " " + "long-path/" * 30 + ' <img src=x onerror="window.injected=true">'
    source["preview"][0]["fields"]["output"] = "File missing: report.json\nNext line of recorded output."
    source["preview"][0]["field_status"]["output"] = {"status": "available"}
    sql = {"label": "[2] Error counts", "rows": 53, "preview_rows": 20,
           "preview": [{"runtime": "codex", "errors": i} for i in range(20)],
           "sql": "SELECT runtime, errors FROM sessions", "truncated": True}
    answer = {"answer": "The recorded command could not find report.json. [1]",
              "conversation_id": "saved", "sources": [source, sql], "panels": []}
    messages = [{"role": "user", "content": "Why did the command fail?"},
                {"role": "assistant", "content": answer["answer"], "sources": answer["sources"]}]
    html = '<!doctype html><html data-theme="' + theme + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>'
    html += (ROOT / "clawmetry/templates/tabs/assistant.html").read_text() + "</body></html>"

    def route(request_route):
        path = request_route.request.url.split("assistant.test", 1)[-1]
        if path == "/":
            request_route.fulfill(content_type="text/html", body=html)
            return
        requests.append(path)
        if path == "/api/assistant/status":
            body = {"available": True, "data_available": True, "providers": [], "managed": {}}
        elif path == "/api/assistant/conversations":
            body = {"conversations": [{"id": "saved", "title": "Recorded command investigation"}]}
        elif path == "/api/assistant/conversations/saved":
            body = {"id": "saved", "messages": messages}
        elif path == "/api/assistant/chat":
            request_route.fulfill(content_type="text/event-stream", body="event: done\ndata: " + json.dumps(answer) + "\n\n")
            return
        else:
            raise AssertionError("Unexpected request: " + path)
        request_route.fulfill(content_type="application/json", body=json.dumps(body))

    context.route("https://assistant.test/**", route)
    try:
        page.goto("https://assistant.test/")
        page.add_style_tag(path=str(ROOT / "clawmetry/static/css/dashboard.css"))
        page.add_style_tag(path=str(ROOT / "clawmetry/static/css/assistant.css"))
        page.evaluate("""() => {
          window.CLOUD_MODE=true; window.CLOUD_NODE_ID='test-node';
          window._cmAssistantRelay={version:1,identity:()=> 'test-identity'};
          window.switchTab=name=>{window.visitedTab=name;window.assistantLeave();};
        }""")
        page.add_script_tag(path=str(ROOT / "clawmetry/static/js/trail.js"))
        page.add_script_tag(path=str(ROOT / "clawmetry/static/js/assistant.js"))
        page.evaluate("loadAssistantPage()")
        page.locator("#cm-assistant-input").fill("Why did the command fail?")
        expect(page.locator("#cm-assistant-send")).to_be_enabled()
        page.locator("#cm-assistant-send").click()
        source_details = page.locator(".cm-assistant-source-details").first
        expect(source_details).to_contain_text("Recorded command failure")
        expect(page.locator("#cm-assistant-status-message")).to_contain_text("Answer ready")
        before = list(requests)
        source_details.locator(":scope > summary").focus()
        page.keyboard.press("Enter")
        record = source_details.locator(".cm-assistant-evidence-item")
        expect(record.locator(":scope > summary")).to_be_visible()
        record.locator(":scope > summary").focus()
        page.keyboard.press("Enter")
        expect(record.locator("pre").first).to_contain_text("<img src=x")
        expect(record).to_contain_text("File missing: report.json")
        expect(record).to_contain_text("linked by their recorded call ID")
        assert page.locator(".cm-assistant-sources img").count() == 0
        assert page.evaluate("window.injected || false") is False
        assert requests == before, "expansion must not fetch or replay inference"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        assert record.evaluate("e => e.getBoundingClientRect().right <= innerWidth + 1")
        sql_details = page.locator(".cm-assistant-source-details").nth(1)
        expect(sql_details).to_contain_text("preview 20 of 53")
        expect(sql_details).to_contain_text("query reached its result limit")

        # The native composer is sticky. Evidence must remain reachable above
        # it, including when a long command expands on a narrow phone.
        output = record.locator("pre").nth(2)
        output.scroll_into_view_if_needed()
        output.evaluate("e => e.scrollIntoView({block:'center',behavior:'instant'})")
        page.wait_for_function("""() => {
          const e=document.querySelectorAll('.cm-assistant-evidence-item pre')[2];
          const r=e.getBoundingClientRect(), x=r.left+r.width/2, y=r.top+r.height/2;
          return y>0 && y<innerHeight && e.contains(document.elementFromPoint(x,y));
        }""")

        capture_dir = os.environ.get("CM_ASSISTANT_EVIDENCE_CAPTURES")
        if capture_dir:
            target = Path(capture_dir)
            target.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target / f"evidence-{width}-{theme}.png"), full_page=True)
            page.screenshot(path=str(target / f"evidence-visible-{width}-{theme}.png"))

        # Reopen persisted history through the same public page path.
        page.locator("#cm-assistant-new-chat").click()
        page.locator(".cm-assistant-history-item").first.click()
        expect(page.locator(".cm-assistant-evidence-item")).to_have_count(1)
        expect(page.locator(".cm-assistant-evidence-item")).to_contain_text("File missing: report.json")
        page.locator(".cm-assistant-source-details").first.locator(":scope > summary").click()
        button = page.get_by_role("button", name="Open session", exact=True)
        before = list(requests)
        button.focus()
        page.keyboard.press("Enter")
        assert page.evaluate("window.visitedTab") == "trail"
        assert page.evaluate("window._trailSessionFromHash()") == SESSION
        assert requests == before, "session action must not submit another Assistant question"
        assert requests.count("/api/assistant/chat") == 1
        assert not errors
    finally:
        context.close()
