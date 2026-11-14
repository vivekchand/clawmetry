"""Serve the actual OSS Asimov page over HTTP with an empty scratch DuckDB.

This verifies installation UI, auth and visibility-scoped polling. It inserts
no robot telemetry and does not qualify any physical robot or SDK connection.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@contextmanager
def native_chromium(chromium, profile, output):
    """Attach without Playwright's per-session focus/capture overrides."""
    profile.mkdir()
    with (output / "native-chromium.log").open("wb") as log:
        process = subprocess.Popen([
            chromium.executable_path, "--remote-debugging-address=127.0.0.1",
            "--remote-debugging-port=0", "--user-data-dir=" + str(profile),
            "--no-first-run", "--no-default-browser-check", "--no-sandbox",
            "--disable-background-networking", "--disable-component-update",
            "--disable-background-timer-throttling", "--window-size=1600,1100", "about:blank",
        ], stdout=log, stderr=subprocess.STDOUT)
        browser = None
        try:
            port_file = profile / "DevToolsActivePort"
            deadline = time.monotonic() + 15
            while True:
                assert process.poll() is None, "native Chromium exited; see native-chromium.log"
                lines = port_file.read_text().splitlines() if port_file.exists() else []
                if len(lines) >= 2:
                    port = int(lines[0])
                    assert 0 < port < 65536 and lines[1].startswith("/devtools/browser/")
                    endpoint = "ws://127.0.0.1:" + str(port) + lines[1]
                    break
                assert time.monotonic() < deadline, "native Chromium CDP startup timed out; see native-chromium.log"
                time.sleep(0.05)
            # Public Playwright >=1.60 option. A secondary CDP session cannot
            # undo the capturer handle owned by Playwright's original session;
            # no_defaults prevents that focus override from being installed.
            browser = chromium.connect_over_cdp(endpoint, no_defaults=True, timeout=10000)
            yield browser
        finally:
            try:
                if browser is not None:
                    browser.close()
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


def run(output, *, headed=False):
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import expect, sync_playwright
    from werkzeug.serving import make_server

    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="clawmetry-asimov-browser-") as scratch:
        data = Path(scratch)
        for name in ("workspace", "logs", "sessions", "memory", "openclaw", "journal"):
            (data / name).mkdir()
        os.environ["CLAWMETRY_LOCAL_STORE_PATH"] = str(data / "empty.duckdb")
        os.environ["CLAWMETRY_NO_CLOUD"] = "1"
        os.environ["CLAWMETRY_ENFORCE"] = "1"
        os.environ["CLAWMETRY_HARD_BLOCK"] = "1"
        os.environ["CLAWMETRY_DESKTOP_ALERTS"] = "0"
        os.environ["CLAWMETRY_CLOUD_INCIDENT_ALERTS"] = "0"
        os.environ["CLAWMETRY_ROBOTICS_DIR"] = str(data / "journal")
        from clawmetry import local_store
        from clawmetry.asimov.store import AsimovLocalStore

        local_store.DB_PATH = data / "empty.duckdb"
        store = local_store.LocalStore()
        local_store._store_rw = store
        local_store._store_ro = None
        AsimovLocalStore(store, initialize=True)
        import dashboard

        dashboard.detect_config(argparse.Namespace(
            workspace=str(data / "workspace"), log_dir=str(data / "logs"),
            sessions_dir=str(data / "sessions"), memory_dir=str(data / "memory"),
            data_dir=str(data / "openclaw"), openclaw_dir=str(data / "openclaw"), name="Browser check"))
        dashboard.GATEWAY_TOKEN = "asimov-browser-local-test-token"
        app = dashboard.app
        client = app.test_client()
        # Exercise the actual shared dashboard auth hook. Browser loopback is
        # trusted by product policy; a remote caller still needs its token.
        remote = {"REMOTE_ADDR": "203.0.113.42"}
        assert client.get("/api/asimov/runs", environ_overrides=remote).status_code == 401
        authorized = client.get("/api/asimov/runs", environ_overrides=remote,
                                headers={"Authorization": "Bearer asimov-browser-local-test-token"})
        assert authorized.status_code == 200 and authorized.json["runs"] == []
        service = make_server("127.0.0.1", 0, app, threaded=True)
        worker = threading.Thread(target=service.serve_forever, daemon=True)
        worker.start()
        origin = "http://127.0.0.1:" + str(service.server_port)
        report = {"environment": "empty_scratch_store", "telemetry_seeded": False,
                  "hardware_qualified": False, "remote_auth_checked": True,
                  "capture_mode": "headless_chromium", "views": []}
        try:
            def open_checked_page(browser, viewport, *, context=None, page=None):
                if context is None:
                    context = browser.new_context(viewport=viewport, reduced_motion="reduce")
                if page is None:
                    page = context.new_page()
                errors, failures, api_calls = [], [], []
                page.on("pageerror", lambda error: errors.append(type(error).__name__))
                page.on("console", lambda message: errors.append(message.type) if message.type == "error" else None)
                page.on("response", lambda response: failures.append(response.status) if response.status >= 400 else None)
                page.on("request", lambda request: api_calls.append(time.monotonic())
                        if "/api/asimov/" in request.url else None)
                try:
                    result = page.goto(origin + "/asimov", wait_until="domcontentloaded")
                    assert result is not None and result.status == 200
                    expect(page.get_by_role("heading", name="Asimov 1", exact=True)).to_be_visible()
                    expect(page.locator("#asimov-empty")).to_be_visible()
                    expect(page.locator("#asimov-workbench")).to_be_hidden()
                    expect(page.locator(".asimov-qualification")).to_contain_text("Hardware qualification is pending")
                    expect(page.locator("#asimov-empty")).to_contain_text("--robot-id my-asimov")
                    expect(page.locator("#asimov-empty")).to_contain_text("cannot move or stop a robot")
                    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "page overflows viewport"
                    page.wait_for_function("window.cmAsimov.getState().loading===null")
                    assert len(api_calls) == 1, "empty page fetches one summary, no trace fanout"
                    assert not errors, "served Asimov page emitted browser errors"
                    assert not failures, "served Asimov page has failed resources or APIs"
                    return context, page, errors, failures, api_calls
                except BaseException:
                    context.close()
                    raise

            with sync_playwright() as pw:
                # Screenshot compositing and native tab visibility exercise
                # different Chromium modes. Never capture the Xvfb framebuffer.
                browser = pw.chromium.launch(headless=True)
                try:
                    for label, viewport in (("desktop", {"width": 1440, "height": 1000}),
                                            ("mobile", {"width": 390, "height": 844})):
                        context, page, errors, failures, _ = open_checked_page(browser, viewport)
                        try:
                            page.evaluate("document.fonts.ready")
                            page.evaluate("new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                            geometry = page.evaluate("""() => ({width: innerWidth, height: innerHeight,
                                scrollWidth: document.documentElement.scrollWidth,
                                scrollHeight: document.documentElement.scrollHeight,
                                devicePixelRatio, visibility: document.visibilityState})""")
                            assert geometry["width"] == viewport["width"]
                            assert 0 < geometry["scrollHeight"] <= 4096, "unexpected screenshot bounds"
                            diagnostic = {"capture_mode": "headless_chromium", "viewport": label,
                                          "geometry": geometry, "browser_errors": errors,
                                          "failed_responses": failures}
                            diagnostic_path = output / (label + "-capture-diagnostic.json")
                            diagnostic_path.write_text(json.dumps(diagnostic, indent=2) + "\n")
                            try:
                                page.screenshot(path=str(output / (label + "-empty.png")), full_page=True,
                                                animations="disabled", timeout=15000)
                            except Exception as exc:
                                diagnostic["capture_error_type"] = type(exc).__name__
                                diagnostic_path.write_text(json.dumps(diagnostic, indent=2) + "\n")
                                raise
                            assert not errors, "served Asimov page emitted browser errors"
                            assert not failures, "served Asimov page has failed resources or APIs"
                            report["views"].append({"viewport": label, "capture_mode": "headless_chromium",
                                                    "browser_errors": 0, "failed_responses": 0,
                                                    "empty_state": True})
                        finally:
                            context.close()
                finally:
                    browser.close()

                assert headed, "The real visibility check requires --headed and an X display"
                # A directly launched normal profile and no_defaults=True keep
                # native visibility intact. Timer throttling remains disabled so
                # the application itself must stop background requests.
                with native_chromium(pw.chromium, data / "visibility-browser", output) as browser:
                    assert len(browser.contexts) == 1, "one native default profile required"
                    context = browser.contexts[0]
                    assert context.pages, "native Chromium must have its initial tab"
                    _, page, errors, failures, api_calls = open_checked_page(
                        browser, {"width": 1440, "height": 1000}, context=context, page=context.pages[0])
                    browser_cdp = browser.new_browser_cdp_session()
                    page_cdp = context.new_cdp_session(page)
                    other = None
                    other_cdp = None
                    visibility_path = output / "native-visibility-diagnostic.json"
                    visibility = {"visibility_mode": "headed_chromium_native_tabs",
                                  "browser_version": browser.version,
                                  "playwright_no_defaults": True,
                                  "playwright_focus_emulation_installed": False,
                                  "background_timer_throttling_disabled": True,
                                  "same_native_window_checked": False}
                    try:
                        page_info = page_cdp.send("Target.getTargetInfo")["targetInfo"]
                        visibility["page_target_id"] = page_info["targetId"]
                        visibility["page_window"] = browser_cdp.send(
                            "Browser.getWindowForTarget", {"targetId": page_info["targetId"]})
                        # Explicit false is stronger than an omitted newWindow:
                        # Chromium rejects it if no existing profile window is
                        # available. See chrome/browser/devtools/protocol/
                        # target_handler.cc, TargetHandler::CreateTarget.
                        create = {"url": "about:blank", "newWindow": False, "background": True}
                        if page_info.get("browserContextId"):
                            create["browserContextId"] = page_info["browserContextId"]
                        with context.expect_page(timeout=10000) as opened:
                            target = browser_cdp.send("Target.createTarget", create)
                        other = opened.value
                        other.wait_for_load_state("domcontentloaded")
                        other_cdp = context.new_cdp_session(other)
                        other_info = other_cdp.send("Target.getTargetInfo")["targetInfo"]
                        visibility["other_target_id"] = other_info["targetId"]
                        visibility["other_window"] = browser_cdp.send(
                            "Browser.getWindowForTarget", {"targetId": other_info["targetId"]})
                        assert target["targetId"] == other_info["targetId"], "wrong native tab attached"
                        assert page_info["targetId"] != other_info["targetId"], "two distinct tabs required"
                        assert visibility["page_window"]["windowId"] == visibility["other_window"]["windowId"], \
                            "visibility check requires two actual tabs in the same native window"
                        visibility["same_native_window_checked"] = True
                        browser_cdp.send("Target.activateTarget", {"targetId": page_info["targetId"]})
                        page.wait_for_function("document.hidden===false", polling=100, timeout=10000)
                        browser_cdp.send("Target.activateTarget", {"targetId": other_info["targetId"]})
                        other.wait_for_function("document.hidden===false", polling=100, timeout=10000)
                        page.wait_for_function("document.hidden===true", polling=100, timeout=10000)
                        visibility["background_state"] = page.evaluate("document.visibilityState")
                        page.wait_for_timeout(150)
                        hidden_count = len(api_calls)
                        page.wait_for_timeout(6500)
                        assert len(api_calls) == hidden_count, "hidden Asimov page continued polling"
                        visibility["requests_while_hidden"] = len(api_calls) - hidden_count
                        browser_cdp.send("Target.activateTarget", {"targetId": page_info["targetId"]})
                        page.wait_for_function("document.hidden===false", polling=100, timeout=10000)
                        page.wait_for_function("window.cmAsimov.getState().loading===null")
                        page.wait_for_timeout(250)
                        assert len(api_calls) > hidden_count, "returning to Asimov did not resume observation"
                        visibility["foreground_state"] = page.evaluate("document.visibilityState")
                        visibility["polling_resumed"] = True
                        assert not errors, "served Asimov page emitted browser errors"
                        assert not failures, "served Asimov page has failed resources or APIs"
                        report["hidden_polling_checked"] = True
                        report["visibility_mode"] = "headed_chromium_native_tabs"
                        report["same_native_window_checked"] = True
                    except Exception as exc:
                        visibility["error_type"] = type(exc).__name__
                        raise
                    finally:
                        visibility["api_requests"] = len(api_calls)
                        for label, candidate in (("page", page), ("other", other)):
                            if candidate is not None:
                                try:
                                    visibility[label] = candidate.evaluate(
                                        "({state: document.visibilityState, hidden: document.hidden, focused: document.hasFocus()})")
                                except PlaywrightError as exc:
                                    visibility[label] = {"diagnostic_error_type": type(exc).__name__}
                        visibility_path.write_text(json.dumps(visibility, indent=2) + "\n")
                        if other_cdp is not None:
                            other_cdp.detach()
                        page_cdp.detach()
                        browser_cdp.detach()
            assert store._fetch("SELECT count(*) FROM asimov_events", [])[0][0] == 0
            (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
            print("Actual served Asimov empty-state, auth, desktop/mobile and hidden-poll checks passed")
        finally:
            service.shutdown()
            worker.join(timeout=5)
            service.server_close()
            store.stop()
            local_store._store_rw = None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/asimov-browser")
    parser.add_argument("--headed", action="store_true", help="Require an additional headed native-tab visibility check under an X display")
    options = parser.parse_args()
    run(options.output, headed=options.headed)
