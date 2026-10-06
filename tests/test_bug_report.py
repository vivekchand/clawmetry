"""Guards for the "Report a bug" surface.

Three bug classes this pins, each of which has shipped here before in
another feature's clothes:

1. **Dead UI.** A control that renders but reaches nothing, or a handler
   with no control pointing at it. The dialog, the script that drives it
   and the sidebar entry that opens it are asserted together against the
   RENDERED page, not the source.
2. **Raw error strings.** Every failure path must answer with a sentence
   a non-engineer can act on -- never a status code, an exception, or an
   upstream ``error`` key echoed through.
3. **A ticket id that does not exist.** The id is minted by the intake,
   never by this process, so an id can never be shown for a report that
   was not stored. An unreachable intake must say so and keep the text.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import routes.support as support  # noqa: E402


@pytest.fixture(scope="module")
def client():
    """detect_config() is what registers the blueprints onto the module-level
    app -- a bare ``dashboard.app.test_client()`` sees zero routes. Same
    pattern as tests/test_security_txt.py."""
    import argparse

    import dashboard as d

    already = any("bug-report" in str(r) for r in d.app.url_map.iter_rules())
    if not already:
        d.detect_config(argparse.Namespace(
            name=None, workspace=None, openclaw_dir=None,
            data_dir=None, log_dir=None, sessions_dir=None))
    d.app.config["TESTING"] = True
    return d.app.test_client()


# ── the surface exists and is wired ──────────────────────────────────────
def test_dialog_script_and_nav_entry_all_render():
    """All three halves of the feature must be in the SERVED page: a modal
    with no opener, or an opener with no modal, is dead UI."""
    import dashboard as d
    from flask import render_template_string

    with d.app.test_request_context("/"):
        html = render_template_string(
            d.DASHBOARD_HTML, version=d.__version__,
            legacy_nav=False, v2_enabled=False, is_pro=False)

    assert 'id="bug-overlay"' in html, "the dialog markup is missing"
    assert "js/bug-report.js" in html, "nothing loads the dialog's behaviour"
    assert "openBugModal()" in html, "no control opens the dialog"
    assert "left-nav-report" in html, "the sidebar entry is missing"
    # The opener must sit OUTSIDE any one tab pane, or it is only reachable
    # from whichever tab happens to be open.
    assert "left-nav-footer" in html


def test_legacy_nav_also_offers_it():
    """The legacy header nav has no sidebar; it needs its own entry or the
    feature silently disappears for anyone on that layout."""
    import dashboard as d
    from flask import render_template_string

    with d.app.test_request_context("/"):
        html = render_template_string(
            d.DASHBOARD_HTML, version=d.__version__,
            legacy_nav=True, v2_enabled=False, is_pro=False)
    assert "openBugModal()" in html


def test_routes_are_registered(client):
    import dashboard as d
    rules = {r.rule for r in d.app.url_map.iter_rules()}
    assert "/api/bug-report" in rules
    assert "/api/bug-report/<ticket>" in rules
    assert "/api/bug-report/diagnostics" in rules


# ── intake behaviour ─────────────────────────────────────────────────────
def test_missing_title_is_refused_in_plain_words(client):
    resp = client.post("/api/bug-report", json={"body": "it broke"})
    assert resp.status_code == 400
    msg = resp.get_json()["error"]
    assert "what went wrong" in msg.lower()
    assert "400" not in msg and "error" != msg.lower()


def test_report_is_forwarded_and_ticket_returned(client, monkeypatch):
    sent = {}

    def fake_post(payload):
        sent.update(payload)
        return {"ok": True, "ticket": "CM-4F2K9Q1X", "status": "received",
                "status_label": "Received",
                "status_url": "https://app.clawmetry.com/bug/CM-4F2K9Q1X"}, 200

    monkeypatch.setattr(support, "_post_to_cloud", fake_post)
    resp = client.post("/api/bug-report", json={
        "idem_key": "abc123", "title": "Cost tab shows zero",
        "body": "Opened Cost, every runtime reads $0.00",
        "severity": "major", "email": "someone@example.com"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ticket"] == "CM-4F2K9Q1X"
    # The forward must carry what makes a report reproducible.
    assert sent["severity"] == "major"
    assert sent["idem_key"] == "abc123"
    assert sent["source"] == "local"
    assert "clawmetry_version" in sent["diagnostics"]
    assert "daemon_running" in sent["diagnostics"]


def test_unknown_severity_falls_back_rather_than_failing(client, monkeypatch):
    monkeypatch.setattr(support, "_post_to_cloud",
                        lambda p: ({"ok": True, "ticket": "CM-11111111"}, 200))
    resp = client.post("/api/bug-report",
                       json={"title": "x", "severity": "catastrophic"})
    assert resp.status_code == 200


def test_offline_says_nothing_was_sent_and_is_retryable(client, monkeypatch):
    """Status 0 means the POST never left the machine. The user must be told
    that plainly -- and told their text is safe -- not shown a code."""
    monkeypatch.setattr(support, "_post_to_cloud", lambda p: ({}, 0))
    resp = client.post("/api/bug-report", json={"title": "the thing broke"})
    assert resp.status_code == 503
    body = resp.get_json()
    assert body["retryable"] is True
    msg = body["error"]
    assert "nothing was sent" in msg.lower()
    assert "hello@clawmetry.com" in msg


def test_intake_failure_never_invents_a_ticket(client, monkeypatch):
    monkeypatch.setattr(support, "_post_to_cloud", lambda p: ({"ok": False}, 500))
    resp = client.post("/api/bug-report", json={"title": "the thing broke"})
    assert resp.status_code == 502
    assert "ticket" not in resp.get_json()


def test_rate_limit_message_is_human(client, monkeypatch):
    monkeypatch.setattr(
        support, "_post_to_cloud",
        lambda p: ({"ok": False, "error": "Slow down there friend."}, 429))
    resp = client.post("/api/bug-report", json={"title": "x"})
    assert resp.status_code == 429
    assert resp.get_json()["error"] == "Slow down there friend."


def test_disabled_install_explains_itself(client, monkeypatch):
    monkeypatch.setattr(support, "CLOUD_INTAKE_URL", "")
    resp = client.post("/api/bug-report", json={"title": "x"})
    assert resp.status_code == 503
    assert "hello@clawmetry.com" in resp.get_json()["error"]


# ── what we attach ───────────────────────────────────────────────────────
def test_diagnostics_carry_environment_but_no_user_content(client):
    resp = client.get("/api/bug-report/diagnostics")
    assert resp.status_code == 200
    diag = resp.get_json()["diagnostics"]
    for key in ("clawmetry_version", "python", "platform",
                "runtimes_detected", "daemon_running"):
        assert key in diag, f"{key} missing from the attached environment"
    # The dialog promises "no prompts, no transcripts, no paths". Keep that
    # promise mechanical: nothing here may look like a filesystem path or a
    # home directory.
    blob = json.dumps(diag)
    assert os.path.expanduser("~") not in blob
    for leaky in ("workspace", "cwd", "session", "transcript", "prompt",
                  "api_key", "token"):
        assert leaky not in blob.lower(), f"{leaky!r} leaked into diagnostics"


def test_client_context_is_clipped_not_trusted():
    """Anything the browser sends is attacker-controlled on a shared machine;
    it must be bounded before it rides along in a report."""
    diag = support.collect_diagnostics({
        "page": "p" * 5000, "user_agent": "u" * 5000,
        "console_errors": ["e" * 5000] * 50,
        "unexpected_key": "should be dropped"})
    assert len(diag["page"]) <= 200
    assert len(diag["user_agent"]) <= 300
    assert len(diag["console_errors"]) <= 10
    assert all(len(e) <= 300 for e in diag["console_errors"])
    assert "unexpected_key" not in diag


# ── screenshots ──────────────────────────────────────────────────────────
_PNG_1X1 = ("data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8"
            "BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def test_a_screenshot_is_forwarded_with_the_report(client, monkeypatch):
    sent = {}
    monkeypatch.setattr(support, "_post_to_cloud",
                        lambda p: (sent.update(p) or ({"ok": True,
                                                       "ticket": "CM-11111111"}, 200)))
    resp = client.post("/api/bug-report", json={
        "title": "Cost tab is blank", "screenshot": _PNG_1X1,
        "screenshot_name": "cost.png"})
    assert resp.status_code == 200
    assert sent["screenshot"] == _PNG_1X1
    assert sent["screenshot_name"] == "cost.png"


def test_a_non_image_attachment_is_refused_before_it_is_forwarded(client, monkeypatch):
    """A data URL is attacker-shaped input. An HTML or SVG payload dressed as
    an attachment must not reach the intake, let alone an inbox."""
    called = []
    monkeypatch.setattr(support, "_post_to_cloud",
                        lambda p: called.append(p) or ({"ok": True}, 200))
    for payload in ("data:text/html;base64,PHNjcmlwdD4=",
                    "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
                    "https://example.com/not-a-data-url.png",
                    "data:image/png;base64,<script>"):
        resp = client.post("/api/bug-report",
                           json={"title": "x", "screenshot": payload})
        assert resp.status_code == 400, payload
        assert "PNG" in resp.get_json()["error"]
    assert not called, "a rejected attachment still reached the intake"


def test_an_oversized_screenshot_is_refused_with_advice(client, monkeypatch):
    called = []
    monkeypatch.setattr(support, "_post_to_cloud",
                        lambda p: called.append(p) or ({"ok": True}, 200))
    huge = "data:image/png;base64," + "A" * (support.MAX_SCREENSHOT_CHARS + 1)
    resp = client.post("/api/bug-report", json={"title": "x", "screenshot": huge})
    assert resp.status_code == 413
    assert "part that is wrong" in resp.get_json()["error"]
    assert not called


def test_the_dialog_offers_all_three_ways_to_attach_one():
    """Drop, paste and pick. People reach for different ones, and a dialog
    that only accepts a file picker loses the person with a screenshot
    already on their clipboard."""
    import dashboard as d
    from flask import render_template_string

    with d.app.test_request_context("/"):
        html = render_template_string(
            d.DASHBOARD_HTML, version=d.__version__,
            legacy_nav=False, v2_enabled=False, is_pro=False)
    assert 'id="bug-drop"' in html
    assert 'id="bug-file"' in html and 'type="file"' in html
    assert "paste" in html.lower() and "drop" in html.lower()
    # And it must say where the image goes, next to the control itself.
    assert "never attached to the public issue" in html

    js = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "clawmetry", "static", "js", "bug-report.js"),
              encoding="utf-8").read()
    for hook in ("'paste'", "'drop'", "input.click()"):
        assert hook in js, f"{hook} is not wired"
    assert "MAX_EDGE" in js, "images are sent at full size"


# ── the intake URL is operator-settable, so it is not trusted ────────────
def test_a_non_http_intake_url_is_refused_rather_than_opened(client, monkeypatch):
    """CLAWMETRY_SUPPORT_URL comes from the environment and urlopen honours
    whatever scheme it is handed. A file:// intake would turn a bug report
    into a local file read."""
    for bad in ("file:///etc/passwd", "ftp://example.com/x", "gopher://x"):
        monkeypatch.setattr(support, "CLOUD_INTAKE_URL", bad)
        resp = client.post("/api/bug-report", json={"title": "x"})
        assert resp.status_code == 503, bad
        msg = resp.get_json()["error"]
        assert "nothing was sent" in msg.lower()
        # A misconfigured intake is not an offline one: telling this person to
        # check their connection sends them to fix the wrong thing.
        assert "connection" not in msg.lower()
        assert "CLAWMETRY_SUPPORT_URL" in msg
    assert support._intake_url_ok("https://app.clawmetry.com/api/bug-report")
    assert support._intake_url_ok("http://127.0.0.1:8977/api/bug-report")
    assert not support._intake_url_ok("file:///etc/passwd")
    assert not support._intake_url_ok(None)


def test_a_bogus_ticket_never_reaches_the_url_path(client, monkeypatch):
    """The ticket lands in a URL we then fetch, so it is pattern-checked
    before it gets there rather than after."""
    called = []
    monkeypatch.setattr(support.urllib.request, "urlopen",
                        lambda *a, **k: called.append(a) or None)
    for bad in ("../../admin", "CM-%2e%2e", "not-a-ticket", ""):
        resp = client.get("/api/bug-report/" + bad)
        assert resp.status_code in (400, 404), bad
    assert not called, "a malformed ticket was fetched anyway"


def test_reopening_shows_the_form_not_the_last_receipt():
    """A fresh click on Report a bug means "I want to report a bug". Leaving
    the previous receipt up also leaves a keyboard user with nowhere to land,
    because the field that would take focus is hidden behind it."""
    js = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "clawmetry", "static", "js", "bug-report.js"),
              encoding="utf-8").read()
    body = js.split("window.openBugModal", 1)[1].split("window.closeBugModal", 1)[0]
    assert "resetBugForm" in body, "openBugModal leaves a stale receipt up"
    assert "preventScroll" in js, "focusing the first field scrolls the dialog"
