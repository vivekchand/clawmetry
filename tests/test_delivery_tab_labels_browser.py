"""The Delivered tab's rows must read as what they are.

Found by looking at the rendered tab rather than at its data: the
Repositories view showed `vivekchand/clawmetry #vivekchand/clawmetry` and a
chip reading "100 pull requests" over a table of repositories. Both come
from the same cause: ``query_delivery`` carries ``kind`` on the envelope,
not on each row, so ``!r.kind`` was true for every row and every row was
rendered in pull-request form.

Uses the shipped template and app.js with synthetic API fixtures, never a
live store or the user's browser.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPO_ROWS = [
    {"repo": "vivekchand/clawmetry", "ref": "vivekchand/clawmetry",
     "sessions": 94, "cost_usd": 0, "confidence": 1.0, "confidence_min": 1.0,
     "role": "explored", "basis": "pr_reference", "evidence": "git remote -v",
     "title": "", "state": "", "url": "", "merged_at": 0},
    {"repo": "huggingface/lerobot", "ref": "huggingface/lerobot",
     "sessions": 3, "cost_usd": 0, "confidence": 1.0, "confidence_min": 1.0,
     "role": "explored", "basis": "pr_reference",
     "evidence": "git clone https://github.com/huggingface/lerobot.git",
     "title": "", "state": "", "url": "", "merged_at": 0},
]
PR_ROWS = [
    {"repo": "vivekchand/clawmetry", "ref": "6450", "sessions": 2,
     "cost_usd": 12.5, "confidence": 1.0, "confidence_min": 1.0,
     "role": "authored", "basis": "pr_reference",
     "evidence": "gh pr view 6450", "title": "A fold", "state": "merged",
     "url": "https://github.com/vivekchand/clawmetry/pull/6450",
     "merged_at": 0},
]
BRANCH_ROWS = [
    {"repo": "", "ref": "feat/case-fold", "sessions": 1, "cost_usd": 0,
     "confidence": 1.0, "confidence_min": 1.0, "role": "authored",
     "basis": "pr_reference", "evidence": "git push origin feat/case-fold",
     "title": "", "state": "", "url": "", "merged_at": 0},
]
TOTALS = {"attributed_usd": 10.0, "unattributed_usd": 2.0,
          "sessions_attributed": 3, "artifacts": 3}


def _page(browser, rows_by_kind):
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console",
            lambda m: errors.append(m.text) if m.type == "error" else None)
    html = ('<!doctype html><html data-theme="dark"><head><meta charset="utf-8">'
            '</head><body>'
            + (ROOT / "clawmetry/templates/tabs/delivery.html").read_text()
            + "</body></html>")

    def route(request_route):
        path = request_route.request.url.split("delivery.test", 1)[-1]
        if path == "/":
            request_route.fulfill(content_type="text/html", body=html)
            return
        kind = "pr"
        if "kind=" in path:
            kind = path.split("kind=", 1)[1].split("&")[0]
        body = {"rows": rows_by_kind.get(kind, []), "totals": TOTALS,
                "available": True, "kind": kind}
        request_route.fulfill(content_type="application/json",
                              body=json.dumps(body))

    context.route("https://delivery.test/**", route)
    page.goto("https://delivery.test/")
    page.evaluate("""() => {
      window.t = (key, _x, fallback) => fallback || key;
      window.escHtml = s => String(s === undefined || s === null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }""")
    page.add_script_tag(path=str(ROOT / "clawmetry/static/js/app.js"))
    return context, page, errors


def test_a_repository_row_is_not_rendered_as_a_pull_request(_shared_chromium):
    context, page, errors = _page(_shared_chromium, {"repo": REPO_ROWS})
    try:
        page.select_option("#dlv-kind", "repo")
        page.wait_for_function(
            "() => document.querySelectorAll('#dlv-table tbody tr').length > 0")
        first = page.locator("#dlv-table tbody tr td").first.inner_text().strip()
        assert first == "vivekchand/clawmetry", first
        assert "#" not in page.locator("#dlv-table").inner_text()
        # The count chip must name what the table actually lists.
        summary = page.locator("#dlv-summary").inner_text()
        assert "repositories" in summary, summary
        assert "pull requests" not in summary.split("not tied")[-1], summary
        assert errors == [], errors
    finally:
        context.close()


def test_a_pull_request_row_still_reads_repo_then_number(_shared_chromium):
    """The half a kind-aware label could quietly break."""
    context, page, errors = _page(_shared_chromium, {"pr": PR_ROWS})
    try:
        page.evaluate("loadDelivery()")
        page.wait_for_function(
            "() => document.querySelectorAll('#dlv-table tbody tr').length > 0")
        first = page.locator("#dlv-table tbody tr td").first.inner_text()
        assert "vivekchand/clawmetry #6450" in first, first
        assert "pull requests" in page.locator("#dlv-summary").inner_text()
        assert errors == [], errors
    finally:
        context.close()


def test_a_branch_row_shows_the_branch_and_no_hash(_shared_chromium):
    context, page, errors = _page(_shared_chromium, {"branch": BRANCH_ROWS})
    try:
        page.select_option("#dlv-kind", "branch")
        page.wait_for_function(
            "() => document.querySelectorAll('#dlv-table tbody tr').length > 0")
        first = page.locator("#dlv-table tbody tr td").first.inner_text().strip()
        assert first == "feat/case-fold", first
        assert "branches" in page.locator("#dlv-summary").inner_text()
        assert errors == [], errors
    finally:
        context.close()
