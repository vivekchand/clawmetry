"""Regression guard for the transcript-markdown XSS (cloud issue #1566).

The bug: `marked.parse(body)` output was assigned to `innerHTML` with no
sanitization. `body` is raw transcript text (agent output, tool args, inbound
chat-channel messages), so `<img src=x onerror=...>` executed in the dashboard
origin -> gateway/cloud token theft.

The fix routes every markdown render through `cmSafeMarkdown()`, which wraps
`marked.parse()` in `DOMPurify.sanitize()`, and vendors+pins both libs locally
(no external CDN).

These are mechanical, auto-discovering guards: any new bare `marked.parse()`
straight into the DOM, or a regression to the unpinned CDN, goes red.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_JS = (ROOT / "clawmetry" / "static" / "js" / "app.js").read_text()
DASHBOARD = (ROOT / "dashboard.py").read_text()
VENDOR = ROOT / "clawmetry" / "static" / "vendor"


def test_every_marked_parse_is_dompurify_wrapped():
    # Count real calls only: `marked.parse(`. Every one must be inside a
    # `DOMPurify.sanitize(marked.parse(` wrap. (Comments must not contain the
    # literal `marked.parse(` token or they inflate the count — see app.js.)
    total = APP_JS.count("marked.parse(")
    wrapped = APP_JS.count("DOMPurify.sanitize(marked.parse(")
    assert total >= 1, "expected at least one markdown render call"
    assert total == wrapped, (
        "Found %d marked.parse() call(s) but only %d wrapped in "
        "DOMPurify.sanitize(). Every markdown render must go through "
        "cmSafeMarkdown(); never feed marked output straight into innerHTML."
        % (total, wrapped)
    )


def test_no_external_marked_cdn():
    assert "cdn.jsdelivr.net/npm/marked" not in DASHBOARD, (
        "marked must be vendored locally, not loaded from an unpinned CDN"
    )
    assert "vendor/marked.min.js" in DASHBOARD
    assert "vendor/purify.min.js" in DASHBOARD


def test_vendored_libs_present_and_pinned():
    marked = VENDOR / "marked.min.js"
    purify = VENDOR / "purify.min.js"
    assert marked.exists(), "vendored marked.min.js missing (won't ship in wheel)"
    assert purify.exists(), "vendored purify.min.js missing (won't ship in wheel)"
    # Pinned, recognizable builds (banner comment carries the version).
    assert "marked v" in marked.read_text()[:200]
    assert "DOMPurify" in purify.read_text()[:200]
